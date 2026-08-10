# Decision log

## Format

Append-only. Add each new decision at the bottom. Do not edit or delete a recorded entry. To reverse
a decision, add a later entry that references and supersedes it. Each entry uses four fields:

- Date: ISO 8601, YYYY-MM-DD.
- Decision: the choice made, stated as one resolved position.
- Alternatives considered: the options rejected.
- Rationale: why the decision holds.

## Entries

### 2026-08-10: Python 3.11 as the interpreter version

- Decision: pin the project to Python 3.11.
- Alternatives considered: Python 3.12, Python 3.13.
- Rationale: 3.11 has wheel coverage for pandas, numpy, statsmodels, arch, and pyarrow at project
  start. Pinning the interpreter removes version drift between contributor machines and the
  deployment target.

### 2026-08-10: uv for environment and lockfile

- Decision: use uv for dependency resolution, the virtual environment, and the lockfile.
- Alternatives considered: pip with a requirements file, poetry, conda.
- Rationale: uv produces a cross-platform lockfile and resolves faster than the alternatives. A
  committed lockfile lets a clone reproduce the environment.

### 2026-08-10: statsmodels over a deep learning stack

- Decision: use statsmodels for estimation. Do not add torch or tensorflow.
- Alternatives considered: a neural network forecasting stack.
- Rationale: the study estimates interpretable econometric models with reported confidence intervals
  and residual diagnostics. A deep learning stack adds dependency weight and reduces interpretability
  with no benefit to the confirmatory design. Adding a deep learning dependency later requires its
  own entry in this log.

### 2026-08-10: parquet snapshots over live fetching

- Decision: persist every fetched series as an immutable parquet snapshot under `data/raw`, then read
  from the snapshot on later runs.
- Alternatives considered: fetch every series live on each run.
- Rationale: source tables and tickers change between releases. A committed manifest of snapshot
  hashes makes a rebuild verifiable. Live fetching makes results non-reproducible and depends on
  source uptime.

### 2026-08-10: free-tier data sources only

- Decision: restrict data sources to free access, with no paid tier and no credit card requirement.
- Alternatives considered: Alpha Vantage paid tier, Nasdaq Data Link, Bloomberg, Refinitiv.
- Rationale: the project targets reproduction by any reader. Alpha Vantage caps the free tier at 25
  calls per day `[Alpha Vantage free tier, 2026-08-10]`, Nasdaq Data Link moved relevant series
  behind payment, and Bloomberg and Refinitiv require institutional licensing.
