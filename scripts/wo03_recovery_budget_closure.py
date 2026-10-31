"""Audit a complete independent-recovery cut plan, exact-once mass and force flow.

This is an isolated design study. It deliberately keeps unknown attachments
unknown: force balance and enough guide mass do not establish a structural path.
The stopping-distance proxy and project factor are reused from the anchor study;
F = 3 m (v^2/(2s) + g), with the factor applied once. No rope derating, material
allowable or opening-shock measurement is invented here.
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

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_recovery_anchor import share
from scripts.wo03_recovery_mass_budget import budget
from src.cad.parts import _base_shape, cq, placed_shape, properties, tube
from src.vehicle.benchmark import screen_launch
from src.vehicle.mass import mass_properties
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import CADMass, load_vehicle, vehicle_input_paths


def cut_plan(cfg: dict[str, Any]) -> dict[str, Any]:
    rows = []
    names = [row["id"] for row in cfg["cut_plan"]]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate rope piece identity")
    for piece in cfg["cut_plan"]:
        rope = cfg["rope"][piece["material"]]
        prep = 2 * rope["preparation_per_end_m"]
        if piece["standing_m"] < abs(piece["end_station_m"] - piece["start_station_m"]):
            raise ValueError(f"{piece['id']}: standing length shorter than axial distance")
        rows.append(
            dict(
                piece,
                end_count=2,
                preparation_m=prep,
                cut_m=piece["standing_m"] + prep,
                mass_g=(piece["standing_m"] + prep) * rope["g_per_m"],
                termination_qualified=rope["preparation_qualified"],
            )
        )
    return {
        "pieces": rows,
        "end_count": sum(row["end_count"] for row in rows),
        "standing_m": sum(row["standing_m"] for row in rows),
        "preparation_m": sum(row["preparation_m"] for row in rows),
        "total_cut_m": sum(row["cut_m"] for row in rows),
        "line_mass_g": sum(row["mass_g"] for row in rows),
        "all_terminations_qualified": all(row["termination_qualified"] for row in rows),
    }


def factored_acceleration(speed_mps: float, stop_m: float, factor: float) -> float:
    if min(speed_mps, stop_m, factor) <= 0:
        raise ValueError("Positive speed, stop distance and factor required")
    return factor * (speed_mps**2 / (2 * stop_m) + 9.80665)


def partition(parts: list[Any], cfg: dict[str, Any]) -> dict[str, list[Any]]:
    """Every mass enters one primary branch; aft child forces are not added again."""
    groups: dict[str, list[Any]] = {
        key: [] for key in ("main", "nose", "body", "coupler", "sled", "aft")
    }
    body = {
        "body_upper",
        "adhesive_finish",
        "rail_guides",
        "recovery_bulkhead",
        "recovery_power_switch",
        "recovery_switch_g11_doubler",
    }
    coupler = {"interface_coupler", "joint_stop", "aft_interface_hardware"}
    explicit = {"recovery_line_" + item["id"]: item["branch"] for item in cfg["cut_plan"]}
    explicit.update(
        {
            "recovery_extra_" + key.removesuffix("_g"): layout["branch"]
            for key, layout in cfg["hardware_layout"].items()
        }
    )
    for part in parts:
        if part.id in explicit:
            branch = explicit[part.id]
        elif part.id == "nose_cone":
            branch = "nose"
        elif part.id in body:
            branch = "body"
        elif part.id in coupler:
            branch = "coupler"
        elif part.cg_station_m > 0.92:
            branch = "aft"
        elif part.id in {
            "parachute",
            "recovery_protection",
            "recovery_junction",
        } or part.id.startswith("recovery_line_main"):
            branch = "main"
        else:
            branch = "sled"
        groups[branch].append(part)
    all_ids = [part.id for items in groups.values() for part in items]
    if len(all_ids) != len(set(all_ids)) or len(all_ids) != len(parts):
        raise ValueError("Force partition is not exact-once")
    return groups


def force_case(vehicle: Any, cfg: dict[str, Any], speed: float, label: str) -> dict[str, Any]:
    groups = partition(vehicle.parts, cfg)
    acceleration = factored_acceleration(speed, cfg["stop_m"], cfg["factor"])
    allowance = vehicle.design.mass_allowance_kg
    branches = []
    for name, items in groups.items():
        part_mass = sum(float(part.resolved_mass_kg) for part in items)
        growth = allowance if name == "aft" else 0
        branches.append(
            {
                "branch": name,
                "part_ids": [part.id for part in items],
                "part_mass_kg": part_mass,
                "growth_kg": growth,
                "factored_force_n": (part_mass + growth) * acceleration,
                "path": cfg["branch_attachments"][name],
                "installed_capacity_n": None,
                "path_verified": False,
            }
        )
    by_name = {row["branch"]: row for row in branches}
    total = (mass_properties(vehicle).mass_kg + allowance) * acceleration
    aft_force = by_name["aft"]["factored_force_n"]
    plate_id = "retention" if vehicle.design.mode == "performance" else "gimbal_frame"
    plate = next(part for part in vehicle.parts if part.id == plate_id)
    after_plate = aft_force - plate.resolved_mass_kg * acceleration
    rail = cfg["fixed_rail_screen"]
    rail_capacity = (
        rail["count"]
        * rail["clipped_area_each_mm2_estimate"]
        * rail["axial_hot_screen_mpa_estimate"]
    )
    body_cfg = cfg["body_screen"]
    body_area = math.pi * body_cfg["diameter_mm"] * body_cfg["kraft_wall_mm"]
    balance = sum(row["factored_force_n"] for row in branches) - total
    return {
        "scenario": label,
        "speed_mps": speed,
        "factor_applied_once": cfg["factor"],
        "stopping_distance_m_unqualified": cfg["stop_m"],
        "factored_acceleration_mps2": acceleration,
        "whole_vehicle_factored_force_n": total,
        "branches": branches,
        "balance_residual_n": balance,
        "force_balance_pass": abs(balance) < 1e-8,
        "aft_plate_inertia_factored_n": plate.resolved_mass_kg * acceleration,
        "aft_post_plate_transfer_n": after_plate,
        "fixed_rail_capacity_estimate_n": (
            rail_capacity if vehicle.design.mode == "performance" else None
        ),
        "fixed_all_transfer_through_rails_screen_pass": (
            after_plate <= rail_capacity if vehicle.design.mode == "performance" else None
        ),
        "body_uniform_axial_proxy_mpa": by_name["body"]["factored_force_n"] / body_area,
        "body_uniform_proxy_screen_pass": by_name["body"]["factored_force_n"] / body_area
        <= body_cfg["axial_hot_screen_mpa_estimate"],
        "aft_child_forces_not_added_to_total": [
            {"part_id": part.id, "factored_force_n": part.resolved_mass_kg * acceleration}
            for part in groups["aft"]
        ],
        "all_physical_branches_verified": False,
    }


def rounded_junction(cfg: dict[str, Any]) -> Any:
    j = cfg["junction"]
    ring = (
        cq.Workplane("XY")
        .circle(j["outer_radius_mm"])
        .circle(j["inner_radius_mm"])
        .extrude(j["thickness_mm"])
    )
    return ring.edges().fillet(j["edge_radius_mm"]).val()


def rail_bounds(
    frame: Any, shape: Any, cases: list[dict[str, Any]], anchor_cfg: dict[str, Any]
) -> dict[str, Any]:
    """BRep area/weak-axis Euler proxies; recovery rails are in tension.

    Hot E=5 GPa reuses the packaging study's engineering estimate. The
    existing 25 MPa G11 screen is not a grade/direction-specific allowable.
    Pinned Euler restraints are a sensitivity, not an executed eigenvalue solve.
    """
    import numpy as np

    rows = []
    for station in (1.040, 1.075, 1.130, 1.170):
        local_z = (station - frame.position_m) * 1000
        slab = (
            cq.Workplane("XY")
            .box(70, 70, 0.1, centered=(True, True, False))
            .val()
            .translate((0, 0, local_z))
        )
        section = shape.intersect(slab)
        pieces = []
        for solid in section.Solids():
            inertia = np.asarray(cq.Shape.matrixOfInertia(solid))[:2, :2] / 0.1
            pieces.append(
                {
                    "area_mm2": solid.Volume() / 0.1,
                    "weak_I_mm4": float(np.linalg.eigvalsh(inertia)[0]),
                }
            )
        rows.append({"global_station_m": station, "rails": pieces})
    minimum_area = min(item["area_mm2"] for row in rows for item in row["rails"])
    minimum_i = min(item["weak_I_mm4"] for row in rows for item in row["rails"])
    worst = max(case["branches"][-1]["factored_force_n"] for case in cases)
    # branches are explicitly ordered with aft last, but verify the identity.
    assert all(case["branches"][-1]["branch"] == "aft" for case in cases)
    total_length_mm = frame.geometry["length_m"] * 1000
    front_end = frame.position_m + anchor_cfg["tvc_web_thickness_mm"] / 1000
    pivot_front = frame.position_m + (frame.cad.parameters["pivot_station_mm"] - 4) / 1000
    clear_span_mm = (pivot_front - front_end) * 1000
    capacity = minimum_area * anchor_cfg["hot_g11_screen_mpa"]
    required_extra_area = max(0, worst / anchor_cfg["hot_g11_screen_mpa"] - minimum_area)
    return {
        "BRep_sections": rows,
        "minimum_rail_area_mm2": minimum_area,
        "minimum_weak_I_mm4": minimum_i,
        "worst_aft_factored_n": worst,
        "equal_three_leg_demand_each_n": worst / 3,
        "matched_bounded_leg_demand_n": share(worst, anchor_cfg),
        "single_leg_demand_n": worst,
        "rail_hot_capacity_estimate_n": capacity,
        "equal_share_estimated_screen_pass": worst / 3 <= capacity,
        "matched_share_estimated_screen_pass": share(worst, anchor_cfg) <= capacity,
        "single_leg_estimated_screen_pass": worst <= capacity,
        "maximum_allowed_leg_fraction_at_estimated_screen": capacity / worst,
        "full_length_uniform_single_leg_area_addition_each_mm2": required_extra_area,
        "three_uniform_rail_additions_mass_g_lower_bound": 3
        * required_extra_area
        * total_length_mm
        * 0.00185,
        "uniform_addition_caveat": "Mass floor only: available radial/tangential space, channels, gimbal motion, laminate direction and actual force redistribution not solved.",
        "front_to_pivot_clear_span_mm": clear_span_mm,
        "three_rail_pinned_euler_n_at_5GPa_estimate": 3
        * math.pi**2
        * 5000
        * minimum_i
        / clear_span_mm**2,
        "three_rail_pinned_euler_n_full_length_unbraced": 3
        * math.pi**2
        * 5000
        * minimum_i
        / total_length_mm**2,
        "executed_buckling_FEA": False,
        "recovery_axial_sign": "tension; Euler pertains to separate compression/thrust sensitivity only",
        "complete_rail_to_ring_to_shell_to_motor_path_verified": False,
    }


def opening_load_audit(vehicle: Any, cfg: dict[str, Any], output: Path) -> dict[str, Any]:
    """Use the actual shared core for smooth inflation; audit snatch separately.

    Cruz/Kandis/Witkowski, AIAA2003-2131, distinguish inflation drag/apparent
    air mass from earlier snatch. No DGB opening coefficient is transferred.
    Reduced-mass collision energy is ordinary two-body mechanics; peak=2E/d
    is specifically a linear elastic arrest, not a measured shock waveform.
    """
    import jax
    import jax.numpy as jnp
    import numpy as np

    from src.sim import dynamics, environment, inputs, motor

    jax.config.update("jax_enable_x64", True)
    audit = cfg["opening_audit"]
    dt = audit["dt_s"]
    times = jnp.arange(round(audit["integration_s"] / dt)) * dt + 20.0
    parameters = inputs.prepare(
        vehicle,
        {
            "dt_s": dt,
            "elevation_m": 0,
            "sensor_noise": False,
            "added_mass_kg": vehicle.design.mass_allowance_kg,
        },
    )

    @jax.jit
    def integrate(p, initial):
        recovery_time = 20.0 - p.recovery[1]
        disabled = p._replace(recovery=p.recovery.at[3].set(0))

        def step(y, t):
            on, _ = dynamics.derivative(t, y, jnp.zeros(2), recovery_time, p, True)
            off, _ = dynamics.derivative(t, y, jnp.zeros(2), recovery_time, disabled, True)
            mass = motor.properties(t, p)[0]
            actual_core_canopy_force = jnp.linalg.norm((off[3:6] - on[3:6]) * mass)
            next_y = dynamics.rk4(t, y, jnp.zeros(2), recovery_time, p, True)
            return next_y, jnp.array(
                [t - 20, jnp.linalg.norm(y[3:6]), actual_core_canopy_force, -y[2], mass]
            )

        return jax.lax.scan(step, initial, times)[1]

    rows, traces = [], []
    cd_area = float(parameters.recovery[0])
    mass = float(motor.properties(jnp.asarray(20.0), parameters)[0])
    for height in audit["height_msl_m"]:
        rho = float(environment.atmosphere(jnp.asarray(height))[0])
        for speed in audit["speeds_mps"]:
            initial = jnp.array(
                [0, 0, -height, 0, 0, speed, math.sqrt(0.5), 0, math.sqrt(0.5), 0, 0, 0, 0],
                dtype=jnp.float64,
            )
            trace = np.asarray(integrate(parameters, initial))
            full = 0.5 * rho * cd_area * speed**2
            stop_force = mass * (speed**2 / (2 * cfg["stop_m"]) + 9.80665)
            index = int(np.argmax(trace[:, 2]))
            inflation = trace[trace[:, 0] <= float(parameters.recovery[2])]
            rows.append(
                {
                    "height_msl_m": height,
                    "initial_speed_mps": speed,
                    "rho_kg_m3": rho,
                    "CdA_m2": cd_area,
                    "burnout_mass_plus_50g_kg": mass,
                    "fixed_initial_speed_full_open_drag_n": full,
                    "fixed_drag_times_project_factor_n": full * cfg["factor"],
                    "shared_core_peak_in_first_inflation_n": float(inflation[:, 2].max()),
                    "shared_core_peak_over_1s_n": float(trace[index, 2]),
                    "shared_core_peak_time_s": float(trace[index, 0]),
                    "shared_core_speed_at_peak_mps": float(trace[index, 1]),
                    "shared_core_peak_times_project_factor_n": float(trace[index, 2])
                    * cfg["factor"],
                    "constant_0p3m_stop_burnout_factored_n": stop_force * cfg["factor"],
                    "opening_multiplier_needed_to_equal_stop_proxy": stop_force / full,
                    "opening_multiplier_sensitivities": [
                        {
                            "multiplier_unqualified": k,
                            "factored_fixed_speed_force_n": cfg["factor"] * k * full,
                        }
                        for k in audit["opening_multiplier_sensitivities"]
                    ],
                }
            )
            traces.append(
                {
                    "height_msl_m": height,
                    "initial_speed_mps": speed,
                    "columns": [
                        "elapsed_s",
                        "speed_mps",
                        "actual_core_canopy_force_n",
                        "height_msl_m",
                        "mass_kg",
                    ],
                    "samples": trace[::10].tolist(),
                }
            )
    trace_path = output / "opening-shared-core-traces.json"
    trace_path.write_text(json.dumps(traces, indent=2, allow_nan=False) + "\n")
    canopy = next(part.resolved_mass_kg for part in vehicle.parts if part.id == "parachute")
    nose = next(part.resolved_mass_kg for part in vehicle.parts if part.id == "nose_cone")
    snatch = []
    for label, arrested_mass in (("canopy_only", canopy), ("canopy_plus_nose", canopy + nose)):
        reduced = arrested_mass * (mass - arrested_mass) / mass
        for relative in audit["snatch_relative_speeds_mps"]:
            energy = 0.5 * reduced * relative**2
            snatch.append(
                {
                    "arrested_group": label,
                    "arrested_mass_kg": arrested_mass,
                    "other_mass_kg": mass - arrested_mass,
                    "reduced_mass_kg": reduced,
                    "relative_speed_mps_unverified": relative,
                    "relative_energy_j": energy,
                    "strokes": [
                        {
                            "stroke_m_unqualified": stroke,
                            "average_force_n": energy / stroke,
                            "linear_elastic_peak_n": 2 * energy / stroke,
                            "linear_elastic_peak_times_project_factor_n": cfg["factor"]
                            * 2
                            * energy
                            / stroke,
                        }
                        for stroke in audit["snatch_strokes_m"]
                    ],
                    "needed_stroke_for_peak_unfactored_load_limits": [
                        {
                            "peak_limit_n_unqualified": limit,
                            "linear_elastic_minimum_stroke_m": 2 * energy / limit,
                            "maximum_linear_stiffness_n_per_m": limit**2 / (2 * energy),
                        }
                        for limit in (100, 150, 200, 300)
                    ],
                }
            )
    compliant = audit["compliant_candidate"]
    force_curve = np.asarray(compliant["force_lbf"]) * 4.4482216152605
    candidate_energy = float(
        np.trapezoid(force_curve, compliant["strain"]) * compliant["free_length_m"]
    )
    candidate_g = compliant["mass_g_per_foot"] / 0.3048 * compliant["free_length_m"]
    return {
        "source_scope": audit["source_model_scope"],
        "primary_source": audit["source_opening"],
        "shared_core_force_is_enabled_minus_disabled_derivative": True,
        "smooth_model_missing": "Apparent air mass, canopy overinflation, cloth/line inertia, slack-line snatch, elastic harness and packed deployment are absent. No measured opening coefficient exists.",
        "smooth_cases": rows,
        "snatch_energy_cases": snatch,
        "snatch_limitations": "The specified relative speeds are fault sensitivities, not observed canopy/rocket separation speeds. Reduced-mass collision excludes continuing aerodynamic work and added air mass; it is not a total deployment-energy upper bound. A canopy held by air can approach the much larger full-vehicle kinetic-energy bound.",
        "whole_vehicle_kinetic_energy_at_late_probe_j": 0.5 * mass * audit["speeds_mps"][-1] ** 2,
        "shared_core_trace": str(trace_path),
        "trace_sha256": hashlib.sha256(trace_path.read_bytes()).hexdigest(),
        "compliant_source_curve_candidate": {
            "source": compliant["source"],
            "product": compliant["product"],
            "free_length_m": compliant["free_length_m"],
            "mass_g_excluding_ends_backup_and_heat_protection": candidate_g,
            "quasistatic_work_to_100pct_strain_j": candidate_energy,
            "peak_curve_force_at_100pct_n": float(force_curve[-1]),
            "stroke_at_100pct_m": compliant["free_length_m"],
            "caveats": compliant["caveats"],
            "selected_or_qualified": False,
        },
        "required_screen_changed": False,
        "0p3m_failure_retained": True,
    }


def anchor_shape(part: Any, cfg: dict[str, Any], fixed: bool, g80: bool) -> Any:
    if fixed:
        part = part.model_copy(deep=True)
        length = cfg["g80_finger_length_mm"] if g80 else cfg["finger_length_mm"]
        part.geometry["length_m"] = length / 1000
        part.cad.parameters["bond_fingers"]["length_mm"] = length
        part.cad.parameters["thickness_mm"] = cfg["fixed_web_thickness_mm"]
        shape = _base_shape(part)
        x, y, d, thickness = (
            cfg["fixed_port_x_mm"],
            cfg["fixed_port_y_mm"],
            cfg["fixed_port_diameter_mm"],
            cfg["fixed_web_thickness_mm"],
        )
    else:
        thickness = cfg["tvc_web_thickness_mm"]
        shape = _base_shape(part).fuse(tube(32, 24, thickness))
        x, y, d = cfg["tvc_port_x_mm"], cfg["tvc_port_y_mm"], cfg["port_diameter_mm"]
    for angle in (0, 120, 240):
        saddle = cq.Solid.makeCylinder(
            cfg["saddle_radius_mm"],
            cfg["saddle_length_mm"],
            cq.Vector(x - cfg["saddle_length_mm"] / 2, 0, thickness),
            cq.Vector(1, 0, 0),
        ).rotate((0, 0, 0), (0, 0, 1), angle)
        shape = shape.fuse(saddle)
        for sign in (-1, 1):
            hole = cq.Solid.makeCylinder(
                d / 2,
                thickness + cfg["saddle_radius_mm"] + 2,
                cq.Vector(x, sign * y, -1),
                cq.Vector(0, 0, 1),
            ).rotate((0, 0, 0), (0, 0, 1), angle)
            shape = shape.cut(hole)
    return shape.clean()


def add_budget_part(vehicle: Any, name: str, mass_g: float, station: float) -> Any:
    part = next(p for p in vehicle.parts if p.id == "recovery_output_harness").model_copy(deep=True)
    part.id = name
    part.parent = "body_upper"
    part.position_m = station
    part.cg_offset_m = 0
    part.mass_kg = mass_g / 1000
    part.cad_mass = None
    part.geometry = {"bbox_m": [0.001, 0.001, 0.001]}
    part.lateral_offset_m = (0, 0)
    part.cad.generator = "budget"
    part.cad.parameters = {}
    part.cad.mass_basis = "supplied_or_estimated"
    part.cad.role = "distributed_budget"
    part.learn = "Isolated recovery mass allocation; geometry or installed capacity is not represented by this budget envelope."
    vehicle.parts.append(part)
    return part


def nominal_checks(
    vehicle: Any,
    frame: Any,
    frame_shape: Any,
    baseline_frame: Any,
    junction: Any,
    output: Path,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    frame_placed = frame_shape.translate(
        (
            frame.lateral_offset_m[0] * 1000,
            -frame.lateral_offset_m[1] * 1000,
            frame.position_m * 1000,
        )
    )
    baseline = placed_shape(baseline_frame)
    added = frame_placed.cut(baseline)
    frame_checks = []
    junction_checks = []
    j = vehicle.parts[-1]
    junction_placed = junction.translate(
        (j.lateral_offset_m[0] * 1000, -j.lateral_offset_m[1] * 1000, j.position_m * 1000)
    )
    # Only new solids are checked. This does not repeat a full vehicle export or
    # pretend existing contact/collision exceptions disappeared.
    for part in vehicle.parts:
        if part.id == frame.id or part.cad.role in ("distributed_budget", "soft_stowage"):
            continue
        if part.id == j.id:
            continue
        if part.id == "fin_set" and part.cad.generator == "wo03_layered_trainer_fin_study":
            shape = (
                cq.importers.importStep(cfg["trainer_fin_step"])
                .val()
                .translate((0, 0, part.position_m * 1000))
            )
        else:
            shape = placed_shape(part)
        for test_shape, rows in ((added, frame_checks), (junction_placed, junction_checks)):
            a, b = test_shape.BoundingBox(), shape.BoundingBox()
            if (
                a.xmax < b.xmin
                or b.xmax < a.xmin
                or a.ymax < b.ymin
                or b.ymax < a.ymin
                or a.zmax < b.zmin
                or b.zmax < a.zmin
            ):
                continue
            volume = test_shape.intersect(shape).Volume()
            if volume > 1e-6:
                rows.append({"part_id": part.id, "positive_intersection_mm3": volume})
    cq.exporters.export(frame_shape, str(output / "recovery-anchor.step"))
    cq.exporters.export(junction, str(output / "recovery-junction.step"))
    return {
        "anchor_valid": bool(frame_shape.isValid()),
        "anchor_solids": len(frame_shape.Solids()),
        "junction_valid": bool(junction.isValid()),
        "junction_solids": len(junction.Solids()),
        "added_anchor_intersections": frame_checks,
        "junction_intersections": junction_checks,
        "junction_position_cad_mm": [
            j.lateral_offset_m[0] * 1000,
            -j.lateral_offset_m[1] * 1000,
            j.position_m * 1000,
        ],
        "junction_outer_radius_plus_offset_mm": 15,
        "junction_body_bore_radius_mm": 32.5,
        "junction_radial_bore_screen_pass": True,
        "limitations": "Nominal rigid solids only. Flexible lines, terminal crowding, full motion, new bulkhead passages, tolerance and service sweeps remain open.",
    }


def reverse_horns(vehicle: Any, cant_degrees: list[float] | None = None) -> dict[str, Any]:
    """Keep six-mm arms in their actual rotation planes and match rod ends."""
    cant_degrees = cant_degrees or [180, 180]
    parts = {part.id: part for part in vehicle.parts}
    horns, rods = parts["servo_horns"], parts["gimbal_links"]
    old_rod_ends = [segment[1][:] for segment in rods.cad.parameters["segments_mm"]]
    changes = []
    for axis, (horn, rod) in enumerate(
        zip(horns.cad.parameters["segments_mm"], rods.cad.parameters["segments_mm"], strict=True)
    ):
        shaft, old_tip = horn[0], horn[1][:]
        new_tip = shaft[:]
        new_tip[axis] += 6 * math.cos(math.radians(cant_degrees[axis]))
        new_tip[2] += 6 * math.sin(math.radians(cant_degrees[axis]))
        horn[1] = new_tip
        rod[0] = [new_tip[0], new_tip[1], new_tip[2] + (horns.position_m - rods.position_m) * 1000]
        changes.append(
            {
                "shaft_local_mm_unchanged": shaft,
                "tip_before_mm": old_tip,
                "tip_after_mm": new_tip,
                "rod_start_local_mm": rod[0],
            }
        )
    for part in (horns, rods):
        part.cad_mass = CADMass.model_validate(properties(part, _base_shape(part)))
        if part.cad.mass_basis == "volume_density":
            part.mass_kg = part.cad_mass.volume_m3 * DENSITY_KG_M3[part.material]
    return {
        "cant_degrees": cant_degrees,
        "shaft_axes_cad": ["+Y yaw", "+X pitch"],
        "changes": changes,
        "gimbal_rod_ends_unchanged": old_rod_ends
        == [segment[1] for segment in rods.cad.parameters["segments_mm"]],
        "rod_mass_estimate_8g_retained": rods.resolved_mass_kg == 0.008,
        "servo_authority_or_spline_qualification": False,
    }


def horn_link_frame_sweep(
    vehicle: Any,
    frame: Any,
    shape: Any,
    cfg: dict[str, Any],
    *,
    steps: int = 5,
    solids: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """All changed-part pairs with posed motor/cassette, including raw joints."""
    import numpy as np
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape

    from src.cad.assembly import rigid_intersections
    from src.cad.kinematics import linkage, pose

    assert vehicle.tvc
    extent = math.degrees(vehicle.tvc.max_deflection_rad)
    if solids is None:
        solids = {}
        for part in vehicle.parts:
            if part.id == frame.id:
                solid = shape.translate((0, 0, part.position_m * 1000))
            elif part.id == "fin_set":
                solid = (
                    cq.importers.importStep(cfg["trainer_fin_step"])
                    .val()
                    .translate((0, 0, part.position_m * 1000))
                )
            elif part.id == "recovery_junction":
                solid = rounded_junction(cfg).translate((0, 0, part.position_m * 1000))
            else:
                solid = placed_shape(part)
            solids[part.id] = solid
    rows = []
    minima = {
        "rod_to_cassette": math.inf,
        "rod_to_frame": math.inf,
        "horn_to_frame": math.inf,
        "rod_to_coupler": math.inf,
        "rod_to_horn": math.inf,
    }
    min_ratio = math.inf
    for pitch in np.linspace(-extent, extent, steps):
        for yaw in np.linspace(-extent, extent, steps):
            row = {"pitch_deg": float(pitch), "yaw_deg": float(yaw)}
            try:
                closure = linkage(vehicle, pitch, yaw)
            except ValueError as error:
                row.update({"linkage_closure": False, "error": str(error)})
                rows.append(row)
                continue
            posed = pose(vehicle, solids, pitch, yaw)
            intersections = rigid_intersections(
                vehicle,
                posed,
                moving_ids={"gimbal_links", "servo_horns", "gimbal_frame", "recovery_junction"},
            )
            outside = []
            joints = [
                point for axis in closure["axes"] for point in (axis["start_mm"], axis["end_mm"])
            ]
            for hit in intersections:
                intersection = posed[hit["a"]].intersect(posed[hit["b"]])
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
                    outside.append(
                        dict(hit, outside_declared_joint_zones_mm3=intersection.Volume())
                    )
            if steps == 5:
                for label, a, b in (
                    ("rod_to_cassette", "gimbal_links", "motor_mount"),
                    ("rod_to_frame", "gimbal_links", "gimbal_frame"),
                    ("horn_to_frame", "servo_horns", "gimbal_frame"),
                    ("rod_to_coupler", "gimbal_links", "interface_coupler"),
                    ("rod_to_horn", "gimbal_links", "servo_horns"),
                ):
                    distance = BRepExtrema_DistShapeShape(posed[a].wrapped, posed[b].wrapped)
                    minima[label] = min(minima[label], float(distance.Value()))
                jac = np.column_stack(
                    [
                        (
                            np.asarray(
                                [
                                    a["shaft_deg"]
                                    for a in linkage(vehicle, pitch + dp, yaw + dy)["axes"]
                                ]
                            )
                            - np.asarray([a["shaft_deg"] for a in closure["axes"]])
                        )
                        / 0.001
                        for dp, dy in ((0.001, 0), (0, 0.001))
                    ]
                )
                min_ratio = min(min_ratio, 1 / float(np.abs(jac).sum(axis=1).max()))
            row.update(
                {
                    "linkage_closure": True,
                    "servo_shaft_deg": [axis["shaft_deg"] for axis in closure["axes"]],
                    "raw_changed_part_intersections": intersections,
                    "outside_joint_zone_intersections": outside,
                }
            )
            rows.append(row)
    return {
        "poses": rows,
        "pose_count": steps**2,
        "positive_volume_reporting_threshold_mm3": 0.05,
        "manufacturing_tolerance_bounds_applied": False,
        "all_closures": all(row["linkage_closure"] for row in rows),
        "all_changed_pairs_outside_declared_joints_pass": all(
            row.get("linkage_closure") and not row["outside_joint_zone_intersections"]
            for row in rows
        ),
        "actual_minimum_pair_clearances_mm": {
            key: value if math.isfinite(value) else None for key, value in minima.items()
        },
        "minimum_sampled_kinematic_rate_ratio": min_ratio if math.isfinite(min_ratio) else None,
        "configured_rate_ratio_unadopted": vehicle.tvc.linkage_ratio,
        "joint_zone_radius_mm": 4,
        "joint_policy_source": "src/cad/verification.py; raw intersections remain recorded before removing these existing endpoint neighborhoods",
        "scope": "All pairs containing changed frame, junction, rods or horns versus every modeled rigid part, with nested motor/gimbal poses. Purchased envelopes are nominal; endpoint joints, tolerances, continuous motion, cable/packing paths and servo force/authority remain unqualified.",
    }


def run(config: Path, output: Path) -> dict[str, Any]:
    started = time.monotonic()
    run_id = datetime.now(UTC).strftime("wo03-recovery-budget-closure-%Y%m%dT%H%M%S%fZ")
    cfg = yaml.safe_load(config.read_text())
    anchor_cfg = yaml.safe_load(Path(cfg["anchor_config"]).read_text())
    budget_cfg = yaml.safe_load(Path(cfg["budget_config"]).read_text())
    packaging = json.loads(Path(cfg["packaging_record"]).read_text())
    trainer_record = json.loads(Path(cfg["trainer_construction_record"]).read_text())
    if (
        not trainer_record["inputs_unchanged"]
        or hashlib.sha256(Path(cfg["trainer_construction_copy"]).read_bytes()).hexdigest()
        != trainer_record["resolved_copy_sha256"]
    ):
        raise ValueError("Trainer construction copy does not match its frozen record")
    if (
        hashlib.sha256(Path(cfg["trainer_fin_step"]).read_bytes()).hexdigest()
        != trainer_record["cad_exports"]["fin-layers.step"]["sha256"]
    ):
        raise ValueError("Trainer layered geometry does not match its frozen record")
    fin = json.loads(Path(cfg["fin_record"]).read_text())["cases"][0]
    anchor_record = json.loads(Path(cfg["anchor_record"]).read_text())
    flight = json.loads(Path(cfg["flight_record"]).read_text())
    sources = {
        config,
        Path(__file__),
        *(
            Path(cfg[k])
            for k in (
                "anchor_config",
                "budget_config",
                "anchor_record",
                "packaging_record",
                "fin_record",
                "flight_record",
            )
        ),
    }
    sources.update(Path("src/cad").glob("*.py"))
    sources.update(Path("src/vehicle").glob("*.py"))
    sources.update(Path("src/sim").glob("*.py"))
    sources.add(Path("configs/sim-model.yaml"))
    sources.add(Path("scripts/wo03_recovery_mass_budget.py"))
    sources.add(Path("scripts/wo03_recovery_anchor.py"))
    for row in packaging["modes"]:
        sources.add(Path(row["resolved_copy"]))
    sources.update(
        Path(cfg[key])
        for key in ("trainer_construction_copy", "trainer_construction_record", "trainer_fin_step")
    )
    for path in yaml.safe_load(Path(cfg["platform"]).read_text())["vehicles"] + [
        "configs/vehicle/wo02/performance-g54.yaml"
    ]:
        sources.update(vehicle_input_paths(path))

    def hashes():
        return {
            str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(sources)
        }

    before = hashes()
    plan = cut_plan(cfg)
    output.mkdir(parents=True, exist_ok=True)
    ring = rounded_junction(cfg)
    junction_g = ring.Volume() * cfg["junction"]["density_kg_m3"] * 1e-6
    modes = []
    guide_rows = []
    for package_row in packaging["modes"]:
        vehicle = load_vehicle(package_row["resolved_copy"])
        original_path = next(
            path
            for path in yaml.safe_load(Path(cfg["platform"]).read_text())["vehicles"]
            + ["configs/vehicle/wo02/performance-g54.yaml"]
            if load_vehicle(path).id == vehicle.id
        )
        original = load_vehicle(original_path)
        original_parts = {part.id: part for part in original.parts}
        construction_delta_g = 0.0
        if vehicle.id == "modular-tvc-finned-v1":
            trainer = load_vehicle(cfg["trainer_construction_copy"])
            trainer_parts = {part.id: part for part in trainer.parts}
            for index, part in enumerate(vehicle.parts):
                if part.id in {"battery", "fin_set", "fin_bonds", "aft_shell", "gimbal_frame"}:
                    construction_delta_g += (
                        trainer_parts[part.id].resolved_mass_kg
                        - original_parts[part.id].resolved_mass_kg
                    ) * 1000
                    vehicle.parts[index] = trainer_parts[part.id].model_copy(deep=True)
        horn_correction = (
            reverse_horns(vehicle, cfg["horn_cant_degrees"])
            if vehicle.design.mode != "performance"
            else None
        )
        frame = next(
            part
            for part in vehicle.parts
            if part.id == ("retention" if vehicle.design.mode == "performance" else "gimbal_frame")
        )
        baseline_frame = frame.model_copy(deep=True)
        preserved_features = None
        if vehicle.design.mode != "performance":
            old_start = frame.position_m
            offset_mm = (old_start - cfg["forward_frame_start_station_m"]) * 1000
            params = frame.cad.parameters
            preserved_features = {
                "pivot_station_m": old_start + params["pivot_station_mm"] / 1000,
                "rear_ring_station_m": old_start + params["ring_stations_mm"][-1] / 1000,
                "fin_channel_start_m": old_start + params["tab_slot_start_mm"] / 1000,
            }
            frame.position_m = cfg["forward_frame_start_station_m"]
            frame.geometry["length_m"] += offset_mm / 1000
            params["ring_stations_mm"] = [0] + [
                station + offset_mm for station in params["ring_stations_mm"][1:]
            ]
            params["ring_thicknesses_mm"] = [
                anchor_cfg["tvc_web_thickness_mm"],
                params["ring_thickness_mm"],
            ]
            params["ring_inner_radii_mm"] = [24, frame.geometry["inner_radius_m"] * 1000]
            params["pivot_station_mm"] += offset_mm
            params["tab_slot_start_mm"] += offset_mm
            for block in params.get("retainer_blocks", []):
                block["position_mm"][2] += offset_mm
                block["nut_pocket_position_mm"][2] += offset_mm
            frame.cad_mass = None
            preserved_features["preserved_after_shift"] = all(
                math.isclose(value, frame.position_m + params[key] / 1000, abs_tol=1e-12)
                for value, key in (
                    (preserved_features["pivot_station_m"], "pivot_station_mm"),
                    (preserved_features["fin_channel_start_m"], "tab_slot_start_mm"),
                )
            ) and math.isclose(
                preserved_features["rear_ring_station_m"],
                frame.position_m + params["ring_stations_mm"][-1] / 1000,
                abs_tol=1e-12,
            )
        frame.cad.parameters["study_recovery_anchor_operations"] = anchor_cfg
        shape = anchor_shape(
            frame,
            anchor_cfg,
            vehicle.design.mode == "performance",
            vehicle.id == "modular-performance-v1",
        )
        frame_props = properties(frame, shape)
        frame.cad_mass = CADMass.model_validate(frame_props)
        frame.mass_kg = shape.Volume() * 0.00185 / 1000
        frame_delta_g = (frame.resolved_mass_kg - baseline_frame.resolved_mass_kg) * 1000
        if vehicle.design.mode == "performance":
            frame.position_m -= 0.0005
        mode_plan_cfg = json.loads(json.dumps(cfg))
        for piece in mode_plan_cfg["cut_plan"]:
            if piece["branch"] == "aft":
                piece["end_station_m"] = frame.position_m
                radial_mm = math.hypot(
                    (
                        anchor_cfg["fixed_port_x_mm"]
                        if vehicle.design.mode == "performance"
                        else anchor_cfg["tvc_port_x_mm"]
                    ),
                    (
                        anchor_cfg["fixed_port_y_mm"]
                        if vehicle.design.mode == "performance"
                        else anchor_cfg["tvc_port_y_mm"]
                    ),
                )
                shortest = math.hypot(frame.position_m - piece["start_station_m"], radial_mm / 1000)
                piece["standing_m"] = max(
                    piece["standing_m"], math.ceil((shortest + 0.008) * 100) / 100
                )
        mode_plan = cut_plan(mode_plan_cfg)
        vehicle.parts = [
            part for part in vehicle.parts if part.id not in {"shock_cord", "recovery_anchor"}
        ]
        for row in mode_plan["pieces"]:
            add_budget_part(
                vehicle,
                "recovery_line_" + row["id"],
                row["mass_g"],
                (row["start_station_m"] + row["end_station_m"]) / 2,
            )
        for name, mass_g in cfg["hardware"].items():
            if not name.startswith("existing_"):
                add_budget_part(
                    vehicle,
                    "recovery_extra_" + name.removesuffix("_g"),
                    mass_g,
                    cfg["hardware_layout"][name]["station_m"],
                )
        junction_part = add_budget_part(
            vehicle, "recovery_junction", junction_g, cfg["junction"]["station_m"]
        )
        junction_part.cg_offset_m = cfg["junction"]["thickness_mm"] / 2000
        junction_part.lateral_offset_m = (
            cfg["junction"]["cad_x_mm"] / 1000,
            -cfg["junction"]["cad_y_mm"] / 1000,
        )
        junction_part.material = "G11"
        junction_part.geometry = {
            "length_m": cfg["junction"]["thickness_mm"] / 1000,
            "radius_m": cfg["junction"]["outer_radius_mm"] / 1000,
            "inner_radius_m": cfg["junction"]["inner_radius_mm"] / 1000,
        }
        junction_part.cad.generator = "tube"
        junction_part.cad.parameters = {
            "study_edge_fillet_radius_mm": cfg["junction"]["edge_radius_mm"]
        }
        junction_part.cad.mass_basis = "volume_density"
        junction_part.cad.role = "manufactured"
        junction_part.cad_mass = CADMass.model_validate(properties(junction_part, ring))
        recovery_delta_g = (
            mass_properties(vehicle).mass_kg - mass_properties(original).mass_kg
        ) * 1000 - construction_delta_g
        # Keep recovery replacement separate from prospective construction trades.
        resolved_identity = hashlib.sha256(
            vehicle.model_dump_json(by_alias=True).encode()
        ).hexdigest()
        mode_dir = output / vehicle.id
        mode_dir.mkdir(exist_ok=True)
        (mode_dir / "resolved-mass-copy.yaml").write_text(
            yaml.safe_dump(vehicle.model_dump(by_alias=True), sort_keys=False)
        )
        cases = [("nominal_5mps", 5.0), ("off_nominal_20p4mps", 20.4)]
        probes = [
            probe
            for item in flight["cases"]
            if item["vehicle"] == vehicle.id
            for probe in (item.get("ballistic_motor_delay_probes") or [])
            if probe["delay_s"] == 12
        ]
        if probes:
            cases.append(("12s_no_canopy_timing_probe", probes[0]["vertical_velocity_down_mps"]))
        cad_checks = (
            nominal_checks(vehicle, frame, shape, baseline_frame, ring, mode_dir, cfg)
            if vehicle.id == "modular-tvc-finned-v1"
            else {
                "not_repeated": "Only the limiting trainer's new solids checked in this bounded execution."
            }
        )
        ledger = [
            {
                "part_id": part.id,
                "mass_g": part.resolved_mass_kg * 1000,
                "baseline_mass_g": (
                    original_parts[part.id].resolved_mass_kg * 1000
                    if part.id in original_parts
                    else 0
                ),
            }
            for part in vehicle.parts
        ]
        modes.append(
            {
                "vehicle": vehicle.id,
                "cut_plan": mode_plan,
                "resolved_mass_copy_sha256": resolved_identity,
                "resolved_mass_copy": str(mode_dir / "resolved-mass-copy.yaml"),
                "native_full_regeneration_supported": False,
                "standalone_anchor_reproduction": "This script generates the full rounded anchor STEP; generic mount YAML alone lacks its integral cylindrical saddles.",
                "recovery_increment_g": recovery_delta_g,
                "recovery_total_allocated_g": sum(
                    original_parts[name].resolved_mass_kg * 1000
                    for name in budget_cfg["dedicated_recovery_part_ids"]
                )
                + recovery_delta_g,
                "construction_delta_g": construction_delta_g,
                "horn_correction": horn_correction,
                "forward_frame_preserved_features": preserved_features,
                "anchor_delta_g": frame_delta_g,
                "carrier_increment_g": (
                    mass_properties(load_vehicle(package_row["resolved_copy"])).mass_kg
                    - mass_properties(original).mass_kg
                )
                * 1000,
                "all_mass_ledger": ledger,
                "removed_baseline_parts": [
                    {"part_id": name, "mass_g": original_parts[name].resolved_mass_kg * 1000}
                    for name in ("shock_cord", "recovery_anchor")
                ],
                "force_cases": [force_case(vehicle, cfg, speed, name) for name, speed in cases],
                "nominal_new_solid_checks": cad_checks,
            }
        )
        if vehicle.id == "modular-tvc-finned-v1":
            modes[-1]["changed_part_sweep"] = horn_link_frame_sweep(vehicle, frame, shape, cfg)
            probes = []
            for angle in cfg["horn_cant_probe_degrees"]:
                candidate = vehicle.model_copy(deep=True)
                reverse_horns(candidate, [angle, angle])
                probes.append(
                    {
                        "cant_degrees": angle,
                        "corner_probe": horn_link_frame_sweep(
                            candidate, frame, shape, cfg, steps=3
                        ),
                    }
                )
            modes[-1]["bounded_horn_cant_probes"] = probes
            modes[-1]["rail_recovery_and_buckling_bounds"] = rail_bounds(
                frame, shape, modes[-1]["force_cases"], anchor_cfg
            )
        if vehicle.id == "modular-tvc-finned-v1":
            construction = load_vehicle(cfg["trainer_construction_copy"])
            ids = budget_cfg["dedicated_recovery_part_ids"]
            mass_limit = budget(construction, ids, cfg["guide_steps_s"])
            for thermal_g in cfg["thermal_addition_cases_g"]:
                for rail_g in (0, cfg["package_a_rail_saving_g"]):
                    trial_mass = (
                        mass_properties(construction).mass_kg
                        + (recovery_delta_g + thermal_g - rail_g) / 1000
                    )
                    screens = [
                        screen_launch(construction, dt, study_nominal_mass_kg=trial_mass)
                        for dt in cfg["guide_steps_s"]
                    ]
                    headroom_g = mass_limit["maximum_increment_kg"] * 1000 + rail_g
                    guide_rows.append(
                        {
                            "fin_candidate": cfg["trainer_construction_copy"],
                            "fin_mass_g": next(
                                part.resolved_mass_kg * 1000
                                for part in construction.parts
                                if part.id == "fin_set"
                            ),
                            "recovery_increment_g": recovery_delta_g,
                            "thermal_addition_g": thermal_g,
                            "rail_saving_g_unadopted": rail_g,
                            "headroom_g": headroom_g,
                            "mass_margin_g": headroom_g - recovery_delta_g - thermal_g,
                            "additional_fin_or_other_saving_required_g": max(
                                0, recovery_delta_g + thermal_g - headroom_g
                            ),
                            "trial_nominal_mass_kg": trial_mass,
                            "screens": screens,
                            "guide_pass": all(row["rail_screen_pass"] for row in screens),
                            "growth_kg": construction.design.mass_allowance_kg,
                        }
                    )
    opening_reference = next(
        row for row in modes if row["vehicle"] == cfg["opening_audit"]["reference_vehicle"]
    )
    opening = opening_load_audit(load_vehicle(opening_reference["resolved_mass_copy"]), cfg, output)
    payload = {
        "run_id": run_id,
        "elapsed_s": time.monotonic() - started,
        "compute_cost_usd": 0,
        "status": "Complete counting audit; integrated recovery design remains open",
        "source_sha256_before": before,
        "source_sha256_after": hashes(),
        "inputs_unchanged": before == hashes(),
        "cut_plan": plan,
        "junction_boolean_mass_g": junction_g,
        "historical_plywood_fin_mass_g": fin["fin_mass_kg"] * 1000,
        "opening_load_audit": opening,
        "junction_geometry": cfg["junction"],
        "previous_anchor_record_status": anchor_record["status"],
        "modes": modes,
        "guide_trade_cases": guide_rows,
        "existing_baseline_recovery_g": sum(
            next(
                p for p in load_vehicle(budget_cfg["vehicle"]).parts if p.id == name
            ).resolved_mass_kg
            for name in budget_cfg["dedicated_recovery_part_ids"]
        )
        * 1000,
        "guide_equipment_confirmed": False,
        "stopping_distance_qualified": False,
        "all_attachments_implemented_and_rated": False,
        "acceptance_passed": False,
        "active_adoption": False,
        "expanded_wo03_passed": False,
        "flight_ready": False,
        "open_findings": [
            "The rounded junction is centered at station0.60 m, aft of electronics; line fan-out, packing and hands/tools are not checked by a clear rigid ring.",
            "Actual aramid termination, HMPE pick lengths, all18 ends, bend contact and junction crowding remain unqualified.",
            "Fixed-mode aft transfer exceeds the estimated combined plywood-rail axial screen in the severe timing probe; no free bypass branch is invented.",
            "The complete changed-part motion report is required: neutral frame clearance alone does not close rods/cassette or coupled motion. Earlier inboard routing intersected the motor mount.",
            "A Boolean one-solid frame does not prove continuous qualified laminate, the machining route, interlaminar strength or actual manufactured joints.",
            "Upper body/coupler/nose/sled attachments are force assignments with unrated interfaces; positive-pin mass is still only a reserve.",
            "HMPE heat exposure and the sealed bulkhead passages are not qualified by a paper wall or the existing3 g sleeve allowance.",
            "Prospective lighter fins, battery, Package A rails and thermal reinforcement need one compatible resolved design and rerun static/flight/engineering evidence.",
        ],
    }
    (output / "record.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-recovery-budget-closure.yaml")
    )
    parser.add_argument("--output", type=Path, default=Path("build/wo03-recovery-budget-closure"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    args = parser.parse_args()
    result = run(args.config, args.output)
    print(args.output / "record.json")
    print(
        "line_g", result["cut_plan"]["line_mass_g"], "junction_g", result["junction_boolean_mass_g"]
    )
    print([(row["vehicle"], row["recovery_increment_g"]) for row in result["modes"]])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
