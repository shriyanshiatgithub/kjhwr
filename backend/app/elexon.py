"""Thin client for the Elexon BMRS API plus parsers.

Parsers are separate from HTTP so they can be unit-tested without network.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from .config import ELEXON_BASE_URL
from .models import Forecast

_EPOCH = datetime.min.replace(tzinfo=timezone.utc)


def parse_dt(value: str) -> datetime:
    """Parse an ISO-8601 timestamp into an aware UTC datetime."""
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def parse_forecasts(rows: list[dict]) -> list[Forecast]:
    return [
        Forecast(
            start_time=parse_dt(r["startTime"]),
            publish_time=parse_dt(r["publishTime"]),
            generation=float(r["generation"]),
        )
        for r in rows
        if r.get("generation") is not None
    ]


def parse_actuals(rows: list[dict]) -> dict[datetime, float]:
    """Keep only WIND rows. If a half-hour appears more than once, the most recently
    published row wins (Elexon can republish a corrected value)."""
    out: dict[datetime, float] = {}
    published: dict[datetime, datetime] = {}
    for r in rows:
        if r.get("fuelType") != "WIND" or r.get("generation") is None:
            continue
        start = parse_dt(r["startTime"])
        pub = parse_dt(r["publishTime"]) if r.get("publishTime") else _EPOCH
        if start not in published or pub >= published[start]:
            published[start] = pub
            out[start] = float(r["generation"])
    return out


def _chunks(start: datetime, end: datetime, days: int):
    """Yield consecutive [a, b) windows covering [start, end) with no overlap."""
    cur = start
    while cur < end:
        nxt = min(cur + timedelta(days=days), end)
        yield cur, nxt
        cur = nxt


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _dedupe(rows: list[dict], key_fields: tuple[str, ...]) -> list[dict]:
    """Drop exact repeats (same key fields), keeping the first occurrence."""
    seen: dict[tuple, dict] = {}
    for r in rows:
        seen.setdefault(tuple(r.get(k) for k in key_fields), r)
    return list(seen.values())


def fetch_forecasts(start: datetime, end: datetime, client: httpx.Client | None = None) -> list[dict]:
    """WINDFOR rows published in [start, end). Fetched in 3-day chunks to keep responses small."""
    own = client is None
    client = client or httpx.Client(timeout=60)
    rows: list[dict] = []
    try:
        for a, b in _chunks(start, end, 3):
            r = client.get(
                f"{ELEXON_BASE_URL}/datasets/WINDFOR/stream",
                params={"publishDateTimeFrom": _iso(a), "publishDateTimeTo": _iso(b)},
            )
            r.raise_for_status()
            rows.extend(r.json())
    finally:
        if own:
            client.close()
    return _dedupe(rows, ("startTime", "publishTime"))


def fetch_actuals(start: datetime, end: datetime, client: httpx.Client | None = None) -> list[dict]:
    """FUELHH WIND rows for settlement dates in [start, end).

    The API's settlementDateTo is INCLUSIVE, so each window ends one day early;
    otherwise the boundary day is downloaded twice.
    """
    own = client is None
    client = client or httpx.Client(timeout=60)
    rows: list[dict] = []
    try:
        for a, b in _chunks(start, end, 7):
            r = client.get(
                f"{ELEXON_BASE_URL}/datasets/FUELHH/stream",
                params={
                    "settlementDateFrom": a.strftime("%Y-%m-%d"),
                    "settlementDateTo": (b - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "fuelType": "WIND",
                },
            )
            r.raise_for_status()
            rows.extend(r.json())
    finally:
        if own:
            client.close()
    return _dedupe(rows, ("startTime", "publishTime"))
