# Run log

## Format

Append-only. Add each run at the bottom. Do not edit or delete a recorded run. One entry per run,
including discarded runs. Each entry records:

- Run id: monotonic integer, starting at 1.
- Timestamp: ISO 8601 with timezone.
- Spec hash: sha256 of `experiments/spec.py` at run time.
- Out-of-sample metric: one-step forecast error on the held-out final 20 percent.
- BIC: on the training portion.
- Diagnostics: pass or fail for Ljung-Box, normality, and companion-matrix stability.
- Decision: kept or discarded.
- Note: one line on what changed relative to the previous run.

## Entries

No runs recorded yet.
