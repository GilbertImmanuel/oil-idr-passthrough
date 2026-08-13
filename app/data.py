"""Cached data access for the dashboard. Reads committed parquet and the manifest only.

Every loader reads from data/processed or the committed data/MANIFEST.json. No network call and
no model import at runtime. The build step (app/build_processed.py) produces the parquet.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED = REPO_ROOT / "data" / "processed"
MANIFEST_PATH = REPO_ROOT / "data" / "MANIFEST.json"
METHODOLOGY_PATH = REPO_ROOT / "docs" / "METHODOLOGY.md"
NEWS_PATH = REPO_ROOT / "data" / "sources" / "news.csv"


@st.cache_data
def load_prices() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "prices.parquet")


@st.cache_data
def load_returns() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "returns.parquet")


@st.cache_data
def load_irf() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "irf.parquet")


@st.cache_data
def load_event_paths() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "event_car_paths.parquet")


@st.cache_data
def load_event_scalar() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "event_car_scalar.parquet")


@st.cache_data
def load_methodology() -> str:
    return METHODOLOGY_PATH.read_text(encoding="utf-8")


@st.cache_data
def load_news() -> pd.DataFrame:
    """Motivating news links, retrieved 2026-08-10 (PROJECT_PLAN section 2). Motivation, not
    evidence: every quantitative claim in the project cites a data series, not a headline."""
    return pd.read_csv(NEWS_PATH, dtype=str)


@st.cache_data
def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def source_tag(series_id: str) -> str:
    """STYLE source tag for a series, e.g. `[FRED:DCOILBRENTEU, 2026-08-10]` (rule 21)."""
    entry = _manifest()[series_id]
    return f"[{entry['source']}:{series_id}, {entry['retrieved_at'][:10]}]"
