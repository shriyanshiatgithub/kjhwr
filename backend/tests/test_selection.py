from datetime import date, time

from app.models import Forecast
from app.selection import (
    ForecastIndex,
    decision_cutoff,
    decision_day_view,
    delivery_day_bounds,
    horizon_pairs,
)
from conftest import utc


def test_cutoff_is_previous_day_at_cutoff_time_winter():
    # January is GMT, so London time == UTC
    assert decision_cutoff(date(2026, 1, 10), time(9, 0)) == utc(2026, 1, 9, 9)


def test_cutoff_respects_british_summer_time():
    # 9:00 BST on 14 Jul is 08:00 UTC
    assert decision_cutoff(date(2026, 7, 15), time(9, 0)) == utc(2026, 7, 14, 8)


def test_ignores_forecasts_published_after_cutoff(small_store):
    points = decision_day_view(small_store.index, small_store.actuals, date(2026, 1, 10))
    assert all(p.forecast == 1000.0 for p in points)  # not the 5000 vintage
    assert all(p.publish_time == utc(2026, 1, 9, 6) for p in points)


def test_picks_latest_forecast_before_cutoff():
    t = utc(2026, 1, 10, 12)
    idx = ForecastIndex(
        [
            Forecast(t, utc(2026, 1, 9, 3), 100.0),
            Forecast(t, utc(2026, 1, 9, 8, 59), 200.0),  # latest allowed
            Forecast(t, utc(2026, 1, 9, 9, 1), 300.0),  # one minute late
        ]
    )
    pts = decision_day_view(idx, {}, date(2026, 1, 10))
    noon = next(p for p in pts if p.start_time == t)
    assert noon.forecast == 200.0


def test_forecast_published_exactly_at_cutoff_is_allowed():
    t = utc(2026, 1, 10, 12)
    idx = ForecastIndex([Forecast(t, utc(2026, 1, 9, 9, 0), 111.0)])
    noon = next(p for p in decision_day_view(idx, {}, date(2026, 1, 10)) if p.start_time == t)
    assert noon.forecast == 111.0


def test_missing_forecast_is_none_not_zero():
    pts = decision_day_view(ForecastIndex([]), {}, date(2026, 1, 10))
    assert len(pts) == 48
    assert all(p.forecast is None and p.error is None for p in pts)


def test_normal_day_has_48_periods_and_clock_change_days_differ():
    assert len(decision_day_view(ForecastIndex([]), {}, date(2026, 1, 10))) == 48
    assert len(decision_day_view(ForecastIndex([]), {}, date(2026, 3, 29))) == 46  # spring forward
    assert len(decision_day_view(ForecastIndex([]), {}, date(2026, 10, 25))) == 50  # fall back


def test_error_sign_positive_means_overforecast(small_store):
    p = decision_day_view(small_store.index, small_store.actuals, date(2026, 1, 10))[0]
    assert p.error == 200.0  # 1000 forecast - 800 actual


def test_delivery_day_bounds_winter():
    assert delivery_day_bounds(date(2026, 1, 10)) == (utc(2026, 1, 10), utc(2026, 1, 11))


def test_horizon_pairs_uses_forecast_published_at_least_h_hours_before():
    t = utc(2026, 1, 10, 12)
    idx = ForecastIndex(
        [
            Forecast(t, utc(2026, 1, 10, 6), 10.0),  # 6h ahead
            Forecast(t, utc(2026, 1, 10, 10), 20.0),  # 2h ahead
            Forecast(t, utc(2026, 1, 10, 11, 30), 30.0),  # 0.5h ahead
        ]
    )
    actuals = {t: 25.0}
    assert horizon_pairs(idx, actuals, 1, [t]) == [(20.0, 25.0)]
    assert horizon_pairs(idx, actuals, 4, [t]) == [(10.0, 25.0)]
    assert horizon_pairs(idx, actuals, 12, [t]) == []  # nothing that old
