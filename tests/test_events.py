import numpy as np

from tracegen.events import interval_mask, poisson_starts_s


def test_interval_mask_rows() -> None:
    m = interval_mask(n_rows=20, step_ms=10, starts_s=np.array([0.05]), dur_s=0.03)
    assert np.flatnonzero(m).tolist() == [5, 6, 7]


def test_interval_mask_clips_at_end() -> None:
    m = interval_mask(n_rows=5, step_ms=10, starts_s=np.array([0.03]), dur_s=1.0)
    assert np.flatnonzero(m).tolist() == [3, 4]


def test_poisson_rate_and_zero() -> None:
    rng = np.random.default_rng(7)
    starts = poisson_starts_s(duration_s=36_000, per_min=1.0, dur_s=1.0, rng=rng)
    assert abs(len(starts) - 600) < 4 * np.sqrt(600)
    assert np.all(np.diff(starts) >= 1.0)
    assert len(poisson_starts_s(600, 0.0, 1.0, np.random.default_rng(1))) == 0
