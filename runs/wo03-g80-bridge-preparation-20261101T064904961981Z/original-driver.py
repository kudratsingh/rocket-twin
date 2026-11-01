"""Bounded bridge diagnostic: existing axial and independent shear fixtures."""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import re
import resource
import signal
import subprocess
import sys
import time
from itertools import pairwise
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


def _rounding_half_width(token):
    """Half of the last displayed decimal unit for one scientific token."""
    m = re.fullmatch(r"[+-]?(\d+)(?:\.(\d*))?[EeDd]([+-]?\d+)", token)
    if not m:
        raise ValueError(f"Unexpected CalculiX numeric format: {token}")
    return 0.5 * 10.0 ** (int(m.group(3)) - len(m.group(2) or ""))


def parse_native_dat(path):
    """Parse only labeled DAT U, RF and six-component integration-point S blocks."""
    marker = re.compile(r"^\s*S\s+T\s+E\s+P\s+(\d+)\s*$", re.IGNORECASE)
    header = re.compile(
        r"^\s*(displacements|forces|stresses)\s*\([^)]*\)\s+for set\s+(\S+)\s+and time\s+(\S+)",
        re.IGNORECASE,
    )
    sections = {}
    step = None
    current = None
    for line in path.read_text().splitlines():
        m = marker.match(line)
        if m:
            step = int(m.group(1))
            current = None
            continue
        h = header.match(line)
        if h:
            if step is None:
                raise ValueError("DAT output header precedes step marker")
            current = (step, h.group(1).lower(), h.group(2).upper())
            if current in sections:
                raise ValueError(f"Duplicate DAT section {current}")
            sections[current] = []
            continue
        fields = line.split()
        if not fields or current is None:
            continue
        if not re.fullmatch(r"\d+", fields[0]):
            current = None
            continue
        stress = current[1] == "stresses"
        expected = 8 if stress else 4
        if len(fields) != expected:
            raise ValueError(f"Malformed DAT row in {current}: {line}")
        try:
            node = int(fields[0])
            ip = int(fields[1]) if stress else None
            tokens = fields[2:] if stress else fields[1:]
            values = [float(v.replace("D", "E").replace("d", "e")) for v in tokens]
            rounding = [_rounding_half_width(v) for v in tokens]
        except (ValueError, OverflowError) as exc:
            raise ValueError(f"Malformed DAT numeric row in {current}: {line}") from exc
        if not np.isfinite(values).all():
            raise ValueError("Nonfinite DAT values")
        sections[current].append(
            {"id": node, "integration_point": ip, "values": values, "rounding_half_width": rounding}
        )
    if not sections or any(not rows for rows in sections.values()):
        raise ValueError("Empty or missing native DAT sections")
    return sections


def force_and_moment(nodes, vectors):
    """Sum N and N mm vectors about mount center from explicitly selected nodes."""
    force = np.zeros(3)
    moment = np.zeros(3)
    for nid, vec in vectors.items():
        if nid not in nodes:
            raise ValueError(f"Force node {nid} has no coordinates")
        f = np.asarray(vec, dtype=float)
        x = np.asarray(nodes[nid], dtype=float)
        if (
            f.shape != (3,)
            or x.shape != (3,)
            or not np.isfinite(f).all()
            or not np.isfinite(x).all()
        ):
            raise ValueError("Malformed force or position vector")
        force += f
        moment += np.cross(x, f)
    return force, moment


def evaluate_balance(nodes, applied, reactions, force_tolerance_n=1e-5):
    """Calculate signed reactions and a conservative printed-rounding interval."""
    bynode = {}
    halfwidth = np.zeros(3)
    moment_halfwidth = np.zeros(3)
    for row in reactions:
        nid = row["id"]
        if nid in bynode:
            raise ValueError("Duplicate reaction node")
        bynode[nid] = row["values"]
        q = np.asarray(row["rounding_half_width"])
        halfwidth += q
        if nid not in nodes:
            raise ValueError("Reaction node lacks coordinates")
        x, y, z = np.abs(np.asarray(nodes[nid], dtype=float))
        moment_halfwidth += [y * q[2] + z * q[1], z * q[0] + x * q[2], x * q[1] + y * q[0]]
    af, am = force_and_moment(nodes, applied)
    rf, rm = force_and_moment(nodes, bynode)
    residual = af + rf
    moment_residual = am + rm
    r = float(np.linalg.norm(residual))
    e = float(np.linalg.norm(halfwidth))
    status = (
        "pass"
        if r + e <= force_tolerance_n
        else "fail" if max(0.0, r - e) > force_tolerance_n else "unavailable_print_precision"
    )
    return {
        "applied_force_N": af.tolist(),
        "reaction_force_N": rf.tolist(),
        "force_residual_N": residual.tolist(),
        "force_residual_norm_N": r,
        "reaction_print_rounding_bound_N": halfwidth.tolist(),
        "force_balance_status": status,
        "applied_moment_Nmm": am.tolist(),
        "reaction_moment_Nmm": rm.tolist(),
        "moment_residual_Nmm": moment_residual.tolist(),
        "reaction_moment_print_rounding_bound_Nmm": moment_halfwidth.tolist(),
        "moment_balance_status": "reported_not_thresholded",
    }


