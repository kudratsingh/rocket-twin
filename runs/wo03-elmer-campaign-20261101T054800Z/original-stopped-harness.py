"""Known-answer Elmer I/O: no custom numerical solver or vehicle analysis.

Converts preserved C3D4 fixture inputs to Elmer's native tetrahedra and boundary
faces. HeatSolveVec evaluates the exact spatial Robin sink at integration
points. This script generates/reads inputs and fields only; output heat and
local balance remain unavailable until a validated native output exists.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import re
import resource
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_deck(
    path: Path,
) -> tuple[dict[int, tuple[float, float, float]], dict[int, tuple[int, int, int, int]]]:
    nodes: dict[int, tuple[float, float, float]] = {}
    cells: dict[int, tuple[int, int, int, int]] = {}
    mode = ""
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("*"):
            mode = (
                "node"
                if line.upper().startswith("*NODE,")
                else ("element" if line.upper().startswith("*ELEMENT,") else "")
            )
            continue
        if mode == "node":
            row = line.split(",")
            nodes[int(row[0])] = tuple(map(float, row[1:4]))
        elif mode == "element":
            row = line.split(",")
            cells[int(row[0])] = tuple(map(int, row[1:5]))
    if list(nodes) != list(range(1, len(nodes) + 1)) or list(cells) != list(
        range(1, len(cells) + 1)
    ):
        raise ValueError("Source nodes/elements not contiguous")
    return nodes, cells


def sub(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, ...]:
    return tuple(x - y for x, y in zip(a, b, strict=True))


def cross(a: tuple[float, ...], b: tuple[float, ...]) -> tuple[float, float, float]:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def dot(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def exterior(
    nodes: dict[int, tuple[float, float, float]],
    cells: dict[int, tuple[int, int, int, int]],
    dims: list[float],
) -> list[tuple[int, int, tuple[int, int, int]]]:
    faces: dict[tuple[int, ...], list[tuple[int, tuple[int, int, int], int]]] = {}
    for eid, cell in cells.items():
        p0, p1, p2, p3 = (nodes[i] for i in cell)
        det = dot(sub(p1, p0), cross(sub(p2, p0), sub(p3, p0)))
        if det <= 0:
            raise ValueError("Nonpositive source tetrahedron")
        for omit in range(4):
            face = tuple(v for j, v in enumerate(cell) if j != omit)
            faces.setdefault(tuple(sorted(face)), []).append((eid, face, cell[omit]))
    boundary = []
    for entries in faces.values():
        if len(entries) > 2:
            raise ValueError("Nonmanifold tetrahedron face")
        if len(entries) == 2:
            continue
        eid, face, opposite = entries[0]
        xyz = [nodes[i] for i in face]
        side = []
        for axis, length in enumerate(dims):
            if all(abs(p[axis]) < 1e-14 for p in xyz):
                side.append(2 * axis + 1)
            if all(abs(p[axis] - length) < 1e-14 for p in xyz):
                side.append(2 * axis + 2)
        if len(side) != 1:
            raise ValueError("Boundary triangle missing unique box side")
        if dot(cross(sub(xyz[1], xyz[0]), sub(xyz[2], xyz[0])), sub(nodes[opposite], xyz[0])) > 0:
            face = (face[0], face[2], face[1])
        boundary.append((side[0], eid, face))
    return boundary


def enrich_quadratic(
    nodes: dict[int, tuple[float, float, float]],
    cells: dict[int, tuple[int, int, int, int]],
    boundary: list[tuple[int, int, tuple[int, int, int]]],
) -> tuple[
    dict[int, tuple[float, float, float]],
    dict[int, tuple[int, ...]],
    list[tuple[int, int, tuple[int, ...]]],
]:
    """Elmer 510 edges 12,23,31,14,24,34; 306 edges 12,23,31."""
    allnodes = dict(nodes)
    edge_ids = {}

    def midpoint(a: int, b: int) -> int:
        edge = tuple(sorted((a, b)))
        if edge not in edge_ids:
            edge_ids[edge] = len(allnodes) + 1
            allnodes[edge_ids[edge]] = tuple(
                (x + y) / 2 for x, y in zip(nodes[a], nodes[b], strict=True)
            )
        return edge_ids[edge]

    qcells = {
        eid: tuple(c)
        + tuple(midpoint(c[i], c[j]) for i, j in ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)))
        for eid, c in cells.items()
    }
    qboundary = [
        (side, eid, tuple(f) + tuple(midpoint(f[i], f[j]) for i, j in ((0, 1), (1, 2), (2, 0))))
        for side, eid, f in boundary
    ]
    for _, eid, face in qboundary:
        if not set(face).issubset(qcells[eid]):
            raise ValueError("Quadratic boundary is not owned by its parent tetrahedron")
    for (a, b), node in edge_ids.items():
        if any(allnodes[node][j] != (nodes[a][j] + nodes[b][j]) / 2 for j in range(3)):
            raise ValueError("Quadratic edge midpoint is incorrect")
    if len({tuple(round(v, 14) for v in p) for p in allnodes.values()}) != len(allnodes):
        raise ValueError("Different edges yielded coincident midpoint nodes")
    return allnodes, qcells, qboundary


def quadratic_quadrature_check() -> dict[str, float]:
    """Check the source 306 six-point and 510 27-point rules on monomials."""
    import numpy as np

    u = [
        0.091576213509771,
        0.816847572980459,
        0.091576213509771,
        0.445948490915965,
        0.108103018168070,
        0.445948490915965,
    ]
    v = [
        0.091576213509771,
        0.091576213509771,
        0.816847572980459,
        0.445948490915965,
        0.445948490915965,
        0.108103018168070,
    ]
    w = [0.109951743655322] * 3 + [0.223381589678011] * 3
    tri_error = 0.0
    for i in range(5):
        for j in range(5 - i):
            numerical = sum(ww / 2 * x**i * y**j for x, y, ww in zip(u, v, w, strict=True))
            exact = math.factorial(i) * math.factorial(j) / math.factorial(i + j + 2)
            tri_error = max(tri_error, abs(numerical - exact))
    gp, gw = np.polynomial.legendre.leggauss(3)
    tet_error = 0.0
    for i in range(3):
        for j in range(3 - i):
            for k in range(3 - i - j):
                total = 0.0
                for ia, ib, ic in itertools.product(range(3), repeat=3):
                    r, s, t = ((gp[z] + 1) / 2 for z in (ia, ib, ic))
                    x = r * (1 - t) * (1 - s)
                    y = s * (1 - t)
                    z = t
                    weight = gw[ia] * gw[ib] * gw[ic] / 8 * (1 - t) ** 2 * (1 - s)
                    total += weight * x**i * y**j * z**k
                exact = (
                    math.factorial(i)
                    * math.factorial(j)
                    * math.factorial(k)
                    / math.factorial(i + j + k + 3)
                )
                tet_error = max(tet_error, abs(total - exact))
    if max(tri_error, tet_error) > 1e-13:
        raise ValueError("Native quadrature monomial check failed")
    return {
        "triangle306_degree4_max_abs_moment_error": tri_error,
        "tetra510_degree2_max_abs_moment_error": tet_error,
    }


def write_mesh(
    folder: Path,
    nodes: dict[int, tuple[float, float, float]],
    cells: dict[int, tuple[int, int, int, int]],
    boundary: list[tuple[int, int, tuple[int, int, int]]],
) -> None:
    folder.mkdir()
    (folder / "mesh.header").write_text(
        f"{len(nodes)} {len(cells)} {len(boundary)}\n2\n306 {len(boundary)}\n510 {len(cells)}\n"
    )
    (folder / "mesh.nodes").write_text(
        "".join(f"{i} -1 " + " ".join(f"{v:.17g}" for v in p) + "\n" for i, p in nodes.items())
    )
    (folder / "mesh.elements").write_text(
        "".join(f"{i} 1 510 " + " ".join(map(str, c)) + "\n" for i, c in cells.items())
    )
    (folder / "mesh.boundary").write_text(
        "".join(
            f"{i} {side} {eid} 0 306 " + " ".join(map(str, face)) + "\n"
            for i, (side, eid, face) in enumerate(boundary, 1)
        )
    )


def matc_sink(side: int, cfg: dict[str, Any], h: float) -> str:
    a = cfg["case_b"]["amplitude_k"] / cfg["dimensions_m"][2] ** 2
    k = cfg["conductivity_w_m_k"]
    nx = {1: -1, 2: 1}.get(side, 0)
    nz = {5: -1, 6: 1}.get(side, 0)
    # tx(0)=x, tx(1)=z. Fixed side normals are source geometry data.
    return f"{cfg['case_b']['base_k']:.17g}+({a:.17g})*(tx(1)*tx(1)-tx(0)*tx(0))+({2*a*k/h:.17g})*({nz}*tx(1)-({nx})*tx(0))"


def sif(case: str, cfg: dict[str, Any], linear_solver: dict[str, str] | None = None) -> str:
    a = cfg["case_a"]
    linear_solver = linear_solver or {"kind": "Direct", "method": "UMFPACK"}
    if linear_solver != {"kind": "Direct", "method": "UMFPACK"}:
        raise ValueError("Undeclared linear solver")
    h = cfg["case_b"]["h_w_m2_k"] if case == "B" else cfg["case_b_strong_h_w_m2_k"]
    text = [
        "Header",
        "  CHECK KEYWORDS Warn",
        '  Mesh DB "." "mesh"',
        "End",
        "Simulation",
        "  Coordinate System = Cartesian",
        "  Coordinate Mapping(3) = 1 2 3",
        "  Simulation Type = Steady State",
        "  Steady State Max Iterations = 1",
        "  Output Intervals = 1",
        "End",
        "Body 1",
        "  Equation = 1",
        "  Material = 1",
        "End",
        "Equation 1",
        "  Active Solvers(3) = 1 2 3",
        "End",
        "Material 1",
        f"  Heat Conductivity = Real {cfg['conductivity_w_m_k']:.17g}",
        "End",
        "Solver 1",
        "  Equation = Heat Equation",
        "  Variable = Temperature",
        '  Procedure = File "HeatSolveVec" "HeatSolver"',
        "  Linear System Solver = Direct",
        "  Linear System Direct Method = UMFPACK",
        "  Linear System Max Iterations = 2000",
        "  Linear System Convergence Tolerance = 1.0e-12",
        "  Linear System Abort Not Converged = Logical True",
        "  Steady State Convergence Tolerance = 1.0e-12",
        "End",
        "Solver 2",
        "  Equation = Result Output",
        '  Procedure = File "ResultOutputSolve" "ResultOutputSolver"',
        '  Output File Name = "field"',
        "  Vtu Format = Logical True",
        "  Binary Output = Logical True",
        "  Single Precision = Logical False",
        "End",
    ]
    text += [
        "Solver 3",
        "  Exec Solver = After All",
        "  Equation = SaveScalars",
        '  Procedure = File "SaveData" "SaveScalars"',
        '  Filename = "diffusive-flux.dat"',
        "  Save Flux Range = Logical False",
    ]
    for side in range(1, 7):
        text += [
            f'  Variable {side} = String "Temperature"',
            f'  Operator {side} = String "diffusive flux"',
            f'  Coefficient {side} = String "Heat Conductivity"',
            f'  Mask Name {side} = String "side_{side}"',
        ]
    text += ["End"]
    if case == "A":
        text += [
            "Boundary Condition 1",
            "  Target Boundaries(1) = 1",
            "  side_1 = Logical True",
            f"  Temperature = Real {a['hot_prescribed_k']:.17g}",
            "End",
            "Boundary Condition 2",
            "  Target Boundaries(1) = 2",
            "  side_2 = Logical True",
            f"  External Temperature = Real {a['cold_bulk_k']:.17g}",
            f"  Heat Transfer Coefficient = Real {a['h_w_m2_k']:.17g}",
            "End",
        ]
        for side in range(3, 7):
            text += [
                f"Boundary Condition {side}",
                f"  Target Boundaries(1) = {side}",
                f"  side_{side} = Logical True",
                "End",
            ]
    else:
        for side in range(1, 7):
            text += [
                f"Boundary Condition {side}",
                f"  Target Boundaries(1) = {side}",
                f"  side_{side} = Logical True",
                f"  Heat Transfer Coefficient = Real {h:.17g}",
                "  External Temperature = Variable Coordinate 1, Coordinate 3",
                f'    Real MATC "{matc_sink(side,cfg,h)}"',
                "  External Temperature At IP = Logical True",
                "  Heat Transfer Coefficient At IP = Logical True",
                "End",
            ]
    return "\n".join(text) + "\n"


def robin_quadrature_error(
    nodes: dict[int, tuple[float, float, float]],
    boundary: list[tuple[int, int, tuple[int, int, int]]],
    cfg: dict[str, Any],
    h: float,
) -> dict[str, float]:
    """Analytic polynomial face load vs default three-point triangle integration.

    This is an input quadrature diagnostic, not a numerical field solve. Triangle
    barycentric moments are E[prod(lambda_i**alpha_i)] = 2 prod(alpha_i!)/(sum(alpha_i)+2)!.
    """
    exact_nodal = {i: 0.0 for i in nodes}
    approx_nodal = {i: 0.0 for i in nodes}
    a = cfg["case_b"]["amplitude_k"] / cfg["dimensions_m"][2] ** 2
    t0 = cfg["case_b"]["base_k"]
    k = cfg["conductivity_w_m_k"]
    bary = [(2 / 3, 1 / 6, 1 / 6), (1 / 6, 2 / 3, 1 / 6), (1 / 6, 1 / 6, 2 / 3)]

    def moment(indices: tuple[int, ...]) -> float:
        counts = [indices.count(i) for i in range(3)]
        return 2 * math.prod(math.factorial(x) for x in counts) / math.factorial(len(indices) + 2)

    for side, _, face in boundary:
        p = [nodes[i] for i in face]
        area = (
            math.sqrt(
                dot(
                    cross(sub(p[1], p[0]), sub(p[2], p[0])), cross(sub(p[1], p[0]), sub(p[2], p[0]))
                )
            )
            / 2
        )
        nx = {1: -1, 2: 1}.get(side, 0)
        nz = {5: -1, 6: 1}.get(side, 0)
        coefficient = 2 * a * k / h
        for i, node in enumerate(face):
            avg = t0 / 3
            for j in range(3):
                avg += coefficient * (nz * p[j][2] - nx * p[j][0]) * moment((i, j))
                for m in range(3):
                    avg += a * (p[j][2] * p[m][2] - p[j][0] * p[m][0]) * moment((i, j, m))
            exact_nodal[node] += h * area * avg
            estimate = 0.0
            for lam in bary:
                x = sum(lam[j] * p[j][0] for j in range(3))
                z = sum(lam[j] * p[j][2] for j in range(3))
                tb = t0 + a * (z * z - x * x) + coefficient * (nz * z - nx * x)
                estimate += lam[i] * tb / 3
            approx_nodal[node] += h * area * estimate
    errors = [approx_nodal[i] - exact_nodal[i] for i in nodes]
    return {
        "max_abs_assembled_nodal_load_error_w": max(map(abs, errors)),
        "sum_abs_nodal_load_error_w": sum(map(abs, errors)),
        "signed_net_load_error_w": sum(errors),
        "faces": len(boundary),
    }


def prepare(cfg: dict[str, Any], out: Path, config_path: Path) -> dict[str, Any]:
    reference = ROOT / cfg["reference"]
    if sha(reference) != cfg["reference_sha256"]:
        raise ValueError("Reference config hash mismatch")
    if sha(ROOT / cfg["criteria"]) != cfg["criteria_sha256"]:
        raise ValueError("Verification criteria hash mismatch")
    casecfg = yaml.safe_load(reference.read_text())
    before = {
        str(p.relative_to(ROOT)): sha(p)
        for p in [
            reference,
            ROOT / cfg["criteria"],
            Path(__file__),
            config_path,
        ]
    }
    sources = {}
    for n, source in cfg["meshes"].items():
        p = ROOT / source["path"]
        if sha(p) != source["sha256"]:
            raise ValueError(f"Original input hash mismatch {n}")
        nodes, cells = read_deck(p)
        boundary = exterior(nodes, cells, casecfg["dimensions_m"])
        if (
            len(nodes) != (int(n) + 1) ** 3
            or len(cells) != 6 * int(n) ** 3
            or len(boundary) != 12 * int(n) ** 2
        ):
            raise ValueError("Unexpected mesh refinement counts")
        if any(sum(side == i for side, _, _ in boundary) != 2 * int(n) ** 2 for i in range(1, 7)):
            raise ValueError("Missing or duplicated boundary side")
        for side, _, face in boundary:
            p0, p1, p2 = (nodes[i] for i in face)
            normal = cross(sub(p1, p0), sub(p2, p0))
            axis = (side - 1) // 2
            direction = -1 if side % 2 else 1
            if direction * normal[axis] <= 0:
                raise ValueError("Boundary face orientation inconsistent with box")
        before[str(p.relative_to(ROOT))] = sha(p)
        sources[int(n)] = (nodes, cells, boundary)
    out.mkdir(parents=True, exist_ok=False)
    for case in ("A", "B", "B_strong"):
        for n, (nodes, cells, boundary) in sources.items():
            folder = out / case / str(n)
            folder.mkdir(parents=True)
            qnodes, qcells, qboundary = enrich_quadratic(nodes, cells, boundary)
            write_mesh(folder / "mesh", qnodes, qcells, qboundary)
            (folder / "case.sif").write_text(sif(case, casecfg, cfg["linear_solver"]))
    after = {key: sha(ROOT / key) for key in before}
    if before != after:
        raise ValueError("Input changed while preparing")
    record = {
        "mode": "prepare-only",
        "linear_solver": cfg["linear_solver"],
        "solver_invoked": False,
        "source_sha256": before,
        "inputs_unchanged": True,
        "cases": ["A", "B", "B_strong"],
        "levels": list(sources),
        "outputs_are_unexecuted": True,
        "native_quadratic_quadrature": quadratic_quadrature_check(),
        "quadratic_mesh_counts": {
            n: len(enrich_quadratic(a, b, c)[0]) for n, (a, b, c) in sources.items()
        },
        "mesh_counts": {
            n: {"nodes": len(a), "tets": len(b), "boundary_triangles": len(c)}
            for n, (a, b, c) in sources.items()
        },
        "case_B_reservoir_decomposition_is_not_direct_boundary": True,
        "default_3_point_quadrature_error": {
            case: {
                n: robin_quadrature_error(
                    nodes,
                    boundary,
                    casecfg,
                    (
                        casecfg["case_b"]["h_w_m2_k"]
                        if case == "B"
                        else casecfg["case_b_strong_h_w_m2_k"]
                    ),
                )
                for n, (nodes, _, boundary) in sources.items()
            }
            for case in ("B", "B_strong")
        },
        "quadrature_note": "analytic polynomial integrated against linear boundary basis vs default three-point triangle; not a solved temperature or reservoir-heat error",
        "generated_file_sha256": {
            str(p.relative_to(out)): sha(p) for p in sorted(out.rglob("*")) if p.is_file()
        },
    }
    (out / "preflight.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def expected_field(points: Any, case: str, cfg: dict[str, Any]) -> Any:
    if case == "A":
        a = cfg["case_a"]
        q = (a["hot_prescribed_k"] - a["cold_bulk_k"]) / (
            cfg["dimensions_m"][0] / cfg["conductivity_w_m_k"] + 1 / a["h_w_m2_k"]
        )
        return a["hot_prescribed_k"] - q * points[:, 0] / cfg["conductivity_w_m_k"]
    return (
        cfg["case_b"]["base_k"]
        + cfg["case_b"]["amplitude_k"]
        * (points[:, 2] ** 2 - points[:, 0] ** 2)
        / cfg["dimensions_m"][2] ** 2
    )


def continuous_p2_bound(case: str, cfg: dict[str, Any], max_nodal_error: float) -> dict[str, Any]:
    """Affine P2 interpolation bound for these exactly representable fields only."""
    lx, _, lz = cfg["dimensions_m"]
    if case == "A":
        params = cfg["case_a"]
        q = (params["hot_prescribed_k"] - params["cold_bulk_k"]) / (
            lx / cfg["conductivity_w_m_k"] + 1 / params["h_w_m2_k"]
        )
        low = params["hot_prescribed_k"] - q * lx / cfg["conductivity_w_m_k"]
        high = params["hot_prescribed_k"]
        wall_low, wall_high = params["cold_bulk_k"], params["hot_prescribed_k"]
    else:
        base = cfg["case_b"]["base_k"]
        a = cfg["case_b"]["amplitude_k"] / lz**2
        low, high = base - a * lx**2, base + a * lz**2
        h = cfg["case_b"]["h_w_m2_k"] if case == "B" else cfg["case_b_strong_h_w_m2_k"]
        wall_low, wall_high = envelope(cfg, h)
    bound = 2 * max_nodal_error
    lo, hi = low - bound, high + bound
    return {
        "continuous_error_bound_k": bound,
        "exact_reference_min_k": low,
        "exact_reference_max_k": high,
        "continuous_min_lower_bound_k": lo,
        "continuous_max_upper_bound_k": hi,
        "effective_boundary_envelope_k": [wall_low, wall_high],
        "continuous_envelope_status": (
            "certified_by_bound"
            if lo >= wall_low and hi <= wall_high
            else "unavailable_bound_straddles"
        ),
        "scope": "affine straight P2 tetrahedra and exactly representable analytic A/B fields only; not an actual-baffle bound",
    }


def read_vtu(
    path: Path, source_nodes: dict[int, tuple[float, float, float]], case: str, cfg: dict[str, Any]
) -> dict[str, Any]:
    import numpy as np
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy

    vtk.vtkSMPTools.Initialize(1)
    vtk.vtkMultiThreader.SetGlobalMaximumNumberOfThreads(1)
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(path))
    reader.Update()
    grid = reader.GetOutput()
    coords = vtk_to_numpy(grid.GetPoints().GetData())
    data = grid.GetPointData()
    names = [data.GetArrayName(i) for i in range(data.GetNumberOfArrays())]
    matches = [name for name in names if name and name.lower() == "temperature"]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one Temperature array; got {names}")
    arr = vtk_to_numpy(data.GetArray(matches[0]))
    if (
        arr.dtype != np.float64
        or arr.ndim != 1
        or len(arr) != len(source_nodes)
        or len(coords) != len(source_nodes)
    ):
        raise ValueError("VTU field dtype/count mismatch")
    if not np.isfinite(coords).all() or not np.isfinite(arr).all():
        raise ValueError("Non-finite field")
    lookup = {tuple(round(v, 12) for v in p): i for i, p in enumerate(coords)}
    if len(lookup) != len(coords):
        raise ValueError("VTU coordinates are not unique")
    ids = [lookup[tuple(round(v, 12) for v in xyz)] for xyz in source_nodes.values()]
    expected_xyz = np.asarray(list(source_nodes.values()))
    if np.max(np.abs(coords[ids] - expected_xyz)) > 1e-12:
        raise ValueError("VTU coordinate mapping failed")
    values = arr[ids]
    exact = expected_field(expected_xyz, case, cfg)
    return {
        "VTK_version": vtk.vtkVersion.GetVTKVersion(),
        "VTK_SMP_estimated_threads": vtk.vtkSMPTools.GetEstimatedNumberOfThreads(),
        "VTK_global_max_threads": vtk.vtkMultiThreader.GetGlobalMaximumNumberOfThreads(),
        "field_type": str(arr.dtype),
        "VTU_sha256": sha(path),
        "max_nodal_error_k": float(np.max(np.abs(values - exact))),
        "temperature_min_k": float(values.min()),
        "temperature_max_k": float(values.max()),
        "temperatures_k": values.tolist(),
        "native_surface_heat_w": None,
        "global_balance_w": None,
        "local_balance_w": None,
        "acceptance": False,
    }


def exact_outward_conduction(case: str, cfg: dict[str, Any]) -> dict[str, float]:
    lx, ly, lz = cfg["dimensions_m"]
    k = cfg["conductivity_w_m_k"]
    if case == "A":
        a = cfg["case_a"]
        heat = (a["hot_prescribed_k"] - a["cold_bulk_k"]) / (lx / k + 1 / a["h_w_m2_k"]) * ly * lz
        return {"1": -heat, "2": heat, "3": 0.0, "4": 0.0, "5": 0.0, "6": 0.0}
    a = cfg["case_b"]["amplitude_k"] / lz**2
    return {
        "1": 0.0,
        "2": 2 * k * a * lx * ly * lz,
        "3": 0.0,
        "4": 0.0,
        "5": 0.0,
        "6": -2 * k * a * lz * lx * ly,
    }


def read_diffusive_flux(folder: Path) -> dict[str, Any]:
    """Parse native per-BC n·k∇T using SaveScalars' own column names."""
    path = folder / "diffusive-flux.dat"
    names = folder / "diffusive-flux.dat.names"
    if not path.is_file() or not names.is_file():
        raise ValueError("Missing native diffusive flux output or metadata")
    columns = {}
    for line in names.read_text().splitlines():
        m = re.match(
            r"\s*(\d+):\s*diffusive flux:\s*temperature\s+over bc\s+(\d+)\s*$", line, re.IGNORECASE
        )
        if m:
            col, side = map(int, m.groups())
            if side in columns:
                raise ValueError("Duplicate native flux label")
            columns[side] = col - 1
    if set(columns) != set(range(1, 7)) or sorted(columns.values()) != list(range(6)):
        raise ValueError("Native flux labels do not uniquely identify six boundaries")
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    if len(lines) != 1:
        raise ValueError("Ambiguous native flux time/output rows")
    values = [float(x.replace("D", "E")) for x in lines[0].split()]
    if len(values) != 6 or not all(math.isfinite(x) for x in values):
        raise ValueError("Malformed native flux values")
    return {
        "outward_conductive_heat_w": {str(side): -values[col] for side, col in columns.items()},
        "sign": "source reports n dot k grad(T); negated for outward Fourier heat",
        "file_sha256": sha(path),
        "names_sha256": sha(names),
        "status": "native output; field/flux accuracy requires known-case comparison, not Robin wall heat",
    }


