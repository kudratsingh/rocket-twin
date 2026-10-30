"""Nominal interface fit and sampled combined-axis interference diagnostics.

BRep intersections check rigid envelopes; articulated rod ends are excluded only
inside explicit 4 mm joint spheres. Those purchased joints remain supplier-fit
requirements. The sweep is a finite pose test, not continuous-collision proof or
manufacturing qualification. A separate conservative cylindrical bound covers
motor/liner versus the aft shell over the entire commanded angular envelope.
Reference: rigid rotation preserves distance; triangle inequality bounds radial
excursion by r + axial lever*sin(pitch+yaw magnitude bound).
"""

from __future__ import annotations

import importlib
from typing import Any

cq: Any = importlib.import_module("cadquery")
import numpy as np

from src.cad.assembly import rigid_intersections
from src.cad.kinematics import linkage, pose
from src.vehicle.schema import Vehicle


def verify(vehicle: Vehicle, solids: dict[str, Any]) -> dict[str, Any]:
    ps = {p.id: p for p in vehicle.parts}
    radial_gap = (
        ps["aft_shell"].geometry["inner_radius_m"] - ps["interface_coupler"].geometry["radius_m"]
    ) * 1000
    interfaces = {
        "coupler_radial_gap_mm": radial_gap,
        "shell_stop_gap_mm": (
            ps["aft_shell"].position_m
            - (ps["body_upper"].position_m + ps["body_upper"].geometry["length_m"])
        )
        * 1000,
        "nominal_pin_radial_gap_mm": 0.2 if vehicle.tvc else None,
    }
    result: dict[str, Any] = {
        "interfaces": interfaces,
        "interface_passed": 0 < radial_gap <= 0.5,
        "sweep": None,
        "passed": 0 < radial_gap <= 0.5,
    }
    if not vehicle.tvc:
        return result
    limit = float(np.rad2deg(vehicle.tvc.max_deflection_rad))
    # Restrict to the actual aft mechanism; all upper rigid envelopes end before
    # the earliest moving bound, even after rotation.
    parts = [
        p
        for p in vehicle.parts
        if p.position_m >= 0.574
        and p.cad
        and p.cad.role not in ("distributed_budget", "soft_stowage")
    ]
    aft = vehicle.model_copy(update={"parts": parts})
    failures = []
    max_shaft = 0.0
    min_ratio = 1.0
    for pitch in np.linspace(-limit, limit, 5):
        for yaw in np.linspace(-limit, limit, 5):
            link = linkage(vehicle, pitch, yaw)
            max_shaft = max(max_shaft, *(abs(a["shaft_deg"]) for a in link["axes"]))
            jac = np.column_stack(
                [
                    (
                        np.array(
                            [a["shaft_deg"] for a in linkage(vehicle, pitch + dp, yaw + dy)["axes"]]
                        )
                        - np.array([a["shaft_deg"] for a in link["axes"]])
                    )
                    / 0.001
                    for dp, dy in [(0.001, 0), (0, 0.001)]
                ]
            )
            min_ratio = min(min_ratio, 1 / float(np.abs(jac).sum(axis=1).max()))
            posed = pose(vehicle, solids, pitch, yaw)
            joints = [point for a in link["axes"] for point in [a["start_mm"], a["end_mm"]]]
            for hit in rigid_intersections(aft, posed):
                intersection = posed[hit["a"]].intersect(posed[hit["b"]])
                # Only the pushrod and horn mating zones can be excluded.
                if "gimbal_links" in (hit["a"], hit["b"]):
                    for point in joints:
                        sphere = cq.Solid.makeSphere(4, cq.Vector(*point), angleDegrees1=-90)
                        if (
                            abs(intersection.Volume() - intersection.intersect(sphere).Volume())
                            < 1e-7
                        ):
                            intersection = None
                            break
                        intersection = intersection.cut(sphere)
                if intersection is not None and intersection.Volume() > 0.05:
                    failures.append(
                        {
                            "pitch_deg": float(pitch),
                            "yaw_deg": float(yaw),
                            **hit,
                            "outside_joint_mm3": intersection.Volume(),
                        }
                    )
    liner = ps["motor_liner"]
    front, back = liner.position_m, liner.position_m + liner.geometry["length_m"]
    lever = max(abs(front - vehicle.tvc.pivot_position_m), abs(back - vehicle.tvc.pivot_position_m))
    # For orthogonal nested rotations, cos(theta)=cos(pitch)*cos(yaw).
    # A cylinder's radial extent is <= its radius + lever*sin(theta).
    tilt_bound = np.arccos(np.cos(vehicle.tvc.max_deflection_rad) ** 2)
    excursion = liner.geometry["radius_m"] + lever * np.sin(tilt_bound)
    shell_clearance = (ps["aft_shell"].geometry["inner_radius_m"] - excursion) * 1000
    sweep = {
        "grid": "5 x 5 inclusive pitch/yaw; 25 poses",
        "axis_limit_deg": limit,
        "max_servo_travel_deg": max_shaft,
        "minimum_sampled_rate_ratio": min_ratio,
        "configured_conservative_rate_ratio": vehicle.tvc.linkage_ratio,
        "motor_liner_to_shell_continuous_bound_mm": shell_clearance,
        "intersections_outside_joint_zones": failures,
        "joint_zone_radius_mm": 4,
        "joint_fit_verified": False,
        "continuous_full_mechanism_verified": False,
        "passed": not failures
        and max_shaft < 60
        and shell_clearance > 0.5
        and vehicle.tvc.linkage_ratio <= min_ratio,
    }
    result.update(sweep=sweep, passed=result["interface_passed"] and sweep["passed"])
    return result
