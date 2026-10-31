"""ONE old-PLC medium replay; preserve raw data before geometry validation.

The determinant/6 is signed tet volume (Zienkiewicz & Taylor, linear tetrahedron
geometry; Gmsh4.15.2 mesh API https://gmsh.info/doc/texinfo/). Exact rational
evaluation treats stored binary coordinates as exact ONLY to diagnose floating
cancellation/coplanarity; it never repairs or overrides the production validator.
Completion, mesh validity, solution accuracy and temperature acceptance are
independent fields. No heat equation, optimization or extra mesh attempt runs.
"""

from __future__ import annotations

import os
from pathlib import Path

for key in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
    os.environ[key] = "1"
os.environ.setdefault("XDG_CACHE_HOME", str(Path(__file__).resolve().parents[1] / ".cache"))

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from fractions import Fraction
from typing import Any

import cadquery as cq
import gmsh
import numpy as np
import yaml
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.analysis.cad_gas_mesh import (
    interior_seeds,
    load_source,
    tetrahedralize,
    verify_volume_mesh,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def save(path: Path, **arrays: Any) -> None:
    temporary = path.with_suffix(".tmp.npz")
    np.savez(temporary, **arrays)
    temporary.replace(path)


def signature(points: Any, node_ids: Any) -> dict[str, Any]:
    p = np.asarray(points)[node_ids]
    edges = p[1:] - p[0]
    determinant = float(edges[0] @ np.cross(edges[1], edges[2]))
    rational = [[Fraction.from_float(float(v)) for v in row] for row in p]
    a, b, c = [[row[j] - rational[0][j] for j in range(3)] for row in rational[1:]]
    exact = (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )
    unique_ids, unique_coords = len(set(map(int, node_ids))), len(np.unique(p, axis=0))
    category = (
        "repeated_node_indices"
        if unique_ids < 4
        else (
            "coincident_distinct_vertex_IDs"
            if unique_coords < 4
            else (
                "four_distinct_exact_binary_coplanar_points"
                if exact == 0
                else (
                    "float_zero_but_exact_binary_nonzero"
                    if determinant == 0
                    else "nonzero_tetrahedron"
                )
            )
        )
    )
    distances = [float(np.linalg.norm(p[i] - p[j])) for i in range(4) for j in range(i + 1, 4)]
    return {
        "category": category,
        "node_ids_zero_based": list(map(int, node_ids)),
        "unique_node_IDs": unique_ids,
        "unique_coordinate_count": unique_coords,
        "points_m": p.tolist(),
        "local_points_mm": ((p - p.mean(axis=0)) * 1000).tolist(),
        "floating_signed_determinant_m3": determinant,
        "floating_signed_volume_m3": determinant / 6,
        "exact_binary_determinant_m3_as_fraction": str(exact),
        "exact_binary_determinant_float_m3": float(exact),
        "singular_values_of_edge_matrix_mm": np.linalg.svd(edges * 1000, compute_uv=False).tolist(),
        "minimum_pair_distance_mm": min(distances) * 1000,
        "maximum_pair_distance_mm": max(distances) * 1000,
    }


def fixture() -> dict[str, Any]:
    planar = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [1.0, 1.0, 0.0]])
    coincident = planar.copy()
    coincident[3] = coincident[2]
    valid = planar.copy()
    valid[3] = [0, 0, 1]
    cases = {
        "flattened": signature(planar, [0, 1, 2, 3]),
        "repeated_ID": signature(planar, [0, 1, 2, 2]),
        "coincident": signature(coincident, [0, 1, 2, 3]),
        "valid": signature(valid, [0, 1, 2, 3]),
    }
    expected = [
        "four_distinct_exact_binary_coplanar_points",
        "repeated_node_indices",
        "coincident_distinct_vertex_IDs",
        "nonzero_tetrahedron",
    ]
    passed = [r["category"] for r in cases.values()] == expected
    if not passed:
        raise ValueError("Flattened/duplicate/coincident tet fixture failed")
    return {"passed": True, "cases": cases, "Gmsh_attempts": 0}


