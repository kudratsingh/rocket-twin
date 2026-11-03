"""Bounded F2-C1 pressure-footprint method correction, never installed strength.

Offline only. Reuses the project's verified Gmsh C3D10/CalculiX ordering and
SPRING1 method. Surface integration is quadratic-triangle six-point quadrature;
energy is linear-isotropic compliance integrated at four tetra Gauss points.
Gmsh4.15.2 manual SecondOrderLinear; CalculiX2.23 C3D10/CLOAD/SPRING1 manual.
"""

from __future__ import annotations

import argparse
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

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "configs/vehicle/candidates/g80-f2-ballast.yaml"
STEP = ROOT / "build/wo03-g80-f2-local-cad-v2/notched_forward_ring.step"
SAVED = ROOT / "build/wo03-vibration-20261030T205443545391Z/known-axial/1.5/report.json"
PARTITION_KIND = "volume"
EXPECTED_SPEC = "7b188941de7fd4061800936c957b962d2165a5965c5cd9e46476d86242ed5a78"
EXPECTED_STEP = "7de1c2cbd7ecbad28f1a10aa3f80ca5be5ab3a330c4cbacc5e427a32ddce786c"
CENTRES = np.array(
    [[23 * math.cos(math.radians(a)), 23 * math.sin(math.radians(a))] for a in [30, 210]]
)


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def triangle6(points):
    """Consistent scalar traction weights and positive spring-lumping areas."""
    a, b, c, d = 0.445948490915965, 0.108103018168070, 0.091576213509771, 0.816847572980459
    quadrature = [
        (a, a, 0.111690794839005),
        (a, b, 0.111690794839005),
        (b, a, 0.111690794839005),
        (c, c, 0.054975871827661),
        (c, d, 0.054975871827661),
        (d, c, 0.054975871827661),
    ]
    load = np.zeros(6)
    positive = np.zeros(6)
    area = 0.0
    for r, s, w in quadrature:
        t = 1 - r - s
        n = np.array(
            [t * (2 * t - 1), r * (2 * r - 1), s * (2 * s - 1), 4 * t * r, 4 * r * s, 4 * s * t]
        )
        dr = np.array([1 - 4 * t, 4 * r - 1, 0, 4 * (t - r), 4 * s, -4 * s])
        ds = np.array([1 - 4 * t, 0, 4 * s - 1, -4 * r, 4 * r, 4 * (t - s)])
        da = w * np.linalg.norm(np.cross(dr @ points, ds @ points))
        load += n * da
        positive += n * n * da
        area += da
    positive *= area / positive.sum()
    return load, positive, float(area)


def known_answer():
    pts = np.array([[0.0, 0, 0], [1.0, 0, 0], [0.0, 1, 0], [0.5, 0, 0], [0.5, 0.5, 0], [0, 0.5, 0]])
    q, _, area = triangle6(pts)
    expected = np.array([0.0, 0, 0, 1 / 6, 1 / 6, 1 / 6])
    error = max(
        float(np.max(abs(q - expected))),
        abs(area - 0.5),
        float(np.max(abs(q @ pts - [1 / 6, 1 / 6, 0]))),
    )
    old = json.loads(SAVED.read_text())
    if error > 1e-12 or not old["passed"] or old["ccx_version"] != "This is Version 2.23":
        raise ValueError("known-answer verification failed; no actual-ring solve")
    return {
        "triangle_area_mm2": area,
        "nodal_loads": q.tolist(),
        "max_absolute_error": error,
        "reused_axial": {
            "path": str(SAVED.relative_to(ROOT)),
            "sha256": digest(SAVED),
            "record": old,
        },
        "spring_fixture": "reused runs/wo03-g80-f2-ring-20261103-v1/record.json known_spring",
        "passed": True,
    }


