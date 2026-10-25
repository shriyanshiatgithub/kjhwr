import { fmtMW, fmtPct, fmtSigned } from "../format";

function Card({ label, value, hint }) {
  return (
    <div className="card">
      <div className="card-label">{label}</div>
      <div className="card-value">{value}</div>
      <div className="card-hint">{hint}</div>
    </div>
  );
}

/** The headline accuracy numbers, each with a plain-English explanation. */
export default function MetricCards({ metrics }) {
  if (!metrics || metrics.n === 0) {
    return <div className="status">No forecast/actual pairs available for this selection.</div>;
  }
  return (
    <div className="cards">
      <Card label="Average miss (MAE)" value={fmtMW(metrics.mae)} hint="Typical size of the forecast error" />
      <Card label="Big-miss measure (RMSE)" value={fmtMW(metrics.rmse)} hint="Like MAE, but punishes large errors" />
      <Card
        label="Bias"
        value={fmtSigned(metrics.bias)}
        hint={metrics.bias > 0 ? "Forecast too high on average (shortfall risk)" : "Forecast too low on average (surplus)"}
      />
      <Card label="90% of misses below" value={fmtMW(metrics.abs_error_p90)} hint="Use as a planning band" />
      <Card label="Shortfall buffer (P90)" value={fmtMW(Math.max(0, metrics.error_p90))} hint="Over-forecast exceeded only 10% of the time" />
      <Card label="Percent error (MAPE)" value={fmtPct(metrics.mape)} hint={`${metrics.n.toLocaleString("en-GB")} half-hours compared`} />
    </div>
  );
}
