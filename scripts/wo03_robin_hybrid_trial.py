"""Final fixture-only wall trial: diagonal M, unchanged accurate B/D.

Declare Mnew=diag(Moriginal*1) as a distinct integration/stabilization, keeping
the original positive-quadrature B/D bitwise unchanged. For nonnegative symmetric
M, diag(M1)-M is a graph Laplacian and positive semidefinite; adding it to the
original augmented wall energy preserves PSD and the constant-field partition.
References: standard P1 lumped mass/graph Laplacian energy identity; frozen
Fourier/manufactured known cases in wo03_thermal_error_isolation.py. No stored
actual operator, production source or volume discretization is changed.
"""

from __future__ import annotations

import os

for name in [
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
]:
    os.environ[name] = "1"

import argparse
import copy
import json
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_robin_lumped_trial import CONFIG, PRIOR, array_sha, load_prior
from scripts.wo03_thermal_error_isolation import sha, structured_box, wall_conditions
from src.analysis.gas_conduction import assemble_tetra_conductivity
from src.analysis.robin_gas import BoundaryCondition, factor_robin_gas, integrated_wall_terms

TRIAL1 = Path("build/wo03-robin-lumped-trial-v1/record.json")
TRIAL1_SHA = "c374323af07f1293a7b2d6b8ac8c73095436cd5d802024c553fdba937b837bca"


