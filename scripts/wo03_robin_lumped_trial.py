"""One separate vertex-quadrature Robin trial; no production changes.

Triangle vertex quadrature is Q(g)=A/3 sum_i g(v_i). Hence M=hA/3 I,
B_c=hA/3(1-f_i), B_h=hA/3 f_i, D=sum B. This quadrature is exact for
affine functions, not quadratic manufactured boundary data. References:
standard P1 nodal quadrature/mass lumping (Thomee, Galerkin Finite Element
Methods for Parabolic Problems, lumped mass method); frozen independent
Fourier/harmonic fixtures in wo03_thermal_error_isolation.py. No saved failed
actual matrix is modified or repaired. Actual volume monotonicity and real
material-interface quadrature remain separate unresolved conditions.
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
import hashlib
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

from scripts.wo03_thermal_error_isolation import (
    effective_bulk,
    sha,
    structured_box,
    wall_conditions,
)
from src.analysis.gas_conduction import assemble_tetra_conductivity
from src.analysis.robin_gas import BoundaryCondition, RobinGasMesh, factor_robin_gas

CONFIG = Path("configs/studies/wo03-thermal-error-isolation.yaml")
PRIOR = Path("build/wo03-thermal-error-isolation-v1")
PRIOR_RECORD_SHA = "bb0075ef2b8e4ece43a818345b6af29a83d2664e59257a6e9c7bfcb9e12915e7"


def array_sha(*arrays: Any) -> str:
    digest = hashlib.sha256()
    for array in arrays:
        value = np.asarray(array)
        digest.update(str(value.shape).encode())
        digest.update(str(value.dtype).encode())
        digest.update(value.tobytes())
    return digest.hexdigest()


def fixture() -> dict[str, Any]:
    area, h = 2.0, 3.0
    f = np.array([0.1, 0.4, 0.9])
    m = h * area / 3 * np.eye(3)
    bc, bh = h * area / 3 * (1 - f), h * area / 3 * f
    t, cold, hot = np.array([301.0, 317.0, 325.0]), 300.0, 420.0
    explicit = float(h * area / 3 * np.sum((1 - f) * (t - cold) ** 2 + f * (t - hot) ** 2))
    form = float(
        t @ m @ t - 2 * t @ (bc * cold + bh * hot) + bc.sum() * cold**2 + bh.sum() * hot**2
    )
    if not np.allclose(m @ np.ones(3), bc + bh, rtol=0, atol=1e-15) or abs(form - explicit) > 1e-9:
        raise ValueError("Vertex quadrature partition/independent energy fixture failed")
    return {
        "passed": True,
        "M_is_diagonal_hA_over3": True,
        "B_D_partition": True,
        "independent_energy_difference_w_k": form - explicit,
        "factor_or_actual_geometry_used": False,
    }


def load_prior() -> dict[str, Any]:
    if sha(PRIOR / "record.json") != PRIOR_RECORD_SHA:
        raise ValueError("Frozen consistent-method record changed")
    prior: dict[str, Any] = json.loads((PRIOR / "record.json").read_text())
    if not all(sha(Path(path)) == expected for path, expected in prior["source_sha256"].items()):
        raise ValueError("Frozen fixture equations/config/production sources changed")
    return prior


def lumped_conditions(
    mesh: RobinGasMesh, sides: np.ndarray, case: str, cfg: dict[str, Any]
) -> tuple[list[BoundaryCondition], dict[str, float], dict[str, float], dict[str, Any]]:
    xyz = mesh.points_m[mesh.boundary_triangles]
    cross = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    area = np.linalg.norm(cross, axis=1) / 2
    normal = cross / (2 * area[:, None])
    conditions: list[BoundaryCondition] = []
    _, bulk, prescribed, exact = wall_conditions(mesh, sides, case, cfg)
    h = cfg["case_a" if case == "A" else "case_b"]["h_w_m2_k"]
    matrices = h * area[:, None, None] / 3 * np.eye(3)
    bc, bh = np.zeros((len(area), 3)), np.zeros((len(area), 3))
    f = np.zeros((len(area), 3))
    if case != "A":
        f = (effective_bulk(xyz, normal[:, None, :], cfg) - bulk["cold"]) / (
            bulk["hot"] - bulk["cold"]
        )
        if f.min() < 0 or f.max() > 1:
            raise ValueError("Nodal analytic fraction outside[0,1]; no clipping")
    for i, side in enumerate(sides):
        if case == "A" and side != 1:
            conditions.append(
                BoundaryCondition("dirichlet", temperature_id="hot")
                if side == 0
                else BoundaryCondition("insulated")
            )
            matrices[i] = 0.0  # This face has no Robin condition, not a repaired operator.
            continue
        bc[i] = h * area[i] / 3 * (1 - f[i])
        vectors = {"cold": bc[i]}
        if case != "A":
            bh[i] = h * area[i] / 3 * f[i]
            vectors["hot"] = bh[i]
        conditions.append(
            BoundaryCondition(
                "robin",
                wall_matrix_w_k=matrices[i],
                bulk_load_vectors_w_k=vectors,
                bulk_diagonal_w_k={name: float(value.sum()) for name, value in vectors.items()},
            )
        )
    return (
        conditions,
        bulk,
        prescribed,
        {
            "matrix_w_k": matrices,
            "Bcold_w_k": bc,
            "Bhot_w_k": bh,
            "D_w_k": np.column_stack([bc.sum(axis=1), bh.sum(axis=1)]),
            "nodal_fraction_hot": f,
            "area_m2": area,
            "normal": normal,
            "exact": exact,
        },
    )


def run_level(
    case: str,
    n: int,
    cfg: dict[str, Any],
    tolerances: dict[str, Any],
    prior_level: dict[str, Any],
    output: Path,
) -> dict[str, Any]:
    started = time.monotonic()
    mesh, sides = structured_box(cfg["dimensions_m"], n)
    old_dir = PRIOR / case / f"n-{n}"
    if (
        sha(old_dir / "mesh-and-wall-inputs.npz") != prior_level["input_arrays_sha256"]
        or sha(old_dir / "arrays.npz") != prior_level["arrays_sha256"]
    ):
        raise ValueError("Frozen prior fixture arrays changed")
    with np.load(old_dir / "mesh-and-wall-inputs.npz", allow_pickle=False) as archive:
        if not all(
            np.array_equal(getattr(mesh, key), archive[key])
            for key in ["points_m", "tetrahedra", "boundary_triangles", "boundary_group_ids"]
        ):
            raise ValueError("Structured fixture mesh differs from prior")
    conditions, bulks, prescribed, wall = lumped_conditions(mesh, sides, case, cfg)
    extra = wall.pop("exact")
    source_signature = array_sha(
        *[wall[key] for key in ["matrix_w_k", "Bcold_w_k", "Bhot_w_k", "D_w_k"]]
    )
    output.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(
        output / "mesh-and-wall-inputs.npz",
        points_m=mesh.points_m,
        tetrahedra=mesh.tetrahedra,
        boundary_triangles=mesh.boundary_triangles,
        boundary_group_ids=mesh.boundary_group_ids,
        boundary_sides=sides,
        **wall,
    )
    factor = factor_robin_gas(mesh, conditions, cfg["conductivity_w_m_k"])
    reference_k = assemble_tetra_conductivity(
        mesh.points_m, mesh.tetrahedra, cfg["conductivity_w_m_k"]
    ).stiffness_w_k
    volume_k_identical = all(
        np.array_equal(getattr(reference_k, key), getattr(factor.assembly.stiffness_w_k, key))
        for key in ["data", "indices", "indptr"]
    )
    before = array_sha(
        *[
            getattr(matrix, key)
            for matrix in [factor.assembly.stiffness_w_k, factor.A_w_k, factor.B_w_k]
            for key in ["data", "indices", "indptr"]
        ],
        factor.D_bulk_w_k,
    )
    bulk = np.array([bulks[name] for name in factor.bulk_ids])
    physical = np.array([prescribed[name] for name in factor.prescribed_ids])
    answer = factor.evaluate(bulk, physical, np.zeros(len(factor.group_ids)))
    field = answer.pop("nodal_temperature_k")
    after = array_sha(
        *[
            getattr(matrix, key)
            for matrix in [factor.assembly.stiffness_w_k, factor.A_w_k, factor.B_w_k]
            for key in ["data", "indices", "indptr"]
        ],
        factor.D_bulk_w_k,
    )
    if (
        before != after
        or not volume_k_identical
        or source_signature
        != array_sha(*[wall[key] for key in ["matrix_w_k", "Bcold_w_k", "Bhot_w_k", "D_w_k"]])
    ):
        raise ValueError("VolumeK/source terms/raw matrices mutated")
    with np.load(old_dir / "arrays.npz", allow_pickle=False) as archive:
        exact = archive["exact_temperature_k"]
        exact_means = archive["exact_facet_mean_k"]
        prior_field = archive["temperature_k"]
    error = field - exact
    mean_error = np.asarray(answer["area_mean_temperature_k"]) - exact_means
    volume_mean = float(
        np.sum(factor.assembly.volumes_m3 * field[mesh.tetrahedra].mean(axis=1))
        / factor.assembly.volumes_m3.sum()
    )
    heat = np.r_[answer["heat_into_bulk_w"], answer["heat_into_prescribed_reservoir_w"]]
    expected_heat = np.array(prior_level["expected_reservoir_heat_w"])
    v = tolerances["verification"]
    algebra_balance = bool(
        factor.diagnostics["algebra_checks_pass"]
        and abs(answer["energy_balance_residual_w"]) < v["heat_absolute_tolerance_w"]
        and abs(answer["form_balance_difference_w_times_k"])
        < v["form_absolute_tolerance_w_times_k"]
    )
    lo, hi = prior_level["physical_boundary_envelope_k"]
    row: dict[str, Any] = {
        "case": case,
        "divisions_each_axis": n,
        "fixture_mesh_bitwise_equal_to_consistent_prior": True,
        "volume_K_bitwise_equal_to_unchanged_assembler_replay": volume_k_identical,
        "raw_K_A_B_D_unchanged_after_construction": before == after,
        "raw_wall_terms_unchanged": True,
        "nodes": len(mesh.points_m),
        "tetrahedra": len(mesh.tetrahedra),
        "Robin_h_w_m2_k": cfg["case_a" if case == "A" else "case_b"]["h_w_m2_k"],
        "maximum_nodal_error_k": float(abs(error).max()),
        "maximum_facet_mean_error_k": float(abs(mean_error).max()),
        "area_weighted_RMS_facet_mean_error_k": float(
            np.sqrt(np.sum(factor.group_areas_m2 * mean_error**2) / factor.group_areas_m2.sum())
        ),
        "volume_mean_error_k": volume_mean - prior_level["exact_volume_mean_k"],
        "physical_effective_boundary_envelope_k": [lo, hi],
        "below_true_effective_boundary_minimum_k": max(0.0, lo - float(field.min())),
        "above_true_effective_boundary_maximum_k": max(0.0, float(field.max()) - hi),
        "maximum_reservoir_heat_error_w": float(abs(heat - expected_heat).max()),
        "exact_reference_heat_tolerance_pass": bool(
            abs(heat - expected_heat).max() < prior_level["reservoir_heat_tolerance_w"]
        ),
        "production_discrete_algebra_energy_form_pass": algebra_balance,
        "exact_A_temperature_heat_balance_pass": (
            bool(
                algebra_balance
                and abs(error).max() < v["temperature_absolute_tolerance_k"]
                and abs(heat - expected_heat).max() < prior_level["reservoir_heat_tolerance_w"]
            )
            if case == "A"
            else None
        ),
        "expected_continuum_reservoir_heat_w": expected_heat.tolist(),
        "actual_lumped_discrete_reservoir_heat_w": heat.tolist(),
        "C_raw_w_k": factor.reservoir_conductance_raw_w_k.tolist(),
        "answer": answer,
        "diagnostics": factor.diagnostics,
        "prior_consistent": {
            key: prior_level[key]
            for key in [
                "maximum_nodal_error_k",
                "maximum_facet_mean_error_k",
                "volume_mean_error_k",
                "maximum_reservoir_heat_error_w",
                "below_effective_boundary_minimum_k",
            ]
        },
        "field_change_from_prior_max_k": float(abs(field - prior_field).max()),
        "actual_mesh_or_operator_qualified": False,
    }
    if case != "A":
        weight, bary, h = (
            extra["normalized_weights"],
            extra["barycentric"],
            cfg["case_b"]["h_w_m2_k"],
        )
        interpolated = np.einsum("qi,ti->tq", bary, field[mesh.boundary_triangles])
        continuum_heat = (
            h
            * wall["area_m2"]
            * np.einsum("q,tq->t", weight, interpolated - extra["effective_bulk_k"])
        )
        cold, hot = bulks["cold"], bulks["hot"]
        source_lumped = (hot - cold) * float(wall["Bhot_w_k"].sum())
        source_exact = (hot - cold) * float(extra["Bhot_w_k"].sum())
        row.update(
            nodal_fraction_hot_min=float(wall["nodal_fraction_hot"].min()),
            nodal_fraction_hot_max=float(wall["nodal_fraction_hot"].max()),
            maximum_boundary_quadrature_point_error_k=float(
                abs(interpolated - extra["exact_u_quadrature_k"]).max()
            ),
            physical_continuum_net_heat_w=float(continuum_heat.sum()),
            physical_continuum_zero_net_heat_tolerance_pass=bool(
                abs(continuum_heat.sum()) < v["heat_absolute_tolerance_w"]
            ),
            source_shifted_forcing_lumped_w=source_lumped,
            source_shifted_forcing_exact_w=source_exact,
            nodal_source_integration_error_w=source_lumped - source_exact,
            continuum_heat_minus_source_quadrature_defect_w=float(continuum_heat.sum())
            - (source_lumped - source_exact),
            Bcold_triangle_max_integration_error_w_k=float(
                abs(wall["Bcold_w_k"] - extra["Bcold_w_k"]).max()
            ),
            Bhot_triangle_max_integration_error_w_k=float(
                abs(wall["Bhot_w_k"] - extra["Bhot_w_k"]).max()
            ),
            M_triangle_max_changed_entry_w_k=float(
                abs(wall["matrix_w_k"] - extra["matrices_w_k"]).max()
            ),
            maximum_continuum_facet_heat_error_w=float(
                abs(continuum_heat - extra["exact_physical_facet_heat_w"]).max()
            ),
        )
    arrays = {
        "temperature_k": field,
        "exact_temperature_k": exact,
        "nodal_error_k": error,
        "prior_consistent_temperature_k": prior_field,
    }
    for name, matrix in [
        ("K", factor.assembly.stiffness_w_k),
        ("A", factor.A_w_k),
        ("B", factor.B_w_k),
    ]:
        for key in ["data", "indices", "indptr"]:
            arrays[f"{name}_{key}"] = getattr(matrix, key)
    arrays["D_bulk_w_k"] = factor.D_bulk_w_k
    np.savez_compressed(output / "raw-matrices-and-field.npz", **arrays)
    row.update(
        elapsed_s=time.monotonic() - started,
        input_arrays_sha256=sha(output / "mesh-and-wall-inputs.npz"),
        result_arrays_sha256=sha(output / "raw-matrices-and-field.npz"),
    )
    (output / "record.json").write_text(json.dumps(row, indent=2, allow_nan=False) + "\n")
    return row


def worker(case: str, output: Path) -> None:
    started, cpu_start = time.monotonic(), time.process_time()
    prior = load_prior()
    cfg = yaml.safe_load(CONFIG.read_text())
    if case == "B_strong":
        cfg = copy.deepcopy(cfg)
        cfg["case_b"]["h_w_m2_k"] = cfg["case_b_strong_h_w_m2_k"]
    source_cfg = yaml.safe_load(Path(cfg["verification_source"]).read_text())
    baseline = next(row for row in prior["cases"] if row["case"] == case)
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    try:
        for n, old in zip(cfg["divisions_per_axis"], baseline["levels"]):
            row = run_level(case, n, cfg, source_cfg, old, output / f"n-{n}")
            rows.append(row)
            if not row["production_discrete_algebra_energy_form_pass"] or (
                case == "A" and not row["exact_A_temperature_heat_balance_pass"]
            ):
                raise ValueError("Discrete algebra/balance or exactA failed; stop this trial case")
        c0, c1 = [np.array(row["C_raw_w_k"]) for row in rows[-2:]]
        change = float(abs(c1 - c0).max() / abs(c1).max())
        result = {
            "status": "complete_trial_not_acceptance",
            "case": case,
            "levels": rows,
            "last_two_C_relative_change": change,
            "existing5percent_C_convergence_pass": change
            < source_cfg["verification"]["convergence_relative_tolerance"],
            "maximum_nodal_error_decreases": all(
                rows[i + 1]["maximum_nodal_error_k"] < rows[i]["maximum_nodal_error_k"]
                for i in range(2)
            ),
            "continuum_quadrature_energy_acceptance": all(
                row.get("physical_continuum_zero_net_heat_tolerance_pass", True) for row in rows
            ),
            "local_true_boundary_envelope_pass_all_levels": all(
                max(
                    row["below_true_effective_boundary_minimum_k"],
                    row["above_true_effective_boundary_maximum_k"],
                )
                < source_cfg["verification"]["temperature_absolute_tolerance_k"]
                for row in rows
            ),
            "actual_operator_qualification": False,
        }
    except Exception as exc:  # noqa: BLE001 - preserve every completed result and stop
        result = {
            "status": "failed_or_incomplete_stop_no_retry",
            "case": case,
            "levels": rows,
            "error": repr(exc),
        }
    result.update(elapsed_s=time.monotonic() - started, cpu_s=time.process_time() - cpu_start)
    (output / "case-record.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("build/wo03-robin-lumped-trial-v1"))
    parser.add_argument("--worker", choices=["A", "B", "B_strong"])
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, args.output)
        return
    prior = load_prior()
    check = fixture()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = [
        Path(__file__),
        PRIOR / "record.json",
        CONFIG,
        Path("scripts/wo03_thermal_error_isolation.py"),
        Path("src/analysis/robin_gas.py"),
        Path("src/analysis/gas_conduction.py"),
    ]
    hashes = {str(path): sha(path) for path in sources}
    started = time.monotonic()
    before_cpu = resource.getrusage(resource.RUSAGE_CHILDREN)
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
                rows.append({"case": case, "status": "incomplete120s_cap"})
    after_cpu = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = {
        "corrective_treatment_trial_counter": 1,
        "maximum_authorized_trials": 2,
        "this_script_executes_only_one_trial": True,
        "cases": rows,
        "algebra_fixture": check,
        "source_sha256": hashes,
        "prior_sources_sha256": prior["source_sha256"],
        "inputs_unchanged": all(sha(Path(path)) == expected for path, expected in hashes.items()),
        "elapsed_s": time.monotonic() - started,
        "all_child_cpu_s": after_cpu.ru_utime
        + after_cpu.ru_stime
        - before_cpu.ru_utime
        - before_cpu.ru_stime,
        "one_cpu": True,
        "per_case_seconds_cap": 120,
        "total_cpu_seconds_cap": 600,
        "no_automatic_retry_or_second_treatment": True,
        "actual_geometry_mesh_factor_rays_ODE_adoption": False,
        "real_material_interface_and_jump_treatment": "unresolved; no vertex ownership/averaging rule authorized",
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
                            "local_true_boundary_envelope_pass_all_levels",
                            "continuum_quadrature_energy_acceptance",
                            "last_two_C_relative_change",
                        ]
                    }
                    for row in rows
                ],
                "elapsed_s": result["elapsed_s"],
                "cpu_s": result["all_child_cpu_s"],
                "inputs_unchanged": result["inputs_unchanged"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
