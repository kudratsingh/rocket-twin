"""Independent slab calorimetry and separate gas/brightness boundaries."""

from typing import Any

import numpy as np
import pytest
from scipy.optimize import brentq

from src.analysis.gas_conduction import assemble_tetra_conductivity
from src.analysis.gas_radiation import GasRadiationNetwork
from src.analysis.robin_gas import RobinGasMesh, factor_robin_gas


def slab(*, prescribed_cold: bool = False) -> Any:
    # Six positive tets around the long cube diagonal. No CAD or Gmsh needed.
    points = np.array(
        [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]],
        dtype=float,
    ) * [0.01, 0.02, 0.03]
    tets = np.array(
        [[0, 1, 2, 6], [0, 2, 3, 6], [0, 3, 7, 6], [0, 7, 4, 6], [0, 4, 5, 6], [0, 5, 1, 6]]
    )
    assembly = assemble_tetra_conductivity(points, tets, 0.026)
    triangles = assembly.exterior_triangles.copy()
    opposite = assembly.exterior_opposite_nodes
    normal = np.cross(
        points[triangles[:, 1]] - points[triangles[:, 0]],
        points[triangles[:, 2]] - points[triangles[:, 0]],
    )
    inward = np.sum(normal * (points[opposite] - points[triangles[:, 0]]), axis=1) > 0
    triangles[inward] = triangles[inward][:, [0, 2, 1]]
    x = points[triangles, 0]
    groups = np.where(np.all(x == 0, axis=1), 0, np.where(np.all(x == 0.01, axis=1), 1, 2))
    cold = (
        {"kind": "dirichlet", "temperature_id": "outside_gas"}
        if prescribed_cold
        else {"kind": "robin", "bulk_id": "cold", "h_w_m2_k": 5.0}
    )
    return factor_robin_gas(
        RobinGasMesh(points, tets, triangles, groups, {"fixture": "affine slab"}),
        {
            0: {"kind": "robin", "bulk_id": "hot", "h_w_m2_k": 10.0},
            1: cold,
            2: {"kind": "insulated"},
        },
        0.026,
    )


def test_common_halfwalls_against_independent_parallel_plate_flux() -> None:
    factor = slab()
    area, sigma = 0.02 * 0.03, 5.670374419e-8
    emissivities = (0.7, 0.9)
    exchange = sigma * area / (1 / emissivities[0] + 1 / emissivities[1] - 1)
    c = exchange * np.array([[-1.0, 1.0], [1.0, -1.0]])
    network = GasRadiationNetwork(
        factor,
        c,
        (0, 1),
        (-1, -1),
        (),
        "Isothermal infinite parallel plates; insulated lateral gas walls",
    )
    by_id = {"hot": 450.0, "cold": 300.0}
    theta = np.array([by_id[k] for k in factor.bulk_ids])
    solution = network.solve(
        theta, np.array([]), np.array([]), reconstruct=True, absolute_tolerance_k=1e-10
    )
    hot_r, cold_r = 1 / (10 * area), 1 / (5 * area)

    def equation(total_heat: float) -> float:
        hot = 450 - total_heat * hot_r
        cold = 300 + total_heat * cold_r
        gas = 0.026 * area / 0.01 * (hot - cold)
        radiation = exchange * (hot**4 - cold**4)
        return gas + radiation - total_heat

    heat = brentq(equation, 0, 150 / (hot_r + cold_r), xtol=1e-14)
    expected = np.array([-heat if k == "hot" else heat for k in factor.bulk_ids])
    assert solution.heat_into_material_and_gas_reservoir_w == pytest.approx(expected, abs=2e-12)
    assert abs(solution.enclosure_energy_residual_w) < 1e-12
    assert solution.reconstruction is not None
    assert solution.reconstruction["nonlinear_mean_reconstruction_difference_k"] < 1e-10
    # Each end is exactly isothermal; the mid-wall field is affine.
    projection_error = solution.reconstruction[
        "radiation_projection_mean_fourth_power_difference_k4"
    ]
    assert np.max(np.abs(np.array(projection_error)[:2])) < 1e-4
    h = 0.01
    for col in range(len(theta)):
        delta = np.eye(len(theta))[col] * h
        plus = network.solve(theta + delta, np.array([]), np.array([]))
        minus = network.solve(theta - delta, np.array([]), np.array([]))
        derivative = (
            plus.heat_into_material_and_gas_reservoir_w
            - minus.heat_into_material_and_gas_reservoir_w
        ) / (2 * h)
        assert solution.state_heat_jacobian_w_k[:, col] == pytest.approx(derivative, abs=1e-11)


