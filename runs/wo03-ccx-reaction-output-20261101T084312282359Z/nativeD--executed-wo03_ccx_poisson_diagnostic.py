"""Prepare the B-derived uniaxial-strain diagnostic; never run a solver."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.wo03_g80_bridge_fea import evaluate_balance, parse_native_dat

CONFIG = ROOT / "configs/studies/wo03-ccx-poisson-diagnostic.yaml"
EDITS = (
    (b"*ELASTIC\n100,0\n", b"*ELASTIC\n100,0.3\n"),
    (b"*ELASTIC\n10000,0\n", b"*ELASTIC\n10000,0.3\n"),
    (b"*BOUNDARY\nSUPPORT,1,3,0\n", b"*BOUNDARY\nSUPPORT,1,3,0\nALL,1,2,0\n"),
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def modified_deck(original):
    if original.count(b"*BOUNDARY\n") != 1 or any(
        token in original for token in (b"*DLOAD", b"*MPC", b"*TRANSFORM", b"*EQUATION")
    ):
        raise ValueError("Unexpected source boundary, distributed load, MPC, or transformation")
    changed = original
    for old, new in EDITS:
        if changed.count(old) != 1 or new in changed:
            raise ValueError("Expected unique unmodified B deck token")
        changed = changed.replace(old, new, 1)
    restored = changed
    for old, new in reversed(EDITS):
        if restored.count(new) != 1:
            raise ValueError("Changed deck token is ambiguous")
        restored = restored.replace(new, old, 1)
    if restored != original:
        raise ValueError("Deck has an unexpected difference")
    return changed


def reference_tensor(force, area, young, nu):
    if not (area > 0 and young > 0 and -1 < nu < 0.5):
        raise ValueError("Invalid elastic parameters")
    sigma = force / area
    lam = young * nu / ((1 + nu) * (1 - 2 * nu))
    mu = young / (2 * (1 + nu))
    eff = lam + 2 * mu
    strain = sigma / eff
    stresses = np.array([lam * strain, lam * strain, (lam + 2 * mu) * strain, 0, 0, 0])
    expected = np.array([nu / (1 - nu) * sigma, nu / (1 - nu) * sigma, sigma, 0, 0, 0])
    if not np.allclose(stresses, expected, rtol=1e-13, atol=1e-13):
        raise ValueError("Independent Hooke substitution failed")
    return {
        "E_MPa": young,
        "nu": nu,
        "effective_axial_modulus_MPa": eff,
        "uniaxial_strain": strain,
        "stress_components_MPa": stresses.tolist(),
    }


def reference_displacement(force, z, area, nu):
    factor = (1 - nu) / ((1 + nu) * (1 - 2 * nu))
    return force / area / factor * (min(max(z, 0), 10) / 100 + max(z - 10, 0) / 10000)


def deck_nodes_and_loads(deck):
    coords = {}
    loads = []
    section = ""
    for line in deck.splitlines():
        line = line.strip()
        if line.startswith("*"):
            section = line.upper().split(",", 1)[0]
            if section == "*CLOAD":
                loads.append({})
            continue
        if not line:
            continue
        fields = line.split(",")
        if section == "*NODE":
            coords[int(fields[0])] = [float(x) for x in fields[1:4]]
        elif section == "*CLOAD":
            n, dof, value = int(fields[0]), int(fields[1]), float(fields[2])
            vector = loads[-1].setdefault(n, [0.0, 0.0, 0.0])
            vector[dof - 1] += value
    if len(loads) != 2 or not coords:
        raise ValueError("Invalid deck node/load blocks")
    return coords, loads


def assess_saved_output(meta, deck_path, dat_path):
    """ALL RF = applied + reaction; reconstruct reactions by subtracting CLOAD."""
    coords, loads = deck_nodes_and_loads(Path(deck_path).read_text())
    sections = parse_native_dat(dat_path)
    support = set(meta["support_node_ids"])
    all_ids = set(coords)
    steps = []
    nu = 0.3
    for step in (1, 2):
        u = sections[(step, "displacements", "ALL")]
        all_rf = sections[(step, "forces", "ALL")]
        sup_rf = sections[(step, "forces", "SUPPORT")]
        if (
            len(u) != len(all_ids)
            or {r["id"] for r in u} != all_ids
            or len(all_rf) != len(all_ids)
            or {r["id"] for r in all_rf} != all_ids
        ):
            raise ValueError("ALL output coverage invalid")
        if len(sup_rf) != len(support) or {r["id"] for r in sup_rf} != support:
            raise ValueError("SUPPORT RF coverage invalid")
        reactions = []
        for row in all_rf:
            applied = loads[step - 1].get(row["id"], [0.0, 0.0, 0.0])
            reactions.append(
                {
                    "id": row["id"],
                    "values": [v - a for v, a in zip(row["values"], applied, strict=True)],
                    "rounding_half_width": row["rounding_half_width"],
                }
            )
        balance = evaluate_balance(coords, loads[step - 1], reactions)
        u_by_node = {r["id"]: r["values"] for r in u}
        bar_report = []
        for bar, ids in enumerate(meta["bar_node_ids_by_bar"]):
            force = (50.0, 50.0, 50.0)[bar] if step == 1 else (150.0, 0.0, 0.0)[bar]
            expected_top = reference_displacement(force, 20.0, 16.0, nu)
            errors = [
                abs(u_by_node[n][2] - reference_displacement(force, coords[n][2], 16.0, nu))
                for n in ids
            ]
            transverse = max(abs(u_by_node[n][j]) for n in ids for j in (0, 1))
            limit = 0.01 * abs(expected_top) if force else 1e-8
            bar_report.append(
                {
                    "bar": bar,
                    "expected_top_z_mm": expected_top,
                    "max_axial_error_mm": max(errors),
                    "relative_to_top_error": max(errors) / abs(expected_top) if force else None,
                    "axial_limit_mm": limit,
                    "max_transverse_abs_mm": transverse,
                    "displacement_pass": max(errors) <= limit and transverse <= 1e-8,
                }
            )
        zsum = sum(r["values"][2] for r in sup_rf)
        zbound = sum(r["rounding_half_width"][2] for r in sup_rf)
        zstatus = (
            "pass"
            if abs(zsum + 150) + zbound <= 1e-5
            else (
                "fail" if max(0, abs(zsum + 150) - zbound) > 1e-5 else "unavailable_print_precision"
            )
        )
        steps.append(
            {
                "step": step,
                "total_reaction_plus_applied_from_all_RF": balance,
                "bars": bar_report,
                "bottom_support_rf_z_sum_N": zsum,
                "bottom_support_rf_z_rounding_bound_N": zbound,
                "bottom_support_rf_z_status": zstatus,
            }
        )
    passed = all(
        x["total_reaction_plus_applied_from_all_RF"]["force_balance_status"] == "pass"
        and x["bottom_support_rf_z_status"] == "pass"
        and all(b["displacement_pass"] for b in x["bars"])
        for x in steps
    )
    return {
        "status": "passed" if passed else "failed_or_unavailable",
        "steps": steps,
        "solver_invoked_by_reader": False,
        "moment_balance": "reported with propagated print rounding, not separately thresholded",
    }


def prepare(out, cfg):
    if (
        cfg["poisson_ratio"] != 0.3
        or cfg["planned_native_cases"] != 1
        or cfg["planned_native_cpu_s"] != 10
        or cfg["planned_native_wall_s"] != 30
        or cfg["threads"] != 1
        or cfg["original_native_case_limit"] != 3
        or cfg["prior_native_cases_executed"] != 2
        or cfg["max_nodes"] != 5000
        or cfg["max_tetrahedra"] != 5000
        or cfg["force_balance_strict_absolute_n"] != 1e-5
        or cfg["relative_displacement_tolerance"] != 0.01
    ):
        raise ValueError("Declared physical inputs, fixture criteria, or packet limits changed")
    asset_paths = [
        Path(__file__).resolve(),
        CONFIG,
        ROOT / "scripts/wo03_g80_bridge_fea.py",
        ROOT / "scripts/wo03_ccx_reaction_fixture.py",
    ]
    asset_before = {str(p): sha(p) for p in asset_paths}
    source = ROOT / cfg["source_case"]
    admission = ROOT / cfg["source_admission_record"]
    prior = json.loads(admission.read_text())
    if (
        prior["status"] != "diagnostic_complete_strict_force_unavailable"
        or prior["case"] != "B"
        or not prior["source_unchanged"]
    ):
        raise ValueError("B diagnostic provenance invalid")
    inp = {name: source / name for name in ("case.inp", "mesh-meta.json", "preflight.json")}
    before = {name: sha(path) for name, path in inp.items()}
    if before != prior["input_sha256_at_admission"]:
        raise ValueError("B source differs from admitted input")
    ccx = Path(cfg["solver"])
    if sha(ccx) != cfg["solver_sha256"]:
        raise ValueError("Pinned solver changed")
    original = inp["case.inp"].read_bytes()
    changed = modified_deck(original)
    meta = json.loads(inp["mesh-meta.json"].read_text())
    if meta["node_count"] > cfg["max_nodes"] or meta["c3d10_count"] > cfg["max_tetrahedra"]:
        raise ValueError("Input cap exceeded")
    factor = (1 - 0.3) / ((1 + 0.3) * (1 - 2 * 0.3))
    tensors = {
        str(f): [reference_tensor(f, 16.0, e, 0.3) for e in (100.0, 10000.0)] for f in (50.0, 150.0)
    }
    refs = [reference_displacement(f, 20, 16, 0.3) for f in (50.0, 150.0)]
    if abs(factor - 1.346153846153846) > 1e-14 or not np.allclose(
        refs, [0.2344642857142857, 0.7033928571428571], atol=1e-14, rtol=0
    ):
        raise ValueError("Uniaxial-strain reference mismatch")
    coords, loads = deck_nodes_and_loads(changed.decode())
    load_balance = []
    for step in loads:
        f = sum((np.asarray(v) for v in step.values()), np.zeros(3))
        moment = sum((np.cross(coords[n], v) for n, v in step.items()), np.zeros(3))
        load_balance.append({"force_N": f.tolist(), "moment_Nmm": moment.tolist()})
    if not np.allclose(
        [x["force_N"] for x in load_balance], [[0, 0, 150], [0, 0, 150]], atol=1e-8, rtol=0
    ) or not np.allclose(
        [x["moment_Nmm"] for x in load_balance], [[0, 0, 0], [0, 1500, 0]], atol=1e-6, rtol=0
    ):
        raise ValueError("Serialized applied resultants changed")
    out.mkdir(parents=True, exist_ok=False)
    (out / "case.inp").write_bytes(changed)
    (out / "mesh-meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    source_after = {name: sha(path) for name, path in inp.items()}
    if source_after != before:
        raise ValueError("B source changed during preparation")
    asset_after = {str(p): sha(p) for p in asset_paths}
    if asset_before != asset_after:
        raise ValueError("Preparation source changed during execution")
    manifest = {
        "status": "prepared_no_solver",
        "preparation_source_sha256_before": asset_before,
        "preparation_source_sha256_after": asset_after,
        "source_B_input_sha256": before,
        "source_B_input_sha256_after": source_after,
        "source_B_admission_record_sha256": sha(admission),
        "modified_deck_sha256": sha(out / "case.inp"),
        "byte_diff": "two Poisson 0 to 0.3 and one ALL x/y constraint; reverse substitution exactly restores source",
        "nodes": meta["node_count"],
        "tetrahedra": meta["c3d10_count"],
        "effective_modulus_factor": factor,
        "reference_top_z_mm_50N_150N": refs,
        "reference_tensors": tensors,
        "serialized_applied_resultants": load_balance,
        "strict_force_tolerance_N": 1e-5,
        "strict_rounding_rule": "residual norm plus output rounding bound <=1e-5 N",
        "all_rf_reaction_interpretation": "total reaction = ALL RF minus known applied CLOAD; no DLOAD or MPC",
        "solver_invoked": False,
        "actual_bridge": False,
        "acceptance": False,
    }
    (out / "preflight.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prepare-only", action="store_true", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    prepare(a.output.resolve(), yaml.safe_load(CONFIG.read_text()))


if __name__ == "__main__":
    main()
