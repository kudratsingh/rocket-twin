"""Physical half-wall coupling, enclosure energy and unavailable-boundary cases."""

import numpy as np
import pytest

from src.analysis.surface_thermal import SurfaceNetwork
from src.analysis.thermal_radial import SIGMA, opaque_gap_flux


def test_common_surfaces_match_independent_halfwall_gap_solution() -> None:
    # Two gray coaxial surfaces. Same air/radiation surfaces, behind two
    # resistive material half walls; compare with the independently scalar solve.
    ri, ro, length, air_k = 0.015, 0.025, 0.12, 0.03
    ei, eo = 0.9, 0.3
    radiation = SIGMA * 2 * np.pi * ri * length / (1 / ei + ri / ro * (1 / eo - 1))
    air = 2 * np.pi * air_k * length / np.log(ro / ri)
    c = radiation * np.array([[-1.0, 1.0], [1.0, -1.0]])
    network = SurfaceNetwork(
        np.diag([1 / 2.0, 1 / 0.5]),
        air * np.array([[0.0, 1.0], [1.0, 0.0]]),
        np.zeros((2, 0)),
        c,
    )
    for hot, cold in ((573.15, 308.15), (308.15, 573.15), (308.15, 308.15)):
        result = network.solve(np.array([hot, cold]), np.empty(0))
        reference = opaque_gap_flux(
            hot,
            cold,
            2.0,
            0.5,
            ri,
            ro,
            length,
            air_k,
            0.9,
            inner_surface_emissivity=ei,
            outer_surface_emissivity=eo,
        )
        np.testing.assert_allclose(result.material_heat_w, [-reference, reference], atol=2e-9)
        assert abs(result.energy_residual_w) < 2e-9
        if hot > cold:
            assert cold < result.surface_temperature_k[1] < result.surface_temperature_k[0] < hot
        analytic, boundary = network.material_temperature_jacobian(result.surface_temperature_k)
        numerical = np.zeros_like(analytic)
        for column in range(2):
            delta = np.eye(2)[column] * 0.001
            plus = network.solve(np.array([hot, cold]) + delta, np.empty(0))
            minus = network.solve(np.array([hot, cold]) - delta, np.empty(0))
            numerical[:, column] = (plus.material_heat_w - minus.material_heat_w) / 0.002
        np.testing.assert_allclose(analytic, numerical, atol=1e-8, rtol=1e-6)
        np.testing.assert_allclose(analytic.sum(axis=0) + boundary.sum(axis=0), 0, atol=1e-12)


def test_black_reservoir_has_opposite_energy_and_monotonic_heat_flow() -> None:
    radiation = SIGMA * 0.01
    network = SurfaceNetwork(
        np.array([[0.2]]),
        np.zeros((1, 1)),
        np.zeros((1, 1)),
        radiation * np.array([[-1.0, 1.0], [1.0, -1.0]]),
    )
    result = network.solve(np.array([300.0]), np.array([573.15]))
    assert 300 < result.surface_temperature_k[0] < 573.15
    assert result.material_heat_w[0] > 0 > result.reservoir_heat_w[0]
    assert abs(result.energy_residual_w) < 1e-9
    derivative, boundary_derivative = network.material_temperature_jacobian(
        result.surface_temperature_k
    )
    plus = network.solve(np.array([300.001]), np.array([573.15]))
    minus = network.solve(np.array([299.999]), np.array([573.15]))
    np.testing.assert_allclose(
        derivative[:, 0],
        (plus.material_heat_w - minus.material_heat_w) / 0.002,
        atol=1e-8,
        rtol=1e-6,
    )
    np.testing.assert_allclose(
        derivative.sum(axis=0) + boundary_derivative.sum(axis=0), 0, atol=1e-12
    )
    same = network.solve(np.array([300.0]), np.array([300.0]))
    np.testing.assert_allclose(same.material_heat_w, [0], atol=1e-10)


def test_unanchored_surface_and_nonconservative_matrix_are_rejected() -> None:
    with pytest.raises(ValueError, match="no thermal boundary"):
        SurfaceNetwork(np.zeros((1, 1)), np.zeros((1, 1)), np.zeros((1, 0)), np.zeros((1, 1)))
    with pytest.raises(ValueError, match="conserve enclosure energy"):
        SurfaceNetwork(np.ones((1, 1)), np.zeros((1, 1)), np.zeros((1, 0)), np.ones((1, 1)))
