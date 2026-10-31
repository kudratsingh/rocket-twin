"""Finite opaque coaxial geometry and diffuse-gray radiation DIAGNOSTICS.

The diffuse view factor is F_ij = (1/A_i) integral_i integral_j
V cos(theta_i) cos(theta_j)/(pi*s**2) dA_j dA_i. Uniform area points and
cosine-weighted hemisphere directions therefore estimate F by first-hit counts.
Rotational symmetry permits the emitting point's azimuth to be fixed at zero;
directions retain both transverse components. Rays terminate at the FIRST solid
boundary. They are never deflected, transmitted, or continued through a shield.

Radiosity: J = eps*sigma*T**4 + (1-eps)*F@J; Q_out=A*(J-F@J).
Reciprocity A_i F_ij=A_j F_ji and closed-enclosure sum_j F_ij=1 are checked
on raw samples. A disclosed symmetric diagonal balancing of sampled exchange
areas supplies a conservative reciprocal matrix for the radiosity diagnostic;
it creates no new visible pairs. Raw sampling errors remain in the output.

Primary references: Hamilton & Morgan, NACA TN 2836 (1952), configurations A-5
and A-7/A-8, https://ntrs.nasa.gov/citations/19930083529 ; COMSOL 6.3, Theory
for Surface-to-Surface Radiation, View Factor Evaluation and Radiosity Method,
https://doc.comsol.com/6.3/doc/com.comsol.help.heat/heat_ug_theory.07.053.html
and ...07.052.html; Argonne SAM Theory Manual (2025), equations 3.18--3.23,
https://publications.anl.gov/anlpubs/2025/05/196116.pdf .
These equations assume opaque, diffuse-gray, isothermal patches and a transparent
nonparticipating medium. This is not conduction, gas circulation, a transient
temperature solution, exact noncoaxial CAD, or physical thermal qualification.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import pairwise
from typing import Any

import numpy as np
from scipy.stats import beta

SIGMA = 5.670374419e-8
GEOMETRY_TOL_M = 1e-11


@dataclass(frozen=True)
class AnnularSolid:
    part_id: str
    inner_radius_m: float
    outer_radius_m: float
    start_m: float
    end_m: float
    fore_face_unknown: bool = False


@dataclass(frozen=True)
class Patch:
    """Cylinder: coordinate=radius, lo/hi=z; annulus: coordinate=z, lo/hi=r.

    Normal points from material into the modeled void. Apertures are explicit
    black boundary surfaces with normals pointing into the truncated enclosure.
    """

    part_id: str
    kind: str
    coordinate_m: float
    lo_m: float
    hi_m: float
    normal_sign: int
    face: str
    unknown_boundary: bool = False

    @property
    def area_m2(self) -> float:
        if self.kind == "cylinder":
            return 2 * np.pi * self.coordinate_m * (self.hi_m - self.lo_m)
        return np.pi * (self.hi_m**2 - self.lo_m**2)

    def record(self) -> dict[str, Any]:
        return {**asdict(self), "area_m2": self.area_m2}


def subtract_intervals(
    lo: float, hi: float, cuts: list[tuple[float, float]]
) -> list[tuple[float, float]]:
    intervals = [(lo, hi)]
    for a, b in sorted(cuts):
        remaining = []
        for x, y in intervals:
            if b <= x + GEOMETRY_TOL_M or a >= y - GEOMETRY_TOL_M:
                remaining.append((x, y))
            else:
                if a > x + GEOMETRY_TOL_M:
                    remaining.append((x, a))
                if b < y - GEOMETRY_TOL_M:
                    remaining.append((b, y))
        intervals = remaining
    return intervals


def enclosure_patches(
    solids: list[AnnularSolid],
    start_m: float,
    end_m: float,
    shell_inner_radius_m: float,
    max_axial_patch_m: float,
) -> list[Patch]:
    """Actual finite annuli, union contact removal, shell and black axial openings.

    Solid overlap is rejected. Coincident mica/foil contact surfaces are removed,
    so a contacting pair cannot exchange radiation or leak rays through a wall.
    The shell is the enclosing cylinder, not an unbounded ambient sink.
    """
    if not (start_m < end_m and shell_inner_radius_m > 0 and max_axial_patch_m > 0):
        raise ValueError("Invalid enclosure dimensions")
    for i, solid in enumerate(solids):
        if not (
            0 <= solid.inner_radius_m < solid.outer_radius_m <= shell_inner_radius_m
            and start_m - GEOMETRY_TOL_M <= solid.start_m < solid.end_m <= end_m + GEOMETRY_TOL_M
        ):
            raise ValueError(f"Invalid/outside annular solid: {solid}")
        for other in solids[:i]:
            if (
                min(solid.outer_radius_m, other.outer_radius_m)
                - max(solid.inner_radius_m, other.inner_radius_m)
                > GEOMETRY_TOL_M
                and min(solid.end_m, other.end_m) - max(solid.start_m, other.start_m)
                > GEOMETRY_TOL_M
            ):
                raise ValueError(f"Overlapping solids: {solid.part_id}/{other.part_id}")
    patches: list[Patch] = []

    def add_cylinder(part: str, r: float, a: float, b: float, sign: int, face: str) -> None:
        n = int(np.ceil((b - a) / max_axial_patch_m))
        cuts = np.linspace(a, b, n + 1)
        patches.extend(
            Patch(part, "cylinder", r, float(x), float(y), sign, face) for x, y in pairwise(cuts)
        )

    for solid in solids:
        for r, sign, face in (
            (solid.inner_radius_m, -1, "inner_cylinder"),
            (solid.outer_radius_m, 1, "outer_cylinder"),
        ):
            if r == 0 or (sign > 0 and abs(r - shell_inner_radius_m) < GEOMETRY_TOL_M):
                continue
            contacts = [
                (other.start_m, other.end_m)
                for other in solids
                if other is not solid
                and (
                    (sign > 0 and abs(other.inner_radius_m - r) < GEOMETRY_TOL_M)
                    or (sign < 0 and abs(other.outer_radius_m - r) < GEOMETRY_TOL_M)
                )
            ]
            for a, b in subtract_intervals(solid.start_m, solid.end_m, contacts):
                add_cylinder(solid.part_id, r, a, b, sign, face)
        for z, sign, face in ((solid.start_m, -1, "fore_face"), (solid.end_m, 1, "aft_face")):
            if abs(z - start_m) < GEOMETRY_TOL_M or abs(z - end_m) < GEOMETRY_TOL_M:
                continue
            contacts = [
                (other.inner_radius_m, other.outer_radius_m)
                for other in solids
                if other is not solid
                and (
                    (sign > 0 and abs(other.start_m - z) < GEOMETRY_TOL_M)
                    or (sign < 0 and abs(other.end_m - z) < GEOMETRY_TOL_M)
                )
            ]
            for a, b in subtract_intervals(solid.inner_radius_m, solid.outer_radius_m, contacts):
                unknown = solid.fore_face_unknown and face == "fore_face"
                part_id = "unknown_motor_fore_face" if unknown else solid.part_id
                patches.append(Patch(part_id, "annulus", z, a, b, sign, face, unknown))
    shell_contacts = [
        (solid.start_m, solid.end_m)
        for solid in solids
        if abs(solid.outer_radius_m - shell_inner_radius_m) < GEOMETRY_TOL_M
    ]
    for a, b in subtract_intervals(start_m, end_m, shell_contacts):
        add_cylinder("aft_shell", shell_inner_radius_m, a, b, -1, "inner_cylinder")
    for z, sign, name in ((start_m, 1, "fore_aperture"), (end_m, -1, "aft_aperture")):
        occupied = [
            (solid.inner_radius_m, solid.outer_radius_m)
            for solid in solids
            if solid.start_m - GEOMETRY_TOL_M <= z <= solid.end_m + GEOMETRY_TOL_M
        ]
        for a, b in subtract_intervals(0.0, shell_inner_radius_m, occupied):
            patches.append(Patch(name, "annulus", z, a, b, sign, "black_aperture", True))
    return patches


class CoaxialTracer:
    """Vectorized analytic intersections, grouped by cylinder radius/plane station."""

    def __init__(self, patches: list[Patch]):
        self.patches = patches
        groups: dict[tuple[str, float], list[int]] = {}
        for i, p in enumerate(patches):
            groups.setdefault((p.kind, p.coordinate_m), []).append(i)
        self.groups = []
        for (kind, coord), ids in groups.items():
            ids = sorted(ids, key=lambda i: patches[i].lo_m)
            lo = np.array([patches[i].lo_m for i in ids])
            hi = np.array([patches[i].hi_m for i in ids])
            if np.any(lo[1:] < hi[:-1] - GEOMETRY_TOL_M):
                raise ValueError("Overlapping radiating patches on the same boundary")
            self.groups.append(
                (
                    kind,
                    coord,
                    np.array(ids),
                    lo,
                    hi,
                    np.array([patches[i].normal_sign for i in ids]),
                )
            )

    def first_hit(self, points: Any, directions: Any) -> np.ndarray:
        points = np.asarray(points, dtype=float)
        directions = np.asarray(directions, dtype=float)
        count = len(points)
        if points.shape != directions.shape or points.shape != (count, 3):
            raise ValueError("Rays require matching N by 3 origins/directions")
        nearest = np.full(count, np.inf)
        hit = np.full(count, -1, dtype=int)
        transverse = directions[:, 0] ** 2 + directions[:, 1] ** 2
        b = points[:, 0] * directions[:, 0] + points[:, 1] * directions[:, 1]
        origin_r2 = points[:, 0] ** 2 + points[:, 1] ** 2
        for kind, coord, ids, lo, hi, signs in self.groups:
            if kind == "cylinder":
                discriminant = b**2 - transverse * (origin_r2 - coord**2)
                root = np.sqrt(np.maximum(discriminant, 0))
                safe_transverse = np.where(transverse > 1e-24, transverse, 1.0)
                roots = [(-b - root) / safe_transverse, (-b + root) / safe_transverse]
            else:
                safe_dz = np.where(abs(directions[:, 2]) > 1e-15, directions[:, 2], 1.0)
                roots = [(coord - points[:, 2]) / safe_dz]
            for distance in roots:
                if kind == "cylinder":
                    position = points[:, 2] + distance * directions[:, 2]
                    derivative = (b + distance * transverse) / coord
                    valid = (discriminant >= 0) & (transverse > 1e-24)
                else:
                    x = points[:, 0] + distance * directions[:, 0]
                    y = points[:, 1] + distance * directions[:, 1]
                    position = np.hypot(x, y)
                    derivative = directions[:, 2]
                    valid = abs(directions[:, 2]) > 1e-15
                index = np.searchsorted(lo, position, side="right") - 1
                safe_index = np.maximum(index, 0)
                valid &= (
                    (index >= 0)
                    & (position <= hi[safe_index] + GEOMETRY_TOL_M)
                    & (distance > GEOMETRY_TOL_M)
                    & (distance < nearest)
                    & (signs[safe_index] * derivative < -1e-14)
                )
                nearest[valid] = distance[valid]
                hit[valid] = ids[safe_index[valid]]
        return hit


def sample_rays(patch: Patch, count: int, rng: np.random.Generator) -> tuple[Any, Any]:
    """Uniform area and Lambert cosine hemisphere, analytically axisymmetric."""
    samples = rng.random((count, 3))
    points = np.zeros((count, 3))
    mu = np.sqrt(samples[:, 1])
    tangent = np.sqrt(1 - samples[:, 1])
    phi = 2 * np.pi * samples[:, 2]
    if patch.kind == "cylinder":
        points[:, 0] = patch.coordinate_m
        points[:, 2] = patch.lo_m + (patch.hi_m - patch.lo_m) * samples[:, 0]
        direction = np.column_stack(
            (patch.normal_sign * mu, tangent * np.cos(phi), tangent * np.sin(phi))
        )
    else:
        points[:, 0] = np.sqrt(patch.lo_m**2 + (patch.hi_m**2 - patch.lo_m**2) * samples[:, 0])
        points[:, 2] = patch.coordinate_m
        direction = np.column_stack(
            (tangent * np.cos(phi), tangent * np.sin(phi), patch.normal_sign * mu)
        )
    return points, direction


def sample_view_factors(
    patches: list[Patch],
    ray_budget: int,
    seed: int,
    chunk_size: int = 4096,
    minimum_per_patch: int = 64,
) -> dict[str, Any]:
    """Area-proportional stratified independent MC, with a strict stated ray count."""
    if ray_budget < minimum_per_patch * len(patches) or chunk_size < 1:
        raise ValueError("Ray budget below patch minimum or invalid chunk size")
    areas = np.array([p.area_m2 for p in patches])
    remaining = ray_budget - minimum_per_patch * len(patches)
    counts = minimum_per_patch + np.floor(remaining * areas / sum(areas)).astype(int)
    counts[np.argmax(areas)] += ray_budget - int(sum(counts))
    tracer = CoaxialTracer(patches)
    rng = np.random.default_rng(seed)
    hits = np.zeros((len(patches), len(patches)), dtype=np.int64)
    escapes = np.zeros(len(patches), dtype=int)
    for source, (patch, n) in enumerate(zip(patches, counts, strict=True)):
        for first in range(0, int(n), chunk_size):
            origins, directions = sample_rays(patch, min(chunk_size, int(n) - first), rng)
            target = tracer.first_hit(origins, directions)
            escapes[source] += int(np.count_nonzero(target < 0))
            hits[source] += np.bincount(target[target >= 0], minlength=len(patches))
    view = hits / counts[:, None]
    exchange = areas[:, None] * view
    variance = areas[:, None] ** 2 * view * (1 - view) / counts[:, None]
    reciprocal_se = np.sqrt(variance + variance.T)
    residual = abs(exchange - exchange.T)
    zscore = np.divide(
        residual, reciprocal_se, out=np.zeros_like(residual), where=reciprocal_se > 0
    )
    # Exact binomial Clopper--Pearson intervals with a union bound over all
    # directed pairs. In particular, zero observed hits do NOT mean zero error.
    # Plug-in Gaussian errors can be arbitrarily misleading for tiny foil rims.
    tail = 0.01 / (2 * len(patches) ** 2)
    lower = beta.ppf(tail, np.maximum(hits, 1), counts[:, None] - hits + 1)
    upper = beta.ppf(1 - tail, hits + 1, np.maximum(counts[:, None] - hits, 1))
    lower[hits == 0] = 0.0
    upper[hits == counts[:, None]] = 1.0
    lower_exchange = areas[:, None] * lower
    upper_exchange = areas[:, None] * upper
    reciprocity_interval_gap = np.maximum(lower_exchange - upper_exchange.T, 0.0)
    return {
        "raw_view_factors": view,
        "counts": counts,
        "hits": hits,
        "areas_m2": areas,
        "sampling": {
            "seed": seed,
            "ray_count": int(sum(counts)),
            "chunk_size": chunk_size,
            "minimum_rays_per_patch": int(min(counts)),
            "maximum_rays_per_patch": int(max(counts)),
            "escaped_rays": int(sum(escapes)),
            "raw_max_row_sum_error": float(np.max(abs(view.sum(axis=1) - 1))),
            "raw_max_reciprocity_residual_m2": float(residual.max()),
            "raw_l1_reciprocity_residual_fraction": float(sum(sum(residual)) / sum(areas)),
            "raw_max_reciprocity_plugin_standard_errors_rare_hits_unreliable": float(zscore.max()),
            "raw_reciprocity_simultaneous_99pct_exact_binomial_intervals_overlap": bool(
                np.max(reciprocity_interval_gap) == 0
            ),
            "raw_reciprocity_max_interval_gap_m2": float(np.max(reciprocity_interval_gap)),
            "uncertainty_scope": "independent ray sampling only; no material, missing geometry or prescribed-temperature uncertainty",
        },
    }


def reciprocal_enclosure(view: Any, areas: Any) -> tuple[Any, dict[str, Any]]:
    """Balance symmetric sampled exchange areas; retain every sampled zero pair.

    Symmetric diagonal matrix equilibration H'=diag(d) H diag(d), row sums A.
    This is an explicitly reported MC reconciliation, not a geometry correction.
    Raw closure/reciprocity must be inspected separately and convergence checked.
    """
    view = np.asarray(view, dtype=float)
    areas = np.asarray(areas, dtype=float)
    if np.max(abs(view.sum(axis=1) - 1)) > 1e-10 or np.any(view < 0):
        raise ValueError("Cannot reconcile escaped rays or an incomplete enclosure")
    initial = areas[:, None] * view
    symmetric = (initial + initial.T) / 2
    scale = np.ones(len(areas))
    for iteration in range(10000):
        row = scale * (symmetric @ scale)
        if np.max(abs(row / areas - 1)) < 1e-12:
            break
        scale *= np.sqrt(areas / row)
    else:
        raise RuntimeError("Symmetric enclosure balancing did not converge")
    exchange = scale[:, None] * symmetric * scale[None, :]
    balanced = exchange / areas[:, None]
    return balanced, {
        "method": "symmetric diagonal equilibration of mean reciprocal sampled exchange areas; no new visibility pairs",
        "iterations": iteration,
        "maximum_row_l1_adjustment": float(np.max(sum(abs(balanced - view).T))),
        "maximum_exchange_adjustment_m2": float(np.max(abs(exchange - initial))),
        "max_row_sum_error": float(np.max(abs(balanced.sum(axis=1) - 1))),
        "max_reciprocity_error_m2": float(np.max(abs(exchange - exchange.T))),
    }


def radiosity(view: Any, areas: Any, temperatures_k: Any, emissivities: Any) -> dict[str, Any]:
    """Opaque diffuse-gray enclosure, positive heat leaves a material/boundary."""
    view = np.asarray(view, dtype=float)
    areas = np.asarray(areas, dtype=float)
    temperature = np.asarray(temperatures_k, dtype=float)
    emissivity = np.asarray(emissivities, dtype=float)
    if (
        view.shape != (len(areas), len(areas))
        or temperature.shape != areas.shape
        or emissivity.shape != areas.shape
        or not np.isfinite(temperature).all()
        or np.any(temperature <= 0)
        or np.any(emissivity <= 0)
        or np.any(emissivity > 1)
    ):
        raise ValueError("Finite positive temperatures and emissivities required for every patch")
    j = np.linalg.solve(
        np.eye(len(areas)) - (1 - emissivity[:, None]) * view, emissivity * SIGMA * temperature**4
    )
    irradiation = view @ j
    q = areas * (j - irradiation)
    exchange = areas[:, None] * view
    pair = exchange * (j[:, None] - j[None, :])
    return {
        "radiosity_w_m2": j,
        "net_outward_w": q,
        "pair_net_outward_w": pair,
        "energy_residual_w": float(sum(q)),
        "max_equation_residual_w_m2": float(
            np.max(abs(j - emissivity * SIGMA * temperature**4 - (1 - emissivity) * irradiation))
        ),
    }


@dataclass(frozen=True)
class CondensedRadiation:
    """A fixed-geometry/emissivity radiative exchange operator in W/K**4.

    Each patch belongs to one supplied temperature group. Eliminating patch
    radiosities gives K=B.T diag(A)(I-F) [I-diag(1-eps)F]^-1 diag(eps)B*sigma.
    For a reciprocal closed enclosure K is a symmetric graph Laplacian. Its
    off-diagonal conductances C_ij=-K_ij give Q_into,i=sum_j C_ij(T_j**4-T_i**4).
    The algebra works for material groups OR separately coupled surface groups.
    Equating a material temperature to its physical surface temperature is an
    additional approximation, not a property of this condensation.
    """

    node_names: tuple[str, ...]
    conductance_w_k4: Any
    patch_node_index: Any
    radiosity_response_w_m2_k4: Any
    checks: dict[str, Any]

    @property
    def inward_operator_w_k4(self) -> np.ndarray:
        """Signed C: net inward W = C @ T_K**4, including sigma and reservoirs."""
        conductance = np.asarray(self.conductance_w_k4, dtype=float)
        return conductance - np.diag(conductance.sum(axis=1))

    def heat_rates(self, temperatures_k: Any) -> np.ndarray:
        temperatures = np.asarray(temperatures_k, dtype=float)
        if (
            temperatures.shape != (len(self.node_names),)
            or not np.isfinite(temperatures).all()
            or np.any(temperatures <= 0)
        ):
            raise ValueError("Every condensed temperature group requires a finite positive K value")
        fourth_power = temperatures**4
        # Subtracting a common blackbody level improves cancellation and makes
        # exact isothermal input give exactly zero heat in floating point.
        shifted = fourth_power - fourth_power[0]
        conductance = self.conductance_w_k4
        return np.asarray(conductance @ shifted - conductance.sum(axis=1) * shifted)

    def pair_fluxes(self, temperatures_k: Any) -> list[tuple[str, str, float]]:
        temperatures = np.asarray(temperatures_k, dtype=float)
        self.heat_rates(temperatures)  # Validate the complete input, including reservoirs.
        fourth_power = temperatures**4
        return [
            (
                self.node_names[i],
                self.node_names[j],
                float(self.conductance_w_k4[i, j] * (fourth_power[i] - fourth_power[j])),
            )
            for i, j in zip(*np.triu_indices(len(self.node_names), 1), strict=True)
            if self.conductance_w_k4[i, j] > 0
        ]


def condense_radiosity(
    view: Any, areas: Any, emissivities: Any, patch_temperature_group_names: list[str]
) -> CondensedRadiation:
    """Eliminate patch radiosities once; require a checked reciprocal enclosure.

    Only floating-point noise is symmetrized/clipped in the condensed operator.
    Sampling reconciliation, if required, must happen separately and be reported.
    Black end surfaces remain explicit groups with emissivity one, not hidden sinks.
    """
    view = np.asarray(view, dtype=float)
    areas = np.asarray(areas, dtype=float)
    emissivity = np.asarray(emissivities, dtype=float)
    count = len(areas)
    if (
        view.shape != (count, count)
        or emissivity.shape != areas.shape
        or len(patch_temperature_group_names) != count
        or not np.isfinite(view).all()
        or not np.isfinite(areas).all()
        or not np.isfinite(emissivity).all()
        or np.any(areas <= 0)
        or np.any(view < 0)
        or np.any(emissivity <= 0)
        or np.any(emissivity > 1)
        or any(not name for name in patch_temperature_group_names)
    ):
        raise ValueError("Complete finite enclosure, areas, emissivities and patch groups required")
    closure = float(np.max(abs(view.sum(axis=1) - 1)))
    exchange = areas[:, None] * view
    reciprocity = float(np.max(abs(exchange - exchange.T)))
    if closure > 1e-9 or reciprocity > 1e-9 * float(max(areas)):
        raise ValueError("Condensation requires a closed reciprocal view-factor matrix")
    names = tuple(dict.fromkeys(patch_temperature_group_names))
    name_index = {name: i for i, name in enumerate(names)}
    patch_index = np.array([name_index[name] for name in patch_temperature_group_names])
    grouping = np.zeros((count, len(names)))
    grouping[np.arange(count), patch_index] = 1.0
    response = np.linalg.solve(
        np.eye(count) - (1 - emissivity[:, None]) * view,
        emissivity[:, None] * grouping * SIGMA,
    )
    raw_k = grouping.T @ (areas[:, None] * (response - view @ response))
    conductance = -(raw_k + raw_k.T) / 2
    np.fill_diagonal(conductance, 0.0)
    scale = float(np.max(abs(raw_k)))
    if float(np.min(conductance)) < -max(1e-24, scale * 1e-9):
        raise ValueError("Condensed radiation has a nonphysical negative exchange conductance")
    conductance = np.maximum(conductance, 0.0)
    reconciled_k = np.diag(conductance.sum(axis=1)) - conductance
    return CondensedRadiation(
        names,
        conductance,
        patch_index,
        response,
        {
            "patch_count": count,
            "temperature_group_count": len(names),
            "view_factor_max_closure_error": closure,
            "view_factor_max_reciprocity_error_m2": reciprocity,
            "raw_condensed_max_asymmetry_w_k4": float(np.max(abs(raw_k - raw_k.T))),
            "raw_condensed_max_row_sum_w_k4": float(np.max(abs(raw_k.sum(axis=1)))),
            "roundoff_laplacian_max_adjustment_w_k4": float(np.max(abs(reconciled_k - raw_k))),
            "scope": "exact algebraic condensation for fixed diffuse-gray geometry/emissivities and supplied patch temperature grouping; no common-surface conduction coupling implied",
        },
    )


class MaterialRadiationAdapter:
    """Explicitly DIAGNOSTIC material-temperature mapping for the recorded RHS.

    This interface does not supply a coupled half-wall surface solve. Inserting
    it beside independent air-only gap fluxes would be a different thermal model,
    not an accepted replacement for shared-surface conduction plus radiation.
    """

    RESERVOIRS = ("motor_case_boundary", "fore_end_reservoir", "aft_end_reservoir")

    def __init__(
        self,
        operator: CondensedRadiation,
        thermal_node_names: list[str],
        end_boundary_modes: dict[str, str],
        provenance: dict[str, Any],
    ):
        self.operator = operator
        self.thermal_node_names = tuple(thermal_node_names)
        self.end_boundary_modes = dict(end_boundary_modes)
        self.provenance = dict(provenance)
        if len(set(thermal_node_names)) != len(thermal_node_names):
            raise ValueError("Thermal node names must be unique")
        if set(end_boundary_modes) != set(self.RESERVOIRS[1:]) or any(
            mode not in {"ambient", "case"} for mode in end_boundary_modes.values()
        ):
            raise ValueError(
                "Both missing ends require explicit ambient/case reservoir assumptions"
            )
        index = {name: i for i, name in enumerate(thermal_node_names)}
        self.node_to_ode: list[int | None] = []
        for name in operator.node_names:
            if name in self.RESERVOIRS:
                self.node_to_ode.append(None)
            elif name in index:
                self.node_to_ode.append(index[name])
            else:
                raise ValueError(f"Missing thermal temperature group: {name}")

    def validate_nodes(self, node_names: list[str]) -> None:
        if tuple(node_names) != self.thermal_node_names:
            raise ValueError("Finite-radiation thermal node identities/order do not match")

    def group_temperatures(
        self, temperature_k: Any, *, case_temperature_k: float, ambient_temperature_k: float
    ) -> np.ndarray:
        temperature = np.asarray(temperature_k, dtype=float)
        if temperature.shape != (len(self.thermal_node_names),):
            raise ValueError("Finite-radiation mapping requires exactly the declared thermal state")
        if not np.isfinite(temperature).all() or np.any(temperature <= 0):
            raise ValueError("Missing/invalid material temperatures cannot become zero or ambient")
        boundaries = np.array([case_temperature_k, ambient_temperature_k])
        if not np.isfinite(boundaries).all() or np.any(boundaries <= 0):
            raise ValueError(
                "Explicit finite positive case and ambient boundary temperatures required"
            )
        result = []
        for name, index in zip(self.operator.node_names, self.node_to_ode, strict=True):
            if index is not None:
                result.append(float(temperature[index]))
            elif name == "motor_case_boundary":
                result.append(float(case_temperature_k))
            else:
                mode = self.end_boundary_modes[name]
                result.append(
                    float(ambient_temperature_k if mode == "ambient" else case_temperature_k)
                )
        return np.array(result)

    def rates(
        self, temperature_k: Any, *, case_temperature_k: float, ambient_temperature_k: float
    ) -> tuple[Any, float, list[tuple[str, str, str, str, float]]]:
        groups = self.group_temperatures(
            temperature_k,
            case_temperature_k=case_temperature_k,
            ambient_temperature_k=ambient_temperature_k,
        )
        heat = self.operator.heat_rates(groups)
        q = np.zeros(len(self.thermal_node_names))
        for index, value in zip(self.node_to_ode, heat, strict=True):
            if index is not None:
                q[index] += value
        links = [
            (f"finite_radiation:{a}->{b}", a, b, "diagnostic_material_node_diffuse_radiation", flux)
            for a, b, flux in self.operator.pair_fluxes(groups)
        ]
        return q, float(sum(q)), links

    def metadata(self) -> dict[str, Any]:
        covered = sorted(set(self.operator.node_names) - set(self.RESERVOIRS))
        return {
            **self.provenance,
            "thermal_node_names": list(self.thermal_node_names),
            "radiation_covered_thermal_nodes": covered,
            "radiation_excluded_thermal_nodes": sorted(set(self.thermal_node_names) - set(covered)),
            "reservoirs": list(self.RESERVOIRS),
            "missing_end_modes": self.end_boundary_modes,
            "condensation": self.operator.checks,
            "common_surface_conduction_radiation_coupling": "unavailable; material-node adapter is diagnostic only",
            "transient_acceptance_available": False,
        }


def aggregate_view_interval(
    sample: dict[str, Any], source_mask: Any, target_mask: Any, alpha: float = 0.01
) -> dict[str, float]:
    """Area-weighted raw first-hit fraction with a nonasymptotic Hoeffding bound.

    P(|estimate-F| >= h) <= alpha for independent weighted Bernoulli rays,
    h=sqrt(log(2/alpha)/2 * sum_i(w_i**2/n_i)). This is deliberately wider
    than a Gaussian standard error and remains valid for zero observed hits.
    """
    source = np.asarray(source_mask, dtype=bool)
    target = np.asarray(target_mask, dtype=bool)
    areas = sample["areas_m2"][source]
    if not len(areas) or not np.any(target):
        raise ValueError("Aggregate source and target must have nonempty coverage")
    weights = areas / sum(areas)
    fractions = sample["raw_view_factors"][source][:, target].sum(axis=1)
    estimate = float(weights @ fractions)
    half = float(np.sqrt(np.log(2 / alpha) / 2 * sum(weights**2 / sample["counts"][source])))
    return {
        "fraction": estimate,
        "confidence": 1 - alpha,
        "hoeffding_half_width": half,
        "lower": max(0.0, estimate - half),
        "upper": min(1.0, estimate + half),
        "source_area_m2": float(sum(areas)),
    }


def known_cases(ray_budget: int = 80000) -> dict[str, Any]:
    """Independent finite-disk result, closed cavity, long-cylinder limit."""
    disk_patches = [
        Patch("disk0", "annulus", 0, 0, 1, 1, "disk"),
        Patch("disk1", "annulus", 1, 0, 1, -1, "disk"),
        Patch("wall", "cylinder", 1, 0, 1, -1, "wall"),
    ]
    sample = sample_view_factors(disk_patches, ray_budget, 1801)
    expected = (3 - np.sqrt(5)) / 2
    interval = aggregate_view_interval(sample, [True, False, False], [False, True, False], 0.001)
    view, balance = reciprocal_enclosure(sample["raw_view_factors"], sample["areas_m2"])
    equilibrium = radiosity(view, sample["areas_m2"], np.full(3, 350.0), np.array([0.2, 0.6, 0.9]))
    hot = radiosity(
        view, sample["areas_m2"], np.array([500.0, 300.0, 350.0]), np.array([0.2, 0.6, 0.9])
    )
    long_patches = [
        Patch("inner", "cylinder", 0.01, 0, 10, 1, "outer"),
        Patch("outer", "cylinder", 0.02, 0, 10, -1, "inner"),
        Patch("end0", "annulus", 0, 0.01, 0.02, 1, "end"),
        Patch("end1", "annulus", 10, 0.01, 0.02, -1, "end"),
    ]
    long = sample_view_factors(long_patches, ray_budget, 1802)
    long_view, _ = reciprocal_enclosure(long["raw_view_factors"], long["areas_m2"])
    temperatures = np.array([500.0, 300.0, 300.0, 300.0])
    long_q = radiosity(long_view, long["areas_m2"], temperatures, np.full(4, 0.9))
    expected_q = SIGMA * long["areas_m2"][0] * (500**4 - 300**4) / (1 / 0.9 + 0.5 * (1 / 0.9 - 1))
    return {
        "finite_equal_disks": {
            "expected_view_factor": float(expected),
            "sampled": interval,
            "sampling": sample["sampling"],
        },
        "closed_cavity": {
            "balancing": balance,
            "uniform_temperature_max_abs_heat_w": float(np.max(abs(equilibrium["net_outward_w"]))),
            "nonuniform_temperature_energy_residual_w": hot["energy_residual_w"],
        },
        "long_cylinders": {
            "length_over_outer_radius": 500.0,
            "raw_inner_to_outer": float(long["raw_view_factors"][0, 1]),
            "raw_outer_to_inner": float(long["raw_view_factors"][1, 0]),
            "infinite_limits": [1.0, 0.5],
            "radiative_power_relative_error_from_infinite_limit": float(
                long_q["net_outward_w"][0] / expected_q - 1
            ),
            "sampling": long["sampling"],
        },
        "passed": bool(
            interval["lower"] <= expected <= interval["upper"]
            and sample["sampling"]["escaped_rays"] == 0
            and long["sampling"]["escaped_rays"] == 0
            and sample["sampling"][
                "raw_reciprocity_simultaneous_99pct_exact_binomial_intervals_overlap"
            ]
            and long["sampling"][
                "raw_reciprocity_simultaneous_99pct_exact_binomial_intervals_overlap"
            ]
            and np.max(abs(equilibrium["net_outward_w"])) < 1e-7
            and abs(hot["energy_residual_w"]) < 1e-6
            and abs(long_q["net_outward_w"][0] / expected_q - 1) < 0.02
        ),
        "ray_count": 2 * ray_budget,
        "scope": "numerical geometry/radiosity checks; no rocket or measured thermal validation",
    }
