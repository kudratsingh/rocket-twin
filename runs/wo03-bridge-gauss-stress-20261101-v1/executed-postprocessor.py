"""Offline material-local C3D10 stress recovery; never invokes a solver or mesher.

Small-strain isotropic law: Elmer StressSolve.F90 LocalStrain/LocalStress,
source commit a19504ac53ec222e3355e182b08f2ff280c2203a. Also Timoshenko
and Goodier, Theory of Elasticity, 3rd ed., ch. 1 (strain and Hooke's law).
Source deck uses N, mm, MPa; saved Elmer displacement is metres. Convert U
into mm before differentiation; output stress remains MPa. No strength gate.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SHAPE_SOURCE = ROOT / "scripts/wo03_elmer_bridge_input.py"
EDGE = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))
COMPONENTS = ("xx", "yy", "zz", "xy", "yz", "xz")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def derivatives(points):
    """Execute only the exact saved source's dlam/grads/point-loop AST.

    No import or execution of its main, native initialization or mesh generation.
    """
    if sha(SHAPE_SOURCE) != "1ed3c28c8c25c6c388f2d04b12992e9fd5c389481484c2f35746a4f7a3f987a4":
        raise ValueError("Verified derivative source changed")
    tree = ast.parse(SHAPE_SOURCE.read_text())
    edge = next(
        n
        for n in tree.body
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "EDGE" for t in n.targets)
    )
    if ast.literal_eval(edge.value) != EDGE:
        raise ValueError("Source edge order changed")
    main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
    start = next(
        i
        for i, n in enumerate(main.body)
        if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "dlam" for t in n.targets)
    )
    selected = main.body[start : start + 3]
    if not isinstance(selected[-1], ast.For) or ast.unparse(selected[-1].target) != "point":
        raise ValueError("Source gradient block changed")
    env = {"np": np, "EDGE": EDGE, "points": np.asarray(points)}
    exec(compile(ast.Module(body=selected, type_ignores=[]), str(SHAPE_SOURCE), "exec"), env)  # noqa: S102 - fixed AST from hash-pinned local source
    return np.asarray(env["grads"])


def quadrature():
    """Query the original pinned rule only; no model, geometry or mesh generated."""
    import gmsh

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    try:
        points, weights = gmsh.model.mesh.getIntegrationPoints(11, "Gauss4")
    finally:
        gmsh.finalize()
    points, weights = np.asarray(points).reshape(-1, 3), np.asarray(weights)
    if points.shape != (11, 3) or weights.shape != (11,):
        raise ValueError("Unexpected original rule")
    return points, weights


def values(points):
    ll = np.column_stack((1 - np.sum(points, axis=1), points))
    return np.column_stack(
        [ll[:, i] * (2 * ll[:, i] - 1) for i in range(4)]
        + [4 * ll[:, i] * ll[:, j] for i, j in EDGE]
    )


def recover(xyz_mm, displacement_m, points, weights, youngs_mpa, poisson):
    """Return unprojected element/Gauss stress, position and signed dV in mm³."""
    xyz, u = np.asarray(xyz_mm), np.asarray(displacement_m) * 1000
    if xyz.shape != u.shape or xyz.ndim != 3 or xyz.shape[1:] != (10, 3):
        raise ValueError("Invalid original C3D10 arrays")
    if not np.isfinite(xyz).all() or not np.isfinite(u).all():
        raise ValueError("Nonfinite nodal arrays")
    grad = derivatives(points)
    # Source J[i,j] = dx_i/dxi_j; dN/dx = dN/dxi @ inv(J).
    jac = np.einsum("eai,qaj->eqij", xyz, grad)
    det = np.linalg.det(jac)
    if not np.isfinite(det).all() or np.min(det) <= 0:
        raise ValueError("Invalid curved Jacobian")
    physical = np.einsum("qaj,eqjk->eqak", grad, np.linalg.inv(jac))
    du = np.einsum("eai,eqaj->eqij", u, physical)
    strain = (du + du.swapaxes(-1, -2)) / 2
    e, nu = np.asarray(youngs_mpa), np.asarray(poisson)
    if np.any(e <= 0) or np.any(nu <= -1) or np.any(nu >= 0.5):
        raise ValueError("Invalid material")
    mu = e / (2 * (1 + nu))
    lam = e * nu / ((1 + nu) * (1 - 2 * nu))
    stress = 2 * mu[:, None, None, None] * strain + lam[:, None, None, None] * np.trace(
        strain, axis1=2, axis2=3
    )[:, :, None, None] * np.eye(3)
    return stress, np.einsum("qa,eai->eqi", values(points), xyz), det * weights


def tensor_components(stress):
    return np.stack(
        [stress[..., i, j] for i, j in ((0, 0), (1, 1), (2, 2), (0, 1), (1, 2), (0, 2))], axis=-1
    )


def von_mises(stress):
    dev = stress - np.trace(stress, axis1=-2, axis2=-1)[..., None, None] * np.eye(3) / 3
    return np.sqrt(1.5 * np.sum(dev * dev, axis=(-2, -1)))


def read_deck(deck_path, meta):
    deck = Path(deck_path).read_text()

    def block(head):
        match = re.search(r"(?ms)^" + re.escape(head) + r"\n(.*?)(?=^\*)", deck)
        if not match:
            raise ValueError("Missing card " + head)
        return match.group(1).splitlines()

    nodes = {
        int(row[0]): np.array(row[1:], dtype=float)
        for row in (line.split(",") for line in block("*NODE"))
    }
    cells = {
        int(row[0]): row[1:]
        for row in (
            [int(v) for v in line.split(",")] for line in block("*ELEMENT,TYPE=C3D10,ELSET=ALL")
        )
    }
    materials, assignments = {}, {}
    for name, ids in meta["material_element_ids"].items():
        modulus = [float(v) for v in block("*MATERIAL,NAME=" + name + "\n*ELASTIC")[0].split(",")]
        if len(modulus) != 2 or "*SOLID SECTION,ELSET=" + name + ",MATERIAL=" + name not in deck:
            raise ValueError("Material card/assignment invalid")
        serialized = {
            int(v) for line in block("*ELSET,ELSET=" + name) for v in line.split(",") if v.strip()
        }
        if set(ids) != serialized or set(assignments) & serialized:
            raise ValueError("Material ownership mismatch")
        assignments.update({i: name for i in ids})
        materials[name] = modulus
    if set(assignments) != set(cells) or any(len(c) != 10 for c in cells.values()):
        raise ValueError("Incomplete C3D10 material ownership")
    return nodes, cells, assignments, materials


def read_displacement(path, nodes):
    """Bounded VTU Float64 U reader with one-to-one original coordinate mapping."""
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy

    vtk.vtkSMPTools.Initialize(1)
    vtk.vtkMultiThreader.SetGlobalMaximumNumberOfThreads(1)
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(path))
    reader.Update()
    grid = reader.GetOutput()
    if grid.GetPoints() is None:
        raise ValueError("Missing points")
    pts = vtk_to_numpy(grid.GetPoints().GetData())
    pd = grid.GetPointData()
    names = [pd.GetArrayName(i) for i in range(pd.GetNumberOfArrays())]
    match = [n for n in names if n and n.lower() == "displacement"]
    if len(match) != 1:
        raise ValueError("Missing/ambiguous U")
    u = vtk_to_numpy(pd.GetArray(match[0]))
    if (
        pts.dtype != np.float64
        or u.dtype != np.float64
        or pts.shape != (len(nodes), 3)
        or u.shape != pts.shape
        or not np.isfinite(pts).all()
        or not np.isfinite(u).all()
    ):
        raise ValueError("Invalid Float64 points/U")
    ids = sorted(nodes)
    lookup = {tuple(np.round(p, 12)): i for i, p in enumerate(pts)}
    if len(lookup) != len(nodes):
        raise ValueError("Duplicate output coordinates")
    order = [lookup[tuple(np.round(nodes[n] * 1e-3, 12))] for n in ids]
    if np.max(np.abs(pts[order] - np.array([nodes[n] * 1e-3 for n in ids]))) > 1e-12:
        raise ValueError("Coordinate map mismatch")
    return {n: u[order[i]] for i, n in enumerate(ids)}


def summaries(stress, xyz, dv, element_ids, names, normals=None):
    result = {}
    for name in sorted(set(names)):
        mask = np.array([n == name for n in names])
        s, x, w, eid = stress[mask], xyz[mask], dv[mask], np.asarray(element_ids)[mask]
        metrics = dict(zip(COMPONENTS, tensor_components(s).transpose(2, 0, 1), strict=True))
        metrics["von_mises"] = von_mises(s)
        if normals and name in normals:
            normal = np.asarray(normals[name])
            traction = np.einsum("eqij,j->eqi", s, normal)
            signed = traction @ normal
            metrics["film_normal_tension_positive"] = signed
            metrics["film_total_shear"] = np.linalg.norm(
                traction - signed[..., None] * normal, axis=-1
            )
        out = {
            "volume_mm3": float(w.sum()),
            "element_count": len(eid),
            "sample_count": int(w.size),
            "metrics_MPa": {},
        }
        for key, v in metrics.items():
            entry = {"signed_quadrature_volume_mean": float(np.sum(w * v) / w.sum())}
            for label, index in (
                ("minimum", np.unravel_index(np.argmin(v), v.shape)),
                ("maximum", np.unravel_index(np.argmax(v), v.shape)),
            ):
                entry[label] = {
                    "value": float(v[index]),
                    "element_id": int(eid[index[0]]),
                    "gauss_index_0_based": int(index[1]),
                    "xyz_mm": x[index].tolist(),
                }
            out["metrics_MPa"][key] = entry
        if normals and name in normals:
            out["film_normal_G11_to_rail"] = list(normals[name])
        result[name] = out
    return result


def run(phase):
    import resource
    import signal
    import time

    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    signal.alarm(30)
    t0, cpu0 = time.monotonic(), time.process_time()
    out = ROOT / "build/wo03-bridge-gauss-stress-v1"
    out.mkdir(exist_ok=True)
    metadata = ROOT / "build/wo03-g80-bridge-area-budget-coarse-v1/bridge_1p5mm/mesh-meta.json"
    deck_path = metadata.with_name("case.inp")
    # Snapshot all retained inputs before any field access; only new output files mutate.
    input_paths = [
        Path(__file__),
        SHAPE_SOURCE,
        metadata,
        deck_path,
        ROOT / "tests/test_bridge_gauss_stress.py",
        ROOT / "build/wo03-elmer-bridge-diagnostic-v1/equal-readonly-recovery.json",
        ROOT / "build/wo03-elmer-bridge-diagnostic-v1/equal-readonly-displacements.npz",
        ROOT / "build/wo03-elmer-bridge-single-continuation-v1/single-readonly-recovery.json",
        ROOT / "build/wo03-elmer-bridge-single-continuation-v1/single/field_t0001.vtu",
        ROOT / "scripts/wo03_elmer_bridge_diagnostic.py",
        ROOT / "build/wo03-elmer-bridge-input-v2/prepared/node-map.json",
        ROOT / "build/wo03-elmer-bridge-input-v2/prepared/mesh/mesh.nodes",
        ROOT / "build/wo03-elmer-bridge-diagnostic-v1/preflight-reviewed.json",
        ROOT / "build/wo03-ccx-reaction-fixture-preflight-v6-b/mesh-meta.json",
        ROOT / "build/wo03-ccx-reaction-fixture-preflight-v6-b/case.inp",
        ROOT / "build/wo03-elmer-stress-fixture-v2/native/case/mesh/field_t0001.vtu",
        ROOT / "build/wo03-elmer-stress-fixture-v2/native/record.json",
    ]
    before = {str(p): sha(p) for p in input_paths}
    meta = json.loads(metadata.read_text())
    points, weights = quadrature()
    if not np.array_equal(weights, meta["tetrahedron_gauss4_reference_weights"]):
        raise ValueError("Original signed Gauss4 weights differ")
    files = [Path(__file__), SHAPE_SOURCE, metadata, deck_path]
    if phase == "verify":
        import subprocess
        import sys

        # Mandatory independent synthetic patch checks run before saved B or actual use.
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "tests/test_bridge_gauss_stress.py"],
            timeout=15,
            check=True,
            capture_output=True,
            text=True,
        )
        fixture = ROOT / "build/wo03-ccx-reaction-fixture-preflight-v6-b"
        bmeta_path, bdeck = fixture / "mesh-meta.json", fixture / "case.inp"
        bmeta = json.loads(bmeta_path.read_text())
        nodes, cells, assignments, materials = read_deck(bdeck, bmeta)
        field = ROOT / "build/wo03-elmer-stress-fixture-v2/native/case/mesh/field_t0001.vtu"
        native_record = field.parents[2] / "record.json"
        source_record = json.loads(native_record.read_text())
        if source_record["status"] != "known_case_pass_not_qualified":
            raise ValueError("Saved native B result not verified")
        u = read_displacement(field, nodes)
        ids = list(cells)
        names = [assignments[eid] for eid in ids]
        stress, _, _ = recover(
            np.array([[nodes[n] for n in cells[eid]] for eid in ids]),
            np.array([[u[n] for n in cells[eid]] for eid in ids]),
            points,
            weights,
            [materials[n][0] for n in names],
            [materials[n][1] for n in names],
        )
        loaded = set(bmeta["bar_node_ids_by_bar"][0])
        target = np.zeros(stress.shape)
        for i, eid in enumerate(ids):
            belongs = set(cells[eid]) <= loaded
            if set(cells[eid]) & loaded and not belongs:
                raise ValueError("Ambiguous B bar ownership")
            if belongs:
                target[i, :, 2, 2] = 9.375
        errors = np.max(np.abs(tensor_components(stress - target)), axis=(0, 1))
        from scripts.wo03_elmer_stress_fixture_reader import read_stress

        native = read_stress(field, bmeta)
        record = {
            "status": "verified_for_coarse_diagnostic_only",
            "synthetic_patch_checks": completed.stdout.strip(),
            "B_expected_loaded_axial_MPa": 9.375,
            "B_component_order": COMPONENTS,
            "B_max_abs_component_errors_MPa": errors.tolist(),
            "B_max_error_reference_scaled": float(max(errors) / 9.375),
            "B_all_components_existing_2pct_pass": bool(max(errors) / 9.375 < 0.02),
            "native_B_PointData_crosscheck_separate_projection": native,
        }
        if not record["B_all_components_existing_2pct_pass"]:
            raise ValueError("Known B 2% check failed; no actual use")
        files += [
            bmeta_path,
            bdeck,
            field,
            native_record,
            ROOT / "tests/test_bridge_gauss_stress.py",
        ]
    else:
        verification = out / "verify.json"
        verified = json.loads(verification.read_text())
        if verified["status"] != "verified_for_coarse_diagnostic_only" or verified["source_sha256"][
            str(Path(__file__))
        ] != sha(__file__):
            raise ValueError("Current script not verified before actual use")
        equal_recovery = ROOT / "build/wo03-elmer-bridge-diagnostic-v1/equal-readonly-recovery.json"
        single_recovery = (
            ROOT / "build/wo03-elmer-bridge-single-continuation-v1/single-readonly-recovery.json"
        )
        recovery = json.loads((equal_recovery if phase == "equal" else single_recovery).read_text())
        source_hashes = recovery.get("file_sha256_after", recovery.get("sha256_after"))
        for p in (metadata, deck_path):
            if sha(p) != source_hashes[str(p)]:
                raise ValueError("Original source hash mismatch")
        nodes, cells, assignments, materials = read_deck(deck_path, meta)
        used = {n for cell in cells.values() for n in cell}
        if cells != {int(k): v for k, v in meta["all_c3d10_connectivity"].items()}:
            raise ValueError("Original connectivity mismatch")
        from scripts.wo03_elmer_bridge_diagnostic import load_mesh

        prepared = ROOT / "build/wo03-elmer-bridge-input-v2/prepared"
        review_path = ROOT / "build/wo03-elmer-bridge-diagnostic-v1/preflight-reviewed.json"
        review = json.loads(review_path.read_text())
        mapping, compact_nodes = load_mesh(prepared)
        if mapping != {n: i for i, n in enumerate(sorted(used), 1)}:
            raise ValueError("Original-to-compact node map mismatch")
        for n in used:
            if not np.allclose(compact_nodes[mapping[n]], nodes[n] * 1e-3, rtol=0, atol=1e-15):
                raise ValueError("Compact coordinates mismatch original deck")
        for path in [prepared / "node-map.json", prepared / "mesh/mesh.nodes"]:
            if sha(path) != review["input_output_sha256"][str(path.relative_to(ROOT))]:
                raise ValueError("Reviewed node-map/mesh hash mismatch")
            files.append(path)
        files.append(review_path)
        if phase == "equal":
            archive = equal_recovery.with_name("equal-readonly-displacements.npz")
            if sha(archive) != recovery["displacement_archive_sha256"]:
                raise ValueError("Mapped archive hash mismatch")
            ar = np.load(archive, allow_pickle=False)
            nid, uu = ar["node_ids"], ar["displacements_m"]
            if (
                set(nid) != set(compact_nodes)
                or len(nid) != len(used)
                or uu.dtype != np.float64
                or uu.shape != (len(used), 3)
            ):
                raise ValueError("Invalid mapped archive")
            compact_u = {int(n): uu[i] for i, n in enumerate(nid)}
            u = {n: compact_u[mapping[n]] for n in used}
            files += [archive]
        else:
            field = ROOT / "build/wo03-elmer-bridge-single-continuation-v1/single/field_t0001.vtu"
            if sha(field) != source_hashes[str(field)]:
                raise ValueError("Saved SINGLE VTU hash mismatch")
            from scripts.wo03_elmer_bridge_diagnostic import read_vtu

            frozen_reader = ROOT / "scripts/wo03_elmer_bridge_diagnostic.py"
            if (
                sha(frozen_reader)
                != "8a74b89fc5e29811b5148f0602f8ed972942f9a73d33f863e56159e3f7cfd399"
            ):
                raise ValueError("Original pure reader changed")
            loads = {
                mapping[int(n)]: str(v[2]) for n, v in meta["step_nodal_forces_N"]["SINGLE"].items()
            }
            field_check, u = read_vtu(
                field, compact_nodes, {mapping[n] for n in meta["support_node_ids"]}, loads
            )
            if field_check["strict_force_status"] != "pass":
                raise ValueError("Preserved field force check failed")
            u = {n: u[mapping[n]] for n in used}
            files += [field, frozen_reader]
        ids = list(cells)
        names = [assignments[eid] for eid in ids]
        stress, xyz, dv = recover(
            np.array([[nodes[n] for n in cells[eid]] for eid in ids]),
            np.array([[u[n] for n in cells[eid]] for eid in ids]),
            points,
            weights,
            [materials[n][0] for n in names],
            [materials[n][1] for n in names],
        )
        saved = [meta["tetrahedron_gauss4_points"][str(eid)] for eid in ids]
        saved_xyz = np.array([[g["xyz_mm"] for g in row] for row in saved])
        saved_dv = np.array([[g["determinant_times_weight_mm3"] for g in row] for row in saved])
        if not np.allclose(xyz, saved_xyz, rtol=1e-10, atol=1e-9) or not np.allclose(
            dv, saved_dv, rtol=1e-8, atol=1e-10
        ):
            raise ValueError("Original physical quadrature/Jacobian mismatch")
        normals = {}
        for film in meta["film_surface_ownership"]:
            # Derive G11-to-rail normal from the two actual saved plane node sets.
            front = np.array([nodes[n] for n in film["bridge_interface"]["node_ids"]])
            back = np.array([nodes[n] for n in film["rail_back"]["node_ids"]])
            _, _, axes = np.linalg.svd(back - back.mean(axis=0), full_matrices=False)
            normal = axes[-1]
            if np.dot(normal, back.mean(axis=0) - front.mean(axis=0)) < 0:
                normal = -normal
            if (
                np.max(np.abs((back - back.mean(axis=0)) @ normal)) > 1e-7
                or abs(abs(np.dot(normal, back.mean(axis=0) - front.mean(axis=0))) - 0.1) > 1e-7
            ):
                raise ValueError("Film normal/thickness unavailable")
            normals[film["epoxy_material"]] = normal.tolist()
        record = {
            "status": "executed_coarse_material_local_diagnostic",
            "case": phase,
            "service_force_N": 150,
            "design_factor_not_applied_to_raw_results": 3,
            "strength_acceptance": False,
            "convergence_acceptance": False,
            "materials_E_MPa_nu_from_original_deck": materials,
            "quadrature": "source-identical eleven-point signed Gauss4; one negative weight; means are signed quadrature volume integrals, no probabilistic percentiles",
            "regions": summaries(stress, xyz, dv, ids, names, normals),
            "original_quadrature_max_xyz_delta_mm": float(np.max(np.abs(xyz - saved_xyz))),
            "original_quadrature_max_dv_delta_mm3": float(np.max(np.abs(dv - saved_dv))),
        }
        files += [verification, equal_recovery, single_recovery]
        np.savez_compressed(
            out / (phase + "-gauss-samples.npz"),
            original_element_ids=ids,
            material_names=names,
            stress_MPa=stress,
            xyz_mm=xyz,
            signed_quadrature_dV_mm3=dv,
        )
    record["source_sha256"] = {str(p): sha(p) for p in files}
    record["retained_inputs_sha256_before"] = before
    record["retained_inputs_sha256_after"] = {str(p): sha(p) for p in input_paths}
    record["retained_inputs_unchanged"] = before == record["retained_inputs_sha256_after"]
    if not record["retained_inputs_unchanged"]:
        raise ValueError("Retained source input changed")
    record["one_cpu_requested"] = True
    record["process_cpu_s"] = time.process_time() - cpu0
    record["wall_s"] = time.monotonic() - t0
    record["peak_process_rss_bytes_macos"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if record["process_cpu_s"] > 30 or record["wall_s"] > 30:
        raise ValueError("Postprocessing resource budget exceeded")
    (out / (phase + ".json")).write_text(json.dumps(record, indent=2) + "\n")
    signal.alarm(0)
    print(
        json.dumps(
            {
                k: v
                for k, v in record.items()
                if k
                not in (
                    "source_sha256",
                    "regions",
                    "retained_inputs_sha256_before",
                    "retained_inputs_sha256_after",
                )
            }
        )
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("verify", "equal", "single"), required=True)
    run(parser.parse_args().phase)
