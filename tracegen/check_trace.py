"""G2: sanity-check every built trace from its meta.json. Exit code 1 if any check fails."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path


def check(meta: dict) -> list[str]:
    cfg = meta["config"]
    problems: list[str] = []
    if cfg["constellation"] != "static":
        p50 = meta["rtt_ms_p5_p50_p95"][1]
        if abs(p50 - cfg["target_median_rtt_ms"]) > 0.5:
            problems.append(f"median rtt {p50} != target {cfg['target_median_rtt_ms']}")
        if meta["constant_offset_ms"] <= 0:
            problems.append("negative constant offset")
        expected_b = cfg["duration_s"] / 15.0
        if abs(meta["n_boundaries"] - expected_b) > 1:
            problems.append(f"boundaries {meta['n_boundaries']} vs {expected_b}")
        if meta["nosat_fraction_1s"] > 0.01:
            problems.append(f"no-satellite fraction {meta['nosat_fraction_1s']:.3f}")
    exp = meta["maneuver_expected"]
    if abs(meta["maneuver_count"] - exp) > 3 * math.sqrt(max(exp, 1.0)) + (0 if exp else 0.5):
        problems.append(f"maneuver count {meta['maneuver_count']} vs expected {exp}")
    return problems


def main(trace_dir: str = "data/traces") -> int:
    bad = 0
    for f in sorted(Path(trace_dir).glob("*.meta.json")):
        meta = json.loads(f.read_text())
        probs = check(meta)
        extra = ""
        if "sat_changes" in meta:
            extra = (f" sats_used={meta['n_sats_used']}/{meta['n_sats_loaded']} changes={meta['sat_changes']}"
                     f" at_boundaries={meta['sat_changes_at_boundaries']} alt_km={meta['selected_alt_km_p5_p50_p95']}"
                     f" prop={meta['prop_rtt_ms_p5_p50_p95']} C={meta['constant_offset_ms']:.2f}")
        print(f"{'OK  ' if not probs else 'FAIL'} {meta['name']} rtt={meta['rtt_ms_p5_p50_p95']}"
              f" outage={meta['outage_fraction']:.4f}{extra}")
        for p in probs:
            print(f"     - {p}")
        bad += bool(probs)
    print(f"{bad} trace(s) failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
