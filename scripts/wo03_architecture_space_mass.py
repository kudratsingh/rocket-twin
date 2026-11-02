"""One two-architecture function/space/mass screen; no CAD/FEA/heat/free flight.

Uses frozen C1 component masses/stations, C2's identical isolated panel and
construction inventory, the existing shared guide model, and unchanged
DF3 energy-equivalent recovery loading. Section/beam formulae are elementary
axial stress, thin tube torsion, and eccentric lap equilibrium demand screens;
they do not qualify composite bearing/peel or installed boundary conditions.
"""

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
from pathlib import Path

for name in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ[name] = "1"
resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
signal.setitimer(signal.ITIMER_REAL, 30)
START_CPU, START_WALL = time.process_time(), time.monotonic()
import yaml

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "configs/studies/wo03-architecture-space-mass.yaml"
OUT = ROOT / "runs/wo03-architecture-space-mass-20261102-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")


def main():
    if OUT.exists():
        raise FileExistsError("Refuse to overwrite the bounded packet")
    OUT.mkdir(parents=True)
    shutil.copy2(CFG, OUT / "executed-config.yaml")
    shutil.copy2(Path(__file__), OUT / "executed-script.py")
    cfg = yaml.safe_load(CFG.read_text())
    source_paths = {
        "configs/studies/wo03-architecture-space-mass.yaml": sha(CFG),
        "scripts/wo03_architecture_space_mass.py": sha(Path(__file__)),
    }
    for key, value in cfg.items():
        if key.startswith("source_") and not key.endswith("sha256"):
            source_paths[value] = sha(ROOT / value)
    if source_paths[cfg["source_research"]] != cfg["source_research_sha256"]:
        raise ValueError("Research packet changed after candidate choice")
    c1 = json.loads((ROOT / cfg["source_c1"]).read_text())
    c2 = json.loads((ROOT / cfg["source_c2"]).read_text())
    parts = json.loads((ROOT / cfg["source_parts"]).read_text())
    launch = json.loads((ROOT / cfg["source_launch"]).read_text())
    baseparts = {row["id"]: row for row in parts["parts"]}
    stations = {row["id"]: row["station_mm"] for row in parts["mass_distribution"]}
    common = cfg["common"]
    rho = common["G11_density_kg_m3"]
    removed = {
        "c1_fin_panels",
        "fin_source_cad_residual",
        "aft_shell",
        "fore_integral_G11_annular_cap",
        "fore_integral_body_skirt",
        "motor_front_annulus",
        "motor_keeper_spring_locking_allocation",
        "fore_skirt_to_paper_extra_epoxy_budget",
        "fore_skirt_M2_spreader_fastener_assembly_budget",
        "S3_end_contact_shims",
        "S3_fin_channel_selected_shims",
        "S3_loop_keepers_chafe_and_stitching",
        "fin_bonds",
        "adhesive_finish",
        "incremental_mount_gap_epoxy_upper_budget",
        "retention_locking_materials_reserve",
    }
    prefixes = (
        "C1_",
        "fore_half_cylinder_saddle_lobe_",
        "aft_half_cylinder_saddle_lobe_",
        "motor_front_prong_",
        "motor_front_stop_key_",
        "motor_aft_hard_stop_spacer_",
        "fore_cap_M3_complete_set_",
        "aft_cap_M3_complete_set_",
        "motor_front_key_5mm_cross_pin_complete_set_",
        "fin_axial_retention_5mm_cross_pin_complete_set_",
        "fin_tab_depth_delta_",
        "raw_Bally_2745_loop_",
    )
    removed |= {identifier for identifier in baseparts if identifier.startswith(prefixes)}
    if removed - baseparts.keys():
        raise ValueError(
            "Removal credits name absent functions: " + str(removed - baseparts.keys())
        )
    if not math.isclose(
        sum(p["mass_g"] for p in baseparts.values()), 1079.8067509765393, abs_tol=1e-8
    ):
        raise ValueError("Frozen C1 subtotal changed")
    # Pin executable source context without regenerating cached historical CAD.
    staged = ROOT / "build/wo03-g80-integration-staging/checkout"
    for relative, digest in c2["input_sha256"].items():
        if "/checkout/" in relative:
            if sha(ROOT / relative) != digest:
                raise ValueError("Changed shared source context: " + relative)
            source_paths[relative] = digest
    sys.path.insert(0, str(staged))
    os.chdir(staged)
    from src.vehicle.benchmark import screen_launch
    from src.vehicle.schema import Vehicle

    vehicle = Vehicle.model_validate(yaml.safe_load((ROOT / cfg["source_spec"]).read_text()))
    saved_roots = next(
        row["roots"]
        for row in launch["results"]
        if row["motor"] == "aerotech_g80_10t_source_hypothesis" and row["usable_travel_m"] == 1.5
    )
    conditional_roots = {
        float(target): row["full_mass_g_interval"][0]
        for target, row in json.loads((ROOT / cfg["source_s3"]).read_text())[
            "full_mass_roots_at_1p971m"
        ].items()
    }
    all_results = []
    for variant in ("A", "B"):
        vcfg = cfg[variant]
        rows = []

        def add(identifier, mass, station, function, basis, ledger=rows):
            ledger.append(
                {
                    "id": identifier,
                    "mass_delta_g": mass,
                    "station_mm": station,
                    "function": function,
                    "basis": basis,
                }
            )

        for identifier in sorted(removed):
            row = baseparts[identifier]
            add(
                "remove_" + identifier,
                -row["mass_g"],
                stations[identifier],
                "Replaced by source-defined complete architecture functions",
                row["function"],
            )
        for old in c2["replacement_ledger"]:
            name = old["id"]
            if name in (
                "C2_dense_root_band",
                "C2_dense_through_body_tabs",
                "C2_PVC_core",
                "C2_carbon_panel",
                "C2_carbon_tab",
                "C2_face_bond_panel",
                "C2_face_bond_tab",
                "C2_edge_finish",
                "C2_root_band_core_butt_bonds",
            ):
                scale = (
                    vcfg["fin_tab_depth_mm"] / 14.7
                    if name in ("C2_dense_through_body_tabs", "C2_carbon_tab", "C2_face_bond_tab")
                    else 1
                )
                add(
                    name.replace("C2", variant + "_fin"),
                    old["mass_delta_g"] * scale,
                    old["station_mm"],
                    old["function"],
                    "Same saved panel/core/skin; tab depth scaled geometrically, no installed strength transfer",
                )

        def annulus(identifier, values, axial, function):
            inner, outer = values
            start, end = axial
            add(
                identifier,
                math.pi * (outer**2 - inner**2) * (end - start) * rho * 1e-6,
                (start + end) / 2,
                function,
                "Gross G11 estimate, no hole/slot/window machining credit",
            )

        annulus(
            variant + "_loadbearing_outer_can",
            common["outer_can"]["r_inner_outer_mm"],
            common["outer_can"]["start_end_mm"],
            "Replaces paper aft shell and old thin receiver with continuous structural body; slotted installed torsion remains unqualified",
        )
        annulus(
            variant + "_structural_motor_tube",
            common["motor_tube"]["r_inner_outer_mm"],
            common["motor_tube"]["start_end_mm"],
            "True structural motor support, independent of liner/case; shared fin load path only in A",
        )
        for i, station in enumerate(common["centering_rings"]["stations_mm"]):
            t = common["centering_rings"]["thickness_mm"]
            annulus(
                f"{variant}_centering_ring_{i}",
                common["centering_rings"]["r_inner_outer_mm"],
                [station - t / 2, station + t / 2],
                "Finite ring transfers tube/body loads through actual bonded inner and outer circumferences",
            )
        annulus(
            variant + "_fore_recovery_cap",
            common["fore_load_cap"]["r_inner_outer_mm"],
            common["fore_load_cap"]["start_end_mm"],
            "Recovery load introduction at three real slots and aft rounded saddles; finite annular plate, not fixed ground",
        )
        annulus(
            variant + "_integral_fore_cuff",
            common["fore_cuff"]["r_inner_outer_mm"],
            common["fore_cuff"]["start_end_mm"],
            "Monolithic cap/cuff to distributed body lap; real bight windows reduce section/bond area, fully counted stock",
        )
        saddle = common["recovery_saddles"]
        add(
            variant + "_three_integral_recovery_saddles",
            3 * 0.5 * math.pi * saddle["radius_mm"] ** 2 * saddle["radial_width_mm"] * rho * 1e-6,
            1010 + 4 * saddle["radius_mm"] / (3 * math.pi),
            "Rounded rear-face bights react directly into fore cap; three forward bridles replace aft-running loop topology",
            "Changed9mm to6mm bend radius; no finished hot capacity claimed",
        )
        loop = common["recovery_loops"]
        loop_length = (
            2
            * (
                loop["upper_face_station_mm"]
                - loop["junction_station_mm"]
                + loop["cap_through_thickness_mm"]
            )
            + math.pi * saddle["radius_mm"]
            + loop["sewn_lap_mm"]
        )
        mass_per_m = loop["raw_mass_oz_per_yard_max"] * 28.349523125 / 0.9144
        add(
            variant + "_three_forward_bridle_eyes",
            3 * loop_length / 1000 * mass_per_m,
            960,
            "Primary backbone reaches fore cap directly; retained body/nose branches unchanged; actual sleeve/bond carries aft components",
            "Source raw maximum linear mass, full sewn lap counted; finished strength unavailable",
        )
        ret = common["retainer"]
        add(
            variant + "_independent_threaded_retainer",
            ret["estimated_installed_mass_g"],
            1210,
            "Threaded body/cap retains motor against ejection; no recovery-strap credit; cap removed before motor",
            "20g allocation, exact product mass/fit/hot capacity unavailable; reservation is not supplier geometry",
        )
        add(
            variant + "_retainer_adapter_and_bond",
            ret["estimated_adapter_and_bond_g"],
            1198,
            "Actual mating adapter and retainer bond, fully charged",
            "5g allocation, supplier OD/thread/nozzle/endseat dimensions unresolved",
        )
        for name, grams in common["new_allocations_g"].items():
            add(
                variant + "_" + name,
                grams,
                1030 if name in ("cap_cuff_bond", "harness_chafe_stitch_reserve") else 1140,
                "Complete replacement " + name.replace("_", " "),
                "Explicit allocation including finishing, joint/process/hardware; full separate50g is additional",
            )
        if variant == "B":
            for name, count_key, dims_key in (
                ("capturing_cheeks", "cheek_count", "cheek_axial_radial_tangential_mm"),
                ("socket_floors", "floor_count", "floor_axial_tangential_radial_mm"),
            ):
                add(
                    "B_" + name,
                    vcfg[count_key] * math.prod(vcfg[dims_key]) * rho * 1e-6,
                    1140,
                    "Mechanically closed shallow root socket connected to finite shell/diaphragms",
                    "Gross stock; no generic bearing allowable or ideal shell support",
                )
            for i, pos in enumerate(vcfg["socket_ring_stations_mm"]):
                annulus(
                    f"B_root_diagram_ring_{i}",
                    vcfg["socket_rings_inner_outer_mm"],
                    [pos - 1.5, pos + 1.5],
                    "Full-circumference diaphragm closes root/socket path into outer sleeve",
                )
            add(
                "B_selected_shims",
                vcfg["selected_shim_mass_g"],
                1140,
                "Root positive capture/play control",
                "Actual hot swelling/contact and1mm movement remain open",
            )
        delta = math.fsum(row["mass_delta_g"] for row in rows)
        first_delta = math.fsum(row["mass_delta_g"] * row["station_mm"] * 1e-6 for row in rows)
        cases = []
        for old, label in zip(
            c1["mass_scenario_results"][2:4],
            ("nominal", "additional20g_motorCG_probe"),
            strict=True,
        ):
            mass = old["loaded_mass_kg"] + delta / 1000
            cg = (old["loaded_first_moment_kg_m"] + first_delta) / mass * 1000
            bm = old["burnout_mass_kg"] + delta / 1000
            bcg = (old["burnout_first_moment_kg_m"] + first_delta) / bm * 1000
            guide = []
            for travel in cfg["budget"]["guide_m"]:
                v = copy.deepcopy(vehicle)
                v.design.rail_length_m = travel
                g = screen_launch(v, study_nominal_mass_kg=mass - 0.05)
                guide.append(
                    {
                        "usable_m": travel,
                        "formal_margin_mps": g["rail_exit_speed_mps"] - 15,
                        "planning_margin_mps": g["rail_exit_speed_mps"] - 15.5,
                        **g,
                    }
                )
            demand = max(1782.253, 3 * mass * (20.4**2 / 0.6 + 9.80665))
            cases.append(
                {
                    "id": label,
                    "subtotal_without_separate_growth_g": mass * 1000 - 50,
                    "separate_growth_g": 50,
                    "total_g": mass * 1000,
                    "cg_mm": cg,
                    "burnout_cg_mm": bcg,
                    "cp_mm": old["cp_mm"],
                    "loaded_static_cal": (old["cp_mm"] - cg) / 66,
                    "burnout_static_cal": (old["cp_mm"] - bcg) / 66,
                    "guides": guide,
                    "baseline_formal_headroom_g": saved_roots["formal"]["total_launch_mass_kg"]
                    * 1000
                    - mass * 1000,
                    "baseline_planning_headroom_g": saved_roots["planning"]["total_launch_mass_kg"]
                    * 1000
                    - mass * 1000,
                    "conditional1p971_formal_headroom_g": conditional_roots[15] - mass * 1000,
                    "conditional1p971_planning_headroom_g": conditional_roots[15.5] - mass * 1000,
                    "required_severe_recovery_DF3_mean_N": demand,
                    "nominal_recovery_DF3_mean_N": 3 * mass * (5**2 / 0.6 + 9.80665),
                    "full_intrinsic_inertia": None,
                    "signed_axial_point_ledger_contribution_kg_m2": sum(
                        row["mass_delta_g"] / 1000 * ((row["station_mm"] - cg) / 1000) ** 2
                        for row in rows
                    ),
                }
            )
        # Necessary hot axial and lap demands, actual windows subtracted from capacity.
        fore = common["fore_cuff"]
        ri, ro = fore["r_inner_outer_mm"]
        sleeve_area = math.pi * (ro**2 - ri**2) * 1e-6
        window_length = fore["windows"]["start_end_mm"][1] - fore["windows"]["start_end_mm"][0]
        lap_effective_length = (
            fore["start_end_mm"][1] - fore["start_end_mm"][0]
        ) - window_length * 0.5
        lap_area = 2 * math.pi * ro * lap_effective_length * 0.75 * 1e-6
        F = cases[-1]["required_severe_recovery_DF3_mean_N"]
        eccentricity = 0.0008
        shear_demand = F / lap_area
        normal_edge_proxy = (
            6
            * F
            * eccentricity
            / (2 * math.pi * ro / 1000 * 0.75 * (lap_effective_length / 1000) ** 2)
        )
        cap_e = (32 - 24) / 1000
        required_spread_width = 6 * F * cap_e / (25e6 * 0.006**2)
        force = c2["load_case"]["normal_DF3_N"]
        rootM = c2["load_case"]["root_DF3_Nm"]
        separation = (32.2 - 17.2) / 1000 if variant == "A" else 0.007
        rootM / separation
        Aroot = 0.1 * 0.012
        one_outer_reaction = (
            (rootM + force * (0.033 - 0.0172)) / 0.015
            if variant == "A"
            else 2 * (rootM + force * 0.0035) / 0.007 + force / 2
        )
        outer_ri, outer_ro = 0.0322, 0.033
        outer_J = math.pi / 2 * (outer_ro**4 - outer_ri**4)
        motor_J = math.pi / 2 * (0.0172**4 - 0.0158**4)
        G = 5e9 / (2 * (1 + 0.25))
        upper_J = outer_J + (motor_J if variant == "A" else 0)
        # Deliberately best-case intact tubes and rigid fore boundary: NOT actual support.
        optimistic_tube_tip = (
            (c2["load_case"]["receiver_axis_DF3_Nm"] / 3) * (0.218) / (G * upper_J) * 0.123
        )
        play = (
            vcfg["control_play_mm"]
            / vcfg["fin_tab_depth_mm"]
            * (90 + vcfg["fin_tab_depth_mm"] / 2)
            / 1000
        )
        min_panel = c2["panel_and_finite_root"]["levels"][-1]["panel_total_m"]
        min_motion = min_panel + optimistic_tube_tip + play
        max_radius = math.hypot(24 + 12.7 / 2, 6 + 0.55 / 2)
        coldgap = 32.2 - 31.8 - 0.2
        hotgap = coldgap + 32.2 * 25e-6 * (45 - 20) - 31.8 * 25e-6 * (150 - 20)
        results = {
            "id": vcfg["id"],
            "status": "not_admitted_pending_complete_connection_and_source_evidence",
            "replacement_ledger": rows,
            "removed_part_ids": sorted(removed),
            "gross_removed_g": -math.fsum(min(0, row["mass_delta_g"]) for row in rows),
            "gross_added_g": math.fsum(max(0, row["mass_delta_g"]) for row in rows),
            "net_mass_delta_g": delta,
            "first_moment_delta_kg_m": first_delta,
            "cases": cases,
            "section_demands": {
                "whole_recovery_at_one_saddle_N": F,
                "cuff_half_section_hot_axial_stress_pa": F / (0.5 * sleeve_area),
                "G11_hot_axial_screen_pa": 25e6,
                "cuff_hot_axial_screen_ratio": 25e6 / (F / (0.5 * sleeve_area)),
                "cuff_body_effective_bond_area_m2": lap_area,
                "cuff_body_mean_shear_pa": shear_demand,
                "unchanged_hot_mean_shear_screen_pa": 1e6,
                "eccentric_lap_normal_edge_demand_proxy_pa": normal_edge_proxy,
                "qualified_peel_allowable_pa": None,
                "cap_minimum_effective_circumferential_spread_width_mm": required_spread_width
                * 1000,
                "cap_actual_effective_width_mm": None,
                "single_fin_outer_root_reaction_DF3_N": one_outer_reaction,
                "A_root_effective_patch_area_m2": Aroot if variant == "A" else None,
                "A_inner_root_reaction_DF3_N": (
                    force - one_outer_reaction if variant == "A" else None
                ),
                "B_opposing_half_depth_contact_area_m2": 0.1 * 0.0035 if variant == "B" else None,
                "B_mean_contact_demand_pa": (
                    one_outer_reaction / (0.1 * 0.0035) if variant == "B" else None
                ),
                "A_mean_root_interface_demand_pa": (
                    one_outer_reaction / Aroot if variant == "A" else None
                ),
                "root_bond_normal_peel_or_socket_bearing_allowable": None,
                "full_tube_torsion_only_best_case_tip_mm": optimistic_tube_tip * 1000,
                "panel_play_ideal_tube_best_case_proxy_mm": min_motion * 1000,
                "installed_tube_joint_motion_mm": None,
                "support_flexibility": "Intact_tube_upper_stiffness_and_rigid_fore_support_are_optimistic_references_only_real_slots_bonds_coupler_and_ring_flexibility_unavailable",
                "installed_flutter": None,
            },
            "space": {
                "source_old_loop_max_radial_mm": math.hypot(30.35, 9.275),
                "new_fore_loop_max_radial_mm": max_radius,
                "outer_can_harness_min_after0p7mm_loss_mm": 32.2 - max_radius - 0.7,
                "fore_cuff_real_windows_required": True,
                "cuff_window_half_angle_deg": 30,
                "max_leg_angle_plus_motion_deg": math.degrees(math.atan2(6.275 + 0.8, 17.65 - 0.8)),
                "window_wall_angle_reserve_deg": 30
                - math.degrees(math.atan2(6.275 + 0.8, 17.65 - 0.8)),
                "recovery_vs_retainer_axial_gap_mm": 1195 - 1016,
                "motor_liner_side_gap_min_mm": 15.8 - 0.1 - (15.12 + 0.1 + 0.04),
                "cuff_body_cold_min_gap_mm": coldgap,
                "cuff_body_differential150_45_min_gap_mm": hotgap,
                "exact_retainer_envelope_and_root_hot_fit": None,
                "scope": "Explicit_concept_reservations_and_analytic_bounds_not_CAD_collision_service_or_supplier_qualification",
            },
            "unresolved_admission": [
                "Finished_hot_bridle_eye_bend_and_saddle_capacity_not_qualified",
                "Cap_annular_spreading_and_finite_ring_body_connections_not_established",
                "Root_peel_or_socket_bearing_and_installed_movement_unqualified",
                "Exact_current_G80_and_Estes_retainer_mass_envelope_mating_hot_capacity_missing",
                "New_thermal_paths_required_matrix_not_calculated",
                "Installed_vibration_flutter_and_full_inertia_unavailable",
            ],
            "thermal": cfg["thermal"],
        }
        all_results.append(results)
    for relative, expected in source_paths.items():
        if sha(ROOT / relative) != expected:
            raise ValueError("Changed input during packet: " + relative)
    record = {
        "id": cfg["id"],
        "status": "completed_two_architecture_screen_no_complete_arrangement_admitted",
        "input_sha256": source_paths,
        "selected_before_execution": cfg["budget"]["selected"],
        "arrangements": all_results,
        "baseline_usable_m": 1.5,
        "formal_mps": 15,
        "planning_mps": 15.5,
        "preferred_direction": "A_motor_fin_can_for_bounded_connection_demand_study_only_not_CAD_admission",
        "decision": "Choose_integrated_TTW_motor_fin_can_as_lower_duplication_direction_if_its_mass_fit_and_connection_demands_are_credible;_no_complete_admission_without_hot_finished_connections_motorfit_and_installed_stiffness._No_third_variant.",
        "resources": {
            "cpu_s": time.process_time() - START_CPU,
            "wall_s": time.monotonic() - START_WALL,
            "cpu_limit_s": 20,
            "wall_limit_s": 30,
            "threads": 1,
            "CAD_FEA_thermal_freeflight_executed": False,
        },
    }
    dump(OUT / "record.json", record)
    print(
        json.dumps(
            {
                "status": record["status"],
                "arrangements": [
                    {
                        "id": r["id"],
                        "delta_g": r["net_mass_delta_g"],
                        "cases": [
                            {
                                "id": c["id"],
                                "mass_g": c["total_g"],
                                "cg_mm": c["cg_mm"],
                                "static_cal": c["loaded_static_cal"],
                                "guide_mps": [g["rail_exit_speed_mps"] for g in c["guides"]],
                                "recovery_N": c["required_severe_recovery_DF3_mean_N"],
                            }
                            for c in r["cases"]
                        ],
                        "cuff_ratio": r["section_demands"]["cuff_hot_axial_screen_ratio"],
                        "root_mean": r["section_demands"]["A_mean_root_interface_demand_pa"],
                        "min_motion_mm": r["section_demands"][
                            "panel_play_ideal_tube_best_case_proxy_mm"
                        ],
                    }
                    for r in all_results
                ],
                "resources": record["resources"],
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        if OUT.exists():
            import traceback

            dump(
                OUT / "failure.json",
                {
                    "error": str(error),
                    "traceback": traceback.format_exc(),
                    "automatic_retry": False,
                },
            )
        raise
