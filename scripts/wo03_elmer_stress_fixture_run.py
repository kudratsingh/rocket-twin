"""One gated known-case execution; default is read-only verification."""

import argparse
import json
import os
import resource
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.wo03_elmer_stress_fixture import CONFIG, sha
from scripts.wo03_elmer_stress_fixture_reader import read_stress
from scripts.wo03_elmer_structural_fixture import evaluate_vtu
from scripts.wo03_owned_process import darwin_process_callbacks, run_owned

OUT = ROOT / "build/wo03-elmer-stress-fixture-v2"


def verify():
    ledger = json.loads((OUT / "reviewed-ledger.json").read_text())
    for p, digest in ledger["files"].items():
        if sha(p) != digest:
            raise ValueError("Changed source/input: " + p)
    review = json.loads(
        (ROOT / "build/wo03-elmer-nodal-fixture-v1/preflight-reviewed.json").read_text()
    )
    for group in ("source_ledger", "baseline_fixture_source_ledger", "observed_runtime_sha256"):
        for p, digest in review[group].items():
            if Path(p) == ROOT / "scripts/wo03_owned_process.py":
                continue  # separately pinned 50 ms supervisor update
            if sha(p) != digest:
                raise ValueError("Changed known-fixture dependency: " + p)
    prefix = ROOT / ".cache/elmer-evaluation/setup-v1/prefix"
    inventory = {str(p): sha(p) for p in prefix.rglob("*") if p.is_file()}
    if inventory != review["prefix_sha256"]:
        raise ValueError("Prefix changed")
    return ledger


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    cfg = yaml.safe_load(CONFIG.read_text())
    if not args.execute:
        if cfg != yaml.safe_load((OUT / "config-disabled.yaml").read_text()):
            raise ValueError("Disabled configuration changed")
        verify()
        print("verified; native execution disabled")
        return
    if not cfg["native_execution_authorized"]:
        raise ValueError("Native execution not authorized")
    # Authorized configuration must be identical to the frozen disabled snapshot.
    cfg["native_execution_authorized"] = False
    frozen = yaml.safe_load((OUT / "config-disabled.yaml").read_text())
    if cfg != frozen:
        raise ValueError("Other config changes not authorized")
    # The config is intentionally excluded from the ledger during its flag-only admission.
    verify()
    dest = OUT / "native"
    dest.mkdir(exist_ok=False)
    rec = {
        "status": "started",
        "qualification": False,
        "one_cpu_requested": True,
        "rss_scope": "root process only",
    }

    def persist():
        u = resource.getrusage(resource.RUSAGE_SELF)
        rec["parent_cpu_s"] = u.ru_utime + u.ru_stime
        rec["parent_peak_rss_bytes"] = u.ru_maxrss
        (dest / "record.json").write_text(json.dumps(rec, indent=2) + "\n")

    try:
        resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
        folder = dest / "case"
        shutil.copytree(OUT / "prepared", folder)
        for p in (OUT / "prepared").rglob("*"):
            if p.is_file() and sha(p) != sha(folder / p.relative_to(OUT / "prepared")):
                raise ValueError("Copied input changed")
        env = dict(os.environ)
        for n in (
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        ):
            env[n] = "1"
        prefix = ROOT / ".cache/elmer-evaluation/setup-v1/prefix"
        env["ELMER_HOME"] = str(prefix)
        env["ELMER_LIB"] = str(prefix / "share/elmersolver/lib")
        solver = prefix / "bin/ElmerSolver"
        command = (
            "import os,resource;resource.setrlimit(resource.RLIMIT_CPU,(120,120));os.execv("
            + repr(str(solver))
            + ",["
            + repr(str(solver))
            + ',"case.sif"])'
        )
        rss, desc = darwin_process_callbacks()
        st = run_owned(
            [sys.executable, "-c", command],
            log_path=folder / "solver.log",
            status_path=folder / "status.json",
            wall_limit_s=120,
            rss_callback=rss,
            descendants_callback=desc,
            rss_limit_bytes=2147483648,
            cwd=folder,
            env=env,
        )
        rec["native_status"] = st
        lines = (folder / "solver.log").read_text(errors="replace").splitlines()
        unused = "solver 1              linear system abort not converged"
        rec["ignored_exact_unused_keyword_count"] = sum(x.strip().lower() == unused for x in lines)
        for line in lines:
            x = line.strip().lower()
            if x != unused and ("fatal:" in x or "error:" in x or "not converged" in x):
                raise ValueError("Native error: " + line)
        log = "\n".join(lines).lower()
        if (
            "directsolver: using direct method: umfpack" not in log
            or "elmer solver: all done" not in log
        ):
            raise ValueError("Direct completion missing")
        found = [
            p for p in (folder / "field_t0001.vtu", folder / "mesh/field_t0001.vtu") if p.is_file()
        ]
        if len(found) != 1:
            raise ValueError("VTU missing or ambiguous")
        meta = json.loads(
            (ROOT / "build/wo03-ccx-reaction-fixture-preflight-v6-b/mesh-meta.json").read_text()
        )
        rec["displacement_force"] = evaluate_vtu(found[0], meta, (150.0, 0.0, 0.0))
        if rec["displacement_force"]["force_status"] != "pass":
            raise ValueError("Strict force unavailable or failed")
        rec["stress"] = read_stress(found[0], meta)
        if (
            not rec["stress"]["original_axial_criterion_pass"]
            or not rec["stress"]["all_components_primary_2pct_scale_pass"]
        ):
            raise ValueError("Stress criterion failed")
        rec["status"] = "known_case_pass_not_qualified"
    except Exception as exc:  # noqa: BLE001
        rec.update(status="stopped", error=repr(exc))
    finally:
        try:
            verify()
            rec["sources_prefix_unchanged"] = True
        except Exception as exc:  # noqa: BLE001
            rec.update(status="stopped", sources_prefix_unchanged=False, postcheck_error=repr(exc))
        persist()


if __name__ == "__main__":
    main()
