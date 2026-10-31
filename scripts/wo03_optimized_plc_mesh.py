"""ONE default Gmsh volume-only optimization, immutable original optical PLC.

API: Gmsh4.15.2 optimize(method='',force=False,niter=1,dimTags=[(3,volume)]),
https://gmsh.info/doc/texinfo/ . Empty method selects default tet optimizer.
No Netgen, forceTrue, surface optimization, manual cell drop or criterion change.
Geometry validity/completion are distinct from PDE accuracy/thermal acceptance.
"""

from __future__ import annotations

import os
from pathlib import Path

for key in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
    os.environ[key] = "1"
os.environ.setdefault("XDG_CACHE_HOME", str(Path(__file__).resolve().parents[1] / ".cache"))

import argparse
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from typing import Any

import gmsh
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.wo03_cad_gas_mesh import export_mesh, fixture_source
from scripts.wo03_medium_mesh_diagnostic import fixture, save, sha, write
from src.analysis.cad_gas_mesh import (
    interior_seeds,
    load_source,
    native_face_mapping,
    tetrahedralize,
    verify_volume_mesh,
)


def snapshot(mapping: Any) -> dict[str, Any]:
    tags, coords, _ = gmsh.model.mesh.getNodes()
    kinds, elements, blocks = gmsh.model.mesh.getElements(3)
    if list(kinds) != [4]:
        raise ValueError("Optimizer trial requires linear tet4 only")
    rows, faces, entities = [], [], []
    for row in mapping["rows"]:
        types, _, surface = gmsh.model.mesh.getElements(2, row["native_entity_tag"])
        if list(types) != [2]:
            raise ValueError("Original surface changed type")
        tri = np.asarray(surface[0]).reshape(-1, 3)
        rows.extend(tri)
        faces.extend([row["original_face_id"]] * len(tri))
        entities.extend([row["native_entity_tag"]] * len(tri))
    return {
        "node_tags": np.asarray(tags),
        "points_mm": np.asarray(coords).reshape(-1, 3),
        "tet_element_tags": np.asarray(elements[0]),
        "tet_node_tags": np.asarray(blocks[0]).reshape(-1, 4),
        "surface_node_tags": np.asarray(rows),
        "surface_original_face_ids": np.asarray(faces, dtype=np.int32),
        "surface_entity_tags": np.asarray(entities, dtype=np.int32),
    }


def fixed_guard(before: Any, after: Any, boundary: Any) -> dict[str, Any]:
    count = len(boundary["vertices_mm"])

    def fixed(data: Any) -> Any:
        order = np.argsort(data["node_tags"])
        tags = data["node_tags"][order]
        take = np.searchsorted(tags, np.arange(1, count + 1))
        if not np.array_equal(tags[take], np.arange(1, count + 1)):
            raise ValueError("Original boundary node tag missing")
        return data["points_mm"][order][take]

    pre, post = fixed(before), fixed(after)

    def labelled(data: Any) -> Any:
        rows = np.column_stack(
            (
                np.sort(data["surface_node_tags"], axis=1),
                data["surface_original_face_ids"],
                data["surface_entity_tags"],
            )
        )
        return rows[np.lexsort(rows.T[::-1])]

    coordinate_bits = np.array_equal(pre.view(np.uint64), post.view(np.uint64))
    original_bits = np.array_equal(pre.view(np.uint64), boundary["vertices_mm"].view(np.uint64))
    facets = np.array_equal(labelled(before), labelled(after))
    result = {
        "original_boundary_nodes": count,
        "original_boundary_facets": len(boundary["triangles"]),
        "pre_coordinates_bitwise_equal_source": bool(original_bits),
        "post_coordinates_bitwise_equal_pre": bool(coordinate_bits),
        "all_labelled_boundary_facet_sets_unchanged": bool(facets),
        "maximum_boundary_coordinate_change_mm": float(np.abs(pre - post).max()),
        "passed": bool(original_bits and coordinate_bits and facets),
    }
    if not result["passed"]:
        raise ValueError("Immutable boundary coordinate/facet guard failed")
    return result


def optimized_mesh(
    source: Any, mapping: Any, seeds: Any, folder: Path, phase: Any
) -> tuple[Any, Any]:
    original = gmsh.model.mesh.generate
    hook = {"optimization_calls": 0}

    def generate(dim: int = 3) -> Any:
        result = original(dim)
        if dim != 3:
            raise ValueError("Unexpected generation dimension")
        phase("saving_preoptimization_raw")
        before = snapshot(mapping)
        save(folder / "pre-optimization-raw.npz", **before)
        write(
            folder / "pre-optimization-counts.json",
            {"nodes": len(before["node_tags"]), "tetrahedra": len(before["tet_node_tags"])},
        )
        volumes = gmsh.model.getEntities(3)
        if len(volumes) != 1:
            raise ValueError("Expected exactly one selected volume")
        hook["optimization_calls"] += 1
        phase("ONE_default_volume_optimizer", volume_entities=volumes)
        timer = time.monotonic()
        try:
            gmsh.model.mesh.optimize(method="", force=False, niter=1, dimTags=volumes)
        finally:
            hook["optimizer_elapsed_s"] = time.monotonic() - timer
            after = snapshot(mapping)
            save(folder / "post-optimization-raw.npz", **after)
            write(
                folder / "optimizer-call.json",
                {**hook, "method": "", "force": False, "niter": 1, "dimTags": volumes},
            )
        phase("checking_bitwise_boundary_immutability")
        hook["boundary_guard"] = fixed_guard(before, after, source["boundary"])
        write(folder / "immutable-boundary-check.json", hook["boundary_guard"])
        return result

    gmsh.model.mesh.generate = generate
    try:
        mesh = tetrahedralize(source["boundary"], mapping, seeds)
    finally:
        gmsh.model.mesh.generate = original
    save(
        folder / "returned-post-mesh-BEFORE-validation.npz",
        **{k: v for k, v in mesh.items() if isinstance(v, np.ndarray)},
    )
    return mesh, hook


