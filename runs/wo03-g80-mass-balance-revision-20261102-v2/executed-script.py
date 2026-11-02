"""Bounded C1 G80 mass, balance, guide, and fin-load study; no CAD/FEA/flight."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import resource
import shutil
import signal
import sys
import time
import traceback
from pathlib import Path

for _name in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ[_name] = "1"

PROCESS_CPU_START = time.process_time()
PROCESS_WALL_START = time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
signal.setitimer(signal.ITIMER_REAL, 30)

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-g80-mass-balance-revision.yaml"
OUT = ROOT / "runs/wo03-g80-mass-balance-revision-20261102-v2"
CPU_LIMIT_S = 20
WALL_LIMIT_S = 30
G = 9.80665


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def need(mapping: dict, path: str):
    value = mapping
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            raise KeyError(f"Missing required config key: {path}")
        value = value[key]
    return value


def kg_from_mm3(volume_mm3: float, density_kg_m3: float) -> float:
    return volume_mm3 * density_kg_m3 * 1e-9


def point_row(
    identifier: str, function: str, mass_kg: float, station_mm: float, basis: str
) -> dict:
    return {
        "id": identifier,
        "function": function,
        "mass_g": mass_kg * 1000,
        "station_mm": station_mm,
        "basis": basis,
    }


def signed_change(row: dict, sign: float) -> dict:
    mass_kg = float(row["mass_g"]) / 1000 * sign
    station_m = float(row["station_mm"]) / 1000
    return {
        "id": row["id"],
        "function": row["function"],
        "mass_delta_kg": mass_kg,
        "first_moment_delta_kg_m": mass_kg * station_m,
        "station_mm": row["station_mm"],
        "basis": row["basis"],
    }


def apply_changes(
    base_mass_kg: float, base_moment_kg_m: float, changes: list[dict]
) -> tuple[float, float]:
    return (
        base_mass_kg + sum(c["mass_delta_kg"] for c in changes),
        base_moment_kg_m + sum(c["first_moment_delta_kg_m"] for c in changes),
    )


def fin_load_screen(geometry: dict, q_pa: float, alpha_deg: float, factor: float) -> dict:
    span, root, tip = geometry["span_m"], geometry["root_chord_m"], geometry["tip_chord_m"]
    area = span * (root + tip) / 2
    ar = 2 * span**2 / area
    slope = 2 * math.pi * ar / (2 + math.sqrt(4 + ar**2))
    force = q_pa * area * slope * math.radians(alpha_deg)
    arm = span * (root + 2 * tip) / (3 * (root + tip))
    moment = force * arm
    return {
        "planform_area_per_fin_m2": area,
        "aspect_ratio": ar,
        "normal_force_slope_per_rad": slope,
        "normal_force_per_fin_unfactored_N": force,
        "root_arm_m_existing_formula": arm,
        "root_moment_per_fin_unfactored_Nm": moment,
        "DF3_once_force_per_fin_N": factor * force,
        "DF3_once_root_moment_per_fin_Nm": factor * moment,
        "strength_and_installed_root_status": "Open; load arithmetic only, no installed stiffness/strength/flutter acceptance",
    }


def recovery_force(
    mass_kg: float, velocity_mps: float, design_factor: float, stopping_m: float
) -> float:
    return design_factor * mass_kg * (velocity_mps**2 / (2 * stopping_m) + G)


def main() -> None:
    started, cpu_started = PROCESS_WALL_START, PROCESS_CPU_START
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite prior packet: {OUT}")
    OUT.mkdir(parents=True)
    shutil.copy2(CONFIG, OUT / "executed-config.yaml")
    shutil.copy2(Path(__file__), OUT / "executed-script.py")

    cfg = yaml.safe_load(CONFIG.read_text())
    required_paths = [
        "id",
        "status",
        "source_s3",
        "source_spec",
        "staged_checkout",
        "separate_full_growth_g",
        "growth_station_mm",
        "formal_static_margin_cal",
        "formal_departure_mps",
        "separate_planning_mps",
        "usable_probes_m",
        "budget.new_mass_scenarios",
        "budget.guide_probes_per_scenario",
        "budget.selected_configuration_required_travel_roots",
        "budget.root_bracket_m",
        "budget.cpu_s",
        "budget.wall_s",
        "receiver_replacement",
        "receiver_replacement.remove_s3_component_id_prefix",
        "receiver_replacement.material",
        "receiver_replacement.density_kg_m3",
        "receiver_replacement.closed_body.start_end_mm",
        "receiver_replacement.closed_body.inner_outer_radius_mm",
        "receiver_replacement.closed_body.thickness_mm",
        "receiver_replacement.local_fin_sockets.centers_station_mm",
        "receiver_replacement.local_fin_sockets.azimuths_deg",
        "receiver_replacement.local_fin_sockets.side_plate_count",
        "receiver_replacement.local_fin_sockets.side_plate_axial_radial_tangential_mm",
        "receiver_replacement.local_fin_sockets.floors_count",
        "receiver_replacement.local_fin_sockets.floor_axial_tangential_radial_mm",
        "receiver_replacement.local_fin_sockets.outer_bridge_count",
        "receiver_replacement.local_fin_sockets.bridge_axial_radial_tangential_mm",
        "receiver_replacement.local_fin_sockets.radial_mount_pad_count",
        "receiver_replacement.local_fin_sockets.mount_pad_axial_tangential_radial_mm",
        "receiver_replacement.integral_end_hardpoints.count",
        "receiver_replacement.integral_end_hardpoints.total_mass_g",
        "receiver_replacement.integral_end_hardpoints.stations_mm",
        "receiver_replacement.forward_motor_key_carriers",
        "receiver_replacement.new_joint_process_and_hardware",
        "receiver_replacement.forward_motor_key_carriers.count",
        "receiver_replacement.forward_motor_key_carriers.total_mass_g",
        "receiver_replacement.forward_motor_key_carriers.station_mm",
        "receiver_replacement.new_joint_process_and_hardware.mass_g",
        "receiver_replacement.new_joint_process_and_hardware.station_mm",
        "independent_motor_service",
        "independent_motor_service.replace_s3_aft_cap_bore_radius_mm",
        "independent_motor_service.retained_cap_outer_radius_mm",
        "independent_motor_service.arm_radial_length_tangential_width_axial_thickness_mm",
        "independent_motor_service.separate_retainer_arms_count",
        "independent_motor_service.extra_captive_keeper_budget_g",
        "independent_motor_service.station_mm",
        "fin_option.source_geometry",
        "fin_option.proposed_geometry",
        "fin_option.density_kg_m3",
        "fin_option.count",
        "fin_option.source_geometry.root_mm",
        "fin_option.source_geometry.span_mm",
        "fin_option.source_geometry.thickness_mm",
        "fin_option.source_geometry.station_mm",
        "fin_option.proposed_geometry.span_mm",
        "fin_option.proposed_geometry.root_mm",
        "fin_option.proposed_geometry.tip_mm",
        "fin_option.proposed_geometry.sweep_mm",
        "fin_option.proposed_geometry.station_mm",
        "fin_option.proposed_geometry.thickness_mm",
        "fin_option.force_case.dynamic_pressure_pa",
        "fin_option.force_case.alpha_deg",
        "fin_option.force_case.design_factor",
        "equipment_relocation.upper_bound_all_identified_equipment_at225mm_kg_m",
        "equipment_relocation.main_sled_and_equipment_mass_g",
        "equipment_relocation.illustration_forward_shift_mm",
        "nose_ballast_comparison.target_static_margin_cal",
        "nose_ballast_comparison.slug_station_mm",
        "nose_ballast_comparison.cylinder_diameter_length_mm",
        "nose_ballast_comparison.density_upper_kg_m3",
        "nose_ballast_comparison.carrier_and_restraint_mass_g",
        "nose_ballast_comparison.carrier_station_mm",
        "nose_ballast_comparison.material",
        "scenarios",
        "selected_preliminary_scenario",
        "required_travel_case",
        "recovery.nominal_mps",
        "recovery.severe_mps",
        "recovery.stopping_m",
        "recovery.design_factor",
    ]
    for path in required_paths:
        need(cfg, path)
    if cfg["status"] != "preliminary_mass_balance_only_not_active_not_structurally_accepted":
        raise ValueError(f"Unexpected config status: {cfg['status']}")
    if len(cfg["scenarios"]) != 4 or len(cfg["usable_probes_m"]) != 3:
        raise ValueError("Frozen C1 packet must contain four mass scenarios and three guide probes")
    for scenario in cfg["scenarios"]:
        for key in ("id", "fins", "ballast", "extra_aft_mass_g"):
            if key not in scenario:
                raise KeyError(f"Scenario lacks required field {key}: {scenario}")
    if cfg["budget"]["new_mass_scenarios"] != 4 or cfg["budget"]["guide_probes_per_scenario"] != 3:
        raise ValueError("Declared scenario/probe budget differs from frozen config")
    if cfg["selected_preliminary_scenario"] != cfg["required_travel_case"]:
        raise ValueError(
            "The selected preliminary scenario and required-travel root case must match"
        )
    if cfg["equipment_relocation"]["selected_moves"]:
        raise ValueError("This packet is frozen with no equipment relocations")

    s3_path = ROOT / cfg["source_s3"]
    source_path = ROOT / cfg["source_spec"]
    staged = ROOT / cfg["staged_checkout"]
    s3 = json.loads(s3_path.read_text())
    source = yaml.safe_load(source_path.read_text())
    source_ids = {p["id"] for p in source["parts"]}
    if len(source_ids) != 73:
        raise ValueError(
            f"Expected saved 73-part source spec, found {len(source_ids)} unique part IDs"
        )
    if s3.get("status") != "one_candidate_preliminary_hand_screen_not_accepted":
        raise ValueError(f"Unexpected saved S3 status: {s3.get('status')}")
    source_parts = {p["id"]: p for p in source["parts"]}
    if "motor" not in source_parts or "fin_set" not in source_parts:
        raise ValueError("Source spec lacks motor or fin_set")

    sys.path.insert(0, str(staged))
    os.chdir(staged)
    from src.vehicle.aero import center_of_pressure
    from src.vehicle.benchmark import screen_launch
    from src.vehicle.geometry import nose_radius, shape_properties
    from src.vehicle.schema import Vehicle

    vehicle = Vehicle.model_validate(source)
    if vehicle.design is None or vehicle.motor is None:
        raise ValueError("Source vehicle lacks design or motor")
    if not math.isclose(
        vehicle.design.mass_allowance_kg * 1000, cfg["separate_full_growth_g"], abs_tol=1e-6
    ):
        raise ValueError(
            "Source guide allowance does not match the separate full-growth allocation"
        )

    curve_path = Path(vehicle.motor.curve)
    if not curve_path.is_absolute():
        curve_path = staged / curve_path
    helper_paths = [
        staged / "src/vehicle/schema.py",
        staged / "src/vehicle/mass.py",
        staged / "src/vehicle/aero.py",
        staged / "src/vehicle/geometry.py",
        staged / "src/vehicle/benchmark.py",
        staged / "src/vehicle/motors.py",
        staged / "src/sim/frames.py",
        curve_path,
    ]
    input_paths = [CONFIG, s3_path, source_path, *helper_paths, Path(__file__).resolve()]
    input_hashes_before = {str(p.relative_to(ROOT)): sha256(p) for p in input_paths}

    s3_mass_g = float(s3["complete_preliminary_budget"]["loaded_full_mass_g"])
    s3_cg_mm = float(s3["complete_preliminary_budget"]["loaded_cg_station_mm"])
    base_mass_kg = s3_mass_g / 1000
    base_moment_kg_m = base_mass_kg * s3_cg_mm / 1000
    source_ledger = {p["id"]: p for p in s3["new_component_mass_ledger"]}
    channel_prefix = cfg["receiver_replacement"]["remove_s3_component_id_prefix"]
    channel_rows = [r for k, r in source_ledger.items() if k.startswith(channel_prefix)]
    if len(channel_rows) != 3:
        raise ValueError(f"Expected exactly three S3 channel rows; found {len(channel_rows)}")

    removed_rows: list[dict] = []
    for row in channel_rows:
        removed_rows.append(
            {
                **row,
                "function": "removed S3 continuous channel, replaced by C1 closed receiver and local socket structure",
            }
        )
    for identifier, function in [
        (
            "aft_integral_G11_annular_cap",
            "S3 aft cap annulus replaced with independent-motor-service bore",
        ),
        (
            "motor_aft_floating_annulus",
            "S3 floating aft motor plate replaced by three independent keeper arms",
        ),
        ("motor_aft_prong_0", "S3 aft plate radial prong removed"),
        ("motor_aft_prong_1", "S3 aft plate radial prong removed"),
        ("motor_aft_prong_2", "S3 aft plate radial prong removed"),
    ]:
        if identifier not in source_ledger:
            raise KeyError(f"Saved S3 mass ledger lacks required replacement part {identifier}")
        removed_rows.append({**source_ledger[identifier], "function": function})

    receiver = cfg["receiver_replacement"]
    density = receiver["density_kg_m3"]
    z0, z1 = receiver["closed_body"]["start_end_mm"]
    ri, ro = receiver["closed_body"]["inner_outer_radius_mm"]
    body_volume = math.pi * (ro**2 - ri**2) * (z1 - z0)
    additions: list[dict] = [
        point_row(
            "C1_closed_G11_body_annulus",
            "Continuous end-to-end receiver, body support, fin-socket foundation, and independent-motor-capture foundation",
            kg_from_mm3(body_volume, density),
            (z0 + z1) / 2,
            "Gross annulus R31.2-32 x 0.8 mm x 201.8 mm; no fin-slot cut credit",
        )
    ]
    sockets = receiver["local_fin_sockets"]
    side_axial, side_radial, side_tangent = sockets["side_plate_axial_radial_tangential_mm"]
    for i in range(sockets["side_plate_count"]):
        mass = kg_from_mm3(side_axial * side_radial * side_tangent, density)
        additions.append(
            point_row(
                f"C1_fin_socket_side_plate_{i + 1}",
                "Fin side contact, axial pin, and through-body tab socket",
                mass,
                sockets["centers_station_mm"][i // 2],
                "Gross rectangular plate from frozen dimensions",
            )
        )
    floor_axial, floor_tangent, floor_radial = sockets["floor_axial_tangential_radial_mm"]
    for i in range(sockets["floors_count"]):
        additions.append(
            point_row(
                f"C1_fin_socket_floor_{i + 1}",
                "Fin socket floor and local frame transfer",
                kg_from_mm3(floor_axial * floor_tangent * floor_radial, density),
                sockets["centers_station_mm"][i],
                "Gross rectangular floor from frozen dimensions",
            )
        )
    bridge_axial, bridge_radial, bridge_tangent = sockets["bridge_axial_radial_tangential_mm"]
    for i in range(sockets["outer_bridge_count"]):
        additions.append(
            point_row(
                f"C1_fin_socket_outer_bridge_{i + 1}",
                "Fin socket outer bridge / local frame transfer",
                kg_from_mm3(bridge_axial * bridge_radial * bridge_tangent, density),
                sockets["centers_station_mm"][i // 2],
                "Gross rectangular bridge from frozen dimensions",
            )
        )
    pad_axial, pad_tangent, pad_radial = sockets["mount_pad_axial_tangential_radial_mm"]
    for i in range(sockets["radial_mount_pad_count"]):
        additions.append(
            point_row(
                f"C1_radial_mount_pad_{i + 1}",
                "Radial through-body tab contact pad",
                kg_from_mm3(pad_axial * pad_tangent * pad_radial, density),
                sockets["centers_station_mm"][i],
                "Gross rectangular pad from frozen dimensions",
            )
        )

    hardpoints = receiver["integral_end_hardpoints"]
    hp_count_each = hardpoints["count"] // 2
    for end, station in enumerate(hardpoints["stations_mm"]):
        for i in range(hp_count_each):
            additions.append(
                point_row(
                    f"C1_integral_end_hardpoint_{end}_{i + 1}",
                    "Integral node and wall transition for one original M3 barrel nut / end contact",
                    hardpoints["total_mass_g"] / hardpoints["count"] / 1000,
                    station,
                    "Budgeted geometry; equal mass per node; local transitions included, no second bond capacity",
                )
            )
    key_carriers = receiver["forward_motor_key_carriers"]
    for i in range(key_carriers["count"]):
        additions.append(
            point_row(
                f"C1_forward_motor_key_carrier_{i + 1}",
                "One original 5 mm motor key pin carrier into closed receiver",
                key_carriers["total_mass_g"] / key_carriers["count"] / 1000,
                key_carriers["station_mm"],
                "18x12x6.6 mm G11 carrier plus wall-transition stock allocation",
            )
        )
    joint = receiver["new_joint_process_and_hardware"]
    additions.append(
        point_row(
            "C1_socket_joint_process_hardware",
            "Socket bonding, secondary retention, thread locks and local strain relief",
            joint["mass_g"] / 1000,
            joint["station_mm"],
            "Additional frozen allowance; existing S3 allocations remain counted",
        )
    )

    # Replace the aft annulus explicitly while preserving its outer radius and thickness.
    cap = source_ledger["aft_integral_G11_annular_cap"]
    service = cfg["independent_motor_service"]
    cap_volume = (
        math.pi
        * (
            service["retained_cap_outer_radius_mm"] ** 2
            - service["replace_s3_aft_cap_bore_radius_mm"] ** 2
        )
        * 6
    )
    new_cap_mass = kg_from_mm3(cap_volume, density)
    additions.append(
        point_row(
            "C1_aft_cap_15p8_bore",
            "Independent motor service cap annulus, retained at S3 aft-cap station",
            new_cap_mass,
            cap["station_mm"],
            "Gross R15.8-32 x 6 mm annulus; no holes or overlap deductions",
        )
    )

    arm_l, arm_w, arm_t = service["arm_radial_length_tangential_width_axial_thickness_mm"]
    for i in range(service["separate_retainer_arms_count"]):
        additions.append(
            point_row(
                f"C1_independent_motor_retainer_arm_{i + 1}",
                "One independent aft motor capture arm",
                kg_from_mm3(arm_l * arm_w * arm_t, density),
                service["station_mm"],
                "Gross G11 rectangular arm; no pin-hole/cut deductions",
            )
        )
    additions.append(
        point_row(
            "C1_captive_motor_keeper",
            "Captive keeper budget for independent aft motor arms",
            service["extra_captive_keeper_budget_g"] / 1000,
            service["station_mm"],
            "Frozen hardware allocation; no item selected",
        )
    )

    base_changes = [signed_change(r, -1) for r in removed_rows] + [
        signed_change(r, 1) for r in additions
    ]
    scenario_a_mass, scenario_a_moment = apply_changes(base_mass_kg, base_moment_kg_m, base_changes)

    # Candidate CP/fin geometry from the source Vehicle copy only; no old fin CAD mass reuse.
    fin_cfg = cfg["fin_option"]
    fin_part = next(p for p in vehicle.parts if p.id == "fin_set")
    source_fin_geom = copy.deepcopy(fin_part.geometry)
    source_panel = fin_cfg["source_geometry"]
    proposed_panel = fin_cfg["proposed_geometry"]
    proposed_geometry = {
        **source_fin_geom,
        "length_m": max(
            proposed_panel["root_mm"], proposed_panel["sweep_mm"] + proposed_panel["tip_mm"]
        )
        / 1000,
        "radius_m": source_fin_geom["radius_m"],
        "count": fin_cfg["count"],
        "span_m": proposed_panel["span_mm"] / 1000,
        "root_chord_m": proposed_panel["root_mm"] / 1000,
        "tip_chord_m": proposed_panel["tip_mm"] / 1000,
        "sweep_m": proposed_panel["sweep_mm"] / 1000,
        "thickness_m": proposed_panel["thickness_mm"] / 1000,
    }
    vehicle_c = copy.deepcopy(vehicle)
    next(p for p in vehicle_c.parts if p.id == "fin_set").geometry = proposed_geometry
    cp_a = center_of_pressure(vehicle)
    cp_c = center_of_pressure(vehicle_c)
    source_motor = next(p for p in vehicle.parts if p.id == "motor")
    motor_cg_mm = source_motor.cg_station_m * 1000
    propellant_kg = vehicle.motor.propellant_mass_kg
    if not math.isclose(propellant_kg * 1000, 62.5, abs_tol=1e-6):
        raise ValueError(
            f"Source motor propellant {propellant_kg * 1000:g} g differs from required 62.5 g burnout removal"
        )

    # B: carrier first, then solve only the ballast needed to reach original CP - 1 calibre.
    ballast_cfg = cfg["nose_ballast_comparison"]
    target_cg_mm = (
        cp_a * 1000
        - ballast_cfg["target_static_margin_cal"] * vehicle.airframe["body_diameter_m"] * 1000
    )
    carrier_mass_kg = ballast_cfg["carrier_and_restraint_mass_g"] / 1000
    carrier_station_m = ballast_cfg["carrier_station_mm"] / 1000
    target_m = target_cg_mm / 1000
    ballast_station_m = ballast_cfg["slug_station_mm"] / 1000
    ballast_kg = (
        scenario_a_moment
        - target_m * scenario_a_mass
        + carrier_mass_kg * (carrier_station_m - target_m)
    ) / (target_m - ballast_station_m)
    if ballast_kg < 0:
        raise ValueError(f"Analytic ballast solution is negative: {ballast_kg} kg")
    diameter_mm, length_mm = ballast_cfg["cylinder_diameter_length_mm"]
    ballast_volume_mm3 = math.pi * (diameter_mm / 2) ** 2 * length_mm
    ballast_capacity_kg = kg_from_mm3(ballast_volume_mm3, ballast_cfg["density_upper_kg_m3"])
    nose = source_parts["nose_cone"]
    ogive_inner_radii = []
    for x_mm in (
        ballast_cfg["slug_station_mm"] - length_mm / 2,
        ballast_cfg["slug_station_mm"] + length_mm / 2,
    ):
        outer = float(
            nose_radius(
                np.array([x_mm / 1000]),
                nose["geometry"]["length_m"],
                nose["geometry"]["radius_m"],
                nose["geometry"]["shape"],
            )[0]
        )
        inner_radius_mm = (outer - nose["geometry"]["wall_m"]) * 1000
        ogive_inner_radii.append(
            {
                "station_mm": x_mm,
                "outer_radius_mm": outer * 1000,
                "nominal_inner_radius_mm_after_wall": inner_radius_mm,
                "slug_radius_mm": diameter_mm / 2,
                "nominal_radial_clearance_mm": inner_radius_mm - diameter_mm / 2,
            }
        )

    original_fin_panel_kg = (
        fin_cfg["count"]
        * source_panel["root_mm"]
        * source_panel["span_mm"]
        * source_panel["thickness_mm"]
        * fin_cfg["density_kg_m3"]
        * 1e-9
    )
    new_panel_shape = shape_properties("fin_set", proposed_geometry)
    new_fin_panel_kg = new_panel_shape.volume_m3 * fin_cfg["density_kg_m3"]
    original_fin_part_kg = fin_part.resolved_mass_kg
    original_fin_station_mm = fin_part.cg_station_m * 1000
    original_fin_residual_kg = original_fin_part_kg - original_fin_panel_kg
    if original_fin_residual_kg < 0:
        raise ValueError("Source CAD fin part mass is below the removed rectangular panel mass")
    original_panel_station_mm = source_panel["station_mm"] + source_panel["root_mm"] / 2
    new_fin_station_mm = proposed_panel["station_mm"] + new_panel_shape.cg_offset_m * 1000
    fin_changes = [
        {
            "id": "source_rectangular_fin_panel_mass",
            "function": "Remove only original 3-plate rectangular fin panel mass; retain CAD residual/gussets/tabs",
            "mass_delta_kg": -original_fin_panel_kg,
            "first_moment_delta_kg_m": -original_fin_panel_kg * original_panel_station_mm / 1000,
            "station_mm": original_panel_station_mm,
            "basis": "3 x 120 x 70 x 6.35 mm x 715 kg/m3",
        },
        {
            "id": "proposed_clipped_trapezoid_fin_panel_mass",
            "function": "New 3-plate clipped/swept panel mass",
            "mass_delta_kg": new_fin_panel_kg,
            "first_moment_delta_kg_m": new_fin_panel_kg * new_fin_station_mm / 1000,
            "station_mm": new_fin_station_mm,
            "basis": "Existing shape_properties fin integration and 715 kg/m3; source CAD fin mass not reused",
        },
    ]
    original_deep_tab_delta = [
        r for r in s3["new_component_mass_ledger"] if r["id"].startswith("fin_tab_depth_delta_")
    ]
    if len(original_deep_tab_delta) != 3:
        raise ValueError("S3 deeper-tab delta rows are missing or duplicated")

    scenario_defs = cfg["scenarios"]
    scenarios = []
    for item in scenario_defs:
        changes = list(base_changes)
        cp_m = cp_a
        fin_geom = source_fin_geom
        selected_fin_changes = []
        if item["fins"] == "proposed":
            changes.extend(fin_changes)
            selected_fin_changes = fin_changes
            cp_m = cp_c
            fin_geom = proposed_geometry
        if item["ballast"]:
            carrier = point_row(
                "C1_nose_ballast_carrier_and_restraint",
                "Nonmetal ballast retention carrier and restraint budget",
                carrier_mass_kg,
                ballast_cfg["carrier_station_mm"],
                "Explicit 8 g source allocation; physical mount not defined",
            )
            slug = point_row(
                "C1_analytic_nose_ballast",
                "Analytic nonmetal ballast needed to reach original CP minus one calibre",
                ballast_kg,
                ballast_cfg["slug_station_mm"],
                "2400 kg/m3 maximum-density nonmetal cylinder capacity comparison; not a selected material",
            )
            changes.extend([signed_change(carrier, 1), signed_change(slug, 1)])
        extra_g = item["extra_aft_mass_g"]
        if extra_g:
            changes.append(
                {
                    "id": "C1_extra_aft_mass",
                    "function": "Additional scenario D mass at the specified aft station",
                    "mass_delta_kg": extra_g / 1000,
                    "first_moment_delta_kg_m": extra_g / 1000 * cfg["growth_station_mm"] / 1000,
                    "station_mm": cfg["growth_station_mm"],
                    "basis": "Additional 20 g beyond the separately retained 50 g",
                }
            )
        motor_shift_mm = item.get("motor_cg_aft_shift_mm", 0)
        if motor_shift_mm:
            motor_shift_moment = source_motor.resolved_mass_kg * motor_shift_mm / 1000
            changes.append(
                {
                    "id": "C1_motor_CG_probe",
                    "function": "Source motor mass unchanged; CG assumption shifted aft",
                    "mass_delta_kg": 0.0,
                    "first_moment_delta_kg_m": motor_shift_moment,
                    "station_mm": motor_cg_mm + motor_shift_mm,
                    "basis": "Illustrative 12.8 mm source sensitivity, not validated tolerance",
                }
            )
        mass_kg, moment_kg_m = apply_changes(base_mass_kg, base_moment_kg_m, changes)
        cg_mm = moment_kg_m / mass_kg * 1000
        burn_shift_mm = motor_shift_mm
        burnout_mass = mass_kg - propellant_kg
        burnout_moment = moment_kg_m - propellant_kg * (motor_cg_mm + burn_shift_mm) / 1000
        burnout_cg_mm = burnout_moment / burnout_mass * 1000
        loaded_margin = (cp_m * 1000 - cg_mm) / (vehicle.airframe["body_diameter_m"] * 1000)
        burnout_margin = (cp_m * 1000 - burnout_cg_mm) / (
            vehicle.airframe["body_diameter_m"] * 1000
        )

        rec = cfg["recovery"]

        demands = {
            "nominal_5m_s_loaded_N": recovery_force(
                mass_kg, rec["nominal_mps"], rec["design_factor"], rec["stopping_m"]
            ),
            "severe_20p4m_s_loaded_N": recovery_force(
                mass_kg, rec["severe_mps"], rec["design_factor"], rec["stopping_m"]
            ),
            "nominal_5m_s_burnout_N": recovery_force(
                burnout_mass, rec["nominal_mps"], rec["design_factor"], rec["stopping_m"]
            ),
            "severe_20p4m_s_burnout_N": recovery_force(
                burnout_mass, rec["severe_mps"], rec["design_factor"], rec["stopping_m"]
            ),
        }
        guide_results = []
        for usable_m in cfg["usable_probes_m"]:
            candidate = copy.deepcopy(vehicle)
            candidate.design.rail_length_m = usable_m
            screen = screen_launch(
                candidate, study_nominal_mass_kg=mass_kg - vehicle.design.mass_allowance_kg
            )
            guide_results.append(
                {
                    "usable_m": usable_m,
                    "conditional_overall_rail_m_under_old_lug_start_assumption": usable_m + 1.077,
                    **screen,
                }
            )
        panel_cfg = fin_cfg["force_case"]
        fin_loads = fin_load_screen(
            fin_geom,
            panel_cfg["dynamic_pressure_pa"],
            panel_cfg["alpha_deg"],
            panel_cfg["design_factor"],
        )
        scenarios.append(
            {
                "id": item["id"],
                "fins": item["fins"],
                "ballast_mode": item["ballast"],
                "loaded_mass_kg": mass_kg,
                "loaded_first_moment_kg_m": moment_kg_m,
                "loaded_cg_mm": cg_mm,
                "cp_mm": cp_m * 1000,
                "loaded_static_margin_cal": loaded_margin,
                "burnout_mass_kg": burnout_mass,
                "burnout_first_moment_kg_m": burnout_moment,
                "burnout_cg_mm": burnout_cg_mm,
                "burnout_static_margin_cal": burnout_margin,
                "motor_CG_assumption_mm": motor_cg_mm + motor_shift_mm,
                "motor_shift_mm": motor_shift_mm,
                "recovery_demands_N": demands,
                "guide_screens": guide_results,
                "fin_load_screen": fin_loads,
                "mass_changes": changes,
                "new_fin_panel_change_rows": selected_fin_changes,
                "ballast_details": None
                if not item["ballast"]
                else {
                    "carrier_g": ballast_cfg["carrier_and_restraint_mass_g"],
                    "carrier_station_mm": ballast_cfg["carrier_station_mm"],
                    "required_slug_g": ballast_kg * 1000,
                    "slug_station_mm": ballast_cfg["slug_station_mm"],
                    "capacity_g_at_max_density": ballast_capacity_kg * 1000,
                    "within_analytic_mass_capacity": ballast_kg <= ballast_capacity_kg,
                    "slug_volume_mm3": ballast_volume_mm3,
                    "nose_inner_radius_checks": ogive_inner_radii,
                    "nose_check_scope": "Nominal internal radial-radius comparison only; packing, shoulder interference, mount, retention and actual nose cavity are unverified.",
                },
            }
        )

    selected_id = cfg["required_travel_case"]
    selected = next(s for s in scenarios if s["id"] == selected_id)
    root_case_mass = selected["loaded_mass_kg"]
    root_targets = cfg["budget"]["selected_configuration_required_travel_roots"]
    lo_bracket, hi_bracket = cfg["budget"]["root_bracket_m"]

    def speed_at_travel(travel_m: float) -> float | None:
        candidate = copy.deepcopy(vehicle)
        candidate.design.rail_length_m = travel_m
        return screen_launch(
            candidate, study_nominal_mass_kg=root_case_mass - vehicle.design.mass_allowance_kg
        )["rail_exit_speed_mps"]

    roots = {}
    lo_speed, hi_speed = speed_at_travel(lo_bracket), speed_at_travel(hi_bracket)
    for target in root_targets:
        if lo_speed is None or hi_speed is None or lo_speed > target or hi_speed < target:
            roots[str(target)] = {
                "status": "target_not_bracketed",
                "bracket_usable_m": [lo_bracket, hi_bracket],
                "speed_bracket_mps": [lo_speed, hi_speed],
            }
            continue
        lo, hi = lo_bracket, hi_bracket
        for _ in range(24):
            mid = (lo + hi) / 2
            mid_speed = speed_at_travel(mid)
            if mid_speed is not None and mid_speed >= target:
                hi = mid
            else:
                lo = mid
        travel = (lo + hi) / 2
        roots[str(target)] = {
            "status": "screen_root",
            "required_usable_travel_m_interval": [lo, hi],
            "estimated_exit_speed_bracket_mps": [speed_at_travel(lo), speed_at_travel(hi)],
            "conditional_overall_rail_m_under_old_lug_start_assumption": travel + 1.077,
            "iterations": 24,
            "available_equipment": False,
        }

    if {r["id"] for r in removed_rows if r["id"].startswith(channel_prefix)} != {
        r["id"] for r in channel_rows
    }:
        raise ValueError("Channel replacement removal set changed unexpectedly")
    hashes_after = {str(p.relative_to(ROOT)): sha256(p) for p in input_paths}
    if hashes_after != input_hashes_before:
        raise RuntimeError("Frozen inputs changed during the packet")
    elapsed, cpu_elapsed = time.monotonic() - started, time.process_time() - cpu_started
    if elapsed > WALL_LIMIT_S or cpu_elapsed > CPU_LIMIT_S:
        raise TimeoutError(f"Declared budget exceeded: wall={elapsed:.3f}s cpu={cpu_elapsed:.3f}s")

    record = {
        "status": "one_bounded_mass_balance_packet_only_not_accepted",
        "candidate_id": cfg["id"],
        "active_spec_changed": False,
        "native_or_flight_execution": False,
        "input_sha256": input_hashes_before,
        "source_s3_loaded_mass_kg": base_mass_kg,
        "source_s3_loaded_cg_mm": s3_cg_mm,
        "source_s3_loaded_first_moment_kg_m": base_moment_kg_m,
        "source_73_nominal_mass_g": s3.get("source_73_nominal_mass_g"),
        "burnout_mass_basis": {
            "source_propellant_mass_removed_g": propellant_kg * 1000,
            "source_motor_CG_station_mm": motor_cg_mm,
            "scenario_D_motor_CG_probe_mm": 12.8,
            "D_shift_applied_to_propellant_removal_station": True,
            "full_50g_growth_unchanged_at_configured_station": True,
        },
        "source_full_growth": {
            "mass_g": cfg["separate_full_growth_g"],
            "station_mm": cfg["growth_station_mm"],
            "retained_once": True,
        },
        "removed_s3_components": removed_rows,
        "retained_s3_mass_ledger_component_ids": [
            r["id"]
            for r in s3["new_component_mass_ledger"]
            if r["id"] not in {x["id"] for x in removed_rows}
        ],
        "added_c1_components": additions,
        "base_replacement_mass_changes": base_changes,
        "mass_scenario_results": scenarios,
        "fin_panel_accounting": {
            "original_fin_set_cad_mass_g": original_fin_part_kg * 1000,
            "original_rectangular_panels_removed_g": original_fin_panel_kg * 1000,
            "original_fin_CAD_residual_retained_g": original_fin_residual_kg * 1000,
            "original_fin_centroid_mm": original_fin_station_mm,
            "original_panel_centroid_mm": original_panel_station_mm,
            "new_panel_mass_g": new_fin_panel_kg * 1000,
            "new_panel_centroid_mm": new_fin_station_mm,
            "source_tab_and_gusset_residual_retained": True,
            "S3_deeper_tab_delta_rows_retained_once": original_deep_tab_delta,
            "CP_recomputed_from_source_vehicle_copy_updated_fin_geometry": cp_c * 1000,
        },
        "nose_ballast_capacity": {
            "slug_cylinder_diameter_length_mm": [diameter_mm, length_mm],
            "maximum_nonmetal_density_kg_m3": ballast_cfg["density_upper_kg_m3"],
            "mass_capacity_g": ballast_capacity_kg * 1000,
            "outer_radii_at_slug_end_stations": ogive_inner_radii,
            "no_pack_retention_or_cavity_pass_claimed": True,
        },
        "equipment_relocation_audit": {
            **cfg["equipment_relocation"],
            "selected_moves": [],
            "five_mm_whole_main_sled_and_equipment_first_moment_gain_kg_m": cfg[
                "equipment_relocation"
            ]["main_sled_and_equipment_mass_g"]
            / 1000
            * cfg["equipment_relocation"]["illustration_forward_shift_mm"]
            / 1000,
            "S3_balance_deficit_kg_m_approx": (s3_mass_g / 1000)
            * (
                (
                    s3_cg_mm
                    - (
                        center_of_pressure(vehicle) * 1000
                        - vehicle.airframe["body_diameter_m"] * 1000
                    )
                )
                / 1000
            ),
            "growth_and_independent_recovery_power_moved": False,
        },
        "required_travel_roots_for_selected_C_case": {
            "case_id": selected_id,
            "roots": roots,
            "formal_departure_mps": cfg["formal_departure_mps"],
            "separate_planning_mps": cfg["separate_planning_mps"],
        },
        "model_limits": {
            "full_candidate_tensor": None,
            "tensor_status": "Unavailable; the source S3 ledger has no complete intrinsic inertia for C1 replacements or layout changes.",
            "structural_thermal_recovery_flight_equipment_and_active_acceptance": "Open; structural, thermal, full recovery, installed fin/root/flutter, exact motor, FAA/club/equipment, flight, and active adoption gates remain unclosed.",
            "launch_equipment": cfg["equipment_status"],
            "ballast_nose_scope": "Analytic mass/radius comparison only; not a packing, retention, materials, or anchor pass.",
            "fin_load_scope": "Existing 40 kPa / 5 degree equation scaled by DF3 once; new installed root/socket/strength/flutter remain open.",
            "motor_cg_shift": "Scenario D 12.8 mm exploratory source sensitivity only, not a manufacturer tolerance or validated bound.",
        },
        "resource": {
            "cpu_s": cpu_elapsed,
            "wall_s": elapsed,
            "threads": 1,
            "cpu_limit_s": CPU_LIMIT_S,
            "wall_limit_s": WALL_LIMIT_S,
        },
    }
    dump_json(OUT / "record.json", record)
    out_paths = [OUT / "executed-config.yaml", OUT / "executed-script.py", OUT / "record.json"]
    dump_json(
        OUT / "manifest.json",
        {
            "input_sha256": input_hashes_before,
            "output_sha256": {p.name: sha256(p) for p in out_paths},
            "status": record["status"],
        },
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # preserve the first attempt and do not retry
        OUT.mkdir(parents=True, exist_ok=True)
        if CONFIG.exists() and not (OUT / "executed-config.yaml").exists():
            shutil.copy2(CONFIG, OUT / "executed-config.yaml")
        if Path(__file__).exists() and not (OUT / "executed-script.py").exists():
            shutil.copy2(Path(__file__), OUT / "executed-script.py")
        dump_json(
            OUT / "record.json",
            {
                "status": "stopped_failure_preserved_no_retry",
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        try:
            artifacts = [
                OUT / "executed-config.yaml",
                OUT / "executed-script.py",
                OUT / "record.json",
            ]
            dump_json(
                OUT / "manifest.json",
                {
                    "output_sha256": {p.name: sha256(p) for p in artifacts if p.exists()},
                    "status": "stopped_failure_preserved_no_retry",
                },
            )
        except Exception:  # noqa: BLE001, S110
            pass
        raise
