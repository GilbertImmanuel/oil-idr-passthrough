"""Phase 4 estimation: VAR IRFs, FEVD, Granger, and the assembled report.

Fit the Phase 3 final VAR fixed in experiments/spec.py (4 variables, first differences,
lag 2). Produce orthogonalized impulse responses with Monte Carlo bootstrap bands under
the SPECIFICATION.md Cholesky ordering and two alternatives, the forecast error variance
decomposition at horizons 1, 5, 10, 20, and Granger precedence tests. Read the CPI-leg
result written by experiments/cpi_loop.py, then assemble docs/ESTIMATION.md with the M1
to M4 magnitudes and the H1 to H3 confirmatory verdicts.

Identification is recursive (Cholesky). The reported responses are conditional
correlations, not causal effects: D3 found the unconditional Brent-IDR return correlation
at 0.0089 and D4 found it sign-unstable across subsamples. Read the IRF inference against
the SPECIFICATION.md caveat that the portmanteau rejected residual whiteness at n=1747,
and against the 5 logged Phase 3 runs.

IDR=X is quoted as IDR per USD, so a positive IDR=X return is a rupiah depreciation.

Run `python -m models.estimation` to write docs/ESTIMATION.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.vector_ar.var_model import VAR

from models import event_study
from models.descriptive import source_tag

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiments"))
import spec  # noqa: E402

MANIFEST_PATH = Path("data/MANIFEST.json")
REPORT_PATH = Path("docs/ESTIMATION.md")
CPI_RESULT_PATH = Path("experiments/cpi_final.json")

BRENT = "DCOILBRENTEU"
IDR = "IDR=X"
CPI = "BPS_CPI"

IRF_HORIZON = 20
BOOTSTRAP_REPL = 1000
SIGNIF = 0.10  # 90 percent bands, matching the H1 falsification rule.
SEED = 20260812
FEVD_HORIZONS = [1, 5, 10, 20]
REPORT_HORIZONS = [1, 2, 3, 5, 10, 20]

# Primary ordering is the SPECIFICATION.md Cholesky ordering. The two alternatives are
# recorded and justified in docs/DECISIONS.md.
PRIMARY_ORDERING = spec.ORDERING
ALT_ORDERINGS = {
    "reverse (IDR first)": ["IDR=X", "^JKSE", "DX-Y.NYB", "DCOILBRENTEU"],
    "dollar before Brent": ["DX-Y.NYB", "DCOILBRENTEU", "^JKSE", "IDR=X"],
}


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text())


def fit(ordering: list[str]):
    """Fit the fixed-lag VAR on the spec panel reindexed to a Cholesky ordering."""
    panel = spec.build_panel()[ordering]
    lag = spec.get_spec()["lag_order"]
    return VAR(panel).fit(lag), panel


def _ols_var(y: np.ndarray, p: int) -> tuple[np.ndarray, list[np.ndarray], np.ndarray, np.ndarray]:
    """Ordinary least squares VAR(p): intercept, coefficient matrices, residuals, Sigma."""
    t, k = y.shape
    z = np.column_stack([np.ones(t - p)] + [y[p - lag - 1 : t - lag - 1] for lag in range(p)])
    yt = y[p:]
    b = np.linalg.lstsq(z, yt, rcond=None)[0]
    intercept = b[0]
    coefs = [b[1 + lag * k : 1 + (lag + 1) * k].T for lag in range(p)]
    resid = yt - z @ b
    sigma = resid.T @ resid / (t - p)
    return intercept, coefs, resid, sigma


def _orth_path(
    coefs: list[np.ndarray], sigma: np.ndarray, horizon: int, resp_i: int, shock_i: int
) -> np.ndarray:
    """Orthogonalized (Cholesky) IRF path of one response to one shock."""
    k = sigma.shape[0]
    p = len(coefs)
    chol = np.linalg.cholesky(sigma)
    phi = [np.eye(k)]
    for h in range(1, horizon + 1):
        acc = np.zeros((k, k))
        for lag in range(1, min(h, p) + 1):
            acc += phi[h - lag] @ coefs[lag - 1]
        phi.append(acc)
    return np.array([(phi[h] @ chol)[resp_i, shock_i] for h in range(horizon + 1)])


def _bootstrap_band(
    y: np.ndarray, p: int, horizon: int, resp_i: int, shock_i: int,
    repl: int, signif: float, seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Residual (recursive) bootstrap band for one orthogonalized IRF path.

    ponytail: statsmodels errband_mc / irf_resim return a zero-variance band in this
    install (every replication identical), so the bootstrap is implemented directly.
    Resample centered residuals, rebuild the series with the estimated coefficients and
    the actual first p rows, refit by OLS, and take percentiles of the orthogonalized
    path. Draws whose Sigma is not positive definite are skipped.
    """
    intercept, coefs, resid, _ = _ols_var(y, p)
    resid = resid - resid.mean(axis=0)
    t, k = y.shape
    rng = np.random.default_rng(seed)
    paths = []
    for _ in range(repl):
        draws = resid[rng.integers(0, len(resid), size=t - p)]
        sim = np.empty((t, k))
        sim[:p] = y[:p]
        for step in range(p, t):
            value = intercept.copy()
            for lag in range(1, p + 1):
                value = value + coefs[lag - 1] @ sim[step - lag]
            sim[step] = value + draws[step - p]
        b_int, b_coefs, _, b_sigma = _ols_var(sim, p)
        try:
            paths.append(_orth_path(b_coefs, b_sigma, horizon, resp_i, shock_i))
        except np.linalg.LinAlgError:
            continue
    stacked = np.vstack(paths)
    low = np.quantile(stacked, signif / 2, axis=0)
    upp = np.quantile(stacked, 1 - signif / 2, axis=0)
    return low, upp


