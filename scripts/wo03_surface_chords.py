"""Bounded actual-material normal-chord halfwall SCREEN, never acceptance.

Screening hypothesis: Fourier h(x)=2*k/d(x), where d is the FIRST exit from
the actual already-owned material component along its inward normal. It is a
local mid-chord path to a lumped component temperature, not a proof of internal
isothermality. DOE-HDBK-1012/2-92 HT-02: plane resistance delta/(k*A).
Three-point positive triangle quadrature preserves PSD wall terms, not validated
gradient/anisotropy physics. No ray is bent, no material is crossed after exit,
and no missing/zero/ambiguous path is replaced with insulation or clipped h.
"""

from __future__ import annotations

import os
from pathlib import Path

for _key in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
    os.environ[_key] = "1"
os.environ.setdefault("XDG_CACHE_HOME", str(Path(__file__).resolve().parents[1] / ".cache"))

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from datetime import UTC, datetime
from itertools import pairwise
from typing import Any

import cadquery as cq
import numpy as np
import yaml
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCP.TopAbs import TopAbs_IN

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ChordField:
    """Exact source-part STEP projection and first-exit intersectors, one CPU."""

    def __init__(self, cfg: dict[str, Any], rows: list[dict[str, Any]]) -> None:
        self.cfg = cfg
        self.rows = {r["fluid_face_id"]: r for r in rows}
        manifest = json.loads((ROOT / cfg["manifest"]).read_text())
        self.source_faces = {}
        self.solids = {}
        self.intersectors = {}
        self.classifiers = {}
        self.assets = {}
        self.calls = 0
        names = {r["part_id"] for r in rows if not r["reservoir"]}
        for part in manifest:
            name = part["part_id"]
            if name not in names:
                continue
            path = (ROOT / cfg["manifest"]).parent / part["step"]
            if sha(path) != part["step_sha256"]:
                raise ValueError(f"Actual source STEP hash changed: {name}")
            self.assets[str(path.relative_to(ROOT))] = part["step_sha256"]
            shape = cq.importers.importStep(str(path)).val()
            self.source_faces[name] = shape.Faces()
            solids = sorted(shape.Solids(), key=lambda s: (*s.Center().toTuple(), s.Volume()))
            for i, solid in enumerate(solids):
                component_id = f"{name}.component_{i}"
                self.solids[component_id] = solid
                hit = IntCurvesFace_ShapeIntersector()
                hit.Load(solid.wrapped, 1e-8)
                self.intersectors[component_id] = hit
                self.classifiers[component_id] = BRepClass3d_SolidClassifier(solid.wrapped)

    def query(self, face_id: int, mesh_point: Any, mesh_gas_normal: Any) -> dict[str, Any]:
        if self.calls >= self.cfg["maximum_queries"]:
            raise RuntimeError("Query cap reached; no complete field")
        self.calls += 1
        row = self.rows[face_id]
        histories = [h for h in row["source_face_history"] if h["part_id"] == row["part_id"]]
        if len(histories) != 1:
            raise ValueError(f"Source-face ancestry ambiguous: {face_id}")
        face = self.source_faces[row["part_id"]][histories[0]["source_face_index"]]
        vertex = cq.Vertex.makeVertex(*mesh_point)
        projection = BRepExtrema_DistShapeShape(vertex.wrapped, face.wrapped)
        projection.Perform()
        if not projection.IsDone() or projection.NbSolution() != 1:
            raise ValueError(f"CAD projection unavailable/ambiguous: {face_id}")
        pnt = projection.PointOnShape2(1)
        point = np.array([pnt.X(), pnt.Y(), pnt.Z()])
        distance = projection.Value()
        bound = (
            self.cfg["source_surface_deflection_mm"] + self.cfg["numerical_geometry_tolerance_mm"]
        )
        if distance > bound:
            raise ValueError(
                f"CAD projection exceeds pinned deflection: face{face_id}, {distance}mm"
            )
        gas_normal = -np.asarray(face.normalAt(cq.Vector(*point)).toTuple())
        alignment = float(np.dot(gas_normal, mesh_gas_normal))
        if alignment < self.cfg["minimum_normal_alignment"]:
            raise ValueError(
                f"Material/gas normal sign or source-face mismatch: {face_id}/{alignment}"
            )
        component = row["component_id"]
        trace: list[bool] = []
        chord = first_exit(
            self.solids[component],
            self.intersectors[component],
            point,
            gas_normal,
            self.cfg,
            classifier=(
                self.classifiers[component]
                if self.cfg.get("use_cached_classifier", False)
                else None
            ),
            classification_trace=trace,
        )
        return {
            "chord_mm": chord,
            "delta_m": chord / 2000,
            "projection_mm": distance,
            "normal_alignment": alignment,
            "inside_signature": trace,
        }


