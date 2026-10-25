# Learning Guide: Wind Forecast Decision App

Read this once before the frontend. By the end you should be able to explain every design choice out loud.

## 1. The business problem in plain words

A UK electricity company must serve its customers' demand every half hour.
It buys power in advance on the **day-ahead market**. The purchase for a given day (the **delivery day**, D) must be decided on the day before (D-1), before the auction closes in the morning.

Wind power is free but unpredictable. The buyer reasons like this:

> Demand tomorrow at 14:00 is X. Wind will supply Y (forecast). So I need to buy X - Y from other sources, such as gas plants.

If the wind forecast is wrong, the buyer buys the wrong amount:
- **Wind over-forecast** (forecast > actual): too little bought, so the company is short and must cover the gap at a worse price.
- **Wind under-forecast** (forecast < actual): too much bought, so there is surplus power.

So the buyer needs two things from your app:
1. **What forecast did I actually have when I had to decide?** (Decision view)
2. **How wrong are these forecasts usually?** (Accuracy view)

## 2. The vocabulary

| Term | Meaning |
|---|---|
| Target time (`startTime`) | The half-hour the forecast or actual is about |
| Publish time (`publishTime`) | When the forecast was created. The same target time has many forecasts published at different times |
| Actual (FUELHH) | Metered wind generation that really happened, in MW |
| Forecast (WINDFOR) | Predicted wind generation, in MW |
| Cutoff | The moment the buyer must decide (assumed 09:00 UK on D-1) |
| Horizon | How far ahead of the target a forecast was published (publish 06:00 for a 14:00 target = 8 hours) |
| Error | forecast - actual. Positive = over-forecast |

## 3. The key idea: no peeking at the future

For each half-hour of delivery day D, the data holds many forecasts, each published at a different time.

The buyer only had the ones published **at or before the cutoff**. Among those, the **latest** one is the best information available.

If you used a forecast published after the cutoff, the forecasts would look more accurate than the buyer ever experienced. In data science this mistake is called **look-ahead bias** (or data leakage). The whole product is built to avoid it.

This is implemented in `backend/app/selection.py`:
- `decision_cutoff()` computes the deadline in UK local time, converted to UTC.
- `ForecastIndex.latest_published_by()` finds the latest forecast at or before a time, using a binary search (`bisect`).
- `decision_day_view()` builds the 48 half-hour rows for one delivery day.

The test `test_ignores_forecasts_published_after_cutoff` proves this. It plants a very different forecast published after the cutoff, and checks it is never used.

## 4. How error is quantified (`metrics.py`)

| Metric | Plain meaning | Why the buyer cares |
|---|---|---|
| MAE | Average size of the miss, in MW | Typical error to plan around |
| RMSE | Like MAE but punishes big misses more | Shows how bad the bad days are |
| Bias | Average signed error | Positive = forecasts tend to be too high (risk of shortfall) |
| P90 of abs error | 90% of half-hours missed by less than this | A planning buffer |
| P90 of signed error | Over-forecast exceeded this only 10% of the time | Size of the shortfall risk to hedge |
| MAPE | Percent error | Easy to read, but unstable when output is near zero, so zero-output periods are skipped |

**Accuracy by horizon** shows how error grows the further ahead the forecast was made. It answers: "Is it worth waiting for a later forecast?"

## 5. Architecture and why

```
Elexon API --(scripts/fetch_snapshot.py, run once)--> backend/data/snapshot.json
                                                        |
React frontend <--JSON-- FastAPI (routes -> service -> selection/metrics) <-- DataStore (in memory)
```

| Choice | Reason (say this in the video) |
|---|---|
| Snapshot file instead of calling Elexon live | January 2026 is history, so it never changes. Serverless deploys are slow and fragile with external calls, and the demo cannot break if Elexon is down |
| Layers: routes / service / pure logic | Business rules have no web code, so they are easy to test |
| Plain dataclasses, no pandas | Small, fast cold starts on Vercel, and every formula is readable |
| Cutoff is a request parameter | The assumption is visible and adjustable, not hidden |
| Missing forecast is `None`, never 0 | Zero would look like "no wind" and silently corrupt the metrics |
| Tests for edge cases | Clock-change days have 46 or 50 half-hours, and a forecast published exactly at the cutoff must count |

## 6. Files in `backend/app/`

| File | Job |
|---|---|
| `config.py` | Settings and assumptions in one place |
| `models.py` | `Forecast` and `DecisionPoint` data shapes |
| `elexon.py` | Download and parse Elexon data |
| `store.py` | Load the snapshot into memory |
| `selection.py` | The no-peeking forecast-selection logic |
| `metrics.py` | Error formulas |
| `service.py` | Combines the pieces into API answers |
| `main.py` | FastAPI routes and input validation |

## 7. Questions a tech lead might ask (practise answers)

1. Why not call Elexon on every request? (history is static, serverless limits)
2. What if two forecasts have the same publish time? (the sort is stable, so the later row in the data wins)
3. How do you handle clock changes? (we iterate in UTC across the local-day bounds)
4. What would you add with more time? (auth, caching, forecast-vs-actual by hour of day, a live data refresh job, CI)
5. What are the limits of this analysis? (one data source, national level only, the cutoff is an assumption)

## 8. Honest limitations to state

- The 09:00 cutoff is an assumption, not an Elexon fact.
- Error metrics describe January 2026 only, and one winter month is a small sample.
- The app does not model demand or prices, so it quantifies forecast error but does not compute a cost.