def level(
    case: str,
    n: int,
    cfg: dict[str, Any],
    source: dict[str, Any],
    old: dict[str, Any],
    old1: dict[str, Any],
    output: Path,
) -> dict[str, Any]:
    started = time.monotonic()
    mesh, sides = structured_box(cfg["dimensions_m"], n)
    prior_dir = PRIOR / case / f"n-{n}"
    if sha(prior_dir / "mesh-and-wall-inputs.npz") != old["input_arrays_sha256"]:
        raise ValueError("Original fixture input archive changed")
    with np.load(prior_dir / "mesh-and-wall-inputs.npz", allow_pickle=False) as archive:
        if not all(
            np.array_equal(getattr(mesh, name), archive[name])
            for name in ["points_m", "tetrahedra", "boundary_triangles", "boundary_group_ids"]
        ):
            raise ValueError("Hybrid source mesh differs from original")
    original, bulks, prescribed, extra = wall_conditions(mesh, sides, case, cfg)
    xyz = mesh.points_m[mesh.boundary_triangles]
    areas = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
    conditions = []
    matrices, cold, hot, d = [], [], [], []
    minimum_augmented = float("inf")
    partition, bdelta, ddelta, convex_partition = 0.0, 0.0, 0.0, 0.0
    effective = []
    minimum_weight, maximum_weight = 1.0, 0.0
    for original_row, area in zip(original, areas):
        if original_row.kind != "robin":
            conditions.append(original_row)
            matrices.append(np.zeros((3, 3)))
            cold.append(np.zeros(3))
            hot.append(np.zeros(3))
            d.append([0.0, 0.0])
            continue
        term = integrated_wall_terms(original_row, float(area))
        lump = np.diag(term["matrix"] @ np.ones(3))
        vectors = {name: value.copy() for name, value in term["vectors"].items()}
        diagonal = dict(term["diagonal"])
        replacement = BoundaryCondition(
            "robin", wall_matrix_w_k=lump, bulk_load_vectors_w_k=vectors, bulk_diagonal_w_k=diagonal
        )
        verified = integrated_wall_terms(replacement, float(area))
        for name in vectors:
            if (
                not np.array_equal(verified["vectors"][name], term["vectors"][name])
                or verified["diagonal"][name] != term["diagonal"][name]
            ):
                raise ValueError("Accurate B/D was changed")
        weights = np.column_stack(list(vectors.values())) / np.diag(lump)[:, None]
        minimum_weight = min(minimum_weight, float(weights.min()))
        maximum_weight = max(maximum_weight, float(weights.max()))
        convex_partition = max(convex_partition, float(abs(weights.sum(axis=1) - 1).max()))
        effective.extend((weights @ np.array([bulks[name] for name in vectors])).tolist())
        if weights.min() < 0 or weights.max() > 1 + 1e-14:
            raise ValueError("Hybrid effective forcing is not convex")
        minimum_augmented = min(minimum_augmented, verified["minimum_augmented_eigenvalue_w_k"])
        partition = max(partition, verified["partition_residual_w_k"])
        conditions.append(replacement)
        matrices.append(lump)
        cold.append(vectors["cold"])
        hot.append(vectors.get("hot", np.zeros(3)))
        d.append([diagonal["cold"], diagonal.get("hot", 0.0)])
    wall = {
        "matrix_w_k": np.array(matrices),
        "Bcold_w_k": np.array(cold),
        "Bhot_w_k": np.array(hot),
        "D_w_k": np.array(d),
    }
    wall_signature = array_sha(*wall.values())
    output.mkdir(parents=True, exist_ok=False)
    input_arrays: dict[str, Any] = {
        "points_m": mesh.points_m,
        "tetrahedra": mesh.tetrahedra,
        "boundary_triangles": mesh.boundary_triangles,
        "boundary_group_ids": mesh.boundary_group_ids,
        "boundary_sides": sides,
        **wall,
    }
    np.savez_compressed(output / "mesh-and-wall-inputs.npz", **input_arrays)
    factor = factor_robin_gas(mesh, conditions, cfg["conductivity_w_m_k"])
    replay = assemble_tetra_conductivity(
        mesh.points_m, mesh.tetrahedra, cfg["conductivity_w_m_k"]
    ).stiffness_w_k
    same_k = all(
        np.array_equal(getattr(replay, name), getattr(factor.assembly.stiffness_w_k, name))
        for name in ["data", "indices", "indptr"]
    )

    def signature() -> str:
        return array_sha(
            *[
                getattr(matrix, name)
                for matrix in [factor.assembly.stiffness_w_k, factor.A_w_k, factor.B_w_k]
                for name in ["data", "indices", "indptr"]
            ],
            factor.D_bulk_w_k,
        )

    before = signature()
    bulk = np.array([bulks[name] for name in factor.bulk_ids])
    physical = np.array([prescribed[name] for name in factor.prescribed_ids])
    answer = factor.evaluate(bulk, physical, np.zeros(len(factor.group_ids)))
    field = answer.pop("nodal_temperature_k")
    if not same_k or signature() != before or array_sha(*wall.values()) != wall_signature:
        raise ValueError("Raw volumeK/A/B/D/wall arrays changed")
    with np.load(prior_dir / "arrays.npz", allow_pickle=False) as archive:
        exact, exact_means = archive["exact_temperature_k"], archive["exact_facet_mean_k"]
    error = field - exact
    mean_error = np.asarray(answer["area_mean_temperature_k"]) - exact_means
    volume_mean = float(
        np.sum(factor.assembly.volumes_m3 * field[mesh.tetrahedra].mean(axis=1))
        / factor.assembly.volumes_m3.sum()
    )
    heat = np.r_[answer["heat_into_bulk_w"], answer["heat_into_prescribed_reservoir_w"]]
    expected = np.array(old["expected_reservoir_heat_w"])
    v = source["verification"]
    balance = bool(
        factor.diagnostics["algebra_checks_pass"]
        and abs(answer["energy_balance_residual_w"]) < v["heat_absolute_tolerance_w"]
        and abs(answer["form_balance_difference_w_times_k"])
        < v["form_absolute_tolerance_w_times_k"]
    )
    lo, hi = old["physical_boundary_envelope_k"]
    row = {
        "case": case,
        "divisions_each_axis": n,
        "nodes": len(mesh.points_m),
        "tetrahedra": len(mesh.tetrahedra),
        "mesh_identical_to_original": True,
        "K_bitwise_identical_to_original_mesh_replay": same_k,
        "original_B_bitwise_unchanged": bdelta == 0,
        "original_D_bitwise_unchanged": ddelta == 0,
        "B_max_change_w_k": bdelta,
        "D_max_change_w_k": ddelta,
        "raw_matrices_and_terms_unchanged_after_construction": True,
        "wall_augmented_minimum_eigenvalue_w_k": minimum_augmented,
        "wall_partition_max_w_k": partition,
        "effective_forcing_convex_weight_min": minimum_weight,
        "effective_forcing_convex_weight_max": maximum_weight,
        "effective_forcing_partition_error": convex_partition,
        "effective_discrete_forcing_range_k": [min(effective), max(effective)],
        "true_effective_boundary_envelope_k": [lo, hi],
        "effective_forcing_within_true_envelope": min(effective) >= lo - 1e-10
        and max(effective) <= hi + 1e-10,
        "maximum_nodal_error_k": float(abs(error).max()),
        "maximum_facet_mean_error_k": float(abs(mean_error).max()),
        "area_weighted_RMS_facet_mean_error_k": float(
            np.sqrt(np.sum(factor.group_areas_m2 * mean_error**2) / factor.group_areas_m2.sum())
        ),
        "volume_mean_error_k": volume_mean - old["exact_volume_mean_k"],
        "below_true_boundary_minimum_k": max(0.0, lo - float(field.min())),
        "above_true_boundary_maximum_k": max(0.0, float(field.max()) - hi),
        "maximum_reservoir_heat_error_w": float(abs(heat - expected).max()),
        "reference_heat_tolerance_pass": bool(
            abs(heat - expected).max() < old["reservoir_heat_tolerance_w"]
        ),
        "discrete_algebra_balance_pass": balance,
        "exact_A_checks_pass": (
            bool(
                balance
                and abs(error).max() < v["temperature_absolute_tolerance_k"]
                and abs(heat - expected).max() < old["reservoir_heat_tolerance_w"]
            )
            if case == "A"
            else None
        ),
        "C_raw_w_k": factor.reservoir_conductance_raw_w_k.tolist(),
        "answer": answer,
        "diagnostics": factor.diagnostics,
        "consistent_prior": {
            key: old[key]
            for key in [
                "maximum_nodal_error_k",
                "maximum_facet_mean_error_k",
                "volume_mean_error_k",
                "maximum_reservoir_heat_error_w",
            ]
        },
        "trial1_prior": {
            key: old1[key]
            for key in [
                "maximum_nodal_error_k",
                "maximum_facet_mean_error_k",
                "volume_mean_error_k",
                "maximum_reservoir_heat_error_w",
            ]
        },
        "actual_accuracy_or_temperature_acceptance": False,
    }
    if case != "A":
        h = cfg["case_b"]["h_w_m2_k"]
        interpolated = np.einsum("qi,ti->tq", extra["barycentric"], field[mesh.boundary_triangles])
        continuum = (
            h
            * areas
            * np.einsum(
                "q,tq->t", extra["normalized_weights"], interpolated - extra["effective_bulk_k"]
            )
        )
        forcing_error = (bulks["hot"] - bulks["cold"]) * float(
            (wall["Bhot_w_k"] - extra["Bhot_w_k"]).sum()
        )
        row.update(
            maximum_boundary_quadrature_point_error_k=float(
                abs(interpolated - extra["exact_u_quadrature_k"]).max()
            ),
            physical_continuum_net_heat_w=float(continuum.sum()),
            physical_continuum_zero_net_heat_tolerance_pass=bool(
                abs(continuum.sum()) < v["heat_absolute_tolerance_w"]
            ),
            source_forcing_integration_change_w=forcing_error,
            independent_continuum_vs_stable_net_heat_difference_w=float(continuum.sum())
            - float(heat.sum()),
        )
    arrays = {"temperature_k": field, "exact_temperature_k": exact, "nodal_error_k": error}
    for label, matrix in [
        ("K", factor.assembly.stiffness_w_k),
        ("A", factor.A_w_k),
        ("B", factor.B_w_k),
    ]:
        for name in ["data", "indices", "indptr"]:
            arrays[f"{label}_{name}"] = getattr(matrix, name)
    arrays["D_bulk_w_k"] = factor.D_bulk_w_k
    np.savez_compressed(output / "raw-matrices-and-field.npz", **arrays)
    row.update(
        elapsed_s=time.monotonic() - started,
        inputs_sha256=sha(output / "mesh-and-wall-inputs.npz"),
        results_sha256=sha(output / "raw-matrices-and-field.npz"),
    )
    (output / "record.json").write_text(json.dumps(row, indent=2, allow_nan=False) + "\n")
    return row


