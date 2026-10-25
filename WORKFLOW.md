# Workflow: Wind Forecast Decision App (budget: 16 hours)

Tick each box as you go. Every stage ends with something you can run or show.

## Stage 0: Understand the problem (30 min)
- [ ] Read the brief twice. Write in one sentence what the buyer must decide each day.
- [ ] Learn 4 terms: day-ahead market, delivery day, publish time vs target time, forecast error.
- [ ] Decide your cutoff assumption (default 09:00 UK on D-1) and write it down.

## Stage 1: Project setup (45 min)
- [ ] Create folders: backend/, frontend/, scripts/, a README.
- [ ] Python venv + `pip install -r backend/requirements-dev.txt`.
- [ ] `git init`, first commit. Commit small and often (reviewers read history).

## Stage 2: Get the real data (1 hr)
- [ ] Run `python scripts/fetch_snapshot.py` on your laptop (needs internet).
- [ ] Open backend/data/snapshot.json. Check: field names, row counts, timestamps in UTC.
- [ ] If the script errors, compare parameter names with the Elexon docs and fix elexon.py.
- [ ] Sanity check: ~48 actuals per day; several forecast publish times per target.

## Stage 3: Backend logic (2-3 hrs) [DONE: starter code and tests exist]
- [ ] Read selection.py, metrics.py, service.py, main.py in that order.
- [ ] Run `cd backend && python -m pytest`. All tests should pass.
- [ ] Run `uvicorn app.main:app --reload`, open http://localhost:8000/docs, try every endpoint.
- [ ] Spot-check one day by hand against the raw snapshot.

## Stage 4: Frontend (4-5 hrs)
- [ ] `npm create vite@latest frontend -- --template react`, add a charting library (Recharts).
- [ ] Page 1, Decision view: date picker + cutoff input, chart of forecast vs actual, cutoff and publish time shown clearly.
- [ ] Page 2, Accuracy view: metric cards (MAE, RMSE, bias, P90), daily error chart, error by horizon chart.
- [ ] Loading, empty and error states for every fetch.
- [ ] Keep API calls in one file (api.js) and state in hooks, not scattered in components.

## Stage 5: Polish and edge cases (1-2 hrs)
- [ ] Missing forecasts shown as gaps, not zeros.
- [ ] Plain-language labels ("Wind was over-forecast: you may be short").
- [ ] Responsive layout, readable axes with units (MW).

## Stage 6: Docker and deploy (2 hrs)
- [ ] Dockerfile for backend and frontend, plus docker-compose.yml; test `docker compose up`.
- [ ] Deploy to Vercel (frontend + FastAPI), set the API URL as an env var.
- [ ] Open the live URL in an incognito window and test it end to end.

## Stage 7: README and repo (1 hr)
- [ ] README: file/directory guide, how to run, live link, AI-tools disclosure.
- [ ] Public GitHub repo with an anonymous name. Check no secrets are committed.

## Stage 8: Video, max 10 min (2-3 hrs)
- [ ] Write a short script for each part. Practise once.
- [ ] Part 1 (customer, about 5 min): the problem, the decision view, the accuracy view, what to do with the error numbers.
- [ ] Part 2 (tech lead, about 5 min): architecture, the "latest forecast before cutoff" rule, tests, trade-offs, what you'd do next.
- [ ] Upload as unlisted on YouTube. Test the link in incognito.

## Stage 9: Submit
- [ ] Open every URL in incognito, then fill in the form.
