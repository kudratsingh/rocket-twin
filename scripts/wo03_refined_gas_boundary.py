"""One targeted linear boundary pilot and, only if valid, one old Gmsh fill."""

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

from src.analysis.cad_gas_mesh import (
    interior_seeds,
    load_source,
    sha,
    tetrahedralize,
    verify_volume_mesh,
)
from src.analysis.refined_gas_boundary import (
    edge_table,
    initial_mesh,
    refine,
    split_edges,
    targets,
    validate_partition,
)


def fixtures() -> dict[str, Any]:
    triangle = {
        "vertices_mm": np.array([[1.2, 2.3, 3.4], [2.4, 2.5, 3.6], [1.1, 3.1, 3.9]]),
        "triangles": np.array([[0, 1, 2]]),
    }
    partitions = []
    for bits in range(1, 8):
        child = split_edges(
            initial_mesh(triangle), np.array([i for i in range(3) if bits & (1 << i)])
        )
        partitions.append(validate_partition(triangle, child, closed=False))
    shared = {
        "vertices_mm": np.array(
            [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0]]
        ),
        "triangles": np.array([[0, 1, 2], [1, 3, 2]]),
    }
    edges, _, _ = edge_table(shared["triangles"])
    index = np.flatnonzero((edges == [1, 2]).all(axis=1))
    child = split_edges(initial_mesh(shared), index)
    shared_check = validate_partition(shared, child, closed=False)
    if len(child["vertices_mm"]) != 5 or len(child["triangles"]) != 4:
        raise ValueError("Shared edge midpoint was not propagated to both triangles")
    p = np.array(
        [
            [0.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [1.0, 1.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 0.02],
            [1.0, 0.0, 0.02],
            [1.0, 1.0, 0.02],
            [0.0, 1.0, 0.02],
        ]
    )
    tri = np.array(
        [
            [0, 2, 1],
            [0, 3, 2],
            [4, 5, 6],
            [4, 6, 7],
            [0, 1, 5],
            [0, 5, 4],
            [1, 2, 6],
            [1, 6, 5],
            [2, 3, 7],
            [2, 7, 6],
            [3, 0, 4],
            [3, 4, 7],
        ]
    )
    barrier = {"vertices_mm": p, "triangles": tri}
    refined = initial_mesh(barrier)
    for _ in range(3):
        e, _, _ = edge_table(refined["triangles"])
        marked = np.flatnonzero(
            abs(refined["vertices_mm"][e[:, 1], 2] - refined["vertices_mm"][e[:, 0], 2])
            > 0.005 * (1 + 1e-12)
        )
        if not len(marked):
            break
        refined = split_edges(refined, marked)
    barrier_check = validate_partition(barrier, refined)
    assert refined["vertices_mm"][:, 2].min() == 0 and refined["vertices_mm"][:, 2].max() == 0.02
    return {
        "passed": True,
        "seven_triangle_partition_templates": partitions,
        "shared_edge": shared_check,
        "20um_barrier": barrier_check,
    }


def worker(args: Any, cfg: dict[str, Any]) -> None:
    started = time.monotonic()
    result: dict[str, Any] = {
        "stage": args.stage,
        "status": "incomplete",
        "thermal_solve": False,
        "adoption": False,
        "new_wall_quadrature_required": True,
    }
    try:
        frozen = yaml.safe_load(Path(cfg["frozen_config"]).read_text())
        source = load_source(frozen["source"])
        if args.stage == "boundary":
            result["fixtures"] = fixtures()
            selection = targets(source)
            derived, refinement = refine(
                source["boundary"], selection, cfg["rules"], cfg["boundary_caps"]
            )
            derived["triangle_face_index"] = source["boundary"]["triangle_face_index"][
                derived["original_optical_parent_triangle_ids"]
            ]
            validation = validate_partition(source["boundary"], derived)
            if set(derived["triangle_face_index"]) != set(
                source["boundary"]["triangle_face_index"]
            ):
                raise ValueError("An original physical face was lost")
            path = args.output / "derived-boundary.npz"
            np.savez_compressed(path, **derived)
            result.update(
                status=(
                    "boundary_ready" if refinement["rules_completed"] else "incomplete_boundary_cap"
                ),
                source_sha256=source["source_sha256"],
                derived_boundary=str(path),
                derived_boundary_sha256=sha(path),
                targets={key: value for key, value in selection.items() if key != "masks"},
                refinement=refinement,
                partition_validation=validation,
                original_face_ids_preserved=len(np.unique(derived["triangle_face_index"])),
            )
        else:
            boundary_record = json.loads((args.boundary_cache / "result.json").read_text())
            if boundary_record["status"] != "boundary_ready":
                raise ValueError("Targeted boundary incomplete/invalid; Gmsh not allowed")
            path = Path(boundary_record["derived_boundary"])
            if (
                sha(path) != boundary_record["derived_boundary_sha256"]
                or source["source_sha256"] != boundary_record["source_sha256"]
            ):
                raise ValueError("Derived boundary/source hash mismatch")
            with np.load(path, allow_pickle=False) as archive:
                derived = {name: archive[name] for name in archive.files}
            mapping_path = Path(cfg["native_mapping"])
            if sha(mapping_path) != cfg["native_mapping_sha256"]:
                raise ValueError("Frozen source face proof changed")
            mapping = json.loads(mapping_path.read_text())
            seeds, seed_info = interior_seeds(
                source["paths"]["step"],
                derived,
                cfg["bulk_spacing_mm"],
                frozen["seeds"]["PLC_clearance_mm"],
                frozen["caps"]["max_nodes"],
            )
            print(
                f"Derived boundary {len(derived['vertices_mm'])} nodes/{len(derived['triangles'])} triangles; retained4mm seeds{len(seeds)}",
                flush=True,
            )
            raw = tetrahedralize(derived, mapping, seeds)
            raw_path = args.output / "raw-volume-before-validation.npz"
            np.savez_compressed(raw_path, **{key: value for key, value in raw.items() if isinstance(value, np.ndarray)})  # type: ignore[arg-type]
            result.update(
                raw_volume=str(raw_path),
                raw_volume_sha256=sha(raw_path),
                raw_nodes=len(raw["points_m"]),
                raw_tetrahedra=len(raw["tetrahedra"]),
            )
            arrays, checks = verify_volume_mesh(
                raw,
                derived,
                source["faces"],
                source["groups"],
                source["face_to_group"],
                frozen["caps"],
            )
            if not np.array_equal(
                arrays["points_m"][arrays["boundary_triangles"]],
                derived["vertices_mm"][derived["triangles"]] * 0.001,
            ):
                raise ValueError("Gmsh changed derived boundary coordinates")
            arrays["boundary_original_optical_parent_triangle_ids"] = derived[
                "original_optical_parent_triangle_ids"
            ]
            arrays["boundary_vertex_original_parent_barycentric"] = derived[
                "child_vertex_parent_barycentric"
            ]
            path = args.output / "mesh.npz"
            np.savez_compressed(path, **arrays)
            (args.output / "boundary-groups.json").write_text(
                json.dumps(
                    {
                        "groups": source["groups"],
                        "metadata": {
                            "old_optical_parent_map_required": True,
                            "recompute_M_B_D": True,
                            "power_conjugate_registration_required": True,
                            "source_sha256": source["source_sha256"],
                            "derived_boundary_sha256": boundary_record["derived_boundary_sha256"],
                        },
                    },
                    indent=2,
                )
                + "\n"
            )
            result.update(
                status="diagnostic_volume_mesh_valid",
                mesh_path=str(path),
                mesh_sha256=sha(path),
                seed_definition=seed_info,
                mesh_checks=checks,
            )
    except RuntimeError as exc:
        result.update(status="incomplete_resource_limit", error=repr(exc))
    except Exception as exc:  # noqa: BLE001 - keep invalid/incomplete pilot evidence
        result.update(status="invalid", error=repr(exc))
    result["elapsed_s"] = time.monotonic() - started
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    if result["status"] not in ["boundary_ready", "diagnostic_volume_mesh_valid"]:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-refined-gas-boundary.yaml")
    )
    parser.add_argument("--preset", choices=["tiny", "sim", "rl", "real"], default="tiny")
    parser.add_argument("--stage", choices=["boundary", "volume"], required=True)
    parser.add_argument("--boundary-cache", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    if args.worker:
        worker(args, cfg)
        return
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "study-config.yaml").write_text(args.config.read_text())
    paths = [
        args.config,
        Path(__file__),
        Path("src/analysis/refined_gas_boundary.py"),
        Path(cfg["frozen_config"]),
    ]
    before = {str(path): sha(path) for path in paths}
    command = [sys.executable, str(Path(__file__)), *sys.argv[1:], "--worker"]
    started = time.monotonic()
    report: dict[str, Any] = {
        "source_sha256": before,
        "stage": args.stage,
        "thermal_solve": False,
        "adoption": False,
    }
    with (args.output / "worker.log").open("w") as log:
        try:
            completed = subprocess.run(
                command,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=cfg["hard_worker_seconds"],
                check=False,
            )
            report.update(
                exit_code=completed.returncode,
                result=json.loads((args.output / "result.json").read_text()),
            )
        except subprocess.TimeoutExpired:
            report["result"] = {"status": "incomplete300s_cap", "complete_calculation": False}
    report.update(
        elapsed_s=time.monotonic() - started,
        inputs_unchanged=before == {str(path): sha(path) for path in paths},
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
    if report["result"]["status"] not in ["boundary_ready", "diagnostic_volume_mesh_valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
