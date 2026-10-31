"""Common physical surface coupling, coverage failures and occupied-gap reporting."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import yaml

from src.analysis.finite_radiation import Patch
from src.analysis.finite_surface_adapter import FiniteSurfaceAdapter
from src.analysis.thermal_radial import opaque_gap_flux
from src.vehicle.schema import load_vehicle


def case_fixture() -> tuple[FiniteSurfaceAdapter, dict[str, float | list[float]], float]:
    vehicle = load_vehicle("configs/vehicle/platform/performance.yaml")
    parts = {part.id: part for part in vehicle.parts}
    case = parts["motor"]
    liner = parts["motor_liner"]
    ri, ro = case.geometry["radius_m"], liner.geometry["inner_radius_m"]
    start, length = liner.position_m, liner.geometry["length_m"]
    # Independent closed long-cylinder fixture: physical finite end-view factors
    # are deliberately not claimed here. This isolates adapter half-wall mapping.
    patches = [
        Patch("motor", "cylinder", ri, start, start + length, 1, "outer_cylinder"),
        Patch("motor_liner", "cylinder", ro, start, start + length, -1, "inner_cylinder"),
    ]
    view = [[0.0, 1.0], [ri / ro, 1 - ri / ro]]
    materials = yaml.safe_load(Path("configs/engineering/wo03.yaml").read_text())["materials"]
    adapter = FiniteSurfaceAdapter(
        vehicle,
        materials,
        patches,
        view,
        [0.9, 0.9],
        end_boundary_modes={"fore_end_reservoir": "ambient", "aft_end_reservoir": "case"},
        provenance={"scope": "independent long-cylinder fixture"},
        surface_tolerance_w=1e-10,
    )
    centre = float(np.sqrt(ro * liner.geometry["radius_m"]))
    context = {
        "motor_radius_m": ri,
        "liner_inner_radius_m": ro,
        "start_m": start,
        "end_m": start + length,
        "air_conductivity_w_m_k": 0.04,
        "liner_radial_centres_m": [centre],
    }
    resistance = np.log(centre / ro) / (
        2 * np.pi * materials["mica"]["conductivity_w_m_k"] * length
    )
    return adapter, context, float(resistance)


def test_adapter_matches_original_gap_at_common_unknown_surfaces() -> None:
    adapter, case_gap, resistance = case_fixture()
    adapter.prepare(["motor_liner.cell_0"], case_gap, [])
    length = float(case_gap["end_m"]) - float(case_gap["start_m"])
    for case, material in ((573.15, 308.15), (308.15, 573.15), (350.0, 350.0)):
        q, external, links = adapter.rates(
            [material], case_temperature_k=case, ambient_temperature_k=300
        )
        reference = opaque_gap_flux(
            case,
            material,
            0,
            resistance,
            float(case_gap["motor_radius_m"]),
            float(case_gap["liner_inner_radius_m"]),
            length,
            0.04,
            0.9,
        )
        assert q[0] == pytest.approx(reference, abs=3e-9)
        assert external == pytest.approx(q[0], abs=3e-9)
        assert links
        matrix, external_jacobian = adapter.jacobian(
            [material], case_temperature_k=case, ambient_temperature_k=300
        )
        step = 0.001
        plus, _, _ = adapter.rates(
            [material + step], case_temperature_k=case, ambient_temperature_k=300
        )
        minus, _, _ = adapter.rates(
            [material - step], case_temperature_k=case, ambient_temperature_k=300
        )
        np.testing.assert_allclose(matrix[:, 0], (plus - minus) / (2 * step), atol=1e-7, rtol=1e-6)
        np.testing.assert_allclose(external_jacobian, matrix.sum(axis=0), atol=1e-10)
    metadata = adapter.metadata()
    assert metadata["maximum_surface_energy_residual_w"] < 1e-9
    assert metadata["full_cad_conservative_bound"] is False
    assert metadata["thermal_acceptance_available"] is False


def test_adapter_rejects_missing_state_and_unexplained_missing_gap_faces() -> None:
    adapter, case_gap, _ = case_fixture()
    with pytest.raises(ValueError, match="prepare"):
        adapter.rates([300], case_temperature_k=500, ambient_temperature_k=300)
    with pytest.raises(ValueError, match="no ODE material node"):
        adapter.prepare(["different_node"], case_gap, [])
    broken = {
        "model": "opaque_gap",
        "source_part_id": "motor_radiant_shield",
        "target_part_id": "aft_shell",
        "source_surface_radius_m": 0.01512,
        "target_surface_radius_m": 0.0325,
        "start_m": case_gap["start_m"],
        "end_m": case_gap["end_m"],
    }
    with pytest.raises(ValueError, match="Incomplete or multiply allocated"):
        adapter.prepare(["motor_liner.cell_0"], case_gap, [broken])
