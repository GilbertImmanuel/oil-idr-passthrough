# Final specification

Selected by the Karpathy Loop on out-of-sample one-step forecast error, then re-estimated once on the full sample. The transformation is a first difference and the model is a VAR in log returns, since D2 Johansen returned cointegration rank 0 on the level set.

## Selected knobs

- Variables: DCOILBRENTEU, DX-Y.NYB, IDR=X, ^JKSE
- Transform: diff
- Lag order: 2
- Cholesky ordering: DCOILBRENTEU, DX-Y.NYB, ^JKSE, IDR=X
- Sample window: 2019-01-01 to 2026-12-31
- Observations after differencing: 1747

## Full-sample diagnostics

| diagnostic | statistic | p-value | pass |
|---|---|---|---|
| Ljung-Box whiteness (portmanteau, 12 lags) | 396.6504 | 0.0000 | no |
| Residual normality (Jarque-Bera) | 379631.7375 | 0.0000 | no |
| Companion stability (min characteristic-root modulus) | 2.4851 | n/a | yes |

Characteristic-root moduli are stable when every value exceeds 1. The reported minimum modulus is the binding one.

## Run count

Total specification runs logged: 5. Reported p-values are read against that count.

## Findings

1. The selected VAR uses 4 variables at lag 2 in log returns, re-estimated on 1747 observations.
2. Ljung-Box whiteness p=0.0000, residual normality p=0.0000, minimum characteristic-root modulus 2.4851.
3. Selection ran over 5 logged specification runs.
