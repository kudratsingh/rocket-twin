"""Isolated one-module Elmer build, disabled until explicit admission."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-elmer-structural-module.yaml"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def inventory(folder):
    return {
        str(p.relative_to(ROOT)): {
            "sha256": sha(p),
            "symlink": str(p.readlink()) if p.is_symlink() else None,
        }
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


def assignment(text, name):
    matches = [
        line.split("=", 1)[1].strip() for line in text.splitlines() if line.startswith(name + " =")
    ]
    if len(matches) != 1:
        raise ValueError("Unexpected generated flags: " + name)
    return shlex.split(matches[0])


def prepare_initial():
    cfg = yaml.safe_load(CONFIG.read_text())
    base = ROOT / cfg["setup_root"]
    out = ROOT / cfg["output_root"]
    build = base / "build"
    prefix = base / "prefix"
    old_module = build / "fem/src/modules"
    meta = old_module / "CMakeFiles/HeatSolve.dir"
    if (
        cfg["native_build_authorized"]
        or cfg["prior_setup_wall_s"] + cfg["new_setup_reserve_wall_s"] + cfg["worker_cpu_wall_s"]
        > cfg["original_setup_ceiling_wall_s"]
    ):
        raise ValueError("Authorization or setup budget invalid")
    source = (
        base / "elmerfem" / ("elmerfem-" + cfg["source_commit"]) / "fem/src/modules/StressSolve.F90"
    )
    flags = (meta / "flags.make").read_text()
    link = shlex.split((meta / "link.txt").read_text())
    cache = (build / "CMakeCache.txt").read_text()
    if (
        "INCLUDE_ELMER_MODULES:STRING=HeatSolve;HeatSolveVec;FluxSolver;ResultOutputSolve;SaveData"
        not in cache
    ):
        raise ValueError("Unexpected original module allowlist")
    if (
        "CMAKE_Fortran_COMPILER:STRING=/opt/homebrew/bin/gfortran" not in cache
        or "CMAKE_Fortran_FLAGS_RELEASE:STRING=-O1 -DNDEBUG" not in cache
    ):
        raise ValueError("Unexpected compiler or build flags")
    defs = assignment(flags, "Fortran_DEFINES")
    incs = assignment(flags, "Fortran_INCLUDES")
    opts = assignment(flags, "Fortran_FLAGS")
    if defs.count("-DHeatSolve_EXPORTS") != 1 or sum(x.startswith("-J") for x in opts) != 1:
        raise ValueError("Unexpected module flags")
    defs[defs.index("-DHeatSolve_EXPORTS")] = "-DStressSolve_EXPORTS"
    fmods = out / "work/fmodules"
    obj = out / "work/StressSolve.F90.o"
    dylib = out / "work/StressSolve.dylib"
    opts = [("-J" + str(fmods)) if x.startswith("-J") else x for x in opts]
    compile_cmd = [
        "/opt/homebrew/bin/gfortran",
        *defs,
        *incs,
        "-I" + str(build / "fmodules"),
        *opts,
        "-c",
        str(source),
        "-o",
        str(obj),
    ]
    if (
        link[0] != "/opt/homebrew/bin/gfortran"
        or link.count("HeatSolve.dylib") != 1
        or link.count("CMakeFiles/HeatSolve.dir/HeatSolve.F90.o") != 1
    ):
        raise ValueError("Unexpected original linker command")
    link[link.index("HeatSolve.dylib")] = str(dylib)
    link[link.index("@rpath/HeatSolve.dylib")] = "@rpath/StressSolve.dylib"
    link[link.index("CMakeFiles/HeatSolve.dir/HeatSolve.F90.o")] = str(obj)
    for i, x in enumerate(link):
        if x.startswith("../"):
            link[i] = str((old_module / x).resolve())
    # Makefile is a proposal only. make -n must later show exactly these two
    # recipes, no other target or install; it is never invoked here.
    out.mkdir(parents=True, exist_ok=True)
    snapshot = out / "metadata-snapshot"
    snapshot.mkdir(exist_ok=False)
    metadata = [
        build / "CMakeCache.txt",
        build / "Makefile",
        meta / "flags.make",
        meta / "link.txt",
        meta / "build.make",
        meta / "DependInfo.cmake",
    ]
    for i, p in enumerate(metadata):
        shutil.copyfile(p, snapshot / f"{i:02d}-{p.name}")
    manifest = {
        "status": "prepared_blocked_tree_cpu_guard",
        "native_build_authorized": False,
        "source_before": inventory(base / "elmerfem"),
        "original_build_before": inventory(build),
        "original_prefix_before": inventory(prefix),
        "metadata_original_to_snapshot": {
            str(p.relative_to(ROOT)): str((snapshot / f"{i:02d}-{p.name}").relative_to(ROOT))
            for i, p in enumerate(metadata)
        },
        "tools": {},
        "planned_commands": {"compile": compile_cmd, "link": link},
        "blocker": "Existing owned runner samples optional CPU data but does not enforce cumulative CPU over gfortran/f951/assembler/linker tree; a validated tree CPU ceiling is required before authorization.",
        "limits": cfg,
        "result": "No configure, make, compiler, linker, install, module load or solver executed.",
    }
    tools = [
        Path("/opt/homebrew/bin/gfortran"),
        Path("/opt/homebrew/Cellar/gcc/16.2.0/libexec/gcc/aarch64-apple-darwin27/16/f951"),
        Path("/usr/bin/make"),
        Path("/usr/bin/otool"),
        Path("/usr/bin/nm"),
        Path("/Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk/SDKSettings.json"),
        base / "cmake/cmake-3.31.8-macos-universal/CMake.app/Contents/bin/cmake",
        Path(__file__).resolve(),
        CONFIG,
        ROOT / "scripts/wo03_owned_process.py",
    ]
    manifest["tools"] = {str(p): sha(p) for p in tools}
    makefile = (
        "all: "
        + shlex.quote(str(dylib))
        + "\n\n"
        + shlex.quote(str(obj))
        + ":\n\t"
        + shlex.join(compile_cmd)
        + "\n\n"
        + shlex.quote(str(dylib))
        + ": "
        + shlex.quote(str(obj))
        + "\n\t"
        + shlex.join(link)
        + "\n"
    )
    (out / "Makefile.proposed").write_text(makefile)
    (out / "preflight.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "source_files": len(manifest["source_before"]),
                "build_files": len(manifest["original_build_before"]),
                "prefix_files": len(manifest["original_prefix_before"]),
            }
        )
    )


def verify_frozen(cfg):
    out = ROOT / cfg["output_root"]
    base = ROOT / cfg["setup_root"]
    ledger = json.loads((out / "preflight-v3.json").read_text())
    frozen = yaml.safe_load((out / "config-disabled-v3.yaml").read_text())
    normalized = dict(cfg)
    normalized["native_build_authorized"] = False
    if not cfg["native_build_authorized"] or normalized != frozen:
        raise ValueError("Build disabled or configuration changed beyond admission")
    for path, digest in ledger["frozen_files"].items():
        if path == str(CONFIG):
            continue
        if sha(Path(path)) != digest:
            raise ValueError("Frozen source or tool changed: " + path)
    prior = json.loads((out / "preflight.json").read_text())
    for k, sub in (
        ("source_before", "elmerfem"),
        ("original_build_before", "build"),
        ("original_prefix_before", "prefix"),
    ):
        if inventory(base / sub) != prior[k]:
            raise ValueError("Original " + sub + " inventory changed")
    return prior, ledger


def launch_guarded(cfg):
    if not cfg["native_build_authorized"]:
        raise ValueError("Build is disabled; no configure or compile was run")
    sys.path.insert(0, str(ROOT))
    from scripts.wo03_owned_process import darwin_process_callbacks, run_owned

    out = ROOT / cfg["output_root"]
    attempt = out / "build-attempt"
    attempt.mkdir(exist_ok=False)
    (attempt / "admission.json").write_text(
        json.dumps(
            {
                "config_sha256": sha(CONFIG),
                "preflight_v3_sha256": sha(out / "preflight-v3.json"),
                "worker_wall_s": 90,
                "whole_wall_s": 100,
                "native_build_authorized": True,
            },
            indent=2,
        )
        + "\n"
    )
    env = dict(os.environ)
    for n in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env[n] = "1"
    rss, desc = darwin_process_callbacks()
    run_owned(
        [sys.executable, str(Path(__file__).resolve()), "--phase", "controller"],
        log_path=attempt / "controller.log",
        status_path=attempt / "controller-status.json",
        wall_limit_s=100,
        rss_callback=rss,
        descendants_callback=desc,
        rss_limit_bytes=2147483648,
        cwd=ROOT,
        env=env,
    )
    result = json.loads((attempt / "record.json").read_text())
    if result["status"] != "module_built_symbol_loaded_not_qualified":
        raise ValueError("Controller did not complete: " + str(result.get("error")))


def controller(cfg):
    sys.path.insert(0, str(ROOT))
    from scripts.wo03_owned_process import darwin_process_callbacks, run_owned

    out = ROOT / cfg["output_root"]
    base = ROOT / cfg["setup_root"]
    attempt = out / "build-attempt"
    start = time.monotonic()
    result = {
        "status": "started",
        "aggregate_cpu_s": None,
        "aggregate_cpu_basis": "unavailable; full compiler-tree attribution not independently verified",
        "native_solver_invoked": False,
    }

    def persist():
        (attempt / "record.json").write_text(json.dumps(result, indent=2) + "\n")

    persist()
    try:
        if not (attempt / "admission.json").is_file():
            raise ValueError("Missing admitted outer controller")
        prior, ledger = verify_frozen(cfg)
        work = out / "work"
        work.mkdir(exist_ok=False)
        (work / "fmodules").mkdir()
        makefile = out / "Makefile.proposed"
        # Captured dry run: exactly two audited recipe lines, no configure or install.
        dry = subprocess.run(
            ["/usr/bin/make", "-n", "-j1", "-f", str(makefile)],
            cwd=out,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        (attempt / "dry-run.stdout").write_text(dry.stdout)
        (attempt / "dry-run.stderr").write_text(dry.stderr)
        if dry.returncode != 0:
            raise ValueError("Make dry run failed")
        commands = [shlex.split(line) for line in dry.stdout.splitlines() if line.strip()]
        expected = [prior["planned_commands"]["compile"], prior["planned_commands"]["link"]]
        if commands != expected:
            raise ValueError("Dry-run contains different, missing or extra commands")
        if time.monotonic() - start >= 10:
            raise TimeoutError("Setup consumed 10 s before compiler launch")
        env = dict(os.environ)
        for n in (
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        ):
            env[n] = "1"
        launch = (
            "import os,resource;resource.setrlimit(resource.RLIMIT_CPU,(90,90));os.execv('/usr/bin/make',['/usr/bin/make','-j1','-f',"
            + repr(str(makefile))
            + "])"
        )
        rss, desc = darwin_process_callbacks()
        status = run_owned(
            [sys.executable, "-c", launch],
            log_path=attempt / "build.log",
            status_path=attempt / "build-status.json",
            wall_limit_s=90,
            rss_callback=rss,
            descendants_callback=desc,
            rss_limit_bytes=2147483648,
            cwd=out,
            env=env,
        )
        result["build_status"] = status
        accounting = status.get("cpu_accounting", {})
        if accounting.get("children_rusage_sampled_after_reap"):
            result["reaped_child_cpu_s"] = accounting.get("child_user_s_delta", 0) + accounting.get(
                "child_system_s_delta", 0
            )
            result["reaped_child_cpu_basis"] = (
                "direct child rusage as reported by owned supervisor; grandchild attribution not independently verified"
            )
        # The source and entire original build/prefix remain immutable.
        for key, sub in (
            ("source_before", "elmerfem"),
            ("original_build_before", "build"),
            ("original_prefix_before", "prefix"),
        ):
            if inventory(base / sub) != prior[key]:
                raise ValueError("Original " + sub + " changed")
        for path, digest in ledger["frozen_files"].items():
            if path != str(CONFIG) and sha(Path(path)) != digest:
                raise ValueError("Source/tool changed")
        lib = work / "StressSolve.dylib"
        obj = work / "StressSolve.F90.o"
        if (
            not obj.is_file()
            or not lib.is_file()
            or not obj.stat().st_size
            or not lib.stat().st_size
        ):
            raise ValueError("Missing output artifact")
        inspections = {}
        for label, argv in (
            ("dependencies", ["/usr/bin/otool", "-L", str(lib)]),
            ("load_commands", ["/usr/bin/otool", "-l", str(lib)]),
            ("exports", ["/usr/bin/nm", "-gU", str(lib)]),
        ):
            completed = subprocess.run(argv, capture_output=True, text=True, timeout=5, check=True)
            inspections[label] = completed.stdout
            (attempt / (label + ".txt")).write_text(completed.stdout)
        if not any(
            line.split() and line.split()[-1] in ("_stresssolver_", "stresssolver_")
            for line in inspections["exports"].splitlines()
        ):
            raise ValueError("StressSolver export missing")
        artifacts = out / "artifacts"
        artifacts.mkdir(exist_ok=False)
        dest = artifacts / "StressSolve.dylib"
        shutil.copyfile(lib, dest)
        # Observe dyld's actual load list: nested LC_RPATH resolution is not
        # inferred from the top-level link flags or treated as a proved path.
        probe = "import ctypes,sys; x=ctypes.CDLL(sys.argv[1]); getattr(x,'stresssolver_'); print('symbol-load-ok')"
        probe_env = dict(env)
        probe_env["DYLD_PRINT_LIBRARIES"] = "1"
        res = subprocess.run(
            [sys.executable, "-c", probe, str(dest)],
            capture_output=True,
            text=True,
            timeout=5,
            env=probe_env,
            check=False,
        )
        (attempt / "probe.stdout").write_text(res.stdout)
        (attempt / "probe.stderr").write_text(res.stderr)
        if res.returncode != 0 or res.stdout.strip() != "symbol-load-ok":
            raise ValueError("Unexpected load probe output")
        observed = []
        for line in res.stderr.splitlines():
            match = re.search(r"(/[^\s]+)", line)
            if match and "dyld" in line.lower():
                observed.append(match.group(1))
        if str(dest.resolve()) not in {str(Path(x).resolve()) for x in observed}:
            raise ValueError("Loader log did not identify the tested module")
        direct = [
            line.strip().split(" (", 1)[0] for line in inspections["dependencies"].splitlines()[1:]
        ]
        required = {
            Path(x).name
            for x in direct
            if x.startswith("@rpath/") and x != "@rpath/StressSolve.dylib"
        }
        by_name = {}
        for item in observed:
            by_name.setdefault(Path(item).name, set()).add(str(Path(item).resolve()))
        if any(name not in by_name or len(by_name[name]) != 1 for name in required):
            raise ValueError("Direct @rpath dependencies not uniquely observed in dyld log")
        dependencies = {}
        for item in sorted(set(observed)):
            path = Path(item)
            if path.is_file():
                dependencies[item] = {
                    "path": str(path.resolve()),
                    "sha256": sha(path),
                    "basis": "observed dyld load",
                }
            elif item.startswith(("/usr/lib/", "/System/Library/")):
                dependencies[item] = {
                    "sha256": None,
                    "reason": "observed system shared-cache path not independently hashable as a file",
                }
            else:
                raise ValueError("Observed non-system load is not hashable: " + item)
        result["runtime_dependencies"] = dependencies
        result["dependency_scope"] = (
            "Paths observed in this probe's dyld load log only; not a claim about other loader configurations."
        )
        result.update(
            status="module_built_symbol_loaded_not_qualified",
            artifact_sha256=sha(dest),
            load_probe=res.stdout.strip(),
        )
    except Exception as e:
        result.update(status="stopped", error=repr(e))
        raise
    finally:
        if "prior" in locals():
            try:
                result["final_inventory_unchanged"] = all(
                    inventory(base / sub) == prior[key]
                    for key, sub in (
                        ("source_before", "elmerfem"),
                        ("original_build_before", "build"),
                        ("original_prefix_before", "prefix"),
                    )
                )
                if not result["final_inventory_unchanged"]:
                    result.update(status="stopped", error="Original inventory changed")
            except (OSError, ValueError, KeyError) as exc:
                result.update(status="stopped", error="Final inventory unavailable: " + repr(exc))
        result["controller_wall_s"] = time.monotonic() - start
        persist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase", choices=("status", "prepare-initial", "build", "controller"), default="status"
    )
    args = parser.parse_args()
    cfg = yaml.safe_load(CONFIG.read_text())
    if args.phase == "status":
        out = ROOT / cfg["output_root"]
        print(
            json.dumps(
                {
                    "status": (
                        "read_only_build_disabled"
                        if not cfg["native_build_authorized"]
                        else "read_only_build_enabled"
                    ),
                    "preflight_sha256": sha(out / "preflight-v3.json"),
                    "native_action": False,
                }
            )
        )
    elif args.phase == "prepare-initial":
        prepare_initial()
    elif args.phase == "build":
        launch_guarded(cfg)
    else:
        controller(cfg)


if __name__ == "__main__":
    main()
