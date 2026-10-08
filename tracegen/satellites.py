"""Load TLE files (CelesTrak 3-line or Hypatia format) into skyfield satellites."""
from __future__ import annotations

from skyfield.api import EarthSatellite

_MU_KM3_S2 = 398600.4418
_EARTH_RADIUS_KM = 6378.135


def load_satellites(path: str, ts) -> list[EarthSatellite]:
    with open(path, encoding="ascii") as f:
        lines = [l.rstrip() for l in f]
    sats: list[EarthSatellite] = []
    for i in range(len(lines) - 1):
        if lines[i].startswith("1 ") and lines[i + 1].startswith("2 "):
            name = lines[i - 1].strip() if i > 0 else f"sat{i}"
            sats.append(EarthSatellite(lines[i], lines[i + 1], name, ts))
    return sats


def mean_altitude_km(sat: EarthSatellite) -> float:
    n_rad_s = sat.model.no_kozai / 60.0
    a_km = (_MU_KM3_S2 / n_rad_s**2) ** (1.0 / 3.0)
    return a_km - _EARTH_RADIUS_KM
