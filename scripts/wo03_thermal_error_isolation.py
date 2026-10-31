"""Independent long-box references around the unchanged production Robin factor.

A: q''=(Th-Tc)/(Lx/k+1/h), T=Th-q''x/k. B: u=T0+a(z²-x²)
is harmonic, a=100/Lz²; Robin effective bulk is u+(k/h)grad(u).n.
Positive tensor Gauss-Legendre/Duffy triangle integration constructs consistent
M/B/D for a two-state convex representation of that varying bulk. References:
Fourier series resistance (DOE-HDBK1012/2-92); manufactured solutions (Roache,
Verification and Validation in Computational Science and Engineering); affine
P1/Freudenthal simplex subdivision; Duffy's reference-triangle transformation.
No Gmsh or actual geometry/PDE/thermal acceptance is used.
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
import itertools
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

from src.analysis.robin_gas import BoundaryCondition, RobinGasMesh, factor_robin_gas


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def structured_box(dimensions: Any, n: int) -> tuple[RobinGasMesh, np.ndarray]:
    """Six conforming Freudenthal tets/cell; no external mesh generator."""
    if not 1 <= n <= 8:
        raise ValueError("Independent fixture divisions must be1..8")
    dims = np.asarray(dimensions, dtype=float)
    axes = [np.linspace(0.0, length, n + 1) for length in dims]
    points = np.array(list(itertools.product(*axes)))
    ids = np.arange(len(points)).reshape((n + 1,) * 3)
    tets = []
    for base in itertools.product(range(n), repeat=3):
        for permutation in itertools.permutations(range(3)):
            index = np.array(base)
            nodes = [int(ids[tuple(index)])]
            for axis in permutation:
                index[axis] += 1
                nodes.append(int(ids[tuple(index)]))
            inversions = sum(
                permutation[i] > permutation[j] for i in range(3) for j in range(i + 1, 3)
            )
            if inversions % 2:
                nodes[1], nodes[2] = nodes[2], nodes[1]
            tets.append(nodes)
    cells = np.array(tets, dtype=np.int64)
    faces = cells[:, [[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]]].reshape(-1, 3)
    _, first, count = np.unique(
        np.sort(faces, axis=1), axis=0, return_index=True, return_counts=True
    )
    if (count > 2).any():
        raise ValueError("Independent structured fixture connectivity invalid")
    boundary = faces[first[count == 1]]
    xyz = points[boundary]
    side = np.full(len(boundary), -1, dtype=np.int64)
    for axis, extent in enumerate(dims):
        side[(xyz[:, :, axis] == 0).all(axis=1)] = axis * 2
        side[(xyz[:, :, axis] == extent).all(axis=1)] = axis * 2 + 1
    if (side < 0).any():
        raise ValueError("A structured boundary facet has no exact box side")
    return (
        RobinGasMesh(
            points,
            cells,
            boundary,
            np.arange(len(boundary)),
            {
                "source": "independent_structured_box",
                "divisions_each_axis": n,
                "six_tets_per_cell": True,
                "dimensions_m": dims.tolist(),
                "aspect_Lz_over_Lx": float(dims[2] / dims[0]),
                "Gmsh_used": False,
            },
        ),
        side,
    )


def triangle_quadrature() -> tuple[np.ndarray, np.ndarray]:
    nodes, raw = np.polynomial.legendre.leggauss(4)
    nodes, weights = (nodes + 1) / 2, raw / 2
    bary, normalized = [], []
    for r, wr in zip(nodes, weights):
        for s, ws in zip(nodes, weights):
            bary.append([1 - r, r * (1 - s), r * s])
            normalized.append(2 * r * wr * ws)
    return np.array(bary), np.array(normalized)


def manufactured(xyz: np.ndarray, cfg: dict[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    a = cfg["case_b"]["amplitude_k"] / cfg["dimensions_m"][2] ** 2
    u = cfg["case_b"]["base_k"] + a * (xyz[..., 2] ** 2 - xyz[..., 0] ** 2)
    gradient = np.zeros_like(xyz)
    gradient[..., 0], gradient[..., 2] = -2 * a * xyz[..., 0], 2 * a * xyz[..., 2]
    return u, gradient


def effective_bulk(xyz: np.ndarray, normal: np.ndarray, cfg: dict[str, Any]) -> np.ndarray:
    u, gradient = manufactured(xyz, cfg)
    return np.asarray(
        u
        + cfg["conductivity_w_m_k"] / cfg["case_b"]["h_w_m2_k"] * np.sum(gradient * normal, axis=-1)
    )


def true_boundary_extrema(cfg: dict[str, Any]) -> dict[str, Any]:
    """Quadratic extrema on all six rectangles, including stationary points."""
    dims = cfg["dimensions_m"]
    kh = cfg["conductivity_w_m_k"] / cfg["case_b"]["h_w_m2_k"]
    values, surface = [], []
    rows = []
    for axis in range(3):
        for sign in [-1, 1]:
            normal = np.eye(3)[axis] * sign
            candidate_axes = []
            for coordinate, extent in enumerate(dims):
                if coordinate == axis:
                    candidates = [0.0 if sign < 0 else extent]
                else:
                    candidates = [0.0, extent]
                    stationary = -kh * normal[coordinate]
                    if coordinate in [0, 2] and 0 < stationary < extent:
                        candidates.append(stationary)
                candidate_axes.append(candidates)
            xyz = np.array(list(itertools.product(*candidate_axes)))
            bulk = effective_bulk(xyz, normal, cfg)
            u, _ = manufactured(xyz, cfg)
            rows.append(
                {
                    "side": axis * 2 + int(sign > 0),
                    "effective_min_k": float(bulk.min()),
                    "effective_max_k": float(bulk.max()),
                }
            )
            values.extend(bulk.tolist())
            surface.extend(u.tolist())
    return {
        "effective_bulk_min_k": min(values),
        "effective_bulk_max_k": max(values),
        "exact_solution_min_k": min(surface),
        "exact_solution_max_k": max(surface),
        "by_side": rows,
        "method": "separable quadratic rectangle extrema at endpoints and any in-face stationary coordinates",
    }


def wall_conditions(
    mesh: RobinGasMesh, sides: np.ndarray, case: str, cfg: dict[str, Any]
) -> tuple[list[BoundaryCondition], dict[str, float], dict[str, float], dict[str, Any]]:
    conditions = []
    extra: dict[str, Any] = {}
    if case == "A":
        for side in sides:
            conditions.append(
                BoundaryCondition("dirichlet", temperature_id="hot")
                if side == 0
                else (
                    BoundaryCondition("robin", bulk_id="cold", h_w_m2_k=cfg["case_a"]["h_w_m2_k"])
                    if side == 1
                    else BoundaryCondition("insulated")
                )
            )
        return (
            conditions,
            {"cold": cfg["case_a"]["cold_bulk_k"]},
            {"hot": cfg["case_a"]["hot_prescribed_k"]},
            extra,
        )
    bary, weight = triangle_quadrature()
    xyz = mesh.points_m[mesh.boundary_triangles]
    cross = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    area = np.linalg.norm(cross, axis=1) / 2
    normal = cross / (2 * area[:, None])
    positions = np.einsum("qi,tij->tqj", bary, xyz)
    u, _ = manufactured(positions, cfg)
    bulk = effective_bulk(positions, normal[:, None, :], cfg)
    cold, hot, h = [cfg["case_b"][key] for key in ["bulk_cold_k", "bulk_hot_k", "h_w_m2_k"]]
    fraction = (bulk - cold) / (hot - cold)
    extrema = true_boundary_extrema(cfg)
    if (
        fraction.min() < 0
        or fraction.max() > 1
        or extrema["effective_bulk_min_k"] < cold
        or extrema["effective_bulk_max_k"] > hot
    ):
        raise ValueError("Manufactured effective bulk outside convex states; no clipping")
    matrices = h * area[:, None, None] * np.einsum("qi,q,qj->ij", bary, weight, bary)
    vectors_cold = h * area[:, None] * np.einsum("q,qi,tq->ti", weight, bary, 1 - fraction)
    vectors_hot = h * area[:, None] * np.einsum("q,qi,tq->ti", weight, bary, fraction)
    for matrix, bc, bh in zip(matrices, vectors_cold, vectors_hot):
        conditions.append(
            BoundaryCondition(
                "robin",
                wall_matrix_w_k=matrix,
                bulk_load_vectors_w_k={"cold": bc, "hot": bh},
                bulk_diagonal_w_k={"cold": float(bc.sum()), "hot": float(bh.sum())},
            )
        )
    extra.update(
        barycentric=bary,
        normalized_weights=weight,
        quadrature_positions_m=positions,
        effective_bulk_k=bulk,
        fraction_hot=fraction,
        exact_u_quadrature_k=u,
        matrices_w_k=matrices,
        Bcold_w_k=vectors_cold,
        Bhot_w_k=vectors_hot,
        area_m2=area,
        outward_normals=normal,
        exact_physical_facet_heat_w=h * area * np.einsum("q,tq->t", weight, u - bulk),
        reference_reservoir_heat={
            "cold": float(np.sum(h * area[:, None] * weight * (1 - fraction) * (u - cold))),
            "hot": float(np.sum(h * area[:, None] * weight * fraction * (u - hot))),
        },
        exact_wall_form_w_k=float(
            np.sum(
                h
                * area[:, None]
                * weight
                * ((1 - fraction) * (u - cold) ** 2 + fraction * (u - hot) ** 2)
            )
        ),
        true_extrema=extrema,
    )
    return conditions, {"cold": cold, "hot": hot}, {}, extra


def run_level(
    case: str, n: int, cfg: dict[str, Any], source_cfg: dict[str, Any], output: Path | None = None
) -> dict[str, Any]:
    started = time.monotonic()
    mesh, sides = structured_box(cfg["dimensions_m"], n)
    conditions, bulk_values, prescribed_values, extra = wall_conditions(mesh, sides, case, cfg)
    if output is not None:
        output.mkdir(parents=True, exist_ok=False)
        inputs = {
            "points_m": mesh.points_m,
            "tetrahedra": mesh.tetrahedra,
            "boundary_triangles": mesh.boundary_triangles,
            "boundary_group_ids": mesh.boundary_group_ids,
            "boundary_sides": sides,
        }
        inputs.update({key: value for key, value in extra.items() if isinstance(value, np.ndarray)})
        np.savez_compressed(output / "mesh-and-wall-inputs.npz", **inputs)
    budget = source_cfg["budget"]
    factor = factor_robin_gas(
        mesh,
        conditions,
        cfg["conductivity_w_m_k"],
        max_tetrahedra=budget["max_tetrahedra"],
        max_nodes=budget["max_nodes"],
        factor_memory_limit_mb=budget["factor_memory_limit_mb"],
        max_factor_free_nodes=budget["max_factor_free_nodes"],
        reduced_map_memory_limit_mb=budget["reduced_map_memory_limit_mb"],
        rhs_block_size=budget["rhs_block_size"],
    )
    bulk = np.array([bulk_values[key] for key in factor.bulk_ids])
    prescribed = np.array([prescribed_values[key] for key in factor.prescribed_ids])
    answer = factor.evaluate(bulk, prescribed, np.zeros(len(factor.group_ids)))
    field = answer.pop("nodal_temperature_k")
    dims, k, v = (
        np.array(cfg["dimensions_m"]),
        cfg["conductivity_w_m_k"],
        source_cfg["verification"],
    )
    reference: dict[str, Any] = {}
    if case == "A":
        hot, cold, h = [
            cfg["case_a"][key] for key in ["hot_prescribed_k", "cold_bulk_k", "h_w_m2_k"]
        ]
        flux = (hot - cold) / (dims[0] / k + 1 / h)
        heat = flux * dims[1] * dims[2]
        exact = hot - flux * mesh.points_m[:, 0] / k
        expected = {"cold": heat, "hot": -heat}
        reference.update(
            flux_w_m2=flux,
            total_series_heat_w=heat,
            exact_cold_surface_k=cold + flux / h,
            exact_total_form_w_k=heat * (hot - cold),
            exact_net_boundary_heat_w=0.0,
        )
        exact_means = exact[mesh.boundary_triangles].mean(axis=1)
        exact_volume_mean = (hot + reference["exact_cold_surface_k"]) / 2
        boundary_low, boundary_high = cold, hot
    else:
        exact, _ = manufactured(mesh.points_m, cfg)
        expected = extra["reference_reservoir_heat"]
        exact_means = np.einsum(
            "q,tq->t", extra["normalized_weights"], extra["exact_u_quadrature_k"]
        )
        exact_volume_mean = (
            cfg["case_b"]["base_k"]
            + cfg["case_b"]["amplitude_k"] * (1 - (dims[0] / dims[2]) ** 2) / 3
        )
        a = cfg["case_b"]["amplitude_k"] / dims[2] ** 2
        exact_air_form = 4 * k * a**2 * float(dims.prod()) * (dims[0] ** 2 + dims[2] ** 2) / 3
        reference.update(
            exact_air_form_w_k=exact_air_form,
            exact_wall_form_w_k=extra["exact_wall_form_w_k"],
            exact_total_form_w_k=exact_air_form + extra["exact_wall_form_w_k"],
            exact_net_boundary_heat_w=0.0,
            quadrature_exact_reference_net_heat_w=float(extra["exact_physical_facet_heat_w"].sum()),
            true_extrema=extra["true_extrema"],
            fraction_hot_min=float(extra["fraction_hot"].min()),
            fraction_hot_max=float(extra["fraction_hot"].max()),
            quadrature_weights_sum=float(extra["normalized_weights"].sum()),
            quadrature_min_weight=float(extra["normalized_weights"].min()),
            exact_laplacian=0.0,
        )
        boundary_low, boundary_high = [
            extra["true_extrema"][key] for key in ["effective_bulk_min_k", "effective_bulk_max_k"]
        ]
    expected_heat = np.array([expected[key] for key in (*factor.bulk_ids, *factor.prescribed_ids)])
    actual_heat = np.r_[answer["heat_into_bulk_w"], answer["heat_into_prescribed_reservoir_w"]]
    error = field - exact
    mean_error = np.asarray(answer["area_mean_temperature_k"]) - exact_means
    volume_mean = float(
        np.sum(factor.assembly.volumes_m3 * field[mesh.tetrahedra].mean(axis=1))
        / factor.assembly.volumes_m3.sum()
    )
    heat_tolerance = v["heat_absolute_tolerance_w"] + v["heat_relative_tolerance"] * float(
        abs(expected_heat).max()
    )
    balance = (
        abs(answer["energy_balance_residual_w"]) < v["heat_absolute_tolerance_w"]
        and abs(answer["form_balance_difference_w_times_k"])
        < v["form_absolute_tolerance_w_times_k"]
    )
    verified = bool(factor.diagnostics["algebra_checks_pass"] and balance)
    exact_checks = bool(
        verified
        and abs(error).max() < v["temperature_absolute_tolerance_k"]
        and abs(actual_heat - expected_heat).max() < heat_tolerance
    )
    side_area = np.bincount(sides, weights=factor.group_areas_m2, minlength=6)
    side_mean = (
        np.bincount(
            sides,
            weights=factor.group_areas_m2 * np.asarray(answer["area_mean_temperature_k"]),
            minlength=6,
        )
        / side_area
    )
    side_exact = (
        np.bincount(sides, weights=factor.group_areas_m2 * exact_means, minlength=6) / side_area
    )
    states = np.r_[bulk, prescribed]
    exact_boundary_work = -float((states - states[0]) @ expected_heat)
    row = {
        "case": case,
        "divisions_each_axis": n,
        "nodes": len(mesh.points_m),
        "tetrahedra": len(mesh.tetrahedra),
        "boundary_facets_and_groups": len(mesh.boundary_triangles),
        "elapsed_s": time.monotonic() - started,
        "production_algebra_and_balance_pass": verified,
        "exact_linear_case_checks_pass": exact_checks if case == "A" else None,
        "approximate_case_not_tested_against_exact_linear_temperature_tolerance": case != "A",
        "dimensions_m": dims.tolist(),
        "conductivity_w_m_k": k,
        "Robin_h_w_m2_k": cfg["case_a" if case == "A" else "case_b"]["h_w_m2_k"],
        "maximum_nodal_error_k": float(abs(error).max()),
        "rms_nodal_error_k": float(np.sqrt(np.mean(error**2))),
        "maximum_facet_mean_error_k": float(abs(mean_error).max()),
        "area_weighted_rms_facet_mean_error_k": float(
            np.sqrt(np.sum(factor.group_areas_m2 * mean_error**2) / factor.group_areas_m2.sum())
        ),
        "volume_mean_k": volume_mean,
        "exact_volume_mean_k": float(exact_volume_mean),
        "volume_mean_error_k": float(volume_mean - exact_volume_mean),
        "physical_side_mean_k": side_mean.tolist(),
        "exact_physical_side_mean_k": side_exact.tolist(),
        "maximum_nodal_error_location_m": mesh.points_m[int(abs(error).argmax())].tolist(),
        "minimum_temperature_location_m": mesh.points_m[int(field.argmin())].tolist(),
        "exact_reference_form_balance_difference_w_k": reference["exact_total_form_w_k"]
        - exact_boundary_work,
        "FE_total_form_error_against_exact_reference_w_k": answer["air_dirichlet_form_w_times_k"]
        + answer["halfwall_dirichlet_form_w_times_k"]
        - reference["exact_total_form_w_k"],
        "physical_boundary_envelope_k": [boundary_low, boundary_high],
        "below_effective_boundary_minimum_k": max(0.0, boundary_low - float(field.min())),
        "above_effective_boundary_maximum_k": max(0.0, float(field.max()) - boundary_high),
        "maximum_reservoir_heat_error_w": float(abs(actual_heat - expected_heat).max()),
        "reservoir_heat_tolerance_w": heat_tolerance,
        "ordered_reservoir_ids": [*factor.bulk_ids, *factor.prescribed_ids],
        "expected_reservoir_heat_w": expected_heat.tolist(),
        "actual_reservoir_heat_w": actual_heat.tolist(),
        "C_raw_w_k": factor.reservoir_conductance_raw_w_k.tolist(),
        "reference": reference,
        "answer": answer,
        "diagnostics": factor.diagnostics,
        "actual_baffle_accuracy_or_temperature_acceptance": False,
    }
    if case != "A":
        interpolated = np.einsum("qi,ti->tq", extra["barycentric"], field[mesh.boundary_triangles])
        physical_heat = (
            cfg["case_b"]["h_w_m2_k"]
            * extra["area_m2"]
            * np.einsum(
                "q,tq->t", extra["normalized_weights"], interpolated - extra["effective_bulk_k"]
            )
        )
        row["independent_facet_heat_error_max_w"] = float(
            abs(physical_heat - extra["exact_physical_facet_heat_w"]).max()
        )
        row["independent_facet_heat_sum_w"] = float(physical_heat.sum())
        row["independent_facet_vs_stable_reservoir_heat_sum_difference_w"] = float(
            physical_heat.sum() - actual_heat.sum()
        )
        partition = extra["matrices_w_k"].sum(axis=2) - extra["Bcold_w_k"] - extra["Bhot_w_k"]
        row["preintegrated_partition_max_w_k"] = float(abs(partition).max())
    if output is not None:
        arrays = {
            "points_m": mesh.points_m,
            "tetrahedra": mesh.tetrahedra,
            "boundary_triangles": mesh.boundary_triangles,
            "boundary_group_ids": mesh.boundary_group_ids,
            "boundary_sides": sides,
            "temperature_k": field,
            "exact_temperature_k": exact,
            "nodal_error_k": error,
            "exact_facet_mean_k": exact_means,
        }
        arrays.update({key: value for key, value in extra.items() if isinstance(value, np.ndarray)})
        np.savez_compressed(output / "arrays.npz", **arrays)
        row["arrays_sha256"] = sha(output / "arrays.npz")
        row["input_arrays_sha256"] = sha(output / "mesh-and-wall-inputs.npz")
        (output / "record.json").write_text(json.dumps(row, indent=2, allow_nan=False) + "\n")
    return row


def case_worker(case: str, cfg: dict[str, Any], output: Path) -> None:
    started = time.monotonic()
    cpu_start = time.process_time()
    if case == "B_strong":
        cfg = copy.deepcopy(cfg)
        cfg["case_b"]["h_w_m2_k"] = cfg["case_b_strong_h_w_m2_k"]
    source = yaml.safe_load(Path(cfg["verification_source"]).read_text())
    rows = []
    output.mkdir(parents=True, exist_ok=False)
    try:
        for n in cfg["divisions_per_axis"]:
            rows.append(run_level(case, n, cfg, source, output / f"n-{n}"))
        matrices = [np.asarray(row["C_raw_w_k"]) for row in rows]
        relative = float(abs(matrices[-1] - matrices[-2]).max() / abs(matrices[-1]).max())
        decreasing = all(
            rows[i + 1]["maximum_nodal_error_k"] < rows[i]["maximum_nodal_error_k"]
            for i in range(2)
        )
        previous, fine = cfg["divisions_per_axis"][-2:]
        fields = []
        for division in [previous, fine]:
            with np.load(output / f"n-{division}" / "arrays.npz", allow_pickle=False) as archive:
                fields.append(archive["temperature_k"].reshape((division + 1,) * 3))
        stride = fine // previous
        nested_change = float(abs(fields[1][::stride, ::stride, ::stride] - fields[0]).max())
        reference_excursion = (
            cfg["case_b"]["amplitude_k"]
            if case != "A"
            else cfg["case_a"]["hot_prescribed_k"] - cfg["case_a"]["cold_bulk_k"]
        )
        field_relative = nested_change / reference_excursion
        result = {
            "status": "complete",
            "case": case,
            "levels": rows,
            "last_two_C_relative_change": relative,
            "existing5percent_C_convergence_pass": relative
            < source["verification"]["convergence_relative_tolerance"],
            "last_two_nested_nodal_change_k": nested_change,
            "last_two_nested_nodal_change_over_independent_excursion": field_relative,
            "existing5percent_field_change_pass": field_relative
            < source["verification"]["convergence_relative_tolerance"],
            "maximum_nodal_error_decreases_each_refinement": decreasing,
            "case_A_exact_checks_all_pass": (
                all(row["exact_linear_case_checks_pass"] for row in rows) if case == "A" else None
            ),
            "case_B_approximate_convergence_pass": (
                decreasing
                and max(relative, field_relative)
                < source["verification"]["convergence_relative_tolerance"]
                and all(row["production_algebra_and_balance_pass"] for row in rows)
                if case != "A"
                else None
            ),
            "actual_baffle_accuracy_or_temperature_acceptance": False,
        }
    except Exception as exc:  # noqa: BLE001 - preserve every failed fixture/partial row
        result = {
            "status": "invalid_or_incomplete",
            "case": case,
            "levels": rows,
            "error": repr(exc),
        }
    result.update(
        elapsed_s=time.monotonic() - started,
        cpu_s=time.process_time() - cpu_start,
        max_rss_bytes=int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            * (1 if sys.platform == "darwin" else 1024)
        ),
    )
    (output / "case-record.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-thermal-error-isolation.yaml")
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", choices=["A", "B", "B_strong"])
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    output = args.output or Path(cfg["default_output"])
    if args.worker:
        case_worker(args.worker, cfg, output)
        return
    if (
        cfg["budget"]["threads"] != 1
        or cfg["budget"]["child_seconds_per_case_all_levels"] > 120
        or cfg["budget"]["total_cpu_seconds"] > 600
        or max(cfg["divisions_per_axis"]) > 8
    ):
        raise ValueError("Retain authorized oneCPU/120s child/600s total/8division caps")
    output.mkdir(parents=True, exist_ok=False)
    paths = [
        args.config,
        Path(__file__),
        Path(cfg["verification_source"]),
        Path("src/analysis/robin_gas.py"),
        Path("src/analysis/gas_conduction.py"),
    ]
    hashes = {str(path): sha(path) for path in paths}
    rows = []
    started = time.monotonic()
    before_cpu = resource.getrusage(resource.RUSAGE_CHILDREN)
    if (
        len(cfg["cases"]) * cfg["budget"]["child_seconds_per_case_all_levels"]
        > cfg["budget"]["total_cpu_seconds"]
    ):
        raise ValueError("Child wall caps exceed600CPU s aggregate allowance")
    for case in cfg["cases"]:
        with (output / f"case-{case}.log").open("w") as log:
            try:
                process = subprocess.run(
                    [
                        sys.executable,
                        str(Path(__file__)),
                        "--config",
                        str(args.config),
                        "--output",
                        str(output / case),
                        "--worker",
                        case,
                    ],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=cfg["budget"]["child_seconds_per_case_all_levels"],
                    check=False,
                )
                record_path = output / case / "case-record.json"
                rows.append(
                    json.loads(record_path.read_text())
                    if record_path.exists()
                    else {"case": case, "status": "worker_failed", "exit_code": process.returncode}
                )
            except subprocess.TimeoutExpired:
                rows.append(
                    {"case": case, "status": "incomplete120s_cap", "complete_calculation": False}
                )
    after_cpu = resource.getrusage(resource.RUSAGE_CHILDREN)
    result = {
        "cases": rows,
        "source_sha256": hashes,
        "inputs_unchanged": hashes == {str(path): sha(path) for path in paths},
        "elapsed_s": time.monotonic() - started,
        "returned_case_cpu_s": sum(row.get("cpu_s", 0.0) for row in rows),
        "all_child_cpu_including_startup_imports_s": after_cpu.ru_utime
        + after_cpu.ru_stime
        - before_cpu.ru_utime
        - before_cpu.ru_stime,
        "one_cpu": True,
        "maximum_case_children": len(cfg["cases"]),
        "per_case_all_levels_wall_cap_s": 120,
        "total_cpu_cap_s": 600,
        "corrective_trials": 0,
        "actual_geometry_mesh_factor_rays_or_adoption": False,
    }
    (output / "record.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                "output": str(output),
                "cases": [
                    {
                        key: row.get(key)
                        for key in [
                            "case",
                            "status",
                            "case_A_exact_checks_all_pass",
                            "case_B_approximate_convergence_pass",
                            "last_two_C_relative_change",
                        ]
                    }
                    for row in rows
                ],
                "elapsed_s": result["elapsed_s"],
                "inputs_unchanged": result["inputs_unchanged"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
