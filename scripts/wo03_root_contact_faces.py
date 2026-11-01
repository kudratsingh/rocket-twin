"""Known-case-checked BRep face-common areas for the saved G12 root.

No geometric gap is closed or assigned an adhesive. Face patches are nominal
coincident BRep surfaces only; physical bond coverage and strength are unknown.
"""

from __future__ import annotations

import argparse
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


def write(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def bbox(shape: Any) -> list[float]:
    b = shape.BoundingBox()
    return [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]


def box_can_touch(a: list[float], b: list[float]) -> bool:
    return all(max(a[2 * i], b[2 * i]) <= min(a[2 * i + 1], b[2 * i + 1]) for i in range(3))


def desc(face: Any) -> dict[str, Any]:
    c = face.Center()
    n = face.normalAt()
    return {
        "area_mm2": face.Area(),
        "bbox_mm": bbox(face),
        "centroid_mm": [c.x, c.y, c.z],
        "surface": face.geomType(),
        "sample_normal_xyz": [n.x, n.y, n.z],
    }


def common(a: Any, b: Any, epsilon: float) -> list[Any]:
    shape = a.intersect(b)
    return [f for f in shape.Faces() if f.Area() > epsilon]


def opposing(face_a: Any, face_b: Any, patch: Any) -> dict[str, Any]:
    u0, u1, v0, v1 = patch.uvBounds()
    point = patch.positionAt((u0 + u1) / 2, (v0 + v1) / 2)
    na = face_a.normalAt(point)
    nb = face_b.normalAt(point)
    return {
        "sample_xyz_mm": [point.x, point.y, point.z],
        "normal_a_xyz": [na.x, na.y, na.z],
        "normal_b_xyz": [nb.x, nb.y, nb.z],
        "normal_dot": na.dot(nb),
        "scope": "one surface sample; not a proof for every point",
    }


def fixtures(cfg: dict[str, Any]) -> dict[str, Any]:
    import cadquery as cq

    e = cfg["positive_patch_area_mm2"]
    tol = cfg["fixture_area_abs_tolerance_mm2"]
    a = cq.Face.makePlane(10, 10)
    b = cq.Face.makePlane(10, 10)
    partial = cq.Face.makePlane(10, 10, basePnt=(5, 0, 0))
    gap = cq.Face.makePlane(10, 10, basePnt=(0, 0, 0.1))
    area = lambda x, y: sum(f.Area() for f in common(x, y, e))
    cyl_a = cq.Solid.makeCylinder(10, 10, angleDegrees=90)
    cyl_b = cq.Solid.makeCylinder(10, 10, angleDegrees=90).rotate((0, 0, 0), (0, 0, 1), 45)
    a_curved = next(f for f in cyl_a.Faces() if f.geomType() == "CYLINDER")
    b_curved = next(f for f in cyl_b.Faces() if f.geomType() == "CYLINDER")
    expected = {
        "planar_full_mm2": 100.0,
        "planar_half_mm2": 50.0,
        "physical_gap_mm2": 0.0,
        "curved_45deg_common_mm2": math.pi / 4 * 10 * 10,
    }
    actual = {
        "planar_full_mm2": area(a, b),
        "planar_half_mm2": area(a, partial),
        "physical_gap_mm2": area(a, gap),
        "curved_45deg_common_mm2": area(a_curved, b_curved),
    }
    return {
        "expected": expected,
        "actual": actual,
        "passed": all(abs(actual[k] - v) <= tol for k, v in expected.items()),
        "meaning": "one planar full, half and positive gap, and one truly curved cylindrical clipped face",
    }


def selected_solids(fin: Any, mapping: dict[str, Any]) -> dict[str, Any]:
    solids = fin.Solids()
    wanted = (
        "foot_bond_-1",
        "foot_bond_1",
        "gusset_-1",
        "gusset_1",
        "root_insert_and_tab",
        "tab_potting",
        "frame_shell_gap_bond",
    )
    out = {}
    for name in wanted:
        rows = [r for r in mapping["matches"] if r["name"] == name and r["fin_angle_deg"] == 0]
        if len(rows) != 1:
            raise ValueError(f"Expected one first-fin mapping for {name}")
        row = rows[0]
        shape = solids[row["original_step_solid_index"]]
        c = shape.Center()
        b = bbox(shape)
        d = row["original_descriptor"]
        if (
            max(abs(x - y) for x, y in zip([c.x, c.y, c.z], d["centroid_mm"], strict=True)) > 1e-5
            or max(abs(x - y) for x, y in zip(b, d["bbox_mm"], strict=True)) > 1e-5
            or abs(shape.Volume() - d["volume_mm3"]) > 1e-4
        ):
            raise ValueError(f"Saved STEP locator does not match mapped solid: {name}")
        out[name] = shape
    return out


def measure(a: Any, b: Any, cfg: dict[str, Any]) -> dict[str, Any]:
    af, bf = a.Faces(), b.Faces()
    eps = cfg["positive_patch_area_mm2"]
    patches = []
    common_shapes = []
    for ai, fa in enumerate(af):
        for bi, fb in enumerate(bf):
            if not box_can_touch(bbox(fa), bbox(fb)):
                continue
            for patch in common(fa, fb, eps):
                if not patch.isValid():
                    raise ValueError("Invalid common face")
                normals = opposing(fa, fb, patch)
                row = {
                    "face_a_index": ai,
                    "face_b_index": bi,
                    "face_a": desc(fa),
                    "face_b": desc(fb),
                    "common_face": desc(patch),
                    **normals,
                    "normals_opposed_at_sample": normals["normal_dot"]
                    <= cfg["normal_opposition_dot_max"],
                }
                patches.append(row)
                common_shapes.append(patch)
    # Overlapping patches imply ambiguous/double counted face ownership.
    for i, p in enumerate(common_shapes):
        for q in common_shapes[i + 1 :]:
            if box_can_touch(bbox(p), bbox(q)) and sum(x.Area() for x in common(p, q, eps)) > eps:
                raise ValueError("Overlapping common patches; cannot add areas")
    return {
        "source_a_faces": len(af),
        "source_b_faces": len(bf),
        "patches": patches,
        "coincident_area_mm2": sum(x["common_face"]["area_mm2"] for x in patches),
        "opposed_at_sample_area_mm2": sum(
            x["common_face"]["area_mm2"] for x in patches if x["normals_opposed_at_sample"]
        ),
        "all_sample_normals_opposed": all(x["normals_opposed_at_sample"] for x in patches),
        "scope": "nominal coincident areas; one normal sample per patch, not actual wet bond",
    }


def actual(cfg: dict[str, Any], out: Path) -> dict[str, Any]:
    import cadquery as cq

    sys.path.insert(0, str(ROOT))
    from src.cad.parts import local_shape
    from src.vehicle.schema import Vehicle

    vehicle = Vehicle.model_validate_json((ROOT / cfg["candidate"]).read_text())
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    if identity != "4ff75b8f2c6ab47ddf90b546761d7fa6d4a72c3af9f382e6b3790cbeb19c1287":
        raise ValueError("Unexpected canonical candidate")
    mapping = json.loads((ROOT / cfg["material_map"]).read_text())
    if (
        mapping["status"] != "solid_mapping_completed_face_ownership_unclosed"
        or len(mapping["matches"]) != 60
        or not mapping["inputs_unchanged"]
    ):
        raise ValueError("Source material map is incomplete")
    finshape = cq.importers.importStep(str(ROOT / cfg["fin_step"])).val()
    parts = {p.id: p for p in vehicle.parts}
    fin = parts["fin_set"]
    frame = parts["gimbal_frame"]
    shell = parts["aft_shell"]
    shapes = {
        k: v.translate(
            (fin.lateral_offset_m[0] * 1000, -fin.lateral_offset_m[1] * 1000, fin.position_m * 1000)
        )
        for k, v in selected_solids(finshape, mapping).items()
    }
    shapes["frame"] = (
        cq.importers.importStep(str(ROOT / cfg["frame_step"]))
        .val()
        .translate(
            (
                frame.lateral_offset_m[0] * 1000,
                -frame.lateral_offset_m[1] * 1000,
                frame.position_m * 1000,
            )
        )
    )
    shapes["shell"] = local_shape(shell).translate(
        (
            shell.lateral_offset_m[0] * 1000,
            -shell.lateral_offset_m[1] * 1000,
            shell.position_m * 1000,
        )
    )
    if any(not s.isValid() for s in shapes.values()):
        raise ValueError("Invalid selected source geometry")
    pairs = [
        ("foot_bond_-1", "gusset_-1"),
        ("foot_bond_-1", "shell"),
        ("foot_bond_1", "gusset_1"),
        ("foot_bond_1", "shell"),
        ("root_insert_and_tab", "tab_potting"),
        ("tab_potting", "frame"),
        ("frame_shell_gap_bond", "frame"),
        ("frame_shell_gap_bond", "shell"),
    ]
    rows = []
    for an, bn in pairs:
        row = {"a": an, "b": bn, **measure(shapes[an], shapes[bn], cfg)}
        rows.append(row)
        write(out / "partial-actual.json", {"interfaces": rows})
    return {
        "candidate_identity": identity,
        "interfaces": rows,
        "shell_basis": "current source local_shape; historical shell BRep equivalence unproved",
        "face_index_basis": "zero-based Faces() index after stated source placement; descriptors and input hashes make locator inspectable; not a cross-version stable face ID",
        "accepted": False,
        "flight_ready": False,
        "wet_bond_or_allowable_established": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/studies/wo03-root-contact-faces.yaml"
    )
    parser.add_argument("--preset", choices=["tiny"], default="tiny")
    parser.add_argument("--child", choices=["fixtures", "actual"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    out = args.output or ROOT / cfg["default_output"]
    paths = [
        args.config,
        Path(__file__),
        ROOT / "src/vehicle/schema.py",
        ROOT / "src/vehicle/materials.py",
        ROOT / "src/vehicle/cad_contract.py",
        *sorted((ROOT / "src/cad").glob("*.py")),
    ] + [ROOT / cfg[k] for k in ("candidate", "material_map", "fin_step", "frame_step")]
    for k in ("candidate", "material_map", "fin_step", "frame_step"):
        if sha(ROOT / cfg[k]) != cfg[k + "_sha256"]:
            raise ValueError(f"{k} source hash mismatch")
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    if args.child:
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (cfg["budget"]["per_child_cpu_seconds"], cfg["budget"]["per_child_cpu_seconds"]),
        )
        start = time.monotonic()
        cpu = time.process_time()
        result = fixtures(cfg) if args.child == "fixtures" else actual(cfg, out)
        result.update(
            input_sha256_before=hashes,
            input_sha256_after={p: sha(ROOT / p) for p in hashes},
            wall_s=time.monotonic() - start,
            cpu_s=time.process_time() - cpu,
            max_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        )
        result["inputs_unchanged"] = result["input_sha256_before"] == result["input_sha256_after"]
        write(out / (args.child + ".json"), result)
        if not result["inputs_unchanged"] or (args.child == "fixtures" and not result["passed"]):
            raise ValueError("Fixture or source identity failure")
        return
    out.mkdir(parents=True, exist_ok=False)
    stages = []
    cpu_total = 0.0
    for phase in ("fixtures", "actual"):
        before = resource.getrusage(resource.RUSAGE_CHILDREN)
        t = time.monotonic()
        try:
            proc = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--child",
                    phase,
                    "--config",
                    str(args.config),
                    "--output",
                    str(out),
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=cfg["budget"]["per_child_wall_seconds"],
                check=False,
            )
            (out / (phase + ".log")).write_text(proc.stdout)
            code = proc.returncode
            timeout = False
        except subprocess.TimeoutExpired as e:
            (out / (phase + ".log")).write_bytes(e.stdout or b"")
            code = None
            timeout = True
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        used = after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime
        cpu_total += used
        stages.append(
            {
                "phase": phase,
                "returncode": code,
                "timed_out": timeout,
                "wall_s": time.monotonic() - t,
                "cpu_s": used,
                "child_cumulative_maxrss_bytes": after.ru_maxrss,
            }
        )
        write(
            out / "completion.json",
            {
                "stages": stages,
                "total_child_cpu_s": cpu_total,
                "complete": phase == "actual" and code == 0 and not timeout,
            },
        )
        if timeout or code != 0 or cpu_total >= cfg["budget"]["total_cpu_seconds"]:
            raise SystemExit(f"{phase} stopped: preserve evidence, no retry")


if __name__ == "__main__":
    main()
