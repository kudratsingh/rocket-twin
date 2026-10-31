"""Copy-only quadratic-tetra support model for a motor-mount STEP solid.

Units in the CalculiX deck are N, mm, MPa. Surface tractions are integrated to
consistent nodal forces on quadratic triangles. Constraints model ideal bonded
ring support and do not qualify the real bond or body substrate.
"""

from __future__ import annotations

import importlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from src.analysis.fea import solver_path


def _quadratic_tets(gmsh: Any) -> tuple[dict[int, np.ndarray], dict[int, list[int]]]:
    node_tags, xyz_raw, _ = gmsh.model.mesh.getNodes()
    coords = {
        int(tag): np.asarray(xyz_raw[3 * i : 3 * i + 3], dtype=float)
        for i, tag in enumerate(node_tags)
    }
    types, element_tags, conn_raw = gmsh.model.mesh.getElements(3)
    elements: dict[int, list[int]] = {}
    for typ, tags, conn in zip(types, element_tags, conn_raw):
        if typ != 11:
            raise ValueError(f"Unsupported solid element type {typ}; expected C3D10")
        for tag, row in zip(tags, np.asarray(conn).reshape(-1, 10)):
            elements[int(tag)] = [int(x) for x in row[[0, 1, 2, 3, 4, 5, 6, 7, 9, 8]]]
    return coords, elements


def buckling_factors_from_dat(path: Path, expected_modes: int) -> list[float]:
    """Read factors only from CalculiX's explicitly labeled factor table."""
    lines = path.read_text(errors="replace").splitlines()
    start = next((i for i, line in enumerate(lines) if "MODE NO" in line.upper()), None)
    if start is None:
        raise RuntimeError("CalculiX .dat has no labeled mode/factor table")
    factors: list[float] = []
    for line in lines[start + 1 :]:
        values = line.split()
        if len(values) < 2:
            if factors:
                break
            continue
        try:
            mode_number = int(values[0])
            factor = float(values[1])
        except ValueError:
            continue
        if mode_number != len(factors) + 1:
            if factors:
                break
            continue
        factors.append(factor)
        if len(factors) == expected_modes:
            return factors
    if not factors:
        raise RuntimeError("No numeric buckling factors found under the factor-table heading")
    return factors


def _run_ccx(folder: Path) -> str:
    ccx = solver_path()
    if not ccx:
        raise RuntimeError("CalculiX executable unavailable")
    version = subprocess.run([ccx, "-v"], capture_output=True, text=True, check=False)
    version_text = version.stdout + version.stderr
    if "2.23" not in version_text:
        raise ValueError("Expected pinned CalculiX 2.23")
    result = subprocess.run(
        [ccx, "-i", "case"],
        cwd=folder,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
        env={**os.environ, "OMP_NUM_THREADS": "1"},
    )
    (folder / "solver.log").write_text(result.stdout + result.stderr)
    if result.returncode or not (folder / "case.dat").exists():
        raise RuntimeError("CalculiX buckling job failed; inspect solver.log")
    if re.search(
        r"(?:\*ERROR|ERROR\s+in\s+[A-Za-z])", result.stdout + result.stderr, re.IGNORECASE
    ):
        raise RuntimeError("CalculiX reported an error; inspect solver.log")
    return version_text.strip()


def _nodes_on_face(gmsh: Any, face: int) -> list[int]:
    tags, _, _ = gmsh.model.mesh.getNodes(2, face, includeBoundary=True)
    return [int(x) for x in tags]


