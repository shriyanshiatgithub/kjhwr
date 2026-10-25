"""The heart of the product: which forecast did the buyer actually have?

Rule: for each half-hour of delivery day D, take the forecast with the latest
publish_time that is <= the decision cutoff (D-1 at cutoff time, UK local).
Anything published after the cutoff is "future information" the buyer did not
have, so using it would make the forecasts look better than they really were.
"""
from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable

from .config import DEFAULT_CUTOFF, LONDON
from .models import DecisionPoint, Forecast

HALF_HOUR = timedelta(minutes=30)


def decision_cutoff(delivery_date: date, cutoff_time: time = DEFAULT_CUTOFF) -> datetime:
    """UTC instant by which the day-ahead purchase for `delivery_date` must be decided."""
    local = datetime.combine(delivery_date - timedelta(days=1), cutoff_time, tzinfo=LONDON)
    return local.astimezone(timezone.utc)


def delivery_day_bounds(delivery_date: date) -> tuple[datetime, datetime]:
    """UTC [start, end) of a UK local calendar day (handles 23h/25h clock-change days)."""
    start = datetime.combine(delivery_date, time(0, 0), tzinfo=LONDON).astimezone(timezone.utc)
    end = datetime.combine(delivery_date + timedelta(days=1), time(0, 0), tzinfo=LONDON).astimezone(
        timezone.utc
    )
    return start, end


class ForecastIndex:
    """Fast lookup: 'latest forecast for target T published at or before time L'."""

    def __init__(self, forecasts: Iterable[Forecast]):
        grouped: dict[datetime, list[Forecast]] = defaultdict(list)
        for f in forecasts:
            grouped[f.start_time].append(f)
        self._items: dict[datetime, list[Forecast]] = {}
        self._keys: dict[datetime, list[datetime]] = {}
        for start, items in grouped.items():
            items.sort(key=lambda f: f.publish_time)
            self._items[start] = items
            self._keys[start] = [f.publish_time for f in items]

    def latest_published_by(self, start_time: datetime, limit: datetime) -> Forecast | None:
        keys = self._keys.get(start_time)
        if not keys:
            return None
        i = bisect_right(keys, limit)  # first index strictly after limit
        return self._items[start_time][i - 1] if i else None


def decision_day_view(
    index: ForecastIndex,
    actuals: dict[datetime, float],
    delivery_date: date,
    cutoff_time: time = DEFAULT_CUTOFF,
) -> list[DecisionPoint]:
    """Every half-hour of `delivery_date`, with the forecast the buyer had at the cutoff."""
    cutoff = decision_cutoff(delivery_date, cutoff_time)
    start, end = delivery_day_bounds(delivery_date)
    points: list[DecisionPoint] = []
    t = start
    while t < end:
        f = index.latest_published_by(t, cutoff)
        points.append(
            DecisionPoint(
                start_time=t,
                forecast=f.generation if f else None,
                publish_time=f.publish_time if f else None,
                actual=actuals.get(t),
            )
        )
        t += HALF_HOUR
    return points


def horizon_pairs(
    index: ForecastIndex,
    actuals: dict[datetime, float],
    horizon_hours: float,
    targets: Iterable[datetime],
) -> list[tuple[float, float]]:
    """(forecast, actual) pairs using the latest forecast published >= `horizon_hours` before target."""
    pairs: list[tuple[float, float]] = []
    for t in targets:
        actual = actuals.get(t)
        if actual is None:
            continue
        f = index.latest_published_by(t, t - timedelta(hours=horizon_hours))
        if f is not None:
            pairs.append((f.generation, actual))
    return pairs
