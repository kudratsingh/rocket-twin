"""Coupled massless surfaces behind material half walls, for offline analysis.

At a surface i, sum G_im(T_m-T_i) + sum G_ij(T_j-T_i) +
sum G_ib(T_b-T_i) + [C T**4]_i = 0. C is the conservative net-INWARD
diffuse-gray radiosity operator, including sigma, over surfaces and reservoirs.
Material temperatures are ODE states; prescribed reservoirs have no finite heat
capacity. Radiation and gap conduction use the SAME solved surface temperature.
This avoids adding radiation at material-node temperature while air conduction
alone sees the physical half-wall resistance.

References: Bergman et al., Fundamentals of Heat and Mass Transfer, 7th ed.,
chapters 3 (resistance networks) and 13 (diffuse-gray radiation); the primary
radiosity/view-factor references in src.analysis.finite_radiation. Massless
surfaces, linear conductance and isothermal patches are modeling assumptions,
not resolved three-dimensional conduction or a complete-geometry thermal bound.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Array = NDArray[np.float64]


@dataclass(frozen=True)
class SurfaceSolution:
    surface_temperature_k: Array
    material_heat_w: Array
    reservoir_heat_w: Array
    surface_residual_w: Array
    energy_residual_w: float
    iterations: int


@dataclass(frozen=True)
class SurfaceNetwork:
    """Surface groups come first, fixed radiative reservoirs last in C.

    G_material[s,m] links a surface to an ODE material node through the
    appropriate physical half wall. G_gap is symmetric, zero-diagonal air-gap
    conductance BETWEEN surfaces, without half walls. G_boundary[s,b] links
    surfaces conductively to prescribed reservoirs. Use exactly one allocation
    of each wall, contact, gap and radiation path in the calling model.
    """

    material_conductance_w_k: Array
    gap_conductance_w_k: Array
    boundary_conductance_w_k: Array
    radiation_inward_w_k4: Array

    def __post_init__(self) -> None:
        gm = np.asarray(self.material_conductance_w_k, dtype=float)
        gg = np.asarray(self.gap_conductance_w_k, dtype=float)
        gb = np.asarray(self.boundary_conductance_w_k, dtype=float)
        c = np.asarray(self.radiation_inward_w_k4, dtype=float)
        if gm.ndim != 2 or gm.shape[0] == 0 or gm.shape[1] == 0 or gb.ndim != 2:
            raise ValueError("Nonempty surface/material arrays and a 2D boundary array required")
        ns = gm.shape[0]
        nb = gb.shape[1]
        if gb.shape[0] != ns or gg.shape != (ns, ns) or c.shape != (ns + nb, ns + nb):
            raise ValueError("Surface, material, reservoir and radiation dimensions disagree")
        if any(not np.isfinite(a).all() for a in (gm, gg, gb, c)):
            raise ValueError("Conductances must be finite")
        if any(np.any(a < 0) for a in (gm, gg, gb)):
            raise ValueError("Conductances must be nonnegative")
        if not np.allclose(gg, gg.T, atol=1e-12, rtol=1e-10) or np.any(np.diag(gg)):
            raise ValueError("Air-gap conductance must be reciprocal and zero-diagonal")
        scale = max(float(np.max(np.abs(c))), 1e-30)
        off_diagonal = c - np.diag(np.diag(c))
        if (
            np.min(off_diagonal) < -1e-10 * scale
            or np.max(np.diag(c)) > 1e-10 * scale
            or np.max(np.abs(c.sum(axis=0))) > 1e-10 * scale
            or np.max(np.abs(c.sum(axis=1))) > 1e-10 * scale
            or not np.allclose(c, c.T, atol=1e-10 * scale, rtol=1e-10)
        ):
            raise ValueError("Radiation matrix must be reciprocal and conserve enclosure energy")
        # Every connected surface component must ultimately reach a prescribed
        # material or reservoir. An isolated reflective cavity has no unique T.
        edges = (gg > 0) | (off_diagonal[:ns, :ns] > 0)
        connected = (gm.sum(axis=1) + gb.sum(axis=1) > 0) | (off_diagonal[:ns, ns:].sum(axis=1) > 0)
        for _ in range(ns):
            expanded = connected | np.any(edges[:, connected], axis=1)
            if np.array_equal(expanded, connected):
                break
            connected = expanded
        if not connected.all():
            raise ValueError("A surface component has no thermal boundary")
        for name, value in (
            ("material_conductance_w_k", gm),
            ("gap_conductance_w_k", gg),
            ("boundary_conductance_w_k", gb),
            ("radiation_inward_w_k4", c),
        ):
            object.__setattr__(self, name, value.copy())

    def material_temperature_jacobian(self, surface_temperature_k: Array) -> tuple[Array, Array]:
        """Implicit derivatives dQ_material/dT_material and dQ_boundary/dT_material.

        Evaluate at a CONVERGED common-surface solution. Boundary temperatures
        are held fixed. Analytic differentiation avoids an inner solver's finite
        residual being amplified by an ODE solver's tiny Jacobian perturbations.
        This method changes neither the nonlinear surface equations nor their
        convergence tolerance.
        """
        gm, gg, gb, c = (
            self.material_conductance_w_k,
            self.gap_conductance_w_k,
            self.boundary_conductance_w_k,
            self.radiation_inward_w_k4,
        )
        ns = gm.shape[0]
        t = np.asarray(surface_temperature_k, dtype=float)
        if t.shape != (ns,) or np.any(t <= 0) or not np.isfinite(t).all():
            raise ValueError("Converged positive surface temperatures required for derivatives")
        jac = gg - np.diag(gg.sum(axis=1) + gm.sum(axis=1) + gb.sum(axis=1))
        jac += c[:ns, :ns] * (4 * t**3)[None, :]
        response = np.linalg.solve(jac, -gm)
        material_jac = gm.T @ response - np.diag(gm.sum(axis=0))
        boundary_jac = (gb.T + c[ns:, :ns] * (4 * t**3)[None, :]) @ response
        return material_jac, boundary_jac

    def solve(
        self,
        material_temperature_k: Array,
        boundary_temperature_k: Array,
        *,
        initial_surface_k: Array | None = None,
        absolute_tolerance_w: float = 1e-9,
        maximum_iterations: int = 60,
    ) -> SurfaceSolution:
        """Damped Newton solve with analytic Jacobian and positive temperatures.

        Nonconvergence is an error, never a zero heat flux or a passing case.
        The caller must assess discretization, input uncertainty and numerical
        tolerances at the transient level as well as this algebraic residual.
        """
        gm, gg, gb, c = (
            self.material_conductance_w_k,
            self.gap_conductance_w_k,
            self.boundary_conductance_w_k,
            self.radiation_inward_w_k4,
        )
        ns, nm = gm.shape
        nb = gb.shape[1]
        tm = np.asarray(material_temperature_k, dtype=float)
        tb = np.asarray(boundary_temperature_k, dtype=float)
        if tm.shape != (nm,) or tb.shape != (nb,):
            raise ValueError("Temperature vectors do not match material/reservoir nodes")
        if (
            not np.isfinite(tm).all()
            or not np.isfinite(tb).all()
            or np.any(tm <= 0)
            or np.any(tb <= 0)
            or absolute_tolerance_w <= 0
            or maximum_iterations < 1
        ):
            raise ValueError("Absolute temperatures and solver limits must be positive/finite")
        known = np.concatenate((tm, tb))
        t = (
            np.full(ns, float(np.mean(known)))
            if initial_surface_k is None
            else np.asarray(initial_surface_k, dtype=float).copy()
        )
        if t.shape != (ns,) or not np.isfinite(t).all() or np.any(t <= 0):
            raise ValueError("Initial surface temperatures must be positive and correctly shaped")
        conductance = gg - np.diag(gg.sum(axis=1) + gm.sum(axis=1) + gb.sum(axis=1))
        radiation_boundary = c[:ns, ns:] @ tb**4

        def residual(temperature: Array) -> Array:
            # Form actual temperature differences before multiplying large foil
            # conductances, rather than subtracting two large G*T products.
            return np.asarray(
                np.sum(gm * (tm[None, :] - temperature[:, None]), axis=1)
                + np.sum(gg * (temperature[None, :] - temperature[:, None]), axis=1)
                + np.sum(gb * (tb[None, :] - temperature[:, None]), axis=1)
                + c[:ns, :ns] @ temperature**4
                + radiation_boundary,
                dtype=np.float64,
            )

        r = residual(t)
        for iteration in range(maximum_iterations + 1):
            if float(np.max(np.abs(r))) <= absolute_tolerance_w:
                all_temperature = np.concatenate((t, tb))
                radiation = c @ all_temperature**4
                material_heat = np.sum(gm * (t[:, None] - tm[None, :]), axis=0)
                boundary_heat = radiation[ns:] + np.sum(gb * (t[:, None] - tb[None, :]), axis=0)
                return SurfaceSolution(
                    t,
                    material_heat,
                    boundary_heat,
                    r,
                    float(material_heat.sum() + boundary_heat.sum()),
                    iteration,
                )
            jacobian = conductance + c[:ns, :ns] * (4 * t**3)[None, :]
            # Row scaling improves conditioning for highly conductive thin foil
            # alongside low-conductivity liner surfaces without altering equations.
            row_scale = np.maximum(np.max(np.abs(jacobian), axis=1), 1e-30)
            step = np.linalg.solve(jacobian / row_scale[:, None], -r / row_scale)
            fraction = 1.0
            norm = float(np.max(np.abs(r)))
            for _ in range(50):
                trial = t + fraction * step
                if np.all(trial > 0):
                    trial_residual = residual(trial)
                    if float(np.max(np.abs(trial_residual))) < norm:
                        t, r = trial, trial_residual
                        break
                fraction /= 2
            else:
                raise RuntimeError("Common-surface thermal Newton line search did not converge")
        raise RuntimeError(f"Common-surface solve exceeded {maximum_iterations} iterations")