def worker(case: str, output: Path) -> None:
    started, cpu = time.monotonic(), time.process_time()
    original = load_prior()
    if sha(TRIAL1) != TRIAL1_SHA:
        raise ValueError("Frozen trial1 changed")
    first = json.loads(TRIAL1.read_text())
    cfg = yaml.safe_load(CONFIG.read_text())
    if case == "B_strong":
        cfg = copy.deepcopy(cfg)
        cfg["case_b"]["h_w_m2_k"] = cfg["case_b_strong_h_w_m2_k"]
    source = yaml.safe_load(Path(cfg["verification_source"]).read_text())
    old = next(row for row in original["cases"] if row["case"] == case)
    old1 = next(row for row in first["cases"] if row["case"] == case)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    try:
        for n, a, b in zip(cfg["divisions_per_axis"], old["levels"], old1["levels"]):
            rows.append(level(case, n, cfg, source, a, b, output / f"n-{n}"))
            if not rows[-1]["discrete_algebra_balance_pass"] or (
                case == "A" and not rows[-1]["exact_A_checks_pass"]
            ):
                raise ValueError("Algebra/balance/exactA failure; final trial stops")
        c0, c1 = [np.asarray(row["C_raw_w_k"]) for row in rows[-2:]]
        relative = float(abs(c1 - c0).max() / abs(c1).max())
        fields = []
        for n in cfg["divisions_per_axis"][-2:]:
            with np.load(
                output / f"n-{n}" / "raw-matrices-and-field.npz", allow_pickle=False
            ) as archive:
                fields.append(archive["temperature_k"].reshape((n + 1,) * 3))
        excursion = 265.0 if case == "A" else 100.0
        field_change = float(abs(fields[1][::2, ::2, ::2] - fields[0]).max()) / excursion
        result = {
            "status": "complete_final_trial_no_further_wall_trials",
            "case": case,
            "levels": rows,
            "last_two_C_relative_change": relative,
            "last_two_nested_field_change_over_independent_excursion": field_change,
            "existing5percent_C_and_field_convergence_pass": max(relative, field_change)
            < source["verification"]["convergence_relative_tolerance"],
            "maximum_nodal_error_decreases": all(
                rows[i + 1]["maximum_nodal_error_k"] < rows[i]["maximum_nodal_error_k"]
                for i in range(2)
            ),
            "all_reference_heat_checks_pass": all(
                row["reference_heat_tolerance_pass"] for row in rows
            ),
            "all_continuum_zero_heat_checks_pass": all(
                row.get("physical_continuum_zero_net_heat_tolerance_pass", True) for row in rows
            ),
            "actual_acceptance": False,
        }
    except Exception as exc:  # noqa: BLE001 - preserve failure and never retry
        result = {
            "status": "failed_final_trial_stop_family",
            "case": case,
            "levels": rows,
            "error": repr(exc),
        }
    result.update(elapsed_s=time.monotonic() - started, cpu_s=time.process_time() - cpu)
    (output / "case-record.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("build/wo03-robin-hybrid-trial-v1"))
    parser.add_argument("--worker", choices=["A", "B", "B_strong"])
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, args.output)
        return
    prior = load_prior()
    if sha(TRIAL1) != TRIAL1_SHA:
        raise ValueError("Frozen trial1 changed")
    args.output.mkdir(parents=True, exist_ok=False)
    paths = [
        Path(__file__),
        CONFIG,
        PRIOR / "record.json",
        TRIAL1,
        Path("scripts/wo03_robin_lumped_trial.py"),
        Path("scripts/wo03_thermal_error_isolation.py"),
        Path("src/analysis/robin_gas.py"),
        Path("src/analysis/gas_conduction.py"),
    ]
    hashes = {str(path): sha(path) for path in paths}
    started = time.monotonic()
    cpu0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    rows = []
    for case in ["A", "B", "B_strong"]:
        with (args.output / f"case-{case}.log").open("w") as log:
            try:
                process = subprocess.run(
                    [
                        sys.executable,
                        str(Path(__file__)),
                        "--worker",
                        case,
                        "--output",
                        str(args.output / case),
                    ],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=120,
                    check=False,
                )
                path = args.output / case / "case-record.json"
                rows.append(
                    json.loads(path.read_text())
                    if path.exists()
                    else {"case": case, "status": "worker_failed", "exit_code": process.returncode}
                )
            except subprocess.TimeoutExpired:
                rows.append({"case": case, "status": "incomplete120s_final_trial_stop"})
    cpu1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = {
        "trial_counter": 2,
        "maximum_authorized_trials": 2,
        "wall_treatment_family_finished_no_third_trial": True,
        "cases": rows,
        "source_sha256": hashes,
        "original_source_sha256": prior["source_sha256"],
        "inputs_unchanged": all(sha(Path(path)) == expected for path, expected in hashes.items()),
        "elapsed_s": time.monotonic() - started,
        "all_child_cpu_s": cpu1.ru_utime + cpu1.ru_stime - cpu0.ru_utime - cpu0.ru_stime,
        "one_cpu": True,
        "child_seconds_per_case": 120,
        "total_cpu_cap_s": 600,
        "actual_geometry_mesh_factor_rays_ODE_production_edits_adoption": False,
        "real_interface_jump_treatment": "unresolved; smooth box proof does not establish actual chord/material/opening treatment",
    }
    (args.output / "record.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "output": str(args.output),
                "cases": [
                    {
                        key: row.get(key)
                        for key in [
                            "case",
                            "status",
                            "existing5percent_C_and_field_convergence_pass",
                            "all_reference_heat_checks_pass",
                            "all_continuum_zero_heat_checks_pass",
                            "last_two_C_relative_change",
                            "last_two_nested_field_change_over_independent_excursion",
                        ]
                    }
                    for row in rows
                ],
                "wall_s": result["elapsed_s"],
                "cpu_s": result["all_child_cpu_s"],
                "inputs_unchanged": result["inputs_unchanged"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