def external_work_energy(applied, displacements):
    """Linear static external work; not independent native internal energy."""
    bynode = {}
    for row in displacements:
        if row["id"] in bynode:
            raise ValueError("Duplicate displacement node")
        bynode[row["id"]] = row["values"]
    if not set(applied).issubset(bynode):
        raise ValueError("Missing applied-node displacement")
    value = 0.5 * sum(float(np.dot(applied[n], bynode[n])) for n in applied)
    if not math.isfinite(value) or value < -1e-10:
        raise ValueError("Invalid external work")
    return value


def summarize_stresses(rows, expected_elements):
    """Retain literal integration-point component extrema and their locators."""
    if not rows:
        raise ValueError("Missing integration-point stress output")
    expected = set(expected_elements)
    seen = set()
    values = []
    for row in rows:
        ident = (row["id"], row["integration_point"])
        if (
            ident in seen
            or row["id"] not in expected
            or row["integration_point"] not in (1, 2, 3, 4)
        ):
            raise ValueError("Duplicate or unexpected stress integration point")
        seen.add(ident)
        values.append(row["values"])
    if seen != {(element, ip) for element in expected for ip in (1, 2, 3, 4)}:
        raise ValueError("Incomplete four-point C3D10 stress output")
    values = np.asarray(values)
    result = {}
    for index, name in enumerate(("Sxx", "Syy", "Szz", "Sxy", "Sxz", "Syz")):
        imin = int(np.argmin(values[:, index]))
        imax = int(np.argmax(values[:, index]))
        result[name] = {
            "minimum_MPa": float(values[imin, index]),
            "minimum_element": rows[imin]["id"],
            "minimum_ip": rows[imin]["integration_point"],
            "maximum_MPa": float(values[imax, index]),
            "maximum_element": rows[imax]["id"],
            "maximum_ip": rows[imax]["integration_point"],
        }
    return result


def assess_native_step(sections, step, nodes, support_ids, applied, material_elements):
    """Account for one full independent CCX step without inferring missing energy."""

    def get(kind, name):
        key = (step, kind, name)
        if key not in sections:
            raise ValueError(f"Required native DAT section absent: {key}")
        return sections[key]

    u = get("displacements", "ALL")
    reactions = get("forces", "SUPPORT")
    if {row["id"] for row in u} != set(nodes):
        raise ValueError("DAT all-node displacement coverage differs from mesh")
    if {row["id"] for row in reactions} != set(support_ids):
        raise ValueError("DAT support reaction coverage differs from constrained nodes")
    balance = evaluate_balance(nodes, applied, reactions)
    work = external_work_energy(applied, u)
    if balance["force_balance_status"] == "fail":
        raise ValueError(f"Force equilibrium fails even allowing printed rounding: {balance}")
    result = {
        "balance": balance,
        "external_work_half_Fu_Nmm": work,
        "native_internal_energy": "unavailable unless independently emitted and verified",
        "effective_loaded_displacement_mm": 2 * work / 150.0,
        "material_stress_extrema": {},
        "regional_stress_convergence": "unavailable until verified fixed physical region integration metadata",
    }
    for material, element_ids in material_elements.items():
        result["material_stress_extrema"][material] = summarize_stresses(
            get("stresses", material), element_ids
        )
    return result


def convergence_changes(values, threshold):
    """Report literal consecutive relative changes; tiny denominators unavailable."""
    if len(values) != 3 or any(not math.isfinite(x) for x in values):
        raise ValueError("Three finite refinement values are required")
    ratios = [None if abs(a) <= 1e-15 else abs(b - a) / abs(a) for a, b in pairwise(values)]
    return {
        "values": values,
        "successive_relative_changes": ratios,
        "threshold": threshold,
        "last_change_status": (
            "unavailable" if ratios[-1] is None else "pass" if ratios[-1] < threshold else "fail"
        ),
    }


