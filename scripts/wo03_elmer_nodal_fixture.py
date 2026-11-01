"""Prepare one source-identical B SINGLE load as direct nodal RHS; never run solver."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-elmer-nodal-fixture.yaml"
OUT = ROOT / "build/wo03-elmer-nodal-fixture-v1"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def cload(deck):
    steps = deck.split("*STEP\n")[1:]
    if len(steps) != 2:
        raise ValueError("Expected two source steps")
    m = re.search(r"(?ms)^\*CLOAD,OP=NEW\n(.*?)(?=^\*)", steps[1])
    if not m:
        raise ValueError("Missing SINGLE CLOAD")
    result = {}
    for line in m.group(1).splitlines():
        n, dof, token = line.split(",")
        n = int(n)
        if dof != "3" or n in result or not math.isfinite(float(token)):
            raise ValueError("Invalid source load")
        result[n] = token
    return result


def replace_traction(sif, loads):
    pattern = re.compile(
        r"(?ms)^Boundary Condition ([123])\n  Target Boundaries\(1\) = \1\n  Force 3 = Real ([^\n]+)\nEnd\n"
    )
    matches = list(pattern.finditer(sif))
    if [(m.group(1), m.group(2)) for m in matches] != [("1", "9375000"), ("2", "0"), ("3", "0")]:
        raise ValueError("Baseline SINGLE surface BC changed")
    base = pattern.sub("", sif)
    lines = []
    for i, (node, token) in enumerate(sorted(loads.items()), 10):
        lines += [
            f"Boundary Condition {i}",
            f"  Target Nodes(1) = {node}",
            f"  Displacement 3 Load = Real {token}",
            "End",
        ]
    result = base + "\n".join(lines) + "\n"
    found = re.findall(
        r"Target Nodes\(1\) = (\d+)\n  Displacement 3 Load = Real ([^\n]+)\n", result
    )
    if len(found) != len(loads) or dict(found) != {str(k): v for k, v in loads.items()}:
        raise ValueError("Nodal load roundtrip mismatch")
    if "Force 3 = Real" in result:
        raise ValueError("Residual face traction")
    return result


def main():
    cfg = yaml.safe_load(CONFIG.read_text())
    if cfg["native_execution_authorized"]:
        raise ValueError("No native execution implemented")
    paths = {
        k: ROOT / cfg[k]
        for k in ("source_deck", "source_metadata", "baseline_review", "reader", "solver", "module")
    }
    base = ROOT / cfg["baseline_case"]
    files = [
        *paths.values(),
        base / "case.sif",
        *[
            base / "mesh" / n
            for n in ("mesh.header", "mesh.nodes", "mesh.elements", "mesh.boundary")
        ],
        Path(__file__).resolve(),
        CONFIG,
    ]
    before = {str(p): sha(p) for p in files}
    for n in ("solver", "module", "reader"):
        if sha(paths[n]) != cfg[n + "_sha256"]:
            raise ValueError("Pinned source changed: " + n)
    review = json.loads(paths["baseline_review"].read_text())
    prefix = ROOT / ".cache/elmer-evaluation/setup-v1/prefix"
    prefix_before = {str(p): sha(p) for p in prefix.rglob("*") if p.is_file()}
    if prefix_before != review["prefix_sha256"]:
        raise ValueError("Pinned Elmer prefix changed")
    original_review = json.loads(
        (ROOT / "build/wo03-elmer-structural-fixture-v3/prepared/record.json").read_text()
    )
    for p in [
        base / "case.sif",
        *[
            base / "mesh" / n
            for n in ("mesh.header", "mesh.nodes", "mesh.elements", "mesh.boundary")
        ],
    ]:
        if sha(p) != original_review["generated_sha256"][str(p.relative_to(ROOT))]:
            raise ValueError("Baseline SIF or mesh differs")
    meta = json.loads(paths["source_metadata"].read_text())
    deck = paths["source_deck"].read_text()
    loads = cload(deck)
    support = set(meta["support_node_ids"])
    bar0 = set(meta["top_node_ids_by_bar"][0])
    ids = sorted(map(int, meta["node_coordinates_mm"]))
    if len(ids) != 593 or ids != list(range(1, 594)) or set(loads) != bar0 or support & set(loads):
        raise ValueError("Source node coverage or support mismatch")
    nodes = {}
    for line in (base / "mesh/mesh.nodes").read_text().splitlines():
        x = line.split()
        nodes[int(x[0])] = tuple(map(float, x[2:]))
    if sorted(nodes) != ids:
        raise ValueError("Elmer node order not contiguous")
    for n in ids:
        expected = np.asarray(meta["node_coordinates_mm"][str(n)]) * 1e-3
        if not np.array_equal(np.asarray(nodes[n]), expected):
            raise ValueError("Source/SI node coordinate mismatch")
        if any(not math.isfinite(v) for v in nodes[n]):
            raise ValueError("Nonfinite coordinate")
    force = math.fsum(float(v) for v in loads.values())
    moment = np.sum(
        [
            np.cross(np.asarray(meta["node_coordinates_mm"][str(n)]) * 1e-3, [0.0, 0.0, float(v)])
            for n, v in loads.items()
        ],
        axis=0,
    )
    if abs(force - 150) > 1e-9 or not np.allclose(moment, [0.0, 1.5, 0.0], rtol=0, atol=1e-9):
        raise ValueError("Known SINGLE force/moment mismatch")
    baseline = (base / "case.sif").read_text()
    candidate = replace_traction(baseline, loads)
    if len(loads) != 13:
        raise ValueError("Unexpected SINGLE load-node count")
    out = OUT / "prepared"
    out.mkdir(parents=True, exist_ok=False)
    shutil.copytree(base / "mesh", out / "mesh")
    (out / "case.sif").write_text(candidate)
    (out / "config-disabled.yaml").write_bytes(CONFIG.read_bytes())
    after = {str(p): sha(p) for p in files}
    prefix_after = {str(p): sha(p) for p in prefix.rglob("*") if p.is_file()}
    if before != after or prefix_before != prefix_after:
        raise ValueError("Source or prefix changed")
    rec = {
        "status": "prepared_no_native_nodal_rhs_unverified",
        "sources_before": before,
        "sources_after": after,
        "source_unchanged": True,
        "prefix_unchanged": True,
        "prefix_sha256": prefix_before,
        "source_tokens_exact": True,
        "load_node_count": len(loads),
        "all_node_count": len(ids),
        "support_node_count": len(support),
        "applied_force_N": force,
        "applied_moment_Nm": moment.tolist(),
        "baseline_change": "three SINGLE surface Force 3 BCs removed; exact original source CLOAD node/token pairs added as Target Nodes/Displacement 3 Load; all other SIF bytes unchanged",
        "reader_sha256": sha(paths["reader"]),
        "outputs": {str(p.relative_to(ROOT)): sha(p) for p in out.rglob("*") if p.is_file()},
        "native_executed": False,
        "source_supported_not_native_proven": True,
    }
    (OUT / "preflight.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: rec[k]
                for k in (
                    "status",
                    "load_node_count",
                    "all_node_count",
                    "applied_force_N",
                    "applied_moment_Nm",
                )
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("prepare",), default="prepare")
    parser.parse_args()
    main()
