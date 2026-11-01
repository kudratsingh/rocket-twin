"""One hand-admission packet, including the unchanged shared guide screen.

No new CAD, stress/heat solver or free-flight calculation. The solid floor
subtracts every listed cut independently (overlapping cuts over-subtract).
It is conditional on this one specified geometry and retained source ledger.
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
CONFIG = ROOT / "configs/studies/wo03-g80-short-subframe.yaml"
OUT = ROOT / "runs/wo03-g80-short-subframe-20261101-v1"


def main():
    started = time.monotonic()
    cfg = yaml.safe_load(CONFIG.read_text())
    staged = ROOT / cfg["staged_checkout"]
    sys.path.insert(0, str(staged))
    os.chdir(staged)
    # Source-identical archived schema: do not override stale root CAD caches.
    from src.vehicle.benchmark import screen_launch
    from src.vehicle.schema import Vehicle

    v = Vehicle.model_validate(yaml.safe_load((ROOT / cfg["source_73_spec"]).read_text()))
    materials = yaml.safe_load((ROOT / cfg["source_materials"]).read_text())["materials"]
    paths = [
        CONFIG,
        Path(__file__).resolve(),
        ROOT / cfg["source_73_spec"],
        ROOT / cfg["source_72_spec"],
        ROOT / cfg["source_materials"],
        staged / "src/vehicle/benchmark.py",
        staged / "src/vehicle/schema.py",
    ]
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    before = {str(p.relative_to(ROOT)): digest(p) for p in paths}
    f, t, b = (cfg[k] for k in ("frame", "termination", "body"))
    rho = materials["G11"]["density_kg_m3"] * 1e-9
    strength = materials["G11"]["hot_strength_screen_pa"] / 1e6
    parts = {p.id: p for p in v.parts}
    base = sum(p.mass_kg for p in v.parts)
    removed = {k: parts[k].mass_kg for k in cfg["remove_source_ids"]}
    retained = base - sum(removed.values()) + cfg["growth_kg"]
    mass = {}
    rail_gross = f["rails"] * (
        f["rail_length_mm"] * f["rail_radial_mm"] * f["rail_tangential_mm"]
        + f["terminal_total_axial_length_per_rail_mm"]
        * f["rail_radial_mm"]
        * (f["terminal_tangential_mm"] - f["rail_tangential_mm"])
    )
    fin_cut = f["rails"] * math.prod(f["fin_pocket_mm"])
    nut_cut = f["rails"] * f["nut_pockets_per_rail"] * math.prod(f["nut_pocket_mm"])
    axial_cut = (
        f["rails"]
        * f["nut_pockets_per_rail"]
        * math.pi
        * f["axial_bore_d_mm"] ** 2
        / 4
        * f["bore_length_per_nut_mm"]
    )
    pin_cut = (
        f["rails"] * math.pi * f["thrust_plate_pin_hole_mm"] ** 2 / 4 * f["rail_tangential_mm"]
    )
    mass["rails_cut_blank_upper"] = (rail_gross - fin_cut) * rho
    mandatory = (rail_gross - fin_cut - nut_cut - axial_cut - pin_cut) * rho
    for key in ("fore_ring", "aft_ring", "thrust_plate", "aft_cap"):
        p = f[key]
        vol = math.pi * (p["outer_radius_mm"] ** 2 - p["inner_radius_mm"] ** 2) * p["thickness_mm"]
        hole_n = f["ring_holes_each"] if "ring" in key else f["plate_holes_each"]
        holes = hole_n * math.pi * f["ring_hole_d_mm"] ** 2 / 4 * p["thickness_mm"]
        if key == "thrust_plate":
            vol -= 3 * math.prod(f["thrust_plate_open_notches_mm"])
            vol += 6 * math.prod(f["thrust_plate_fingers_mm"])
            holes += 6 * math.pi * f["thrust_plate_pin_hole_mm"] ** 2 / 4 * 2
        mass[key + "_cut_blank_upper"] = vol * rho
        mandatory += (vol - holes) * rho
    cheek_vol = (
        t["cheeks"]
        * t["cheek_width_radial_mm"]
        * t["cheek_length_axial_mm"]
        * t["cheek_thickness_mm"]
    )
    cheek_cut = t["cheeks"] * math.pi * t["pin_hole_mm"] ** 2 / 4 * t["cheek_thickness_mm"]
    mass["clevis_cheeks_cut_blank_upper"] = cheek_vol * rho
    mandatory += (cheek_vol - cheek_cut) * rho
    mass["clevis_heel_blocks"] = t["heel_blocks"] * math.prod(t["heel_block_mm"]) * rho
    mass["M6_pin_shaft"] = math.pi * t["pin_d_mm"] ** 2 / 4 * t["pin_length_mm"] * 7850e-9
    ro, ri = b["ring_outer_inner_radius_mm"]
    band_vol = (
        len(b["ring_stations_mm"])
        * (
            math.pi * (ro * ro - ri * ri)
            - b["notch_count"] * b["notch_width_mm"] * b["notch_radial_depth_mm"]
        )
        * b["ring_length_mm"]
    )
    mass["body_bond_bands"] = band_vol * rho
    mass["body_spreader_blanks"] = b["external_spreaders"] * math.prod(b["spreader_blank_mm"]) * rho
    for name, grams in cfg["budget_items_g"].items():
        mass[name] = grams / 1000
    floor_mass = retained + mandatory
    budget_mass = retained + sum(mass.values())
    r = cfg["recovery"]
    accel = r["design_factor"] * (
        r["severe_speed_mps"] ** 2 / (2 * r["stopping_distance_m"]) + 9.80665
    )
    demand_floor = max(r["prior_factored_floor_n"], accel * floor_mass)
    demand_budget = max(r["prior_factored_floor_n"], accel * budget_mass)
    total_t = t["cheeks"] * t["cheek_thickness_mm"]
    net = total_t * (t["cheek_width_radial_mm"] - t["pin_hole_mm"])
    bearing = total_t * t["pin_d_mm"]
    span = t["gap_mm"] + t["cheek_thickness_mm"]
    moment = demand_budget * (2 * span - t["gap_mm"]) / 8
    screens = {}
    for name, m in (
        ("source", base + cfg["growth_kg"]),
        ("mandatory_solid_floor", floor_mass),
        ("complete_preliminary_budget", budget_mass),
    ):
        screens[name] = screen_launch(v, study_nominal_mass_kg=m - cfg["growth_kg"])
    lo, hi = 0.5, 1.5
    for _ in range(22):
        mid = (lo + hi) / 2
        if screen_launch(v, study_nominal_mass_kg=mid - cfg["growth_kg"])["rail_screen_pass"]:
            lo = mid
        else:
            hi = mid
    # Pin-ended axial-force-only frame bookkeeping, not installed stiffness.
    reactions = [
        demand_budget
        * (
            1 / 3
            + 2
            * t["radius_mm"]
            / (3 * f["rail_radius_mm"])
            * math.cos(math.radians(a - t["azimuth_deg"]))
        )
        for a in f["axes_deg"]
    ]
    assert math.isclose(sum(reactions), demand_budget, rel_tol=1e-12)
    assert math.isclose(
        sum(
            q * f["rail_radius_mm"] * math.cos(math.radians(a))
            for q, a in zip(reactions, f["axes_deg"], strict=True)
        ),
        demand_budget * t["radius_mm"] * math.cos(math.radians(t["azimuth_deg"])),
        rel_tol=1e-12,
    )
    cpu = (
        resource.getrusage(resource.RUSAGE_SELF).ru_utime
        + resource.getrusage(resource.RUSAGE_SELF).ru_stime
    )
    record = {
        "status": "one_concept_not_admitted",
        "inputs_sha256": before,
        "source_73_nominal_kg": base,
        "removed_kg": removed,
        "source_retained_plus_separate_growth_kg": retained,
        "growth_kg": cfg["growth_kg"],
        "new_component_budget_kg": mass,
        "mandatory_solid_floor_kg": floor_mass,
        "complete_preliminary_budget_kg": budget_mass,
        "mass_note": "Floor over-subtracts all intersecting listed cuts; budget uses cut blanks/explicit allowances. Neither is a CAD-reconciled installed mass.",
        "factored_severe_acceleration_N_kg": accel,
        "factored_recovery_floor_N": demand_floor,
        "factored_recovery_budget_N": demand_budget,
        "clevis_net_mm2": net,
        "clevis_projected_bearing_mm2": bearing,
        "clevis_net_budget_MPa": demand_budget / net,
        "clevis_projected_bearing_floor_MPa": demand_floor / bearing,
        "clevis_projected_bearing_budget_MPa": demand_budget / bearing,
        "generic_hot_screen_MPa": strength,
        "conditional_net_margin": strength * net / demand_budget,
        "conditional_bearing_margin": strength * bearing / demand_budget,
        "bearing_not_a_qualified_mode_specific_allowable": True,
        "maximum_full_mass_at_generic_bearing_screen_kg": strength * bearing / accel,
        "pin_budget_double_shear_MPa": demand_budget / (2 * math.pi * t["pin_d_mm"] ** 2 / 4),
        "pin_uniform_eye_bending_MPa": moment / (math.pi * t["pin_d_mm"] ** 3 / 32),
        "pin_grade_hot_capacity": "unavailable",
        "axial_force_only_frame_reactions_N": reactions,
        "frame_reactions_not_installed_bounds": True,
        "guide_screens": screens,
        "maximum_guide_full_mass_kg_interval": [lo, hi],
        "thermal_temperatures": None,
        "thermal_acceptance": "unavailable unchanged matrix/45C",
        "native_CAD_FEA_thermal_freeflight_calls": 0,
        "cpu_s": cpu,
        "wall_s": time.monotonic() - started,
        "source_unchanged": before == {str(p.relative_to(ROOT)): digest(p) for p in paths},
    }
    assert record["source_unchanged"]
    assert cpu < cfg["budget"]["total_cpu_s"]
    assert record["wall_s"] < cfg["budget"]["wall_s"]
    OUT.mkdir(exist_ok=False)
    (OUT / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: record[k]
                for k in (
                    "mandatory_solid_floor_kg",
                    "complete_preliminary_budget_kg",
                    "factored_recovery_floor_N",
                    "factored_recovery_budget_N",
                    "conditional_net_margin",
                    "conditional_bearing_margin",
                    "guide_screens",
                    "maximum_guide_full_mass_kg_interval",
                    "cpu_s",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
