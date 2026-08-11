"""Karpathy Loop harness. Reads experiments/spec.py, estimates the VAR, logs one run.

One invocation evaluates the current spec once. The metric is the out-of-sample
one-step forecast error on the held-out final 20 percent of the sample, reported
with BIC on the training portion. Selection uses the out-of-sample value only,
never a p-value or the sign of the Brent coefficient (guardrail 2).

Each run writes experiments/runs/run_NNN.json and appends one entry to
experiments/LOG.md, whether kept or discarded. The loop stops at 50 runs or 3
consecutive non-improving runs (guardrail 4).

Usage:
  python experiments/run_loop.py           evaluate the current spec, log the run
  python experiments/run_loop.py --final    re-estimate on the full sample, write
                                             docs/SPECIFICATION.md
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from statsmodels.tsa.vector_ar.var_model import VAR

sys.path.insert(0, str(Path(__file__).resolve().parent))
import spec  # noqa: E402

RUNS_DIR = Path("experiments/runs")
LOG_PATH = Path("experiments/LOG.md")
SPEC_PATH = Path("experiments/spec.py")
SPECIFICATION_PATH = Path("docs/SPECIFICATION.md")

TEST_FRACTION = 0.20
LJUNGBOX_LAGS = 10
ALPHA = 0.05
MAX_RUNS = 50
MAX_NONIMPROVING = 3


def spec_hash() -> str:
    return hashlib.sha256(SPEC_PATH.read_bytes()).hexdigest()


def split_index(n: int) -> int:
    """Row index where the held-out tail begins. Training is the first 80 percent."""
    return int(n * (1 - TEST_FRACTION))


def oos_one_step_rmse(panel, lag_order: int) -> float:
    """Standardized one-step out-of-sample RMSE on the held-out tail.

    Fit the VAR on the training rows, then roll one-step forecasts across the tail
    with fixed coefficients and the realized history. Errors are divided by the
    training standard deviation per variable, so the metric is scale-free.
    """
    values = panel.to_numpy()
    n = len(values)
    cut = split_index(n)
    train = values[:cut]
    results = VAR(train).fit(lag_order)
    scale = train.std(axis=0, ddof=1)

    squared = []
    for i in range(cut, n):
        history = values[:i][-lag_order:]
        forecast = results.forecast(history, steps=1)[0]
        squared.append(((values[i] - forecast) / scale) ** 2)
    return float(np.sqrt(np.mean(squared)))


def diagnostics(panel, lag_order: int) -> dict:
    """Ljung-Box whiteness, residual normality, and companion stability on training."""
    values = panel.to_numpy()
    cut = split_index(len(values))
    results = VAR(values[:cut]).fit(lag_order)
    whiteness = results.test_whiteness(nlags=lag_order + LJUNGBOX_LAGS, adjusted=True)
    normality = results.test_normality()
    moduli = np.abs(results.roots)
    return {
        "ljungbox_p": float(whiteness.pvalue),
        "normality_p": float(normality.pvalue),
        "companion_min_modulus": float(moduli.min()),
        "ljungbox_pass": bool(whiteness.pvalue > ALPHA),
        "normality_pass": bool(normality.pvalue > ALPHA),
        "stability_pass": bool(results.is_stable(verbose=False)),
        "bic": float(results.bic),
    }


def run_history() -> list[dict]:
    """Every recorded run, ordered by run id."""
    runs = [json.loads(p.read_text()) for p in RUNS_DIR.glob("run_*.json")]
    return sorted(runs, key=lambda r: r["run_id"])


def should_stop(history: list[dict]) -> bool:
    """Stop at MAX_RUNS or MAX_NONIMPROVING consecutive non-improving runs."""
    if len(history) >= MAX_RUNS:
        return True
    if len(history) < MAX_NONIMPROVING:
        return False
    tail = history[-MAX_NONIMPROVING:]
    return all(not run["improved"] for run in tail)


def evaluate() -> dict:
    """Evaluate the current spec, log the run, and return its record."""
    panel = spec.build_panel()
    config = spec.get_spec()
    lag_order = config["lag_order"]

    oos = oos_one_step_rmse(panel, lag_order)
    diag = diagnostics(panel, lag_order)
    # Keep gate: residual whiteness and companion stability. Daily returns are
    # leptokurtic, so residual normality is reported in full but does not gate the
    # keep decision. program.md names the Ljung-Box test as the disqualifier.
    diag_pass = diag["ljungbox_pass"] and diag["stability_pass"]

    history = run_history()
    prior_best = min((r["oos_metric"] for r in history), default=float("inf"))
    improved = oos < prior_best
    kept = improved and diag_pass

    run_id = (history[-1]["run_id"] + 1) if history else 1
    record = {
        "run_id": run_id,
        "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
        "spec_hash": spec_hash(),
        "spec": config,
        "oos_metric": oos,
        "bic": diag["bic"],
        "diagnostics": {
            "ljungbox_p": diag["ljungbox_p"],
            "normality_p": diag["normality_p"],
            "companion_min_modulus": diag["companion_min_modulus"],
            "ljungbox_pass": diag["ljungbox_pass"],
            "normality_pass": diag["normality_pass"],
            "stability_pass": diag["stability_pass"],
        },
        "improved": improved,
        "kept": kept,
    }

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    (RUNS_DIR / f"run_{run_id:03d}.json").write_text(json.dumps(record, indent=2) + "\n")
    _append_log(record, config)
    return record


def _append_log(record: dict, config: dict) -> None:
    diag = record["diagnostics"]
    passes = "pass" if (diag["ljungbox_pass"] and diag["stability_pass"]) else "fail"
    note = (
        f"vars={len(config['variables'])} lag={config['lag_order']} "
        f"window={config['sample_window'][0]}:{config['sample_window'][1]}"
    )
    line = (
        f"\n### Run {record['run_id']}\n\n"
        f"- Timestamp: {record['timestamp']}\n"
        f"- Spec hash: {record['spec_hash']}\n"
        f"- Out-of-sample metric: {record['oos_metric']:.6f}\n"
        f"- BIC: {record['bic']:.4f}\n"
        f"- Diagnostics: Ljung-Box p={diag['ljungbox_p']:.4f}, "
        f"normality p={diag['normality_p']:.4f}, "
        f"companion min modulus={diag['companion_min_modulus']:.4f} ({passes})\n"
        f"- Decision: {'kept' if record['kept'] else 'discarded'}\n"
        f"- Note: {note}\n"
    )
    with LOG_PATH.open("a") as handle:
        handle.write(line)


def _fmt(value: float, places: int = 4) -> str:
    return f"{value:.{places}f}"


def write_specification() -> str:
    """Re-estimate the current spec on the full sample and write docs/SPECIFICATION.md."""
    panel = spec.build_panel()
    config = spec.get_spec()
    lag_order = config["lag_order"]
    results = VAR(panel.to_numpy()).fit(lag_order)

    whiteness = results.test_whiteness(nlags=lag_order + LJUNGBOX_LAGS, adjusted=True)
    normality = results.test_normality()
    moduli = np.abs(results.roots)
    history = run_history()
    total_runs = len(history)

    lines: list[str] = []
    lines.append("# Final specification")
    lines.append("")
    lines.append(
        "Selected by the Karpathy Loop on out-of-sample one-step forecast error, then "
        "re-estimated once on the full sample. The transformation is a first difference "
        "and the model is a VAR in log returns, since D2 Johansen returned cointegration "
        "rank 0 on the level set."
    )
    lines.append("")
    lines.append("## Selected knobs")
    lines.append("")
    lines.append(f"- Variables: {', '.join(config['variables'])}")
    lines.append(f"- Transform: {config['transform']}")
    lines.append(f"- Lag order: {config['lag_order']}")
    lines.append(f"- Cholesky ordering: {', '.join(config['ordering'])}")
    lines.append(f"- Sample window: {config['sample_window'][0]} to {config['sample_window'][1]}")
    lines.append(f"- Observations after differencing: {int(results.nobs)}")
    lines.append("")
    lines.append("## Full-sample diagnostics")
    lines.append("")
    lines.append("| diagnostic | statistic | p-value | pass |")
    lines.append("|---|---|---|---|")
    lines.append(
        f"| Ljung-Box whiteness (portmanteau, {lag_order + LJUNGBOX_LAGS} lags) | "
        f"{_fmt(float(whiteness.test_statistic))} | {_fmt(float(whiteness.pvalue))} | "
        f"{'yes' if whiteness.pvalue > ALPHA else 'no'} |"
    )
    lines.append(
        f"| Residual normality (Jarque-Bera) | {_fmt(float(normality.test_statistic))} | "
        f"{_fmt(float(normality.pvalue))} | {'yes' if normality.pvalue > ALPHA else 'no'} |"
    )
    lines.append(
        f"| Companion stability (min characteristic-root modulus) | "
        f"{_fmt(float(moduli.min()))} | n/a | "
        f"{'yes' if results.is_stable(verbose=False) else 'no'} |"
    )
    lines.append("")
    lines.append(
        "Characteristic-root moduli are stable when every value exceeds 1. "
        "The reported minimum modulus is the binding one."
    )
    lines.append("")
    lines.append("## Run count")
    lines.append("")
    lines.append(
        f"Total specification runs logged: {total_runs}. Reported p-values are read "
        "against that count."
    )
    lines.append("")
    lines.append("## Findings")
    lines.append("")
    lines.append(
        f"1. The selected VAR uses {len(config['variables'])} variables at lag "
        f"{config['lag_order']} in log returns, re-estimated on {int(results.nobs)} "
        "observations."
    )
    lines.append(
        f"2. Ljung-Box whiteness p={_fmt(float(whiteness.pvalue))}, residual normality "
        f"p={_fmt(float(normality.pvalue))}, minimum characteristic-root modulus "
        f"{_fmt(float(moduli.min()))}."
    )
    lines.append(f"3. Selection ran over {total_runs} logged specification runs.")
    lines.append("")

    text = "\n".join(lines)
    SPECIFICATION_PATH.parent.mkdir(parents=True, exist_ok=True)
    SPECIFICATION_PATH.write_text(text)
    return text


def main() -> None:
    if "--final" in sys.argv[1:]:
        write_specification()
        print(f"wrote {SPECIFICATION_PATH.as_posix()}")
        return
    record = evaluate()
    history = run_history()
    print(
        f"run {record['run_id']}: oos={record['oos_metric']:.6f} bic={record['bic']:.4f} "
        f"{'kept' if record['kept'] else 'discarded'}"
    )
    if should_stop(history):
        print(f"stop condition met after {len(history)} runs")


if __name__ == "__main__":
    main()
