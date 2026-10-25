"""Generate SYNTHETIC wind data so the app can run before real Elexon data is fetched.

!! This is NOT real data. The output is labelled "SYNTHETIC" and the UI shows a
!! warning banner. Replace it by running scripts/fetch_snapshot.py.

Shape mimics the real feeds: forecasts are published every 3 hours, up to 48h
ahead of each target half-hour, and get noisier the further ahead they are made.
"""
import json
import math
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "backend" / "data" / "snapshot.json"
UTC = timezone.utc
HALF = timedelta(minutes=30)


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> None:
    rng = random.Random(42)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 2, 2, tzinfo=UTC)

    # "True" wind: slow weather systems + AR(1) noise, clamped to a plausible GB range (MW)
    actuals: dict[datetime, float] = {}
    noise = 0.0
    t = start
    while t < end:
        hours = (t - start).total_seconds() / 3600
        base = 7500 + 4500 * math.sin(hours / 41) + 2500 * math.sin(hours / 17 + 1.3)
        noise = 0.97 * noise + rng.gauss(0, 120)
        actuals[t] = max(250.0, min(17000.0, base + noise))
        t += HALF

    publish_times = []
    p = start
    while p < end:
        publish_times.append(p)
        p += timedelta(hours=3)

    forecasts = []
    for target, actual in actuals.items():
        for pub in publish_times:
            horizon_h = (target - pub).total_seconds() / 3600
            if not (0.5 <= horizon_h <= 48):
                continue
            sd = 150 + 55 * horizon_h  # error grows with horizon
            value = max(0.0, actual + rng.gauss(0.01 * horizon_h * 100, sd))
            forecasts.append(
                {"dataset": "WINDFOR", "publishTime": iso(pub), "startTime": iso(target), "generation": round(value, 1)}
            )

    actual_rows = [
        {
            "dataset": "FUELHH",
            "startTime": iso(t),
            "settlementDate": t.strftime("%Y-%m-%d"),
            "fuelType": "WIND",
            "generation": round(v, 1),
        }
        for t, v in actuals.items()
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "source": "SYNTHETIC DEMO DATA - not from Elexon",
                "fetched_at": datetime.now(UTC).isoformat(),
                "forecasts": forecasts,
                "actuals": actual_rows,
            }
        )
    )
    print(f"Wrote {OUT}: {len(forecasts)} forecasts, {len(actual_rows)} actuals")


if __name__ == "__main__":
    main()
