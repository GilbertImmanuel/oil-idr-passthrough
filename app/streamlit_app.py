"""Dashboard entrypoint and navigation.

Set the page config once, render the sidebar appearance toggle, and dispatch to the view pages
through st.navigation. Run with `uv run streamlit run app/streamlit_app.py`.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Oil to Indonesia passthrough", page_icon="🛢️", layout="wide")

import theme  # noqa: E402

theme.render_toggle()

pages = [
    st.Page("views/home.py", title="Home", icon="🏠", default=True),
    st.Page("views/series_explorer.py", title="Series Explorer", icon="📈"),
    st.Page("views/event_study.py", title="Event Study", icon="📅"),
    st.Page("views/irf_viewer.py", title="IRF Viewer", icon="📉"),
    st.Page("views/methodology.py", title="Methodology", icon="📄"),
]
st.navigation(pages).run()
