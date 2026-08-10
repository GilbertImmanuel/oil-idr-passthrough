"""Ingest Bank Indonesia series from a pinned downloaded snapshot.

Bank Indonesia publishes the policy rate history and JISDOR as table pages with
no stable programmatic endpoint. To keep a rebuild reproducible, this module
parses a downloaded snapshot rather than the live page.

Prepare each snapshot as a two-column CSV with header `date,value`, where `date`
is `YYYY-MM-DD` and `value` is the numeric level (percent for the policy rate,
IDR per USD for JISDOR). Save it at the path from snapshot_path(series_id), then
call fetch(series_id). The parquet and its sha256 are then recorded in the manifest.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .store import RAW_DIR, load_or_fetch

SNAPSHOT_DIR = RAW_DIR / "snapshots"

# series_id: (snapshot filename, source label).
SERIES = {
    "BI_POLICY_RATE": ("bi_policy_rate.csv", "Bank Indonesia policy rate"),
    "BI_JISDOR": ("bi_jisdor.csv", "Bank Indonesia JISDOR"),
}


def snapshot_path(series_id: str) -> Path:
    filename, _ = SERIES[series_id]
    return SNAPSHOT_DIR / filename


def _read_snapshot(series_id: str) -> pd.DataFrame:
    path = snapshot_path(series_id)
    if not path.exists():
        raise FileNotFoundError(
            f"{series_id}: snapshot not found at {path.as_posix()}. Download the "
            f"series from https://www.bi.go.id and save it as a date,value CSV there."
        )
    frame = pd.read_csv(path)
    frame = frame.rename(columns={frame.columns[0]: "date", frame.columns[1]: "value"})
    frame["series_id"] = series_id
    return frame


def fetch(series_id: str) -> pd.DataFrame:
    """Ingest one Bank Indonesia series from its snapshot as a tidy long frame."""
    _, source = SERIES[series_id]
    return load_or_fetch(series_id, source, lambda: _read_snapshot(series_id))
