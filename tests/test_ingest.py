"""Ingestion invariants: no duplicate date pairs, monotonic dates, manifest match.

These tests run without network access. The live fetchers in fred.py and yahoo.py
are exercised by a manual run, not here.
"""

import json

import pandas as pd
import pytest

from ingest import bps, store


def _frame(dates, values, series_id="X"):
    return pd.DataFrame({"date": dates, "series_id": series_id, "value": values})


@pytest.fixture
def tmp_store(tmp_path, monkeypatch):
    """Redirect the cache and manifest into a temporary directory."""
    raw = tmp_path / "data" / "raw"
    manifest = tmp_path / "data" / "MANIFEST.json"
    monkeypatch.setattr(store, "RAW_DIR", raw)
    monkeypatch.setattr(store, "MANIFEST_PATH", manifest)
    return raw, manifest


def test_tidy_sorts_and_deduplicates():
    frame = store._tidy(_frame(["2020-01-02", "2020-01-01", "2020-01-02"], [2, 1, 2]), "X")
    assert list(frame["date"].astype(str).str[:10]) == ["2020-01-01", "2020-01-02"]
    store.validate(frame, "X")


def test_validate_rejects_duplicate_date_pairs():
    with pytest.raises(AssertionError):
        store.validate(_frame(["2020-01-01", "2020-01-01"], [1, 2]), "X")


def test_validate_rejects_non_monotonic_dates():
    bad = _frame(["2020-01-02", "2020-01-01"], [1, 2])
    bad["date"] = pd.to_datetime(bad["date"])
    with pytest.raises(AssertionError):
        store.validate(bad, "X")


def test_load_or_fetch_caches_once_and_manifest_matches(tmp_store):
    _, manifest = tmp_store
    calls = {"n": 0}

    def fetch_fn():
        calls["n"] += 1
        return _frame(["2020-01-01", "2020-01-02", "2020-01-03"], [1.0, 2.0, 3.0])

    first = store.load_or_fetch("X", "test", fetch_fn)
    second = store.load_or_fetch("X", "test", fetch_fn)

    assert calls["n"] == 1  # second call served from the parquet cache
    assert len(first) == len(second) == 3
    entry = json.loads(manifest.read_text())["X"]
    assert entry["row_count"] == len(first)
    assert entry["first_date"] == "2020-01-01"
    assert entry["last_date"] == "2020-01-03"
    assert len(entry["sha256"]) == 64


def test_bps_snapshot_missing_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(bps, "SNAPSHOT_DIR", tmp_path / "snapshots")
    with pytest.raises(FileNotFoundError):
        bps.fetch("BPS_CPI")


def test_bps_snapshot_parsed_and_cached(tmp_path, monkeypatch, tmp_store):
    snap = tmp_path / "snapshots"
    snap.mkdir()
    (snap / "bps_cpi.csv").write_text("date,value\n2020-01,105.1\n2020-02,105.6\n")
    monkeypatch.setattr(bps, "SNAPSHOT_DIR", snap)

    out = bps.fetch("BPS_CPI")
    assert len(out) == 2
    store.validate(out, "BPS_CPI")
