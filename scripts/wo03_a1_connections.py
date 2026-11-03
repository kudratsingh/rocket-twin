"""One A1 connection admission packet: dimensions, equilibrium and shared guide.

Elementary annulus/beam/lap/bolt formulae are demand bounds, not joint allowables.
Root force/moment and DF3 recovery case are inherited without a second factor.
No FEA, heat solver, actual CAD sweep, statistical uncertainty or free flight.
"""

from __future__ import annotations

import argparse
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
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def radial_bounds(bore, shaft, tolerance, hot_loss=0, wet_loss=0, ovality=0):
    nominal = bore - shaft
    return {
        "nominal_mm": nominal,
        "minimum_cold_mm": nominal - 2 * tolerance,
        "maximum_cold_mm": nominal + 2 * tolerance,
        "minimum_bounded_mm": nominal - 2 * tolerance - hot_loss - wet_loss - ovality,
        "maximum_bounded_mm": nominal + 2 * tolerance + hot_loss + wet_loss + ovality,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/studies/wo03-a1-connections.yaml")
    parser.add_argument("--preset", choices=["tiny"], default="tiny")
    args = parser.parse_args()
    cfg_path = ROOT / args.config
    cfg = yaml.safe_load(cfg_path.read_text())
    out = ROOT / "runs/wo03-a1-connections-20261102-v1"
    if out.exists():
        raise FileExistsError("Preserve executed packet; no automatic variant or retry")
    out.mkdir(parents=True)
    shutil.copy2(cfg_path, out / "executed-config.yaml")
    shutil.copy2(Path(__file__), out / "executed-script.py")
    for name in (
        "OPENBLAS_NUM_THREADS",
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
    ):
        os.environ[name] = "1"
    resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
    signal.setitimer(signal.ITIMER_REAL, 30)
    start_cpu, start_wall = time.process_time(), time.monotonic()
    inputs = {
        args.config: sha(cfg_path),
        str(Path(__file__).relative_to(ROOT)): sha(Path(__file__)),
    }
    for key, path in cfg.items():
        if key.startswith("source_"):
            inputs[path] = sha(ROOT / path)
    old_record = json.loads((ROOT / cfg["source_a"]).read_text())
    if (
        inputs[cfg["source_a"]]
        != "7f4a0262a7ed5be0427bb7a1fe22c8870697014a6f2c807032091561511a82d2"
    ):
        raise ValueError("Frozen A/B record changed")
    a = old_record["arrangements"][0]
    source = json.loads((ROOT / cfg["source_parts"]).read_text())
    c1 = json.loads((ROOT / cfg["source_c1"]).read_text())
    c2 = json.loads((ROOT / cfg["source_c2"]).read_text())
    source_parts = {p["id"]: p for p in source["parts"]}
    source_stations = {p["id"]: p["station_mm"] for p in source["mass_distribution"]}
    a_additions = {r["id"]: r for r in a["replacement_ledger"] if r["mass_delta_g"] > 0}
    m, interface = cfg["materials"], cfg["interface"]
    rho, epoxy = m["G11_rho"], m["adhesive_rho"]
    rows = []

    def add(pid, mass, station, function, basis):
        rows.append(
            {
                "id": pid,
                "mass_delta_g": mass,
                "station_mm": station,
                "function": function,
                "basis": basis,
            }
        )

    def remove(pid):
        if pid in source_parts:
            add(
                "remove_" + pid,
                -source_parts[pid]["mass_g"],
                source_stations[pid],
                "Function replaced explicitly by A1 connection parts",
                source_parts[pid]["function"],
            )
        else:
            row = a_additions[pid]
            add(
                "remove_" + pid,
                -row["mass_delta_g"],
                row["station_mm"],
                "Function replaced explicitly by A1 connection parts",
                row["function"],
            )

    def annulus(pid, ri, ro, z, material_rho, function):
        mass = math.pi * (ro * ro - ri * ri) * (z[1] - z[0]) * material_rho * 1e-6
        add(
            pid,
            mass,
            sum(z) / 2,
            function,
            "Gross source-defined volume/density; no holes/slots credited",
        )

    for pid in (
        "interface_coupler",
        "joint_stop",
        "aft_interface_hardware",
        "A_root_axial_pins_and_washers",
        "A_three_forward_bridle_eyes",
        "A_centering_ring_0",
        "A_centering_ring_1",
        "A_structural_motor_tube",
    ):
        remove(pid)
    sleeve, stop, collar = (interface[k] for k in ("sleeve", "stop", "collar"))
    annulus(
        "A1_G11_sleeve",
        sleeve["ri_mm"],
        sleeve["ro_mm"],
        sleeve["z_mm"],
        rho,
        "76mm bonded upper overlap and40mm removable aft overlap",
    )
    annulus(
        "A1_integral_stop",
        stop["ri_mm"],
        stop["ro_mm"],
        stop["z_mm"],
        rho,
        "Axial assembly datum, integral with sleeve; no ASA stop",
    )
    keys = interface["index"]
    add(
        "A1_integral_keys",
        sum(keys["widths_mm"])
        * (keys["ro_mm"] - keys["ri_mm"])
        * (keys["z_mm"][1] - keys["z_mm"][0])
        * rho
        * 1e-6,
        sum(keys["z_mm"]) / 2,
        "Unequal key widths prevent120degree pairing; primary forces use bolts/bond",
        "Gross keys, common integral tube stock, no overlap/hole credits",
    )
    ub = interface["upper_bond"]
    annulus(
        "A1_upper_bond_and_process",
        sleeve["ro_mm"],
        interface["upper_body"]["ri_mm"],
        ub["z_mm"],
        epoxy * (1 + ub["wet_mix_process_extra_fraction"]),
        "Full annular adhesive mass plus25percent process; capacity uses75percent coverage",
    )
    annulus(
        "A1_outer_G11_load_collar",
        collar["ri_mm"],
        collar["ro_mm"],
        collar["z_mm"],
        rho,
        "Finite external can reinforcement; changes external aero envelope",
    )
    d = interface["sleeve_inner_doublers"]
    add(
        "A1_three_curved_inner_doublers",
        d["count"] * math.prod(d["axial_arc_radial_mm"]) * rho * 1e-6,
        952,
        "Bearing spreaders bonded to sleeve at bolts; curved stock, not flat overlapping boxes",
        "Gross3x30axialx25arcx2radialmm",
    )
    annulus(
        "A1_collar_bond",
        33,
        33.2,
        collar["z_mm"],
        epoxy,
        "Real collar-can annular bond, no air path through adhesive",
    )
    b = interface["bolts"]
    D, L = b["diameter_mm"], b["length_mm"]
    hw = b["washer_OD_ID_thickness_mm"]
    nutAF, nutT = b["nut_across_flats_thickness_mm"]
    headD, headT = b["head_diameter_height_mm"]
    steel_volume = math.pi * D**2 / 4 * L + math.pi * headD**2 / 4 * headT
    steel_volume += 2 * math.pi / 4 * (hw[0] ** 2 - hw[1] ** 2) * hw[2]
    steel_volume += (math.sqrt(3) / 2 * nutAF**2 - math.pi * 4.2**2 / 4) * nutT
    add(
        "A1_three_M5_complete_sets",
        b["count"] * steel_volume * m["steel_rho"] * 1e-6,
        b["station_mm"],
        "ThreeM5x16 partial-thread bolts, six washers, three full nuts; actual supplier SKU/locking proof pending",
        "Gross nominal steel volume, no thread removal credit",
    )
    spacers = interface["crush_spacers"]
    add(
        "A1_fitted_crush_spacers",
        spacers["count"] * math.pi / 4 * (8**2 - 5.4**2) * spacers["length_mm"] * rho * 1e-6,
        952,
        "Fitted radial sleeves bridge actual gap; avoid tightening across empty gap",
        "Nominal mass; actual gap fit requires measurement",
    )
    for name, mass in (
        ("collar_doubler_bond_g", cfg["process"]["collar_doubler_bond_g"]),
        ("additional_joint_process_mass_g", cfg["process"]["additional_joint_process_mass_g"]),
    ):
        add(
            "A1_" + name,
            mass,
            952,
            "Additional joint adhesive/finish/locking process",
            "Explicit additional allocation, not growth allowance",
        )
    root, rings, motor, h = (cfg[k] for k in ("root", "rings", "motor", "harness"))
    for i, z in enumerate(rings["stations_mm"]):
        annulus(
            f"A1_centering_ring_{i}",
            *rings["ri_ro_mm"],
            [z - 1.5, z + 1.5],
            rho,
            "Resized ring provides real0.3mm nominal inner/outer bond regions; lateral alignment, not rigid ground",
        )
    annulus(
        "A1_shortened_motor_tube",
        15.8,
        17.2,
        motor["shortened_structural_tube_z_mm"],
        rho,
        "Seat bears on tube end; motor thrust may transfer through continuous root webs",
    )
    seat = motor["seat_insert"]
    annulus(
        "A1_motor_thrust_seat",
        seat["ri_mm"],
        seat["ro_mm"],
        seat["z_mm"],
        rho,
        "Independent annular thrust seat, motor rear ring dimension remains historical hypothesis",
    )
    for name in ("toe", "heel"):
        z = root[name + "_z_mm"]
        add(
            "A1_three_fin_" + name + "_stops",
            3 * (z[1] - z[0]) * math.prod(root["stop_radial_tangential_mm"]) * rho * 1e-6,
            sum(z) / 2,
            "Actual axial root stop contacts centering ring and dense root; bonded TTW fin not proven radial capture",
            "Gross stock, no slot/holes credited",
        )
    linear = h["linear_oz_yard_max"] * 28.349523125 / 0.9144
    leg_len = (
        h["sleeve_exit_mm"]
        - h["start_mm"]
        + math.hypot(h["cap_front_mm"] - h["sleeve_exit_mm"], 3)
        + 6
    )
    add(
        "A1_routed_three_bridles",
        3 * (2 * leg_len + math.pi * 6 + h["seam_mm"]) / 1000 * linear,
        960,
        "Six legs atR21 in sleeve fan toR24 at cap; finished eye/seam/bend capacity unknown",
        "Raw maximum linear density, full seams and curvature counted",
    )
    add(
        "A1_extra_service_slack",
        h["additional_service_slack_mm"] / 1000 * linear,
        930,
        "100mm additional extraction/connector access slack; retained connector mass counted already",
        "Extra to original retained backbone mass",
    )
    add(
        "A1_harness_edge_protection",
        h["extra_chafe_guide_mass_g"],
        962,
        "Sleeve exit chafe protection; geometry/heat qualification remains open",
        "2g separate allocation, no free service hardware",
    )
    delta = math.fsum(r["mass_delta_g"] for r in rows)
    delta_first = math.fsum(r["mass_delta_g"] * r["station_mm"] * 1e-6 for r in rows)
    staged = ROOT / "build/wo03-g80-integration-staging/checkout"
    for path, digest in old_record["input_sha256"].items():
        if "/checkout/" in path:
            if sha(ROOT / path) != digest:
                raise ValueError("Frozen guide context changed: " + path)
            inputs[path] = digest
    sys.path.insert(0, str(staged))
    os.chdir(staged)
    from src.vehicle.benchmark import screen_launch
    from src.vehicle.schema import Vehicle

    vehicle = Vehicle.model_validate(yaml.safe_load((ROOT / cfg["source_spec"]).read_text()))
    cases = []
    for index, old in enumerate(a["cases"]):
        mass = old["total_g"] + delta
        old_burnout_mass = (
            c1["mass_scenario_results"][index + 2]["burnout_mass_kg"] * 1000 + a["net_mass_delta_g"]
        )
        cg = (old["total_g"] * old["cg_mm"] + delta_first * 1e6) / mass
        bcg = (old_burnout_mass * old["burnout_cg_mm"] + delta_first * 1e6) / (
            old_burnout_mass + delta
        )
        guides = []
        for travel in cfg["budget"]["guide_m"]:
            v = copy.deepcopy(vehicle)
            v.design.rail_length_m = travel
            g = screen_launch(v, study_nominal_mass_kg=mass / 1000 - 0.05)
            guides.append(
                {
                    "usable_m": travel,
                    "speed_mps": g["rail_exit_speed_mps"],
                    "formal_margin_mps": g["rail_exit_speed_mps"] - 15,
                    "planning_margin_mps": g["rail_exit_speed_mps"] - 15.5,
                }
            )
        cases.append(
            {
                "id": old["id"],
                "total_g": mass,
                "separate_growth_g": 50,
                "extra_aft_g": index * 20,
                "cg_mm": cg,
                "burnout_cg_mm": bcg,
                "reference_cp_mm": old["cp_mm"],
                "reference_loaded_static_cal": (old["cp_mm"] - cg) / 66,
                "reference_burnout_static_cal": (old["cp_mm"] - bcg) / 66,
                "validated_new_cp_mm": None,
                "full_intrinsic_inertia": None,
                "guides": guides,
                "baseline_formal_headroom_g": old["baseline_formal_headroom_g"] - delta,
                "baseline_planning_headroom_g": old["baseline_planning_headroom_g"] - delta,
                "conditional1p971_formal_headroom_g": old["conditional1p971_formal_headroom_g"]
                - delta,
                "conditional1p971_planning_headroom_g": old["conditional1p971_planning_headroom_g"]
                - delta,
                "severe_recovery_DF3_N": max(1782.253, 3 * mass / 1000 * (20.4**2 / 0.6 + 9.80665)),
            }
        )
    thermal_loss = 31.7 * m["cte_bound_per_k"] * 130 - 32.2 * m["cte_bound_per_k"] * 25
    fit = radial_bounds(32.2, 31.7, 0.1, thermal_loss, 0.05, 0.05)
    # No positive thermal expansion credit is taken for the uncharacterized paper bore.
    upper_fit = radial_bounds(32.5, 31.7, 0.1, 31.7 * m["cte_bound_per_k"] * 130, 0.05, 0.05)
    key_rows = []
    for width, slot in zip(keys["widths_mm"], keys["slots_mm"], strict=True):
        hot_width = width * m["cte_bound_per_k"] * 130 - slot * m["cte_bound_per_k"] * 25
        key_rows.append(
            {
                "key_mm": width,
                "slot_mm": slot,
                "nominal_per_flank_mm": (slot - width) / 2,
                "minimum_per_flank_mm": (slot - width - 0.2 - max(0, hot_width) - 0.1) / 2,
                "maximum_cold_per_flank_mm": (slot - width + 0.2) / 2,
            }
        )
    harness_radius = math.hypot(21 + 12.7 / 2, 6 + 0.55 / 2)
    old_harness_radius = math.hypot(24 + 12.7 / 2, 6 + 0.55 / 2)
    # Sector bounds include every corner/motion-expanded rectangular leg and complete doubler arc.
    harness_half_angle = math.degrees(math.atan2(6 + 0.55 / 2 + 0.7, 21 - 12.7 / 2 - 0.7))
    doubler_half_angle = math.degrees((25 / 2 + 0.2) / (30.7 - 1))
    angular_gap = 60 - harness_half_angle - doubler_half_angle
    F = cases[1]["severe_recovery_DF3_N"]
    torque = c2["load_case"]["receiver_axis_DF3_Nm"]
    bolt_resultant = math.hypot(F, torque / 0.0322)
    bearing_t_can = 0.8 + 2
    bearing_t_sleeve = 1 + 2
    bolt_span = 2 / 2 + 0.8 + 0.5 + 1 + 2 / 2
    bolt_moment = bolt_resultant * bolt_span / 2
    bending_pa = 32 * bolt_moment / (math.pi * 5**3) * 1e6
    shear_pa = bolt_resultant / (math.pi * 5**2 / 4) * 1e6
    bolt_vm = math.sqrt(bending_pa**2 + 3 * shear_pa**2)
    lap_area = 2 * math.pi * 31.7 * 76 * 0.75
    upper_shear = F / lap_area * 1e6
    root_force = c2["load_case"]["normal_DF3_N"]
    root_moment = c2["load_case"]["root_DF3_Nm"]
    outer_reaction = (root_moment + root_force * (0.033 - 0.0172)) / 0.015
    root_area = 100 * root["tab_finished_thickness_mm"]
    # No installed stiffness follows from elementary constituent spring compliance.
    upper_slip_bounds = {
        str(G): F * (0.8 / 1000) / (G * (lap_area * 1e-6)) * 1000 for G in (1e6, 10e6, 100e6)
    }
    section = {
        "recovery_full_one_joint_N": F,
        "motor_forward_N": 450,
        "motor_reverse_N": 450,
        "design_factor_applied_once": True,
        "one_bolt_whole_recovery_plus_whole_torque_N": bolt_resultant,
        "bolt_single_shear_pa": shear_pa,
        "bolt_simple_span_bending_pa": bending_pa,
        "bolt_combined_proxy_pa": bolt_vm,
        "hot_steel_estimate_pa": 200e6,
        "bolt_combined_screen_pass": bolt_vm <= 200e6,
        "can_collar_bearing_demand_pa": bolt_resultant / (5 * bearing_t_can) * 1e6,
        "sleeve_doubler_bearing_demand_pa": bolt_resultant / (5 * bearing_t_sleeve) * 1e6,
        "qualified_drilled_G11_bearing_pa": None,
        "sleeve_hole_net_axial_pa": F / (math.pi * (31.7**2 - 30.7**2) - 3 * 5.4) * 1e6,
        "sleeve_edge_shearout_demand_pa": bolt_resultant / (2 * (962 - 952 - 2.7) * 3) * 1e6,
        "upper_lap_effective_area_mm2": lap_area,
        "upper_lap_mean_shear_pa": upper_shear,
        "upper_lap_edge_normal_proxy_pa": 6
        * F
        * 0.0008
        / ((2 * math.pi * 0.0317 * 0.75) * (0.076**2)),
        "upper_paper_and_peel_capacity_pa": None,
        "upper_adhesive_slip_mm_at_explicit_G_pa": upper_slip_bounds,
        "upper_paper_shell_axial_demand_pa": F / (math.pi * (33**2 - 32.5**2)) * 1e6,
        "upper_paper_hot_allowable_pa": None,
        "root_outer_reaction_N": outer_reaction,
        "root_inner_reaction_N": root_force - outer_reaction,
        "root_true_edge_area_mm2": root_area,
        "root_outer_normal_demand_pa": outer_reaction / root_area * 1e6,
        "root_motor_thrust_shear_if_one_web_carries_all_pa": 450 / root_area * 1e6,
        "root_peel_allowable_pa": None,
        "root_toe_or_heel_axial_bearing_demand_pa": root_force / (14.4 * 8.98) * 1e6,
        "annular_ring_unbraced_half_circumference_strip_bending_pa": 6
        * 450
        * 0.0144
        / ((math.pi * 0.0175) * 0.003**2),
        "ring_strip_bound_is_not_actual_axisymmetric_solution": True,
        "motor_thrust_seat_halfcircumference_lip_bending_pa": 6
        * 450
        * 0.0012
        / ((math.pi * 0.0158) * 0.002**2),
        "current_motor_ring_contact_capacity": None,
        "cap_circumferential_spread_width_needed_mm": 6 * F * 0.008 / (25e6 * 0.006**2) * 1000,
        "cap_actual_spread_and_joint_flexibility": None,
        "installed_fin_flutter": None,
        "installed_motion_and_full_inertia": None,
    }
    stack_nominal = 1 + 2 + 0.2 + 0.8 + 0.5 + 1 + 2 + 1 + 4
    fit.update(
        {
            "required_minimum_mm": 0.1,
            "calculated_bounded_pass": fit["minimum_bounded_mm"] >= 0.1,
            "manufactured_and_hot_wet_qualified": False,
        }
    )
    record = {
        "id": cfg["id"],
        "status": "not_admitted_complete_mass_and_connections_open",
        "input_sha256": inputs,
        "replacement_ledger": rows,
        "net_delta_from_A_g": delta,
        "first_moment_delta_from_A_kg_m": delta_first,
        "complete_cases": cases,
        "interface_fit": fit,
        "upper_bond_fit": upper_fit,
        "key_flanks": key_rows,
        "hardware_stack": {
            "nominal_grip_plus_nut_mm": stack_nominal,
            "declared_max_mm": stack_nominal + 0.8,
            "bolt_length_mm": 16,
            "minimum_thread_protrusion_mm": 16 - stack_nominal - 0.8,
            "plain_shank_min_mm": 8,
            "shear_plane_from_underhead_max_mm": 1 + 2 + 0.2 + 0.8 + 0.8,
            "actual_SKU_and_clamp_qualification": None,
        },
        "space": {
            "old_R24_harness_min_in_new_sleeve_mm": 30.7 - old_harness_radius - 0.7,
            "routed_R21_harness_min_in_sleeve_mm": 30.7 - harness_radius - 0.7,
            "angular_gap_between_legs_and_inner_doublers_deg": angular_gap,
            "protected_motor_to_joint_axial_gap_mm": 1069 - 967,
            "extra_slack_mm": 100,
            "removal_translation_required_mm": 40.5,
            "sampled_CAD_or_continuous_motion_validation": False,
            "actual_connector_bend_and_guard_access": None,
            "maximum_bolt_head_radius_mm": 35.2 + 1 + 5,
            "source_stays_body_diameter_mm": 66,
            "new_external_aero_validated": False,
        },
        "section_demands": section,
        "thermal": {
            "required_matrix_unchanged": True,
            "substrate_c": 45,
            "new_temperatures": None,
            "routes": "New sleeve/collar/bonds/seat and changed ring gaps require compatible future thermal analysis; no glue/air overlap",
        },
        "decision": "Hold_A1_before_detailed_vehicle_CAD_FEA: complete1p5m_mass_fails; hot_finished_joint_motor_and_stiffness_evidence_missing. No_auto_variant.",
        "resources": {
            "cpu_s": time.process_time() - start_cpu,
            "wall_s": time.monotonic() - start_wall,
            "cpu_limit_s": 20,
            "wall_limit_s": 30,
            "threads": 1,
            "old_solvers_repeated": False,
            "CAD_FEA_heat_freeflight": False,
        },
    }
    (out / "record.json").write_text(
        json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(
        json.dumps(
            {
                "record": str(out.relative_to(ROOT)),
                "delta_g": delta,
                "total_g": [c["total_g"] for c in cases],
                "fit": fit,
                "resources": record["resources"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
