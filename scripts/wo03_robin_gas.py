"""Source-independent Robin/Neumann/prescribed-temperature gas FEM fixtures."""

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
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.gas_conduction import _positive_offdiagonal, assemble_tetra_conductivity
from src.analysis.robin_gas import BoundaryCondition, RobinGasMesh, factor_robin_gas


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture_mesh(fixture: str, level: int, cfg: dict[str, Any]) -> tuple[RobinGasMesh, Path]:
    name = "insulated_divider" if fixture == "insulated_divider" else "slab"
    path = Path(cfg["source_fixture_root"]) / name / f"level-{level}" / "mesh.npz"
    with np.load(path, allow_pickle=False) as data:
        points, tets = data["points_m"], data["tetrahedra"]
    a = assemble_tetra_conductivity(points, tets, cfg["conductivity_w_m_k"])
    faces = a.exterior_triangles.copy()
    xyz = points[faces]
    sign = np.sum(
        np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
        * (points[a.exterior_opposite_nodes] - xyz[:, 0]),
        axis=1,
    )
    flip = sign > 0
    faces[flip, 1], faces[flip, 2] = faces[flip, 2].copy(), faces[flip, 1].copy()
    length, width, height = cfg["slab"]["dimensions_m"]
    centers = points[faces].mean(axis=1)
    ids = np.full(len(faces), -1, dtype=np.int64)
    for axis, extent in enumerate((length, width, height)):
        ids[np.abs(centers[:, axis]) < 1e-12] = axis * 2
        ids[np.abs(centers[:, axis] - extent) < 1e-12] = axis * 2 + 1
    if fixture == "insulated_divider":
        ids[ids < 0] = 6  # explicitly insulated cut faces
    if np.any(ids < 0):
        raise ValueError("Fixture face classification incomplete")
    return (
        RobinGasMesh(
            points,
            tets,
            faces,
            ids,
            {
                "source": "independent_fixture_not_rocket",
                "source_mesh_npz_sha256": sha(path),
                "boundary_orientation": "Derived outward from positive source tetrahedra",
                "all_boundary_faces_explicit": True,
            },
        ),
        path,
    )


