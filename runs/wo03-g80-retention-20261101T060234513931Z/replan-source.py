"""One nominal-only BRep retention study; not a regenerated vehicle model."""

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

import yaml

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
from src.vehicle.schema import load_vehicle

CONFIG = Path("configs/studies/wo03-g80-retention-geometry.yaml")
OUT = Path("build/wo03-g80-retention-geometry-replan-v1")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight():
    cfg = yaml.safe_load(CONFIG.read_text())
    v = load_vehicle(cfg["source_candidate"])
    identity = hashlib.sha256(v.model_dump_json(by_alias=True).encode()).hexdigest()
    if identity != cfg["source_identity"] or len(v.parts) != 52:
        raise ValueError("Frozen candidate identity mismatch")
    manifest = json.loads(Path(cfg["source_manifest"]).read_text())
    if manifest["identity"]["resolved_spec_sha256"] != identity:
        raise ValueError("Frozen manifest identity mismatch")
    fab = yaml.safe_load(Path(cfg["fabrication_study"]).read_text())
    hw = yaml.safe_load(Path(cfg["hardware_study"]).read_text())
    if fab["source_identity"] != identity or hw["source_identity"] != identity:
        raise ValueError("Study source mismatch")
    if (
        hw["candidate_parts"]["washer"]["part_number"] != "HPW-M3-V2-A2"
        or hw["candidate_parts"]["screw"]["part_number"] != "SSCF-M3-35-A2"
        or hw["candidate_parts"]["nut"]["part_number"] != "HPN-M3-A2"
    ):
        raise ValueError("Hardware identity mismatch")
    if hw["candidate_parts"]["washer"]["outer_diameter_tolerance_mm"] is not None:
        raise ValueError("Washer tolerance assumptions changed; replan")
    if (cfg["relief_width_mm"], cfg["washer_outer_mm"], cfg["bolt_length_mm"]) != (9.6, 9.0, 35.0):
        raise ValueError("Unexpected nominal inputs")
    # All coordinates in local mount mm. Full hardware envelopes are checked
    # where they pass through the relief, bridge and cap, not assumed relieved
    # for their entire axial length.
    inner, outer = cfg["relief_start_radius_mm"], cfg["relief_end_radius_mm"]
    axis, half = 25.5, cfg["relief_width_mm"] / 2
    washer_r = cfg["washer_outer_mm"] / 2
    nut_r = cfg["nut_across_flats_mm"] / math.sqrt(3)
    screw_r = cfg["bolt_shank_diameter_mm"] / 2
    bridge_front = fab["bridge_start_mm"]
    washer_front = bridge_front - cfg["washer_thickness_mm"]
    nut_front = washer_front - cfg["nut_height_mm"]
    cap_end = hw["nominal_geometry_basis"]["cap_aft_face_local_station_mm"]
    screw_front = cap_end - cfg["bolt_length_mm"]
    extents = {
        "washer": {
            "radial": [axis - washer_r, axis + washer_r],
            "half_width": washer_r,
            "axial": [washer_front, bridge_front],
        },
        "nut": {
            "radial": [axis - nut_r, axis + nut_r],
            "half_width": nut_r,
            "axial": [nut_front, washer_front],
        },
        "screw_through_ring": {
            "radial": [axis - screw_r, axis + screw_r],
            "half_width": screw_r,
            "axial": [167.0, 170.0],
        },
    }
    if (inner, outer, cfg["nominal_inner_ligament_mm"]) != (20.7, 34.5, 4.9):
        raise ValueError("Unexpected replan radius or ligament")
    for name, x in extents.items():
        if (
            x["radial"][0] < inner
            or x["radial"][1] > outer
            or x["half_width"] > half
            or x["axial"][0] < 166.1
            or x["axial"][1] > 170.1
        ):
            raise ValueError(f"Nominal relief does not contain {name} extent")
    if not (
        screw_front
        <= nut_front
        < washer_front
        < bridge_front
        < fab["retainer_block_start_mm"]
        < fab["retainer_block_end_mm"]
        < cap_end
    ):
        raise ValueError("Axial stack does not match source cap and guide")
    extents["screw_full"] = {
        "radial": [axis - screw_r, axis + screw_r],
        "axial": [screw_front, cap_end],
        "head_axial": [cap_end, cap_end + cfg["bolt_head_height_mm"]],
        "head_radius": cfg["bolt_head_diameter_mm"] / 2,
    }
    if any(
        abs(a - b) > 1e-8
        for a, b in [
            (screw_front, 162),
            (nut_front, 166.8),
            (washer_front, 169.2),
            (bridge_front, 170.1),
            (cap_end, 197),
        ]
    ):
        raise ValueError("Reconstruction constants do not match nominal stack")
    if not (
        cfg["bolt_shank_diameter_mm"] < cfg["washer_inner_mm"]
        and cfg["bolt_shank_diameter_mm"] < 3.4
        and cfg["bolt_head_diameter_mm"] > 3.4
    ):
        raise ValueError("Nominal shaft, bore or head relationship fails")
    cfg["nominal_preflight_extents_mm"] = extents
    cfg["preflight_note"] = (
        "Nominal extents only; washer OD tolerance, screw length tolerance, tolerances and keeper remain unresolved."
    )
    ids = [
        "motor_mount",
        "motor",
        "motor_liner",
        "fin_set",
        "retention",
        "aft_retainer",
        "aft_shell",
        "aft_thrust_pads",
    ]
    parts = {p.id: p for p in v.parts}
    if any(
        not Path(f"build/wo03-g80-integrated-candidate-v1/parts/{i}.step").is_file() for i in ids
    ):
        raise ValueError("Missing frozen source solids")
    if parts["motor_mount"].position_m != 1.01 or parts["aft_retainer"].position_m != 1.203:
        raise ValueError("Unexpected source positions")
    return cfg, fab, hw, v, ids


