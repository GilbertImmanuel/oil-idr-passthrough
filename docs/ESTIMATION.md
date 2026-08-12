# Estimation results

Phase 4 estimation of the event study, the Phase 3 final VAR, and the CPI leg. Every result is a conditional correlation, not a causal effect. D3 reported the unconditional Brent-IDR return correlation at 0.0089 (n=1749) and D4 reported it sign-unstable across subsamples, so the identification assumption is stated and the responses are read as conditional associations. Series are retrieved per data/MANIFEST.json.

## Event study: Hormuz events and sector CAR

Market model per sector ticker on the Jakarta Composite [Yahoo:^JKSE, 2026-08-10] return, estimation window 120 trading days ending 6 days before t=0, post-event window [0, 5] trading days inclusive. Event dates and the selection rule: data/sources/events/. Sector membership is frozen in docs/DECISIONS.md 2026-08-10. Energy: MEDC.JK, PGAS.JK, ADRO.JK, ITMG.JK, PTBA.JK [Yahoo:MEDC.JK, 2026-08-10] [Yahoo:PGAS.JK, 2026-08-10] [Yahoo:ADRO.JK, 2026-08-10] [Yahoo:ITMG.JK, 2026-08-10] [Yahoo:PTBA.JK, 2026-08-10]. Consumer: UNVR.JK, ICBP.JK, INDF.JK, MYOR.JK, GGRM.JK [Yahoo:UNVR.JK, 2026-08-10] [Yahoo:ICBP.JK, 2026-08-10] [Yahoo:INDF.JK, 2026-08-10] [Yahoo:MYOR.JK, 2026-08-10] [Yahoo:GGRM.JK, 2026-08-10].

Events in the list: 11. Events with a full estimation and post-event window inside the daily panel: 11.

At n=11 the cross-event test carries low power (PROJECT_PLAN section 10). The 2019 events and the 2026 closure-episode events cluster, so their windows overlap and the events are not independent. The event study is a supporting result, not the headline.

| event | t=0 | energy CAR | consumer CAR | energy minus consumer |
|---|---|---|---|---|
| 2019-05-12 | 2019-05-13 | -0.0129 | 0.0214 | -0.0344 |
| 2019-06-13 | 2019-06-13 | -0.0054 | -0.0092 | 0.0038 |
| 2019-07-19 | 2019-07-19 | -0.0087 | 0.0208 | -0.0295 |
| 2019-09-14 | 2019-09-16 | 0.0316 | -0.0264 | 0.0580 |
| 2020-01-03 | 2020-01-03 | 0.0624 | 0.0299 | 0.0325 |
| 2024-04-13 | 2024-04-16 | 0.0334 | -0.0494 | 0.0828 |
| 2026-03-04 | 2026-03-04 | -0.0470 | -0.0406 | -0.0064 |
| 2026-04-19 | 2026-04-20 | 0.0049 | -0.0250 | 0.0299 |
| 2026-06-26 | 2026-06-26 | -0.0088 | 0.0062 | -0.0150 |
| 2026-07-07 | 2026-07-07 | 0.0496 | -0.0142 | 0.0638 |
| 2026-07-22 | 2026-07-22 | -0.0194 | 0.0196 | -0.0390 |

| portfolio | CAAR | cross-event SE | t | n |
|---|---|---|---|---|
| energy | 0.0073 | 0.0099 | 0.7302 | 11 |
| consumer | -0.0061 | 0.0083 | -0.7353 | 11 |
| energy minus consumer | 0.0133 | 0.0128 | 1.0375 | 11 |

## VAR impulse responses, FEVD, and Granger precedence

Phase 3 final VAR: 4 variables in first differences at lag 2, 1747 observations. Cholesky ordering DCOILBRENTEU, DX-Y.NYB, ^JKSE, IDR=X. Series: [FRED:DCOILBRENTEU, 2026-08-10] [Yahoo:DX-Y.NYB, 2026-08-10] [Yahoo:^JKSE, 2026-08-10] [Yahoo:IDR=X, 2026-08-10]. Orthogonalized responses use 1000 Monte Carlo bootstrap replications at the 90 percent band. Identification is recursive; the responses are conditional correlations, not causal effects. The SPECIFICATION.md portmanteau rejected residual whiteness at n=1747, so read the band inference against that and the 5 logged Phase 3 runs.

