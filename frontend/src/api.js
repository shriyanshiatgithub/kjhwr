// All network calls live here, so components never build URLs themselves.
const BASE = import.meta.env.VITE_API_URL ?? "";

async function get(path, params = {}, signal) {
  const qs = new URLSearchParams(params).toString();
  const res = await fetch(`${BASE}${path}${qs ? `?${qs}` : ""}`, { signal });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* body was not JSON; keep statusText */
    }
    throw new Error(`Request failed (${res.status}): ${detail}`);
  }
  return res.json();
}

export const api = {
  health: (signal) => get("/api/health", {}, signal),
  config: (signal) => get("/api/config", {}, signal),
  decisionDay: (deliveryDate, cutoffTime, signal) =>
    get("/api/decision-day", { delivery_date: deliveryDate, cutoff_time: cutoffTime }, signal),
  metrics: (first, last, cutoffTime, signal) =>
    get("/api/metrics", { first, last, cutoff_time: cutoffTime }, signal),
  horizonMetrics: (first, last, signal) => get("/api/horizon-metrics", { first, last }, signal),
};
