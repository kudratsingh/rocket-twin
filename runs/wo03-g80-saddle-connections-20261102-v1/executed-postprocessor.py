"""Read-only S2 decision audit; no geometry refinement or candidate revision.

All strength comparisons are demands against provisional scalar screens, not
mode-specific qualified capacities. Uses the saved S2 diagnostic record.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import resource
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-g80-saddle-study.yaml"
RUN = ROOT / "runs/wo03-g80-saddle-study-20261102-v2"
OUT = ROOT / "runs/wo03-g80-saddle-connections-20261102-v1"


def main():
    started = time.monotonic()
    cfg = yaml.safe_load(CONFIG.read_text())
    raw = json.loads((RUN / "record.json").read_text())
    refinement = json.loads((RUN / "quadrature-review.json").read_text())
    stage = ROOT / cfg["staged_checkout"]
    sys.path.insert(0, str(stage))
    os.chdir(stage)
    from src.vehicle.aero import center_of_pressure
    from src.vehicle.benchmark import screen_launch
    from src.vehicle.schema import Vehicle

    v = Vehicle.model_validate(yaml.safe_load((ROOT / cfg["source_spec"]).read_text()))
    paths = [
        CONFIG,
        Path(__file__).resolve(),
        RUN / "record.json",
        RUN / "quadrature-review.json",
        ROOT / cfg["source_spec"],
        stage / "src/vehicle/aero.py",
        stage / "src/vehicle/benchmark.py",
    ]
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    before = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    full = raw["full_mass_with_growth_kg"]
    F = raw["recovery_design_floor_N"]
    c, ca, straps, stack = (cfg[k] for k in ("collars", "carrier", "straps", "motor_stack"))
    hot = c["scalar_screen_MPa"]
    area = math.pi * (ca["outer_radius_mm"] ** 2 - ca["inner_radius_mm"] ** 2)
    inertia = math.pi * (ca["outer_radius_mm"] ** 4 - ca["inner_radius_mm"] ** 4) / 4
    # No equal loop/rail sharing is credited. Full F is a local demand sensitivity.
    tube = {
        "area_mm2": area,
        "whole_force_mean_MPa": F / area,
        "scalar_axial_ratio": hot * area / F,
        "contact_fraction_needed_at_scalar_screen": F / (hot * area),
        "mean_contact_MPa_by_effective_fraction": {str(q): F / (area * q) for q in (0.25, 0.5, 1)},
        "Euler_pinned_diagnostic_N": [
            math.pi**2 * (E / 1e6) * inertia / ca["length_mm"] ** 2 for E in ca["youngs_range_Pa"]
        ],
        "note": "Global ideal-column diagnostic only; local wall/end bearing, anisotropy, partial contact and installed capacity unverified.",
    }
    point = cfg["primary_connector"]
    x0 = point["planning_radius_mm"] * math.cos(math.radians(point["planning_azimuth_deg"]))
    y0 = point["planning_radius_mm"] * math.sin(math.radians(point["planning_azimuth_deg"]))
    bight_z = c["fore_contact_plane_mm"] - c["saddle_base_axial_mm"]
    dz = bight_z - point["planning_station_mm"]
    branch = []
    for angle in c["saddle_axes_deg"]:
        dx = straps["center_x_mm"] * math.cos(math.radians(angle)) - x0
        dy = straps["center_x_mm"] * math.sin(math.radians(angle)) - y0
        transverse = math.hypot(dx, dy)
        amplify = math.hypot(dz, transverse) / dz
        branch.append(
            {
                "angle_deg": angle,
                "point_junction_amp": amplify,
                "whole_axial_force_in_one_branch_tension_N": F * amplify,
                "fixed_point_lateral_reaction_N": F * transverse / dz,
            }
        )
    maxamp = max(q["point_junction_amp"] for q in branch)
    curved_pressure = F * maxamp / (c["saddle_radius_mm"] * straps["width_mm"])
    lbf = 4.4482216152605
    rawstrap = straps["raw_tensile_lbf"] * lbf
    rawcord = cfg["backbone"]["raw_tensile_lbf"] * lbf
    soft = {
        "raw_webbing_tensile_N": rawstrap,
        "combined_efficiency_needed_whole_force": F / rawstrap,
        "combined_efficiency_needed_point_geometry": F * maxamp / rawstrap,
        "finished_strength_sensitivity_ratios": {
            str(e): rawstrap * e / (F * maxamp)
            for e in straps["combined_finished_hot_efficiency_sensitivity"]
        },
        "backbone_finished_efficiency_needed": F / rawcord,
        "connector_raw_assembly_breaking_ratio": point["manufacturer_breaking_load_kg"]
        * 9.80665
        / F,
        "accepted_finished_loop_capacity_N": None,
        "note": "No raw tensile or marine connector ratio qualifies hot sewn loops, loaded bends, multi-leg direction or rocket use.",
    }
    # Thermal expansion endpoints: no temperatures or motor-case material asserted.
    plays = []
    for am in stack["case_CTE_estimate_range_per_K"]:
        for ag in stack["carrier_CTE_estimate_range_per_K"]:
            for Tg in stack["carrier_temperature_sensitivity_C"]:
                motor_growth = (
                    stack["motor_length_nominal_mm"]
                    * am
                    * (stack["required_case_upper_C"] - stack["ambient_C"])
                )
                tube_growth = ca["length_mm"] * ag * (Tg - stack["ambient_C"])
                for cold in [
                    stack["cold_endplay_target_mm"] - stack["cold_endplay_tolerance_mm"],
                    stack["cold_endplay_target_mm"] + stack["cold_endplay_tolerance_mm"],
                ]:
                    plays.append(cold - (motor_growth - tube_growth))
    keeper = cfg["keeper_fasteners"]
    grip = keeper["measured_saddle_grip_max_mm"] + keeper["remaining_base_web_mm"]
    need = (
        grip
        - c["keeper_counterbore_depth_mm"]
        + keeper["nut_thickness_mm"]
        + keeper["washer_thickness_mm"]
        + keeper["thread_protrusion_mm"]
    )
    # Explicit assumed tolerance stack, not supplier data or a new criterion.
    need_worst = need + 0.2 + 0.1 + 0.1 + 0.1 + 0.05
    lo, hi = 0.5, 1.5
    for _ in range(22):
        mid = (lo + hi) / 2
        s = screen_launch(v, study_nominal_mass_kg=mid - cfg["growth_kg"])["rail_exit_speed_mps"]
        if s is not None and s >= cfg["planning_target_guide_mps"]:
            lo = mid
        else:
            hi = mid
    CP = center_of_pressure(v)
    cg = raw["axial_cg_estimate_m"]
    dcg = raw["axial_cg_uncertainty_from_backbone_and_cut_station_m"]
    D = v.airframe["body_diameter_m"]
    grids = {}
    final = raw["quadrature"]["128"]
    for order, values in raw["quadrature"].items():
        dm = (
            sum(values[k]["volume_mm3"] - final[k]["volume_mm3"] for k in ("fore", "aft"))
            * c["density_kg_m3"]
            * 1e-9
        )
        m = full + dm
        grids[order] = {
            "diagnostic_full_mass_kg": m,
            "guide": screen_launch(v, study_nominal_mass_kg=m - cfg["growth_kg"]),
        }
    record = {
        "status": "S2_not_admitted_no_new_geometry_or_solver",
        "input_sha256": before,
        "raw_mass_result_unqualified": True,
        "full_mass_kg": full,
        "growth_kg_separate": cfg["growth_kg"],
        "recovery_factored_N": F,
        "tube_and_end_contact": tube,
        "bridle_point_geometry_sensitivity": branch,
        "point_geometry_not_an_installed_reaction_model": True,
        "saddle_mean_curvature_pressure_MPa_full_force": F
        / (c["saddle_radius_mm"] * straps["width_mm"]),
        "saddle_point_geometry_curvature_pressure_MPa": curved_pressure,
        "provisional_scalar_comparison_ratio": hot / curved_pressure,
        "soft_assembly": soft,
        "motor_thermal_endplay_sensitivity_mm": [min(plays), max(plays)],
        "actual_case_CTE_and_temperature_history": "unavailable",
        "nominal_keeper_length_needed_mm": need,
        "assumed_tolerance_keeper_length_needed_mm": need_worst,
        "minimum_specified_keeper_length_mm": keeper["finished_length_mm"]
        - keeper["length_tolerance_mm"],
        "keeper_grip_sensitivity_pass": keeper["finished_length_mm"] - keeper["length_tolerance_mm"]
        >= need_worst,
        "planning_guide_mass_ceiling_kg_interval": [lo, hi],
        "excess_above_planning_ceiling_kg": full - hi,
        "source_CP_proxy_m": CP,
        "preliminary_CG_m": cg,
        "partial_CG_sensitivity_m": dcg,
        "source_CP_proxy_stability_cal": [(CP - cg) / D, (CP - cg - dcg) / D],
        "stability_note": "Uses retained source aero only, not a complete new-geometry benchmark; CG range covers only named cut/backbone-location assumptions.",
        "all_saved_geometry_levels_guide": grids,
        "all_adjacent_quadrature_pass": False,
        "refinement_review": refinement,
        "aft_foot_one_sided_envelope_to_rail_end_gap_mm": c["aft_contact_plane_mm"] - 1200,
        "foot_contact_note": "As-run collar axial convention leaves a gap to retained rail ends; no accepted spacer, fore-extending foot or pocket geometry exists. Not a fixed support.",
        "outbound_body_fin_strength": "unavailable; no bypass strength from tube average",
        "thermal_matrix_and_45C": "unchanged; temperatures unavailable",
        "native_calls": 0,
        "cpu_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime
        + resource.getrusage(resource.RUSAGE_SELF).ru_stime,
        "wall_s": time.monotonic() - started,
        "input_unchanged": before == {str(p.relative_to(ROOT)): sha(p) for p in paths},
    }
    assert record["input_unchanged"]
    OUT.mkdir(exist_ok=False)
    (OUT / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: record[k]
                for k in (
                    "planning_guide_mass_ceiling_kg_interval",
                    "excess_above_planning_ceiling_kg",
                    "source_CP_proxy_stability_cal",
                    "motor_thermal_endplay_sensitivity_mm",
                    "provisional_scalar_comparison_ratio",
                    "cpu_s",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
