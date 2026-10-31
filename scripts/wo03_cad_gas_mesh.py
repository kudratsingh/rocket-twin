"""Bounded actual gas PLC mesh and complete facet ownership; no conduction solve."""

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
import cadquery as cq
import numpy as np
import yaml

from src.analysis.cad_gas_mesh import (
    interior_seeds,
    load_source,
    native_face_mapping,
    sha,
    source_facet_correspondence,
    tetrahedralize,
    validate_boundary,
    verify_volume_mesh,
)
from src.analysis.cad_radiation import interior_sample, triangulate_fluid


def fixture_source(kind: str, folder: Path) -> dict[str, Any]:
    """Independent geometry only; the real source is never re-Booleaned."""
    if kind == "split_wall":
        fluid = cq.Solid.makeBox(10, 10, 5).fuse(cq.Solid.makeBox(10, 10, 5, cq.Vector(0, 0, 5)))
        expected_volume = 1000.0
    elif kind == "cavity":
        fluid = cq.Solid.makeBox(20, 20, 20).cut(cq.Solid.makeBox(16, 16, 16, cq.Vector(2, 2, 2)))
        expected_volume = 3904.0
    else:
        slab = cq.Solid.makeBox(0.02, 20, 20, cq.Vector(9.99, 0, 0)).cut(
            cq.Solid.makeBox(0.04, 2, 2, cq.Vector(9.98, 9, 9))
        )
        fluid = cq.Solid.makeBox(20, 20, 20).cut(slab)
        expected_volume = 8000 - 0.02 * (400 - 4)
    faces = []
    for i, face in enumerate(fluid.Faces()):
        point, normal = interior_sample(face)
        if kind == "split_wall":
            group = (0 if point[2] < 5 else 1) if abs(point[0]) < 1e-6 else 2
        elif kind == "cavity":
            group = 1 if ((point >= 2 - 1e-6) & (point <= 18 + 1e-6)).all() else 0
        else:
            group = 1 if 9.98 < point[0] < 10.02 else 0
        faces.append(
            {
                "fluid_face_id": i + 1,
                "part_id": f"fixture_group_{group}",
                "cad_area_mm2": face.Area(),
                "ownership_interior_point_mm": point.tolist(),
                "void_outward_normal": normal.tolist(),
                "source_face_history": [{"fixture_source_face": i + 1}],
                "group_id": group,
            }
        )
    group_ids = sorted({face["group_id"] for face in faces})
    groups = [
        {
            "group_id": i,
            "part_id": f"fixture_group_{i}",
            "fluid_face_ids": [face["fluid_face_id"] for face in faces if face["group_id"] == i],
            "reservoir": False,
        }
        for i in group_ids
    ]
    face_to_group = np.array([row["group_id"] for row in faces], dtype=np.int32)
    boundary = triangulate_fluid(fluid, faces, 0.002, 0.1, 1e-7, 150000, 1e-4)
    folder.mkdir(parents=True, exist_ok=False)
    step = folder / "fixture.step"
    cq.exporters.export(fluid, str(step))
    return {
        "faces": faces,
        "groups": groups,
        "face_to_group": face_to_group,
        "boundary": boundary,
        "step": step,
        "expected_volume_mm3": expected_volume,
    }


def export_mesh(
    folder: Path,
    arrays: dict[str, Any],
    diagnostics: dict[str, Any],
    source: dict[str, Any],
    mapping: dict[str, Any],
    seed_info: dict[str, Any],
    level: dict[str, Any],
) -> dict[str, Any]:
    npz = folder / "mesh.npz"
    np.savez_compressed(npz, **arrays)
    correspondence = source_facet_correspondence(arrays, source["boundary"])
    correspondence_path = folder / "boundary-source-correspondence.npz"
    np.savez_compressed(correspondence_path, **correspondence)  # type: ignore[arg-type]
    metadata = {
        "schema": "labelled-gas-tet4-robin-v1",
        "groups": source["groups"],
        "metadata": {
            "units": "SI points_m, m2 boundary areas",
            "indices": "zero-based connectivity and original integer radiation groups; original CAD face IDs one-based",
            "shared_boundary_nodes_retained": True,
            "node_temperature_or_material_ownership_assigned": False,
            "all_exterior_faces_explicitly_labelled": True,
            "unlisted_exterior_faces": "error",
            "source_sha256": source.get("source_sha256", {}),
            "native_face_mapping": mapping["rows"],
            "seed_definition": seed_info,
            "volume_level": level,
            "boundary_refinement_is_separate": True,
            "diagnostics": diagnostics,
            "gas_conduction_solved": False,
            "material_halfwall_mapping_owned_by_primary": True,
        },
    }
    group_path = folder / "boundary-groups.json"
    group_path.write_text(json.dumps(metadata, indent=2) + "\n")
    return {
        "mesh_path": str(npz),
        "mesh_sha256": sha(npz),
        "groups_path": str(group_path),
        "groups_sha256": sha(group_path),
        "correspondence_path": str(correspondence_path),
        "correspondence_sha256": sha(correspondence_path),
        "diagnostics": diagnostics,
        "seed_definition": seed_info,
    }


