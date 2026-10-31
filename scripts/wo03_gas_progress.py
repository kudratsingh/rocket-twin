"""Fixture-only progress/checkpoint verification; never attempts actual gas CAD."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
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

from scripts.wo03_robin_gas import fixture_mesh
from src.analysis.robin_gas import GasProgressCallbackError, factor_robin_gas

MAP_NAMES = (
    "mean_by_reservoir_temperature",
    "reservoir_conductance_raw_w_k",
    "mean_by_group_neumann_k_w",
    "reservoir_heat_by_group_neumann",
)
PRIOR_SHA256 = "21c115c6ca170a4eecf1bcad222fcea94b61de5482a3eb91533b51eafff1825b"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


class BlockCheckpoint:
    """Atomic raw blocks, bound to immutable input identities; partial is invalid.

    This observer never owns a native factor or full nodal response basis.
    finalize() requires all raw columns and successful source algebra checks.
    There is no partial restart/merge implementation or ODE adapter.
    """

    def __init__(
        self, directory: Path, source_binding: dict[str, Any], *, interrupt_after_blocks: int = 0
    ) -> None:
        if not source_binding.get("input_sha256") or not source_binding.get("physical_inputs"):
            raise ValueError("Explicit source hashes and physical inputs required")
        if directory.exists() and any(directory.iterdir()):
            raise ValueError("Checkpoint output must be fresh; no implicit resume")
        directory.mkdir(parents=True, exist_ok=True)
        self.directory = directory
        self.interrupt_after_blocks = interrupt_after_blocks
        # JSON copy prevents a caller mutating the supplied nested metadata later.
        self.manifest: dict[str, Any] = {
            "source_binding": json.loads(json.dumps(source_binding, allow_nan=False)),
            "complete_operator": False,
            "numerical_checks_pass": False,
            "partial_operator_usable_for_ODE": False,
            "native_LU_or_full_nodal_basis_exported": False,
            "events": [],
            "blocks": [],
        }
        write_json(directory / "manifest.json", self.manifest)

    def __call__(self, event: dict[str, Any]) -> None:
        plain = {key: value for key, value in event.items() if key != "map_blocks"}
        self.manifest["events"].append(json.loads(json.dumps(plain, allow_nan=False)))
        self.manifest["last_phase"] = event["phase"]
        self.manifest["ordered_ids"] = plain["ordered_ids"]
        if "map_blocks" in event:
            family = "reservoir" if event["phase"] == "reservoir_block_end" else "surface"
            expected = set(MAP_NAMES[:2] if family == "reservoir" else MAP_NAMES[2:])
            if (
                event["phase"] not in ("reservoir_block_end", "surface_block_end")
                or set(event["map_blocks"]) != expected
            ):
                raise ValueError("Unexpected raw checkpoint block identity")
            start, stop = int(event["column_start"]), int(event["column_stop"])
            if not 0 <= start < stop:
                raise ValueError("Invalid completed raw block interval")
            filename = f"{family}-{start:06d}-{stop:06d}.npz"
            destination = self.directory / filename
            if destination.exists():
                raise ValueError("Duplicate completed checkpoint block")
            temporary = destination.with_suffix(".npz.tmp")
            with temporary.open("wb") as stream:
                np.savez(stream, **event["map_blocks"])
            temporary.replace(destination)
            self.manifest["blocks"].append(
                {
                    "family": family,
                    "column_start": start,
                    "column_stop": stop,
                    "path": filename,
                    "sha256": sha(destination),
                    "arrays": {
                        key: list(value.shape) for key, value in event["map_blocks"].items()
                    },
                }
            )
        write_json(self.directory / "manifest.json", self.manifest)
        if (
            "map_blocks" in event
            and self.interrupt_after_blocks
            and len(self.manifest["blocks"]) >= self.interrupt_after_blocks
        ):
            raise OSError("Deliberate fixture checkpoint interruption")

    def finalize(self, factor: Any) -> None:
        if (
            self.manifest.get("last_phase") != "final_checks_end"
            or not self.manifest["events"][-1].get("algebra_checks_pass")
            or not factor.diagnostics["algebra_checks_pass"]
        ):
            raise ValueError("Complete returned factor and final algebra checks required")
        expected_ids = {
            "group_ids": list(factor.group_ids),
            "bulk_ids": list(factor.bulk_ids),
            "prescribed_ids": list(factor.prescribed_ids),
        }
        if self.manifest["ordered_ids"] != expected_ids:
            raise ValueError("Checkpoint ordered identities changed")
        coverage = {name: np.zeros(getattr(factor, name).shape[1], dtype=int) for name in MAP_NAMES}
        for block in self.manifest["blocks"]:
            path = self.directory / block["path"]
            if sha(path) != block["sha256"]:
                raise ValueError("Checkpoint block hash changed")
            with np.load(path, allow_pickle=False) as data:
                for name in data.files:
                    start, stop = block["column_start"], block["column_stop"]
                    expected = getattr(factor, name)[:, start:stop]
                    if not np.array_equal(data[name], expected):
                        raise ValueError("Checkpoint differs from returned raw map")
                    coverage[name][start:stop] += 1
        if any(np.any(value != 1) for value in coverage.values()):
            raise ValueError("Incomplete/overlapping checkpoint column coverage")
        arrays = {name: getattr(factor, name) for name in MAP_NAMES}
        arrays["group_areas_m2"] = factor.group_areas_m2
        operator = self.directory / "gas-response.npz"
        with operator.with_suffix(".npz.tmp").open("wb") as stream:
            np.savez(stream, **arrays)
        operator.with_suffix(".npz.tmp").replace(operator)
        write_json(
            self.directory / "gas-response.json",
            {
                **expected_ids,
                "diagnostics": factor.diagnostics,
                "source_binding": self.manifest["source_binding"],
                "operator_sha256": sha(operator),
                "spatial_field_reconstruction_from_reduced_cache": "unavailable",
                "fixture_only_not_actual_thermal_acceptance": True,
            },
        )
        self.manifest.update(
            complete_operator=True,
            numerical_checks_pass=True,
            complete_scope="Returned fixture linear operator only; no actual thermal acceptance",
            operator_sha256=sha(operator),
            metadata_sha256=sha(self.directory / "gas-response.json"),
        )
        write_json(self.directory / "manifest.json", self.manifest)


def load_prior(path: Path) -> Any:
    if sha(path) != PRIOR_SHA256:
        raise ValueError("Preserved prior executed module identity changed")
    name = "wo03_preserved_prior_robin_gas"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ValueError("Cannot load preserved module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fixture_conditions(fixture: str, cfg: dict[str, Any], groups: Any) -> dict[int, Any]:
    s = cfg["slab"]
    conditions = {int(g): {"kind": "insulated"} for g in groups}
    if fixture in ("finite_halfwall_slab", "insulated_divider"):
        for group, side in [(0, "hot"), (1, "cold")]:
            conditions[group] = {
                "kind": "robin",
                "bulk_id": f"{side}_bulk",
                "h_w_m2_k": s[f"{side}_halfwall_conductivity_w_m_k"]
                / s[f"{side}_halfwall_length_m"],
            }
    elif fixture == "shared_corner":
        conditions = {
            g: {
                "kind": "robin",
                "bulk_id": f"component{g}",
                "h_w_m2_k": cfg["shared_corner"]["h_by_face_w_m2_k"][g],
            }
            for g in range(6)
        }
    elif fixture == "mixed_prescribed":
        conditions = {g: {"kind": "robin", "bulk_id": "wall", "h_w_m2_k": 2 + g} for g in range(6)}
        conditions[0] = {"kind": "dirichlet", "temperature_id": "physical_gas_ambient"}
    else:
        raise ValueError("Unknown source-independent fixture")
    return conditions


def campaign(config: Path, prior_path: Path, output: Path) -> dict[str, Any]:
    started = time.monotonic()
    prior = load_prior(prior_path)
    cfg = yaml.safe_load(config.read_text())
    output.mkdir(parents=True, exist_ok=False)
    source_paths = [
        config,
        prior_path,
        Path(__file__),
        Path("src/analysis/robin_gas.py"),
        Path("src/analysis/gas_conduction.py"),
        Path("scripts/wo03_robin_gas.py"),
    ]
    before = {str(path): sha(path) for path in source_paths}
    results = []
    for fixture in cfg["fixtures"]:
        fixture_started = time.monotonic()
        for level in cfg["mesh_levels"]:
            mesh, source = fixture_mesh(fixture, level, cfg)
            if len(mesh.points_m) > 5000 or len(mesh.tetrahedra) > 20000:
                raise ValueError(
                    "This verification runner permits small fixtures only, never actual gas CAD"
                )
            conditions = fixture_conditions(fixture, cfg, np.unique(mesh.boundary_group_ids))
            binding = {
                "input_sha256": {**before, str(source): sha(source)},
                "physical_inputs": {
                    "conductivity_w_m_k": cfg["conductivity_w_m_k"],
                    "conditions": conditions,
                    "ordering": "COLAMD",
                    "rhs_block_size": 16,
                },
                "fixture": fixture,
                "level": level,
            }
            observer = BlockCheckpoint(output / fixture / f"level-{level}", binding)
            arguments = {"max_tetrahedra": 150000, "rhs_block_size": 16}
            old = prior.factor_robin_gas(mesh, conditions, cfg["conductivity_w_m_k"], **arguments)
            default = factor_robin_gas(mesh, conditions, cfg["conductivity_w_m_k"], **arguments)
            observed = factor_robin_gas(
                mesh, conditions, cfg["conductivity_w_m_k"], progress_callback=observer, **arguments
            )
            maps_equal = all(
                np.array_equal(getattr(old, name), getattr(default, name))
                and np.array_equal(getattr(default, name), getattr(observed, name))
                for name in (*MAP_NAMES, "group_areas_m2")
            )
            bulk = np.linspace(291, 309, len(default.bulk_ids))
            fixed = np.full(len(default.prescribed_ids), 302.0)
            loads = np.linspace(-0.0001, 0.0001, len(default.group_ids))
            fields = [factor.reconstruct(bulk, fixed, loads) for factor in [old, default, observed]]
            fields_equal = np.array_equal(fields[0], fields[1]) and np.array_equal(
                fields[1], fields[2]
            )
            observer.finalize(observed)
            if not maps_equal or not fields_equal:
                raise ValueError(
                    "Observation or default-path change altered raw matrix/field bytes"
                )
            results.append(
                {
                    "fixture": fixture,
                    "level": level,
                    "prior_default_observed_maps_exactly_equal": maps_equal,
                    "prior_default_observed_nodal_fields_exactly_equal": fields_equal,
                    "algebra_checks_pass": observed.diagnostics["algebra_checks_pass"],
                    "manifest": str(observer.directory / "manifest.json"),
                    "manifest_sha256": sha(observer.directory / "manifest.json"),
                }
            )
            if time.monotonic() - fixture_started > 180:
                raise TimeoutError("Fixture verification exceeded180s; no actual retry")
    mesh, source = fixture_mesh("finite_halfwall_slab", 0, cfg)
    conditions = fixture_conditions("finite_halfwall_slab", cfg, np.unique(mesh.boundary_group_ids))
    interruption = BlockCheckpoint(
        output / "deliberate-interruption",
        {
            "input_sha256": {**before, str(source): sha(source)},
            "physical_inputs": {
                "conductivity_w_m_k": cfg["conductivity_w_m_k"],
                "conditions": conditions,
                "ordering": "COLAMD",
                "rhs_block_size": 16,
            },
            "fixture": "finite_halfwall_slab",
            "level": 0,
        },
        interrupt_after_blocks=1,
    )
    interrupted_explicitly = False
    try:
        factor_robin_gas(
            mesh, conditions, cfg["conductivity_w_m_k"], progress_callback=interruption
        )
    except GasProgressCallbackError as exc:
        interrupted_explicitly = isinstance(exc.__cause__, OSError)
    partial = json.loads((interruption.directory / "manifest.json").read_text())
    fail_closed = bool(
        interrupted_explicitly
        and not partial["complete_operator"]
        and not partial["numerical_checks_pass"]
        and len(partial["blocks"]) == 1
        and not (interruption.directory / "gas-response.npz").exists()
    )
    if not fail_closed:
        raise ValueError("Deliberate known-case interruption did not fail closed")
    after = {str(path): sha(path) for path in source_paths}
    result = {
        "run_id": datetime.now(UTC).strftime("wo03-gas-progress-%Y%m%dT%H%M%S%fZ"),
        "elapsed_s": time.monotonic() - started,
        "compute_cost_usd": 0,
        "one_CPU": True,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "inputs_unchanged": before == after,
        "preserved_prior_source_sha256": PRIOR_SHA256,
        "fixtures": results,
        "all_prior_default_observed_maps_and_fields_exactly_equal": all(
            row["prior_default_observed_maps_exactly_equal"]
            and row["prior_default_observed_nodal_fields_exactly_equal"]
            for row in results
        ),
        "actual_mesh_factor_attempted": False,
        "actual_ODE_or_thermal_acceptance": False,
        "deliberate_interruption_fail_closed": fail_closed,
        "interrupted_manifest": str(interruption.directory / "manifest.json"),
        "interrupted_manifest_sha256": sha(interruption.directory / "manifest.json"),
    }
    write_json(output / "record.json", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/studies/wo03-robin-gas.yaml"))
    parser.add_argument(
        "--prior-source",
        type=Path,
        default=Path("build/wo03-gas-progress/prior-source/robin_gas.py"),
    )
    parser.add_argument("--output", type=Path, default=Path("build/wo03-gas-progress/fixtures"))
    args = parser.parse_args()
    try:
        result = campaign(args.config, args.prior_source, args.output)
    except GasProgressCallbackError as exc:
        raise SystemExit(f"Observation/checkpoint failed explicitly: {exc}") from exc
    print(args.output / "record.json")
    return (
        0
        if result["inputs_unchanged"]
        and result["all_prior_default_observed_maps_and_fields_exactly_equal"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