### IDR=X response to a one-standard-deviation Brent shock

IDR=X is IDR per USD, so a positive response is a rupiah depreciation. The impulse response is in log-return units per horizon; the cumulative response is the level response. The band is the 90 percent Monte Carlo band.

| horizon | impulse response | 90 band low | 90 band high | cumulative response |
|---|---|---|---|---|
| 1 | -0.000312 | -0.000604 | 0.000005 | -0.000344 |
| 2 | -0.000062 | -0.000315 | 0.000194 | -0.000406 |
| 3 | 0.000044 | -0.000090 | 0.000179 | -0.000361 |
| 5 | -0.000009 | -0.000039 | 0.000022 | -0.000357 |
| 10 | 0.000000 | -0.000000 | 0.000001 | -0.000357 |
| 20 | 0.000000 | -0.000000 | 0.000000 | -0.000357 |

Peak absolute response at horizon 1: -0.000312, 90 percent band [-0.000604, 0.000005].

### Cholesky ordering sensitivity

IDR=X response to a Brent shock at the peak horizon under the primary ordering and two alternatives, justification in docs/DECISIONS.md.

| ordering | peak horizon | peak response | 90 band low | 90 band high |
|---|---|---|---|---|
| primary: DCOILBRENTEU, DX-Y.NYB, ^JKSE, IDR=X | 1 | -0.000312 | -0.000604 | 0.000005 |
| reverse (IDR first): IDR=X, ^JKSE, DX-Y.NYB, DCOILBRENTEU | 1 | -0.000208 | -0.000433 | 0.000030 |
| dollar before Brent: DX-Y.NYB, DCOILBRENTEU, ^JKSE, IDR=X | 1 | -0.000310 | -0.000586 | -0.000009 |

### Forecast error variance decomposition of IDR=X

Share of IDR=X forecast error variance from each orthogonalized shock at the reported horizons, primary ordering.

| shock | h=1 | h=5 | h=10 | h=20 |
|---|---|---|---|---|
| DCOILBRENTEU | 0.000029 | 0.002292 | 0.002293 | 0.002293 |
| DX-Y.NYB | 0.001275 | 0.084587 | 0.084587 | 0.084587 |
| ^JKSE | 0.004633 | 0.020256 | 0.020288 | 0.020288 |
| IDR=X | 0.994064 | 0.892865 | 0.892832 | 0.892832 |

Brent share of IDR=X variance under the alternative orderings:

| ordering | h=1 | h=5 | h=10 | h=20 |
|---|---|---|---|---|
| primary | 0.000029 | 0.002292 | 0.002293 | 0.002293 |
| reverse (IDR first) | 0.000000 | 0.000983 | 0.000984 | 0.000984 |
| dollar before Brent | 0.000028 | 0.002256 | 0.002258 | 0.002258 |

### Granger precedence

F tests within the fitted VAR. A rejection is temporal precedence in the sense of Granger, not causation (STYLE rule 20).

| causing | caused | F | p-value |
|---|---|---|---|
| DCOILBRENTEU | IDR=X | 1.0684 | 0.3436 |
| IDR=X | DCOILBRENTEU | 1.0992 | 0.3332 |
| DCOILBRENTEU | ^JKSE | 2.6622 | 0.0699 |
| DCOILBRENTEU | DX-Y.NYB | 0.8724 | 0.4180 |

## CPI leg: ARDL on monthly inflation

ARDL(1, 3) in log differences: monthly inflation (log difference of the BPS CPI index [BPS:BPS_CPI, 2026-08-11]) on the monthly Brent return (log difference of the monthly-mean Brent price [FRED:DCOILBRENTEU, 2026-08-10]) and its lags. Selected on out-of-sample one-step forecast error over 6 logged CPI runs (experiments/LOG.md), re-estimated once on the full sample. Estimation is ordinary least squares on the lag matrix with Newey-West standard errors. MIDAS is not used; the choice is recorded in docs/DECISIONS.md.