def run_fixtures(cfg: dict[str, Any], output: Path) -> dict[str, Any]:
    rows = []
    for kind in ["split_wall", "cavity", "thin_barrier_window"]:
        source = fixture_source(kind, output / kind)
        mapping = native_face_mapping(
            source["step"], source["faces"], source["boundary"], cfg["mapping"]
        )
        levels = []
        for level in cfg["levels"]:
            folder = output / kind / level["id"]
            folder.mkdir()
            seeds, seed_info = interior_seeds(
                source["step"],
                source["boundary"],
                level["bulk_spacing_mm"],
                cfg["seeds"]["PLC_clearance_mm"],
                cfg["caps"]["max_nodes"],
            )
            mesh = tetrahedralize(source["boundary"], mapping, seeds)
            arrays, checks = verify_volume_mesh(
                mesh,
                source["boundary"],
                source["faces"],
                source["groups"],
                source["face_to_group"],
                cfg["caps"],
            )
            if abs(checks["tetra_volume_mm3"] - source["expected_volume_mm3"]) > 1e-5:
                raise ValueError("Independent fixture volume failed")
            if kind == "split_wall":
                shared = set(
                    arrays["boundary_triangles"][arrays["boundary_group_ids"] == 0].ravel()
                ) & set(arrays["boundary_triangles"][arrays["boundary_group_ids"] == 1].ravel())
                if not shared:
                    raise ValueError("Split-wall common edge nodes were duplicated or lost")
                checks["different_wall_group_shared_nodes"] = len(shared)
            if kind == "cavity":
                center = arrays["points_m"][arrays["tetrahedra"]].mean(axis=1) * 1000
                if ((center > 2) & (center < 18)).all(axis=1).any():
                    raise ValueError("Cavity was filled with gas tetrahedra")
            levels.append(export_mesh(folder, arrays, checks, source, mapping, seed_info, level))
        rows.append(
            {
                "fixture": kind,
                "expected_volume_mm3": source["expected_volume_mm3"],
                "original_CAD_face_count": len(source["faces"]),
                "levels": levels,
                "passed": True,
            }
        )
    return {"passed": True, "cases": rows, "solve_executed": False}


