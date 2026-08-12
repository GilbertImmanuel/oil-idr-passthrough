"""Event study for the Hormuz event dates, Phase 4.

Estimate a market model for each JKSE sector ticker against the Jakarta Composite,
compute abnormal returns and cumulative abnormal returns (CAR) around each event, and
aggregate to an energy portfolio and a consumer portfolio. Sector membership is frozen
in docs/DECISIONS.md (2026-08-10) and is not changed here. The event dates and their
selection rule are committed in data/sources/events/.

The market model regresses a ticker log return on the Jakarta Composite log return over
an estimation window that ends GAP trading days before t=0, so the event window does not
contaminate the alpha and beta. Abnormal return is the realized return minus the fitted
market return. CAR is the sum of abnormal returns over the post-event window.

This module returns results and renders a markdown section. src/models/estimation.py
assembles it into docs/ESTIMATION.md. Run `python -m models.event_study` to print the
event count and the aggregate CAR.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from models.descriptive import source_tag

RETURNS_PATH = Path("data/interim/daily_returns.parquet")
EVENTS_PATH = Path("data/sources/events/hormuz_events.csv")

MARKET = "^JKSE"

# Frozen sector membership, docs/DECISIONS.md 2026-08-10.
ENERGY = ["MEDC.JK", "PGAS.JK", "ADRO.JK", "ITMG.JK", "PTBA.JK"]
CONSUMER = ["UNVR.JK", "ICBP.JK", "INDF.JK", "MYOR.JK", "GGRM.JK"]

# Estimation window length and the gap between the window end and t=0, in trading days.
# The post-event window runs [0, POST_WINDOW] inclusive. MIN_EST drops an event whose
# available pre-history is too short to fit a stable market model.
EST_LEN = 120
GAP = 6
POST_WINDOW = 5
MIN_EST = 60


def load_events(path: Path = EVENTS_PATH) -> pd.DataFrame:
    """Read the committed event csv, parsed and sorted by date."""
    events = pd.read_csv(path, parse_dates=["date"])
    return events.sort_values("date").reset_index(drop=True)


def market_model(ticker: pd.Series, market: pd.Series) -> tuple[float, float]:
    """Ordinary least squares alpha and beta of a ticker return on the market return."""
    x = np.column_stack([np.ones(len(market)), market.to_numpy()])
    beta, _, _, _ = np.linalg.lstsq(x, ticker.to_numpy(), rcond=None)
    return float(beta[0]), float(beta[1])


def event_car(
    returns: pd.DataFrame,
    event_date: pd.Timestamp,
    tickers: list[str],
    est_len: int = EST_LEN,
    gap: int = GAP,
    post_window: int = POST_WINDOW,
) -> dict | None:
    """Per-ticker and portfolio CAR for one event, or None if the pre-history is short.

    t=0 is the first trading day on or after event_date. The estimation window is the
    trading days [t0 - gap - est_len, t0 - gap). The post-event window is [t0, t0 +
    post_window] inclusive. Portfolio CAR is the mean CAR across the tickers.
    """
    index = returns.index
    t0 = int(index.searchsorted(event_date, side="left"))
    if t0 >= len(index) or t0 + post_window >= len(index):
        return None

    est_end = t0 - gap
    est_start = max(0, est_end - est_len)
    if est_end - est_start < MIN_EST:
        return None

    market = returns[MARKET]
    est_market = market.iloc[est_start:est_end]
    event_market = market.iloc[t0 : t0 + post_window + 1]

    car_by_ticker: dict[str, float] = {}
    for ticker in tickers:
        alpha, beta = market_model(returns[ticker].iloc[est_start:est_end], est_market)
        realized = returns[ticker].iloc[t0 : t0 + post_window + 1]
        abnormal = realized - (alpha + beta * event_market)
        car_by_ticker[ticker] = float(abnormal.sum())

    return {
        "event_date": event_date,
        "t0_date": index[t0],
        "est_n": int(est_end - est_start),
        "car_by_ticker": car_by_ticker,
        "car_portfolio": float(np.mean(list(car_by_ticker.values()))),
    }


def _caar(cars: list[float]) -> dict:
    """Cumulative average abnormal return with a cross-event t statistic."""
    arr = np.asarray(cars, dtype=float)
    n = len(arr)
    mean = float(arr.mean())
    se = float(arr.std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
    t = mean / se if se and np.isfinite(se) and se > 0 else float("nan")
    return {"caar": mean, "se": se, "t": t, "n": n}


def run(returns: pd.DataFrame | None = None, events: pd.DataFrame | None = None) -> dict:
    """Compute per-event and aggregate CAR for the energy and consumer portfolios.

    The spread is the per-event energy CAR minus consumer CAR, aggregated across events.
    It answers H2 (sign) and M3 (sign and size). Dropped events carry too short a
    pre-history and are reported, not silently omitted.
    """
    returns = pd.read_parquet(RETURNS_PATH) if returns is None else returns
    events = load_events() if events is None else events

    per_event = []
    dropped = []
    for _, row in events.iterrows():
        energy = event_car(returns, row["date"], ENERGY)
        consumer = event_car(returns, row["date"], CONSUMER)
        if energy is None or consumer is None:
            dropped.append(row["date"])
            continue
        per_event.append(
            {
                "event_date": row["date"],
                "t0_date": energy["t0_date"],
                "energy_car": energy["car_portfolio"],
                "consumer_car": consumer["car_portfolio"],
                "spread": energy["car_portfolio"] - consumer["car_portfolio"],
            }
        )

    energy_cars = [e["energy_car"] for e in per_event]
    consumer_cars = [e["consumer_car"] for e in per_event]
    spreads = [e["spread"] for e in per_event]

    return {
        "per_event": per_event,
        "dropped": dropped,
        "n_events_total": int(len(events)),
        "n_events_used": int(len(per_event)),
        "post_window": POST_WINDOW,
        "est_len": EST_LEN,
        "energy": _caar(energy_cars) if energy_cars else None,
        "consumer": _caar(consumer_cars) if consumer_cars else None,
        "spread": _caar(spreads) if spreads else None,
    }


def _fmt(value: float, places: int = 4) -> str:
    return f"{value:.{places}f}"


def render_section(result: dict, manifest: dict) -> str:
    """Render the event-study markdown section for docs/ESTIMATION.md."""
    market_tag = source_tag(MARKET, manifest)
    energy_tags = " ".join(source_tag(s, manifest) for s in ENERGY)
    consumer_tags = " ".join(source_tag(s, manifest) for s in CONSUMER)

    lines: list[str] = []
    lines.append("## Event study: Hormuz events and sector CAR")
    lines.append("")
    lines.append(
        f"Market model per sector ticker on the Jakarta Composite {market_tag} return, "
        f"estimation window {result['est_len']} trading days ending {GAP} days before "
        f"t=0, post-event window [0, {result['post_window']}] trading days inclusive. "
        "Event dates and the selection rule: data/sources/events/. Sector membership is "
        "frozen in docs/DECISIONS.md 2026-08-10. Energy: "
        + ", ".join(ENERGY)
        + f" {energy_tags}. Consumer: "
        + ", ".join(CONSUMER)
        + f" {consumer_tags}."
    )
    lines.append("")
    lines.append(
        f"Events in the list: {result['n_events_total']}. Events with a full estimation "
        f"and post-event window inside the daily panel: {result['n_events_used']}."
    )
    if result["dropped"]:
        dropped = ", ".join(d.date().isoformat() for d in result["dropped"])
        lines.append("")
        lines.append(f"Dropped for short pre-history: {dropped}.")
    lines.append("")
    lines.append(
        f"At n={result['n_events_used']} the cross-event test carries low power "
        "(PROJECT_PLAN section 10). The 2019 events and the 2026 closure-episode events "
        "cluster, so their windows overlap and the events are not independent. The event "
        "study is a supporting result, not the headline."
    )
    lines.append("")
    lines.append("| event | t=0 | energy CAR | consumer CAR | energy minus consumer |")
    lines.append("|---|---|---|---|---|")
    for e in result["per_event"]:
        lines.append(
            f"| {e['event_date'].date().isoformat()} | {e['t0_date'].date().isoformat()} | "
            f"{_fmt(e['energy_car'])} | {_fmt(e['consumer_car'])} | {_fmt(e['spread'])} |"
        )
    lines.append("")
    lines.append("| portfolio | CAAR | cross-event SE | t | n |")
    lines.append("|---|---|---|---|---|")
    labels = [("energy", "energy"), ("consumer", "consumer"), ("energy minus consumer", "spread")]
    for label, key in labels:
        agg = result[key]
        lines.append(
            f"| {label} | {_fmt(agg['caar'])} | {_fmt(agg['se'])} | {_fmt(agg['t'])} | {agg['n']} |"
        )
    lines.append("")
    return "\n".join(lines)


def demo() -> None:
    """Self-check: a ticker equal to beta times the market has near-zero abnormal return,
    and an injected post-event jump raises the CAR by that jump.
    """
    idx = pd.date_range("2020-01-01", periods=200, freq="B")
    rng = np.random.default_rng(0)
    market = pd.Series(rng.normal(scale=0.01, size=200), index=idx, name=MARKET)
    # Ticker tracks the market at beta=1.5 with no idiosyncratic move.
    ticker = 1.5 * market
    returns = pd.DataFrame({MARKET: market, "MEDC.JK": ticker})
    event_date = idx[150]
    base = event_car(returns, event_date, ["MEDC.JK"])
    assert base is not None
    assert abs(base["car_portfolio"]) < 1e-8, base["car_portfolio"]

    # Inject a 0.05 abnormal jump on t=0 only; CAR rises by 0.05.
    bumped = returns.copy()
    t0 = returns.index.searchsorted(event_date)
    bumped.iloc[t0, bumped.columns.get_loc("MEDC.JK")] += 0.05
    bumped_car = event_car(bumped, event_date, ["MEDC.JK"])["car_portfolio"]
    assert abs(bumped_car - 0.05) < 1e-8, bumped_car
    print("event_study demo ok")


if __name__ == "__main__":
    result = run()
    print(
        f"events total={result['n_events_total']} used={result['n_events_used']} "
        f"energy CAAR={result['energy']['caar']:.4f} "
        f"consumer CAAR={result['consumer']['caar']:.4f} "
        f"spread={result['spread']['caar']:.4f} (t={result['spread']['t']:.2f})"
    )
