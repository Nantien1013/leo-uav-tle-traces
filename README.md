# leo-uav-tle-traces

Link timelines for a UAV on a Starlink LEO link, built from a real Starlink TLE snapshot. This repository holds the
snapshot, the code that turns it into timelines, and the SHA-256 of every timeline used in the manuscript
*A TLE-Driven Testbed for Post-Quantum TLS on LEO UAV Control Links: Deadline-Based Establishment Success over Real
Starlink Orbits* (Y.-C. Wei and N.-T. Chen, submitted to Computer Networks).

The timelines themselves (about 230 MB) are not stored here. They rebuild byte-identically from the snapshot with
one command; `SHA256SUMS` lets you check that.

## Contents

| Path | What it is |
|---|---|
| `data/tle/starlink-20260919T0834Z.tle` | CelesTrak GP element sets of the Starlink group in TLE format, retrieved 2026-09-19 08:34 UTC, 10,699 satellites |
| `data/tle/starlink-20260919T0834Z.tle.sha256` | Its SHA-256 and the query URL |
| `data/tle/hypatia-starlink550.txt` | Synthetic TLEs of the Hypatia `starlink_550` shell (72 x 22 satellites, 550 km, 53 deg), the comparison constellation |
| `tracegen/` | Timeline generator (Python) |
| `tests/` | Unit tests for event scheduling, satellite selection and timeline rows |
| `SHA256SUMS` | SHA-256 of every timeline CSV and metadata file |

## Install

Tested with Python 3.14.8 and the pinned versions in `requirements.txt`; with them the timelines rebuild
byte-identically. Other versions of Skyfield, sgp4 or NumPy may change the last digits of `rtt_ms`.

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt        # Windows: .venv\Scripts\pip install -r requirements.txt
python -m pytest -q
```

## Rebuild the timelines

From the repository root:

```
python -m tracegen.build_all --tle data/tle/starlink-20260919T0834Z.tle --start-utc 2026-09-19T09:00:00 --out data/traces
sha256sum -c SHA256SUMS
```

This writes 44 timelines, each as `<name>.csv` plus `<name>.meta.json`. `--only <name>` builds a single one.
`python -m tracegen.check_trace data/traces` runs sanity checks on the metadata.

## What a timeline is

Each timeline is a 1,800 s link timeline at 10 ms resolution (180,000 rows) for a terminal near Catania
(37.5079 N, 15.083 E, 20 m). Every satellite in the snapshot is propagated with SGP4 (Skyfield) at every second;
a satellite is visible above 25 deg elevation (the Hypatia comparison timeline instead uses Hypatia's maximum
ground-to-satellite link length). The serving satellite is chosen at the Starlink reconfiguration
instants (seconds 12, 27, 42 and 57 of each UTC minute) by rule R1 (highest elevation) or R2 (longest remaining
visibility). The round-trip time is the propagation delay plus a constant offset that sets the median to the
target RTT. Reconfiguration gaps, maneuver outages (Poisson starts, 1 s each, seed 1) and a random round-trip loss
rate are added on top.

CSV columns:

| Column | Meaning |
|---|---|
| `t_ms` | Time since the start of the timeline (ms) |
| `rtt_ms` | Round-trip time (ms) |
| `sat_id` | NORAD id of the serving satellite |
| `reconfig` | 1 inside a reconfiguration gap |
| `maneuver` | 1 inside a maneuver outage |
| `nosat` | 1 if no satellite is visible |
| `loss_rt_pct` | Random round-trip loss rate (%) |

Names encode the parameters: `tle_R1_rc100_mv1_l3_rtt150` is the TLE constellation, rule R1, 100 ms
reconfiguration gap, 1 maneuver per minute, 3 % loss, 150 ms target median RTT.

## Which timelines the manuscript uses

| Experiment | Timelines |
|---|---|
| Main | `tle_R1_rc100_mv{0,1}_l1_rtt50` |
| Selection-rule check | `tle_R2_rc100_mv{0,1}_l1_rtt50` |
| Stress sweep | `tle_R1_rc100_mv{0,1,4}_l{1,3,10}_rtt{50,150,300,600}` (36) |
| Comparison constellation | `hyp_R1_rc100_mv0_l1_rtt50` |

The `rc20` timelines (20 ms reconfiguration gap) and `static_rtt100` are also built; the reported results use
only the 100 ms gap.

## Data sources

- **Starlink snapshot.** CelesTrak, "Starlink GP element sets in TLE format",
  https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=tle, retrieved 2026-09-19 08:34 UTC.
  CelesTrak serves only the current element sets, so this archived copy is what makes the timelines
  reproducible. It is redistributed unchanged for that purpose, with attribution to CelesTrak; it is not
  covered by this repository's MIT License.
- **Hypatia `starlink_550` shell.** Generated with code vendored unmodified from Hypatia
  (https://github.com/snkas/hypatia, MIT License, Copyright (c) 2020 ETH Zurich); see `tracegen/hypatia_tles.py`.

## License

Code: MIT, see `LICENSE`. Data: see "Data sources".

## Citation

See `CITATION.cff`. Please also cite the manuscript once it is published.
