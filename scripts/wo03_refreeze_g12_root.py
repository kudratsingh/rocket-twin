"""Refreeze a historical G12 layered-fin source copy; never claim qualification.

Validates an existing reconciled copy and rebuilds the assembly with the
original fin and frame STEPs and the current native geometry pipeline. A fresh child is killed after the declared wall cap; source artifacts are
read-only. Current generator output for other parts is compared to historical
mass properties, which is not by itself proof of geometric identity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
for variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[variable] = "1"
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def bounds(shape: Any) -> list[float]:
    b = shape.BoundingBox()
    return [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]


def difference(a: Any, b: Any) -> float | None:
    if a is None or b is None:
        return None
    if isinstance(a, list):
        vals = [difference(x, y) for x, y in zip(a, b, strict=True)]
        return max((v for v in vals if v is not None), default=0.0)
    return abs(float(a) - float(b))


def worker(cfg: dict[str, Any], out: Path, input_hashes: dict[str, str]) -> None:
    import cadquery as cq

    sys.path.insert(0, str(ROOT))
    from src.cad.parts import local_shape, properties
    from src.vehicle.schema import Vehicle

    start, cpu = time.monotonic(), time.process_time()
    previous_bytes = (ROOT / cfg["old_reconciled"]).read_bytes()
    previous = json.loads(previous_bytes)
    original = yaml.safe_load((ROOT / cfg["source_hoop"]).read_text())
    audit = json.loads((ROOT / cfg["old_audit"]).read_text())
    vehicle = Vehicle.model_validate(previous)
    normalized = json.loads(vehicle.model_dump_json(by_alias=True))
    if normalized != previous:
        raise ValueError("Historical valid copy changes on schema round trip")
    spec_sha = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    if spec_sha != "4ff75b8f2c6ab47ddf90b546761d7fa6d4a72c3af9f382e6b3790cbeb19c1287":
        raise ValueError("Historical reconciled canonical identity changed")
    prior = {p["id"]: p for p in previous["parts"]}
    old = {p["id"]: p for p in original["parts"]}
    if set(prior) != set(old):
        raise ValueError("Part identity set changed")
    ignored = {"cad_mass", "mass_kg", "cg_offset_m"}
    changes = []
    for ident, source_part in old.items():
        for key in set(source_part) | set(prior[ident]):
            if key not in ignored and source_part.get(key) != prior[ident].get(key):
                changes.append({"part": ident, "field": key})
    if changes:
        raise ValueError(f"Unexpected proposal input changes: {changes[:5]}")
    fin_file, frame_file = ROOT / cfg["fin_step"], ROOT / cfg["frame_step"]
    fin = cq.importers.importStep(str(fin_file)).val()
    frame = cq.importers.importStep(str(frame_file)).val()
    j = yaml.safe_load((ROOT / cfg["recovery_config"]).read_text())["junction"]
    # Simple historical ring/edge fillet; preserve the input configuration.
    junction = (
        cq.Workplane("XY")
        .circle(j["outer_radius_mm"])
        .circle(j["inner_radius_mm"])
        .extrude(j["thickness_mm"])
        .edges()
        .fillet(j["edge_radius_mm"])
        .val()
    )
    solids, rows = {}, []
    (out / "stage.txt").write_text(
        "regenerating 75 ordinary shapes; preserving original fin and frame STEPs\n"
    )
    for part in vehicle.parts:
        if part.id == "fin_set":
            shape = fin
        elif part.id == "gimbal_frame":
            shape = frame
        elif part.id == "recovery_junction":
            shape = junction
        else:
            shape = local_shape(part)
        if not shape.isValid() or shape.Volume() <= 0:
            raise ValueError(f"Invalid or empty part shape: {part.id}")
        actual = properties(part, shape)
        cached = prior[part.id]["cad_mass"]
        if cached is None:
            raise ValueError(f"Missing historical CAD property cache: {part.id}")
        weighted_fin = part.id == "fin_set"
        placed = shape.translate(
            (
                part.lateral_offset_m[0] * 1000,
                -part.lateral_offset_m[1] * 1000,
                part.position_m * 1000,
            )
        )
        solids[part.id] = placed
        rows.append(
            {
                "id": part.id,
                "historical_volume_m3": cached["volume_m3"],
                "new_geometric_volume_m3": actual["volume_m3"],
                "volume_difference_m3": difference(cached["volume_m3"], actual["volume_m3"]),
                "historical_centroid_body_m": cached["cg_local_body_m"],
                "new_geometric_centroid_body_m": actual["cg_local_body_m"],
                "centroid_max_abs_difference_m": (
                    None
                    if weighted_fin
                    else difference(cached["cg_local_body_m"], actual["cg_local_body_m"])
                ),
                "historical_inertia_per_kg_m2": cached["inertia_per_kg_m2"],
                "new_geometric_inertia_per_kg_m2": actual["inertia_per_kg_m2"],
                "inertia_max_abs_difference_m2": (
                    None
                    if weighted_fin
                    else difference(cached["inertia_per_kg_m2"], actual["inertia_per_kg_m2"])
                ),
                "historical_mass_kg": old[part.id]["mass_kg"],
                "new_mass_kg": part.resolved_mass_kg,
                "new_local_bbox_mm": bounds(shape),
                "new_placed_bbox_mm": bounds(placed),
                "historical_bbox_mm": (
                    bounds(shape) if part.id in ("fin_set", "gimbal_frame") else None
                ),
                "old_vs_new_shape_equivalence": (
                    "original_STEP_preserved"
                    if part.id in ("fin_set", "gimbal_frame")
                    else "unproved_no_individual_old_STEP"
                ),
                "fin_centroid_inertia_basis": (
                    "historical density-weighted composite; current geometric values are uniform-volume, not comparable"
                    if weighted_fin
                    else None
                ),
            }
        )
    fresh = out / "resolved-candidate.json"
    fresh.write_bytes(previous_bytes)
    if sha(fresh) != sha(ROOT / cfg["old_reconciled"]):
        raise ValueError("Historical validated file copy changed")
    (out / "stage.txt").write_text("exporting actual assembled STEP\n")
    assembly = out / "assembly.step"
    cq.exporters.export(cq.Compound.makeCompound(list(solids.values())), str(assembly))
    # Keep original sources as standalone exact-byte inspectable exports.
    (out / "fin-layers.step").write_bytes(fin_file.read_bytes())
    (out / "recovery-cap-frame.step").write_bytes(frame_file.read_bytes())
    fin_part = next(p for p in vehicle.parts if p.id == "fin_set")
    frame_part = next(p for p in vehicle.parts if p.id == "gimbal_frame")
    shell = next(p for p in vehicle.parts if p.id == "aft_shell")
    result = {
        "status": "validated_existing_reconciled_copy_assembly_unqualified",
        "accepted": False,
        "flight_ready": False,
        "input_sha256_before": input_hashes,
        "input_sha256_after": {p: sha(ROOT / p) for p in input_hashes},
        "new_resolved_file_sha256": sha(fresh),
        "new_resolved_spec_sha256": spec_sha,
        "historical_reconciled_spec_sha256": audit["source_identity"][
            "historical_reconciled_actual_identity"
        ],
        "reload_valid": True,
        "proposal_non_mass_property_changes": changes,
        "historical_hoop_mass_kg": sum(float(p["mass_kg"]) for p in original["parts"]),
        "reconciled_mass_kg": sum(p.resolved_mass_kg for p in vehicle.parts),
        "mass_saving_credited": False,
        "parts": rows,
        "assembly_step_sha256": sha(assembly),
        "original_steps_byte_identical": sha(out / "fin-layers.step") == sha(fin_file)
        and sha(out / "recovery-cap-frame.step") == sha(frame_file),
        "fin_and_frame_original_STEP_geometry": {
            "fin_local_bbox_mm": bounds(fin),
            "frame_local_bbox_mm": bounds(frame),
            "fin_global_bbox_mm": bounds(solids["fin_set"]),
            "frame_global_bbox_mm": bounds(solids["gimbal_frame"]),
            "fin_station_m": fin_part.position_m,
            "frame_station_m": frame_part.position_m,
            "fin_dimensions": fin_part.geometry,
            "frame_dimensions": frame_part.geometry,
            "fin_parameters": fin_part.cad.parameters,
            "frame_parameters": frame_part.cad.parameters,
            "shell_station_m": shell.position_m,
            "shell_parameters": shell.cad.parameters,
        },
        "geometry_equivalence_all_parts": None,
        "geometry_comparison_limit": "Old per-part STEP unavailable except fin and frame; identical volume/centroid/inertia is not proof of same shape.",
        "reconstruction_limit": "Generic export_vehicle regenerates a homogeneous fin and omits frame post-Boolean rounded saddles; use explicit source STEP substitution and output assembly.",
        "motion_history": "Flat servo horns/fixed-shaft and prior conflict evidence remain open; no inherited motion or strength pass.",
        "old_contact_or_strength_transferred": False,
        "elapsed_wall_s": time.monotonic() - start,
        "process_cpu_s": time.process_time() - cpu,
        "max_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    result["source_identity_unchanged"] = (
        result["input_sha256_before"] == result["input_sha256_after"]
    )
    if not result["source_identity_unchanged"]:
        raise ValueError("Source changed during run")
    write(out / "record.json", result)
    (out / "stage.txt").write_text("completed\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/studies/wo03-refreeze-g12-root.yaml"
    )
    parser.add_argument("--preset", choices=["tiny"], default="tiny")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    out = args.output or ROOT / cfg["output"]
    paths = [args.config, Path(__file__)] + [
        ROOT / cfg[k]
        for k in (
            "installed_root_config",
            "old_audit",
            "old_reconciled",
            "source_hoop",
            "recovery_config",
            "fin_step",
            "frame_step",
        )
    ]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    audit = json.loads((ROOT / cfg["old_audit"]).read_text())
    for key, expected in [
        ("source_hoop", audit["source_identity"]["hoop_resolved_copy_sha256"]),
        ("fin_step", audit["source_identity"]["layered_fin_step_sha256"]),
        ("frame_step", audit["source_identity"]["actual_frame_step_sha256"]),
    ]:
        if sha(ROOT / cfg[key]) != expected:
            raise ValueError(f"Historical pin mismatch: {key}")
    if args.worker:
        resource.setrlimit(
            resource.RLIMIT_CPU, (cfg["budget"]["cpu_seconds"], cfg["budget"]["cpu_seconds"])
        )
        worker(cfg, out, hashes)
        return
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    try:
        p = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--worker",
                "--config",
                str(args.config),
                "--output",
                str(out),
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=cfg["budget"]["wall_seconds"],
            check=False,
        )
        (out / "worker.log").write_text(p.stdout)
        status = {
            "exit_code": p.returncode,
            "wall_seconds": time.monotonic() - start,
            "timeout": False,
            "completed": p.returncode == 0 and (out / "record.json").exists(),
        }
    except subprocess.TimeoutExpired as e:
        (out / "worker.log").write_bytes(e.stdout or b"")
        status = {
            "exit_code": None,
            "wall_seconds": time.monotonic() - start,
            "timeout": True,
            "completed": False,
        }
    write(out / "completion.json", status)
    if not status["completed"]:
        raise SystemExit("Rebuild stopped; retain partial evidence and do not retry without replan")


if __name__ == "__main__":
    main()
