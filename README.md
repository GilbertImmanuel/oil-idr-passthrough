# oil-idr-passthrough

Measure how a crude oil price shock propagates to Indonesian financial variables, and over what
horizon, along the chain Brent crude to the US dollar index to IDR/USD to Jakarta Composite (JKSE)
sector returns to consumer price inflation (CPI). Results are conditional correlations, not causal
effects.

Live dashboard: https://oil-idr-passthrough.streamlit.app/

## Research question

Estimate the response of Indonesian financial variables following a shock to the Brent crude price,
and the horizon over which it appears. The question set is organized in four tiers.

- Confirmatory (fixed before estimation, no re-specification):
  - H1: a positive Brent shock is followed by IDR depreciation within 10 trading days.
  - H2: JKSE energy sector returns respond in the opposite sign to JKSE consumer sector returns
    following a Brent shock.
  - H3: the CPI response to a Brent shock is detectable at monthly frequency with a lag of 1 to 3
    months.
- Descriptive (D1 to D6): integration order, cointegration, the Brent-IDR return correlation and its
  subsample stability, a pre-specified structural break in the IDR equation, and the trading days
  lost to calendar mismatch.
- Magnitude (M1 to M4): the IDR response size and peak horizon, the Brent share of IDR forecast
  error variance, the energy-minus-consumer sector spread, and the CPI lag and magnitude.
- Exploratory: anything found during estimation that is not listed above, labeled exploratory
  wherever reported.

The design does not identify a causal effect. Read every reported coefficient as an association
conditional on the specification and the ordering. Full detail: docs/METHODOLOGY.md.

## Data sources

All sources are free. No paid tier. No credit card. Sources requiring a key use a free key.
data/MANIFEST.json records the source, retrieval date, first and last date, row count, and sha256 of
every snapshot, so a clone verifies a rebuild against the recorded hashes.

| Series | Source | Access | Key required | Frequency |
|---|---|---|---|---|
| Brent spot | FRED `DCOILBRENTEU` | `fredapi` | Free key | Daily |
| Brent futures | Yahoo `BZ=F` | `yfinance` | None | Daily |
| Jakarta Composite | Yahoo `^JKSE` | `yfinance` | None | Daily |
| IDR/USD | Yahoo `IDR=X` | `yfinance` | None | Daily |
| Dollar index | Yahoo `DX-Y.NYB` | `yfinance` | None | Daily |
| Indonesian sector tickers | Yahoo, `.JK` suffix | `yfinance` | None | Daily |
| CPI Indonesia | BPS | WebAPI or table download | Free token | Monthly |
| Trade balance | BPS | WebAPI or table download | Free token | Monthly |
| BI policy rate, JISDOR | Bank Indonesia | Direct download | None | Meeting, daily |

Snapshots carry a STYLE source tag, for example [FRED:DCOILBRENTEU, 2026-08-10] and
[Yahoo:^JKSE, 2026-08-10]. Rejected sources: Alpha Vantage caps the free tier at a daily call limit
too low for the series count, Nasdaq Data Link moved relevant series behind payment, and Bloomberg
and Refinitiv require institutional licensing.

## Method

- Panel: build the daily estimation panel on the intersection of the observed trading dates across
  all daily series, so no imputed or forward-filled price enters (docs/DECISIONS.md 2026-08-11).
- VAR: estimate a 4-variable VAR (DCOILBRENTEU, DX-Y.NYB, IDR=X, ^JKSE) in first differences at lag
  2, since D2 Johansen returned cointegration rank 0 on the level set. Produce orthogonalized impulse
  responses with a residual bootstrap, 1000 replications, 90 percent percentile band, under a
  recursive Cholesky identification with two alternative orderings for the sensitivity check.
- Event study: estimate a market model per JKSE sector ticker on 11 Hormuz events fixed by a written
  selection rule (data/sources/events/), and compute cumulative abnormal returns for the energy and
  consumer portfolios.
- CPI leg: estimate an ARDL(1, 3) in log differences of the monthly CPI index on the monthly Brent
  return and its lags, by ordinary least squares with Newey-West standard errors. Do not forward-fill
  monthly CPI to daily frequency.

The specification was selected by an out-of-sample forecast-error loop over 5 logged runs, then
re-estimated once on the full sample. Full specification, Cholesky ordering justification, and
diagnostics: docs/METHODOLOGY.md. Descriptive results: docs/DESCRIPTIVES.md. Estimation results:
docs/ESTIMATION.md.

## Findings

Each result carries a point estimate, an interval where one applies, and a horizon. Every number is
drawn from the committed result docs.

1. Event study over 11 Hormuz events: energy CAAR 0.007252, consumer CAAR -0.006070, energy-minus-
   consumer spread 0.013322, cross-event t=1.04, n=11. At n=11 the cross-event test carries low
   power, so the event study is a supporting result [docs/ESTIMATION.md, 2026-08-12].
2. M1, IDR=X response to a one-standard-deviation Brent shock: peak absolute response -0.000312 at
   trading-day horizon 1, 90 percent band [-0.000604, 0.000005], in log-return units; cumulative
   level response at horizon 20 is -0.000357. IDR=X is IDR per USD, so a positive value is a
   depreciation [docs/ESTIMATION.md, 2026-08-12].
