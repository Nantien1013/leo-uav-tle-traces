"""Build every trace in profiles.all_profiles(); geometry is computed once per constellation."""
from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from skyfield.api import load

from tracegen.config import SPEED_OF_LIGHT_KM_S, TraceConfig
from tracegen.events import poisson_starts_s
from tracegen.geometry import elev_range
from tracegen.hypatia_tles import write_starlink550
from tracegen.profiles import all_profiles, to_config
from tracegen.satellites import load_satellites, mean_altitude_km
from tracegen.selection import reconfig_boundaries, select_satellites
from tracegen.trace import build_rows, calibrate_rtt

logger = logging.getLogger(__name__)


def _unix(start_utc: str) -> float:
    return datetime.fromisoformat(start_utc).replace(tzinfo=timezone.utc).timestamp()


def build_one(cfg: TraceConfig, geo: dict | None, out_dir: Path) -> dict:
    t_s = np.arange(cfg.duration_s + 1, dtype=float)
    rng = np.random.default_rng(cfg.seed)
    meta: dict = {"name": cfg.name, "config": cfg.__dict__}
    if cfg.constellation == "static":
        rtt_1s = np.full(t_s.size, cfg.static_rtt_ms, dtype=float)
        sat_1s = np.full(t_s.size, -1, dtype=np.int64)
        boundaries = np.array([], dtype=float)
    else:
        elev, rng_km, sats = geo["elev"], geo["range"], geo["sats"]
        if cfg.min_elev_deg is not None:
            visible = elev >= cfg.min_elev_deg
        else:
            visible = rng_km * 1000.0 <= cfg.max_gsl_m
        boundaries = reconfig_boundaries(_unix(cfg.start_utc), cfg.duration_s)
        sat_1s = select_satellites(visible, elev, t_s, boundaries, cfg.rule)
        r = np.where(sat_1s >= 0, rng_km[np.maximum(sat_1s, 0), np.arange(t_s.size)], np.nan)
        prop_ms = 4.0 * r / SPEED_OF_LIGHT_KM_S * 1000.0
        rtt_1s, c = calibrate_rtt(prop_ms, cfg.target_median_rtt_ms)
        used = np.unique(sat_1s[sat_1s >= 0])
        alts = np.array([mean_altitude_km(sats[i]) for i in used])
        changes = np.flatnonzero(np.diff(sat_1s) != 0) + 1
        meta.update({
            "constant_offset_ms": c,
            "n_sats_loaded": len(sats),
            "n_sats_used": int(used.size),
            "selected_alt_km_p5_p50_p95": np.percentile(alts, [5, 50, 95]).round(1).tolist(),
            "sat_changes": int(changes.size),
            "sat_changes_at_boundaries": int(np.isin(t_s[changes], np.ceil(boundaries)).sum()),
            "nosat_fraction_1s": float(np.mean(sat_1s < 0)),
            "prop_rtt_ms_p5_p50_p95": np.nanpercentile(prop_ms, [5, 50, 95]).round(2).tolist(),
        })
    man = poisson_starts_s(cfg.duration_s, cfg.maneuver_per_min, cfg.maneuver_outage_s, rng)
    df = build_rows(cfg, t_s, rtt_1s, sat_1s, boundaries, man)
    df.to_csv(out_dir / f"{cfg.name}.csv", index=False, lineterminator="\n")
    meta.update({
        "rows": len(df),
        "rtt_ms_p5_p50_p95": np.percentile(df.rtt_ms, [5, 50, 95]).round(2).tolist(),
        "n_boundaries": int(boundaries.size),
        "maneuver_count": int(man.size),
        "maneuver_expected": cfg.maneuver_per_min * cfg.duration_s / 60.0,
        "outage_fraction": float(np.mean(df.loss_rt_pct >= 100.0)),
    })
    (out_dir / f"{cfg.name}.meta.json").write_text(json.dumps(meta, indent=2, default=str))
    return meta


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--tle", required=True)
    ap.add_argument("--start-utc", required=True, help="e.g. 2026-09-20T00:00:00 (within a day of the TLE epoch)")
    ap.add_argument("--out", default="data/traces")
    ap.add_argument("--only", default=None, help="build only the trace with this name")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    hyp_path = "data/tle/hypatia-starlink550.txt"
    if not Path(hyp_path).exists():
        write_starlink550(hyp_path)
    ts = load.timescale()
    cfgs = [to_config(p, args.tle, hyp_path, args.start_utc) for p in all_profiles()]
    if args.only:
        cfgs = [c for c in cfgs if c.name == args.only]
    geo_cache: dict[tuple, dict] = {}
    for cfg in cfgs:
        geo = None
        if cfg.constellation != "static":
            key = (cfg.tle_path, cfg.start_utc, cfg.duration_s)
            if key not in geo_cache:
                logger.info("geometry for %s", key)
                sats = load_satellites(cfg.tle_path, ts)
                elev, rng_km = elev_range(sats, cfg, np.arange(cfg.duration_s + 1, dtype=float), ts)
                geo_cache[key] = {"elev": elev, "range": rng_km, "sats": sats}
            geo = geo_cache[key]
        meta = build_one(cfg, geo, out)
        logger.info("%s rtt p5/p50/p95=%s outage=%.4f", cfg.name, meta["rtt_ms_p5_p50_p95"], meta["outage_fraction"])


if __name__ == "__main__":
    main()
