# BPS CPI source tables

Raw source for the national consumer price index snapshot at
`data/raw/snapshots/bps_cpi.csv`. Committed because `data/raw` is gitignored and
BPS cannot be re-fetched programmatically, unlike the Yahoo and FRED series. These
files plus `assemble_cpi.py` are the full provenance of the CPI series.

## Files

BPS splits the national CPI across three base-year regimes. Each file is a
downloaded statistics table; the national series is its `INDONESIA` row.

| File | Base | Period | BPS table |
|---|---|---|---|
| Consumer Price Index (General), 2019.csv | 2012=100 | 2019 | Indeks Harga Konsumen (Umum), frozen at 2019 |
| Consumer Price Index of 90 City (General), 2020-2023.csv | 2018=100 | 2020 to 2023 | Indeks Harga Konsumen 90 Kota (Umum) |
| Indeks Harga Konsumen 38 Provinsi (2022=100), 2024-2026.csv | 2022=100 | 2024 to 2026-07 | Indeks Harga Konsumen 38 Provinsi (2022=100) |

Retrieved from https://www.bps.go.id on 2026-08-11.

## Rebuild

```
python data/sources/cpi/assemble_cpi.py
```

The script extracts the `INDONESIA` row from each file and chains the three
segments onto the 2022=100 base by level-matching at each boundary. The result is
one continuous monthly series, 2019-01 to 2026-07, written to
`data/raw/snapshots/bps_cpi.csv`.

## Chaining assumption

Level-matching forces a zero month-over-month change at the two base-change months,
2020-01 and 2024-01, which suppresses their true small inflation. A constant
rescale does not affect month-over-month growth in any other month, so only those
two monthly changes carry the assumption. Cross-check: the 2022=100 segment reports
111.09 for April 2026, matching the BPS press release.
