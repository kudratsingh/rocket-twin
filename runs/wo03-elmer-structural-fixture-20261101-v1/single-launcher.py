"""One separately admitted SINGLE continuation; original driver remains frozen."""

from __future__ import annotations

import hashlib
import json
import os
import resource
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.wo03_elmer_structural_fixture import evaluate_vtu
from scripts.wo03_owned_process import darwin_process_callbacks, run_owned

OUT = ROOT / "build/wo03-elmer-structural-fixture-v3"
CONFIG = ROOT / "configs/studies/wo03-elmer-structural-fixture.yaml"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    dest = OUT / "single-continuation"
    dest.mkdir(exist_ok=False)
    rec = {
        "status": "preflight_started",
        "case": "single",
        "original_packet_reclassified": False,
        "equal_rerun": False,
        "rss_scope": "supervised root process only",
        "one_cpu_requested": True,
    }

    def persist():
        (dest / "record.json").write_text(json.dumps(rec, indent=2) + "\n")

    persist()
    try:
        cfg = yaml.safe_load(CONFIG.read_text())
        assert cfg["native_execution_authorized"] is False
        review = json.loads((OUT / "preflight-reviewed.json").read_text())
        pre = json.loads((OUT / "prepared/record.json").read_text())
        original = json.loads((OUT / "native/record.json").read_text())
        equal = json.loads((OUT / "readonly-equal-result.json").read_text())
        restore = json.loads((OUT / "restoration.json").read_text())
        assert (
            original["status"] == "stopped"
            and equal["status"] == "completed_readonly_not_retroactive_pass"
            and equal["result"]["force_status"] == "pass"
            and equal["source_unchanged"]
            and restore["restored_matches_original_disabled"]
        )
        paths = {
            k: ROOT / cfg[k]
            for k in ("solver", "module", "fixture_deck", "fixture_metadata", "fixture_mesh")
        }
        before = {k: sha(p) for k, p in paths.items()}
        assert before == pre["input_sha256"]
        for p, h in review["source_ledger"].items():
            if sha(Path(p)) != h:
                raise ValueError("Pinned source differs: " + p)
        for p, h in pre["generated_sha256"].items():
            if sha(ROOT / p) != h:
                raise ValueError("Prepared input changed: " + p)
        prefix = ROOT / ".cache/elmer-evaluation/setup-v1/prefix"
        inv = lambda: {str(p): sha(p) for p in prefix.rglob("*") if p.is_file()}
        assert inv() == review["prefix_sha256"]
        probe = json.loads(
            (
                ROOT / ".cache/elmer-evaluation/structural-module-v1/build-attempt/record.json"
            ).read_text()
        )
        runtime = {
            p: v["sha256"] for p, v in probe["runtime_dependencies"].items() if v.get("sha256")
        }
        if any(sha(Path(p)) != h for p, h in runtime.items()):
            raise ValueError("Runtime dependency changed")
        inputs = [
            CONFIG,
            Path(__file__).resolve(),
            OUT / "preflight-reviewed.json",
            OUT / "native/record.json",
            OUT / "readonly-equal-result.json",
            OUT / "restoration.json",
            *paths.values(),
        ]
        rec["source_before"] = {str(p): sha(p) for p in inputs}
        rec["source_ledger_before"] = review["source_ledger"]
        rec["runtime_before"] = runtime
        rec["prefix_before"] = review["prefix_sha256"]
        rec["generated_before"] = pre["generated_sha256"]
        rec["status"] = "preflight_pass_no_native_yet"
        persist()
        (dest / "preflight.json").write_text(
            json.dumps(
                {
                    "status": "pass",
                    "source_before": rec["source_before"],
                    "source_ledger": rec["source_ledger_before"],
                    "generated": rec["generated_before"],
                    "prefix": rec["prefix_before"],
                    "runtime": runtime,
                },
                indent=2,
            )
            + "\n"
        )
        admission = {
            "status": "primary_admitted_one_single_continuation",
            "equal_rerun": False,
            "native_case_limit": 1,
            "config_remains_disabled_sha256": sha(CONFIG),
            "original_packet_sha256": sha(OUT / "native/record.json"),
            "readonly_equal_sha256": sha(OUT / "readonly-equal-result.json"),
            "launcher_sha256": sha(Path(__file__).resolve()),
            "preflight_sha256": sha(dest / "preflight.json"),
            "case_cpu_wall_s": 120,
            "parent_cpu_s": 120,
            "root_rss_bytes": 2147483648,
        }
        (dest / "primary-admission.json").write_text(json.dumps(admission, indent=2) + "\n")
        shutil.copyfile(CONFIG, dest / "as-run-disabled-config.yaml")
        folder = dest / "single"
        shutil.copytree(OUT / "prepared/cases/single", folder)
        for p in (OUT / "prepared/cases/single").rglob("*"):
            if p.is_file() and sha(p) != sha(folder / p.relative_to(OUT / "prepared/cases/single")):
                raise ValueError("Copied case mismatch")
        resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
        env = dict(os.environ)
        for n in (
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        ):
            env[n] = "1"
        env["ELMER_HOME"] = str(prefix.resolve())
        env["ELMER_LIB"] = str((prefix / "share/elmersolver/lib").resolve())
        rss, desc = darwin_process_callbacks()
        cmd = (
            "import os,resource;resource.setrlimit(resource.RLIMIT_CPU,(120,120));os.execv("
            + repr(str(paths["solver"]))
            + ",["
            + repr(str(paths["solver"]))
            + ',"case.sif"])'
        )
        st = run_owned(
            [sys.executable, "-c", cmd],
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
        rec["ignored_exact_unused_keyword_count"] = sum(
            line.strip().lower() == unused for line in lines
        )
        for line in lines:
            lower = line.strip().lower()
            if lower == unused:
                continue
            if "fatal:" in lower or "error:" in lower or "not converged" in lower:
                raise ValueError("Solver failure text: " + line)
        log = "\n".join(lines).lower()
        if (
            "directsolver: using direct method: umfpack" not in log
            or "elmer solver: all done" not in log
        ):
            raise ValueError("Direct solver completion not evidenced")
        rec["unused_iterative_settings"] = (
            "reported unused by direct UMFPACK; no iterative convergence claim"
        )
        files = [
            p for p in (folder / "field_t0001.vtu", folder / "mesh/field_t0001.vtu") if p.is_file()
        ]
        if len(files) != 1:
            raise ValueError("Missing or ambiguous VTU")
        result = evaluate_vtu(
            files[0], json.loads(paths["fixture_metadata"].read_text()), (150.0, 0.0, 0.0)
        )
        rec["result"] = result
        if result["force_status"] != "pass":
            raise ValueError("Strict force unavailable or failed")
        rec["status"] = "single_known_answer_pass_not_qualified"
    except Exception as e:
        rec.update(status="stopped", error=repr(e))
        raise
    finally:
        if "inputs" in locals():
            rec["source_after"] = {str(p): sha(p) for p in inputs}
            rec["source_unchanged"] = rec["source_after"] == rec["source_before"]
            rec["prefix_unchanged"] = inv() == review["prefix_sha256"]
            rec["generated_unchanged"] = all(
                sha(ROOT / p) == h for p, h in pre["generated_sha256"].items()
            )
            rec["runtime_unchanged"] = all(sha(Path(p)) == h for p, h in runtime.items())
            rec["source_ledger_unchanged"] = all(
                sha(Path(p)) == h for p, h in review["source_ledger"].items()
            )
            if not all(
                rec[k]
                for k in (
                    "source_unchanged",
                    "prefix_unchanged",
                    "generated_unchanged",
                    "runtime_unchanged",
                    "source_ledger_unchanged",
                )
            ):
                rec.update(status="stopped", error="Source or dependency changed")
        usage = resource.getrusage(resource.RUSAGE_SELF)
        rec["parent_cpu_s"] = usage.ru_utime + usage.ru_stime
        rec["parent_peak_rss_bytes"] = usage.ru_maxrss
        persist()


if __name__ == "__main__":
    main()
