"""Page 3: IRF viewer with shock-size and horizon controls.

Plot the orthogonalized IDR=X response to a Brent shock with its 90 percent bootstrap band, under
a selectable Cholesky ordering, scaled by a shock multiplier and sliced to a horizon. Read only
the committed irf.parquet.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

import compute
import data
import theme

st.title("IRF viewer: IDR=X response to a Brent shock")

irf = data.load_irf()
orderings = list(irf["ordering"].unique())

st.markdown(
    "Orthogonalized impulse response of IDR=X to a Brent shock from the Phase 3 final VAR, four "
    "variables in first differences at lag 2, 90 percent residual-bootstrap band, 1000 "
    "replications [docs/ESTIMATION.md, 2026-08-12]. IDR=X is IDR per USD, so a positive response "
    "is a rupiah depreciation. The response is linear in the shock, so the shock multiplier "
    "scales the response and the band."
)

col1, col2, col3 = st.columns(3)
with col1:
    ordering = st.selectbox("Cholesky ordering", orderings)
with col2:
    shock = st.slider("Shock size (standard deviations)", 0.5, 5.0, 1.0, step=0.5)
with col3:
    horizon = st.slider("Horizon (trading days)", 1, 20, 20, step=1)

leg = compute.scale_irf(irf[irf["ordering"] == ordering], shock)
leg = leg[leg["horizon"] <= horizon].sort_values("horizon")

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=leg["horizon"], y=leg["band_upp"], name="90 band high", mode="lines",
        line={"width": 0}, showlegend=False,
    )
)
fig.add_trace(
    go.Scatter(
        x=leg["horizon"], y=leg["band_low"], name="90 percent band", mode="lines",
        line={"width": 0}, fill="tonexty", fillcolor=theme.band_color(),
    )
)
fig.add_trace(
    go.Scatter(
        x=leg["horizon"], y=leg["response"], name="response", mode="lines",
        line={"color": theme.RESPONSE_COLOR},
    )
)
fig.add_hline(y=0, line_dash="dot", line_color=theme.ZERO_LINE_COLOR)
fig.update_layout(
    title=f"IDR=X response, {ordering} ordering, {shock:.1f} SD shock",
    xaxis_title="horizon (trading days)",
    yaxis_title="IDR=X response (log-return units)",
    hovermode="x unified",
)
theme.style_fig(fig)
st.plotly_chart(fig, use_container_width=True)

resp = leg[leg["horizon"] >= 1]
peak = resp.loc[resp["response"].abs().idxmax()]
c1, c2, c3 = st.columns(3)
c1.metric("Peak response", f"{peak['response']:.5f}")
c2.metric("Peak horizon (days)", int(peak["horizon"]))
c3.metric(f"Cumulative at h={horizon}", f"{float(leg['cum'].iloc[-1]):.5f}")

st.markdown(
    "**Conditional-correlation caveat.** Identification is recursive (Cholesky), so the response "
    "is a conditional correlation, not a causal effect (docs/STYLE.md rule 20). The SPECIFICATION "
    "portmanteau rejected residual whiteness at n=1747 [docs/ESTIMATION.md, 2026-08-12], so read "
    "the band against that. The ordering sensitivity check reports two alternative orderings; the "
    "justification is in docs/DECISIONS.md (2026-08-12)."
)
