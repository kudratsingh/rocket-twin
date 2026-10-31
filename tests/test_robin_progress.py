"""Observer copies, exact algebra, atomic completeness and explicit interruption."""

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from scripts.wo03_gas_progress import MAP_NAMES, BlockCheckpoint
from src.analysis.gas_conduction import assemble_tetra_conductivity
from src.analysis.recorded_gas import RecordedGasResponse
from src.analysis.robin_gas import GasProgressCallbackError, RobinGasMesh, factor_robin_gas


def disconnected_fixture() -> tuple[RobinGasMesh, dict[int, Any]]:
    # 24 surfaces/states exercise a full16-column block plus a tail block.
    tetra = np.array([[0, 0, 0], [1, 0, 0], [-0.3, 0.2, 0], [0, 0, 1]])
    points = np.vstack([tetra + [3 * i, 0, 0] for i in range(6)])
    cells = np.arange(24).reshape(6, 4)
    assembly = assemble_tetra_conductivity(points, cells, 1)
    faces = assembly.exterior_triangles.copy()
    xyz = points[faces]
    flip = (
        np.sum(
            np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
            * (points[assembly.exterior_opposite_nodes] - xyz[:, 0]),
            axis=1,
        )
        > 0
    )
    faces[flip, 1], faces[flip, 2] = faces[flip, 2].copy(), faces[flip, 1].copy()
    groups = np.arange(len(faces))
    mesh = RobinGasMesh(points, cells, faces, groups, {"source": "source_independent_fixture"})
    conditions = {
        int(g): {"kind": "robin", "bulk_id": f"bulk{g}", "h_w_m2_k": 1 + g / 10} for g in groups
    }
    conditions[0] = {"kind": "dirichlet", "temperature_id": "physical_gas_ambient"}
    return mesh, conditions


def binding() -> dict[str, Any]:
    return {
        "input_sha256": {
            "fixture_definition": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        },
        "physical_inputs": {
            "conductivity_w_m_k": 1,
            "ordering": "COLAMD",
            "rhs_block_size": 16,
            "actual_mesh": False,
        },
    }


def test_observer_cannot_mutate_factor_and_all_blocks_are_exact() -> None:
    mesh, conditions = disconnected_fixture()
    default = factor_robin_gas(mesh, conditions, 1)
    events = []

    def destructive_observer(event: dict[str, Any]) -> None:
        events.append(
            {
                "phase": event["phase"],
                "start": event.get("column_start"),
                "stop": event.get("column_stop"),
            }
        )
        for block in event.get("map_blocks", {}).values():
            block[:] = np.nan
        event["ordered_ids"]["group_ids"].append(999)
        event["resource_counts"]["free_nodes"] = -999

    observed = factor_robin_gas(mesh, conditions, 1, progress_callback=destructive_observer)
    for name in (*MAP_NAMES, "group_areas_m2"):
        assert np.array_equal(getattr(default, name), getattr(observed, name))
    bulk = np.linspace(290, 310, len(default.bulk_ids))
    prescribed = np.full(len(default.prescribed_ids), 302.0)
    loads = np.linspace(-0.1, 0.1, 24)
    assert np.array_equal(
        default.reconstruct(bulk, prescribed, loads), observed.reconstruct(bulk, prescribed, loads)
    )
    for family in ["reservoir", "surface"]:
        assert [(e["start"], e["stop"]) for e in events if e["phase"] == f"{family}_block_end"] == [
            (0, 16),
            (16, 24),
        ]
    phases = [e["phase"] for e in events]
    assert phases[:8] == [
        "assembly_begin",
        "assembly_end",
        "wall_build_begin",
        "wall_build_end",
        "preflight_begin",
        "preflight_end",
        "LU_begin",
        "LU_end",
    ]
    assert phases[-2:] == ["final_checks_begin", "final_checks_end"]
    assert observed.diagnostics["algebra_checks_pass"]


def test_atomic_checkpoint_complete_cache_and_interruption(tmp_path: Path) -> None:
    mesh, conditions = disconnected_fixture()
    observer = BlockCheckpoint(tmp_path / "complete", binding())
    factor = factor_robin_gas(mesh, conditions, 1, progress_callback=observer)
    manifest = json.loads((observer.directory / "manifest.json").read_text())
    assert not manifest[
        "complete_operator"
    ]  # Returned final event alone never publishes completion.
    assert len(manifest["blocks"]) == 4
    observer.finalize(factor)
    manifest = json.loads((observer.directory / "manifest.json").read_text())
    assert manifest["complete_operator"] and manifest["numerical_checks_pass"]
    assert not manifest["native_LU_or_full_nodal_basis_exported"]
    cached = RecordedGasResponse.load(
        observer.directory / "gas-response.npz",
        observer.directory / "gas-response.json",
        operator_sha256=manifest["operator_sha256"],
        metadata_sha256=manifest["metadata_sha256"],
    )
    for name in MAP_NAMES:
        assert np.array_equal(getattr(factor, name), getattr(cached, name))
    interrupted = BlockCheckpoint(tmp_path / "interrupted", binding(), interrupt_after_blocks=1)
    with pytest.raises(GasProgressCallbackError, match="reservoir_block_end") as failure:
        factor_robin_gas(mesh, conditions, 1, progress_callback=interrupted)
    assert isinstance(failure.value.__cause__, OSError)
    partial = json.loads((interrupted.directory / "manifest.json").read_text())
    assert len(partial["blocks"]) == 1
    assert not partial["complete_operator"] and not partial["numerical_checks_pass"]
    assert not (interrupted.directory / "gas-response.npz").exists()
    assert not any(e["phase"] == "final_checks_end" for e in partial["events"])
    with pytest.raises(ValueError, match="Complete returned factor"):
        interrupted.finalize(factor)
    # Altered checkpoint bytes cannot be promoted to a complete operator.
    untrusted = BlockCheckpoint(tmp_path / "untrusted", binding())
    f = factor_robin_gas(mesh, conditions, 1, progress_callback=untrusted)
    block_path = untrusted.directory / untrusted.manifest["blocks"][0]["path"]
    block_path.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="hash changed"):
        untrusted.finalize(f)
    assert not untrusted.manifest["complete_operator"]


def test_observer_failure_and_preflight_rejection_stop_before_native_lu() -> None:
    mesh, conditions = disconnected_fixture()

    def failure(_event: dict[str, Any]) -> None:
        raise OSError("checkpoint unavailable")

    with pytest.raises(GasProgressCallbackError, match="assembly_begin") as result:
        factor_robin_gas(mesh, conditions, 1, progress_callback=failure)
    assert isinstance(result.value.__cause__, OSError)
    events: list[dict[str, Any]] = []
    with pytest.raises(MemoryError, match="preflight stop"):
        factor_robin_gas(
            mesh, conditions, 1, max_factor_free_nodes=0, progress_callback=events.append
        )
    assert events[-1]["phase"] == "preflight_end" and not events[-1]["accepted"]
    assert not any(event["phase"] == "LU_begin" for event in events)
