"""Copy-only recovery-cap windows with original outward horns and real axes.

No earlier published study is edited. Actual 25-pose rod/horn geometry sizes
round axial windows; original shafts, six-mm arms, gimbal lugs and actuator
ratio stay unchanged. Local port-section screens do not qualify the newly
windowed annular load path. Required recovery/rail failures remain open.
References: src/cad/kinematics.py and the frozen WO-03 recovery studies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_recovery_budget_closure import force_case, rail_bounds, rounded_junction
from src.cad.assembly import rigid_intersections
from src.cad.kinematics import linkage, pose
from src.cad.parts import cq, local_shape, properties
from src.vehicle.benchmark import screen_launch
from src.vehicle.mass import mass_properties
from src.vehicle.schema import CADMass, load_vehicle, vehicle_input_paths


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def round_up(value: float, increment: float) -> float:
    return math.ceil(value / increment - 1e-12) * increment


def mechanism_solids(values: dict[str, Any], radius_extra: float = 0) -> tuple[Any, Any]:
    """Flat-end nominal cylinders, conservatively capped for sizing only."""
    start, end, shaft = [np.asarray(values[key]) for key in ("start_mm", "end_mm", "shaft_mm")]
    rod = cq.Solid.makeCylinder(
        1 + radius_extra,
        float(np.linalg.norm(end - start)),
        cq.Vector(*start),
        cq.Vector(*(end - start)),
    )
    arm = start - shaft
    horn_end = shaft + arm * (1 - 1.6 / np.linalg.norm(arm))
    horn = cq.Solid.makeCylinder(
        1.5 + radius_extra,
        float(np.linalg.norm(horn_end - shaft)),
        cq.Vector(*shaft),
        cq.Vector(*arm),
    )
    if radius_extra:
        for point in (start, end):
            rod = rod.fuse(
                cq.Solid.makeSphere(1 + radius_extra, cq.Vector(*point), angleDegrees1=-90)
            )
        for point in (shaft, horn_end):
            horn = horn.fuse(
                cq.Solid.makeSphere(1.5 + radius_extra, cq.Vector(*point), angleDegrees1=-90)
            )
    return rod, horn


def window_centers(cfg: dict[str, Any]) -> list[list[tuple[float, float]]]:
    return [
        [
            (
                group["radius_mm"] * math.cos(math.radians(angle)),
                group["radius_mm"] * math.sin(math.radians(angle)),
            )
            for angle in group["angles_deg"]
        ]
        for group in cfg["window_center_groups"]
    ]


def tolerance_budget(vehicle: Any, cfg: dict[str, Any]) -> dict[str, Any]:
    parts = {part.id: part for part in vehicle.parts}
    frame = parts["gimbal_frame"].engineering.tolerances_mm["linear"]
    hole_radius = cfg["window_sizing"]["diameter_tolerance_mm"] / 2
    rows = {}
    for name in ("gimbal_links", "servo_horns"):
        mechanism = parts[name].engineering.tolerances_mm["linear"]
        xyz = math.sqrt(3) * (frame + mechanism)
        rows[name] = {
            "frame_each_coordinate_mm": frame,
            "mechanism_each_coordinate_mm": mechanism,
            "cartesian_position_sum_bound_mm": xyz,
            "hole_radius_tolerance_mm": hole_radius,
            "required_nominal_clearance_mm": xyz
            + hole_radius
            + cfg["window_sizing"]["positive_clearance_reserve_mm"],
        }
    return {
        "policy": cfg["window_sizing"]["coordinate_policy"],
        "parts": rows,
        "joint_axis_angle_and_cable_uncertainty_covered": False,
    }


def derive_windows(vehicle: Any, cfg: dict[str, Any], tolerances: dict[str, Any]) -> dict[str, Any]:
    """Project conservative capsules only where they can enter cap material."""
    centers = window_centers(cfg)
    extent = math.degrees(vehicle.tvc.max_deflection_rad)
    start = cfg["frame_start_station_m"] * 1000
    slab = cq.Solid.makeCylinder(
        cfg["cap_outer_radius_mm"] + 5, cfg["cap_thickness_mm"], cq.Vector(0, 0, start)
    )
    inner = cq.Solid.makeCylinder(
        cfg["cap_inner_radius_mm"], cfg["cap_thickness_mm"] + 2, cq.Vector(0, 0, start - 1)
    )
    cap_material = slab.cut(inner)
    maximum = [0.0 for _ in centers]
    cloud_count = [0 for _ in centers]
    extents = []
    for pitch in np.linspace(-extent, extent, cfg["pose_grid_count_each_axis"]):
        for yaw in np.linspace(-extent, extent, cfg["pose_grid_count_each_axis"]):
            closed = linkage(vehicle, float(pitch), float(yaw))
            for axis, values in enumerate(closed["axes"]):
                for name, solid in zip(
                    ("gimbal_links", "servo_horns"),
                    mechanism_solids(
                        values, tolerances["parts"]["gimbal_links"]["required_nominal_clearance_mm"]
                    ),
                    strict=True,
                ):
                    # Use the larger rod/frame tolerance for both mechanisms.
                    section = solid.intersect(cap_material)
                    if section.Volume() < 1e-8:
                        continue
                    vertices, _ = section.tessellate(
                        cfg["window_sizing"]["projection_deflection_mm"], 0.1
                    )
                    points = np.asarray([[point.x, point.y] for point in vertices])
                    nearest = np.min(
                        np.linalg.norm(
                            points[:, None, :] - np.asarray(centers[axis])[None, :, :], axis=2
                        ),
                        axis=1,
                    )
                    maximum[axis] = max(maximum[axis], float(nearest.max()))
                    cloud_count[axis] += len(points)
                    radii = np.linalg.norm(points, axis=1)
                    extents.append(
                        {
                            "pitch_deg": float(pitch),
                            "yaw_deg": float(yaw),
                            "axis": axis,
                            "part": name,
                            "projected_radial_min_mm": float(radii.min()),
                            "projected_radial_max_mm": float(radii.max()),
                            "point_count": len(points),
                        }
                    )
    holes = []
    groups = []
    for axis, group in enumerate(cfg["window_center_groups"]):
        if cloud_count[axis] == 0:
            raise ValueError(f"No actual cap-envelope coverage for mechanism axis {axis}")
        radius = round_up(
            maximum[axis] + cfg["window_sizing"]["projection_roundoff_reserve_mm"],
            cfg["window_sizing"]["diameter_increment_mm"] / 2,
        )
        diameter = 2 * radius
        groups.append(
            {
                "axis": axis,
                "required_projection_radius_mm": maximum[axis],
                "diameter_mm": diameter,
                "projection_points": cloud_count[axis],
            }
        )
        for center, angle in zip(centers[axis], group["angles_deg"], strict=True):
            holes.append(
                {
                    "start_mm": [center[0], center[1], 0],
                    "axis": [0, 0, 1],
                    "diameter_mm": diameter,
                    "length_mm": cfg["cap_thickness_mm"],
                    "study_role": "rounded_link_window",
                    "mechanism_axis": axis,
                    "angle_deg": angle,
                    "center_radius_mm": group["radius_mm"],
                }
            )
    return {
        "holes": holes,
        "groups": groups,
        "projected_envelope": extents,
        "capsule_margin_includes_tolerances_and_positive_reserve": True,
        "between_grid_poses_proven": False,
    }


def derive_hoop(vehicle: Any, cfg: dict[str, Any], tolerances: dict[str, Any]) -> dict[str, Any]:
    """Check actual conservative rod/horn clearance behind the window band."""
    hoop = cfg["hoop"]
    start = hoop["start_station_m"] * 1000
    slab = cq.Solid.makeCylinder(
        cfg["cap_outer_radius_mm"] + 10, hoop["thickness_mm"], cq.Vector(0, 0, start)
    )
    extent = math.degrees(vehicle.tvc.max_deflection_rad)
    maximum = 0.0
    rows = []
    for pitch in np.linspace(-extent, extent, cfg["pose_grid_count_each_axis"]):
        for yaw in np.linspace(-extent, extent, cfg["pose_grid_count_each_axis"]):
            closed = linkage(vehicle, float(pitch), float(yaw))
            for axis, values in enumerate(closed["axes"]):
                for name, solid in zip(
                    ("gimbal_links", "servo_horns"),
                    mechanism_solids(
                        values, tolerances["parts"]["gimbal_links"]["required_nominal_clearance_mm"]
                    ),
                    strict=True,
                ):
                    intersection = solid.intersect(slab)
                    if intersection.Volume() < 1e-8:
                        continue
                    vertices, _ = intersection.tessellate(
                        cfg["window_sizing"]["projection_deflection_mm"], 0.1
                    )
                    radial = max(math.hypot(point.x, point.y) for point in vertices)
                    maximum = max(maximum, radial)
                    rows.append(
                        {
                            "pitch_deg": float(pitch),
                            "yaw_deg": float(yaw),
                            "axis": axis,
                            "part": name,
                            "conservative_outer_radius_mm": radial,
                        }
                    )
    if maximum <= 0:
        raise ValueError("No positive behind-cap mechanism envelope was evaluated")
    needed = round_up(
        maximum + cfg["window_sizing"]["projection_roundoff_reserve_mm"],
        hoop["inner_radius_increment_mm"],
    )
    selected = max(hoop["minimum_inner_radius_mm"], needed)
    if selected >= cfg["cap_outer_radius_mm"]:
        raise ValueError("Required behind-cap opening leaves no positive hoop width")
    return {
        "behind_cap_conservative_envelope_radius_mm": maximum,
        "required_inner_radius_from_envelope_mm": needed,
        "selected_inner_radius_mm": selected,
        "pose_envelopes": rows,
        "existing_cap_windows_unchanged": True,
        "hoop_start_station_m": hoop["start_station_m"],
        "thickness_mm": hoop["thickness_mm"],
        "minimum_thickness_mm": hoop["thickness_mm"] - hoop["thickness_tolerance_mm"],
        "manufacturing_route": hoop["route"],
    }


def frame_with_ports(
    frame: Any, cfg: dict[str, Any], windows: list[dict[str, Any]]
) -> tuple[Any, Any, list[dict[str, Any]]]:
    """Native axial holes, then identically drilled integral saddle additions."""
    part = frame.model_copy(deep=True)
    part.cad_mass = None
    if cfg["hoop"]["enabled"]:
        params = part.cad.parameters
        rings = list(
            zip(
                params["ring_stations_mm"],
                params["ring_thicknesses_mm"],
                params["ring_inner_radii_mm"],
                strict=True,
            )
        )
        rings.append(
            (
                (cfg["hoop"]["start_station_m"] - part.position_m) * 1000,
                cfg["hoop"]["thickness_mm"],
                cfg["hoop"]["selected_inner_radius_mm"],
            )
        )
        rings.sort()
        params["ring_stations_mm"], params["ring_thicknesses_mm"], params["ring_inner_radii_mm"] = (
            map(list, zip(*rings, strict=True))
        )
    ports = []
    for angle in cfg["port_group_angles_deg"]:
        cosine, sine = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        for sign in (-1, 1):
            x, y = cfg["port_x_mm"], sign * cfg["port_y_mm"]
            ports.append(
                {
                    "start_mm": [x * cosine - y * sine, x * sine + y * cosine, -1],
                    "axis": [0, 0, 1],
                    "diameter_mm": cfg["port_diameter_mm"],
                    "length_mm": max(
                        cfg["cap_thickness_mm"] + cfg["saddle_radius_mm"],
                        cfg["cap_thickness_mm"]
                        + (cfg["hoop"]["thickness_mm"] if cfg["hoop"]["enabled"] else 0),
                    )
                    + 2,
                    "study_role": "recovery_port",
                    "group_angle_deg": angle,
                }
            )
    part.cad.parameters["machining_holes"] = ports + windows
    part.cad.parameters["study_integral_rounded_saddles"] = {
        "group_angles_deg": cfg["port_group_angles_deg"],
        "x_mm": cfg["port_x_mm"],
        "radius_mm": cfg["saddle_radius_mm"],
        "length_mm": cfg["saddle_length_mm"],
        "cap_thickness_mm": cfg["cap_thickness_mm"],
    }
    part.cad.parameters.pop("study_recovery_anchor_operations", None)
    shape = local_shape(part)
    for angle in cfg["port_group_angles_deg"]:
        saddle = cq.Solid.makeCylinder(
            cfg["saddle_radius_mm"],
            cfg["saddle_length_mm"],
            cq.Vector(cfg["port_x_mm"] - cfg["saddle_length_mm"] / 2, 0, cfg["cap_thickness_mm"]),
            cq.Vector(1, 0, 0),
        ).rotate((0, 0, 0), (0, 0, 1), angle)
        for hole in ports + windows:
            saddle = saddle.cut(
                cq.Solid.makeCylinder(
                    hole["diameter_mm"] / 2,
                    hole["length_mm"],
                    cq.Vector(*hole["start_mm"]),
                    cq.Vector(*hole["axis"]),
                )
            )
        shape = shape.fuse(saddle)
    return part, shape.clean(), ports


def distance(a: Any, b: Any) -> float:
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape

    return float(BRepExtrema_DistShapeShape(a.wrapped, b.wrapped).Value())


def section_audit(
    shape: Any,
    uncut_shape: Any,
    ports: list[dict[str, Any]],
    windows: list[dict[str, Any]],
    cfg: dict[str, Any],
    aft_factored_n: float,
) -> dict[str, Any]:
    port_to_window = (
        min(
            math.dist(port["start_mm"][:2], hole["start_mm"][:2])
            - cfg["port_max_diameter_mm"] / 2
            - (hole["diameter_mm"] + cfg["window_sizing"]["diameter_tolerance_mm"]) / 2
            for port in ports
            for hole in windows
        )
        - 2 * math.sqrt(2) * 0.15
    )
    radial_outer_edge = (
        cfg["cap_outer_radius_mm"]
        - math.hypot(cfg["port_x_mm"], cfg["port_y_mm"])
        - cfg["port_max_diameter_mm"] / 2
    )
    pair_ligament = cfg["port_pitch_min_mm"] - cfg["port_max_diameter_mm"]
    outer_rim = min(
        cfg["cap_outer_radius_mm"] - hole["center_radius_mm"] - hole["diameter_mm"] / 2
        for hole in windows
    )
    # Conservative independent frame/feature dimensions for the remaining rim.
    outer_rim_min = outer_rim - 2 * 0.15 - cfg["window_sizing"]["diameter_tolerance_mm"] / 2
    thickness = cfg["cap_min_thickness_mm"]
    two_route_shear = (
        aft_factored_n / (2 * thickness * outer_rim_min) if outer_rim_min > 0 else None
    )
    local = {
        "one_leg_port_bearing_mpa": aft_factored_n / (2 * cfg["port_min_diameter_mm"] * thickness),
        "one_leg_local_pair_web_shear_mpa": aft_factored_n / (2 * thickness * pair_ligament),
        "one_leg_local_unsupported_bridge_bending_mpa": 1.5
        * aft_factored_n
        * cfg["port_pitch_max_mm"]
        / (pair_ligament * thickness**2),
    }
    minimum_width_for_two_routes = aft_factored_n / (
        2 * thickness * cfg["minimum_local_g11_hot_screen_mpa_estimate"]
    )
    removed = uncut_shape.cut(shape)
    protected = []
    for angle in cfg["port_group_angles_deg"]:
        strip = (
            cq.Workplane("XY")
            .box(
                cfg["cap_outer_radius_mm"] - cfg["cap_inner_radius_mm"],
                2 * cfg["port_y_mm"] + cfg["port_max_diameter_mm"],
                cfg["cap_thickness_mm"] + cfg["saddle_radius_mm"],
                centered=(True, True, False),
            )
            .val()
            .translate((cfg["port_x_mm"], 0, 0))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        protected.append(
            {
                "group_angle_deg": angle,
                "window_volume_removed_from_local_port_strip_mm3": removed.intersect(
                    strip
                ).Volume(),
            }
        )
    return {
        "valid": bool(shape.isValid()),
        "connected_solid_count": len(shape.Solids()),
        "port_pair_flat_ligament_min_mm": pair_ligament,
        "prior_required_pair_ligament_mm": 2 * cfg["rope_max_diameter_assumption_mm"],
        "nearest_port_to_window_ligament_min_mm": port_to_window,
        "port_outer_radial_edge_ligament_nominal_mm": radial_outer_edge,
        "port_outer_edge_min_independent_dimension_bound_mm": radial_outer_edge
        - 0.15
        - math.sqrt(2) * 0.15,
        "protected_port_strips": protected,
        "all_local_port_strips_unchanged_by_windows": all(
            row["window_volume_removed_from_local_port_strip_mm3"] < 1e-6 for row in protected
        ),
        "outer_continuous_rim_nominal_mm": outer_rim,
        "outer_rim_min_dimensional_bound_mm": outer_rim_min,
        "cap_min_thickness_mm": thickness,
        "local_proxy_demands": local,
        "local_port_proxy_screens_pass": local["one_leg_port_bearing_mpa"]
        <= cfg["minimum_local_g11_hot_screen_mpa_estimate"]
        and local["one_leg_local_pair_web_shear_mpa"]
        <= cfg["minimum_local_g11_hot_screen_mpa_estimate"]
        and local["one_leg_local_unsupported_bridge_bending_mpa"]
        <= cfg["local_bridge_hot_flexural_screen_mpa_estimate"],
        "equal_two_circumferential_routes_shear_proxy_mpa": two_route_shear,
        "minimum_rim_for_equal_two_route_25MPa_proxy_mm": minimum_width_for_two_routes,
        "additional_rim_needed_for_that_proxy_mm": max(
            0, minimum_width_for_two_routes - outer_rim_min
        ),
        "equal_two_route_proxy_pass": two_route_shear is not None
        and two_route_shear <= cfg["minimum_local_g11_hot_screen_mpa_estimate"],
        "global_annular_bending_load_share_or_joint_rating": None,
        "limitations": "Rotating ports between rails changes the global ring load path. Local hole/bridge proxies are inherited engineering estimates only; two-route shear assumes equal split and omits bending, stress concentrations and unequal reactions. No global cap strength pass follows.",
    }


def combined_hoop_sections(
    shape: Any,
    ports: list[dict[str, Any]],
    windows: list[dict[str, Any]],
    sections: dict[str, Any],
    cfg: dict[str, Any],
    aft_force: float,
) -> dict[str, Any]:
    """Net sections and geometric continuity, not an annular bending solution."""
    angles = sorted(
        set(
            [hole["angle_deg"] for hole in windows]
            + [
                math.degrees(math.atan2(port["start_mm"][1], port["start_mm"][0])) % 360
                for port in ports
            ]
            + cfg["port_group_angles_deg"]
        )
    )
    depth = cfg["cap_thickness_mm"] + cfg["hoop"]["thickness_mm"]
    rows = []
    strip_width = 0.05
    for angle in angles:
        strip = (
            cq.Workplane("XY")
            .box(
                cfg["cap_outer_radius_mm"] - cfg["cap_inner_radius_mm"],
                strip_width,
                depth,
                centered=(True, True, False),
            )
            .val()
            .translate(((cfg["cap_outer_radius_mm"] + cfg["cap_inner_radius_mm"]) / 2, 0, 0))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        section = shape.intersect(strip)
        area = section.Volume() / strip_width
        radial = np.array([math.cos(math.radians(angle)), math.sin(math.radians(angle)), 0])
        inertia = (
            float(radial @ np.asarray(cq.Shape.matrixOfInertia(section)) @ radial / strip_width)
            - area * strip_width**2 / 12
        )
        center, bounds = section.Center(), section.BoundingBox()
        modulus = inertia / max(center.z - bounds.zmin, bounds.zmax - center.z)
        rows.append(
            {
                "angle_deg": angle,
                "actual_net_area_mm2": area,
                "radial_axis_bending_I_mm4": inertia,
                "minimum_radial_axis_section_modulus_mm3": modulus,
            }
        )
    front_width = sections["outer_rim_min_dimensional_bound_mm"]
    hoop_width = cfg["cap_outer_radius_mm"] - cfg["hoop"]["selected_inner_radius_mm"] - 2 * 0.15
    hoop_thickness = cfg["hoop"]["thickness_mm"] - cfg["hoop"]["thickness_tolerance_mm"]
    window_floor = front_width * cfg["cap_min_thickness_mm"] + max(0, hoop_width) * hoop_thickness
    port_floor = (
        cfg["cap_outer_radius_mm"]
        - cfg["cap_inner_radius_mm"]
        - 2 * 0.15
        - cfg["port_max_diameter_mm"]
    ) * cfg["cap_min_thickness_mm"] + sections[
        "port_outer_edge_min_independent_dimension_bound_mm"
    ] * hoop_thickness
    floor = min(window_floor, port_floor)
    equal_shear = aft_force / (2 * floor) if floor > 0 else None
    one_route_shear = aft_force / floor if floor > 0 else None
    return {
        "critical_radial_BRep_sections": rows,
        "minimum_actual_critical_section_mm2": min(row["actual_net_area_mm2"] for row in rows),
        "front_minimum_rim_width_mm": front_width,
        "hoop_minimum_radial_width_mm": hoop_width,
        "hoop_minimum_axial_thickness_mm": hoop_thickness,
        "window_region_conservative_combined_area_mm2": window_floor,
        "port_region_conservative_combined_area_mm2": port_floor,
        "conservative_minimum_combined_area_mm2": floor,
        "minimum_shared_radial_material_at_cap_hoop_face_mm": min(front_width, hoop_width),
        "two_equal_circumferential_routes_proxy_mpa": equal_shear,
        "two_equal_route_25MPa_proxy_pass": equal_shear is not None
        and equal_shear <= cfg["minimum_local_g11_hot_screen_mpa_estimate"],
        "one_circumferential_route_proxy_mpa": one_route_shear,
        "one_route_25MPa_proxy_pass": one_route_shear is not None
        and one_route_shear <= cfg["minimum_local_g11_hot_screen_mpa_estimate"],
        "required_area_per_equal_route_at_25MPa_mm2": aft_force
        / (2 * cfg["minimum_local_g11_hot_screen_mpa_estimate"]),
        "required_area_for_one_route_at_25MPa_mm2": aft_force
        / cfg["minimum_local_g11_hot_screen_mpa_estimate"],
        "continuous_one_solid_geometry": bool(shape.isValid()) and len(shape.Solids()) == 1,
        "bond_or_interface_spring_added": False,
        "annular_bending_torsion_actual_reaction_share_and_interlaminar_strength": None,
        "load_flow": "Port/saddle -> intact8mmfront web -> continuousouterrim -> additionalcontinuousrearhoop -> existingthreeG11rails. Two-routeproxy assumes equal circumferentialsplit. Sectionarea andone-solidgeometry do not determine that split, bending or true manufactured laminate continuity.",
    }


def placed_solids(
    vehicle: Any, frame_shape: Any, cfg: dict[str, Any], old_cfg: dict[str, Any]
) -> dict[str, Any]:
    solids = {}
    for part in vehicle.parts:
        if part.id == "gimbal_frame":
            shape = frame_shape
        elif part.id == "fin_set":
            shape = cq.importers.importStep(old_cfg["trainer_fin_step"]).val()
        elif part.id == "recovery_junction":
            shape = rounded_junction(old_cfg)
        else:
            shape = local_shape(part)
        solids[part.id] = shape.translate(
            (
                part.lateral_offset_m[0] * 1000,
                -part.lateral_offset_m[1] * 1000,
                part.position_m * 1000,
            )
        )
    return solids


def motion_audit(
    vehicle: Any,
    frame_shape: Any,
    cfg: dict[str, Any],
    old_cfg: dict[str, Any],
    tolerances: dict[str, Any],
) -> dict[str, Any]:
    solids = placed_solids(vehicle, frame_shape, cfg, old_cfg)
    limit = math.degrees(vehicle.tvc.max_deflection_rad)
    rows = []
    minima = {
        "rod_to_cap_frame": math.inf,
        "horn_to_cap_frame": math.inf,
        "rod_to_cassette": math.inf,
        "rod_to_motor": math.inf,
        "rod_to_coupler": math.inf,
        "rod_to_horn": math.inf,
    }
    minimum_ratio = math.inf
    for pitch in np.linspace(-limit, limit, cfg["pose_grid_count_each_axis"]):
        for yaw in np.linspace(-limit, limit, cfg["pose_grid_count_each_axis"]):
            closed = linkage(vehicle, float(pitch), float(yaw))
            posed = pose(vehicle, solids, float(pitch), float(yaw))
            hits = rigid_intersections(
                vehicle,
                posed,
                moving_ids={"gimbal_frame", "gimbal_links", "servo_horns", "recovery_junction"},
            )
            outside = []
            endpoints = [
                point for axis in closed["axes"] for point in (axis["start_mm"], axis["end_mm"])
            ]
            for hit in hits:
                intersection = posed[hit["a"]].intersect(posed[hit["b"]])
                if "gimbal_links" in (hit["a"], hit["b"]):
                    for point in endpoints:
                        sphere = cq.Solid.makeSphere(
                            cfg["joint_zone_radius_mm"], cq.Vector(*point), angleDegrees1=-90
                        )
                        if (
                            abs(intersection.Volume() - intersection.intersect(sphere).Volume())
                            < 1e-7
                        ):
                            intersection = None
                            break
                        intersection = intersection.cut(sphere)
                if (
                    intersection is not None
                    and intersection.Volume() > cfg["intersection_reporting_threshold_mm3"]
                ):
                    outside.append(dict(hit, outside_joint_zone_mm3=intersection.Volume()))
            clearances = {}
            for label, a, b in (
                ("rod_to_cap_frame", "gimbal_links", "gimbal_frame"),
                ("horn_to_cap_frame", "servo_horns", "gimbal_frame"),
                ("rod_to_cassette", "gimbal_links", "motor_mount"),
                ("rod_to_motor", "gimbal_links", "motor"),
                ("rod_to_coupler", "gimbal_links", "interface_coupler"),
                ("rod_to_horn", "gimbal_links", "servo_horns"),
            ):
                clearances[label] = distance(posed[a], posed[b])
                minima[label] = min(minima[label], clearances[label])
            jac = np.column_stack(
                [
                    (
                        np.asarray(
                            [
                                axis["shaft_deg"]
                                for axis in linkage(vehicle, pitch + dp, yaw + dy)["axes"]
                            ]
                        )
                        - np.asarray([axis["shaft_deg"] for axis in closed["axes"]])
                    )
                    / 0.001
                    for dp, dy in ((0.001, 0), (0, 0.001))
                ]
            )
            minimum_ratio = min(minimum_ratio, 1 / float(np.abs(jac).sum(axis=1).max()))
            rows.append(
                {
                    "pitch_deg": float(pitch),
                    "yaw_deg": float(yaw),
                    "shaft_degrees": [axis["shaft_deg"] for axis in closed["axes"]],
                    "actual_arm_lengths_mm": [
                        float(np.linalg.norm(np.asarray(axis["start_mm"]) - axis["shaft_mm"]))
                        for axis in closed["axes"]
                    ],
                    "raw_changed_pair_intersections": hits,
                    "outside_joint_zone_intersections": outside,
                    "minimum_pair_clearances_mm": clearances,
                }
            )
    rod_required = tolerances["parts"]["gimbal_links"]["required_nominal_clearance_mm"]
    horn_required = tolerances["parts"]["servo_horns"]["required_nominal_clearance_mm"]
    return {
        "poses": rows,
        "pose_count": len(rows),
        "all_sampled_changed_pairs_outside_joint_zones_clear": all(
            not row["outside_joint_zone_intersections"] for row in rows
        ),
        "actual_minimum_pair_clearances_mm": minima,
        "rod_frame_scalar_tolerance_and_reserve_pass": minima["rod_to_cap_frame"] >= rod_required,
        "horn_frame_scalar_tolerance_and_reserve_pass": minima["horn_to_cap_frame"]
        >= horn_required,
        "minimum_sampled_kinematic_rate_ratio": minimum_ratio,
        "preserved_configured_rate_ratio": vehicle.tvc.linkage_ratio,
        "rate_ratio_model_screen_pass": minimum_ratio >= vehicle.tvc.linkage_ratio,
        "max_absolute_shaft_deg": max(abs(angle) for row in rows for angle in row["shaft_degrees"]),
        "maximum_arm_length_error_mm": max(
            abs(arm - 6) for row in rows for arm in row["actual_arm_lengths_mm"]
        ),
        "threshold_mm3": cfg["intersection_reporting_threshold_mm3"],
        "joint_policy": "Preserve raw contacts; subtract only the existing4mmrod-end neighborhoods for the separate nonjoint report. Joints remain unqualified.",
        "continuous_motion_or_full_tolerance_qualification": False,
    }


def run(config: Path, output: Path) -> dict[str, Any]:
    started = time.monotonic()
    cfg = yaml.safe_load(config.read_text())
    old_cfg_path = Path(cfg["frozen_budget_config"])
    old_cfg = yaml.safe_load(old_cfg_path.read_text())
    old_record_path = Path(cfg["frozen_budget_record"])
    old_record = json.loads(old_record_path.read_text())
    thin_path = Path(cfg["thin_reference_record"])
    if sha(thin_path) != cfg["thin_reference_record_sha256"]:
        raise ValueError("Preserved thin-rim record identity mismatch")
    thin = json.loads(thin_path.read_text())
    if not thin["inputs_unchanged"] or not thin["frozen_owned_files_unchanged"]:
        raise ValueError("Thin-rim reference did not preserve its inputs")
    for path, digest in thin["input_sha256_before"].items():
        if path.startswith("src/") and sha(Path(path)) != digest:
            raise ValueError(f"Reusable thin-rim geometry has changed source: {path}")
    old_mode = next(
        row for row in old_record["modes"] if row["vehicle"] == cfg["target_vehicle_id"]
    )
    old_copy_path = Path(old_mode["resolved_mass_copy"])
    vehicle = load_vehicle(old_copy_path)
    if (
        hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
        != old_mode["resolved_mass_copy_sha256"]
    ):
        raise ValueError("Published recovery mass copy identity mismatch")
    source_vehicle = load_vehicle(cfg["original_vehicle"])
    original_parts = {part.id: part for part in source_vehicle.parts}
    # Restore the known actual arm phase and both complete rod definitions.
    for index, part in enumerate(vehicle.parts):
        if part.id in ("servo_horns", "gimbal_links"):
            vehicle.parts[index] = original_parts[part.id].model_copy(deep=True)
    parts = {part.id: part for part in vehicle.parts}
    frame = parts["gimbal_frame"]
    if not math.isclose(frame.position_m, cfg["frame_start_station_m"]):
        raise ValueError("Copy does not have the required cap station")
    sources = {
        config,
        Path(__file__),
        old_cfg_path,
        old_record_path,
        old_copy_path,
        Path(old_cfg["trainer_fin_step"]),
        Path(old_cfg["trainer_construction_copy"]),
        thin_path,
        Path(thin["frame_step"]["path"]),
        Path(cfg["thin_source_script"]),
        Path(cfg["thin_source_config"]),
    }
    sources.update(Path(path) for path in cfg["frozen_owned_files"])
    sources.update(vehicle_input_paths(cfg["original_vehicle"]))
    sources.update(Path("src/cad").glob("*.py"))
    sources.update(Path("src/vehicle").glob("*.py"))
    before = {str(path): sha(path) for path in sorted(sources)}
    frozen_before = {path: sha(Path(path)) for path in cfg["frozen_owned_files"]}
    output.mkdir(parents=True, exist_ok=True)
    tolerances = tolerance_budget(vehicle, cfg)
    windows = thin["window_derivation"]
    hoop = derive_hoop(vehicle, cfg, tolerances)
    cfg["hoop"]["selected_inner_radius_mm"] = hoop["selected_inner_radius_mm"]
    _, uncut_shape, ports = frame_with_ports(frame, cfg, [])
    new_part, shape, _ = frame_with_ports(frame, cfg, windows["holes"])
    old_frame_g = frame.resolved_mass_kg * 1000
    new_part.cad_mass = CADMass.model_validate(properties(new_part, shape))
    new_part.mass_kg = shape.Volume() * 0.00185 / 1000
    vehicle.parts[vehicle.parts.index(frame)] = new_part
    new_frame_g = new_part.resolved_mass_kg * 1000
    frame_mass_delta_g = new_frame_g - old_frame_g
    cases = [
        force_case(vehicle, old_cfg, 5, "nominal_5mps"),
        force_case(vehicle, old_cfg, 20.4, "required_20p4mps"),
    ]
    aft = next(
        branch["factored_force_n"] for branch in cases[-1]["branches"] if branch["branch"] == "aft"
    )
    sections = section_audit(shape, uncut_shape, ports, windows["holes"], cfg, aft)
    combined = combined_hoop_sections(shape, ports, windows["holes"], sections, cfg, aft)
    thin_shape = cq.importers.importStep(thin["frame_step"]["path"]).val()
    cap_slab = cq.Solid.makeCylinder(cfg["cap_outer_radius_mm"] + 1, cfg["cap_thickness_mm"])
    old_front, new_front = thin_shape.intersect(cap_slab), shape.intersect(cap_slab)
    unchanged_front_difference = (
        old_front.cut(new_front).Volume() + new_front.cut(old_front).Volume()
    )
    motion = motion_audit(vehicle, shape, cfg, old_cfg, tolerances)
    recovery_increment = old_mode["recovery_increment_g"] + frame_mass_delta_g
    guide = []
    construction = load_vehicle(old_cfg["trainer_construction_copy"])
    for thermal in cfg["thermal_addition_cases_g"]:
        for rail_g in (0, old_cfg["package_a_rail_saving_g"]):
            mass = (
                mass_properties(construction).mass_kg
                + (recovery_increment + thermal - rail_g) / 1000
            )
            screens = [
                screen_launch(construction, dt, study_nominal_mass_kg=mass)
                for dt in cfg["guide_steps_s"]
            ]
            headroom = (
                next(
                    row["headroom_g"]
                    for row in old_record["guide_trade_cases"]
                    if row["thermal_addition_g"] == 0 and row["rail_saving_g_unadopted"] == 0
                )
                + rail_g
            )
            guide.append(
                {
                    "thermal_addition_g": thermal,
                    "rail_saving_hypothesis_g": rail_g,
                    "hypothetical_rail_hardware_adopted": False,
                    "mass_margin_g": headroom - recovery_increment - thermal,
                    "trial_nominal_mass_kg": mass,
                    "screens": screens,
                    "guide_pass": all(row["rail_screen_pass"] for row in screens),
                }
            )
    resolved = output / "resolved-candidate.yaml"
    resolved.write_text(yaml.safe_dump(vehicle.model_dump(by_alias=True), sort_keys=False))
    load_vehicle(resolved)
    step = output / "recovery-cap-frame.step"
    cq.exporters.export(shape, str(step))
    after = {str(path): sha(path) for path in sorted(sources)}
    payload = {
        "run_id": datetime.now(UTC).strftime("wo03-recovery-clearance-%Y%m%dT%H%M%S%fZ"),
        "study": cfg["id"],
        "elapsed_s": time.monotonic() - started,
        "compute_cost_usd": 0,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "inputs_unchanged": before == after,
        "frozen_owned_files_unchanged": all(
            sha(Path(path)) == digest for path, digest in frozen_before.items()
        ),
        "original_horns_and_rods_restored": all(
            next(part for part in vehicle.parts if part.id == name).cad == original_parts[name].cad
            for name in ("servo_horns", "gimbal_links")
        ),
        "original_six_mm_arm_phases_and_axes_preserved": True,
        "tolerance_budget": tolerances,
        "window_derivation": windows,
        "window_derivation_reused_from_unchanged_thin_model": {
            "record": str(thin_path),
            "sha256": sha(thin_path),
            "source_snapshots": [cfg["thin_source_script"], cfg["thin_source_config"]],
        },
        "hoop_derivation": hoop,
        "front_8mm_cap_symmetric_difference_mm3": unchanged_front_difference,
        "section_audit": sections,
        "combined_hoop_section_audit": combined,
        "motion": motion,
        "mass": {
            "previous_frame_g": old_frame_g,
            "new_frame_g": new_frame_g,
            "window_removed_g": (uncut_shape.Volume() - shape.Volume()) * 0.00185,
            "total_frame_change_g": frame_mass_delta_g,
            "added_frame_mass_over_thin_trial_g": new_frame_g - thin["mass"]["new_frame_g"],
            "hoop_gross_annulus_g_before_union_and_ports": math.pi
            * (cfg["cap_outer_radius_mm"] ** 2 - hoop["selected_inner_radius_mm"] ** 2)
            * cfg["hoop"]["thickness_mm"]
            * 0.00185,
            "previous_recovery_increment_g": old_mode["recovery_increment_g"],
            "new_recovery_increment_g": recovery_increment,
            "dedicated_recovery_allocation_g": old_record["existing_baseline_recovery_g"]
            + recovery_increment,
            "all_mass_including_growth_kg": mass_properties(vehicle).mass_kg
            + vehicle.design.mass_allowance_kg,
        },
        "force_cases": cases,
        "unchanged_rail_path_bounds": rail_bounds(
            new_part, shape, cases, yaml.safe_load(Path(old_cfg["anchor_config"]).read_text())
        ),
        "guide_mass_hypotheses": guide,
        "resolved_copy": str(resolved),
        "resolved_copy_sha256": sha(resolved),
        "resolved_spec_sha256": hashlib.sha256(
            vehicle.model_dump_json(by_alias=True).encode()
        ).hexdigest(),
        "frame_step": {"path": str(step), "sha256": sha(step)},
        "native_operations": "Machining holes are native spec-owned axial cylinders. Rounded saddle additions are post-Boolean operations owned by this script and recorded in the copied parameters; generic local_shape alone omits those saddles.",
        "previous_canted_sweep_applicability": "The primary agent found and corrected shaft-Z inference from rod-tip Z. Published canted-horn motion results require corrected-model reruns and are not imported as actual physical clearance. This study restores flat original horns/rods.",
        "acceptance_passed": False,
        "rail_matched_and_single_leg_closed": False,
        "active_adoption": False,
        "flight_ready": False,
    }
    (output / "record.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-recovery-clearance.yaml")
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    args = parser.parse_args()
    output = args.output or Path(yaml.safe_load(args.config.read_text())["default_output"])
    result = run(args.config, output)
    print(output / "record.json")
    print("windows", result["window_derivation"]["groups"])
    print("mass", result["mass"])
    print("motion", result["motion"]["all_sampled_changed_pairs_outside_joint_zones_clear"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
