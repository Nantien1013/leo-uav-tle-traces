"""Trace configuration and unit conversions."""
from __future__ import annotations

import math
from dataclasses import dataclass

RECONFIG_SECONDS: tuple[int, ...] = (12, 27, 42, 57)
SPEED_OF_LIGHT_KM_S: float = 299_792.458
_CONSTELLATIONS = ("tle", "hypatia550", "static")
_RULES = ("R1", "R2")


def per_direction_loss_pct(rt_pct: float) -> float:
    """Convert round-trip loss (ping-style) to the equivalent independent per-direction loss."""
    if not 0.0 <= rt_pct <= 100.0:
        raise ValueError(f"loss out of range: {rt_pct}")
    if rt_pct >= 100.0:
        return 100.0
    return 100.0 * (1.0 - math.sqrt(1.0 - rt_pct / 100.0))


@dataclass(frozen=True)
class TraceConfig:
    name: str
    constellation: str
    tle_path: str | None
    start_utc: str
    duration_s: int = 1800
    step_ms: int = 10
    lat_deg: float = 37.5079
    lon_deg: float = 15.0830
    alt_m: float = 20.0
    min_elev_deg: float | None = 25.0
    max_gsl_m: float | None = None
    rule: str = "R1"
    reconfig_outage_ms: int = 100
    target_median_rtt_ms: float = 50.0
    loss_rt_pct: float = 1.0
    maneuver_per_min: float = 0.0
    maneuver_outage_s: float = 1.0
    static_rtt_ms: float | None = None
    seed: int = 1

    def __post_init__(self) -> None:
        if self.constellation not in _CONSTELLATIONS:
            raise ValueError(f"unknown constellation {self.constellation}")
        if self.rule not in _RULES:
            raise ValueError(f"unknown rule {self.rule}")
        if self.constellation == "static" and self.static_rtt_ms is None:
            raise ValueError("static trace needs static_rtt_ms")
        if self.constellation != "static" and self.tle_path is None:
            raise ValueError("non-static trace needs tle_path")
        if self.step_ms <= 0 or 1000 % self.step_ms != 0:
            raise ValueError("step_ms must divide 1000")
