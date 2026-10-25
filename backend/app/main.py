"""FastAPI entrypoint. Routes validate input, call service functions, return JSON."""
from __future__ import annotations

from datetime import date, time

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import service
from .config import DECISION_MONTH_END, DECISION_MONTH_START, DEFAULT_CUTOFF
from .store import DataStore

_store: DataStore | None = None


def get_store() -> DataStore:
    """Dependency: lazily load the snapshot once. Tests override this."""
    global _store
    if _store is None:
        _store = DataStore.from_snapshot()
    return _store


def parse_cutoff(cutoff_time: str = Query(DEFAULT_CUTOFF.strftime("%H:%M"), pattern=r"^\d{2}:\d{2}$")) -> time:
    try:
        return time.fromisoformat(cutoff_time)
    except ValueError:
        raise HTTPException(status_code=422, detail="cutoff must be HH:MM, e.g. 09:00")


def create_app() -> FastAPI:
    app = FastAPI(title="Wind Forecast Decision Support", version="0.1.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])

    @app.get("/api/health")
    def health(store: DataStore = Depends(get_store)):
        return {
            "status": "ok",
            "forecast_rows": len(store.forecasts),
            "actual_rows": len(store.actuals),
            **store.meta,
        }

    @app.get("/api/config")
    def config():
        return {
            "default_cutoff": DEFAULT_CUTOFF.strftime("%H:%M"),
            "decision_month_start": DECISION_MONTH_START,
            "decision_month_end": DECISION_MONTH_END,
        }

    @app.get("/api/decision-day")
    def decision_day(
        delivery_date: date,
        cutoff_time: time = Depends(parse_cutoff),
        store: DataStore = Depends(get_store),
    ):
        return service.decision_day(store, delivery_date, cutoff_time)

    @app.get("/api/metrics")
    def metrics(
        first: date,
        last: date,
        cutoff_time: time = Depends(parse_cutoff),
        store: DataStore = Depends(get_store),
    ):
        if last < first:
            raise HTTPException(status_code=422, detail="last must be on or after first")
        if (last - first).days > 62:
            raise HTTPException(status_code=422, detail="range too large (max 62 days)")
        return service.period_metrics(store, first, last, cutoff_time)

    @app.get("/api/horizon-metrics")
    def horizon_metrics(first: date, last: date, store: DataStore = Depends(get_store)):
        if last < first:
            raise HTTPException(status_code=422, detail="last must be on or after first")
        return service.horizon_metrics(store, first, last)

    return app


app = create_app()
