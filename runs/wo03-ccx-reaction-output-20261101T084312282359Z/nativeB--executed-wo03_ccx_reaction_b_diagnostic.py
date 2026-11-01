"""One separately authorized B-only CCX reaction diagnostic; no remeshing."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.wo03_ccx_reaction_fixture import assess_native_fixture
from scripts.wo03_owned_process import OwnedProcessError, darwin_process_callbacks, run_owned


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def classify(result):
    """Unavailable printed precision is diagnostic-only; other failures stop."""
    steps = result["steps"]
    if len(steps) != 2 or {r["step"] for r in steps} != {1, 2}:
        raise ValueError("Expected exactly two parsed native steps")
    for step in steps:
        status = step["support_balance"]["force_balance_status"]
        if status not in ("pass", "unavailable_print_precision"):
            raise ValueError(f"Gross force imbalance or invalid precision status: {status}")
        if not all(bar["passed"] for bar in step["free_end"]):
            raise ValueError("Axial displacement accuracy failed")
    return (
        "diagnostic_complete_strict_force_unavailable"
        if any(
            s["support_balance"]["force_balance_status"] == "unavailable_print_precision"
            for s in steps
        )
        else "diagnostic_complete_strict_force_pass"
    )


def packet(out):
    out.mkdir(parents=True, exist_ok=False)
    prior_path = ROOT / "build/wo03-ccx-reaction-native-ab-v1/record.json"
    prior = json.loads(prior_path.read_text())
    if (
        prior["status"] != "stopped"
        or not prior["B_unavailable_if_not_run"]
        or len(prior["cases"]) != 1
    ):
        raise ValueError("Expected original A precision-stop with B unrun")
    cfg_path = ROOT / "configs/studies/wo03-ccx-reaction-fixture.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    ccx = Path(cfg["solver"])
    generator = ROOT / "scripts/wo03_ccx_reaction_fixture.py"
    snapshot = ROOT / ".cache/wo03-ccx-reaction-fixture/preflight-v6-source.py"
    if sha(ccx) != cfg["solver_sha256"] or sha(generator) != sha(snapshot):
        raise ValueError("Pinned binary or generator differs from v6 source")
    original = ROOT / "build/wo03-ccx-reaction-fixture-preflight-v6-b"
    inputs = [original / "case.inp", original / "mesh-meta.json", original / "preflight.json"]
    meta = json.loads(inputs[1].read_text())
    pre = json.loads(inputs[2].read_text())
    if (
        pre["status"] != "pass"
        or meta["case"] != "B"
        or meta["solver_invoked"]
        or max(meta["node_count"], meta["c3d10_count"]) > 5000
    ):
        raise ValueError("B input preflight or node/tet cap invalid")
    sources = [
        Path(__file__).resolve(),
        generator,
        snapshot,
        cfg_path,
        ROOT / "scripts/wo03_g80_bridge_fea.py",
        ROOT / "scripts/wo03_owned_process.py",
        ccx,
        prior_path,
    ]
    before = {str(p): sha(p) for p in sources}
    input_before = {p.name: sha(p) for p in inputs}
    for p in sources[:-2]:
        (out / ("executed-" + p.name)).write_bytes(p.read_bytes())
    folder = out / "B"
    folder.mkdir()
    for p in inputs:
        shutil.copy2(p, folder / p.name)
    if input_before != {p.name: sha(folder / p.name) for p in inputs}:
        raise ValueError("B copied inputs do not match admission hashes")
    record = {
        "status": "started",
        "case": "B",
        "prior_A_packet_sha256": sha(prior_path),
        "replan": "primary selected B only after original packet stopped at A print precision; prior packet remains unchanged",
        "strict_force_limit_N": 1e-5,
        "unavailable_print_precision_is_pass": False,
        "source_before": before,
        "input_sha256_at_admission": input_before,
        "input_hash_scope": "v6 original first hashed at this packet admission; stable original and copy verified through case",
        "case_node_count": meta["node_count"],
        "case_tetrahedron_count": meta["c3d10_count"],
        "case_cpu_limit_s": 10,
        "case_wall_limit_s": 30,
        "solver_invoked": False,
        "native_case_count_including_A": 2,
        "case_C": "unavailable and unexecuted",
        "earlier_setup_cpu": "some earlier attempts unavailable, not zero",
        "engineering_acceptance": False,
    }

    def persist():
        (out / "record.json").write_text(json.dumps(record, indent=2) + "\n")

    persist()
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
    failure = None
    try:
        command = (
            "import os,resource;resource.setrlimit(resource.RLIMIT_CPU,(10,10));os.execv("
            + repr(str(ccx))
            + ",["
            + repr(str(ccx))
            + ",'-i','case'])"
        )
        record["solver_invoked"] = True
        persist()
        record["owned_status"] = run_owned(
            [sys.executable, "-c", command],
            log_path=folder / "solver.log",
            status_path=folder / "owned-status.json",
            wall_limit_s=30,
            rss_callback=rss,
            descendants_callback=children,
            rss_limit_bytes=2147483648,
            cwd=folder,
            env=env,
        )
        log = (folder / "solver.log").read_text(errors="replace")
        record["native_warning_lines"] = [
            line
            for line in log.splitlines()
            if "warning" in line.lower() or "*ERROR" in line.upper()
        ]
        if "*ERROR" in log.upper() or not (folder / "case.dat").is_file():
            raise ValueError("B native output failure")
        if input_before != {p.name: sha(p) for p in inputs} or input_before != {
            p.name: sha(folder / p.name) for p in inputs
        }:
            raise ValueError("B input changed during native execution")
        result = assess_native_fixture(meta, folder / "case.dat")
        for step in result["steps"]:
            for bar in step["free_end"]:
                target = bar["expected_mm"]
                bar["max_relative_error"] = (
                    bar["max_abs_error_mm"] / abs(target) if target else None
                )
        record["result"] = result
        record["status"] = classify(result)
    except (OwnedProcessError, OSError, ValueError, KeyError) as exc:
        failure = f"{type(exc).__name__}: {exc}"
        record["status"] = "stopped"
        record["error"] = failure
    finally:
        path = folder / "owned-status.json"
        if path.exists():
            record["owned_status"] = json.loads(path.read_text())
        record["source_after"] = {str(p): sha(p) for p in sources}
        record["source_unchanged"] = record["source_before"] == record["source_after"]
        persist()
    if failure or not record["source_unchanged"]:
        raise RuntimeError(f'B diagnostic stopped: {failure or "source changed"}')
    print(
        json.dumps(
            {
                "status": record["status"],
                "force_status_by_step": [
                    s["support_balance"]["force_balance_status"] for s in record["result"]["steps"]
                ],
            }
        ),
        flush=True,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    packet(args.output.resolve())


if __name__ == "__main__":
    main()
