import numpy as np

from tracegen.config import TraceConfig
from tracegen.profiles import MAIN_PROFILES, RULE_PROFILES, STRESS_PROFILES, all_profiles
from tracegen.trace import build_rows, calibrate_rtt

COLS = ["t_ms", "rtt_ms", "sat_id", "reconfig", "maneuver", "nosat", "loss_rt_pct"]


def _cfg(**kw) -> TraceConfig:
    base = dict(name="t", constellation="tle", tle_path="x.tle", start_utc="2026-09-20T00:00:00",
                duration_s=30, reconfig_outage_ms=100, loss_rt_pct=1.0)
    base.update(kw)
    return TraceConfig(**base)


def test_calibrate_rtt_hits_target_median() -> None:
    rtt, c = calibrate_rtt(np.array([8.0, 9.0, 10.0, np.nan]), 50.0)
    assert np.nanmedian(rtt) == 50.0 and c == 41.0


def test_build_rows_columns_and_outages() -> None:
    cfg = _cfg()
    t_s = np.arange(31.0)
    rtt = np.full(31, 50.0)
    sat = np.zeros(31, dtype=int)
    sat[20:] = 3
    df = build_rows(cfg, t_s, rtt, sat, boundaries_s=np.array([12.0, 27.0]), maneuver_starts_s=np.array([5.0]))
    assert list(df.columns) == COLS
    assert len(df) == 3000
    assert df.loc[df.t_ms == 12_000, "reconfig"].item() == 1
    assert df.loc[df.t_ms == 12_090, "reconfig"].item() == 1
    assert df.loc[df.t_ms == 12_100, "reconfig"].item() == 0
    assert df.loc[df.t_ms == 5_500, "maneuver"].item() == 1
    assert df.loc[df.t_ms == 12_050, "loss_rt_pct"].item() == 100.0
    assert df.loc[df.t_ms == 1_000, "loss_rt_pct"].item() == 1.0
    assert df.loc[df.t_ms == 25_000, "sat_id"].item() == 3


def test_nosat_rows_are_outage_with_held_rtt() -> None:
    cfg = _cfg()
    t_s = np.arange(31.0)
    rtt = np.full(31, 50.0)
    rtt[10] = np.nan
    sat = np.zeros(31, dtype=int)
    sat[10] = -1
    df = build_rows(cfg, t_s, rtt, sat, np.array([]), np.array([]))
    row = df.loc[df.t_ms == 10_000]
    assert row.nosat.item() == 1 and row.loss_rt_pct.item() == 100.0 and row.rtt_ms.item() == 50.0


def test_static_trace() -> None:
    cfg = TraceConfig(name="s", constellation="static", tle_path=None, start_utc="2026-09-20T00:00:00",
                      duration_s=10, static_rtt_ms=100.0, loss_rt_pct=0.0)
    df = build_rows(cfg, np.arange(11.0), np.full(11, 100.0), np.full(11, -1), np.array([]), np.array([]))
    assert df.rtt_ms.eq(100.0).all() and df.loss_rt_pct.eq(0.0).all() and df.nosat.eq(0).all()


def test_profile_counts() -> None:
    assert len(MAIN_PROFILES) == 4 and len(RULE_PROFILES) == 4 and len(STRESS_PROFILES) == 36
    names = [p.name() for p in all_profiles()]
    assert len(names) == len(set(names)) == 44
