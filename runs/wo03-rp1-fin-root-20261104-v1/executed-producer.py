"""One stock-based RP1 fin/root preflight. No continuum solver or adoption."""

from __future__ import annotations

import hashlib
import json
import math
import os
import resource
import sys
import time
from pathlib import Path

for key in [
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
]:
    os.environ[key] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import yaml

from scripts.wo03_f2_c1_load_path import FACTOR, NOSE
from src.vehicle.aero import center_of_pressure
from src.vehicle.benchmark import screen_launch
from src.vehicle.mass import mass_properties
from src.vehicle.reference import compare_rocketpy
from src.vehicle.schema import Vehicle, load_vehicle

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "configs/studies/rp1-fin-root-replacement.yaml"
TARGET = ROOT / "configs/vehicle/candidates/g80-rp1-fr1.yaml"
OUT = ROOT / "runs/wo03-rp1-fin-root-20261104-v1"


def panel(E: float, thickness: float, moment: float, divisions: int = 1600) -> dict:
    x = np.linspace(0, 0.06, divisions + 1)
    chord = 0.13 - 0.065 * x / 0.06
    a, b = 0.13, -0.065 / 0.06
    m = a * (0.06 - x) ** 2 / 2 + b * (0.06**3 / 3 - x * 0.06**2 / 2 + x**3 / 6)
    m *= moment / m[0]
    return {
        "tip_m": float(np.trapezoid(m * (0.06 - x) / (E * chord * thickness**3 / 12), x)),
        "max_bending_Pa": float(np.max(6 * m / (chord * thickness**2))),
        "divisions": divisions,
    }


def supported_root(F: float, M: float, E: float, t: float, Kb: float, Km: float, Kr: float) -> dict:
    """Reciprocal beam flexibility plus finite root springs; reactions in newtons."""
    g, length = 0.017451, 0.06
    EI = E * 0.1094 * t**3 / 12
    cv = 1 / Km + g * g / Kr + g**3 / (3 * EI)
    cm = g / Kr + g * g / (2 * EI)
    cy = 1 / Kr + g / EI
    y = (cv * F + cm * M) / (1 + Kb * cv)
    reaction = Kb * y
    v = F - reaction
    torque = M + v * g
    theta = cm * v + cy * M
    return {
        "Kb_N_m": Kb,
        "Km_N_m": Km,
        "Kr_Nm_rad": Kr,
        "body_translation_m": y,
        "body_rotation_rad": theta,
        "body_reaction_N": reaction,
        "mount_reaction_N": v,
        "mount_torque_Nm": torque,
        "root_added_tip_m": y + length * theta,
        "force_balance_residual_N": reaction + v - F,
        "moment_balance_residual_Nm": torque - v * g - M,
        "root_max_bending_Pa": 6 * max(abs(M), abs(torque)) / (0.1094 * t**2),
        "compliance": [[cv, cm], [cm, cy]],
    }


