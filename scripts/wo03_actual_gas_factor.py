"""One bounded actual coarse Robin factor, without hidden wall/temperature repair."""

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

from src.analysis.robin_gas import BoundaryCondition, RobinGasMesh, factor_robin_gas


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def rss() -> int:
    return int(
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        * (1 if sys.platform == "darwin" else 1024)
    )


def inputs(config: Path) -> tuple[dict[str, Any], dict[str, Path], dict[str, str]]:
    cfg = yaml.safe_load(config.read_text())
    wall = Path(cfg["wall_directory"])
    paths = {
        key: Path(cfg[key])
        for key in [
            "mesh",
            "groups",
            "correspondence",
            "source_optical_boundary",
            "engineering",
            "thermal_acceptance",
        ]
    }
    paths.update(
        wall_record=wall / "record.json",
        wall_operator=wall / "wall-quadrature-screen.npz",
        wall_metadata=wall / "wall-map-metadata.json",
        wall_qa=wall / "wall-algebra-qa.json",
        frozen_robin_module=Path("src/analysis/robin_gas.py"),
        frozen_assembly_module=Path("src/analysis/gas_conduction.py"),
    )
    hashes = {key: sha(path) for key, path in paths.items()}
    for key, expected in cfg["expected_sha256"].items():
        if hashes[key] != expected:
            raise ValueError(f"Input identity mismatch:{key}")
    record = json.loads(paths["wall_record"].read_text())
    if (
        not record.get("full_level_executed")
        or not record.get("inputs_unchanged")
        or record.get("failure") is not None
    ):
        raise ValueError("Complete unchanged wall operator unavailable")
    if record["operator_sha256"] != hashes["wall_operator"]:
        raise ValueError("Wall record/operator mismatch")
    hashes["config"] = sha(config)
    hashes["script"] = sha(Path(__file__))
    return cfg, paths, hashes


