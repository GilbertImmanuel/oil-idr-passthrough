"""Unit checks for the dashboard compute layer and the processed-data build.

These run without network access. Each test builds a small frame in memory. The event CAR path
check reuses the Phase 4 event_study.event_car to confirm the build path is consistent with it.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

APP_DIR = Path(__file__).resolve().parents[1] / "app"
sys.path.insert(0, str(APP_DIR))

import build_processed  # noqa: E402

import compute  # noqa: E402
from models import event_study  # noqa: E402


def test_compute_selection_and_scaling():
    # Band selection, forward-window length, and linear IRF scaling.
    compute.demo()


def test_conditional_window_respects_horizon_and_band():
    idx = pd.date_range("2020-01-01", periods=12, freq="B")
    brent = np.zeros(12)
    brent[2] = 0.05  # one day in the +0.05 neighborhood
    brent[7] = 0.05  # a second day, far enough from the end for n=3
    port = np.full(12, 0.01)
    returns = pd.DataFrame({compute.BRENT: brent, "MEDC.JK": port}, index=idx)

    res = compute.conditional_forward_returns(returns, ["MEDC.JK"], move=0.05, band=0.001, n=3)
    assert res["n_candidates"] == 2, res["n_candidates"]
    assert res["n_episodes"] == 2, res["n_episodes"]
    # Forward 3-day cumulative of a constant 0.01 return is 0.03.
    assert np.allclose(res["sample"], 0.03), res["sample"]
    # A day outside the band contributes nothing.
    empty = compute.conditional_forward_returns(returns, ["MEDC.JK"], move=-0.05, band=0.001, n=3)
    assert empty["n_episodes"] == 0, empty


def _synthetic_returns(n: int = 200, seed: int = 0) -> pd.DataFrame:
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    rng = np.random.default_rng(seed)
    market = rng.normal(scale=0.01, size=n)
    columns = {event_study.MARKET: market}
    for ticker in event_study.ENERGY + event_study.CONSUMER:
        beta = rng.uniform(0.8, 1.4)
        columns[ticker] = beta * market + rng.normal(scale=0.005, size=n)
    return pd.DataFrame(columns, index=idx)


def test_event_car_path_day5_matches_scalar():
    # The build path day-POST_WINDOW cumulative equals the Phase 4 scalar portfolio CAR.
    returns = _synthetic_returns()
    event_date = returns.index[150]
    path = build_processed._portfolio_car_path(returns, event_date, event_study.ENERGY)
    scalar = event_study.event_car(returns, event_date, event_study.ENERGY)
    assert path is not None and scalar is not None
    assert abs(path["cum_ar"][event_study.POST_WINDOW] - scalar["car_portfolio"]) < 1e-9
    assert path["t0_date"] == scalar["t0_date"]