def test_opening_brightness_changes_radiation_without_changing_gas_temperature() -> None:
    factor = slab(prescribed_cold=True)
    c = 0.02 * 0.03 * 5.670374419e-8 * np.array([[-1.0, 1.0], [1.0, -1.0]])
    network = GasRadiationNetwork(
        factor,
        c,
        (0, -1),
        (-1, 0),
        ("outside_radiation",),
        "Black opening brightness distinct from prescribed gas",
    )
    bulk, gas = np.array([350.0]), np.array([300.0])
    cool = network.solve(bulk, gas, np.array([300.0]), reconstruct=True)
    hot = network.solve(bulk, gas, np.array([500.0]), reconstruct=True)
    assert (
        hot.heat_into_material_and_gas_reservoir_w[0]
        > cool.heat_into_material_and_gas_reservoir_w[0]
    )
    assert abs(cool.enclosure_energy_residual_w) < 1e-12
    assert abs(hot.enclosure_energy_residual_w) < 1e-12
    assert hot.reconstruction is not None
    # Physical opening nodes remain exactly300K despite500K radiative brightness.
    field = hot.reconstruction["nodal_temperature_k"]
    points = factor.mesh.points_m
    assert field[points[:, 0] == 0.01] == pytest.approx(300, abs=1e-12)
    h = 0.01
    plus = network.solve(bulk, gas, np.array([500.0 + h]))
    minus = network.solve(bulk, gas, np.array([500.0 - h]))
    derivative = (
        plus.heat_into_material_and_gas_reservoir_w - minus.heat_into_material_and_gas_reservoir_w
    ) / (2 * h)
    assert hot.fixed_brightness_heat_jacobian_w_k[:, 0] == pytest.approx(derivative, abs=1e-10)
    with pytest.raises(ValueError, match="owner"):
        GasRadiationNetwork(factor, c, (0, 1), (0, -1), ("outside",), "invalid double owner")
    with pytest.raises(RuntimeError, match="limit"):
        network.solve(bulk, gas, np.array([1000.0]), maximum_iterations=1)


def test_transient_hook_keeps_one_capacity_and_external_energy_ledger() -> None:
    from src.analysis.cad_gas_surface_adapter import CadGasSurfaceAdapter

    factor = slab(prescribed_cold=True)
    c = 0.02 * 0.03 * 5.670374419e-8 * np.array([[-1.0, 1.0], [1.0, -1.0]])
    network = GasRadiationNetwork(
        factor, c, (0, -1), (-1, 0), ("opening",), "Independent slab hook calorimetry"
    )
    adapter = CadGasSurfaceAdapter(
        network,
        {"hot": "motor_mount"},
        {"outside_gas": "ambient"},
        {"opening": "case"},
        {"fixture": "no geometry acceptance"},
    )
    adapter.prepare(
        ["motor_mount"],
        {"air_conductivity_w_m_k": 0.026},
        [{"model": "opaque_gap"}, {"model": "direct_solid_contact"}],
    )
    heat, external, _ = adapter.rates(
        np.array([350.0]), case_temperature_k=500, ambient_temperature_k=300
    )
    direct = network.solve(np.array([350.0]), np.array([300.0]), np.array([500.0]))
    assert heat[0] == pytest.approx(direct.heat_into_material_and_gas_reservoir_w[0], abs=1e-12)
    assert heat.sum() == pytest.approx(external, abs=1e-12)
    derivative, external_derivative = adapter.jacobian(
        np.array([350.0]), case_temperature_k=500, ambient_temperature_k=300
    )
    assert derivative.sum(axis=0) == pytest.approx(external_derivative, abs=1e-12)
    metadata = adapter.metadata()
    assert metadata["provenance"]["legacy_opaque_gaps_replaced"] == 1
    assert metadata["provenance"]["legacy_direct_solid_contacts_retained_by_caller"] == 1
    assert metadata["capacities_and_existing_solid_contacts_owned_once_by_transient_caller"]
    assert not metadata["engineering_acceptance"]
    with pytest.raises(ValueError, match="missing"):
        adapter.prepare(["wrong_node"], {"air_conductivity_w_m_k": 0.026}, [])
