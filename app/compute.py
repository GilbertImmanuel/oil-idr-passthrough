"""Pure computation for the dashboard, free of Streamlit and of any network call.

Functions here are imported by both the build step (app/build_processed.py) and the tests.
Keeping them Streamlit-free lets the tests import them without launching a server, and keeps
the app runtime clear of the statsmodels and ingestion import chain.

Returns are log returns. IDR=X is quoted as IDR per USD, so a positive IDR=X return is a rupiah
depreciation. Every relationship reported by the dashboard is a conditional correlation, not a
causal effect (docs/STYLE.md rule 20).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Brent spot series id, the conditioning variable for the core visitor feature.
BRENT = "DCOILBRENTEU"

# Frozen JKSE sector membership, docs/DECISIONS.md 2026-08-10. Duplicated from
# src/models/event_study.py (the source of truth) so the app runtime does not import the model
# stack. Change membership through a DECISIONS.md entry, not a silent edit here.
FROZEN_ENERGY = ["MEDC.JK", "PGAS.JK", "ADRO.JK", "ITMG.JK", "PTBA.JK"]
FROZEN_CONSUMER = ["UNVR.JK", "ICBP.JK", "INDF.JK", "MYOR.JK", "GGRM.JK"]

IRF_VALUE_COLUMNS = ["response", "band_low", "band_upp", "cum"]


def portfolio_mean(returns: pd.DataFrame, tickers: list[str]) -> pd.Series:
    """Equal-weight mean daily return of the portfolio members."""
    return returns[tickers].mean(axis=1)


def conditional_forward_returns(
    returns: pd.DataFrame, tickers: list[str], move: float, band: float, n: int
) -> dict:
    """Historical forward N-day portfolio return distribution, conditioned on a Brent move.

    Select each historical day whose Brent log return falls in [move - band, move + band], then
    take the forward cumulative portfolio return over the next n trading days [t+1, t+n]. Days
    without a full forward window are dropped. Return the conditional sample and its counts.

    The result is a conditional empirical distribution over history, not a forecast. move and
    band are in log-return units.
    """
    brent = returns[BRENT].to_numpy()
    portfolio = portfolio_mean(returns, tickers).to_numpy()
    dates = returns.index

    in_band = np.abs(brent - move) <= band
    candidate_pos = np.flatnonzero(in_band)

    sample = []
    episode_dates = []
    for i in candidate_pos:
        if i + n >= len(portfolio):
            continue
        sample.append(float(portfolio[i + 1 : i + n + 1].sum()))
        episode_dates.append(dates[i])
    return {
        "sample": np.asarray(sample, dtype=float),
        "n_episodes": len(sample),
        "n_candidates": int(candidate_pos.size),
        "episode_dates": episode_dates,
    }


def scale_irf(df: pd.DataFrame, k: float) -> pd.DataFrame:
    """Scale an impulse-response frame by a shock multiplier k.

    The orthogonalized IRF is linear in the shock, so a k-fold shock scales the response, the
    band, and the cumulative response by k. Horizon and ordering columns are unchanged.
    """
    out = df.copy()
    out[IRF_VALUE_COLUMNS] = out[IRF_VALUE_COLUMNS] * k
    return out


def demo() -> None:
    """Self-check: band selection, forward-window length, and linear IRF scaling."""
    idx = pd.date_range("2020-01-01", periods=10, freq="B")
    # Brent is +0.05 on day 0 only; every other day is 0. One member portfolio equal to a ramp.
    brent = np.zeros(10)
    brent[0] = 0.05
    port = np.arange(10, dtype=float) / 100.0  # 0.00, 0.01, ...
    returns = pd.DataFrame({BRENT: brent, "MEDC.JK": port}, index=idx)

    res = conditional_forward_returns(returns, ["MEDC.JK"], move=0.05, band=0.001, n=3)
    assert res["n_candidates"] == 1, res["n_candidates"]
    assert res["n_episodes"] == 1, res["n_episodes"]
    # Forward 3-day cumulative from day 0 is days 1, 2, 3: 0.01 + 0.02 + 0.03 = 0.06.
    assert abs(res["sample"][0] - 0.06) < 1e-12, res["sample"][0]

    # A candidate too close to the end drops out for lack of a full forward window.
    res_end = conditional_forward_returns(returns, ["MEDC.JK"], move=0.05, band=0.001, n=20)
    assert res_end["n_candidates"] == 1 and res_end["n_episodes"] == 0, res_end

    irf = pd.DataFrame(
        {"horizon": [0, 1], "response": [1.0, 2.0], "band_low": [0.5, 1.0],
         "band_upp": [1.5, 3.0], "cum": [1.0, 3.0]}
    )
    scaled = scale_irf(irf, 2.0)
    assert scaled["response"].tolist() == [2.0, 4.0], scaled["response"].tolist()
    assert scaled["band_upp"].tolist() == [3.0, 6.0], scaled["band_upp"].tolist()
    assert scaled["horizon"].tolist() == [0, 1], "horizon must not scale"
    print("compute demo ok")


if __name__ == "__main__":
    demo()
