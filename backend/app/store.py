"""In-memory data store loaded once from a JSON snapshot.

Why a snapshot instead of calling Elexon on every request?
 - Vercel serverless functions are short-lived and Elexon calls are slow.
 - January 2026 is historical, so the data never changes.
 - The demo cannot break because an external API is down.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .elexon import parse_actuals, parse_forecasts
from .models import Forecast
from .selection import ForecastIndex

DEFAULT_SNAPSHOT = Path(__file__).resolve().parent.parent / "data" / "snapshot.json"


class DataStore:
    def __init__(self, forecasts: list[Forecast], actuals: dict[datetime, float], meta: dict | None = None):
        self.forecasts = forecasts
        self.actuals = actuals
        self.index = ForecastIndex(forecasts)
        self.meta = meta or {}

    @classmethod
    def from_snapshot(cls, path: Path = DEFAULT_SNAPSHOT) -> "DataStore":
        raw = json.loads(Path(path).read_text())
        return cls(
            forecasts=parse_forecasts(raw["forecasts"]),
            actuals=parse_actuals(raw["actuals"]),
            meta={"fetched_at": raw.get("fetched_at"), "source": raw.get("source")},
        )
