"""Read saved S3 only: finite joint, patch contact and dimensional audit.

Two opposing, half-depth uniform contact patches satisfy force AND moment.
They are demand sensitivities, not an elasticity solution or local peak bound.
References: elementary beam equilibrium and bearing definitions, Roark's
Formulas for Stress and Strain; existing project DF3 and material screens.
"""

import hashlib
import json
import math
import resource
import signal
import time
from pathlib import Path

import yaml

resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
signal.alarm(5)
started, cpu = time.monotonic(), time.process_time()
out = Path(__file__).resolve().parent
root = out.parents[1]
cfg_path = root / "configs/studies/wo03-g80-connected-receiver.yaml"
record_path = out / "record.json"
cfg = yaml.safe_load(cfg_path.read_text())
r = json.loads(record_path.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
before = {str(p.relative_to(root)): sha(p) for p in [cfg_path, record_path]}
F = r["recovery_demands"]["severe_20p4m_s_0p3m_DF3_N"]
joint = r["reverse_motor_retention_screen"]
one_ear = joint["one_loaded_ear_width_mm"]
hole_r = cfg["cap_connections"]["barrel_clearance_hole_mm"] / 2
M = r["fin_root_screen"]["root_moment_per_fin_Nm_after_DF3"]
V = r["fin_root_screen"]["root_force_per_fin_N_after_DF3"]
L = cfg["rails"]["channel_radial_depth_mm"] / 1000
area = cfg["fins"]["tab_length_mm"] * cfg["rails"]["channel_radial_depth_mm"] / 2
sum_reactions = 4 * M / L
positive, negative = (sum_reactions + V) / 2, (sum_reactions - V) / 2
fin_pin = r["fin_root_screen"]["own_fin_mass_severe_inertia_force_n"]
edge = cfg["fins"]["positive_axial_pins"]["axial_distance_to_tab_end_mm"]
fin_hole_r = cfg["fins"]["positive_axial_pins"]["clearance_hole_mm"] / 2
depth = cfg["fins"]["new_tab_depth_mm"]
angle_factor = math.hypot(95, 48) / 95
pressure_full = F * angle_factor / (9 * 12.7)
cap_cases = []
for force in [450, F]:
    cap_cases.append({
        "single_joint_axial_force_N": force,
        "M3_tensile_MPa": force / 5.03,
        "estimated_steel_200MPa_ratio_not_allowable": 200 / (force / 5.03),
        "washer_mean_MPa": force / joint["washer_annulus_area_mm2"],
        "single_barrel_one_ear_mean_MPa": force / (6 * one_ear),
        "end_tearout_mean_MPa_by_end": {
            name: force / (2 * (end - hole_r) * one_ear)
            for name, end in zip(["fore", "aft"], [14, 8])
        },
        "note": "Full recovery joint force is a sensitivity until contact signs, prying and unequal-loop reactions are solved. 450N retention alone cannot qualify recovery.",
    })
result = {
    "status": "S3_not_admitted_no_new_geometry_solver_or_guide_run",
    "declared_budget": {"packets": 1, "cpu_s": 2, "wall_s": 5, "threads": 1},
    "inputs_before": before,
    "cap_joint_sensitivities": cap_cases,
    "fin_opposing_half_depth_patches": {
        "force_after_DF3_N": V,
        "moment_after_DF3_Nm": M,
        "contact_centroid_separation_mm": L * 1000 / 2,
        "positive_patch_N": positive,
        "opposing_patch_N": negative,
        "area_each_mm2": area,
        "mean_pressures_MPa": [positive / area, negative / area],
        "force_residual_N": positive - negative - V,
        "moment_residual_Nm": (positive + negative) * L / 4 - M,
        "local_peak_pressure_MPa": None,
        "note": "Supersedes favorable full-area/full-depth proxy. Uniform half-patches are still idealized; patch stiffness, wood compression and local peaks unavailable.",
    },
    "fin_5p3mm_hole_end_tearout": {
        "net_ligament_mm": edge - fin_hole_r,
        "two_plane_area_mm2": 2 * (edge - fin_hole_r) * depth,
        "mean_shear_MPa": fin_pin / (2 * (edge - fin_hole_r) * depth),
        "capacity": "unavailable_directional_hot_material_and_hole_data",
    },
    "unequal_loop_point_sensitivity": {
        "junction_radial_motion_mm": 24,
        "saddle_radial_center_mm": 24,
        "axial_separation_mm": 95,
        "one_branch_full_force_amplification": angle_factor,
        "pressure_MPa_at_full_width": pressure_full,
        "pressure_MPa_at_75pct_effective_width": pressure_full / 0.75,
        "25MPa_screen_ratios": [25 / pressure_full, 25 / (pressure_full / 0.75)],
        "finished_hot_eye_capacity_N": None,
        "note": "Not an installed reaction solution or qualified contact allowable. Junction motion, stitch/bend strength and cap flexibility unresolved.",
    },
    "dimensions": {
        "former_gap_mm": 3.8,
        "candidate_fore_end_face_gap_nominal_mm": 1010 - 1010,
        "candidate_aft_end_face_gap_nominal_mm": 1211.8 - 1211.8,
        "no_CAD_interference_or_capacity_acceptance_claim": True,
        "nominal_aft_screw_tip_to_fin_pin_axial_separation_mm": (1217.8 + 0.5 - 19.5) - (1180 + 2.65),
        "source_lugs_to_actual_rail_conversion": "unavailable_requires_real_buttons_and_attachment",
    },
    "acceptance_closed": [],
    "unchanged_required_cases_and_active_vehicle": True,
}
result["inputs_after"] = {str(p.relative_to(root)): sha(p) for p in [cfg_path, record_path]}
assert before == result["inputs_after"]
assert abs(result["fin_opposing_half_depth_patches"]["force_residual_N"]) < 1e-10
assert abs(result["fin_opposing_half_depth_patches"]["moment_residual_Nm"]) < 1e-12
result["cpu_after_imports_s"] = time.process_time() - cpu
result["wall_after_imports_s"] = time.monotonic() - started
(out / "connection-audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({k: result[k] for k in ["status", "cap_joint_sensitivities", "fin_opposing_half_depth_patches", "unequal_loop_point_sensitivity"]}))