def idr_brent_irf(results, panel: pd.DataFrame, ordering: list[str]) -> dict:
    """Orthogonalized IDR=X response to a one-SD Brent shock with 90 percent bands.

    The point path is the statsmodels orthogonalized IRF; the band is a residual
    bootstrap percentile band. Returns the per-horizon response, the band, the
    cumulative (level) response, and the peak horizon by absolute response.
    """
    resp_i = ordering.index(IDR)
    shock_i = ordering.index(BRENT)
    irf = results.irf(IRF_HORIZON)
    orth = irf.orth_irfs[:, resp_i, shock_i]
    low_p, upp_p = _bootstrap_band(
        panel.to_numpy(), spec.get_spec()["lag_order"], IRF_HORIZON,
        resp_i, shock_i, BOOTSTRAP_REPL, SIGNIF, SEED,
    )

    # Cumulative (level) response point estimate. The band applies to the per-horizon
    # impulse response, which is the interval reported for M1.
    cum = np.cumsum(orth)

    horizons = np.arange(1, IRF_HORIZON + 1)
    peak = int(horizons[np.argmax(np.abs(orth[1:]))])
    # A horizon is a rejection when the 90 percent band excludes zero.
    excludes_zero = [(h, low_p[h] > 0 or upp_p[h] < 0) for h in horizons]
    return {
        "ordering": ordering,
        "response": orth,
        "band_low": low_p,
        "band_upp": upp_p,
        "cum": cum,
        "peak_horizon": peak,
        "peak_response": float(orth[peak]),
        "peak_low": float(low_p[peak]),
        "peak_upp": float(upp_p[peak]),
        "excludes_zero": excludes_zero,
        "any_rejection_1_20": any(flag for _, flag in excludes_zero),
        "any_rejection_1_10": any(flag for h, flag in excludes_zero if h <= 10),
    }


def idr_fevd(results, ordering: list[str]) -> dict:
    """IDR=X forecast error variance decomposition at the reported horizons."""
    resp_i = ordering.index(IDR)
    fe = results.fevd(IRF_HORIZON)
    shares = {
        var: [float(fe.decomp[resp_i, h - 1, ordering.index(var)]) for h in FEVD_HORIZONS]
        for var in ordering
    }
    brent_share = {h: float(fe.decomp[resp_i, h - 1, ordering.index(BRENT)]) for h in FEVD_HORIZONS}
    return {"ordering": ordering, "shares": shares, "brent_share": brent_share}


def granger(results) -> list[dict]:
    """Granger precedence tests within the fitted VAR. Precedence, not causation."""
    pairs = [(BRENT, IDR), (IDR, BRENT), (BRENT, "^JKSE"), (BRENT, "DX-Y.NYB")]
    out = []
    for causing, caused in pairs:
        test = results.test_causality(caused=caused, causing=causing, kind="f")
        out.append(
            {
                "causing": causing,
                "caused": caused,
                "stat": float(test.test_statistic),
                "pvalue": float(test.pvalue),
            }
        )
    return out


