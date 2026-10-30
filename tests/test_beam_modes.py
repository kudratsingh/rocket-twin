from __future__ import annotations

import numpy as np
import pytest

from src.analysis.beam_modes import PointMass, assemble_free_free_beam, free_free_beam_modes


def exact_frequencies(length: float, ei: float, mu: float, count: int = 3) -> np.ndarray:
    roots = np.array([4.7300407449, 7.8532046241, 10.9956078380])[:count]
    return roots**2 / (2.0 * np.pi * length**2) * np.sqrt(ei / mu)


@pytest.mark.parametrize("elements", [10, 20, 40])
def test_uniform_free_free_beam_modes_converge(elements: int) -> None:
    length, ei, mu = 1.2, 15.0, 0.8
    result = free_free_beam_modes(
        np.linspace(0.0, length, elements + 1),
        np.full(elements, ei),
        np.full(elements, mu),
        elastic_modes=3,
    )
    relative_error = np.abs(
        result.frequencies_hz - exact_frequencies(length, ei, mu)
    ) / exact_frequencies(length, ei, mu)
    assert np.max(relative_error) < 0.01
    assert np.max(result.rigid_residuals) < 1e-9
    np.testing.assert_allclose(result.modal_mass_gram, np.eye(3), atol=1e-10)
    assert np.all(
        result.rigid_eigenvalues <= 1e-9 * np.max(result.frequencies_hz**2 * (2 * np.pi) ** 2)
    )


def test_stiffness_scaling_scales_frequency_by_sqrt() -> None:
    x = np.linspace(0.0, 1.0, 21)
    first = free_free_beam_modes(x, np.full(20, 12.0), np.full(20, 0.5))
    second = free_free_beam_modes(x, np.full(20, 6.0), np.full(20, 0.5))
    np.testing.assert_allclose(
        second.frequencies_hz / first.frequencies_hz, np.sqrt(0.5), rtol=1e-11
    )


def test_point_mass_uses_hermite_location_and_rejects_outside_domain() -> None:
    stations = np.array([0.0, 0.5, 1.0])
    k0, m0 = assemble_free_free_beam(stations, [10.0, 10.0], [1.0, 1.0])
    _, m1 = assemble_free_free_beam(
        stations,
        [10.0, 10.0],
        [1.0, 1.0],
        [PointMass(0.25, 0.2, 0.01)],
    )
    assert np.linalg.norm(m1 - m0) > 0.0
    assert np.allclose(k0, k0.T)
    with pytest.raises(ValueError, match="outside the beam domain"):
        assemble_free_free_beam(stations, [10.0, 10.0], [1.0, 1.0], [PointMass(1.01, 0.2)])


def test_rejects_nonincreasing_stations_and_nonpositive_profile() -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
        assemble_free_free_beam([0.0, 0.5, 0.5], [1.0, 1.0], [1.0, 1.0])
    with pytest.raises(ValueError, match="finite positive"):
        assemble_free_free_beam([0.0, 1.0], [0.0], [1.0])
