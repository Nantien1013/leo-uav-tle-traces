"""Outage event processes: scheduled reconfiguration gaps and Poisson maneuver outages."""
from __future__ import annotations

import numpy as np


def poisson_starts_s(duration_s: int, per_min: float, dur_s: float, rng: np.random.Generator) -> np.ndarray:
    """Poisson arrivals at `per_min`; an arrival during an ongoing outage is skipped."""
    if per_min <= 0.0:
        return np.array([], dtype=float)
    starts: list[float] = []
    t = rng.exponential(60.0 / per_min)
    while t < duration_s:
        if not starts or t >= starts[-1] + dur_s:
            starts.append(t)
        t += rng.exponential(60.0 / per_min)
    return np.array(starts, dtype=float)


def interval_mask(n_rows: int, step_ms: int, starts_s: np.ndarray, dur_s: float) -> np.ndarray:
    """Rows r with start <= r*step < start + dur."""
    mask = np.zeros(n_rows, dtype=bool)
    dur_ms = int(round(dur_s * 1000.0))
    for s in starts_s:
        s_ms = int(round(float(s) * 1000.0))
        a = -(-s_ms // step_ms)
        b = -(-(s_ms + dur_ms) // step_ms)
        mask[max(a, 0):min(b, n_rows)] = True
    return mask
