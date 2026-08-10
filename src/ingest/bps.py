"""Ingest BPS monthly series from a pinned downloaded snapshot.

BPS publishes the consumer price index per city, with no single national series
at the WebAPI national domain, and its WebAPI data model takes per-domain and
per-year parameters that change between releases. To keep a rebuild reproducible,
this module parses a downloaded snapshot rather than the live endpoint.

Prepare each snapshot as a two-column CSV with header `date,value`, where `date`
is `YYYY-MM` or `YYYY-MM-DD` and `value` is the numeric level. Save it at the path
from snapshot_path(series_id), then call fetch(series_id). The parquet and its
sha256 are then recorded in the manifest.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .store import RAW_DIR, load_or_fetch

SNAPSHOT_DIR = RAW_DIR / "snapshots"

# series_id: (snapshot filename, source label). The BPS variable ids are 2 for
# the consumer price index and 498 for the trade balance value.
SERIES = {
    "BPS_CPI": ("bps_cpi.csv", "BPS var 2 Indeks Harga Konsumen (Umum)"),
    "BPS_TRADE_BALANCE": ("bps_trade_balance.csv", "BPS var 498 Nilai Neraca Perdagangan"),
}


def snapshot_path(series_id: str) -> Path:
    filename, _ = SERIES[series_id]
    return SNAPSHOT_DIR / filename


def _read_snapshot(series_id: str) -> pd.DataFrame:
    path = snapshot_path(series_id)
    if not path.exists():
        raise FileNotFoundError(
            f"{series_id}: snapshot not found at {path.as_posix()}. Download the "
            f"series from https://www.bps.go.id and save it as a date,value CSV there."
        )
    frame = pd.read_csv(path)
    frame = frame.rename(columns={frame.columns[0]: "date", frame.columns[1]: "value"})
    frame["series_id"] = series_id
    return frame


def fetch(series_id: str) -> pd.DataFrame:
    """Ingest one BPS series from its snapshot and cache it as a tidy long frame."""
    _, source = SERIES[series_id]
    return load_or_fetch(series_id, source, lambda: _read_snapshot(series_id))