def detailed_cells(mesh: Any, zero: Any, source: Any, seeds: Any, cfg: Any) -> list[dict[str, Any]]:
    points, tets = mesh["points_m"], mesh["tetrahedra"]
    boundary = source["boundary"]
    seed_tree = cKDTree(seeds)
    manifest = json.loads(Path(cfg["manifest"]).read_text())
    included = {row["part_id"] for row in source["faces"] if not row["reservoir"]}
    solids = {}
    for row in manifest:
        if row["part_id"] in included:
            path = Path(cfg["manifest"]).parent / row["step"]
            if sha(path) != row["step_sha256"]:
                raise ValueError("Actual source part STEP changed")
            solids[row["part_id"]] = cq.importers.importStep(str(path)).val()
    result = []
    for tet_id in zero[: cfg["caps"]["detailed_zero_cells"]]:
        ids = tets[tet_id]
        detail = signature(points, ids)
        detail["tet_index_zero_based"] = int(tet_id)
        nodes = []
        for node in ids:
            p = points[node] * 1000
            original = (
                int(node)
                if int(node) < len(boundary["vertices_mm"])
                and np.allclose(p, boundary["vertices_mm"][node], rtol=0, atol=1e-10)
                else None
            )
            incident = (
                np.flatnonzero(np.any(boundary["triangles"] == original, axis=1))
                if original is not None
                else np.array([], dtype=int)
            )
            face_ids = sorted(set(map(int, boundary["triangle_face_index"][incident] + 1)))
            distance, seed = seed_tree.query(p)
            distances = {
                name: float(shape.distance(cq.Vertex.makeVertex(*p)))
                for name, shape in solids.items()
            }
            nearest = sorted(distances.items(), key=lambda item: item[1])[:5]
            nodes.append(
                {
                    "node_index_zero_based": int(node),
                    "original_boundary_vertex_index": original,
                    "origin": (
                        "original_optical_boundary"
                        if original is not None
                        else (
                            "retained_embedded_seed"
                            if distance <= 1e-10
                            else "Gmsh_created_interior_node"
                        )
                    ),
                    "nearest_retained_seed_index": int(seed),
                    "nearest_seed_distance_mm": float(distance),
                    "original_source_facet_indices": incident.tolist(),
                    "CAD_face_ids": face_ids,
                    "radiation_group_ids": sorted(
                        {int(source["face_to_group"][i - 1]) for i in face_ids}
                    ),
                    "face_ancestry": [source["faces"][i - 1] for i in face_ids],
                    "nearest_actual_solid_clearances_mm": nearest,
                    "node_has_no_invented_single_material_owner": True,
                }
            )
        centroid = points[ids].mean(axis=0) * 1000
        detail["centroid_CAD_mm"] = centroid.tolist()
        detail["centroid_nearest_actual_solid_clearances_mm"] = sorted(
            (
                (name, float(shape.distance(cq.Vertex.makeVertex(*centroid))))
                for name, shape in solids.items()
            ),
            key=lambda item: item[1],
        )[:5]
        detail["nodes"] = nodes
        result.append(detail)
    return result


