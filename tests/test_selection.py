import numpy as np

from tracegen.selection import reconfig_boundaries, remaining_visible, select_satellites


def test_boundaries_follow_12_27_42_57() -> None:
    t0 = 1_000_000_020.0 + 20.0  # 20 s past a whole minute (1_000_000_020 is divisible by 60)
    b = reconfig_boundaries(t0_unix_s=t0, duration_s=60)
    assert list(b) == [7.0, 22.0, 37.0, 52.0]  # :27, :42, :57, then :12 of the next minute


def test_remaining_visible() -> None:
    v = np.array([[1, 1, 0, 1], [0, 1, 1, 1]], dtype=bool)
    assert remaining_visible(v).tolist() == [[2, 1, 0, 1], [0, 3, 2, 1]]


def _toy():
    t = np.arange(10.0)
    vis = np.zeros((2, 10), dtype=bool)
    vis[0, 0:7] = True           # high but short-lived
    vis[1, :] = True             # lower but long-lived
    elev = np.where(vis, 0.0, -90.0)
    elev[0, 0:7] = 80.0
    elev[1, :] = 40.0
    return t, vis, elev


def test_r1_highest_elevation_reselects_at_boundary_and_on_loss() -> None:
    t, vis, elev = _toy()
    sel = select_satellites(vis, elev, t, np.array([5.0]), "R1")
    assert sel.tolist() == [0, 0, 0, 0, 0, 0, 0, 1, 1, 1]


def test_r2_longest_remaining_visibility() -> None:
    t, vis, elev = _toy()
    sel = select_satellites(vis, elev, t, np.array([5.0]), "R2")
    assert sel.tolist() == [1] * 10


def test_no_satellite_gives_minus_one() -> None:
    t = np.arange(3.0)
    vis = np.zeros((1, 3), dtype=bool)
    sel = select_satellites(vis, np.zeros((1, 3)), t, np.array([]), "R1")
    assert sel.tolist() == [-1, -1, -1]
