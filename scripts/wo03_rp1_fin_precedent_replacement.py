"""Bounded layered-fin screen; no installed-strength or flight qualification.

Layer bending uses EI=sum(E*I) with a symmetric neutral axis and perfect bond.
Timoshenko core shear is integrated separately. The unsupported tab has finite
bending/translation/shear compliance under the fin-root moment AND force.
These are elementary beam/laminated-section screens, not anisotropic plate FEA.
Manufacturer and equation references: docs/wo03-rp1-fin-precedent-replacement.md.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[variable] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import yaml

from src.vehicle.aero import center_of_pressure
from src.vehicle.benchmark import screen_launch
from src.vehicle.mass import mass_properties
from src.vehicle.schema import Vehicle, load_vehicle

STUDY = ROOT / "configs/studies/rp1-fin-precedent-replacement.yaml"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def section(study: dict[str, Any]) -> dict[str, float]:
    """Minimum dimensions for stiffness; bond layers supply separation, not EI."""
    g, p = study["geometry"], study["screening_inputs"]
    wood = g["plywood_thickness_min_m"]
    carbon = g["carbon_each_face_min_m"]
    film = g["bond_each_face_min_m"]
    y = wood / 2 + film + carbon / 2
    ew, ec = p["plywood_E_Pa"], p["carbon_E_Pa"]
    d = ew * wood**3 / 12 + 2 * ec * (carbon**3 / 12 + carbon * y**2)
    return {"D_Nm": d, "wood_m": wood, "carbon_m": carbon, "skin_centroid_m": y}


def component_screen(study: dict[str, Any], divisions: int = 1600) -> dict[str, Any]:
    g, p = study["geometry"], study["screening_inputs"]
    sec = section(study)
    length, root, tip = g["span_m"], g["root_m"], g["tip_m"]
    x = np.linspace(0.0, length, divisions + 1)
    chord = root + (tip - root) * x / length
    a, b = root, (tip - root) / length
    raw_moment = a * (length - x) ** 2 / 2 + b * (length**3 / 3 - x * length**2 / 2 + x**3 / 6)
    moment = raw_moment * study["loads"]["factored_root_moment_Nm"] / raw_moment[0]
    pressure = study["loads"]["factored_tip_force_equivalent_N"] / (length * (root + tip) / 2)
    shear_force = pressure * (a * (length - x) + b * (length**2 - x**2) / 2)
    covered = x <= g["skin_span_m"]
    dw = p["plywood_E_Pa"] * sec["wood_m"] ** 3 / 12
    ei = chord * np.where(covered, sec["D_Nm"], dw)
    bend = float(np.trapezoid(moment * (length - x) / ei, x))
    kappa, gw = p["shear_correction_factor"], p["plywood_G_Pa"]
    core_shear = float(np.trapezoid(shear_force / (kappa * gw * chord * sec["wood_m"]), x))
    h, width = g["tab_depth_m"], g["tab_chord_m"]
    eit = sec["D_Nm"] * width
    m, v = study["loads"]["factored_root_moment_Nm"], float(shear_force[0])
    rotation = m * h / eit + v * h**2 / (2 * eit)
    translation = m * h**2 / (2 * eit) + v * h**3 / (3 * eit)
    tab_shear = v * h / (kappa * gw * width * sec["wood_m"])
    root_movement = translation + rotation * length + tab_shear
    sub = bend + core_shear + root_movement
    total = sub + p["extra_attachment_tip_budget_m"]
    wood_panel = float(np.max(p["plywood_E_Pa"] * sec["wood_m"] / 2 * moment / ei))
    carbon_panel = float(
        np.max(
            p["carbon_E_Pa"]
            * (sec["skin_centroid_m"] + sec["carbon_m"] / 2)
            * moment[covered]
            / ei[covered]
        )
    )
    base_moment = m + v * h
    wood_tab = p["plywood_E_Pa"] * sec["wood_m"] / 2 * base_moment / eit
    carbon_tab = (
        p["carbon_E_Pa"] * (sec["skin_centroid_m"] + sec["carbon_m"] / 2) * base_moment / eit
    )
    wood_shear = max(
        float(np.max(shear_force / (kappa * chord * sec["wood_m"]))),
        v / (kappa * width * sec["wood_m"]),
    )
    # Interface shear flow from one skin: tau = V*E*A*y/(EI*b).
    # The layer-end/free-edge peel singularity is NOT established by this mean.
    q = p["carbon_E_Pa"] * sec["carbon_m"] * sec["skin_centroid_m"]
    mean_bond_shear = max(
        float(np.max(shear_force[covered] * q / (sec["D_Nm"] * chord[covered]))),
        v * q / (sec["D_Nm"] * width),
    )
    individual = {
        "wood_bending": max(wood_panel, wood_tab) <= p["plywood_bending_screen_Pa"],
        "carbon_bending": max(carbon_panel, carbon_tab) <= p["carbon_stress_screen_Pa"],
        "wood_shear": wood_shear <= p["plywood_shear_screen_Pa"],
        "mean_bond_shear": mean_bond_shear <= p["adhesive_mean_shear_screen_Pa"],
        "movement_with_reserved_attachment_budget": total <= p["tip_movement_limit_m"],
    }
    return {
        "divisions": divisions,
        "panel_bending_mm": bend * 1000,
        "panel_shear_mm": core_shear * 1000,
        "finite_tab_translation_rotation_shear_mm": root_movement * 1000,
        "component_tip_subtotal_mm": sub * 1000,
        "unverified_attachment_reserve_mm": p["extra_attachment_tip_budget_m"] * 1000,
        "screen_total_tip_mm": total * 1000,
        "remaining_tip_budget_mm": (p["tip_movement_limit_m"] - sub) * 1000,
        "max_wood_bending_MPa": max(wood_panel, wood_tab) / 1e6,
        "max_carbon_bending_MPa": max(carbon_panel, carbon_tab) / 1e6,
        "max_wood_shear_MPa": wood_shear / 1e6,
        "max_mean_interface_shear_MPa": mean_bond_shear / 1e6,
        "individual_provisional_screens": individual,
        "conditional_numeric_pass": all(individual.values()),
        "installed_strength_pass": None,
        "installed_tip_movement_pass": None,
        "peel_delamination_capacity": None,
        "hot_wet_material_bounds_verified": False,
        "section_D_Nm": sec["D_Nm"],
    }


def replacement(study: dict[str, Any], source: Vehicle) -> tuple[Vehicle, dict[str, Any]]:
    g, budget = study["geometry"], study["mass_budget"]
    n, span = g["count"], g["skin_span_m"]
    panel_area = n * g["span_m"] * (g["root_m"] + g["tip_m"]) / 2
    tab_area = n * g["tab_chord_m"] * g["tab_depth_m"]
    skin_area_panel = n * (
        g["root_m"] * span + (g["tip_m"] - g["root_m"]) * span**2 / (2 * g["span_m"])
    )
    # Spanwise chord/sweep integrate the actual patch's axial centroid.
    x = np.linspace(0, span, 1601)
    chord = g["root_m"] + (g["tip_m"] - g["root_m"]) * x / g["span_m"]
    station = g["panel_station_m"] + g["sweep_m"] * x / g["span_m"] + chord / 2
    skin_cg = float(np.trapezoid(station * chord, x) / np.trapezoid(chord, x))
    tab_cg = g["tab_station_m"] + g["tab_chord_m"] / 2
    data = source.model_dump(by_alias=True, exclude_none=True)
    data["parts"][0]["parent"] = None
    removed = {"root_gussets", "root_extra_bond_finish"}
    data["parts"] = [part for part in data["parts"] if part["id"] not in removed]
    by = {part["id"]: part for part in data["parts"]}
    for pid, area in (("fin_set", panel_area), ("fin_tabs", tab_area)):
        by[pid]["mass_kg"] = (
            area * g["plywood_thickness_max_m"] * budget["plywood_density_max_kg_m3"]
        )
    additions = []
    for name, area, cg in (("panel", skin_area_panel, skin_cg), ("tab", tab_area, tab_cg)):
        for kind, mass in (
            ("carbon", 2 * area * g["carbon_each_face_max_m"] * budget["carbon_density_max_kg_m3"]),
            (
                "bond",
                2
                * area
                * g["bond_each_face_max_m"]
                * budget["adhesive_density_kg_m3"]
                * budget["adhesive_process_multiplier"],
            ),
        ):
            part = copy.deepcopy(by["ad1_slot_fill"])
            part.update(
                id=f"fp1_{name}_{kind}", mass_kg=mass, position_m=cg - 0.065, cg_offset_m=0.065
            )
            part["parent"] = "body"
            part["material"] = "carbon_fiber_epoxy" if kind == "carbon" else "epoxy"
            part["geometry"] = {"bbox_m": [0.13, 0.06, 0.001]}
            part["learn"] = (
                "FP1 mass-only allocation; no CAD solid, quoted cost or installed capacity."
            )
            part["cad"]["generator"] = "unavailable_fp1_laminate"
            part["build"]["cost_usd"] = 0
            data["parts"].append(part)
            additions.append(
                {"id": part["id"], "mass_g": mass * 1000, "cg_mm": cg * 1000, "cost_usd": None}
            )
    part = copy.deepcopy(by["ad1_slot_fill"])
    part.update(
        id="fp1_skin_termination_finish",
        mass_kg=budget["skin_end_finish_g"] / 1000,
        position_m=skin_cg - 0.065,
        cg_offset_m=0.065,
    )
    part["build"]["cost_usd"] = 0
    data["parts"].append(part)
    data.update(id=study["id"], name="FP1 unadopted mass-only fin laminate screen")
    candidate = Vehicle.model_validate(data)
    old = {p.id: p for p in source.parts}
    changed_ids = budget["replaced_ids"]
    old_mass = sum(old[pid].resolved_mass_kg for pid in changed_ids)
    new_mass = (
        sum(by[pid]["mass_kg"] for pid in ("fin_set", "fin_tabs"))
        + sum(row["mass_g"] / 1000 for row in additions)
        + budget["skin_end_finish_g"] / 1000
    )
    return candidate, {
        "replaced_allocations_g": {pid: old[pid].resolved_mass_kg * 1000 for pid in changed_ids},
        "new_core_g": {pid: by[pid]["mass_kg"] * 1000 for pid in ("fin_set", "fin_tabs")},
        "added_allocations": additions,
        "skin_termination_finish_g": budget["skin_end_finish_g"],
        "net_change_g": (new_mass - old_mass) * 1000,
        "retained_bonds_and_global_finish": budget["retained_ids"],
        "new_complete_fin_group_g": (new_mass + 0.014 + 0.010) * 1000,
        "maximum_laminate_m": g["plywood_thickness_max_m"]
        + 2 * (g["carbon_each_face_max_m"] + g["bond_each_face_max_m"]),
        "cost_complete": False,
        "note": "Zero build-cost placeholders exist only in the in-memory mass model; new component cost is unavailable, never free. No full candidate spec or CAD is adopted/exported.",
    }


def coupled_cases(study: dict[str, Any], candidate: Vehicle) -> list[dict[str, Any]]:
    props = mass_properties(candidate)
    cp = center_of_pressure(candidate)
    motor = next(p for p in candidate.parts if p.id == "motor")
    limits = study["saved_guide_limits"]
    cases = []
    for main_g in study["mass_budget"]["harness_g_cases"]:
        for label, extra, probe in (("nominal", 0.0, 0.0), ("adverse", 0.02, 0.0128)):
            correction = (main_g - 55) / 1000
            total = props.mass_kg + 0.05 + extra + correction
            moment = (
                props.mass_kg * props.cg_m
                + (0.05 + extra) * 1.25
                + motor.resolved_mass_kg * probe
                + correction * 0.34
            )
            cg = moment / total
            q = candidate.model_copy(deep=True)
            q.design.rail_length_m = 1.5
            guide = screen_launch(q, study_nominal_mass_kg=total - 0.05)["rail_exit_speed_mps"]
            cases.append(
                {
                    "case": label,
                    "nylon_mass_g": main_g,
                    "nylon_probe_is_measurement_or_bound": False,
                    "mass_g": total * 1000,
                    "cg_mm": cg * 1000,
                    "cp_mm": cp * 1000,
                    "margin_cal": (cp - cg) / 0.066802,
                    "guide_1_5m_mps": guide,
                    "formal_mass_headroom_g": (limits["formal_15_mps_total_mass_kg"] - total)
                    * 1000,
                    "planning_mass_headroom_g": (limits["planning_15_5_mps_total_mass_kg"] - total)
                    * 1000,
                }
            )
    return cases


def diagnostic_sensitivities(study: dict[str, Any]) -> list[dict[str, Any]]:
    """One-input diagnostics; these are not verified property bounds."""
    rows = []
    for parameter, values in study["sensitivities"].items():
        if not isinstance(values, list):
            continue
        for value in values:
            case = copy.deepcopy(study)
            case["screening_inputs"][parameter] = value
            rows.append(
                {"parameter": parameter, "value": value, "result": component_screen(case, 6400)}
            )
    return rows


def run(output: Path) -> None:
    start = time.monotonic()
    if output.exists():
        raise ValueError("Choose a new output identity; preserve completed records")
    study = yaml.safe_load(STUDY.read_text())
    path = ROOT / study["source"]
    if sha(path) != study["source_sha256"]:
        raise ValueError("Frozen source changed; reconcile before screening")
    source = load_vehicle(path)
    candidate, ledger = replacement(study, source)
    levels = [component_screen(study, n) for n in (400, 1600, 6400)]
    sensitivities = diagnostic_sensitivities(study)
    output.mkdir(parents=True)
    record = {
        "id": study["id"],
        "status": study["status"],
        "source_sha256": sha(path),
        "study_sha256": sha(STUDY),
        "producer_sha256": sha(Path(__file__)),
        "runtime_dependency_sha256": {
            name: sha(Path(sys.modules[name].__file__))
            for name in (
                "src.vehicle.schema",
                "src.vehicle.mass",
                "src.vehicle.aero",
                "src.vehicle.geometry",
                "src.vehicle.benchmark",
                "src.vehicle.motors",
            )
        },
        "motor_curve_sha256": sha(ROOT / source.motor.curve) if source.motor else None,
        "source_run_not_modified": True,
        "adopted": False,
        "flight_ready": False,
        "baseline_frozen_record": "runs/wo03-rp1-attachment-definition-20261103-v2/record.json",
        "component_screens": levels,
        "diagnostic_sensitivities": sensitivities,
        "all_diagnostics_pass": all(
            row["result"]["conditional_numeric_pass"] for row in sensitivities
        ),
        "replacement_admitted": False,
        "replacement_ledger": ledger,
        "complete_vehicle_cases": coupled_cases(study, candidate),
        "unavailable": [
            "conditioned material minimums",
            "installed bond peel/delamination capacity",
            "complete tube/body/ring attachment compliance",
            "thermal layout",
            "installed flutter",
            "full-vehicle CAD/physical inertia/new flight prediction",
            "finished harness mass/capacity",
            "verified upper and lower wood stiffness coupled to retained strength screen",
        ],
        "resources": {
            "wall_s": time.monotonic() - start,
            "cpu_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime,
            "new_FEA_or_CAD_or_simulation_runs": 0,
        },
    }
    (output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "output": str(output),
                "component": levels[-1],
                "ledger": ledger,
                "cases": record["complete_vehicle_cases"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    run(args.out)
