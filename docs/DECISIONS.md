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

### 2026-08-10: adjusted close as the daily price value

- Decision: use the yfinance auto-adjusted close as the single daily value per price series.
- Alternatives considered: raw close, open, a volume-weighted average.
- Rationale: the adjusted close accounts for splits and dividends and is the standard input for
  log-return computation.

### 2026-08-10: JKSE sector composition for the return contrast

- Decision: define the energy sector as MEDC.JK, PGAS.JK, ADRO.JK, ITMG.JK, PTBA.JK, and the
  consumer sector as UNVR.JK, ICBP.JK, INDF.JK, MYOR.JK, GGRM.JK.
- Alternatives considered: an IDX sector index ticker, a wider constituent set, a free-float-weighted
  basket.
- Rationale: these are liquid large-cap constituents with continuous history across the sample
  window. Membership is fixed here so the sector contrast in H2 is defined before estimation. Change
  membership through a later entry, not by a silent edit.

### 2026-08-10: BPS and BI ingested from pinned snapshots

- Decision: ingest BPS CPI and trade balance, and Bank Indonesia policy rate and JISDOR, from
  downloaded snapshot files parsed to parquet. Do not couple the build to the live endpoints.
- Alternatives considered: the BPS WebAPI dynamic-data endpoint, and scraping the Bank Indonesia
  table pages.
- Rationale: the BPS consumer price index is published per city, with no single national series at
  the WebAPI national domain, and the WebAPI data model takes per-domain and per-year parameters that
  change between releases. A pinned snapshot with its sha256 and retrieval date recorded in the
  manifest makes a rebuild verifiable. The BPS variable ids are 2 for the consumer price index and
  498 for the trade balance value `[BPS WebAPI, 2026-08-10]`.

### 2026-08-11: research question organized into tiers, D5 pre-specified

- Decision: organize the research question into four tiers. Tier 1 confirmatory holds H1 to H3,
  fixed before estimation with no re-specification. Tier 2 descriptive holds D1 to D6. Tier 3
  magnitude holds M1 to M4. Tier 4 exploratory holds anything found during estimation, labeled
  exploratory wherever reported. Record D5, the structural break in the IDR equation at the April
  2026 Bank Indonesia anti-speculation effective date, as pre-specified before estimation.
- Alternatives considered: a single flat hypothesis list; adding the break test after inspecting
  residuals.
- Rationale: tiering separates fixed confirmatory claims from descriptive and magnitude questions,
  which keeps the confirmatory set small and the exploratory results labeled. Pre-specifying D5
  fixes the break date in advance, since a break test added after inspecting residuals carries
  different inferential weight.

### 2026-08-11: intersection spine for the daily panel, union stored alongside

- Decision: build the daily estimation panel on the intersection of the observed
  trading dates across all daily series. Keep the union frame, with NaN on days a
  market was closed and no forward-fill, alongside the intersection frame for
  reference and robustness checks. Derive each series calendar from its own
  observed dates rather than a holiday table.
- Alternatives considered: a single named market calendar as the spine (IDX, FX,
  or NYSE); a union panel forward-filled to a common daily grid; a market-calendar
  dependency for the holiday sets.
- Rationale: the intersection admits only dates on which every series traded, so
  the estimation frame carries no imputed price and no forward-filled value on a
  closed day. Empirical calendars avoid a hardcoded holiday table and an added
  dependency, both of which drift between releases. The union frame retains the
  dropped dates so the row loss is measurable (D6) and available for a robustness
  comparison.

### 2026-08-11: monthly mean as the primary daily-to-monthly aggregation

- Decision: aggregate the daily series to monthly by the calendar-month mean for
  the CPI-leg panel. Produce the month-end last observation as a second variant
  for a robustness check. Do not forward-fill monthly CPI to daily frequency.
- Alternatives considered: month-end last observation as the primary aggregation;
  forward-filling CPI to daily to force a single-frequency daily VAR.
- Rationale: the monthly mean uses every observed trading day in the month rather
  than one end-of-month print, which reduces sensitivity to the final day value.
  The month-end variant is retained so the aggregation choice can be tested.
  Forward-filling CPI to daily is prohibited by the alignment plan because it
  fabricates daily variation the source does not report.

### 2026-08-11: Phase 3 run on daily series, CPI leg deferred

- Decision: run Phase 3 on the daily series only. Defer the BPS CPI leg and the
  monthly panels until the snapshot is provided.
- Alternatives considered: block Phase 3 until the snapshot arrives; interpolate or
  fabricate CPI values to proceed.
- Rationale: the snapshot data/raw/snapshots/bps_cpi.csv is absent, and CPI is not
  fabricated. D1 to D5 and the VAR specification are daily-based and complete without
  CPI. The monthly panel and the CPI response questions H3 and M4 move to Phase 4,
  pending the snapshot. The BPS ingest module and align.panel already skip the CPI
  leg when the snapshot is missing, so no code path fabricates a value.

### 2026-08-11: supF single-break for the D5 unknown-date test

- Decision: test the unknown break date in D5 with a supF, or Quandt-Andrews,
  single-break search over the interior 15 percent-trimmed sample, by ordinary least
  squares on the IDR return equation.
- Alternatives considered: full Bai-Perron multiple-break estimation via the ruptures
  package; an untrimmed grid.
- Rationale: statsmodels 0.14.6 has no Bai-Perron routine and ruptures is not a
  project dependency. The supF single-break test covers the unknown-date case with the
  standard 15 percent trim and adds no dependency. The supF reference distribution is
  non-standard, so the argmax date is reported without a pointwise p-value. Add
  ruptures and multiple-break estimation through a later entry if more than one break
  is required.

### 2026-08-11: VAR in differences from the D2 rank

- Decision: estimate a VAR in first differences of the log price series. Set the
  specification transformation to diff. Do not estimate a VECM in levels.
- Alternatives considered: a VECM in levels with a cointegrating rank.
- Rationale: D2 Johansen on the level set (DCOILBRENTEU, DX-Y.NYB, IDR=X, ^JKSE)
  returned cointegration rank 0 by both the trace and maximum-eigenvalue statistics at
  5 percent, n=1750. Rank 0 leaves no cointegrating relation to embed, so a VECM
  reduces to a VAR in differences. The level set is the macro passthrough chain; the
  ten sector tickers feed the H2 sector spread and are not part of the cointegration
  system.

### 2026-08-11: loop keep gate on whiteness and stability, normality reported only

- Decision: gate the loop keep decision on residual whiteness by the Ljung-Box
  portmanteau test and on companion-matrix stability. Report residual normality in
  full, but do not gate on it.
- Alternatives considered: gate on all three diagnostics, including the Jarque-Bera
  normality test.
- Rationale: daily log returns are leptokurtic, so Jarque-Bera rejects normality for
  every specification, which would discard every run and make the out-of-sample
  selection vacuous. Non-normal residuals leave the VAR point estimates consistent and
  affect only exact small-sample inference. experiments/program.md names the Ljung-Box
  test as the disqualifier. The normality statistic and p-value are recorded per run
  and in the final report. On this sample the portmanteau rejected whiteness at every
  lag order searched, so no run was kept and selection fell to the out-of-sample metric
  with the whiteness failure disclosed in docs/SPECIFICATION.md.