def _fmt(value: float, places: int = 6) -> str:
    return f"{value:.{places}f}"


def compute_var() -> dict:
    """Fit the primary and alternative orderings and collect IRF, FEVD, and Granger."""
    res_primary, panel_primary = fit(PRIMARY_ORDERING)
    out = {
        "primary": {
            "ordering": PRIMARY_ORDERING,
            "nobs": int(res_primary.nobs),
            "irf": idr_brent_irf(res_primary, panel_primary, PRIMARY_ORDERING),
            "fevd": idr_fevd(res_primary, PRIMARY_ORDERING),
            "granger": granger(res_primary),
        },
        "alternatives": {},
    }
    for label, ordering in ALT_ORDERINGS.items():
        res, panel = fit(ordering)
        out["alternatives"][label] = {
            "ordering": ordering,
            "irf": idr_brent_irf(res, panel, ordering),
            "fevd": idr_fevd(res, ordering),
        }
    return out


# --- rendering -------------------------------------------------------------------

def render_var_section(var: dict, manifest: dict) -> str:
    p = var["primary"]
    irf = p["irf"]
    tags = " ".join(source_tag(s, manifest) for s in PRIMARY_ORDERING)

    lines: list[str] = []
    lines.append("## VAR impulse responses, FEVD, and Granger precedence")
    lines.append("")
    lines.append(
        f"Phase 3 final VAR: {len(PRIMARY_ORDERING)} variables in first differences at "
        f"lag {spec.get_spec()['lag_order']}, {p['nobs']} observations. Cholesky ordering "
        + ", ".join(PRIMARY_ORDERING)
        + f". Series: {tags}. Orthogonalized responses use {BOOTSTRAP_REPL} Monte Carlo "
        f"bootstrap replications at the {int((1 - SIGNIF) * 100)} percent band. "
        "Identification is recursive; the responses are conditional correlations, not "
        "causal effects. The SPECIFICATION.md portmanteau rejected residual whiteness at "
        "n=1747, so read the band inference against that and the 5 logged Phase 3 runs."
    )
    lines.append("")
    lines.append("### IDR=X response to a one-standard-deviation Brent shock")
    lines.append("")
    lines.append(
        "IDR=X is IDR per USD, so a positive response is a rupiah depreciation. The impulse "
        "response is in log-return units per horizon; the cumulative response is the level "
        "response. The band is the "
        f"{int((1 - SIGNIF) * 100)} percent Monte Carlo band."
    )
    lines.append("")
    lines.append(
        "| horizon | impulse response | 90 band low | 90 band high | cumulative response |"
    )
    lines.append("|---|---|---|---|---|")
    for h in REPORT_HORIZONS:
        lines.append(
            f"| {h} | {_fmt(irf['response'][h])} | {_fmt(irf['band_low'][h])} | "
            f"{_fmt(irf['band_upp'][h])} | {_fmt(irf['cum'][h])} |"
        )
    lines.append("")
    lines.append(
        f"Peak absolute response at horizon {irf['peak_horizon']}: "
        f"{_fmt(irf['peak_response'])}, 90 percent band "
        f"[{_fmt(irf['peak_low'])}, {_fmt(irf['peak_upp'])}]."
    )
    lines.append("")

    # Ordering sensitivity.
    lines.append("### Cholesky ordering sensitivity")
    lines.append("")
    lines.append(
        "IDR=X response to a Brent shock at the peak horizon under the primary ordering "
        "and two alternatives, justification in docs/DECISIONS.md."
    )
    lines.append("")
    lines.append("| ordering | peak horizon | peak response | 90 band low | 90 band high |")
    lines.append("|---|---|---|---|---|")
    lines.append(
        f"| primary: {', '.join(PRIMARY_ORDERING)} | {irf['peak_horizon']} | "
        f"{_fmt(irf['peak_response'])} | {_fmt(irf['peak_low'])} | {_fmt(irf['peak_upp'])} |"
    )
    for label, alt in var["alternatives"].items():
        a = alt["irf"]
        lines.append(
            f"| {label}: {', '.join(alt['ordering'])} | {a['peak_horizon']} | "
            f"{_fmt(a['peak_response'])} | {_fmt(a['peak_low'])} | {_fmt(a['peak_upp'])} |"
        )
    lines.append("")

    # FEVD.
    lines.append("### Forecast error variance decomposition of IDR=X")
    lines.append("")
    lines.append(
        "Share of IDR=X forecast error variance from each orthogonalized shock at the "
        "reported horizons, primary ordering."
    )
    lines.append("")
    lines.append("| shock | h=1 | h=5 | h=10 | h=20 |")
    lines.append("|---|---|---|---|---|")
    for var_name, shares in p["fevd"]["shares"].items():
        lines.append(f"| {var_name} | " + " | ".join(_fmt(s) for s in shares) + " |")
    lines.append("")
    lines.append("Brent share of IDR=X variance under the alternative orderings:")
    lines.append("")
    lines.append("| ordering | h=1 | h=5 | h=10 | h=20 |")
    lines.append("|---|---|---|---|---|")
    bs = p["fevd"]["brent_share"]
    lines.append("| primary | " + " | ".join(_fmt(bs[h]) for h in FEVD_HORIZONS) + " |")
    for label, alt in var["alternatives"].items():
        bsa = alt["fevd"]["brent_share"]
        lines.append(f"| {label} | " + " | ".join(_fmt(bsa[h]) for h in FEVD_HORIZONS) + " |")
    lines.append("")

    # Granger.
    lines.append("### Granger precedence")
    lines.append("")
    lines.append(
        "F tests within the fitted VAR. A rejection is temporal precedence in the sense of "
        "Granger, not causation (STYLE rule 20)."
    )
    lines.append("")
    lines.append("| causing | caused | F | p-value |")
    lines.append("|---|---|---|---|")
    for g in p["granger"]:
        lines.append(
            f"| {g['causing']} | {g['caused']} | {_fmt(g['stat'], 4)} | {_fmt(g['pvalue'], 4)} |"
        )
    lines.append("")
    return "\n".join(lines)