def normalize_adapter_materials(meta):
    """Translate six separately-owned film sets to the deck's output aliases."""
    raw = meta["material_element_ids"]
    expected = {"G11", *(f"EPOXY_{i}" for i in range(6))}
    if set(raw) != expected:
        raise ValueError("Expected one G11 and six distinct epoxy regions")
    sets = {name: {int(n) for n in values} for name, values in raw.items()}
    all_seen = set()
    for name, ids in sets.items():
        if not ids or all_seen & ids:
            raise ValueError(f"Missing or duplicate material ownership in {name}")
        all_seen.update(ids)
    return {"BRIDGE": sorted(sets["G11"]), "ADHESIVE": sorted(all_seen - sets["G11"])}


def adapter_step_forces(meta, step):
    key = {1: "EQUAL", 2: "SINGLE"}[step]
    return {int(k): v for k, v in meta["step_nodal_forces_N"][key].items()}


def assess_adapter_output(folder):
    """Verify source loads and two native steps using adapter-owned mesh metadata."""
    meta = json.loads((folder / "mesh-meta.json").read_text())
    nodes = {int(k): v for k, v in meta["coordinates_mm"].items()}
    support = [int(n) for n in meta["support_node_ids"]]
    materials = normalize_adapter_materials(meta)
    if set(materials) != {"BRIDGE", "ADHESIVE"} or not nodes or not support:
        raise ValueError("Missing required mesh material or support sets")
    if set(materials["BRIDGE"]) & set(materials["ADHESIVE"]):
        raise ValueError("Material elements overlap")
    sections = parse_native_dat(folder / "case.dat")
    if {key[0] for key in sections} != {1, 2}:
        raise ValueError("Expected exactly two native static steps")
    expected_moment = {
        1: np.zeros(3),
        2: np.array([150 * 25.5 * math.sin(math.pi / 3), -150 * 25.5 * math.cos(math.pi / 3), 0]),
    }
    reports = []
    for step in (1, 2):
        forces = adapter_step_forces(meta, step)
        applied_force, applied_moment = force_and_moment(nodes, forces)
        if (
            np.linalg.norm(applied_force - np.array([0.0, 0.0, 150.0])) > 1e-6
            or np.linalg.norm(applied_moment - expected_moment[step]) > 1e-4
        ):
            raise ValueError(f"Applied load or source-coordinate moment mismatch in step {step}")
        report = assess_native_step(sections, step, nodes, support, forces, materials)
        report["step"] = step
        report["expected_applied_force_N"] = [0, 0, 150]
        report["expected_applied_moment_Nmm"] = expected_moment[step].tolist()
        reports.append(report)
    return {
        "steps": reports,
        "node_count": len(nodes),
        "element_count": sum(map(len, materials.values())),
        "integration_point_order_verified": False,
        "regional_stress_convergence": "unavailable: CCX/Gmsh integration-point mapping not independently verified",
    }


def check_preserved_preflight(cfg):
    """Revalidate earlier known cases and geometric evidence without rerunning them."""
    known_cpu = 0.0
    for filename, snapshot in (
        ("packet.json", "fixtures-executed.py"),
        ("geometry-packet.json", "geometry-executed.py"),
    ):
        record = json.loads((OUT / filename).read_text())
        if record["inputs_before"] != record["inputs_after"]:
            raise ValueError(f"Source hashes changed in preserved {filename}")
        for name, expected in record["inputs_after"].items():
            p = Path(name)
            if p.resolve() == Path(__file__).resolve():
                p = OUT / snapshot
            elif p.resolve() == CONFIG.resolve():
                p = OUT / "fixtures-config.yaml"
            if not p.is_file() or sha(p) != expected:
                raise ValueError(f"Preserved preflight source mismatch: {name}")
        for case in record["cases"]:
            data = json.loads(case["worker_output"])
            known_cpu += data["process_and_children_cpu_s"]
            if case["name"] == "axial_fixture" and not data["result"]["passed"]:
                raise ValueError("Preserved axial fixture did not pass")
            if case["name"] == "shear_fixture":
                r = data["result"]
                if (
                    abs(r["top_displacement_mm"] / r["expected_displacement_mm"] - 1) > 0.01
                    or abs(r["reaction_N"] + 10) > 1e-5
                    or abs(r["reconstructed_layer_energy_Nmm"] / r["expected_energy_Nmm"] - 1)
                    > 0.02
                ):
                    raise ValueError("Preserved shear fixture did not pass")
            if case["name"] == "geometry_preflight" and (
                data["result"]["pair_count"] != 6 or len(data["result"]["seat_areas_mm2"]) != 3
            ):
                raise ValueError("Preserved source geometry mapping incomplete")
    if known_cpu >= cfg["packet_cpu_limit_s"]:
        raise ValueError("Original packet CPU budget exhausted")
    return {"known_prior_cpu_s": known_cpu, "fixtures_and_geometry_reused_without_rerun": True}


