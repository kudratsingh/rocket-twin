"""Free-free Euler-Bernoulli beam modes for supplied 1D section profiles.

Small-deflection linear bending only. This utility does not model torsion,
attachments, aerodynamic coupling, fin/servo/control dynamics, or qualification.
References: Weaver, Timoshenko & Young, *Vibration Problems in Engineering*,
5th ed., §5.10 and finite-element chapter (Wiley ISBN 978-0-471-63228-3,
https://www.wiley.com/en-us/Vibration%2BProblems%2Bin%2BEngineering%2C%2B5th%2BEdition-p-9780471632283);
SciPy ``linalg.eigh`` generalized symmetric eigenproblem documentation
(https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.eigh.html).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise

import numpy as np
from numpy.typing import NDArray
from scipy.linalg import eigh

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class PointMass:
    """A concentrated translational mass and rotary inertia at a beam station."""

    station_m: float
    mass_kg: float
    rotary_inertia_kg_m2: float = 0.0


@dataclass(frozen=True)
class BeamModes:
    """Elastic modes and diagnostics; shapes are mass-normalized nodal DOFs."""

    frequencies_hz: FloatArray
    shapes: FloatArray  # rows are [w0, theta0, w1, theta1, ...], columns are modes
    rigid_eigenvalues: FloatArray
    rigid_residuals: FloatArray
    rigid_mass_gram: FloatArray
    modal_mass_gram: FloatArray


def _as_positive_profile(values: Sequence[float], size: int, name: str) -> FloatArray:
    array = np.asarray(values, dtype=np.float64)
    if array.shape != (size,) or not np.all(np.isfinite(array)) or np.any(array <= 0.0):
        raise ValueError(f"{name} must contain {size} finite positive values")
    return array


def _element_matrices(length_m: float, ei: float, mu: float) -> tuple[FloatArray, FloatArray]:
    length2 = length_m * length_m
    stiffness = (
        ei
        / (length_m**3)
        * np.array(
            [
                [12.0, 6.0 * length_m, -12.0, 6.0 * length_m],
                [6.0 * length_m, 4.0 * length2, -6.0 * length_m, 2.0 * length2],
                [-12.0, -6.0 * length_m, 12.0, -6.0 * length_m],
                [6.0 * length_m, 2.0 * length2, -6.0 * length_m, 4.0 * length2],
            ],
            dtype=np.float64,
        )
    )
    mass = (
        mu
        * length_m
        / 420.0
        * np.array(
            [
                [156.0, 22.0 * length_m, 54.0, -13.0 * length_m],
                [22.0 * length_m, 4.0 * length2, 13.0 * length_m, -3.0 * length2],
                [54.0, 13.0 * length_m, 156.0, -22.0 * length_m],
                [-13.0 * length_m, -3.0 * length2, -22.0 * length_m, 4.0 * length2],
            ],
            dtype=np.float64,
        )
    )
    return stiffness, mass


def _shape_functions(xi: float, length_m: float) -> tuple[FloatArray, FloatArray]:
    xi2, xi3 = xi * xi, xi * xi * xi
    shape = np.array(
        [
            1.0 - 3.0 * xi2 + 2.0 * xi3,
            length_m * (xi - 2.0 * xi2 + xi3),
            3.0 * xi2 - 2.0 * xi3,
            length_m * (-xi2 + xi3),
        ],
        dtype=np.float64,
    )
    derivative = np.array(
        [
            (-6.0 * xi + 6.0 * xi2) / length_m,
            1.0 - 4.0 * xi + 3.0 * xi2,
            (6.0 * xi - 6.0 * xi2) / length_m,
            -2.0 * xi + 3.0 * xi2,
        ],
        dtype=np.float64,
    )
    return shape, derivative


def assemble_free_free_beam(
    stations_m: Sequence[float],
    EI_Nm2: Sequence[float],
    mu_kg_m: Sequence[float],
    point_masses: Sequence[PointMass] = (),
) -> tuple[FloatArray, FloatArray]:
    """Assemble global stiffness and consistent mass matrices.

    Each profile value applies to its corresponding interval between stations.
    Point-mass translational/rotary terms are interpolated using the cubic
    Hermite displacement/derivative fields at the supplied physical station.
    """
    x = np.asarray(stations_m, dtype=np.float64)
    if x.ndim != 1 or x.size < 2 or not np.all(np.isfinite(x)) or np.any(np.diff(x) <= 0.0):
        raise ValueError("stations_m must be finite and strictly increasing")
    element_count = x.size - 1
    ei = _as_positive_profile(EI_Nm2, element_count, "EI_Nm2")
    mu = _as_positive_profile(mu_kg_m, element_count, "mu_kg_m")
    dof_count = 2 * x.size
    stiffness = np.zeros((dof_count, dof_count), dtype=np.float64)
    mass = np.zeros_like(stiffness)

    for index, (left, right) in enumerate(pairwise(x)):
        length = float(right - left)
        local_k, local_m = _element_matrices(length, float(ei[index]), float(mu[index]))
        dofs = np.array([2 * index, 2 * index + 1, 2 * index + 2, 2 * index + 3])
        stiffness[np.ix_(dofs, dofs)] += local_k
        mass[np.ix_(dofs, dofs)] += local_m

    for point in point_masses:
        if (
            not np.isfinite(point.station_m)
            or not np.isfinite(point.mass_kg)
            or not np.isfinite(point.rotary_inertia_kg_m2)
        ):
            raise ValueError("point-mass properties must be finite")
        if point.station_m < x[0] or point.station_m > x[-1]:
            raise ValueError("point-mass station lies outside the beam domain")
        if point.mass_kg < 0.0 or point.rotary_inertia_kg_m2 < 0.0:
            raise ValueError("point mass and rotary inertia must be nonnegative")
        if point.mass_kg == 0.0 and point.rotary_inertia_kg_m2 == 0.0:
            raise ValueError("point mass entry must contribute positive inertia")
        element = min(int(np.searchsorted(x, point.station_m, side="right") - 1), element_count - 1)
        element = max(element, 0)
        length = float(x[element + 1] - x[element])
        xi = float((point.station_m - x[element]) / length)
        shape, derivative = _shape_functions(xi, length)
        dofs = np.array([2 * element, 2 * element + 1, 2 * element + 2, 2 * element + 3])
        local_m = point.mass_kg * np.outer(shape, shape)
        local_m += point.rotary_inertia_kg_m2 * np.outer(derivative, derivative)
        mass[np.ix_(dofs, dofs)] += local_m

    return stiffness, mass


def free_free_beam_modes(
    stations_m: Sequence[float],
    EI_Nm2: Sequence[float],
    mu_kg_m: Sequence[float],
    point_masses: Sequence[PointMass] = (),
    elastic_modes: int = 3,
    rigid_tolerance: float = 1e-9,
) -> BeamModes:
    """Solve and return elastic modes after the two free-free rigid modes.

    Shape columns are normalized to unit generalized mass (phi.T M phi = 1);
    their sign is chosen so the largest-magnitude transverse displacement is
    positive. No stiffness or mass regularization is applied.
    """
    if elastic_modes < 1:
        raise ValueError("elastic_modes must be positive")
    if not np.isfinite(rigid_tolerance) or rigid_tolerance <= 0.0:
        raise ValueError("rigid_tolerance must be finite and positive")
    stiffness, mass = assemble_free_free_beam(stations_m, EI_Nm2, mu_kg_m, point_masses)
    symmetry_error_k = np.max(np.abs(stiffness - stiffness.T))
    symmetry_error_m = np.max(np.abs(mass - mass.T))
    if symmetry_error_k > 1e-12 or symmetry_error_m > 1e-12:
        raise ValueError("assembled matrices are not symmetric")
    try:
        np.linalg.cholesky(mass)
    except np.linalg.LinAlgError as exc:
        raise ValueError("assembled mass matrix is not positive definite") from exc

    eigenvalues, eigenvectors = eigh(stiffness, mass, check_finite=True)
    scale = max(float(np.max(np.abs(eigenvalues))), np.finfo(np.float64).tiny)
    zero_limit = rigid_tolerance * scale
    if np.count_nonzero(np.abs(eigenvalues) <= zero_limit) != 2:
        raise ValueError("free-free stiffness must have exactly two rigid-body eigenvalues")
    if np.any(eigenvalues[2:] <= zero_limit):
        raise ValueError("elastic eigenvalues must be positive")

    stations = np.asarray(stations_m, dtype=np.float64)
    rigid_shapes = np.zeros((2 * stations.size, 2), dtype=np.float64)
    rigid_shapes[0::2, 0] = 1.0
    rigid_shapes[0::2, 1] = stations - stations[0]
    rigid_shapes[1::2, 1] = 1.0
    rigid_residuals = np.array(
        [
            np.linalg.norm(stiffness @ rigid_shapes[:, i])
            / (np.linalg.norm(stiffness, ord=2) * np.linalg.norm(rigid_shapes[:, i]))
            for i in range(2)
        ],
        dtype=np.float64,
    )
    if np.any(rigid_residuals > rigid_tolerance):
        raise ValueError("analytical rigid-body modes fail the stiffness residual check")

    rigid_eigenvalues = eigenvalues[:2].copy()
    eigenvalues = eigenvalues[2 : 2 + elastic_modes]
    shapes = eigenvectors[:, 2 : 2 + elastic_modes].copy()
    if eigenvalues.size != elastic_modes:
        raise ValueError(f"requested {elastic_modes} elastic modes, but the mesh has fewer")
    for column in range(shapes.shape[1]):
        transverse = shapes[0::2, column]
        pivot = int(np.argmax(np.abs(transverse)))
        if transverse[pivot] < 0.0:
            shapes[:, column] *= -1.0

    return BeamModes(
        frequencies_hz=np.sqrt(eigenvalues) / (2.0 * np.pi),
        shapes=shapes,
        rigid_eigenvalues=rigid_eigenvalues,
        rigid_residuals=rigid_residuals,
        rigid_mass_gram=rigid_shapes.T @ mass @ rigid_shapes,
        modal_mass_gram=shapes.T @ mass @ shapes,
    )
