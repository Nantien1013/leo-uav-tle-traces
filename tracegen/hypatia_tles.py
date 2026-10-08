# The MIT License (MIT)
#
# Copyright (c) 2020 ETH Zurich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Vendored from https://raw.githubusercontent.com/snkas/hypatia/master/satgenpy/satgen/tles/generate_tles_from_scratch.py
# (fetched 2026-09-19). Only generate_tles_from_scratch_manual and calculate_tle_line_checksum are kept, unmodified.


def generate_tles_from_scratch_manual(
        filename_out,
        constellation_name,
        num_orbits,
        num_sats_per_orbit,
        phase_diff,
        inclination_degree,
        eccentricity,
        arg_of_perigee_degree,
        mean_motion_rev_per_day
):

    with open(filename_out, "w+") as f_out:

        # First line:
        #
        # <number of orbits> <number of satellites per orbit>
        #
        f_out.write("%d %d\n" % (num_orbits, num_sats_per_orbit))

        # Each of the subsequent (number of orbits * number of satellites per orbit) blocks
        # define a satellite as follows:
        #
        # <constellation_name> <global satellite id>
        # <TLE line 1>
        # <TLE line 2>
        satellite_counter = 0
        for orbit in range(0, num_orbits):

            # Orbit-dependent
            raan_degree = orbit * 360.0 / num_orbits
            orbit_wise_shift = 0
            if orbit % 2 == 1:
                if phase_diff:
                    orbit_wise_shift = 360.0 / (num_sats_per_orbit * 2.0)

            # For each satellite in the orbit
            for n_sat in range(0, num_sats_per_orbit):
                mean_anomaly_degree = orbit_wise_shift + (n_sat * 360 / num_sats_per_orbit)

                # Epoch is 2000-01-01 00:00:00, which is 00001 in ddyyy format
                # See also: https://www.celestrak.com/columns/v04n03/#FAQ04
                tle_line1 = "1 %05dU 00000ABC 00001.00000000  .00000000  00000-0  00000+0 0    0" % (
                    satellite_counter + 1
                )

                tle_line2 = "2 %05d %s %s %s %s %s %s    0" % (
                    satellite_counter + 1,
                    ("%3.4f" % inclination_degree).rjust(8),
                    ("%3.4f" % raan_degree).rjust(8),
                    ("%0.7f" % eccentricity)[2:],
                    ("%3.4f" % arg_of_perigee_degree).rjust(8),
                    ("%3.4f" % mean_anomaly_degree).rjust(8),
                    ("%2.8f" % mean_motion_rev_per_day).rjust(11),
                )

                # Append checksums
                tle_line1 = tle_line1 + str(calculate_tle_line_checksum(tle_line1))
                tle_line2 = tle_line2 + str(calculate_tle_line_checksum(tle_line2))

                # Write TLE to file
                f_out.write(constellation_name + " " + str(orbit * num_sats_per_orbit + n_sat) + "\n")
                f_out.write(tle_line1 + "\n")
                f_out.write(tle_line2 + "\n")

                # One more satellite there
                satellite_counter += 1


def calculate_tle_line_checksum(tle_line_without_checksum):
    if len(tle_line_without_checksum) != 68:
        raise ValueError("Must have exactly 68 characters")
    s = 0
    for i in range(len(tle_line_without_checksum)):
        if tle_line_without_checksum[i].isnumeric():
            s += int(tle_line_without_checksum[i])
        if tle_line_without_checksum[i] == "-":
            s += 1
    return s % 10


# --- additions for this project (not part of the vendored Hypatia code) ---
# Constants copied verbatim from hypatia/paper/satellite_networks_state/main_starlink_550.py
import math as _math

EARTH_RADIUS = 6378135.0
ECCENTRICITY = 0.0000001
ARG_OF_PERIGEE_DEGREE = 0.0
PHASE_DIFF = True
MEAN_MOTION_REV_PER_DAY = 15.19
ALTITUDE_M = 550000
SATELLITE_CONE_RADIUS_M = 940700
MAX_GSL_LENGTH_M = _math.sqrt(_math.pow(SATELLITE_CONE_RADIUS_M, 2) + _math.pow(ALTITUDE_M, 2))
NUM_ORBS = 72
NUM_SATS_PER_ORB = 22
INCLINATION_DEGREE = 53


def write_starlink550(filename_out: str) -> None:
    """Write Hypatia's starlink_550 shell exactly as Hypatia parameterises it."""
    generate_tles_from_scratch_manual(
        filename_out, "Starlink-550", NUM_ORBS, NUM_SATS_PER_ORB, PHASE_DIFF,
        INCLINATION_DEGREE, ECCENTRICITY, ARG_OF_PERIGEE_DEGREE, MEAN_MOTION_REV_PER_DAY,
    )
