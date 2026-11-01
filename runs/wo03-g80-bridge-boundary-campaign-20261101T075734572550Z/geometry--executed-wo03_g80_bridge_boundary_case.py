"""Owned-child, no-mesh geometry preflight for the proposed washer controls."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.wo03_g80_bridge_adapter import build_case, source_hashes
from scripts.wo03_g80_washer_boundary import (
    apply_washer_boundary,
    verify_source_hashes,
)
from scripts.wo03_owned_process import OwnedProcessError, darwin_process_callbacks, run_owned

CONFIG = ROOT / "configs/studies/wo03-g80-bridge-boundary-case.yaml"


def inspect_and_apply(gmsh, patches, spec, output):
    """Persist observed ownership before attempting strict circle identification."""
    inventory = []
    for i, patch in enumerate(patches):
        faces = [(2, int(tag)) for tag in patch["face_tags"]]
        boundary = gmsh.model.getBoundary(faces, combined=True, oriented=False, recursive=False)
        curves = [
            {
                "tag": int(tag),
                "type": gmsh.model.getType(1, int(tag)),
                "arc_length_mm": float(gmsh.model.occ.getMass(1, int(tag))),
            }
            for dim, tag in boundary
            if dim == 1
        ]
        inventory.append(
            {
                "patch_index": i,
                "face_tags": patch["face_tags"],
                "step_center_xyz_mm": patch["center_xyz_mm"],
                "face_area_mm2": sum(float(gmsh.model.occ.getMass(2, t)) for _, t in faces),
                "boundary_curves": curves,
            }
        )
    evidence = {"status": "selection_started", "patches": inventory}
    Path(output).write_text(json.dumps(evidence, indent=2) + "\n")
    try:
        report = apply_washer_boundary(
            gmsh,
            patches,
            outer_radius=spec["patch_outer_radius_mm"],
            inner_radius=spec["patch_inner_radius_mm"],
            outer_segments=spec["full_circle_equivalent_segments"]["outer"],
            inner_segments=spec["full_circle_equivalent_segments"]["inner"],
            tolerance=spec["curve_match_tolerance_mm"],
        )
        if len(report["patches"]) != 3:
            raise ValueError("Expected exactly three washer patches")
        evidence.update(status="controls_applied_no_mesh", assignment=report)
        return evidence
    except Exception as exc:
        evidence.update(status="selection_failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        Path(output).write_text(json.dumps(evidence, indent=2) + "\n")


def worker(out, cfg, spec):
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    import gmsh

    old = gmsh.model.mesh.generate

    def forbidden(*_args, **_kwargs):
        raise RuntimeError("Geometry-only guard forbids mesh generation")

    gmsh.model.mesh.generate = forbidden
    try:
        verify_source_hashes(ROOT, spec)
        result = build_case(
            out / "geometry",
            cfg["bulk_mesh_target_mm"],
            cfg["maximum_nodes"],
            cfg["maximum_tetrahedra"],
            geometry_only=True,
            boundary_callback=lambda g, p: inspect_and_apply(
                g, p, spec, out / "boundary-inventory.json"
            ),
        )
        if result["mesh_generated"] or result["solver_invoked"] or not result["boundary_control"]:
            raise ValueError("Incomplete geometry-only boundary report")
        print(
            json.dumps({"status": result["status"], "boundary": result["boundary_control"]}),
            flush=True,
        )
    finally:
        gmsh.model.mesh.generate = old
        self_usage = resource.getrusage(resource.RUSAGE_SELF)
        child_usage = resource.getrusage(resource.RUSAGE_CHILDREN)
        (out / "worker-resources.json").write_text(
            json.dumps(
                {
                    "worker_cpu_s": self_usage.ru_utime + self_usage.ru_stime,
                    "child_cpu_s": child_usage.ru_utime + child_usage.ru_stime,
                    "worker_peak_rss_bytes_macos": self_usage.ru_maxrss,
                },
                indent=2,
            )
            + "\n"
        )


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def packet(out, cfg, spec):
    out.mkdir(parents=True, exist_ok=False)
    prior = ROOT / "build/wo03-g80-bridge-mapping-replan-v1/record.json"
    previous = json.loads(prior.read_text())
    if (
        previous["status"] != "stopped"
        or previous["solver_invoked"]
        or not previous["source_unchanged"]
    ):
        raise ValueError("Previous guarded stop provenance is invalid")
    if (
        cfg["prior_conservative_cpu_charge_s"]
        + cfg["additional_setup_and_control_cpu_reservation_s"]
        + 10
        > cfg["packet_cpu_limit_s"]
    ):
        raise ValueError("Insufficient packet CPU budget")
    physical = source_hashes()
    if physical != previous["physical_source_sha256"]:
        raise ValueError("Physical source differs from previous case")
    verify_source_hashes(ROOT, spec)
    files = [
        Path(__file__).resolve(),
        CONFIG,
        ROOT / "configs/studies/wo03-g80-washer-boundary.yaml",
        ROOT / "scripts/wo03_g80_bridge_adapter.py",
        ROOT / "scripts/wo03_g80_washer_boundary.py",
        ROOT / "scripts/wo03_owned_process.py",
        ROOT / "tests/test_g80_bridge_boundary_case.py",
    ]
    before = {str(p): digest(p) for p in files}
    for p in files:
        (out / ("executed-" + p.name)).write_bytes(p.read_bytes())
    status = None
    failure = None
    env = dict(os.environ)
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env[name] = "1"
    rss, children = darwin_process_callbacks()
    try:
        status = run_owned(
            [sys.executable, str(Path(__file__).resolve()), "--worker", "--output", str(out)],
            log_path=out / "worker.log",
            status_path=out / "owned-status.json",
            wall_limit_s=30,
            rss_callback=rss,
            descendants_callback=children,
            rss_limit_bytes=cfg["maximum_process_rss_bytes"],
            cwd=ROOT,
            env=env,
        )
    except (OwnedProcessError, OSError, ValueError) as exc:
        failure = f"{type(exc).__name__}: {exc}"
    finally:
        status_path = out / "owned-status.json"
        if status_path.exists():
            status = json.loads(status_path.read_text())
        after = {str(p): digest(p) for p in files}
        record = {
            "status": (
                "geometry_boundary_preflight_passed"
                if failure is None and before == after
                else "stopped"
            ),
            "error": failure,
            "source_before": before,
            "source_after": after,
            "source_unchanged": before == after,
            "physical_source_sha256": physical,
            "prior_case_record_sha256": digest(prior),
            "prior_conservative_cpu_charge_s": cfg["prior_conservative_cpu_charge_s"],
            "setup_control_cpu_reservation_s": cfg[
                "additional_setup_and_control_cpu_reservation_s"
            ],
            "setup_reservation_is_measured": False,
            "worker_cpu_limit_s": 10,
            "worker_wall_limit_s": 30,
            "rss_limit_bytes": cfg["maximum_process_rss_bytes"],
            "owned_status": status,
            "mesh_generated": False,
            "ccx_invoked": False,
            "actual_acceptance": False,
        }
        (out / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    if failure or before != after:
        raise RuntimeError(f'Geometry boundary preflight stopped: {failure or "source changed"}')
    print(json.dumps({"status": record["status"], "worker": status}), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    cfg = yaml.safe_load(CONFIG.read_text())
    spec = yaml.safe_load((ROOT / cfg["boundary_spec"]).read_text())
    if args.worker:
        worker(args.output.resolve(), cfg, spec)
    else:
        packet(args.output.resolve(), cfg, spec)


if __name__ == "__main__":
    main()
