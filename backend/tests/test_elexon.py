from datetime import datetime, timezone

from app.elexon import _chunks, _dedupe, parse_actuals


def utc(d, h=0):
    return datetime(2026, 1, d, h, tzinfo=timezone.utc)


def test_parse_actuals_keeps_only_wind():
    rows = [
        {"startTime": "2026-01-02T00:00:00Z", "fuelType": "WIND", "generation": 100},
        {"startTime": "2026-01-02T00:00:00Z", "fuelType": "CCGT", "generation": 999},
    ]
    assert parse_actuals(rows) == {utc(2): 100.0}


def test_parse_actuals_latest_publish_wins_whatever_the_row_order():
    old = {"startTime": "2026-01-02T00:00:00Z", "publishTime": "2026-01-02T01:00:00Z", "fuelType": "WIND", "generation": 100}
    new = {"startTime": "2026-01-02T00:00:00Z", "publishTime": "2026-01-03T01:00:00Z", "fuelType": "WIND", "generation": 120}
    assert parse_actuals([old, new]) == {utc(2): 120.0}
    assert parse_actuals([new, old]) == {utc(2): 120.0}


def test_chunks_cover_range_with_no_overlap_or_gap():
    windows = list(_chunks(utc(1), utc(11), 4))
    assert windows == [(utc(1), utc(5)), (utc(5), utc(9)), (utc(9), utc(11))]


def test_dedupe_removes_exact_repeats_only():
    rows = [
        {"startTime": "a", "publishTime": "1", "generation": 1},
        {"startTime": "a", "publishTime": "1", "generation": 1},  # repeat
        {"startTime": "a", "publishTime": "2", "generation": 2},  # different vintage, keep
    ]
    assert len(_dedupe(rows, ("startTime", "publishTime"))) == 2
