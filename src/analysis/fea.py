"""Pinned Gmsh quadratic-tetra export and CalculiX verification boundary.

Units in solver decks: N, mm, MPa. Export converts no display triangles into FEA.
Gmsh type-11 tetra nodes 9/10 are swapped for CalculiX/Abaqus C3D10 ordering.
A traction-loaded axial bar with a Poisson-compatible supported end verifies
units, element mapping, reactions, displacement and regional stress analytically.
Reference: Gmsh 4.15 element ordering; CalculiX 2.23 C3D10/BOUNDARY/CLOAD manuals;
Hooke law u=FL/(AE), sigma=F/A. This fixture is not rocket strength evidence.
"""

from __future__ import annotations

import importlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import numpy as np


def solver_path() -> str | None:
    candidates = [
        os.environ.get("CCX"),
        shutil.which("ccx"),
        "/opt/homebrew/opt/calculix@2.23/bin/ccx",
    ]
    return next((str(p) for p in candidates if p and Path(p).is_file()), None)


def axial_bar(folder: Path, size_mm: float) -> dict[str, Any]:
    gmsh: Any = importlib.import_module("gmsh")
    if gmsh.__version__ != "4.15.2":
        raise ValueError("FEA requires pinned Gmsh 4.15.2")
    folder.mkdir(parents=True, exist_ok=True)
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("axial_bar_known_case")
        gmsh.model.occ.addBox(0, 0, 0, 5, 5, 50)
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMin", size_mm)
        gmsh.option.setNumber("Mesh.MeshSizeMax", size_mm)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.model.mesh.generate(3)
        gmsh.write(str(folder / "mesh.msh"))
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        nodes = {int(n): np.array(x) for n, x in zip(tags, np.asarray(xyz).reshape(-1, 3))}
        types, etags, connectivity = gmsh.model.mesh.getElements(3)
        elements = {}
        for kind, ids, conn in zip(types, etags, connectivity):
            if kind != 11:
                raise ValueError("Expected complete quadratic tetrahedra")
            for id, row in zip(ids, np.asarray(conn).reshape(-1, 10)):
                elements[int(id)] = [int(n) for n in row[[0, 1, 2, 3, 4, 5, 6, 7, 9, 8]]]
        loads: dict[int, float] = {}
        for _, face in gmsh.model.getEntities(2):
            bounds = gmsh.model.getBoundingBox(2, face)
            if abs(bounds[2] - 50) < 1e-5 and abs(bounds[5] - 50) < 1e-5:
                stypes, _, sconn = gmsh.model.mesh.getElements(2, face)
                for kind, conn in zip(stypes, sconn):
                    if kind != 9:
                        raise ValueError("Expected quadratic triangular traction surface")
                    for tri in np.asarray(conn).reshape(-1, 6):
                        a, b, c = [nodes[int(n)] for n in tri[:3]]
                        area = float(np.linalg.norm(np.cross(b - a, c - a)) / 2)
                        for n in tri[3:]:
                            loads[int(n)] = loads.get(int(n), 0.0) + area / 25 / 3
    finally:
        gmsh.finalize()
    fixed = [n for n, x in nodes.items() if abs(x[2]) < 1e-7]
    top = [n for n, x in nodes.items() if abs(x[2] - 50) < 1e-7]
    origin = min(fixed, key=lambda n: float(np.linalg.norm(nodes[n])))
    on_x = min(fixed, key=lambda n: float(np.linalg.norm(nodes[n] - [5, 0, 0])))
    if abs(sum(loads.values()) - 1) > 1e-8:
        raise ValueError("Traction resultant does not sum to one newton")
    deck = ["*HEADING", "Axial bar analytic verification: N mm MPa", "*NODE"]
    deck += [f"{n}, " + ", ".join(f"{v:.12g}" for v in x) for n, x in nodes.items()]
    deck += ["*ELEMENT,TYPE=C3D10,ELSET=ALL"] + [
        f"{n}, " + ", ".join(map(str, conn)) for n, conn in elements.items()
    ]
    for name, ids in [("SUPPORT", fixed), ("TOP", top)]:
        deck += [f"*NSET,NSET={name}"] + [
            ", ".join(map(str, ids[i : i + 12])) for i in range(0, len(ids), 12)
        ]
    deck += [
        "*MATERIAL,NAME=ELASTIC",
        "*ELASTIC",
        "1500., 0.3",
        "*SOLID SECTION,ELSET=ALL,MATERIAL=ELASTIC",
        "*BOUNDARY",
        "SUPPORT,3,3,0",
        f"{origin},1,2,0",
        f"{on_x},2,2,0",
        "*STEP",
        "*STATIC",
        "*CLOAD",
    ]
    deck += [f"{n},3,{f:.12g}" for n, f in loads.items()]
    deck += [
        "*NODE PRINT,NSET=TOP",
        "U",
        "*NODE PRINT,NSET=SUPPORT",
        "RF",
        "*EL PRINT,ELSET=ALL",
        "S",
        "*END STEP",
    ]
    inp = folder / "case.inp"
    inp.write_text("\n".join(deck) + "\n")
    summary = {
        "fixture": "axial bar; no rocket geometry",
        "gmsh_version": gmsh.__version__,
        "mesh_size_mm": size_mm,
        "node_count": len(nodes),
        "element_count": len(elements),
        "load_n": sum(loads.values()),
        "expected_displacement_mm": 50 / (25 * 1500),
        "expected_stress_mpa": 1 / 25,
        "mesh_generated": True,
        "solver_executed": False,
    }
    ccx = solver_path()
    if not ccx:
        summary["unavailable_reason"] = (
            "CalculiX 2.23 executable absent; mesh/deck generation is not solver validation."
        )
    else:
        version = subprocess.run([ccx, "-v"], capture_output=True, text=True, check=False)
        version_text = version.stdout + version.stderr
        if "2.23" not in version_text:
            raise ValueError("Expected pinned CalculiX 2.23")
        result = subprocess.run(
            [ccx, "-i", "case"],
            cwd=folder,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
            env={**os.environ, "OMP_NUM_THREADS": "1"},
        )
        (folder / "solver.log").write_text(result.stdout + result.stderr)
        if result.returncode or not (folder / "case.dat").exists():
            raise RuntimeError("CalculiX known-case failed; inspect solver.log")
        sections: dict[str, list[list[float]]] = {"U": [], "RF": [], "S": []}
        section = None
        for line in (folder / "case.dat").read_text().splitlines():
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
                    values = [float(x) for x in fields]
                except ValueError:
                    continue
                sections[section].append(values)
        if not all(sections.values()):
            raise RuntimeError("Known-case output sections incomplete")
        displacement = float(np.mean([r[3] for r in sections["U"]]))
        reaction = float(sum(r[3] for r in sections["RF"]))
        central = {
            n for n, conn in elements.items() if 15 < np.mean([nodes[x][2] for x in conn[:4]]) < 35
        }
        stresses = [r[4] for r in sections["S"] if int(r[0]) in central]
        stress = float(np.mean(stresses))
        errors = {
            "displacement_relative": abs(displacement / summary["expected_displacement_mm"] - 1),
            "stress_relative": abs(stress / summary["expected_stress_mpa"] - 1),
            "equilibrium_n": abs(reaction + 1),
        }
        summary.update(
            solver_executed=True,
            ccx_version=version_text.strip(),
            displacement_mm=displacement,
            regional_stress_mpa=stress,
            support_reaction_n=reaction,
            errors=errors,
            passed=errors["displacement_relative"] < 0.01
            and errors["stress_relative"] < 0.02
            and errors["equilibrium_n"] < 1e-5,
        )
    (folder / "report.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
