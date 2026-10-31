"""Read-only completed-field heat ledgers: no factorization or PDE/ODE solve."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

for variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
):
    os.environ[variable] = "1"

import numpy as np
from scipy.sparse import coo_matrix

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_actual_gas_factor import build_conditions
from scripts.wo03_actual_gas_observed import inputs
from src.analysis.gas_conduction import assemble_tetra_conductivity

OBSERVED = Path("build/wo03-actual-gas-observed/coarse-nominal")
CONFIG = Path("configs/studies/wo03-actual-gas-observed.yaml")
EXPECTED = {
    CONFIG: "3eadf89d9bd80ecdf49aa4254200c1c6ccb6ecf1144b121d94ce8b80e7783995",
    OBSERVED / "record.json": "d4b4cffe6d296f2ae446ad389afd6513c2f5f2af28113b8345e5652754145fee",
    OBSERVED
    / "gas-response.json": "7725547235cd8d07ea2461bb42539345362b8d77b12821088f50346291f33e04",
    OBSERVED
    / "gas-response.npz": "ed6a820d15d64224fd3201ef230f341da69304ae490559c4c79303a507f02ded",
    OBSERVED
    / "checked-gas-surface-fields.npz": "741fcec8ef7684d43bc1420fd41bc8ff6c30c35cd617d4d0dbd055ad4d12bea7",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def audit(output: Path) -> dict[str, Any]:
    started = time.monotonic()
    for path, expected in EXPECTED.items():
        if sha(path) != expected:
            raise ValueError(f"Completed immutable input changed: {path}")
    cfg, paths, source_hashes = inputs(CONFIG)
    source_hashes = {
        **source_hashes,
        **{str(p): h for p, h in EXPECTED.items()},
        "audit_script": sha(Path(__file__)),
    }
    state = json.loads((OBSERVED / "gas-response.json").read_text())
    original = json.loads((OBSERVED / "record.json").read_text())
    mesh, conditions, _, source = build_conditions(cfg, paths)
    k = source["air_conductivity_w_m_k"]
    assembly = assemble_tetra_conductivity(
        mesh.points_m, mesh.tetrahedra, k, max_tetrahedra=750000, max_nodes=150000
    )
    K = assembly.stiffness_w_k
    triangles = np.asarray(mesh.boundary_triangles)
    n = len(mesh.points_m)
    gids = state["group_ids"]
    bulk_ids, prescribed_ids = state["bulk_ids"], state["prescribed_ids"]
    nb, nd, ng = len(bulk_ids), len(prescribed_ids), len(gids)
    bulk_index = {name: i for i, name in enumerate(bulk_ids)}
    dir_index = {name: i for i, name in enumerate(prescribed_ids)}
    robin = np.array([i for i, row in enumerate(conditions) if row.kind == "robin"])
    rt = triangles[robin]
    M = np.array([conditions[i].wall_matrix_w_k for i in robin])
    path_faces, path_bulks, path_vectors, path_diagonals = [], [], [], []
    reference_bulk = []
    D = np.zeros(nb)
    owner = np.full(n, -1, dtype=int)
    for face, row in enumerate(conditions):
        if row.kind == "dirichlet":
            column = dir_index[row.temperature_id]
            if np.any((owner[triangles[face]] >= 0) & (owner[triangles[face]] != column)):
                raise ValueError("Conflicting physical prescribed IDs")
            owner[triangles[face]] = column
    for local_face, face in enumerate(robin):
        row = conditions[face]
        reference_bulk.append(bulk_index[next(iter(row.bulk_load_vectors_w_k))])
        for name, vector in row.bulk_load_vectors_w_k.items():
            column = bulk_index[name]
            value = row.bulk_diagonal_w_k[name]
            path_faces.append(local_face)
            path_bulks.append(column)
            path_vectors.append(vector)
            path_diagonals.append(value)
            D[column] += value
    pf, pb = np.array(path_faces), np.array(path_bulks)
    vectors, diagonals = np.array(path_vectors), np.array(path_diagonals)
    R = coo_matrix(
        (M.ravel(), (np.repeat(rt, 3, axis=1).ravel(), np.tile(rt, (1, 3)).ravel())), shape=(n, n)
    ).tocsr()
    B = coo_matrix((vectors.ravel(), (rt[pf].ravel(), np.repeat(pb, 3))), shape=(n, nb)).tocsr()
    A = K + R
    xyz = np.asarray(mesh.points_m)[triangles]
    areas = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
    columns = np.searchsorted(gids, mesh.boundary_group_ids)
    group_areas = np.bincount(columns, weights=areas, minlength=ng)
    L = coo_matrix(
        (
            np.repeat(areas / (3 * group_areas[columns]), 3),
            (triangles.ravel(), np.repeat(columns, 3)),
        ),
        shape=(n, ng),
    ).tocsr()
    fixed, free = np.flatnonzero(owner >= 0), np.flatnonzero(owner < 0)
    E = coo_matrix((np.ones(len(fixed)), (fixed, owner[fixed])), shape=(n, nd)).tocsr()
    with np.load(OBSERVED / "checked-gas-surface-fields.npz", allow_pickle=False) as data:
        names = [str(name) for name in data["case_ids"]]
        T = data["nodal_temperature_k"].T.copy()
        saved_means = data["area_mean_temperature_k"].T.copy()
    nc = len(names)
    bulk = np.full((nb, nc), 300.0)
    prescribed = np.full((nd, nc), 300.0)
    loads = np.zeros((ng, nc))
    hot_index = names.index("case300C_ambient35C_nominalwall_no_radiation")
    uniform_index = names.index("uniform_300K_unforced")
    ambient = source["selected_case"]["ambient_c"] + 273.15
    bulk[:, hot_index] = ambient
    prescribed[:, hot_index] = [
        (
            source["selected_case"]["case_peak_c"] + 273.15
            if name == cfg["shared_motor_case_temperature_id"]
            else ambient
        )
        for name in prescribed_ids
    ]
    for i, name in enumerate(names):
        if name.startswith("group"):
            group, sign = name.split("_", 1)
            loads[gids.index(int(group[5:])), i] = 1.0 if sign.startswith("+") else -1.0
    # Extra fields are explicitly read-only counterchecks, not repaired inputs.
    names.extend(
        [
            "exact_constant_300K_countercheck",
            "hot_uniform_mode_subtraction_roundoff_DIAGNOSTIC_ONLY",
        ]
    )
    T = np.column_stack(
        (T, np.full(n, 300.0), T[:, hot_index] - ambient / 300 * (T[:, uniform_index] - 300))
    )
    bulk = np.column_stack((bulk, np.full(nb, 300.0), bulk[:, hot_index]))
    prescribed = np.column_stack((prescribed, np.full(nd, 300.0), prescribed[:, hot_index]))
    loads = np.column_stack((loads, np.zeros(ng), loads[:, hot_index]))
    nc = len(names)
    original_columns = len(saved_means.T)
    means = np.asarray(L.T @ T)
    saved_mean_difference = float(np.abs(means[:, :original_columns] - saved_means).max())
    K1 = np.asarray(K @ np.ones(n))
    Bsumface = np.zeros((len(robin), 3))
    np.add.at(Bsumface, pf, vectors)
    wall_row_partition = M.sum(axis=2) - Bsumface
    bulk_path_partition = vectors.sum(axis=1) - diagonals
    # Finite-wall heat into bulk from local TEMPERATURE DIFFERENCES.
    local_bulk = np.zeros((nb, nc))
    local_bulk_partition = np.zeros_like(local_bulk)
    np.add.at(local_bulk, pb, np.einsum("pi,pic->pc", vectors, T[rt[pf]] - bulk[pb, None, :]))
    np.add.at(local_bulk_partition, pb, bulk_path_partition[:, None] * bulk[pb])
    # Robin nodal reactions, retaining the raw partition defect separately.
    reference = bulk[np.asarray(reference_bulk)]
    wall_local = np.einsum("fij,fjc->fic", M, T[rt] - reference[:, None, :])
    np.add.at(wall_local, pf, -vectors[:, :, None] * (bulk[pb] - reference[pf])[:, None, :])
    wall_difference = np.zeros((n, nc))
    wall_partition = np.zeros_like(wall_difference)
    np.add.at(wall_difference, rt.ravel(), wall_local.reshape(-1, nc))
    np.add.at(
        wall_partition,
        rt.ravel(),
        (wall_row_partition[:, :, None] * reference[:, None, :]).reshape(-1, nc),
    )
    # Independent element Fourier reactions from local temperature differences.
    # This is postprocessing of SAVED fields, never a new PDE solve.
    air_difference = np.zeros((n, nc))
    for start in range(0, len(assembly.tetrahedra), 25000):
        stop = min(start + 25000, len(assembly.tetrahedra))
        cells = assembly.tetrahedra[start:stop]
        values = T[cells]
        gradients = assembly.gradients_per_m[start:stop]
        gradT = np.einsum("tic,tij->tjc", values - values[:, :1], gradients)
        element = (
            k
            * assembly.volumes_m3[start:stop, None, None]
            * np.einsum("tij,tjc->tic", gradients, gradT)
        )
        np.add.at(air_difference, cells.ravel(), element.reshape(-1, nc))
    reports = []
    original_checks = {row["id"]: row for row in original["field_checks"]}
    for case, name in enumerate(names):
        t, tb, q = T[:, case : case + 1], bulk[:, case : case + 1], loads[:, case : case + 1]
        old_bulk = np.asarray(B.T @ t) - D[:, None] * tb
        raw_air = np.asarray(K @ t)
        raw_residual = np.asarray(A @ t - B @ tb - L @ q)
        old_prescribed = -np.asarray(E.T @ raw_residual)
        diff_prescribed_rawK = -np.asarray(
            E.T @ (raw_air + wall_difference[:, case : case + 1] - L @ q)
        )
        exact_partition_prescribed = -np.asarray(
            E.T
            @ (
                raw_air
                + wall_difference[:, case : case + 1]
                + wall_partition[:, case : case + 1]
                - L @ q
            )
        )
        stable_residual = (
            air_difference[:, case : case + 1] + wall_difference[:, case : case + 1] - L @ q
        )
        stable_prescribed = -np.asarray(E.T @ stable_residual)
        old_energy = float(old_bulk.sum() + old_prescribed.sum() - q.sum())
        local_rawK_energy = float(local_bulk[:, case].sum() + diff_prescribed_rawK.sum() - q.sum())
        partition_energy = float(
            (local_bulk[:, case] + local_bulk_partition[:, case]).sum()
            + exact_partition_prescribed.sum()
            - q.sum()
        )
        stable_energy = float(local_bulk[:, case].sum() + stable_prescribed.sum() - q.sum())
        reference_temperature = float(tb[0, 0])
        centered_air = np.asarray(K @ (t - reference_temperature))
        air_decomposition_residual = raw_air - centered_air - K1[:, None] * reference_temperature
        gradient = np.einsum(
            "ti,tij->tj",
            (t[assembly.tetrahedra] - t[assembly.tetrahedra[:, :1]])[:, :, 0],
            assembly.gradients_per_m,
        )
        air_form = float(np.sum(k * assembly.volumes_m3 * np.sum(gradient**2, axis=1)))
        surface_values = T[rt, case] - reference[:, case, None]
        wall_form = float(np.einsum("fi,fij,fj->", surface_values, M, surface_values))
        # All saved probes prescribe equal bulk temperatures; no mixed-cell drop.
        if not np.all(tb == tb[0]):
            raise ValueError("This bounded form diagnostic assumes observed equal bulk states only")
        stable_heat = np.r_[local_bulk[:, case], stable_prescribed[:, 0]]
        reservoir_temperatures = np.r_[tb[:, 0], prescribed[:, case]]
        boundary_form = float(q[:, 0] @ means[:, case] - reservoir_temperatures @ stable_heat)
        shifted_boundary_form = float(
            q[:, 0] @ (means[:, case] - reference_temperature)
            - (reservoir_temperatures - reference_temperature) @ stable_heat
        )
        old = original_checks.get(name)
        lo, hi = float(reservoir_temperatures.min()), float(reservoir_temperatures.max())
        reports.append(
            {
                "case": name,
                "saved_original_field": case < original_columns,
                "old_record_energy_residual_w": old["energy_balance_residual_w"] if old else None,
                "raw_assembled_energy_residual_w": old_energy,
                "raw_vs_record_energy_difference_w": (
                    old_energy - old["energy_balance_residual_w"] if old else None
                ),
                "local_bulk_with_rawK_prescribed_energy_residual_w": local_rawK_energy,
                "local_with_source_partition_defects_energy_residual_w": partition_energy,
                "local_wall_and_element_gradient_difference_energy_residual_w": stable_energy,
                "raw_assembled_heat_into_prescribed_w": old_prescribed[:, 0].tolist(),
                "local_wall_rawK_heat_into_prescribed_w": diff_prescribed_rawK[:, 0].tolist(),
                "local_element_gradient_heat_into_prescribed_w": stable_prescribed[:, 0].tolist(),
                "raw_assembled_bulk_heat_sum_w": float(old_bulk.sum()),
                "local_difference_bulk_heat_sum_w": float(local_bulk[:, case].sum()),
                "maximum_bulk_state_cancellation_difference_w": float(
                    np.abs(old_bulk[:, 0] - local_bulk[:, case]).max()
                ),
                "absolute_raw_reservoir_heat_scale_w": float(
                    np.abs(np.r_[old_bulk[:, 0], old_prescribed[:, 0]]).sum()
                ),
                "absolute_local_reservoir_heat_scale_w": float(np.abs(stable_heat).sum()),
                "old_record_form_difference_w_k": (
                    old["form_balance_difference_w_times_k"] if old else None
                ),
                "local_difference_form_difference_w_k": air_form + wall_form - boundary_form,
                "reference_shifted_difference_form_difference_w_k": air_form
                + wall_form
                - shifted_boundary_form,
                "reference_shift_identity_residual_w_k": (air_form + wall_form - boundary_form)
                - (air_form + wall_form - shifted_boundary_form)
                - reference_temperature * stable_energy,
                "air_difference_form_w_k": air_form,
                "wall_difference_form_w_k": wall_form,
                "rawK_reference_mode_max_w": float(np.abs(K1 * reference_temperature).max()),
                "rawK_reference_mode_sum_w": float(K1.sum() * reference_temperature),
                "rawK_matmul_centered_decomposition_max_difference_w": float(
                    np.abs(air_decomposition_residual).max()
                ),
                "local_gradient_vs_rawK_nodal_max_difference_w": float(
                    np.abs(air_difference[:, case] - raw_air[:, 0]).max()
                ),
                "stable_free_node_residual_max_w": float(np.abs(stable_residual[free]).max()),
                "P1_nodal_min_k": float(t.min()),
                "P1_nodal_max_k": float(t.max()),
                "area_mean_min_k": float(means[:, case].min()),
                "area_mean_max_k": float(means[:, case].max()),
                "prescribed_state_interval_k": [lo, hi],
                "unchanged_1uW_check_raw": abs(old_energy) <= 1e-6,
                "unchanged_1uW_check_difference_diagnostic": abs(stable_energy) <= 1e-6,
                "unchanged_1mWK_check_difference_diagnostic": abs(
                    air_form + wall_form - boundary_form
                )
                <= 1e-3,
            }
        )
    exact = reports[-2]
    current_cfg, current_paths, current_hashes = inputs(CONFIG)
    del current_cfg, current_paths
    after = {
        **current_hashes,
        **{str(p): sha(p) for p in EXPECTED},
        "audit_script": sha(Path(__file__)),
    }
    result = {
        "run_id": datetime.now(UTC).strftime("wo03-gas-energy-diagnostic-%Y%m%dT%H%M%S%fZ"),
        "elapsed_s": time.monotonic() - started,
        "input_sha256_before": source_hashes,
        "input_sha256_after": after,
        "inputs_unchanged": source_hashes == after,
        "conductivity_w_m_k": k,
        "one_CPU": True,
        "exact_prescribed_reaction_scope": "ALL prescribed-node reactions from complete raw assembled residual, plus separately labelled local-difference postprocessing; no omitted prescribed heat",
        "cases": reports,
        "rawK1": {
            "maximum_absolute_w_k": float(np.abs(K1).max()),
            "sum_w_k": float(K1.sum()),
            "absolute_sum_w_k": float(np.abs(K1).sum()),
        },
        "wall_partition": {
            "maximum_row_defect_w_k": float(np.abs(wall_row_partition).max()),
            "maximum_path_BminusD_w_k": float(np.abs(bulk_path_partition).max()),
            "assembled_Bcolumn_minusD_max_w_k": float(
                np.abs(np.asarray(B.sum(axis=0)).ravel() - D).max()
            ),
        },
        "exact_uniform_countercheck_difference_heat_zero": exact[
            "local_wall_and_element_gradient_difference_energy_residual_w"
        ]
        == 0
        and exact["local_difference_bulk_heat_sum_w"] == 0
        and all(v == 0 for v in exact["local_element_gradient_heat_into_prescribed_w"]),
        "saved_surface_mean_reconstruction_max_difference_k": saved_mean_difference,
        "uniform_mode_subtraction_field_max_difference_k": float(
            np.abs(T[:, -1] - T[:, hot_index]).max()
        ),
        "uniform_mode_subtraction_scope": "Read-only roundoff diagnostic ONLY; no original field/operator/cache replaced, no repaired-field claim",
        "criteria_unchanged": {"heat_absolute_w": 1e-6, "form_absolute_w_k": 1e-3},
        "original_actual_record_numerical_checks_pass": original["numerical_checks_pass"],
        "no_relabelled_actual_pass": True,
        "new_factor_PDE_or_ODE_solve": False,
        "new_actual_temperature_acceptance": False,
        "measured_process_max_rss_bytes": int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            * (1 if sys.platform == "darwin" else 1024)
        ),
    }
    write_json(output / "energy-ledger.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("build/wo03-gas-energy-diagnostic/final")
    )
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        audit(args.output)
        return 0
    args.output.mkdir(parents=True, exist_ok=False)
    before = sha(Path(__file__))
    with (args.output / "worker.log").open("w") as log:
        try:
            child = subprocess.run(
                [sys.executable, str(Path(__file__)), "--worker", "--output", str(args.output)],
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=120,
                check=False,
            )
            code, capped = child.returncode, False
        except subprocess.TimeoutExpired:
            code, capped = None, True
    result = {
        "source_sha256": before,
        "child_returncode": code,
        "child120s_cap_reached": capped,
        "one_CPU": True,
        "compute_cost_usd": 0,
        "new_factor_PDE_or_ODE_solve": False,
        "actual_temperature_acceptance": False,
    }
    ledger = args.output / "energy-ledger.json"
    if ledger.exists():
        result.update(ledger=str(ledger), ledger_sha256=sha(ledger))
    write_json(args.output / "record.json", result)
    print(args.output / "record.json")
    return 0 if code == 0 and not capped else 1


if __name__ == "__main__":
    raise SystemExit(main())
