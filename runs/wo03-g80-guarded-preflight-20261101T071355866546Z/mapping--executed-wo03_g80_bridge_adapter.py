"""Case-specific G80 bridge-to-CalculiX input adapter (no solver invocation)."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "build/wo03-g80-keeper-service-v1"
BRIDGE = SOURCE / "bridge.step"
RAIL_REFERENCE = SOURCE / "modified_mount.step"
WASHERS = [SOURCE / f"washer_{i}.step" for i in range(3)]
GEOMETRY_PREFLIGHT = ROOT / "build/wo03-g80-bridge-fea-v1/geometry-preflight.json"
FILM_RECIPE = ROOT / "build/wo03-g80-bridge-fea-v1/geometry-executed.py"
TET_ORDER_SOURCE = ROOT / "src/analysis/support_fea.py"

EXPECTED_SHA256 = {
    "bridge": "f92832b8cf272ef0f4a2f38b6e62312321b80f899e7efba98a004879806408ed",
    "modified_mount_reference": "8f88eeeb8c41e2f19b4c9b8ad9eb42a7ece433814ed9f079f9ac2b6c0ae50a14",
    "washer_0": "acf7cf97bee7d38d74cc5e3dbe1b655fab56b3c969b21716a50203f59b46fac2",
    "washer_1": "890a1ce02c81d9ae9e79b4a852e05c86367b19325d73cc333e25668a8789d96b",
    "washer_2": "95d24c89b863bc5221e99e6c3aac5d27eccf2b2824b2f76349a0d4d12ba67f47",
    "geometry_preflight": "52abfc4af9c47017ef0caa628f5517a8a41c2042daba483ab787ce996e387dcd",
    "film_recipe_source": "f4124ec5932bd648306f16426d19a28118a8d4d4d0419dc0da5fc89960e68a05",
    "tet_order_source": "1554ff852289a32701ca7b57d5b4843910fd484c6b12c005295e79844bedc695",
}

FILM_ANGLES_DEG = (0.0, 120.0, 240.0)
WASHER_ANGLES_DEG = (60.0, 180.0, 300.0)
WASHER_RADIUS_MM = 25.5
PATCH_AREAS_MM2 = (54.53804846631881, 54.53804846631885, 54.53804846631881)
FILM_BRIDGE_AREA_MM2 = 99.2538877015
FILM_RAIL_AREA_MM2 = 99.5408306980
FILM_VOLUME_MM3 = 9.93977689015
BRIDGE_E_MPA = 10_000.0
EPOXY_E_MPA = 100.0
POISSON = 0.3


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    """Return and verify the exact BRep/recipe/order inputs used by this adapter."""
    paths = {
        "bridge": BRIDGE,
        "modified_mount_reference": RAIL_REFERENCE,
        "washer_0": WASHERS[0],
        "washer_1": WASHERS[1],
        "washer_2": WASHERS[2],
        "geometry_preflight": GEOMETRY_PREFLIGHT,
        "film_recipe_source": FILM_RECIPE,
        "tet_order_source": TET_ORDER_SOURCE,
    }
    actual = {name: sha256(path) for name, path in paths.items()}
    mismatches = {
        name: (EXPECTED_SHA256[name], value)
        for name, value in actual.items()
        if value != EXPECTED_SHA256[name]
    }
    if mismatches:
        raise ValueError(f"Pinned bridge adapter input hash mismatch: {mismatches}")
    return actual


def _quadratic_shape_functions(xi: float, eta: float) -> tuple[float, ...]:
    l1, l2, l3 = 1.0 - xi - eta, xi, eta
    return (
        l1 * (2 * l1 - 1),
        l2 * (2 * l2 - 1),
        l3 * (2 * l3 - 1),
        4 * l1 * l2,
        4 * l2 * l3,
        4 * l3 * l1,
    )


def quadratic_surface_weights(
    triangles: Iterable[Iterable[int]],
    coords: dict[int, np.ndarray],
    local_points: Iterable[float],
    quadrature_weights: Iterable[float],
    jacobian_determinants: Iterable[float],
) -> tuple[dict[int, float], float]:
    """Integrate six-node triangle shape functions using Gmsh surface Jacobians.

    Gmsh type-9 node order is the 3 corners followed by midsides 1-2, 2-3,
    3-1. ``jacobian_determinants`` is element-major, then quadrature point.
    The returned nodal weights have units mm2 and sum to the physical area.
    """
    points = np.asarray(tuple(local_points), dtype=float).reshape(-1, 2)
    qweights = np.asarray(tuple(quadrature_weights), dtype=float)
    jac = np.asarray(tuple(jacobian_determinants), dtype=float)
    elems = [tuple(int(n) for n in tri) for tri in triangles]
    if not elems or len(points) != len(qweights) or len(jac) != len(elems) * len(points):
        raise ValueError("Quadratic triangle quadrature dimensions are inconsistent")
    if any(len(tri) != 6 for tri in elems) or not np.isfinite(jac).all() or np.any(jac <= 0):
        raise ValueError("Expected positive Jacobians for six-node surface triangles")
    weights: dict[int, float] = {}
    for elem_index, tri in enumerate(elems):
        for q_index, ((xi, eta), qweight) in enumerate(zip(points, qweights, strict=True)):
            da = float(qweight * jac[elem_index * len(points) + q_index])
            for node, shape in zip(
                tri, _quadratic_shape_functions(float(xi), float(eta)), strict=True
            ):
                weights[node] = weights.get(node, 0.0) + float(shape * da)
    area = float(sum(weights.values()))
    if not math.isfinite(area) or area <= 0:
        raise ValueError("Integrated quadratic surface has nonpositive area")
    return weights, area


def quadratic_surface_loads(
    triangles: Iterable[Iterable[int]],
    coords: dict[int, np.ndarray],
    local_points: Iterable[float],
    quadrature_weights: Iterable[float],
    jacobian_determinants: Iterable[float],
    traction,
) -> tuple[dict[int, np.ndarray], float]:
    """Integrate a spatially varying traction against quadratic surface shapes."""
    points = np.asarray(tuple(local_points), dtype=float).reshape(-1, 2)
    qweights = np.asarray(tuple(quadrature_weights), dtype=float)
    jac = np.asarray(tuple(jacobian_determinants), dtype=float)
    elems = [tuple(int(n) for n in tri) for tri in triangles]
    if not elems or len(points) != len(qweights) or len(jac) != len(elems) * len(points):
        raise ValueError("Quadratic triangle quadrature dimensions are inconsistent")
    if any(len(tri) != 6 for tri in elems) or not np.isfinite(jac).all() or np.any(jac <= 0):
        raise ValueError("Expected positive Jacobians for six-node surface triangles")
    nodal: dict[int, np.ndarray] = {}
    area = 0.0
    for elem_index, tri in enumerate(elems):
        for q_index, ((xi, eta), qweight) in enumerate(zip(points, qweights, strict=True)):
            shape = np.asarray(_quadratic_shape_functions(float(xi), float(eta)))
            xyz = sum((coords[n] * shape[j] for j, n in enumerate(tri)), np.zeros(3))
            da = float(qweight * jac[elem_index * len(points) + q_index])
            traction_xyz = np.asarray(traction(xyz), dtype=float)
            if traction_xyz.shape != (3,) or not np.isfinite(traction_xyz).all():
                raise ValueError("Traction function must return a finite three-vector")
            area += da
            for j, node in enumerate(tri):
                nodal[node] = nodal.get(node, np.zeros(3)) + shape[j] * traction_xyz * da
    if not math.isfinite(area) or area <= 0:
        raise ValueError("Integrated quadratic surface has nonpositive area")
    return nodal, area


def equilibrated_washer_loads(
    triangles,
    coords,
    local_points,
    quadrature_weights,
    jacobian_determinants,
    exact_center,
    max_relative_correction=0.005,
    diagnostic=None,
):
    """Unit axial resultant with affine pressure and exact prescribed first moment.

    A quadratic-triangle Bernstein enclosure bounds pressure across the complete
    discrete patch, rather than merely sampling quadrature or nodal points.
    """
    triangles = [tuple(map(int, tri)) for tri in triangles]
    center = np.asarray(exact_center, dtype=float)
    if center.shape != (3,) or not np.isfinite(center).all():
        raise ValueError("Invalid exact washer center")
    baseline, area = quadratic_surface_weights(
        triangles, coords, local_points, quadrature_weights, jacobian_determinants
    )
    mesh_center = sum((coords[n] * w for n, w in baseline.items()), np.zeros(3)) / area
    scale = math.sqrt(area)
    basis = lambda x: np.array([1.0, (x[0] - center[0]) / scale, (x[1] - center[1]) / scale])
    columns = []
    for j in range(3):
        nodal, integrated_area = quadratic_surface_loads(
            triangles,
            coords,
            local_points,
            quadrature_weights,
            jacobian_determinants,
            lambda x, j=j: np.array([0.0, 0.0, basis(x)[j]]),
        )
        if abs(integrated_area - area) > 1e-9:
            raise ValueError("Patch integration area mismatch")
        columns.append({n: float(v[2]) for n, v in nodal.items()})
    matrix = np.array(
        [
            [sum(basis(coords[n])[i] * v for n, v in col.items()) for col in columns]
            for i in range(3)
        ]
    )
    condition = float(np.linalg.cond(matrix))
    if diagnostic is not None:
        diagnostic["affine_system_condition"] = condition
    if not math.isfinite(condition) or condition > 1e8:
        raise ValueError("Washer pressure system is ill-conditioned")
    coeff = np.linalg.solve(matrix, [1.0, 0.0, 0.0])
    nodal_loads = {n: float(sum(coeff[j] * columns[j][n] for j in range(3))) for n in baseline}
    force, moment = _force_resultant(nodal_loads, coords)
    expected = np.cross(center, [0.0, 0.0, 1.0])
    if np.linalg.norm(force - [0.0, 0.0, 1.0]) > 1e-10 or np.linalg.norm(moment - expected) > 1e-8:
        raise ValueError("Equilibrated washer force or moment mismatch")
    pressure = {n: float(np.dot(coeff, basis(coords[n]))) for n in baseline}
    bernstein = []
    for a, b, c, ab, bc, ca in triangles:
        bernstein.extend(
            [
                pressure[a],
                pressure[b],
                pressure[c],
                2 * pressure[ab] - 0.5 * (pressure[a] + pressure[b]),
                2 * pressure[bc] - 0.5 * (pressure[b] + pressure[c]),
                2 * pressure[ca] - 0.5 * (pressure[c] + pressure[a]),
            ]
        )
    relative = np.asarray(bernstein) * area - 1.0
    low, high = float(np.min(relative)), float(np.max(relative))
    if diagnostic is not None:
        diagnostic["pressure_relative_to_mean_bernstein_bounds"] = [low, high]
        diagnostic["maximum_absolute_relative_pressure_correction"] = max(abs(low), abs(high))
        diagnostic["pressure_correction_limit"] = max_relative_correction
    if not np.isfinite(relative).all() or max(abs(low), abs(high)) > max_relative_correction:
        raise ValueError("Washer affine pressure correction exceeds declared ceiling")
    return nodal_loads, {
        "exact_center_xyz_mm": center.tolist(),
        "uncorrected_mesh_center_xyz_mm": mesh_center.tolist(),
        "discrete_area_mm2": area,
        "pressure_relative_to_mean_bernstein_bounds": [low, high],
        "maximum_absolute_relative_pressure_correction": max(abs(low), abs(high)),
        "pressure_correction_limit": max_relative_correction,
        "affine_system_condition": condition,
        "uncorrected_unit_force_moment_Nmm": np.cross(mesh_center, [0.0, 0.0, 1.0]).tolist(),
        "corrected_unit_force_N": force.tolist(),
        "corrected_unit_moment_Nmm": moment.tolist(),
        "assumption": "equilibrated resultant; actual washer pressure distribution unverified",
        "applied_load_reports": {
            str(f): {
                "uncorrected_moment_Nmm": (np.cross(mesh_center, [0.0, 0.0, f])).tolist(),
                "corrected_force_N": (force * f).tolist(),
                "corrected_moment_Nmm": (moment * f).tolist(),
            }
            for f in (50.0, 150.0)
        },
    }


def tetrahedral_gauss_volume(
    jacobian_determinants: Iterable[float], quadrature_weights: Iterable[float]
) -> float:
    """Integrate one tet's signed Gauss rule; Jacobians must stay positive."""
    det = np.asarray(tuple(jacobian_determinants), dtype=float)
    weight = np.asarray(tuple(quadrature_weights), dtype=float)
    if det.shape != weight.shape or not len(det):
        raise ValueError("Tetrahedron Gauss determinants/weights have incompatible sizes")
    if not np.isfinite(det).all() or np.any(det <= 0) or not np.isfinite(weight).all():
        raise ValueError(
            "Tetrahedron needs finite positive Jacobians and finite quadrature weights"
        )
    volume = float(np.dot(det, weight))
    if not math.isfinite(volume) or volume <= 0:
        raise ValueError("Tetrahedral Gauss integration did not produce positive volume")
    return volume


