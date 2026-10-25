import { useMemo, useState } from "react";
import { api } from "./api";
import AccuracyView from "./components/AccuracyView";
import DecisionView from "./components/DecisionView";
import StatusBlock from "./components/StatusBlock";
import { useApi } from "./useApi";

function addDays(isoDate, n) {
  const d = new Date(`${isoDate}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + n);
  return d.toISOString().slice(0, 10);
}

export default function App() {
  const [tab, setTab] = useState("decision");
  const [cutoff, setCutoff] = useState(null); // null until config supplies the default
  const config = useApi((s) => api.config(s), []);
  const health = useApi((s) => api.health(s), []);

  // Decisions are made in January; each is for the NEXT day's delivery.
  const range = useMemo(() => {
    if (!config.data) return null;
    const min = addDays(config.data.decision_month_start, 1);
    const max = addDays(config.data.decision_month_end, 1);
    return { min, max, defaultDate: addDays(min, 13) };
  }, [config.data]);

  const activeCutoff = cutoff ?? config.data?.default_cutoff;
  const synthetic = health.data?.source?.toUpperCase().includes("SYNTHETIC");

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Wind Forecast Desk</h1>
          <p className="muted">GB day-ahead purchasing: what forecast did we have, and how far can we trust it?</p>
        </div>
        {activeCutoff && (
          <label className="cutoff">
            Decision deadline (UK time, day before)
            <input type="time" value={activeCutoff} onChange={(e) => e.target.value && setCutoff(e.target.value)} />
          </label>
        )}
      </header>

      {synthetic && (
        <div className="banner" role="alert">
          Showing SYNTHETIC demo data, not Elexon data. Run scripts/fetch_snapshot.py to load the real data.
        </div>
      )}

      <nav className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === "decision"} className={tab === "decision" ? "active" : ""} onClick={() => setTab("decision")}>
          Decision view
        </button>
        <button role="tab" aria-selected={tab === "accuracy"} className={tab === "accuracy" ? "active" : ""} onClick={() => setTab("accuracy")}>
          Forecast accuracy
        </button>
      </nav>

      <StatusBlock loading={config.loading} error={config.error}>
        {range && activeCutoff && (tab === "decision" ? <DecisionView range={range} cutoff={activeCutoff} /> : <AccuracyView range={range} cutoff={activeCutoff} />)}
      </StatusBlock>

      <footer className="footer">Source: Elexon BMRS (FUELHH actuals, WINDFOR forecasts), national wind generation, half-hourly.</footer>
    </div>
  );
}
