"""Rebuild the national CPI snapshot from the BPS source tables in this folder.

BPS publishes the national consumer price index across three base-year regimes,
and the free FRED and OECD mirrors stop between 2023 and 2025. Each table here
holds the national INDONESIA row for its period. This script extracts that row
from each file, chains the three segments onto the current 2022=100 base by
level-matching at each boundary, and writes data/raw/snapshots/bps_cpi.csv.

Run from any directory:
    python data/sources/cpi/assemble_cpi.py
"""

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]  # data/sources/cpi -> repo root
OUT = REPO / "data" / "raw" / "snapshots" / "bps_cpi.csv"

# (filename, year), chronological within each base regime.
SEG_2012 = [("Consumer Price Index (General), 2019.csv", 2019)]
SEG_2018 = [
    ("Consumer Price Index of 90 City (General), 2020.csv", 2020),
    ("Consumer Price Index of 90 City (General), 2021.csv", 2021),
    ("Consumer Price Index of 90 City (General), 2022.csv", 2022),
    ("Consumer Price Index of 90 City (General), 2023.csv", 2023),
]
SEG_2022 = [
    ("Indeks Harga Konsumen 38 Provinsi (2022=100), 2024.csv", 2024),
    ("Indeks Harga Konsumen 38 Provinsi (2022=100), 2025.csv", 2025),
    ("Indeks Harga Konsumen 38 Provinsi (2022=100), 2026.csv", 2026),
]


def indonesia_months(filename: str, year: int) -> list[tuple[str, float]]:
    """Return [(YYYY-MM, value)] for the INDONESIA row, skipping missing months."""
    rows = list(csv.reader((HERE / filename).read_text(encoding="utf-8").splitlines()))
    line = next(r for r in rows if r and r[0].strip().upper() == "INDONESIA")
    out = []
    for month, cell in enumerate(line[1:13], start=1):  # 12 month columns
        cell = cell.strip()
        if cell and cell != "-":
            out.append((f"{year}-{month:02d}", float(cell)))
    return out


def collect(segment) -> list[tuple[str, float]]:
    out: list[tuple[str, float]] = []
    for filename, year in segment:
        out.extend(indonesia_months(filename, year))
    return out


def main() -> None:
    s2012 = collect(SEG_2012)
    s2018 = collect(SEG_2018)
    s2022 = collect(SEG_2022)

    # Level-matching link factors onto the 2022=100 base. l2 links 2018=100 to
    # 2022=100 at Dec2023/Jan2024; l1 links 2012=100 to 2018=100 at Dec2019/Jan2020,
    # then onto 2022=100. Each boundary month carries a zero-change assumption.
    l2 = dict(s2022)["2024-01"] / dict(s2018)["2023-12"]
    l1 = (dict(s2018)["2020-01"] / dict(s2012)["2019-12"]) * l2

    chained = (
        [(d, v * l1) for d, v in s2012]
        + [(d, v * l2) for d, v in s2018]
        + list(s2022)
    )
    chained.sort()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["date", "value"])
        for date, value in chained:
            writer.writerow([date, round(value, 4)])

    print(f"wrote {OUT} with {len(chained)} rows, {chained[0][0]} to {chained[-1][0]}")


if __name__ == "__main__":
    main()