def independent_fixture_checks(
    kind: str, arrays: Any, checks: Any, expected: float
) -> dict[str, Any]:
    if abs(checks["tetra_volume_mm3"] - expected) > 1e-5:
        raise ValueError("Independent fixture volume failed")
    p = arrays["points_m"][arrays["tetrahedra"]] * 1000
    if kind == "cavity" and ((p.mean(axis=1) > 2) & (p.mean(axis=1) < 18)).all(axis=1).any():
        raise ValueError("Closed cavity filled")
    sections = 0
    if kind == "thin_barrier_window":
        for station in [9.995, 10.0, 10.005]:
            candidates = p[(p[:, :, 0].min(axis=1) < station) & (p[:, :, 0].max(axis=1) > station)]
            for tet in candidates:
                for a, b in [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]:
                    if (tet[a, 0] - station) * (tet[b, 0] - station) < 0:
                        point = tet[a] + (station - tet[a, 0]) / (tet[b, 0] - tet[a, 0]) * (
                            tet[b] - tet[a]
                        )
                        sections += 1
                        if ((point[1:] < 9 - 1e-7) | (point[1:] > 11 + 1e-7)).any():
                            raise ValueError("Tet enters barrier outside actual window")
    return {
        "passed": True,
        "analytic_volume_mm3": expected,
        "tet_plane_intersection_samples_checked": sections,
        "heat_solve": False,
    }


