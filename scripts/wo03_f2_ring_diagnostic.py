"""Bounded notched-ring elastic-support diagnostic, not installed recovery acceptance.
SPRING1/C3D10 per CalculiX manual; output equilibrium checked independently.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import gmsh
import numpy as np

from src.analysis.fea import solver_path

BASE = Path("build/wo03-g80-f2-ring-diagnostic-v1")
STEP = Path("build/wo03-g80-f2-local-cad-v2/notched_forward_ring.step")


def case(h):
    out = BASE / str(h)
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.model.add("F2_ring_component_diagnostic")
        ring = gmsh.model.occ.importShapes(str(STEP))
        wash = []
        for a in [30, 210]:
            x, y = 23 * math.cos(math.radians(a)), 23 * math.sin(math.radians(a))
            o = gmsh.model.occ.addCylinder(x, y, 12.2, 0, 0, 1, 7)
            i = gmsh.model.occ.addCylinder(x, y, 12.2, 0, 0, 1, 2.25)
            v, _ = gmsh.model.occ.cut([(3, o)], [(3, i)])
            wash += v
        gmsh.model.occ.fragment(ring, wash)
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMin", h)
        gmsh.option.setNumber("Mesh.MeshSizeMax", h)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.model.mesh.generate(3)
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        nodes = {int(n): v for n, v in zip(tags, np.asarray(xyz).reshape(-1, 3))}
        elements = {}
        sets = {"WOOD": [], "STEEL": []}
        for dim, vol in gmsh.model.getEntities(3):
            material = "STEEL" if gmsh.model.occ.getCenterOfMass(dim, vol)[2] > 12.2 else "WOOD"
            types, ids, conn = gmsh.model.mesh.getElements(3, vol)
            for typ, ee, cc in zip(types, ids, conn):
                if typ != 11:
                    raise ValueError("quadratic tetra required")
                for eid, row in zip(ee, np.asarray(cc).reshape(-1, 10)):
                    elements[int(eid)] = [int(n) for n in row[[0, 1, 2, 3, 4, 5, 6, 7, 9, 8]]]
                    sets[material].append(int(eid))
        quality = gmsh.model.mesh.getElementQualities(list(elements), "minSJ")
        if min(quality) <= 0:
            (out / "invalid-mesh.json").write_text(
                json.dumps(
                    {"minimum_scaled_jacobian": float(min(quality)), "solver_executed": False}
                )
            )
            raise ValueError("invalid quadratic mesh; stop before solver")
        weights = {k: {} for k in ["outer", "inner", "tabs", "load0", "load1"]}
        for _, face in gmsh.model.getEntities(2):
            types, _, conn = gmsh.model.mesh.getElements(2, face)
            for typ, cc in zip(types, conn):
                if typ != 9:
                    continue
                for tri in np.asarray(cc).reshape(-1, 6):
                    q = np.array([nodes[int(n)] for n in tri[:3]])
                    center = q.mean(axis=0)
                    r = math.hypot(center[0], center[1])
                    key = None
                    if np.max(abs(q[:, 2] - 13.2)) < 1e-5:
                        key = "load0" if center[1] > 0 else "load1"
                    elif np.max(abs(q[:, 2] - 4.8)) < 1e-5:
                        key = "tabs"
                    elif abs(r - 32.3) < 0.15 and np.ptp(q[:, 2]) > 1e-4:
                        key = "outer"
                    elif abs(r - 15.8845) < 0.15 and np.ptp(q[:, 2]) > 1e-4:
                        key = "inner"
                    if key:
                        area = float(np.linalg.norm(np.cross(q[1] - q[0], q[2] - q[0])) / 2)
                        for n in tri[3:]:
                            weights[key][int(n)] = weights[key].get(int(n), 0) + area / 3
        if any(sum(v.values()) <= 0 for v in weights.values()):
            raise ValueError("missing load/support surface")
        gmsh.write(str(out / "mesh.msh"))
    finally:
        gmsh.finalize()
    # These finite stiffnesses represent explicitly hypothetical subassembly extensions.
    # They do not resolve global recovery inertia or justify a rigid ground support.
    stiffness = {
        "outer": 500 * math.pi * (33.401**2 - 32.512**2) / 100,
        "inner": 500 * math.pi * (15.6845**2 - 14.5845**2) / 165,
        "tabs": 3 * 1000 * 6 * 17.5165 / 109.8,
    }
    deck = ["*HEADING", "F2 notched ring finite-spring COMPONENT DIAGNOSTIC N mm MPa", "*NODE"] + [
        f"{n}," + ",".join(f"{x:.12g}" for x in p) for n, p in nodes.items()
    ]
    deck += ["*ELEMENT,TYPE=C3D10,ELSET=SOLIDS"] + [
        f"{e}," + ",".join(map(str, conn)) for e, conn in elements.items()
    ]
    for name, ids in sets.items():
        deck += ["*ELSET,ELSET=" + name] + [
            ",".join(map(str, ids[i : i + 12])) for i in range(0, len(ids), 12)
        ]
    deck += [
        "*MATERIAL,NAME=PLY_ESTIMATE",
        "*ELASTIC",
        "1000.,0.25",
        "*MATERIAL,NAME=STEEL",
        "*ELASTIC",
        "200000.,0.3",
        "*SOLID SECTION,ELSET=WOOD,MATERIAL=PLY_ESTIMATE",
        "*SOLID SECTION,ELSET=STEEL,MATERIAL=STEEL",
    ]
    springs = []
    eid = max(elements) + 1
    for group in ["outer", "inner", "tabs"]:
        total = sum(weights[group].values())
        for node, area in weights[group].items():
            k = stiffness[group] * area / total
            name = f"K{eid}"
            deck += [
                "*ELEMENT,TYPE=SPRING1,ELSET=" + name,
                f"{eid},{node}",
                "*SPRING,ELSET=" + name,
                "3",
                f"{k:.12e}",
            ]
            springs.append((group, node, k, area))
            eid += 1
    # Only three in-plane rigid motions removed. Axial/tilting stiffness is elastic.
    n0 = min(nodes, key=lambda n: np.linalg.norm(nodes[n] - [32.3, 0, 0]))
    n1 = min(nodes, key=lambda n: np.linalg.norm(nodes[n] - [-32.3, 0, 0]))
    deck += ["*BOUNDARY", f"{n0},1,2,0", f"{n1},2,2,0", "*NSET,NSET=ALLN"] + [
        ",".join(map(str, list(nodes)[i : i + 12])) for i in range(0, len(nodes), 12)
    ]
    for name, shares in [("seventy_thirty", [0.7, 0.3]), ("single_anchor", [1.0, 0.0])]:
        deck += ["*STEP", "*STATIC", "*CLOAD,OP=NEW"]
        for index, share in enumerate(shares):
            total = sum(weights["load" + str(index)].values())
            deck += [
                f"{n},3,{-100*share*area/total:.12e}"
                for n, area in weights["load" + str(index)].items()
                if share
            ]
        deck += ["*NODE PRINT,NSET=ALLN", "U", "*EL PRINT,ELSET=WOOD", "S", "*END STEP"]
    (out / "case.inp").write_text("\n".join(deck) + "\n")
    ccx = solver_path()
    proc = subprocess.run(
        [ccx, "-i", "case"],
        cwd=out,
        capture_output=True,
        check=False,
        text=True,
        timeout=120,
        env={**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1"},
    )
    (out / "solver.log").write_text(proc.stdout + proc.stderr)
    if proc.returncode:
        raise RuntimeError("CalculiX failure; stop, inspect log")
    phases = []
    mode = None
    phase = None
    for line in (out / "case.dat").read_text().splitlines():
        low = line.lower()
        if "displacements (" in low:
            phase = {"u": {}, "stress": []}
            phases.append(phase)
            mode = "u"
            continue
        if "stresses (" in low:
            mode = "s"
            continue
        try:
            r = [float(x) for x in line.split()]
        except ValueError:
            continue
        if not r or phase is None:
            continue
        if mode == "u" and len(r) == 4:
            phase["u"][int(r[0])] = r[1:]
        elif mode == "s" and len(r) == 8:
            phase["stress"].append(r[2:])
    if len(phases) != 2:
        raise ValueError("expected2 load phases")
    rows = []
    for phase in phases:
        u = phase["u"]
        stress = np.asarray(phase["stress"])
        xx, yy, zz, xy, xz, yz = stress.T
        vm = np.sqrt(
            ((xx - yy) ** 2 + (yy - zz) ** 2 + (zz - xx) ** 2) / 2
            + 3 * (xy * xy + xz * xz + yz * yz)
        )
        reaction = {g: 0.0 for g in stiffness}
        bondpeak = {g: 0.0 for g in stiffness}
        for group, n, k, area in springs:
            force = -k * u[n][2]
            reaction[group] += force
            bondpeak[group] = max(bondpeak[group], abs(force) / area)
        rows.append(
            {
                "load_N": 100,
                "support_reactions_N": reaction,
                "force_balance_relative_error": abs(sum(reaction.values()) - 100) / 100,
                "max_displacement_mm": max(abs(p[2]) for p in u.values()),
                "wood_VM_max_MPa": float(vm.max()),
                "wood_VM_p95_MPa": float(np.quantile(vm, 0.95)),
                "estimated_interface_normal_peak_MPa": bondpeak,
            }
        )
    report = {
        "h_mm": h,
        "nodes": len(nodes),
        "elements": len(elements),
        "surface_area_mm2": {k: sum(v.values()) for k, v in weights.items()},
        "support_stiffness_N_mm": stiffness,
        "cases": rows,
        "wall_s": time.monotonic() - start,
        "scope": "linear component fixture only; spring extensions/washer bonding/isotropic plywood estimated, not installed recovery acceptance",
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    BASE.mkdir(parents=True, exist_ok=False)
    reports = []
    failure = None
    start = time.monotonic()
    try:
        for h in [3.0, 2.0, 1.4]:
            reports.append(case(h))
            print("complete", h, flush=True)
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.TimeoutExpired) as e:
        failure = repr(e)
    summary = {
        "reports": reports,
        "failure": failure,
        "wall_s": time.monotonic() - start,
        "source_step_sha256": hashlib.sha256(STEP.read_bytes()).hexdigest(),
        "engineering_accepted": False,
        "no_retry": "Stop on first invalid/time-limited case; no resource extension",
    }
    (BASE / "record.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    raise SystemExit(bool(failure))
