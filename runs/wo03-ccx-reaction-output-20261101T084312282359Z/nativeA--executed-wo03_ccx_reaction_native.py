"""Execute the two separately authorized saved A/B reaction fixtures, without remeshing."""

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


def native_packet(out):
    out.mkdir(parents=True, exist_ok=False)
    cfg_path = ROOT / "configs/studies/wo03-ccx-reaction-fixture.yaml"
    cfg = yaml.safe_load(cfg_path.read_text())
    ccx = Path(cfg["solver"])
    if sha(ccx) != cfg["solver_sha256"]:
        raise ValueError("CCX binary hash mismatch")
    generator = ROOT / "scripts/wo03_ccx_reaction_fixture.py"
    snapshot = ROOT / ".cache/wo03-ccx-reaction-fixture/preflight-v6-source.py"
    if sha(generator) != sha(snapshot):
        raise ValueError("Current fixture generator differs from saved v6 source")
    sources = [
        Path(__file__).resolve(),
        generator,
        snapshot,
        cfg_path,
        ROOT / "scripts/wo03_g80_bridge_fea.py",
        ROOT / "scripts/wo03_owned_process.py",
        ccx,
    ]
    source_before = {str(p): sha(p) for p in sources}
    for p in sources[:-1]:
        (out / ("executed-" + p.name)).write_bytes(p.read_bytes())
    env = dict(os.environ)
    for n in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env[n] = "1"
    record = {
        "status": "started",
        "authorized_native_cases": ["A", "B"],
        "case_C": "unavailable: nonnative input moment failed",
        "explicit_authorization": "primary authorized A then B from saved v6 decks; overrides nonnative-only proposal for these two cases only",
        "input_hash_scope": "input files first hashed at admission and checked through copy and execution; no original deck/meta hashes were recorded at v6 generation",
        "source_before": source_before,
        "cases": [],
        "earlier_setup_cpu": "unavailable for some previous attempts; not zero",
        "native_packet_cpu_limit_s": 20,
        "cpu_limit_per_case_s": 10,
        "wall_limit_per_case_s": 30,
        "node_and_tet_caps": 5000,
        "actual_bridge_run": False,
        "strength_acceptance": False,
    }

    def persist():
        (out / "record.json").write_text(json.dumps(record, indent=2) + "\n")

    persist()
    rss, children = darwin_process_callbacks()
    failure = None
    try:
        for case in ("A", "B"):
            original = ROOT / f"build/wo03-ccx-reaction-fixture-preflight-v6-{case.lower()}"
            meta = json.loads((original / "mesh-meta.json").read_text())
            pre = json.loads((original / "preflight.json").read_text())
            if (
                pre["status"] != "pass"
                or meta["case"] != case
                or meta["solver_invoked"]
                or max(meta["node_count"], meta["c3d10_count"]) > 5000
            ):
                raise ValueError(f"{case}: saved nonnative preflight or input cap failed")
            inputs = [
                original / "case.inp",
                original / "mesh-meta.json",
                original / "preflight.json",
            ]
            input_before = {p.name: sha(p) for p in inputs}
            folder = out / case
            folder.mkdir()
            for p in inputs:
                shutil.copy2(p, folder / p.name)
            if input_before != {p.name: sha(folder / p.name) for p in inputs}:
                raise ValueError(f"{case}: copied input hash mismatch")
            row = {
                "case": case,
                "status": "running",
                "input_sha256_at_admission": input_before,
                "solver_invoked": True,
                "node_count": meta["node_count"],
                "tetrahedron_count": meta["c3d10_count"],
            }
            record["cases"].append(row)
            persist()
            command = (
                "import os,resource;resource.setrlimit(resource.RLIMIT_CPU,(10,10));os.execv("
                + repr(str(ccx))
                + ",["
                + repr(str(ccx))
                + ",'-i','case'])"
            )
            try:
                status = run_owned(
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
                row["owned_status"] = status
                log = (folder / "solver.log").read_text(errors="replace")
                row["native_warning_lines"] = [
                    line
                    for line in log.splitlines()
                    if "warning" in line.lower() or "*ERROR" in line.upper()
                ]
                if "*ERROR" in log.upper() or not (folder / "case.dat").is_file():
                    raise ValueError(f"{case}: native output failure")
                if input_before != {p.name: sha(p) for p in inputs} or input_before != {
                    p.name: sha(folder / p.name) for p in inputs
                }:
                    raise ValueError(f"{case}: input changed during native execution")
                outcome = assess_native_fixture(meta, folder / "case.dat")
                for step in outcome["steps"]:
                    for bar in step["free_end"]:
                        target = bar["expected_mm"]
                        bar["max_relative_error"] = (
                            bar["max_abs_error_mm"] / abs(target) if target else None
                        )
                row["result"] = outcome
                if outcome["status"] != "passed":
                    raise ValueError(f"{case}: force/displacement failed or unavailable")
                row["status"] = "passed"
            except (OwnedProcessError, OSError, ValueError, KeyError) as exc:
                row["status"] = "stopped"
                row["error"] = f"{type(exc).__name__}: {exc}"
                if (folder / "owned-status.json").exists():
                    row["owned_status"] = json.loads((folder / "owned-status.json").read_text())
                raise
            finally:
                persist()
        record["status"] = "A_and_B_passed_known_fixtures_only"
    except (OwnedProcessError, OSError, ValueError, KeyError) as exc:
        failure = f"{type(exc).__name__}: {exc}"
        record["status"] = "stopped"
        record["error"] = failure
    finally:
        record["source_after"] = {str(p): sha(p) for p in sources}
        record["source_unchanged"] = record["source_before"] == record["source_after"]
        record["B_unavailable_if_not_run"] = not any(x["case"] == "B" for x in record["cases"])
        persist()
    if failure or not record["source_unchanged"]:
        raise RuntimeError(f'Native packet stopped: {failure or "source changed"}')
    print(
        json.dumps(
            {
                "status": record["status"],
                "cases": [{"case": r["case"], "status": r["status"]} for r in record["cases"]],
            }
        ),
        flush=True,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    native_packet(args.output.resolve())


if __name__ == "__main__":
    main()
