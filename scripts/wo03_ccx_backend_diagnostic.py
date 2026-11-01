"""Prepare reversible CCX output/backend changes; no solver execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import resource
import shutil
import struct
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-ccx-backend-diagnostic.yaml"
OUT = ROOT / "build/wo03-ccx-backend-diagnostic-v2"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform(source: str, iterative: bool) -> str:
    """Replace exactly two STATIC selectors and add only two node output blocks."""
    if source.count("*STATIC\n") != 2 or source.count("*END STEP\n") != 2:
        raise ValueError("Expected exactly two unmodified static steps")
    if "*NODE OUTPUT" in source:
        raise ValueError("Already has binary output")
    out = (
        source.replace("*STATIC\n", "*STATIC,SOLVER=ITERATIVE CHOLESKY\n") if iterative else source
    )
    out = out.replace("*END STEP\n", "*NODE OUTPUT\nU,RF\n*END STEP\n")
    undo = out.replace("*NODE OUTPUT\nU,RF\n*END STEP\n", "*END STEP\n")
    undo = undo.replace("*STATIC,SOLVER=ITERATIVE CHOLESKY\n", "*STATIC\n")
    if undo != source:
        raise ValueError("Input whitelist reversal failed")
    return out


def parse_vector_fields(data: bytes, node_ids: list[int]):
    """Tentative upstream-master vector layout; reject unexpected native framing.

    B must independently verify actual 2.23 framing and compare with DAT and
    analytic values before this decoder can support any subsequent case.
    """
    if sorted(set(node_ids)) != node_ids or not node_ids:
        raise ValueError("Node ID list must be strictly ordered")
    pattern = re.compile(rb"(?m)^ -4  (DISP|FORC) +4 +1\n")
    hits = list(pattern.finditer(data))
    all_headers = re.findall(rb"(?m)^ -4  [A-Za-z0-9_]+[^\n]*\n", data)
    if len(all_headers) != len(hits):
        raise ValueError("Unexpected extra result field")
    if [h.group(1) for h in hits] != [b"DISP", b"FORC", b"DISP", b"FORC"]:
        raise ValueError("Expected exactly two ordered DISP/FORC pairs")
    records = []
    for index, h in enumerate(hits):
        # Source frdheader.c: counter, increment and step at fixed offsets;
        # 100CL has time, count and binary-format flag at fixed offsets.
        p = data.rfind(b"    1PSTEP", 0, h.start())
        if p < 0:
            raise ValueError("Missing 1PSTEP field metadata")
        line_end = data.find(b"\n", p)
        header = data[p:line_end]
        cl_end = data.find(b"\n", line_end + 1)
        cl = data[line_end + 1 : cl_end]
        if len(header) < 60 or len(cl) < 75 or not cl.startswith(b"  100CL"):
            raise ValueError("Malformed step or 100CL metadata")
        try:
            counter, inc, step = (int(header[i : i + 12]) for i in (24, 36, 48))
            time = float(cl[12:24])
            count = int(cl[24:36])
            encoding = int(cl[74:75])
        except ValueError as exc:
            raise ValueError("Malformed native step metadata") from exc
        if (
            step != index // 2 + 1
            or inc < 1
            or counter != index + 1
            or count != len(node_ids)
            or encoding != 2
            or not math.isclose(time, float(step), abs_tol=1e-8)
        ):
            raise ValueError("Unexpected step, increment, time, count or binary mode")
        if cl_end + 1 != h.start():
            raise ValueError("Unexpected bytes between metadata and field")
        field = h.group(1)
        components = (
            (b"D1", b"D2", b"D3", b"ALL") if field == b"DISP" else (b"F1", b"F2", b"F3", b"ALL")
        )
        pos = h.end()
        for expected in components:
            end = data.find(b"\n", pos)
            if end < 0:
                raise ValueError("Truncated component header")
            tokens = data[pos:end].split()
            if len(tokens) < 2 or tokens[:2] != [b"-5", expected]:
                raise ValueError("Unexpected component header")
            pos = end + 1
        end = pos + 16 * len(node_ids)
        if end > len(data) or not (
            data[end:].startswith(b"    1PSTEP") or data[end:].startswith(b" 9999\n")
        ):
            raise ValueError("Unexpected vector framing or record length")
        values = {}
        for i, expected in enumerate(node_ids):
            node, x, y, z = struct.unpack_from("<ifff", data, pos + i * 16)
            if node != expected or not all(math.isfinite(v) for v in (x, y, z)):
                raise ValueError("Unexpected node order or nonfinite value")
            values[node] = (x, y, z)
        records.append(
            {
                "field": field.decode(),
                "values": values,
                "step": step,
                "time": time,
                "increment": inc,
            }
        )
    return records


def float32_radius(value):
    f = np.float32(value)
    if not np.isfinite(f):
        raise ValueError("Nonfinite float32")
    below = np.nextafter(f, np.float32(-np.inf), dtype=np.float32)
    above = np.nextafter(f, np.float32(np.inf), dtype=np.float32)
    radius = max(float(f) - float(below), float(above) - float(f)) / 2
    if not math.isfinite(radius):
        raise ValueError("Unbounded float32 interval")
    return radius


def assess_b(meta, deck, dat_path, frd_path):
    from scripts.wo03_ccx_reaction_fixture import nonnative_preflight
    from scripts.wo03_g80_bridge_fea import parse_native_dat

    nonnative_preflight(meta, deck)
    coords = {int(k): np.asarray(v, dtype=float) for k, v in meta["node_coordinates_mm"].items()}
    ids = sorted(coords)
    support = set(meta["support_node_ids"])
    if len(ids) != meta["node_count"] or len(ids) > 5000 or meta["c3d10_count"] > 5000:
        raise ValueError("Node or element cap mismatch")

    def nset(name):
        m = re.search(r"(?ms)^\*NSET,NSET=" + name + r"\s*\n(.*?)(?=^\*)", deck)
        if not m:
            raise ValueError("Missing NSET")
        ns = [int(x.strip()) for x in m.group(1).replace("\n", ",").split(",") if x.strip()]
        if len(set(ns)) != len(ns):
            raise ValueError("Duplicate NSET")
        return set(ns)

    if (
        nset("ALL") != set(ids)
        or nset("SUPPORT") != support
        or deck.count("*BOUNDARY\nSUPPORT,1,3,0\n") != 1
        or deck.count("*BOUNDARY") != 1
    ):
        raise ValueError("NSET or boundary mismatch")
    if any(k in deck.upper() for k in ("*EQUATION", "*MPC", "*TRANSFORM", "*DLOAD")):
        raise ValueError("Unexpected constraint or distributed load")
    fields = parse_vector_fields(frd_path.read_bytes(), ids)
    dat = parse_native_dat(dat_path)
    dat_text = dat_path.read_text()
    headers = re.findall(
        r"(?im)^\s*(displacements|forces)\s*\([^)]*\)\s+for set\s+(ALL|SUPPORT)\s+and time\s+(\S+)",
        dat_text,
    )
    expected_headers = [
        ("displacements", "all", 1.0),
        ("forces", "all", 1.0),
        ("forces", "support", 1.0),
        ("displacements", "all", 2.0),
        ("forces", "all", 2.0),
        ("forces", "support", 2.0),
    ]
    actual_headers = [(a.lower(), b.lower(), float(t.replace("D", "E"))) for a, b, t in headers]
    if actual_headers != expected_headers:
        raise ValueError("DAT field times or order mismatch")
    bars = [set(x) for x in meta["bar_node_ids_by_bar"]]
    if len(bars) != 3 or set.union(*bars) != set(ids) or sum(map(len, bars)) != len(ids):
        raise ValueError("Bar membership incomplete or duplicated")
    reports = []
    for step in (1, 2):
        U = fields[2 * (step - 1)]["values"]
        RF = fields[2 * (step - 1) + 1]["values"]
        for key, native in (("displacements", U), ("forces", RF)):
            rows = dat[(step, key, "ALL")]
            if len(rows) != len(ids) or {r["id"] for r in rows} != set(ids):
                raise ValueError("DAT ALL nodes mismatch")
            for row in rows:
                for i, value in enumerate(row["values"]):
                    f = native[row["id"]][i]
                    width = row["rounding_half_width"][i] + float32_radius(f)
                    if abs(f - value) > width:
                        raise ValueError("DAT and binary intervals disjoint")
        sr = dat[(step, "forces", "SUPPORT")]
        if len(sr) != len(support) or {r["id"] for r in sr} != support:
            raise ValueError("DAT support mismatch")
        for row in sr:
            for i, v in enumerate(row["values"]):
                f = RF[row["id"]][i]
                if abs(f - v) > row["rounding_half_width"][i] + float32_radius(f):
                    raise ValueError("Support DAT mismatch")
        loads = {
            int(k): np.asarray(v, dtype=float)
            for k, v in meta["step_nodal_forces_N"][step - 1].items()
        }
        chunks = deck.split("*STEP\n")
        m = re.search(r"(?ms)^\*CLOAD,OP=NEW\n(.*?)(?=^\*)", chunks[step])
        if not m:
            raise ValueError("Missing CLOAD block")
        deck_loads = {}
        for line in m.group(1).splitlines():
            node, dof, value = (x.strip() for x in line.split(","))
            node = int(node)
            dof = int(dof)
            if dof not in (1, 2, 3) or not math.isfinite(float(value)):
                raise ValueError("Invalid load")
            deck_loads.setdefault(node, np.zeros(3))[dof - 1] += float(value)
        if set(deck_loads) != set(loads) or any(
            not np.allclose(deck_loads[n], loads[n], rtol=1e-13, atol=1e-14) for n in loads
        ):
            raise ValueError("Deck/metadata load mismatch")
        loads = deck_loads
        if support & set(loads):
            raise ValueError("Applied force on support")
        forces = meta["step_bar_resultants_N"][step - 1]
        area = meta["cross_section_area_analytic_mm2"]
        max_error = 0.0
        for bar, nodes in enumerate(bars):
            for n in nodes:
                z = coords[n][2]
                expected = (
                    forces[bar] / area * (min(z, 10.0) / 100.0 + max(z - 10.0, 0.0) / 10000.0)
                )
                err = abs(U[n][2] - expected)
                max_error = max(max_error, err)
                if (
                    err > (0.01 * abs(expected) if expected else 1e-8)
                    or abs(U[n][0]) > 1e-8
                    or abs(U[n][1]) > 1e-8
                ):
                    raise ValueError("Analytic displacement mismatch")
        residual = np.sum([RF[n] for n in sorted(support)], axis=0) + np.sum(
            list(loads.values()), axis=0
        )
        bounds = np.sum([[float32_radius(x) for x in RF[n]] for n in sorted(support)], axis=0)
        rr = float(np.linalg.norm(residual))
        bb = float(np.linalg.norm(bounds))
        tol = 1e-5
        status = (
            "pass"
            if rr + bb <= tol
            else ("fail" if max(0.0, rr - bb) > tol else "unavailable_precision")
        )
        moment = np.sum([np.cross(coords[n], RF[n]) for n in sorted(support)], axis=0) + np.sum(
            [np.cross(coords[n], f) for n, f in loads.items()], axis=0
        )
        # Conservatively bound each cross product by sum of absolute terms.
        moment_bound = np.sum(
            [
                [
                    abs(coords[n][1]) * float32_radius(RF[n][2])
                    + abs(coords[n][2]) * float32_radius(RF[n][1]),
                    abs(coords[n][2]) * float32_radius(RF[n][0])
                    + abs(coords[n][0]) * float32_radius(RF[n][2]),
                    abs(coords[n][0]) * float32_radius(RF[n][1])
                    + abs(coords[n][1]) * float32_radius(RF[n][0]),
                ]
                for n in sorted(support)
            ],
            axis=0,
        )
        reports.append(
            {
                "step": step,
                "force_residual_N": residual.tolist(),
                "encoding_bound_N": bounds.tolist(),
                "force_status": status,
                "moment_residual_Nmm": moment.tolist(),
                "moment_encoding_bound_Nmm": moment_bound.tolist(),
                "max_node_displacement_error_mm": max_error,
            }
        )
    return {
        "steps": reports,
        "strict_force_pass": all(r["force_status"] == "pass" for r in reports),
    }


def run_b1(cfg):
    """Only B1, gated by explicit changed authorization; never advance automatically."""
    sys.path.insert(0, str(ROOT))
    from scripts.wo03_owned_process import darwin_process_callbacks, run_owned

    admission = json.loads((OUT / "preflight-reviewed.json").read_text())
    frozen_cfg = yaml.safe_load(
        (ROOT / "build/wo03-ccx-backend-diagnostic-v1/executed-config.yaml").read_text()
    )
    normalized = dict(cfg)
    normalized["native_execution_authorized"] = False
    if normalized != frozen_cfg:
        raise ValueError("Configuration changed beyond B1 authorization")
    source = {
        k: ROOT / cfg[k]
        for k in (
            "fixture_deck",
            "fixture_meta",
            "fixture_saved_dat",
            "actual_deck",
            "actual_meta",
            "actual_saved_dat",
        )
    }
    if {k: sha(p) for k, p in source.items()} != admission["source_sha256_before"]:
        raise ValueError("Input changed")
    for p, h in admission["source_ledger"].items():
        if p == str(CONFIG):
            continue  # explicit authorization changes only config flag; verify all other config keys
        if sha(Path(p)) != h:
            raise ValueError("Source changed")
    if any(
        cfg[k] != v
        for k, v in (
            ("case_cpu_s", 120),
            ("case_wall_s", 120),
            ("rss_tree_limit_bytes", 2147483648),
            ("strict_reaction_force_N", 1e-5),
        )
    ):
        raise ValueError("Budget or criteria changed")
    prepared = OUT / "B_spooles_binary.inp"
    if sha(prepared) != admission["outputs"]["B_spooles_binary"]["sha256"]:
        raise ValueError("Prepared deck changed")
    original = source["fixture_deck"].read_text()
    meta = json.loads(source["fixture_meta"].read_text())
    if transform(original, False) != prepared.read_text():
        raise ValueError("Deck mismatch")
    folder = OUT / "native-B1"
    folder.mkdir(exist_ok=False)
    shutil.copyfile(prepared, folder / "case.inp")
    # The inherited parent hard limit matches the child hard limit; both are within packet reserve.
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    env = dict(os.environ)
    for k in (
        "OMP_NUM_THREADS",
        "CCX_NPROC_EQUATION_SOLVER",
        "CCX_NPROC_RESULTS",
        "CCX_NPROC_STIFFNESS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
    ):
        env[k] = "1"
    rss, desc = darwin_process_callbacks()
    launch = (
        "import os,resource;resource.setrlimit(resource.RLIMIT_CPU,(120,120));os.execv("
        + repr(cfg["solver"])
        + ",["
        + repr(cfg["solver"])
        + ",'-i','case'])"
    )
    record = {
        "status": "started",
        "source_before": {
            str(p): sha(p)
            for p in list(source.values())
            + [Path(cfg["solver"]), prepared, Path(__file__).resolve(), CONFIG]
        },
        "limits": {"child_cpu_s": 120, "wall_s": 120, "rss_bytes": 2147483648, "parent_cpu_s": 120},
        "no_automatic_next_case": True,
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
            "error" in log
            or "not converged" in log
            or "spooles" not in log
            or not re.search(r"using\s+1\s+cpu\s+for\s+spooles", log)
            or re.search(r"using\s+(?:[2-9]|[1-9][0-9]+)\s+cpu", log)
        ):
            raise ValueError("Solver log failure or backend not evidenced")
        record["assessment"] = assess_b(
            meta, prepared.read_text(), folder / "case.dat", folder / "case.frd"
        )
        record["status"] = (
            "b1_pass" if record["assessment"]["strict_force_pass"] else "stopped_precision_or_force"
        )
    except Exception as exc:
        record.update(status="stopped", error=repr(exc))
        raise
    finally:
        record["source_after"] = {p: sha(Path(p)) for p in record["source_before"]}
        record["source_unchanged"] = record["source_before"] == record["source_after"]
        if not record["source_unchanged"]:
            record.update(status="stopped", error="Source changed during execution")
        (folder / "assessment.json").write_text(json.dumps(record, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("prepare", "b1"), default="prepare")
    args = parser.parse_args()
    cfg = yaml.safe_load(CONFIG.read_text())
    if sha(Path(cfg["solver"])) != cfg["solver_sha256"]:
        raise ValueError("Pinned binary differs")
    if args.phase == "b1":
        if not cfg["native_execution_authorized"]:
            raise ValueError("B1 not admitted in frozen configuration")
        run_b1(cfg)
        return
    if cfg["native_execution_authorized"]:
        raise ValueError("Prepare-only config must keep native disabled")
    sources = {
        k: ROOT / cfg[k]
        for k in (
            "fixture_deck",
            "fixture_meta",
            "fixture_saved_dat",
            "actual_deck",
            "actual_meta",
            "actual_saved_dat",
        )
    }
    before = {k: sha(p) for k, p in sources.items()}
    sys.path.insert(0, str(ROOT))
    from scripts.wo03_ccx_reaction_fixture import nonnative_preflight

    meta = json.loads(sources["fixture_meta"].read_text())
    if max(meta["node_count"], meta["c3d10_count"]) > 5000:
        raise ValueError("Fixture exceeds cap")
    nonnative_preflight(meta, sources["fixture_deck"].read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    outputs = {}
    for label, key, iterative in [
        ("B_spooles_binary", "fixture_deck", False),
        ("B_iterative_cholesky_binary", "fixture_deck", True),
        ("actual_iterative_cholesky_binary", "actual_deck", True),
    ]:
        raw = sources[key].read_text()
        path = OUT / (label + ".inp")
        if path.exists():
            raise FileExistsError(path)
        path.write_text(transform(raw, iterative))
        outputs[label] = {
            "sha256": sha(path),
            "source_key": key,
            "node_output_blocks": 2,
            "iterative_cholesky": iterative,
        }
    after = {k: sha(p) for k, p in sources.items()}
    if before != after:
        raise ValueError("Saved source changed during preparation")
    rec = {
        "status": "prepared_no_native_run",
        "source_sha256_before": before,
        "source_sha256_after": after,
        "solver_sha256": cfg["solver_sha256"],
        "outputs": outputs,
        "reader_status": "B1 reader/gates prepared, conditional on unverified installed vector format",
        "native_execution_authorized": False,
        "source_ledger": {
            str(p): sha(p)
            for p in [
                Path(__file__).resolve(),
                CONFIG,
                ROOT / "scripts/wo03_g80_bridge_fea.py",
                ROOT / "scripts/wo03_ccx_reaction_fixture.py",
                ROOT / "scripts/wo03_owned_process.py",
                ROOT / "tests/test_ccx_backend_diagnostic.py",
                ROOT / "build/wo03-ccx-backend-diagnostic-v1/executed-config.yaml",
            ]
        },
    }
    (OUT / "preflight.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(json.dumps(rec, indent=2))


if __name__ == "__main__":
    main()
