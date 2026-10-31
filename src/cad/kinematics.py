"""Rigid nested-gimbal geometry and fixed-length articulated pushrod closure.

CAD axes: yaw about +Y, inner pitch about +X, common pivot from YAML.
Servo horns rotate about the transverse axis at their fixed shaft. A scalar
root enforces each rod length, including both gimbal axes. This is geometric
closure, not a torque, backlash, hot-bearing or flexible-link qualification.
Reference: Shigley, Mechanical Engineering Design, linkage position analysis.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

cq: Any = importlib.import_module("cadquery")
import numpy as np
from scipy.optimize import brentq

from src.vehicle.schema import Vehicle


def rotation(pitch: float, yaw: float) -> tuple[Any, Any]:
    p, y = np.deg2rad([pitch, yaw])
    rx = np.array([[1, 0, 0], [0, np.cos(p), -np.sin(p)], [0, np.sin(p), np.cos(p)]])
    ry = np.array([[np.cos(y), 0, np.sin(y)], [0, 1, 0], [-np.sin(y), 0, np.cos(y)]])
    return rx, ry


def linkage(vehicle: Vehicle, pitch: float, yaw: float) -> dict[str, Any]:
    assert vehicle.tvc
    ps = {p.id: p for p in vehicle.parts}
    links = ps["gimbal_links"]
    horns = ps["servo_horns"]
    assert links.cad and horns.cad
    pivot = np.array([0, 0, vehicle.tvc.pivot_position_m * 1000])
    rx, ry = rotation(pitch, yaw)
    results = []
    for i, (a, b) in enumerate(links.cad.parameters["segments_mm"]):
        a = np.array(a, dtype=float) + [0, 0, links.position_m * 1000]
        b = np.array(b, dtype=float) + [0, 0, links.position_m * 1000]
        # The manufactured horn declares the shaft and neutral tip. Inferring
        # shaft height from the rod tip silently moves a canted horn's shaft
        # and shortens its effective lever arm. Flat legacy horns are unchanged.
        shaft_local, tip_local = horns.cad.parameters["segments_mm"][i]
        offset = np.array(
            [
                horns.lateral_offset_m[0] * 1000,
                -horns.lateral_offset_m[1] * 1000,
                horns.position_m * 1000,
            ]
        )
        shaft = np.array(shaft_local, dtype=float) + offset
        tip = np.array(tip_local, dtype=float) + offset
        if not np.allclose(a, tip, rtol=0, atol=1e-7):
            raise ValueError("Rod neutral start must match the spec-owned servo-horn tip")
        arm = a - shaft
        end = pivot + ry @ ((b - pivot) if i == 0 else rx @ (b - pivot))
        length = np.linalg.norm(b - a)

        def horn(angle: float, i: int = i, shaft: Any = shaft, arm: Any = arm) -> Any:
            rp, r_y = rotation(angle if i == 1 else 0, angle if i == 0 else 0)
            return shaft + (r_y if i == 0 else rp) @ arm

        def closure(
            angle: float,
            end: Any = end,
            horn_fn: Callable[[float], Any] = horn,
            rod_length: float = float(length),
        ) -> float:
            return float(np.linalg.norm(end - horn_fn(angle)) - rod_length)

        alternatives: list[float] = []
        if abs(closure(0)) < 1e-10:
            theta = 0.0
        elif closure(-60) * closure(60) < 0:
            # Preserve the original monotone flat-horn solution and precision.
            theta = float(brentq(closure, -60, 60))
        else:
            # Canted arms can have two interior roots despite equal endpoint
            # signs. Select the assembly solution nearest neutral, and expose
            # ambiguity rather than claiming continuous branch validation.
            angles = np.linspace(-60, 60, 241)
            residuals = [closure(float(a)) for a in angles]
            for a0, a1, f0, f1 in zip(angles[:-1], angles[1:], residuals[:-1], residuals[1:]):
                if abs(f0) < 1e-10:
                    alternatives.append(float(a0))
                elif f0 * f1 < 0:
                    alternatives.append(float(brentq(closure, float(a0), float(a1))))
            if abs(residuals[-1]) < 1e-10:
                alternatives.append(float(angles[-1]))
            if not alternatives:
                raise ValueError("No fixed-length linkage solution within the ±60° model bounds")
            theta = min(alternatives, key=abs)
        results.append(
            {
                "shaft_deg": theta,
                "start_mm": horn(theta).tolist(),
                "end_mm": end.tolist(),
                "shaft_mm": shaft.tolist(),
                "rod_length_mm": float(length),
                "interior_solution_candidates_deg": alternatives,
                "continuous_branch_validation": "not established by an isolated pose",
            }
        )
    return {"axes": results}


def pose(vehicle: Vehicle, solids: dict[str, Any], pitch: float, yaw: float) -> dict[str, Any]:
    assert vehicle.tvc
    pivot = (0, 0, vehicle.tvc.pivot_position_m * 1000)
    out = {}
    for part in vehicle.parts:
        assert part.cad
        shape = solids[part.id]
        if part.cad.moving_group == "motor":
            shape = shape.rotate(pivot, (1, 0, pivot[2]), pitch)
        if part.cad.moving_group in ("motor", "yaw"):
            shape = shape.rotate(pivot, (0, 1, pivot[2]), yaw)
        out[part.id] = shape
    rods, horns = [], []
    for axis in linkage(vehicle, pitch, yaw)["axes"]:
        a, b, shaft = (np.array(axis[k]) for k in ["start_mm", "end_mm", "shaft_mm"])
        v = b - a
        rods.append(
            cq.Solid.makeCylinder(1, float(np.linalg.norm(v)), cq.Vector(*a), cq.Vector(*v))
        )
        h = a - shaft
        horns.append(
            cq.Solid.makeCylinder(
                1.5, float(np.linalg.norm(h)) - 1.6, cq.Vector(*shaft), cq.Vector(*h)
            )
        )
    out["gimbal_links"] = cq.Compound.makeCompound(rods)
    out["servo_horns"] = cq.Compound.makeCompound(horns)
    return out
