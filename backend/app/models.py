"""Plain data containers. Kept as dataclasses so the core logic has no framework dependency."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Forecast:
    start_time: datetime  # target half-hour (UTC, timezone-aware)
    publish_time: datetime  # when this forecast was created (UTC, timezone-aware)
    generation: float  # MW


@dataclass(frozen=True)
class DecisionPoint:
    """One half-hour of a delivery day, as seen by the buyer at decision time."""

    start_time: datetime
    forecast: float | None  # MW, latest forecast published at/before the cutoff
    publish_time: datetime | None
    actual: float | None  # MW, what really happened (known only afterwards)

    @property
    def error(self) -> float | None:
        """forecast - actual. Positive = wind was OVER-forecast (buyer is short of power)."""
        if self.forecast is None or self.actual is None:
            return None
        return self.forecast - self.actual
