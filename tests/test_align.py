"""Alignment invariants: spine intersection, returns, null policy, no lookahead.

These run without network access or real snapshots. Each test builds a small
frame in memory.
"""

import numpy as np
import pandas as pd
import pytest

from align import panel


def _wide():
    # A trades all 4 days, B is closed on day 2, C is closed on day 4.
    idx = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-06"])
    return pd.DataFrame(
        {
            "A": [10.0, 11.0, 12.0, 13.0],
            "B": [20.0, np.nan, 22.0, 23.0],
            "C": [30.0, 31.0, 32.0, np.nan],
        },
        index=idx,
    )


def test_trading_spine_is_intersection():
    spine = panel.trading_spine(_wide())
    assert list(spine.strftime("%Y-%m-%d")) == ["2020-01-01", "2020-01-03"]


def test_log_returns_matches_hand_value():
    wide = _wide()
    returns = panel.log_returns(wide.loc[panel.trading_spine(wide)])
    # A on the spine steps 10 -> 12.
    assert returns["A"].iloc[0] == pytest.approx(np.log(12 / 10))


def test_daily_returns_have_no_nan_on_spine():
    wide = _wide()
    returns = panel.log_returns(wide.loc[panel.trading_spine(wide)])
    assert not returns.isna().any().any()
    assert returns.index.is_monotonic_increasing


def test_log_returns_rejects_non_positive():
    idx = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"])
    bad = pd.DataFrame({"A": [1.0, -1.0, 2.0]}, index=idx)
    with pytest.raises(AssertionError):
        panel.log_returns(bad)


def test_lagged_has_no_lookahead():
    series = pd.Series([1, 2, 3, 4])
    # Value at each t equals the value at t-1, so no future data enters.
    assert panel.lagged(series, 1).tolist()[1:] == [1, 2, 3]
    with pytest.raises(AssertionError):
        panel.lagged(series, -1)


def test_monthly_panel_does_not_forward_fill_cpi():
    idx = pd.date_range("2020-01-01", "2020-03-31", freq="D")
    daily = pd.DataFrame({"A": np.arange(len(idx), dtype=float)}, index=idx)
    cpi = pd.Series([105.0, 106.0], index=pd.to_datetime(["2020-01-01", "2020-03-01"]))
    monthly = panel.monthly_panel(daily, cpi, agg="mean")
    # Three month-ends present. February CPI is absent and stays NaN, not filled.
    assert len(monthly) == 3
    assert monthly[panel.CPI_SERIES].isna().sum() == 1
    february = monthly.loc[monthly.index.month == 2, panel.CPI_SERIES]
    assert february.isna().all()


def test_monthly_mean_and_last_differ():
    idx = pd.date_range("2020-01-01", "2020-01-31", freq="D")
    daily = pd.DataFrame({"A": np.arange(1, len(idx) + 1, dtype=float)}, index=idx)
    mean_panel = panel.monthly_panel(daily, agg="mean")
    last_panel = panel.monthly_panel(daily, agg="last")
    assert mean_panel["A"].iloc[0] == pytest.approx(np.mean(np.arange(1, 32)))
    assert last_panel["A"].iloc[0] == 31.0


def test_calendar_report_counts():
    report = panel.calendar_report(_wide())
    assert report["union_days"] == 4
    assert report["spine_days"] == 2
    assert report["per_series"]["B"]["observed_days"] == 3
    assert report["per_series"]["B"]["closed_vs_union"] == 1
