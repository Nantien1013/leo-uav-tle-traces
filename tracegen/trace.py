"""Assemble the 10 ms trace from 1 s geometry and event processes."""
from __future__ import annotations

import numpy as np
import pandas as pd

from tracegen.config import TraceConfig
from tracegen.events import interval_mask

COLUMNS = ["t_ms", "rtt_ms", "sat_id", "reconfig", "maneuver", "nosat", "loss_rt_pct"]


def calibrate_rtt(prop_ms: np.ndarray, target_ms: float) -> tuple[np.ndarray, float]:
    c = float(target_ms - np.nanmedian(prop_ms))
    return prop_ms + c, c


def build_rows(
    cfg: TraceConfig,
    t_s: np.ndarray,
    rtt_1s_ms: np.ndarray,
    sat_1s: np.ndarray,
    boundaries_s: np.ndarray,
    maneuver_starts_s: np.ndarray,
) -> pd.DataFrame:
    n = cfg.duration_s * 1000 // cfg.step_ms
    t_ms = np.arange(n, dtype=np.int64) * cfg.step_ms
    held = pd.Series(rtt_1s_ms, dtype=float).ffill().bfill().to_numpy()
    rtt = np.interp(t_ms / 1000.0, t_s, held)
    idx = np.minimum((t_ms // 1000).astype(np.int64), len(sat_1s) - 1)
    sat = np.asarray(sat_1s)[idx]
    nosat = (sat < 0) & (cfg.constellation != "static")
    reconfig = interval_mask(n, cfg.step_ms, boundaries_s, cfg.reconfig_outage_ms / 1000.0)
    maneuver = interval_mask(n, cfg.step_ms, maneuver_starts_s, cfg.maneuver_outage_s)
    loss = np.where(reconfig | maneuver | nosat, 100.0, cfg.loss_rt_pct)
    return pd.DataFrame(
        {"t_ms": t_ms, "rtt_ms": np.round(rtt, 3), "sat_id": sat, "reconfig": reconfig.astype(int),
         "maneuver": maneuver.astype(int), "nosat": nosat.astype(int), "loss_rt_pct": loss},
        columns=COLUMNS,
    )
