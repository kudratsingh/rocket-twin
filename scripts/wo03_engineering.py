"""Run preliminary structural/thermal screens and export recorded Analysis fields."""

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

from src.analysis.engineering import structural
from src.analysis.motor_support import motor_support
from src.analysis.records import AnalysisRecord, export_record, load_compatible
from src.analysis.thermal_topology import run_thermal_topology
from src.sim.inputs import source_hashes
from src.vehicle.schema import load_vehicle, vehicle_input_paths


def encoded(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, allow_nan=False).encode() + b"\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/platform.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    parser.add_argument("--require-benchmark", action="store_true")
    args = parser.parse_args()
    cfgpath = Path("configs/engineering/wo03.yaml")
    study_path = Path("configs/studies/wo03-thermal-topology.yaml")
    cfg = yaml.safe_load(cfgpath.read_text())
    study = yaml.safe_load(study_path.read_text())
    platform = yaml.safe_load(args.config.read_text())
    paths = platform["vehicles"] + ["configs/vehicle/wo02/performance-g54.yaml"]
    run = datetime.now(UTC).strftime("wo03-engineering-%Y%m%dT%H%M%S%fZ")
    out = Path("runs") / run
    out.mkdir()
    cad_hash = hashlib.sha256(
        b"".join(p.read_bytes() for p in sorted(Path("src/cad").glob("*.py")))
    ).hexdigest()
    inputs = {args.config, cfgpath, study_path}
    for p in paths:
        inputs.update(vehicle_input_paths(p))
    inputs.update(Path("src").rglob("*.py"))
    inputs.add(Path(__file__).resolve().relative_to(Path.cwd()))
    hashes = {
        p.resolve().relative_to(Path.cwd()).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in inputs
    }
    for path in paths:
        hashes.update(source_hashes(load_vehicle(path)))
    summaries = []
    for path in paths:
        v = load_vehicle(path)
        assert v.motor
        structure = structural(v, cfg)
        support = motor_support(v, cfg, float(structure["peak_scaled_thrust_n"]))
        structure["motor_support"] = support
        mount = next((p for p in v.parts if p.id == "motor_mount"), None)
        if mount and mount.cad and mount.cad.generator == "motor_cassette":
            rails = support["screens"].get("rails")
            for row in structure["rows"]:
                if row["part_id"] == mount.id and row["case"] == "motor_thrust":
                    row.update(
                        {
                            "stress_pa": None,
                            "strength_bound_pa": None,
                            "margin": None,
                            "passed": None,
                            "evidence": "unavailable: legacy structural() rail area is invalid for the current motor cassette",
                            "unavailable_reason": (
                                "The legacy mount equation assumes a 3x6x3 mm rail section. "
                                "Use the recorded actual-CAD motor_support rail screen instead."
                            ),
                            "motor_support_rail_screen": rails,
                        }
                    )
        thermal_cases = [
            run_thermal_topology(v, cfg, study, severe, cells=8) for severe in (False, True)
        ]
        refined = run_thermal_topology(v, cfg, study, True, cells=8, max_step_s=1.0)
        delta = float(
            np.max(
                np.abs(
                    np.array(refined["temperature_k"]) - np.array(thermal_cases[1]["temperature_k"])
                )
            )
        )
        identity = {
            "configuration_id": v.id,
            "resolved_spec_sha256": hashlib.sha256(
                v.model_dump_json(by_alias=True).encode()
            ).hexdigest(),
            "cad_revision_sha256": cad_hash,
            "part_shape_sha256": {p.id: p.cad_mass.shape_sha256 for p in v.parts if p.cad_mass},
        }
        if len(identity["part_shape_sha256"]) != len(v.parts):
            raise ValueError("Reconcile all CAD properties before analysis export")
        ids = [p.id for p in v.parts]
        fields = []
        assets = {}
        cases = {}
        evidence = {
            "provenance": "calculated",
            "validation": "unvalidated",
            "assumptions": [
                cfg["scope"],
                "Material, case boundary, contact and load inputs are estimates.",
                "Fin panel screen remains an unreinforced flat-panel hand bound; installed tabs/gussets are not represented as a gusset FEA pass.",
            ],
            "limits": [
                "Part means and elementary load-path screens; no qualified spatial FEA field."
            ],
            "sources": [str(cfgpath), str(study_path), *cfg["material_sources"].values()],
            "uncertainty": "Bounded scenarios, not a probability distribution or measured physical validation.",
            "required_physical_tests": [
                "Material/orientation and hot joint coupons; instrumented burn/soak; proof and recovery tests."
            ],
            "report": f"{run}/record.json",
        }
        for t in thermal_cases:
            case = t["case"]
            cases[case] = {
                "kind": "transient_thermal",
                "boundary": t["case_boundary_basis"],
                "external_case_peak_c": t.get(
                    "external_case_peak_c", t.get("prescribed_case_peak_c")
                ),
                "ambient_c": t["ambient_c"],
                "cooling_tau_s": t.get("cooling_tau_s", t.get("post_burn_cooling_tau_s")),
                "radial_cells": t.get("radial_cells"),
                "thermal_model": t.get("model", "legacy-thermal-radial-v1"),
                "pad_conduction": t.get("pad_conduction", []),
            }
            asset = f"fields/{case}.json"
            values = [
                [frame[t["part_ids"].index(id)] if id in t["part_ids"] else None for id in ids]
                for frame in t["temperature_k"]
            ]
            payload = {"values": values, "resolution": "uniform part mean", "part_ids": ids}
            assets[asset] = payload
            fields.append(
                {
                    "id": case + "-temperature",
                    "case_id": case,
                    "quantity": "temperature",
                    "component": "uniform part mean",
                    "units": "K",
                    "association": "part",
                    "part_ids": ids,
                    "times_s": t["times_s"],
                    "artifact": asset,
                    "artifact_sha256": hashlib.sha256(encoded(payload)).hexdigest(),
                    "sample_count": len(ids),
                    "coverage_notes": "Null parts are not modeled. No fabricated surface gradient.",
                    "reported_extrema": {"parts": t["peaks"]},
                    "evidence": evidence,
                }
            )
        for case in sorted({r["case"] for r in structure["rows"]}):
            rows = {r["part_id"]: r for r in structure["rows"] if r["case"] == case}
            for row in rows.values():
                row["displacement_screen_m"] = row.get(
                    "tip_deflection_upper_m", row.get("elastic_shortening_m")
                )
            cases[case] = {
                "kind": "structural_screen",
                "rows": list(rows.values()),
                "design_factor": cfg["loads"]["design_factor"],
            }
            for quantity, key, unit in [
                ("stress", "stress_pa", "Pa"),
                ("design_margin", "margin", "1"),
                ("displacement", "displacement_screen_m", "m"),
            ]:
                asset = f"fields/{case}-{quantity}.json"
                payload = {
                    "values": [[rows[id].get(key) if id in rows else None for id in ids]],
                    "resolution": "part scalar screen",
                    "part_ids": ids,
                }
                available = any(value is not None for value in payload["values"][0])
                if available:
                    assets[asset] = payload
                fields.append(
                    {
                        "id": case + "-" + quantity,
                        "case_id": case,
                        "quantity": quantity,
                        "component": (
                            "elementary nominal stress"
                            if quantity == "stress"
                            else (
                                "part maximum/axial displacement screen"
                                if quantity == "displacement"
                                else "screen strength margin"
                            )
                        ),
                        "units": unit,
                        "association": "part",
                        "part_ids": ids,
                        "artifact": asset if available else None,
                        "artifact_sha256": (
                            hashlib.sha256(encoded(payload)).hexdigest() if available else None
                        ),
                        "sample_count": len(ids) if available else 0,
                        "unavailable_reason": (
                            None if available else "No calculation for this quantity in this case."
                        ),
                        "coverage_notes": "Only listed rows evaluated; absent parts are unavailable. Buckling and connection effects remain separate.",
                        "margin_definition": (
                            "strength_bound/(design_factor*nominal_stress)-1; pass >=0. Excludes unmodeled failure modes."
                            if quantity == "design_margin"
                            else None
                        ),
                        "evidence": (
                            evidence
                            if available
                            else {
                                **evidence,
                                "provenance": "unavailable",
                                "validation": "unavailable",
                            }
                        ),
                    }
                )
        record = AnalysisRecord.model_validate(
            {
                "run_id": run + "-" + v.id,
                "identity": identity,
                "cases": cases,
                "fields": fields,
                "tools": {
                    "numpy": np.__version__,
                    "thermal": "SciPy solve_ivp BDF rtol1e-8 atol1e-7",
                },
                "input_sha256": hashes,
            }
        )
        folder = Path("build") / v.id / "analysis" / run
        manifest = export_record(folder, record, assets)
        load_compatible(manifest, record.identity)
        bypart: dict[str, list[dict[str, Any]]] = {p.id: [] for p in v.parts}
        for t in thermal_cases:
            for row in t["peaks"]:
                bypart[row["part_id"]].append({"case": t["case"], **row})
        for row in structure["rows"]:
            bypart[row["part_id"]].append(row)
        table: list[dict[str, Any]] = []
        for p in v.parts:
            e = p.engineering
            table.append(
                {
                    "part_id": p.id,
                    "function": e.function if e else p.learn,
                    "material": p.material,
                    "manufacturing_method": p.build.method if p.build else None,
                    "mass_basis": p.cad.mass_basis if p.cad else None,
                    "mass_kg": p.resolved_mass_kg,
                    "critical_dimensions_si": p.geometry,
                    "cad_feature_dimensions_mm": p.cad.parameters if p.cad else {},
                    "mass_provenance": {"estimated": p.estimate, "citation": p.cite},
                    "motor_support": support if p.id == "motor_mount" else None,
                    "motor_support_rail_screen": (
                        support["screens"].get("rails") if p.id == "motor_mount" else None
                    ),
                    "print_settings": p.print_settings.model_dump() if p.print_settings else None,
                    "tolerances_mm": e.tolerances_mm if e else None,
                    "load_cases": e.load_cases if e else [],
                    "thermal_cases": e.thermal_cases if e else [],
                    "results": bypart[p.id],
                    "evidence_status": (
                        "calculated_with_estimated_inputs" if bypart[p.id] else "unavailable"
                    ),
                    "physical_verification": (
                        e.required_physical_verification if e else ["Missing engineering metadata"]
                    ),
                }
            )
        (folder / "engineering-table.json").write_text(json.dumps(table, indent=2) + "\n")
        header = "| Part | Function | Material / method | Mass basis; g | Critical dimensions / tolerances | Cases | Results / margin | Motor support rail screen | Evidence / physical verification |\n|---|---|---|---|---|---|---|---|---|\n"

        def cell(value: Any) -> str:
            return str(value).replace("|", "/").replace("\n", " ")

        lines = []
        for p in table:
            results = (
                "; ".join(
                    f"{r['case']}: {r.get('margin') if r.get('margin') is not None else r.get('unavailable_reason', r.get('margin_k', 'unavailable'))}"
                    for r in p["results"]
                )
                or "Unavailable"
            )
            vals = [
                p["part_id"],
                p["function"],
                f"{p['material']} / {p['manufacturing_method']}",
                f"{p['mass_basis']}; {p['mass_kg']*1000:.2f}",
                f"{p['critical_dimensions_si']}; +/-mm {p['tolerances_mm']}",
                p["load_cases"],
                results,
                p["motor_support_rail_screen"],
                f"{p['evidence_status']}; {p['physical_verification']}",
            ]
            lines.append("| " + " | ".join(map(cell, vals)) + " |")
        (folder / "engineering-table.md").write_text(
            "# "
            + v.name
            + " engineering screen\n\nPreliminary; all required physical qualification remains open.\n\n"
            + header
            + "\n".join(lines)
            + "\n"
        )
        summary = {
            "vehicle": v.id,
            "structural": structure,
            "motor_support": support,
            "thermal": [
                {
                    "case": t["case"],
                    "peaks": t["peaks"],
                    "energy_residual_j": t["energy_residual_j"],
                    "model": t.get("model", "legacy-thermal-radial-v1"),
                    "pad_conduction": t.get("pad_conduction", []),
                }
                for t in thermal_cases
            ],
            "thermal_step_refinement_max_delta_k": delta,
            "thermal_refinement_threshold_k": study["refinement_peak_delta_k"],
            "thermal_step_refinement_passed": delta < study["refinement_peak_delta_k"],
            "analysis_manifest": str(manifest),
            "export_consumer_check_passed": True,
            "engineering_benchmark_passed": False,
        }
        summaries.append(summary)
        print(
            v.id,
            "exported; upper-case failures:",
            [r["part_id"] for r in thermal_cases[1]["peaks"] if not r["passed"]],
            flush=True,
        )
    result = {
        "run_id": run,
        "input_sha256": hashes,
        "inputs_unchanged": all(
            hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items()
        ),
        "vehicles": summaries,
        "engineering_benchmark_passed": False,
        "open_items": [
            "Critical FEA, known-case/convergence, strength and buckling conclusions",
            "Hot-case history/material limits and design corrections",
            "Tolerance-expanded continuous mechanism, wiring, nozzle and retention",
            "Recovery packing/service access, isolated power and hardware interfaces",
        ],
        "cost_usd": 0,
        "flight_ready": False,
    }
    (out / "record.json").write_text(json.dumps(result, indent=2) + "\n")
    print(out / "record.json")
    return int(args.require_benchmark)


if __name__ == "__main__":
    raise SystemExit(main())
