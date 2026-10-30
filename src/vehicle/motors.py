"""Read single-motor RASP files without modifying the source data.

Format: https://www.thrustcurve.org/info/raspformat.html (header dimensions
in millimetres, masses in kg, samples in seconds/Newtons; implicit origin).
Impulse integrates piecewise-linear thrust exactly. Remaining propellant assumes
constant effective exhaust velocity, so depletion follows cumulative impulse.
This parser validates file structure; it does not establish motor certification.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class MotorCurve:
    designation: str
    diameter_m: float
    length_m: float
    delays: str
    propellant_mass_kg: float
    loaded_mass_kg: float
    manufacturer: str
    samples: NDArray[np.float64]

    @property
    def burn_time_s(self) -> float:
        return float(self.samples[-1, 0])

    @property
    def total_impulse_ns(self) -> float:
        return float(np.trapezoid(self.samples[:, 1], self.samples[:, 0]))

    @property
    def average_thrust_n(self) -> float:
        return self.total_impulse_ns / self.burn_time_s

    def thrust_n(self, time_s: float) -> float:
        if not np.isfinite(time_s):
            raise ValueError("time must be finite")
        return float(np.interp(time_s, self.samples[:, 0], self.samples[:, 1], left=0, right=0))

    def burned_fraction(self, time_s: float) -> float:
        if not np.isfinite(time_s):
            raise ValueError("time must be finite")
        t = min(max(time_s, 0), self.burn_time_s)
        earlier = self.samples[self.samples[:, 0] < t]
        points = np.vstack([earlier, [t, self.thrust_n(t)]])
        impulse = float(np.trapezoid(points[:, 1], points[:, 0]))
        return impulse / self.total_impulse_ns


def parse_rasp(text: str) -> MotorCurve:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith(";")
    ]
    if not lines:
        raise ValueError("empty RASP motor file")
    header = lines[0].split()
    if len(header) != 7:
        raise ValueError("RASP header needs seven fields")
    name, diameter, length, delays, propellant, loaded, manufacturer = header
    try:
        dimensions = np.array(
            [float(diameter) / 1000, float(length) / 1000, float(propellant), float(loaded)]
        )
        points = np.array([[float(v) for v in line.split()] for line in lines[1:]])
    except (ValueError, TypeError) as exc:
        raise ValueError("invalid numeric RASP data or multiple motor entries") from exc
    if not np.isfinite(dimensions).all() or np.any(dimensions <= 0):
        raise ValueError("RASP dimensions and masses must be finite and positive")
    if dimensions[2] >= dimensions[3]:
        raise ValueError("loaded mass must exceed propellant mass")
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 2:
        raise ValueError("RASP needs at least two time/thrust pairs")
    if not np.isfinite(points).all() or np.any(points < 0):
        raise ValueError("RASP samples must be finite and nonnegative")
    if np.any(np.diff(points[:, 0]) <= 0) or points[-1, 0] <= 0:
        raise ValueError("sample times must strictly increase")
    if points[-1, 1] != 0:
        raise ValueError("RASP must end at zero thrust")
    if points[0, 0] == 0:
        if points[0, 1] != 0:
            raise ValueError("explicit origin must have zero thrust")
    else:
        points = np.vstack([[0.0, 0.0], points])
    if np.any(points[1:-1, 1] <= 0):
        raise ValueError("zero thrust inside RASP burn interval")
    points.setflags(write=False)
    result = MotorCurve(
        name,
        float(dimensions[0]),
        float(dimensions[1]),
        delays,
        float(dimensions[2]),
        float(dimensions[3]),
        manufacturer,
        points,
    )
    if result.total_impulse_ns <= 0:
        raise ValueError("RASP impulse must be positive")
    return result


def load_rasp(path: str | Path) -> MotorCurve:
    return parse_rasp(Path(path).read_text(encoding="utf-8-sig"))
