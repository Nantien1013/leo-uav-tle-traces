"""Every trace the experiment matrix needs, named deterministically."""
from __future__ import annotations

from dataclasses import dataclass

from tracegen.config import TraceConfig
from tracegen.hypatia_tles import MAX_GSL_LENGTH_M


@dataclass(frozen=True)
class Profile:
    constellation: str
    rule: str = "R1"
    reconfig_ms: int = 100
    maneuver_per_min: float = 0.0
    loss_rt_pct: float = 1.0
    rtt_target_ms: float = 50.0
    static_rtt_ms: float | None = None

    def name(self) -> str:
        if self.constellation == "static":
            return f"static_rtt{self.static_rtt_ms:g}"
        prefix = "tle" if self.constellation == "tle" else "hyp"
        return (f"{prefix}_{self.rule}_rc{self.reconfig_ms}_mv{self.maneuver_per_min:g}"
                f"_l{self.loss_rt_pct:g}_rtt{self.rtt_target_ms:g}")


MAIN_PROFILES = [Profile("tle", "R1", rc, mv) for rc in (20, 100) for mv in (0.0, 1.0)]
RULE_PROFILES = [Profile("tle", "R2", rc, mv) for rc in (20, 100) for mv in (0.0, 1.0)]
STRESS_PROFILES = [
    Profile("tle", "R1", 100, mv, loss, rtt)
    for rtt in (50.0, 150.0, 300.0, 600.0) for loss in (1.0, 3.0, 10.0) for mv in (0.0, 1.0, 4.0)
]
STATIC_PROFILE = Profile("static", static_rtt_ms=100.0, loss_rt_pct=0.0)
HYPATIA_PROFILE = Profile("hypatia550", "R1", 100, 0.0)


def all_profiles() -> list[Profile]:
    seen: dict[str, Profile] = {}
    for p in [*MAIN_PROFILES, *RULE_PROFILES, *STRESS_PROFILES, STATIC_PROFILE, HYPATIA_PROFILE]:
        seen.setdefault(p.name(), p)
    return list(seen.values())


def to_config(p: Profile, tle_path: str, hyp_path: str, start_utc: str) -> TraceConfig:
    if p.constellation == "static":
        return TraceConfig(name=p.name(), constellation="static", tle_path=None, start_utc=start_utc,
                           static_rtt_ms=p.static_rtt_ms, loss_rt_pct=0.0, reconfig_outage_ms=0)
    if p.constellation == "hypatia550":
        return TraceConfig(name=p.name(), constellation="hypatia550", tle_path=hyp_path,
                           start_utc="2000-01-01T00:00:00", min_elev_deg=None, max_gsl_m=MAX_GSL_LENGTH_M,
                           rule=p.rule, reconfig_outage_ms=p.reconfig_ms, target_median_rtt_ms=p.rtt_target_ms,
                           loss_rt_pct=p.loss_rt_pct, maneuver_per_min=p.maneuver_per_min)
    return TraceConfig(name=p.name(), constellation="tle", tle_path=tle_path, start_utc=start_utc,
                       rule=p.rule, reconfig_outage_ms=p.reconfig_ms, target_median_rtt_ms=p.rtt_target_ms,
                       loss_rt_pct=p.loss_rt_pct, maneuver_per_min=p.maneuver_per_min)