def _chunks(values: list[int], size: int = 12) -> list[str]:
    return [",".join(str(x) for x in values[i : i + size]) for i in range(0, len(values), size)]


def _emit_deck(
    coords: dict[int, np.ndarray],
    elements: dict[int, list[int]],
    element_sets: dict[str, list[int]],
    support_nodes: list[int],
    load_sets: dict[str, dict[int, float]],
) -> str:
    lines = ["*HEADING", "G80 bridge and six finite adhesive films; case-specific study", "*NODE"]
    lines.extend(
        f"{node},{xyz[0]:.12g},{xyz[1]:.12g},{xyz[2]:.12g}" for node, xyz in sorted(coords.items())
    )
    lines.append("*ELEMENT,TYPE=C3D10,ELSET=ALL")
    lines.extend(f"{tag}," + ",".join(str(n) for n in row) for tag, row in sorted(elements.items()))
    for name, ids in element_sets.items():
        lines.append(f"*ELSET,ELSET={name}")
        lines.extend(_chunks(sorted(ids)))
    lines.append("*ELSET,ELSET=BRIDGE")
    lines.extend(_chunks(sorted(element_sets["G11"])))
    adhesive_ids = sorted(
        set().union(*(set(v) for key, v in element_sets.items() if key.startswith("EPOXY_")))
    )
    lines.append("*ELSET,ELSET=ADHESIVE")
    lines.extend(_chunks(adhesive_ids))
    lines.append("*NSET,NSET=ALL")
    lines.extend(_chunks(sorted(coords)))
    lines.append("*NSET,NSET=SUPPORT")
    lines.extend(_chunks(sorted(support_nodes)))
    for name, young in [("G11", BRIDGE_E_MPA)] + [(f"EPOXY_{i}", EPOXY_E_MPA) for i in range(6)]:
        lines.extend(
            [
                f"*MATERIAL,NAME={name}",
                "*ELASTIC",
                f"{young:.12g},{POISSON:.12g}",
                f"*SOLID SECTION,ELSET={name},MATERIAL={name}",
            ]
        )
    lines.extend(["*BOUNDARY", "SUPPORT,1,3,0"])
    for _step_name, active in (("EQUAL_50N", "EQUAL"), ("SINGLE_150N", "SINGLE")):
        lines.extend(["*STEP", "*STATIC", "*CLOAD,OP=NEW"])
        for node, force in sorted(load_sets[active].items()):
            if abs(force) > 1e-18:
                lines.append(f"{node},3,{force:.15g}")
        lines.extend(
            [
                "*NODE PRINT,NSET=ALL",
                "U",
                "*NODE PRINT,NSET=SUPPORT",
                "RF",
                "*EL PRINT,ELSET=BRIDGE",
                "S",
                "ENER",
                "*EL PRINT,ELSET=ADHESIVE",
                "S",
                "ENER",
                "*END STEP",
            ]
        )
    lines.append("")
    return "\n".join(lines)