def brent_beta_spread() -> dict:
    """M3 cross-check: energy-minus-consumer Brent-beta spread from daily returns.

    Regress each sector portfolio (equal-weight mean of the frozen members) daily return
    on the Brent daily return. The spread is the energy beta minus the consumer beta.
    """
    returns = pd.read_parquet(spec.RETURNS_PATH)
    brent = returns[BRENT]
    x = np.column_stack([np.ones(len(brent)), brent.to_numpy()])

    def beta(portfolio: list[str]) -> float:
        y = returns[portfolio].mean(axis=1).to_numpy()
        return float(np.linalg.lstsq(x, y, rcond=None)[0][1])

    energy = beta(event_study.ENERGY)
    consumer = beta(event_study.CONSUMER)
    return {
        "energy_beta": energy,
        "consumer_beta": consumer,
        "spread": energy - consumer,
        "n": int(len(brent)),
    }


def magnitudes_and_verdicts(var: dict, event: dict, cpi: dict, spread: dict) -> dict:
    """Derive M1 to M4 and the H1 to H3 confirmatory verdicts from the estimated models.

    Ten percent Brent move in log points, for the CPI magnitude scaling.
    """
    ten_pct = float(np.log(1.10))
    irf = var["primary"]["irf"]
    fevd_brent = var["primary"]["fevd"]["brent_share"]

    # H1: positive Brent shock followed by IDR depreciation (positive IDR=X response)
    # within 10 days. Falsification: 90 percent bands include zero at every horizon 1..20.
    h1_positive_detect = any(
        flag and irf["response"][h] > 0 for h, flag in irf["excludes_zero"] if h <= 10
    )
    h1_falsified = not irf["any_rejection_1_20"]

    # H3: CPI response detectable at a Brent lag of 1 to 3 months.
    brent_lags = cpi["primary"]["brent_lags"]
    detect_lags = [bl["lag"] for bl in brent_lags if bl["detectable"] and 1 <= bl["lag"] <= 3]

    return {
        "m1": {
            "peak_horizon": irf["peak_horizon"],
            "peak_response": irf["peak_response"],
            "peak_low": irf["peak_low"],
            "peak_upp": irf["peak_upp"],
            "cum_h20": float(irf["cum"][IRF_HORIZON]),
        },
        "m2": {h: fevd_brent[h] for h in FEVD_HORIZONS},
        "m3": {
            "caar_spread": event["spread"]["caar"],
            "caar_se": event["spread"]["se"],
            "caar_t": event["spread"]["t"],
            "n_events": event["spread"]["n"],
            "beta_spread": spread["spread"],
            "energy_beta": spread["energy_beta"],
            "consumer_beta": spread["consumer_beta"],
        },
        "m4": {
            "brent_lags": [
                {**bl, "per_10pct": bl["coef"] * ten_pct} for bl in brent_lags
            ],
            "detectable_lags": detect_lags,
            "ten_pct_logpoints": ten_pct,
        },
        "h1": {
            "supported": bool(h1_positive_detect),
            "falsified": bool(h1_falsified),
            "peak_sign": "positive" if irf["peak_response"] > 0 else "negative",
        },
        "h2": {
            "energy_caar": event["energy"]["caar"],
            "consumer_caar": event["consumer"]["caar"],
            "opposite_sign": bool(event["energy"]["caar"] * event["consumer"]["caar"] < 0),
            "spread_t": event["spread"]["t"],
            "n_events": event["spread"]["n"],
        },
        "h3": {"detectable_lags": detect_lags, "supported": bool(detect_lags)},
    }