def first_exit(
    solid: Any,
    hit: Any,
    point: Any,
    normal: Any,
    cfg: dict[str, Any],
    *,
    classifier: Any = None,
    classification_trace: list[bool] | None = None,
) -> float:
    """Gas-outward/material-inward sign verified by two sides, never auto-flipped."""
    point, normal = np.asarray(point), np.asarray(normal)
    offset = cfg["probe_offset_mm"]

    def inside(p: Any) -> bool:
        # Exact installed CadQuery shapes.py:4097-4100 semantics. Only loading
        # the immutable source solid once differs; State/OnFace/tol are unchanged.
        if classifier is None:
            result = solid.isInside(cq.Vector(*p), 1e-8)
        else:
            classifier.Perform(gp_Pnt(*p), 1e-8)
            result = classifier.State() == TopAbs_IN or classifier.IsOnAFace()
        if classification_trace is not None:
            classification_trace.append(bool(result))
        return bool(result)

    if not inside(point + offset * normal):
        raise ValueError("Positive normal does not enter owned material")
    if inside(point - offset * normal):
        raise ValueError("Negative normal is not outside owned material")
    hit.Perform(gp_Lin(gp_Pnt(*point), gp_Dir(*normal)), 0, cfg["maximum_normal_chord_mm"])
    roots = sorted(hit.WParameter(i) for i in range(1, hit.NbPnt() + 1))
    positive = [x for x in roots if x > cfg["minimum_normal_chord_mm"]]
    if not positive:
        raise ValueError("No positive first material exit")
    chord = positive[0]
    for fraction in [0.001, 0.25, 0.5, 0.75, 0.999]:
        if not inside(point + fraction * chord * normal):
            raise ValueError("Normal chord crosses an earlier gap/exit")
    return float(chord)


