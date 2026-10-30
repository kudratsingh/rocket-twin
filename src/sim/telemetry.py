"""Parquet export of physics telemetry; the frontend never recomputes a flight.

Axes are NED, height AGL, quaternion wxyz, body rates xyz, SI units throughout.
Large trajectories remain ignored; committed records carry configuration hashes.
Reference: ADR-0001 and the Apache Arrow Parquet format specification.
No resampling of the numerical solution is hidden in this export.
"""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray


def write_parquet(path: Path, rows: NDArray[np.float64]) -> None:
    import pyarrow as pa
    import pyarrow.parquet as pq

    names = [
        "time_s",
        "north_m",
        "east_m",
        "down_m",
        "vn_mps",
        "ve_mps",
        "vd_mps",
        "qw",
        "qx",
        "qy",
        "qz",
        "wx_rad_s",
        "wy_rad_s",
        "wz_rad_s",
        "mass_kg",
        "cg_station_m",
        "thrust_n",
        "mach",
        "alpha_rad",
        "dynamic_pressure_pa",
        "specific_x_mps2",
        "specific_y_mps2",
        "specific_z_mps2",
        "gimbal_pitch_rad",
        "gimbal_yaw_rad",
        "landed",
    ]
    pq.write_table(pa.table({name: rows[:, i] for i, name in enumerate(names)}), path)
