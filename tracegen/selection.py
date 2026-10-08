"""Serving-satellite selection at the global reconfiguration instants (rules R1/R2 are assumptions)."""
from __future__ import annotations

import math

import numpy as np

from tracegen.config import RECONFIG_SECONDS


def reconfig_boundaries(t0_unix_s: float, duration_s: int) -> np.ndarray:
    out: list[float] = []
    minute = math.floor(t0_unix_s / 60.0) * 60.0
    while minute < t0_unix_s + duration_s:
        for s in RECONFIG_SECONDS:
            t = minute + s - t0_unix_s
            if 0.0 <= t < duration_s:
                out.append(t)
        minute += 60.0
    return np.array(sorted(out), dtype=float)


def remaining_visible(visible: np.ndarray) -> np.ndarray:
    run = np.zeros(visible.shape, dtype=np.int64)
    run[:, -1] = visible[:, -1]
    for j in range(visible.shape[1] - 2, -1, -1):
        run[:, j] = (run[:, j + 1] + 1) * visible[:, j]
    return run


def select_satellites(
    visible: np.ndarray, elev: np.ndarray, t_s: np.ndarray, boundaries_s: np.ndarray, rule: str
) -> np.ndarray:
    """Pick one satellite per interval between boundaries; reselect early only if it drops out of view."""
    n_t = visible.shape[1]
    run = remaining_visible(visible)
    sel = np.full(n_t, -1, dtype=np.int64)
    starts = np.unique(np.concatenate(([0], np.searchsorted(t_s, boundaries_s, side="left")))).astype(np.int64)
    starts = starts[starts < n_t]
    ends = np.append(starts[1:], n_t)
    for a, b in zip(starts, ends):
        i = int(a)
        while i < b:
            cand = np.flatnonzero(visible[:, i])
            if cand.size == 0:
                i += 1
                continue
            key = elev[cand, i] if rule == "R1" else run[cand, i]
            s = int(cand[int(np.argmax(key))])
            stop = min(int(b), i + int(run[s, i]))
            sel[i:stop] = s
            i = stop
    return sel
