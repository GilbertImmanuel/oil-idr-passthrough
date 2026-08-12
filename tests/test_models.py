"""Unit checks for the Phase 3 descriptive helpers and the loop harness.

These run without network access or real snapshots. Each test builds a small
frame or list in memory.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from models import descriptive, estimation, event_study

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments"))
import cpi_loop  # noqa: E402
import run_loop  # noqa: E402


def test_classify_clear_cells():
    # ADF rejects, KPSS does not reject: stationary in levels, I(0).
    assert descriptive.classify(adf_p_level=0.01, kpss_p_level=0.10) == "I(0)"
    # ADF does not reject, KPSS rejects: unit root in levels, I(1).
    assert descriptive.classify(adf_p_level=0.50, kpss_p_level=0.01) == "I(1)"
    # Both agree: ambiguous, not forced.
    assert descriptive.classify(adf_p_level=0.01, kpss_p_level=0.01) == "ambiguous"
    assert descriptive.classify(adf_p_level=0.50, kpss_p_level=0.10) == "ambiguous"


def test_chow_splits_into_nonempty_finite():
    rng = np.random.default_rng(0)
    n = 200
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    brent = pd.Series(rng.normal(size=n), index=idx)
    idr = pd.Series(rng.normal(size=n), index=idx)
    returns = pd.DataFrame({descriptive.BRENT: brent, descriptive.IDR: idr})
    index, y, x = descriptive._idr_equation(returns)
    split = n // 2
    f = descriptive._chow_f(y, x, split)
    assert split > x.shape[1] and (len(y) - split) > x.shape[1]
    assert np.isfinite(f)


def test_split_index_has_no_lookahead():
    n = 100
    cut = run_loop.split_index(n)
    train_idx = list(range(cut))
    test_idx = list(range(cut, n))
    assert cut == 80
    assert max(train_idx) < min(test_idx)


def test_should_stop_on_consecutive_nonimproving():
    improving = [{"improved": True}, {"improved": False}, {"improved": True}]
    assert run_loop.should_stop(improving) is False
    three_flat = [{"improved": False}, {"improved": False}, {"improved": False}]
    assert run_loop.should_stop(three_flat) is True
    two_flat = [{"improved": True}, {"improved": False}, {"improved": False}]
    assert run_loop.should_stop(two_flat) is False


def test_event_car_recovers_zero_and_injected_jump():
    # Market model, abnormal returns, and portfolio CAR against a synthetic panel.
    event_study.demo()


def test_cpi_leg_splice_exclusion_and_recovered_lag():
    # Splice months absent from the ARDL rows, and a planted Brent lag recovered by OLS.
    cpi_loop.demo()


def test_estimation_irf_matches_and_bootstrap_band_nondegenerate():
    # numpy orthogonalized IRF matches statsmodels, and the bootstrap band brackets it.
    estimation.demo()
