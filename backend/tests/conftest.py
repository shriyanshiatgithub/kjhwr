from datetime import datetime, timedelta, timezone

import pytest

from app.models import Forecast
from app.store import DataStore


def utc(y, m, d, h=0, mi=0):
    return datetime(y, m, d, h, mi, tzinfo=timezone.utc)


@pytest.fixture
def small_store():
    """Delivery day 2026-01-10. Two forecast vintages per half-hour:
    - published 2026-01-09 06:00 (before 09:00 cutoff)  -> forecast 1000
    - published 2026-01-09 12:00 (AFTER the cutoff)     -> forecast 5000 (must be ignored)
    Actual output is a flat 800 MW.
    """
    forecasts, actuals = [], {}
    t = utc(2026, 1, 10)
    while t < utc(2026, 1, 11):
        forecasts.append(Forecast(t, utc(2026, 1, 9, 6), 1000.0))
        forecasts.append(Forecast(t, utc(2026, 1, 9, 12), 5000.0))
        actuals[t] = 800.0
        t += timedelta(minutes=30)
    return DataStore(forecasts, actuals, meta={"source": "test"})
