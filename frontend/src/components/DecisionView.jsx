import { useMemo, useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import { bufferAdvice, fmtMW, fmtSigned, toChartRows, ukDateTime } from "../format";
import { useApi } from "../useApi";
import MetricCards from "./MetricCards";
import StatusBlock from "./StatusBlock";

/** Decision view: the forecast the buyer actually had on D-1, next to what really happened. */
export default function DecisionView({ range, cutoff }) {
  const [date, setDate] = useState(range.defaultDate);
  const { data, error, loading } = useApi((signal) => api.decisionDay(date, cutoff, signal), [date, cutoff]);

  const summary = useMemo(() => {
    if (!data) return null;
    const pubs = data.points.map((p) => p.publish_time).filter(Boolean).sort();
    // Energy totals must use the SAME periods on both sides, or the forecast looks artificially low.
    const paired = data.points.filter((p) => p.forecast != null && p.actual != null);
    return {
      rows: toChartRows(data.points),
      avgForecast: paired.length ? paired.reduce((t, p) => t + p.forecast, 0) / paired.length : null,
      avgActual: paired.length ? paired.reduce((t, p) => t + p.actual, 0) / paired.length : null,
      firstPub: pubs[0],
      lastPub: pubs[pubs.length - 1],
    };
  }, [data]);

  return (
    <section>
      <div className="controls">
        <label>
          Delivery day
          <input type="date" value={date} min={range.min} max={range.max} onChange={(e) => e.target.value && setDate(e.target.value)} />
        </label>
      </div>

      <StatusBlock loading={loading} error={error}>
        {data && summary && (
          <>
            <div className="callout">
              <strong>Decision deadline: {ukDateTime(data.decision_cutoff)} (UK).</strong> The forecast shown is the
              latest one published at or before that moment
              {summary.firstPub && (
                <>
                  {" "}
                  (versions published {ukDateTime(summary.firstPub)} to {ukDateTime(summary.lastPub)})
                </>
              )}
              . Actuals are shown for comparison only; the buyer would not have known them.
              {data.missing_forecast_periods > 0 && (
                <span className="warn">
                  {" "}
                  The forecast feed has no value for {data.missing_forecast_periods} of {data.points.length} half-hours,
                  so comparisons use the {data.metrics.n} periods that have both a forecast and an actual.
                </span>
              )}
            </div>

            <div className="panel">
              <h2>Forecast vs actual wind generation</h2>
              <div className="chart">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={summary.rows} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" />
                    <XAxis dataKey="time" interval={5} tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} width={64} tickFormatter={(v) => v.toLocaleString("en-GB")} label={{ value: "MW", angle: -90, position: "insideLeft", fontSize: 12 }} />
                    <Tooltip formatter={(v) => fmtMW(v)} />
                    <Legend />
                    <Line type="monotone" dataKey="forecast" name="Forecast (known at decision time)" stroke="var(--c-forecast)" strokeWidth={2} dot={{ r: 2 }} connectNulls />
                    <Line type="monotone" dataKey="actual" name="Actual (known afterwards)" stroke="var(--c-actual)" strokeWidth={2} dot={false} connectNulls={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="grid-2">
              <div className="panel">
                <h2>What this means for the purchase</h2>
                <dl className="facts">
                  <dt>Average forecast wind output</dt>
                  <dd>{fmtMW(summary.avgForecast)}</dd>
                  <dt>Average actual wind output</dt>
                  <dd>{fmtMW(summary.avgActual)}</dd>
                  <dt>Difference (forecast - actual)</dt>
                  <dd>{fmtSigned(data.metrics.bias)} on average ({data.metrics.bias > 0 ? "over-forecast: shortfall" : "under-forecast: surplus"})</dd>
                </dl>
                <p className="muted">{bufferAdvice(data.metrics)}</p>
              </div>
              <div className="panel">
                <h2>How accurate was this day?</h2>
                <MetricCards metrics={data.metrics} />
              </div>
            </div>
          </>
        )}
      </StatusBlock>
    </section>
  );
}
