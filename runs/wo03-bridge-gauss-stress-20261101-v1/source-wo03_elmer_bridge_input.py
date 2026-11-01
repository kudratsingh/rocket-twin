"""Source-pinned bridge mesh and direct-nodal-load input assessment; no solver."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import gmsh
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/wo03-elmer-bridge-input-v2"
CONFIG = ROOT / "configs/studies/wo03-elmer-bridge-input.yaml"
EDGE = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))
FACES = ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def block(deck, head):
    m = re.search(r"(?ms)^" + re.escape(head) + r"\n(.*?)(?=^\*)", deck)
    if not m:
        raise ValueError("Missing card " + head)
    return m.group(1).splitlines()


def main():
    cfg = yaml.safe_load(CONFIG.read_text())
    assert not cfg["native_execution_authorized"]
    paths = {
        k: ROOT / cfg[k]
        for k in ("source_deck", "source_metadata", "elmer_solver", "stress_module")
    }
    before = {k: sha(v) for k, v in paths.items()}
    assert (
        before["elmer_solver"] == cfg["elmer_solver_sha256"]
        and before["stress_module"] == cfg["stress_module_sha256"]
    )
    deck = paths["source_deck"].read_text()
    meta = json.loads(paths["source_metadata"].read_text())
    assert deck.count("*BOUNDARY\nSUPPORT,1,3,0\n") == 1 and all(
        x not in deck.upper() for x in ("*MPC", "*EQUATION", "*TRANSFORM", "*DLOAD")
    )
    coords = {}
    cells = {}
    for line in block(deck, "*NODE"):
        x = line.split(",")
        coords[int(x[0])] = tuple(float(v) for v in x[1:])
        assert len(x) == 4
    for line in block(deck, "*ELEMENT,TYPE=C3D10,ELSET=ALL"):
        x = [int(v) for v in line.split(",")]
        cells[x[0]] = x[1:]
    if len(coords) != 42850 or len(cells) != 22495 or any(len(c) != 10 for c in cells.values()):
        raise ValueError("Unexpected mesh")
    if cells != {int(k): v for k, v in meta["all_c3d10_connectivity"].items()}:
        raise ValueError("Connectivity mismatch")
    if not np.isfinite(np.asarray(list(coords.values()))).all():
        raise ValueError("Nonfinite coordinates")
    groups = meta["material_element_ids"]
    names = ["G11"] + [f"EPOXY_{i}" for i in range(6)]
    mat = {}
    for i, name in enumerate(names, 1):
        for eid in groups[name]:
            if eid in mat:
                raise ValueError("Material overlap")
            mat[eid] = i
    if set(mat) != set(cells):
        raise ValueError("Material missing")
    for name in names:
        expected = "10000,0.3" if name == "G11" else "100,0.3"
        if expected not in block(deck, "*MATERIAL,NAME=" + name + "\n*ELASTIC"):
            raise ValueError("Unexpected material")
    support = {
        int(x.strip())
        for line in block(deck, "*NSET,NSET=SUPPORT")
        for x in line.split(",")
        if x.strip()
    }
    if support != set(meta["support_node_ids"]):
        raise ValueError("Support set mismatch")
    load_steps = []
    for chunk in deck.split("*STEP\n")[1:]:
        lines = block(chunk, "*CLOAD,OP=NEW")
        loads = {}
        for line in lines:
            node, dof, token = line.split(",")
            node = int(node)
            if dof != "3" or node in loads or not math.isfinite(float(token)):
                raise ValueError("Unsupported load")
            loads[node] = token
        load_steps.append(loads)
    if len(load_steps) != 2:
        raise ValueError("Unexpected steps")
    used = {n for cell in cells.values() for n in cell}
    allnodes = set(coords)
    loadnodes = set().union(*(set(x) for x in load_steps))
    unused = allnodes - used
    if (
        len(used) != 42715
        or len(unused) != 135
        or (support | loadnodes) - used
        or support & loadnodes
    ):
        raise ValueError("Unused/support/load mismatch")
    for step, name in zip(load_steps, ("EQUAL", "SINGLE"), strict=True):
        saved = {int(k): float(v[2]) for k, v in meta["step_nodal_forces_N"][name].items()}
        if set(step) != set(saved):
            raise ValueError("Load IDs differ")
        for n, token in step.items():
            if not math.isclose(float(token), saved[n], rel_tol=1e-14, abs_tol=1e-16):
                raise ValueError("Load value differs")
    mapping = {old: i for i, old in enumerate(sorted(used), 1)}
    faces = defaultdict(list)
    for eid, c in cells.items():
        edges = {tuple(sorted((c[a], c[b]))): c[4 + j] for j, (a, b) in enumerate(EDGE)}
        for indices in FACES:
            v = [c[j] for j in indices]
            f = tuple(v + [edges[tuple(sorted((v[a], v[b])))] for a, b in ((0, 1), (1, 2), (2, 0))])
            faces[tuple(sorted(v))].append((eid, f))
    boundary = []
    support_covered = set()
    for owners in faces.values():
        if len(owners) == 2:
            if set(owners[0][1]) != set(owners[1][1]):
                raise ValueError("Nonconformal interface")
            continue
        if len(owners) != 1:
            raise ValueError("Nonmanifold")
        eid, f = owners[0]
        tag = 1 if set(f) <= support else 2
        if tag == 1:
            support_covered.update(f)
        boundary.append((tag, eid, f))
    if support_covered != support:
        raise ValueError("Support face coverage incomplete")
    # Recover each imprinted washer patch by its source nodal-weight set;
    # evaluate its serialized quadratic boundary geometry with source Gauss6.
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    try:
        tpoints, tweights = gmsh.model.mesh.getIntegrationPoints(9, "Gauss6")
    finally:
        gmsh.finalize()
    tpoints = np.asarray(tpoints).reshape(-1, 3)[:, :2]
    tweights = np.asarray(tweights)
    tri_dl = np.array([[-1.0, -1.0], [1.0, 0.0], [0.0, 1.0]])
    tri_grad = []
    for point in tpoints:
        ll = np.r_[1.0 - sum(point), point]
        tri_grad.append(
            np.array(
                [(4 * ll[i] - 1) * tri_dl[i] for i in range(3)]
                + [4 * (ll[i] * tri_dl[j] + ll[j] * tri_dl[i]) for i, j in ((0, 1), (1, 2), (2, 0))]
            )
        )
    washer_checks = []
    for patch in meta["washer_patches"]:
        patch_nodes = set(map(int, patch["unit_pressure_nodal_weights_mm2"]))
        selected = [f for _, _, f in boundary if set(f) <= patch_nodes]
        if len(selected) != patch["quadratic_triangle_count"]:
            raise ValueError("Washer triangle ownership mismatch")
        txyz = np.asarray([[coords[n] for n in face] for face in selected])
        tj = np.einsum("eai,qaj->eqij", txyz, np.asarray(tri_grad))
        metric = np.linalg.norm(np.cross(tj[:, :, :, 0], tj[:, :, :, 1]), axis=2)
        if not np.isfinite(metric).all() or np.min(metric) <= 0:
            raise ValueError("Washer Jacobian invalid")
        area = float(np.sum(metric @ tweights))
        saved = float(patch["area_mm2"])
        cad = float(patch["exact_cad_area_mm2"])
        washer_checks.append(
            {
                "source_index": patch["source_index"],
                "triangles": len(selected),
                "serialized_area_mm2": area,
                "saved_mesh_area_mm2": saved,
                "cad_area_mm2": cad,
                "serialization_delta_mm2": area - saved,
                "cad_delta_mm2": area - cad,
            }
        )
    OUT.mkdir(parents=True, exist_ok=False)
    (OUT / "washer-area-guards.json").write_text(json.dumps(washer_checks, indent=2) + "\n")
    for x in washer_checks:
        if (
            not math.isclose(
                x["serialized_area_mm2"], x["saved_mesh_area_mm2"], rel_tol=1e-8, abs_tol=1e-8
            )
            or abs(x["cad_delta_mm2"]) > 0.0002
        ):
            raise ValueError("Washer area guard failed")
    # Geometry-only 510 Jacobian check at the original eleven-point tetra rule;
    # no finite-element field solve is implemented here.
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    try:
        points, weights = gmsh.model.mesh.getIntegrationPoints(11, "Gauss4")
    finally:
        gmsh.finalize()
    points = np.asarray(points).reshape(-1, 3)
    weights = np.asarray(weights)
    if len(points) != 11 or len(weights) != 11:
        raise ValueError("Unexpected original quadrature")
    dlam = np.array([[-1.0, -1.0, -1.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    grads = []
    for point in points:
        lam = np.r_[1.0 - sum(point), point]
        grads.append(
            np.array(
                [(4 * lam[i] - 1) * dlam[i] for i in range(4)]
                + [4 * (lam[i] * dlam[j] + lam[j] * dlam[i]) for i, j in EDGE]
            )
        )
    xyz = np.asarray([[coords[n] for n in c] for c in cells.values()])
    jac = np.einsum("eai,qaj->eqij", xyz, np.asarray(grads))
    dets = np.linalg.det(jac)
    if not np.isfinite(dets).all() or np.min(dets) <= 0:
        raise ValueError("Serialized curved Jacobian nonpositive")
    values = dets @ weights
    volumes = {name: 0.0 for name in names}
    for eid, volume in zip(cells, values, strict=True):
        volumes[names[mat[eid] - 1]] += float(volume)
    # Preserve the saved mesh-integral comparison at the original strict
    # 1e-8 guard, and separately check the upstream 1% mesh/CAD criterion.
    checks = {}
    for name in names:
        saved_mesh = math.fsum(meta["tetrahedron_volumes_mm3"][str(e)] for e in groups[name])
        cad = float(meta["material_region_volumes_mm3"][name])
        mesh_ok = math.isclose(volumes[name], saved_mesh, rel_tol=1e-8, abs_tol=1e-8)
        cad_ok = math.isclose(volumes[name], cad, rel_tol=0.01, abs_tol=0.0)
        checks[name] = {
            "serialized_mesh_mm3": volumes[name],
            "saved_mesh_mm3": saved_mesh,
            "CAD_mm3": cad,
            "serialization_abs_delta_mm3": volumes[name] - saved_mesh,
            "mesh_CAD_relative_delta": (volumes[name] - cad) / cad,
            "strict_1e-8_mesh_guard": mesh_ok,
            "existing_1pct_CAD_guard": cad_ok,
        }
    (OUT / "volume-guards.json").write_text(json.dumps(checks, indent=2) + "\n")
    for name in names:
        if (
            not checks[name]["strict_1e-8_mesh_guard"]
            or not checks[name]["existing_1pct_CAD_guard"]
        ):
            raise ValueError("Material volume guard failed: " + name)
    # Connectivity requires one shared-node component, without inventing joints.
    parent = {n: n for n in used}

    def find(n):
        while parent[n] != n:
            parent[n] = parent[parent[n]]
            n = parent[n]
        return n

    for cell in cells.values():
        anchor = find(cell[0])
        for n in cell[1:]:
            other = find(n)
            if other != anchor:
                parent[other] = anchor
    components = len({find(n) for n in used})
    if components != 1:
        raise ValueError("Disconnected node graph")
    if not meta["jacobian"]["positive_all_samples"] or meta["jacobian"]["minimum_determinant"] <= 0:
        raise ValueError("Source Jacobian preflight invalid")
    out = OUT / "prepared"
    out.mkdir(parents=True, exist_ok=False)
    mesh = out / "mesh"
    mesh.mkdir()
    (mesh / "mesh.header").write_text(
        f"{len(used)} {len(cells)} {len(boundary)}\n2\n306 {len(boundary)}\n510 {len(cells)}\n"
    )
    (mesh / "mesh.nodes").write_text(
        "".join(
            f"{mapping[n]} -1 " + " ".join(f"{x*1e-3:.17g}" for x in coords[n]) + "\n"
            for n in sorted(used)
        )
    )
    (mesh / "mesh.elements").write_text(
        "".join(
            f"{eid} {mat[eid]} 510 " + " ".join(str(mapping[n]) for n in c) + "\n"
            for eid, c in cells.items()
        )
    )
    (mesh / "mesh.boundary").write_text(
        "".join(
            f"{i} {tag} {eid} 0 306 " + " ".join(str(mapping[n]) for n in f) + "\n"
            for i, (tag, eid, f) in enumerate(boundary, 1)
        )
    )
    (out / "node-map.json").write_text(json.dumps(mapping, sort_keys=True) + "\n")
    resultants = []
    for name, loads in zip(("equal", "single"), load_steps, strict=True):
        folder = out / name
        folder.mkdir()
        sif = []
        for i, (old, token) in enumerate(sorted(loads.items()), 10):
            sif += [
                f"Boundary Condition {i}",
                f"  Target Nodes(1) = {mapping[old]}",
                f"  Displacement 3 Load = Real {token}",
                "End",
            ]
        (folder / "nodal-loads.sif.fragment").write_text("\n".join(sif) + "\n")
        module = paths["stress_module"].resolve()
        header = [
            "Header",
            '  Mesh DB ".." "mesh"',
            "End",
            "Simulation",
            "  Coordinate System = Cartesian",
            "  Coordinate Mapping(3) = 1 2 3",
            "  Simulation Type = Steady State",
            "  Steady State Max Iterations = 1",
            "  Output Intervals = 1",
            "End",
        ]
        for i in range(1, 8):
            E = 1e10 if i == 1 else 1e8
            header += [
                f"Body {i}",
                "  Equation = 1",
                f"  Material = {i}",
                "End",
                f"Material {i}",
                f"  Youngs Modulus = Real {E:.17g}",
                "  Poisson Ratio = Real 0.3",
                "End",
            ]
        header += [
            "Equation 1",
            "  Active Solvers(2) = 1 2",
            "End",
            "Solver 1",
            "  Equation = Elasticity",
            '  Variable = String "Displacement"',
            "  Variable DOFs = Integer 3",
            f'  Procedure = File "{module}" "StressSolver"',
            "  Displace Mesh = Logical False",
            "  Calculate Loads = Logical True",
            "  Linear System Solver = Direct",
            "  Linear System Direct Method = UMFPACK",
            "  Linear System Abort Not Converged = Logical True",
            "  Nonlinear System Max Iterations = Integer 1",
            "End",
            "Solver 2",
            "  Equation = Result Output",
            '  Procedure = File "ResultOutputSolve" "ResultOutputSolver"',
            '  Output File Name = "field"',
            "  Vtu Format = Logical True",
            "  Binary Output = Logical True",
            "  Single Precision = Logical False",
            "End",
            "Boundary Condition 1",
            "  Target Boundaries(1) = 1",
            "  Displacement 1 = Real 0",
            "  Displacement 2 = Real 0",
            "  Displacement 3 = Real 0",
            "End",
        ]
        (folder / "case.sif").write_text("\n".join(header + sif) + "\n")
        r = np.array([0.0, 0.0, math.fsum(float(t) for t in loads.values())])
        moment = np.sum(
            [np.cross(coords[n], (0.0, 0.0, float(t))) for n, t in loads.items()], axis=0
        )
        resultants.append(
            {
                "case": name,
                "node_count": len(loads),
                "force_N": r.tolist(),
                "moment_Nmm": moment.tolist(),
                "serialized_nodal_loads_exact": True,
            }
        )
        text = (folder / "nodal-loads.sif.fragment").read_text()
        parsed = re.findall(
            r"Target Nodes\(1\) = (\d+)\n  Displacement 3 Load = Real ([^\n]+)\n", text
        )
        if len(parsed) != len(loads) or dict(parsed) != {
            str(mapping[n]): token for n, token in loads.items()
        }:
            raise ValueError("Load serialization roundtrip failed")
    # Match the prior deck-derived net force and moment independently.
    for i, x in enumerate(resultants):
        old = meta["serialized_deck_load_resultants"][i]
        x["source_force_N"] = old["force_N"]
        x["source_moment_Nmm"] = old["moment_Nmm"]
        x["force_delta_N"] = (np.asarray(x["force_N"]) - old["force_N"]).tolist()
        x["moment_delta_Nmm"] = (np.asarray(x["moment_Nmm"]) - old["moment_Nmm"]).tolist()
    (OUT / "load-guards.json").write_text(json.dumps(resultants, indent=2) + "\n")
    for x in resultants:
        if not np.allclose(
            x["force_N"], x["source_force_N"], rtol=1e-10, atol=1e-8
        ) or not np.allclose(x["moment_Nmm"], x["source_moment_Nmm"], rtol=1e-10, atol=1e-6):
            raise ValueError("Serialized load force/moment mismatch")
    after = {k: sha(v) for k, v in paths.items()}
    assert before == after
    rec = {
        "status": "input_mapping_proposal_no_native",
        "source_sha256_before": before,
        "source_sha256_after": after,
        "nodes_declared": len(coords),
        "nodes_used": len(used),
        "unused_nodes_excluded": len(unused),
        "support_count": len(support),
        "boundary_faces": len(boundary),
        "support_faces": sum(x[0] == 1 for x in boundary),
        "materials": names,
        "source_jacobian": meta["jacobian"],
        "serialized_deck_min_gauss11_determinant_mm3": float(np.min(dets)),
        "serialized_deck_material_volumes_mm3": volumes,
        "volume_guard_checks": checks,
        "used_node_graph_components": components,
        "source_material_volumes_mm3": meta["material_region_volumes_mm3"],
        "source_washer_areas_mm2": [x["area_mm2"] for x in meta["washer_patches"]],
        "serialized_washer_area_checks": washer_checks,
        "load_resultants": resultants,
        "output_hashes": {str(p.relative_to(ROOT)): sha(p) for p in out.rglob("*") if p.is_file()},
        "native_executed": False,
        "critical_dependency": "Target Nodes / Displacement 3 Load is source-supported but not covered by prior uniform-traction B; a separate matching-B nodal-RHS known-answer gate is required before actual solve.",
    }
    (out / "record.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: rec[k]
                for k in (
                    "status",
                    "nodes_used",
                    "unused_nodes_excluded",
                    "boundary_faces",
                    "support_faces",
                    "load_resultants",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