def mesh(h, circle_nodes, out):
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("General.NumThreads", 1)
        gmsh.model.add("F2_C1_pressure_footprint")
        ring = gmsh.model.occ.importShapes(str(STEP))
        volume = sum(gmsh.model.occ.getMass(*v) for v in ring)
        tools = (
            [(2, gmsh.model.occ.addDisk(x, y, 12.2, 7, 7)) for x, y in CENTRES]
            if PARTITION_KIND == "boundary"
            else [(3, gmsh.model.occ.addCylinder(x, y, 0, 0, 0, 12.2, 7)) for x, y in CENTRES]
        )
        allvol, mapping = gmsh.model.occ.fragment(ring, tools)
        keep = {v for mapped in mapping[: len(ring)] for v in mapped if v[0] == 3}
        gmsh.model.occ.remove([v for v in allvol if v[0] == 3 and v not in keep], recursive=True)
        gmsh.model.occ.synchronize()
        if PARTITION_KIND == "boundary":
            boundary = set(
                gmsh.model.getBoundary(gmsh.model.getEntities(3), combined=True, oriented=False)
            )
            unused = [f for f in gmsh.model.getEntities(2) if f not in boundary]
            gmsh.model.occ.remove(unused, recursive=True)
            gmsh.model.occ.synchronize()
        actual = sum(gmsh.model.occ.getMass(*v) for v in gmsh.model.getEntities(3))
        if abs(actual / volume - 1) > 1e-8:
            raise ValueError("ring material/void occupancy changed")
        for option, value in [
            ("Mesh.MeshSizeMin", h),
            ("Mesh.MeshSizeMax", h),
            ("Mesh.MinimumCircleNodes", circle_nodes),
            ("Mesh.SecondOrderLinear", 1),
        ]:
            gmsh.option.setNumber(option, value)
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.setOrder(2)
        ids, xyz, _ = gmsh.model.mesh.getNodes()
        nodes = {int(n): p for n, p in zip(ids, np.asarray(xyz).reshape(-1, 3))}
        if len(nodes) > 100000:
            (out / "node-budget-stop.json").write_text(
                json.dumps({"nodes": len(nodes), "limit": 100000, "solver_executed": False})
            )
            raise ValueError("node budget exceeded before solver")
        types, ids, conn = gmsh.model.mesh.getElements(3)
        elements = {}
        volumes = {}
        deviation = 0.0
        for typ, ee, cc in zip(types, ids, conn):
            if typ != 11:
                raise ValueError("expected complete C3D10")
            for eid, row in zip(ee, np.asarray(cc).reshape(-1, 10)):
                row = [int(n) for n in row]
                points = np.array([nodes[n] for n in row])
                v = np.linalg.det((points[1:4] - points[0]).T) / 6
                if v <= 0:
                    raise ValueError("nonpositive element volume before solver")
                pairs = [(0, 1), (1, 2), (2, 0), (0, 3), (2, 3), (1, 3)]
                deviation = max(
                    deviation,
                    max(
                        np.linalg.norm(points[4 + i] - (points[a] + points[b]) / 2)
                        for i, (a, b) in enumerate(pairs)
                    ),
                )
                elements[int(eid)] = [row[i] for i in [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]]
                volumes[int(eid)] = v
        qualities = gmsh.model.mesh.getElementQualities(list(elements), "minSJ")
        if deviation > 1e-8 or min(qualities) <= 0:
            raise ValueError("non-affine/invalid quadratic mesh; stop before solver")
        if abs(sum(volumes.values()) / volume - 1) > 0.01:
            raise ValueError("mesh volume approximation exceeds1percent")
        loads = {"load0": {}, "load1": {}}
        supports = {g: {} for g in ["outer", "inner", "tabs"]}
        areas = {g: 0.0 for g in [*loads, *supports]}
        for _, face in gmsh.model.getBoundary(
            gmsh.model.getEntities(3), combined=True, oriented=False
        ):
            types, _, conn = gmsh.model.mesh.getElements(2, face)
            for typ, cc in zip(types, conn):
                if typ != 9:
                    raise ValueError("expected TRI6 boundary")
                for tri in np.asarray(cc).reshape(-1, 6):
                    tri = [int(n) for n in tri]
                    p = np.array([nodes[n] for n in tri])
                    centre = p[:3].mean(axis=0)
                    r = np.linalg.norm(centre[:2])
                    key = None
                    if max(abs(p[:, 2] - 12.2)) < 1e-6:
                        for i, eye in enumerate(CENTRES):
                            if np.linalg.norm(centre[:2] - eye) < 7.00001:
                                key = "load" + str(i)
                    elif max(abs(p[:, 2] - 4.8)) < 1e-6:
                        key = "tabs"
                    elif abs(r - 32.3) < 0.15 and np.ptp(p[:, 2]) > 1e-4:
                        key = "outer"
                    elif abs(r - 15.8845) < 0.15 and np.ptp(p[:, 2]) > 1e-4:
                        key = "inner"
                    if key:
                        q, w, area = triangle6(p)
                        areas[key] += area
                        dest = loads[key] if key in loads else supports[key]
                        for n, value in zip(tri, q if key in loads else w):
                            dest[n] = dest.get(n, 0) + float(value)
        if min(areas.values()) <= 0:
            raise ValueError("required surface absent")
        exact = math.pi * (7**2 - 2.25**2)
        for i, eye in enumerate(CENTRES):
            load = loads["load" + str(i)]
            centre = sum(nodes[n] * w for n, w in load.items()) / sum(load.values())
            if (
                abs(areas["load" + str(i)] / exact - 1) > 0.01
                or np.linalg.norm(centre[:2] - eye) > 0.05
            ):
                raise ValueError("footprint area/centroid accuracy failed before solver")
        gmsh.write(str(out / "mesh.msh"))
        quality = {
            "nodes": len(nodes),
            "elements": len(elements),
            "minimum_scaled_Jacobian": float(min(qualities)),
            "maximum_midpoint_deviation_mm": deviation,
            "Jacobian_scope": "affine each tetra; positive throughout, not only sampled",
            "CAD_volume_mm3": volume,
            "mesh_volume_mm3": sum(volumes.values()),
            "surface_area_mm2": areas,
            "analytic_footprint_area_mm2": exact,
            "minimum_circle_nodes": circle_nodes,
            "partition_kind": PARTITION_KIND,
        }
        (out / "mesh-check.json").write_text(json.dumps(quality, indent=2) + "\n")
        return nodes, elements, volumes, loads, supports, quality
    finally:
        gmsh.finalize()


