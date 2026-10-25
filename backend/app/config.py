"""Central settings. Anything a reviewer might ask "why this value?" lives here."""
from datetime import time
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")

ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

# Day-ahead decisions are made on D-1 before the auction gate closes.
# GB day-ahead auctions close in the morning (roughly 09:20-09:50 UK time),
# so we assume the buyer must decide by 09:00 UK time on D-1. This is an
# ASSUMPTION: it is configurable per request and must be stated in the demo.
DEFAULT_CUTOFF = time(9, 0)

# Scope fixed by the assignment: decisions made in January 2026.
DECISION_MONTH_START = "2026-01-01"
DECISION_MONTH_END = "2026-01-31"

# Forecast horizons (hours ahead of the target time) for the accuracy-by-horizon view.
HORIZONS_HOURS = [1, 3, 6, 12, 24, 36, 48]