def known_cases(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    slab = cq.Solid.makeBox(20, 30, 4)
    ring = cq.Workplane("XY").circle(20).circle(18).extrude(10).val()
    for name, shape, point, normal, exact in [
        ("slab_inner", slab, [10, 15, 0], [0, 0, 1], 4),
        ("slab_outer", slab, [10, 15, 4], [0, 0, -1], 4),
        ("ring_inner", ring, [18, 0, 5], [1, 0, 0], 2),
        ("ring_outer", ring, [20, 0, 5], [-1, 0, 0], 2),
    ]:
        hit = IntCurvesFace_ShapeIntersector()
        hit.Load(shape.wrapped, 1e-8)
        surface = min(shape.Faces(), key=lambda f: f.distance(cq.Vertex.makeVertex(*point)))
        material_normal = np.asarray(surface.normalAt(cq.Vector(*point)).toTuple())
        outward_dot = float(np.dot(material_normal, normal))
        actual = first_exit(shape, hit, point, normal, cfg)
        cached = BRepClass3d_SolidClassifier(shape.wrapped)
        cached_actual = first_exit(shape, hit, point, normal, cfg, classifier=cached)
        rejected = False
        try:
            first_exit(shape, hit, point, -np.asarray(normal), cfg)
        except ValueError:
            rejected = True
        cached_rejected = False
        try:
            first_exit(shape, hit, point, -np.asarray(normal), cfg, classifier=cached)
        except ValueError:
            cached_rejected = True
        rows.append(
            {
                "id": name,
                "expected_chord_mm": exact,
                "actual_chord_mm": actual,
                "cached_actual_chord_mm": cached_actual,
                "cached_reversed_normal_rejected": cached_rejected,
                "reversed_normal_rejected": rejected,
                "material_outward_dot_gas_outward": outward_dot,
                "passed": abs(actual - exact) < 1e-8
                and abs(cached_actual - actual) < 1e-8
                and cached_rejected
                and rejected
                and abs(outward_dot + 1) < 1e-8,
            }
        )
    if not all(row["passed"] for row in rows):
        raise ValueError("Slab/ring/sign fixture failed")
    return rows


def cross2(a: Any, b: Any) -> float:
    return float(a[0] * b[1] - a[1] * b[0])


def triangle_radial_bounds(xy: Any) -> tuple[float, float]:
    """True radius extrema over a flat triangle, not just its centroid."""
    xy = np.asarray(xy, dtype=float)
    maximum = float(np.linalg.norm(xy, axis=1).max())
    cross = [cross2(xy[(i + 1) % 3] - xy[i], -xy[i]) for i in range(3)]
    if min(cross) >= 0 or max(cross) <= 0:
        return 0.0, maximum
    distances = []
    for i in range(3):
        a, b = xy[i], xy[(i + 1) % 3]
        d = b - a
        fraction = min(1.0, max(0.0, -float(a @ d) / float(d @ d)))
        distances.append(float(np.linalg.norm(a + fraction * d)))
    return min(distances), maximum


def disk_triangle_moments(xy: Any, radius: float) -> np.ndarray:
    """Area and first moments of a planar triangle intersected with a disk.

    Sum signed origin/edge triangles; split each edge at circle intersections.
    Inside pieces give ordinary triangle moments, outside pieces circular-sector
    moments from polar integration. These are exact planar-facet integrals up to
    floating point, NOT exact area of the curved source CAD annulus.
    """
    xy = np.asarray(xy, dtype=float)
    determinant = cross2(xy[1] - xy[0], xy[2] - xy[0])
    if determinant == 0:
        raise ValueError("Degenerate end triangle")
    if determinant < 0:
        xy = xy[[0, 2, 1]]
    area = abs(determinant) / 2
    minimum, maximum = triangle_radial_bounds(xy)
    if radius >= maximum:
        return np.array([area, *(area * xy.mean(axis=0))])
    if radius <= minimum:
        return np.zeros(3)
    contributions = []
    for i in range(3):
        p, q = xy[i], xy[(i + 1) % 3]
        d = q - p
        aa, bb, cc = float(d @ d), float(2 * p @ d), float(p @ p - radius**2)
        discriminant = bb * bb - 4 * aa * cc
        cuts = [0.0, 1.0]
        if discriminant > 0:
            root = math.sqrt(discriminant)
            cuts += [
                value
                for value in [(-bb - root) / (2 * aa), (-bb + root) / (2 * aa)]
                if 0 < value < 1
            ]
        cuts = sorted(cuts)
        for a, b in pairwise(cuts):
            start, end = p + a * d, p + b * d
            midpoint = (start + end) / 2
            cross = cross2(start, end)
            if midpoint @ midpoint <= radius**2:
                signed_area = cross / 2
                contributions.append([signed_area, *(signed_area * (start + end) / 3)])
            else:
                angle = math.atan2(cross, float(start @ end))
                t0, t1 = math.atan2(start[1], start[0]), math.atan2(end[1], end[0])
                contributions.append(
                    [
                        radius**2 * angle / 2,
                        radius**3 / 3 * (math.sin(t1) - math.sin(t0)),
                        radius**3 / 3 * (math.cos(t0) - math.cos(t1)),
                    ]
                )
    return np.array([math.fsum(row[j] for row in contributions) for j in range(3)])


def liner_triangle_basis(xy: Any, radii: Any, deflection_bound_mm: float) -> dict[str, Any]:
    """Full FACET area partition; permitted endpoint-cell extension is explicit."""
    xy, radii = np.asarray(xy, dtype=float), np.asarray(radii, dtype=float)
    area = abs(cross2(xy[1] - xy[0], xy[2] - xy[0])) / 2
    minimum, maximum = triangle_radial_bounds(xy)
    excursion = max(0.0, radii[0] - minimum, maximum - radii[-1])
    if excursion > deflection_bound_mm:
        raise ValueError(f"Liner facet radius excursion exceeds bound: {excursion}mm")
    full = np.array([area, *(area * xy.mean(axis=0))])
    cumulative = [np.zeros(3)]
    cumulative += [disk_triangle_moments(xy, radius) for radius in radii[1:-1]]
    cumulative += [full]
    # Barycentric Ni = ai + bi*x + ci*y; rows of inverse transpose contain ai,bi,ci.
    inverse = np.linalg.inv(np.column_stack((np.ones(3), xy)))
    moments = np.diff(np.asarray(cumulative), axis=0)
    integrals = moments @ inverse
    if (integrals < 0).any() or (moments[:, 0] < 0).any():
        raise ValueError(f"Negative raw strip area/basis integral, no clipping: {integrals.min()}")
    residual = integrals.sum(axis=0) - area / 3
    if np.max(np.abs(residual)) > max(1e-12, area * 1e-8):
        raise ValueError("Strip basis integrals do not cover whole facet")
    inside = disk_triangle_moments(xy, radii[-1]) - disk_triangle_moments(xy, radii[0])
    outside_inner = disk_triangle_moments(xy, radii[0])[0]
    outside_outer = area - disk_triangle_moments(xy, radii[-1])[0]
    return {
        "basis_integrals_m2": integrals * 1e-6,
        "area_by_cell_m2": moments[:, 0] * 1e-6,
        "facet_area_m2": area * 1e-6,
        "actual_annulus_intersection_area_mm2": float(inside[0]),
        "endpoint_projection_assigned_area_mm2": float(outside_inner + outside_outer),
        "signed_area_error_mm2": float(area - inside[0]),
        "absolute_area_error_mm2": abs(float(area - inside[0])),
        "maximum_radius_excursion_mm": excursion,
        "basis_sum_residual_m2": float(np.abs(residual).max() * 1e-6),
    }


def component_capacities(cfg: dict[str, Any], field: ChordField) -> dict[str, Any]:
    """Mass is counted ONCE; capacity splitting is a proposal, never adopted."""
    components = json.loads((ROOT / cfg["baseline_components"]).read_text())
    parts = {p["id"]: p for p in json.loads((ROOT / cfg["candidate"]).read_text())["parts"]}
    materials = yaml.safe_load((ROOT / cfg["engineering"]).read_text())["materials"]
    manifest = {p["part_id"]: p for p in json.loads((ROOT / cfg["manifest"]).read_text())}
    rows = []
    totals = {}
    for name in sorted({c["part_id"] for c in components}):
        part = parts[name]
        subset = [c for c in components if c["part_id"] == name]
        mass = part["mass_kg"]
        if mass is None or mass <= 0:
            raise ValueError(f"Missing physical source-part mass: {name}")
        profile_id = part["engineering"]["material_profile"]
        profile = materials[profile_id]
        volume = sum(c["volume_m3"] for c in subset)
        for component in subset:
            cid = component["component_id"]
            solid = field.solids[cid]
            box = solid.BoundingBox()
            fraction = component["volume_m3"] / volume
            cmass = mass * fraction
            face_indices = [
                j
                for j, f in enumerate(field.source_faces[name])
                if any(f.wrapped.IsSame(s.wrapped) for s in solid.Faces())
            ]
            states = [{"bulk_id": cid, "mass_kg": cmass}]
            if name == "motor_liner":
                strips = next(
                    r["halfwall"]["explicit_axial_FV_paths"]
                    for r in field.rows.values()
                    if r["mapping_kind"] == "radial_FV_end_strips_coarse_axial_hypothesis"
                )
                area = sum(strip["area_m2"] for strip in strips)
                states = [
                    {
                        "bulk_id": strip["material_state_id"],
                        "mass_kg": cmass * strip["area_m2"] / area,
                    }
                    for strip in strips
                ]
            for state in states:
                state["capacity_j_k"] = (
                    None if name == "motor" else state["mass_kg"] * profile["cp_j_kg_k"]
                )
            rows.append(
                {
                    **component,
                    "proposed_bulk_states": states,
                    "component_mass_kg": cmass,
                    "source_part_mass_kg": mass,
                    "source_part_mass_fraction": fraction,
                    "mass_allocation": "homogeneous actual component volume fraction; purchased-envelope split unverified",
                    "material_profile": profile_id,
                    "cp_j_kg_k": None if name == "motor" else profile["cp_j_kg_k"],
                    "cp_range_j_kg_k": (
                        None
                        if name == "motor"
                        else profile.get(
                            "cp_range_j_kg_k",
                            [0.7 * profile["cp_j_kg_k"], 1.3 * profile["cp_j_kg_k"]],
                        )
                    ),
                    "prescribed_motor_has_no_finite_capacity_in_this_boundary_model": name
                    == "motor",
                    "source_step": str(Path(cfg["manifest"]).parent / manifest[name]["step"]),
                    "source_step_sha256": manifest[name]["step_sha256"],
                    "source_part_face_indices_zero_based": face_indices,
                    "actual_component_bbox_mm_FOR_CONTACT_CULLING_ONLY": [
                        box.xmin,
                        box.xmax,
                        box.ymin,
                        box.ymax,
                        box.zmin,
                        box.zmax,
                    ],
                    "bbox_used_for_halfwall": False,
                    "capacity_split_adopted": False,
                    "contact_routing": "primary must prove actual touching component pairs/areas before allocating old part-level contacts; no automatic division or replication",
                }
            )
        totals[name] = {
            "source_mass_kg": mass,
            "allocated_mass_kg": sum(r["component_mass_kg"] for r in rows if r["part_id"] == name),
        }
    error = max(abs(t["source_mass_kg"] - t["allocated_mass_kg"]) for t in totals.values())
    if error > 1e-12:
        raise ValueError("Component mass ledger does not conserve source mass")
    return {
        "components": rows,
        "part_mass_totals": totals,
        "maximum_part_mass_residual_kg": error,
        "total_covered_source_part_mass_kg": sum(t["source_mass_kg"] for t in totals.values()),
        "total_allocated_component_mass_kg": sum(r["component_mass_kg"] for r in rows),
        "whole_vehicle_mass_kg": sum(p["mass_kg"] for p in parts.values()),
        "parts_not_intersecting_selected_gas_domain": sorted(set(parts) - set(totals)),
        "component_count": len(rows),
        "capacity_split_adopted": False,
    }


def write_json(path: Path, data: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    temporary.replace(path)


def quadrature_wall(area_m2: float, h_values: Any, barycentric: Any) -> tuple[Any, Any, Any]:
    """Positive three-point wall rule: exact constant-h mass, raw PSD energy."""
    h_values, basis = np.asarray(h_values), np.asarray(barycentric)
    if area_m2 <= 0 or np.min(h_values) <= 0 or basis.shape != (3, 3):
        raise ValueError("Positive wall area/h and three triangle basis points required")
    weights = h_values * area_m2 / 3
    return np.einsum("q,qi,qj->ij", weights, basis, basis), weights @ basis, weights.sum()


def paired_cache_benchmark(
    cfg: dict[str, Any], rows: Any, arrays: Any, sources: Any, output: Path, started: float
) -> None:
    """One exact same-point classifier-cache comparison, no operator creation."""
    field = ChordField(cfg, rows)
    sources.update(field.assets)
    fixtures = known_cases(cfg)
    faces = {r["fluid_face_id"]: r for r in rows}
    face_ids = arrays["triangle_face_index"] + 1
    unavailable = np.array(
        [
            i
            for i, f in enumerate(face_ids)
            if faces[int(f)]["mapping_kind"] == "unavailable_halfwall_mapping"
        ]
    )
    selection = unavailable[
        np.linspace(0, len(unavailable) - 1, cfg["benchmark_queries"], dtype=int)
    ]
    setup = time.monotonic() - started
    timings, results = {}, {}
    for method, use_cache in [("original", False), ("cached", True)]:
        field.cfg["use_cached_classifier"] = use_cache
        timer = time.monotonic()
        values = []
        for i in selection:
            point = arrays["vertices_mm"][arrays["triangles"][i]].mean(axis=0)
            values.append(
                field.query(int(face_ids[i]), point, arrays["outward_triangle_normal"][i])
            )
        timings[method] = time.monotonic() - timer
        results[method] = values
    chord_error = max(
        abs(a["chord_mm"] - b["chord_mm"])
        for a, b in zip(results["original"], results["cached"], strict=True)
    )
    projection_error = max(
        abs(a["projection_mm"] - b["projection_mm"])
        for a, b in zip(results["original"], results["cached"], strict=True)
    )
    signs_match = all(
        a["inside_signature"] == b["inside_signature"]
        for a, b in zip(results["original"], results["cached"], strict=True)
    )
    overhead = max(setup, 64.27642037499754)
    projected = overhead + timings["cached"] / len(selection) * (4 * len(unavailable)) + 5
    passed = chord_error <= 1e-7 and projection_error <= 1e-7 and signs_match and projected <= 1200
    source = ROOT / ".venv/lib/python3.11/site-packages/cadquery/occ_impl/shapes.py"
    sources[str(source.relative_to(ROOT))] = sha(source)
    record = {
        "status": (
            "EXACT_CLASSIFIER_CACHE_BENCHMARK_PASSED"
            if passed
            else "CACHE_BENCHMARK_INSUFFICIENT_STOP"
        ),
        "source_sha256": sources,
        "known_cases": fixtures,
        "same_points": len(selection),
        "timings_seconds": timings,
        "maximum_chord_difference_mm": chord_error,
        "maximum_projection_difference_mm": projection_error,
        "inside_signatures_identical": signs_match,
        "original_predicate": "State()==TopAbs_IN or IsOnAFace(), tolerance1e-8mm; installedCadQuery shapes.py4097-4100",
        "only_API_change": "one BRepClass3d_SolidClassifier per immutable component reused with Perform; same source geometry/points/tolerances/predicate",
        "setup_elapsed_s": setup,
        "projection_overhead_s": overhead,
        "projected_full_level_seconds_including_overhead": projected,
        "restart_gate_seconds": 1200,
        "queries_required_full": 4 * len(unavailable),
        "query_comparisons_this_benchmark": field.calls,
        "full_operator_available": False,
        "temperature_solve_executed": False,
        "acceptance": False,
        "inputs_unchanged": all(sha(Path(p)) == value for p, value in sources.items()),
        "elapsed_s": time.monotonic() - started,
        "cpu_workers": 1,
        "cost_usd": 0,
    }
    write_json(
        output / "paired-cache-query-results.json",
        {"original_triangle_indices": selection.tolist(), **results},
    )
    write_json(output / "record.json", record)
    print(
        json.dumps(
            {
                "output": str(output.relative_to(ROOT)),
                **{
                    k: record[k]
                    for k in [
                        "status",
                        "timings_seconds",
                        "maximum_chord_difference_mm",
                        "inside_signatures_identical",
                        "projected_full_level_seconds_including_overhead",
                    ]
                },
            },
            indent=2,
        ),
        flush=True,
    )


def run_full(
    cfg: dict[str, Any],
    rows: list[dict[str, Any]],
    arrays: dict[str, Any],
    sources: dict[str, str],
    output: Path,
    started: float,
    *,
    preflight_only: bool = False,
) -> None:
    """One full level, positive wall quadrature, hard runtime/query stop."""
    cfg = dict(cfg)
    cfg["maximum_queries"] = cfg["authorized_full_level_queries"]
    field = ChordField(cfg, rows)
    sources.update(field.assets)
    fixtures = known_cases(cfg)
    ledger = component_capacities(cfg, field)
    write_json(output / "component-capacity-ledger.json", ledger)
    by_face = {r["fluid_face_id"]: r for r in rows}
    vertices, triangles = arrays["vertices_mm"], arrays["triangles"]
    face_ids = arrays["triangle_face_index"] + 1
    normals, areas = arrays["outward_triangle_normal"], arrays["triangle_area_mm2"] * 1e-6
    kinds = [by_face[int(fid)]["mapping_kind"] for fid in face_ids]
    robin_triangles = np.array(
        [
            i
            for i, kind in enumerate(kinds)
            if kind not in {"external_opening", "prescribed_motor_surface"}
        ]
    )
    unavailable_count = kinds.count("unavailable_halfwall_mapping")
    required = 4 * unavailable_count
    state_ids = sorted(
        state["bulk_id"]
        for comp in ledger["components"]
        for state in comp["proposed_bulk_states"]
        if state["capacity_j_k"] is not None
    )
    if len(state_ids) != len(set(state_ids)):
        raise ValueError("Duplicate proposed finite-capacity bulk IDs")
    state_index = {name: i for i, name in enumerate(state_ids)}
    matrices = np.full((len(robin_triangles), 3, 3), np.nan)
    loads = np.full((len(robin_triangles), 3), np.nan)
    diagonals = np.full(len(robin_triangles), np.nan)
    bulk_indices = np.full(len(robin_triangles), -1, dtype=np.int32)
    chord_samples = np.full((unavailable_count, 4), np.nan)
    projections = np.full((unavailable_count, 4), np.nan)
    scalar_h = np.full(len(robin_triangles), np.nan)
    property_factors = np.full((len(robin_triangles), 2), np.nan)
    liner_local_indices, liner_loads, liner_diagonals = [], [], []
    liner_diagnostics = []
    quadrature = np.asarray(cfg["triangle_quadrature_barycentric"])
    exact_mass = (np.eye(3) + np.ones((3, 3))) / 12
    liner_rows = [
        r for r in rows if r["mapping_kind"] == "radial_FV_end_strips_coarse_axial_hypothesis"
    ]
    strips = liner_rows[0]["halfwall"]["explicit_axial_FV_paths"]
    radii = (
        np.array(
            [
                strips[0]["radial_interval_m"][0],
                *[strip["radial_interval_m"][1] for strip in strips],
            ]
        )
        * 1000
    )
    bound = cfg["source_surface_deflection_mm"] + cfg["numerical_geometry_tolerance_mm"]
    # Validate every radial end triangle BEFORE the long chord loop. No centroid
    # cell assignment, lost area or invented material state at shared nodes.
    for local_i, triangle_i in enumerate(robin_triangles):
        if kinds[triangle_i] != "radial_FV_end_strips_coarse_axial_hypothesis":
            continue
        row = by_face[int(face_ids[triangle_i])]
        result = liner_triangle_basis(vertices[triangles[triangle_i], :2], radii, bound)
        h = row["h_nominal_w_m2_k"]
        matrices[local_i] = h * areas[triangle_i] * exact_mass
        liner_local_indices.append(local_i)
        liner_loads.append(h * result.pop("basis_integrals_m2"))
        liner_diagonals.append(h * result.pop("area_by_cell_m2"))
        liner_diagnostics.append(
            {
                "triangle_index": int(triangle_i),
                "fluid_face_id": int(face_ids[triangle_i]),
                **result,
            }
        )
    write_json(output / "liner-facet-projection.json", liner_diagnostics)
    base_record = {
        "stage": "preflight" if preflight_only else "full",
        "source_sha256": sources,
        "known_cases": fixtures,
        "preserved_300s_capped_benchmark": cfg["benchmark_record"],
        "full_level_authorized_seconds": cfg["authorized_full_level_seconds"],
        "full_level_authorized_queries": cfg["authorized_full_level_queries"],
        "queries_required": required,
        "triangle_count": len(triangles),
        "Robin_triangle_count": len(robin_triangles),
        "liner_triangle_count": len(liner_diagnostics),
        "capacity_ledger": "component-capacity-ledger.json",
        "component_count": ledger["component_count"],
        "finite_bulk_state_count": len(state_ids),
        "maximum_part_mass_residual_kg": ledger["maximum_part_mass_residual_kg"],
        "capacity_split_adopted": False,
        "temperature_solve_executed": False,
        "acceptance": False,
        "unresolved_internal_gradients": True,
        "directional_conductivity_measured": False,
        "cpu_workers": 1,
        "cost_usd": 0,
    }
    if preflight_only or required > cfg["authorized_full_level_queries"]:
        write_json(
            output / "record.json",
            {
                **base_record,
                "status": "PREFLIGHT_ONLY" if preflight_only else "QUERY_CAP_BEFORE_FULL_LEVEL",
                "full_level_executed": False,
                "inputs_unchanged": all(sha(Path(p)) == value for p, value in sources.items()),
                "elapsed_s": time.monotonic() - started,
            },
        )
        print(output.relative_to(ROOT), flush=True)
        return
    completed, unknown_i, failure = 0, 0, None
    checkpoint = -1
    try:
        for local_i, triangle_i in enumerate(robin_triangles):
            if time.monotonic() - started > cfg["authorized_full_level_seconds"]:
                raise RuntimeError("Full-level1500s runtime cap reached")
            row = by_face[int(face_ids[triangle_i])]
            profile = row["conductivity"]
            property_factors[local_i] = (
                np.asarray(profile["bounds_w_m_k"]) / profile["nominal_w_m_k"]
            )
            kind = kinds[triangle_i]
            if kind == "radial_FV_end_strips_coarse_axial_hypothesis":
                scalar_h[local_i] = row["h_nominal_w_m2_k"]
                completed += 1
                continue
            bulk_id = row["halfwall"].get("bulk_state_override", row["component_id"])
            bulk_indices[local_i] = state_index[bulk_id]
            if kind == "finite_solid_halfwall":
                h = row["h_nominal_w_m2_k"]
                scalar_h[local_i] = h
                matrices[local_i] = h * areas[triangle_i] * exact_mass
                loads[local_i] = h * areas[triangle_i] / 3
                diagonals[local_i] = h * areas[triangle_i]
            else:
                coords = vertices[triangles[triangle_i]]
                barycentric = np.vstack(([1 / 3] * 3, quadrature))
                samples = [
                    field.query(int(face_ids[triangle_i]), bary @ coords, normals[triangle_i])
                    for bary in barycentric
                ]
                chord_samples[unknown_i] = [s["chord_mm"] for s in samples]
                projections[unknown_i] = [s["projection_mm"] for s in samples]
                hq = profile["nominal_w_m_k"] / np.array([s["delta_m"] for s in samples[1:]])
                matrices[local_i], loads[local_i], diagonals[local_i] = quadrature_wall(
                    areas[triangle_i], hq, quadrature
                )
                unknown_i += 1
            completed += 1
            if field.calls // 1000 != checkpoint:
                checkpoint = field.calls // 1000
                write_json(
                    output / "progress.json",
                    {
                        "status": "RUNNING",
                        "completed_Robin_triangles": completed,
                        "total_Robin_triangles": len(robin_triangles),
                        "queries": field.calls,
                        "query_cap": cfg["authorized_full_level_queries"],
                        "elapsed_s": time.monotonic() - started,
                        "runtime_cap_s": cfg["authorized_full_level_seconds"],
                        "complete_operator_available": False,
                    },
                )
    except (ValueError, RuntimeError) as exc:
        failure = str(exc)
    complete = failure is None and completed == len(robin_triangles)
    record = {
        **base_record,
        "status": (
            "COMPLETE_CHORD_SCREEN_NOT_ACCEPTANCE"
            if complete
            else "CAPPED_OR_BLOCKED_PARTIAL_CHORD_SCREEN"
        ),
        "failure": failure,
        "completed_Robin_triangles": completed,
        "queries": field.calls,
        "full_level_executed": complete,
        "inputs_unchanged": all(sha(Path(p)) == value for p, value in sources.items()),
        "elapsed_s": time.monotonic() - started,
    }
    if complete:
        liner_set = set(liner_local_indices)
        ordinary = np.array([i for i in range(len(robin_triangles)) if i not in liner_set])
        conservation = max(
            float(np.abs(matrices[ordinary].sum(axis=2) - loads[ordinary]).max()),
            float(np.abs(loads[ordinary].sum(axis=1) - diagonals[ordinary]).max()),
        )
        quadrature_chords = chord_samples[:, 1:]
        variation = quadrature_chords.max(axis=1) / quadrature_chords.min(axis=1)
        record.update(
            maximum_ordinary_wall_conservation_residual_w_k=conservation,
            maximum_threepoint_chord_ratio=float(variation.max()),
            threepoint_chord_ratio_percentiles={
                str(p): float(np.percentile(variation, p)) for p in [50, 90, 95, 99, 100]
            },
            maximum_sample_projection_mm=float(projections.max()),
            minimum_chord_mm=float(chord_samples.min()),
            maximum_chord_mm=float(chord_samples.max()),
            liner_max_radius_excursion_mm=max(
                d["maximum_radius_excursion_mm"] for d in liner_diagnostics
            ),
            liner_endpoint_projection_assigned_area_mm2=sum(
                d["endpoint_projection_assigned_area_mm2"] for d in liner_diagnostics
            ),
            liner_signed_area_error_mm2=sum(d["signed_area_error_mm2"] for d in liner_diagnostics),
            liner_absolute_area_error_mm2=sum(
                d["absolute_area_error_mm2"] for d in liner_diagnostics
            ),
        )
        np.savez_compressed(
            output / "wall-quadrature-screen.npz",
            original_triangle_indices=robin_triangles,
            original_CAD_face_ids=face_ids[robin_triangles],
            radiation_group_ids=np.array(
                [by_face[int(fid)]["radiation_group_id"] for fid in face_ids[robin_triangles]]
            ),
            wall_matrix_w_k=matrices,
            bulk_load_vector_w_k=loads,
            bulk_diagonal_w_k=diagonals,
            bulk_index=bulk_indices,
            scalar_recipe_h_w_m2_k=scalar_h,
            material_property_factors=property_factors,
            liner_Robin_local_indices=np.array(liner_local_indices),
            liner_bulk_indices=np.array([state_index[s["material_state_id"]] for s in strips]),
            liner_bulk_load_vectors_w_k=np.asarray(liner_loads),
            liner_bulk_diagonals_w_k=np.asarray(liner_diagonals),
            unknown_chord_samples_mm=chord_samples,
            unknown_sample_projection_mm=projections,
            unknown_original_triangle_indices=np.array(
                [i for i, kind in enumerate(kinds) if kind == "unavailable_halfwall_mapping"]
            ),
        )
        write_json(
            output / "wall-map-metadata.json",
            {
                "bulk_state_ids": state_ids,
                "scalar_recipe_NaN_means_variable_h_or_non_scalar_path": True,
                "ordinary_bulk_index_minus_one_means_explicit_liner_multi_bulk_terms": True,
                "liner_ordinary_B_D_NaN_are_unused_not_missing": True,
                "Robin_matrix_and_load_terms_are_preintegrated_W_per_K": True,
                "variable_h_quadrature": cfg["triangle_quadrature_barycentric"],
                "centroid_sample_used_in_matrix": False,
                "Dirichlet_faces": [
                    {
                        "fluid_face_id": r["fluid_face_id"],
                        "radiation_group_id": r["radiation_group_id"],
                        "temperature_id": r.get("gas_temperature_id", r.get("temperature_id")),
                        "radiative_brightness_id": r.get("radiative_brightness_id"),
                        "input_value_available": r.get("source_temperature_available", False),
                    }
                    for r in rows
                    if r["mapping_kind"] in {"external_opening", "prescribed_motor_surface"}
                ],
                "no_actual_temperature_solve": True,
                "screening_only": True,
                "source_frozen_map": cfg["baseline_faces"],
                "radiation_groups_unchanged_no_new_optical_rays": True,
            },
        )
        record["operator_sha256"] = sha(output / "wall-quadrature-screen.npz")
    write_json(output / "record.json", record)
    write_json(
        output / "progress.json",
        {
            "status": record["status"],
            "queries": field.calls,
            "elapsed_s": record["elapsed_s"],
            "complete_operator_available": complete,
        },
    )
    print(
        json.dumps(
            {
                "output": str(output.relative_to(ROOT)),
                **{key: record[key] for key in ["status", "failure", "queries", "elapsed_s"]},
            },
            indent=2,
        ),
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/studies/wo03-surface-chords.yaml")
    parser.add_argument(
        "--stage",
        choices=["benchmark", "cache-benchmark", "preflight", "full"],
        default="benchmark",
    )
    parser.add_argument("--supervise", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    os.chdir(ROOT)
    started = time.monotonic()
    cfg = yaml.safe_load(Path(args.config).read_text())
    output = (
        ROOT / args.output
        if args.output
        else ROOT
        / "runs"
        / ("wo03-surface-chords-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"))
    )
    if args.supervise:
        if args.stage != "full":
            raise ValueError("Only the authorized full level uses supervision")
        output.mkdir(parents=True)
        command = [
            sys.executable,
            "-u",
            str(Path(__file__)),
            "--config",
            args.config,
            "--stage",
            "full",
            "--output",
            str(output.relative_to(ROOT)),
        ]
        print(
            json.dumps(
                {
                    "supervised_output": str(output.relative_to(ROOT)),
                    "hard_timeout_s": cfg["authorized_full_level_seconds"],
                }
            ),
            flush=True,
        )
        with (output / "worker.log").open("w") as log:
            child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            write_json(
                output / "supervisor.json",
                {
                    "pid": child.pid,
                    "hard_timeout_s": cfg["authorized_full_level_seconds"],
                    "command": command,
                },
            )
            try:
                code = child.wait(timeout=cfg["authorized_full_level_seconds"])
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
                write_json(
                    output / "supervisor-stop.json",
                    {
                        "status": "HARD_1500S_CAP_NO_COMPLETE_OPERATOR",
                        "elapsed_s": time.monotonic() - started,
                    },
                )
                return
        print(
            json.dumps({"output": str(output.relative_to(ROOT)), "worker_exit_code": code}),
            flush=True,
        )
        return
    sources = {
        args.config: sha(Path(args.config)),
        str(Path(__file__).relative_to(ROOT)): sha(Path(__file__)),
    }
    for key, expected in cfg["expected_sha256"].items():
        path = Path(cfg[key])
        if sha(path) != expected:
            raise ValueError(f"Pinned input changed: {key}")
        sources[str(path)] = expected
    rows = json.loads(Path(cfg["baseline_faces"]).read_text())
    by_id = {row["fluid_face_id"]: row for row in rows}
    with np.load(cfg["boundary"]) as data:
        arrays = {key: data[key] for key in data.files}
        vertices = data["vertices_mm"]
        triangles = data["triangles"]
        face_ids = data["triangle_face_index"] + 1
        normals = data["outward_triangle_normal"]
    if args.stage == "cache-benchmark":
        output.mkdir(parents=True, exist_ok=True)
        paired_cache_benchmark(cfg, rows, arrays, sources, output, started)
        return
    if args.stage != "benchmark":
        if cfg.get("use_cached_classifier", False):
            proof = json.loads(Path(cfg["cache_benchmark_record"]).read_text())
            if (
                proof["status"] != "EXACT_CLASSIFIER_CACHE_BENCHMARK_PASSED"
                or proof["projected_full_level_seconds_including_overhead"] > 1200
            ):
                raise ValueError("Exact-cache restart gate not satisfied")
        output.mkdir(parents=True, exist_ok=True)
        try:
            run_full(
                cfg,
                rows,
                arrays,
                sources,
                output,
                started,
                preflight_only=args.stage == "preflight",
            )
        except (ValueError, RuntimeError) as exc:
            write_json(
                output / "record.json",
                {
                    "status": "BLOCKED_PREFLIGHT_NO_COMPLETE_FIELD",
                    "failure": str(exc),
                    "source_sha256": sources,
                    "temperature_solve_executed": False,
                    "acceptance": False,
                    "elapsed_s": time.monotonic() - started,
                },
            )
            raise
        return
    unavailable = np.array(
        [
            i
            for i, face_id in enumerate(face_ids)
            if by_id[int(face_id)]["mapping_kind"] == "unavailable_halfwall_mapping"
        ]
    )
    queries_required = 4 * len(unavailable)
    field = ChordField(cfg, rows)
    sources.update(field.assets)
    fixtures = known_cases(cfg)
    selection = unavailable[
        np.linspace(0, len(unavailable) - 1, cfg["benchmark_queries"], dtype=int)
    ]
    timer = time.monotonic()
    results = []
    failure = None
    try:
        for i in selection:
            point = vertices[triangles[i]].mean(axis=0)
            results.append(field.query(int(face_ids[i]), point, normals[i]))
    except (ValueError, RuntimeError) as exc:
        failure = str(exc)
    elapsed = time.monotonic() - timer
    projected = elapsed / max(field.calls, 1) * queries_required
    record = {
        "stage": args.stage,
        "status": (
            "BENCHMARK_PASSED"
            if failure is None
            and projected <= cfg["maximum_level_seconds"]
            and queries_required <= cfg["maximum_queries"]
            else "CAPPED_OR_BLOCKED_BEFORE_FULL_LEVEL"
        ),
        "source_sha256": sources,
        "inputs_unchanged": all(sha(Path(p)) == value for p, value in sources.items()),
        "known_cases": fixtures,
        "triangle_count": len(triangles),
        "unavailable_triangles": len(unavailable),
        "queries_required": queries_required,
        "benchmark_completed_queries": len(results),
        "benchmark_attempted_queries": field.calls,
        "benchmark_seconds": elapsed,
        "projected_full_query_seconds": projected,
        "failure": failure,
        "maximum_projection_mm": max((r["projection_mm"] for r in results), default=None),
        "minimum_normal_alignment": min((r["normal_alignment"] for r in results), default=None),
        "maximum_level_seconds": cfg["maximum_level_seconds"],
        "maximum_queries": cfg["maximum_queries"],
        "full_level_executed": False,
        "temperature_solve_executed": False,
        "acceptance": False,
        "cpu_workers": 1,
        "cost_usd": 0,
        "elapsed_s": time.monotonic() - started,
    }
    output = (
        ROOT / "runs" / ("wo03-surface-chords-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"))
    )
    output.mkdir(parents=True)
    (output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "run_dir": str(output.relative_to(ROOT)),
                **{
                    k: record[k]
                    for k in [
                        "status",
                        "unavailable_triangles",
                        "queries_required",
                        "benchmark_completed_queries",
                        "benchmark_seconds",
                        "projected_full_query_seconds",
                        "failure",
                    ]
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
