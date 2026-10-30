"""Quantitative recovery-package, access and electrical-integration screen.

This module reports resolved-envelope clearances and prescribed opening-load
demands. It does not infer fabric packing density, component ratings, or physical
fit from estimated CAD envelopes.
"""

from __future__ import annotations

import math
from itertools import combinations
from typing import Any

from src.cad.parts import placed_shape
from src.vehicle.mass import mass_properties
from src.vehicle.schema import Part, Vehicle

SOFT_PARTS = ("parachute", "shock_cord", "recovery_protection")
RECOVERY_PACKAGE = (
    "independent_recovery",
    "recovery_battery",
    "recovery_power_switch",
    "recovery_mount_carrier",
    "recovery_alignment_pins",
    "recovery_mount_hardware_allowance",
    "recovery_output_harness",
)
RIGID_CHECK = (
    "recovery_bulkhead",
    "recovery_anchor",
    "independent_recovery",
    "recovery_battery",
    "recovery_power_switch",
    "recovery_mount_carrier",
    "recovery_alignment_pins",
    "flight_computer",
    "battery",
    "arming_switch",
    "imu",
    "baro",
    "micro_sd",
    "high_g_accel",
)


def _part_map(vehicle: Vehicle) -> dict[str, Part]:
    return {part.id: part for part in vehicle.parts}


def _bounds(part: Part) -> dict[str, float]:
    shape = placed_shape(part)
    box = shape.BoundingBox()
    radius = math.hypot(max(abs(box.xmin), abs(box.xmax)), max(abs(box.ymin), abs(box.ymax)))
    return {
        "station_front_m": box.zmin / 1000,
        "station_aft_m": box.zmax / 1000,
        "axial_extent_m": box.zlen / 1000,
        "cross_x_mm": box.xlen,
        "cross_y_mm": box.ylen,
        "max_corner_radius_mm": radius,
    }


def _opening_cases(vehicle: Vehicle, cfg: dict[str, Any]) -> dict[str, Any]:
    mp = mass_properties(vehicle)
    allowance = float(vehicle.design.mass_allowance_kg if vehicle.design else 0)
    factor = float(cfg["loads"]["design_factor"])
    cases = []
    for velocity in cfg["loads"]["recovery_velocity_mps"]:
        for stopping_distance in cfg["loads"]["recovery_stopping_distance_m"]:
            acceleration = velocity**2 / (2 * stopping_distance) + 9.80665
            demand = (mp.mass_kg + allowance) * acceleration
            cases.append(
                {
                    "opening_velocity_mps": float(velocity),
                    "stopping_distance_m": float(stopping_distance),
                    "vehicle_mass_kg": mp.mass_kg,
                    "mass_allowance_kg": allowance,
                    "effective_mass_kg": mp.mass_kg + allowance,
                    "constant_deceleration_plus_gravity_mps2": acceleration,
                    "anchor_load_unfactored_n": demand,
                    "anchor_load_factored_n": factor * demand,
                    "design_factor": factor,
                    "basis": "Constant deceleration over configured stopping distance plus gravity; no snap/opening-shock multiplier.",
                }
            )
    return {
        "vehicle_mass_kg": mp.mass_kg,
        "mass_allowance_kg": allowance,
        "effective_mass_kg": mp.mass_kg + allowance,
        "cases": cases,
        "maximum_case": max(cases, key=lambda case: case["anchor_load_factored_n"]),
    }