def worker(stage: str, cfg: Any, base: Any, folder: Path) -> None:
    started = time.monotonic()

    def phase(name: str, **extra: Any) -> None:
        write(
            folder / "progress.json",
            {"phase": name, "elapsed_s": time.monotonic() - started, **extra},
        )

    result = {
        "stage": stage,
        "completion": "incomplete",
        "mesh_validity": "unavailable",
        "solution_accuracy": "unavailable_no_PDE",
        "temperature_acceptance": "unavailable_no_heat",
        "optimization_calls": 0,
    }
    try:
        phase("known_flattened_duplicate_and_coincident_diagnostic")
        write(folder / "known-tet-classifier.json", fixture())
        original_cfg = yaml.safe_load(Path(base["original_config"]).read_text())
        cases = cfg["fixtures"] if stage == "fixtures" else ["actual_medium"]
        rows = []
        for kind in cases:
            case_folder = folder / kind
            case_folder.mkdir()
            if stage == "fixtures":
                source = fixture_source(kind, case_folder / "source")
                mapping = native_face_mapping(
                    source["step"], source["faces"], source["boundary"], original_cfg["mapping"]
                )
                step = source["step"]
            else:
                phase("loading_original_frozen_actual_PLC")
                source = load_source(original_cfg["source"])
                mapping = json.loads(Path(base["mapping"]).read_text())
                step = source["paths"]["step"]
            phase("original_deterministic_3mm_seeds", case=kind)
            seeds, seed_info = interior_seeds(
                step,
                source["boundary"],
                3.0,
                original_cfg["seeds"]["PLC_clearance_mm"],
                cfg["caps"]["max_nodes"],
            )
            save(case_folder / "retained-seeds.npz", seeds_mm=seeds)
            phase("original_fixed_PLC_generation", case=kind, seed_count=len(seeds))
            mesh, hook = optimized_mesh(source, mapping, seeds, case_folder, phase)
            result["optimization_calls"] += hook["optimization_calls"]
            phase("unchanged_production_validity_checks", case=kind)
            p = mesh["points_m"][mesh["tetrahedra"]]
            determinant = np.einsum(
                "ij,ij->i", p[:, 1] - p[:, 0], np.cross(p[:, 2] - p[:, 0], p[:, 3] - p[:, 0])
            )
            save(
                case_folder / "post-raw-determinants.npz",
                signed_determinant_m3=determinant,
                zero_indices=np.flatnonzero(determinant == 0),
            )
            write(
                case_folder / "post-counts-and-zero-cells.json",
                {
                    "nodes": len(mesh["points_m"]),
                    "tetrahedra": len(mesh["tetrahedra"]),
                    "zero_count": int((determinant == 0).sum()),
                    "zero_indices": np.flatnonzero(determinant == 0).tolist(),
                },
            )
            arrays, checks = verify_volume_mesh(
                {k: v.copy() if isinstance(v, np.ndarray) else v for k, v in mesh.items()},
                source["boundary"],
                source["faces"],
                source["groups"],
                source["face_to_group"],
                original_cfg["caps"],
            )
            independent = (
                independent_fixture_checks(kind, arrays, checks, source["expected_volume_mm3"])
                if stage == "fixtures"
                else None
            )
            exported = export_mesh(
                case_folder,
                arrays,
                checks,
                source,
                mapping,
                seed_info,
                {"id": "medium_ONE_default_volume_optimization", "bulk_spacing_mm": 3.0},
            )
            rows.append(
                {"case": kind, "optimizer": hook, "independent_fixture": independent, **exported}
            )
        result.update(
            status="COMPLETE_VALIDITY_CHECKS_PASSED",
            completion="complete",
            mesh_validity="checks_passed",
            cases=rows,
        )
    except Exception as exc:  # noqa: BLE001 - retain exact mesh/optimizer errors without repair
        result.update(
            status="COMPLETE_INVALID_OR_OPTIMIZER_ERROR",
            completion="complete",
            mesh_validity="invalid_or_not_completed",
            error=repr(exc),
        )
    result["elapsed_s"] = time.monotonic() - started
    write(folder / "worker-result.json", result)
    print(
        json.dumps({k: result.get(k) for k in ["stage", "status", "error", "elapsed_s"]}),
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/studies/wo03-optimized-plc-mesh.yaml")
    parser.add_argument("--worker", choices=["fixtures", "actual"])
    parser.add_argument("--output")
    args = parser.parse_args()
    os.chdir(ROOT)
    cfg = yaml.safe_load(Path(args.config).read_text())
    for key in ["base_diagnostic", "fixture_builder", "diagnostic_helpers"]:
        if sha(Path(cfg[key])) != cfg[key + "_sha256"]:
            raise ValueError(f"Pinned source changed:{key}")
    base = yaml.safe_load(Path(cfg["base_diagnostic"]).read_text())
    for key, expected in base["expected_sha256"].items():
        if sha(Path(base[key])) != expected:
            raise ValueError(f"Original source changed:{key}")
    if sha(Path("src/analysis/cad_gas_mesh.py")) != base["shared_module_sha256"]:
        raise ValueError("Shared mesh code changed")
    folder = (
        ROOT / args.output
        if args.output
        else ROOT
        / "runs"
        / ("wo03-optimized-plc-mesh-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"))
    )
    if args.worker:
        worker(args.worker, cfg, base, folder)
        return
    folder.mkdir(parents=True)
    sources = {
        str(p): sha(p)
        for p in [
            Path(args.config),
            Path(__file__).relative_to(ROOT),
            Path(cfg["base_diagnostic"]),
            Path(cfg["fixture_builder"]),
            Path(cfg["diagnostic_helpers"]),
            Path("src/analysis/cad_gas_mesh.py"),
        ]
    }
    print(
        json.dumps(
            {
                "output": str(folder.relative_to(ROOT)),
                "actual_cap_s": cfg["caps"]["max_worker_seconds"],
            }
        ),
        flush=True,
    )
    stages = []
    for stage in ["fixtures", "actual"]:
        out = folder / stage
        out.mkdir()
        command = [
            sys.executable,
            "-u",
            str(Path(__file__)),
            "--config",
            args.config,
            "--worker",
            stage,
            "--output",
            str(out.relative_to(ROOT)),
        ]
        timer = time.monotonic()
        with (out / "worker.log").open("w") as log:
            child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            try:
                code = child.wait(timeout=cfg["caps"]["max_worker_seconds"])
                capped = False
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
                code = None
                capped = True
        result_path = out / "worker-result.json"
        result = (
            json.loads(result_path.read_text())
            if result_path.exists()
            else {
                "status": "INCOMPLETE_TIME_CAP" if capped else "INCOMPLETE_WORKER_ERROR",
                "completion": "incomplete",
                "mesh_validity": "unavailable",
            }
        )
        result.update(
            worker_exit_code=code,
            hard_cap_reached=capped,
            supervisor_elapsed_s=time.monotonic() - timer,
            output=str(out.relative_to(ROOT)),
        )
        stages.append(result)
        if result.get("status") != "COMPLETE_VALIDITY_CHECKS_PASSED":
            break
    record = {
        "stages": stages,
        "source_sha256": sources,
        "inputs_unchanged": all(sha(Path(p)) == v for p, v in sources.items()),
        "actual_attempts": sum(
            s.get("stage") == "actual" or s["output"].endswith("/actual") for s in stages
        ),
        "PDE_or_heat_solve": False,
        "accuracy_established": False,
        "temperature_acceptance": False,
        "cpu_workers": 1,
        "cost_usd": 0,
    }
    write(folder / "record.json", record)
    print(
        json.dumps(
            {
                "output": str(folder.relative_to(ROOT)),
                "stages": [
                    {k: s.get(k) for k in ["stage", "status", "error", "supervisor_elapsed_s"]}
                    for s in stages
                ],
                "inputs_unchanged": record["inputs_unchanged"],
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
