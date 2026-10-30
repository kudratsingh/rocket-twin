"""Record reconciled vehicle mass, full inertia and growth/depletion sensitivities.

The motor-CG interval is an explicit unsourced sensitivity, not a measured motor
property or a replacement for the active static-margin requirement. No geometry
or mass is edited by this report. Parallel-axis calculations use body coordinates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import yaml

from src.vehicle.aero import center_of_pressure
from src.vehicle.benchmark import screen_launch
from src.vehicle.mass import MassProperties, mass_properties
from src.vehicle.schema import load_vehicle, vehicle_input_paths


def add_growth(m: MassProperties, amount: float, station: float) -> dict[str, Any]:
    origin = np.array([-m.cg_m, *m.cg_lateral_m])
    point = np.array([-station, 0.0, 0.0])
    total = m.mass_kg + amount
    cg = (m.mass_kg * origin + amount * point) / total
    inertia = m.inertia_kg_m2.copy()
    for mass, position in [(m.mass_kg, origin), (amount, point)]:
        d = position - cg
        inertia += mass * (np.dot(d, d) * np.eye(3) - np.outer(d, d))
    return {
        "mass_kg": total,
        "cg_station_m": float(-cg[0]),
        "cg_lateral_body_m": cg[1:].tolist(),
        "inertia_body_kg_m2": inertia.tolist(),
        "growth_mass_kg": amount,
        "growth_station_m": station,
        "growth_inertia_basis": "Point-mass allowance; no invented component shape.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/platform.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    parser.add_argument("--evidence", type=Path, action="append", default=[])
    args = parser.parse_args()
    platform = yaml.safe_load(args.config.read_text())
    paths = platform["vehicles"] + ["configs/vehicle/wo02/performance-g54.yaml"]
    inputs = {args.config, Path(__file__)}
    inputs.update(Path("src/vehicle").glob("*.py"))
    inputs.update(Path("src/cad").glob("*.py"))
    for path in paths:
        inputs.update(vehicle_input_paths(path))

    def hashes() -> dict[str, str]:
        return {
            p.resolve()
            .relative_to(Path.cwd())
            .as_posix(): hashlib.sha256(p.read_bytes())
            .hexdigest()
            for p in sorted(inputs)
        }

    before = hashes()
    vehicles = []
    for path in paths:
        v = load_vehicle(path)
        assert v.motor and v.design
        cp = center_of_pressure(v)
        diameter = v.airframe["body_diameter_m"]
        spec_sha = hashlib.sha256(v.model_dump_json(by_alias=True).encode()).hexdigest()
        states = []
        for burn in [0.0, 0.5, 1.0]:
            mass = mass_properties(v, burn)
            for growth, station in [
                (0.0, 0.0),
                (v.design.mass_allowance_kg, 0.0),
                (v.design.mass_allowance_kg, v.airframe["length_m"]),
            ]:
                row = add_growth(mass, growth, station)
                row.update(
                    burn_fraction=burn,
                    cp_station_m=cp,
                    static_margin_cal=(cp - row["cg_station_m"]) / diameter,
                )
                states.append(row)
        loaded = mass_properties(v)
        motor = next(p for p in v.parts if p.type == "motor")
        sensitivity = []
        for shift in [-0.1 * motor.geometry["length_m"], 0.1 * motor.geometry["length_m"]]:
            cg = (
                loaded.mass_kg * loaded.cg_m
                + motor.resolved_mass_kg * shift
                + v.design.mass_allowance_kg * v.airframe["length_m"]
            ) / (loaded.mass_kg + v.design.mass_allowance_kg)
            sensitivity.append(
                {"motor_cg_shift_m": shift, "cg_station_m": cg, "margin_cal": (cp - cg) / diameter}
            )
        manifest_path = Path("build") / v.id / "manifest.json"
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        vehicles.append(
            {
                "configuration_id": v.id,
                "source": str(path),
                "resolved_spec_sha256": spec_sha,
                "cad_manifest": str(manifest_path),
                "cad_manifest_matches_spec": manifest.get("identity", {}).get(
                    "resolved_spec_sha256"
                )
                == spec_sha,
                "loaded_mass_kg": loaded.mass_kg,
                "loaded_cg_station_m": loaded.cg_m,
                "loaded_inertia_body_kg_m2": loaded.inertia_kg_m2.tolist(),
                "cp_station_m": cp,
                "states": states,
                "minimum_growth_depletion_margin_cal": min(r["static_margin_cal"] for r in states),
                "passive_margin_requirement_cal": v.design.minimum_static_margin_cal,
                "passive_margin_requirement_applicable": v.design.minimum_static_margin_cal
                is not None,
                "motor_cg_sensitivity": sensitivity,
                "motor_cg_sensitivity_basis": "Estimated exploratory +/-10% motor-length shift from uniform-midpoint CG; not measured, not a certification tolerance. Other parts and the full aft growth allowance are retained.",
                "launch_screen": screen_launch(v),
                "mass_basis": "CAD volume and estimated density for custom solids; supplied/estimated commercial masses. None measured.",
                "parts_mass_budget_kg": loaded.budget_kg,
                "preliminary_bom_usd": sum(p.build.cost_usd for p in v.parts if p.build),
            }
        )
    evidence = [
        {
            "path": str(p),
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "run_id": json.loads(p.read_text()).get("run_id"),
        }
        for p in args.evidence
    ]
    run_id = datetime.now(UTC).strftime("wo03-integrated-%Y%m%dT%H%M%S%fZ")
    out = Path("runs") / run_id
    out.mkdir()
    record = {
        "run_id": run_id,
        "work_order": "03",
        "vehicles": vehicles,
        "evidence": evidence,
        "input_sha256": before,
        "inputs_unchanged": before == hashes(),
        "expanded_wo03_benchmark_passed": False,
        "flight_ready": False,
        "cost_usd": 0,
    }
    (out / "record.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    lines = [
        "# Integrated WO-03 vehicle properties",
        "",
        f"Generated by `scripts/wo03_integrated_report.py`; record `{run_id}`. Mass properties are calculated using estimated inputs, not measured hardware. The full 50 g allowance remains separate from parts. CP uses the shared Barrowman model; large-angle applicability is limited.",
        "",
        "| Configuration | Loaded mass, g | With allowance, g | CG, mm from nose | CP, mm | Minimum growth/depletion margin, cal | Guide screen, m/s |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for v in vehicles:
        launch = v["launch_screen"]
        lines.append(
            f"| {v['configuration_id']} | {v['loaded_mass_kg']*1000:.3f} | {launch['worst_case_mass_kg']*1000:.3f} | {v['loaded_cg_station_m']*1000:.3f} | {v['cp_station_m']*1000:.3f} | {v['minimum_growth_depletion_margin_cal']:.6f} | {launch['rail_exit_speed_mps']:.4f} |"
        )
    lines += [
        "",
        "The margin minimum checks launch, half depletion and burnout, with no growth and all growth at either axial extreme. Finless static margin is reported for information; it has no positive passive-margin gate. Its control and burnout/recovery transition remain separate requirements.",
        "",
        "The motor-CG sensitivity below is an additional assumption check, separate from the established growth/depletion screen. A passing growth screen does not resolve exact motor CG/source correspondence.",
        "",
        "| Configuration | Motor CG shift, mm | Aft-growth margin, cal |",
        "|---|---:|---:|",
    ]
    for v in vehicles:
        for s in v["motor_cg_sensitivity"]:
            lines.append(
                f"| {v['configuration_id']} | {s['motor_cg_shift_m']*1000:+.3f} | {s['margin_cal']:.6f} |"
            )
    lines += [
        "",
        "Full loaded inertia tensors, kg m², in the project body axes (x noseward, z down):",
        "",
    ]
    for v in vehicles:
        lines += [
            f"**{v['configuration_id']}**",
            "",
            "```json",
            json.dumps(v["loaded_inertia_body_kg_m2"], indent=2),
            "```",
            "",
        ]
    lines += [
        "All growth/depletion tensors and per-part budgets are in the run record. Growth is treated as a point mass with no invented intrinsic inertia. Rotor/servo state-dependent moving inertia remains a later dynamic model requirement.",
        "",
        "Evidence references (file SHA-256 stored in the record):",
        "",
    ] + [f"- `{e['path']}`" for e in evidence]
    lines += [
        "",
        "Expanded WO-03 acceptance and flight readiness remain false. See [correction closure](wo03-correction-closure.md) for remaining design failures and the separate later physical qualification gates.",
        "",
    ]
    Path("docs/wo03-integrated-vehicle.md").write_text("\n".join(lines))
    print(out / "record.json")
    return 0 if record["inputs_unchanged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
