"""Prepare the preserved CCX B problem for an isolated Elmer comparison, no solve."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import resource
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import gmsh
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.wo03_ccx_reaction_fixture import _load_for_face

OUT = ROOT / "build/wo03-elmer-structural-fixture-v3"
CONFIG = ROOT / "configs/studies/wo03-elmer-structural-fixture.yaml"
EDGE = ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3))
FACES = ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    cfg = yaml.safe_load(CONFIG.read_text())
    if cfg["native_execution_authorized"]:
        raise ValueError("No native execution is implemented")
    files = {
        k: ROOT / cfg[k]
        for k in ("solver", "module", "fixture_deck", "fixture_metadata", "fixture_mesh")
    }
    for k in ("solver", "module"):
        if sha(files[k]) != cfg[k + "_sha256"]:
            raise ValueError("Pinned " + k + " mismatch")
    before = {k: sha(p) for k, p in files.items()}
    m = json.loads(files["fixture_metadata"].read_text())
    deck = files["fixture_deck"].read_text()
    coords = {int(k): np.array(v, dtype=float) for k, v in m["node_coordinates_mm"].items()}
    chunks = deck.split("*STEP\n")[1:]
    assert len(coords) == 593 and len(chunks) == 2
    cells = {}
    for line in (
        re.search(r"(?ms)^\*ELEMENT,TYPE=C3D10,ELSET=ALL\n(.*?)(?=^\*)", deck).group(1).splitlines()
    ):
        row = [int(x) for x in line.split(",")]
        cells[row[0]] = row[1:]
    if len(cells) != 254 or any(len(c) != 10 for c in cells.values()):
        raise ValueError("Unexpected saved tets")
    mat = {
        int(n): idx + 1
        for idx, name in enumerate(("LAYER0", "LAYER1"))
        for n in m["material_element_ids"][name]
    }
    assert len(mat) == 254 and set(mat) == set(cells)
    faces = defaultdict(list)
    vol = {1: 0.0, 2: 0.0}
    for eid, c in cells.items():
        a = np.array([coords[n] for n in c[:4]])
        det = float(np.linalg.det((a[1:] - a[0]).T))
        if det <= 0:
            raise ValueError("Non-positive original tetra orientation")
        vol[mat[eid]] += det / 6
        for j, (x, y) in enumerate(EDGE):
            if not np.allclose(coords[c[4 + j]], (a[x] + a[y]) / 2, atol=1e-10, rtol=0):
                raise ValueError("Curved or misordered tetra edge")
        edge = {tuple(sorted((c[x], c[y]))): c[4 + j] for j, (x, y) in enumerate(EDGE)}
        for tri in FACES:
            v = [c[i] for i in tri]
            f = tuple(v + [edge[tuple(sorted((v[i], v[j])))] for i, j in ((0, 1), (1, 2), (2, 0))])
            faces[tuple(sorted(v))].append((eid, f))
    if any(abs(vol[i] - 480.0) > 1e-8 for i in (1, 2)):
        raise ValueError("Material volume mismatch")
    boundary = []
    areas = [0.0, 0.0, 0.0]
    supports = set()
    topsets = [set(), set(), set()]
    for group in faces.values():
        if len(group) == 2:
            if set(group[0][1]) != set(group[1][1]):
                raise ValueError("Nonconformal internal face")
            continue
        if len(group) != 1:
            raise ValueError("Ambiguous face ownership")
        eid, f = group[0]
        p = np.array([coords[n] for n in f])
        z = p[:, 2]
        tag = 7
        if np.allclose(z, 0, rtol=0, atol=1e-10):
            tag = 4
            supports.update(f)
        elif np.allclose(z, 20, rtol=0, atol=1e-10):
            bar = next(
                (i for i, nodes in enumerate(m["top_node_ids_by_bar"]) if set(f) <= set(nodes)),
                None,
            )
            if bar is None:
                raise ValueError("Top ownership")
            tag = bar + 1
            topsets[bar].update(f)
            areas[bar] += np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0])) / 2
        boundary.append((tag, eid, f))
    if supports != set(m["support_node_ids"]) or any(
        topsets[i] != set(m["top_node_ids_by_bar"][i]) or abs(areas[i] - 16) > 1e-10
        for i in range(3)
    ):
        raise ValueError("Boundary/source support mismatch")
    # Reconstruct every originally serialized CLOAD using the pinned preflight's own
    # Gauss6 routine on the retained mesh; no remesh and no numerical retry.
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    try:
        gmsh.open(str(files["fixture_mesh"]))
        tags = []
        for top in topsets:
            matches = []
            for _, tag in gmsh.model.getEntities(2):
                if {
                    int(x) for x in gmsh.model.mesh.getNodes(2, tag, includeBoundary=True)[0]
                } == top:
                    matches.append(tag)
            if len(matches) != 1:
                raise ValueError("Ambiguous top source face")
            tags.append(matches[0])
        load_checks = []
        for step, forces in enumerate(((50.0, 50.0, 50.0), (150.0, 0.0, 0.0))):
            rebuilt = {}
            for tag, force in zip(tags, forces, strict=True):
                if force:
                    loads, _ = _load_for_face(gmsh, tag, coords, force)
                    for n, v in loads.items():
                        if abs(v[2]) > 1e-18:
                            rebuilt[n] = format(v[2], ".15g")
            block = re.search(r"(?s)\*CLOAD,OP=NEW\n(.*?)\*NODE PRINT", chunks[step]).group(1)
            orig = {int(f[0]): f[2] for f in (line.split(",") for line in block.splitlines())}
            if rebuilt != orig:
                raise ValueError("Original serialized CLOAD mismatch")
            load_checks.append({"step": step + 1, "exact_serialized_values": len(orig)})
    finally:
        gmsh.finalize()
    if before != {k: sha(p) for k, p in files.items()}:
        raise ValueError("Input sources changed")
    out = OUT / "prepared"
    out.mkdir(parents=True, exist_ok=False)
    mesh = out / "mesh"
    mesh.mkdir()
    (mesh / "mesh.header").write_text(
        f"{len(coords)} {len(cells)} {len(boundary)}\n2\n306 {len(boundary)}\n510 {len(cells)}\n"
    )
    (mesh / "mesh.nodes").write_text(
        "".join(
            f"{i} -1 " + " ".join(f"{x*1e-3:.17g}" for x in p) + "\n" for i, p in coords.items()
        )
    )
    (mesh / "mesh.elements").write_text(
        "".join(f"{i} {mat[i]} 510 " + " ".join(map(str, c)) + "\n" for i, c in cells.items())
    )
    (mesh / "mesh.boundary").write_text(
        "".join(
            f"{i} {tag} {eid} 0 306 " + " ".join(map(str, face)) + "\n"
            for i, (tag, eid, face) in enumerate(boundary, 1)
        )
    )
    cases = out / "cases"
    cases.mkdir()
    for name, forces in (("equal", (50.0, 50.0, 50.0)), ("single", (150.0, 0.0, 0.0))):
        folder = cases / name
        folder.mkdir()
        shutil.copytree(mesh, folder / "mesh")
        (folder / "case.sif").write_text(sif(files["module"].resolve(), forces))
    generated = {str(p.relative_to(ROOT)): sha(p) for p in sorted(out.rglob("*")) if p.is_file()}
    result = {
        "generated_sha256": generated,
        "status": "inputs_prepared_no_native",
        "input_sha256": before,
        "source_sha256": sha(Path(__file__)),
        "config_sha256": sha(CONFIG),
        "node_count": len(coords),
        "tet_count": len(cells),
        "boundary_count": len(boundary),
        "material_volumes_mm3": vol,
        "top_areas_mm2": areas,
        "load_token_checks": load_checks,
        "source_surface_tags": tags,
        "native_executed": False,
        "remaining": "Native procedure loading, reaction field and output semantics unverified",
    }
    (out / "record.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


def sif(module: Path, forces: tuple[float, float, float]) -> str:
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
    ]
    for i, E in ((1, 1e8), (2, 1e10)):
        text += [
            f"Body {i}",
            "  Equation = 1",
            f"  Material = {i}",
            "End",
            f"Material {i}",
            f"  Youngs Modulus = Real {E:.17g}",
            "  Poisson Ratio = Real 0.0",
            "End",
        ]
    text += [
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
        "  Calculate Boundary Fluxes = Logical True",
        "  Linear System Solver = Direct",
        "  Linear System Direct Method = UMFPACK",
        "  Linear System Max Iterations = 2000",
        "  Linear System Convergence Tolerance = 1.0e-12",
        "  Linear System Abort Not Converged = Logical True",
        "  Nonlinear System Max Iterations = Integer 1",
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
        "Boundary Condition 4",
        "  Target Boundaries(1) = 4",
        "  Displacement 1 = Real 0",
        "  Displacement 2 = Real 0",
        "  Displacement 3 = Real 0",
        "End",
    ]
    for i, force in enumerate(forces, 1):
        text += [
            f"Boundary Condition {i}",
            f"  Target Boundaries(1) = {i}",
            f"  Force 3 = Real {force / 16e-6:.17g}",
            "End",
        ]
    return "\n".join(text) + "\n"


def evaluate_vtu(path: Path, meta: dict, forces: tuple[float, float, float]):
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy

    vtk.vtkSMPTools.Initialize(1)
    vtk.vtkMultiThreader.SetGlobalMaximumNumberOfThreads(1)
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(path))
    reader.Update()
    grid = reader.GetOutput()
    points = vtk_to_numpy(grid.GetPoints().GetData())
    pd = grid.GetPointData()
    names = [pd.GetArrayName(i) for i in range(pd.GetNumberOfArrays())]

    def field(name):
        matches = [n for n in names if n and n.lower() == name.lower()]
        if len(matches) != 1:
            raise ValueError(f"Expected one {name}, got {names}")
        x = vtk_to_numpy(pd.GetArray(matches[0]))
        if x.dtype != np.float64 or x.shape != (len(points), 3) or not np.isfinite(x).all():
            raise ValueError("Missing, non-Float64 or malformed field " + name)
        return x

    U = field("Displacement")
    reaction = field("Displacement Loads")
    coords = {int(k): np.asarray(v) * 1e-3 for k, v in meta["node_coordinates_mm"].items()}
    ids = sorted(coords)
    if points.dtype != np.float64 or len(points) != len(ids) or not np.isfinite(points).all():
        raise ValueError("Invalid VTU coordinates")
    lookup = {tuple(np.round(p, 12)): i for i, p in enumerate(points)}
    if len(lookup) != len(points):
        raise ValueError("Duplicate VTU coordinates")
    order = [lookup[tuple(np.round(coords[n], 12))] for n in ids]
    if np.max(np.abs(points[order] - np.array([coords[n] for n in ids]))) > 1e-12:
        raise ValueError("VTU node mapping mismatch")
    U = {n: U[order[i]] for i, n in enumerate(ids)}
    R = {n: reaction[order[i]] for i, n in enumerate(ids)}
    errors = []
    for b, nodes in enumerate(meta["bar_node_ids_by_bar"]):
        for n in nodes:
            z = coords[n][2] * 1000
            expected = forces[b] / 16 * (min(z, 10) / 100 + max(z - 10, 0) / 10000) * 1e-3
            err = abs(float(U[n][2]) - expected)
            tol = 0.01 * abs(expected) if expected else 1e-11
            if err > tol or max(abs(float(U[n][0])), abs(float(U[n][1]))) > 1e-11:
                raise ValueError("Known B displacement gate failed")
            errors.append(err)
    support = meta["support_node_ids"]
    F = np.array([math.fsum(float(R[n][j]) for n in support) for j in range(3)])
    applied = np.array([0.0, 0.0, sum(forces)])
    res = F + applied
    bounds = np.array([math.fsum(math.ulp(float(R[n][j])) / 2 for n in support) for j in range(3)])
    rr = float(np.linalg.norm(res))
    bb = float(np.linalg.norm(bounds))
    status = (
        "pass"
        if rr + bb <= 1e-5
        else ("fail" if max(0.0, rr - bb) > 1e-5 else "unavailable_precision")
    )
    moment = np.sum([np.cross(coords[n], R[n]) for n in support], axis=0)
    centers = np.asarray(meta["load_center_xyz_mm_by_bar"]) * 1e-3
    moment += sum((np.cross(centers[i], [0, 0, forces[i]]) for i in range(3)), np.zeros(3))
    moment_bounds = np.sum(
        [
            [
                abs(coords[n][1]) * math.ulp(float(R[n][2])) / 2
                + abs(coords[n][2]) * math.ulp(float(R[n][1])) / 2,
                abs(coords[n][2]) * math.ulp(float(R[n][0])) / 2
                + abs(coords[n][0]) * math.ulp(float(R[n][2])) / 2,
                abs(coords[n][0]) * math.ulp(float(R[n][1])) / 2
                + abs(coords[n][1]) * math.ulp(float(R[n][0])) / 2,
            ]
            for n in support
        ],
        axis=0,
    )
    return {
        "field_names": names,
        "displacement_dtype": "float64",
        "load_dtype": "float64",
        "VTU_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "max_nodal_displacement_error_m": max(errors),
        "support_reaction_N": F.tolist(),
        "force_residual_N": res.tolist(),
        "rounding_bound_N": bounds.tolist(),
        "force_status": status,
        "moment_residual_Nm": moment.tolist(),
        "moment_encoding_bound_Nm": moment_bounds.tolist(),
        "support_node_count": len(support),
        "reaction_semantics": "native Ax-b load field hypothesis; checked by known-case equilibrium without sign flip",
        "vtk_version": vtk.vtkVersion.GetVTKVersion(),
    }


def run_packet():
    cfg = yaml.safe_load(CONFIG.read_text())
    out = OUT / "prepared"
    if not cfg["native_execution_authorized"]:
        raise ValueError("Execution not admitted")
    old = yaml.safe_load((out / "config-disabled.yaml").read_text())
    normalized = dict(cfg)
    normalized["native_execution_authorized"] = False
    if normalized != old:
        raise ValueError("Config changes exceed explicit admission")
    pre = json.loads((out / "record.json").read_text())
    review = json.loads((OUT / "preflight-reviewed.json").read_text())
    if sha(Path(__file__)) != review["reviewed_driver_sha256"]:
        raise ValueError("Source changed")
    for path, digest in review["source_ledger"].items():
        if path == str(CONFIG):
            continue
        if sha(Path(path)) != digest:
            raise ValueError("Pinned source or tool changed: " + path)
    prefix = ROOT / ".cache/elmer-evaluation/setup-v1/prefix"

    def prefix_inventory():
        return {str(p): sha(p) for p in prefix.rglob("*") if p.is_file()}

    if prefix_inventory() != review["prefix_sha256"]:
        raise ValueError("Elmer prefix changed")
    paths = {
        k: ROOT / cfg[k]
        for k in ("solver", "module", "fixture_deck", "fixture_metadata", "fixture_mesh")
    }
    before = {k: sha(p) for k, p in paths.items()}
    if before != pre["input_sha256"]:
        raise ValueError("Input changed")
    for f, h in pre["generated_sha256"].items():
        if sha(ROOT / f) != h:
            raise ValueError("Prepared SIF or mesh changed")
    # Runtime libraries were observed during the module probe. Non-system paths
    # must retain their hash; system shared-cache hashes remain unavailable.
    probe = json.loads(
        (
            ROOT / ".cache/elmer-evaluation/structural-module-v1/build-attempt/record.json"
        ).read_text()
    )
    runtime = {k: v["sha256"] for k, v in probe["runtime_dependencies"].items() if v.get("sha256")}
    for p, h in runtime.items():
        if sha(Path(p)) != h:
            raise ValueError("Probed runtime dependency changed")
    native = OUT / "native"
    native.mkdir(exist_ok=False)
    from scripts.wo03_owned_process import darwin_process_callbacks, run_owned

    rss, desc = darwin_process_callbacks()
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    env = dict(os.environ)
    for n in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env[n] = "1"
    env["ELMER_HOME"] = str(prefix.resolve())
    env["ELMER_LIB"] = str((prefix / "share/elmersolver/lib").resolve())
    record = {
        "status": "started",
        "cases": [],
        "source_before": before,
        "runtime_before": runtime,
        "parent_rss_bytes": None,
        "qualification": False,
        "rss_scope": "per-process root only, not tree",
        "planned_cpu_s": 420,
        "prefix_before": review["prefix_sha256"],
        "source_ledger_before": review["source_ledger"],
    }

    def persist():
        record["parent_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        (native / "record.json").write_text(json.dumps(record, indent=2) + "\n")

    persist()
    try:
        for name, forces in (("equal", (50.0, 50.0, 50.0)), ("single", (150.0, 0.0, 0.0))):
            folder = native / name
            shutil.copytree(out / "cases" / name, folder)
            for p in (out / "cases" / name).rglob("*"):
                if p.is_file() and sha(p) != sha(folder / p.relative_to(out / "cases" / name)):
                    raise ValueError("Copied case changed")
            cmd = (
                "import os,resource;resource.setrlimit(resource.RLIMIT_CPU,(120,120));os.execv("
                + repr(str(paths["solver"]))
                + ",["
                + repr(str(paths["solver"]))
                + ",'case.sif'])"
            )
            status = run_owned(
                [sys.executable, "-c", cmd],
                log_path=folder / "solver.log",
                status_path=folder / "status.json",
                wall_limit_s=120,
                rss_callback=rss,
                descendants_callback=desc,
                rss_limit_bytes=2147483648,
                cwd=folder,
                env=env,
            )
            log = (folder / "solver.log").read_text(errors="replace").lower()
            if "fatal:" in log or "error:" in log or "not converged" in log:
                raise ValueError("Solver reports error or nonconvergence")
            matches = [
                p
                for p in [folder / "field_t0001.vtu", folder / "mesh/field_t0001.vtu"]
                if p.is_file()
            ]
            if len(matches) != 1:
                raise ValueError("Missing or ambiguous VTU")
            res = evaluate_vtu(
                matches[0], json.loads(paths["fixture_metadata"].read_text()), forces
            )
            record["cases"].append({"name": name, "results": res, "resource_status": status})
            if res["force_status"] != "pass":
                raise ValueError("Strict force unavailable or failed")
            if {k: sha(p) for k, p in paths.items()} != before or any(
                sha(Path(p)) != h for p, h in runtime.items()
            ):
                raise ValueError("Input or dependency changed")
            persist()
        record["status"] = "complete_known_answer_not_qualified"
    except Exception as exc:
        record.update(status="stopped", error=repr(exc))
        raise
    finally:
        record["generated_after"] = {f: sha(ROOT / f) for f in pre["generated_sha256"]}
        record["generated_unchanged"] = record["generated_after"] == pre["generated_sha256"]
        record["source_after"] = {k: sha(p) for k, p in paths.items()}
        record["source_unchanged"] = record["source_after"] == before
        record["runtime_after"] = {p: sha(Path(p)) for p in runtime}
        record["runtime_unchanged"] = record["runtime_after"] == runtime
        record["prefix_after"] = prefix_inventory()
        record["prefix_unchanged"] = record["prefix_after"] == review["prefix_sha256"]
        record["source_ledger_after"] = {
            p: sha(Path(p)) for p in review["source_ledger"] if p != str(CONFIG)
        }
        record["source_ledger_unchanged"] = all(
            record["source_ledger_after"][p] == h
            for p, h in review["source_ledger"].items()
            if p != str(CONFIG)
        )
        parent = resource.getrusage(resource.RUSAGE_SELF)
        record["parent_cpu_s"] = parent.ru_utime + parent.ru_stime
        if (
            not record["source_unchanged"]
            or not record["runtime_unchanged"]
            or not record["prefix_unchanged"]
            or not record["source_ledger_unchanged"]
            or not record["generated_unchanged"]
        ):
            record.update(status="stopped", error="Source or runtime changed")
        persist()


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("prepare", "execute"), default="prepare")
    args = parser.parse_args()
    if args.phase == "prepare":
        main()
    else:
        run_packet()


if __name__ == "__main__":
    cli()
