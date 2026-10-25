import math

import pytest

from app.metrics import compute_metrics, percentile


def test_percentile_matches_known_values():
    assert percentile([1, 2, 3, 4], 50) == 2.5
    assert percentile([10], 90) == 10
    assert percentile([0, 100], 90) == 90


def test_percentile_empty_raises():
    with pytest.raises(ValueError):
        percentile([], 50)


def test_metrics_hand_computed():
    # forecast, actual -> errors: +10, -20, 0
    m = compute_metrics([(110, 100), (80, 100), (50, 50)])
    assert m["n"] == 3
    assert m["mae"] == pytest.approx(10.0)
    assert m["rmse"] == pytest.approx(math.sqrt((100 + 400 + 0) / 3))
    assert m["bias"] == pytest.approx(-10 / 3)


def test_bias_positive_when_overforecasting():
    assert compute_metrics([(120, 100), (130, 100)])["bias"] == pytest.approx(25)


def test_mape_skips_zero_actuals():
    m = compute_metrics([(10, 0), (110, 100)])
    assert m["mape"] == pytest.approx(10.0)


def test_empty_returns_none_fields_not_crash():
    m = compute_metrics([])
    assert m["n"] == 0 and m["mae"] is None and m["rmse"] is None
