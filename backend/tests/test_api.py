import pytest
from fastapi.testclient import TestClient

from app.main import create_app, get_store


@pytest.fixture
def client(small_store):
    app = create_app()
    app.dependency_overrides[get_store] = lambda: small_store
    return TestClient(app)


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_decision_day_uses_pre_cutoff_forecast(client):
    r = client.get("/api/decision-day", params={"delivery_date": "2026-01-10"})
    body = r.json()
    assert r.status_code == 200
    assert body["decision_cutoff"].startswith("2026-01-09T09:00")
    assert len(body["points"]) == 48
    assert {p["forecast"] for p in body["points"]} == {1000.0}
    assert body["metrics"]["mae"] == pytest.approx(200.0)
    assert body["metrics"]["bias"] == pytest.approx(200.0)


def test_later_cutoff_picks_up_newer_forecast(client):
    r = client.get("/api/decision-day", params={"delivery_date": "2026-01-10", "cutoff_time": "13:00"})
    assert {p["forecast"] for p in r.json()["points"]} == {5000.0}


def test_bad_cutoff_rejected(client):
    r = client.get("/api/decision-day", params={"delivery_date": "2026-01-10", "cutoff_time": "25:99"})
    assert r.status_code == 422


def test_bad_date_rejected(client):
    assert client.get("/api/decision-day", params={"delivery_date": "not-a-date"}).status_code == 422


def test_metrics_range_validation(client):
    assert client.get("/api/metrics", params={"first": "2026-01-10", "last": "2026-01-09"}).status_code == 422
    assert client.get("/api/metrics", params={"first": "2026-01-01", "last": "2026-06-01"}).status_code == 422


def test_metrics_overall_and_daily(client):
    r = client.get("/api/metrics", params={"first": "2026-01-10", "last": "2026-01-11"})
    body = r.json()
    assert len(body["daily"]) == 2
    assert body["daily"][0]["n"] == 48
    assert body["daily"][1]["n"] == 0  # no data for the 11th


def test_horizon_metrics_shape(client):
    r = client.get("/api/horizon-metrics", params={"first": "2026-01-10", "last": "2026-01-10"})
    assert r.status_code == 200
    assert [h["horizon_hours"] for h in r.json()][:2] == [1, 3]
