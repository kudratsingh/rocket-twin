"""Verify stable heat evaluation on fixtures and replay completed fields only."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
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
from scipy.sparse import coo_matrix

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_actual_gas_factor import build_conditions
from scripts.wo03_gas_energy_diagnostic import CONFIG, EXPECTED, OBSERVED
from scripts.wo03_gas_progress import MAP_NAMES, fixture_conditions
from scripts.wo03_robin_gas import campaign as known_campaign
from scripts.wo03_robin_gas import fixture_mesh
from src.analysis.gas_conduction import assemble_tetra_conductivity
from src.analysis.robin_gas import RobinGasFactor, factor_robin_gas, integrated_wall_terms

PRIOR = Path("build/wo03-stable-gas-ledger/prior-source/robin_gas.py")
PRIOR_SHA = "6a1756130bee8c0db5527d81e86480a41a398366c982784189c9c54dd552fc9f"
FIXTURE_CONFIG = Path("configs/studies/wo03-robin-gas.yaml")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def load_prior() -> Any:
    if sha(PRIOR) != PRIOR_SHA:
        raise ValueError("Preserved prior6a source changed")
    name = "wo03_stable_ledger_prior6a"
    spec = importlib.util.spec_from_file_location(name, PRIOR)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load preserved prior source")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sparse_equal(a: Any, b: Any) -> bool:
    return a.shape == b.shape and all(
        np.array_equal(getattr(a, key), getattr(b, key)) for key in ["indptr", "indices", "data"]
    )


def fixtures(output: Path) -> dict[str, Any]:
    prior = load_prior()
    cfg = yaml.safe_load(FIXTURE_CONFIG.read_text())
    rows = []
    for fixture in cfg["fixtures"]:
        for level in cfg["mesh_levels"]:
            mesh, meshpath = fixture_mesh(fixture, level, cfg)
            if len(mesh.points_m) > 5000 or len(mesh.tetrahedra) > 20000:
                raise ValueError("Only source-independent small fixtures may be factored here")
            conditions = fixture_conditions(fixture, cfg, np.unique(mesh.boundary_group_ids))
            old = prior.factor_robin_gas(mesh, conditions, cfg["conductivity_w_m_k"])
            new = factor_robin_gas(mesh, conditions, cfg["conductivity_w_m_k"])
            events: list[dict[str, Any]] = []
            observed = factor_robin_gas(
                mesh, conditions, cfg["conductivity_w_m_k"], progress_callback=events.append
            )
            bulk = np.linspace(291, 309, len(new.bulk_ids))
            prescribed = np.full(len(new.prescribed_ids), 302.0)
            q = np.linspace(-0.0001, 0.0001, len(new.group_ids))
            fields = [f.reconstruct(bulk, prescribed, q) for f in [old, new, observed]]
            matrices_equal = all(
                sparse_equal(getattr(old, name), getattr(new, name))
                for name in ["A_w_k", "B_w_k", "L_per_area", "E_prescribed"]
            )
            matrices_equal = matrices_equal and np.array_equal(old.D_bulk_w_k, new.D_bulk_w_k)
            fields_equal = np.array_equal(fields[0], fields[1]) and np.array_equal(
                fields[1], fields[2]
            )
            GR_equal = all(
                np.array_equal(getattr(old, name), getattr(new, name))
                for name in [
                    "mean_by_reservoir_temperature",
                    "mean_by_group_neumann_k_w",
                    "group_areas_m2",
                ]
            )
            observed_equal = all(
                np.array_equal(getattr(new, name), getattr(observed, name))
                for name in (*MAP_NAMES, "group_areas_m2")
            )
            LU_equal = (
                sparse_equal(old.lu.L, new.lu.L)
                and sparse_equal(old.lu.U, new.lu.U)
                and np.array_equal(old.lu.perm_r, new.lu.perm_r)
                and np.array_equal(old.lu.perm_c, new.lu.perm_c)
            )
            answer = new.evaluate(bulk, prescribed, q)
            Cdiff = float(
                np.abs(old.reservoir_conductance_raw_w_k - new.reservoir_conductance_raw_w_k).max()
            )
            Jdiff = float(
                np.abs(
                    old.reservoir_heat_by_group_neumann - new.reservoir_heat_by_group_neumann
                ).max()
            )
            if not (
                matrices_equal
                and fields_equal
                and GR_equal
                and observed_equal
                and LU_equal
                and new.diagnostics["algebra_checks_pass"]
            ):
                raise ValueError(
                    "Solve algebra/observation equivalence changed beyond permitted heat ledger"
                )
            rows.append(
                {
                    "fixture": fixture,
                    "level": level,
                    "source_mesh_sha256": sha(meshpath),
                    "A_B_D_L_E_exactly_equal": matrices_equal,
                    "L_U_permutations_exactly_equal": LU_equal,
                    "prior_new_observed_fields_exactly_equal": fields_equal,
                    "prior_new_G_R_areas_exactly_equal": GR_equal,
                    "new_default_observed_ALL_maps_exactly_equal": observed_equal,
                    "C_prior_new_max_abs_difference_w_k": Cdiff,
                    "J_prior_new_max_abs_difference": Jdiff,
                    "energy_residual_w": answer["energy_balance_residual_w"],
                    "form_difference_w_k": answer["form_balance_difference_w_times_k"],
                    "raw_assembled_energy_residual_w": answer[
                        "raw_assembled_energy_balance_residual_w"
                    ],
                    "algebra_checks_pass": new.diagnostics["algebra_checks_pass"],
                }
            )
    return {
        "fixtures": rows,
        "all_exact_solve_and_observation_checks_pass": True,
        "C_maximum_prior_new_difference_w_k": max(
            row["C_prior_new_max_abs_difference_w_k"] for row in rows
        ),
        "J_maximum_prior_new_difference": max(
            row["J_prior_new_max_abs_difference"] for row in rows
        ),
        "no_actual_factor_PDE_or_ODE": True,
    }


def completed_shell() -> tuple[Any, dict[str, Any], dict[str, Any], dict[str, str]]:
    for path, expected in EXPECTED.items():
        if sha(path) != expected:
            raise ValueError(f"Completed source changed: {path}")
    cfg = yaml.safe_load(CONFIG.read_text())
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
        wall_operator=wall / "wall-quadrature-screen.npz",
        wall_metadata=wall / "wall-map-metadata.json",
        wall_record=wall / "record.json",
        wall_qa=wall / "wall-algebra-qa.json",
        frozen_robin_module=PRIOR,
        frozen_assembly_module=Path("src/analysis/gas_conduction.py"),
        condition_builder=Path("scripts/wo03_actual_gas_factor.py"),
        checkpoint_writer=Path("scripts/wo03_gas_progress.py"),
        wrapper=Path("scripts/wo03_actual_gas_observed.py"),
        observation_equivalence_record=Path(cfg["observation_equivalence_record"]),
        original_capped_record=Path("build/wo03-actual-gas-factor/coarse-nominal/record.json"),
    )
    for key, expected in cfg["expected_sha256"].items():
        if sha(paths[key]) != expected:
            raise ValueError(f"Original source pin changed: {key}")
    hashes = {str(path): sha(path) for path in paths.values()}
    hashes.update({str(p): h for p, h in EXPECTED.items()})
    mesh, conditions, _, source = build_conditions(cfg, paths)
    state = json.loads((OBSERVED / "gas-response.json").read_text())
    assembly = assemble_tetra_conductivity(
        mesh.points_m,
        mesh.tetrahedra,
        source["air_conductivity_w_m_k"],
        max_tetrahedra=750000,
        max_nodes=150000,
    )
    triangles = np.asarray(mesh.boundary_triangles)
    n, nb, nd, ng = (
        len(mesh.points_m),
        len(state["bulk_ids"]),
        len(state["prescribed_ids"]),
        len(state["group_ids"]),
    )
    xyz = np.asarray(mesh.points_m)[triangles]
    areas = np.linalg.norm(np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0]), axis=1) / 2
    cols = np.searchsorted(state["group_ids"], mesh.boundary_group_ids)
    group_areas = np.bincount(cols, weights=areas, minlength=ng)
    bi = {name: i for i, name in enumerate(state["bulk_ids"])}
    di = {name: i for i, name in enumerate(state["prescribed_ids"])}
    terms = []
    br, bc, bv = [], [], []
    D = np.zeros(nb)
    owner = np.full(n, -1, dtype=int)
    for face, row in enumerate(conditions):
        term = integrated_wall_terms(row, areas[face]) if row.kind == "robin" else None
        if term is not None:
            term["indexed"] = []
            for name, vector in term["vectors"].items():
                column = bi[name]
                br.extend(triangles[face].tolist())
                bc.extend([column] * 3)
                bv.extend(vector.tolist())
                D[column] += term["diagonal"][name]
                term["indexed"].append((column, vector, term["diagonal"][name]))
        elif row.kind == "dirichlet":
            column = di[row.temperature_id]
            if np.any((owner[triangles[face]] >= 0) & (owner[triangles[face]] != column)):
                raise ValueError("Conflicting physical prescribed temperatures")
            owner[triangles[face]] = column
        else:
            raise ValueError("Actual boundary classification missing")
        terms.append(term)
    robin = np.array([i for i, term in enumerate(terms) if term is not None])
    rt = triangles[robin]
    M = np.array([terms[i]["matrix"] for i in robin])
    R = coo_matrix(
        (M.ravel(), (np.repeat(rt, 3, axis=1).ravel(), np.tile(rt, (1, 3)).ravel())), shape=(n, n)
    ).tocsr()
    B = coo_matrix((bv, (br, bc)), shape=(n, nb)).tocsr()
    L = coo_matrix(
        (np.repeat(areas / (3 * group_areas[cols]), 3), (triangles.ravel(), np.repeat(cols, 3))),
        shape=(n, ng),
    ).tocsr()
    fixed, free = np.flatnonzero(owner >= 0), np.flatnonzero(owner < 0)
    E = coo_matrix((np.ones(len(fixed)), (fixed, owner[fixed])), shape=(n, nd)).tocsr()
    with np.load(OBSERVED / "gas-response.npz", allow_pickle=False) as data:
        maps = {name: data[name] for name in MAP_NAMES}
    factor = RobinGasFactor(
        mesh,
        assembly,
        tuple(state["group_ids"]),
        tuple(state["bulk_ids"]),
        tuple(state["prescribed_ids"]),
        group_areas,
        assembly.stiffness_w_k + R,
        B,
        D,
        L,
        E,
        free,
        fixed,
        None,
        np.zeros(len(triangles)),
        np.full(len(triangles), -1),
        areas,
        cols,
        terms,
        maps["reservoir_conductance_raw_w_k"],
        maps["mean_by_reservoir_temperature"],
        maps["mean_by_group_neumann_k_w"],
        maps["reservoir_heat_by_group_neumann"],
        state["diagnostics"],
    )
    return factor, cfg, source, hashes


def actual_replay(output: Path) -> dict[str, Any]:
    factor, cfg, source, hashes = completed_shell()
    if factor.lu is not None:
        raise ValueError("Actual replay must have NO native factor")
    with np.load(OBSERVED / "checked-gas-surface-fields.npz", allow_pickle=False) as data:
        ids, fields, saved_means = (
            data["case_ids"],
            data["nodal_temperature_k"],
            data["area_mean_temperature_k"],
        )
    prior_ledger = Path("build/wo03-gas-energy-diagnostic/final/energy-ledger.json")
    if sha(prior_ledger) != "77587b121669a1279e413a74e772f26ea7e223c8ee31e11c3eb16279894e2952":
        raise ValueError("Prior read-only ledger identity changed")
    old = {row["case"]: row for row in json.loads(prior_ledger.read_text())["cases"]}
    rows = []
    for case, field, means in zip(ids, fields, saved_means, strict=True):
        case = str(case)
        nb, nd, ng = len(factor.bulk_ids), len(factor.prescribed_ids), len(factor.group_ids)
        bulk, prescribed, loads = np.full(nb, 300.0), np.full(nd, 300.0), np.zeros(ng)
        if case.startswith("case300C"):
            ambient = source["selected_case"]["ambient_c"] + 273.15
            bulk[:] = ambient
            prescribed[:] = [
                573.15 if name == cfg["shared_motor_case_temperature_id"] else ambient
                for name in factor.prescribed_ids
            ]
        elif case.startswith("group"):
            group, sign = case.split("_", 1)
            loads[factor.group_ids.index(int(group[5:]))] = 1 if sign.startswith("+") else -1
        before = field.copy()
        answer = factor.evaluate_saved_field(field, bulk, prescribed, loads)
        field_out = answer.pop("nodal_temperature_k")
        if not np.array_equal(field_out, before):
            raise ValueError("Read-only evaluation changed a saved field")
        answer.pop("area_mean_fourth_power_k4")
        answer.pop("fourth_power_of_area_mean_k4")
        answer["saved_mean_max_difference_k"] = float(
            np.abs(np.asarray(answer["area_mean_temperature_k"]) - means).max()
        )
        answer["prior_audit_local_energy_difference_w"] = (
            answer["energy_balance_residual_w"]
            - old[case]["local_wall_and_element_gradient_difference_energy_residual_w"]
        )
        answer["heatmap_reference_scope"] = (
            "Old6a C/J retained for raw-cache comparison ONLY; not newly condensed stable C/J"
        )
        answer["case"] = case
        rows.append(answer)
    after = {path: sha(Path(path)) for path in hashes}
    return {
        "cases": rows,
        "original_inputs_unchanged": hashes == after,
        "original_input_sha256": hashes,
        "all10_stable_energy_under_unchanged1uW": all(
            abs(row["energy_balance_residual_w"]) <= 1e-6 for row in rows
        ),
        "all10_reference_form_under_unchanged1mWK": all(
            abs(row["form_balance_difference_w_times_k"]) <= 1e-3 for row in rows
        ),
        "new_actual_factor_PDE_or_ODE": False,
        "original_actual_record_remains_failed_and_immutable": True,
        "DMP_or_actual_temperature_accepted": False,
        "old_cache_C_J_not_replaced": True,
    }


def worker(mode: str, output: Path) -> None:
    started = time.monotonic()
    sources = [
        Path(__file__),
        Path("src/analysis/robin_gas.py"),
        Path("src/analysis/gas_conduction.py"),
        PRIOR,
        FIXTURE_CONFIG,
    ]
    before = {str(path): sha(path) for path in sources}
    if mode == "fixture-equivalence":
        result = fixtures(output)
    elif mode == "actual-field-replay":
        result = actual_replay(output)
    else:
        result = known_campaign(FIXTURE_CONFIG, output / "known-case-campaign")
    result.update(
        run_id=datetime.now(UTC).strftime(f"wo03-stable-ledger-{mode}-%Y%m%dT%H%M%S%fZ"),
        elapsed_s=time.monotonic() - started,
        input_sha256_before=before,
        input_sha256_after={str(path): sha(path) for path in sources},
        one_CPU=True,
        source_bytes_unchanged=all(sha(Path(path)) == digest for path, digest in before.items()),
    )
    write_json(output / "record.json", result)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = ["fixture-equivalence", "known-cases", "actual-field-replay"]
    parser.add_argument("--worker", choices=modes)
    parser.add_argument("--output", type=Path, default=Path("build/wo03-stable-gas-ledger/final"))
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, args.output)
        return 0
    args.output.mkdir(parents=True, exist_ok=False)
    results = []
    for mode in modes:
        folder = args.output / mode
        folder.mkdir()
        with (folder / "worker.log").open("w") as log:
            try:
                child = subprocess.run(
                    [
                        sys.executable,
                        str(Path(__file__)),
                        "--worker",
                        mode,
                        "--output",
                        str(folder),
                    ],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=120,
                    check=False,
                )
                code, capped = child.returncode, False
            except subprocess.TimeoutExpired:
                code, capped = None, True
        result = {"mode": mode, "child_returncode": code, "child120s_cap_reached": capped}
        if (folder / "record.json").exists():
            result.update(record=str(folder / "record.json"), sha256=sha(folder / "record.json"))
        results.append(result)
        if code != 0 or capped:
            break
    write_json(
        args.output / "record.json",
        {
            "evidence": results,
            "compute_cost_usd": 0,
            "one_CPU": True,
            "new_actual_factor_PDE_ODE_or_mesh": False,
            "no_actual_temperature_acceptance": True,
        },
    )
    print(args.output / "record.json")
    return (
        0
        if len(results) == 3
        and all(
            row["child_returncode"] == 0 and not row["child120s_cap_reached"] for row in results
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
