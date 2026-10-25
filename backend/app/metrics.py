"""Quantifying forecast error. Pure functions, no numpy, easy to test by hand.

Sign convention (important for a power buyer):
    error = forecast - actual
    error > 0  -> wind was OVER-forecast -> buyer under-bought -> must cover the gap later
    error < 0  -> wind was UNDER-forecast -> buyer over-bought  -> surplus power
"""
from __future__ import annotations

import math
from typing import Sequence


def percentile(values: Sequence[float], q: float) -> float:
    """Linear-interpolated percentile, q in [0, 100]. Matches numpy's default method."""
    if not values:
        raise ValueError("percentile of empty sequence")
    s = sorted(values)
    if len(s) == 1:
        return s[0]
    pos = (len(s) - 1) * q / 100
    lo, hi = math.floor(pos), math.ceil(pos)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def compute_metrics(pairs: Sequence[tuple[float, float]]) -> dict:
    """pairs = [(forecast, actual), ...] in MW. Returns {} fields as None when no data."""
    n = len(pairs)
    if n == 0:
        return {
            "n": 0, "mae": None, "rmse": None, "bias": None, "mape": None,
            "abs_error_p50": None, "abs_error_p90": None, "abs_error_p95": None,
            "error_p10": None, "error_p90": None,
        }
    errors = [f - a for f, a in pairs]
    abs_errors = [abs(e) for e in errors]
    pct = [abs(f - a) / a * 100 for f, a in pairs if a > 0]  # MAPE ignores zero-output periods
    return {
        "n": n,
        "mae": sum(abs_errors) / n,
        "rmse": math.sqrt(sum(e * e for e in errors) / n),
        "bias": sum(errors) / n,
        "mape": sum(pct) / len(pct) if pct else None,
        "abs_error_p50": percentile(abs_errors, 50),
        "abs_error_p90": percentile(abs_errors, 90),
        "abs_error_p95": percentile(abs_errors, 95),
        # 10% of half-hours were over-forecast by at least error_p90 MW (planning buffer)
        "error_p10": percentile(errors, 10),
        "error_p90": percentile(errors, 90),
    }
