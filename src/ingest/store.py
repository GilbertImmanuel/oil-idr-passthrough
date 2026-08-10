"""Immutable parquet cache and manifest for ingested series.

Each series is fetched at most once. The first fetch writes
`data/raw/<slug>.parquet` and records an entry in `data/MANIFEST.json`. Later
calls read the parquet and never overwrite it. A clone verifies a rebuild by
comparing the recorded sha256 against a re-fetch.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw")
MANIFEST_PATH = Path("data/MANIFEST.json")
COLUMNS = ["date", "series_id", "value"]


def load_env(path: str | os.PathLike = ".env") -> None:
    """Read KEY=VALUE lines from a .env file into os.environ without overwriting.

    Existing environment values win, so an exported variable is not replaced.
    """
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        line = line.strip()
        # ponytail: minimal reader; add python-dotenv if quoting or interpolation is needed.
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _slug(series_id: str) -> str:
    """Filesystem-safe file stem for a series id. `^JKSE` becomes `_JKSE`."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", series_id)


def _tidy(frame: pd.DataFrame, series_id: str) -> pd.DataFrame:
    """Coerce a fetched frame to the tidy long schema, sorted and deduplicated."""
    out = frame.loc[:, COLUMNS].copy()
    dates = pd.to_datetime(out["date"])
    try:
        dates = dates.dt.tz_localize(None)
    except TypeError:
        pass  # already tz-naive
    out["date"] = dates.dt.normalize()
    out["series_id"] = series_id
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    out = out.dropna(subset=["value"])
    out = out.drop_duplicates(subset=["date", "series_id"])
    out = out.sort_values("date").reset_index(drop=True)
    return out


def validate(frame: pd.DataFrame, series_id: str) -> None:
    """Enforce the ingestion invariants. Raises AssertionError on any violation."""
    assert list(frame.columns) == COLUMNS, f"{series_id}: columns are {list(frame.columns)}"
    assert len(frame) > 0, f"{series_id}: empty frame"
    assert (frame["series_id"] == series_id).all(), f"{series_id}: mixed series_id values"
    assert not frame.duplicated(["date", "series_id"]).any(), f"{series_id}: duplicate date pairs"
    assert frame["date"].is_monotonic_increasing, f"{series_id}: date index is not monotonic"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_manifest_entry(series_id: str, source: str, path: Path, frame: pd.DataFrame) -> None:
    manifest: dict = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text())
    manifest[series_id] = {
        "source": source,
        "file": path.as_posix(),
        "retrieved_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "first_date": frame["date"].min().date().isoformat(),
        "last_date": frame["date"].max().date().isoformat(),
        "row_count": int(len(frame)),
        "sha256": _sha256(path),
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(dict(sorted(manifest.items())), indent=2) + "\n")


def load_or_fetch(
    series_id: str, source: str, fetch_fn: Callable[[], pd.DataFrame]
) -> pd.DataFrame:
    """Return the cached series if present, else fetch once, cache, and record it.

    The parquet snapshot is immutable. An existing file is read and never
    overwritten, so a second call for the same series makes no network request.
    """
    path = RAW_DIR / f"{_slug(series_id)}.parquet"
    if path.exists():
        return pd.read_parquet(path)
    frame = _tidy(fetch_fn(), series_id)
    validate(frame, series_id)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)
    _write_manifest_entry(series_id, source, path, frame)
    return frame
