"""Read-only counts for planar-parent strips, without constructing a mesh.

For a triangulated parent disk with B added boundary points and I interior
points, Euler's relation gives T=1+B+2I. A full noncrossing strip cut adds two
edge points; orthogonal cap lines add one interior vertex per proper crossing.
The planar graph subdivision relation is F=1+nx+ny+I. References: Euler's
formula for planar graphs; affine triangle clipping/barycentric coordinates.
These are topology/count calculations, not an FE validity or accuracy proof.
"""

from __future__ import annotations

import os

for key in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"]:
    os.environ[key] = "1"

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.cad_gas_mesh import load_source
from src.analysis.refined_gas_boundary import edge_table, targets


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rational(value: float) -> Fraction:
    return Fraction.from_float(float(value))


def interior_planes(low: float, high: float, planes: list[Fraction]) -> list[Fraction]:
    lo, hi = rational(low), rational(high)
    return [plane for plane in planes if lo < plane < hi]


def ticks(low: Fraction, high: Fraction, step: Fraction) -> list[Fraction]:
    return [k * step for k in range(math.ceil(low / step), math.floor(high / step) + 1)]


def strict_inside_grid(triangle: np.ndarray, step: Fraction) -> tuple[int, int]:
    """Count only proper grid crossings, using exact rational fallback near edges."""
    xs = interior_planes(
        triangle[:, 0].min(),
        triangle[:, 0].max(),
        ticks(rational(triangle[:, 0].min()), rational(triangle[:, 0].max()), step),
    )
    ys = interior_planes(
        triangle[:, 1].min(),
        triangle[:, 1].max(),
        ticks(rational(triangle[:, 1].min()), rational(triangle[:, 1].max()), step),
    )
    if not xs or not ys:
        return 0, 0
    x, y = np.meshgrid(np.array(xs, dtype=float), np.array(ys, dtype=float), indexing="ij")
    p = np.column_stack([x.ravel(), y.ravel()])
    cross = []
    tolerances = []
    for a, b in zip(triangle[:, :2], np.roll(triangle[:, :2], -1, axis=0)):
        d = b - a
        v = p - a
        cross.append(d[0] * v[:, 1] - d[1] * v[:, 0])
        tolerances.append(64 * np.finfo(float).eps * (abs(d[0] * v[:, 1]) + abs(d[1] * v[:, 0])))
    values, error = np.array(cross), np.array(tolerances)
    d0, d1 = triangle[1, :2] - triangle[0, :2], triangle[2, :2] - triangle[0, :2]
    sign = 1 if d0[0] * d1[1] - d0[1] * d1[0] > 0 else -1
    signed = values * sign
    definitely_inside = (signed > error).all(axis=0)
    definitely_outside = (signed < -error).any(axis=0)
    ambiguous = np.flatnonzero(~definitely_inside & ~definitely_outside)
    total = int(definitely_inside.sum())
    rtri = [[rational(c) for c in row[:2]] for row in triangle]
    for index in ambiguous:
        rx, ry = xs[index // len(ys)], ys[index % len(ys)]
        checks = []
        for a, b in zip(rtri, rtri[1:] + rtri[:1]):
            checks.append(sign * ((b[0] - a[0]) * (ry - a[1]) - (b[1] - a[1]) * (rx - a[0])))
        total += int(all(value > 0 for value in checks))
    return total, len(ambiguous)


def insert_planes(
    parent: int,
    axis: int,
    planes: list[Fraction],
    triangles: np.ndarray,
    points: np.ndarray,
    triangle_edges: np.ndarray,
    edges: np.ndarray,
    registry: dict[int, set[Fraction]],
) -> None:
    for edge_id in triangle_edges[parent]:
        a, b = points[edges[edge_id], axis]
        if a == b:
            continue
        ra, rb = rational(a), rational(b)
        for plane in planes:
            t = (plane - ra) / (rb - ra)
            if 0 < t < 1:
                registry[int(edge_id)].add(t)


def fixtures() -> dict[str, Any]:
    p = np.array([[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, 2.0, 0.0], [2.0, 2.0, 0.0]])
    tri = np.array([[0, 1, 2], [1, 3, 2]])
    edges, te, _ = edge_table(tri)
    registry: dict[int, set[Fraction]] = defaultdict(set)
    insert_planes(0, 0, [Fraction(1)], tri, p, te, edges, registry)
    insert_planes(1, 0, [Fraction(1)], tri, p, te, edges, registry)
    assert sum(len(value) for value in registry.values()) == 3
    assert sum(sum(len(registry[int(e)]) for e in row) for row in te) == 4
    interior, exact = strict_inside_grid(p[tri[0]], Fraction(1, 2))
    assert interior == 3
    # No geometric movement is involved: this fixture just counts two parallel
    # sheets, with the same intersection counts regardless of their 20um gap.
    shifted = p[tri[0]].copy()
    shifted[:, 2] = 0.02
    assert strict_inside_grid(shifted, Fraction(1, 2))[0] == interior
    return {
        "passed": True,
        "shared_edge_union_points": 3,
        "two_parent_added_boundary_points": 4,
        "proper_grid_crossings": interior,
        "exact_boundary_escalations": exact,
        "20um_parallel_barrier_count_invariant": True,
        "generated_mesh": False,
    }


def necessary_lower_counts(source: dict[str, Any]) -> dict[str, Any]:
    """Relaxed necessary counts; never a candidate or optimum construction.

    Integrate axial resolution work along each preserved old edge: dz/0.1 in
    critical intervals and dz/12 elsewhere on global case/liner edges. Each
    admissible child segment has work <=1. We omit radial-crossing edges from
    the local bound unless BOTH endpoints are strictly inside r16, for which
    convexity guarantees the entire chord is inside. Cap triangle area cannot
    exceed sqrt(3)/4 for maximum edge1mm. Each additional surface vertex can
    increase cap triangle count by at most two.
    """
    boundary = source["boundary"]
    p, tri = boundary["vertices_mm"], boundary["triangles"]
    edges, te, _ = edge_table(tri)
    selection = targets(source)
    flags = {}
    for name, mask in selection["masks"].items():
        flag = np.zeros(len(edges), dtype=bool)
        np.logical_or.at(flag, te.ravel(), np.repeat(mask, 3))
        flags[name] = flag
    fore, aft, pad = [rational(selection[name]) for name in ["fore_mm", "aft_mm", "pad_fore_mm"]]
    minimum_added = np.zeros(len(edges), dtype=np.int64)
    radial_omissions = 0
    for index in np.flatnonzero(
        flags["global_case_liner"] | flags["local_ends"] | flags["fore_corner"] | flags["planar"]
    ):
        a, b = p[edges[index]]
        za, zb = rational(a[2]), rational(b[2])
        length = abs(zb - za)
        intervals: list[tuple[Fraction, Fraction]] = []
        if length and (flags["local_ends"][index] or flags["fore_corner"][index]):
            if max(np.linalg.norm(a[:2]), np.linalg.norm(b[:2])) < 16 - 1e-9:
                bands = []
                if flags["local_ends"][index]:
                    bands += [
                        (fore - Fraction(2, 5), fore + Fraction(2, 5)),
                        (aft - Fraction(2, 5), aft + Fraction(2, 5)),
                    ]
                if flags["fore_corner"][index]:
                    bands += [(pad, fore)]
                for low, high in bands:
                    lo, hi = max(min(za, zb), low), min(max(za, zb), high)
                    if hi > lo:
                        intervals.append((lo, hi))
            else:
                radial_omissions += 1
        merged: list[tuple[Fraction, Fraction]] = []
        for lo, hi in sorted(intervals):
            if merged and lo <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
            else:
                merged.append((lo, hi))
        local = sum((hi - lo for lo, hi in merged), Fraction(0))
        work = local * 10
        if flags["global_case_liner"][index]:
            work += (length - local) / 12
        # Relax ONLY this necessary-count bound by1e-10 relative, larger than
        # the frozen1e-12 comparison allowance, avoiding binary64 ceil jumps.
        # Actual refinement criteria remain unchanged.
        segments = max(1, math.ceil(work / (1 + Fraction(1, 10**10))))
        if flags["planar"][index]:
            # The downward padding makes this a conservative necessary count,
            # without treating a floating near-integer as an extra whole point.
            segments = max(
                segments, math.ceil(float(np.linalg.norm(b[:2] - a[:2])) / (1 + 1e-10) - 1e-10)
            )
        minimum_added[index] = segments - 1
    bmin = minimum_added[te].sum(axis=1)
    cap = selection["masks"]["planar"]
    vertices = p[tri[cap]]
    area = (
        np.linalg.norm(
            np.cross(vertices[:, 1] - vertices[:, 0], vertices[:, 2] - vertices[:, 0]), axis=1
        )
        / 2
    )
    area_triangles = np.maximum(
        1, np.ceil(area / ((math.sqrt(3) / 4) * (1 + 1e-10) ** 2) - 1e-10)
    ).astype(np.int64)
    cap_deficit = int(np.maximum(0, area_triangles - 1 - bmin[cap]).sum())
    area_extra = (cap_deficit + 1) // 2
    added_edges = int(minimum_added.sum())
    added = added_edges + area_extra
    return {
        "bound_kind": "relaxed necessary count, not a constructible mesh or sufficiency proof",
        "mandatory_old_edge_added_nodes_at_least": added_edges,
        "additional_nodes_from_cap_area_at_least": area_extra,
        "boundary_nodes_at_least": len(p) + added,
        "boundary_triangles_at_least": len(tri) + 2 * added,
        "selected_cap_area_mm2": float(area.sum()),
        "cap_triangle_area_limit_mm2": math.sqrt(3) / 4,
        "cap_parent_area_triangle_counts_sum": int(area_triangles.sum()),
        "original_edges_omitted_from_local_bound_due_radial_endpoint_test": radial_omissions,
        "conservatism": "Local radial-crossing chords omitted; outside local intervals on non-global edges impose no axial work. Endpoint/graded-strip transitions, angular quality and tetrahedral quality are not lower-bounded. Necessary-count limits ONLY are relaxed1e-10 relative to avoid roundoff ceil jumps (larger than frozen1e-12 comparison allowance); cap integer counts also receive downward1e-10 padding. Actual criteria unchanged.",
        "triangle_count_relation": "Euler invariant: added surface vertex increases closed triangulation count by2 when topology and all old vertices are retained",
    }


def analyze(source: dict[str, Any]) -> dict[str, Any]:
    boundary = source["boundary"]
    points, triangles = boundary["vertices_mm"], boundary["triangles"]
    edges, te, incidence = edge_table(triangles)
    if (incidence != 2).any():
        raise ValueError("Frozen source is not closed two-manifold")
    selection = targets(source)
    masks = selection["masks"]
    fore, aft, pad = [rational(selection[name]) for name in ["fore_mm", "aft_mm", "pad_fore_mm"]]
    tenth = Fraction(1, 10)
    endplanes = sorted(
        set(
            ticks(fore - Fraction(1, 2), fore + Fraction(1, 2), tenth)
            + ticks(aft - Fraction(1, 2), aft + Fraction(1, 2), tenth)
        )
    )
    cornerplanes = ticks(pad - tenth, fore + tenth, tenth)
    globalplanes = [
        fore + k * 12
        for k in range(
            math.floor((points[:, 2].min() - float(fore)) / 12),
            math.ceil((points[:, 2].max() - float(fore)) / 12) + 1,
        )
    ]
    registry: dict[int, set[Fraction]] = defaultdict(set)
    strip_counts = np.zeros(len(triangles), dtype=np.int64)
    cap_lines = np.zeros((len(triangles), 2), dtype=np.int64)
    cap_interior = np.zeros(len(triangles), dtype=np.int64)
    exact = 0
    selected = (
        masks["global_case_liner"] | masks["local_ends"] | masks["fore_corner"] | masks["planar"]
    )
    for parent_index in np.flatnonzero(selected):
        parent = int(parent_index)
        p = points[triangles[parent]]
        proposed: list[Fraction] = []
        if masks["global_case_liner"][parent]:
            proposed += globalplanes
        # Applying local cuts across the whole selected parent, including its
        # r>=16 portion, is an explicit conservative count construction. It
        # guarantees the r<16 rule without a circular interior cut approximation.
        if masks["local_ends"][parent]:
            proposed += endplanes
        if masks["fore_corner"][parent]:
            proposed += cornerplanes
        zcuts = interior_planes(p[:, 2].min(), p[:, 2].max(), sorted(set(proposed)))
        strip_counts[parent] = len(zcuts)
        insert_planes(parent, 2, zcuts, triangles, points, te, edges, registry)
        if masks["planar"][parent]:
            if np.ptp(p[:, 2]) > 1e-8:
                raise ValueError("Selected cap is not horizontal in the actual PLC")
            for axis in [0, 1]:
                cuts = interior_planes(
                    p[:, axis].min(),
                    p[:, axis].max(),
                    ticks(rational(p[:, axis].min()), rational(p[:, axis].max()), Fraction(1, 2)),
                )
                cap_lines[parent, axis] = len(cuts)
                insert_planes(parent, axis, cuts, triangles, points, te, edges, registry)
            cap_interior[parent], escalations = strict_inside_grid(p, Fraction(1, 2))
            exact += escalations
    edge_counts = np.array([len(registry[i]) for i in range(len(edges))], dtype=np.int64)
    b = edge_counts[te].sum(axis=1)
    added_edge = int(edge_counts.sum())
    added_inside = int(cap_interior.sum())
    predicted_nodes = len(points) + added_edge + added_inside
    predicted_triangles = len(triangles) + int(b.sum()) + 2 * added_inside
    if int(b.sum()) != 2 * added_edge:
        raise ValueError("Shared original-edge counts were not propagated to both parents")
    # Polygon partitions are counts only; no vertices/children are constructed.
    polygons = 1 + strip_counts + cap_lines.sum(axis=1) + cap_interior
    modified = (b > 0) | (cap_interior > 0)
    by_part: dict[str, dict[str, int]] = {}
    by_face: dict[str, dict[str, int]] = {}
    face_group = source["face_to_group"][boundary["triangle_face_index"]]
    for parent_index in np.flatnonzero(modified):
        parent = int(parent_index)
        part = source["groups"][face_group[parent]]["part_id"]
        face = int(boundary["triangle_face_index"][parent]) + 1
        for rows, key in [(by_part, part), (by_face, str(face))]:
            row = rows.setdefault(
                key,
                {
                    "modified_original_parents": 0,
                    "added_boundary_vertex_incidences": 0,
                    "interior_grid_points": 0,
                    "polygon_partitions": 0,
                    "counted_child_triangles": 0,
                },
            )
            row["modified_original_parents"] += 1
            row["added_boundary_vertex_incidences"] += int(b[parent])
            row["interior_grid_points"] += int(cap_interior[parent])
            row["polygon_partitions"] += int(polygons[parent])
            row["counted_child_triangles"] += 1 + int(b[parent]) + 2 * int(cap_interior[parent])
    unselected_neighbors = modified & ~selected
    transition_only = modified & (strip_counts == 0) & (cap_lines.sum(axis=1) == 0)
    old_nodes, old_tets, old_interior = 80186, 427940, 8269
    future_nodes = predicted_nodes + old_interior
    return {
        "status": "read_only_combinatorial_preflight_complete",
        "candidate_mesh_generated": False,
        "source_sha256": source["source_sha256"],
        "source_candidate_identity": source["handoff"]["candidate_identity"],
        "target_selection": {key: value for key, value in selection.items() if key != "masks"},
        "count_construction": {
            "z_planes": "12mm anchored at actual fore station, 0.1mm local planes including one extra interval outside each closed band",
            "local_radius_handling": "conservative whole-parent cuts on selected part masks; no circular clipping, so r>=16mm portions may be overcounted",
            "cap_grid_step_mm": 0.5,
            "cap_cell_diameter_mm": math.sqrt(0.5),
            "original_vertices_and_parent_faces": "retained by construction, not a generated/validated mesh",
            "edge_parameters": "exact rational intersection parameters of original binary64 coordinates with rational plane stations",
            "exact_grid_boundary_escalations": exact,
        },
        "counts": {
            "original_nodes": len(points),
            "original_triangles": len(triangles),
            "unique_original_edges": len(edges),
            "original_face_ids": len(np.unique(boundary["triangle_face_index"])),
            "original_edge_plane_intersections_unique": added_edge,
            "cap_interior_grid_crossings": added_inside,
            "added_nodes": added_edge + added_inside,
            "predicted_nodes": predicted_nodes,
            "predicted_triangles": predicted_triangles,
            "parent_strip_line_segments": int(strip_counts.sum()),
            "parent_cap_line_segments": int(cap_lines.sum()),
            "partitioned_parents": int(modified.sum()),
            "polygon_partitions_on_modified_parents": int(polygons[modified].sum()),
            "unselected_neighbor_parents_receiving_shared_edge_points": int(
                unselected_neighbors.sum()
            ),
            "unselected_neighbor_added_triangle_cost": int(b[unselected_neighbors].sum()),
            "transition_only_parents_without_own_cut_lines": int(transition_only.sum()),
            "transition_only_added_triangle_cost": int(b[transition_only].sum()),
            "nodes_below_120k": predicted_nodes <= 120000,
            "triangles_below_240k": predicted_triangles <= 240000,
            "additional_nodes_allowed_by_joint_boundary_caps": min(
                120000 - len(points), (240000 - len(triangles)) // 2
            ),
        },
        "by_part": by_part,
        "by_original_face_id": by_face,
        "future_volume_resource_analogy_not_bound": {
            "old_coarse_nodes": old_nodes,
            "old_coarse_tetrahedra": old_tets,
            "old_4mm_interior_nodes": old_interior,
            "boundary_plus_same_interior_seed_count": future_nodes,
            "analogy_tetrahedra_by_old_tets_per_node": math.ceil(
                future_nodes * old_tets / old_nodes
            ),
            "analogy_tetrahedra_by_old_tets_per_boundary_triangle": math.ceil(
                predicted_triangles * old_tets / len(triangles)
            ),
            "future_node_cap": 150000,
            "future_tet_cap": 750000,
            "unknown": "actual narrow-gap quality/Steiner points, tet count, positive/scaled volume, embedding, factor memory/time and numerical accuracy; no guarantee from these ratios",
        },
        "limits": [
            "Counts use a conservative specified strip/cap-line arrangement, not an optimum or universal upper bound over all FE-quality requirements.",
            "Simple nondegenerate planar constrained triangulation is presumed; its geometric implementation, child containment, orientation, exact area/volume and all quality guards remain to be executed if authorized.",
            "Shared edge intersections are deduplicated and charged to every incident parent. Extra boundary points can be triangulated within each existing strip/cap cell; no angular refinement cost is included beyond source angular facets.",
            "The 0.5mm square cap grid gives maximum possible in-cell edge sqrt(0.5)mm<1mm, but does not impose a minimum angle; quality refinement/transition costs are unbounded here.",
            "All old optical angular geometry and physical barriers remain the intended union. No CAD projection, parent merging, quadrature transfer, Gmsh, field solve, rays or adoption.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=Path("build/wo03-strip-refinement-preflight-v1")
    )
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        started = time.monotonic()
        fixture = fixtures()
        cfg = yaml.safe_load(Path("configs/studies/wo03-cad-gas-mesh.yaml").read_text())
        result = analyze(load_source(cfg["source"]))
        result["necessary_lower_counts"] = necessary_lower_counts(load_source(cfg["source"]))
        result.update(fixtures=fixture, elapsed_s=time.monotonic() - started)
        (args.output / "counts.json").write_text(json.dumps(result, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "counts": result["counts"],
                    "elapsed_s": result["elapsed_s"],
                },
                indent=2,
            )
        )
        return
    args.output.mkdir(parents=True, exist_ok=False)
    paths = [
        Path(__file__),
        Path("src/analysis/refined_gas_boundary.py"),
        Path("src/analysis/cad_gas_mesh.py"),
        Path("configs/studies/wo03-cad-gas-mesh.yaml"),
    ]
    before = {str(path): sha(path) for path in paths}
    started = time.monotonic()
    with (args.output / "worker.log").open("w") as log:
        try:
            completed = subprocess.run(
                [sys.executable, str(Path(__file__)), "--output", str(args.output), "--worker"],
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=60,
                check=False,
            )
            status = (
                "complete_read_only_counts"
                if completed.returncode == 0
                else "incomplete_or_invalid_read_only_counts"
            )
            code: int | None = completed.returncode
        except subprocess.TimeoutExpired:
            status, code = "incomplete60s_cap", None
    report = {
        "status": status,
        "exit_code": code,
        "elapsed_s": time.monotonic() - started,
        "source_code_sha256": before,
        "inputs_unchanged": before == {str(path): sha(path) for path in paths},
        "one_cpu": True,
        "hard_seconds": 60,
        "generated_mesh": False,
        "Gmsh_PDE_new_rays": False,
        "adoption": False,
    }
    if (args.output / "counts.json").exists():
        report["counts_sha256"] = sha(args.output / "counts.json")
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    if status != "complete_read_only_counts":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
