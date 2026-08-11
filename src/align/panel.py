"""Align ingested series into model-ready panels.

Phase 2 turns the per-series parquet snapshots written by src/ingest into
aligned panels for the stationarity tests and the VAR. Each series carries its
own trading calendar. IDX, NYSE, and FX close on different holidays, so the
series do not share every date. The estimation spine is the intersection of the
observed dates. The union frame is kept alongside, with NaN on days a market was
closed and no forward-fill, for reference and robustness checks.

Run `python -m align.panel` to read the raw snapshots, write the interim panels
under data/interim, and print the D6 calendar report.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from ingest import fred, yahoo
from ingest.store import RAW_DIR, _slug  # _slug is the single source of the file-stem rule

INTERIM_DIR = Path("data/interim")

# Daily price series ingested in Phase 1. Log returns apply to these.
PRICE_SERIES = [fred.BRENT_SPOT, *yahoo.all_tickers()]

# Monthly BPS consumer price index. Aligns the monthly leg when its snapshot exists.
CPI_SERIES = "BPS_CPI"


def load_wide(series_ids: list[str]) -> pd.DataFrame:
    """Read each series parquet and pivot to a wide date-indexed frame.

    A missing snapshot file is skipped. Columns follow the order of series_ids.
    The outer join over dates yields the union calendar, with NaN where a series
    had no observation.
    """
    cols: dict[str, pd.Series] = {}
    for sid in series_ids:
        path = RAW_DIR / f"{_slug(sid)}.parquet"
        if not path.exists():
            continue
        frame = pd.read_parquet(path)
        series = frame.set_index("date")["value"]
        series.index = pd.to_datetime(series.index)
        cols[sid] = series.sort_index()
    if not cols:
        raise FileNotFoundError(f"no snapshots found for {series_ids} under {RAW_DIR.as_posix()}")
    wide = pd.DataFrame(cols)
    wide.index.name = "date"
    return wide.sort_index()


def trading_spine(wide: pd.DataFrame) -> pd.DatetimeIndex:
    """Intersection of the dates on which every column has a value.

    A date joins the spine only if every series traded that day. The estimation
    frame uses this spine, so it holds no forward-filled or imputed value.
    """
    return wide.dropna(how="any").index


def log_returns(wide: pd.DataFrame) -> pd.DataFrame:
    """Log first difference of each price column. The first row drops out.

    Prices must be strictly positive. A non-positive price raises AssertionError.
    """
    assert (wide.dropna(how="any") > 0).all().all(), "log_returns requires positive prices"
    return np.log(wide).diff().dropna(how="all")


def rate_diff(wide: pd.DataFrame) -> pd.DataFrame:
    """Level first difference of each rate column. Used for a policy-rate series."""
    return wide.diff().dropna(how="all")


def monthly_panel(
    daily: pd.DataFrame, cpi: pd.Series | None = None, agg: str = "mean"
) -> pd.DataFrame:
    """Aggregate the daily series to monthly and join monthly CPI.

    agg="mean" averages the observed daily values in each calendar month.
    agg="last" takes the month-end observation as a robustness variant. CPI
    enters at its native monthly frequency and is never forward-filled to daily.
    """
    if agg not in {"mean", "last"}:
        raise ValueError(f"agg must be 'mean' or 'last', got {agg!r}")
    grouped = daily.resample("ME")
    monthly = grouped.mean() if agg == "mean" else grouped.last()
    if cpi is not None:
        cpi_m = cpi.copy()
        cpi_m.index = pd.to_datetime(cpi_m.index)
        cpi_m = cpi_m.resample("ME").last().rename(CPI_SERIES)
        monthly = monthly.join(cpi_m, how="left")
    return monthly


def lagged(series: pd.Series, k: int) -> pd.Series:
    """Shift a series k periods into the past. lagged(x, 1) at t equals x at t-1.

    k must be non-negative. A negative shift would pull future values into the
    present and introduce lookahead.
    """
    assert k >= 0, "lag must be non-negative to avoid lookahead"
    return series.shift(k)


def calendar_report(wide: pd.DataFrame) -> dict:
    """D6: trading days per series, days lost to calendar mismatch, spine share.

    union_days counts the distinct dates any series traded. spine_days counts the
    dates every series traded. Per series, observed_days is that series own count
    and closed_vs_union is the days it was closed while at least one market traded.
    """
    union = wide.index
    spine = trading_spine(wide)
    per_series = {}
    for col in wide.columns:
        observed = int(wide[col].notna().sum())
        per_series[col] = {
            "observed_days": observed,
            "closed_vs_union": int(len(union) - observed),
        }
    return {
        "union_days": int(len(union)),
        "spine_days": int(len(spine)),
        "spine_share_of_union": round(len(spine) / len(union), 4) if len(union) else 0.0,
        "first_date": union.min().date().isoformat(),
        "last_date": union.max().date().isoformat(),
        "per_series": per_series,
    }


def build() -> dict:
    """Read the raw snapshots, write the interim panels, and return the D6 report."""
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    wide = load_wide(PRICE_SERIES)
    spine = trading_spine(wide)
    levels = wide.loc[spine]
    returns = log_returns(levels)

    # Intersection frame for estimation, union frame (NaN on closed days) alongside.
    levels.to_parquet(INTERIM_DIR / "daily_panel.parquet")
    wide.to_parquet(INTERIM_DIR / "daily_panel_union.parquet")
    returns.to_parquet(INTERIM_DIR / "daily_returns.parquet")

    report = calendar_report(wide)
    (INTERIM_DIR / "calendar_report.json").write_text(json.dumps(report, indent=2) + "\n")

    # Monthly CPI leg. Runs only when the BPS CPI snapshot is present.
    cpi_path = RAW_DIR / f"{_slug(CPI_SERIES)}.parquet"
    if cpi_path.exists():
        cpi = pd.read_parquet(cpi_path).set_index("date")["value"]
        for agg in ("mean", "last"):
            monthly_panel(wide, cpi, agg=agg).to_parquet(
                INTERIM_DIR / f"monthly_panel_{agg}.parquet"
            )
    return report


if __name__ == "__main__":
    rep = build()
    print(f"union days: {rep['union_days']}")
    print(f"spine days: {rep['spine_days']}")
    print(f"spine share of union: {rep['spine_share_of_union']}")
    print(f"range: {rep['first_date']} to {rep['last_date']}")
    for col, d in rep["per_series"].items():
        print(f"  {col}: observed {d['observed_days']}, closed vs union {d['closed_vs_union']}")
