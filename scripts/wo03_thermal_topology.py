"""Execute a refined opaque-wall thermal topology comparison without changing hardware."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import scipy
import yaml

from src.analysis.records import AnalysisRecord, export_record, load_compatible
from src.analysis.thermal_radial import known_cases
from src.analysis.thermal_topology import run_thermal_topology
from src.sim.inputs import source_hashes
from src.vehicle.schema import load_vehicle, vehicle_input_paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-thermal-topology.yaml")
    )
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    args = parser.parse_args()
    study = yaml.safe_load(args.config.read_text())
    cfgpath = Path("configs/engineering/wo03.yaml")
    cfg = yaml.safe_load(cfgpath.read_text())
    paths = [
        Path("configs/vehicle/platform") / (name + ".yaml")
        for name in ["performance", "tvc-finned", "tvc-finless"]
    ]
    paths.append(Path("configs/vehicle/wo02/performance-g54.yaml"))
    inputs = {args.config, cfgpath, Path("scripts/wo03_thermal_topology.py")}
    inputs.update(Path("src/vehicle").glob("*.py"))
    inputs.update(Path("src/cad").glob("*.py"))
    inputs.update(
        Path("src/analysis") / name
        for name in [
            "__init__.py",
            "engineering.py",
            "records.py",
            "thermal_radial.py",
            "thermal_topology.py",
        ]
    )
    inputs.add(Path("src/sim/inputs.py"))
    for path in paths:
        inputs.update(vehicle_input_paths(path))
    hashes = {
        p.resolve().relative_to(Path.cwd()).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in inputs
    }
    for path in paths:
        hashes.update(source_hashes(load_vehicle(path)))
    run = datetime.now(UTC).strftime("wo03-thermal-%Y%m%dT%H%M%S%fZ")
    out = Path("build") / run
    out.mkdir()
    known = known_cases()
    summaries = []
    for path in paths:
        vehicle = load_vehicle(path)
        lower = run_thermal_topology(
            vehicle, cfg, study, False, cells=study["refinement_cells"][-1]
        )
        levels = [
            run_thermal_topology(vehicle, cfg, study, True, cells=cells)
            for cells in study["refinement_cells"]
        ]
        temporal = run_thermal_topology(
            vehicle, cfg, study, True, cells=study["refinement_cells"][-1], max_step_s=1
        )
        delta_space = float(
            np.max(
                np.abs(
                    np.array(levels[-1]["temperature_k"]) - np.array(levels[-2]["temperature_k"])
                )
            )
        )
        delta_time = float(
            np.max(
                np.abs(np.array(levels[-1]["temperature_k"]) - np.array(temporal["temperature_k"]))
            )
        )
        folder = out / vehicle.id
        folder.mkdir()
        artifact_hashes = {}
        for filename, result in [
            ("lower.json", lower),
            *[(f'upper-{r["radial_cells"]}.json', r) for r in levels],
            ("time-refined.json", temporal),
        ]:
            artifact = folder / filename
            artifact.write_text(json.dumps(result, separators=(",", ":"), allow_nan=False) + "\n")
            artifact_hashes[filename] = hashlib.sha256(artifact.read_bytes()).hexdigest()
        identity = {
            "configuration_id": vehicle.id,
            "resolved_spec_sha256": hashlib.sha256(
                vehicle.model_dump_json(by_alias=True).encode()
            ).hexdigest(),
            "cad_revision_sha256": hashlib.sha256(
                b"".join(p.read_bytes() for p in sorted(Path("src/cad").glob("*.py")))
            ).hexdigest(),
            "part_shape_sha256": {
                p.id: p.cad_mass.shape_sha256 for p in vehicle.parts if p.cad_mass
            },
        }
        assets = {}
        fields = []
        cases = {}
        for case in [lower, levels[-1]]:
            case_id = case["case"] + "-v2"
            artifact = f"fields/{case_id}.json"
            payload = {"values": case["temperature_k"], "part_ids": case["part_ids"]}
            encoded = json.dumps(payload, sort_keys=True, allow_nan=False).encode() + b"\n"
            assets[artifact] = payload
            cases[case_id] = {
                "kind": "transient_thermal",
                "model": case["model"],
                "boundary": case["case_boundary_basis"],
                "axial_radial_topology": case["radial_bands"],
                "estimated_settings": cfg["thermal"],
                "study": study,
            }
            fields.append(
                {
                    "id": case_id + "-temperature",
                    "case_id": case_id,
                    "quantity": "temperature",
                    "component": "uniform part mean; radial liner is capacity weighted",
                    "units": "K",
                    "association": "part",
                    "part_ids": case["part_ids"],
                    "times_s": case["times_s"],
                    "artifact": artifact,
                    "artifact_sha256": hashlib.sha256(encoded).hexdigest(),
                    "sample_count": len(case["part_ids"]),
                    "reported_extrema": {
                        "part_mean_peaks": case["peaks"],
                        "liner_radial_peak_c": case["liner_radial_peak_c"],
                    },
                    "coverage_notes": "Modeled part means only. Other parts and spatial hot spots are unavailable; no CAD face gradient is inferred.",
                    "evidence": {
                        "provenance": "calculated",
                        "validation": (
                            "numerically_verified"
                            if known["passed"]
                            and max(delta_space, delta_time) < study["refinement_peak_delta_k"]
                            else "failed"
                        ),
                        "known_case_verified": bool(known["passed"]),
                        "mesh_converged": max(delta_space, delta_time)
                        < study["refinement_peak_delta_k"],
                        "assumptions": study["limitations"],
                        "limits": [
                            "One-dimensional radial liner and coaxial axial-band network. Physical temperatures and three-dimensional radiation remain unvalidated."
                        ],
                        "sources": [
                            str(args.config),
                            str(cfgpath),
                            "src/analysis/thermal_radial.py",
                            "src/analysis/thermal_topology.py",
                        ],
                        "uncertainty": "Explicit estimated property and boundary scenarios, not measured confidence intervals.",
                        "required_physical_tests": [
                            "Instrumented exact-motor external-case and structure temperatures through soak",
                            "Hot coupons, adhesive and assembled mechanism tests",
                        ],
                        "report": f"runs/{run}/record.json",
                    },
                }
            )
        analysis = AnalysisRecord.model_validate(
            {
                "run_id": run + "-" + vehicle.id,
                "identity": identity,
                "cases": cases,
                "fields": fields,
                "tools": {
                    "solver": "SciPy solve_ivp BDF",
                    "scipy": scipy.__version__,
                    "numpy": np.__version__,
                },
                "input_sha256": hashes,
            }
        )
        analysis_manifest = export_record(folder / "analysis", analysis, assets)
        load_compatible(analysis_manifest, analysis.identity)
        summary = {
            "identity": identity,
            "lower_peaks": lower["peaks"],
            "upper_peaks": levels[-1]["peaks"],
            "spatial_refinement_max_delta_k": delta_space,
            "time_refinement_max_delta_k": delta_time,
            "refinement_passed": max(delta_space, delta_time) < study["refinement_peak_delta_k"],
            "max_energy_residual_j": max(
                r["energy_residual_j"] for r in [lower, *levels, temporal]
            ),
            "fields_directory": str(folder),
            "artifact_sha256": artifact_hashes,
            "source_model_version": levels[-1]["model"],
            "analysis_manifest": str(analysis_manifest),
            "export_consumer_check_passed": True,
            "thermal_acceptance_passed": False,
        }
        summaries.append(summary)
        print(
            vehicle.id,
            "upper peaks C",
            [(p["part_id"], round(p["peak_c"], 1)) for p in levels[-1]["peaks"]],
            flush=True,
        )
    result = {
        "run_id": run,
        "tools": {
            "solver": "SciPy solve_ivp BDF",
            "scipy": scipy.__version__,
            "numpy": np.__version__,
        },
        "known_cases": known,
        "vehicles": summaries,
        "input_sha256": hashes,
        "inputs_unchanged": all(
            hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items()
        ),
        "thermal_acceptance_passed": False,
        "expanded_wo03_benchmark_passed": False,
        "limitations": study["limitations"],
        "cost_usd": 0,
        "flight_ready": False,
    }
    record = Path("runs") / run
    record.mkdir()
    (record / "record.json").write_text(json.dumps(result, indent=2) + "\n")
    print(record / "record.json")
    return int(
        not known["passed"]
        or not result["inputs_unchanged"]
        or not all(r["refinement_passed"] for r in summaries)
    )


if __name__ == "__main__":
    raise SystemExit(main())
