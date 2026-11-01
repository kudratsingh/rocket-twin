"""Prepare or, only when separately authorized, run classic Elmer A comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import resource
import shutil
import sys
import time
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.wo03_elmer_thermal_comparison import (
    continuous_p2_bound,
    exact_outward_conduction,
    find_vtu,
    read_diffusive_flux,
    read_vtu,
)
from scripts.wo03_owned_process import darwin_process_callbacks, run_owned

CONFIG = ROOT / "configs/studies/wo03-elmer-classic-comparison.yaml"
OLD = b'Procedure = File "HeatSolveVec" "HeatSolver"'
NEW = b'Procedure = File "HeatSolve" "HeatSolver"'
MESH_FILES = ("mesh.header", "mesh.nodes", "mesh.elements", "mesh.boundary")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def classic_sif(source):
    if source.count(OLD) != 1 or NEW in source:
        raise ValueError("Unexpected source SIF procedure; stop")
    result = source.replace(OLD, NEW, 1)
    if result.replace(NEW, OLD, 1) != source:
        raise ValueError("SIF differs beyond classic procedure-file replacement")
    return result


def read_mesh_nodes(path):
    nodes = {}
    for line in Path(path).read_text().splitlines():
        fields = line.split()
        if len(fields) != 5 or int(fields[0]) in nodes:
            raise ValueError("Malformed or duplicate Elmer mesh node")
        xyz = tuple(float(x) for x in fields[2:])
        if not all(math.isfinite(x) for x in xyz):
            raise ValueError("Nonfinite mesh coordinates")
        nodes[int(fields[0])] = xyz
    if not nodes:
        raise ValueError("Empty Elmer mesh")
    return nodes


def collect_inputs(cfg):
    source = ROOT / cfg["source_packet"]
    home = ROOT / cfg["elmer_home"]
    runtime = json.loads((ROOT / cfg["source_runtime_record"]).read_text())
    record = json.loads((source / "record.json").read_text())
    pre = json.loads((source / "preflight.json").read_text())
    if (
        runtime["status"] != "isolated_available_not_qualified"
        or record["status"] != "completed_fields_heat_and_balances_unavailable"
        or not record["inputs_unchanged"]
        or not record["tool_unchanged"]
    ):
        raise ValueError("Original completed packet/runtime status invalid")
    for name, expected in runtime["artifact_sha256"].items():
        if sha(home / name) != expected:
            raise ValueError(f"Pinned runtime changed: {name}")
    for name, expected in record["tool_sha256"].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"Prior campaign tool changed: {name}")
    for name, expected in pre["source_sha256"].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f"Prior source changed: {name}")
    files = [ROOT / cfg["source_runtime_record"], source / "record.json", source / "preflight.json"]
    rows = {int(row["level"]): row for row in record["cases"]["A"]}
    if set(rows) != {2, 4, 8}:
        raise ValueError("Expected exactly three preserved A levels")
    for n in cfg["levels"]:
        for name in ("case.sif", *(f"mesh/{x}" for x in MESH_FILES)):
            rel = f"A/{n}/{name}"
            path = source / rel
            if sha(path) != pre["generated_file_sha256"][rel]:
                raise ValueError(f"Prior mesh/SIF hash changed: {rel}")
            files.append(path)
        vtu = source / f"A/{n}/mesh/field_t0001.vtu"
        if sha(vtu) != rows[n]["VTU_sha256"]:
            raise ValueError(f"Prior VTU hash changed: A/{n}")
        files.append(vtu)
    files += [Path(__file__).resolve(), CONFIG, ROOT / "scripts/wo03_owned_process.py"]
    files += [home / name for name in runtime["artifact_sha256"]]
    files += [ROOT / name for name in record["tool_sha256"]]
    files += [
        ROOT / cfg["source_harness"],
        ROOT / cfg["source_config"],
        ROOT / cfg["source_runtime_record"],
    ]
    return source, home, record, pre, rows, {str(p): sha(p) for p in set(files)}


def prepare(cfg, out):
    source, home, record, _pre, rows, source_hashes = collect_inputs(cfg)
    out.mkdir(parents=True, exist_ok=False)
    casecfg = yaml.safe_load(
        (ROOT / "configs/studies/wo03-thermal-error-isolation.yaml").read_text()
    )
    levels = []
    for n in cfg["levels"]:
        original = source / f"A/{n}"
        folder = out / "A" / str(n)
        (folder / "mesh").mkdir(parents=True)
        original_sif = (original / "case.sif").read_bytes()
        edited = classic_sif(original_sif)
        (folder / "case.sif").write_bytes(edited)
        for name in MESH_FILES:
            shutil.copy2(original / "mesh" / name, folder / "mesh" / name)
            if sha(folder / "mesh" / name) != sha(original / "mesh" / name):
                raise ValueError("Copied mesh differs")
        nodes = read_mesh_nodes(folder / "mesh/mesh.nodes")
        field = read_vtu(original / "mesh/field_t0001.vtu", nodes, "A", casecfg)
        if field["field_type"] != "float64" or field["VTK_version"] != "9.6.2":
            raise ValueError("Unexpected saved field type/reader version")
        saved = rows[n]
        delta = float(
            np.max(
                np.abs(np.asarray(field["temperatures_k"]) - np.asarray(saved["temperatures_k"]))
            )
        )
        if delta > 1e-12 or abs(field["max_nodal_error_k"] - saved["max_nodal_error_k"]) > 1e-12:
            raise ValueError(f"Prior field/reference mismatch for level {n}")
        levels.append(
            {
                "level": n,
                "node_count": len(nodes),
                "original_sif_sha256": sha(original / "case.sif"),
                "classic_sif_sha256": sha(folder / "case.sif"),
                "mesh_sha256": {name: sha(folder / "mesh" / name) for name in MESH_FILES},
                "vec_vtu_sha256": field["VTU_sha256"],
                "vec_max_nodal_error_k": field["max_nodal_error_k"],
                "prior_record_field_difference_k": delta,
                "only_sif_change_verified": True,
            }
        )
    after = {p: sha(p) for p in source_hashes}
    if after != source_hashes:
        raise ValueError("Source changed while preparing")
    manifest = {
        "status": "prepare_only_no_solver",
        "levels": levels,
        "source_sha256_before": source_hashes,
        "source_sha256_after": after,
        "tool_sha256": record["tool_sha256"],
        "classic_module_sha256": sha(home / "share/elmersolver/lib/HeatSolve.dylib"),
        "source_unchanged": True,
        "solver_invoked": False,
        "acceptance": False,
        "threshold_k": cfg["field_absolute_tolerance_k"],
        "native_cpu_plan_s": cfg["planned_native_cpu_seconds"],
        "note": "only the procedure library name changes; common HeatSolver, direct solver, BCs, material, mesh and output remain unchanged",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": manifest["status"], "levels": levels}, indent=2))


def execute(cfg, out):
    """Run only after a separate primary declaration; never called by prepare."""
    if (
        cfg["levels"] != [2, 4, 8]
        or cfg["threads"] != 1
        or cfg["cpu_seconds_per_level"] != 120
        or cfg["wall_seconds_per_level"] != 120
        or cfg["planned_native_cpu_seconds"] != 360
        or cfg["packet_cpu_ceiling"] != 600
        or cfg["parent_cpu_cap_s"] != 60
        or cfg["setup_cpu_reservation_s"] != 30
        or cfg["planned_total_cpu_reservation_s"] != 450
        or cfg["native_execution_authorized"] is not True
    ):
        raise ValueError("Declared classic packet budget changed")
    # Reserve 30 CPU s for setup, cap parent at 60, and three children at
    # 120 each: planned maximum 450 CPU s within the 600 CPU s packet.
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    parent_start = time.process_time()
    manifest = json.loads((out / "manifest.json").read_text())
    if manifest["status"] != "prepare_only_no_solver" or not manifest["source_unchanged"]:
        raise ValueError("Missing successful prepare-only manifest")
    source, home, _record, _pre, _rows, source_hashes = collect_inputs(cfg)
    if source_hashes != manifest["source_sha256_before"]:
        raise ValueError("Pinned inputs changed since preparation")
    for item in manifest["levels"]:
        folder = out / "A" / str(item["level"])
        original = source / "A" / str(item["level"])
        if (folder / "case.sif").read_bytes() != classic_sif((original / "case.sif").read_bytes()):
            raise ValueError("Prepared SIF differs beyond permitted byte change")
        if any(sha(folder / "mesh" / name) != item["mesh_sha256"][name] for name in MESH_FILES):
            raise ValueError("Prepared mesh changed")
    cfg0 = yaml.safe_load((ROOT / "configs/studies/wo03-elmer-thermal-comparison.yaml").read_text())
    casecfg = yaml.safe_load((ROOT / cfg0["reference"]).read_text())
    criteria = yaml.safe_load((ROOT / cfg0["criteria"]).read_text())["verification"]
    if criteria["temperature_absolute_tolerance_k"] != cfg["field_absolute_tolerance_k"]:
        raise ValueError("Original exact-field threshold changed")
    rss, children = darwin_process_callbacks()
    env = dict(os.environ)
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "BLIS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env[name] = "1"
    env["ELMER_HOME"] = str(home.resolve())
    env["ELMER_LIB"] = str((home / "share/elmersolver/lib").resolve())
    binary = home / "bin/ElmerSolver"
    results = []
    result = {
        "status": "in_progress",
        "levels": results,
        "source_sha256_before": source_hashes,
        "solver_invoked": False,
        "acceptance": False,
        "setup_cpu_reservation_s": 30,
        "parent_cpu_limit_s": 60,
        "native_cpu_limit_s": 360,
        "total_planned_cpu_reservation_s": 450,
        "global_robin_or_algebra_balance": None,
        "local_balance": None,
        "raw_C_convergence": None,
        "actual_baffle": False,
    }

    def persist():
        (out / "record.json").write_text(json.dumps(result, indent=2) + "\n")

    persist()
    try:
        for n in cfg["levels"]:
            folder = out / "A" / str(n)
            entry = {"level": n}
            results.append(entry)
            result["solver_invoked"] = True
            persist()
            cmd = (
                "import os,resource;resource.setrlimit(resource.RLIMIT_CPU,(120,120));os.execv("
                + repr(str(binary.resolve()))
                + ",["
                + repr(str(binary.resolve()))
                + ",'case.sif'])"
            )
            status = run_owned(
                [sys.executable, "-c", cmd],
                log_path=folder / "solver.log",
                status_path=folder / "owned-status.json",
                wall_limit_s=120,
                rss_callback=rss,
                descendants_callback=children,
                cwd=folder,
                env=env,
            )
            entry["owned_status"] = status
            baseline = next(item for item in manifest["levels"] if item["level"] == n)
            if sha(folder / "case.sif") != baseline["classic_sif_sha256"] or any(
                sha(folder / "mesh" / name) != baseline["mesh_sha256"][name] for name in MESH_FILES
            ):
                raise ValueError("Prepared mesh or SIF changed during solver execution")
            log = (folder / "solver.log").read_text(errors="replace")
            if "FATAL" in log.upper() or re.search(
                r"did not converge|failed to converge", log, re.IGNORECASE
            ):
                raise ValueError("Elmer failure or nonconvergence")
            nodes = read_mesh_nodes(folder / "mesh/mesh.nodes")
            field = read_vtu(find_vtu(folder), nodes, "A", casecfg)
            vec = read_vtu(source / f"A/{n}/mesh/field_t0001.vtu", nodes, "A", casecfg)
            field["max_abs_classic_minus_vec_k"] = float(
                np.max(
                    np.abs(np.asarray(field["temperatures_k"]) - np.asarray(vec["temperatures_k"]))
                )
            )
            field.update(continuous_p2_bound("A", casecfg, field["max_nodal_error_k"]))
            field["exact_nodal_temperature_pass"] = (
                field["max_nodal_error_k"] < criteria["temperature_absolute_tolerance_k"]
            )
            flux = read_diffusive_flux(folder)
            expected = exact_outward_conduction("A", casecfg)
            observed = flux["outward_conductive_heat_w"]
            flux["reference_outward_conduction_w"] = expected
            flux["max_reference_error_w"] = max(abs(observed[k] - expected[k]) for k in expected)
            tol = criteria["heat_absolute_tolerance_w"] + criteria["heat_relative_tolerance"] * max(
                abs(v) for v in expected.values()
            )
            flux["A_reference_tolerance_w"] = tol
            flux["A_reference_comparison_pass"] = flux["max_reference_error_w"] < tol
            flux["sum_outward_conduction_w"] = sum(observed.values())
            flux["sum_is_not_robin_or_algebra_balance"] = True
            field["native_diffusive_flux"] = flux
            entry["field"] = field
            persist()
        result["status"] = "completed_diagnostic_no_acceptance"
    except Exception as exc:
        result["status"] = "stopped"
        result["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        result["source_sha256_after"] = {p: sha(p) for p in source_hashes}
        result["source_unchanged"] = result["source_sha256_before"] == result["source_sha256_after"]
        for row in results:
            status_path = out / "A" / str(row["level"]) / "owned-status.json"
            if status_path.exists() and "owned_status" not in row:
                row["owned_status"] = json.loads(status_path.read_text())
        result["parent_cpu_s"] = time.process_time() - parent_start
        result["parent_peak_rss_bytes_macos"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result["child_cpu_s"] = sum(
            row["owned_status"]["cpu_accounting"]["child_user_s_delta"]
            + row["owned_status"]["cpu_accounting"]["child_system_s_delta"]
            for row in results
            if "owned_status" in row
        )
        result["memory_note"] = "Parent and child RSS peaks are separate, not simultaneous."
        if not result["source_unchanged"]:
            result["status"] = "stopped"
            result["error"] = "Source or pinned tool changed during execution"
        persist()


def main():
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--prepare-only", action="store_true")
    g.add_argument("--execute", action="store_true")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    cfg = yaml.safe_load(CONFIG.read_text())
    if args.prepare_only:
        prepare(cfg, args.output.resolve())
    else:
        execute(cfg, args.output.resolve())


if __name__ == "__main__":
    main()
