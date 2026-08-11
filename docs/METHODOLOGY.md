# Methodology

## Research question

This study measures how Indonesian financial variables respond following a shock to the crude oil
price, and over what horizon. The response chain under test runs from Brent crude to the US dollar
index to IDR/USD to Jakarta Composite (JKSE) sector returns to consumer price inflation (CPI).

Results are framed as conditional associations. The design does not identify a causal effect. Read
every reported coefficient as an association conditional on the specification and the ordering, not
as an isolated causal quantity.

The question set is organized in four tiers: confirmatory, descriptive, magnitude, and exploratory.

### Tier 1: confirmatory

Fixed before estimation. No re-specification permitted.

- H1: a positive Brent shock is followed by IDR depreciation within 10 trading days.
- H2: JKSE energy sector returns respond in the opposite sign to JKSE consumer sector returns
  following a Brent shock.
- H3: the CPI response to a Brent shock is detectable at monthly frequency with a lag of 1 to 3
  months.

Any additional relationship found during estimation is exploratory and is labeled as exploratory in
the writeup.

#### Falsification condition

If the H1 impulse response confidence bands include zero at every horizon from 1 to 20 days, record
H1 as unsupported and publish that result. Do not re-specify the model to produce a significant band.

### Tier 2: descriptive

No hypothesis attached. Answered by the stationarity and alignment work.

- D1 Integration order of each series in levels and first differences, by ADF and KPSS.
- D2 Cointegration of the level series, and the rank.
- D3 Unconditional correlation of Brent returns and IDR/USD returns, full sample.
- D4 Stability of that correlation across the 2020, 2022, and 2026 subsamples.
- D5 Structural break in the IDR equation at the April 2026 effective date of Bank Indonesia's
  anti-speculation measures. Chow test at the known date, Bai-Perron for unknown dates. Record this
  as pre-specified, since the break date is known in advance and a break test added after inspecting
  residuals carries different inferential weight.
- D6 Trading days lost to calendar mismatch across IDX, NYSE, and FX, and the share of the sample
  covered by the union spine.

### Tier 3: magnitude

Answered by estimation.

- M1 IDR/USD response to a one-standard-deviation Brent shock, and the peak horizon.
- M2 Share of IDR forecast error variance explained by Brent at horizons 1, 5, 10, 20.
- M3 Sign and size of the JKSE energy minus consumer sector return spread following a Brent shock.
- M4 Lag in months before a detectable CPI response, and magnitude per 10 percent Brent move.

### Tier 4: exploratory

Anything found during estimation that is not listed above. Label it exploratory wherever reported.

## Data sources

All sources are free. No paid tier. No credit card. Sources requiring a key use a free key.

| Series | Source | Access | Key required | Frequency | URL |
|---|---|---|---|---|---|
| Brent spot | FRED `DCOILBRENTEU` | `fredapi` | Free key | Daily | https://fred.stlouisfed.org/series/DCOILBRENTEU |
| Brent futures | Yahoo `BZ=F` | `yfinance` | None | Daily | https://finance.yahoo.com/quote/BZ=F |
| Jakarta Composite | Yahoo `^JKSE` | `yfinance` | None | Daily | https://finance.yahoo.com/quote/%5EJKSE |
| IDR/USD | Yahoo `IDR=X` | `yfinance` | None | Daily | https://finance.yahoo.com/quote/IDR=X |
| Dollar index | Yahoo `DX-Y.NYB` | `yfinance` | None | Daily | https://finance.yahoo.com/quote/DX-Y.NYB |
| Indonesian sector tickers | Yahoo, `.JK` suffix | `yfinance` | None | Daily | https://finance.yahoo.com |
| CPI Indonesia | BPS | WebAPI or table download | Free token | Monthly | https://www.bps.go.id |
| Trade balance | BPS | WebAPI or table download | Free token | Monthly | https://www.bps.go.id |
| BI policy rate, JISDOR | Bank Indonesia | Direct download | None | Meeting, daily | https://www.bi.go.id |

Rejected sources and reason: Alpha Vantage caps the free tier at a fixed daily call limit that is too
low for the series count. Nasdaq Data Link moved relevant series behind payment. Bloomberg and
Refinitiv require institutional licensing.

## Sample window

2019-01-01 to the build date, where the build date is the date the snapshots are retrieved. The
window covers the 2020 negative-price episode, the 2022 energy shock, and the 2026 Hormuz episode.

## Planned estimation approach

1. Stationarity: run ADF and KPSS on every series in levels and in first differences. Record the
   integration order per series in a committed table.
2. Cointegration: run the Johansen test on the level set. Choose a VAR in differences or a VECM in
   levels based on the result, and record the choice in the decision log.
3. Lag selection: select by AIC, BIC, and HQIC. Report all three.
4. Residual diagnostics: Ljung-Box, normality, and stability of the companion matrix.
5. Event study: define event dates for the Hormuz-related episodes with a documented selection rule.
   Estimate the market model, compute abnormal returns and cumulative abnormal returns per JKSE
   sector. Report the event count and its power implication.
6. Impulse responses: fit the VAR and produce orthogonalized impulse responses with bootstrap
   confidence bands, minimum 1000 replications. Run a Cholesky ordering sensitivity check with at
   least 2 alternative orderings.
7. Variance decomposition: forecast error variance decomposition at horizons 1, 5, 10, and 20.
8. Precedence tests: Granger causality tests, reported with the precedence-not-causation caveat.
9. CPI leg: ARDL or MIDAS at monthly frequency. Do not forward-fill monthly CPI to daily frequency.

## Scope exclusions

- Price forecasting as a product.
- Neural network models.
- Intraday data.
- Trading signals or position sizing.
- Any output framed as investment advice.

Deliberate omissions that require sources not ingested, planned as a v2.0 extension:

- Oil import volumes.
- Fuel subsidy expenditure.
- Pass-through to retail Pertamina prices.

## Results

Not yet populated. The integration-order table, event-study cumulative abnormal returns, impulse
responses, variance decompositions, and the numbered Findings block are added after estimation. Each
reported result carries a point estimate, an interval, and a horizon.
