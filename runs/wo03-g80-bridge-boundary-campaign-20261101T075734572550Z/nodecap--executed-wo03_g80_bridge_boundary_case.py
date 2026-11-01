"""Owned-child, no-mesh geometry preflight for the proposed washer controls."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import sys
import time
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


def mesh_worker(out, cfg, spec):
    """Create one controlled mesh and run all existing pre-solver guards."""
    resource.setrlimit(resource.RLIMIT_CPU, (45, 45))
    from scripts.wo03_g80_bridge_fea import validate_adapter_loads

    try:
        verify_source_hashes(ROOT, spec)
        fea_cfg = yaml.safe_load((ROOT / "configs/studies/wo03-g80-bridge-fea.yaml").read_text())
        folder = out / "bridge_1p5mm"
        build_case(
            folder,
            cfg["bulk_mesh_target_mm"],
            cfg["maximum_nodes"],
            cfg["maximum_tetrahedra"],
            boundary_callback=lambda g, p: inspect_and_apply(
                g, p, spec, out / "boundary-inventory.json"
            ),
        )
        metadata = json.loads((folder / "mesh-meta.json").read_text())
        checks = validate_adapter_loads(metadata, fea_cfg)
        deck = (folder / "case.inp").read_text().upper()
        if deck.count("*STEP") != 2 or deck.count("*CLOAD,OP=NEW") != 2:
            raise ValueError("Expected two independent load steps")
        (folder / "input-check.json").write_text(json.dumps(checks, indent=2) + "\n")
        print(json.dumps(checks), flush=True)
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        (out / "mesh-worker-resources.json").write_text(
            json.dumps(
                {
                    "worker_cpu_s": usage.ru_utime + usage.ru_stime,
                    "child_cpu_s": children.ru_utime + children.ru_stime,
                    "peak_rss_bytes_macos": usage.ru_maxrss,
                },
                indent=2,
            )
            + "\n"
        )


def coarse_packet(out, cfg, spec):
    """One 1.5 mm, two-step case; each direct child and total wall are guarded."""
    from scripts.wo03_g80_bridge_fea import assess_adapter_output

    out.mkdir(parents=True, exist_ok=False)
    stage_dir = ROOT / "build/wo03-g80-bridge-boundary-case-v1"
    stage = json.loads((stage_dir / "record.json").read_text())
    if stage["status"] != "geometry_boundary_preflight_passed" or not stage["source_unchanged"]:
        raise ValueError("Geometry stage is not validated")
    physical = source_hashes()
    if physical != stage["physical_source_sha256"]:
        raise ValueError("Physical source changed since geometry stage")
    verify_source_hashes(ROOT, spec)
    unchanged = [
        "wo03_g80_bridge_adapter.py",
        "wo03_g80_washer_boundary.py",
        "wo03_owned_process.py",
        "wo03-g80-washer-boundary.yaml",
        "wo03-g80-bridge-boundary-case.yaml",
    ]
    for name in unchanged:
        path = ROOT / ("configs/studies" if name.endswith(".yaml") else "scripts") / name
        if digest(path) != digest(stage_dir / ("executed-" + name)):
            raise ValueError(f"Geometry-stage source changed: {name}")
    old_case = stage_dir / "executed-wo03_g80_bridge_boundary_case.py"
    if digest(old_case) != stage["source_before"][str(Path(__file__).resolve())]:
        raise ValueError("Geometry-stage script snapshot does not match its ledger")
    ccx = Path("/opt/homebrew/bin/ccx")
    fea_cfg = yaml.safe_load((ROOT / "configs/studies/wo03-g80-bridge-fea.yaml").read_text())
    if str(ccx) != fea_cfg["ccx"] or digest(ccx) != fea_cfg["ccx_sha256"]:
        raise ValueError("Pinned CCX changed")
    prior = (
        cfg["prior_conservative_cpu_charge_s"]
        + cfg["additional_setup_and_control_cpu_reservation_s"]
    )
    cpu = stage["owned_status"]["cpu_accounting"]
    prior += cpu["child_user_s_delta"] + cpu["child_system_s_delta"]
    if prior + 90 > cfg["packet_cpu_limit_s"]:
        raise ValueError("Insufficient packet CPU budget")
    files = [
        Path(__file__).resolve(),
        CONFIG,
        ROOT / "configs/studies/wo03-g80-washer-boundary.yaml",
        ROOT / "configs/studies/wo03-g80-bridge-fea.yaml",
        ROOT / "scripts/wo03_g80_bridge_adapter.py",
        ROOT / "scripts/wo03_g80_washer_boundary.py",
        ROOT / "scripts/wo03_g80_bridge_fea.py",
        ROOT / "scripts/wo03_owned_process.py",
        ROOT / "tests/test_g80_bridge_boundary_case.py",
        ccx,
    ]
    before = {str(p): digest(p) for p in files}
    for p in files[:-1]:
        (out / ("executed-" + p.name)).write_bytes(p.read_bytes())
    record = {
        "status": "started",
        "geometry_stage_record_sha256": digest(stage_dir / "record.json"),
        "geometry_stage_previous_case_script_sha256": digest(old_case),
        "case_script_change_reason": "Add separately authorized 45+45 CPU coarse branch; geometry-stage snapshot preserved.",
        "physical_source_sha256": physical,
        "source_before": before,
        "prior_conservative_cpu_charge_s": prior,
        "case_cpu_cap_s": 90,
        "case_wall_cap_s": 120,
        "mesh_cpu_cap_s": 45,
        "solver_cpu_cap_s": 45,
        "rss_cap_bytes": cfg["maximum_process_rss_bytes"],
        "node_cap": cfg["maximum_nodes"],
        "tet_cap": cfg["maximum_tetrahedra"],
        "solver_invoked": False,
        "actual_acceptance": False,
    }

    def persist():
        (out / "record.json").write_text(json.dumps(record, indent=2) + "\n")

    persist()
    start = time.monotonic()
    failure = None
    rss, children = darwin_process_callbacks()
    env = dict(os.environ)
    for n in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env[n] = "1"
    try:
        record["mesh_status"] = run_owned(
            [sys.executable, str(Path(__file__).resolve()), "--mesh-worker", "--output", str(out)],
            log_path=out / "mesh.log",
            status_path=out / "mesh-status.json",
            wall_limit_s=120,
            rss_callback=rss,
            descendants_callback=children,
            rss_limit_bytes=cfg["maximum_process_rss_bytes"],
            cwd=ROOT,
            env=env,
        )
        folder = out / "bridge_1p5mm"
        record["input_check"] = json.loads((folder / "input-check.json").read_text())
        if before != {str(p): digest(p) for p in files} or physical != source_hashes():
            raise ValueError("Sources changed before solver")
        remaining = 120 - (time.monotonic() - start)
        if remaining <= 0:
            raise TimeoutError("Case wall budget exhausted before solver")
        command = (
            "import os,resource;resource.setrlimit(resource.RLIMIT_CPU,(45,45));os.execv("
            + repr(str(ccx))
            + ",["
            + repr(str(ccx))
            + ",'-i','case'])"
        )
        record["solver_invoked"] = True
        persist()
        record["solver_status"] = run_owned(
            [sys.executable, "-c", command],
            log_path=out / "solver.log",
            status_path=out / "solver-status.json",
            wall_limit_s=remaining,
            rss_callback=rss,
            descendants_callback=children,
            rss_limit_bytes=cfg["maximum_process_rss_bytes"],
            cwd=folder,
            env=env,
        )
        if (
            "*ERROR" in (out / "solver.log").read_text(errors="replace").upper()
            or not (folder / "case.dat").exists()
        ):
            raise ValueError("CCX returned error or did not write native output")
        record["result"] = assess_adapter_output(folder)
        record["status"] = "coarse_diagnostic_complete_no_acceptance"
    except (OwnedProcessError, OSError, ValueError, TimeoutError, KeyError) as exc:
        failure = f"{type(exc).__name__}: {exc}"
        record["status"] = "stopped"
        record["error"] = failure
    finally:
        record["case_wall_s"] = time.monotonic() - start
        record["source_after"] = {str(p): digest(p) for p in files}
        record["source_unchanged"] = record["source_before"] == record["source_after"]
        for name in ("mesh", "solver"):
            path = out / (name + "-status.json")
            if path.exists():
                record[name + "_status"] = json.loads(path.read_text())
        persist()
    if failure or not record["source_unchanged"]:
        raise RuntimeError(f'Coarse diagnostic stopped: {failure or "source changed"}')
    print(
        json.dumps(
            {
                "status": record["status"],
                "input_check": record["input_check"],
                "result": record["result"],
            }
        ),
        flush=True,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worker", action="store_true")
    p.add_argument("--mesh-worker", action="store_true")
    p.add_argument("--coarse", action="store_true")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    cfg = yaml.safe_load(CONFIG.read_text())
    spec = yaml.safe_load((ROOT / cfg["boundary_spec"]).read_text())
    if args.mesh_worker:
        mesh_worker(args.output.resolve(), cfg, spec)
    elif args.coarse:
        coarse_packet(args.output.resolve(), cfg, spec)
    elif args.worker:
        worker(args.output.resolve(), cfg, spec)
    else:
        packet(args.output.resolve(), cfg, spec)


if __name__ == "__main__":
    main()
