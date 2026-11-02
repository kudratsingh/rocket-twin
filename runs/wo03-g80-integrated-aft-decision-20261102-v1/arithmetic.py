"""One read-only arithmetic packet. No geometry, solver or flight execution."""

import hashlib
import json
import math
import resource
import signal
import time
from pathlib import Path

import yaml

started = time.monotonic()
cpu_started = time.process_time()
resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
signal.alarm(5)
root = Path(__file__).resolve().parents[2]
names = [
    "configs/studies/wo03-g80-integrated-aft-proposal.yaml",
    "runs/wo03-g80-saddle-study-20261102-v2/record.json",
    "runs/wo03-g80-saddle-study-20261102-v2/quadrature-review.json",
    "runs/wo03-g80-saddle-connections-20261102-v1/record.json",
    "runs/wo03-g80-short-subframe-20261101-v1/record.json",
]
sha = lambda name: hashlib.sha256((root / name).read_bytes()).hexdigest()
before = {name: sha(name) for name in names}
cfg = yaml.safe_load((root / names[0]).read_text())
s2, _, audit, s1 = [json.loads((root / name).read_text()) for name in names[1:]]
stock = cfg["mass_screen_g"]
added_g = sum(v for k, v in stock.items() if k.startswith("extra_"))
full_kg = s2["full_mass_with_growth_kg"] + added_g / 1000
factor = 3 * (20.4**2 / (2 * 0.3) + 9.80665)
force = full_kg * factor
amp = max(q["point_junction_amp"] for q in audit["bridle_point_geometry_sensitivity"])
point_pressure = force * amp / (8 * 12.7)
formal_limit_kg = cfg["limits"]["formal_guide_full_mass_ceiling_g"] / 1000
planning_limit_kg = cfg["limits"]["planning_guide_full_mass_ceiling_g"] / 1000
# These are broad conditional bookkeeping placements, not installed-CG bounds.
cg0 = s2["axial_cg_estimate_m"]
spread = s2["axial_cg_uncertainty_from_backbone_and_cut_station_m"]
cg_bookkeeping = [
    (s2["full_mass_with_growth_kg"] * old + added_g / 1000 * new) / full_kg
    for old, new in [(cg0 - spread, 1.069), (cg0 + spread, 1.221)]
]
cp = audit["source_CP_proxy_m"]
retained = s1["source_retained_plus_separate_growth_kg"]
out = {
    "status": "rejected_additive_stock_screen_not_an_installed_candidate",
    "input_sha256_before": before,
    "declared_limits": cfg["arithmetic_budget"],
    "additional_stock_g": added_g,
    "partial_nominal_stock_g": full_kg * 1000 - 50,
    "separate_growth_g": 50,
    "partial_stock_including_growth_g": full_kg * 1000,
    "stock_completeness": "incomplete_and_uncertain_not_a_bound",
    "formal_guide_mass_excess_g": (full_kg - formal_limit_kg) * 1000,
    "planning_guide_mass_excess_g": (full_kg - planning_limit_kg) * 1000,
    "required_severe_force_at_partial_stock_N": force,
    "nominal_force_at_partial_stock_N": full_kg * 3 * (5**2 / (2 * 0.3) + 9.80665),
    "source_s2_recovery_N": s2["recovery_factored_N"],
    "single_branch_point_tension_sensitivity_N": force * amp,
    "point_curvature_pressure_sensitivity_MPa": point_pressure,
    "provisional_25MPa_pressure_ratio": 25 / point_pressure,
    "point_model_not_installed_reactions": True,
    "m3_nominal_projection_mm": 22 - 16.4 - 1.8 - 2.4,
    "wood_single_pin_bearing_sensitivity_MPa": 450 / (3 * 8),
    "wood_single_pin_net_sensitivity_MPa": 450 / (8 * (7 - cfg["additive_receiver_screen_rejected"]["assumed_m3_clearance_hole_mm"])),
    "partial_cg_bookkeeping_m": cg_bookkeeping,
    "source_cp_proxy_stability_cal": [(cp - cg) / 0.066 for cg in cg_bookkeeping],
    "cg_and_cp_not_new_geometry_validation": True,
    "full_tensor": None,
    "exact_guide_speed": None,
    "gross_full_source_replacement_budget_g": {
        "source_bundle_removed_once_g": sum(s1["removed_kg"].values()) * 1000,
        "source_retained_including_separate_growth_g": retained * 1000,
        "maximum_new_package_at_formal_15_source_model_g": (formal_limit_kg - retained) * 1000,
        "maximum_new_package_at_planning_15p5_source_model_g": (planning_limit_kg - retained) * 1000,
        "note": "Not_free_mass_credit_all_removed_functions_and_hardware_must_be_replaced",
    },
    "cad_fea_thermal_free_flight_calls": 0,
    "input_sha256_after": {name: sha(name) for name in names},
    "physical_acceptance_closed": [],
}
out["input_unchanged"] = out["input_sha256_before"] == out["input_sha256_after"]
out["cpu_s_this_process_after_imports"] = time.process_time() - cpu_started
out["wall_s_this_process_after_imports"] = time.monotonic() - started
Path(__file__).with_name("record.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps({k: out[k] for k in ["status", "partial_stock_including_growth_g", "required_severe_force_at_partial_stock_N", "partial_cg_bookkeeping_m", "source_cp_proxy_stability_cal", "gross_full_source_replacement_budget_g"]}))
