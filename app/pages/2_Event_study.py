"""Page 2: event study, sector CAR chart with an event selector.

Plot the cumulative abnormal-return path of the energy and consumer portfolios over the
post-event window for a selected Hormuz event, and the cross-event CAAR summary. Read only the
committed event-study parquet.
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

import data

st.set_page_config(page_title="Event study", layout="wide")
st.title("Event study: Hormuz events and sector CAR")

paths = data.load_event_paths()
scalar = data.load_event_scalar()

st.markdown(
    "Market model per sector ticker on the Jakarta Composite return, estimation window 120 "
    "trading days ending 6 days before t=0, post-event window days 0 to 5 inclusive "
    "[docs/ESTIMATION.md, 2026-08-12]. The abnormal return is the realized return minus the "
    "fitted market return; the path is its cumulative sum. Event dates and the selection rule are "
    "committed in data/sources/events/."
)

n_events = int(scalar.shape[0])
st.info(
    f"Events used: {n_events} [docs/ESTIMATION.md, 2026-08-12]. At this count the cross-event "
    "test carries low power (PROJECT_PLAN section 10), and the clustered 2019 and 2026 windows "
    "are not independent. The event study is a supporting result, not the headline."
)

event_dates = list(scalar["event_date"])
chosen = st.selectbox(
    "Event (t=0 date)", event_dates, format_func=lambda d: d.date().isoformat()
)

sub = paths[paths["event_date"] == chosen]
fig = go.Figure()
for portfolio in ["energy", "consumer"]:
    leg = sub[sub["portfolio"] == portfolio].sort_values("day")
    fig.add_trace(go.Scatter(x=leg["day"], y=leg["cum_ar"], name=portfolio, mode="lines+markers"))
fig.update_layout(
    xaxis_title="trading days since t=0",
    yaxis_title="cumulative abnormal return (log points)",
    height=460,
)
st.plotly_chart(fig, use_container_width=True)

row = scalar[scalar["event_date"] == chosen].iloc[0]
st.caption(
    f"Event {chosen.date().isoformat()}: energy CAR {row['energy_car']:.4f}, consumer CAR "
    f"{row['consumer_car']:.4f}, energy minus consumer {row['spread']:.4f}, over the "
    "five-day window."
)

st.subheader("Per-event CAR across the event list")
table = scalar.copy()
table["event_date"] = table["event_date"].dt.date.astype(str)
table["t0_date"] = table["t0_date"].dt.date.astype(str)
st.dataframe(
    table[["event_date", "t0_date", "energy_car", "consumer_car", "spread"]],
    hide_index=True,
    use_container_width=True,
)
