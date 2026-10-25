# Wind Forecast Desk

A web app for a UK energy utility's day-ahead power buyers. It shows:

1. **Decision view**: the wind forecast that was actually available when the day-ahead purchase had to be decided (the latest forecast published before the deadline on the previous day), next to what really happened.
2. **Forecast accuracy**: quantified error (MAE, RMSE, bias, percentile bands, error by forecast horizon) so purchase decisions can allow for it.

Scope: national wind generation only, from Elexon BMRS (`FUELHH` actuals, `WINDFOR` forecasts), for purchase decisions made in **January 2026**.

**Live app:** `<ADD VERCEL URL HERE>`

## AI tools disclosure

This project was built with the help of an AI assistant (Claude by Anthropic) for code generation, tests and documentation. I reviewed the code and can explain and modify it.

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
├── api/index.py             Vercel serverless entrypoint
├── vercel.json, requirements.txt   Vercel deployment config
├── docker-compose.yml
├── .github/workflows/ci.yml        runs backend and frontend tests on every push
├── GUIDE.md                 domain and design explanation
└── WORKFLOW.md              build checklist
```

## How to start

### 1. Get the data (needs internet, once)

```bash
pip install -r backend/requirements-dev.txt
python scripts/fetch_snapshot.py
```

This writes `backend/data/snapshot.json`. Until you do, the repo may contain *synthetic* demo data; the UI shows a warning banner when it does.

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

1. Push the repo to GitHub, import it in Vercel.
2. Leave the framework preset as "Other"; `vercel.json` sets the build command, output directory and the `/api` rewrite.
3. Put the live URL at the top of this README.

## Limitations

- One data source and national level only, as specified.
- The 09:00 deadline is an assumption.
- One winter month is a small sample; results should not be generalised to other seasons.
- The app quantifies forecast error but does not model demand or prices.
