"""Finite half-wall coupling on a shared gas FEM surface field.

On each planar triangle, integral h Ni Nj dA=hA/12*(I+11.T), with
integral h Ni dA=hA/3. Thus A=Kair+R, A*Tgas=B*Tbulk+L*Q plus exact
prescribed-temperature elimination. Heat INTO bulk is B.T*Tgas-D*Tbulk.
L distributes a TOTAL surface-group Neumann load with normalized area weights;
S=L.T returns the conjugate group area mean. The same gas/surface field receives
loads and sets half-wall exchange. No fourth-power averaging is substituted for
the temperature mean, no radiation law is solved, and no legacy path is added.
References: MFEM mass/diffusion/boundary integrators, https://mfem.org/bilininteg/;
the verified project tet4 assembler and DOE-HDBK1012/2-92 Fourier resistance.
"""

from __future__ import annotations

import resource
import sys
import time
from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import splu

from src.analysis.gas_conduction import _positive_offdiagonal, assemble_tetra_conductivity


@dataclass(frozen=True)
class RobinGasMesh:
    points_m: Any
    tetrahedra: Any
    boundary_triangles: Any
    boundary_group_ids: Any
    metadata: dict[str, Any]


@dataclass(frozen=True)
class BoundaryCondition:
    kind: str
    bulk_id: str | None = None
    h_w_m2_k: float | None = None
    temperature_id: str | None = None
    bulk_basis_integrals_m2: dict[str, Any] | None = None
    wall_matrix_w_k: Any = None
    bulk_load_vectors_w_k: dict[str, Any] | None = None
    bulk_diagonal_w_k: dict[str, float] | None = None


def triangle_robin_matrix(area_m2: float, h_w_m2_k: float) -> Any:
    if not np.isfinite(area_m2 * h_w_m2_k) or min(area_m2, h_w_m2_k) <= 0:
        raise ValueError("Positive finite triangle area and Robin h required")
    return area_m2 * h_w_m2_k / 12 * (np.ones((3, 3)) + np.eye(3))


def integrated_wall_terms(row: BoundaryCondition, area: float) -> dict[str, Any]:
    """Normalize explicit scalar/basis/quadrature wall terms without repairs."""
    if row.temperature_id is not None:
        raise ValueError("Robin condition cannot use prescribed/radiative temperature IDs")
    if row.wall_matrix_w_k is not None:
        if (
            row.h_w_m2_k is not None
            or row.bulk_id is not None
            or row.bulk_basis_integrals_m2 is not None
        ):
            raise ValueError("Preintegrated wall terms cannot also specify scalar h/bulk/basis")
        matrix = np.asarray(row.wall_matrix_w_k, dtype=float)
        if (
            not row.bulk_load_vectors_w_k
            or not row.bulk_diagonal_w_k
            or set(row.bulk_load_vectors_w_k) != set(row.bulk_diagonal_w_k)
        ):
            raise ValueError("Explicit integrated B and D need identical named bulk IDs")
        vectors = {
            name: np.asarray(value, dtype=float)
            for name, value in row.bulk_load_vectors_w_k.items()
        }
        diagonal = {name: float(value) for name, value in row.bulk_diagonal_w_k.items()}
    else:
        if (
            row.bulk_load_vectors_w_k is not None
            or row.bulk_diagonal_w_k is not None
            or row.h_w_m2_k is None
            or not np.isfinite(row.h_w_m2_k)
            or row.h_w_m2_k <= 0
        ):
            raise ValueError("Robin face needs positive h or complete preintegrated terms")
        matrix = triangle_robin_matrix(area, row.h_w_m2_k)
        if row.bulk_basis_integrals_m2 is not None:
            if row.bulk_id is not None or not row.bulk_basis_integrals_m2:
                raise ValueError("Split-cell basis terms cannot also assign one bulk ID")
            vectors = {
                name: row.h_w_m2_k * np.asarray(value, dtype=float)
                for name, value in row.bulk_basis_integrals_m2.items()
            }
            diagonal = {name: float(value.sum()) for name, value in vectors.items()}
        else:
            if not row.bulk_id:
                raise ValueError("Robin face needs explicit physical bulk_id")
            vectors = {row.bulk_id: np.ones(3) * row.h_w_m2_k * area / 3}
            diagonal = {row.bulk_id: row.h_w_m2_k * area}
    if matrix.shape != (3, 3) or not np.isfinite(matrix).all() or np.any(matrix < 0):
        raise ValueError("Finite nonnegative3x3 wall matrix required")
    for name, vector in vectors.items():
        if (
            not name
            or vector.shape != (3,)
            or not np.isfinite(vector).all()
            or np.any(vector < 0)
            or not np.isfinite(diagonal[name])
            or diagonal[name] <= 0
        ):
            raise ValueError("Finite nonnegative named B vectors and positive D required")
    columns = np.column_stack(list(vectors.values()))
    d = np.array(list(diagonal.values()))
    scale = max(float(np.abs(matrix).max()), float(d.max()))
    tol = max(1e-14, scale * 1e-9)
    partition = max(
        float(np.abs(matrix @ np.ones(3) - columns.sum(axis=1)).max()),
        float(np.abs(d - columns.sum(axis=0)).max()),
    )
    asym = float(np.abs(matrix - matrix.T).max())
    augmented = np.block([[matrix, -columns], [-columns.T, np.diag(d)]])
    minimum = float(np.linalg.eigvalsh((augmented + augmented.T) / 2).min())
    if partition > tol or asym > tol or minimum < -tol:
        raise ValueError("Integrated wall energy PSD/symmetry/B/D partition failure; no repair")
    return {
        "matrix": matrix,
        "vectors": vectors,
        "diagonal": diagonal,
        "minimum_augmented_eigenvalue_w_k": minimum,
        "partition_residual_w_k": partition,
    }


