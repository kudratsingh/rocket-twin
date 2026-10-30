"""Prototype a three-loop recovery bridle, including temporary CAD mass deltas."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.cad.parts import _base_shape, cq, tube
from src.vehicle.mass import mass_properties
from src.vehicle.schema import load_vehicle, vehicle_input_paths


def holes(shape, x, y, d, length):
    for angle in (0, 120, 240):
        for sign in (-1, 1):
            hole = cq.Solid.makeCylinder(
                d / 2, length + 2, cq.Vector(x, sign * y, -1), cq.Vector(0, 0, 1)
            )
            shape = shape.cut(hole.rotate((0, 0, 0), (0, 0, 1), angle))
    return shape


def cad_mass(part, cfg, fixed, thickness_override=None, finger_length=None):
    baseline = _base_shape(part)
    thickness = (
        thickness_override
        if thickness_override is not None
        else cfg["fixed_web_thickness_mm" if fixed else "tvc_web_thickness_mm"]
    )
    if fixed:
        proposal = part.model_copy(deep=True)
        proposal.geometry["length_m"] = finger_length / 1000
        proposal.cad.parameters["bond_fingers"]["length_mm"] = finger_length
        proposal.cad.parameters["thickness_mm"] = thickness
        shape = _base_shape(proposal)
        x = cfg["fixed_port_x_mm"]
        y = cfg["fixed_port_y_mm"]
        diameter = cfg["fixed_port_diameter_mm"]
    else:
        shape = baseline.fuse(tube(32, 24, thickness))
        x = cfg["tvc_port_x_mm"]
        y = cfg["tvc_port_y_mm"]
        diameter = cfg["port_diameter_mm"]
    # Integral radial saddle: lower half is fused into the aft web face.
    pre_saddles = shape.Volume()
    for angle in (0, 120, 240):
        cylinder = cq.Solid.makeCylinder(
            cfg["saddle_radius_mm"],
            cfg["saddle_length_mm"],
            cq.Vector(x - cfg["saddle_length_mm"] / 2, 0, thickness),
            cq.Vector(1, 0, 0),
        )
        shape = shape.fuse(cylinder.rotate((0, 0, 0), (0, 0, 1), angle))
    saddle_volume = shape.Volume() - pre_saddles
    before_holes = shape.Volume()
    shape = holes(shape, x, y, diameter, thickness + cfg["saddle_radius_mm"])
    return {
        "baseline_volume_mm3": baseline.Volume(),
        "candidate_volume_mm3": shape.Volume(),
        "delta_mass_g": (shape.Volume() - baseline.Volume()) * 0.00185,
        "saddle_added_volume_mm3": saddle_volume,
        "saddle_added_mass_g": saddle_volume * 0.00185,
        "ports_removed_volume_mm3": before_holes - shape.Volume(),
        "valid": bool(shape.isValid()),
        "solid_count": len(shape.Solids()),
    }


def share(force, cfg):
    # One shortest stiff leg, two equally slack soft legs; k = EA/L.
    lo, hi = cfg["leg_axial_rigidity_range_n"]
    length = cfg["leg_loaded_length_mm"]
    k_lo, k_hi = lo / length, hi / length
    delta = cfg["leg_loaded_length_spread_mm"]
    return min(force, k_hi * (force + 2 * k_lo * delta) / (k_hi + 2 * k_lo))


def run(config, platform, output):
    cfg = yaml.safe_load(config.read_text())
    known = dict(cfg, leg_axial_rigidity_range_n=[100000, 100000], leg_loaded_length_spread_mm=0)
    assert math.isclose(share(900, known), 300)
    assert math.isclose(1.5 * 100 * 8 / (4 * 10**2), 3.0)
    flight_path = Path(cfg["flight_record"])
    flight = json.loads(flight_path.read_text())
    probes = {
        case["vehicle"]: next(
            (
                p["vertical_velocity_down_mps"]
                for p in case.get("ballistic_motor_delay_probes", [])
                if p["delay_s"] == 12
            ),
            None,
        )
        for case in flight["cases"]
        if case.get("ballistic_motor_delay_probes")
    }
    paths = [Path(p) for p in yaml.safe_load(platform.read_text())["vehicles"]] + [
        Path("configs/vehicle/wo02/performance-g54.yaml")
    ]
    source = {
        Path("configs/studies/wo03-g11-load-properties.yaml"),
        config,
        platform,
        flight_path,
        Path(__file__),
        Path("src/cad/parts.py"),
        Path("src/cad/retention_parts.py"),
    }
    thin_length = (
        3 * cfg["leg_loaded_length_mm"] / 1000
        + cfg["splice_end_count"] * cfg["splice_blank_per_end_mm"] / 1000
        + cfg["upper_nose_sled_branch_length_m"]
        + cfg["termination_extra_length_m"]
    )
    line_nominal = (
        (cfg["main_line_length_m"] - cfg["main_leader_length_m"]) * cfg["main_line_g_m_estimate"]
        + cfg["main_leader_length_m"] * cfg["main_leader_g_m_estimate"]
        + thin_length * cfg["thin_line_g_m_estimate"]
    )
    line_high = (
        cfg["main_line_length_m"] * 8 + thin_length * cfg["aramid_alternative_g_m_gross_package"]
    )
    hardware = cfg["hardware"]
    fixed_delta = (
        sum(
            hardware[k]
            for k in (
                "bridle_termination_and_stitch_g",
                "upper_body_band_g",
                "sled_tabs_g",
                "seal_and_grommet_g",
                "heat_sleeve_g",
                "adhesive_and_fillet_g",
                "future_positive_pin_delta_g_estimate",
            )
        )
        - hardware["existing_anchor_removed_g"]
        - hardware["existing_shock_cord_removed_g"]
        + line_nominal
    )
    masses, cases = [], []
    for path in paths:
        source.update(vehicle_input_paths(path))
        vehicle = load_vehicle(path)
        parts = {p.id: p for p in vehicle.parts}
        fixed = vehicle.design.mode == "performance"
        plate = parts["retention" if fixed else "gimbal_frame"]
        is_g80 = vehicle.id == "modular-performance-v1"
        finger_length = cfg["g80_finger_length_mm"] if is_g80 else cfg["finger_length_mm"]
        cad = cad_mass(plate, cfg, fixed, finger_length=finger_length)
        min_cad = (
            cad_mass(
                plate, cfg, False, cfg["tvc_web_min_thickness_mm"], finger_length=finger_length
            )
            if not fixed
            else None
        )
        delta_g = fixed_delta + cad["delta_mass_g"] + cfg["sled_packaging_increment_g"]
        mass = float(mass_properties(vehicle).mass_kg)
        allowance = float(vehicle.design.mass_allowance_kg)
        aft_parts = [p for p in vehicle.parts if float(p.cg_station_m) > 0.92]
        aft_mass = sum(float(p.resolved_mass_kg) for p in aft_parts)
        motor_mass = float(parts["motor"].resolved_mass_kg)
        body_ids = {"body_upper", "adhesive_finish", "rail_guides"}
        coupler_ids = {"interface_coupler", "joint_stop"}
        nose_ids = {"nose_cone"}
        aft_ids = {p.id for p in aft_parts}
        body_mass = sum(float(parts[k].resolved_mass_kg) for k in body_ids if k in parts)
        coupler_mass = sum(
            float(parts[k].resolved_mass_kg) for k in coupler_ids if k in parts and k not in aft_ids
        )
        nose_mass = sum(float(parts[k].resolved_mass_kg) for k in nose_ids if k in parts)
        upper_other_mass = mass - aft_mass - body_mass - coupler_mass - nose_mass
        masses.append(
            {
                "vehicle": vehicle.id,
                "fixed": fixed,
                "cad": cad,
                "finger_length_mm": finger_length if fixed else None,
                "minimum_tvc_cad": min_cad,
                "base_mass_kg": mass,
                "recovery_increment_g_excluding_packaging": fixed_delta + cad["delta_mass_g"],
                "increment_including_packaging_g": delta_g,
                "selected_battery_fins_and_rail_changes_applied": False,
            }
        )
        scenarios = [("5ms_nominal", 5.0), ("20_4ms_probe", 20.4)]
        if probes.get(vehicle.id) is not None:
            scenarios.append(("12s_no_canopy_probe", probes[vehicle.id]))
        for label, velocity in scenarios:
            acceleration = velocity**2 / (2 * cfg["stop_m"]) + 9.80665
            force = (mass + allowance + delta_g / 1000) * acceleration * cfg["factor"]
            # The main junction extracts separately tethered upper/nose/sled loads;
            # only aft inertia passes through the anchor when every branch engages.
            anchor_force = (aft_mass + allowance + delta_g / 1000) * acceleration * cfg["factor"]
            plate_inertia = (
                (float(plate.resolved_mass_kg) + cad["delta_mass_g"] / 1000)
                * acceleration
                * cfg["factor"]
            )
            rail_force = max(0.0, anchor_force - plate_inertia)
            max_leg = share(anchor_force, cfg)
            thickness = (
                cfg["fixed_web_min_thickness_mm"] if fixed else cfg["tvc_web_min_thickness_mm"]
            )
            hole_min = cfg["fixed_port_min_diameter_mm"] if fixed else cfg["port_min_diameter_mm"]
            hole_max = cfg["fixed_port_max_diameter_mm"] if fixed else cfg["port_max_diameter_mm"]
            ligament = cfg["hole_pitch_min_mm"] - hole_max
            for hypothesis, leg in (("matched_bounded", max_leg), ("single_leg", anchor_force)):
                port = leg / 2
                cases.append(
                    {
                        "vehicle": vehicle.id,
                        "scenario": label,
                        "sharing": hypothesis,
                        "speed_mps": velocity,
                        "total_factored_n": force,
                        "aft_anchor_factored_n": anchor_force,
                        "aft_cg_partition_ids": [p.id for p in aft_parts],
                        "fixed_rail_transfer_factored_n": rail_force if fixed else None,
                        "motor_inertia_factored_n": motor_mass * acceleration * cfg["factor"],
                        "body_branch_factored_n": body_mass * acceleration * cfg["factor"],
                        "coupler_branch_factored_n": coupler_mass * acceleration * cfg["factor"],
                        "nose_branch_factored_n": nose_mass * acceleration * cfg["factor"],
                        "other_upper_and_recovery_factored_n": upper_other_mass
                        * acceleration
                        * cfg["factor"],
                        "body_kraft_uniform_axial_mpa": body_mass
                        * acceleration
                        * cfg["factor"]
                        / (math.pi * 66 * 0.5),
                        "leg_force_n": leg,
                        "line_strand_force_n": port,
                        "standing_cord_reference_mbs_margin": cfg["thin_line_mbs_n"] / leg - 1,
                        "standing_cord_half_strength_sensitivity_margin": cfg["thin_line_mbs_n"]
                        * 0.5
                        / leg
                        - 1,
                        "full_force_termination_n": leg,
                        "main_hmpe_half_strength_sensitivity_margin": cfg["thin_line_mbs_n"]
                        * 0.5
                        / force
                        - 1,
                        "main_aramid_leader_half_strength_sensitivity_margin": cfg[
                            "main_line_strength_n"
                        ]
                        * 0.5
                        / force
                        - 1,
                        "port_bearing_mpa": port / (hole_min * thickness),
                        "web_shear_mpa": leg / (2 * thickness * ligament),
                        "unsupported_web_beam_bending_mpa": 1.5
                        * leg
                        * cfg["hole_pitch_max_mm"]
                        / (ligament * thickness**2),
                        "hot_G11_estimated_screen_mpa": cfg["hot_g11_screen_mpa"],
                        "bridge_bending_hot_flexural_estimate_mpa": cfg[
                            "hot_bridge_flexural_estimate_mpa"
                        ],
                        "bridge_bending_assumed_lamination": "plate plane XY, load out-of-plane Z; orientation to verify",
                        "thickness_used_mm": thickness,
                        "six_finger_mean_shear_mpa": (
                            rail_force
                            / (cfg["finger_count"] * cfg["finger_width_mm"] * finger_length)
                            if fixed
                            else None
                        ),
                        "adhesive_hot_screen_mpa": cfg["hot_bond_screen_mpa"],
                        "limitations": "uniform bond and beam stress are idealizations; loaded-leg matching and EA bounds unverified; no component or joint rating",
                    }
                )
    payload = {
        "status": "prototype; not adopted or qualified",
        "flight_ready": False,
        "thin_line_m": thin_length,
        "line_nominal_g": line_nominal,
        "legacy_aramid_alternative_gross_package_line_g": line_high,
        "mass_inputs": cfg["hardware"],
        "masses": masses,
        "cases": cases,
        "source_sha256": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(source)
            if p.is_file()
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    print(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-recovery-anchor.yaml")
    )
    parser.add_argument("--platform", type=Path, default=Path("configs/platform.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim", "rl", "real"], default="tiny")
    parser.add_argument(
        "--output", type=Path, default=Path("build/wo03-recovery-anchor/record.json")
    )
    args = parser.parse_args()
    run(args.config, args.platform, args.output)


if __name__ == "__main__":
    main()