def build_conditions(
    cfg: dict[str, Any], paths: dict[str, Path]
) -> tuple[Any, list[Any], dict[str, Any], dict[str, Any]]:
    with np.load(paths["mesh"], allow_pickle=False) as d:
        meshdata = {name: d[name] for name in d.files}
    with np.load(paths["correspondence"], allow_pickle=False) as d:
        source_ids = d["boundary_source_triangle_ids"]
        permutation = d["boundary_source_vertex_permutation"]
    with np.load(paths["source_optical_boundary"], allow_pickle=False) as d:
        vertices = d["vertices_mm"] * 0.001
        source_triangles = d["triangles"]
        source_faces = d["triangle_face_index"] + 1
    count = len(meshdata["boundary_triangles"])
    if (
        len(source_triangles) != count
        or not np.array_equal(np.sort(source_ids), np.arange(count))
        or permutation.shape != (count, 3)
        or not np.all(np.sort(permutation, axis=1) == [0, 1, 2])
    ):
        raise ValueError("Exact bijective source/facet/vertex correspondence missing")
    source_vertices = vertices[source_triangles[source_ids]]
    mapped = source_vertices[np.arange(count)[:, None], permutation]
    if not np.array_equal(mapped, meshdata["points_m"][meshdata["boundary_triangles"]]):
        raise ValueError("Triangle vertex permutation not bitwise SI-coordinate exact")
    if not np.array_equal(source_faces[source_ids], meshdata["boundary_face_ids"]):
        raise ValueError("Original CAD face identity does not match facet correspondence")
    metadata = json.loads(paths["wall_metadata"].read_text())
    states = metadata["bulk_state_ids"]
    with np.load(paths["wall_operator"], allow_pickle=False) as d:
        operator = {name: d[name] for name in d.files}
    selected = operator["original_triangle_indices"]
    lookup = np.full(count, -1, dtype=int)
    if len(np.unique(selected)) != len(selected) or selected.min() < 0 or selected.max() >= count:
        raise ValueError("Robin source row identity invalid/duplicate")
    lookup[selected] = np.arange(len(selected))
    liner_rows = operator["liner_Robin_local_indices"]
    liner_lookup = {int(row): i for i, row in enumerate(liner_rows)}
    if set(liner_lookup) != set(np.flatnonzero(operator["bulk_index"] == -1)):
        raise ValueError("Specialized liner row coverage mismatch")
    dir_faces = {int(row["fluid_face_id"]): row for row in metadata["Dirichlet_faces"]}
    aliases = []
    conditions = []
    robin_count = 0
    dir_count = 0
    for i in range(count):
        sid = int(source_ids[i])
        fid = int(meshdata["boundary_face_ids"][i])
        perm = permutation[i]
        j = int(lookup[sid])
        if j >= 0:
            if int(operator["original_CAD_face_ids"][j]) != fid or int(
                operator["radiation_group_ids"][j]
            ) != int(meshdata["boundary_group_ids"][i]):
                raise ValueError("Robin row CAD/radiation identity mismatch")
            matrix = operator["wall_matrix_w_k"][j][np.ix_(perm, perm)]
            bulk = int(operator["bulk_index"][j])
            if bulk >= 0:
                vectors = {states[bulk]: operator["bulk_load_vector_w_k"][j][perm]}
                diagonal = {states[bulk]: float(operator["bulk_diagonal_w_k"][j])}
            elif bulk == -1:
                row = liner_lookup[j]
                vectors = {}
                diagonal = {}
                for cell, state in enumerate(operator["liner_bulk_indices"]):
                    dvalue = float(operator["liner_bulk_diagonals_w_k"][row, cell])
                    vector = operator["liner_bulk_load_vectors_w_k"][row, cell][perm]
                    if dvalue == 0 and np.all(vector == 0):
                        continue  # exactly absent computed cell, not clipping
                    vectors[states[int(state)]] = vector
                    diagonal[states[int(state)]] = dvalue
                if not vectors:
                    raise ValueError("Liner facet has no positive integrated cell path")
            else:
                raise ValueError("Unknown specialized wall row")
            conditions.append(
                BoundaryCondition(
                    "robin",
                    wall_matrix_w_k=matrix,
                    bulk_load_vectors_w_k=vectors,
                    bulk_diagonal_w_k=diagonal,
                )
            )
            robin_count += 1
        else:
            if fid not in dir_faces:
                raise ValueError(
                    f"Missing physical boundary on triangle{i}/face{fid}; no fallbackh"
                )
            row = dir_faces[fid]
            original = row["temperature_id"]
            if fid in [901, 902, 903]:
                temperature_id = cfg["shared_motor_case_temperature_id"]
            elif original == cfg["ambient_physical_gas_temperature_id"]:
                temperature_id = original
            else:
                raise ValueError("Unapproved prescribed gas-temperature alias")
            conditions.append(BoundaryCondition("dirichlet", temperature_id=temperature_id))
            dir_count += 1
    if robin_count != len(selected) or dir_count != count - len(selected):
        raise ValueError("Incomplete physical facet coverage")
    for fid, row in sorted(dir_faces.items()):
        aliases.append(
            {
                **row,
                "screening_physical_temperature_id": (
                    cfg["shared_motor_case_temperature_id"]
                    if fid in [901, 902, 903]
                    else cfg["ambient_physical_gas_temperature_id"]
                ),
                "hypothesis": (
                    "Allthree motor surfaces share ONE required-hot case history ONLY for this explicit screen"
                    if fid in [901, 902, 903]
                    else "Ambient physical gas boundary; independent radiative brightness retained"
                ),
                "measured_surface_history": False,
            }
        )
    if (
        len([a for a in aliases if a["fluid_face_id"] in [901, 902, 903]]) != 3
        or len(aliases) != 12
    ):
        raise ValueError("Expected three motor hypotheses and nine real gas openings")
    provenance = {
        "source_wall_metadata": metadata,
        "material_operator_corner": cfg["material_operator_corner"],
        "physical_boundary_alias_table": aliases,
        "Robin_triangles": robin_count,
        "Dirichlet_triangles": dir_count,
        "liner_facets": len(liner_rows),
        "source_vertices_bitwise_equal_after_permutation": True,
        "no_fallbackh_or_node_priority": True,
        "nominal_material_factors_not_rescaled": True,
    }
    mesh = RobinGasMesh(
        meshdata["points_m"],
        meshdata["tetrahedra"],
        meshdata["boundary_triangles"],
        meshdata["boundary_group_ids"],
        provenance,
    )
    engineering = yaml.safe_load(paths["engineering"].read_text())
    acceptance = yaml.safe_load(paths["thermal_acceptance"].read_text())
    case = next(c for c in acceptance["cases"] if c["id"] == cfg["selected_case_id"])
    index = case["source_scenario_index"]
    air_k = float(engineering["thermal"]["air_conductivity_w_m_k"][index])
    if (
        cfg["material_operator_corner"] != "nominal"
        or case["case_peak_c"] != 300
        or case["ambient_c"] != 35
        or air_k != 0.04
    ):
        raise ValueError("This single screening hypothesis must remain300C/35C/air.04/nominalwall")
    return (
        mesh,
        conditions,
        metadata,
        {
            "selected_case": case,
            "required_acceptance_label": acceptance["acceptance"]["required_robustness_case"],
            "source_air_index": index,
            "air_conductivity_w_m_k": air_k,
            "fixture_air_conductivity_not_used": 0.026,
            "nominal_material_operator_only": True,
            "high_k_material_uncertainty_corner_executed": False,
        },
    )


