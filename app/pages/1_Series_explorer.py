"""Page 1: series explorer with a date-range control.

Plot the level series from the aligned daily panel over a selectable date range. Read only the
committed data/processed/prices.parquet.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

import data

st.set_page_config(page_title="Series explorer", layout="wide")
st.title("Series explorer")

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

if not selected:
    st.info("Select one or more series.")
else:
    window = prices.loc[start:end, selected]
    fig = go.Figure()
    for series in selected:
        fig.add_trace(go.Scatter(x=window.index, y=window[series], name=series, mode="lines"))
    fig.update_layout(yaxis_title="level (adjusted close, or index level)", height=520)
    st.plotly_chart(fig, use_container_width=True)

    tags = "  ".join(data.source_tag(s) for s in selected)
    st.caption(
        f"Levels are the yfinance auto-adjusted close, or the FRED level for Brent spot "
        f"(docs/DECISIONS.md 2026-08-10). Sources: {tags}. Range "
        f"{start.date().isoformat()} to {end.date().isoformat()}, {len(window)} trading days."
    )
