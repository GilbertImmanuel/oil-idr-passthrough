# Experiment loop program

## Source of the pattern

The loop follows the automated research pattern at https://github.com/karpathy/autoresearch. The
mapping below adapts that pattern to an econometric specification search. The loop applies to the
stationarity-and-specification stage and the estimation stage. It does not run during ingestion or
alignment.

## Files and roles

- `experiments/spec.py`: the only file the loop edits. It holds the specification: variable set,
  transformation, lag order, ordering, and sample window.
- `src/` and `data/`: fixed during a loop. The loop does not modify ingestion or alignment code, and
  does not modify any snapshot.
- `experiments/program.md`: this file. Human-edited. It defines the metric, the budget, and the
  keep-or-discard rule.
- `experiments/LOG.md`: append-only. One entry per run, including discarded runs.

## Loop mechanics

- Budget: a fixed wall-clock limit of 90 seconds per run. Estimation on this data size completes
  inside that limit.
- Metric: out-of-sample one-step forecast error on the held-out final 20 percent of the sample,
  reported together with BIC on the training portion. Report both values. Selection uses the
  out-of-sample value.
- Keep or discard: keep a run if the out-of-sample metric improves and residual diagnostics still
  pass. Discard otherwise. A specification that improves fit and fails the Ljung-Box test is
  discarded.
- Every run appends one entry to `experiments/LOG.md` regardless of outcome.

## Guardrails

1. The confirmatory hypotheses are fixed before the loop starts. The loop tunes the specification.
   The loop does not select the hypothesis.
2. Selection runs on out-of-sample error, never on the p-value or the coefficient sign of the
   variable of interest. Selecting on significance is specification mining and invalidates the
   reported inference.
3. The total run count is logged and reported in the repository writeup. Reported p-values are
   interpreted against that count.
4. The loop stops at 50 runs or at 3 consecutive non-improving runs, whichever comes first.
5. The final reported model is re-estimated once on the full sample, and its diagnostics are reported
   in full.

## Why the guardrails exist

An econometric specification search differs from a language-model training loop in one respect that
matters for inference. Lower validation loss on a language model is the goal itself. Lower forecast
error on a macro panel is a proxy. Searching hard against a proxy produces overfitted specifications
that still look defensible, and the risk grows as the number of independent events falls, because a
single event then shifts the metric. Guardrails 1 through 3 constrain that failure mode.