@dataclass
class RobinGasFactor:
    mesh: RobinGasMesh
    assembly: Any
    group_ids: tuple[int, ...]
    bulk_ids: tuple[str, ...]
    prescribed_ids: tuple[str, ...]
    group_areas_m2: Any
    A_w_k: Any
    B_w_k: Any
    D_bulk_w_k: Any
    L_per_area: Any
    E_prescribed: Any
    free_nodes: Any
    fixed_nodes: Any
    lu: Any
    triangle_h: Any
    triangle_bulk: Any
    triangle_areas: Any
    triangle_group_columns: Any
    wall_terms: Any
    reservoir_conductance_raw_w_k: Any
    mean_by_reservoir_temperature: Any
    mean_by_group_neumann_k_w: Any
    reservoir_heat_by_group_neumann: Any
    diagnostics: dict[str, Any]

    def _solve(self, bulk: Any, prescribed: Any, loads: Any) -> Any:
        count = bulk.shape[1]
        field = np.asarray(self.E_prescribed @ prescribed)
        rhs = np.asarray(self.B_w_k @ bulk + self.L_per_area @ loads - self.A_w_k @ field)
        if len(self.free_nodes):
            field[self.free_nodes] = self.lu.solve(rhs[self.free_nodes])
        if field.shape != (len(self.mesh.points_m), count):
            raise ValueError("Unexpected reconstructed field shape")
        return field

    def _reservoir_heat(self, field: Any, bulk: Any, loads: Any) -> Any:
        into_bulk = np.asarray(self.B_w_k.T @ field) - self.D_bulk_w_k[:, None] * bulk
        residual = np.asarray(self.A_w_k @ field - self.B_w_k @ bulk - self.L_per_area @ loads)
        into_prescribed = -np.asarray(self.E_prescribed.T @ residual)
        return np.vstack((into_bulk, into_prescribed))

    def reconstruct(
        self, bulk_temperature_k: Any, prescribed_temperature_k: Any, group_neumann_w: Any
    ) -> Any:
        """Complete nodal T for physical bulk/prescribed states and signed loads."""
        vectors = []
        for raw, size in (
            (bulk_temperature_k, len(self.bulk_ids)),
            (prescribed_temperature_k, len(self.prescribed_ids)),
            (group_neumann_w, len(self.group_ids)),
        ):
            vector = np.asarray(raw, dtype=float)
            if vector.shape != (size,) or not np.isfinite(vector).all():
                raise ValueError("Finite vectors in reported state/group order required")
            vectors.append(vector[:, None])
        return self._solve(*vectors)[:, 0]

    def evaluate(
        self, bulk_temperature_k: Any, prescribed_temperature_k: Any, group_neumann_w: Any
    ) -> dict[str, Any]:
        bulk = np.asarray(bulk_temperature_k, dtype=float)
        prescribed = np.asarray(prescribed_temperature_k, dtype=float)
        loads = np.asarray(group_neumann_w, dtype=float)
        field = self.reconstruct(bulk, prescribed, loads)
        mean = np.asarray(self.L_per_area.T @ field)
        into = self._reservoir_heat(field[:, None], bulk[:, None], loads[:, None])[:, 0]
        residual = np.asarray(self.A_w_k @ field - self.B_w_k @ bulk - self.L_per_area @ loads)
        gradient = np.einsum(
            "ti,tij->tj", field[self.assembly.tetrahedra], self.assembly.gradients_per_m
        )
        air_form = float(
            np.sum(
                self.assembly.volumes_m3
                * self.diagnostics["conductivity_w_m_k"]
                * np.sum(gradient**2, axis=1)
            )
        )
        tris = np.asarray(self.mesh.boundary_triangles)
        values = field[tris]
        wall_form = 0.0
        for face, term in enumerate(self.wall_terms):
            if term is None:
                continue
            # Shift the physical temperature differences only for stable energy
            # evaluation; raw assembled matrices/reactions remain untouched.
            reference = bulk[term["indexed"][0][0]]
            surface = values[face] - reference
            local_form = float(surface @ term["matrix"] @ surface)
            for column, vector, diagonal in term["indexed"]:
                shifted = bulk[column] - reference
                local_form += float(-2 * shifted * (vector @ surface) + diagonal * shifted**2)
            wall_form += local_form
        states = np.r_[bulk, prescribed]
        boundary_form = float(loads @ mean - states @ into)
        # Exact fourth-power integral of the P1 interpolant: sum15 monomials/15.
        fourth = np.zeros(len(tris))
        for a in range(5):
            for b in range(5 - a):
                c = 4 - a - b
                fourth += values[:, 0] ** a * values[:, 1] ** b * values[:, 2] ** c / 15
        mean_fourth = (
            np.bincount(
                self.triangle_group_columns,
                weights=self.triangle_areas * fourth,
                minlength=len(self.group_ids),
            )
            / self.group_areas_m2
        )
        mean_from_maps = (
            self.mean_by_reservoir_temperature @ states + self.mean_by_group_neumann_k_w @ loads
        )
        heat_from_maps = (
            -self.reservoir_conductance_raw_w_k @ states
            + self.reservoir_heat_by_group_neumann @ loads
        )
        return {
            "group_ids": list(self.group_ids),
            "bulk_ids": list(self.bulk_ids),
            "prescribed_ids": list(self.prescribed_ids),
            "nodal_temperature_k": field,
            "area_mean_temperature_k": mean.tolist(),
            "area_mean_fourth_power_k4": mean_fourth.tolist(),
            "fourth_power_of_area_mean_k4": (mean**4).tolist(),
            "P1_nodal_minimum_k": float(field.min()),
            "P1_nodal_maximum_k": float(field.max()),
            "heat_into_bulk_w": into[: len(self.bulk_ids)].tolist(),
            "heat_into_prescribed_reservoir_w": into[len(self.bulk_ids) :].tolist(),
            "total_group_neumann_into_surface_gas_w": loads.tolist(),
            "energy_balance_residual_w": float(into.sum() - loads.sum()),
            "free_residual_max_w": (
                float(np.abs(residual[self.free_nodes]).max()) if len(self.free_nodes) else 0
            ),
            "air_dirichlet_form_w_times_k": air_form,
            "halfwall_dirichlet_form_w_times_k": wall_form,
            "boundary_work_form_w_times_k": boundary_form,
            "form_balance_difference_w_times_k": air_form + wall_form - boundary_form,
            "mean_map_reconstruction_difference_k": float(np.abs(mean - mean_from_maps).max()),
            "heat_map_reconstruction_difference_w": float(np.abs(into - heat_from_maps).max()),
            "physical_local_hot_spot_or_nonlinear_radiation_qualified": False,
        }