def worker(
    config: Path, fixture: str, level: int, output: Path, ordering: str = "COLAMD"
) -> dict[str, Any]:
    started = time.monotonic()
    cfg = yaml.safe_load(config.read_text())
    mesh, source = fixture_mesh(fixture, level, cfg)
    s = cfg["slab"]
    hhot = s["hot_halfwall_conductivity_w_m_k"] / s["hot_halfwall_length_m"]
    hcold = s["cold_halfwall_conductivity_w_m_k"] / s["cold_halfwall_length_m"]
    conditions = {
        int(g): BoundaryCondition("insulated") for g in np.unique(mesh.boundary_group_ids)
    }
    temperatures = {}
    prescribed = {}
    if fixture in ["finite_halfwall_slab", "insulated_divider"]:
        conditions[0] = BoundaryCondition("robin", bulk_id="hot_bulk", h_w_m2_k=hhot)
        conditions[1] = BoundaryCondition("robin", bulk_id="cold_bulk", h_w_m2_k=hcold)
        temperatures = {"hot_bulk": s["hot_bulk_k"], "cold_bulk": s["cold_bulk_k"]}
    elif fixture == "shared_corner":
        for g in range(6):
            conditions[g] = BoundaryCondition(
                "robin",
                bulk_id=f"component{g}",
                h_w_m2_k=cfg["shared_corner"]["h_by_face_w_m2_k"][g],
            )
            temperatures[f"component{g}"] = cfg["shared_corner"]["bulk_temperature_by_face_k"][g]
    elif fixture == "mixed_prescribed":
        conditions = {
            g: BoundaryCondition("robin", bulk_id="wall", h_w_m2_k=2 + g) for g in range(6)
        }
        conditions[0] = BoundaryCondition("dirichlet", temperature_id="physical_gas_ambient")
        temperatures = {"wall": cfg["mixed_prescribed"]["ambient_surface_k"]}
        prescribed = {"physical_gas_ambient": cfg["mixed_prescribed"]["ambient_surface_k"]}
    else:
        raise ValueError("Unknown independent fixture")
    budget = cfg["budget"]
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
        ordering=ordering,
    )
    bulk = np.array([temperatures[x] for x in factor.bulk_ids])
    physical = np.array([prescribed[x] for x in factor.prescribed_ids])
    q = np.zeros(len(factor.group_ids))
    gindex = {g: i for i, g in enumerate(factor.group_ids)}
    nb = len(factor.bulk_ids)
    expected_heat = np.zeros(nb + len(factor.prescribed_ids))
    length, width, height = s["dimensions_m"]
    area = width * height
    if fixture == "finite_halfwall_slab":
        q[gindex[0]] = s["hot_surface_neumann_w"]
        rhot, rair, rcold = (
            1 / (hhot * area),
            length / (cfg["conductivity_w_m_k"] * area),
            1 / (hcold * area),
        )
        flow = (s["hot_bulk_k"] - s["cold_bulk_k"] + q[gindex[0]] * rhot) / (rhot + rair + rcold)
        left = s["hot_bulk_k"] + (q[gindex[0]] - flow) * rhot
        right = s["cold_bulk_k"] + flow * rcold
        exact = left + (right - left) * np.asarray(mesh.points_m)[:, 0] / length
        expected_heat[factor.bulk_ids.index("hot_bulk")] = q[gindex[0]] - flow
        expected_heat[factor.bulk_ids.index("cold_bulk")] = flow
        analytic = {
            "formula": "q_air=(Th-Tc+Qhot*Rhot)/(Rhot+Rair+Rcold); gas surface endpoints include finite halfwall drops",
            "series_resistances_k_w": [rhot, rair, rcold],
            "air_heat_w": flow,
            "surface_end_temperature_k": [left, right],
            "zero_load_series_conductance_w_k": 1 / (rhot + rair + rcold),
        }
    elif fixture == "insulated_divider":
        exact = np.where(
            np.asarray(mesh.points_m)[:, 0] < length / 2, s["hot_bulk_k"], s["cold_bulk_k"]
        )
        analytic = {
            "formula": "Absent-air/insulated divider leaves two components, each one Robin bulk; zero intercomponent heat"
        }
    elif fixture == "shared_corner":
        target = cfg["shared_corner"]["exact_surface_k"]
        for i, g in enumerate(factor.group_ids):
            wall = conditions[g]
            q[i] = wall.h_w_m2_k * factor.group_areas_m2[i] * (target - temperatures[wall.bulk_id])
            expected_heat[factor.bulk_ids.index(wall.bulk_id)] += q[i]
        exact = np.full(len(mesh.points_m), target)
        analytic = {
            "formula": "Qgroup=h*A*(Tsurface_exact-Tbulk) cancels each finite Robin face independently, even at shared vertices; exact constant gasT",
            "different_bulk_states_share_corners": True,
        }
    else:
        q[gindex[0]] = cfg["mixed_prescribed"]["prescribed_surface_neumann_w"]
        expected_heat[nb] = q[gindex[0]]
        exact = np.full(len(mesh.points_m), cfg["mixed_prescribed"]["ambient_surface_k"])
        analytic = {
            "formula": "Uniform equal physical temperatures; surface Neumann load on prescribed face goes exactly to prescribed reservoir reaction; Robin bulk heat zero",
            "physical_gas_temperature_not_radiative_brightness": True,
        }
    answer = factor.evaluate(bulk, physical, q)
    field = answer.pop("nodal_temperature_k")
    temperature_error = float(np.abs(field - exact).max())
    heat = np.r_[answer["heat_into_bulk_w"], answer["heat_into_prescribed_reservoir_w"]]
    heat_error = heat - expected_heat
    output.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output / "mesh.npz",
        points_m=mesh.points_m,
        tetrahedra=mesh.tetrahedra,
        boundary_triangles=mesh.boundary_triangles,
        boundary_group_ids=mesh.boundary_group_ids,
    )
    np.savez_compressed(output / "nodal-field.npz", temperature_k=field, exact_temperature_k=exact)
    v = cfg["verification"]
    heat_tol = v["heat_absolute_tolerance_w"] + v["heat_relative_tolerance"] * float(
        np.abs(expected_heat).max()
    )
    verified = bool(
        factor.diagnostics["algebra_checks_pass"]
        and temperature_error < v["temperature_absolute_tolerance_k"]
        and float(np.abs(heat_error).max()) < heat_tol
        and abs(answer["energy_balance_residual_w"]) < v["heat_absolute_tolerance_w"]
        and abs(answer["form_balance_difference_w_times_k"])
        < v["form_absolute_tolerance_w_times_k"]
    )
    report = {
        "fixture": fixture,
        "level": level,
        "elapsed_s": time.monotonic() - started,
        "source_mesh": str(source),
        "source_mesh_sha256": sha(source),
        "metadata": mesh.metadata,
        "bulk_temperature_k": bulk.tolist(),
        "prescribed_physical_temperature_k": physical.tolist(),
        "analytic": analytic,
        "expected_heat_into_reservoirs_w": expected_heat.tolist(),
        "raw_heat_error_w": heat_error.tolist(),
        "maximum_temperature_error_k": temperature_error,
        "group_ids": list(factor.group_ids),
        "group_areas_m2": factor.group_areas_m2.tolist(),
        "bulk_ids": list(factor.bulk_ids),
        "prescribed_ids": list(factor.prescribed_ids),
        "C_reservoir_raw_w_k": factor.reservoir_conductance_raw_w_k.tolist(),
        "G_mean_by_reservoir": factor.mean_by_reservoir_temperature.tolist(),
        "R_mean_by_neumann_k_w": factor.mean_by_group_neumann_k_w.tolist(),
        "J_heat_by_neumann": factor.reservoir_heat_by_group_neumann.tolist(),
        "answer": answer,
        "diagnostics": factor.diagnostics,
        "fixture_verified": verified,
        "actual_rocket_mesh_temperature_radiation_acceptance": False,
        "artifacts": [
            {"path": str(output / name), "sha256": sha(output / name)}
            for name in ["mesh.npz", "nodal-field.npz"]
        ],
    }
    (output / "record.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def campaign(config: Path, output: Path) -> dict[str, Any]:
    started = time.monotonic()
    cfg = yaml.safe_load(config.read_text())
    budget = cfg["budget"]
    if (
        budget["threads"] != 1
        or budget["max_tetrahedra"] > 150000
        or budget["seconds_per_fixture_all_levels"] > 180
    ):
        raise ValueError("Retain oneCPU/150kfixture/180s budget")
    regression = Path(cfg["source_fixture_root"]) / "record.json"
    base = json.loads(regression.read_text())
    if not base["source_independent_fixture_method_verified"] or not base["inputs_unchanged"]:
        raise ValueError("Shared assembler legacy regression unavailable or failed")
    sources = [
        config,
        Path(__file__),
        Path("src/analysis/robin_gas.py"),
        Path("src/analysis/gas_conduction.py"),
        regression,
        Path(cfg["legacy_reference_record"]),
    ]
    before = {str(p): sha(p) for p in sources}
    output.mkdir(parents=True, exist_ok=True)
    fixtures = []
    stopped = None
    for fixture in cfg["fixtures"]:
        start = time.monotonic()
        levels = []
        for level in cfg["mesh_levels"]:
            folder = output / fixture / f"level-{level}"
            remaining = budget["seconds_per_fixture_all_levels"] - (time.monotonic() - start)
            try:
                process = subprocess.run(
                    [
                        sys.executable,
                        str(Path(__file__)),
                        "--config",
                        str(config),
                        "--worker",
                        fixture,
                        "--level",
                        str(level),
                        "--output",
                        str(folder),
                    ],
                    text=True,
                    capture_output=True,
                    timeout=max(0.01, remaining),
                    check=False,
                )
                if process.returncode:
                    stopped = {
                        "fixture": fixture,
                        "level": level,
                        "reason": "invalid_method_mesh_or_worker",
                        "stderr": process.stderr[-8000:],
                    }
                    break
                report = json.loads((folder / "record.json").read_text())
                levels.append(report)
                print(
                    f"{fixture} level{level}: maxTerr{report['maximum_temperature_error_k']:.4g}K, verified={report['fixture_verified']}",
                    flush=True,
                )
                if not report["fixture_verified"]:
                    stopped = {
                        "fixture": fixture,
                        "level": level,
                        "reason": "known_case_algebra_or_balance_failure",
                    }
                    break
            except subprocess.TimeoutExpired:
                stopped = {
                    "fixture": fixture,
                    "level": level,
                    "reason": "180s_total_fixture_budget",
                }
                break
        if len(levels) == 3:
            a = np.asarray(levels[-2]["C_reservoir_raw_w_k"])
            b = np.asarray(levels[-1]["C_reservoir_raw_w_k"])
            scale = float(np.abs(b).max())
            change = float(np.abs(b - a).max() / scale) if scale > 1e-12 else None
            converged = (
                change is None or change < cfg["verification"]["convergence_relative_tolerance"]
            )
        else:
            change = None
            converged = False
        fixtures.append(
            {
                "fixture": fixture,
                "levels": levels,
                "elapsed_s": time.monotonic() - start,
                "last_two_raw_C_relative_change": change,
                "three_level_verified": len(levels) == 3
                and all(r["fixture_verified"] for r in levels)
                and converged,
            }
        )
        if stopped:
            break
    after = {str(p): sha(p) for p in sources}
    prior = json.loads(Path(cfg["legacy_reference_record"]).read_text())
    regression_max_difference = 0.0
    for a, b in zip(base["fixtures"], prior["fixtures"], strict=True):
        for x, y in zip(a["levels"], b["levels"], strict=True):
            regression_max_difference = max(
                regression_max_difference,
                float(np.abs(np.asarray(x["C_raw_w_k"]) - np.asarray(y["C_raw_w_k"])).max()),
            )
    r = {
        "run_id": datetime.now(UTC).strftime("wo03-robin-gas-%Y%m%dT%H%M%S%fZ"),
        "elapsed_s": time.monotonic() - started,
        "compute_cost_usd": 0,
        "threads": 1,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "inputs_unchanged": before == after,
        "shared_tetra_legacy_regression_run_id": base["run_id"],
        "legacy12_C_maximum_absolute_difference_w_k": regression_max_difference,
        "fixtures": fixtures,
        "stopped": stopped,
        "source_independent_method_verified": stopped is None
        and len(fixtures) == 4
        and all(f["three_level_verified"] for f in fixtures),
        "actual_halfwall_or_surface_group_mapping_available": False,
        "radiation_ODE_or_legacy_path_replacement_executed": False,
        "actual_rocket_temperature_or_matrix_acceptance": False,
        "flight_ready": False,
    }
    (output / "record.json").write_text(json.dumps(r, indent=2, allow_nan=False) + "\n")
    return r


def compare_orderings(config: Path, output: Path) -> dict[str, Any]:
    cfg = yaml.safe_load(config.read_text())
    results = []
    for level in cfg["mesh_levels"]:
        rows = []
        matrices = []
        for ordering in ["COLAMD", "MMD_AT_PLUS_A"]:
            folder = output / f"level-{level}" / ordering
            process = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__)),
                    "--config",
                    str(config),
                    "--worker",
                    "finite_halfwall_slab",
                    "--level",
                    str(level),
                    "--ordering",
                    ordering,
                    "--output",
                    str(folder),
                ],
                text=True,
                capture_output=True,
                timeout=180,
                check=False,
            )
            if process.returncode:
                raise ValueError(process.stderr[-4000:])
            report = json.loads((folder / "record.json").read_text())
            d = report["diagnostics"]
            rows.append(
                {
                    "ordering": ordering,
                    "nodes": d["nodes"],
                    "native_LU_s": d["native_LU_elapsed_s"],
                    "native_L_U_nonzeros": d["LU_actual_L_U_nonzeros"],
                    "isolated_child_process_max_rss_bytes": d["measured_process_max_rss_bytes"],
                    "algebra_checks_pass": d["algebra_checks_pass"],
                }
            )
            matrices.append(
                (
                    np.asarray(report["C_reservoir_raw_w_k"]),
                    np.asarray(report["R_mean_by_neumann_k_w"]),
                )
            )
        results.append(
            {
                "level": level,
                "orderings": rows,
                "C_maximum_absolute_difference_w_k": float(
                    np.abs(matrices[0][0] - matrices[1][0]).max()
                ),
                "mean_load_maximum_absolute_difference_k_w": float(
                    np.abs(matrices[0][1] - matrices[1][1]).max()
                ),
            }
        )
    record = {
        "results": results,
        "raw_matrix_modified": False,
        "default_api_ordering": "COLAMD",
        "actual_ordering_is_explicit_primary_decision": True,
        "single_CPU": True,
        "RSS_comparison_scope": "Each ordering/level runs in its own fresh child; RSS includes imports/assembly/maps",
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "ordering-comparison.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def actual_pattern_preflight(mesh_path: Path, groups_path: Path, output: Path) -> dict[str, Any]:
    """Primary-authorized actual K/pattern audit ONLY; no invented Robin h/BC."""
    started = time.monotonic()
    paths = [
        mesh_path,
        groups_path,
        Path(__file__),
        Path("src/analysis/gas_conduction.py"),
        Path("src/analysis/robin_gas.py"),
    ]
    before = {str(p): sha(p) for p in paths}
    with np.load(mesh_path, allow_pickle=False) as data:
        points, tets, faces, gids = (
            data[k] for k in ["points_m", "tetrahedra", "boundary_triangles", "boundary_group_ids"]
        )
    a = assemble_tetra_conductivity(points, tets, 0.026, max_tetrahedra=750000, max_nodes=150000)
    canonical = np.sort(faces, axis=1)
    order = np.lexsort(canonical[:, ::-1].T)
    if not np.array_equal(canonical[order], a.exterior_triangles) or gids.shape != (len(faces),):
        raise ValueError("Actual exterior triangle/label completeness failure")
    opposite = np.empty(len(faces), dtype=int)
    opposite[order] = a.exterior_opposite_nodes
    xyz = points[faces]
    normal = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    if np.any(np.sum(normal * (points[opposite] - xyz[:, 0]), axis=1) >= 0):
        raise ValueError("Actual boundary orientation failure")
    K = a.stiffness_w_k
    diagonal = K.diagonal()
    difference = K - K.T
    span = np.ptp(points, axis=0)
    fields = [("constant", np.ones(len(points)))]
    for dim in range(3):
        fields.append((f"affine_axis{dim}", (points[:, dim] - points[:, dim].min()) / span[dim]))
    fields.append(("P1_quadratic_probe", fields[1][1] ** 2 + fields[2][1] ** 2))
    energies = []
    for name, field in fields:
        gradient = np.einsum("ti,tij->tj", field[tets], a.gradients_per_m)
        local = float(np.sum(0.026 * a.volumes_m3 * np.sum(gradient**2, axis=1)))
        matrix = float(field @ (K @ field))
        oracle = (
            0.026 * float(a.volumes_m3.sum()) / span[int(name[-1])] ** 2
            if name.startswith("affine_axis")
            else 0 if name == "constant" else None
        )
        energies.append(
            {
                "mode": name,
                "assembled_quadratic_form_w_times_k": matrix,
                "element_quadratic_form_w_times_k": local,
                "matrix_minus_element_w_times_k": matrix - local,
                "raw_relative_difference": (matrix - local) / local if local > 1e-20 else None,
                "affine_exact_integral_w_times_k": oracle,
            }
        )
    estimated = int(K.nnz * 64 * 16 + len(points) * 128)
    ng = len(np.unique(gids))
    allowed_states = int(np.sqrt(128 * 1024**2 / 8) - ng)
    after = {str(p): sha(p) for p in paths}
    report = {
        "elapsed_s": time.monotonic() - started,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "inputs_unchanged": before == after,
        "nodes": len(points),
        "tetrahedra": len(tets),
        "boundary_triangles": len(faces),
        "surface_groups": ng,
        "air_components": a.component_count,
        "K_nonzeros_including_stored_zeros": K.nnz,
        "K_diagonal_min_w_k": float(diagonal.min()),
        "K_diagonal_max_w_k": float(diagonal.max()),
        "K_diagonal_max_min_ratio": float(diagonal.max() / diagonal.min()),
        "K_symmetry_max_w_k": float(np.abs(difference.data).max()) if difference.nnz else 0,
        "K_constant_residual_max_w_k": float(np.abs(K @ np.ones(len(points))).max()),
        "K_positive_offdiagonals": _positive_offdiagonal(K, float(diagonal.max()) * 1e-9),
        "quadratic_energy_probes": energies,
        "minimum_scaled_determinant": a.minimum_scaled_determinant,
        "minimum_tet_volume_m3": float(a.volumes_m3.min()),
        "assembly_retained_array_bytes": a.retained_array_bytes,
        "all_free_K_pattern_LU_estimate_bytes": estimated,
        "LU_estimate_fill_multiplier": 64,
        "pattern_basis": "Positive Robin triangle mass adds only existing tetrahedron-edge sparsity; no physical h assigned. All nodes free is conservative before unknown prescriptions.",
        "approved_one_attempt_budget": {
            "max_free_nodes": 100000,
            "estimated_LU_limit_mib": 1536,
            "map_limit_mib": 128,
            "child_elapsed_limit_s": 300,
        },
        "all_free_LU_estimate_within_budget": bool(
            estimated <= 1536 * 1024**2 and len(points) <= 100000
        ),
        "number_of_reservoir_states_fitting128MiB_map_estimate": allowed_states,
        "actual_reservoir_state_count": None,
        "native_factorization_attempted": False,
        "actual_L_U_nonzeros": None,
        "raw_solved_response_overshoots": None,
        "reason_no_response": "Complete physical Robin/Dirichlet boundary conditions unavailable; no actual solve authorized or performed.",
        "measured_process_max_rss_bytes": int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            * (1 if sys.platform == "darwin" else 1024)
        ),
        "actual_matrix_or_temperature_acceptance": False,
        "raw_K_repaired_clipped_or_regularized": False,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "preflight.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/studies/wo03-robin-gas.yaml"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    parser.add_argument("--worker")
    parser.add_argument("--level", type=int, default=0)
    parser.add_argument("--ordering", choices=["COLAMD", "MMD_AT_PLUS_A"], default="COLAMD")
    parser.add_argument("--compare-orderings", action="store_true")
    parser.add_argument("--preflight-mesh", type=Path)
    parser.add_argument("--preflight-groups-json", type=Path)
    parser.add_argument("--preflight-worker", action="store_true")
    args = parser.parse_args()
    output = args.output or Path(yaml.safe_load(args.config.read_text())["default_output"])
    if args.compare_orderings:
        compare_orderings(args.config, output)
        return 0
    if args.preflight_mesh:
        groups = args.preflight_groups_json or args.preflight_mesh.parent / "boundary-groups.json"
        if args.preflight_worker:
            actual_pattern_preflight(args.preflight_mesh, groups, output)
            return 0
        process = subprocess.run(
            [
                sys.executable,
                str(Path(__file__)),
                "--preflight-mesh",
                str(args.preflight_mesh),
                "--preflight-groups-json",
                str(groups),
                "--output",
                str(output),
                "--preflight-worker",
            ],
            timeout=300,
            check=False,
        )
        return process.returncode
    if args.worker:
        worker(args.config, args.worker, args.level, output, args.ordering)
        return 0
    result = campaign(args.config, output)
    print(output / "record.json")
    return 0 if result["source_independent_method_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
