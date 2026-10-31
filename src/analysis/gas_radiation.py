"""Offline Robin gas/radiation coupling at one common surface field.

A verified linear gas FEM reduction gives area-mean surface temperatures
s=G theta+R q and inward reservoir heat H=-K theta+J q. Diffuse-gray
radiation supplies q=P.T C ((P s+E b)**4), with C the net-inward
conservative radiative operator. Newton solves s-G theta-R q(s)=0.
Gas and radiation therefore see the same mean surface temperature; half-wall
resistances remain in the Robin FEM, never a duplicate parallel gap route.

The area-mean/groupwise-uniform radiation projection is EXPLICITLY an
approximation. Radiation from mean(T)**4 differs from mean(T**4) where the
actual surface field varies. Reconstructed P1 fields diagnose this difference;
they do not turn gas mesh nodes into measured or qualified solid hot spots.
No isothermal grouping follows merely from a CAD part ID or a shared node.
Opening gas temperature and opening radiative brightness are separate inputs.

References: project Robin FEM derivation (MFEM boundary mass integrators) in
robin_gas.py; Bergman et al., Fundamentals of Heat and Mass Transfer, 7th ed.,
chapters 3 and 13; finite_radiation.py contains the cited radiosity derivation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from src.analysis.recorded_gas import GasResponse

Array = NDArray[np.float64]


@dataclass(frozen=True)
class GasRadiationSolution:
    surface_area_mean_k: Array
    heat_into_gas_surface_w: Array
    heat_into_material_and_gas_reservoir_w: Array
    heat_into_radiative_brightness_reservoir_w: Array
    state_heat_jacobian_w_k: Array
    fixed_brightness_heat_jacobian_w_k: Array
    mean_response_jacobian_k_k: Array
    surface_residual_k: float
    enclosure_energy_residual_w: float
    iterations: int
    reconstruction: dict[str, Any] | None


@dataclass(frozen=True)
class GasRadiationNetwork:
    """Each radiative node is exactly one gas group OR one brightness input.

    ``radiation_gas_group_columns`` contains gas-group columns or -1, while
    ``radiation_brightness_columns`` contains brightness columns or -1. Each
    radiative node must have one owner. A black opening is brightness-owned;
    its radiative heat belongs to that reservoir, not an extra gas heat load.
    All unused gas groups receive zero *radiative* load; their physical gas
    boundary classifications are still required by factor_robin_gas.
    """

    gas: GasResponse
    radiation_inward_w_k4: Array
    radiation_gas_group_columns: tuple[int, ...]
    radiation_brightness_columns: tuple[int, ...]
    brightness_ids: tuple[str, ...]
    projection_basis: str

    def __post_init__(self) -> None:
        c = np.asarray(self.radiation_inward_w_k4, dtype=float)
        ng = len(self.gas.group_ids)
        nr = len(self.radiation_gas_group_columns)
        if (
            nr < 1
            or c.shape != (nr, nr)
            or len(self.radiation_brightness_columns) != nr
            or not self.projection_basis.strip()
            or len(set(self.brightness_ids)) != len(self.brightness_ids)
        ):
            raise ValueError("Complete radiation owners, matrix and projection basis required")
        for g, b in zip(
            self.radiation_gas_group_columns, self.radiation_brightness_columns, strict=True
        ):
            if not ((0 <= g < ng and b == -1) or (g == -1 and 0 <= b < len(self.brightness_ids))):
                raise ValueError("Every radiation node needs exactly one valid physical owner")
        # Multiple patches may share a temperature group before condensation,
        # but this reduced operator must already be in unique group order.
        owned = [g for g in self.radiation_gas_group_columns if g >= 0]
        if len(set(owned)) != len(owned):
            raise ValueError("Condense duplicate gas temperature groups before coupling")
        if not np.isfinite(c).all():
            raise ValueError("Finite radiation matrix required")
        scale = max(float(np.abs(c).max()), 1e-30)
        off = c - np.diag(np.diag(c))
        if (
            np.min(off) < -1e-10 * scale
            or np.max(np.diag(c)) > 1e-10 * scale
            or np.max(np.abs(c.sum(axis=0))) > 1e-9 * scale
            or np.max(np.abs(c.sum(axis=1))) > 1e-9 * scale
            or not np.allclose(c, c.T, atol=1e-10 * scale, rtol=1e-10)
        ):
            raise ValueError("Reciprocal conservative net-inward radiation matrix required")
        object.__setattr__(self, "radiation_inward_w_k4", c.copy())

    def _selectors(self) -> tuple[Array, Array]:
        nr = len(self.radiation_gas_group_columns)
        p = np.zeros((nr, len(self.gas.group_ids)))
        e = np.zeros((nr, len(self.brightness_ids)))
        for i, (g, b) in enumerate(
            zip(self.radiation_gas_group_columns, self.radiation_brightness_columns, strict=True)
        ):
            if g >= 0:
                p[i, g] = 1
            else:
                e[i, b] = 1
        return p, e

    def solve(
        self,
        bulk_temperature_k: Array,
        prescribed_gas_temperature_k: Array,
        radiative_brightness_temperature_k: Array,
        *,
        initial_surface_k: Array | None = None,
        absolute_tolerance_k: float = 1e-8,
        maximum_iterations: int = 60,
        reconstruct: bool = False,
    ) -> GasRadiationSolution:
        """Damped Newton with exact reduced Jacobians; never clip raw FEM maps.

        The returned state derivative holds prescribed gas temperatures and
        radiative brightness fixed. It is suitable for an ODE material heat
        Jacobian only under this declared radiation projection approximation.
        A missing boundary/halfwall must fail upstream, never become insulation.
        """
        bulk = np.asarray(bulk_temperature_k, dtype=float)
        prescribed = np.asarray(prescribed_gas_temperature_k, dtype=float)
        brightness = np.asarray(radiative_brightness_temperature_k, dtype=float)
        for value, size in (
            (bulk, len(self.gas.bulk_ids)),
            (prescribed, len(self.gas.prescribed_ids)),
            (brightness, len(self.brightness_ids)),
        ):
            if value.shape != (size,) or not np.isfinite(value).all() or np.any(value <= 0):
                raise ValueError("Positive finite absolute temperatures in reported order required")
        if absolute_tolerance_k <= 0 or maximum_iterations < 1:
            raise ValueError("Positive nonlinear tolerance and iteration limit required")
        theta = np.r_[bulk, prescribed]
        g = self.gas.mean_by_reservoir_temperature
        r = self.gas.mean_by_group_neumann_k_w
        c = self.radiation_inward_w_k4
        p, e = self._selectors()
        baseline = g @ theta
        s = baseline.copy() if initial_surface_k is None else np.asarray(initial_surface_k).copy()
        if s.shape != baseline.shape or not np.isfinite(s).all() or np.any(s <= 0):
            raise ValueError("Positive finite initial surface means required")

        def residual(surface: Array) -> tuple[Array, Array, Array, Array]:
            tr = p @ surface + e @ brightness
            # A common reference removes isothermal roundoff without changing C.
            fourth = tr**4
            qr = c @ (fourth - fourth[0])
            q = p.T @ qr
            return surface - baseline - r @ q, q, qr, tr

        for iteration in range(maximum_iterations + 1):
            error, q, qr, tr = residual(s)
            norm = float(np.abs(error).max())
            dq_ds = p.T @ (c * (4 * tr**3)[None, :]) @ p
            jac = np.eye(len(s)) - r @ dq_ds
            if norm <= absolute_tolerance_k:
                response = np.linalg.solve(jac, g)
                heat = (
                    -self.gas.reservoir_conductance_raw_w_k @ theta
                    + self.gas.reservoir_heat_by_group_neumann @ q
                )
                qbright = e.T @ qr
                heat_jac = (
                    -self.gas.reservoir_conductance_raw_w_k
                    + self.gas.reservoir_heat_by_group_neumann @ dq_ds @ response
                )
                db = p.T @ (c * (4 * tr**3)[None, :]) @ e
                ds_db = np.linalg.solve(jac, r @ db)
                heat_db = self.gas.reservoir_heat_by_group_neumann @ (dq_ds @ ds_db + db)
                diagnostic = None
                if reconstruct:
                    diagnostic = self.gas.evaluate(bulk, prescribed, q)
                    actual_mean = np.asarray(diagnostic["area_mean_temperature_k"])
                    mean4 = np.asarray(diagnostic["area_mean_fourth_power_k4"])
                    diagnostic["nonlinear_mean_reconstruction_difference_k"] = float(
                        np.max(np.abs(actual_mean - s))
                    )
                    diagnostic["radiation_projection_mean_fourth_power_difference_k4"] = (
                        mean4 - s**4
                    ).tolist()
                    # This is a *diagnostic change to integrated radiation*, not
                    # a spatial radiosity solution or another accepted heat load.
                    fourth = tr**4
                    for row, group in enumerate(self.radiation_gas_group_columns):
                        if group >= 0:
                            fourth[row] = mean4[group]
                    diagnostic["diagnostic_mean_T4_radiation_heat_change_w"] = (
                        c @ (fourth - fourth[0]) - qr
                    ).tolist()
                    diagnostic["radiation_projection_basis"] = self.projection_basis
                    diagnostic["resolved_spatial_radiosity_acceptance"] = False
                nb = len(bulk)
                return GasRadiationSolution(
                    s,
                    q,
                    heat,
                    qbright,
                    heat_jac[:, :nb],
                    heat_db,
                    response[:, :nb],
                    norm,
                    float(heat.sum() + qbright.sum()),
                    iteration,
                    diagnostic,
                )
            direction = np.linalg.solve(jac, -error)
            fraction = 1.0
            for _ in range(50):
                trial = s + fraction * direction
                if np.all(trial > 0) and float(np.abs(residual(trial)[0]).max()) < norm:
                    s = trial
                    break
                fraction /= 2
            else:
                raise RuntimeError("Gas/radiation nonlinear line search did not converge")
        raise RuntimeError("Gas/radiation nonlinear iteration limit exceeded")