def _clipped_quadratic_triangle_weights(
    tri: np.ndarray, coords: dict[int, np.ndarray], lower_z: float, upper_z: float
) -> tuple[dict[int, float], float]:
    """Integrate quadratic surface shape functions over a z-clipped facet."""
    nodes = [int(n) for n in tri]
    corners = [coords[n] for n in nodes[:3]]
    polygon: list[tuple[np.ndarray, np.ndarray]] = [(np.eye(3)[i], corners[i]) for i in range(3)]

    def clip(
        points: list[tuple[np.ndarray, np.ndarray]], bound: float, above: bool
    ) -> list[tuple[np.ndarray, np.ndarray]]:
        if not points:
            return []
        result: list[tuple[np.ndarray, np.ndarray]] = []
        for current, following in zip(points, points[1:] + points[:1], strict=True):
            b0, x0 = current
            b1, x1 = following
            v0 = x0[2] - bound
            v1 = x1[2] - bound
            inside0 = v0 >= -1e-12 if above else v0 <= 1e-12
            inside1 = v1 >= -1e-12 if above else v1 <= 1e-12
            if inside0:
                result.append(current)
            if inside0 != inside1:
                fraction = (bound - x0[2]) / (x1[2] - x0[2])
                result.append((b0 + fraction * (b1 - b0), x0 + fraction * (x1 - x0)))
        return result

    polygon = clip(polygon, lower_z, True)
    polygon = clip(polygon, upper_z, False)
    result = {n: 0.0 for n in nodes}
    area_total = 0.0
    quadrature = ((2 / 3, 1 / 6, 1 / 6), (1 / 6, 2 / 3, 1 / 6), (1 / 6, 1 / 6, 2 / 3))
    for j in range(1, len(polygon) - 1):
        vertices = (polygon[0], polygon[j], polygon[j + 1])
        xyz = [v[1] for v in vertices]
        area = float(np.linalg.norm(np.cross(xyz[1] - xyz[0], xyz[2] - xyz[0])) / 2)
        if area <= 1e-14:
            continue
        area_total += area
        original_bary = [v[0] for v in vertices]
        for q in quadrature:
            bary = q[0] * original_bary[0] + q[1] * original_bary[1] + q[2] * original_bary[2]
            l1, l2, l3 = bary
            shapes = (
                l1 * (2 * l1 - 1),
                l2 * (2 * l2 - 1),
                l3 * (2 * l3 - 1),
                4 * l1 * l2,
                4 * l2 * l3,
                4 * l3 * l1,
            )
            for node, shape in zip(nodes, shapes, strict=True):
                result[node] += area * shape / 3
    return result, area_total


