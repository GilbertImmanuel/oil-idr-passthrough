"""VAR specification for the Karpathy Loop. The loop edits only this file.

The knobs below define the specification: the endogenous variable set, the
transformation, the lag order, the Cholesky ordering, and the sample window.
experiments/run_loop.py reads this file, estimates the model, and logs the run.
The loop tunes these knobs. It does not touch src/, data/, or the log harness.

Guardrail H1: Brent and IDR per USD are fixed members of the variable set and are
never removed. D2 Johansen returned cointegration rank 0 on the level set, so the
transformation is a first difference (log returns) and the model is a VAR in
differences. VECM in levels is not instantiated because rank 0 rules it out.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

RETURNS_PATH = Path("data/interim/daily_returns.parquet")

# Fixed members. The variable of interest is the Brent to IDR link (H1).
FIXED = ["DCOILBRENTEU", "IDR=X"]

# Endogenous variable set. Loop-editable, but FIXED must stay in it.
VARIABLES = ["DCOILBRENTEU", "DX-Y.NYB", "IDR=X", "^JKSE"]

# Transformation. "diff" reads the log-return panel. VECM in levels is out because
# D2 rank is 0.
TRANSFORM = "diff"

# VAR lag order in the transformed series. Loop-editable.
LAG_ORDER = 2

# Cholesky ordering for later IRF identification. Recorded here, not used by the
# forecast metric. Brent first, IDR last follows the passthrough chain.
ORDERING = ["DCOILBRENTEU", "DX-Y.NYB", "^JKSE", "IDR=X"]

# Sample window, inclusive. Loop-editable.
SAMPLE_WINDOW = ("2019-01-01", "2026-12-31")


def get_spec() -> dict:
    """Return the resolved specification as a plain dict."""
    return {
        "variables": list(VARIABLES),
        "transform": TRANSFORM,
        "lag_order": LAG_ORDER,
        "ordering": list(ORDERING),
        "sample_window": list(SAMPLE_WINDOW),
    }


def build_panel() -> pd.DataFrame:
    """Return the model-ready panel for the current spec.

    Reads the log-return panel, restricts to VARIABLES and SAMPLE_WINDOW, and drops
    any row with a missing value. Asserts the FIXED members are present.
    """
    assert TRANSFORM == "diff", f"only the diff transform is supported, got {TRANSFORM!r}"
    for member in FIXED:
        assert member in VARIABLES, f"fixed member {member} missing from VARIABLES"
    frame = pd.read_parquet(RETURNS_PATH)[VARIABLES]
    start, end = SAMPLE_WINDOW
    frame = frame.loc[start:end].dropna(how="any")
    return frame
