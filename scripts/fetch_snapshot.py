"""Download January-2026 decision data from Elexon and save backend/data/snapshot.json.

Run from the repo root on a machine with internet access:
    pip install -r backend/requirements-dev.txt
    python scripts/fetch_snapshot.py

Decisions made in January 2026 => delivery days 2 Jan .. 1 Feb 2026.
Forecasts needed: published from 1 Jan to the cutoff on 31 Jan.
Actuals needed: 2 Jan .. 1 Feb (we fetch a day either side for safety).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.elexon import fetch_actuals, fetch_forecasts  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "backend" / "data" / "snapshot.json"


def main() -> None:
    pub_from = datetime(2026, 1, 1, tzinfo=timezone.utc)
    pub_to = datetime(2026, 2, 1, tzinfo=timezone.utc)
    act_from = datetime(2026, 1, 1, tzinfo=timezone.utc)
    act_to = datetime(2026, 2, 2, tzinfo=timezone.utc)

    print("Fetching WINDFOR forecasts ...")
    forecasts = fetch_forecasts(pub_from, pub_to)
    print(f"  {len(forecasts)} rows")
    print("Fetching FUELHH wind actuals ...")
    actuals = fetch_actuals(act_from, act_to)
    print(f"  {len(actuals)} rows")

    if not forecasts or not actuals:
        sys.exit("Got no rows - check the parameter names against the Elexon docs.")
    print("Sample forecast:", forecasts[0])
    print("Sample actual:  ", actuals[0])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "source": "Elexon BMRS (WINDFOR, FUELHH)",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "forecasts": forecasts,
                "actuals": actuals,
            }
        )
    )
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