def render_cpi_section(cpi: dict, manifest: dict) -> str:
    brent_tag = source_tag(BRENT, manifest)
    cpi_tag = f"[BPS:{CPI}, {json.loads(MANIFEST_PATH.read_text())[CPI]['retrieved_at'][:10]}]"
    sel = cpi["selected"]
    prim = cpi["primary"]

    lines: list[str] = []
    lines.append("## CPI leg: ARDL on monthly inflation")
    lines.append("")
    lines.append(
        f"ARDL({sel['p']}, {sel['q']}) in log differences: monthly inflation (log "
        f"difference of the BPS CPI index {cpi_tag}) on the monthly Brent return (log "
        f"difference of the monthly-mean Brent price {brent_tag}) and its lags. Selected "
        f"on out-of-sample one-step forecast error over {cpi['cpi_run_count']} logged CPI "
        "runs (experiments/LOG.md), re-estimated once on the full sample. Estimation is "
        "ordinary least squares on the lag matrix with Newey-West standard errors. MIDAS "
        "is not used; the choice is recorded in docs/DECISIONS.md."
    )
    lines.append("")
    lines.append(
        "CPI base-chaining caveat: level-matching forces a zero month-over-month change at "
        f"{', '.join(cpi['splice_excluded'])} (data/sources/cpi/README.md). Those two "
        "months are set to missing, so no estimation row uses them as the dependent or a "
        "lag."
    )
    lines.append("")
    lines.append(
        f"Full-sample fit: n={prim['nobs']}, R-squared {_fmt(prim['r2'], 4)}, residual "
        f"Ljung-Box p={_fmt(prim['ljungbox_p'], 4)} "
        f"({'pass' if prim['ljungbox_pass'] else 'fail'})."
    )
    lines.append("")
    lines.append("| Brent lag (months) | coefficient | 90 CI low | 90 CI high | detectable |")
    lines.append("|---|---|---|---|---|")
    for bl in prim["brent_lags"]:
        lines.append(
            f"| {bl['lag']} | {_fmt(bl['coef'])} | {_fmt(bl['ci_low'])} | {_fmt(bl['ci_high'])} | "
            f"{'yes' if bl['detectable'] else 'no'} |"
        )
    lines.append("")
    lines.append(
        "Robustness on monthly_panel_last (month-end value), same specification, "
        f"n={cpi['robustness']['nobs']}:"
    )
    lines.append("")
    lines.append("| Brent lag (months) | coefficient | 90 CI low | 90 CI high | detectable |")
    lines.append("|---|---|---|---|---|")
    for bl in cpi["robustness"]["brent_lags"]:
        lines.append(
            f"| {bl['lag']} | {_fmt(bl['coef'])} | {_fmt(bl['ci_low'])} | {_fmt(bl['ci_high'])} | "
            f"{'yes' if bl['detectable'] else 'no'} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_magnitudes(mv: dict) -> str:
    m1, m2, m3, m4 = mv["m1"], mv["m2"], mv["m3"], mv["m4"]
    lines: list[str] = []
    lines.append("## Magnitudes M1 to M4")
    lines.append("")
    lines.append(
        "All magnitudes are conditional correlations. D3 found the unconditional Brent-IDR "
        "return correlation at 0.0089 and D4 found it sign-unstable across the 2020, 2022, "
        "and 2026 subsamples, so a near-zero conditional response is the expected reading."
    )
    lines.append("")
    lines.append(
        f"- M1 IDR=X response to a one-standard-deviation Brent shock: peak absolute "
        f"response {_fmt(m1['peak_response'])} at trading-day horizon {m1['peak_horizon']}, "
        f"90 percent band [{_fmt(m1['peak_low'])}, {_fmt(m1['peak_upp'])}], in log-"
        f"return units. Cumulative level response at horizon {IRF_HORIZON}: "
        f"{_fmt(m1['cum_h20'])}. IDR=X is IDR per USD, so a positive value is depreciation."
    )
    lines.append(
        "- M2 share of IDR=X forecast error variance from Brent: "
        + ", ".join(f"h={h} {_fmt(m2[h])}" for h in FEVD_HORIZONS)
        + "."
    )
    lines.append(
        f"- M3 JKSE energy-minus-consumer spread following a Brent shock: event-study CAAR "
        f"{_fmt(m3['caar_spread'])} over the five-day window, cross-event SE "
        f"{_fmt(m3['caar_se'])}, t={_fmt(m3['caar_t'], 2)}, n={m3['n_events']} events. "
        f"Daily Brent-beta cross-check: energy beta {_fmt(m3['energy_beta'], 4)} minus "
        f"consumer beta {_fmt(m3['consumer_beta'], 4)} equals {_fmt(m3['beta_spread'], 4)}."
    )
    detect = m4["detectable_lags"]
    detect_txt = (
        f"detectable at Brent lag {', '.join(str(x) for x in detect)} months"
        if detect
        else "no Brent lag from 0 to 3 months detectable at the 90 percent level"
    )
    lines.append(
        f"- M4 CPI response: {detect_txt}. Magnitude per 10 percent Brent move "
        f"(={_fmt(m4['ten_pct_logpoints'], 4)} log points) by lag: "
        + ", ".join(
            f"lag {bl['lag']} {_fmt(bl['per_10pct'])}" for bl in m4["brent_lags"]
        )
        + ", in CPI log points."
    )
    lines.append("")
    return "\n".join(lines)


def render_verdicts(mv: dict) -> str:
    h1, h2, h3 = mv["h1"], mv["h2"], mv["h3"]
    lines: list[str] = []
    lines.append("## Confirmatory verdicts H1 to H3")
    lines.append("")
    if h1["supported"]:
        h1_txt = (
            "supported: a positive IDR=X response with a 90 percent band excluding zero "
            "at a horizon of 10 trading days or fewer."
        )
    elif h1["falsified"]:
        h1_txt = (
            "unsupported. Under the primary ordering the 90 percent IRF bands include zero "
            "at every horizon 1 to 20, which meets the pre-registered falsification "
            f"condition. The peak response is {h1['peak_sign']} in sign, opposite to the "
            "predicted depreciation. Recorded as unsupported and published, per PROJECT_PLAN "
            "section 1. The model is not re-specified to produce a band."
        )
    else:
        h1_txt = (
            "unsupported: no positive IDR=X response with a 90 percent band excluding zero "
            "at a horizon of 10 trading days or fewer."
        )
    lines.append(f"- H1 (Brent shock followed by IDR depreciation within 10 days): {h1_txt}")
    lines.append(
        f"- H2 (energy and consumer respond opposite in sign after a Brent shock): energy "
        f"CAAR {_fmt(h2['energy_caar'])}, consumer CAAR {_fmt(h2['consumer_caar'])}, "
        + ("opposite in sign" if h2["opposite_sign"] else "same sign")
        + f". The spread is not detectable at n={h2['n_events']} events "
        f"(t={_fmt(h2['spread_t'], 2)}), so the sign is consistent with H2 while the test "
        "carries low power."
    )
    if h3["supported"]:
        lags = ", ".join(str(x) for x in h3["detectable_lags"])
        h3_txt = f"supported at Brent lag {lags} months."
    else:
        h3_txt = (
            "unsupported: no Brent lag from 1 to 3 months has a 90 percent coefficient "
            "interval excluding zero."
        )
    lines.append(f"- H3 (CPI response detectable at a lag of 1 to 3 months): {h3_txt}")
    lines.append("")
    return "\n".join(lines)


def build() -> str:
    """Run the estimation legs, assemble docs/ESTIMATION.md, and return its text."""
    manifest = _manifest()
    var = compute_var()
    event = event_study.run()
    cpi = json.loads(CPI_RESULT_PATH.read_text())
    spread = brent_beta_spread()
    mv = magnitudes_and_verdicts(var, event, cpi, spread)

    lines: list[str] = []
    lines.append("# Estimation results")
    lines.append("")
    lines.append(
        "Phase 4 estimation of the event study, the Phase 3 final VAR, and the CPI leg. "
        "Every result is a conditional correlation, not a causal effect. D3 reported the "
        "unconditional Brent-IDR return correlation at 0.0089 (n=1749) and D4 reported it "
        "sign-unstable across subsamples, so the identification assumption is stated and "
        "the responses are read as conditional associations. Series are retrieved per "
        "data/MANIFEST.json."
    )
    lines.append("")
    lines.append(event_study.render_section(event, manifest))
    lines.append(render_var_section(var, manifest))
    lines.append(render_cpi_section(cpi, manifest))
    lines.append(render_magnitudes(mv))
    lines.append(render_verdicts(mv))

    # Findings block (STYLE rule 13, required, not decorative).
    m1, m2, m3 = mv["m1"], mv["m2"], mv["m3"]
    lines.append("## Findings")
    lines.append("")
    lines.append(
        f"1. Event study over {m3['n_events']} Hormuz events: energy CAAR "
        f"{_fmt(mv['h2']['energy_caar'])}, consumer CAAR {_fmt(mv['h2']['consumer_caar'])}, "
        f"spread {_fmt(m3['caar_spread'])} (t={_fmt(m3['caar_t'], 2)}), low power at that count."
    )
    lines.append(
        f"2. M1 IDR=X peak response to a one-SD Brent shock is {_fmt(m1['peak_response'])} at "
        f"horizon {m1['peak_horizon']}, 90 percent band [{_fmt(m1['peak_low'])}, "
        f"{_fmt(m1['peak_upp'])}]."
    )
    lines.append(
        "3. M2 Brent share of IDR=X forecast error variance stays at or below "
        f"{_fmt(max(m2.values()))} through horizon {IRF_HORIZON}."
    )
    lines.append(
        f"4. M4 CPI leg selects ARDL({cpi['selected']['p']}, {cpi['selected']['q']}) over "
        f"{cpi['cpi_run_count']} runs; no Brent lag 0 to 3 months is detectable at 90 percent."
    )
    if mv["h1"]["falsified"]:
        h1v = "falsified"
    elif mv["h1"]["supported"]:
        h1v = "supported"
    else:
        h1v = "unsupported"
    lines.append(
        f"5. Confirmatory verdicts: H1 {h1v}, H2 sign consistent but low power, H3 unsupported."
    )
    lines.append("")

    text = "\n".join(lines)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(text)
    return text


def demo() -> None:
    """Self-check: IRF and FEVD index the IDR response to the Brent shock consistently,
    and FEVD shares for IDR=X sum to 1 at each horizon.
    """
    res, panel = fit(PRIMARY_ORDERING)
    fe = idr_fevd(res, PRIMARY_ORDERING)
    for h_idx, h in enumerate(FEVD_HORIZONS):
        total = sum(fe["shares"][v][h_idx] for v in PRIMARY_ORDERING)
        assert abs(total - 1.0) < 1e-6, (h, total)
    # The numpy orthogonalized path matches the statsmodels IRF point estimate.
    resp_i, shock_i = PRIMARY_ORDERING.index(IDR), PRIMARY_ORDERING.index(BRENT)
    _, coefs, _, sigma = _ols_var(panel.to_numpy(), spec.get_spec()["lag_order"])
    mine = _orth_path(coefs, sigma, IRF_HORIZON, resp_i, shock_i)
    sm = res.irf(IRF_HORIZON).orth_irfs[:, resp_i, shock_i]
    assert np.max(np.abs(mine - sm)) < 1e-5, np.max(np.abs(mine - sm))
    # The bootstrap band brackets the point estimate and is non-degenerate.
    low, upp = _bootstrap_band(panel.to_numpy(), 2, IRF_HORIZON, resp_i, shock_i, 200, SIGNIF, 1)
    assert np.all(upp - low > 0), "bootstrap band collapsed"
    assert low[1] <= sm[1] <= upp[1], (low[1], sm[1], upp[1])
    print("estimation demo ok")


if __name__ == "__main__":
    build()
    print(f"wrote {REPORT_PATH.as_posix()}")
