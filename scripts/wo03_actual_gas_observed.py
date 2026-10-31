"""One observed900s repeat of the same actual coarse nominal-wall Robin factor."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import shutil
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

from scripts.wo03_actual_gas_factor import build_conditions
from scripts.wo03_gas_progress import BlockCheckpoint
from src.analysis.robin_gas import factor_robin_gas


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
        condition_builder=Path("scripts/wo03_actual_gas_factor.py"),
        checkpoint_writer=Path("scripts/wo03_gas_progress.py"),
        wrapper=Path(__file__),
        observation_equivalence_record=Path(cfg["observation_equivalence_record"]),
        original_capped_record=Path("build/wo03-actual-gas-factor/coarse-nominal/record.json"),
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
    equivalence = json.loads(paths["observation_equivalence_record"].read_text())
    if (
        not equivalence["all_prior_default_observed_maps_and_fields_exactly_equal"]
        or not equivalence["inputs_unchanged"]
        or equivalence["input_sha256_before"]["src/analysis/robin_gas.py"]
        != hashes["frozen_robin_module"]
    ):
        raise ValueError("Pure observation equivalence proof unavailable")
    hashes["config"] = sha(config)
    hashes["script"] = sha(Path(__file__))
    return cfg, paths, hashes


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
            "native_factor_stage_observed": True,
        },
    )
    budget = cfg["budget"]
    checkpoint = BlockCheckpoint(
        output / "checkpoints",
        {
            "input_sha256": hashes,
            "physical_inputs": {
                **source,
                "material_operator_corner": cfg["material_operator_corner"],
                "ordering": budget["ordering"],
                "rhs_block_size": budget["rhs_block_size"],
                "physical_boundary_alias_table": mesh.metadata["physical_boundary_alias_table"],
            },
            "explicit_budget_revision": cfg["explicit_budget_revision"],
        },
    )

    def observe(event: dict[str, Any]) -> None:
        checkpoint(event)
        write_json(
            output / "progress.json",
            {
                **{key: value for key, value in event.items() if key != "map_blocks"},
                "worker_elapsed_s": time.monotonic() - started,
                "checkpoint_manifest": str(checkpoint.directory / "manifest.json"),
                "completed_raw_blocks": len(checkpoint.manifest["blocks"]),
            },
        )

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
            progress_callback=observe,
        )
    except (ValueError, MemoryError, RuntimeError, np.linalg.LinAlgError) as exc:
        write_json(
            output / "worker-result.json",
            {
                "status": "RESOURCE_OR_NUMERICAL_FACTOR_REJECTED",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "native_LU_attempted": any(
                    e["phase"] == "LU_begin" for e in checkpoint.manifest["events"]
                ),
                "observed_last_phase": checkpoint.manifest.get("last_phase"),
                "checkpoint_manifest": str(checkpoint.directory / "manifest.json"),
                "numerical_checks_pass": False,
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
    checkpoint.finalize(factor)
    shutil.copyfile(checkpoint.directory / "gas-response.npz", output / "gas-response.npz.tmp")
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
        "checkpoint_manifest": str(checkpoint.directory / "manifest.json"),
        "observation_only_equivalence_source_sha256": hashes["observation_equivalence_record"],
        "explicit_budget_revision": cfg["explicit_budget_revision"],
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
            else "ONE_OBSERVED_ACTUAL_FACTOR_CHECKS_FAILED_NOT_ACCEPTED"
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
        "checkpoint_manifest": str(checkpoint.directory / "manifest.json"),
        "checkpoint_manifest_sha256": sha(checkpoint.directory / "manifest.json"),
        "explicit_budget_revision": cfg["explicit_budget_revision"],
        "flight_ready": False,
    }
    write_json(output / "worker-result.json", record)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-actual-gas-observed.yaml")
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
        "child_seconds": 900,
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
    run_id = datetime.now(UTC).strftime("wo03-actual-gas-observed-%Y%m%dT%H%M%S%fZ")
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
    manifest_path = output / "checkpoints" / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        result.update(
            checkpoint_manifest=str(manifest_path),
            checkpoint_manifest_sha256=sha(manifest_path),
            observed_last_phase=manifest.get("last_phase"),
            observed_completed_raw_blocks=len(manifest["blocks"]),
            observed_native_LU_started=any(e["phase"] == "LU_begin" for e in manifest["events"]),
            observed_native_LU_returned=any(e["phase"] == "LU_end" for e in manifest["events"]),
            last_observed_resource_counts=(
                manifest["events"][-1]["resource_counts"] if manifest["events"] else {}
            ),
        )
    result.setdefault("numerical_checks_pass", False)
    result.update(
        run_id=run_id,
        parent_elapsed_s=time.monotonic() - started,
        child_returncode=code,
        child900s_cap_reached=timeout,
        explicit_budget_revision=cfg["explicit_budget_revision"],
        input_sha256_at_start=hashes,
        compute_cost_usd=0,
        one_CPU=True,
        no_retry_or_budget_raise=True,
        actual_thermal_acceptance=False,
    )
    write_json(output / "record.json", result)
    print(output / "record.json")
    print(result["status"])
    return 0 if result.get("numerical_checks_pass") and result.get("inputs_unchanged") else 1


if __name__ == "__main__":
    raise SystemExit(main())