CPI base-chaining caveat: level-matching forces a zero month-over-month change at 2020-01, 2024-01 (data/sources/cpi/README.md). Those two months are set to missing, so no estimation row uses them as the dependent or a lag.

Full-sample fit: n=83, R-squared 0.0241, residual Ljung-Box p=0.2297 (pass).

| Brent lag (months) | coefficient | 90 CI low | 90 CI high | detectable |
|---|---|---|---|---|
| 0 | -0.001275 | -0.004065 | 0.001515 | no |
| 1 | 0.002192 | -0.000733 | 0.005116 | no |
| 2 | -0.000360 | -0.004178 | 0.003459 | no |
| 3 | 0.002671 | -0.000646 | 0.005988 | no |

Robustness on monthly_panel_last (month-end value), same specification, n=83:

| Brent lag (months) | coefficient | 90 CI low | 90 CI high | detectable |
|---|---|---|---|---|
| 0 | -0.000664 | -0.002456 | 0.001128 | no |
| 1 | 0.000559 | -0.000772 | 0.001890 | no |
| 2 | 0.000601 | -0.001374 | 0.002577 | no |
| 3 | 0.000198 | -0.001962 | 0.002358 | no |

## Magnitudes M1 to M4

All magnitudes are conditional correlations. D3 found the unconditional Brent-IDR return correlation at 0.0089 and D4 found it sign-unstable across the 2020, 2022, and 2026 subsamples, so a near-zero conditional response is the expected reading.

- M1 IDR=X response to a one-standard-deviation Brent shock: peak absolute response -0.000312 at trading-day horizon 1, 90 percent band [-0.000604, 0.000005], in log-return units. Cumulative level response at horizon 20: -0.000357. IDR=X is IDR per USD, so a positive value is depreciation.
- M2 share of IDR=X forecast error variance from Brent: h=1 0.000029, h=5 0.002292, h=10 0.002293, h=20 0.002293.
- M3 JKSE energy-minus-consumer spread following a Brent shock: event-study CAAR 0.013322 over the five-day window, cross-event SE 0.012841, t=1.04, n=11 events. Daily Brent-beta cross-check: energy beta 0.1125 minus consumer beta 0.0089 equals 0.1036.
- M4 CPI response: no Brent lag from 0 to 3 months detectable at the 90 percent level. Magnitude per 10 percent Brent move (=0.0953 log points) by lag: lag 0 -0.000122, lag 1 0.000209, lag 2 -0.000034, lag 3 0.000255, in CPI log points.

## Confirmatory verdicts H1 to H3

- H1 (Brent shock followed by IDR depreciation within 10 days): unsupported. Under the primary ordering the 90 percent IRF bands include zero at every horizon 1 to 20, which meets the pre-registered falsification condition. The peak response is negative in sign, opposite to the predicted depreciation. Recorded as unsupported and published, per PROJECT_PLAN section 1. The model is not re-specified to produce a band.
- H2 (energy and consumer respond opposite in sign after a Brent shock): energy CAAR 0.007252, consumer CAAR -0.006070, opposite in sign. The spread is not detectable at n=11 events (t=1.04), so the sign is consistent with H2 while the test carries low power.
- H3 (CPI response detectable at a lag of 1 to 3 months): unsupported: no Brent lag from 1 to 3 months has a 90 percent coefficient interval excluding zero.

## Findings

1. Event study over 11 Hormuz events: energy CAAR 0.007252, consumer CAAR -0.006070, spread 0.013322 (t=1.04), low power at that count.
2. M1 IDR=X peak response to a one-SD Brent shock is -0.000312 at horizon 1, 90 percent band [-0.000604, 0.000005].
3. M2 Brent share of IDR=X forecast error variance stays at or below 0.002293 through horizon 20.
4. M4 CPI leg selects ARDL(1, 3) over 6 runs; no Brent lag 0 to 3 months is detectable at 90 percent.
5. Confirmatory verdicts: H1 falsified, H2 sign consistent but low power, H3 unsupported.
