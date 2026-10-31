"""Steady homogeneous-air tetrahedral conduction and boundary condensation.

For div(k grad T)=0 the weak bilinear form is integral k grad(v).grad(T)dV
(MFEM DiffusionIntegrator, https://mfem.org/bilininteg/). Linear tetrahedra
have constant gradients, so Ke=k*V*B*B.T. With prescribed isothermal boundary
groups, sparse elimination gives H_I=-K_II^-1 K_IB A and C=A.T K_B*H.
C*T is heat INTO the gas from each reservoir; -C*T is NET INWARD heat into
each solid/reservoir boundary. T.T*C*T is the positive Dirichlet quadratic form
in W K (not stored energy in joules or heat rate in watts).
This is a homogeneous, steady Laplace model: no radiation, gas capacity,
advection, convection enhancement, solid conduction or rocket acceptance.
References: MFEM weak form above; Gmsh 4.15.2 reference manual for tet4 node
ordering, https://gmsh.info/doc/texinfo/ ; DOE-HDBK-1012/2-92 for Fourier law.
Raw matrices and nonmonotone couplings are never clipped or symmetrized.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu


@dataclass(frozen=True)
class GasMesh:
    """SI coordinates; zero-based tet4 IDs and disjoint Dirichlet node groups.

    metadata MUST declare unlisted_exterior_faces='insulated'. The exporter is
    responsible for complete physical face classification and edge ownership;
    missing CAD labels must not be converted into this declaration. Other data
    (STEP/spec/mesh identities, physical face tags) is carried without inventing it.
    """

    points_m: Any
    tetrahedra: Any
    boundary_groups: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TetraAssembly:
    """Boundary-independent validated geometry and chunked tet4 conductivity."""

    points_m: Any
    tetrahedra: Any
    stiffness_w_k: Any
    gradients_per_m: Any
    volumes_m3: Any
    exterior_triangles: Any
    exterior_opposite_nodes: Any
    component_labels: Any
    component_count: int
    minimum_scaled_determinant: float
    retained_array_bytes: int


def assemble_tetra_conductivity(
    points_m: Any,
    tetrahedra: Any,
    conductivity_w_m_k: float,
    *,
    max_tetrahedra: int = 150000,
    max_nodes: int = 150000,
    chunk_tetrahedra: int = 25000,
) -> TetraAssembly:
    """Public shared assembly; no artificial boundary temperatures or solve.

    Default fixture cap remains150k. Primary-authorized actual-mesh callers may
    explicitly request up to750k tetrahedra/150k nodes. Element temporaries are
    chunked; COO arrays and gradients remain O(elements). This cap is NOT an LU
    memory approval: callers must bound factorization separately.
    """
    points = np.asarray(points_m, dtype=float)
    raw_tets = np.asarray(tetrahedra)
    if not 1 <= max_tetrahedra <= 750000 or not 1 <= max_nodes <= 150000 or chunk_tetrahedra < 1:
        raise ValueError("Invalid explicit tetra/node/chunk assembly budget")
    if not np.isfinite(conductivity_w_m_k) or conductivity_w_m_k <= 0:
        raise ValueError("Positive finite homogeneous conductivity required")
    if points.ndim != 2 or points.shape[1] != 3 or not np.isfinite(points).all():
        raise ValueError("Finite points_m[N,3] required")
    if raw_tets.ndim != 2 or raw_tets.shape[1] != 4 or raw_tets.dtype.kind not in "iu":
        raise ValueError("Integer tetrahedra[M,4] required")
    tets = raw_tets.astype(np.int64, copy=False)
    if not 0 < len(tets) <= max_tetrahedra or not 0 < len(points) <= max_nodes:
        raise ValueError("Empty mesh or tetrahedron/node budget exceeded")
    if int(tets.min()) < 0 or int(tets.max()) >= len(points):
        raise ValueError("Tetrahedron node ID outside points array")
    if len(np.unique(tets)) != len(points):
        raise ValueError("Orphan points are not permitted")
    canonical = np.sort(tets, axis=1)
    if np.any(np.diff(canonical, axis=1) == 0) or len(np.unique(canonical, axis=0)) != len(tets):
        raise ValueError("Repeated vertex or duplicate tetrahedron")
    gradients = np.empty((len(tets), 4, 3))
    volumes = np.empty(len(tets))
    row = np.empty(len(tets) * 16, dtype=np.int32)
    column = np.empty_like(row)
    data = np.empty(len(row))
    minimum_scaled = float("inf")
    for start in range(0, len(tets), chunk_tetrahedra):
        stop = min(start + chunk_tetrahedra, len(tets))
        cells = tets[start:stop]
        xyz = points[cells]
        jacobian = np.stack([xyz[:, i] - xyz[:, 0] for i in (1, 2, 3)], axis=2)
        determinants = np.linalg.det(jacobian)
        scale = np.max(np.linalg.norm(xyz[:, :, None] - xyz[:, None, :], axis=3), axis=(1, 2))
        if np.any(determinants <= 1e-12 * scale**3):
            raise ValueError(
                "Inverted or degenerate tetrahedron; orientation is not silently repaired"
            )
        minimum_scaled = min(minimum_scaled, float((determinants / scale**3).min()))
        inverse = np.linalg.inv(jacobian)
        gradients[start:stop] = np.concatenate((-inverse.sum(axis=1)[:, None, :], inverse), axis=1)
        volumes[start:stop] = determinants / 6
        local = (
            conductivity_w_m_k
            * volumes[start:stop, None, None]
            * np.einsum("tik,tjk->tij", gradients[start:stop], gradients[start:stop])
        )
        row[start * 16 : stop * 16] = np.repeat(cells, 4, axis=1).ravel()
        column[start * 16 : stop * 16] = np.tile(cells, (1, 4)).ravel()
        data[start * 16 : stop * 16] = local.ravel()
    stiffness = coo_matrix((data, (row, column)), shape=(len(points), len(points))).tocsr()
    face_nodes = tets[:, [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]].reshape(-1, 3)
    faces, first, counts = np.unique(
        np.sort(face_nodes, axis=1), axis=0, return_index=True, return_counts=True
    )
    if np.any(counts > 2):
        raise ValueError("Nonmanifold tetrahedral face")
    exterior = faces[counts == 1]
    opposite = tets[:, [3, 2, 1, 0]].ravel()[first[counts == 1]]
    edge_a = np.repeat(tets[:, 0], 3)
    edge_b = tets[:, 1:].ravel()
    graph = coo_matrix(
        (np.ones(len(edge_a) * 2), (np.r_[edge_a, edge_b], np.r_[edge_b, edge_a])),
        shape=stiffness.shape,
    ).tocsr()
    count, component = connected_components(graph, directed=False)
    retained = sum(
        array.nbytes
        for array in [
            points,
            tets,
            gradients,
            volumes,
            exterior,
            opposite,
            component,
            stiffness.data,
            stiffness.indices,
            stiffness.indptr,
        ]
    )
    return TetraAssembly(
        points,
        tets,
        stiffness,
        gradients,
        volumes,
        exterior,
        opposite,
        component,
        int(count),
        minimum_scaled,
        retained,
    )


def load_gas_mesh(mesh_npz: Path, groups_json: Path) -> GasMesh:
    """Load non-pickled points_m/tetrahedra NPZ and explicit groups/metadata JSON."""
    groups = json.loads(groups_json.read_text())
    with np.load(mesh_npz, allow_pickle=False) as archive:
        return GasMesh(
            archive["points_m"],
            archive["tetrahedra"],
            groups["boundary_groups"],
            groups["metadata"],
        )


def _positive_offdiagonal(matrix: Any, tolerance: float) -> dict[str, Any]:
    coo = matrix.tocoo()
    mask = (coo.row != coo.col) & (coo.data > 0)
    values, rows, cols = coo.data[mask], coo.row[mask], coo.col[mask]
    order = np.argsort(values)[::-1][:12]
    return {
        "strict_positive_count": len(values),
        "count_above_declared_tolerance": int(np.sum(values > tolerance)),
        "maximum_positive_w_k": float(values.max()) if len(values) else 0.0,
        "report_tolerance_w_k": tolerance,
        "largest_raw_entries": [
            {"row": int(rows[i]), "column": int(cols[i]), "value_w_k": float(values[i])}
            for i in order
        ],
    }


@dataclass(frozen=True)
class GasConductance:
    group_ids: tuple[str, ...]
    matrix_w_k: Any
    diagnostics: dict[str, Any]
    stiffness_w_k: Any
    harmonic_basis: Any
    points_m: Any
    tetrahedra: Any
    gradients_per_m: Any
    volumes_m3: Any
    free_nodes: Any
    conductivity_w_m_k: float

    @property
    def net_inward_matrix_w_k(self) -> Any:
        """Raw signed matrix for heat INWARD into solid/reservoir boundaries."""
        return -self.matrix_w_k

    def evaluate(self, group_temperature_k: Any) -> dict[str, Any]:
        """Raw signed rates, nodal field, residuals and independent element energy."""
        temperature = np.asarray(group_temperature_k, dtype=float)
        if temperature.shape != (len(self.group_ids),) or not np.isfinite(temperature).all():
            raise ValueError("One finite temperature per ordered boundary group is required")
        nodal = self.harmonic_basis @ temperature
        reaction = np.asarray(self.stiffness_w_k @ nodal)
        into_gas = self.matrix_w_k @ temperature
        grad_t = np.einsum("ti,tij->tj", nodal[self.tetrahedra], self.gradients_per_m)
        element_energy = float(
            np.sum(self.conductivity_w_m_k * self.volumes_m3 * np.sum(grad_t**2, axis=1))
        )
        matrix_energy = float(temperature @ self.matrix_w_k @ temperature)
        return {
            "group_ids": list(self.group_ids),
            "group_temperature_k": temperature.tolist(),
            "heat_into_gas_w": into_gas.tolist(),
            "net_inward_to_boundary_w": (-into_gas).tolist(),
            "sum_heat_into_gas_w": float(into_gas.sum()),
            "interior_residual_max_w": (
                float(np.abs(reaction[self.free_nodes]).max()) if len(self.free_nodes) else 0.0
            ),
            "matrix_dirichlet_form_w_times_k": matrix_energy,
            "element_dirichlet_form_w_times_k": element_energy,
            "dirichlet_form_difference_w_times_k": matrix_energy - element_energy,
            "nodal_temperature_k": nodal,
            "element_gradient_k_m": grad_t,
        }


def group_conductance(
    mesh: GasMesh,
    conductivity_w_m_k: float,
    *,
    max_tetrahedra: int = 150_000,
    algebra_relative_tolerance: float = 1e-9,
) -> GasConductance:
    """Assemble tet4 K and eliminate free nodes, preserving every signed entry.

    Missing/duplicate ownership, orphan nodes, nonmanifold faces, nonpositive or
    numerically degenerate Jacobians and unanchored air components are errors.
    Positive offdiagonals are diagnostics, not silently removed. A PSD condensed
    matrix does not guarantee a monotone resistor graph or a discrete maximum
    principle on an arbitrary tetrahedral mesh.
    """
    if not 1 <= max_tetrahedra <= 150000:
        raise ValueError("The bounded study permits at most150000 tetrahedra")
    if not np.isfinite(algebra_relative_tolerance) or algebra_relative_tolerance <= 0:
        raise ValueError("Positive finite algebra tolerance required")
    if mesh.metadata.get("unlisted_exterior_faces") != "insulated":
        raise ValueError(
            "Explicit complete boundary classification/insulation declaration required"
        )
    if not mesh.boundary_groups or any(not name for name in mesh.boundary_groups):
        raise ValueError("Named Dirichlet boundary groups required")
    assembly = assemble_tetra_conductivity(
        mesh.points_m, mesh.tetrahedra, conductivity_w_m_k, max_tetrahedra=max_tetrahedra
    )
    points, tets = assembly.points_m, assembly.tetrahedra
    stiffness, gradients, volumes = (
        assembly.stiffness_w_k,
        assembly.gradients_per_m,
        assembly.volumes_m3,
    )
    exterior = assembly.exterior_triangles
    component_count, component = assembly.component_count, assembly.component_labels
    exterior_mask = np.zeros(len(points), dtype=bool)
    exterior_mask[exterior.ravel()] = True
    owner = np.full(len(points), -1, dtype=int)
    group_ids = tuple(mesh.boundary_groups)
    for i, name in enumerate(group_ids):
        raw = np.asarray(mesh.boundary_groups[name])
        if raw.ndim != 1 or raw.dtype.kind not in "iu" or len(raw) == 0:
            raise ValueError(f"{name}: nonempty integer boundary node IDs required")
        nodes = raw.astype(np.int64, copy=False)
        if int(nodes.min()) < 0 or int(nodes.max()) >= len(points):
            raise ValueError(f"{name}: boundary node ID out of range")
        if len(np.unique(nodes)) != len(nodes) or np.any(owner[nodes] >= 0):
            raise ValueError(
                f"{name}: duplicate boundary ownership; exporter must resolve edges explicitly"
            )
        if not exterior_mask[nodes].all():
            raise ValueError(f"{name}: Dirichlet node is not on the exterior boundary")
        owner[nodes] = i
    if len(np.unique(component[owner >= 0])) != component_count:
        raise ValueError("Disconnected air component without a defined-temperature group")
    free = np.flatnonzero(owner < 0)
    harmonic = np.zeros((len(points), len(group_ids)))
    harmonic[np.flatnonzero(owner >= 0), owner[owner >= 0]] = 1
    if len(free):
        kii = stiffness[free][:, free].tocsc()
        lu = splu(kii)
        right = -(stiffness[free] @ harmonic)
        # One sparse factorization, one right-hand side per group.
        for i in range(len(group_ids)):
            harmonic[free, i] = lu.solve(right[:, i])
    reaction_basis = np.asarray(stiffness @ harmonic)
    condensed = np.vstack([reaction_basis[owner == i].sum(axis=0) for i in range(len(group_ids))])
    norm = float(max(np.abs(condensed).max(), np.abs(stiffness.diagonal()).max()))
    tol = max(np.finfo(float).eps * norm * 100, algebra_relative_tolerance * norm)
    symmetry_error = float(np.abs(condensed - condensed.T).max())
    row_residual = float(np.abs(condensed.sum(axis=1)).max())
    # Symmetric part is used ONLY for the diagnostic eigenvalue, never returned as C.
    eigenvalues = np.linalg.eigvalsh((condensed + condensed.T) / 2)
    k_asym = stiffness - stiffness.T
    k_symmetry = float(np.abs(k_asym.data).max()) if k_asym.nnz else 0.0
    free_residual = float(np.abs(reaction_basis[free]).max()) if len(free) else 0.0
    pair_g = -condensed.copy()
    np.fill_diagonal(pair_g, 0)  # Diagonal has no pair meaning; C is untouched.
    negatives = np.argwhere((pair_g < 0) & ~np.eye(len(group_ids), dtype=bool))
    ex_xyz = points[exterior]
    areas = (
        np.linalg.norm(np.cross(ex_xyz[:, 1] - ex_xyz[:, 0], ex_xyz[:, 2] - ex_xyz[:, 0]), axis=1)
        / 2
    )
    labels = owner[exterior]
    group_areas = {
        name: float(areas[np.all(labels == i, axis=1)].sum()) for i, name in enumerate(group_ids)
    }
    digest = hashlib.sha256()
    digest.update(points.astype("<f8").tobytes())
    digest.update(tets.astype("<i8").tobytes())
    digest.update(json.dumps(group_ids).encode())
    digest.update(owner.astype("<i8").tobytes())
    diagnostics = {
        "mesh_arrays_and_group_ownership_sha256": digest.hexdigest(),
        "source_metadata": mesh.metadata,
        "units": {
            "coordinates": "m",
            "K_and_C": "W/K",
            "heat_rates": "W",
            "temperature": "K",
            "dirichlet_quadratic_form": "W K",
        },
        "nodes": len(points),
        "tetrahedra": len(tets),
        "air_components": int(component_count),
        "volume_m3": float(volumes.sum()),
        "minimum_volume_m3": float(volumes.min()),
        "minimum_det_over_max_edge_cubed": assembly.minimum_scaled_determinant,
        "exterior_triangles": len(exterior),
        "exterior_area_m2": float(areas.sum()),
        "fully_group_owned_exterior_area_m2": group_areas,
        "other_exterior_faces_explicitly_insulated": True,
        "K_symmetry_max_w_k": k_symmetry,
        "K_constant_temperature_residual_max_w_k": float(
            np.abs(stiffness @ np.ones(len(points))).max()
        ),
        "K_PSD_basis": "Sum of positive k*V times gradient Gram matrices; positive determinants checked. No global dense eigenvalue computation.",
        "K_positive_offdiagonals": _positive_offdiagonal(stiffness, tol),
        "C_symmetry_max_w_k": symmetry_error,
        "C_row_sum_max_w_k": row_residual,
        "C_symmetric_part_eigenvalues_w_k": eigenvalues.tolist(),
        "C_raw_positive_offdiagonals": _positive_offdiagonal(coo_matrix(condensed), tol),
        "negative_raw_pair_conductances": [
            {"groups": [group_ids[i], group_ids[j]], "G_w_k": float(pair_g[i, j])}
            for i, j in negatives
        ],
        "interior_basis_residual_max_w_k": free_residual,
        "algebra_check_tolerance_w_k": tol,
        "algebra_checks_pass": max(symmetry_error, row_residual, free_residual, k_symmetry) <= tol
        and float(eigenvalues.min()) >= -tol,
        "raw_matrix_repaired_or_clipped": False,
        "global_tetrahedron_overlap_or_actual_CAD_occupancy_checked": False,
        "sign_convention": "C@T is heat INTO gas; -C@T is net heat INWARD into each solid/reservoir boundary.",
        "actual_CAD_mapping_or_rocket_thermal_acceptance": False,
    }
    return GasConductance(
        group_ids,
        condensed,
        diagnostics,
        stiffness,
        harmonic,
        points,
        tets,
        gradients,
        volumes,
        free,
        conductivity_w_m_k,
    )
