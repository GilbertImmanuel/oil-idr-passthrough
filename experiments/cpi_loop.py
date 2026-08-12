"""CPI-leg ARDL loop for Phase 4, under the program.md Karpathy guardrails.

Model monthly Indonesian inflation on monthly Brent returns and their lags:

    dcpi_t = c + sum_{i=1..p} phi_i dcpi_{t-i} + sum_{j=0..q} beta_j dbrent_{t-j} + e_t

where dcpi is the log difference of the BPS CPI index and dbrent is the log difference
of the monthly-mean Brent price. Both level series are I(1) (D1), so the model is
specified in log differences. Estimation is ordinary least squares on the lag matrix,
which is the ARDL(p, q) form. MIDAS is not used: statsmodels has no MIDAS routine and the
panels are already monthly, so a mixed-frequency model adds a dependency with no gain.
The ARDL-vs-MIDAS choice is recorded in docs/DECISIONS.md.

CPI base-chaining caveat: level-matching forces a zero month-over-month change at the two
splice months 2020-01 and 2024-01 (data/sources/cpi/README.md). Those two dcpi values are
set to NaN, so any row using them as the dependent or as a lag is dropped from estimation.

Guardrails (program.md): H1 to H3 are fixed. Selection runs only on out-of-sample
one-step forecast error on the held-out final 20 percent, never on a p-value or the Brent
coefficient sign. Every candidate appends one run to experiments/LOG.md with a per-run
json in experiments/runs/. The loop stops at 50 runs or 3 consecutive non-improving runs.
The selected model is re-estimated once on the full sample and its diagnostics are
reported. The Brent lag inference for H3 and M4 is read off the selected model, separate
from selection.

Run `python experiments/cpi_loop.py` to run the loop and write experiments/cpi_final.json.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import acorr_ljungbox

MEAN_PATH = Path("data/interim/monthly_panel_mean.parquet")
LAST_PATH = Path("data/interim/monthly_panel_last.parquet")
RUNS_DIR = Path("experiments/runs")
LOG_PATH = Path("experiments/LOG.md")
RESULT_PATH = Path("experiments/cpi_final.json")

BRENT = "DCOILBRENTEU"
CPI = "BPS_CPI"
SPLICE_MONTHS = ["2020-01", "2024-01"]

TEST_FRACTION = 0.20
MAX_RUNS = 50
MAX_NONIMPROVING = 3
LJUNGBOX_LAGS = 6
ALPHA = 0.05
SIGNIF = 0.10  # 90 percent intervals, matching the VAR leg.

# Candidate (p, q) grid, ordered from the H3 prior (Brent lags 1 to 3) outward.
GRID = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (1, 0), (2, 0), (3, 2)]


def build_series(path: Path) -> pd.DataFrame:
    """Monthly inflation and Brent return, splice-month inflation set to NaN."""
    panel = pd.read_parquet(path)
    dcpi = np.log(panel[CPI]).diff()
    dbrent = np.log(panel[BRENT]).diff()
    for month in SPLICE_MONTHS:
        mask = dcpi.index.strftime("%Y-%m") == month
        dcpi[mask] = np.nan
    return pd.DataFrame({"dcpi": dcpi, "dbrent": dbrent})


def design(
    df: pd.DataFrame, p: int, q: int
) -> tuple[np.ndarray, np.ndarray, list[str], pd.DatetimeIndex]:
    """Build y, X (with intercept), column names, and the row index for ARDL(p, q).

    Rows with any missing value in y or a used lag are dropped, which also removes the
    splice-month observations and any row that lags onto them.
    """
    names = ["const"]
    frame = {"dcpi": df["dcpi"]}
    for i in range(1, p + 1):
        frame[f"dcpi_l{i}"] = df["dcpi"].shift(i)
        names.append(f"dcpi_l{i}")
    for j in range(0, q + 1):
        frame[f"dbrent_l{j}"] = df["dbrent"].shift(j)
        names.append(f"dbrent_l{j}")
    full = pd.DataFrame(frame).dropna(how="any")
    y = full["dcpi"].to_numpy()
    x = sm.add_constant(full[names[1:]].to_numpy(), has_constant="add")
    return y, x, names, full.index


def oos_one_step_rmse(y: np.ndarray, x: np.ndarray) -> float:
    """Standardized one-step out-of-sample RMSE on the held-out final 20 percent."""
    n = len(y)
    cut = int(n * (1 - TEST_FRACTION))
    beta, _, _, _ = np.linalg.lstsq(x[:cut], y[:cut], rcond=None)
    scale = y[:cut].std(ddof=1)
    resid = (y[cut:] - x[cut:] @ beta) / scale
    return float(np.sqrt(np.mean(resid**2)))


def fit_full(y: np.ndarray, x: np.ndarray, names: list[str]) -> dict:
    """Full-sample OLS with HAC (Newey-West) standard errors and 90 percent intervals."""
    model = sm.OLS(y, x).fit(cov_type="HAC", cov_kwds={"maxlags": LJUNGBOX_LAGS})
    z = 1.6448536269514722  # 0.95 normal quantile for the 90 percent interval.
    coefs = {}
    for i, name in enumerate(names):
        coefs[name] = {
            "coef": float(model.params[i]),
            "se": float(model.bse[i]),
            "ci_low": float(model.params[i] - z * model.bse[i]),
            "ci_high": float(model.params[i] + z * model.bse[i]),
        }
    lb = acorr_ljungbox(model.resid, lags=[LJUNGBOX_LAGS], return_df=True)
    return {
        "coefs": coefs,
        "nobs": int(model.nobs),
        "r2": float(model.rsquared),
        "ljungbox_stat": float(lb["lb_stat"].iloc[0]),
        "ljungbox_p": float(lb["lb_pvalue"].iloc[0]),
        "ljungbox_pass": bool(lb["lb_pvalue"].iloc[0] > ALPHA),
    }


def _spec_hash(p: int, q: int, path: Path) -> str:
    return hashlib.sha256(f"cpi-ardl:{path.name}:p={p}:q={q}".encode()).hexdigest()


def _append_log(run_id: int, p: int, q: int, oos: float, diag: dict, kept: bool) -> None:
    passes = "pass" if diag["ljungbox_pass"] else "fail"
    line = (
        f"\n### Run {run_id}\n\n"
        f"- Timestamp: {datetime.now(UTC).isoformat(timespec='seconds')}\n"
        f"- Spec hash: {_spec_hash(p, q, MEAN_PATH)}\n"
        f"- Out-of-sample metric: {oos:.6f}\n"
        f"- BIC: n/a\n"
        f"- Diagnostics: Ljung-Box p={diag['ljungbox_p']:.4f} ({passes})\n"
        f"- Decision: {'kept' if kept else 'discarded'}\n"
        f"- Note: cpi-leg ARDL p={p} q={q} panel=monthly_panel_mean\n"
    )
    with LOG_PATH.open("a") as handle:
        handle.write(line)


def _next_run_id() -> int:
    existing = [int(p.stem.split("_")[1]) for p in RUNS_DIR.glob("run_*.json")]
    return (max(existing) + 1) if existing else 1


def _brent_lags(coefs: dict) -> list[dict]:
    """Brent distributed-lag coefficients ordered by lag, with detectability flag."""
    out = []
    for name, c in coefs.items():
        if name.startswith("dbrent_l"):
            lag = int(name.split("l")[-1])
            detect = c["ci_low"] > 0 or c["ci_high"] < 0
            out.append({"lag": lag, **c, "detectable": bool(detect)})
    return sorted(out, key=lambda d: d["lag"])


def run() -> dict:
    """Run the guarded loop, log each candidate, and write the selected-model result."""
    df = build_series(MEAN_PATH)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    prior_best = float("inf")
    nonimproving = 0
    selected = None
    runs_done = 0

    with LOG_PATH.open("a") as handle:
        handle.write("\n## CPI leg (Phase 4)\n\n")
        handle.write(
            "ARDL(p, q) in log differences on monthly inflation and Brent returns, "
            "selected on out-of-sample one-step forecast error. Run ids continue the "
            "append-only sequence. The Phase 3 VAR run count (5) is unchanged.\n"
        )

    for p, q in GRID:
        if runs_done >= MAX_RUNS or nonimproving >= MAX_NONIMPROVING:
            break
        y, x, names, _ = design(df, p, q)
        oos = oos_one_step_rmse(y, x)
        diag = fit_full(y, x, names)
        improved = oos < prior_best
        kept = improved and diag["ljungbox_pass"]

        run_id = _next_run_id()
        record = {
            "run_id": run_id,
            "leg": "cpi",
            "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
            "spec": {"p": p, "q": q, "panel": "monthly_panel_mean"},
            "oos_metric": oos,
            "diagnostics": {
                "ljungbox_p": diag["ljungbox_p"],
                "ljungbox_pass": diag["ljungbox_pass"],
            },
            "improved": improved,
            "kept": kept,
        }
        (RUNS_DIR / f"run_{run_id:03d}.json").write_text(json.dumps(record, indent=2) + "\n")
        _append_log(run_id, p, q, oos, diag, kept)

        if improved:
            prior_best = oos
            selected = (p, q)
            nonimproving = 0
        else:
            nonimproving += 1
        runs_done += 1

    # Guardrail 5: re-estimate the selected model once on the full sample.
    p, q = selected
    y, x, names, _ = design(df, p, q)
    final_mean = fit_full(y, x, names)

    # Robustness: the selected spec on the month-end-last panel.
    df_last = build_series(LAST_PATH)
    yl, xl, names_l, _ = design(df_last, p, q)
    final_last = fit_full(yl, xl, names_l)

    result = {
        "selected": {"p": p, "q": q},
        "oos_metric": prior_best,
        "cpi_run_count": runs_done,
        "primary": {
            "panel": "monthly_panel_mean",
            "nobs": final_mean["nobs"],
            "r2": final_mean["r2"],
            "ljungbox_p": final_mean["ljungbox_p"],
            "ljungbox_pass": final_mean["ljungbox_pass"],
            "coefs": final_mean["coefs"],
            "brent_lags": _brent_lags(final_mean["coefs"]),
        },
        "robustness": {
            "panel": "monthly_panel_last",
            "nobs": final_last["nobs"],
            "brent_lags": _brent_lags(final_last["coefs"]),
        },
        "splice_excluded": SPLICE_MONTHS,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2) + "\n")
    return result


def demo() -> None:
    """Self-check: splice months are absent from the estimation rows, and a planted
    Brent effect is recovered by OLS.
    """
    df = build_series(MEAN_PATH)
    _, _, _, index = design(df, 2, 2)
    stamps = index.strftime("%Y-%m")
    for month in SPLICE_MONTHS:
        assert month not in set(stamps), f"splice month {month} leaked into estimation"

    rng = np.random.default_rng(0)
    n = 120
    idx = pd.date_range("2015-01-31", periods=n, freq="ME")
    dbrent = pd.Series(rng.normal(scale=0.05, size=n), index=idx)
    dcpi = 0.30 * dbrent.shift(1).fillna(0.0) + rng.normal(scale=0.001, size=n)
    planted = pd.DataFrame({"dcpi": dcpi, "dbrent": dbrent})
    y, x, names, _ = design(planted, 1, 1)
    beta, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
    lag1 = beta[names.index("dbrent_l1")]
    assert abs(lag1 - 0.30) < 0.05, lag1
    print("cpi_loop demo ok")


if __name__ == "__main__":
    result = run()
    sel = result["selected"]
    print(
        f"selected ARDL p={sel['p']} q={sel['q']} oos={result['oos_metric']:.6f} "
        f"cpi runs={result['cpi_run_count']} nobs={result['primary']['nobs']}"
    )
    for bl in result["primary"]["brent_lags"]:
        flag = "detectable" if bl["detectable"] else "not detectable"
        print(
            f"  dbrent lag {bl['lag']}: {bl['coef']:.4f} "
            f"[90% {bl['ci_low']:.4f}, {bl['ci_high']:.4f}] {flag}"
        )
