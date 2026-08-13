"""Page 1: series explorer with a date-range control.

Plot the level series from the aligned daily panel over a selectable date range. Read only the
committed data/processed/prices.parquet.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

import data
import theme

st.title("Series explorer")
st.markdown(
    "Compare the level series over a selectable date range. The index-to-100 option rebases each "
    "selected series to 100 at the range start, so series on different scales line up. Values load "
    "from the committed data/processed panel with no network call at runtime."
)

prices = data.load_prices()
all_series = list(prices.columns)

default = [s for s in ["DCOILBRENTEU", "IDR=X", "^JKSE"] if s in all_series]
selected = st.multiselect("Series", all_series, default=default)

index = prices.index
start, end = st.select_slider(
    "Date range",
    options=list(index),
    value=(index[0], index[-1]),
    format_func=lambda d: d.date().isoformat(),
)
indexed = st.checkbox("Index to 100 at range start", value=True)

if not selected:
    st.info("Select one or more series.")
else:
    window = prices.loc[start:end, selected]
    if indexed:
        # Rebase each series to 100 at the first day in the range so series on different scales
        # (Brent near 80, JKSE near 7000, IDR near 16000) are comparable on one axis.
        window = window.divide(window.iloc[0]).multiply(100.0)
    ytitle = "indexed level (range start = 100)" if indexed else "level"
    fig = go.Figure()
    for series in selected:
        fig.add_trace(go.Scatter(x=window.index, y=window[series], name=series, mode="lines"))
    fig.update_layout(title="Series levels", yaxis_title=ytitle, hovermode="x unified")
    theme.style_fig(fig, height=520)
    st.plotly_chart(fig, use_container_width=True)

    tags = "  ".join(data.source_tag(s) for s in selected)
    st.caption(
        f"Levels are the yfinance auto-adjusted close, or the FRED level for Brent spot "
        f"(docs/DECISIONS.md 2026-08-10). Sources: {tags}. Range "
        f"{start.date().isoformat()} to {end.date().isoformat()}, {len(window)} trading days."
    )
