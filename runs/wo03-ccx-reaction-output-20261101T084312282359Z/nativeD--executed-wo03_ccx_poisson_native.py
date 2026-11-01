"""One primary-authorized native D reaction diagnostic; no remesh."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.wo03_ccx_poisson_diagnostic import assess_saved_output, modified_deck
from scripts.wo03_owned_process import OwnedProcessError, darwin_process_callbacks, run_owned


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def classify(result):
    steps = result["steps"]
    if len(steps) != 2 or {s["step"] for s in steps} != {1, 2}:
        raise ValueError("Expected exactly two output steps")
    unavailable = False
    for step in steps:
        statuses = [
            step["total_reaction_plus_applied_from_all_RF"]["force_balance_status"],
            step["bottom_support_rf_z_status"],
        ]
        if any(s not in ("pass", "unavailable_print_precision") for s in statuses):
            raise ValueError("Gross reaction imbalance or invalid balance status")
        if not all(x["displacement_pass"] for x in step["bars"]):
            raise ValueError("Displacement reference failure")
        unavailable |= "unavailable_print_precision" in statuses
    return (
        "diagnostic_complete_strict_force_unavailable"
        if unavailable
        else "diagnostic_complete_strict_force_pass"
    )


def packet(out):
    out.mkdir(parents=True, exist_ok=False)
    cfg_path = ROOT / "configs/studies/wo03-ccx-poisson-diagnostic.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    prepared = ROOT / "build/wo03-ccx-poisson-diagnostic-v1"
    pre = json.loads((prepared / "preflight.json").read_text())
    original = ROOT / cfg["source_case"]
    admission = ROOT / cfg["source_admission_record"]
    a_record = ROOT / "build/wo03-ccx-reaction-native-ab-v1/record.json"
    b_record = admission
    a = json.loads(a_record.read_text())
    b = json.loads(b_record.read_text())
    if (
        pre["status"] != "prepared_no_solver"
        or pre["solver_invoked"]
        or a["status"] != "stopped"
        or not a["B_unavailable_if_not_run"]
        or b["case"] != "B"
        or not b["source_unchanged"]
    ):
        raise ValueError("Prior fixture or D preparation state invalid")
    if b["status"] not in (
        "diagnostic_complete_strict_force_unavailable",
        "diagnostic_complete_strict_force_pass",
    ):
        raise ValueError("Prior B diagnostic not completed")
    if sha(admission) != pre["source_B_admission_record_sha256"]:
        raise ValueError("B admission record changed")
    for name, want in pre["source_B_input_sha256"].items():
        if sha(original / name) != want:
            raise ValueError(f"B admitted input changed: {name}")
    if sha(prepared / "case.inp") != pre["modified_deck_sha256"] or (
        prepared / "case.inp"
    ).read_bytes() != modified_deck((original / "case.inp").read_bytes()):
        raise ValueError("Prepared D deck changed from approved byte edits")
    meta = json.loads((prepared / "mesh-meta.json").read_text())
    if (
        meta != json.loads((original / "mesh-meta.json").read_text())
        or max(meta["node_count"], meta["c3d10_count"]) > 5000
    ):
        raise ValueError("D source mesh metadata or cap changed")
    for name, want in pre["preparation_source_sha256_before"].items():
        if sha(name) != want:
            raise ValueError(f"D preparation source changed: {name}")
    ccx = Path(cfg["solver"])
    if (
        sha(ccx) != cfg["solver_sha256"]
        or cfg["planned_native_cpu_s"] != 10
        or cfg["planned_native_wall_s"] != 30
        or cfg["prior_native_cases_executed"] != 2
    ):
        raise ValueError("Pinned solver or authorized fixture cap changed")
    files = [
        Path(__file__).resolve(),
        cfg_path,
        ROOT / "scripts/wo03_ccx_poisson_diagnostic.py",
        ROOT / "scripts/wo03_g80_bridge_fea.py",
        ROOT / "scripts/wo03_ccx_reaction_fixture.py",
        ROOT / "scripts/wo03_owned_process.py",
        prepared / "preflight.json",
        prepared / "case.inp",
        prepared / "mesh-meta.json",
        original / "case.inp",
        original / "mesh-meta.json",
        original / "preflight.json",
        a_record,
        b_record,
        ccx,
    ]
    before = {str(p): sha(p) for p in files}
    case = out / "D"
    case.mkdir()
    for name in ("case.inp", "mesh-meta.json", "preflight.json"):
        shutil.copy2(prepared / name, case / name)
    if any(
        sha(prepared / name) != sha(case / name)
        for name in ("case.inp", "mesh-meta.json", "preflight.json")
    ):
        raise ValueError("D copied inputs differ")
    for p in files[:6]:
        (out / ("executed-" + p.name)).write_bytes(p.read_bytes())
    record = {
        "status": "started",
        "case": "D",
        "native_authorization": "primary explicitly authorized D only; overrides prepare-only proposal for one case",
        "source_before": before,
        "prior_cases": "A and B executed; C never executed",
        "native_fixture_slot": 3,
        "node_count": meta["node_count"],
        "tetrahedron_count": meta["c3d10_count"],
        "case_cpu_limit_s": 10,
        "case_wall_limit_s": 30,
        "threads_requested": 1,
        "strict_force_limit_N": 1e-5,
        "earlier_setup_cpu": "some earlier setup unavailable, not zero",
        "actual_bridge": False,
        "acceptance": False,
        "launch_attempted": False,
        "elmer_or_ccx_banner_observed": False,
    }

    def persist():
        (out / "record.json").write_text(json.dumps(record, indent=2) + "\n")

    persist()
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
        cmd = (
            "import os,resource;resource.setrlimit(resource.RLIMIT_CPU,(10,10));os.execv("
            + repr(str(ccx))
            + ",["
            + repr(str(ccx))
            + ",'-i','case'])"
        )
        record["launch_attempted"] = True
        persist()
        record["owned_status"] = run_owned(
            [sys.executable, "-c", cmd],
            log_path=case / "solver.log",
            status_path=case / "owned-status.json",
            wall_limit_s=30,
            rss_callback=rss,
            descendants_callback=children,
            rss_limit_bytes=2147483648,
            cwd=case,
            env=env,
        )
        log = (case / "solver.log").read_text(errors="replace")
        record["elmer_or_ccx_banner_observed"] = (
            "CALCULIX" in log.upper() or (case / "case.dat").is_file()
        )
        record["native_warning_lines"] = [
            line
            for line in log.splitlines()
            if "WARNING" in line.upper() or "*ERROR" in line.upper()
        ]
        record["solver_summary_constraint_lines"] = [
            line.strip()
            for line in log.splitlines()
            if re.search(r"constraints|terms in all multiple point", line, re.IGNORECASE)
        ]
        if "*ERROR" in log.upper() or not (case / "case.dat").is_file():
            raise ValueError("D solver failure or output missing")
        if any(
            sha(prepared / name) != sha(case / name)
            for name in ("case.inp", "mesh-meta.json", "preflight.json")
        ):
            raise ValueError("D copied input changed during execution")
        result = assess_saved_output(meta, case / "case.inp", case / "case.dat")
        record["result"] = result
        record["status"] = classify(result)
    except (OwnedProcessError, OSError, ValueError, KeyError) as exc:
        failure = f"{type(exc).__name__}: {exc}"
        record["status"] = "stopped"
        record["error"] = failure
    finally:
        path = case / "owned-status.json"
        if path.exists():
            record["owned_status"] = json.loads(path.read_text())
        logpath = case / "solver.log"
        if logpath.exists() and "solver_summary_constraint_lines" not in record:
            log = logpath.read_text(errors="replace")
            record["elmer_or_ccx_banner_observed"] = (
                "CALCULIX" in log.upper() or (case / "case.dat").is_file()
            )
            record["solver_summary_constraint_lines"] = [
                line.strip()
                for line in log.splitlines()
                if re.search(r"constraints|terms in all multiple point", line, re.IGNORECASE)
            ]
        record["source_after"] = {str(p): sha(p) for p in files}
        record["source_unchanged"] = before == record["source_after"]
        persist()
    if failure or not record["source_unchanged"]:
        raise RuntimeError(f'D diagnostic stopped: {failure or "source changed"}')
    print(
        json.dumps(
            {
                "status": record["status"],
                "steps": [
                    {
                        "step": s["step"],
                        "all_RF": s["total_reaction_plus_applied_from_all_RF"][
                            "force_balance_status"
                        ],
                        "bottom_z": s["bottom_support_rf_z_status"],
                    }
                    for s in record["result"]["steps"]
                ],
            }
        )
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    packet(args.output.resolve())


if __name__ == "__main__":
    main()