def envelope(cfg: dict[str, Any], h: float) -> tuple[float, float]:
    # Exact extrema of each quadratic boundary rectangle, including stationary points.
    dims = cfg["dimensions_m"]
    k = cfg["conductivity_w_m_k"]
    a = cfg["case_b"]["amplitude_k"] / dims[2] ** 2
    values = []
    for axis in range(3):
        for sign in (-1, 1):
            normal = [0, 0, 0]
            normal[axis] = sign
            choices = []
            for j, L in enumerate(dims):
                if j == axis:
                    choices.append([0.0 if sign < 0 else L])
                else:
                    c = [0.0, L]
                    stationary = -k / h * normal[j]
                    if j in (0, 2) and 0 < stationary < L:
                        c.append(stationary)
                    choices.append(c)
            for x, y, z in itertools.product(*choices):
                values.append(
                    cfg["case_b"]["base_k"]
                    + a * (z * z - x * x)
                    + 2 * a * k / h * (z * normal[2] - x * normal[0])
                )
    return min(values), max(values)


def execute(cfg: dict[str, Any], out: Path, config_path: Path) -> None:
    # This explicit flag is used only after the primary declares the packet.
    budget = cfg["budget"]
    if budget != {"threads": 1, "seconds_per_case_all_levels": 120, "total_cpu_seconds": 600}:
        raise ValueError("Declared budget changed")
    parent_cpu_start = time.process_time()
    preflight = prepare(cfg, out, config_path)
    root = ROOT / cfg["elmer_home"]
    binary = ROOT / cfg["solver"]
    libraries = [
        root / "share/elmersolver/lib" / name
        for name in (
            "HeatSolveVec.dylib",
            "ResultOutputSolve.dylib",
            "SaveData.dylib",
            "elements.def",
        )
    ]
    pins = {str(p.relative_to(ROOT)): sha(p) for p in [binary, *libraries]}
    casecfg = yaml.safe_load((ROOT / cfg["reference"]).read_text())
    criteria = yaml.safe_load((ROOT / cfg["criteria"]).read_text())["verification"]
    env = os.environ.copy()
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "BLIS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env[name] = "1"
    env["ELMER_HOME"] = str(root.resolve())
    env["ELMER_LIB"] = str((root / "share/elmersolver/lib").resolve())
    overall = {
        "status": "incomplete",
        "tool_sha256": pins,
        "cases": {},
        "cpu_s": 0.0,
        "criteria": criteria,
        "accepted": False,
        "native_surface_heat_w": None,
        "global_balance_w": None,
        "local_balance_w": None,
        "curved_geometry": "not_executed",
    }
    record = out / "record.json"
    try:
        for case in ("A", "B", "B_strong"):
            start = time.monotonic()
            rows = []
            overall["cases"][case] = rows
            for n in (2, 4, 8):
                remain_wall = budget["seconds_per_case_all_levels"] - (time.monotonic() - start)
                remain_cpu = (
                    budget["total_cpu_seconds"]
                    - overall["cpu_s"]
                    - (time.process_time() - parent_cpu_start)
                )
                if remain_wall <= 1 or remain_cpu <= 1:
                    raise TimeoutError("declared packet budget exhausted")
                folder = out / case / str(n)
                before = resource.getrusage(resource.RUSAGE_CHILDREN)
                tick = time.monotonic()
                limit = max(1, math.floor(min(remain_wall, remain_cpu)))

                def restrict(limit_value: int = limit) -> None:
                    resource.setrlimit(resource.RLIMIT_CPU, (limit_value, limit_value))

                try:
                    p = subprocess.run(
                        [str(binary.resolve()), "case.sif"],
                        cwd=folder,
                        env=env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=remain_wall,
                        check=False,
                        preexec_fn=restrict,
                    )
                    log = p.stdout
                    code = p.returncode
                except subprocess.TimeoutExpired as exc:
                    (folder / "solver.log").write_bytes(exc.stdout or b"")
                    after = resource.getrusage(resource.RUSAGE_CHILDREN)
                    used = after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime
                    overall["cpu_s"] += used
                    rows.append(
                        {
                            "level": n,
                            "timed_out": True,
                            "cpu_s": used,
                            "wall_s": time.monotonic() - tick,
                        }
                    )
                    raise TimeoutError("case wall cap reached") from exc
                after = resource.getrusage(resource.RUSAGE_CHILDREN)
                used = after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime
                overall["cpu_s"] += used
                (folder / "solver.log").write_text(log)
                row = {
                    "level": n,
                    "returncode": code,
                    "wall_s": time.monotonic() - tick,
                    "cpu_s": used,
                    "child_cumulative_peak_rss": after.ru_maxrss,
                }
                rows.append(row)
                record.write_text(json.dumps(overall, indent=2) + "\n")
                if (
                    code != 0
                    or "FATAL" in log.upper()
                    or re.search(r"did not converge|failed to converge", log, re.IGNORECASE)
                ):
                    raise RuntimeError("Elmer failure or nonconvergence; stop")
                files = list(folder.glob("field*.vtu"))
                if len(files) != 1:
                    raise ValueError("Expected one VTU result; stop")
                linear_nodes, linear_cells = read_deck(ROOT / cfg["meshes"][n]["path"])
                nodes, _, _ = enrich_quadratic(
                    linear_nodes,
                    linear_cells,
                    exterior(linear_nodes, linear_cells, casecfg["dimensions_m"]),
                )
                result = read_vtu(files[0], nodes, case, casecfg)
                result.update(continuous_p2_bound(case, casecfg, result["max_nodal_error_k"]))
                result["absolute_field_within_existing_1e-7K"] = (
                    result["max_nodal_error_k"] < criteria["temperature_absolute_tolerance_k"]
                )
                if case == "A":
                    result["exact_nodal_temperature_pass"] = result[
                        "absolute_field_within_existing_1e-7K"
                    ]
                else:
                    h = (
                        casecfg["case_b"]["h_w_m2_k"]
                        if case == "B"
                        else casecfg["case_b_strong_h_w_m2_k"]
                    )
                    low, high = envelope(casecfg, h)
                    result["effective_boundary_envelope_k"] = [low, high]
                    result["below_boundary_min_k"] = max(0.0, low - result["temperature_min_k"])
                    result["above_boundary_max_k"] = max(0.0, result["temperature_max_k"] - high)
                    result["nodal_no_envelope_violation"] = (
                        result["below_boundary_min_k"] == 0 and result["above_boundary_max_k"] == 0
                    )
                result["native_diffusive_flux"] = read_diffusive_flux(folder)
                expected_heat = exact_outward_conduction(case, casecfg)
                observed = result["native_diffusive_flux"]["outward_conductive_heat_w"]
                result["native_diffusive_flux"]["reference_outward_conduction_w"] = expected_heat
                result["native_diffusive_flux"]["max_reference_error_w"] = max(
                    abs(observed[k] - expected_heat[k]) for k in expected_heat
                )
                result["native_diffusive_flux"]["sum_outward_conduction_w"] = sum(observed.values())
                result["native_diffusive_flux"]["sum_is_not_robin_or_algebra_balance"] = True
                if case == "A":
                    tolerance = criteria["heat_absolute_tolerance_w"] + criteria[
                        "heat_relative_tolerance"
                    ] * max(abs(v) for v in expected_heat.values())
                    result["native_diffusive_flux"]["A_reference_tolerance_w"] = tolerance
                    result["native_diffusive_flux"]["A_reference_comparison_pass"] = (
                        result["native_diffusive_flux"]["max_reference_error_w"] < tolerance
                    )
                row.update(result)
                record.write_text(json.dumps(overall, indent=2) + "\n")
            if case != "A":
                errors = [r["max_nodal_error_k"] for r in rows]
                rows[-1]["nodal_error_strictly_decreases"] = errors[0] > errors[1] > errors[2]
                rows[-1][
                    "nodal_monotonicity_interpretation"
                ] = "literal comparison only; not a failure gate at roundoff"
                mid_linear, mid_cells = read_deck(ROOT / cfg["meshes"][4]["path"])
                fine_linear, fine_cells = read_deck(ROOT / cfg["meshes"][8]["path"])
                middle_nodes, _, _ = enrich_quadratic(
                    mid_linear, mid_cells, exterior(mid_linear, mid_cells, casecfg["dimensions_m"])
                )
                fine_nodes, _, _ = enrich_quadratic(
                    fine_linear,
                    fine_cells,
                    exterior(fine_linear, fine_cells, casecfg["dimensions_m"]),
                )
                fine_by_xyz = {
                    tuple(round(v, 12) for v in xyz): rows[2]["temperatures_k"][i]
                    for i, xyz in enumerate(fine_nodes.values())
                }
                changes = [
                    abs(
                        rows[1]["temperatures_k"][i] - fine_by_xyz[tuple(round(v, 12) for v in xyz)]
                    )
                    for i, xyz in enumerate(middle_nodes.values())
                ]
                rows[-1]["nested_field_change_fraction_of_100K"] = (
                    max(changes) / casecfg["case_b"]["amplitude_k"]
                )
                rows[-1]["nested_field_change_below_5pct"] = (
                    rows[-1]["nested_field_change_fraction_of_100K"]
                    < criteria["convergence_relative_tolerance"]
                )
                rows[-1]["existing_raw_C_convergence"] = None
                rows[-1]["approximate_case_pass"] = False
        overall["status"] = "completed_fields_heat_and_balances_unavailable"
    finally:
        overall["parent_cpu_s"] = time.process_time() - parent_cpu_start
        overall["parent_peak_rss_bytes_macos"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        overall["memory_note"] = (
            "parent and cumulative child peak RSS are separate maxima, not a measured simultaneous sum"
        )
        overall["total_cpu_s"] = overall["cpu_s"] + overall["parent_cpu_s"]
        overall["tool_sha256_after"] = {
            str(p.relative_to(ROOT)): sha(p) for p in [binary, *libraries]
        }
        overall["tool_unchanged"] = overall["tool_sha256"] == overall["tool_sha256_after"]
        overall["input_sha256_after"] = {key: sha(ROOT / key) for key in preflight["source_sha256"]}
        overall["inputs_unchanged"] = overall["input_sha256_after"] == preflight["source_sha256"]
        record.write_text(json.dumps(overall, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/studies/wo03-elmer-thermal-comparison.yaml"
    )
    parser.add_argument("--preset", choices=["tiny"], default="tiny")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare-only", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    if args.execute:
        execute(cfg, args.output or ROOT / cfg["output"], args.config)
    else:
        out = args.output or Path(tempfile.mkdtemp(prefix="wo03-elmer-preflight-")) / "prepared"
        prepare(cfg, out, args.config)
        print(out)


if __name__ == "__main__":
    main()
