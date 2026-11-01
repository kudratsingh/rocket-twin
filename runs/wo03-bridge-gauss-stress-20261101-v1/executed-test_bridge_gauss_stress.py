"""Independent affine-field patch checks before applying saved actual U."""

import numpy as np
import pytest

from scripts.wo03_bridge_gauss_stress import EDGE, quadrature, recover, von_mises


@pytest.mark.parametrize("curved", [False, True])
@pytest.mark.parametrize("kind", ["normal", "shear", "hydrostatic", "nonsymmetric"])
def test_affine_field_on_affine_and_curved_geometry(curved, kind):
    vertices = np.array([[0.2, -0.4, 0.7], [2.3, 0.3, 0.9], [0.6, 1.8, 0.4], [-0.1, 0.2, 2.6]])
    xyz = np.vstack([vertices] + [(vertices[a] + vertices[b])[None, :] / 2 for a, b in EDGE])
    if curved:
        xyz[4:] += np.array(
            [
                [0.02, -0.01, 0.01],
                [-0.01, 0.02, 0.01],
                [0.01, 0.01, -0.02],
                [0.02, 0.01, 0.01],
                [-0.01, -0.01, 0.02],
                [0.01, -0.02, -0.01],
            ]
        )
    a = {
        "normal": np.diag([0.001, -0.002, 0.003]),
        "shear": np.array([[0, 0.004, 0], [0, 0, 0], [0, 0, 0]]),
        "hydrostatic": np.eye(3) * 0.001,
        "nonsymmetric": np.array(
            [[0.001, 0.004, -0.002], [-0.003, -0.002, 0.006], [0.007, 0.001, 0.003]]
        ),
    }[kind]
    u_mm = xyz @ a.T + np.array([0.0003, -0.0007, 0.0002])
    e, nu = 1200.0, 0.3
    # Independent component Hooke law; engineering shear gamma_ij=Aij+Aji.
    expected = np.zeros((3, 3))
    lam = e * nu / ((1 + nu) * (1 - 2 * nu))
    for i in range(3):
        expected[i, i] = e / (1 + nu) * a[i, i] + lam * sum(a[j, j] for j in range(3))
        for j in range(i):
            expected[i, j] = expected[j, i] = e / (2 * (1 + nu)) * (a[i, j] + a[j, i])
    points, weights = quadrature()
    stress, _, _ = recover(xyz[None], u_mm[None] * 1e-3, points, weights, [e], [nu])
    assert np.max(np.abs(stress - expected)) / max(1.0, np.max(np.abs(expected))) < 1e-10
    if kind == "hydrostatic":
        assert np.max(von_mises(stress)) < 1e-10
