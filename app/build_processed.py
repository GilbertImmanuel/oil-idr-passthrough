"""Build the data/processed parquet artifacts the dashboard reads.

Read the aligned frames in data/interim and call the Phase 4 model functions, then write the
model-ready frames the Streamlit app loads at runtime. The app makes no network call and runs no
estimation; every artifact is produced here, once, and committed. Run this whenever the interim
frames or the Phase 4 estimation change.

The build only calls public Phase 4 functions (src/models/estimation.py, event_study.py). It does
not modify Phase 4 code or its outputs. Run `uv run python app/build_processed.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "experiments"))

from models import estimation, event_study  # noqa: E402

INTERIM = REPO_ROOT / "data" / "interim"
PROCESSED = REPO_ROOT / "data" / "processed"

DAILY_PANEL = INTERIM / "daily_panel.parquet"
DAILY_RETURNS = INTERIM / "daily_returns.parquet"


def build_prices() -> pd.DataFrame:
    """Levels panel for the series explorer, copied from the aligned daily panel."""
    return pd.read_parquet(DAILY_PANEL)


def build_returns() -> pd.DataFrame:
    """Log-return panel for the conditional-distribution page, copied from the daily returns."""
    return pd.read_parquet(DAILY_RETURNS)


def build_irf() -> pd.DataFrame:
    """Long-form IDR=X response to a Brent shock, primary ordering and two alternatives.

    Columns: ordering, horizon (0 to 20), response, band_low, band_upp, cum. The viewer scales
    the value columns by the shock multiplier and slices horizon at runtime.
    """
    var = estimation.compute_var()
    horizons = np.arange(estimation.IRF_HORIZON + 1)

    def rows(label: str, irf: dict) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "ordering": label,
                "horizon": horizons,
                "response": irf["response"],
                "band_low": irf["band_low"],
                "band_upp": irf["band_upp"],
                "cum": irf["cum"],
            }
        )

    frames = [rows("primary", var["primary"]["irf"])]
    for label, alt in var["alternatives"].items():
        frames.append(rows(label, alt["irf"]))
    return pd.concat(frames, ignore_index=True)


def _portfolio_car_path(
    returns: pd.DataFrame, event_date: pd.Timestamp, tickers: list[str]
) -> dict | None:
    """Cumulative abnormal-return path of an equal-weight portfolio over the post-event window.

    Mirror the window logic of event_study.event_car so dropped events match Phase 4. The day
    event_study.POST_WINDOW cumulative equals event_study.event_car car_portfolio, since the mean
    across tickers and the cumulative sum over days commute.
    """
    index = returns.index
    t0 = int(index.searchsorted(event_date, side="left"))
    post = event_study.POST_WINDOW
    if t0 >= len(index) or t0 + post >= len(index):
        return None

    est_end = t0 - event_study.GAP
    est_start = max(0, est_end - event_study.EST_LEN)
    if est_end - est_start < event_study.MIN_EST:
        return None

    market = returns[event_study.MARKET]
    est_market = market.iloc[est_start:est_end]
    event_market = market.iloc[t0 : t0 + post + 1]

    abnormal_by_ticker = []
    for ticker in tickers:
        alpha, beta = event_study.market_model(returns[ticker].iloc[est_start:est_end], est_market)
        realized = returns[ticker].iloc[t0 : t0 + post + 1]
        abnormal_by_ticker.append((realized - (alpha + beta * event_market)).to_numpy())

    portfolio_abnormal = np.mean(abnormal_by_ticker, axis=0)
    cum_path = np.cumsum(portfolio_abnormal)
    return {"t0_date": index[t0], "cum_ar": cum_path}


def build_event_car_paths(returns: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-day cumulative AR paths and the scalar per-event CAR table.

    Return (paths_long, scalar_table). paths_long has columns event_date, t0_date, day (0 to
    POST_WINDOW), portfolio (energy or consumer), cum_ar. scalar_table comes from
    event_study.run so the committed numbers match the Phase 4 report.
    """
    events = event_study.load_events()
    portfolios = {"energy": event_study.ENERGY, "consumer": event_study.CONSUMER}

    path_rows = []
    for _, row in events.iterrows():
        computed = {
            name: _portfolio_car_path(returns, row["date"], tickers)
            for name, tickers in portfolios.items()
        }
        if any(c is None for c in computed.values()):
            continue
        for name, comp in computed.items():
            for day, value in enumerate(comp["cum_ar"]):
                path_rows.append(
                    {
                        "event_date": row["date"],
                        "t0_date": comp["t0_date"],
                        "day": day,
                        "portfolio": name,
                        "cum_ar": float(value),
                    }
                )
    paths_long = pd.DataFrame(path_rows)

    result = event_study.run(returns=returns, events=events)
    scalar_table = pd.DataFrame(result["per_event"])
    return paths_long, scalar_table


def build() -> None:
    """Write every processed artifact and run the self-checks."""
    PROCESSED.mkdir(parents=True, exist_ok=True)

    prices = build_prices()
    returns = build_returns()
    irf = build_irf()
    paths, scalar_table = build_event_car_paths(returns)

    # Self-check: the day-POST_WINDOW cumulative path equals the scalar portfolio CAR.
    post = event_study.POST_WINDOW
    day5 = paths[paths["day"] == post].set_index(["event_date", "portfolio"])["cum_ar"]
    for _, e in scalar_table.iterrows():
        got_energy = day5.loc[(e["event_date"], "energy")]
        got_consumer = day5.loc[(e["event_date"], "consumer")]
        assert abs(got_energy - e["energy_car"]) < 1e-9, (e["event_date"], got_energy)
        assert abs(got_consumer - e["consumer_car"]) < 1e-9, (e["event_date"], got_consumer)
    assert len(irf[irf["ordering"] == "primary"]) == estimation.IRF_HORIZON + 1
    assert not prices.empty and not returns.empty

    prices.to_parquet(PROCESSED / "prices.parquet")
    returns.to_parquet(PROCESSED / "returns.parquet")
    irf.to_parquet(PROCESSED / "irf.parquet")
    paths.to_parquet(PROCESSED / "event_car_paths.parquet")
    scalar_table.to_parquet(PROCESSED / "event_car_scalar.parquet")

    written = ["prices", "returns", "irf", "event_car_paths", "event_car_scalar"]
    print("wrote " + ", ".join(f"data/processed/{name}.parquet" for name in written))
    print(
        f"events used {scalar_table.shape[0]}, irf orderings {irf['ordering'].nunique()}, "
        f"prices {prices.shape[0]} rows, returns {returns.shape[0]} rows"
    )


if __name__ == "__main__":
    build()