def _force_resultant(
    loads: dict[int, float], coords: dict[int, np.ndarray]
) -> tuple[np.ndarray, np.ndarray]:
    resultant = np.zeros(3)
    moment = np.zeros(3)
    for node, fz in loads.items():
        force = np.array([0.0, 0.0, float(fz)])
        resultant += force
        moment += np.cross(coords[node], force)
    return resultant, moment


def verify_serialized_loads(deck):
    """Independently recompute force and moments using only emitted decimal text."""
    coords = {}
    loads = []
    section = None
    for line in deck.splitlines():
        if line.startswith("*"):
            section = line.upper().split(",", 1)[0]
            if section == "*CLOAD":
                loads.append({})
            continue
        fields = line.split(",")
        if section == "*NODE":
            coords[int(fields[0])] = np.array([float(v) for v in fields[1:4]])
        elif section == "*CLOAD":
            if int(fields[1]) != 3:
                raise ValueError("Unexpected load direction in serialized deck")
            node = int(fields[0])
            loads[-1][node] = loads[-1].get(node, 0.0) + float(fields[2])
    if len(loads) != 2:
        raise ValueError("Expected two serialized load steps")
    targets = [
        np.zeros(3),
        np.array(
            [
                150 * WASHER_RADIUS_MM * math.sin(math.radians(WASHER_ANGLES_DEG[0])),
                -150 * WASHER_RADIUS_MM * math.cos(math.radians(WASHER_ANGLES_DEG[0])),
                0.0,
            ]
        ),
    ]
    result = []
    for load, target in zip(loads, targets, strict=True):
        force, moment = _force_resultant(load, coords)
        if (
            np.linalg.norm(force - [0.0, 0.0, 150.0]) > 2e-7
            or np.linalg.norm(moment - target) > 2e-5
        ):
            raise ValueError("Serialized deck resultant or moment failed unchanged guard")
        result.append({"force_N": force.tolist(), "moment_Nmm": moment.tolist()})
    return result


