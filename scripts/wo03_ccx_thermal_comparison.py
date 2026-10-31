"""Bounded CalculiX known-answer fixture; never solves a PDE in Python.

Case A is the unchanged 935:1 affine finite-wall problem in the referenced
study. CalculiX's nonuniform film requires a linked user routine, so B cases
are reported unavailable rather than replaced with approximate wall inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import resource
import subprocess
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "configs/studies/wo03-thermal-error-isolation.yaml"
BINARY = Path("/opt/homebrew/bin/ccx")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_deck(cfg: dict, n: int) -> tuple[str, list[tuple[float, float, float]]]:
    if n not in (2, 4, 8):
        raise ValueError("Only the declared refinement levels are allowed")
    dims = cfg["dimensions_m"]
    indices = list(itertools.product(range(n + 1), repeat=3))
    nodes = [tuple(dims[j] * v[j] / n for j in range(3)) for v in indices]
    ids = {v: i + 1 for i, v in enumerate(indices)}
    tetra = []
    for base in itertools.product(range(n), repeat=3):
        for order in itertools.permutations(range(3)):
            at = list(base)
            tet = [ids[tuple(at)]]
            for axis in order:
                at[axis] += 1
                tet.append(ids[tuple(at)])
            if sum(order[i] > order[j] for i in range(3) for j in range(i + 1, 3)) % 2:
                tet[1], tet[2] = tet[2], tet[1]
            tetra.append(tet)
    faces = ((0, 1, 2), (0, 3, 1), (1, 3, 2), (2, 3, 0))
    film = []
    for eid, tet in enumerate(tetra, 1):
        for side, face in enumerate(faces, 1):
            if all(nodes[tet[v] - 1][0] == dims[0] for v in face):
                film.append((eid, side))
    hot = [i + 1 for i, xyz in enumerate(nodes) if xyz[0] == 0]
    lines = ["*HEADING", f"WO03 A level {n}", "*NODE,NSET=ALL"]
    lines += [f"{i}," + ",".join(f"{v:.12g}" for v in p) for i, p in enumerate(nodes, 1)]
    lines += ["*ELEMENT,TYPE=C3D4,ELSET=SOLID"]
    lines += [f"{i}," + ",".join(map(str, t)) for i, t in enumerate(tetra, 1)]
    lines += ["*NSET,NSET=HOT"]
    lines += [",".join(map(str, hot[i : i + 16])) for i in range(0, len(hot), 16)]
    lines += [
        "*MATERIAL,NAME=GAS",
        "*CONDUCTIVITY",
        str(cfg["conductivity_w_m_k"]),
        "*SOLID SECTION,ELSET=SOLID,MATERIAL=GAS",
        "*STEP",
        "*HEAT TRANSFER,STEADY STATE",
        "*BOUNDARY",
        f"HOT,11,11,{cfg['case_a']['hot_prescribed_k']}",
        "*FILM",
    ]
    lines += [
        f"{eid},F{face},{cfg['case_a']['cold_bulk_k']},{cfg['case_a']['h_w_m2_k']}"
        for eid, face in film
    ]
    lines += ["*NODE PRINT,NSET=ALL", "NT", "*NODE PRINT,NSET=HOT,TOTALS=YES", "RFL", "*END STEP"]
    return "\n".join(lines) + "\n", nodes


def parse_temperature(dat: str) -> dict[int, float]:
    text = dat.lower().split("temperatures", 1)
    if len(text) != 2:
        raise ValueError("No temperature output; stop and diagnose input")
    result = {}
    for line in text[1].splitlines()[1:]:
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit():
            result[int(parts[0])] = float(parts[1])
        elif result:
            break
    if not result:
        raise ValueError("Empty temperature output; stop and diagnose input")
    return result


def run(output: Path, resume: bool = False) -> None:
    if output.exists() and not resume:
        raise FileExistsError("Use a fresh output directory; previous evidence is preserved")
    cfg = yaml.safe_load(SOURCE.read_text())
    output.mkdir(parents=True, exist_ok=resume)
    env = os.environ.copy()
    for key in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "BLIS_NUM_THREADS",
        "CCX_NPROC_EQUATION_SOLVER",
        "CCX_NPROC_RESULTS",
        "CCX_NPROC_CFD",
    ):
        env[key] = "1"
    rec = {
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": digest(SOURCE),
        "script_sha256": digest(Path(__file__)),
        "binary": str(BINARY),
        "binary_realpath": str(BINARY.resolve()),
        "binary_sha256": digest(BINARY),
        "threads_requested": 1,
        "per_case_wall_limit_s": 120,
        "total_cpu_limit_s": 600,
        "case_A": [],
        "case_B": "unavailable: exact spatial sink requires linked film.f",
        "case_B_strong": "unavailable: exact spatial sink requires linked film.f",
        "surface_heat": "unavailable until output precision and integrated heat are verified",
        "local_balance": "unavailable",
        "acceptance": "not established",
    }
    if resume:
        old = json.loads((output / "record.json").read_text())
        if [r["returncode"] for r in old["case_A"]] != [0, 201] or "first_attempt" not in old:
            raise ValueError("Only the documented two-format-error packet may be resumed")
        rec["prior_attempts"] = old
        rec["case_A"] = [old["case_A"][0]]
    started = time.monotonic()
    all_cpu = old["total_cpu_s"] if resume else 0.0
    try:
        for n in cfg["divisions_per_axis"]:
            if resume and n == 2:
                continue
            remain = 120 - (time.monotonic() - started)
            if remain <= 0 or all_cpu >= 600:
                raise TimeoutError("Declared case/packet budget reached")
            deck, nodes = make_deck(cfg, n)
            folder = output / (f"A-{n}-field-width-fixed" if resume and n == 4 else f"A-{n}")
            folder.mkdir()
            inp = folder / "case.inp"
            inp.write_text(deck)
            before = resource.getrusage(resource.RUSAGE_CHILDREN)
            begin = time.monotonic()
            proc = subprocess.run(
                [str(BINARY), "-i", "case"],
                cwd=folder,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=remain,
                check=False,
            )
            usage = resource.getrusage(resource.RUSAGE_CHILDREN)
            cpu = usage.ru_utime + usage.ru_stime - before.ru_utime - before.ru_stime
            all_cpu += cpu
            (folder / "stdout.txt").write_text(proc.stdout)
            row = {
                "n": n,
                "input_sha256": digest(inp),
                "returncode": proc.returncode,
                "wall_s": time.monotonic() - begin,
                "cpu_s": cpu,
                "child_peak_rss_bytes_cumulative_max": usage.ru_maxrss,
            }
            rec["case_A"].append(row)
            if proc.returncode != 0 or "Job finished" not in proc.stdout:
                raise RuntimeError("CalculiX did not complete; stop, no blind retries")
            values = parse_temperature((folder / "case.dat").read_text())
            if len(values) != len(nodes):
                raise ValueError("Incomplete temperature field")
            a = cfg["case_a"]
            q = (a["hot_prescribed_k"] - a["cold_bulk_k"]) / (
                cfg["dimensions_m"][0] / cfg["conductivity_w_m_k"] + 1 / a["h_w_m2_k"]
            )
            errors = [
                abs(values[i] - (a["hot_prescribed_k"] - q * p[0] / cfg["conductivity_w_m_k"]))
                for i, p in enumerate(nodes, 1)
            ]
            row.update(
                max_coordinate_rounding_m=max(
                    abs(float(f"{v:.12g}") - v) for p in nodes for v in p
                ),
                max_printed_temperature_error_k=max(errors),
                printed_output_resolution_limitation="DAT precision must be considered before 1e-7 K claim",
                exact_temperature_check="unavailable at printed precision",
                expected_reservoir_heat_w=q * cfg["dimensions_m"][1] * cfg["dimensions_m"][2],
            )
    finally:
        rec["total_cpu_s"] = all_cpu
        rec["total_wall_s"] = time.monotonic() - started
        (output / "record.json").write_text(json.dumps(rec, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs/studies/wo03-external-thermal-comparison.yaml",
    )
    parser.add_argument("--preset", choices=["tiny"], default="tiny")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--resume-syntax-fix", action="store_true")
    parser.add_argument("--annular", action="store_true")
    args = parser.parse_args()
    study = yaml.safe_load(args.config.read_text())
    budget = study["budget"]
    if (
        budget["threads"] != 1
        or budget["seconds_per_case_all_levels"] != 120
        or budget["total_cpu_seconds"] != 600
        or budget["setup_wall_seconds"] != 600
    ):
        raise ValueError("Retain the declared one-CPU/120 s/600 s evaluation limits")
    if args.annular:
        run_annular(args.output or ROOT / study["default_output"])
    else:
        run(args.output or ROOT / study["default_output"], resume=args.resume_syntax_fix)


def run_annular(output: Path) -> None:
    import math

    import numpy as np

    root = ROOT
    out = output
    rec = json.loads((out / "record.json").read_text())
    if "annular" in rec or any((out / f"annular-{level}").exists() for level in range(3)):
        raise FileExistsError("Preserve existing annular results; use a fresh packet directory")
    rows = []
    begin = time.monotonic()
    cpu = 0
    os.environ.update(
        {
            k: "1"
            for k in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "BLIS_NUM_THREADS",
                "CCX_NPROC_EQUATION_SOLVER",
                "CCX_NPROC_RESULTS",
                "CCX_NPROC_CFD",
            )
        }
    )

    def sha(p):
        return hashlib.sha256(p.read_bytes()).hexdigest()

    try:
        for n in range(3):
            remain = 120 - (time.monotonic() - begin)
            if remain <= 0 or rec["total_cpu_s"] + cpu >= 600:
                raise RuntimeError("budget exhausted")
            src = root / f"build/wo03-gas-conduction/final/concentric_cylinder/level-{n}"
            mesh = src / "mesh.npz"
            groups = src / "groups.json"
            obj = np.load(mesh)
            pts = obj["points_m"]
            cells = obj["tetrahedra"].copy()
            boundary = json.loads(groups.read_text())["boundary_groups"]
            det = np.linalg.det(pts[cells[:, 1:]] - pts[cells[:, 0, None]])
            if np.any(det <= 0):
                raise RuntimeError("mesh has nonpositive signed determinant, stop")
            lines = ["*HEADING", "Concentric cylinder known answer", "*NODE,NSET=ALL"]
            lines.extend(f"{i}," + ",".join(f"{v:.12g}" for v in p) for i, p in enumerate(pts, 1))
            lines.append("*ELEMENT,TYPE=C3D4,ELSET=SOLID")
            lines.extend(
                f"{i}," + ",".join(str(int(v) + 1) for v in t) for i, t in enumerate(cells, 1)
            )
            for name in ("hot", "cold"):
                arr = boundary[name]
                lines.append(f"*NSET,NSET={name.upper()}")
                lines.extend(
                    ",".join(str(i + 1) for i in arr[k : k + 16]) for k in range(0, len(arr), 16)
                )
            lines += [
                "*MATERIAL,NAME=GAS",
                "*CONDUCTIVITY",
                "0.026",
                "*SOLID SECTION,ELSET=SOLID,MATERIAL=GAS",
                "*STEP",
                "*HEAT TRANSFER,STEADY STATE",
                "*BOUNDARY",
                "HOT,11,11,310",
                "COLD,11,11,290",
                "*NODE PRINT,NSET=ALL",
                "NT",
                "*NODE PRINT,NSET=HOT,TOTALS=YES",
                "RFL",
                "*NODE PRINT,NSET=COLD,TOTALS=YES",
                "RFL",
                "*END STEP",
            ]
            folder = out / f"annular-{n}"
            folder.mkdir()
            inp = folder / "case.inp"
            inp.write_text("\n".join(lines) + "\n")
            before = resource.getrusage(resource.RUSAGE_CHILDREN)
            t = time.monotonic()
            proc = subprocess.run(
                ["/opt/homebrew/bin/ccx", "-i", "case"],
                cwd=folder,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=remain,
                check=False,
            )
            usage = resource.getrusage(resource.RUSAGE_CHILDREN)
            used = usage.ru_utime + usage.ru_stime - before.ru_utime - before.ru_stime
            cpu += used
            (folder / "stdout.txt").write_text(proc.stdout)
            row = {
                "level": n,
                "mesh_sha256": sha(mesh),
                "groups_sha256": sha(groups),
                "deck_sha256": sha(inp),
                "nodes": len(pts),
                "tetrahedra": len(cells),
                "returncode": proc.returncode,
                "wall_s": time.monotonic() - t,
                "cpu_s": used,
                "child_cumulative_peak_rss_bytes": usage.ru_maxrss,
                "max_coordinate_rounding_m": max(abs(float(f"{v:.12g}") - v) for v in pts.ravel()),
            }
            rows.append(row)
            if proc.returncode or "Job finished" not in proc.stdout:
                raise RuntimeError("input/solve failed; stop without retry")

            dat = (folder / "case.dat").read_text()
            vals = parse_temperature(dat)
            assert len(vals) == len(pts)
            r = np.sqrt(pts[:, 0] ** 2 + pts[:, 1] ** 2)
            ref = 290 + 20 * np.log(0.01 / r) / math.log(2)
            arr = np.array([vals[i + 1] for i in range(len(pts))])
            row["max_printed_temperature_error_k"] = float(np.max(np.abs(arr - ref)))
            row["min_printed_k"] = float(arr.min())
            row["max_printed_k"] = float(arr.max())
            row["analytic_heat_w"] = 2 * math.pi * 0.026 * 0.012 * 20 / math.log(2)
            for side in ("hot", "cold"):
                s = dat.lower().split(f"total heat generation for set {side}", 1)
                if len(s) != 2:
                    raise ValueError("missing reservoir total")
                row[side + "_printed_heat_w"] = float(s[1].splitlines()[2].strip())
    finally:
        rec["annular"] = rows
        rec["annular_cpu_s"] = cpu
        rec["annular_wall_s"] = time.monotonic() - begin
        rec["total_cpu_with_annular_s"] = rec["total_cpu_s"] + cpu
        (out / "record.json").write_text(json.dumps(rec, indent=2) + "\n")


if __name__ == "__main__":
    main()
