"""Fetch daily price series from Yahoo Finance via yfinance."""

from __future__ import annotations

import pandas as pd
import yfinance as yf

from .store import load_or_fetch

START = "2019-01-01"

# Index, currency, and futures series for the response chain under study.
PRICE_SERIES = ["BZ=F", "^JKSE", "IDR=X", "DX-Y.NYB"]

# JKSE sector constituents for the energy-versus-consumer return contrast.
# ponytail: fixed large-cap lists; revise membership through docs/DECISIONS.md
# rather than editing silently, since H2 is defined by these members.
ENERGY_JK = ["MEDC.JK", "PGAS.JK", "ADRO.JK", "ITMG.JK", "PTBA.JK"]
CONSUMER_JK = ["UNVR.JK", "ICBP.JK", "INDF.JK", "MYOR.JK", "GGRM.JK"]


def all_tickers() -> list[str]:
    return PRICE_SERIES + ENERGY_JK + CONSUMER_JK


def fetch(ticker: str, start: str = START) -> pd.DataFrame:
    """Fetch one ticker and cache its adjusted close as a tidy long frame."""

    def _fetch() -> pd.DataFrame:
        raw = yf.download(ticker, start=start, progress=False, auto_adjust=True)
        assert not raw.empty, f"{ticker}: yfinance returned no rows"
        close = raw["Close"]
        # yfinance returns MultiIndex columns keyed by ticker even for one symbol.
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        frame = close.rename("value").rename_axis("date").reset_index()
        frame["series_id"] = ticker
        return frame

    return load_or_fetch(ticker, "Yahoo", _fetch)


def fetch_all(start: str = START) -> dict[str, int]:
    """Fetch every configured ticker. Returns {ticker: row_count}, -1 on failure."""
    result: dict[str, int] = {}
    for ticker in all_tickers():
        try:
            result[ticker] = len(fetch(ticker, start))
        except Exception as exc:
            result[ticker] = -1
            print(f"skip {ticker}: {exc}")
    return result