3. M2, Brent share of IDR=X forecast error variance: 0.000029 at horizon 1, 0.002292 at horizon 5,
   0.002293 at horizons 10 and 20 [docs/ESTIMATION.md, 2026-08-12].
4. M3, JKSE energy-minus-consumer spread following a Brent shock: event-study CAAR 0.013322 over the
   5-day window, cross-event SE 0.012841, t=1.04, n=11 [docs/ESTIMATION.md, 2026-08-12].
5. M4, CPI leg ARDL(1, 3) selected over 6 logged runs: no Brent lag from 0 to 3 months has a 90
   percent coefficient interval excluding zero [docs/ESTIMATION.md, 2026-08-12].
6. Confirmatory verdicts: H1 falsified under the pre-registered condition, since the 90 percent IRF
   bands include zero at every horizon 1 to 20 and the peak sign is opposite to the predicted
   depreciation; H2 sign-consistent (energy CAAR positive, consumer CAAR negative) but low power at
   n=11; H3 unsupported, no detectable CPI lag from 1 to 3 months [docs/ESTIMATION.md, 2026-08-12].

## Limitations

- Event count. The Hormuz event study holds 11 events (docs/ESTIMATION.md). At n=11 the cross-event
  test carries low power, and the 2019 events and the 2026 closure-episode events cluster, so their
  windows overlap and the events are not independent. The event study is reported as a supporting
  result, not the headline (PROJECT_PLAN section 10).
- Identification. Identification is recursive (a Cholesky ordering), so every impulse response is a
  conditional correlation, not a causal effect. Oil, the dollar, and risk sentiment move together
  contemporaneously (PROJECT_PLAN section 10). The unconditional Brent-IDR return correlation is
  0.0089, n=1749 [docs/DESCRIPTIVES.md D3, 2026-08-11], and it is sign-unstable across the 2020,
  2022, and 2026 subsamples [docs/DESCRIPTIVES.md D4, 2026-08-11], so a near-zero conditional
  response is the expected reading.
- Confirmatory versus exploratory. H1 to H3 are fixed before estimation with no re-specification.
  Any additional relationship found during estimation is labeled exploratory wherever reported. H1
  met its pre-registered falsification condition and is published as unsupported, not re-specified to
  produce a significant band.
- Residual whiteness. The selected VAR fails the Ljung-Box portmanteau whiteness test at p=0.0000
  [docs/SPECIFICATION.md, 2026-08-12]. No loop run met the whiteness keep gate, so selection fell to
  the out-of-sample metric with the failure disclosed. Read the impulse-response bands against that
  failure.

## Reproduction

The pipeline uses uv (PROJECT_PLAN section 5). The environment is pinned by uv.lock and .python-version
(Python 3.11). Run every command from the repository root. data/raw, data/interim, and data/processed
snapshots are gitignored except the committed model-ready parquet the dashboard reads.

1. Set up the environment:
   ```bash
   uv sync
   ```
2. Provide credentials for ingestion. Copy .env.example to .env and set `FRED_API_KEY`. Place the BPS
   CPI snapshot at data/raw/snapshots/ per data/sources/cpi/. Yahoo series need no key.
3. Ingest the raw snapshots (writes data/raw, records data/MANIFEST.json):
   ```bash
   PYTHONPATH=src uv run python -c "from ingest.yahoo import fetch_all; fetch_all()"
   PYTHONPATH=src uv run python -c "from ingest.fred import fetch; fetch()"
   ```
4. Build the aligned panels (writes data/interim):
   ```bash
   PYTHONPATH=src uv run python -m align.panel
   ```
5. Run the descriptive and estimation builders (writes docs/DESCRIPTIVES.md, docs/SPECIFICATION.md,
   docs/ESTIMATION.md):
   ```bash
   PYTHONPATH=src uv run python -m models.descriptive
   PYTHONPATH=src:experiments uv run python -m models.estimation
   PYTHONPATH=src uv run python -m models.event_study
   ```
6. Build the model-ready parquet the dashboard reads (writes data/processed):
   ```bash
   uv run python app/build_processed.py
   ```
7. Run the tests:
   ```bash
   uv run pytest -q
   ```
8. Run the dashboard:
   ```bash
   uv run streamlit run app/streamlit_app.py
   ```

The dashboard reads the committed data/processed parquet and makes no network call at runtime
(docs/DECISIONS.md 2026-08-13), so a clone runs step 8 without repeating steps 2 to 6.

## Repository layout

- `src/ingest`, `src/align`, `src/models`: ingestion, calendar alignment, and estimation.
- `experiments/`: the specification loop (spec.py, run_loop.py, cpi_loop.py) and the append-only
  run log (LOG.md).
- `app/`: the Streamlit dashboard and the data/processed build step.
- `docs/`: METHODOLOGY.md, DESCRIPTIVES.md, SPECIFICATION.md, ESTIMATION.md, DECISIONS.md, STYLE.md.
- `data/MANIFEST.json`: the committed snapshot manifest.
- `tests/`: ingestion, alignment, model, and dashboard tests.