def validate_adapter_loads(meta, cfg):
    """Refuse to run the solver unless material ownership and source loads match."""
    nodes = {int(k): v for k, v in meta["coordinates_mm"].items()}
    supports = {int(n) for n in meta["support_node_ids"]}
    materials = {k: set(v) for k, v in normalize_adapter_materials(meta).items()}
    if (
        not nodes
        or not supports
        or not supports.issubset(nodes)
        or set(materials) != {"BRIDGE", "ADHESIVE"}
    ):
        raise ValueError("Adapter mesh node/support/material ownership invalid")
    if not all(materials.values()) or materials["BRIDGE"] & materials["ADHESIVE"]:
        raise ValueError("Adapter material volumes missing or duplicated")
    if (
        len(nodes) > cfg["maximum_nodes"]
        or sum(map(len, materials.values())) > cfg["maximum_tetrahedra"]
    ):
        raise ValueError("Adapter mesh exceeds fixed node/tetrahedron guards")
    if (
        meta.get("gmsh_version") != cfg["gmsh_version"]
        or not meta["jacobian"]["positive_all_samples"]
        or meta["jacobian"]["minimum_determinant"] <= 0
    ):
        raise ValueError("Adapter Gmsh version or sampled Jacobian invalid")
    if (
        meta["preflight"]["status"] != "adapter_preflight_passed_no_solver_invoked"
        or len(meta["film_surface_ownership"]) != 6
        or len(meta["washer_patches"]) != 3
    ):
        raise ValueError("Adapter face ownership/traction preflight incomplete")
    for patch in meta["washer_patches"]:
        if abs(patch["area_mm2"] - 54.5380484663) > 2e-4:
            raise ValueError("Washer patch area differs from source geometry")
    for film in meta["film_surface_ownership"]:
        if (
            abs(film["bridge_interface"]["area_mm2"] - 99.2538877015) > 2e-4
            or abs(film["rail_back"]["area_mm2"] - 99.5408306980) > 2e-4
        ):
            raise ValueError("Film face area differs from source geometry")
    connectivity = {int(k): v for k, v in meta["all_c3d10_connectivity"].items()}
    if set(connectivity) != materials["BRIDGE"] | materials["ADHESIVE"] or any(
        len(row) != 10 or not set(map(int, row)).issubset(nodes) for row in connectivity.values()
    ):
        raise ValueError("C3D10 connectivity/material coverage invalid")
    mesh_volumes = {int(k): float(v) for k, v in meta["tetrahedron_volumes_mm3"].items()}
    if set(mesh_volumes) != materials["BRIDGE"] | materials["ADHESIVE"] or any(
        v <= 0 or not math.isfinite(v) for v in mesh_volumes.values()
    ):
        raise ValueError("Missing, nonpositive or invalid tetrahedral integrated volumes")
    volume_errors = {}
    for name, ids in meta["material_element_ids"].items():
        cad = float(meta["material_region_volumes_mm3"][name])
        if cad <= 0:
            raise ValueError("Invalid CAD region volume")
        mesh = sum(mesh_volumes[int(e)] for e in ids)
        volume_errors[name] = mesh / cad - 1.0
        if abs(volume_errors[name]) > cfg["maximum_relative_material_mesh_volume_error"]:
            raise ValueError(f"Mesh-to-CAD material volume differs by >1% for {name}")
    for film in meta["film_surface_ownership"]:
        theta = math.radians(float(film["film_angle_deg"]))
        tangent = np.array([-math.sin(theta), math.cos(theta)])
        side = float(film["side"])
        outer = np.asarray([nodes[int(n)][:2] for n in film["rail_back"]["node_ids"]])
        inner = np.asarray([nodes[int(n)][:2] for n in film["bridge_interface"]["node_ids"]])
        if (
            not len(outer)
            or not len(inner)
            or np.max(np.abs(outer @ tangent - side * 6.0)) > 2e-6
            or np.max(np.abs(inner @ tangent - side * 6.1)) > 2e-6
        ):
            raise ValueError("Film face node positions do not preserve 0.1 mm physical gap")
    expected = {
        1: np.zeros(3),
        2: np.array([150 * 25.5 * math.sin(math.pi / 3), -150 * 25.5 * math.cos(math.pi / 3), 0]),
    }
    for step in (1, 2):
        forces = adapter_step_forces(meta, step)
        force, moment = force_and_moment(nodes, forces)
        if (
            np.linalg.norm(force - [0, 0, 150]) > 1e-6
            or np.linalg.norm(moment - expected[step]) > 1e-4
        ):
            raise ValueError(f"Step {step} traction does not preserve force and moment")
    return {
        "nodes": len(nodes),
        "tetrahedra": sum(map(len, materials.values())),
        "load_resultants": "independently verified",
        "material_mesh_to_cad_relative_volume_errors": volume_errors,
        "maximum_material_relative_volume_error": cfg[
            "maximum_relative_material_mesh_volume_error"
        ],
    }