def _verify_preflight(
    coords: dict[int, np.ndarray],
    elements: dict[int, list[int]],
    element_sets: dict[str, list[int]],
    support_nodes: list[int],
    patch_data: list[dict[str, Any]],
    load_sets: dict[str, dict[int, float]],
    deck: str,
    node_cap: int,
    tet_cap: int,
) -> dict[str, Any]:
    all_elems = set(elements)
    owners = [set(ids) for ids in element_sets.values()]
    if len(coords) > node_cap or len(elements) > tet_cap:
        raise ValueError(
            f"Mesh guard exceeded: nodes={len(coords)}/{node_cap}, tets={len(elements)}/{tet_cap}"
        )
    if any(not group for group in owners) or set.union(*owners) != all_elems:
        raise ValueError("Material ownership does not cover every tetrahedron")
    if sum(len(group) for group in owners) != len(all_elems):
        raise ValueError("Material element sets overlap")
    if not support_nodes or not set(support_nodes) <= set(coords):
        raise ValueError("Rigid-back support node region is empty or invalid")
    if len(patch_data) != 3:
        raise ValueError("Expected three washer patches")
    for name, expected_forces in (("EQUAL", (50.0, 50.0, 50.0)), ("SINGLE", (150.0, 0.0, 0.0))):
        for patch, target in zip(patch_data, expected_forces, strict=True):
            weights = patch["unit_force_weights"]
            if abs(sum(weights.values()) - 1.0) > 1e-9:
                raise ValueError(f"Patch nodal weights fail area conservation: {name}")
            patch_loads = {node: target * value for node, value in weights.items()}
            patch_force, patch_moment = _force_resultant(patch_loads, coords)
            expected_force = np.array([0.0, 0.0, target])
            expected_moment = np.cross(np.asarray(patch["center_xyz_mm"]), expected_force)
            if not np.allclose(patch_force, expected_force, rtol=1e-10, atol=1e-8):
                raise ValueError(f"Patch load resultant mismatch: {name} {patch_force}")
            if not np.allclose(patch_moment, expected_moment, rtol=1e-10, atol=1e-6):
                raise ValueError(
                    f"Patch load moment mismatch: {name} {patch_moment} vs {expected_moment}"
                )
    results = {}
    for name, expected_fz, expected_m in (
        ("EQUAL", 150.0, np.zeros(3)),
        (
            "SINGLE",
            150.0,
            np.array(
                [
                    WASHER_RADIUS_MM * math.sin(math.radians(WASHER_ANGLES_DEG[0])) * 150.0,
                    -WASHER_RADIUS_MM * math.cos(math.radians(WASHER_ANGLES_DEG[0])) * 150.0,
                    0.0,
                ]
            ),
        ),
    ):
        f, m = _force_resultant(load_sets[name], coords)
        if not np.allclose(f, [0, 0, expected_fz], rtol=1e-10, atol=2e-7):
            raise ValueError(f"Unexpected {name} applied force resultant {f}")
        if not np.allclose(m, expected_m, rtol=1e-9, atol=2e-5):
            raise ValueError(
                f"Unexpected {name} applied moment resultant {m}; expected {expected_m}"
            )
        results[name] = {"force_xyz_N": f.tolist(), "moment_xyz_Nmm": m.tolist()}
    if deck.count("*CLOAD,OP=NEW") != 2 or deck.count("*STEP") != 2:
        raise ValueError("Deck does not contain exactly two independent load-reset steps")
    if "*NODE PRINT,NSET=ALL\nU" not in deck or "*NODE PRINT,NSET=SUPPORT\nRF" not in deck:
        raise ValueError("Deck is missing displacement or support-reaction output")
    if (
        "*EL PRINT,ELSET=BRIDGE\nS\nENER" not in deck
        or "*EL PRINT,ELSET=ADHESIVE\nS\nENER" not in deck
    ):
        raise ValueError("Deck is missing stress/energy output requests")
    return {
        "status": "adapter_preflight_passed_no_solver_invoked",
        "mesh_nodes": len(coords),
        "mesh_c3d10_tetrahedra": len(elements),
        "material_element_counts": {name: len(ids) for name, ids in element_sets.items()},
        "support_node_count": len(support_nodes),
        "washer_patches": [
            {k: p[k] for k in ("center_xyz_mm", "area_mm2", "integrated_nodal_weight_sum_mm2")}
            for p in patch_data
        ],
        "load_resultants": results,
        "deck_two_step_cload_reset": True,
        "validation_scope": "actual generated mesh ownership, pressure integration and deck; no solver result",
    }


def _gmsh_film(gmsh: Any, angle_deg: float, side: int) -> int:
    """Reproduce the existing CadQuery film: box∩R32.2 cylinder, then rotate."""
    origin_y = 6.0 if side == 1 else -6.1
    box = gmsh.model.occ.addBox(25.0, origin_y, 172.1, 7.2, 0.1, 15.0)
    cylinder = gmsh.model.occ.addCylinder(0.0, 0.0, 172.1, 0.0, 0.0, 15.0, 32.2)
    clipped, _ = gmsh.model.occ.intersect(
        [(3, box)], [(3, cylinder)], removeObject=True, removeTool=True
    )
    gmsh.model.occ.synchronize()
    volume_tags = [tag for dim, tag in clipped if dim == 3]
    if len(volume_tags) != 1 or gmsh.model.occ.getMass(3, volume_tags[0]) <= 0:
        raise ValueError("Source CadQuery film recipe did not create one positive solid")
    tag = volume_tags[0]
    gmsh.model.occ.rotate([(3, tag)], 0, 0, 0, 0, 0, 1, math.radians(angle_deg))
    gmsh.model.occ.synchronize()
    return tag


def _import_washer_patch(gmsh: Any, path: Path, expected_center: tuple[float, float]) -> int:
    imported = gmsh.model.occ.importShapes(str(path), highestDimOnly=True)
    gmsh.model.occ.synchronize()
    volumes = [tag for dim, tag in imported if dim == 3]
    if len(volumes) != 1:
        raise ValueError(f"Expected one saved washer solid in {path}")
    boundary = gmsh.model.getBoundary([(3, volumes[0])], oriented=False, recursive=False)
    candidates = []
    for dim, face in boundary:
        if dim != 2:
            continue
        bb = gmsh.model.getBoundingBox(2, face)
        area = gmsh.model.occ.getMass(2, face)
        center = gmsh.model.occ.getCenterOfMass(2, face)
        if (
            abs(bb[2] - 170.1) < 1e-5
            and abs(bb[5] - 170.1) < 1e-5
            and abs(center[0] - expected_center[0]) < 1e-5
            and abs(center[1] - expected_center[1]) < 1e-5
            and abs(center[2] - 170.1) < 1e-5
            and abs(area - 55.574774042) < 2e-5
        ):
            normal = _surface_normal(gmsh, face, center)
            if np.allclose(normal, [0.0, 0.0, 1.0], atol=1e-8):
                candidates.append(face)
    if len(candidates) != 1:
        raise ValueError(
            f"Could not identify unique z=170.1 washer contact face in {path}: {candidates}"
        )
    copied = gmsh.model.occ.copy([(2, candidates[0])])
    gmsh.model.occ.remove([(3, volumes[0])], recursive=True)
    gmsh.model.occ.synchronize()
    copied_faces = [int(tag) for dim, tag in copied if dim == 2]
    if len(copied_faces) != 1:
        raise ValueError("Could not preserve isolated washer patch surface")
    return copied_faces[0]