def solve_support_case(
    step_path: Path,
    output: Path,
    mesh_size_mm: float,
    load_n: float,
    load_sign: int,
    young_mpa: float = 1000.0,
    poisson: float = 0.25,
    ring_stations_mm: list[float] | None = None,
    ring_thickness_mm: float = 3.0,
) -> dict[str, Any]:
    """Mesh and solve one axial load direction on the imported mount solid."""
    gmsh: Any = importlib.import_module("gmsh")
    if gmsh.__version__ != "4.15.2":
        raise ValueError("FEA requires pinned Gmsh 4.15.2")
    if load_sign not in (-1, 1) or min(mesh_size_mm, load_n, young_mpa) <= 0:
        raise ValueError("Mesh size, load, modulus must be positive; load sign must be +/-1")
    output.mkdir(parents=True, exist_ok=False)
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("motor_mount_support")
        gmsh.model.occ.importShapes(str(step_path), highestDimOnly=True)
        gmsh.model.occ.synchronize()
        volumes = gmsh.model.getEntities(3)
        if not volumes:
            raise ValueError("Imported STEP contains no solid volume")
        gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size_mm)
        gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size_mm)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.optimize("HighOrder")
        gmsh.write(str(output / "mesh.msh"))
        node_tags, xyz_raw, _ = gmsh.model.mesh.getNodes()
        coords = {
            int(tag): np.asarray(xyz_raw[3 * i : 3 * i + 3], dtype=float)
            for i, tag in enumerate(node_tags)
        }
        types, element_tags, conn_raw = gmsh.model.mesh.getElements(3)
        elements: dict[int, list[int]] = {}
        for typ, tags, conn in zip(types, element_tags, conn_raw):
            if typ != 11:
                raise ValueError(f"Unsupported solid element type {typ}; expected C3D10")
            for tag, row in zip(tags, np.asarray(conn).reshape(-1, 10)):
                elements[int(tag)] = [int(x) for x in row[[0, 1, 2, 3, 4, 5, 6, 7, 9, 8]]]
        surfaces = gmsh.model.getEntities(2)
        ring_stations = ring_stations_mm or [0.0, 110.0, 187.0]
        support_faces: list[int] = []
        load_faces: list[tuple[int, np.ndarray]] = []
        radial_coverage: list[float] = []
        for _, face in surfaces:
            bb = gmsh.model.getBoundingBox(2, face)
            zmin, zmax = float(bb[2]), float(bb[5])
            # Find ring axial face surfaces from the actual supplied station list.
            if any(
                zmin >= s - 1e-5 and zmax <= s + ring_thickness_mm + 1e-5 and abs(zmin - s) < 1e-4
                for s in ring_stations
            ):
                support_faces.append(face)
            # Select six longitudinal rail side faces by their CAD center
            # relative to the three rail centerlines, then trim mesh facets to
            # the actual 18 mm finger engagement band.
            if (zmax - zmin) > 5:
                center = np.asarray(gmsh.model.occ.getCenterOfMass(2, face))
                for angle in (0.0, 120.0, 240.0):
                    rad = np.deg2rad(angle)
                    radial = np.asarray([np.cos(rad), np.sin(rad)])
                    tangent = np.asarray([-np.sin(rad), np.cos(rad)])
                    planar = center[:2] - 28.5 * radial
                    if (
                        abs(float(np.dot(planar, radial))) < 0.75
                        and abs(abs(float(np.dot(planar, tangent))) - 6.0) < 0.2
                    ):
                        load_faces.append((face, radial))
                        face_nodes = _nodes_on_face(gmsh, face)
                        radial_coverage.extend(
                            float(np.dot(coords[n][:2], radial))
                            for n in face_nodes
                            if n in coords and 11.0 <= coords[n][2] <= 29.0
                        )
                        break
        if not support_faces or not load_faces:
            raise ValueError(
                f"Could not identify support/load surfaces (supports={len(support_faces)}, loads={len(load_faces)})"
            )
        load_weights: dict[int, float] = {}
        load_area_mm2 = 0.0
        active_load_faces = 0
        for face, _ in load_faces:
            stypes, _, sconn = gmsh.model.mesh.getElements(2, face)
            face_area = 0.0
            for typ, conn in zip(stypes, sconn):
                if typ != 9:
                    raise ValueError("Expected quadratic triangular load-patch facets")
                for tri in np.asarray(conn).reshape(-1, 6):
                    weights, area = _clipped_quadratic_triangle_weights(tri, coords, 11.0, 29.0)
                    load_area_mm2 += area
                    face_area += area
                    for n, weight in weights.items():
                        load_weights[n] = load_weights.get(n, 0.0) + weight
            if face_area > 1e-10:
                active_load_faces += 1
        support_surface_nodes = {n for face in support_faces for n in _nodes_on_face(gmsh, face)}
        support_radius = max(float(np.linalg.norm(coords[n][:2])) for n in support_surface_nodes)
        # Restrict axial constraints to nodes on the ring OD (not whole ring
        # faces) so reactions remain attributable to each actual ring station.
        ring_nodes: dict[float, list[int]] = {}
        for station in ring_stations:
            ring_nodes[station] = sorted(
                n
                for n in support_surface_nodes
                if abs(np.linalg.norm(coords[n][:2]) - support_radius) < 0.25
                and station - 1e-5 <= coords[n][2] <= station + ring_thickness_mm + 1e-5
            )
        ring_nodes = {s: nodes for s, nodes in ring_nodes.items() if nodes}
        support_nodes = sorted({n for nodes in ring_nodes.values() for n in nodes})
        if not load_weights or not support_nodes:
            raise ValueError("Selected surface patches have no mesh nodes")
        gmsh.finalize()
    except BaseException:
        gmsh.finalize()
        raise

    # Distribute force over midside nodes on selected load surfaces. Nodal
    # forces preserve the specified resultant; actual patch area is recorded.
    load_weights = {n: weight for n, weight in load_weights.items() if n in coords}
    weight_sum = sum(load_weights.values())
    loads = {n: load_sign * load_n * weight / weight_sum for n, weight in load_weights.items()}
    origin = min(support_nodes, key=lambda n: float(np.linalg.norm(coords[n])))
    other = max(support_nodes, key=lambda n: abs(float(coords[n][0] - coords[origin][0])))
    if origin == other or abs(coords[other][0] - coords[origin][0]) < 1e-3:
        raise ValueError("Could not establish a non-collinear in-plane rigid-mode restraint")
    deck = ["*HEADING", "Copy-only motor mount support screen N mm MPa", "*NODE"]
    deck += [f"{n}, {x[0]:.12g}, {x[1]:.12g}, {x[2]:.12g}" for n, x in coords.items()]
    deck += ["*ELEMENT,TYPE=C3D10,ELSET=ALL"] + [
        f"{n}, " + ", ".join(map(str, row)) for n, row in elements.items()
    ]
    deck += ["*NSET,NSET=ALL"] + [
        ", ".join(map(str, node_ids[i : i + 12]))
        for node_ids in [sorted(coords)]
        for i in range(0, len(node_ids), 12)
    ]
    deck += ["*NSET,NSET=SUPPORT"] + [
        ", ".join(map(str, support_nodes[i : i + 12])) for i in range(0, len(support_nodes), 12)
    ]
    for index, ring_nodes_list in enumerate(ring_nodes.values()):
        deck += [f"*NSET,NSET=RING{index}"] + [
            ", ".join(map(str, ring_nodes_list[i : i + 12]))
            for i in range(0, len(ring_nodes_list), 12)
        ]
    deck += [
        "*MATERIAL,NAME=PLY",
        "*ELASTIC",
        f"{young_mpa:.12g},{poisson:.12g}",
        "*SOLID SECTION,ELSET=ALL,MATERIAL=PLY",
        "*BOUNDARY",
        "SUPPORT,3,3,0",
        f"{origin},1,2,0",
        f"{other},2,2,0",
        "*STEP",
        "*STATIC",
        "*CLOAD",
    ]
    deck += [f"{n},3,{force:.12g}" for n, force in loads.items()]
    deck += [
        "*NODE PRINT,NSET=SUPPORT",
        "RF",
        "*NODE PRINT,NSET=ALL",
        "U",
        "*EL PRINT,ELSET=ALL",
        "S",
        "*END STEP",
    ]
    (output / "case.inp").write_text("\n".join(deck) + "\n")
    ccx = solver_path()
    if not ccx:
        raise RuntimeError("CalculiX executable unavailable")
    version = subprocess.run([ccx, "-v"], capture_output=True, text=True, check=False)
    version_text = version.stdout + version.stderr
    if "2.23" not in version_text:
        raise ValueError("Expected pinned CalculiX 2.23")
    result = subprocess.run(
        [ccx, "-i", "case"],
        cwd=output,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
        env={**os.environ, "OMP_NUM_THREADS": "1"},
    )
    (output / "solver.log").write_text(result.stdout + result.stderr)
    if result.returncode or not (output / "case.dat").exists():
        raise RuntimeError("CalculiX support solve failed")
    sections: dict[str, list[list[float]]] = {"U": [], "RF": [], "S": []}
    section: str | None = None
    for line in (output / "case.dat").read_text().splitlines():
        low = line.lower()
        if "displacements (" in low:
            section = "U"
            continue
        if "forces (" in low:
            section = "RF"
            continue
        if "stresses (" in low:
            section = "S"
            continue
        fields = line.split()
        if section and fields:
            try:
                int(fields[0])
                sections[section].append([float(x) for x in fields])
            except ValueError:
                continue
    if not all(sections.values()):
        raise RuntimeError("Solver output missing displacement, reaction or stress data")
    reactions = np.asarray(sections["RF"])
    stresses = np.asarray(sections["S"])
    disp = np.asarray(sections["U"])
    element_z = {
        eid: float(np.mean([coords[node][2] for node in conn[:4]]))
        for eid, conn in elements.items()
    }
    regional = np.asarray(
        [row for row in sections["S"] if 15.0 <= element_z.get(int(row[0]), -1.0) <= 25.0]
    )
    if len(regional) == 0:
        raise RuntimeError("No stress integration points in the defined regional band")
    report = {
        "mesh_size_mm": mesh_size_mm,
        "node_count": len(coords),
        "element_count": len(elements),
        "load_sign_z": load_sign,
        "applied_resultant_n": sum(loads.values()),
        "load_patch_area_mm2": load_area_mm2,
        "load_face_count": active_load_faces,
        "load_patch_radial_projection_bounds_mm": [
            min(radial_coverage),
            max(radial_coverage),
        ],
        "load_patch_axial_bounds_mm": [11.0, 29.0],
        "load_node_count": len(loads),
        "support_node_count": len(support_nodes),
        "in_plane_rigid_mode_constraints": {
            "origin_xy_fixed_node": origin,
            "second_node_y_fixed": other,
            "x_separation_mm": float(coords[other][0] - coords[origin][0]),
            "basis": "three independent scalar constraints: origin X/Y and distinct noncollinear point Y; removes in-plane translation and yaw only",
        },
        "support_reaction_z_n": float(reactions[:, 3].sum()),
        "ring_support_reaction_z_n": {
            str(station): float(
                sum(row[3] for row in reactions if int(row[0]) in set(ring_nodes[station]))
            )
            for station in ring_nodes
        },
        "equilibrium_residual_n": float(reactions[:, 3].sum() + load_sign * load_n),
        "maximum_displacement_mm": float(np.linalg.norm(disp[:, 1:4], axis=1).max()),
        "maximum_absolute_szz_mpa": float(np.abs(stresses[:, 4]).max()),
        "regional_szz_band_station_mm": [15.0, 25.0],
        "regional_szz_max_abs_mpa": float(np.abs(regional[:, 4]).max()),
        "regional_szz_mean_abs_mpa": float(np.abs(regional[:, 4]).mean()),
        "regional_stress_point_count": len(regional),
        "stress_exclusion_note": "Regional summary excludes near-edge load transfer zones at z=11..15 and 25..29 mm plus the global maximum retains all support/load singularities. It is a descriptive mesh-dependent statistic, not an allowable check.",
        "max_abs_stress_components_mpa": [float(np.abs(stresses[:, i]).max()) for i in range(2, 8)],
        "solver_version": version_text.strip(),
        "support_model": "ideal axial displacement fixed on ring nodes; x/y rigid-mode restraints only",
        "interpretation": "screen only; support is ideal bonded ring, not actual adhesive/body qualification",
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def solve_braced_buckling_case(
    step_path: Path,
    output: Path,
    mesh_size_mm: float,
    factored_load_n: float,
    ring_stations_mm: list[float],
    ring_thickness_mm: float = 3.0,
    young_mpa: float = 1000.0,
    poisson: float = 0.25,
    mode_count: int = 5,
) -> dict[str, Any]:
    """Linear buckle the braced motor-mount frame against aft-ring support."""
    gmsh: Any = importlib.import_module("gmsh")
    if gmsh.__version__ != "4.15.2":
        raise ValueError("FEA requires pinned Gmsh 4.15.2")
    if len(ring_stations_mm) < 1 or min(mesh_size_mm, factored_load_n, young_mpa) <= 0:
        raise ValueError("Buckling geometry, load, and material inputs must be positive")
    output.mkdir(parents=True, exist_ok=False)
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("braced_mount_linear_buckling")
        gmsh.model.occ.importShapes(str(step_path), highestDimOnly=True)
        gmsh.model.occ.synchronize()
        if not gmsh.model.getEntities(3):
            raise ValueError("Imported STEP contains no solid volume")
        gmsh.option.setNumber("Mesh.MeshSizeMin", mesh_size_mm)
        gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size_mm)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.optimize("HighOrder")
        gmsh.write(str(output / "mesh.msh"))
        coords, elements = _quadratic_tets(gmsh)
        ring_station = max(ring_stations_mm)
        support_faces: list[int] = []
        load_faces: list[tuple[int, np.ndarray]] = []
        radial_coverage: list[float] = []
        for _, face in gmsh.model.getEntities(2):
            bb = gmsh.model.getBoundingBox(2, face)
            zmin, zmax = float(bb[2]), float(bb[5])
            if (
                zmin >= ring_station - 1e-5
                and zmax <= ring_station + ring_thickness_mm + 1e-5
                and abs(zmin - ring_station) < 1e-4
            ):
                support_faces.append(face)
            if (zmax - zmin) > 5:
                center = np.asarray(gmsh.model.occ.getCenterOfMass(2, face))
                for angle in (0.0, 120.0, 240.0):
                    rad = np.deg2rad(angle)
                    radial = np.asarray([np.cos(rad), np.sin(rad)])
                    tangent = np.asarray([-np.sin(rad), np.cos(rad)])
                    planar = center[:2] - 28.5 * radial
                    if (
                        abs(float(np.dot(planar, radial))) < 0.75
                        and abs(abs(float(np.dot(planar, tangent))) - 6.0) < 0.2
                    ):
                        load_faces.append((face, radial))
                        radial_coverage.extend(
                            float(np.dot(coords[n][:2], radial))
                            for n in _nodes_on_face(gmsh, face)
                            if n in coords and 11.0 <= coords[n][2] <= 29.0
                        )
                        break
        if not support_faces or not load_faces:
            raise ValueError("Aft-ring support or forefinger flank faces were not found")
        load_weights: dict[int, float] = {}
        load_area_mm2 = 0.0
        active_faces = 0
        for face, _ in load_faces:
            stypes, _, sconn = gmsh.model.mesh.getElements(2, face)
            face_area = 0.0
            for typ, conn in zip(stypes, sconn):
                if typ != 9:
                    raise ValueError("Expected six-node quadratic triangular facets")
                for tri in np.asarray(conn).reshape(-1, 6):
                    weights, area = _clipped_quadratic_triangle_weights(tri, coords, 11.0, 29.0)
                    load_area_mm2 += area
                    face_area += area
                    for node, weight in weights.items():
                        load_weights[node] = load_weights.get(node, 0.0) + weight
            if face_area > 1e-10:
                active_faces += 1
        support_surface_nodes = {
            node for face in support_faces for node in _nodes_on_face(gmsh, face)
        }
        max_radius = max(float(np.linalg.norm(coords[node][:2])) for node in support_surface_nodes)
        aft_nodes = sorted(
            node
            for node in support_surface_nodes
            if abs(float(np.linalg.norm(coords[node][:2])) - max_radius) < 0.25
            and ring_station - 1e-5 <= coords[node][2] <= ring_station + ring_thickness_mm + 1e-5
        )
        if not aft_nodes or not load_weights:
            raise ValueError("Aft support or load quadrature selected zero nodes")
        gmsh.finalize()
    except BaseException:
        gmsh.finalize()
        raise

    weights = {node: val for node, val in load_weights.items() if node in coords}
    total_weight = sum(weights.values())
    loads = {node: factored_load_n * val / total_weight for node, val in weights.items()}
    anchor = min(aft_nodes, key=lambda node: float(np.linalg.norm(coords[node])))
    second = max(aft_nodes, key=lambda node: abs(float(coords[node][0] - coords[anchor][0])))
    if abs(float(coords[second][0] - coords[anchor][0])) < 1e-3:
        raise ValueError("Cannot remove in-plane rigid modes with the selected aft ring")

    deck = ["*HEADING", "Braced mount linear buckling N mm MPa", "*NODE"]
    deck += [f"{n}, {x[0]:.12g}, {x[1]:.12g}, {x[2]:.12g}" for n, x in coords.items()]
    deck += ["*ELEMENT,TYPE=C3D10,ELSET=ALL"] + [
        f"{n}, " + ", ".join(map(str, row)) for n, row in elements.items()
    ]
    deck += ["*NSET,NSET=ALL"] + [
        ", ".join(map(str, ids[i : i + 12]))
        for ids in [sorted(coords)]
        for i in range(0, len(ids), 12)
    ]
    deck += ["*NSET,NSET=AFT"] + [
        ", ".join(map(str, aft_nodes[i : i + 12])) for i in range(0, len(aft_nodes), 12)
    ]
    deck += [
        "*MATERIAL,NAME=PLYWOOD",
        "*ELASTIC",
        f"{young_mpa:.12g},{poisson:.12g}",
        "*SOLID SECTION,ELSET=ALL,MATERIAL=PLYWOOD",
        "*BOUNDARY",
        "AFT,3,3,0",
        f"{anchor},1,2,0",
        f"{second},2,2,0",
        "*STEP",
        "*STATIC",
        "*CLOAD",
    ]
    deck += [f"{node},3,{force:.12g}" for node, force in loads.items()]
    deck += [
        "*NODE PRINT,NSET=AFT",
        "RF",
        "*END STEP",
        "*STEP",
        "*BUCKLE",
        f"{mode_count},0.001",
        "*CLOAD",
    ]
    deck += [f"{node},3,{force:.12g}" for node, force in loads.items()]
    deck += ["*NODE FILE", "U", "*END STEP"]
    (output / "case.inp").write_text("\n".join(deck) + "\n")
    solver_version = _run_ccx(output)
    factors = buckling_factors_from_dat(output / "case.dat", mode_count)
    positive = [factor for factor in factors if factor > 1e-8]
    if not positive:
        raise RuntimeError(f"No positive buckling factors; raw factors={factors}")
    reactions: list[list[float]] = []
    recording = False
    for line in (output / "case.dat").read_text(errors="replace").splitlines():
        lower = line.lower()
        if "forces (" in lower:
            recording = "set aft" in lower
            continue
        if recording:
            fields = line.split()
            try:
                int(fields[0])
                reactions.append([float(value) for value in fields])
            except (ValueError, IndexError):
                if reactions:
                    recording = False
    reaction_z = sum(row[3] for row in reactions)
    frd_exists = (output / "case.frd").is_file()
    report = {
        "mesh_size_mm": mesh_size_mm,
        "node_count": len(coords),
        "element_count": len(elements),
        "load_n": factored_load_n,
        "load_sign": "+Z, foreplate to aft-ring compression",
        "load_resultant_n": sum(loads.values()),
        "load_face_count": active_faces,
        "load_patch_area_mm2": load_area_mm2,
        "load_patch_radial_projection_bounds_mm": [min(radial_coverage), max(radial_coverage)],
        "load_patch_axial_bounds_mm": [11.0, 29.0],
        "support": {
            "aft_ring_station_mm": ring_station,
            "axial_fixed_nodes": len(aft_nodes),
            "intermediate_rings_laterally_and_axially_free": True,
            "reaction_z_n_from_static_reference_step": reaction_z,
            "reaction_balance_n": reaction_z + factored_load_n,
            "minimal_rigid_mode_anchors": {
                "origin_xy_fixed_node": anchor,
                "second_node_y_fixed": second,
                "delta_x_mm": float(coords[second][0] - coords[anchor][0]),
            },
        },
        "eigenvalue_factors": factors,
        "critical_positive_factor": min(positive),
        "capacity_at_reference_load_n": min(positive) * factored_load_n,
        "required_factor": 3.0,
        "screen_factor_margin": min(positive) / 3.0 - 1.0,
        "mode_classification": {
            "negative_factors": [value for value in factors if value < -1e-8],
            "near_zero_factors": [value for value in factors if abs(value) <= 1e-8],
            "positive_factors": positive,
            "note": "Nonpositive or near-zero factors are retained as possible numerical/mechanism modes, not discarded.",
        },
        "mode_shape_file": "case.frd" if frd_exists else None,
        "mode_shape_exported": frd_exists,
        "solver_version": solver_version,
        "basis": "Linear eigenvalue buckling; each factor multiplies the specified factored reference load. No geometric imperfection/nonlinear postbuckling, bond, body, or torsional failure modeled.",
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def euler_buckling_fixture(output: Path, young_mpa: float = 1000.0) -> dict[str, Any]:
    """Cantilever solid-column fixture compared with Euler's fixed-free load."""
    gmsh: Any = importlib.import_module("gmsh")
    size_mm, width_mm, length_mm = 4.0, 8.0, 200.0
    output.mkdir(parents=True, exist_ok=False)
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("euler_buckling_fixture")
        gmsh.model.occ.addBox(-width_mm / 2, -width_mm / 2, 0, width_mm, width_mm, length_mm)
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMin", size_mm)
        gmsh.option.setNumber("Mesh.MeshSizeMax", size_mm)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.optimize("HighOrder")
        gmsh.write(str(output / "mesh.msh"))
        coords, elements = _quadratic_tets(gmsh)
        bottom: set[int] = set()
        top_faces: list[int] = []
        for _, face in gmsh.model.getEntities(2):
            bb = gmsh.model.getBoundingBox(2, face)
            if abs(bb[2]) < 1e-5 and abs(bb[5]) < 1e-5:
                bottom.update(_nodes_on_face(gmsh, face))
            if abs(bb[2] - length_mm) < 1e-5 and abs(bb[5] - length_mm) < 1e-5:
                top_faces.append(face)
        weights: dict[int, float] = {}
        for face in top_faces:
            types, _, connectivity = gmsh.model.mesh.getElements(2, face)
            for typ, conn in zip(types, connectivity):
                if typ != 9:
                    raise ValueError("Expected quadratic top triangles for Euler fixture")
                for tri in np.asarray(conn).reshape(-1, 6):
                    shape_weights, _ = _clipped_quadratic_triangle_weights(
                        tri, coords, -1.0, length_mm + 1.0
                    )
                    for node, value in shape_weights.items():
                        weights[node] = weights.get(node, 0.0) + value
        gmsh.finalize()
    except BaseException:
        gmsh.finalize()
        raise
    reference = 1.0
    sum_weights = sum(weights.values())
    loads = {node: -reference * value / sum_weights for node, value in weights.items()}
    deck = ["*HEADING", "Euler fixed-free buckling verification N mm MPa", "*NODE"]
    deck += [f"{n}, {x[0]:.12g}, {x[1]:.12g}, {x[2]:.12g}" for n, x in coords.items()]
    deck += ["*ELEMENT,TYPE=C3D10,ELSET=ALL"] + [
        f"{n}, " + ", ".join(map(str, row)) for n, row in elements.items()
    ]
    deck += ["*NSET,NSET=BASE"] + [
        ", ".join(map(str, sorted(bottom)[i : i + 12])) for i in range(0, len(bottom), 12)
    ]
    deck += [
        "*MATERIAL,NAME=ELASTIC",
        "*ELASTIC",
        f"{young_mpa:.12g},0.25",
        "*SOLID SECTION,ELSET=ALL,MATERIAL=ELASTIC",
        "*BOUNDARY",
        "BASE,1,3,0",
        "*STEP",
        "*BUCKLE",
        "5,0.001",
        "*CLOAD",
    ]
    deck += [f"{node},3,{force:.12g}" for node, force in loads.items()]
    deck += ["*NODE FILE", "U", "*END STEP"]
    (output / "case.inp").write_text("\n".join(deck) + "\n")
    solver_version = _run_ccx(output)
    factors = buckling_factors_from_dat(output / "case.dat", 5)
    inertia_mm4 = width_mm * width_mm**3 / 12
    euler_n = np.pi**2 * young_mpa * inertia_mm4 / (4 * length_mm**2)
    calculated_n = min(value for value in factors if value > 0) * reference
    result = {
        "fixture": "C3D10 prismatic solid cantilever under end compression",
        "solver_version": solver_version,
        "mesh_size_mm": size_mm,
        "node_count": len(coords),
        "element_count": len(elements),
        "eigenvalue_factors": factors,
        "reference_load_n": reference,
        "euler_fixed_free_critical_n": float(euler_n),
        "calculated_critical_n": float(calculated_n),
        "relative_error": abs(float(calculated_n) / float(euler_n) - 1.0),
        "passed": abs(float(calculated_n) / float(euler_n) - 1.0) < 0.1,
        "mode_shape_file": "case.frd" if (output / "case.frd").exists() else None,
    }
    (output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