def actual_worker(name, cfg):
    """Execute exactly one validated mesh and two CCX steps, without retries."""
    resource.setrlimit(resource.RLIMIT_CPU, (cfg["worker_cpu_limit_s"], cfg["worker_cpu_limit_s"]))
    from scripts.wo03_g80_bridge_adapter import build_case

    sizes = {"bridge_1p5mm": 1.5, "bridge_1p0mm": 1.0, "bridge_0p7mm": 0.7}
    folder = OUT / name
    meta = build_case(folder, sizes[name], cfg["maximum_nodes"], cfg["maximum_tetrahedra"])
    saved = json.loads((folder / "mesh-meta.json").read_text())
    # JSON integer keys naturally become strings; validation uses the persisted artifact.
    if not isinstance(meta, dict) or not isinstance(saved, dict):
        raise TypeError("Adapter did not return or persist metadata")
    input_check = validate_adapter_loads(saved, cfg)
    deck = (folder / "case.inp").read_text().upper()
    if deck.count("*STEP") != 2 or deck.count("*CLOAD,OP=NEW") != 2:
        raise ValueError("Adapter deck lacks two independent OP=NEW load steps")
    with (folder / "solver.log").open("w") as log:
        proc = subprocess.run(
            [cfg["ccx"], "-i", "case"],
            cwd=folder,
            stdout=log,
            stderr=subprocess.STDOUT,
            timeout=cfg["child_wall_limit_s"],
            check=False,
        )
    logtext = (folder / "solver.log").read_text(errors="replace")
    if proc.returncode or "*ERROR" in logtext.upper() or not (folder / "case.dat").exists():
        raise RuntimeError("CalculiX failed or output missing; see preserved solver.log")
    result = assess_adapter_output(folder)
    own = resource.getrusage(resource.RUSAGE_SELF)
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    output = {
        "name": name,
        "mesh_size_mm": sizes[name],
        "input_check": input_check,
        "result": result,
        "process_and_children_cpu_s": own.ru_utime + own.ru_stime + child.ru_utime + child.ru_stime,
    }
    (folder / "driver-result.json").write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output), flush=True)