def worker(args: Any, cfg: dict[str, Any]) -> None:
    started = time.monotonic()
    result: dict[str, Any] = {"worker": args.worker, "status": "failed", "conduction_solved": False}
    mesh: dict[str, Any] | None = None
    try:
        if args.worker == "fixtures":
            result.update(run_fixtures(cfg, args.output), status="passed")
        else:
            source = load_source(cfg["source"])
            if args.worker == "mapping":
                mapping = native_face_mapping(
                    source["paths"]["step"], source["faces"], source["boundary"], cfg["mapping"]
                )
                expected = source["handoff"]["actual_CAD_fluid_volume_mm3"]
                if (
                    abs(mapping["native_volume_mm3"] / expected - 1)
                    > cfg["mapping"]["relative_CAD_volume_tolerance"]
                ):
                    raise ValueError("Native Gmsh STEP units/volume disagree with actual source")
                (args.output / "native-face-mapping.json").write_text(
                    json.dumps(mapping, indent=2) + "\n"
                )
                result.update(
                    status="passed",
                    mapping_path=str(args.output / "native-face-mapping.json"),
                    mapping_sha256=sha(args.output / "native-face-mapping.json"),
                    source_sha256=source["source_sha256"],
                    boundary=validate_boundary(source["boundary"], len(source["faces"])),
                    native_volume_mm3=mapping["native_volume_mm3"],
                )
            else:
                mapping_path = args.mapping_cache / "native-face-mapping.json"
                mapping_record = json.loads(
                    (args.mapping_cache / "mapping-result.json").read_text()
                )
                if (
                    mapping_record["status"] != "passed"
                    or sha(mapping_path) != mapping_record["mapping_sha256"]
                ):
                    raise ValueError("Native face mapping cache is not verified")
                if mapping_record["source_sha256"] != source["source_sha256"]:
                    raise ValueError("Native face mapping physical source changed")
                mapping = json.loads(mapping_path.read_text())
                level = next(row for row in cfg["levels"] if row["id"] == args.worker)
                seeds, seed_info = interior_seeds(
                    source["paths"]["step"],
                    source["boundary"],
                    level["bulk_spacing_mm"],
                    cfg["seeds"]["PLC_clearance_mm"],
                    cfg["caps"]["max_nodes"],
                )
                print(
                    f"Actual fixed boundary {len(source['boundary']['vertices_mm'])} nodes; actual-fluid seeds {len(seeds)}",
                    flush=True,
                )
                mesh = tetrahedralize(source["boundary"], mapping, seeds)
                arrays, diagnostics = verify_volume_mesh(
                    mesh,
                    source["boundary"],
                    source["faces"],
                    source["groups"],
                    source["face_to_group"],
                    cfg["caps"],
                )
                result.update(
                    export_mesh(
                        args.output, arrays, diagnostics, source, mapping, seed_info, level
                    ),
                    status="passed",
                    candidate_identity=source["handoff"]["candidate_identity"],
                )
    except Exception as exc:  # noqa: BLE001 - preserve every geometry/resource failure
        result["error"] = repr(exc)
        if mesh is not None:
            raw_path = args.output / "failed-raw-mesh.npz"
            np.savez_compressed(
                raw_path,
                **{key: value for key, value in mesh.items() if isinstance(value, np.ndarray)},  # type: ignore[arg-type]
            )
            result["failed_raw_mesh_path"] = str(raw_path)
            result["failed_raw_mesh_sha256"] = sha(raw_path)
            result["failed_mesh_counts"] = {
                "nodes": len(mesh["points_m"]),
                "tetrahedra": len(mesh["tetrahedra"]),
                "Gmsh_boundary_triangles": len(mesh["gmsh_boundary_triangles"]),
            }
        print(result["error"], flush=True)
    result["elapsed_s"] = time.monotonic() - started
    (args.output / (args.worker + "-result.json")).write_text(json.dumps(result, indent=2) + "\n")
    if result["status"] != "passed":
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-cad-gas-mesh.yaml")
    )
    parser.add_argument("--preset", choices=["tiny", "sim", "rl", "real"], default="tiny")
    parser.add_argument("--stage", choices=["fixtures", "mapping", "all", "meshes"], default="all")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mapping-cache", type=Path)
    parser.add_argument("--level", choices=["coarse", "medium", "fine"], action="append")
    parser.add_argument("--worker", choices=["fixtures", "mapping", "coarse", "medium", "fine"])
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
        Path("src/analysis/cad_gas_mesh.py"),
        Path("src/analysis/cad_radiation.py"),
    ]
    before = {str(path): sha(path) for path in paths}
    report: dict[str, Any] = {
        "study_id": cfg["id"],
        "source_sha256": before,
        "stages": [],
        "cpu_workers": 1,
        "conduction_solved": False,
        "engineering_acceptance_passed": False,
        "cost_usd": 0,
    }
    started = time.monotonic()
    work = (
        ["fixtures"]
        if args.stage == "fixtures"
        else (
            ["mapping"]
            if args.stage == "mapping"
            else (
                [row["id"] for row in cfg["levels"]]
                if args.stage == "meshes"
                else ["fixtures", "mapping", *[row["id"] for row in cfg["levels"]]]
            )
        )
    )
    if args.level:
        work = [name for name in work if name in ["fixtures", "mapping"] or name in args.level]
    report["selected_workers"] = work
    cache = args.mapping_cache or args.output / "mapping"
    for name in work:
        folder = args.output / name
        folder.mkdir()
        command = [
            sys.executable,
            str(Path(__file__)),
            "--config",
            str(args.config),
            "--output",
            str(folder),
            "--worker",
            name,
            "--mapping-cache",
            str(cache),
        ]
        entry: dict[str, Any] = {"worker": name, "output": str(folder)}
        print(f"Starting bounded {name} worker", flush=True)
        with (folder / "worker.log").open("w") as log:
            try:
                process = subprocess.run(
                    command,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=cfg["caps"]["max_worker_seconds"],
                    check=False,
                )
                entry["exit_code"] = process.returncode
                result_path = folder / (name + "-result.json")
                if result_path.exists():
                    entry["result"] = json.loads(result_path.read_text())
                    entry["result_sha256"] = sha(result_path)
                entry["status"] = "passed" if process.returncode == 0 else "failed"
            except subprocess.TimeoutExpired:
                entry.update(
                    status="failed",
                    error="Hard worker time cap; child killed; no solve or accepted mesh",
                )
        report["stages"].append(entry)
        report["elapsed_s"] = time.monotonic() - started
        report["inputs_unchanged"] = before == {str(path): sha(path) for path in paths}
        report["status"] = "passed" if entry["status"] == "passed" else "failed"
        (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"{name}: {entry['status']}", flush=True)
        if entry["status"] != "passed":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
