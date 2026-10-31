"""Fixture-first, one bounded native analysis mesh; no thermal/optical solve."""

from __future__ import annotations

import os

for key in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"]:
    os.environ[key] = "1"

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import yaml

from scripts.wo03_cad_gas_mesh import fixture_source
from src.analysis.cad_gas_mesh import load_source, native_face_mapping, sha
from src.analysis.native_gas_mesh import native_mesh


def execute_worker(args: Any, cfg: dict[str, Any]) -> None:
    started = time.monotonic()
    result: dict[str, Any] = {
        "status": "incomplete",
        "thermal_solve": False,
        "new_wall_quadrature_required": True,
    }
    try:
        frozen_cfg = yaml.safe_load(Path(cfg["frozen_source_config"]).read_text())
        if args.worker == "fixtures":
            cases = []
            for kind in ["split_wall", "cavity", "thin_barrier_window"]:
                source = fixture_source(kind, args.output / kind)
                source["paths"] = {"step": source["step"]}
                mapping = native_face_mapping(
                    source["step"], source["faces"], source["boundary"], frozen_cfg["mapping"]
                )
                arrays, audit = native_mesh(source, mapping, cfg, args.output / kind)
                if (
                    abs(audit["mesh_checks"]["tetra_volume_mm3"] - source["expected_volume_mm3"])
                    > 1e-5
                ):
                    raise ValueError("Independent native fixture volume mismatch")
                if kind == "split_wall":
                    left = set(
                        arrays["boundary_triangles"][arrays["boundary_group_ids"] == 0].ravel()
                    )
                    right = set(
                        arrays["boundary_triangles"][arrays["boundary_group_ids"] == 1].ravel()
                    )
                    if not left & right:
                        raise ValueError("Native split-wall shared nodes lost")
                if kind == "cavity":
                    center = arrays["points_m"][arrays["tetrahedra"]].mean(axis=1) * 1000
                    if ((center > 2) & (center < 18)).all(axis=1).any():
                        raise ValueError("Opaque fixture cavity filled with gas")
                cases.append(
                    {
                        "kind": kind,
                        "checks": {
                            k: v
                            for k, v in audit["mesh_checks"].items()
                            if k not in ["face_area_mm2", "group_area_mm2"]
                        },
                    }
                )
            result.update(status="fixtures_passed", cases=cases)
        else:
            fixture_result = json.loads((args.fixture_cache / "result.json").read_text())
            if fixture_result["status"] != "fixtures_passed":
                raise ValueError("Independent native fixtures have not passed")
            source = load_source(frozen_cfg["source"])
            mapping_path = Path(cfg["native_mapping"])
            if sha(mapping_path) != cfg["native_mapping_sha256"]:
                raise ValueError("Frozen native face proof hash mismatch")
            mapping = json.loads(mapping_path.read_text())
            if mapping["source_step_sha256"] != sha(source["paths"]["step"]):
                raise ValueError("Frozen native face proof source changed")
            arrays, audit = native_mesh(source, mapping, cfg, args.output)
            mesh_path = args.output / "mesh.npz"
            np.savez_compressed(mesh_path, **arrays)
            (args.output / "boundary-groups.json").write_text(
                json.dumps(
                    {
                        "groups": source["groups"],
                        "metadata": {
                            "new_wall_quadrature_required": True,
                            "copy_optical_M_B_D_forbidden": True,
                            "source_sha256": source["source_sha256"],
                            "all_exterior_triangles_labelled": True,
                            "shared_nodes_retained": True,
                            "halfwall_mapping_unassigned": True,
                        },
                    },
                    indent=2,
                )
                + "\n"
            )
            (args.output / "mesh-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
            result.update(
                status="diagnostic_mesh_valid",
                mesh_path=str(mesh_path),
                mesh_sha256=sha(mesh_path),
                audit_path=str(args.output / "mesh-audit.json"),
                audit_sha256=sha(args.output / "mesh-audit.json"),
                counts={
                    k: audit["mesh_checks"][k]
                    for k in [
                        "node_count",
                        "boundary_node_count",
                        "interior_node_count",
                        "tetrahedron_count",
                    ]
                },
            )
    except RuntimeError as exc:
        result.update(status="incomplete_resource_limit", error=repr(exc))
    except Exception as exc:  # noqa: BLE001 - retain native geometry/numerical failure
        result.update(status="invalid_mesh", error=repr(exc))
    result["elapsed_s"] = time.monotonic() - started
    result["gates"] = {
        "valid_mesh": result["status"] in ["diagnostic_mesh_valid", "fixtures_passed"],
        "complete_calculation": result["status"] not in ["incomplete", "incomplete_resource_limit"],
        "numerical_accuracy": "unestablished",
        "temperature_acceptance": "not_computed",
    }
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    if result["status"] not in ["diagnostic_mesh_valid", "fixtures_passed"]:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-native-gas-mesh.yaml")
    )
    parser.add_argument("--preset", choices=["tiny", "sim", "rl", "real"], default="tiny")
    parser.add_argument("--stage", choices=["fixtures", "actual"], required=True)
    parser.add_argument("--worker", choices=["fixtures", "actual"])
    parser.add_argument("--fixture-cache", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    if args.worker:
        execute_worker(args, cfg)
        return
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "study-config.yaml").write_text(args.config.read_text())
    paths = [
        args.config,
        Path(__file__),
        Path("src/analysis/native_gas_mesh.py"),
        Path(cfg["frozen_source_config"]),
        Path(cfg["native_mapping"]),
    ]
    before = {str(p): sha(p) for p in paths}
    command = [
        sys.executable,
        str(Path(__file__)),
        "--config",
        str(args.config),
        "--stage",
        args.stage,
        "--worker",
        args.stage,
        "--output",
        str(args.output),
    ]
    if args.fixture_cache:
        command += ["--fixture-cache", str(args.fixture_cache)]
    start = time.monotonic()
    report: dict[str, Any] = {
        "source_sha256": before,
        "stage": args.stage,
        "actual_attempt_limit": 1,
        "thermal_solve": False,
        "adoption": False,
    }
    with (args.output / "worker.log").open("w") as log:
        try:
            completed = subprocess.run(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=cfg["caps"]["max_worker_seconds"],
                check=False,
            )
            report["exit_code"] = completed.returncode
            report["result"] = json.loads((args.output / "result.json").read_text())
        except subprocess.TimeoutExpired:
            report["result"] = {
                "status": "incomplete_time_cap",
                "gates": {
                    "valid_mesh": "unestablished",
                    "complete_calculation": False,
                    "numerical_accuracy": "unestablished",
                    "temperature_acceptance": "not_computed",
                },
            }
    report.update(
        elapsed_s=time.monotonic() - start,
        inputs_unchanged=before == {str(p): sha(p) for p in paths},
    )
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "status": report["result"]["status"],
                "elapsed_s": report["elapsed_s"],
                "inputs_unchanged": report["inputs_unchanged"],
            },
            indent=2,
        )
    )
    if report["result"]["status"] not in ["diagnostic_mesh_valid", "fixtures_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
