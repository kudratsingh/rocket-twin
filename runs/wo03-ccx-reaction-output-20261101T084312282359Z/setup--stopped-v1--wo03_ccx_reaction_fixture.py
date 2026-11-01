"""Generate tiny CCX reaction/output fixtures; this module never runs CCX."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.wo03_g80_bridge_adapter import quadratic_surface_loads  # noqa: E402
from src.analysis.support_fea import _quadratic_tets  # noqa: E402


LENGTH_MM = 20.0
BAR_CENTERS_X_MM = (-10.0, 0.0, 10.0)
FLAT_WIDTH_MM = 4.0
FLAT_DEPTH_MM = 4.0
ANNULUS_OUTER_RADIUS_MM = 3.0
ANNULUS_INNER_RADIUS_MM = 1.5
YOUNG_SINGLE_MPA = 1000.0
LAYER_YOUNG_MPA = (100.0, 10000.0)
POISSON = 0.0
STEP_LOADS_N = ((50.0, 50.0, 50.0), (150.0, 0.0, 0.0))


def _chunks(ids: list[int], size: int = 12) -> list[str]:
    return [", ".join(map(str, ids[i : i + size])) for i in range(0, len(ids), size)]


def _area(case: str) -> float:
    if case in ("A", "B"):
        return FLAT_WIDTH_MM * FLAT_DEPTH_MM
    return math.pi * (ANNULUS_OUTER_RADIUS_MM**2 - ANNULUS_INNER_RADIUS_MM**2)


def _new_volumes(gmsh: Any, case: str) -> list[tuple[int, int, int]]:
    """Return OCC volumes with (entity, bar index, axial layer index)."""
    occ = gmsh.model.occ
    layers = 1 if case == "A" else 2
    z_bounds = [0.0, LENGTH_MM] if layers == 1 else [0.0, 10.0, LENGTH_MM]
    objects: list[tuple[int, int, int]] = []
    for bar, cx in enumerate(BAR_CENTERS_X_MM):
        for layer in range(layers):
            z0, z1 = z_bounds[layer : layer + 2]
            if case in ("A", "B"):
                volume = occ.addBox(
                    cx - FLAT_WIDTH_MM / 2,
                    -FLAT_DEPTH_MM / 2,
                    z0,
                    FLAT_WIDTH_MM,
                    FLAT_DEPTH_MM,
                    z1 - z0,
                )
            else:
                outer = occ.addCylinder(cx, 0.0, z0, 0.0, 0.0, z1 - z0,
                                        ANNULUS_OUTER_RADIUS_MM)
                inner = occ.addCylinder(cx, 0.0, z0, 0.0, 0.0, z1 - z0,
                                        ANNULUS_INNER_RADIUS_MM)
                cut, _ = occ.cut([(3, outer)], [(3, inner)], removeObject=True,
                                 removeTool=True)
                candidates = [tag for dim, tag in cut if dim == 3]
                if len(candidates) != 1:
                    raise ValueError("Expected one annular prism per bar and layer")
                volume = candidates[0]
            objects.append((3, volume, bar, layer))
    # Fragment all axial segments together. Each pair belonging to one bar shares
    # a conformal interface; separated bars remain independent.
    fragments, _ = occ.fragment(
        [(dim, tag) for dim, tag, _, _ in objects], [],
        removeObject=True, removeTool=True,
    )
    del fragments
    occ.synchronize()
    volumes = []
    for _, tag in gmsh.model.getEntities(3):
        bb = gmsh.model.getBoundingBox(3, tag)
        cx = (bb[0] + bb[3]) / 2
        cz = (bb[2] + bb[5]) / 2
        bar = min(range(3), key=lambda i: abs(cx - BAR_CENTERS_X_MM[i]))
        layer = 0 if case == "A" or cz < LENGTH_MM / 2 else 1
        if abs(cx - BAR_CENTERS_X_MM[bar]) > (FLAT_WIDTH_MM if case != "C" else 2 * ANNULUS_OUTER_RADIUS_MM):
            raise ValueError("Could not assign OCC volume to a fixture bar")
        volumes.append((tag, bar, layer))
    if len(volumes) != 3 * layers:
        raise ValueError(f"Unexpected fragmented volume count: {len(volumes)}")
    return volumes


def _face_nodes(gmsh: Any, face: int) -> set[int]:
    tags, _, _ = gmsh.model.mesh.getNodes(2, face, includeBoundary=True)
    return {int(n) for n in tags}


def _load_for_face(gmsh: Any, face: int, coords: dict[int, np.ndarray], force_n: float):
    types, element_tags, connectivities = gmsh.model.mesh.getElements(2, face)
    triangles = []
    jacobians = []
    points, weights = gmsh.model.mesh.getIntegrationPoints(9, "Gauss6")
    for typ, raw, tags in zip(types, connectivities, element_tags, strict=True):
        if typ != 9:
            raise ValueError(f"Expected quadratic type-9 end facets, got type {typ}")
        triangles.extend(np.asarray(raw, dtype=np.int64).reshape(-1, 6).tolist())
        _, det, _ = gmsh.model.mesh.getJacobians(typ, points, face)
        if len(det) != len(tags) * len(weights):
            raise ValueError(
                f"Unexpected Gmsh surface Jacobian count on face {face}: "
                f"{len(det)} != {len(tags)}*{len(weights)}"
            )
        jacobians.extend(np.asarray(det, dtype=float).tolist())
    if not triangles:
        raise ValueError("No quadratic facets on free end face")
    loads, area = quadratic_surface_loads(
        triangles, coords, np.asarray(points).reshape(-1, 2), weights,
        jacobians, lambda _xyz: np.array([0.0, 0.0, force_n / _area("A")]),
    )
    # Rescale by the measured end-face area to make the integrated resultant
    # exactly the requested force while preserving uniform traction.
    resultant = sum(float(v[2]) for v in loads.values())
    if resultant <= 0:
        raise ValueError("Nonpositive integrated traction resultant")
    scale = force_n / resultant
    return {n: v * scale for n, v in loads.items()}, area


def _emit_deck(case: str, coords, elements, material_elements, supports, loads_by_step):
    lines = ["*HEADING", f"WO03 CCX reaction fixture {case}; N mm MPa", "*NODE"]
    lines.extend(f"{n},{p[0]:.14g},{p[1]:.14g},{p[2]:.14g}" for n, p in sorted(coords.items()))
    lines.append("*ELEMENT,TYPE=C3D10,ELSET=ALL")
    lines.extend(f"{eid}," + ",".join(map(str, conn)) for eid, conn in sorted(elements.items()))
    for name, ids in material_elements.items():
        lines.append(f"*ELSET,ELSET={name}")
        lines.extend(_chunks(sorted(ids)))
    all_nodes = sorted(coords)
    support_ids = sorted(supports)
    for name, ids in (("ALL", all_nodes), ("SUPPORT", support_ids)):
        lines.append(f"*NSET,NSET={name}")
        lines.extend(_chunks(ids))
    for name in material_elements:
        young = YOUNG_SINGLE_MPA if case == "A" else LAYER_YOUNG_MPA[int(name[-1])]
        lines.extend([
            f"*MATERIAL,NAME={name}", "*ELASTIC", f"{young:.12g},{POISSON:.12g}",
            f"*SOLID SECTION,ELSET={name},MATERIAL={name}",
        ])
    lines.extend(["*BOUNDARY", "SUPPORT,1,3,0"])
    for step_loads in loads_by_step:
        lines.extend(["*STEP", "*STATIC", "*CLOAD,OP=NEW"])
        for node, vector in sorted(step_loads.items()):
            for dof, force in enumerate(vector, start=1):
                if abs(float(force)) > 1e-18:
                    lines.append(f"{node},{dof},{float(force):.15g}")
        lines.extend([
            "*NODE PRINT,NSET=ALL", "U",
            "*NODE PRINT,NSET=ALL", "RF",
            "*NODE PRINT,NSET=SUPPORT", "RF",
            "*END STEP",
        ])
    return "\n".join(lines) + "\n"


def generate_fixture(case: str, output: Path, *, mesh_size_mm: float = 5.0,
                     node_cap: int = 5000) -> dict[str, Any]:
    """Generate one case-specific C3D10 deck and metadata; never invokes CCX."""
    case = case.upper()
    if case not in ("A", "B", "C"):
        raise ValueError("case must be A, B, or C")
    if output.exists():
        raise FileExistsError(output)
    if mesh_size_mm <= 0 or node_cap <= 0:
        raise ValueError("Mesh size and node cap must be positive")
    output.mkdir(parents=True, exist_ok=False)
    import gmsh

    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size_mm)
        gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size_mm)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.model.add(f"reaction_fixture_{case}")
        volume_map = _new_volumes(gmsh, case)
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.optimize("HighOrder")
        coords, elements = _quadratic_tets(gmsh)
        if len(coords) > node_cap or len(elements) > 5000:
            raise ValueError("Fixture exceeds node/tetrahedron cap")

        material_elements: dict[str, set[int]] = {}
        for vol, bar, layer in volume_map:
            material = "MAT" if case == "A" else f"LAYER{layer}"
            material_elements.setdefault(material, set())
            for typ, tags, conn in zip(*gmsh.model.mesh.getElements(3, vol), strict=True):
                if typ != 11:
                    raise ValueError(f"Expected C3D10 type 11, got {typ}")
                material_elements[material].update(map(int, tags))
        owned = set().union(*material_elements.values())
        if owned != set(elements) or sum(map(len, material_elements.values())) != len(elements):
            raise ValueError("Material element ownership is incomplete or overlapping")

        support_by_bar = [set() for _ in range(3)]
        top_by_bar = [set() for _ in range(3)]
        loads_by_bar_step = [{}, {}]
        areas = []
        top_centers = []
        for _, face in gmsh.model.getEntities(2):
            bb = gmsh.model.getBoundingBox(2, face)
            if abs(bb[2]) < 1e-5 and abs(bb[5]) < 1e-5:
                cx = (bb[0] + bb[3]) / 2
                bar = min(range(3), key=lambda i: abs(cx - BAR_CENTERS_X_MM[i]))
                support_by_bar[bar].update(_face_nodes(gmsh, face))
            if abs(bb[2] - LENGTH_MM) < 1e-5 and abs(bb[5] - LENGTH_MM) < 1e-5:
                cx = (bb[0] + bb[3]) / 2
                bar = min(range(3), key=lambda i: abs(cx - BAR_CENTERS_X_MM[i]))
                top_by_bar[bar].add(face)
        support_ids = set().union(*support_by_bar)
        if not all(support_by_bar) or not all(top_by_bar):
            raise ValueError("Could not identify all three bottom/top bar faces")
        load_records = []
        for bar in range(3):
            faces = sorted(top_by_bar[bar])
            face_area = 0.0
            for face in faces:
                bb = gmsh.model.getBoundingBox(2, face)
                center = [(bb[0] + bb[3]) / 2, (bb[1] + bb[4]) / 2, LENGTH_MM]
                face_area += gmsh.model.occ.getMass(2, face)
            areas.append(face_area)
            top_centers.append([BAR_CENTERS_X_MM[bar], 0.0, LENGTH_MM])
            for step_index, forces in enumerate(STEP_LOADS_N):
                force_n = forces[bar]
                for face in faces:
                    nodal, _ = _load_for_face(gmsh, face, coords, force_n / len(faces))
                    for node, vec in nodal.items():
                        loads_by_bar_step[step_index][node] = (
                            loads_by_bar_step[step_index].get(node, np.zeros(3)) + vec
                        )
                load_records.append({"step": step_index + 1, "bar": bar,
                                     "requested_force_N": force_n,
                                     "load_face_count": len(faces)})
        gmsh.write(str(output / "mesh.msh"))
        points, _ = gmsh.model.mesh.getIntegrationPoints(11, "Gauss4")
        _, dets, _ = gmsh.model.mesh.getJacobians(11, points)
        if not len(dets) or not np.isfinite(dets).all() or float(np.min(dets)) <= 0:
            raise ValueError("C3D10 Jacobian determinants are not positive finite")
    finally:
        gmsh.finalize()

    deck = _emit_deck(case, coords, elements, material_elements, support_ids,
                      loads_by_bar_step)
    (output / "case.inp").write_text(deck)
    expected_u = []
    for forces in STEP_LOADS_N:
        compliance = LENGTH_MM / YOUNG_SINGLE_MPA if case == "A" else (
            10.0 / LAYER_YOUNG_MPA[0] + 10.0 / LAYER_YOUNG_MPA[1]
        )
        expected_u.append([force * compliance / _area(case) for force in forces])
    applied_moments = []
    for step_loads in loads_by_bar_step:
        moment = np.zeros(3)
        for node, vector in step_loads.items():
            moment += np.cross(coords[node], vector)
        applied_moments.append(moment.tolist())
    metadata = {
        "case": case,
        "solver_invoked": False,
        "mesh_size_mm": mesh_size_mm,
        "node_count": len(coords),
        "c3d10_count": len(elements),
        "node_coordinates_mm": {str(n): p.tolist() for n, p in coords.items()},
        "support_node_ids": sorted(support_ids),
        "material_element_ids": {k: sorted(v) for k, v in material_elements.items()},
        "cross_section_area_analytic_mm2": _area(case),
        "top_face_mesh_area_mm2_by_bar": areas,
        "load_center_xyz_mm_by_bar": top_centers,
        "step_bar_resultants_N": [list(x) for x in STEP_LOADS_N],
        "step_nodal_forces_N": [
            {str(n): v.tolist() for n, v in sorted(loads.items())}
            for loads in loads_by_bar_step
        ],
        "step_applied_moment_about_global_origin_Nmm": applied_moments,
        "expected_free_end_displacement_mm_by_step_bar": expected_u,
        "load_face_counts": load_records,
        "material_model": {"poisson": POISSON, "single_E_MPa": YOUNG_SINGLE_MPA,
                           "layer_E_MPa": list(LAYER_YOUNG_MPA)},
        "max_c3d10_jacobian_minimum": float(np.min(dets)),
        "limitations": ["No CalculiX solve or DAT parser validation performed."],
    }
    (output / "mesh-meta.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


def nonnative_preflight(meta: dict[str, Any], deck: str) -> dict[str, Any]:
    """Check deck/load contracts and analytic resultants without a solver."""
    if deck.count("*STEP") != 2 or deck.count("*CLOAD,OP=NEW") != 2:
        raise ValueError("Deck is not exactly two OP=NEW load steps")
    if "*BOUNDARY\nSUPPORT,1,3,0" not in deck:
        raise ValueError("Support is not fully fixed on global DOFs 1-3")
    if "*NODE PRINT,NSET=ALL\nU" not in deck or "*NODE PRINT,NSET=SUPPORT\nRF" not in deck:
        raise ValueError("Required native output requests are missing")
    if "*NODE PRINT,NSET=ALL\nRF" not in deck:
        raise ValueError("All-node native RF output request is missing")
    if any(tag in deck for tag in ("*MPC", "*TRANSFORM", "*EQUATION")):
        raise ValueError("Unexpected hidden kinematic constraint in fixture deck")
    force_sums = []
    for step in meta["step_nodal_forces_N"]:
        total = np.sum(np.asarray(list(step.values()), dtype=float), axis=0)
        force_sums.append(total.tolist())
    expected = [[0.0, 0.0, 150.0], [0.0, 0.0, 150.0]]
    if not np.allclose(force_sums, expected, atol=1e-8, rtol=0):
        raise ValueError(f"Integrated CLOAD resultant mismatch: {force_sums}")
    moments = np.asarray(meta["step_applied_moment_about_global_origin_Nmm"])
    if moments.shape != (2, 3) or not np.isfinite(moments).all():
        raise ValueError("Integrated nodal load moments are absent or invalid")
    return {"status": "pass", "native_solver_invoked": False,
            "steps": 2, "op_new_count": 2, "integrated_force_N": force_sums,
            "integrated_moment_about_global_origin_Nmm": moments.tolist(),
            "checks": ["global support", "all-node U/support RF output", "force resultant",
                       "no MPC/transform/equation constraints"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("A", "B", "C"))
    parser.add_argument("output", type=Path)
    parser.add_argument("--mesh-size-mm", type=float, default=5.0)
    parser.add_argument("--node-cap", type=int, default=5000)
    args = parser.parse_args()
    meta = generate_fixture(args.case, args.output, mesh_size_mm=args.mesh_size_mm,
                            node_cap=args.node_cap)
    result = nonnative_preflight(meta, (args.output / "case.inp").read_text())
    (args.output / "preflight.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
