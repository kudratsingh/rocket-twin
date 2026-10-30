"""Rigid nested-gimbal geometry and fixed-length articulated pushrod closure.

CAD axes: yaw about +Y, inner pitch about +X, common pivot from YAML.
Servo horns rotate about the transverse axis at their fixed shaft. A scalar
root enforces each rod length, including both gimbal axes. This is geometric
closure, not a torque, backlash, hot-bearing or flexible-link qualification.
Reference: Shigley, Mechanical Engineering Design, linkage position analysis.
"""

from __future__ import annotations

import importlib
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
    assert links.cad
    pivot = np.array([0, 0, vehicle.tvc.pivot_position_m * 1000])
    rx, ry = rotation(pitch, yaw)
    results = []
    for i, (a, b) in enumerate(links.cad.parameters["segments_mm"]):
        a = np.array(a, dtype=float) + [0, 0, links.position_m * 1000]
        b = np.array(b, dtype=float) + [0, 0, links.position_m * 1000]
        servo = ps["servo_yaw" if i == 0 else "servo_pitch"]
        shaft = np.array(
            [servo.lateral_offset_m[0] * 1000, -servo.lateral_offset_m[1] * 1000, a[2]]
        )
        arm = a - shaft
        end = pivot + ry @ ((b - pivot) if i == 0 else rx @ (b - pivot))
        length = np.linalg.norm(b - a)

        def horn(angle: float, i: int = i, shaft: Any = shaft, arm: Any = arm) -> Any:
            rp, r_y = rotation(angle if i == 1 else 0, angle if i == 0 else 0)
            return shaft + (r_y if i == 0 else rp) @ arm

        theta = brentq(
            lambda angle, end=end, horn=horn, length=length: np.linalg.norm(end - horn(angle))
            - length,
            -60,
            60,
        )
        results.append(
            {
                "shaft_deg": theta,
                "start_mm": horn(theta).tolist(),
                "end_mm": end.tolist(),
                "shaft_mm": shaft.tolist(),
                "rod_length_mm": float(length),
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