def worker(cfg: Any, output: Path) -> None:
    started = time.monotonic()

    def phase(name: str, **data: Any) -> None:
        write(
            output / "progress.json",
            {"phase": name, "elapsed_s": time.monotonic() - started, **data},
        )

    known = fixture()
    write(output / "known-flattened-tet.json", known)
    source_cfg = yaml.safe_load(Path(cfg["original_config"]).read_text())
    phase("loading_frozen_source_and_verified_mapping")
    source = load_source(source_cfg["source"])
    mapping_record = json.loads(Path(cfg["mapping_record"]).read_text())
    if mapping_record["source_sha256"] != source["source_sha256"]:
        raise ValueError("Native mapping geometry identity mismatch")
    mapping = json.loads(Path(cfg["mapping"]).read_text())
    phase("generating_original_3mm_lattice_and_4percent_jitter")
    seeds, seed_info = interior_seeds(
        source["paths"]["step"],
        source["boundary"],
        3.0,
        source_cfg["seeds"]["PLC_clearance_mm"],
        cfg["caps"]["max_nodes"],
    )
    save(output / "retained-seeds.npz", seeds_mm=seeds)
    write(output / "seed-info.json", seed_info)
    phase("meshing_unchanged_fixed_optical_PLC", seed_count=len(seeds))
    original_nodes, original_elements = gmsh.model.mesh.getNodes, gmsh.model.mesh.getElements

    def capture_nodes(*args: Any, **kwargs: Any) -> Any:
        values = original_nodes(*args, **kwargs)
        save(
            output / "Gmsh-raw-nodes.npz",
            node_tags=values[0],
            coordinates_mm=values[1],
            parametric_coordinates=values[2],
        )
        phase("raw_node_readback_saved_BEFORE_validation", nodes=len(values[0]))
        return values

    def capture_elements(*args: Any, **kwargs: Any) -> Any:
        values = original_elements(*args, **kwargs)
        if args and args[0] == 3:
            arrays = {"element_types": values[0]}
            for i, (tags, nodes) in enumerate(zip(values[1], values[2], strict=True)):
                arrays[f"element_tags_block_{i}"] = tags
                arrays[f"node_tags_block_{i}"] = nodes
            save(output / "Gmsh-raw-volume-elements.npz", **arrays)
            phase(
                "raw_volume_readback_saved_BEFORE_validation",
                element_count=sum(len(t) for t in values[1]),
            )
        return values

    gmsh.model.mesh.getNodes = capture_nodes
    gmsh.model.mesh.getElements = capture_elements
    try:
        mesh = tetrahedralize(source["boundary"], mapping, seeds)
    finally:
        gmsh.model.mesh.getNodes = original_nodes
        gmsh.model.mesh.getElements = original_elements
    save(
        output / "raw-mesh-BEFORE-validation.npz",
        **{k: v for k, v in mesh.items() if isinstance(v, np.ndarray)},
    )
    write(
        output / "raw-mesh-settings.json",
        {k: v for k, v in mesh.items() if not isinstance(v, np.ndarray)},
    )
    phase(
        "raw_mesh_saved_BEFORE_validation",
        nodes=len(mesh["points_m"]),
        tetrahedra=len(mesh["tetrahedra"]),
    )
    p = mesh["points_m"][mesh["tetrahedra"]]
    determinant = np.einsum(
        "ij,ij->i", p[:, 1] - p[:, 0], np.cross(p[:, 2] - p[:, 0], p[:, 3] - p[:, 0])
    )
    zero = np.flatnonzero(determinant == 0)
    save(
        output / "all-raw-determinants.npz",
        signed_determinant_m3=determinant,
        zero_tet_indices=zero,
    )
    validation_error = None
    try:
        _, checks = verify_volume_mesh(
            {k: v.copy() if isinstance(v, np.ndarray) else v for k, v in mesh.items()},
            source["boundary"],
            source["faces"],
            source["groups"],
            source["face_to_group"],
            source_cfg["caps"],
        )
    except (ValueError, RuntimeError) as exc:
        validation_error = repr(exc)
        checks = None
    phase(
        "classifying_invalid_cells_without_repair",
        zero_count=len(zero),
        validation_error=validation_error,
    )
    classes = [
        {"tet_index_zero_based": int(i), **signature(mesh["points_m"], mesh["tetrahedra"][i])}
        for i in zero
    ]
    write(output / "all-zero-cell-classification.json", classes)
    details = detailed_cells(mesh, zero, source, seeds, cfg) if len(zero) else []
    write(output / "detailed-zero-cells.json", details)
    counts = {
        "boundary_nodes": mesh["source_boundary_nodes"],
        "seeds": len(seeds),
        "nodes": len(mesh["points_m"]),
        "tetrahedra": len(mesh["tetrahedra"]),
    }
    result = {
        "status": (
            "COMPLETE_INVALID_MEDIUM_DIAGNOSTIC"
            if validation_error
            else "COMPLETE_REPLAY_VALIDITY_CHECKS_PASSED_ORIGINAL_FAILURE_UNREPRODUCED"
        ),
        "completion": "completed",
        "mesh_validity": "invalid" if validation_error else "checks_passed",
        "solution_accuracy": "unavailable_no_heat_solve",
        "temperature_acceptance": "unavailable_no_temperature_solve",
        "counts": counts,
        "original_log_counts": cfg["expected_original_counts"],
        "counts_match_original": counts == cfg["expected_original_counts"],
        "zero_count": len(zero),
        "zero_indices": zero.tolist(),
        "validation_error": validation_error,
        "validity_checks": checks,
        "exact_original_raw_mesh_identity": "unavailable_original_arrays_lost; matching counts/error alone cannot establish identical cells",
        "current_shared_source_hash_differs_from_historical": True,
        "known_fixture_passed": known["passed"],
        "raw_saved_BEFORE_validation": True,
        "detailed_cell_count": len(details),
        "complete_detailed_coverage": len(details) == len(zero),
        "source_sha256": source["source_sha256"],
        "seeds": seed_info,
        "repairs_performed": False,
        "heat_calculation": False,
        "elapsed_s": time.monotonic() - started,
        "cpu_workers": 1,
        "cost_usd": 0,
    }
    write(output / "worker-result.json", result)
    phase("complete", **counts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/studies/wo03-medium-mesh-diagnostic.yaml")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    os.chdir(ROOT)
    cfg = yaml.safe_load(Path(args.config).read_text())
    for key, expected in cfg["expected_sha256"].items():
        if sha(Path(cfg[key])) != expected:
            raise ValueError(f"Pinned input changed:{key}")
    module = Path("src/analysis/cad_gas_mesh.py")
    if sha(module) != cfg["shared_module_sha256"]:
        raise ValueError("Shared gas mesh module changed before bounded replay")
    output = (
        ROOT / args.output
        if args.output
        else ROOT
        / "runs"
        / ("wo03-medium-mesh-diagnostic-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"))
    )
    if args.worker:
        worker(cfg, output)
        return
    output.mkdir(parents=True)
    before = {
        str(p): sha(p)
        for p in [
            Path(args.config),
            Path(__file__).relative_to(ROOT),
            module,
            *[Path(cfg[k]) for k in cfg["expected_sha256"]],
        ]
    }
    known = fixture()
    write(output / "known-flattened-tet-supervisor.json", known)
    command = [
        sys.executable,
        "-u",
        str(Path(__file__)),
        "--config",
        args.config,
        "--worker",
        "--output",
        str(output.relative_to(ROOT)),
    ]
    print(
        json.dumps(
            {"output": str(output.relative_to(ROOT)), "cap_seconds": cfg["caps"]["seconds"]}
        ),
        flush=True,
    )
    started = time.monotonic()
    capped = False
    with (output / "worker.log").open("w") as log:
        child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
        try:
            code = child.wait(timeout=cfg["caps"]["seconds"])
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
            code = None
            capped = True
    worker_path = output / "worker-result.json"
    result = (
        json.loads(worker_path.read_text())
        if worker_path.exists()
        else {
            "status": "INCOMPLETE_TIME_CAP" if capped else "INCOMPLETE_WORKER_ERROR",
            "completion": "incomplete",
            "mesh_validity": "unavailable",
            "solution_accuracy": "unavailable",
            "temperature_acceptance": "unavailable",
        }
    )
    result.update(
        worker_exit_code=code,
        hard_time_cap_reached=capped,
        supervisor_elapsed_s=time.monotonic() - started,
        input_sha256=before,
        inputs_unchanged=all(sha(Path(p)) == v for p, v in before.items()),
        available_artifacts={p.name: sha(p) for p in output.iterdir() if p.is_file()},
        last_progress=(
            json.loads((output / "progress.json").read_text())
            if (output / "progress.json").exists()
            else None
        ),
        actual_mesh_attempts=1,
        old_fine_300s_result="incomplete_not_demonstrated_numerical_failure",
        engineering_acceptance=False,
    )
    write(output / "record.json", result)
    print(
        json.dumps(
            {
                "output": str(output.relative_to(ROOT)),
                **{
                    k: result.get(k)
                    for k in [
                        "status",
                        "counts",
                        "zero_count",
                        "counts_match_original",
                        "inputs_unchanged",
                        "supervisor_elapsed_s",
                    ]
                },
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
