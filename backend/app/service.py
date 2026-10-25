"""Use-cases the API exposes. Combines selection + metrics; no HTTP concerns here."""
from __future__ import annotations

from datetime import date, time, timedelta

from .config import HORIZONS_HOURS
from .metrics import compute_metrics
from .selection import decision_day_view, delivery_day_bounds, horizon_pairs, decision_cutoff
from .store import DataStore

HALF_HOUR = timedelta(minutes=30)


def decision_day(store: DataStore, delivery_date: date, cutoff_time: time) -> dict:
    points = decision_day_view(store.index, store.actuals, delivery_date, cutoff_time)
    pairs = [(p.forecast, p.actual) for p in points if p.forecast is not None and p.actual is not None]
    return {
        "delivery_date": delivery_date.isoformat(),
        "decision_cutoff": decision_cutoff(delivery_date, cutoff_time).isoformat(),
        "points": [
            {
                "start_time": p.start_time.isoformat(),
                "forecast": p.forecast,
                "publish_time": p.publish_time.isoformat() if p.publish_time else None,
                "actual": p.actual,
                "error": p.error,
            }
            for p in points
        ],
        "metrics": compute_metrics(pairs),
        "missing_forecast_periods": sum(1 for p in points if p.forecast is None),
    }


def period_metrics(store: DataStore, first: date, last: date, cutoff_time: time) -> dict:
    """Accuracy over a range of delivery dates, overall and per day."""
    daily, all_pairs = [], []
    d = first
    while d <= last:
        points = decision_day_view(store.index, store.actuals, d, cutoff_time)
        pairs = [(p.forecast, p.actual) for p in points if p.forecast is not None and p.actual is not None]
        daily.append({"date": d.isoformat(), **compute_metrics(pairs)})
        all_pairs.extend(pairs)
        d += timedelta(days=1)
    return {"overall": compute_metrics(all_pairs), "daily": daily}


def horizon_metrics(store: DataStore, first: date, last: date) -> list[dict]:
    """How error grows as the forecast is made further ahead of the target time."""
    start, _ = delivery_day_bounds(first)
    _, end = delivery_day_bounds(last)
    targets = []
    t = start
    while t < end:
        targets.append(t)
        t += HALF_HOUR
    return [
        {"horizon_hours": h, **compute_metrics(horizon_pairs(store.index, store.actuals, h, targets))}
        for h in HORIZONS_HOURS
    ]