def _surface_normal(gmsh: Any, face: int, xyz: Iterable[float]) -> np.ndarray:
    """Get the oriented OCC surface normal at a BRep point."""
    uv = gmsh.model.getParametrization(2, face, [float(x) for x in xyz])
    normal = np.asarray(gmsh.model.getNormal(face, uv), dtype=float).reshape(-1, 3)[0]
    norm = float(np.linalg.norm(normal))
    if not math.isfinite(norm) or norm <= 0:
        raise ValueError(f"Invalid washer face normal on surface {face}")
    return normal / norm


def _volume_entities_from_map(mapping: list[list[tuple[int, int]]]) -> list[int]:
    return sorted({int(tag) for group in mapping for dim, tag in group if dim == 3})


def build_case(
    folder: Path, mesh_size_mm: float, node_cap: int, tet_cap: int, *, geometry_only: bool = False
) -> dict[str, Any]:
    """Create one exact-source bridge mesh/deck for the comparison packet.

    This adapter does not call CalculiX. ``folder`` must be new. The caller owns
    process/RSS/CPU guards and later decides whether to execute the generated deck.
    """
    folder = Path(folder)
    if folder.exists():
        raise FileExistsError(folder)
    if min(mesh_size_mm, node_cap, tet_cap) <= 0:
        raise ValueError("Mesh size and pre-solver caps must be positive")
    hashes = source_hashes()
    folder.mkdir(parents=True, exist_ok=False)
    import gmsh

    from src.analysis.support_fea import _quadratic_tets

    if gmsh.__version__ != "4.15.2":
        raise ValueError(f"Expected pinned Gmsh 4.15.2, found {gmsh.__version__}")
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("g80_bridge_finite_films")
        imported = gmsh.model.occ.importShapes(str(BRIDGE), highestDimOnly=True)
        gmsh.model.occ.synchronize()
        bridge_vols = [tag for dim, tag in imported if dim == 3]
        if len(bridge_vols) != 1:
            raise ValueError(f"Expected one exact bridge STEP volume, found {bridge_vols}")
        bridge_tag = int(bridge_vols[0])
        bridge_volume = float(gmsh.model.occ.getMass(3, bridge_tag))
        source_volumes = [(3, bridge_tag)]
        film_source_areas = []
        for angle in FILM_ANGLES_DEG:
            for side in (-1, 1):
                tag = _gmsh_film(gmsh, angle, side)
                source_volumes.append((3, tag))
                film_source_areas.append(float(gmsh.model.occ.getMass(3, tag)))
        if any(abs(v - FILM_VOLUME_MM3) > 2e-5 for v in film_source_areas):
            raise ValueError(f"Film volume differs from saved CadQuery recipe: {film_source_areas}")
        first_output, first_mapping = gmsh.model.occ.fragment(
            [source_volumes[0]], source_volumes[1:], removeObject=True, removeTool=True
        )
        gmsh.model.occ.synchronize()
        if len(first_mapping) != 7:
            raise ValueError(
                f"Unexpected bridge/film fragment ownership map length: {len(first_mapping)}"
            )
        first_material = {}
        for owner, mapped in enumerate(first_mapping):
            for dim, tag in mapped:
                if dim != 3:
                    continue
                name = "G11" if owner == 0 else f"EPOXY_{owner - 1}"
                if int(tag) in first_material and first_material[int(tag)] != name:
                    raise ValueError("Gmsh fragment mapped one volume to multiple materials")
                first_material[int(tag)] = name
        volume_tags = sorted(first_material)
        if len(volume_tags) != 7 or len(first_output) == 0:
            raise ValueError(f"Expected seven distinct material volumes, got {len(volume_tags)}")
        sums = {"G11": 0.0, **{f"EPOXY_{i}": 0.0 for i in range(6)}}
        for tag, name in first_material.items():
            sums[name] += float(gmsh.model.occ.getMass(3, tag))
        if abs(sums["G11"] - bridge_volume) > max(1e-6, bridge_volume * 1e-8):
            raise ValueError("G11 volume was not conserved by film fragmentation")
        if any(abs(sums[f"EPOXY_{i}"] - film_source_areas[i]) > 2e-5 for i in range(6)):
            raise ValueError("An adhesive-film volume was not conserved by fragmentation")

        washer_centers = [
            (
                WASHER_RADIUS_MM * math.cos(math.radians(angle)),
                WASHER_RADIUS_MM * math.sin(math.radians(angle)),
            )
            for angle in WASHER_ANGLES_DEG
        ]
        washer_faces = [
            _import_washer_patch(gmsh, path, center)
            for path, center in zip(WASHERS, washer_centers, strict=True)
        ]
        washer_exact_centers = [
            list(map(float, gmsh.model.occ.getCenterOfMass(2, face))) for face in washer_faces
        ]
        all_volumes = [(3, tag) for tag in volume_tags]
        patch_surfaces = [(2, tag) for tag in washer_faces]
        _second_output, second_mapping = gmsh.model.occ.fragment(
            all_volumes, patch_surfaces, removeObject=True, removeTool=True
        )
        gmsh.model.occ.synchronize()
        if len(second_mapping) != len(all_volumes) + len(patch_surfaces):
            raise ValueError("Mixed-dimension fragment returned unexpected ownership map")
        final_material: dict[int, str] = {}
        for prior_index, (_dim, prior_tag) in enumerate(all_volumes):
            name = first_material[int(prior_tag)]
            for dim, tag in second_mapping[prior_index]:
                if dim != 3:
                    continue
                if int(tag) in final_material and final_material[int(tag)] != name:
                    raise ValueError("Washer imprint merged volumes with different material owners")
                final_material[int(tag)] = name
        final_volume_tags = sorted(final_material)
        if len(final_volume_tags) != 7:
            raise ValueError(
                f"Mixed-dimensional washer imprint changed volume partition: {len(final_volume_tags)}"
            )
        washer_candidates = []
        for i, _source_face in enumerate(washer_faces):
            expected_center = washer_centers[i]
            mapped_surfaces = [
                int(tag) for dim, tag in second_mapping[len(all_volumes) + i] if dim == 2
            ]
            bridge_boundary = {
                int(tag)
                for dim, tag in gmsh.model.getBoundary(
                    [(3, volume) for volume, owner in final_material.items() if owner == "G11"],
                    oriented=False,
                    recursive=False,
                )
                if dim == 2
            }
            candidates = sorted(set(mapped_surfaces) & bridge_boundary)
            keep = []
            for face in candidates:
                bb = gmsh.model.getBoundingBox(2, face)
                area = float(gmsh.model.occ.getMass(2, face))
                if abs(bb[2] - 170.1) < 1e-5 and abs(bb[5] - 170.1) < 1e-5 and area > 1e-10:
                    face_center = np.asarray(gmsh.model.occ.getCenterOfMass(2, face), dtype=float)
                    face_normal = _surface_normal(gmsh, face, face_center)
                    if abs(face_normal[2]) < 1 - 1e-8:
                        raise ValueError(
                            f"Washer imprint face {face} is not parallel to the z plane"
                        )
                    keep.append((face, area, face_center))
            area = sum(x[1] for x in keep)
            if abs(area - PATCH_AREAS_MM2[i]) > 2e-5:
                raise ValueError(f"Imprinted washer patch {i} area mismatch: {area}")
            center = sum((entry[1] * entry[2] for entry in keep), np.zeros(3)) / area
            if (
                abs(center[0] - expected_center[0]) > 1e-5
                or abs(center[1] - expected_center[1]) > 1e-5
                or abs(center[2] - 170.1) > 1e-5
            ):
                raise ValueError(f"Imprinted washer patch {i} center mismatch: {center}")
            washer_candidates.append([face for face, _face_area, _face_center in keep])

        if geometry_only:
            # Diagnostic boundary only: preserve the exact source OCC construction
            # and stop before ANY mesh generation or solver invocation.
            actual_volumes = {
                name: sum(
                    float(gmsh.model.occ.getMass(3, tag))
                    for tag, owner in final_material.items()
                    if owner == name
                )
                for name in sums
            }
            if any(
                abs(actual_volumes[name] - sums[name]) > max(2e-5, abs(sums[name]) * 1e-8)
                for name in sums
            ):
                raise ValueError("Washer imprint did not conserve a material volume")
            if len(gmsh.model.mesh.getNodes()[0]) or len(gmsh.model.mesh.getElements(3)[0]):
                raise ValueError("Geometry-only stage unexpectedly contains mesh data")
            info = {
                "status": "geometry_only_complete_no_mesh_or_solver",
                "source_sha256": hashes,
                "gmsh_version": gmsh.__version__,
                "volume_owner_by_tag": final_material,
                "volume_by_material_mm3": actual_volumes,
                "washer_surface_tags": washer_candidates,
                "washer_surface_areas_mm2": [
                    sum(float(gmsh.model.occ.getMass(2, face)) for face in group)
                    for group in washer_candidates
                ],
                "washer_centers_mm": washer_centers,
                "mesh_generated": False,
                "solver_invoked": False,
                "meaning": "Exact OCC import, two fragment mappings and washer identification only; no mesh-node/interface ownership or force distribution was checked.",
            }
            (folder / "geometry-only.json").write_text(json.dumps(info, indent=2) + "\n")
            return info

        gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size_mm)
        gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size_mm)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.optimize("HighOrder")
        coords, elements = _quadratic_tets(gmsh)
        if len(coords) > node_cap or len(elements) > tet_cap:
            raise ValueError(
                f"Pre-solver mesh cap exceeded: {len(coords)} nodes, {len(elements)} tets"
            )
        types, _, _ = gmsh.model.mesh.getElements(3)
        if not types or {int(t) for t in types} != {11}:
            raise ValueError(f"Unexpected non-C3D10 solid element types: {types}")
        ips_vol, _weights_vol = gmsh.model.mesh.getIntegrationPoints(11, "Gauss4")
        _, determinants, _ = gmsh.model.mesh.getJacobians(11, ips_vol)
        determinants = np.asarray(determinants, dtype=float)
        if (
            not len(determinants)
            or not np.isfinite(determinants).all()
            or float(determinants.min()) <= 0
        ):
            raise ValueError("Nonpositive or invalid quadratic tetrahedron Jacobian")
        material_elements = {name: [] for name in sums}
        for volume, name in final_material.items():
            types_v, tags_v, conn_v = gmsh.model.mesh.getElements(3, volume)
            for typ, ids, conns in zip(types_v, tags_v, conn_v, strict=True):
                if int(typ) != 11:
                    raise ValueError(f"Unexpected solid element type {typ} in material {name}")
                material_elements[name].extend(int(x) for x in ids)
        all_ids = set(elements)
        if set().union(*(set(v) for v in material_elements.values())) != all_ids:
            raise ValueError("Material element ownership does not cover the generated mesh")

        # Identify the six free rail-side film faces by their exact rotated y=±6 mm plane.
        support_nodes: set[int] = set()
        support_face_areas = []
        bridge_interface_face_areas = []
        support_face_node_ids = []
        bridge_interface_node_ids = []
        film_surface_ownership = []
        epoxy_volume_entities = [
            (3, volume) for volume, owner in final_material.items() if owner.startswith("EPOXY_")
        ]
        for angle_index, angle in enumerate(FILM_ANGLES_DEG):
            theta = math.radians(angle)
            tangent = np.array([-math.sin(theta), math.cos(theta)])
            for side_index, side in enumerate((-1, 1)):
                ownership = {
                    "epoxy_material": f"EPOXY_{angle_index * 2 + side_index}",
                    "film_angle_deg": angle,
                    "side": side,
                }
                for plane_y, target_area, collection, ownership_key in (
                    (6.0 * side, FILM_RAIL_AREA_MM2, support_face_areas, "rail_back"),
                    (
                        6.1 * side,
                        FILM_BRIDGE_AREA_MM2,
                        bridge_interface_face_areas,
                        "bridge_interface",
                    ),
                ):
                    selected = []
                    for dim, face in gmsh.model.getBoundary(
                        epoxy_volume_entities, oriented=False, recursive=False
                    ):
                        if dim != 2:
                            continue
                        node_tags, xyz_raw, _ = gmsh.model.mesh.getNodes(
                            2, face, includeBoundary=True
                        )
                        if not len(node_tags):
                            continue
                        xyz = np.asarray(xyz_raw).reshape(-1, 3)
                        if np.max(np.abs(xyz[:, :2] @ tangent - plane_y)) < 2e-6:
                            area = float(gmsh.model.occ.getMass(2, face))
                            if area > 1e-8:
                                selected.append((int(face), area, [int(n) for n in node_tags]))
                    dedup = {face: (area, nodes) for face, area, nodes in selected}
                    area_sum = sum(item[0] for item in dedup.values())
                    if abs(area_sum - target_area) > 2e-4:
                        raise ValueError(
                            f"Film interface area mismatch angle={angle}, side={side}, plane={plane_y}: {area_sum}"
                        )
                    collection.append(area_sum)
                    ownership[ownership_key] = {
                        "surface_entity_tags": sorted(dedup),
                        "area_mm2": area_sum,
                    }
                    plane_nodes = sorted(
                        {node for _area, nodes in dedup.values() for node in nodes}
                    )
                    if abs(plane_y) == 6.0:
                        support_face_node_ids.append(plane_nodes)
                        ownership["rail_back"]["node_ids"] = plane_nodes
                        support_nodes.update(plane_nodes)
                    else:
                        bridge_interface_node_ids.append(plane_nodes)
                        ownership["bridge_interface"]["node_ids"] = plane_nodes
                film_surface_ownership.append(ownership)
        if (
            len(support_face_areas) != 6
            or len(bridge_interface_face_areas) != 6
            or not support_nodes
        ):
            raise ValueError("Did not identify six distinct rigid-back faces")

        ips_surf, qweights_surf = gmsh.model.mesh.getIntegrationPoints(9, "Gauss6")
        local_points = np.asarray(ips_surf, dtype=float).reshape(-1, 3)[:, :2]
        patch_data = []
        patch_diagnostics = []
        diagnostic_path = folder / "patch-diagnostics.json"
        diagnostic_path.write_text(json.dumps(patch_diagnostics, indent=2) + "\n")
        load_sets: dict[str, dict[int, float]] = {"EQUAL": {}, "SINGLE": {}}
        for i, surfaces in enumerate(washer_candidates):
            tri_ids = []
            jacobians = []
            for surface in surfaces:
                stypes, stags, sconn = gmsh.model.mesh.getElements(2, surface)
                for typ, ids, conn in zip(stypes, stags, sconn, strict=True):
                    if int(typ) != 9:
                        raise ValueError(
                            f"Washer imprint surface is not quadratic triangle type 9: {typ}"
                        )
                    tris = np.asarray(conn, dtype=int).reshape(-1, 6)
                    tri_ids.extend([tuple(int(n) for n in tri) for tri in tris])
                    ips_raw, _ = gmsh.model.mesh.getIntegrationPoints(9, "Gauss6")
                    _, dets, _ = gmsh.model.mesh.getJacobians(9, ips_raw, int(surface))
                    jacobians.extend(float(x) for x in dets)
            if not tri_ids:
                raise ValueError(f"Washer patch {i} has no quadratic surface facets")
            weights, area = quadratic_surface_weights(
                tri_ids, coords, local_points, qweights_surf, jacobians
            )
            center = sum((coords[node] * w for node, w in weights.items()), np.zeros(3)) / area
            exact_center = washer_exact_centers[i]
            diagnostic = {
                "source_index": i,
                "status": "in_progress",
                "exact_center_xyz_mm": exact_center,
                "uncorrected_mesh_center_xyz_mm": center.tolist(),
                "discrete_area_mm2": area,
                "exact_cad_area_mm2": PATCH_AREAS_MM2[i],
                "uncorrected_50N_moment_Nmm": np.cross(center, [0.0, 0.0, 50.0]).tolist(),
                "quadratic_triangle_count": len(tri_ids),
            }
            patch_diagnostics.append(diagnostic)
            diagnostic_path.write_text(json.dumps(patch_diagnostics, indent=2) + "\n")
            try:
                if abs(area - PATCH_AREAS_MM2[i]) > PATCH_AREAS_MM2[i] * 0.002:
                    raise ValueError(f"Integrated washer patch area mismatch at {i}: {area}")
                if abs(center[2] - 170.1) > 2e-7:
                    raise ValueError(f"Washer patch {i} center is not on z=170.1: {center}")
                unit_loads, pressure_report = equilibrated_washer_loads(
                    tri_ids,
                    coords,
                    local_points,
                    qweights_surf,
                    jacobians,
                    exact_center,
                    diagnostic=diagnostic,
                )
                diagnostic.update(pressure_report)
                diagnostic["status"] = "passed"
            except Exception as exc:
                diagnostic["status"] = "failed"
                diagnostic["error"] = f"{type(exc).__name__}: {exc}"
                raise
            finally:
                diagnostic_path.write_text(json.dumps(patch_diagnostics, indent=2) + "\n")
            patch_data.append(
                {
                    "source_index": i,
                    "angle_deg": WASHER_ANGLES_DEG[i],
                    "center_xyz_mm": exact_center,
                    "uncorrected_mesh_center_xyz_mm": center.tolist(),
                    "pressure_report": pressure_report,
                    "unit_force_weights": unit_loads,
                    "area_mm2": area,
                    "integrated_nodal_weight_sum_mm2": float(sum(weights.values())),
                    "unit_pressure_weights": weights,
                    "surface_entities": surfaces,
                    "quadratic_triangle_count": len(tri_ids),
                }
            )
            for step_name, force in (
                ("EQUAL", (50.0, 50.0, 50.0)[i]),
                ("SINGLE", (150.0, 0.0, 0.0)[i]),
            ):
                if force == 0:
                    continue
                for node, w in unit_loads.items():
                    load_sets[step_name][node] = load_sets[step_name].get(node, 0.0) + force * w

        # Gmsh's tetrahedral rule named Gauss4 has 11 points and includes a
        # negative reference weight. Preserve signed contributions and validate
        # Jacobians separately; this is geometry integration, not CCX IP order.
        ips_tet, tet_reference_weights = gmsh.model.mesh.getIntegrationPoints(11, "Gauss4")
        tet_reference_weights = np.asarray(tet_reference_weights, dtype=float)
        tet_ip_meta: dict[int, list[dict[str, Any]]] = {}
        tet_volume_map: dict[int, float] = {}
        tet_centroid_map: dict[int, list[float]] = {}
        for volume in final_volume_tags:
            types_v, tags_v, _ = gmsh.model.mesh.getElements(3, volume)
            for typ, element_tags in zip(types_v, tags_v, strict=True):
                if int(typ) != 11:
                    raise ValueError(f"Unexpected type {typ} in C3D10 quadrature metadata")
                _, dets, xyz_at_ip = gmsh.model.mesh.getJacobians(11, ips_tet, int(volume))
                dets = np.asarray(dets, dtype=float).reshape(
                    len(element_tags), len(tet_reference_weights)
                )
                xyz_at_ip = np.asarray(xyz_at_ip, dtype=float).reshape(
                    len(element_tags), len(tet_reference_weights), 3
                )
                for row, raw_tag in enumerate(element_tags):
                    eid = int(raw_tag)
                    if np.any(dets[row] <= 0) or not np.isfinite(dets[row]).all():
                        raise ValueError(f"C3D10 {eid} has nonpositive Gauss Jacobian")
                    dv = dets[row] * tet_reference_weights
                    volume_mm3 = tetrahedral_gauss_volume(dets[row], tet_reference_weights)
                    tet_volume_map[eid] = volume_mm3
                    tet_centroid_map[eid] = [
                        float(x) for x in (xyz_at_ip[row] * dv[:, None]).sum(axis=0) / volume_mm3
                    ]
                    tet_ip_meta[eid] = [
                        {
                            "xyz_mm": [float(x) for x in xyz_at_ip[row, q]],
                            "determinant_times_weight_mm3": float(dv[q]),
                        }
                        for q in range(len(tet_reference_weights))
                    ]
        if set(tet_volume_map) != set(elements):
            raise ValueError("Four-point integration metadata does not cover deck C3D10 elements")

        # Actual generated C3D10 region volumes, useful for physical stress averaging.
        region_volumes = {}
        region_centroids = {}
        for name, ids in material_elements.items():
            region_volumes[name] = float(
                sum(
                    gmsh.model.occ.getMass(3, vol)
                    for vol, owner in final_material.items()
                    if owner == name
                )
            )
            region_centroids[name] = [
                float(x)
                for x in (
                    sum(
                        gmsh.model.occ.getMass(3, vol)
                        * np.asarray(gmsh.model.occ.getCenterOfMass(3, vol), dtype=float)
                        for vol, owner in final_material.items()
                        if owner == name
                    )
                    / region_volumes[name]
                )
            ]
        node_records = {int(n): [float(x) for x in xyz] for n, xyz in coords.items()}
        load_records = {
            name: {
                int(node): [0.0, 0.0, float(value)]
                for node, value in sorted(loads.items())
                if abs(value) > 1e-18
            }
            for name, loads in load_sets.items()
        }
        element_records = {name: sorted(ids) for name, ids in material_elements.items()}
        deck = _emit_deck(coords, elements, material_elements, sorted(support_nodes), load_sets)
        serialized_resultants = verify_serialized_loads(deck)
        preflight = _verify_preflight(
            coords,
            elements,
            material_elements,
            sorted(support_nodes),
            patch_data,
            load_sets,
            deck,
            node_cap,
            tet_cap,
        )
        mesh_meta = {
            "source_sha256": hashes,
            "gmsh_version": gmsh.__version__,
            "mesh_size_mm": mesh_size_mm,
            "coordinates_mm": node_records,
            "support_node_ids": sorted(support_nodes),
            "support_face_node_ids": support_face_node_ids,
            "film_bridge_interface_node_ids": bridge_interface_node_ids,
            "film_surface_ownership": film_surface_ownership,
            "material_element_ids": element_records,
            "tetrahedron_material": {
                int(tag): name for name, ids in material_elements.items() for tag in ids
            },
            "material_region_volumes_mm3": region_volumes,
            "material_region_centroids_mm": region_centroids,
            "all_c3d10_connectivity": {str(tag): row for tag, row in elements.items()},
            "tetrahedron_centroids_mm": tet_centroid_map,
            "tetrahedron_volumes_mm3": tet_volume_map,
            "tetrahedron_gauss4_points": tet_ip_meta,
            "tetrahedron_gauss4_point_count": len(tet_reference_weights),
            "tetrahedron_gauss4_reference_weights": [float(x) for x in tet_reference_weights],
            "ccx_integration_point_order_verified": False,
            "jacobian": {
                "type": "Gmsh element type 11 / Gauss4",
                "sample_count": len(determinants),
                "minimum_determinant": float(determinants.min()),
                "positive_all_samples": True,
            },
            "washer_patches": [
                {
                    "source_index": p["source_index"],
                    "angle_deg": p["angle_deg"],
                    "center_xyz_mm": p["center_xyz_mm"],
                    "uncorrected_mesh_center_xyz_mm": p["uncorrected_mesh_center_xyz_mm"],
                    "pressure_report": p["pressure_report"],
                    "exact_cad_area_mm2": PATCH_AREAS_MM2[p["source_index"]],
                    "area_mm2": p["area_mm2"],
                    "quadratic_triangle_count": p["quadratic_triangle_count"],
                    "unit_pressure_nodal_weights_mm2": {
                        int(node): float(w)
                        for node, w in sorted(p["unit_pressure_weights"].items())
                    },
                }
                for p in patch_data
            ],
            "step_nodal_forces_N": load_records,
            "preflight": preflight,
            "serialized_deck_load_resultants": serialized_resultants,
            "solver_invoked": False,
        }
        (folder / "case.inp").write_text(deck)
        (folder / "mesh-meta.json").write_text(json.dumps(mesh_meta, indent=2) + "\n")
        return mesh_meta
    finally:
        gmsh.finalize()


__all__ = ["build_case", "quadratic_surface_loads", "quadratic_surface_weights", "source_hashes"]