def _electrical(vehicle: Vehicle, cfg: dict[str, Any]) -> dict[str, Any]:
    edges: list[dict[str, Any]] = []
    for net in vehicle.netlist:
        targets = [net.to] if isinstance(net.to, str) else list(net.to)
        edges.append(
            {
                "net": net.net,
                "from": net.source,
                "to": targets,
                "gauge_awg": net.gauge_awg,
                "pin": net.pin,
            }
        )
    recovery_nets = {
        "RECOVERY_BAT_POS",
        "RECOVERY_ARMED_POS",
        "RECOVERY_RETURN",
        "RECOVERY_OUTPUT_BUNDLE",
        "RECOVERY_INDEPENDENT",
    }
    recovery_edges = [edge for edge in edges if edge["net"] in recovery_nets]
    power_parts = {part.id: part for part in vehicle.parts}
    expected = {
        ("RECOVERY_BAT_POS", "recovery_battery", "recovery_power_switch"),
        ("RECOVERY_ARMED_POS", "recovery_power_switch", "independent_recovery"),
        ("RECOVERY_RETURN", "recovery_battery", "independent_recovery"),
        ("RECOVERY_OUTPUT_BUNDLE", "independent_recovery", "recovery_output_harness"),
    }
    observed = {
        (edge["net"], edge["from"], target) for edge in recovery_edges for target in edge["to"]
    }
    main_nodes = {
        item
        for edge in edges
        if edge["net"] not in recovery_nets
        for item in [edge["from"], *edge["to"]]
    }
    recovery_nodes = {item for edge in recovery_edges for item in [edge["from"], *edge["to"]]}
    recovery_battery = power_parts.get("recovery_battery")
    controller = power_parts.get("independent_recovery")
    switch = power_parts.get("recovery_power_switch")
    battery_v = (
        recovery_battery.electrical.nominal_v
        if recovery_battery and recovery_battery.electrical
        else None
    )
    capacity = (
        recovery_battery.electrical.capacity_mah
        if recovery_battery and recovery_battery.electrical
        else None
    )
    return {
        "recovery_edges": recovery_edges,
        "expected_edges_present": expected <= observed,
        "no_shared_nodes_with_main_power_or_flight_computer": not (recovery_nodes & main_nodes),
        "unexpected_direct_main_battery_net": any(
            edge["net"] == "RECOVERY_INDEPENDENT" and edge["from"] == "battery"
            for edge in recovery_edges
        ),
        "positive_line_opened_by_switch": (
            ("RECOVERY_BAT_POS", "recovery_battery", "recovery_power_switch") in observed
            and ("RECOVERY_ARMED_POS", "recovery_power_switch", "independent_recovery") in observed
        ),
        "return_line_is_direct_unswitched": (
            "RECOVERY_RETURN",
            "recovery_battery",
            "independent_recovery",
        )
        in observed,
        "battery_nominal_voltage_v": battery_v,
        "battery_capacity_mah": capacity,
        "battery_mass_kg_estimate": recovery_battery.mass_kg if recovery_battery else None,
        "controller_electrical_profile": (
            controller.electrical.model_dump() if controller and controller.electrical else None
        ),
        "switch_electrical_profile": (
            switch.electrical.model_dump() if switch and switch.electrical else None
        ),
        "assumed_output_pulse_a": cfg["power"]["recovery_output_pulse_a"],
        "assumed_output_pulse_s": cfg["power"]["recovery_output_pulse_s"],
        "assumed_output_voltage_v": cfg["power"]["recovery_output_v"],
        "assumed_output_energy_j": cfg["power"]["recovery_output_pulse_a"]
        * cfg["power"]["recovery_output_pulse_s"]
        * cfg["power"]["recovery_output_v"],
        "current_power_ratings_verified": False,
        "unresolved": [
            "Recovery battery, controller and switch have no resolved electrical ratings in the vehicle spec.",
            "The active mode netlist must be checked for dedicated positive, switched-positive and return paths; a direct-main-battery edge does not provide an isolated supply.",
            "Battery pulse-current/ESR, converter input current, output waveform, continuity load and connector ratings are unmeasured.",
        ],
    }