def child():
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    import cadquery as cq
    from OCP.OSD import OSD_Parallel, OSD_ThreadPool

    started = time.monotonic()
    cfg, _fab, _hw, v, ids = preflight()
    OSD_Parallel.SetUseOcctThreads_s(True)
    pool = OSD_ThreadPool.DefaultPool_s()
    pool.Init(1)
    if pool.NbThreads() != 1:
        raise RuntimeError("OCCT pool not one")
    paths = [
        CONFIG,
        Path(__file__),
        Path(cfg["source_candidate"]),
        Path(cfg["source_manifest"]),
        Path(cfg["fabrication_study"]),
        Path(cfg["hardware_study"]),
    ]
    paths += [Path(f"build/wo03-g80-integrated-candidate-v1/parts/{i}.step") for i in ids]
    before = {str(p): sha(p) for p in paths}
    OUT.mkdir(parents=True, exist_ok=True)

    def checkpoint(status, **values):
        (OUT / "progress.json").write_text(
            json.dumps({"status": status, **values}, indent=2) + "\n"
        )

    def box(x, y, z, z0=0):
        return (
            cq.Workplane("XY")
            .box(x, y, z, centered=(True, True, False))
            .val()
            .translate((0, 0, z0))
        )

    def rotate(s, a):
        return s.rotate((0, 0, 0), (0, 0, 1), a)

    def cylinder(r, z0, h, x=0, y=0):
        return cq.Solid.makeCylinder(r, h, cq.Vector(x, y, z0))

    def annulus(ro, ri, z0, h):
        return cylinder(ro, z0, h).cut(cylinder(ri, z0 - 0.1, h + 0.2))

    a = box(2, 2, 2)
    overlap = a.intersect(box(2, 2, 2).translate((1, 0, 0))).Volume()
    gap = a.intersect(box(2, 2, 2).translate((2.1, 0, 0))).Volume()
    if abs(overlap - 4) > 1e-7 or gap > 1e-7:
        raise ValueError("Known overlap/gap fixture failed")
    checkpoint("fixture_passed", overlap_mm3=overlap, gap_mm3=gap)
    part = {p.id: p for p in v.parts}
    shapes = {}
    for name in ids:
        q = cq.importers.importStep(
            str(Path("build/wo03-g80-integrated-candidate-v1/parts") / (name + ".step"))
        ).val()
        if not q.isValid() or q.Volume() <= 0:
            raise ValueError(f"Invalid source shape {name}")
        expected = part[name].cad_mass.volume_m3
        if abs(q.Volume() * 1e-9 - expected) > max(1e-11, expected * 1e-5):
            raise ValueError(f"Source shape volume mismatch {name}")
        shapes[name] = q.translate(
            (
                part[name].lateral_offset_m[0] * 1000,
                -part[name].lateral_offset_m[1] * 1000,
                (part[name].position_m - 1.01) * 1000,
            )
        )
    mount = shapes["motor_mount"]
    newmount = mount
    # Remove the old rear block regions, then restore non-load-bearing guide blocks without nut pockets.
    for angle in [60, 180, 300]:
        cutter = rotate(box(12.02, 12.02, 20.02, 169.99).translate((25.5, 0, 0)), angle)
        newmount = newmount.cut(cutter)
    blocks = []
    for angle in [60, 180, 300]:
        b = (
            box(12, 12, 17.8, 172.2)
            .translate((25.5, 0, 0))
            .cut(cylinder(1.7, 172.1, 18.1, 25.5, 0))
        )
        b = b.intersect(cylinder(32.2, 172, 19))
        b = rotate(b, angle)
        blocks.append(b)
    # Existing ring relief is radial-open in the last 3 mm ring, widened for the 9 mm washer.
    for angle in [60, 180, 300]:
        radial_start, radial_end = cfg["relief_start_radius_mm"], cfg["relief_end_radius_mm"]
        cutter = rotate(
            box(radial_end - radial_start, cfg["relief_width_mm"], 4, 166.1).translate(
                ((radial_start + radial_end) / 2, 0, 0)
            ),
            angle,
        )
        newmount = newmount.cut(cutter)
    # These are separately constructed guides; no structural union is credited.
    bridge = annulus(32.2, 15.8, 170.1, 2.0)
    for angle in [0, 120, 240]:
        notch = rotate(box(14, 12.2, 2.2, 170.0).translate((31.9, 0, 0)), angle)
        bridge = bridge.cut(notch)
    for angle in [60, 180, 300]:
        x = 25.5 * math.cos(math.radians(angle))
        y = 25.5 * math.sin(math.radians(angle))
        bridge = bridge.cut(cylinder(1.7, 170, 2.2, x, y))
    for angle in [0, 120, 240]:
        for sign in [-1, 1]:
            tab = (
                box(7, 2, 15, 172.1)
                .translate((28.5, sign * 7.1, 0))
                .intersect(cylinder(32.2, 172, 15.2))
            )
            bridge = bridge.fuse(rotate(tab, angle))
    bridge = bridge.clean()
    if not bridge.isValid() or len(bridge.Solids()) != 1 or bridge.Volume() <= 0:
        checkpoint("stopped_invalid_bridge", valid=bridge.isValid(), solids=len(bridge.Solids()))
        raise ValueError("Bridge not one valid connected solid")
    hardware = []
    washers = []
    nuts = []
    for angle in [60, 180, 300]:
        x = 25.5 * math.cos(math.radians(angle))
        y = 25.5 * math.sin(math.radians(angle))
        washer = annulus(4.5, 1.6, 169.2, 0.9).translate((x, y, 0))
        washers.append(washer)
        nut = (
            cq.Workplane("XY")
            .polygon(6, 5.5 / math.cos(math.pi / 6))
            .extrude(2.4)
            .val()
            .translate((x, y, 166.8))
            .cut(cylinder(1.5, 166.7, 2.6, x, y))
        )
        nuts.append(nut)
        screw = cylinder(1.5, 162, 35, x, y).fuse(cylinder(2.75, 197, 3, x, y))
        hardware.append(screw)
    components = {
        "modified_mount": newmount,
        "bridge": bridge,
        **{f"guide_{i}": b for i, b in enumerate(blocks)},
        **{f"washer_{i}": b for i, b in enumerate(washers)},
        **{f"nut_{i}": b for i, b in enumerate(nuts)},
        **{f"screw_{i}": b for i, b in enumerate(hardware)},
    }
    for name, s in components.items():
        if not s.isValid() or s.Volume() <= 0:
            raise ValueError(f"Invalid candidate shape {name}")
    # Preserve original motors, fins, liner, cap and shell; report every intersection.
    references = {k: s for k, s in shapes.items() if k != "motor_mount"}
    obstacles = {**references, **components}
    results = []
    labels = list(obstacles)
    for i, x in enumerate(labels):
        for y in labels[i + 1 :]:
            if x in references and y in references:
                continue
            sa, sb = obstacles[x], obstacles[y]
            ba, bb = sa.BoundingBox(), sb.BoundingBox()
            if any(
                getattr(ba, axis + "max") <= getattr(bb, axis + "min") + 1e-6
                or getattr(bb, axis + "max") <= getattr(ba, axis + "min") + 1e-6
                for axis in "xyz"
            ):
                continue
            vol = sa.intersect(sb).Volume()
            if vol > 0.05:
                results.append({"a": x, "b": y, "intersection_mm3": vol})
    if results:
        checkpoint("stopped_positive_intersections", intersections=results)
        raise ValueError("Positive-volume intersections require a new design decision; stop")
    # Washer bearing uses intersection with a 0.001 mm bridge surface probe; this is a nominal numerical area.
    seats = []
    for w in washers:
        probe = w.translate((0, 0, 0.001)).intersect(bridge).Volume() / 0.001
        seats.append(probe)
    # Straight radial installation path, outward through the installed shell, sampled at 1 mm.
    corridors = []
    for idx, (angle, nut, washer) in enumerate(zip([60, 180, 300], nuts, washers, strict=True)):
        dx = math.cos(math.radians(angle))
        dy = math.sin(math.radians(angle))
        blockers = set()
        for step in range(1, 16):
            moved = cq.Compound.makeCompound([nut, washer]).translate((dx * step, dy * step, 0))
            for name in [
                "modified_mount",
                "bridge",
                "aft_shell",
                "fin_set",
                "retention",
                "motor_liner",
                "motor",
            ]:
                if moved.intersect(obstacles[name]).Volume() > 0.05:
                    blockers.add(name)
        corridors.append(
            {
                "axis_deg": angle,
                "direction": "radially outward, installed assembly, 1 mm samples",
                "blockers": sorted(blockers),
                "keeper_modeled": False,
            }
        )
    density_plywood = 715
    density_g11 = 1850
    masses = {
        "source_mount_g": mount.Volume() * 1e-6 * density_plywood,
        "modified_mount_and_guides_g": (newmount.Volume() + sum(s.Volume() for s in blocks))
        * 1e-6
        * density_plywood,
        "bridge_g": bridge.Volume() * 1e-6 * density_g11,
        "three_stacks_supplier_nominal_g": 8.52,
        "hardware_increment_g": None,
        "keeper_mass_g": None,
    }
    outpaths = {}
    for name, shape in components.items():
        p = OUT / (name + ".step")
        cq.exporters.export(shape, str(p))
        outpaths[name] = str(p)
    cq.exporters.export(
        cq.Compound.makeCompound(list(obstacles.values())), str(OUT / "study-assembly.step")
    )
    after = {str(p): sha(p) for p in paths}
    if before != after:
        raise ValueError("Input changed during attempt")
    record = {
        "status": "nominal_study_unaccepted",
        "source_identity": cfg["source_identity"],
        "source_hashes_before": before,
        "source_hashes_after": after,
        "fixture": {"overlap_mm3": overlap, "gap_mm3": gap},
        "candidate_valid": {k: s.isValid() for k, s in components.items()},
        "intersections": results,
        "washer_seat_areas_mm2": seats,
        "radial_nut_washer_access": corridors,
        "masses": masses,
        "dimensions": cfg,
        "references": ids,
        "output_paths": outpaths,
        "full_vehicle_validated": False,
        "capture_accepted": False,
        "reason": "nominal geometry only; unverified keeper, washer OD tolerance, assembly, load and thermal conditions",
        "elapsed_s": time.monotonic() - started,
        "cpu_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime
        + resource.getrusage(resource.RUSAGE_SELF).ru_stime,
    }
    (OUT / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    checkpoint("complete", identity=cfg["source_identity"])
    print(
        json.dumps(
            {
                "intersections": results,
                "seats_mm2": seats,
                "access": corridors,
                "masses": masses,
                "elapsed_s": record["elapsed_s"],
                "cpu_s": record["cpu_s"],
            }
        )
    )


def main():
    if sys.argv[1:] == ["--child"]:
        child()
        return
    cfg, _, _, v, ids = preflight()
    print(
        f"Preflight passed: {len(v.parts)} source parts, {len(ids)} source STEP references; one child",
        flush=True,
    )
    OUT.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            k: "1"
            for k in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        }
    )
    paths = [
        CONFIG,
        Path(__file__),
        Path(cfg["source_candidate"]),
        Path(cfg["source_manifest"]),
        Path(cfg["fabrication_study"]),
        Path(cfg["hardware_study"]),
    ]
    paths += [Path(f"build/wo03-g80-integrated-candidate-v1/parts/{i}.step") for i in ids]
    hashes = {str(p): sha(p) for p in paths}
    (OUT / "preflight.json").write_text(
        json.dumps(
            {
                "source_sha256_before": hashes,
                "nominal_extents": cfg["nominal_preflight_extents_mm"],
                "minimum_tolerance_pass": None,
                "ligament_mm": 4.9,
                "initial_attempt_cpu_s": None,
            },
            indent=2,
        )
        + "\n"
    )
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.monotonic()
    result = {"returncode": None, "timeout": False}
    try:
        r = subprocess.run(
            [sys.executable, __file__, "--child"], env=env, timeout=cfg["wall_cap_s"], check=False
        )
        result["returncode"] = r.returncode
    except subprocess.TimeoutExpired:
        result["timeout"] = True
    finally:
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        result.update(
            {
                "child_user_cpu_s": after.ru_utime - before.ru_utime,
                "child_system_cpu_s": after.ru_stime - before.ru_stime,
                "wall_s": time.monotonic() - started,
                "source_sha256_before": hashes,
                "source_sha256_after": {str(p): sha(p) for p in paths},
                "prior_attempt_cpu_s": None,
                "aggregate_packet_cpu_s": None,
            }
        )
        (OUT / "execution-status.json").write_text(json.dumps(result, indent=2) + "\n")
    if result["timeout"] or result["returncode"] != 0:
        raise SystemExit("Stopped after authorized replan; no further retry")


if __name__ == "__main__":
    main()
