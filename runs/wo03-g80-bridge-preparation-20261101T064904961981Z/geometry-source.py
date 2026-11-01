"""Bounded bridge diagnostic: existing axial and independent shear fixtures."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-g80-bridge-fea.yaml"
OUT = ROOT / "build/wo03-g80-bridge-fea-v1"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


class Task(ctypes.Structure):
    _fields_ = [
        (name, ctypes.c_uint64)
        for name in (
            "virtual",
            "resident",
            "total_user",
            "total_system",
            "threads_user",
            "threads_system",
        )
    ] + [(f"i{i}", ctypes.c_int32) for i in range(12)]


def proc_lib():
    lib = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
    lib.proc_pidinfo.argtypes = [
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint64,
        ctypes.c_void_p,
        ctypes.c_int,
    ]
    lib.proc_pidinfo.restype = ctypes.c_int
    lib.proc_listchildpids.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
    lib.proc_listchildpids.restype = ctypes.c_int
    return lib


def children(lib, pid):
    arr = (ctypes.c_int * 256)()
    n = lib.proc_listchildpids(pid, arr, ctypes.sizeof(arr))
    if n < 0 or n >= len(arr):
        raise RuntimeError("Cannot enumerate owned process children within guard")
    return list(arr)[:n]


def rss(lib, pid):
    x = Task()
    if lib.proc_pidinfo(pid, 4, 0, ctypes.byref(x), ctypes.sizeof(x)) != ctypes.sizeof(x):
        raise ProcessLookupError(f"Live RSS unavailable for {pid}")
    return x.resident


def validate_monitor(lib):
    code = "import time; x=bytearray(16777216); print('ready',flush=True); time.sleep(5)"
    p = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.PIPE, text=True)
    try:
        if p.stdout.readline().strip() != "ready" or rss(lib, p.pid) < 16777216:
            raise RuntimeError("RSS monitor sentinel failed")
        if p.pid not in children(lib, os.getpid()):
            raise RuntimeError("Cannot enumerate owned sentinel child")
    finally:
        p.terminate()
        p.wait()


def group_pids(lib, parent):
    todo = [parent]
    found = []
    while todo:
        pid = todo.pop()
        if pid in found:
            continue
        found.append(pid)
        todo.extend(children(lib, pid))
    return found


def parse_dat(path, coords):
    sections = {"U": [], "RF": []}
    kind = None
    for line in path.read_text().splitlines():
        low = line.lower()
        if "displacements (" in low:
            kind = "U"
            continue
        if "forces (" in low:
            kind = "RF"
            continue
        f = line.split()
        if kind and len(f) >= 4:
            try:
                node = int(f[0])
                vals = [float(x) for x in f[1:4]]
            except ValueError:
                continue
            if node in coords:
                sections[kind].append((node, *vals))
    if not all(sections.values()):
        raise ValueError("Missing fixture displacement or force output")
    return sections


def shear_fixture(folder, cfg):
    import gmsh

    from src.analysis.support_fea import _quadratic_tets, _run_ccx

    folder.mkdir(parents=True, exist_ok=False)
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("thin_bonded_shear")
        a = gmsh.model.occ.addBox(0, 0, 0, 10, 10, 0.1)
        b = gmsh.model.occ.addBox(0, 0, 0.1, 10, 10, 2.0)
        _, mapping = gmsh.model.occ.fragment([(3, a)], [(3, b)])
        gmsh.model.occ.synchronize()
        gmsh.option.setNumber("Mesh.MeshSizeMin", 0.1)
        gmsh.option.setNumber("Mesh.MeshSizeMax", 2.0)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.optimize("HighOrder")
        coords, elements = _quadratic_tets(gmsh)
        if len(coords) > cfg["maximum_nodes"] or len(elements) > cfg["maximum_tetrahedra"]:
            raise ValueError("Fixture mesh exceeds node/element guard")
        ips, _ = gmsh.model.mesh.getIntegrationPoints(11, "Gauss4")
        _, dets, _ = gmsh.model.mesh.getJacobians(11, ips)
        if not len(dets) or not np.isfinite(dets).all() or min(dets) <= 0:
            raise ValueError("Invalid thin-layer Jacobian")
        groups = []
        for entities in mapping:
            ids = []
            for dim, tag in entities:
                if dim != 3:
                    continue
                for typ, tags in zip(*gmsh.model.mesh.getElements(3, tag)[:2], strict=True):
                    if typ != 11:
                        raise ValueError("Unexpected element type")
                    ids.extend(int(v) for v in tags)
            groups.append(ids)
        if (
            len(groups) != 2
            or not all(groups)
            or set(groups[0]) & set(groups[1])
            or set(groups[0]) | set(groups[1]) != set(elements)
        ):
            raise ValueError("Fixture material ownership invalid")
        loads = {}
        area = 0.0
        for _, face in gmsh.model.getEntities(2):
            bb = gmsh.model.getBoundingBox(2, face)
            if abs(bb[2] - 2.1) > 1e-5 or abs(bb[5] - 2.1) > 1e-5:
                continue
            types, _, conn = gmsh.model.mesh.getElements(2, face)
            for typ, raw in zip(types, conn, strict=True):
                if typ != 9:
                    raise ValueError("Unexpected traction facet")
                for tri in np.asarray(raw).reshape(-1, 6):
                    x, y, z = [coords[int(i)] for i in tri[:3]]
                    ar = float(np.linalg.norm(np.cross(y - x, z - x)) / 2)
                    area += ar
                    for node in tri[3:]:
                        loads[int(node)] = loads.get(int(node), 0) + ar / 30
        if abs(area - 100) > 1e-5 or abs(sum(loads.values()) - 10) > 1e-8:
            raise ValueError("Fixture traction area/force mismatch")
    finally:
        gmsh.finalize()
    bottom = sorted(n for n, x in coords.items() if abs(x[2]) < 1e-7)
    interface = sorted(n for n, x in coords.items() if abs(x[2] - 0.1) < 1e-7)
    top = sorted(n for n, x in coords.items() if abs(x[2] - 2.1) < 1e-7)
    if not all((bottom, interface, top)):
        raise ValueError("Missing fixture face nodes")
    deck = ["*HEADING", "thin bonded shear", "*NODE"] + [
        f"{n}," + ",".join(f"{v:.12g}" for v in x) for n, x in coords.items()
    ]
    deck += ["*ELEMENT,TYPE=C3D10,ELSET=ALL"] + [
        f"{n}," + ",".join(map(str, c)) for n, c in elements.items()
    ]
    for name, ids in [("BOND", groups[0]), ("BRIDGE", groups[1])]:
        deck += [f"*ELSET,ELSET={name}"] + [
            ",".join(map(str, ids[i : i + 16])) for i in range(0, len(ids), 16)
        ]
    for name, ids in [("ALL", sorted(coords)), ("BOTTOM", bottom)]:
        deck += [f"*NSET,NSET={name}"] + [
            ",".join(map(str, ids[i : i + 16])) for i in range(0, len(ids), 16)
        ]
    for name, E in [("BOND", 100), ("BRIDGE", 10000)]:
        deck += [
            f"*MATERIAL,NAME={name}",
            "*ELASTIC",
            f"{E},0.3",
            f"*SOLID SECTION,ELSET={name},MATERIAL={name}",
        ]
    deck += ["*BOUNDARY", "ALL,2,3,0", "BOTTOM,1,1,0", "*STEP", "*STATIC", "*CLOAD"] + [
        f"{n},1,{f:.12g}" for n, f in loads.items()
    ]
    deck += ["*NODE PRINT,NSET=ALL", "U", "*NODE PRINT,NSET=BOTTOM", "RF", "*END STEP"]
    (folder / "case.inp").write_text("\n".join(deck) + "\n")
    _run_ccx(folder)
    parsed = parse_dat(folder / "case.dat", coords)
    bynode = {r[0]: r[1] for r in parsed["U"]}
    if not set(interface + top) <= bynode.keys():
        raise ValueError("Missing interface/top displacements")
    ui = float(np.mean([bynode[n] for n in interface]))
    ut = float(np.mean([bynode[n] for n in top]))
    reaction = sum(r[1] for r in parsed["RF"])
    g1 = 100 / (2 * 1.3)
    g2 = 10000 / (2 * 1.3)
    exact = 10 / 100 * (0.1 / g1 + 2 / g2)
    expected_energy = 0.5 * 10 * exact
    reconstructed_energy = 0.5 * 100 * (g1 * ui**2 / 0.1 + g2 * (ut - ui) ** 2 / 2)
    external_energy = 0.5 * 10 * ut
    out = {
        "area_mm2": area,
        "force_N": sum(loads.values()),
        "expected_displacement_mm": exact,
        "top_displacement_mm": ut,
        "interface_displacement_mm": ui,
        "reaction_N": reaction,
        "expected_energy_Nmm": expected_energy,
        "reconstructed_layer_energy_Nmm": reconstructed_energy,
        "external_work_Nmm": external_energy,
        "nodes": len(coords),
        "tetrahedra": len(elements),
        "minimum_jacobian": float(min(dets)),
        "energy_basis": "Reconstructed homogeneous-layer strain energy from interface/top displacements, not native CCX element energy.",
    }
    if (
        abs(ut / exact - 1) > 0.01
        or abs(reaction + 10) > 1e-5
        or abs(reconstructed_energy / expected_energy - 1) > 0.02
        or abs(external_energy / expected_energy - 1) > 0.01
    ):
        raise ValueError(f"Thin shear known-case mismatch: {out}")
    (folder / "report.json").write_text(json.dumps(out, indent=2) + "\n")
    return out


def geometry_preflight(cfg):
    """Verify each proposed adhesive pair and measured washer area on saved BReps."""
    import cadquery as cq
    from OCP.OSD import OSD_Parallel, OSD_ThreadPool

    from scripts.wo03_root_contact_faces import measure

    OSD_Parallel.SetUseOcctThreads_s(True)
    pool = OSD_ThreadPool.DefaultPool_s()
    pool.Init(1)
    if pool.NbThreads() != 1:
        raise ValueError("OCCT pool is not one")
    source = ROOT / "build/wo03-g80-keeper-service-v1"
    bridge = cq.importers.importStep(str(source / "bridge.step")).val()
    rail = cq.importers.importStep(str(source / "modified_mount.step")).val()
    settings = {"positive_patch_area_mm2": 1e-7, "normal_opposition_dot_max": -0.999}
    pairs = []
    cylinder = cq.Solid.makeCylinder(32.2, 15, cq.Vector(0, 0, 172.1))
    for angle in (0, 120, 240):
        for side in (-1, 1):
            origin_y = 6.0 if side == 1 else -6.1
            blank = cq.Solid.makeBox(7.2, 0.1, 15, cq.Vector(25, origin_y, 172.1))
            film = blank.intersect(cylinder).rotate((0, 0, 0), (0, 0, 1), angle)
            if not film.isValid() or len(film.Solids()) != 1 or film.Volume() <= 0:
                raise ValueError("Invalid proposed adhesive film")
            if film.intersect(bridge).Volume() > 1e-5 or film.intersect(rail).Volume() > 1e-5:
                raise ValueError("Proposed film overlaps adherend volume")
            on_bridge = measure(film, bridge, settings)
            on_rail = measure(film, rail, settings)
            if (
                not on_bridge["all_sample_normals_opposed"]
                or not on_rail["all_sample_normals_opposed"]
            ):
                raise ValueError("Adhesive interface normal is not opposed")
            if not (
                98 < on_bridge["coincident_area_mm2"] < 101
                and 98 < on_rail["coincident_area_mm2"] < 101
            ):
                raise ValueError(
                    f"Incomplete or ambiguous tab surface: {angle}, {side}, {on_bridge['coincident_area_mm2']}, {on_rail['coincident_area_mm2']}"
                )
            pairs.append(
                {
                    "angle_deg": angle,
                    "side": side,
                    "volume_mm3": film.Volume(),
                    "bridge": on_bridge,
                    "rail": on_rail,
                }
            )
    seats = []
    for i in range(3):
        washer = cq.importers.importStep(str(source / f"washer_{i}.step")).val()
        result = measure(bridge, washer, settings)
        if (
            abs(result["coincident_area_mm2"] - 54.53804846658) > 1e-5
            or not result["all_sample_normals_opposed"]
        ):
            raise ValueError(
                f"Washer seat mapping failed at axis {i}: {result['coincident_area_mm2']}"
            )
        seats.append(result)
    output = {
        "status": "six_finite_films_and_three_seats_nominally_mapped",
        "pairs": pairs,
        "washer_seats": seats,
        "physical_wetting": "unavailable",
        "mesh_or_solver": "not performed",
    }
    (OUT / "geometry-preflight.json").write_text(json.dumps(output, indent=2) + "\n")
    return {
        "pair_count": len(pairs),
        "bridge_areas_mm2": [x["bridge"]["coincident_area_mm2"] for x in pairs],
        "rail_areas_mm2": [x["rail"]["coincident_area_mm2"] for x in pairs],
        "seat_areas_mm2": [x["coincident_area_mm2"] for x in seats],
    }


def worker(name, cfg):
    resource.setrlimit(resource.RLIMIT_CPU, (cfg["worker_cpu_limit_s"], cfg["worker_cpu_limit_s"]))
    os.environ["CCX"] = cfg["ccx"]
    folder = OUT / name
    if name == "axial_fixture":
        from src.analysis.fea import axial_bar

        result = axial_bar(folder, 3.0)
        if (
            not result.get("passed")
            or result["node_count"] > cfg["maximum_nodes"]
            or result["element_count"] > cfg["maximum_tetrahedra"]
        ):
            raise ValueError(f"Axial fixture failed: {result}")
    elif name == "shear_fixture":
        result = shear_fixture(folder, cfg)
    elif name == "geometry_preflight":
        result = geometry_preflight(cfg)
    else:
        raise ValueError("Actual bridge emitter not yet implemented")
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    own = resource.getrusage(resource.RUSAGE_SELF)
    print(
        json.dumps(
            {
                "name": name,
                "result": result,
                "process_and_children_cpu_s": own.ru_utime
                + own.ru_stime
                + child.ru_utime
                + child.ru_stime,
            }
        ),
        flush=True,
    )


def packet(cfg, geometry_only=False):
    lib = proc_lib()
    validate_monitor(lib)
    paths = [
        CONFIG,
        Path(__file__).resolve(),
        ROOT / cfg["source_preflight"],
        ROOT / cfg["bridge_step"],
        Path(cfg["ccx"]),
        ROOT / "src/analysis/fea.py",
        ROOT / "src/analysis/support_fea.py",
        ROOT / "scripts/wo03_root_contact_faces.py",
        ROOT / "build/wo03-g80-keeper-service-v1/modified_mount.step",
        *(ROOT / f"build/wo03-g80-keeper-service-v1/washer_{i}.step" for i in range(3)),
    ]
    if (
        sha(ROOT / cfg["bridge_step"]) != cfg["bridge_sha256"]
        or sha(Path(cfg["ccx"])) != cfg["ccx_sha256"]
    ):
        raise ValueError("Pinned bridge/solver hash mismatch")
    before = {str(p): sha(p) for p in paths}
    results = []
    for name in (("geometry_preflight",) if geometry_only else ("axial_fixture", "shear_fixture")):

        proc = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "--worker", name],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
        start = time.monotonic()
        peak = 0
        try:
            while proc.poll() is None:
                if time.monotonic() - start > cfg["child_wall_limit_s"]:
                    raise TimeoutError("wall guard")
                try:
                    for pid in group_pids(lib, proc.pid):
                        try:
                            peak = max(peak, rss(lib, pid))
                        except ProcessLookupError:
                            if proc.poll() is None and pid == proc.pid:
                                raise
                except ProcessLookupError:
                    if proc.poll() is None:
                        raise
                if peak > cfg["maximum_process_rss_bytes"]:
                    raise MemoryError("RSS guard")
                time.sleep(0.05)
            output = proc.stdout.read()
            (OUT / f"{name}.log").write_text(output)
            if proc.returncode:
                raise RuntimeError(f"{name} failed (exit {proc.returncode}); see preserved log")
            results.append(
                {
                    "name": name,
                    "child_wall_s": time.monotonic() - start,
                    "observed_peak_process_rss_bytes": peak,
                    "worker_output": output.strip(),
                }
            )
        except BaseException:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
            raise
    after = {str(p): sha(p) for p in paths}
    if before != after:
        raise ValueError("Inputs changed")
    out = {
        "status": "fixtures_complete_bridge_face_emitter_unavailable",
        "cases": results,
        "inputs_before": before,
        "inputs_after": after,
        "remaining": "Exact bridge/adhesive face ownership, finite load patches and 3D CalculiX emitter not implemented; no bridge mesh/solve.",
        "acceptance": False,
    }
    (OUT / ("geometry-packet.json" if geometry_only else "packet.json")).write_text(
        json.dumps(out, indent=2) + "\n"
    )
    print(json.dumps(out, indent=2))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--worker", choices=["axial_fixture", "shear_fixture", "geometry_preflight"])
    p.add_argument("--map-geometry", action="store_true")
    a = p.parse_args()
    cfg = yaml.safe_load(CONFIG.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    if a.worker:
        worker(a.worker, cfg)
    else:
        packet(cfg, geometry_only=a.map_geometry)


if __name__ == "__main__":
    main()
