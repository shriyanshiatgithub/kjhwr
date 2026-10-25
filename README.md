# Wind Forecast Desk

A web app for a UK energy utility's day-ahead power buyers. It shows:

1. **Decision view**: the wind forecast that was actually available when the day-ahead purchase had to be decided (the latest forecast published before the deadline on the previous day), next to what really happened.
2. **Forecast accuracy**: quantified error (MAE, RMSE, bias, percentile bands, error by forecast horizon) so purchase decisions can allow for it.

Scope: national wind generation only, from Elexon BMRS (`FUELHH` actuals, `WINDFOR` forecasts), for purchase decisions made in **January 2026**.

**Live app:** `https://kjhwr-snowy.vercel.app/`

## AI tools disclosure

Claude (Anthropic) was used as an AI-assisted tool for coding support, testing, and documentation. The code was reviewed and validated to ensure functionality and quality.

## Key assumptions

- **Decision deadline = 09:00 UK time on the day before delivery.** GB day-ahead auctions close in the morning; the exact time is configurable in the UI and API (`cutoff_time`).
- **Forecast used = latest forecast with `publishTime` <= deadline.** Later forecasts are never used (that would be look-ahead bias).
- **Error = forecast - actual.** Positive means wind was over-forecast, so the buyer is short of power.
- Data is a **snapshot** (`backend/data/snapshot.json`) because January 2026 is historical and a snapshot keeps the serverless deploy fast and reliable.

## Files and directories

```
.
├── backend/
│   ├── app/
│   │   ├── config.py        settings and assumptions (cutoff, horizons)
│   │   ├── models.py        Forecast and DecisionPoint dataclasses
│   │   ├── elexon.py        Elexon API client and parsers
│   │   ├── store.py         loads the snapshot into memory
│   │   ├── selection.py     "latest forecast before the deadline" logic
│   │   ├── metrics.py       error formulas (MAE, RMSE, bias, percentiles)
│   │   ├── service.py       combines selection + metrics into API answers
│   │   └── main.py          FastAPI routes and validation
│   ├── tests/               pytest suite (selection, metrics, API)
│   ├── data/snapshot.json   data used by the app
│   ├── Dockerfile
│   ├── requirements.txt         runtime dependencies
│   └── requirements-dev.txt     adds pytest
├── frontend/
│   ├── src/
│   │   ├── App.jsx, main.jsx    shell, tabs, shared deadline control
│   │   ├── api.js               all HTTP calls
│   │   ├── useApi.js            data-loading hook (cancels stale requests)
│   │   ├── format.js(+test)     formatting and small calculations
│   │   ├── styles.css
│   │   └── components/          DecisionView, AccuracyView, MetricCards, StatusBlock
│   ├── Dockerfile, nginx.conf
│   └── package.json
├── scripts/
│   ├── fetch_snapshot.py            download real data from Elexon
│   └── make_synthetic_snapshot.py   generate labelled SYNTHETIC data for development only
├── vercel.json              Vercel config: frontend + backend as two services
├── docker-compose.yml
├── .github/workflows/ci.yml        runs backend and frontend tests on every push
└── GUIDE.md                 domain and design explanation
```

## How to start

### 1. Get the data (needs internet, once)

```bash
pip install -r backend/requirements-dev.txt
python scripts/fetch_snapshot.py
```

This writes `backend/data/snapshot.json`. The repo already contains a snapshot of the real January 2026 data, so this step is only needed to refresh it. (`scripts/make_synthetic_snapshot.py` can generate clearly labelled fake data for development; the UI shows a warning banner if that is loaded.)

### 2. Run locally

```bash
# terminal 1: API on :8000
cd backend && uvicorn app.main:app --reload

# terminal 2: UI on :5173
cd frontend && npm install && npm run dev
```

Open http://localhost:5173. API docs: http://localhost:8000/docs.

### 3. Run with Docker

```bash
docker compose up --build
```

Open http://localhost:8080.

### 4. Tests

```bash
cd backend && python -m pytest      # API, selection and metrics
cd frontend && npm test             # formatting and calculation helpers
```

## API

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Row counts and data source |
| `GET /api/config` | Default deadline and decision month |
| `GET /api/decision-day?delivery_date=2026-01-15&cutoff_time=09:00` | 48 half-hours of forecast vs actual plus metrics |
| `GET /api/metrics?first=2026-01-02&last=2026-02-01&cutoff_time=09:00` | Overall and per-day accuracy |
| `GET /api/horizon-metrics?first=...&last=...` | Error vs how far ahead the forecast was made |

## Deploying to Vercel

`vercel.json` defines two services in one project: the Vite `frontend` (served at `/`) and the FastAPI `backend` (served at `/api/*`; the path is passed through unchanged, so routes already start with `/api`).

1. Push the repo to GitHub and import it in Vercel (root directory `./`).
2. Vercel reads `vercel.json` and builds both services; no extra settings are needed.
3. Check `<url>/api/health`, then open `<url>/`.

## Findings (January 2026 pilot, delivery days 2 Jan - 1 Feb)

Using the forecast available at a 09:00 UK deadline on the previous day (744 hourly comparisons):

| Metric | Value |
|---|---|
| Mean absolute error | about 2,022 MW |
| RMSE | about 2,497 MW |
| Bias (forecast - actual) | about +1,746 MW (forecasts too high) |
| 90% of misses below | about 4,154 MW |
| Mean absolute percentage error | about 21.9% |

- **Forecasts were too high on most days**, so a buyer relying on them would usually be short of wind power.
- **Waiting for a later forecast barely helps.** Error is already about 1,700 MW (MAE) for forecasts made 1 hour ahead and rises only to about 2,300 MW at 48 hours. This suggests a systematic offset between the two datasets rather than weather uncertainty. The cause is not yet established; possible explanations (for example curtailment, or differing definitions of the two series) are untested.
- **The forecast feed only has values for every other half-hour** on the days inspected, so comparisons use the periods that have both a forecast and an actual.
- Error is concentrated in a few days (11-12 Jan and 28 Jan stand out in the daily chart).

## Limitations

- One data source and national level only, as specified.
- The 09:00 deadline is an assumption.
- One winter month is a small sample; results should not be generalised to other seasons.
- The app quantifies forecast error but does not model demand or prices.
