"""Page 4: methodology and limitations, rendered from docs/METHODOLOGY.md."""

from __future__ import annotations

import streamlit as st

import data

st.set_page_config(page_title="Methodology", layout="wide")
st.markdown(data.load_methodology())
