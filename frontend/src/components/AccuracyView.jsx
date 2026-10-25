import { Bar, CartesianGrid, ComposedChart, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api } from "../api";
import { bufferAdvice, fmtMW } from "../format";
import { useApi } from "../useApi";
import MetricCards from "./MetricCards";
import StatusBlock from "./StatusBlock";

/** Accuracy view: how wrong are the forecasts across the whole decision month? */
export default function AccuracyView({ range, cutoff }) {
  const overall = useApi((s) => api.metrics(range.min, range.max, cutoff, s), [range.min, range.max, cutoff]);
  const horizon = useApi((s) => api.horizonMetrics(range.min, range.max, s), [range.min, range.max]);

  const daily = (overall.data?.daily ?? []).map((d) => ({ day: d.date.slice(5), mae: d.mae, bias: d.bias }));
  const horizonRows = (horizon.data ?? []).map((h) => ({ ahead: `${h.horizon_hours}h`, mae: h.mae, rmse: h.rmse }));

  return (
    <section>
      <StatusBlock loading={overall.loading} error={overall.error}>
        {overall.data && (
          <>
            <div className="callout">
              Accuracy of the forecast that was available at each day's decision deadline, across all delivery days
              in the pilot month. {bufferAdvice(overall.data.overall)}
            </div>
            <div className="panel">
              <h2>Overall accuracy</h2>
              <MetricCards metrics={overall.data.overall} />
            </div>

            <div className="panel">
              <h2>Error by delivery day</h2>
              <p className="muted">Bars: average miss (MAE). Line: bias (above zero means forecasts were too high).</p>
              <div className="chart">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={daily} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" />
                    <XAxis dataKey="day" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} width={64} tickFormatter={(v) => v.toLocaleString("en-GB")} />
                    <Tooltip formatter={(v) => fmtMW(v)} />
                    <Legend />
                    <Bar dataKey="mae" name="MAE" fill="var(--c-forecast)" />
                    <Line type="monotone" dataKey="bias" name="Bias" stroke="var(--c-actual)" strokeWidth={2} dot={false} />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        )}
      </StatusBlock>

      <StatusBlock loading={horizon.loading} error={horizon.error}>
        {horizon.data && (
          <div className="panel">
            <h2>Does waiting for a later forecast help?</h2>
            <p className="muted">
              Error of the latest forecast available N hours before each half-hour. Smaller is better; the gap shows
              what a later decision deadline would be worth.
            </p>
            <div className="chart chart-short">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={horizonRows} margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--grid)" />
                  <XAxis dataKey="ahead" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} width={64} tickFormatter={(v) => v.toLocaleString("en-GB")} />
                  <Tooltip formatter={(v) => fmtMW(v)} />
                  <Legend />
                  <Line type="monotone" dataKey="mae" name="MAE" stroke="var(--c-forecast)" strokeWidth={2} />
                  <Line type="monotone" dataKey="rmse" name="RMSE" stroke="var(--c-actual)" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </StatusBlock>
    </section>
  );
}
