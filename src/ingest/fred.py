"""Fetch series from FRED. Requires FRED_API_KEY in the environment or in .env."""

from __future__ import annotations

import os

import pandas as pd
from fredapi import Fred

from .store import load_env, load_or_fetch

BRENT_SPOT = "DCOILBRENTEU"
START = "2019-01-01"


def fetch(series_id: str = BRENT_SPOT, start: str = START) -> pd.DataFrame:
    """Fetch one FRED series by id and cache it as a tidy long frame."""

    def _fetch() -> pd.DataFrame:
        load_env()
        key = os.environ.get("FRED_API_KEY")
        assert key, "FRED_API_KEY is not set (add it to .env)"
        series = Fred(api_key=key).get_series(series_id, observation_start=start)
        frame = series.rename("value").rename_axis("date").reset_index()
        frame["series_id"] = series_id
        return frame

    return load_or_fetch(series_id, "FRED", _fetch)