def factor_robin_gas(
    mesh: RobinGasMesh,
    conditions: Any,
    conductivity_w_m_k: float,
    *,
    max_tetrahedra: int = 150000,
    max_nodes: int = 150000,
    factor_memory_limit_mb: float = 512,
    max_factor_free_nodes: int = 25000,
    reduced_map_memory_limit_mb: float = 256,
    rhs_block_size: int = 16,
    ordering: str = "COLAMD",
) -> RobinGasFactor:
    """All facets classified; conditions are group defaults OR per-facet rows.

    Physical prescribed temperatures are independent of radiative brightness.
    Variable-h or mixed-cell triangles require caller-resolved subfacets; no
    centroid substitution is made. LU guards are conservative estimates and a
    free-node cap, not a guaranteed native allocator/RSS limit.
    """
    if (
        not np.isfinite(factor_memory_limit_mb)
        or not np.isfinite(reduced_map_memory_limit_mb)
        or min(factor_memory_limit_mb, reduced_map_memory_limit_mb) <= 0
        or not 0 <= max_factor_free_nodes <= 150000
        or not 1 <= rhs_block_size <= 32
    ):
        raise ValueError(
            "Positive explicit memory limits and bounded free-node/RHS budgets required"
        )
    assembly = assemble_tetra_conductivity(
        mesh.points_m,
        mesh.tetrahedra,
        conductivity_w_m_k,
        max_tetrahedra=max_tetrahedra,
        max_nodes=max_nodes,
    )
    points = assembly.points_m
    n = len(points)
    raw = np.asarray(mesh.boundary_triangles)
    raw_ids = np.asarray(mesh.boundary_group_ids)
    if (
        raw.ndim != 2
        or raw.shape[1] != 3
        or raw.dtype.kind not in "iu"
        or raw_ids.shape != (len(raw),)
        or raw_ids.dtype.kind not in "iu"
    ):
        raise ValueError(
            "Integer complete boundary_triangles[B,3] and boundary_group_ids[B] required"
        )
    triangles = raw.astype(np.int64, copy=False)
    if not len(triangles) or triangles.min() < 0 or triangles.max() >= n:
        raise ValueError("Boundary triangle node IDs invalid")
    canonical = np.sort(triangles, axis=1)
    order = np.lexsort(canonical[:, ::-1].T)
    if not np.array_equal(canonical[order], assembly.exterior_triangles):
        raise ValueError(
            "ALL exterior triangles must appear exactly once; no missing/duplicate/internal facets"
        )
    opposite = np.empty(len(triangles), dtype=int)
    opposite[order] = assembly.exterior_opposite_nodes
    xyz = points[triangles]
    normal = np.cross(xyz[:, 1] - xyz[:, 0], xyz[:, 2] - xyz[:, 0])
    if np.any(np.sum(normal * (points[opposite] - xyz[:, 0]), axis=1) >= 0):
        raise ValueError("Boundary triangles must be outward oriented; no automatic repair")
    areas = np.linalg.norm(normal, axis=1) / 2
    group_ids = tuple(int(i) for i in np.unique(raw_ids))
    columns = np.searchsorted(group_ids, raw_ids)
    group_areas = np.bincount(columns, weights=areas, minlength=len(group_ids))
    rows = []
    terms = []
    for i, gid in enumerate(raw_ids):
        spec = (
            conditions.get(int(gid))
            if isinstance(conditions, dict)
            else conditions[i] if len(conditions) == len(triangles) else None
        )
        if spec is None:
            raise ValueError(f"Missing boundary classification for facet{i}/group{gid}")
        row = spec if isinstance(spec, BoundaryCondition) else BoundaryCondition(**spec)
        extra_wall = (
            row.bulk_id is not None
            or row.h_w_m2_k is not None
            or row.bulk_basis_integrals_m2 is not None
            or row.wall_matrix_w_k is not None
            or row.bulk_load_vectors_w_k is not None
            or row.bulk_diagonal_w_k is not None
        )
        if row.kind == "robin":
            term = integrated_wall_terms(row, areas[i])
        elif row.kind == "dirichlet":
            if not row.temperature_id or extra_wall:
                raise ValueError("Prescribed gas surface needs separate physical temperature_id")
            term = None
        elif row.kind == "insulated":
            if row.temperature_id is not None or extra_wall:
                raise ValueError("Insulated condition must be explicit without a hidden reservoir")
            term = None
        else:
            raise ValueError("Every triangle needs robin/dirichlet/insulated classification")
        rows.append(row)
        terms.append(term)
    bulk_ids = tuple(
        dict.fromkeys(name for term in terms if term is not None for name in term["vectors"])
    )
    prescribed_ids = tuple(
        dict.fromkeys(
            r.temperature_id for r in rows if r.kind == "dirichlet" and r.temperature_id is not None
        )
    )
    nb, nd, ng = len(bulk_ids), len(prescribed_ids), len(group_ids)
    if nb + nd == 0:
        raise ValueError("At least one physical anchored boundary required")
    bulk_index = {name: i for i, name in enumerate(bulk_ids)}
    dir_index = {name: i for i, name in enumerate(prescribed_ids)}
    h = np.array([r.h_w_m2_k or 0 for r in rows], dtype=float)
    bulk_col = np.array(
        [
            bulk_index[str(r.bulk_id)] if r.kind == "robin" and r.bulk_id is not None else -1
            for r in rows
        ]
    )
    robin = np.array([i for i, term in enumerate(terms) if term is not None], dtype=int)
    rt = triangles[robin]
    local = np.asarray([terms[i]["matrix"] for i in robin]).reshape(-1, 3, 3)
    rr, rc = np.repeat(rt, 3, axis=1).ravel(), np.tile(rt, (1, 3)).ravel()
    R = coo_matrix((local.ravel(), (rr, rc)), shape=(n, n)).tocsr()
    br, bc, bv = [], [], []
    D = np.zeros(nb)
    for face, term in enumerate(terms):
        if term is None:
            continue
        term["indexed"] = []
        for name, vector in term["vectors"].items():
            column = bulk_index[name]
            br.extend(triangles[face].tolist())
            bc.extend([column] * 3)
            bv.extend(vector.tolist())
            D[column] += term["diagonal"][name]
            term["indexed"].append((column, vector, term["diagonal"][name]))
    B = coo_matrix((bv, (br, bc)), shape=(n, nb)).tocsr()
    L = coo_matrix(
        (
            np.repeat(areas / (3 * group_areas[columns]), 3),
            (triangles.ravel(), np.repeat(columns, 3)),
        ),
        shape=(n, ng),
    ).tocsr()
    owner = np.full(n, -1, dtype=int)
    for i, row in enumerate(rows):
        if row.kind == "dirichlet":
            col = dir_index[str(row.temperature_id)]
            nodes = triangles[i]
            if np.any((owner[nodes] >= 0) & (owner[nodes] != col)):
                raise ValueError(
                    "Conflicting prescribed temperature IDs share a node; no corner priority"
                )
            owner[nodes] = col
    fixed = np.flatnonzero(owner >= 0)
    free = np.flatnonzero(owner < 0)
    E = coo_matrix((np.ones(len(fixed)), (fixed, owner[fixed])), shape=(n, nd)).tocsr()
    anchored = np.unique(
        np.r_[assembly.component_labels[fixed], assembly.component_labels[rt.ravel()]]
    )
    if len(anchored) != assembly.component_count:
        raise ValueError(
            "Disconnected air component has neither positive Robin coupling nor prescribed temperature"
        )
    A = assembly.stiffness_w_k + R
    Aff = A[free][:, free].tocsc()
    estimated_lu_bytes = int(Aff.nnz * 64 * 16 + len(free) * 16 * 8)
    map_bytes = int(8 * ((nb + nd) ** 2 + 2 * ng * (nb + nd) + ng**2))
    if len(free) > max_factor_free_nodes or estimated_lu_bytes > factor_memory_limit_mb * 1024**2:
        raise MemoryError(
            f"Factorization preflight stop: {len(free)} free nodes, estimated{estimated_lu_bytes/1024**2:.1f}MiB; no oversized LU attempted"
        )
    if map_bytes > reduced_map_memory_limit_mb * 1024**2:
        raise MemoryError("Reduced-map memory budget exceeded before factorization")
    if rhs_block_size < 1:
        raise ValueError("Positive bounded RHS block size required")
    if ordering not in ("COLAMD", "MMD_AT_PLUS_A"):
        raise ValueError("Explicit COLAMD or MMD_AT_PLUS_A ordering required")
    factor_started = time.monotonic()
    lu = splu(Aff, permc_spec=ordering) if len(free) else None
    factor_elapsed = time.monotonic() - factor_started
    result = RobinGasFactor(
        mesh,
        assembly,
        group_ids,
        bulk_ids,
        prescribed_ids,
        group_areas,
        A,
        B,
        D,
        L,
        E,
        free,
        fixed,
        lu,
        h,
        bulk_col,
        areas,
        columns,
        terms,
        np.empty((nb + nd, nb + nd)),
        np.empty((ng, nb + nd)),
        np.empty((ng, ng)),
        np.empty((nb + nd, ng)),
        {},
    )
    nr = nb + nd
    reservoir_nodal_min = float("inf")
    reservoir_nodal_max = -float("inf")
    load_nodal_min = float("inf")
    load_nodal_max = -float("inf")
    for start in range(0, nr, rhs_block_size):
        stop = min(start + rhs_block_size, nr)
        basis = np.eye(nr)[:, start:stop]
        field = result._solve(basis[:nb], basis[nb:], np.zeros((ng, stop - start)))
        reservoir_nodal_min = min(reservoir_nodal_min, float(field.min()))
        reservoir_nodal_max = max(reservoir_nodal_max, float(field.max()))
        result.mean_by_reservoir_temperature[:, start:stop] = L.T @ field
        result.reservoir_conductance_raw_w_k[:, start:stop] = -result._reservoir_heat(
            field, basis[:nb], np.zeros((ng, stop - start))
        )
    for start in range(0, ng, rhs_block_size):
        stop = min(start + rhs_block_size, ng)
        basis = np.eye(ng)[:, start:stop]
        field = result._solve(np.zeros((nb, stop - start)), np.zeros((nd, stop - start)), basis)
        load_nodal_min = min(load_nodal_min, float(field.min()))
        load_nodal_max = max(load_nodal_max, float(field.max()))
        result.mean_by_group_neumann_k_w[:, start:stop] = L.T @ field
        result.reservoir_heat_by_group_neumann[:, start:stop] = result._reservoir_heat(
            field, np.zeros((nb, stop - start)), basis
        )
    C = result.reservoir_conductance_raw_w_k
    W = result.mean_by_group_neumann_k_w
    G = result.mean_by_reservoir_temperature
    scale = max(float(np.abs(A.diagonal()).max()), float(np.abs(C).max()))
    tol = scale * 1e-9
    eigen = np.linalg.eigvalsh((C + C.T) / 2)
    weigen = np.linalg.eigvalsh((W + W.T) / 2)
    errors = {
        "C_symmetry_w_k": float(np.abs(C - C.T).max()),
        "C_row_sum_w_k": float(np.abs(C.sum(axis=1)).max()),
        "mean_load_symmetry_k_w": float(np.abs(W - W.T).max()),
        "power_conjugacy_dimensionless": float(
            np.abs(result.reservoir_heat_by_group_neumann - G.T).max()
        ),
        "uniform_temperature_mean_partition": float(np.abs(G.sum(axis=1) - 1).max()),
    }
    result.diagnostics = {
        "nodes": n,
        "tetrahedra": len(assembly.tetrahedra),
        "boundary_triangles": len(triangles),
        "air_components": assembly.component_count,
        "conductivity_w_m_k": conductivity_w_m_k,
        "ordering": ordering,
        "raw_nodal_reservoir_basis_minimum_k_k": reservoir_nodal_min,
        "raw_nodal_reservoir_basis_maximum_k_k": reservoir_nodal_max,
        "raw_nodal_positive_Neumann_basis_minimum_k_w": load_nodal_min,
        "raw_nodal_positive_Neumann_basis_maximum_k_w": load_nodal_max,
        "native_LU_elapsed_s": factor_elapsed,
        "measured_process_max_rss_bytes": int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            * (1 if sys.platform == "darwin" else 1024)
        ),
        "rss_scope": "Process high-water RSS including imports/assembly/maps, not an incremental LU allocation or a hard allocator limit",
        "local_wall_partition_residual_max_w_k": max(
            (t["partition_residual_w_k"] for t in terms if t is not None), default=0.0
        ),
        "local_wall_augmented_eigenvalue_min_w_k": min(
            (t["minimum_augmented_eigenvalue_w_k"] for t in terms if t is not None), default=0.0
        ),
        "multi_bulk_wall_triangles": sum(len(t["vectors"]) > 1 for t in terms if t is not None),
        "bulk_ids": list(bulk_ids),
        "prescribed_ids": list(prescribed_ids),
        "ordered_surface_group_ids": list(group_ids),
        "assembly_retained_array_bytes": assembly.retained_array_bytes,
        "preflight_estimated_LU_bytes": estimated_lu_bytes,
        "preflight_fill_multiplier_estimate": 64,
        "LU_actual_L_U_nonzeros": 0 if lu is None else int(lu.L.nnz + lu.U.nnz),
        "reduced_maps_bytes": map_bytes,
        "full_field_response_basis_stored": False,
        "K_positive_offdiagonals": _positive_offdiagonal(assembly.stiffness_w_k, tol),
        "A_positive_offdiagonals": _positive_offdiagonal(A, tol),
        "C_positive_offdiagonals": _positive_offdiagonal(coo_matrix(C), tol),
        "C_symmetric_part_eigenvalues_w_k": eigen.tolist(),
        "mean_load_symmetric_part_eigenvalues_k_w": weigen.tolist(),
        "minimum_raw_mean_temperature_response_to_positive_load_k_w": float(W.min()),
        "minimum_raw_mean_temperature_response_to_reservoir_k_k": float(G.min()),
        "checks": errors,
        "algebra_checks_pass": errors["C_symmetry_w_k"] <= max(tol, 1e-12)
        and errors["C_row_sum_w_k"] <= max(tol, 1e-12)
        and float(eigen.min()) >= -max(tol, 1e-12)
        and errors["mean_load_symmetry_k_w"] <= max(1e-8, float(np.abs(W).max()) * 1e-9)
        and float(weigen.min()) >= -max(1e-8, float(np.abs(W).max()) * 1e-9)
        and errors["power_conjugacy_dimensionless"] < 1e-8
        and errors["uniform_temperature_mean_partition"] < 1e-8,
        "raw_matrix_clipped_repaired_or_corner_prioritized": False,
        "actual_rocket_mesh_temperature_or_radiation_acceptance": False,
    }
    return result
