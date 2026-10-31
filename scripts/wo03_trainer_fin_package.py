"""Execute isolated G12 fin candidates and unchanged guide-mass threshold."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.wo03_fin_acceptance import (
    ORTHOTROPIC,
    _component_screen,
    _minimum_thickness_copy,
    panel_force_n,
    run_acceptance,
)
from scripts.wo03_recovery_mass_budget import budget
from src.analysis import fin_fea
from src.cad.parts import local_shape, properties
from src.vehicle.benchmark import screen_launch
from src.vehicle.mass import mass_properties
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import CADMass, load_vehicle, vehicle_input_paths


def run(config: Path, output: Path, reuse_5_report: Path | None = None) -> None:
    cfg = yaml.safe_load(config.read_text())
    budget_path = Path(cfg["budget_config"])
    budget_cfg = yaml.safe_load(budget_path.read_text())
    vehicle_path = Path(cfg["base_vehicle"])
    flight_path = Path(cfg["flight_record"])
    source = {
        config,
        budget_path,
        vehicle_path,
        flight_path,
        Path(__file__),
        Path("scripts/wo03_fin_acceptance.py"),
        Path("scripts/wo03_recovery_mass_budget.py"),
    }
    source.update(vehicle_input_paths(vehicle_path))
    source.update(Path("src/cad").glob("*.py"))
    source.update(Path("src/vehicle").glob("*.py"))
    source.add(Path("src/analysis/fin_fea.py"))

    def hashes():
        return {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(source)
            if p.is_file()
        }

    before = hashes()
    vehicle = load_vehicle(vehicle_path)
    output.mkdir(parents=True, exist_ok=True)
    cases = []
    for option in cfg["candidates"]:
        copy = vehicle.model_copy(deep=True)
        battery_cfg = budget_cfg["main_battery_trade"]
        battery = next(p for p in copy.parts if p.id == "battery")
        battery.geometry = {"bbox_m": battery_cfg["envelope_m"]}
        battery.mass_kg = battery_cfg["supplied_mass_kg"]
        battery.cad_mass = None
        battery.cg_offset_m = battery_cfg["envelope_m"][0] / 2
        assert battery.electrical
        battery.electrical.capacity_mah = battery_cfg["capacity_mah"]
        battery.electrical.max_discharge_a = (
            battery_cfg["capacity_mah"] / 1000 * battery_cfg["stated_discharge_c"]
        )
        fin = next(p for p in copy.parts if p.id == "fin_set")
        fin.geometry["thickness_m"] = option["thickness_m"]
        assert fin.cad and fin.engineering
        fin.cad.parameters["root_gusset_span_mm"] = option["gusset_span_mm"]
        fin.cad_mass = None
        props = properties(fin, local_shape(fin))
        fin.cad_mass = CADMass.model_validate(props)
        fin.mass_kg = props["volume_m3"] * DENSITY_KG_M3[fin.material]
        case_dir = output / option["id"]
        case_dir.mkdir(parents=True, exist_ok=True)
        resolved = case_dir / "resolved-candidate.yaml"
        resolved.write_text(yaml.safe_dump(copy.model_dump(by_alias=True), sort_keys=False))
        original_run = subprocess.run

        def longer_solver_timeout(*args, _original=original_run, **kwargs):
            if kwargs.get("timeout") == 180:
                kwargs["timeout"] = cfg["solver_timeout_s"]
            return _original(*args, **kwargs)

        fin_fea.subprocess.run = longer_solver_timeout
        try:
            if option["thickness_m"] == 0.004:
                minimum_fin = _minimum_thickness_copy(fin)
                hot = fin_fea.run_shell(
                    case_dir / "hot-rejection",
                    minimum_fin,
                    5.0,
                    force_n=panel_force_n(minimum_fin, 40000, 5),
                    stiffness_fraction=0.5,
                    orthotropic=ORTHOTROPIC,
                )
                hot_strength = _component_screen(hot, 0.5)
                fin_report_path = case_dir / "hot-rejection" / "report.json"
                if hot["max_displacement_m"] <= 0.001:
                    raise ValueError(
                        "The 4 mm fin no longer fails hot deflection; run full acceptance"
                    )
                convergence = {
                    "converged": False,
                    "status": "unresolved; fine solve stopped after hot deflection failure",
                }
                cold_strength = {"status": "not evaluated in this short-circuit"}
                large_alpha = {"status": "not evaluated after hot deflection failure"}
                hot_displacement = hot["max_displacement_m"]
            else:
                fin_report_path = reuse_5_report or run_acceptance(
                    resolved, case_dir / "fin-fea", flight_path
                )
                fin_report = json.loads(fin_report_path.read_text())
                expected = hashlib.sha256(
                    load_vehicle(resolved).model_dump_json(by_alias=True).encode()
                ).hexdigest()
                if (
                    fin_report["resolved_spec_sha256"] != expected
                    or not fin_report["inputs_unchanged"]
                ):
                    raise ValueError(
                        "Reusable fin report has a different vehicle or changed inputs"
                    )
                if any(
                    not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest() != h
                    for p, h in fin_report["input_sha256_after"].items()
                ):
                    raise ValueError("Reusable fin report source hashes no longer match")
                convergence = fin_report["static_40kpa_5deg"]["cold_convergence"]
                cold_strength = fin_report["static_40kpa_5deg"]["cold_strength_screen"]
                hot_strength = fin_report["static_40kpa_5deg"]["hot_strength_screen"]
                hot_displacement = fin_report["static_40kpa_5deg"]["hot_fine_mesh"][
                    "max_displacement_m"
                ]
                large_alpha = fin_report["large_alpha_g12_bound"]
        finally:
            fin_fea.subprocess.run = original_run
        mass_budget = budget(
            copy, budget_cfg["dedicated_recovery_part_ids"], budget_cfg["numerical_timestep_s"]
        )
        nominal = float(mass_properties(copy).mass_kg)
        candidate_mass = (
            nominal + cfg["recovery_increment_kg"] - cfg["package_a_rail_mass_saving_kg"]
        )
        departure = [
            screen_launch(copy, dt, study_nominal_mass_kg=candidate_mass)
            for dt in budget_cfg["numerical_timestep_s"]
        ]
        cases.append(
            {
                "id": option["id"],
                "resolved_copy": str(resolved),
                "fin_report": str(fin_report_path),
                "fin_mass_kg": fin.resolved_mass_kg,
                "fin_shape_sha256": props["shape_sha256"],
                "thickness_nominal_m": option["thickness_m"],
                "thickness_minimum_m": option["thickness_m"]
                - fin.engineering.tolerances_mm["thickness"] / 1000,
                "gusset_span_mm": option["gusset_span_mm"],
                "vehicle_nominal_mass_kg": nominal,
                "mass_budget": mass_budget,
                "rail_saving_hypothesis_kg": cfg["package_a_rail_mass_saving_kg"],
                "recovery_increment_hypothesis_kg": cfg["recovery_increment_kg"],
                "guide_candidate_nominal_mass_kg": candidate_mass,
                "guide_screen_by_timestep": departure,
                "guide_increment_headroom_kg_after_rail_saving": mass_budget["maximum_increment_kg"]
                + cfg["package_a_rail_mass_saving_kg"],
                "hypothesis_guide_pass": all(x["rail_screen_pass"] for x in departure),
                "panel_convergence": convergence,
                "cold_strength": cold_strength,
                "hot_strength": hot_strength,
                "hot_max_displacement_m": hot_displacement,
                "hot_displacement_screen_pass": hot_displacement <= 0.001,
                "large_alpha": large_alpha,
                "root_qualification": "open",
                "flutter_qualification": "open",
            }
        )
        print(option["id"], "panel report:", fin_report_path, flush=True)
    # Bounded simply supported circular plate with fixed-radius pressure boundary.
    # Roark's Formulas for Stress and Strain, 8th ed., circular plates: uniform
    # pressure, simply supported edge. Material and edge idealization are estimates.
    pressure_cfg = cfg["pressure_seal_trade"]
    pressure_results = []
    baseline_seal = next(p for p in vehicle.parts if p.id == "recovery_bulkhead")
    radius = float(baseline_seal.geometry["radius_m"])
    for nominal_t in pressure_cfg["nominal_thicknesses_m"]:
        seal = baseline_seal.model_copy(deep=True)
        seal.geometry["length_m"] = nominal_t
        seal.cad_mass = None
        seal_props = properties(seal, local_shape(seal))
        seal_mass = seal_props["volume_m3"] * DENSITY_KG_M3[seal.material]
        savings = float(baseline_seal.resolved_mass_kg) - seal_mass
        min_t = nominal_t - pressure_cfg["thickness_tolerance_m"]
        nu = pressure_cfg["poisson_estimate"]
        rigidity = pressure_cfg["youngs_modulus_pa_estimate"] * min_t**3 / (12 * (1 - nu**2))
        pressure_cases = []
        for name, pressure in [
            ("service", pressure_cfg["assumed_service_differential_pa"]),
            ("proof", pressure_cfg["proposed_proof_differential_pa"]),
            (
                "factored_service",
                pressure_cfg["assumed_service_differential_pa"]
                * pressure_cfg["pressure_design_factor"],
            ),
        ]:
            force = pressure * math.pi * radius**2
            bending = (3 + nu) * pressure * radius**2 / (8 * min_t**2)
            deflection = pressure * radius**4 / (64 * rigidity) * (5 + nu) / (1 + nu)
            bond = force / (2 * math.pi * radius * pressure_cfg["bond_axial_overlap_m"])
            pressure_cases.append(
                {
                    "id": name,
                    "differential_pa": pressure,
                    "force_n": force,
                    "estimated_bending_pa": bending,
                    "estimated_deflection_m": deflection,
                    "estimated_mean_bond_shear_pa": bond,
                    "estimated_screen_pass": bending
                    <= pressure_cfg["hot_bending_screen_pa_estimate"]
                    and bond <= pressure_cfg["hot_bond_shear_screen_pa_estimate"],
                }
            )
        pressure_results.append(
            {
                "nominal_thickness_m": nominal_t,
                "minimum_thickness_m": min_t,
                "cad_mass_kg": seal_mass,
                "cad_shape_sha256": seal_props["shape_sha256"],
                "mass_saving_kg": savings,
                "pressure_cases": pressure_cases,
                "guide_trade_by_fin_and_collar": [
                    {
                        "fin_id": case["id"],
                        "collar_mass_kg": collar,
                        "recovery_headroom_kg": case[
                            "guide_increment_headroom_kg_after_rail_saving"
                        ]
                        + savings
                        - collar,
                        "recovery_increment_kg": cfg["recovery_increment_kg"],
                        "passes_recovery_mass_hypothesis": case[
                            "guide_increment_headroom_kg_after_rail_saving"
                        ]
                        + savings
                        - collar
                        >= cfg["recovery_increment_kg"],
                    }
                    for case in cases
                    for collar in pressure_cfg["collar_mass_cases_kg"]
                ],
                "limitations": "pressure bound, seal, support, adhesive peel, pressure transient and collar all unverified; do not substitute this plate for a recovery anchor",
            }
        )
    record = {
        "status": "isolated candidates; no adoption",
        "flight_ready": False,
        "input_sha256": before,
        "inputs_unchanged": before == hashes(),
        "cases": cases,
        "pressure_seal_trade": pressure_results,
        "solver_timeout_s": cfg["solver_timeout_s"],
    }
    path = output / "record.json"
    path.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    print(path, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-trainer-fin-package.yaml")
    )
    parser.add_argument("--preset", choices=["tiny", "sim", "rl", "real"], default="tiny")
    parser.add_argument("--output", type=Path, default=Path("build/wo03-trainer-fin-package"))
    parser.add_argument("--reuse-5-report", type=Path)
    args = parser.parse_args()
    run(args.config, args.output, args.reuse_5_report)


if __name__ == "__main__":
    main()
