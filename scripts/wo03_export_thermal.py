"""Export exact recorded thermal samples; no solve, relabeling or active registration."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.records import AnalysisRecord, export_record, load_compatible

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    path = args.record.resolve(strict=True)
    run = json.loads(path.read_bytes())
    config_key = "configs/studies/wo03-finite-transient.yaml"
    config_path = path.parent / "source-snapshot" / config_key
    if hashlib.sha256(config_path.read_bytes()).hexdigest() != run["source_sha256"][config_key]:
        raise ValueError("Recorded configuration snapshot changed")
    config = yaml.safe_load(config_path.read_text())
    source_key = config["candidate_record"]
    source_path = path.parent / "source-snapshot" / source_key
    if hashlib.sha256(source_path.read_bytes()).hexdigest() != run["source_sha256"][source_key]:
        raise ValueError("Recorded source identity changed")
    source = json.loads(source_path.read_bytes())
    if (
        source["candidate_identity"] != run["candidate_identity"]
        or source["cad_revision_sha256"] != run["cad_revision_sha256"]
    ):
        raise ValueError("Temperature data and geometry have different identities")
    identity = {
        "configuration_id": source["configuration_id"],
        "resolved_spec_sha256": source["candidate_identity"],
        "cad_revision_sha256": source["cad_revision_sha256"],
        "part_shape_sha256": source["part_shape_sha256"],
    }
    cases, fields, assets = {}, [], {}
    for index, row in enumerate(run["rows"]):
        output = ROOT / row["output"]
        if hashlib.sha256(output.read_bytes()).hexdigest() != row["output_sha256"]:
            raise ValueError("Recorded temperature history changed")
        result = json.loads(output.read_bytes())
        name = f"thermal-{index:03d}"
        artifact = name + ".json"
        payload = {"values": result["temperature_k"]}
        encoded = json.dumps(payload, sort_keys=True, allow_nan=False).encode() + b"\n"
        assets[artifact] = payload
        cases[name] = {
            "source_case": row["case"],
            "material_corner": row["corner"],
            "missing_end_reservoir": row["end_reservoir_mode"],
            "model": result["model"],
            "source_run": run["run_id"],
            "source_output": row["output"],
            "source_output_sha256": row["output_sha256"],
            "projection_reuse": run.get("projection_reuse"),
            "engineering_acceptance_passed": False,
        }
        evidence = {
            "provenance": "calculated",
            "validation": "unvalidated",
            "known_case_verified": all(
                c["passed"] for c in result["common_surface_jacobian_verification"]
            ),
            "mesh_converged": False,
            "assumptions": [
                "Part-average lumped thermal states with radial liner cells; all source case/material/geometry assumptions retained.",
                "Finite coaxial radiation projection excludes actual angular slots/rails/pads; slotted bond proxy is incomplete.",
                "Missing-end ambient/case reservoir assignments are exploratory physical assumptions.",
            ],
            "limits": [
                "Scoped diagnostic, not the complete required configuration/gap/contact matrix.",
                "No local CAD hot spots, measured temperatures or build/flight acceptance.",
                "Cannot be displayed on a different candidate, CAD revision or active configuration.",
            ],
            "sources": [str(path.relative_to(ROOT)), row["output"]],
            "uncertainty": "Estimated boundary/material/contact inputs; raw geometry/sampling and gas-coverage uncertainties remain open.",
            "required_physical_tests": [
                "Instrumented motor case and structure soak",
                "Representative hot bonds, materials and assembled mechanism",
            ],
            "report": str(path.relative_to(ROOT)),
        }
        fields.append(
            {
                "id": name + "-part-temperature",
                "case_id": name,
                "quantity": "temperature",
                "component": "Part mean in kelvin; liner capacity-weighted mean, not its hottest radial cell",
                "units": "K",
                "association": "part",
                "part_ids": result["part_ids"],
                "times_s": result["times_s"],
                "artifact": artifact,
                "artifact_sha256": hashlib.sha256(encoded).hexdigest(),
                "sample_count": len(result["part_ids"]),
                "evidence": evidence,
                "reported_extrema": {
                    "part_mean_peaks": result["peaks"],
                    "liner_radial_peak_c": result["liner_radial_peak_c"],
                },
                "coverage_notes": "Only named part averages; other parts and all spatial hot spots unavailable. Superseded cases remain diagnostic.",
            }
        )
        missing = sorted(set(identity["part_shape_sha256"]) - set(result["part_ids"]))
        if missing:
            fields.append(
                {
                    "id": name + "-temperature-unavailable",
                    "case_id": name,
                    "quantity": "temperature",
                    "component": "No recorded temperature coverage",
                    "units": "K",
                    "association": "part",
                    "part_ids": missing,
                    "sample_count": 0,
                    "unavailable_reason": "These parts have no temperature state in this recorded diagnostic.",
                    "coverage_notes": "No zero or ambient-temperature substitute is supplied.",
                    "evidence": {
                        **evidence,
                        "provenance": "unavailable",
                        "validation": "unavailable",
                        "known_case_verified": False,
                    },
                }
            )
    record = AnalysisRecord.model_validate(
        {
            "run_id": run["run_id"],
            "identity": identity,
            "cases": cases,
            "fields": fields,
            "tools": {
                "source_solver": "SciPy BDF, analytic common-surface Jacobian",
                "export": "recorded samples only; no new computation",
            },
            "input_sha256": {
                **run["source_sha256"],
                str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest(),
                str(Path(__file__).resolve().relative_to(ROOT)): hashlib.sha256(
                    Path(__file__).read_bytes()
                ).hexdigest(),
            },
        }
    )
    manifest = export_record(path.parent / "analysis", record, assets)
    load_compatible(manifest, record.identity)
    print(manifest, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