def worker(config: Path, output: Path) -> int:
    started = time.monotonic()
    cfg, paths, hashes = inputs(config)
    write_json(
        output / "progress.json",
        {"phase": "validating_exact_wall_and_triangle_mapping", "input_sha256": hashes},
    )
    mesh, conditions, metadata, source = build_conditions(cfg, paths)
    write_json(
        output / "progress.json",
        {
            "phase": "entering_ONE_factor_and_reduced_maps",
            "input_sha256": hashes,
            "Robin_facets": sum(x.kind == "robin" for x in conditions),
            "native_factor_stage_not_separately_observed": True,
        },
    )
    budget = cfg["budget"]
    try:
        factor = factor_robin_gas(
            mesh,
            conditions,
            source["air_conductivity_w_m_k"],
            max_tetrahedra=budget["max_tetrahedra"],
            max_nodes=budget["max_nodes"],
            max_factor_free_nodes=budget["max_factor_free_nodes"],
            factor_memory_limit_mb=budget["factor_memory_limit_mb"],
            reduced_map_memory_limit_mb=budget["reduced_map_memory_limit_mb"],
            rhs_block_size=budget["rhs_block_size"],
            ordering=budget["ordering"],
        )
    except (ValueError, MemoryError, RuntimeError, np.linalg.LinAlgError) as exc:
        write_json(
            output / "worker-result.json",
            {
                "status": "RESOURCE_OR_NUMERICAL_FACTOR_REJECTED",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "native_LU_attempted": False if isinstance(exc, MemoryError) else None,
                "native_successful_factor_available": False,
                "elapsed_s": time.monotonic() - started,
                "measured_process_max_rss_bytes": rss(),
                "input_sha256": hashes,
                "source_hypothesis": source,
                "actual_thermal_acceptance": False,
            },
        )
        return 2
    if set(factor.bulk_ids) != set(metadata["bulk_state_ids"]):
        raise ValueError("Material component/16liner state identity lost")
    kdiag = factor.assembly.stiffness_w_k.diagonal()
    adiag = factor.A_w_k.diagonal()
    factor.diagnostics["actual_geometry_conditioning"] = {
        "minimum_scaled_tetrahedron_determinant": factor.assembly.minimum_scaled_determinant,
        "minimum_tetrahedron_volume_m3": float(factor.assembly.volumes_m3.min()),
        "K_diagonal_min_w_k": float(kdiag.min()),
        "K_diagonal_max_w_k": float(kdiag.max()),
        "K_diagonal_max_to_min_ratio": float(kdiag.max() / kdiag.min()),
        "A_diagonal_min_w_k": float(adiag.min()),
        "A_diagonal_max_w_k": float(adiag.max()),
        "A_diagonal_max_to_min_ratio": float(adiag.max() / adiag.min()),
        "free_nodes": len(factor.free_nodes),
        "prescribed_nodes": len(factor.fixed_nodes),
        "sliver_conditioning_or_mesh_convergence_qualified": False,
    }
    arrays = {
        name: getattr(factor, name)
        for name in [
            "mean_by_reservoir_temperature",
            "mean_by_group_neumann_k_w",
            "reservoir_conductance_raw_w_k",
            "reservoir_heat_by_group_neumann",
            "group_areas_m2",
        ]
    }
    with (output / "gas-response.npz.tmp").open("wb") as stream:
        np.savez_compressed(stream, **arrays)
    (output / "gas-response.npz.tmp").replace(output / "gas-response.npz")
    state = {
        "group_ids": list(factor.group_ids),
        "bulk_ids": list(factor.bulk_ids),
        "prescribed_ids": list(factor.prescribed_ids),
        "diagnostics": factor.diagnostics,
        "input_sha256": hashes,
        "source_hypothesis": source,
        "physical_boundary_alias_table": mesh.metadata["physical_boundary_alias_table"],
        "operator_sha256": sha(output / "gas-response.npz"),
        "new_spatial_reconstruction_from_cache": "unavailable",
        "nominal_material_operator": True,
        "full_required_thermal_matrix_or_ODE_accepted": False,
    }
    write_json(output / "gas-response.json", state)
    write_json(
        output / "progress.json",
        {
            "phase": "native_factor_complete_executing_field_checks",
            "diagnostics": factor.diagnostics,
        },
    )
    nb, nd, ng = len(factor.bulk_ids), len(factor.prescribed_ids), len(factor.group_ids)
    checks = []
    fields = []
    surface_means = []
    field_ids = []
    uniform = cfg["checks"]["uniform_temperature_k"]

    def check_case(
        name: str, bulk: Any, prescribed: Any, q: Any, expected_uniform: float | None = None
    ) -> Any:
        answer = factor.evaluate(bulk, prescribed, q)
        field = answer.pop("nodal_temperature_k")
        fields.append(field)
        surface_means.append(answer["area_mean_temperature_k"])
        field_ids.append(name)
        lo, hi = float(min(np.r_[bulk, prescribed])), float(max(np.r_[bulk, prescribed]))
        tolerance = cfg["checks"]["overshoot_reporting_tolerance_k"]
        summary = {
            "id": name,
            "max_uniform_error_k": (
                float(np.abs(field - expected_uniform).max())
                if expected_uniform is not None
                else None
            ),
            "state_minimum_k": lo,
            "state_maximum_k": hi,
            "P1_field_minimum_k": float(field.min()),
            "P1_field_maximum_k": float(field.max()),
            "below_state_interval_nodes": int(np.sum(field < lo - tolerance)),
            "above_state_interval_nodes": int(np.sum(field > hi + tolerance)),
            "interval_scope": "Maximum-principle diagnostic only whenNeumannloadiszero; unitloads may legitimately exceed source-state interval",
            "energy_balance_residual_w": answer["energy_balance_residual_w"],
            "form_balance_difference_w_times_k": answer["form_balance_difference_w_times_k"],
            "free_residual_max_w": answer["free_residual_max_w"],
            "mean_map_reconstruction_difference_k": answer["mean_map_reconstruction_difference_k"],
            "heat_map_reconstruction_difference_w": answer["heat_map_reconstruction_difference_w"],
            "heat_into_bulk_sum_w": float(sum(answer["heat_into_bulk_w"])),
            "heat_into_prescribed_reservoir_w": answer["heat_into_prescribed_reservoir_w"],
            "net_surface_source_w": float(np.sum(q)),
            "maximum_meanT4_minus_meanT_to_fourth_k4": float(
                np.max(
                    np.abs(
                        np.asarray(answer["area_mean_fourth_power_k4"])
                        - np.asarray(answer["fourth_power_of_area_mean_k4"])
                    )
                )
            ),
        }
        checks.append(summary)
        return field

    base = check_case(
        "uniform_300K_unforced", np.full(nb, uniform), np.full(nd, uniform), np.zeros(ng), uniform
    )
    ambient = source["selected_case"]["ambient_c"] + 273.15
    hot = source["selected_case"]["case_peak_c"] + 273.15
    physical = np.array(
        [
            hot if name == cfg["shared_motor_case_temperature_id"] else ambient
            for name in factor.prescribed_ids
        ]
    )
    check_case(
        "case300C_ambient35C_nominalwall_no_radiation", np.full(nb, ambient), physical, np.zeros(ng)
    )
    signed = []
    for gid in cfg["checks"]["selected_signed_unit_load_group_ids"]:
        col = factor.group_ids.index(gid)
        pair = []
        for sign in [1, -1]:
            q = np.zeros(ng)
            q[col] = sign
            pair.append(
                check_case(
                    f"group{gid}_{sign:+d}W_at300K", np.full(nb, uniform), np.full(nd, uniform), q
                )
            )
        signed.append(
            {
                "group_id": gid,
                "odd_response_linearity_max_k": float(np.abs(pair[0] + pair[1] - 2 * base).max()),
                "positive1W_response_min_k_w": float((pair[0] - base).min()),
                "positive1W_response_max_k_w": float((pair[0] - base).max()),
            }
        )
    np.savez_compressed(
        output / "checked-gas-surface-fields.npz",
        case_ids=np.asarray(field_ids),
        nodal_temperature_k=np.asarray(fields),
        area_mean_temperature_k=np.asarray(surface_means),
        group_ids=np.asarray(factor.group_ids),
    )
    current = {key: sha(path) for key, path in paths.items()}
    current["config"] = sha(config)
    current["script"] = sha(Path(__file__))
    numerical = bool(
        factor.diagnostics["algebra_checks_pass"]
        and checks[0]["max_uniform_error_k"] <= cfg["checks"]["uniform_maximum_error_k"]
        and all(
            abs(c["energy_balance_residual_w"])
            <= cfg["checks"]["heat_balance_absolute_tolerance_w"]
            and abs(c["form_balance_difference_w_times_k"])
            <= cfg["checks"]["form_absolute_tolerance_w_times_k"]
            for c in checks
        )
    )
    record = {
        "status": (
            "ONE_ACTUAL_FACTOR_NUMERICAL_CHECKS_PASSED"
            if numerical
            else "ONE_ACTUAL_FACTOR_CHECKS_FAILED_NOT_ACCEPTED"
        ),
        "elapsed_s": time.monotonic() - started,
        "native_LU_attempted": True,
        "native_successful_factor_available": True,
        "input_sha256": hashes,
        "input_sha256_after": current,
        "inputs_unchanged": hashes == current,
        "source_hypothesis": source,
        "physical_boundary_alias_table": mesh.metadata["physical_boundary_alias_table"],
        "mapping": {
            "Robin_facets": mesh.metadata["Robin_triangles"],
            "Dirichlet_facets": mesh.metadata["Dirichlet_triangles"],
            "liner_facets": mesh.metadata["liner_facets"],
            "component_bulk_states": nb,
            "prescribed_physical_states": nd,
            "surface_groups": ng,
            "bitwise_source_coordinate_and_vertex_permutation_pass": True,
        },
        "diagnostics": factor.diagnostics,
        "field_checks": checks,
        "signed_unit_load_checks": signed,
        "numerical_checks_pass": numerical,
        "measured_process_max_rss_bytes": rss(),
        "artifacts": [
            {"path": str(output / name), "sha256": sha(output / name)}
            for name in ["gas-response.npz", "gas-response.json", "checked-gas-surface-fields.npz"]
        ],
        "actual_solid_transient_radiation_ODE_or_thermal_acceptance": False,
        "flight_ready": False,
    }
    write_json(output / "worker-result.json", record)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-actual-gas-factor.yaml")
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    cfg, _, hashes = inputs(args.config)
    output = args.output or Path(cfg["default_output"])
    output.mkdir(parents=True, exist_ok=True)
    b = cfg["budget"]
    if b != {
        "threads": 1,
        "child_seconds": 300,
        "max_tetrahedra": 750000,
        "max_nodes": 150000,
        "max_factor_free_nodes": 100000,
        "factor_memory_limit_mb": 1536,
        "reduced_map_memory_limit_mb": 128,
        "rhs_block_size": 16,
        "ordering": "MMD_AT_PLUS_A",
    }:
        raise ValueError("Single approved resource budget/ordering changed")
    if args.validate_only:
        _, paths, _ = inputs(args.config)
        _mesh, conditions, _, source = build_conditions(cfg, paths)
        print(
            json.dumps(
                {
                    "boundary_triangles": len(conditions),
                    "robin": sum(c.kind == "robin" for c in conditions),
                    "prescribed": sum(c.kind == "dirichlet" for c in conditions),
                    "source": source,
                },
                indent=2,
            )
        )
        return 0
    if args.worker:
        return worker(args.config, output)
    if (output / "attempt-start.json").exists():
        raise ValueError("ONE actual attempt alreadystarted; no automatic retry/budgetraise")
    started = time.monotonic()
    run_id = datetime.now(UTC).strftime("wo03-actual-gas-factor-%Y%m%dT%H%M%S%fZ")
    write_json(
        output / "attempt-start.json", {"run_id": run_id, "budget": b, "input_sha256": hashes}
    )
    timeout = False
    with (output / "worker.log").open("w") as log:
        try:
            process = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__)),
                    "--config",
                    str(args.config),
                    "--output",
                    str(output),
                    "--worker",
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=b["child_seconds"],
                check=False,
            )
            code = process.returncode
        except subprocess.TimeoutExpired:
            timeout = True
            code = None
    result_path = output / "worker-result.json"
    result = (
        json.loads(result_path.read_text())
        if result_path.exists()
        else {
            "status": "CHILD_CAP_OR_FAILURE_NO_RESULT",
            "native_LU_attempted": None,
            "native_successful_factor_available": False,
            "measured_child_max_rss_bytes": int(
                resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
                * (1 if sys.platform == "darwin" else 1024)
            ),
        }
    )
    result.update(
        run_id=run_id,
        parent_elapsed_s=time.monotonic() - started,
        child_returncode=code,
        child300s_cap_reached=timeout,
        compute_cost_usd=0,
        one_CPU=True,
        no_retry_or_budget_raise=True,
        actual_thermal_acceptance=False,
    )
    write_json(output / "record.json", result)
    print(output / "record.json")
    print(result["status"])
    return 0 if result.get("native_successful_factor_available") else 1


if __name__ == "__main__":
    raise SystemExit(main())
