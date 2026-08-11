# Descriptive deliverables D1 to D5

Computed once from data/interim/daily_panel.parquet, spine 2019-01-02 to 2026-08-03, 1750 trading days. Each series is retrieved per data/MANIFEST.json. Test statistics and p-values are reported as returned and are not re-run.

## D1 integration order

ADF null is a unit root, KPSS null is stationarity, decided at 0.05. The order column applies the levels tests: ADF rejects with KPSS not rejecting is I(0), the reverse is I(1), an agreement is ambiguous.

| series | ADF level | ADF p | KPSS level | KPSS p | ADF diff | ADF p | KPSS diff | KPSS p | order | source |
|---|---|---|---|---|---|---|---|---|---|---|
| DCOILBRENTEU | -2.247 | 0.190 | 1.821 | 0.010 | -9.241 | 0.000 | 0.038 | 0.100 | I(1) | [FRED:DCOILBRENTEU, 2026-08-10] |
| BZ=F | -2.206 | 0.204 | 1.827 | 0.010 | -12.640 | 0.000 | 0.040 | 0.100 | I(1) | [Yahoo:BZ=F, 2026-08-10] |
| ^JKSE | -2.099 | 0.245 | 3.627 | 0.010 | -22.032 | 0.000 | 0.084 | 0.100 | I(1) | [Yahoo:^JKSE, 2026-08-10] |
| IDR=X | -0.676 | 0.853 | 5.478 | 0.010 | -8.677 | 0.000 | 0.098 | 0.100 | I(1) | [Yahoo:IDR=X, 2026-08-10] |
| DX-Y.NYB | -1.768 | 0.396 | 2.160 | 0.010 | -18.905 | 0.000 | 0.067 | 0.100 | I(1) | [Yahoo:DX-Y.NYB, 2026-08-10] |
| MEDC.JK | -1.429 | 0.568 | 5.348 | 0.010 | -29.019 | 0.000 | 0.035 | 0.100 | I(1) | [Yahoo:MEDC.JK, 2026-08-10] |
| PGAS.JK | -1.734 | 0.414 | 2.618 | 0.010 | -11.604 | 0.000 | 0.117 | 0.100 | I(1) | [Yahoo:PGAS.JK, 2026-08-10] |
| ADRO.JK | 0.308 | 0.978 | 5.883 | 0.010 | -13.691 | 0.000 | 0.121 | 0.100 | I(1) | [Yahoo:ADRO.JK, 2026-08-10] |
| ITMG.JK | -0.738 | 0.837 | 5.688 | 0.010 | -14.323 | 0.000 | 0.085 | 0.100 | I(1) | [Yahoo:ITMG.JK, 2026-08-10] |
| PTBA.JK | -0.933 | 0.777 | 5.682 | 0.010 | -32.429 | 0.000 | 0.087 | 0.100 | I(1) | [Yahoo:PTBA.JK, 2026-08-10] |
| UNVR.JK | -1.454 | 0.556 | 5.943 | 0.010 | -13.717 | 0.000 | 0.058 | 0.100 | I(1) | [Yahoo:UNVR.JK, 2026-08-10] |
| ICBP.JK | -1.569 | 0.499 | 0.996 | 0.010 | -16.403 | 0.000 | 0.114 | 0.100 | I(1) | [Yahoo:ICBP.JK, 2026-08-10] |
| INDF.JK | -1.992 | 0.290 | 3.818 | 0.010 | -23.266 | 0.000 | 0.038 | 0.100 | I(1) | [Yahoo:INDF.JK, 2026-08-10] |
| MYOR.JK | -2.627 | 0.087 | 0.581 | 0.024 | -26.725 | 0.000 | 0.053 | 0.100 | I(1) | [Yahoo:MYOR.JK, 2026-08-10] |
| GGRM.JK | -2.779 | 0.061 | 5.315 | 0.010 | -10.692 | 0.000 | 0.308 | 0.100 | I(1) | [Yahoo:GGRM.JK, 2026-08-10] |

## D2 Johansen cointegration

Level set: the macro passthrough chain, DCOILBRENTEU, DX-Y.NYB, IDR=X, ^JKSE. Trace and maximum-eigenvalue statistics at the 95 percent critical value, n=1750. Series: [FRED:DCOILBRENTEU, 2026-08-10] [Yahoo:DX-Y.NYB, 2026-08-10] [Yahoo:IDR=X, 2026-08-10] [Yahoo:^JKSE, 2026-08-10].

| null rank r | trace stat | trace 95 crit | max-eig stat | max-eig 95 crit |
|---|---|---|---|---|
| r <= 0 | 36.434 | 47.855 | 19.723 | 27.586 |
| r <= 1 | 16.711 | 29.796 | 12.546 | 21.131 |
| r <= 2 | 4.165 | 15.494 | 3.614 | 14.264 |
| r <= 3 | 0.551 | 3.841 | 0.551 | 3.841 |

Rank by trace: 0. Rank by maximum eigenvalue: 0.

## D3 Brent and IDR return correlation

Unconditional Pearson correlation of Brent returns and IDR per USD returns, full sample. r=0.0089, n=1749. Series: [FRED:DCOILBRENTEU, 2026-08-10] [Yahoo:IDR=X, 2026-08-10].

## D4 correlation stability across subsamples

The D3 correlation recomputed by calendar year. Series: [FRED:DCOILBRENTEU, 2026-08-10] [Yahoo:IDR=X, 2026-08-10].

| subsample | r | n |
|---|---|---|
| 2020 | 0.0358 | 234 |
| 2022 | -0.0757 | 233 |
| 2026 | -0.0061 | 130 |

## D5 pre-specified structural break in the IDR equation

Equation: IDR return on a constant, its own first lag, and the Brent return. The break date is pre-specified at the Bank Indonesia anti-speculation effective date [Trading Economics, 2026-03-18]. The Chow test uses that date. The supF search takes the maximum Chow statistic over the interior 15 percent-trimmed sample. The supF reference distribution is non-standard (Andrews 1993), so the argmax date is reported without a pointwise p-value. Series: [FRED:DCOILBRENTEU, 2026-08-10] [Yahoo:IDR=X, 2026-08-10].

| test | statistic | p-value | date |
|---|---|---|---|
| Chow at known date | 0.8741 | 0.4538 | 2026-04-01 |
| supF unknown date | 3.8066 | n/a | 2020-03-20 |

n=1748, parameters per segment k=3.

## Findings

1. Integration order across 15 series: 15 I(1).
2. Johansen rank on the level set is 0 by trace and 0 by maximum eigenvalue, n=1750.
3. Full-sample Brent and IDR return correlation is 0.0089, n=1749.
4. Subsample correlation: 2020 0.0358 (n=234), 2022 -0.0757 (n=233), 2026 -0.0061 (n=130).
5. Chow at 2026-04-01 is 0.8741 (p=0.4538); supF over the trimmed interior is 3.8066 at 2020-03-20.