def solve(h, circle_nodes, base):
    out = base / str(h)
    out.mkdir()
    started = time.monotonic()
    cpu_start = (
        resource.getrusage(resource.RUSAGE_SELF).ru_utime
        + resource.getrusage(resource.RUSAGE_SELF).ru_stime
    )
    child_start = (
        resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime
        + resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime
    )
    nodes, elements, volumes, loads, supports, quality = mesh(h, circle_nodes, out)
    stiffness = {
        "outer": 500 * math.pi * (33.401**2 - 32.512**2) / 100,
        "inner": 500 * math.pi * (15.6845**2 - 14.5845**2) / 165,
        "tabs": 3 * 1000 * 6 * 17.5165 / 109.8,
    }
    deck = ["*HEADING", "F2-C1 hypothetical component fixture N mm MPa", "*NODE"] + [
        f"{n}," + ",".join(f"{x:.12g}" for x in p) for n, p in nodes.items()
    ]
    deck += ["*ELEMENT,TYPE=C3D10,ELSET=WOOD"] + [
        f"{e}," + ",".join(map(str, row)) for e, row in elements.items()
    ]
    deck += [
        "*MATERIAL,NAME=WOOD_ESTIMATE",
        "*ELASTIC",
        "1000.,0.25",
        "*SOLID SECTION,ELSET=WOOD,MATERIAL=WOOD_ESTIMATE",
    ]
    springs = []
    eid = max(elements) + 1
    for group, weights in supports.items():
        for n, w in weights.items():
            k = stiffness[group] * w / sum(weights.values())
            name = f"K{eid}"
            deck += [
                "*ELEMENT,TYPE=SPRING1,ELSET=" + name,
                f"{eid},{n}",
                "*SPRING,ELSET=" + name,
                "3",
                f"{k:.12e}",
            ]
            springs.append((group, n, k, w))
            eid += 1
    n0 = min(nodes, key=lambda n: np.linalg.norm(nodes[n] - [32.3, 0, 0]))
    n1 = min(nodes, key=lambda n: np.linalg.norm(nodes[n] - [-32.3, 0, 0]))
    deck += ["*BOUNDARY", f"{n0},1,2,0", f"{n1},2,2,0", "*NSET,NSET=ALLN"] + [
        ",".join(map(str, list(nodes)[i : i + 12])) for i in range(0, len(nodes), 12)
    ]
    vectors = []
    for shares in [[0.7, 0.3], [1.0, 0.0]]:
        f = {}
        for i, share in enumerate(shares):
            weights = loads["load" + str(i)]
            for n, w in weights.items():
                f[n] = f.get(n, 0) - 100 * share * w / sum(weights.values())
        vectors.append(f)
        deck += ["*STEP", "*STATIC", "*CLOAD,OP=NEW"] + [
            f"{n},3,{f0:.12e}" for n, f0 in f.items() if f0
        ]
        deck += ["*NODE PRINT,NSET=ALLN", "U", "*EL PRINT,ELSET=WOOD", "S", "*END STEP"]
    (out / "case.inp").write_text("\n".join(deck) + "\n")
    ccx = solver_path()
    if not ccx:
        raise ValueError("pinned solver unavailable")
    cpu_used = (
        resource.getrusage(resource.RUSAGE_SELF).ru_utime
        + resource.getrusage(resource.RUSAGE_SELF).ru_stime
        - cpu_start
    )
    remaining_cpu = math.floor(60 - cpu_used)
    remaining_wall = 120 - (time.monotonic() - started)
    if remaining_cpu < 1 or remaining_wall < 1:
        raise ValueError("grid resource budget reached before solver")

    def child_limit():
        resource.setrlimit(resource.RLIMIT_CPU, (remaining_cpu, remaining_cpu))

    p = subprocess.run(
        [ccx, "-i", "case"],
        cwd=out,
        capture_output=True,
        text=True,
        timeout=remaining_wall,
        preexec_fn=child_limit,
        check=False,
        env={
            **os.environ,
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "VECLIB_MAXIMUM_THREADS": "1",
            "CCX_NPROC_RESULTS": "1",
        },
    )
    (out / "solver.log").write_text(p.stdout + p.stderr)
    if p.returncode:
        raise ValueError("solver failed; stop packet")
    phases = []
    phase = None
    mode = None
    for line in (out / "case.dat").read_text().splitlines():
        if "displacements (" in line.lower():
            phase = {"u": {}, "s": []}
            phases.append(phase)
            mode = "u"
            continue
        if "stresses (" in line.lower():
            mode = "s"
            continue
        try:
            r = [float(x) for x in line.split()]
        except ValueError:
            continue
        if not r or phase is None:
            continue
        if mode == "u" and len(r) == 4:
            phase["u"][int(r[0])] = np.array(r[1:])
        elif mode == "s" and len(r) == 8:
            phase["s"].append(r)
    if len(phases) != 2:
        raise ValueError("missing calculated phases")
    results = []
    for phase, f in zip(phases, vectors):
        u = phase["u"]
        stress = np.asarray(phase["s"])
        s = stress[:, 2:]
        w = np.array([volumes[int(e)] / 4 for e in stress[:, 0]])
        if len(stress) != 4 * len(elements):
            raise ValueError("integration-point coverage is incomplete")
        xx, yy, zz, xy, xz, yz = s.T
        vm = np.sqrt(
            ((xx - yy) ** 2 + (yy - zz) ** 2 + (zz - xx) ** 2) / 2
            + 3 * (xy * xy + xz * xz + yz * yz)
        )
        tensors = np.zeros((len(s), 3, 3))
        tensors[:, 0, 0] = xx
        tensors[:, 1, 1] = yy
        tensors[:, 2, 2] = zz
        tensors[:, 0, 1] = tensors[:, 1, 0] = xy
        tensors[:, 0, 2] = tensors[:, 2, 0] = xz
        tensors[:, 1, 2] = tensors[:, 2, 1] = yz
        principal = np.max(abs(np.linalg.eigvalsh(tensors)), axis=1)

        def quantile(values, weights=w):
            order = np.argsort(values)
            return float(
                np.interp(0.95 * np.sum(weights), np.cumsum(weights[order]), values[order])
            )

        external = 0.5 * sum(force * u[n][2] for n, force in f.items())
        spring_energy = 0.5 * sum(k * u[n][2] ** 2 for _, n, k, _ in springs)
        density = (
            0.5
            / 1000
            * (
                xx * xx
                + yy * yy
                + zz * zz
                - 0.5 * (xx * yy + yy * zz + zz * xx)
                + 2.5 * (xy * xy + xz * xz + yz * yz)
            )
        )
        solid_energy = float(w @ density)
        reaction = {g: 0.0 for g in supports}
        moment = np.zeros(2)
        force = sum(f.values())
        applied = np.array(
            [
                sum(nodes[n][1] * fz for n, fz in f.items()),
                -sum(nodes[n][0] * fz for n, fz in f.items()),
            ]
        )
        for group, n, k, _ in springs:
            rf = -k * u[n][2]
            reaction[group] += rf
            moment += rf * np.array([nodes[n][1], -nodes[n][0]])
        force_error = abs(sum(reaction.values()) + force) / 100
        moment_error = float(np.linalg.norm(applied + moment) / (100 * 32.3))
        energy_error = abs((solid_energy + spring_energy) / external - 1)
        if max(force_error, moment_error, energy_error) > 1e-5:
            raise ValueError("force/moment/energy consistency failed")
        results.append(
            {
                "load_N": 100,
                "reaction_N": reaction,
                "force_error": force_error,
                "moment_error": moment_error,
                "energy_error": energy_error,
                "external_half_work_Nmm": external,
                "solid_energy_Nmm": solid_energy,
                "spring_energy_Nmm": spring_energy,
                "maximum_displacement_mm": max(abs(v[2]) for v in u.values()),
                "VM_max_MPa": float(max(vm)),
                "VM_volume_p95_MPa": quantile(vm),
                "absolute_principal_max_MPa": float(max(principal)),
                "absolute_principal_volume_p95_MPa": quantile(principal),
            }
        )
    work12 = sum(f * phases[1]["u"][n][2] for n, f in vectors[0].items())
    work21 = sum(f * phases[0]["u"][n][2] for n, f in vectors[1].items())
    reciprocal = abs(work12 - work21) / max(abs(work12), abs(work21))
    if reciprocal > 1e-5:
        raise ValueError("reciprocal-work consistency failed")
    cpu_used = (
        resource.getrusage(resource.RUSAGE_SELF).ru_utime
        + resource.getrusage(resource.RUSAGE_SELF).ru_stime
        - cpu_start
        + resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime
        + resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime
        - child_start
    )
    if cpu_used > 60 or time.monotonic() - started > 120:
        raise ValueError("grid resource budget exceeded; no further grid")
    result = {
        "cpu_s": cpu_used,
        "h_mm": h,
        "quality": quality,
        "cases": results,
        "reciprocal_work_error": reciprocal,
        "support_stiffness_N_mm": stiffness,
        "wall_s": time.monotonic() - started,
        "installed_strength_accepted": False,
    }
    (out / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("preserve existing results; output must be new")
    args.output.mkdir(parents=True)
    resource.setrlimit(resource.RLIMIT_CPU, (180, 180))
    start = time.monotonic()
    reports = []
    failure = None
    try:
        if digest(SPEC) != EXPECTED_SPEC or digest(STEP) != EXPECTED_STEP:
            raise ValueError("frozen source identity mismatch")
        known = known_answer()
        (args.output / "known-answer.json").write_text(json.dumps(known, indent=2) + "\n")
        for h, n in [(3.0, 32), (2.0, 48), (1.4, 69)]:
            result = solve(h, n, args.output)
            reports.append(result)
            print("completed", h, "wall", result["wall_s"], flush=True)
            if time.monotonic() - start > 300:
                raise ValueError("aggregate wall budget reached")
    except (ValueError, RuntimeError, OSError, KeyError, subprocess.TimeoutExpired) as error:
        failure = repr(error)
    refinement = {}
    if len(reports) == 3:
        for i, label in enumerate(["seventy_thirty", "single_anchor"]):
            a, b = reports[-2]["cases"][i], reports[-1]["cases"][i]
            refinement[label] = {
                key: abs(b[key] / a[key] - 1)
                for key in [
                    "maximum_displacement_mm",
                    "absolute_principal_volume_p95_MPa",
                    "absolute_principal_max_MPa",
                ]
            }
    record = {
        "identity": "G80-F2-C1-pressure-footprint-v1",
        "source_spec_sha256": digest(SPEC),
        "source_STEP_sha256": digest(STEP),
        "producer_sha256": digest(Path(__file__)),
        "reports": reports,
        "refinement": refinement,
        "failure": failure,
        "wall_s": time.monotonic() - start,
        "installed_strength_accepted": False,
        "scope": "hypothetical finite-support component fixture; purchased eye/contact, global inertia/load route and orthotropic joint capacity unresolved",
    }
    (args.output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "failure": failure,
                "grids": len(reports),
                "wall_s": record["wall_s"],
                "refinement": refinement,
            }
        )
    )
    raise SystemExit(bool(failure))