def main() -> None:
    start = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    if OUT.exists() or TARGET.exists():
        raise ValueError("One packet only: preserve completed/failed attempts, no automatic rerun")
    s = yaml.safe_load(STUDY.read_text())
    source = ROOT / s["source"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != s["source_sha256"]:
        raise ValueError("Frozen RP1 AD1 changed")
    before = load_vehicle(source)
    d = before.model_dump(by_alias=True, exclude_none=True)
    d["parts"][0]["parent"] = None
    d.update(id=s["id"], name="RP1 FR1 monolithic carbon preflight — not adopted")
    by = {p["id"]: p for p in d["parts"]}
    removed = [
        p
        for p in d["parts"]
        if p["id"] in {"root_gussets", "root_extra_bond_finish", "ad1_slot_fill"}
    ]
    d["parts"] = [p for p in d["parts"] if p["id"] not in {p["id"] for p in removed}]
    h, rho = 0.003175, 1520.0
    area = 3 * 0.06 * (0.13 + 0.065) / 2
    tab_area = 3 * 0.1094 * 0.017451
    old_fin_cost = by["fin_set"]["build"]["cost_usd"]
    by["forward_ring"]["build"][
        "cost_usd"
    ] += old_fin_cost  # Wood sheet remains needed for rings/nose.
    for pid, mass in [("fin_set", area * h * rho), ("fin_tabs", tab_area * h * rho)]:
        p = by[pid]
        p["mass_kg"] = mass
        p["material"] = "carbon_epoxy"
        p["learn"] = (
            "FR1 exact204-11 nominal1/8inCFRP; minimum2.921/maximum3.429mm. CLTreferenceonly; hotfinishedstrength/stiffness and joints unqualified. No front-ring tab support or wooden root wedges."
        )
        p["build"]["notes"] = p["learn"]
        p["engineering"]["service_notes"] = p["learn"]
        p["engineering"]["function"] = p["learn"]
        p["cad"]["notes"] = p["learn"]
        p["cad"]["generator"] = "unadmitted_fr1_integral_carbon"
        p["build"]["cost_usd"] = 108.99 if pid == "fin_set" else 0.0
    by["fin_set"]["geometry"]["thickness_m"] = h
    by["fin_set"]["cad"]["parameters"].update(root_gusset_span_mm=0, root_gusset_base_mm=0)
    by["fin_tabs"]["geometry"]["bbox_m"] = [0.1094, 0.017451, h]
    by["body"]["cad"]["parameters"]["fr1_fin_slot_width_m"] = 0.0038
    finish = json.loads(json.dumps(by["rp1_notch_sealer"]))
    finish.update(
        id="fr1_edge_finish",
        mass_kg=0.002,
        position_m=1.075,
        cg_offset_m=0.065,
        geometry={"bbox_m": [0.13, 0.004, 0.004]},
        learn="2g curedCFRPcut-edge seal/finish budget; not a structural/thermal/electrical qualification.",
    )
    finish["build"].update(cost_usd=2.0, notes=finish["learn"])
    finish["engineering"]["function"] = finish["learn"]
    d["parts"].append(finish)
    candidate = Vehicle.model_validate(d)
    TARGET.write_text(yaml.safe_dump(d, sort_keys=False))
    nominal = mass_properties(candidate)
    old = mass_properties(before)
    cp = center_of_pressure(candidate)
    motor = next(p for p in candidate.parts if p.id == "motor")
    prior = json.loads(
        (ROOT / "runs/wo03-rp1-attachment-definition-20261103-v2/record.json").read_text()
    )
    limits = json.loads((ROOT / "runs/wo03-g80-f2-selected-20261103-v2/record.json").read_text())[
        "guide_total_mass_limits_kg"
    ]["1.5"]
    cases = []
    soft = {
        "parachute",
        "shock_cord",
        "recovery_connectors",
        "recovery_protection",
        "rp1_kevlar_wrap",
    }
    body_mass = nominal.mass_kg - sum(
        p.resolved_mass_kg for p in candidate.parts if p.id in NOSE | soft
    )
    for thickness in [h, 0.003429]:
        delta_stock_mass = (area + tab_area) * (thickness - h) * rho
        delta_stock_moment = (area * 1.1455555555555554 + tab_area * 1.1351) * (thickness - h) * rho
        for nylon in [55, 68]:
            for case, extra, probe in [("nominal", 0.0, 0.0), ("adverse", 0.02, 0.0128)]:
                delta = (nylon - 55) / 1000
                mass = nominal.mass_kg + 0.05 + extra + delta + delta_stock_mass
                moment = (
                    nominal.mass_kg * nominal.cg_m
                    + (0.05 + extra) * 1.25
                    + motor.resolved_mass_kg * probe
                    + delta * 0.34
                    + delta_stock_moment
                )
                cg = moment / mass
                guide = {}
                for rail in [1.5, 1.8]:
                    v = candidate.model_copy(deep=True)
                    v.design.rail_length_m = rail
                    guide[str(rail)] = screen_launch(v, study_nominal_mass_kg=mass - 0.05)[
                        "rail_exit_speed_mps"
                    ]
                dry_cg = (moment - candidate.motor.propellant_mass_kg * motor.cg_station_m) / (
                    mass - candidate.motor.propellant_mass_kg
                )
                stow = cg + (0.01625 * 0.25 + nylon / 1000 * 0.06) / mass
                cases.append(
                    {
                        "case": case,
                        "stock_thickness_mm": thickness * 1000,
                        "nylon_mass_g": nylon,
                        "nylon_probe_is_bound": False,
                        "total_mass_g": mass * 1000,
                        "growth_g": 50,
                        "extra_aft_g": extra * 1000,
                        "motor_cg_probe_mm": probe * 1000,
                        "cg_mm": cg * 1000,
                        "cp_mm": cp * 1000,
                        "margin_cal": (cp - cg) / 0.066802,
                        "burnout_margin_cal": (cp - dry_cg) / 0.066802,
                        "aft_stowage_margin_cal": (cp - stow) / 0.066802,
                        "guide_mps": guide,
                        "formal_speed_margin_mps": guide["1.5"] - 15,
                        "planning_speed_margin_mps": guide["1.5"] - 15.5,
                        "formal_headroom_g": (limits["15.0"] - mass) * 1000,
                        "planning_headroom_g": (limits["15.5"] - mass) * 1000,
                        "whole_recovery_mean_proxy_N": FACTOR * mass,
                        "body_recovery_proxy_N": FACTOR
                        * (body_mass + delta_stock_mass + 0.05 + extra),
                    }
                )
    E = s["stock"]["room_reference_E_Pa"]
    t = 0.002921
    M = 8.83
    F = M / (0.06 * (0.13 + 2 * 0.065) / (3 * (0.13 + 0.065)))
    q, alpha = 40000.0, math.radians(5)
    a = 0.06 * (0.13 + 0.065) / 2
    ar = 2 * 0.06**2 / a
    direct_F = q * a * (2 * math.pi * ar / (2 + math.sqrt(4 + ar**2))) * alpha * 3
    direct_M = direct_F * (0.06 * (0.13 + 2 * 0.065) / (3 * (0.13 + 0.065)))
    # An optimistic rotation stiffness from the actual paper tube's polar J.
    Gpaper = 5e8 / (2 * (1 + 0.3))
    J = math.pi / 2 * (0.0156845**4 - 0.0145845**4)
    resultant_z = 1.1349
    Kr = Gpaper * J * (1 / (resultant_z - 1.0661) + 1 / (1.193 - resultant_z))
    structure = []
    for fraction in [1.0, 0.5]:
        ep = E * fraction
        p = panel(ep, t, M)
        roots = []
        for kb in [1e5, 1e6, 1e7, 1e8]:
            for km in [1e6, 1e7]:
                root = supported_root(F, M, ep, t, kb, km, Kr)
                root["total_tip_mm"] = (p["tip_m"] + root["root_added_tip_m"]) * 1000
                root["movement_screen_pass"] = root["total_tip_mm"] <= 1
                roots.append(root)
        ideal = supported_root(F, M, ep, t, 1e20, 1e20, 1e20)
        ideal["total_tip_mm"] = (p["tip_m"] + ideal["root_added_tip_m"]) * 1000
        structure.append(
            {
                "E_fraction": fraction,
                "E_Pa": ep,
                "scope": "reference interpretation / exploratory stiffness, not qualified hot bound",
                "clamped_outboard_panel": p,
                "finite_roots": roots,
                "ideal_body_mount_translation_and_rotation": ideal,
                "qualified_strength_pass": None,
                "qualified_movement_pass": None,
            }
        )
    peak = max(abs(r["body_reaction_N"]) for row in structure for r in row["finite_roots"])
    one_area = (0.1094 - 0.0001) * 0.0058
    refinement = [panel(E, t, M, n) for n in [100, 400, 1600]]
    slot = (3.8 - 0.05 - 3.429 - 0.05) / 2
    knot_clearance = (
        16.5 * math.sin(math.pi / 3) - 10 * math.cos(math.pi / 3) - (3.429 / 2 + 6) - 0.2
    )
    sources = [
        source,
        STUDY,
        TARGET,
        Path(__file__),
        ROOT / "configs/studies/rp1-fin-input-sources.yaml",
        ROOT / "scripts/wo03_f2_c1_load_path.py",
        ROOT / "src/vehicle/benchmark.py",
        ROOT / "src/vehicle/mass.py",
        ROOT / "src/vehicle/aero.py",
        ROOT / "src/vehicle/reference.py",
        ROOT / candidate.motor.curve,
        ROOT / "runs/wo03-g80-f2-selected-20261103-v2/record.json",
    ]
    record = {
        "identity": candidate.id,
        "adopted": False,
        "decision": "STOP: finite-support movement fails; asymmetric mean-bond demand exceeds retained shear screen; finished hot laminate/peel/stiffness data unknown",
        "cases": cases,
        "baseline_cases": prior["cases"],
        "ledger": [
            {
                "id": p.id,
                "mass_g": p.resolved_mass_kg * 1000,
                "cg_mm": p.cg_station_m * 1000,
                "cost_usd": p.build.cost_usd,
                "basis": p.learn,
            }
            for p in candidate.parts
        ],
        "removed": [
            {
                "id": p["id"],
                "mass_g": p["mass_kg"] * 1000,
                "function_replacement": "Proposed CFRP panel/TTW fillets replace wedges only if installed screens pass; removal is proposal accounting, no admitted functional saving",
            }
            for p in removed
        ],
        "physical_mass_g": nominal.mass_kg * 1000,
        "net_mass_change_from_AD1_g": (nominal.mass_kg - old.mass_kg) * 1000,
        "estimated_cost_usd": sum(p.build.cost_usd for p in candidate.parts),
        "wood_purchase_retained_and_reallocated_usd": old_fin_cost,
        "retained_bond_budgets_g": {"fin_internal_bonds": 14, "outer_fin_fillets": 10},
        "physical_inertia": None,
        "flight": "not run; source/physical inertia unavailable",
        "load_trace": {
            "retained_M_Nm": M,
            "retained_F_N": F,
            "direct_40kPa_5deg_DF3_F_N": direct_F,
            "direct_40kPa_5deg_DF3_M_Nm": direct_M,
            "extra_legacy_envelope_ratio": M / direct_M,
            "revision_adopted": False,
        },
        "structural_sensitivity": structure,
        "mount_rotation_bound": {
            "Gpaper_Pa_estimated": Gpaper,
            "tube_polar_J_m4": J,
            "Kr_Nm_rad": Kr,
            "scope": "actual tube dimensions but estimated properties; rigid ring-end rotations optimistic, actual connections unqualified",
        },
        "joint_demand": {
            "max_body_reaction_N_in_sweep": peak,
            "minimum_one_face_area_mm2": one_area * 1e6,
            "single_face_mean_shear_Pa": peak / one_area,
            "seventy_percent_face_mean_Pa": 0.7 * peak / one_area,
            "equal_share_mean_Pa_diagnostic_only": 0.5 * peak / one_area,
            "existing_hot_shear_screen_Pa": 1e6,
            "single_face_screen_pass": peak / one_area <= 1e6,
            "minimum_leg_mm_for_full_force_mean1MPa": peak / (0.1093 * 1e6) * 1000,
            "normal_peel_allowable": None,
            "load_sharing_qualified": False,
        },
        "geometry": {
            "slot_minimum_per_flank_mm": slot,
            "slot_screen_pass_conditional": slot >= 0.1,
            "knot_box_vs_fillet_min_projection_mm": knot_clearance,
            "knot_actual_geometry_verified": False,
            "recovery_wrap_to_tab_clearance_mm": 1080.2 - 1077 - 0.15,
            "motor_bore_or_retainer_changed": False,
            "sampling_or_CAD_motion": "not executed; only station and projected keep-out checks",
        },
        "panel_refinement": refinement,
        "panel_relative_change_last_two": abs(
            refinement[-1]["tip_m"] / refinement[-2]["tip_m"] - 1
        ),
        "reference": compare_rocketpy(candidate),
        "sources": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources
        },
        "resources": {
            "cpu_seconds": time.process_time(),
            "wall_seconds": time.monotonic() - start,
            "thread_environment": 1,
            "affinity_verified": False,
            "vehicle_cases": len(cases),
            "guide_evaluations": 2 * len(cases),
            "new_CAD_or_continuum_runs": 0,
        },
    }
    OUT.mkdir()
    (OUT / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    (OUT / "executed-producer.py").write_bytes(Path(__file__).read_bytes())
    (OUT / "specification.yaml").write_bytes(TARGET.read_bytes())
    print(
        json.dumps(
            {
                k: record[k]
                for k in [
                    "identity",
                    "decision",
                    "net_mass_change_from_AD1_g",
                    "load_trace",
                    "joint_demand",
                    "geometry",
                    "resources",
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
