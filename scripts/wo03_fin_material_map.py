"""Map nominal G12 material solids by geometric identity, not STEP order.

One capped child compares each regenerated solid to source STEP using bounding
boxes and centroids then two-way boolean differences. It checks positive-volume
intersections between mapped solids, not contact face ownership or strength.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
for name in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[name] = "1"
os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def function_hashes(path: Path) -> dict[str, str]:
    parsed = ast.parse(path.read_text())
    return {
        node.name: hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
        for node in parsed.body
        if isinstance(node, ast.FunctionDef) and node.name in ("_part", "layered_shapes")
    }


def write(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def descriptor(shape: Any) -> dict[str, Any]:
    b = shape.BoundingBox()
    c = shape.Center()
    return {
        "centroid_mm": [c.x, c.y, c.z],
        "bbox_mm": [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax],
        "volume_mm3": shape.Volume(),
    }


def candidate(a: dict[str, Any], b: dict[str, Any], tol: dict[str, float]) -> bool:
    return (
        abs(a["volume_mm3"] - b["volume_mm3"]) <= tol["candidate_volume_abs_mm3"]
        and max(abs(x - y) for x, y in zip(a["centroid_mm"], b["centroid_mm"], strict=True))
        <= tol["bbox_and_centroid_abs_mm"]
        and max(abs(x - y) for x, y in zip(a["bbox_mm"], b["bbox_mm"], strict=True))
        <= tol["bbox_and_centroid_abs_mm"]
    )


def material(name: str) -> str:
    if name.startswith(("root_insert", "gusset_")) and not name.startswith("gusset_face_bond"):
        return "plywood"
    if name.startswith("foam_"):
        return "PVC_foam"
    if name.startswith("skin_"):
        return "carbon_sheet"
    if name.startswith("cap_"):
        return "fiberglass"
    if name.startswith(
        ("foot_bond", "face_bond", "gusset_face_bond", "tab_potting", "frame_shell_gap_bond")
    ):
        return "epoxy"
    raise ValueError(f"Unrecognized material region {name}")


def worker(cfg: dict[str, Any], out: Path, hashes: dict[str, str]) -> None:
    start = time.monotonic()
    cpu = time.process_time()
    result: dict[str, Any] = {
        "status": "incomplete",
        "matches": [],
        "overlap_checks_completed": 0,
        "input_sha256_before": hashes,
        "face_interface_mapping": None,
        "accepted": False,
        "flight_ready": False,
    }
    try:
        import cadquery as cq

        sys.path.insert(0, str(ROOT))
        from src.analysis.layered_fin_geometry import layered_shapes
        from src.vehicle.schema import Vehicle

        candidate_file = ROOT / cfg["candidate"]
        vehicle = Vehicle.model_validate_json(candidate_file.read_text())
        if (
            hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
            != cfg["candidate_identity"]
        ):
            raise ValueError("Unexpected canonical resolved candidate")
        study = yaml.safe_load((ROOT / cfg["study"]).read_text())["root_closure"]
        fin = next(p for p in vehicle.parts if p.id == "fin_set")
        if fin.cad.parameters["layered_study"] != study:
            raise ValueError("Source study does not match embedded resolved candidate")
        layers = layered_shapes(vehicle, study)
        original = cq.importers.importStep(str(ROOT / cfg["original_fin_step"])).val()
        old = original.Solids()
        if len(layers) != 20 or len(old) != 60:
            raise ValueError("Unexpected layer or archived solid count")
        regenerated = []
        for name, shape, density in layers:
            pieces = shape.Solids()
            if len(pieces) != 3:
                raise ValueError(f"{name} did not produce three solids")
            for piece in pieces:
                if not piece.isValid() or piece.Volume() <= 0:
                    raise ValueError("Invalid regenerated solid")
                d = descriptor(piece)
                a = math.degrees(math.atan2(d["centroid_mm"][1], d["centroid_mm"][0])) % 360
                n = round(a / 120) % 3
                nearest = 120 * n
                delta = ((a - nearest + 180) % 360) - 180
                if abs(delta) >= 60:
                    raise ValueError("Cannot assign fin rotational sector")
                regenerated.append(
                    {
                        "name": name,
                        "material": material(name),
                        "density_kg_m3": density,
                        "fin_angle_deg": nearest,
                        "shape": piece,
                        "descriptor": d,
                    }
                )
        if len({(r["name"], r["fin_angle_deg"]) for r in regenerated}) != 60:
            raise ValueError("Layer / fin-angle labels are not unique")
        descriptors = [descriptor(s) for s in old]
        used = set()
        (out / "stage.txt").write_text("matching original and generated solids\n")
        for item in regenerated:
            indexes = [
                i
                for i, d in enumerate(descriptors)
                if candidate(item["descriptor"], d, cfg["matching"])
            ]
            if len(indexes) != 1 or indexes[0] in used:
                raise ValueError(
                    f"No unique geometric candidate for {item['name']} angle {item['fin_angle_deg']}: {indexes}"
                )
            i = indexes[0]
            diff = item["shape"].cut(old[i]).Volume() + old[i].cut(item["shape"]).Volume()
            row = {k: v for k, v in item.items() if k != "shape"}
            row.update(
                original_step_solid_index=i,
                original_descriptor=descriptors[i],
                symmetric_difference_mm3=diff,
            )
            result["matches"].append(row)
            write(out / "partial.json", result)
            if diff > cfg["matching"]["symmetric_difference_abs_mm3"]:
                raise ValueError(
                    f"Boolean mismatch for {item['name']} angle {item['fin_angle_deg']}: {diff}"
                )
            used.add(i)
        if len(used) != 60:
            raise ValueError("Original solid ownership not one-to-one")
        (out / "stage.txt").write_text("checking candidate solid overlap\n")
        checks = 0
        max_overlap = 0.0
        for i, a in enumerate(regenerated):
            aa = a["descriptor"]["bbox_mm"]
            for b in regenerated[i + 1 :]:
                bb = b["descriptor"]["bbox_mm"]
                if all(
                    min(aa[2 * k + 1], bb[2 * k + 1]) - max(aa[2 * k], bb[2 * k]) > 1e-7
                    for k in range(3)
                ):
                    vol = a["shape"].intersect(b["shape"]).Volume()
                    checks += 1
                    max_overlap = max(max_overlap, vol)
                    if vol > cfg["matching"]["intersection_volume_abs_mm3"]:
                        result["overlap_failure"] = {
                            "a": a["name"],
                            "b": b["name"],
                            "overlap_mm3": vol,
                        }
                        raise ValueError("Positive volume material overlap")
        result.update(
            status="solid_mapping_completed_face_ownership_unclosed",
            overlap_checks_completed=checks,
            max_overlap_mm3=max_overlap,
            matching="unique bbox/centroid/volume candidates plus per-solid two-way boolean differences; STEP index only identifies original file",
            material_basis="named nominal geometry/density identity, not measured hot allowables",
            physics_acceptance=False,
        )
    finally:
        result["input_sha256_after"] = {p: sha(ROOT / p) for p in hashes}
        result["inputs_unchanged"] = result["input_sha256_before"] == result["input_sha256_after"]
        result["elapsed_wall_s"] = time.monotonic() - start
        result["process_cpu_s"] = time.process_time() - cpu
        result["max_rss_bytes_macos"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        write(out / "record.json", result)
    if not result["inputs_unchanged"]:
        raise ValueError("Source files changed during packet")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/studies/wo03-fin-material-map.yaml"
    )
    parser.add_argument("--preset", choices=["tiny"], default="tiny")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    out = args.output or ROOT / cfg["default_output"]
    helper = ROOT / "src/analysis/layered_fin_geometry.py"
    if function_hashes(helper) != cfg["source_function_ast_sha256"]:
        raise ValueError("Extracted AST identity mismatch")
    if (
        sha(ROOT / cfg["candidate"]) != cfg["candidate_file_sha256"]
        or sha(ROOT / cfg["original_fin_step"]) != cfg["original_fin_step_sha256"]
    ):
        raise ValueError("Candidate or STEP hash mismatch")
    driver = ROOT / "scripts/wo03_trainer_fin_root.py"
    if driver.exists() and (
        sha(driver) != cfg["historical_driver_sha256"]
        or function_hashes(driver) != cfg["source_function_ast_sha256"]
    ):
        raise ValueError("Historical driver source mismatch")
    paths = [
        Path(__file__),
        args.config,
        helper,
        ROOT / cfg["candidate"],
        ROOT / cfg["study"],
        ROOT / cfg["original_fin_step"],
        ROOT / "src/vehicle/schema.py",
        ROOT / "src/vehicle/materials.py",
        ROOT / "src/vehicle/cad_contract.py",
        *sorted((ROOT / "src/cad").glob("*.py")),
    ]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    if args.worker:
        resource.setrlimit(
            resource.RLIMIT_CPU, (cfg["budget"]["cpu_seconds"], cfg["budget"]["cpu_seconds"])
        )
        worker(cfg, out, hashes)
        return
    out.mkdir(parents=True, exist_ok=False)
    begin = time.monotonic()
    try:
        proc = subprocess.run(
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
        (out / "worker.log").write_text(proc.stdout)
        status = {
            "returncode": proc.returncode,
            "wall_s": time.monotonic() - begin,
            "timed_out": False,
            "completed": proc.returncode == 0,
        }
    except subprocess.TimeoutExpired as e:
        (out / "worker.log").write_bytes(e.stdout or b"")
        status = {
            "returncode": None,
            "wall_s": time.monotonic() - begin,
            "timed_out": True,
            "completed": False,
        }
    write(out / "completion.json", status)
    if not status["completed"]:
        raise SystemExit("Stopped; preserve evidence and replan before any repeat")


if __name__ == "__main__":
    main()
