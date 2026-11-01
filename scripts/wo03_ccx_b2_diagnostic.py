"""Separate B2-only diagnostic preparation; no actual bridge launch path."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import resource
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-ccx-b2-diagnostic.yaml"
OUT = ROOT / "build/wo03-ccx-b2-diagnostic-v1"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def b1_module(cfg):
    p = ROOT / cfg["b1_driver"]
    if sha(p) != cfg["b1_driver_sha256"]:
        raise ValueError("B1 frozen driver changed")
    spec = importlib.util.spec_from_file_location("frozen_b1", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def field_consistency(
    meta, baseline_frd, baseline_dat, candidate_frd, candidate_dat, reader, dat_parser
):
    ids = sorted(map(int, meta["node_coordinates_mm"]))
    a = reader.parse_vector_fields(baseline_frd.read_bytes(), ids)
    b = reader.parse_vector_fields(candidate_frd.read_bytes(), ids)
    da = dat_parser(baseline_dat)
    db = dat_parser(candidate_dat)
    reports = []
    for index, (x, y) in enumerate(zip(a, b)):
        step = index // 2 + 1
        name = "displacements" if x["field"] == "DISP" else "forces"
        if x["field"] != y["field"] or x["step"] != step or y["step"] != step:
            raise ValueError("Field identity mismatch")
        ra = {r["id"]: r for r in da[(step, name, "ALL")]}
        rb = {r["id"]: r for r in db[(step, name, "ALL")]}
        if set(ra) != set(ids) or set(rb) != set(ids):
            raise ValueError("DAT ID set mismatch")
        rows = []
        for n in ids:
            u = x["values"][n]
            v = y["values"][n]
            diffs = [v[j] - u[j] for j in range(3)]
            bounds = [reader.float32_radius(u[j]) + reader.float32_radius(v[j]) for j in range(3)]
            delta = math.sqrt(sum(z * z for z in diffs))
            unc = math.sqrt(sum(z * z for z in bounds))
            if not math.isfinite(delta + unc):
                raise ValueError("Nonfinite comparison")
            rows.append(
                {
                    "node": n,
                    "difference": diffs,
                    "difference_norm": delta,
                    "combined_encoding_bound_norm": unc,
                    "diagnostic_cap_N": 1e-5 if name == "forces" else None,
                    "diagnostic_pass": delta + unc <= 1e-5 if name == "forces" else None,
                }
            )
        reports.append(
            {
                "step": step,
                "field": x["field"],
                "max_difference_norm": max(r["difference_norm"] for r in rows),
                "nodes": rows,
                "u_comparison_basis": (
                    "reported only; both independently pass analytic gate"
                    if name == "displacements"
                    else None
                ),
            }
        )
    return reports


def paths(cfg):
    return {
        k: ROOT / cfg[k]
        for k in (
            "fixture_source",
            "fixture_meta",
            "b1_frd",
            "b1_dat",
            "b1_assessment",
            "b1_driver",
        )
    }


def prepare(cfg):
    if cfg["native_execution_authorized"]:
        raise ValueError("Prepare-only config must be disabled")
    reader = b1_module(cfg)
    ps = paths(cfg)
    before = {k: sha(v) for k, v in ps.items()}
    b1 = json.loads(ps["b1_assessment"].read_text())
    restoration = json.loads(
        (ROOT / "build/wo03-ccx-backend-diagnostic-v2/restoration.json").read_text()
    )
    if (
        before["b1_frd"] != restoration["raw_frd_sha256"]
        or before["b1_dat"] != restoration["raw_dat_sha256"]
        or before["b1_assessment"] != restoration["raw_assessment_sha256"]
    ):
        raise ValueError("Preserved B1 evidence does not match original restoration ledger")
    if b1["status"] != "stopped_precision_or_force" or not b1["source_unchanged"]:
        raise ValueError("B1 closed state mismatch")
    if sha(Path(cfg["solver"])) != cfg["solver_sha256"]:
        raise ValueError("Binary hash mismatch")
    deck = reader.transform(ps["fixture_source"].read_text(), True)
    target = OUT / "B2.inp"
    OUT.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(target)
    target.write_text(deck)
    v1 = ROOT / "build/wo03-ccx-backend-diagnostic-v2/B_iterative_cholesky_binary.inp"
    if sha(target) != sha(v1):
        raise ValueError("B2 differs from earlier reversible deck")
    from scripts.wo03_ccx_reaction_fixture import nonnative_preflight

    meta = json.loads(ps["fixture_meta"].read_text())
    nonnative_preflight(meta, deck)
    if meta["node_count"] != 593 or max(meta["node_count"], meta["c3d10_count"]) > 5000:
        raise ValueError("B mesh cap mismatch")
    check = reader.assess_b(meta, deck, ps["b1_dat"], ps["b1_frd"])
    if [x["force_status"] for x in check["steps"]] != ["unavailable_precision", "pass"]:
        raise ValueError("B1 assessment changed")
    sources = [
        Path(__file__).resolve(),
        CONFIG,
        ROOT / "scripts/wo03_ccx_reaction_fixture.py",
        ROOT / "scripts/wo03_g80_bridge_fea.py",
        ROOT / "scripts/wo03_owned_process.py",
        ROOT / "tests/test_ccx_b2_diagnostic.py",
    ]
    for p, h in (
        (sources[2], "4444ec418530a775ac6dfbec7573c33e9f14185a6ab64b58bfa83c1e08d0d8c3"),
        (sources[3], "81c667881957fed28b68cc2bf595c04a778701002b0e3c7ed09321ee26ca740e"),
        (sources[4], "65b2cf8b647412ad35c38171c119eadd538de4a760ffd1224926cfbb9fa4cd9f"),
    ):
        if sha(p) != h:
            raise ValueError("B1 helper changed")
    after = {k: sha(v) for k, v in ps.items()}
    if before != after:
        raise ValueError("Source changed")
    rec = {
        "status": "prepared_no_native",
        "source_before": before,
        "source_after": after,
        "source_ledger": {str(p): sha(p) for p in sources},
        "solver_sha256": cfg["solver_sha256"],
        "b2_deck_sha256": sha(target),
        "b1_recheck": check,
        "native_execution_authorized": False,
        "packet_cpu_reservation_s": 420,
        "actual_case_implemented": False,
    }
    (OUT / "preflight.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps({"status": rec["status"], "b2_sha256": rec["b2_deck_sha256"]}))


def run_b2(cfg):
    if not cfg["native_execution_authorized"]:
        raise ValueError("B2 not admitted")
    saved = yaml.safe_load((OUT / "config-disabled.yaml").read_text())
    norm = dict(cfg)
    norm["native_execution_authorized"] = False
    if norm != saved:
        raise ValueError("Configuration changed beyond admission")
    rec = json.loads((OUT / "preflight-reviewed.json").read_text())
    ps = paths(cfg)
    if {k: sha(v) for k, v in ps.items()} != rec["source_before"] or sha(
        Path(cfg["solver"])
    ) != rec["solver_sha256"]:
        raise ValueError("Source changed")
    for p, h in rec["source_ledger"].items():
        if p != str(CONFIG) and sha(p) != h:
            raise ValueError("Helper changed")
    deck = OUT / "B2.inp"
    if sha(deck) != rec["b2_deck_sha256"]:
        raise ValueError("Prepared deck changed")
    folder = OUT / "native-B2"
    folder.mkdir(exist_ok=False)
    shutil.copyfile(deck, folder / "case.inp")
    from scripts.wo03_g80_bridge_fea import parse_native_dat
    from scripts.wo03_owned_process import darwin_process_callbacks, run_owned

    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    env = dict(os.environ)
    for n in (
        "OMP_NUM_THREADS",
        "CCX_NPROC_EQUATION_SOLVER",
        "CCX_NPROC_RESULTS",
        "CCX_NPROC_STIFFNESS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
    ):
        env[n] = "1"
    rss, desc = darwin_process_callbacks()
    launch = f'import os,resource;resource.setrlimit(resource.RLIMIT_CPU,(120,120));os.execv({cfg["solver"]!r},[{cfg["solver"]!r},"-i","case"])'
    inputs = list(ps.values()) + [Path(cfg["solver"]), deck, Path(__file__).resolve(), CONFIG]
    before = {str(p): sha(p) for p in inputs}
    result = {
        "status": "started",
        "source_before": before,
        "no_actual_or_automatic_continuation": True,
        "strict_force_criterion_N": 1e-5,
        "cause_isolation_only": True,
    }
    try:
        run_owned(
            [sys.executable, "-c", launch],
            log_path=folder / "solver.log",
            status_path=folder / "status.json",
            wall_limit_s=120,
            rss_callback=rss,
            descendants_callback=desc,
            rss_limit_bytes=2147483648,
            cwd=folder,
            env=env,
        )
        log = (folder / "solver.log").read_text(errors="replace").lower()
        if (
            "solving the system of equations using the iterative solver" not in log
            or "cholesky preconditioning" not in log
            or "*error" in log
            or "no convergence" in log
        ):
            raise ValueError("Iterative Cholesky backend or convergence not evidenced")
        meta = json.loads(ps["fixture_meta"].read_text())
        reader = b1_module(cfg)
        assessment = reader.assess_b(
            meta, deck.read_text(), folder / "case.dat", folder / "case.frd"
        )
        if any(x["force_status"] == "fail" for x in assessment["steps"]):
            raise ValueError("Strict force failure")
        for x in assessment["steps"]:
            if x["force_status"] == "unavailable_precision" and any(
                abs(v) > q for v, q in zip(x["force_residual_N"], x["encoding_bound_N"])
            ):
                raise ValueError("Unavailable-precision interval excludes equilibrium")
        consistency = field_consistency(
            meta,
            ps["b1_frd"],
            ps["b1_dat"],
            folder / "case.frd",
            folder / "case.dat",
            reader,
            parse_native_dat,
        )
        result["b1_b2_field_consistency"] = consistency
        if any(
            row["diagnostic_pass"] is False for report in consistency for row in report["nodes"]
        ):
            raise ValueError("B1/B2 local RF diagnostic failed")
        result.update(
            status="cause_isolation_complete_not_qualified",
            assessment=assessment,
            b1_b2_field_consistency=consistency,
            strict_force_aggregate_pass=assessment["strict_force_pass"],
        )
    except Exception as exc:
        result.update(status="stopped", error=repr(exc))
        raise
    finally:
        result["source_after"] = {p: sha(p) for p in before}
        result["source_unchanged"] = result["source_after"] == before
        if not result["source_unchanged"]:
            result.update(status="stopped", error="source changed")
        (folder / "assessment.json").write_text(json.dumps(result, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("prepare", "b2"), default="prepare")
    args = parser.parse_args()
    cfg = yaml.safe_load(CONFIG.read_text())
    sys.path.insert(0, str(ROOT))
    if args.phase == "prepare":
        if OUT.joinpath("config-disabled.yaml").exists():
            raise FileExistsError("preparation already exists")
        OUT.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CONFIG, OUT / "config-disabled.yaml")
        prepare(cfg)
    else:
        run_b2(cfg)


if __name__ == "__main__":
    main()
