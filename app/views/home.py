"""Home view: conditional distribution of JKSE sector returns after a Brent move.

Answer one visitor question. Given a Brent move of a stated size today, show the historical
distribution of JKSE sector returns over the next N trading days. The distribution is a
conditional empirical distribution over 2019 to 2026 history, not a forecast, and the association
is a conditional correlation, not a causal effect (docs/STYLE.md rule 20).
"""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go
import streamlit as st

import compute
import data
import theme

st.title("Brent move to JKSE sector returns")
st.markdown(
    "Select a Brent daily move and a horizon. The chart shows the historical distribution of the "
    "forward cumulative return of the JKSE energy and consumer portfolios over the next N trading "
    "days, across every past day whose Brent move fell near the selected size. Sector membership "
    "is frozen in docs/DECISIONS.md (2026-08-10)."
)

returns = data.load_returns()
brent_tag = data.source_tag(compute.BRENT)

col1, col2, col3 = st.columns(3)
with col1:
    move_pct = st.slider("Brent move today (percent)", -20.0, 20.0, 5.0, step=0.5)
with col2:
    horizon = st.slider("Horizon N (trading days)", 1, 20, 5, step=1)
with col3:
    band_pct = st.slider("Neighborhood half-width (percentage points)", 0.5, 5.0, 2.0, step=0.5)

# Work in log-return units to match the panel. The band is a symmetric half-width in log points.
move_log = float(np.log1p(move_pct / 100.0))
band_log = band_pct / 100.0

energy = compute.conditional_forward_returns(
    returns, compute.FROZEN_ENERGY, move_log, band_log, horizon
)
consumer = compute.conditional_forward_returns(
    returns, compute.FROZEN_CONSUMER, move_log, band_log, horizon
)

st.subheader(
    f"Forward {horizon}-day return after a Brent move near {move_pct:+.1f} percent "
    f"(half-width {band_pct:.1f} points)"
)

n_episodes = energy["n_episodes"]
if n_episodes == 0:
    st.warning(
        "No historical day has a Brent move in this neighborhood with a full forward window. "
        "Widen the half-width or reduce the horizon."
    )
else:
    if n_episodes < 5:
        st.warning(
            f"Only {n_episodes} historical episodes match. The distribution is thin, so read it "
            "with caution."
        )

    def to_percent(sample: np.ndarray) -> np.ndarray:
        # Cumulative log return to simple percent return.
        return 100.0 * np.expm1(sample)

    energy_pct = to_percent(energy["sample"])
    consumer_pct = to_percent(consumer["sample"])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Episodes", n_episodes)
    m2.metric("Median energy return", f"{float(np.median(energy_pct)):+.2f}%")
    m3.metric("Median consumer return", f"{float(np.median(consumer_pct)):+.2f}%")
    m4.metric("Energy share positive", f"{float(np.mean(energy_pct > 0)) * 100:.0f}%")

    fig = go.Figure()
    fig.add_trace(
        go.Box(
            y=energy_pct, name="energy", boxpoints="all", jitter=0.4, pointpos=0,
            marker_color=theme.ENERGY_COLOR, boxmean=True,
        )
    )
    fig.add_trace(
        go.Box(
            y=consumer_pct, name="consumer", boxpoints="all", jitter=0.4, pointpos=0,
            marker_color=theme.CONSUMER_COLOR, boxmean=True,
        )
    )
    fig.add_hline(y=0, line_dash="dot", line_color=theme.ZERO_LINE_COLOR)
    fig.update_layout(
        title=f"Forward {horizon}-day return distribution",
        yaxis_title=f"forward {horizon}-day return (percent)",
        showlegend=False,
    )
    theme.style_fig(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        f"Conditioning series: Brent spot {brent_tag}. Matched {n_episodes} historical days of "
        f"{len(returns)} in the panel. The box shows the quartiles and the median; the dashed "
        "line marks the mean."
    )

st.divider()
st.markdown(
    "**Conditional-correlation caveat.** The chart is a conditional empirical distribution over "
    "history, not a forecast and not a causal effect. The unconditional correlation of Brent "
    "returns and IDR per USD returns is 0.0089 over the full sample "
    "[docs/DESCRIPTIVES.md D3, 2026-08-11], and that correlation is sign-unstable across the "
    "2020, 2022, and 2026 subsamples [docs/DESCRIPTIVES.md D4, 2026-08-11]. Oil, the dollar, and "
    "risk sentiment move together, so the displayed association is conditional on the sample and "
    "the confounders, not an identified response. See the Methodology page for the full "
    "specification and limitations."
)

with st.expander("News context and sources (motivation, not evidence)"):
    st.markdown(
        "The headlines below motivate the question and anchor it to conditions through 2026. They "
        "are not evidence: every quantitative claim in the project cites a data series, not a "
        "headline (PROJECT_PLAN section 2). Retrieved 2026-08-10."
    )
    st.dataframe(
        data.load_news(),
        hide_index=True,
        use_container_width=True,
        column_config={"url": st.column_config.LinkColumn("link", display_text="open")},
    )