def actual_packet(cfg):
    """Run three serial source-pinned levels after all no-solve checks pass."""
    evidence = check_preserved_preflight(cfg)
    lib = proc_lib()
    validate_monitor(lib)
    # The adapter's four independent synthetic tests perform no solver call.
    test_start = time.monotonic()
    usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    test = subprocess.run(
        [
            sys.executable,
            "-c",
            "import resource,runpy,sys; resource.setrlimit(resource.RLIMIT_CPU,(60,60)); sys.argv=['pytest','-q','tests/test_g80_bridge_adapter.py']; runpy.run_module('pytest',run_name='__main__')",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=cfg["child_wall_limit_s"],
        check=False,
    )
    usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    adapter_cpu = (usage_after.ru_utime + usage_after.ru_stime) - (
        usage_before.ru_utime + usage_before.ru_stime
    )
    adapter_check = {
        "passed": test.returncode == 0,
        "stdout": test.stdout,
        "stderr": test.stderr,
        "solver_invoked": False,
        "wall_s": time.monotonic() - test_start,
        "cpu_s": adapter_cpu,
    }
    evidence["known_prior_cpu_s"] += adapter_cpu
    if not adapter_check["passed"] or evidence["known_prior_cpu_s"] >= cfg["packet_cpu_limit_s"]:
        raise ValueError("Adapter synthetic output preflight failed or packet CPU exhausted")
    inputs = {
        CONFIG,
        Path(__file__).resolve(),
        ROOT / "scripts/wo03_g80_bridge_adapter.py",
        ROOT / "tests/test_g80_bridge_adapter.py",
        ROOT / cfg["source_preflight"],
        ROOT / cfg["bridge_step"],
        Path(cfg["ccx"]),
        ROOT / "src/analysis/fea.py",
        ROOT / "src/analysis/support_fea.py",
        ROOT / "scripts/wo03_root_contact_faces.py",
    }
    inputs.update(
        ROOT / f"build/wo03-g80-keeper-service-v1/{name}.step"
        for name in ("modified_mount", "washer_0", "washer_1", "washer_2")
    )
    before = {str(p): sha(p) for p in sorted(inputs)}
    evidence["adapter_no_solve_preflight"] = adapter_check
    evidence["source_sha256_before"] = before
    progress = {"status": "in_progress", "preflight": evidence, "completed": []}
    (OUT / "actual-progress.json").write_text(json.dumps(progress, indent=2) + "\n")
    for name in ("bridge_1p5mm", "bridge_1p0mm", "bridge_0p7mm"):
        process = subprocess.Popen(
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
            while process.poll() is None:
                if time.monotonic() - start > cfg["child_wall_limit_s"]:
                    raise TimeoutError("child wall cap")
                try:
                    for pid in group_pids(lib, process.pid):
                        try:
                            peak = max(peak, rss(lib, pid))
                        except ProcessLookupError:
                            if process.poll() is None and pid == process.pid:
                                raise
                except ProcessLookupError:
                    if process.poll() is None:
                        raise
                if peak > cfg["maximum_process_rss_bytes"]:
                    raise MemoryError("live per-process RSS cap")
                time.sleep(0.05)
            output = process.stdout.read()
            (OUT / f"{name}.log").write_text(output)
            if process.returncode:
                raise RuntimeError(f"{name} stopped exit {process.returncode}; preserved log")
            summary = json.loads(output.strip().splitlines()[-1])
            evidence["known_prior_cpu_s"] += summary["process_and_children_cpu_s"]
            if evidence["known_prior_cpu_s"] > cfg["packet_cpu_limit_s"]:
                raise TimeoutError("packet CPU cap")
            progress["completed"].append(
                {
                    "name": name,
                    "wall_s": time.monotonic() - start,
                    "observed_peak_rss_bytes": peak,
                    "result": summary,
                }
            )
            (OUT / "actual-progress.json").write_text(json.dumps(progress, indent=2) + "\n")
        except BaseException as exc:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            progress.update(
                status="stopped",
                error=f"{type(exc).__name__}: {exc}",
                source_sha256_after={str(p): sha(p) for p in sorted(inputs)},
            )
            (OUT / "actual-progress.json").write_text(json.dumps(progress, indent=2) + "\n")
            raise
    after = {str(p): sha(p) for p in sorted(inputs)}
    if before != after:
        raise ValueError("Actual packet inputs changed during execution")
    progress.update(status="complete_diagnostic_only", source_sha256_after=after)
    for step in (0, 1):
        values = [
            row["result"]["result"]["steps"][step]["effective_loaded_displacement_mm"]
            for row in progress["completed"]
        ]
        progress.setdefault("convergence", {})[f"step_{step+1}_loaded_displacement"] = (
            convergence_changes(values, 0.05)
        )
    progress["regional_stress_convergence"] = (
        "unavailable until verified CCX/Gmsh integration-point ordering"
    )
    (OUT / "actual-record.json").write_text(json.dumps(progress, indent=2) + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--worker",
        choices=[
            "axial_fixture",
            "shear_fixture",
            "geometry_preflight",
            "bridge_1p5mm",
            "bridge_1p0mm",
            "bridge_0p7mm",
        ],
    )
    p.add_argument("--map-geometry", action="store_true")
    p.add_argument("--actual-packet", action="store_true")
    a = p.parse_args()
    cfg = yaml.safe_load(CONFIG.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    if a.worker and a.worker.startswith("bridge_"):
        actual_worker(a.worker, cfg)
    elif a.worker:
        worker(a.worker, cfg)
    elif a.actual_packet:
        actual_packet(cfg)
    else:
        packet(cfg, geometry_only=a.map_geometry)


if __name__ == "__main__":
    main()
