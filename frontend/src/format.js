// Pure helpers: formatting and small calculations. Unit-tested in format.test.js.

export const fmtMW = (v) => (v == null ? "-" : `${Math.round(v).toLocaleString("en-GB")} MW`);

export const fmtSigned = (v) =>
  v == null ? "-" : `${v > 0 ? "+" : v < 0 ? "-" : ""}${Math.abs(Math.round(v)).toLocaleString("en-GB")} MW`;

export const fmtPct = (v) => (v == null ? "-" : `${v.toFixed(1)}%`);

/** "HH:mm" in UK local time, from an ISO timestamp. */
export function ukTime(iso) {
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/London",
  }).format(new Date(iso));
}

/** "Fri 9 Jan, 09:00" in UK local time. */
export function ukDateTime(iso) {
  return new Intl.DateTimeFormat("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "Europe/London",
  }).format(new Date(iso));
}

/** Energy in MWh from half-hourly MW readings (each reading covers 0.5 h). Nulls are skipped. */
export function energyMWh(values) {
  return values.reduce((sum, v) => (v == null ? sum : sum + v * 0.5), 0);
}

/** Turn API points into chart rows. Missing forecasts stay null so the line shows a gap. */
export function toChartRows(points) {
  return points.map((p) => ({
    time: ukTime(p.start_time),
    forecast: p.forecast,
    actual: p.actual,
    error: p.error,
  }));
}

/** One plain-English sentence a buyer can act on. */
export function bufferAdvice(m) {
  if (!m || m.n === 0 || m.error_p90 == null) return "Not enough data to suggest a buffer.";
  const buffer = Math.max(0, Math.round(m.error_p90));
  const bias =
    m.bias > 0 ? "Forecasts tended to be too high" : m.bias < 0 ? "Forecasts tended to be too low" : "No overall bias";
  return `${bias}. In 90% of half-hours, wind was over-forecast by no more than ${buffer.toLocaleString(
    "en-GB"
  )} MW - a sensible reserve to plan for.`;
}
