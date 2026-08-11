"""Descriptive deliverables D1 to D5 for Phase 3.

Read the aligned daily panels written by src/align/panel.py and report the
stationarity, cointegration, correlation, and structural-break results. Run once
and write docs/DESCRIPTIVES.md. The tests referenced by D1 to D5 are executed a
single time; the reported values are what the tests return.

D2 and the VAR use the macro passthrough chain as the level set: Brent spot,
dollar index, IDR per USD, and the Jakarta Composite. The ten sector tickers feed
the H2 sector spread, not the cointegration system, and are excluded from the
Johansen system. D1 covers every ingested series.

Run `python -m models.descriptive` to regenerate the report.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.tsa.vector_ar.vecm import coint_johansen

INTERIM_DIR = Path("data/interim")
MANIFEST_PATH = Path("data/MANIFEST.json")
REPORT_PATH = Path("docs/DESCRIPTIVES.md")

BRENT = "DCOILBRENTEU"
IDR = "IDR=X"

# Level set for D2 and the VAR: the Brent to dollar to rupiah to equity chain.
LEVEL_SET = ["DCOILBRENTEU", "DX-Y.NYB", "IDR=X", "^JKSE"]

# Bank Indonesia anti-speculation measures, effective April 2026
# [Trading Economics, 2026-03-18].
BREAK_DATE = pd.Timestamp("2026-04-01")

# Subsample years for D4 correlation stability.
SUBSAMPLE_YEARS = [2020, 2022, 2026]

# Symmetric trim for the supF break search. 0.15 keeps the interior 70 percent.
TRIM = 0.15

# Significance level for the ADF, KPSS, and Johansen decisions.
ALPHA = 0.05


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text())


def source_tag(series_id: str, manifest: dict | None = None) -> str:
    """Return the STYLE source tag for a series, e.g. `[FRED:DCOILBRENTEU, 2026-08-10]`."""
    manifest = manifest or _manifest()
    entry = manifest[series_id]
    retrieved = entry["retrieved_at"][:10]
    return f"[{entry['source']}:{series_id}, {retrieved}]"


def _adf(series: pd.Series) -> tuple[float, float]:
    stat, pvalue, *_ = adfuller(series.to_numpy(), autolag="AIC")
    return float(stat), float(pvalue)


def _kpss(series: pd.Series) -> tuple[float, float]:
    with warnings.catch_warnings():
        # KPSS interpolates the p-value from a fixed table and warns at the edges.
        warnings.simplefilter("ignore")
        stat, pvalue, *_ = kpss(series.to_numpy(), regression="c", nlags="auto")
    return float(stat), float(pvalue)


def classify(adf_p_level: float, kpss_p_level: float) -> str:
    """Integration order from the levels tests. ADF null is a unit root, KPSS null is
    stationarity. Reject at ALPHA. The two clear cells are I(0) and I(1); the two
    agreements report as ambiguous rather than force an order.
    """
    adf_stationary = adf_p_level < ALPHA
    kpss_stationary = kpss_p_level >= ALPHA
    if adf_stationary and kpss_stationary:
        return "I(0)"
    if not adf_stationary and not kpss_stationary:
        return "I(1)"
    return "ambiguous"


def d1_integration_order(levels: pd.DataFrame) -> pd.DataFrame:
    """ADF and KPSS on every series in levels and first differences, with the order."""
    rows = []
    for col in levels.columns:
        x = levels[col].dropna()
        dx = x.diff().dropna()
        adf_l, adf_lp = _adf(x)
        kpss_l, kpss_lp = _kpss(x)
        adf_d, adf_dp = _adf(dx)
        kpss_d, kpss_dp = _kpss(dx)
        rows.append(
            {
                "series": col,
                "adf_stat_level": adf_l,
                "adf_p_level": adf_lp,
                "kpss_stat_level": kpss_l,
                "kpss_p_level": kpss_lp,
                "adf_stat_diff": adf_d,
                "adf_p_diff": adf_dp,
                "kpss_stat_diff": kpss_d,
                "kpss_p_diff": kpss_dp,
                "order": classify(adf_lp, kpss_lp),
            }
        )
    return pd.DataFrame(rows).set_index("series")


def _johansen_rank(stat: np.ndarray, crit_95: np.ndarray) -> int:
    """Count rejections of the trace or maximum-eigenvalue null in sequence."""
    rank = 0
    for s, c in zip(stat, crit_95, strict=True):
        if s > c:
            rank += 1
        else:
            break
    return rank


def d2_johansen(levels: pd.DataFrame) -> dict:
    """Johansen cointegration on the level set. Report the rank at ALPHA."""
    system = levels[LEVEL_SET]
    res = coint_johansen(system.to_numpy(), det_order=0, k_ar_diff=1)
    trace, trace_crit = res.lr1, res.cvt[:, 1]
    maxeig, maxeig_crit = res.lr2, res.cvm[:, 1]
    return {
        "series": LEVEL_SET,
        "trace_stat": trace.tolist(),
        "trace_crit_95": trace_crit.tolist(),
        "maxeig_stat": maxeig.tolist(),
        "maxeig_crit_95": maxeig_crit.tolist(),
        "rank_trace": _johansen_rank(trace, trace_crit),
        "rank_maxeig": _johansen_rank(maxeig, maxeig_crit),
        "n": int(len(system)),
    }


def d3_correlation(returns: pd.DataFrame) -> dict:
    """Unconditional Pearson correlation of Brent returns and IDR/USD returns."""
    pair = returns[[BRENT, IDR]].dropna()
    r = float(pair[BRENT].corr(pair[IDR]))
    return {"r": r, "n": int(len(pair))}


def d4_stability(returns: pd.DataFrame) -> pd.DataFrame:
    """D3 correlation recomputed on each subsample year."""
    rows = []
    for year in SUBSAMPLE_YEARS:
        pair = returns.loc[returns.index.year == year, [BRENT, IDR]].dropna()
        r = float(pair[BRENT].corr(pair[IDR])) if len(pair) > 1 else float("nan")
        rows.append({"subsample": str(year), "r": r, "n": int(len(pair))})
    return pd.DataFrame(rows).set_index("subsample")


def _idr_equation(returns: pd.DataFrame) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray]:
    """IDR return equation: idr_t on a constant, idr_{t-1}, and Brent return_t.

    The lagged own term and the contemporaneous Brent return form the equation whose
    parameter constancy D5 tests. The design carries no future value.
    """
    frame = pd.DataFrame(
        {
            "idr": returns[IDR],
            "idr_l1": returns[IDR].shift(1),
            "brent": returns[BRENT],
        }
    ).dropna()
    y = frame["idr"].to_numpy()
    x = sm.add_constant(frame[["idr_l1", "brent"]].to_numpy())
    return frame.index, y, x


def _rss(y: np.ndarray, x: np.ndarray) -> float:
    beta, _, _, _ = np.linalg.lstsq(x, y, rcond=None)
    resid = y - x @ beta
    return float(resid @ resid)


def _chow_f(y: np.ndarray, x: np.ndarray, split: int) -> float:
    """Chow F statistic for a break between rows [0:split) and [split:n)."""
    n, k = x.shape
    pooled = _rss(y, x)
    first = _rss(y[:split], x[:split])
    second = _rss(y[split:], x[split:])
    numerator = (pooled - (first + second)) / k
    denominator = (first + second) / (n - 2 * k)
    return numerator / denominator


def d5_break(returns: pd.DataFrame) -> dict:
    """Chow at the known BI date and a supF search for an unknown break date."""
    index, y, x = _idr_equation(returns)
    n, k = x.shape

    split_known = int((index < BREAK_DATE).sum())
    chow_stat = _chow_f(y, x, split_known)
    chow_p = float(stats.f.sf(chow_stat, k, n - 2 * k))

    lo, hi = int(TRIM * n), int((1 - TRIM) * n)
    sup_stat, sup_split = -np.inf, lo
    for split in range(lo, hi):
        f = _chow_f(y, x, split)
        if f > sup_stat:
            sup_stat, sup_split = f, split

    return {
        "n": int(n),
        "k": int(k),
        "break_date": BREAK_DATE.date().isoformat(),
        "split_known": int(split_known),
        "chow_stat": float(chow_stat),
        "chow_p": chow_p,
        "supf_stat": float(sup_stat),
        "supf_date": index[sup_split].date().isoformat(),
        "trim": TRIM,
    }


def _fmt(value: float, places: int = 4) -> str:
    return f"{value:.{places}f}"


def render(
    d1: pd.DataFrame,
    d2: dict,
    d3: dict,
    d4: pd.DataFrame,
    d5: dict,
    levels: pd.DataFrame,
    manifest: dict,
) -> str:
    """Build the committed markdown report from the D1 to D5 results."""
    brent_tag = source_tag(BRENT, manifest)
    idr_tag = source_tag(IDR, manifest)
    level_tags = " ".join(source_tag(s, manifest) for s in LEVEL_SET)
    first = levels.index.min().date().isoformat()
    last = levels.index.max().date().isoformat()

    lines: list[str] = []
    lines.append("# Descriptive deliverables D1 to D5")
    lines.append("")
    lines.append(
        f"Computed once from data/interim/daily_panel.parquet, spine {first} to {last}, "
        f"{len(levels)} trading days. Each series is retrieved per data/MANIFEST.json. "
        "Test statistics and p-values are reported as returned and are not re-run."
    )
    lines.append("")

    # D1
    lines.append("## D1 integration order")
    lines.append("")
    lines.append(
        f"ADF null is a unit root, KPSS null is stationarity, decided at {ALPHA:.2f}. "
        "The order column applies the levels tests: ADF rejects with KPSS not rejecting "
        "is I(0), the reverse is I(1), an agreement is ambiguous."
    )
    lines.append("")
    lines.append(
        "| series | ADF level | ADF p | KPSS level | KPSS p | ADF diff | ADF p | "
        "KPSS diff | KPSS p | order | source |"
    )
    lines.append("|" + "---|" * 11)
    for series, row in d1.iterrows():
        lines.append(
            f"| {series} | {_fmt(row.adf_stat_level, 3)} | {_fmt(row.adf_p_level, 3)} | "
            f"{_fmt(row.kpss_stat_level, 3)} | {_fmt(row.kpss_p_level, 3)} | "
            f"{_fmt(row.adf_stat_diff, 3)} | {_fmt(row.adf_p_diff, 3)} | "
            f"{_fmt(row.kpss_stat_diff, 3)} | {_fmt(row.kpss_p_diff, 3)} | "
            f"{row.order} | {source_tag(series, manifest)} |"
        )
    lines.append("")

    # D2
    lines.append("## D2 Johansen cointegration")
    lines.append("")
    lines.append(
        "Level set: the macro passthrough chain, "
        + ", ".join(LEVEL_SET)
        + f". Trace and maximum-eigenvalue statistics at the 95 percent critical value, "
        f"n={d2['n']}. Series: {level_tags}."
    )
    lines.append("")
    lines.append("| null rank r | trace stat | trace 95 crit | max-eig stat | max-eig 95 crit |")
    lines.append("|---|---|---|---|---|")
    for i in range(len(d2["series"])):
        lines.append(
            f"| r <= {i} | {_fmt(d2['trace_stat'][i], 3)} | {_fmt(d2['trace_crit_95'][i], 3)} | "
            f"{_fmt(d2['maxeig_stat'][i], 3)} | {_fmt(d2['maxeig_crit_95'][i], 3)} |"
        )
    lines.append("")
    lines.append(
        f"Rank by trace: {d2['rank_trace']}. Rank by maximum eigenvalue: {d2['rank_maxeig']}."
    )
    lines.append("")

    # D3
    lines.append("## D3 Brent and IDR return correlation")
    lines.append("")
    lines.append(
        f"Unconditional Pearson correlation of Brent returns and IDR per USD returns, "
        f"full sample. r={_fmt(d3['r'])}, n={d3['n']}. Series: {brent_tag} {idr_tag}."
    )
    lines.append("")

    # D4
    lines.append("## D4 correlation stability across subsamples")
    lines.append("")
    lines.append(f"The D3 correlation recomputed by calendar year. Series: {brent_tag} {idr_tag}.")
    lines.append("")
    lines.append("| subsample | r | n |")
    lines.append("|---|---|---|")
    for subsample, row in d4.iterrows():
        lines.append(f"| {subsample} | {_fmt(row.r)} | {int(row.n)} |")
    lines.append("")

    # D5
    lines.append("## D5 pre-specified structural break in the IDR equation")
    lines.append("")
    lines.append(
        "Equation: IDR return on a constant, its own first lag, and the Brent return. "
        "The break date is pre-specified at the Bank Indonesia anti-speculation effective "
        "date [Trading Economics, 2026-03-18]. The Chow test uses that date. The supF "
        "search takes the maximum Chow statistic over the interior "
        f"{int(TRIM * 100)} percent-trimmed sample. The supF reference distribution is "
        "non-standard (Andrews 1993), so the argmax date is reported without a pointwise "
        f"p-value. Series: {brent_tag} {idr_tag}."
    )
    lines.append("")
    lines.append("| test | statistic | p-value | date |")
    lines.append("|---|---|---|---|")
    lines.append(
        f"| Chow at known date | {_fmt(d5['chow_stat'])} | {_fmt(d5['chow_p'])} | "
        f"{d5['break_date']} |"
    )
    lines.append(f"| supF unknown date | {_fmt(d5['supf_stat'])} | n/a | {d5['supf_date']} |")
    lines.append("")
    lines.append(f"n={d5['n']}, parameters per segment k={d5['k']}.")
    lines.append("")

    # Findings block (STYLE rule 13, required, not decorative).
    orders = d1["order"].value_counts().to_dict()
    lines.append("## Findings")
    lines.append("")
    lines.append(
        f"1. Integration order across {len(d1)} series: "
        + ", ".join(f"{count} {order}" for order, count in orders.items())
        + "."
    )
    lines.append(
        f"2. Johansen rank on the level set is {d2['rank_trace']} by trace and "
        f"{d2['rank_maxeig']} by maximum eigenvalue, n={d2['n']}."
    )
    lines.append(
        f"3. Full-sample Brent and IDR return correlation is {_fmt(d3['r'])}, n={d3['n']}."
    )
    subsample_txt = ", ".join(
        f"{sub} {_fmt(row.r)} (n={int(row.n)})" for sub, row in d4.iterrows()
    )
    lines.append(f"4. Subsample correlation: {subsample_txt}.")
    lines.append(
        f"5. Chow at {d5['break_date']} is {_fmt(d5['chow_stat'])} "
        f"(p={_fmt(d5['chow_p'])}); supF over the trimmed interior is "
        f"{_fmt(d5['supf_stat'])} at {d5['supf_date']}."
    )
    lines.append("")
    return "\n".join(lines)


def build() -> str:
    """Run D1 to D5 once, write the report, and return its text."""
    levels = pd.read_parquet(INTERIM_DIR / "daily_panel.parquet")
    returns = pd.read_parquet(INTERIM_DIR / "daily_returns.parquet")
    manifest = _manifest()

    d1 = d1_integration_order(levels)
    d2 = d2_johansen(levels)
    d3 = d3_correlation(returns)
    d4 = d4_stability(returns)
    d5 = d5_break(returns)

    report = render(d1, d2, d3, d4, d5, levels, manifest)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report)
    return report


if __name__ == "__main__":
    build()
    print(f"wrote {REPORT_PATH.as_posix()}")
