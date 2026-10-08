"""UT-to-satellite elevation and slant range on a 1 s grid (skyfield)."""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
from skyfield.api import wgs84

from tracegen.config import TraceConfig


def start_time(ts, start_utc: str):
    return ts.from_datetime(datetime.fromisoformat(start_utc).replace(tzinfo=timezone.utc))


def elev_range(sats: list, cfg: TraceConfig, t_s: np.ndarray, ts) -> tuple[np.ndarray, np.ndarray]:
    t0 = start_time(ts, cfg.start_utc)
    times = ts.tt_jd(t0.tt + t_s / 86400.0)
    site = wgs84.latlon(cfg.lat_deg, cfg.lon_deg, elevation_m=cfg.alt_m)
    elev = np.empty((len(sats), len(t_s)))
    rng = np.empty((len(sats), len(t_s)))
    for k, sat in enumerate(sats):
        alt, _az, dist = (sat - site).at(times).altaz()
        elev[k] = alt.degrees
        rng[k] = dist.km
    return elev, rng