def recovery_integration(vehicle: Vehicle, cfg: dict[str, Any]) -> dict[str, Any]:
    """Summarize current soft-package fit, access envelopes and recovery demands."""
    parts = _part_map(vehicle)
    needed = (
        set(SOFT_PARTS)
        | set(RECOVERY_PACKAGE)
        | set(RIGID_CHECK)
        | {
            "body_upper",
            "nose_cone",
            "avionics_bay",
            "recovery_bulkhead",
            "recovery_anchor",
            "recovery_battery",
            "recovery_power_switch",
        }
    )
    missing = sorted(needed - set(parts))
    if missing:
        raise ValueError(f"missing required recovery integration parts: {missing}")

    body = parts["body_upper"]
    nose = parts["nose_cone"]
    bay = parts["avionics_bay"]
    bulkhead = parts["recovery_bulkhead"]
    anchor = parts["recovery_anchor"]
    nose_id = float(nose.cad.parameters.get("shoulder_inner_mm", 0)) if nose.cad else 0.0
    body_id = 2 * float(body.geometry.get("inner_radius_m", 0)) * 1000
    soft_bounds = {part_id: _bounds(parts[part_id]) for part_id in SOFT_PARTS}
    package_front = min(bounds["station_front_m"] for bounds in soft_bounds.values())
    package_aft = max(bounds["station_aft_m"] for bounds in soft_bounds.values())
    package_radius = max(bounds["max_corner_radius_mm"] for bounds in soft_bounds.values())
    soft_box_volume = sum(
        parts[part_id].geometry["bbox_m"][0]
        * parts[part_id].geometry["bbox_m"][1]
        * parts[part_id].geometry["bbox_m"][2]
        for part_id in SOFT_PARTS
    )
    soft_mass = sum(float(parts[part_id].resolved_mass_kg) for part_id in SOFT_PARTS)
    soft_bounds_mass_is_estimated = any(parts[part_id].estimate for part_id in SOFT_PARTS)
    opening = _opening_cases(vehicle, cfg)
    max_factored = float(opening["maximum_case"]["anchor_load_factored_n"])
    washer_od = 8.0
    bulkhead_hole = (
        float(bulkhead.cad.parameters.get("anchor_hole_mm", 3.4)) if bulkhead.cad else 3.4
    )
    washer_area = math.pi / 4 * (washer_od**2 - bulkhead_hole**2)
    m3_gross_area = math.pi * 3.0**2 / 4
    m3_tensile_area = 5.03

    envelope_parts = [parts[part_id] for part_id in RECOVERY_PACKAGE]
    package_envelopes = {part.id: _bounds(part) for part in envelope_parts}
    package_masses = {part.id: float(part.resolved_mass_kg) for part in envelope_parts}
    total_recovery_electronics_mass = sum(package_masses.values())

    # BRep intersections between nominal rigid components/electronics in the
    # shared bay; soft fabric, wires and budget allowances are intentionally not
    # collision-qualified by these solid checks.
    rigid_ids = []
    for part_id in RIGID_CHECK:
        definition = parts[part_id].cad
        if definition and definition.generator != "budget" and definition.role != "soft_stowage":
            rigid_ids.append(part_id)
    shapes = {part_id: placed_shape(parts[part_id]) for part_id in rigid_ids}
    overlap_pairs = []
    for first, second in combinations(rigid_ids, 2):
        a, b = shapes[first].BoundingBox(), shapes[second].BoundingBox()
        if (
            a.xmin >= b.xmax
            or b.xmin >= a.xmax
            or a.ymin >= b.ymax
            or b.ymin >= a.ymax
            or a.zmin >= b.zmax
            or b.zmin >= a.zmax
        ):
            continue
        volume = float(shapes[first].intersect(shapes[second]).Volume())
        if volume > 1e-6:
            overlap_pairs.append({"part_ids": [first, second], "overlap_volume_mm3": volume})

    netlist = _electrical(vehicle, cfg)
    switch_bounds = package_envelopes["recovery_power_switch"]
    carrier_bounds = package_envelopes["recovery_mount_carrier"]
    board = parts["independent_recovery"]
    board_holes = board.cad.parameters.get("mount_holes_mm", []) if board.cad else []
    hole_x = [float(point[0]) for point in board_holes]
    hole_z = [float(point[-1]) for point in board_holes]
    pin_data = (
        parts["recovery_alignment_pins"].cad.parameters
        if parts["recovery_alignment_pins"].cad
        else {}
    )
    pin_diameter = float(pin_data.get("pins", [{}])[0].get("radius_mm", 0)) * 2
    output_bounds = package_envelopes["recovery_output_harness"]
    flight_harness_bounds = _bounds(parts["harness"])
    return {
        "configuration_id": vehicle.id,
        "mode": vehicle.design.mode if vehicle.design else None,
        "airframe_body_id_mm": body_id,
        "nose_shoulder_id_mm": nose_id,
        "nose_shoulder_inner_diameter_mm": nose_id * 2,
        "nose_throat_nominal_clearance_mm": (nose_id - package_radius) if nose_id else None,
        "body_bore_nominal_clearance_mm": body_id / 2 - package_radius,
        "soft_recovery_package": {
            "part_ids": list(SOFT_PARTS),
            "part_bounds": soft_bounds,
            "axial_front_m": package_front,
            "axial_aft_m": package_aft,
            "axial_length_mm": (package_aft - package_front) * 1000,
            "cross_section_circumscribed_diameter_mm": package_radius * 2,
            "sum_of_component_box_volumes_cm3": soft_box_volume * 1e6,
            "sum_of_estimated_component_masses_g": soft_mass * 1000,
            "component_masses_estimated": soft_bounds_mass_is_estimated,
            "nose_shoulder_overlap_length_mm": max(
                0.0,
                (
                    min(
                        package_aft,
                        nose.position_m
                        + float(nose.geometry["length_m"])
                        + float(nose.geometry.get("shoulder_length_m", 0)),
                    )
                    - max(package_front, nose.position_m + float(nose.geometry["length_m"]))
                )
                * 1000,
            ),
            "fabric_or_cord_solid_volume_lower_bound_m3": None,
            "fabric_volume_unavailable_reason": "The YAML contains whole-component estimated masses and soft envelope boxes, but no reliably measured textile/cord-only material masses or verified material densities; no rho-based solid-volume lower bound is supportable.",
            "packing_status": "CAD envelope bounds only; actual fold, compression, knots, connectors, extraction force and repeatable packing have not been verified.",
        },
        "shared_avionics_package": {
            "component_bounds": package_envelopes,
            "component_masses_kg": package_masses,
            "total_envelope_component_mass_g": total_recovery_electronics_mass * 1000,
            "carrier_axial_bounds_m": [
                carrier_bounds["station_front_m"],
                carrier_bounds["station_aft_m"],
            ],
            "switch_axial_bounds_m": [
                switch_bounds["station_front_m"],
                switch_bounds["station_aft_m"],
            ],
            "avionics_bay_envelope_station_m": [
                bay.position_m,
                bay.position_m + float(bay.geometry["length_m"]),
            ],
            "nominal_bore_diameter_mm": body_id,
            "rigid_brep_overlap_pair_count": len(overlap_pairs),
            "rigid_brep_overlap_pairs": overlap_pairs,
            "rigid_check_part_ids": rigid_ids,
            "rigid_check_limit": "Nominal rigid BRep solids only; flexible wires, strain relief, connectors, switch shaft, bushing, panel, hand/tool access and assembly sequence are not modeled.",
            "switch_access_status": "Open: switch envelope is internal and no sidewall opening, panel bushing, shaft projection, retention or tool/screwdriver envelope is modeled.",
            "switch_envelope_max_radius_mm": switch_bounds["max_corner_radius_mm"],
            "switch_bore_radial_gap_mm": body_id / 2 - switch_bounds["max_corner_radius_mm"],
            "controller_mount_hole_count": len(board_holes),
            "controller_mount_hole_pitch_x_mm": max(hole_x) - min(hole_x) if hole_x else None,
            "controller_mount_hole_pitch_z_mm": max(hole_z) - min(hole_z) if hole_z else None,
            "controller_mount_hole_diameter_mm": (
                float(board.cad.parameters.get("hole_diameter_mm", 0)) if board.cad else None
            ),
            "alignment_pin_diameter_mm": pin_diameter or None,
            "nominal_board_pin_radial_clearance_mm": (
                (float(board.cad.parameters.get("hole_diameter_mm", 0)) - pin_diameter) / 2
                if board.cad and pin_diameter
                else None
            ),
            "recovery_output_harness_to_switch_axial_gap_mm": (
                switch_bounds["station_front_m"] - output_bounds["station_aft_m"]
            )
            * 1000,
            "recovery_output_to_flight_harness_axial_overlap_mm": max(
                0.0,
                (
                    min(output_bounds["station_aft_m"], flight_harness_bounds["station_aft_m"])
                    - max(
                        output_bounds["station_front_m"], flight_harness_bounds["station_front_m"]
                    )
                )
                * 1000,
            ),
            "battery_definition_note": parts["recovery_battery"].learn,
            "battery_actual_electrical_profile": (
                parts["recovery_battery"].electrical.model_dump()
                if parts["recovery_battery"].electrical
                else None
            ),
            "nose_insertion_direction": "Soft recovery pack is proposed to enter from the removable nose toward the aft bulkhead; axial carrier electronics leave through the open aft end when the aft module is separated.",
            "insertion_access_status": "Nominal rectangular-envelope radial clearances are positive. Flexible pack compression and the required carrier/cable extraction trajectory are not validated by these bounds.",
        },
        "bulkhead_anchor": {
            "bulkhead_part_id": bulkhead.id,
            "bulkhead_station_m": bulkhead.position_m,
            "bulkhead_thickness_mm": float(bulkhead.geometry["length_m"]) * 1000,
            "bulkhead_diameter_mm": float(bulkhead.geometry["radius_m"]) * 2 * 1000,
            "bulkhead_to_body_radial_gap_mm_nominal": float(
                body.geometry["inner_radius_m"] - bulkhead.geometry["radius_m"]
            )
            * 1000,
            "anchor_part_id": anchor.id,
            "anchor_station_m": anchor.position_m,
            "anchor_length_mm": float(anchor.geometry["length_m"]) * 1000,
            "bulkhead_anchor_hole_mm": bulkhead_hole,
            "anchor_shank_diameter_mm_nominal": 3.0,
            "radial_shank_clearance_mm_nominal": (bulkhead_hole - 3.0) / 2,
            "washer_outer_diameter_mm_nominal": washer_od,
            "washer_annular_bearing_area_mm2": washer_area,
            "worst_factored_opening_load_n": max_factored,
            "M3_gross_shank_stress_mpa_at_worst_factored_case": max_factored / m3_gross_area,
            "M3_tensile_area_demand_mpa_at_worst_factored_case": max_factored / m3_tensile_area,
            "washer_average_bearing_pressure_mpa_at_worst_factored_case": max_factored
            / washer_area,
            "opening_cases": opening["cases"],
            "capacity_assessment": "Anchor/washer ratings, G11 hole bearing and plate bending, bulkhead-to-tube bond/retention, opening shock and harness attachment strength are unavailable; calculated demands are not compared to invented allowables.",
        },
        "electrical": netlist,
        "service_sequence": [
            "Keep both vehicle power systems unarmed and the recovery positive-line switch OFF. Disconnect/remove the dedicated recovery battery before handling the carrier; the recovery return conductor itself is direct and unswitched.",
            "Separate the aft module at the modular joint for aft access. Keep the recovery output harness controlled; its flex path and strain relief are budget-only and not modeled.",
            "Slide the recovery carrier axially through the open aft end only after its actual retention and connectors are released; replace the 1S battery with correct polarity and positive retention, then reconnect the isolated board and harness.",
            "Repack the parachute/protection/harness from the nose opening toward the bulkhead. Preserve a clear path past the 61.6 mm nominal nose-shoulder bore and inspect anchor/washer seating.",
            "After an aft-module swap, verify mechanical indexing, recovery harness/anchor engagement and electrical connections. Arm only after the external rotary-switch panel hole, bushing, retention and tool access are designed and physically checked; this CAD does not establish usable switch access.",
        ],
        "open_items": [
            "Physical canopy/harness/protection packing, neck passage, extraction and repacking repeatability.",
            "Anchor eye, washer, M3 strength, G11 hole bearing and bulkhead bending/bond/retention ratings and proof evidence.",
            "External rotary switch shaft, panel hole/bushing, screw or nut retention, actuation/tool access and accidental-contact protection.",
            "Cell connector, polarity protection, restraint, pulse current/voltage, controller consumption and complete manufacturer-approved ground test.",
            "Carrier positive retention, board fasteners, connector clearance, wire bend radius, flex strain relief and routing around the avionics sled.",
        ],
        "acceptance_closed": False,
        "flight_ready": False,
    }
