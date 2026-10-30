"""Quadratic shell static/modal screens of the actual single-fin planform.

Gmsh independent analysis meshes, CalculiX S6 shell, N/mm/MPa/tonne units.
Consistent uniform pressure loads put zero force on triangle vertices and A*p/3
on midside nodes. Actual root tabs are included and idealized clamped at/below the
body tangent. The root attachment is an upper-stiffness assumption, not a bond
qualification. Regional stresses exclude the first two thicknesses from the ideal
clamp and remain distinct from whole-part/root-joint strength.
Reference: CalculiX 2.23 S6 shell, NODE/EL PRINT and FREQUENCY documentation;
Euler-Bernoulli uniform cantilever u=FL^3/(8EI), f1=1.875104^2/(2piL^2)*sqrt(EI/mu).
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from src.analysis.fea import solver_path
from src.vehicle.schema import Part


def run_shell(
    folder: Path,
    part: Part | None,
    size_mm: float,
    young_pa: float = 2e9,
    density_kg_m3: float = 550.0,
    force_n: float = 0.001,
    stiffness_fraction: float = 1.0,
) -> dict[str, Any]:
    gmsh: Any = importlib.import_module("gmsh")
    if gmsh.__version__ != "4.15.2":
        raise ValueError("Pinned Gmsh 4.15.2 required")
    if part:
        g = part.geometry
        o = part.cad.parameters if part.cad else {}
        span, root, tip, sweep, thickness = [
            g[k] * 1000 for k in ["span_m", "root_chord_m", "tip_chord_m", "sweep_m", "thickness_m"]
        ]
    else:
        span, root, tip, sweep, thickness = 100.0, 10.0, 10.0, 0.0, 1.0
        o = {}
    folder.mkdir(parents=True, exist_ok=True)
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("single_fin_shell")
        coords = [(0.0, 0.0), (span, sweep), (span, sweep + tip), (0.0, root)]
        points = [gmsh.model.occ.addPoint(x, y, 0) for x, y in coords]
        lines = [gmsh.model.occ.addLine(a, b) for a, b in zip(points, points[1:] + points[:1])]
        face = gmsh.model.occ.addPlaneSurface([gmsh.model.occ.addCurveLoop(lines)])
        if o.get("tab_depth_mm"):
            tab = gmsh.model.occ.addRectangle(
                -o["tab_depth_mm"], o["tab_offset_mm"], 0, o["tab_depth_mm"], o["tab_length_mm"]
            )
            # Keep a conforming internal edge on the body tangent so the
            # idealized root constraint does not move with the mesh.
            gmsh.model.occ.fragment([(2, face)], [(2, tab)])
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMin", size_mm)
        gmsh.option.setNumber("Mesh.MeshSizeMax", size_mm)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.model.mesh.generate(2)
        gmsh.write(str(folder / "mesh.msh"))
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        nodes = {int(n): np.array(x) for n, x in zip(tags, np.asarray(xyz).reshape(-1, 3))}
        types, tags, conn = gmsh.model.mesh.getElements(2)
        elements = {}
        for kind, ids, data in zip(types, tags, conn):
            if kind != 9:
                raise ValueError("Expected Gmsh six-node triangles")
            for id, row in zip(ids, np.asarray(data).reshape(-1, 6)):
                elements[int(id)] = [int(n) for n in row]
    finally:
        gmsh.finalize()
    exposed_area = span * (root + tip) / 2
    pressure = force_n / exposed_area
    loads: dict[int, float] = {}
    centroids = {}
    for id, tri in elements.items():
        xyz = np.array([nodes[n] for n in tri[:3]])
        center = xyz.mean(axis=0)
        centroids[id] = center
        if center[0] <= 0:
            continue
        area = float(np.linalg.norm(np.cross(xyz[1] - xyz[0], xyz[2] - xyz[0])) / 2)
        for n in tri[3:]:
            loads[n] = loads.get(n, 0.0) + pressure * area / 3
    if abs(sum(loads.values()) - force_n) > abs(force_n) * 1e-8:
        raise ValueError("Fin traction resultant mismatch")
    fixed = [n for n, x in nodes.items() if x[0] <= 1e-7]
    deck = ["*HEADING", "Single-fin/strip static and modal screen; N mm MPa tonne", "*NODE"]
    deck += [f"{n}, " + ", ".join(f"{v:.12g}" for v in x) for n, x in nodes.items()]
    deck += ["*ELEMENT,TYPE=S6,ELSET=FIN"] + [
        f"{n}, " + ", ".join(map(str, c)) for n, c in elements.items()
    ]
    for label, ids in [("FIXED", fixed), ("NALL", list(nodes))]:
        deck += [f"*NSET,NSET={label}"] + [
            ", ".join(map(str, ids[i : i + 12])) for i in range(0, len(ids), 12)
        ]
    deck += [
        "*MATERIAL,NAME=LOWERBOUND",
        "*ELASTIC",
        f"{young_pa*stiffness_fraction*1e-6:.12g},0.25",
        "*DENSITY",
        f"{density_kg_m3*1e-12:.12g}",
        "*SHELL SECTION,ELSET=FIN,MATERIAL=LOWERBOUND",
        str(thickness),
        "*BOUNDARY",
        "FIXED,1,6,0",
        "*STEP",
        "*STATIC",
        "*CLOAD",
    ]
    deck += [f"{n},3,{f:.12g}" for n, f in loads.items()]
    deck += [
        "*NODE PRINT,NSET=NALL",
        "U",
        "*NODE PRINT,NSET=FIXED",
        "RF",
        "*EL PRINT,ELSET=FIN",
        "S",
        "*NODE FILE",
        "U",
        "*END STEP",
        "*STEP",
        "*FREQUENCY",
        "6",
        "*NODE PRINT,NSET=NALL",
        "U",
        "*NODE FILE",
        "U",
        "*END STEP",
    ]
    inp = folder / "case.inp"
    inp.write_text("\n".join(deck) + "\n")
    mesh = {
        "frame": "FEM X=span from body tangent; Y=chord aft from fin front; Z=plate normal; mm",
        "nodes": [{"id": n, "xyz_mm": x.tolist()} for n, x in nodes.items()],
        "elements": [{"id": n, "type": "S6", "nodes": c} for n, c in elements.items()],
        "part_id": part.id if part else "known-strip",
        "coverage": "One fin, ideal clamped root/tab; other fins are not resolved by this field.",
    }
    (folder / "analysis-mesh.json").write_text(json.dumps(mesh) + "\n")
    result: dict[str, Any] = {
        "part_id": part.id if part else "known-strip",
        "part_shape_sha256": part.cad_mass.shape_sha256 if part and part.cad_mass else None,
        "gmsh": "4.15.2",
        "size_mm": size_mm,
        "nodes": len(nodes),
        "elements": len(elements),
        "force_n": force_n,
        "stiffness_fraction": stiffness_fraction,
        "youngs_pa": young_pa,
        "density_kg_m3": density_kg_m3,
        "input_sha256": hashlib.sha256(inp.read_bytes()).hexdigest(),
        "mesh_sha256": hashlib.sha256((folder / "analysis-mesh.json").read_bytes()).hexdigest(),
        "attachment": "Ideal clamp at and inside the body tangent; flexible root/bond not qualified",
        "solver_executed": False,
        "flight_ready": False,
    }
    ccx = solver_path()
    if not ccx:
        raise FileNotFoundError("CalculiX2.23 required for executed fin screen")
    proc = subprocess.run(
        [ccx, "-i", "case"],
        cwd=folder,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
        env={**os.environ, "OMP_NUM_THREADS": "1"},
    )
    (folder / "solver.log").write_text(proc.stdout + proc.stderr)
    if proc.returncode or not (folder / "case.dat").exists():
        raise RuntimeError("Fin shell solve failed; inspect solver.log")
    displacements: list[list[list[float]]] = []
    stress: list[list[float]] = []
    reaction: list[list[float]] = []
    frequencies: list[float] = []
    section = None
    eigen = False
    modal_started = False
    for line in (folder / "case.dat").read_text().splitlines():
        low = line.lower()
        compact = "".join(line.upper().split())
        if "EIGENVALUEOUTPUT" in compact:
            eigen = True
            section = None
            continue
        if "EIGENVALUENUMBER" in compact:
            modal_started = True
            eigen = False
            section = None
            continue
        if "displacements (" in low:
            displacements.append([])
            section = "U"
            eigen = False
            continue
        if "forces (" in low:
            section = "RF"
            eigen = False
            continue
        if "stresses (" in low:
            section = "S" if not modal_started else None
            eigen = False
            continue
        fields = line.split()
        if not fields:
            if eigen and frequencies:
                eigen = False
            if section == "U" and displacements[-1]:
                section = None
            if section == "RF" and reaction:
                section = None
            if section == "S" and stress:
                section = None
            continue
        try:
            int(fields[0])
            count = 8 if section == "S" else 5 if eigen else 4
            values = [float(x.replace("D", "E")) for x in fields[:count]]
        except ValueError:
            continue
        if eigen and len(values) >= 4:
            frequencies.append(values[3])
        elif section == "U":
            displacements[-1].append(values)
        elif section == "RF":
            reaction.append(values)
        elif section == "S":
            stress.append(values)
    if not displacements or not displacements[0] or not frequencies or not stress:
        raise RuntimeError("Static/modal output parsing incomplete")
    static = displacements[0]
    maxdef = float(max(abs(r[3]) for r in static))
    # CalculiX RF is the nodal force. Subtract CLOAD already applied at
    # constrained nodes to obtain the support reaction (K*u-F).
    reported_rf = sum(r[3] for r in reaction)
    support_cload = sum(loads.get(n, 0) for n in fixed)
    support_reaction = reported_rf - support_cload
    balance = abs(support_reaction + force_n)
    # S6 is expanded to a 3D shell: tensor output remains integration-point data.
    regional = [r for r in stress if centroids[int(r[0])][0] >= 2 * thickness]

    def vm(r: list[float]) -> float:
        xx, yy, zz, xy, xz, yz = r[2:8]
        return float(
            np.sqrt(
                0.5 * ((xx - yy) ** 2 + (yy - zz) ** 2 + (zz - xx) ** 2)
                + 3 * (xy**2 + xz**2 + yz**2)
            )
        )

    peak = float(max(vm(r) for r in regional))
    (folder / "static-fields.json").write_text(
        json.dumps(
            {
                "displacements_node_mm": static,
                "stress_integration_point_mpa": stress,
                "stress_components": ["xx", "yy", "zz", "xy", "xz", "yz"],
                "regional_exclusion_span_mm": 2 * thickness,
                "von_mises_usage": "Diagnostic isotropic stress only, not an anisotropic plywood failure criterion.",
            }
        )
        + "\n"
    )
    (folder / "mode-fields.json").write_text(
        json.dumps(
            {
                "frequencies_hz": frequencies,
                "node_vectors": displacements[1:],
                "normalization": "Solver eigenvectors have arbitrary/mass normalization; not actual displacement amplitude.",
            }
        )
        + "\n"
    )
    result.update(
        solver_executed=True,
        max_displacement_m=maxdef * 1e-3,
        regional_von_mises_pa=peak * 1e6,
        frequencies_hz=frequencies,
        equilibrium_error_n=balance,
        support_reaction_n=support_reaction,
        reported_support_nodal_force_n=reported_rf,
        applied_support_cload_n=support_cload,
    )
    if part is None:
        length = span * 0.001
        width = root * 0.001
        t = thickness * 0.001
        ei = young_pa * width * t**3 / 12
        mu = density_kg_m3 * width * t
        expected = force_n * length**3 / (8 * ei)
        f1 = 1.8751040687**2 / (2 * np.pi * length**2) * np.sqrt(ei / mu)
        result.update(
            analytic_deflection_m=expected,
            analytic_first_mode_hz=f1,
            known_case_passed=abs(maxdef * 0.001 / expected - 1) < 0.05
            and abs(frequencies[0] / f1 - 1) < 0.05
            and balance < 1e-7,
        )
    (folder / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
