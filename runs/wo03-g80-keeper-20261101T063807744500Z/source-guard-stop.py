"""One source-identical nominal keeper service continuation; no vehicle adoption."""

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

CONFIG = Path("configs/studies/wo03-g80-keeper-geometry.yaml")
OUT = Path("build/wo03-g80-keeper-service-v1")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def preflight():
    cfg = yaml.safe_load(CONFIG.read_text())
    plan = yaml.safe_load(Path(cfg["keeper_plan"]).read_text())
    m2 = yaml.safe_load(Path(cfg["m2_hardware"]).read_text())
    m3 = yaml.safe_load(Path(cfg["m3_hardware"]).read_text())
    v = load_vehicle(cfg["source_candidate"])
    identity = hashlib.sha256(v.model_dump_json(by_alias=True).encode()).hexdigest()
    if (
        identity != cfg["source_identity"]
        or identity != plan["source_candidate_identity"]
        or len(v.parts) != 52
    ):
        raise ValueError("Source candidate identity mismatch")
    prev = Path(cfg["source_replan"])
    previous = json.loads((prev / "record.json").read_text())
    if previous["source_identity"] != identity or previous["intersections"]:
        raise ValueError("Source replan missing or conflicted")
    if (
        m2["candidate_screw"]["part_number"] != "SSCF-M2-10-A2-BL"
        or m2["candidate_nut"]["part_number"] != "HPN-M2-A2"
    ):
        raise ValueError("Unexpected M2 hardware")
    if (
        m3["candidate_parts"]["washer"]["outer_diameter_tolerance_mm"] is not None
        or m2["candidate_washer"]["thickness_mm"] is not None
    ):
        raise ValueError("Hardware uncertainty changed; replan")
    k = plan["keeper"]
    c = plan["closure"]
    # Nominal closed stack, all lengths in local mount coordinates.
    axial = {
        "keeper": [k["forward_station"], k["aft_station"]],
        "pocket_floor": k["nut_hex_pocket_floor_station"],
        "hex_pocket": [
            k["nut_hex_pocket_floor_station"],
            k["aft_station"] - k["washer_counterbore_depth_from_aft"],
        ],
        "washer_pocket": [
            k["aft_station"] - k["washer_counterbore_depth_from_aft"],
            k["aft_station"],
        ],
        "bridge": [c["bridge_forward_station"], c["bridge_forward_station"] + 2],
        "washer": [169.2, 170.1],
        "nut": [166.8, 169.2],
        "m3_screw": [162.0, 197.0],
        "m2_shank": [166.0, 176.0],
        "m2_head": [164.0, 166.0],
        "m2_nut_without_washer": [172.1, 173.7],
    }
    if (
        axial["keeper"] != [166.0, 170.0]
        or abs(axial["washer_pocket"][0] - 168.9) > 1e-8
        or axial["hex_pocket"][0] != 166.5
        or axial["bridge"] != [170.1, 172.1]
    ):
        raise ValueError("Unexpected keeper/bridge profile")
    if not (
        axial["washer"][0] >= axial["washer_pocket"][0]
        and axial["washer"][1] == axial["bridge"][0]
        and axial["nut"][0] >= axial["hex_pocket"][0]
        and axial["nut"][1] <= axial["washer"][0]
    ):
        raise ValueError("M3 axial pocket containment failure")
    if not (
        k["washer_counterbore_diameter_nominal"] > 9
        and k["nut_hex_pocket_across_flats_nominal"] > 5.5
        and k["screw_tip_clearance_bore_diameter_nominal"] > 3
        and c["stowage_hole_diameter_nominal"] > 2
        and c["standoff_outer_diameter_nominal"] > c["standoff_bore_nominal"]
    ):
        raise ValueError("Nominal radial clearance profile failure")
    if (
        abs(k["nut_hex_pocket_floor_station"] - k["forward_station"] - 0.5) > 1e-9
        or abs(c["bridge_forward_station"] - k["aft_station"] - 0.1) > 1e-9
    ):
        raise ValueError("Floor or gap mismatch")
    if not (
        axial["m2_shank"][0] == k["forward_station"]
        and abs(
            axial["m2_shank"][1]
            - axial["m2_nut_without_washer"][1]
            - cfg["nominal_m2_protrusion_mm"]
        )
        < 1e-8
    ):
        raise ValueError("M2 nominal hypothetical stack does not fit")
    # Pad is integral to keeper, outboard of its bore and clear of the nearest
    # M3 pocket at nominal axes. Rail notch clearance is checked by BRep later.
    pad_r = cfg["integral_g11_pad_outer_mm"] / 2
    if (cfg["m2_washers"], cfg["integral_g11_pad_bore_mm"], cfg["integral_g11_pad_height_mm"]) != (
        "none",
        2.2,
        0.1,
    ):
        raise ValueError("Unexpected primary closure inputs")
    center_distance = math.sqrt(19**2 + 25.5**2 - 2 * 19 * 25.5 * math.cos(math.radians(30)))
    if (
        19 - pad_r <= k["inner_radius"]
        or 19 + pad_r >= k["outer_radius"]
        or center_distance <= pad_r + k["washer_counterbore_diameter_nominal"] / 2
    ):
        raise ValueError("Nominal pad conflicts with ring boundaries or M3 pocket")
    # Full nominal XY envelopes for the M3 pocket, M2 head/nut and shanks.
    m3_bore_r = 1.8
    m2_head_r = m2["candidate_screw"]["head_diameter_mm"] / 2
    m2_nut_r = m2["candidate_nut"]["across_flats_mm"] / math.sqrt(3)
    if not (
        25.5 - k["washer_counterbore_diameter_nominal"] / 2 > k["inner_radius"]
        and 25.5 + k["washer_counterbore_diameter_nominal"] / 2 < k["outer_radius"]
        and 19 - m2_head_r > k["inner_radius"]
        and 19 + m2_head_r < k["outer_radius"]
        and 19 - m2_nut_r > k["inner_radius"]
        and 19 + m2_nut_r < k["outer_radius"]
        and 3.0 < 2 * m3_bore_r
        and 2.0 < c["stowage_hole_diameter_nominal"]
        and center_distance > m2_nut_r + k["washer_counterbore_diameter_nominal"] / 2
    ):
        raise ValueError("Nominal fastener envelopes cross keeper bounds or adjacent pocket")
    axial["m3_washer_radial_mm"] = [21.0, 30.0]
    axial["m3_pocket_radial_mm"] = [20.7, 30.3]
    axial["m2_head_radial_mm"] = [19 - m2_head_r, 19 + m2_head_r]
    axial["m2_nut_bounding_radial_mm"] = [19 - m2_nut_r, 19 + m2_nut_r]
    axial["integral_pad"] = [170.0, 170.1]
    axial["m2_protrusion_nominal_mm"] = 2.3
    inputs = [
        CONFIG,
        Path(__file__),
        Path(cfg["source_candidate"]),
        Path(cfg["keeper_plan"]),
        Path(cfg["m3_hardware"]),
        Path(cfg["m2_hardware"]),
        prev / "record.json",
        prev / "modified_mount.step",
        prev / "bridge.step",
    ]
    inputs += [
        prev / f"{name}_{i}.step" for name in ("guide", "nut", "washer", "screw") for i in range(3)
    ]
    inputs += [
        Path("build/wo03-g80-integrated-candidate-v1/parts") / (p.id + ".step") for p in v.parts
    ]
    missing = [str(p) for p in inputs if not p.is_file()]
    if missing:
        raise ValueError(f"Missing required sources: {missing}")
    return cfg, plan, m2, m3, v, inputs, axial


def child():
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    import cadquery as cq
    from OCP.OSD import OSD_Parallel, OSD_ThreadPool

    cfg, _plan, _m2, _m3, v, _, _axial = preflight()
    OSD_Parallel.SetUseOcctThreads_s(True)
    pool = OSD_ThreadPool.DefaultPool_s()
    pool.Init(1)
    if pool.NbThreads() != 1:
        raise RuntimeError("OCCT pool did not select one worker")
    OUT.mkdir(parents=True, exist_ok=True)

    def save(stage, **data):
        (OUT / "progress.json").write_text(json.dumps({"stage": stage, **data}, indent=2) + "\n")

    def cylinder(r, z, h, x=0.0, y=0.0):
        return cq.Solid.makeCylinder(r, h, cq.Vector(x, y, z))

    def box(x, y, z, z0):
        return (
            cq.Workplane("XY")
            .box(x, y, z, centered=(True, True, False))
            .val()
            .translate((0, 0, z0))
        )

    def rot(s, a):
        return s.rotate((0, 0, 0), (0, 0, 1), a)

    def annulus(ro, ri, z, h):
        return cylinder(ro, z, h).cut(cylinder(ri, z - 0.01, h + 0.02))

    def hexprism(af, z, h, x=0.0, y=0.0):
        return (
            cq.Workplane("XY")
            .polygon(6, af / math.cos(math.pi / 6))
            .extrude(h)
            .val()
            .translate((x, y, z))
        )

    def point(r, a):
        return r * math.cos(math.radians(a)), r * math.sin(math.radians(a))

    def pocket(s, x, y):
        s = s.cut(cylinder(4.8, 168.9, 1.2, x, y))
        s = s.cut(hexprism(5.7, 166.5, 2.41, x, y))
        s = s.cut(cylinder(1.8, 165.9, 4.2, x, y))
        corner = 5.7 / math.sqrt(3)
        for a in range(0, 360, 60):
            cx = x + corner * math.cos(math.radians(a))
            cy = y + corner * math.sin(math.radians(a))
            s = s.cut(cylinder(0.5, 166.5, 2.41, cx, cy))
        return s

    # Flat known-case: verify blind pocket leaves material in the forward wall,
    # known bore is clear, and known washer probe recovers the expected area.
    fixture = pocket(box(20, 20, 4, 166), 0, 0)
    wall = fixture.intersect(cylinder(4, 166, 0.5)).Volume()
    bore = fixture.intersect(cylinder(1.79, 165.9, 4.2)).Volume()
    plate = annulus(10, 1.7, 170.1, 2)
    w = annulus(4.5, 1.6, 169.2, 0.9)
    bearing = w.translate((0, 0, 0.001)).intersect(plate).Volume() / 0.001
    expected = math.pi * (4.5**2 - 1.7**2)
    if not fixture.isValid() or wall <= 1 or bore > 1e-6 or abs(bearing - expected) > 1e-3:
        save(
            "fixture_failed",
            wall_mm3=wall,
            bore_overlap_mm3=bore,
            bearing_mm2=bearing,
            expected_mm2=expected,
        )
        raise ValueError("Blind pocket/wall/bearing fixture failed")
    save("fixture_passed", wall_mm3=wall, bore_overlap_mm3=bore, bearing_mm2=bearing)
    (OUT / "fixture.json").write_text(
        json.dumps(
            {
                "wall_mm3": wall,
                "bore_overlap_mm3": bore,
                "bearing_mm2": bearing,
                "expected_bearing_mm2": expected,
            },
            indent=2,
        )
        + "\n"
    )
    (OUT / "fixture.json").write_text(
        json.dumps(
            {
                "wall_mm3": wall,
                "bore_overlap_mm3": bore,
                "bearing_mm2": bearing,
                "expected_bearing_mm2": expected,
            },
            indent=2,
        )
        + "\n"
    )
    prev = Path(cfg["source_replan"])

    def step(name):
        s = cq.importers.importStep(str(name)).val()
        if not s.isValid() or s.Volume() <= 0:
            raise ValueError(f"Invalid STEP source: {name}")
        return s

    old = step(prev / "modified_mount.step")
    oldbridge = step(prev / "bridge.step")
    guides = [step(prev / f"guide_{i}.step") for i in range(3)]
    # Remove the actual old ring-band contribution while retaining any material
    # within the exact source rail envelopes. Do not assign shared overlap twice.
    ring_band = annulus(32.2, 15.8, 167, 3)
    rail_envelopes = []
    for angle in (0, 120, 240):
        rail_envelopes.append(rot(box(7, 12, 190, 0).translate((28.5, 0, 0)), angle))
    removal = old.intersect(ring_band)
    for rail in rail_envelopes:
        removal = removal.cut(rail)
    removed_volume = removal.Volume()
    if removed_volume <= 0:
        raise ValueError("No source rear-ring contribution identified")
    mount = old.cut(removal)
    removed_check = old.Volume() - mount.Volume()
    if abs(removed_check - removed_volume) > 1e-4:
        raise ValueError("Old-ring removal volume mismatch")
    keeper = annulus(32.2, 15.8, 166, 4)
    for angle in (0, 120, 240):
        keeper = keeper.cut(rot(box(14, 12.2, 4.2, 165.9).translate((31.9, 0, 0)), angle))
    for angle in (60, 180, 300):
        x, y = point(25.5, angle)
        keeper = pocket(keeper, x, y)
    bridge = oldbridge
    m2parts = {}
    for i, angle in enumerate((30, 150, 270)):
        x, y = point(19, angle)
        keeper = keeper.cut(cylinder(1.1, 165.9, 4.2, x, y))
        bridge = bridge.cut(cylinder(1.1, 170.0, 2.2, x, y))
        pad = annulus(2, 1.1, 170, 0.1).translate((x, y, 0))
        keeper = keeper.fuse(pad)
        screw = cylinder(1, 166, 10, x, y).fuse(cylinder(1.9, 164, 2, x, y))
        nut = hexprism(4, 172.1, 1.6, x, y).cut(cylinder(1, 172, 1.8, x, y))
        m2parts[f"m2_screw_{i}"] = screw
        m2parts[f"m2_nut_{i}"] = nut
    keeper = keeper.clean()
    bridge = bridge.clean()
    if (
        not keeper.isValid()
        or len(keeper.Solids()) != 1
        or not bridge.isValid()
        or len(bridge.Solids()) != 1
        or not mount.isValid()
    ):
        save(
            "stopped_invalid_keeper_mount_or_bridge",
            keeper_solids=len(keeper.Solids()),
            bridge_solids=len(bridge.Solids()),
        )
        raise ValueError("Invalid candidate")
    m3 = {
        f"{kind}_{i}": step(prev / f"{kind}_{i}.step")
        for kind in ("nut", "washer", "screw")
        for i in range(3)
    }
    candidates = {
        "modified_mount": mount,
        "keeper": keeper,
        "bridge": bridge,
        **{f"guide_{i}": s for i, s in enumerate(guides)},
        **m2parts,
        **m3,
    }
    if any(not s.isValid() or s.Volume() <= 0 for s in candidates.values()):
        raise ValueError("Invalid candidate component")
    references = {}
    for p in v.parts:
        if p.id in {"motor_mount", "retention_hardware"} or p.cad.role in (
            "soft_stowage",
            "distributed_budget",
        ):
            continue
        s = step(Path("build/wo03-g80-integrated-candidate-v1/parts") / (p.id + ".step"))
        if abs(s.Volume() * 1e-9 - p.cad_mass.volume_m3) > max(1e-11, p.cad_mass.volume_m3 * 1e-5):
            raise ValueError(f"Source volume mismatch {p.id}")
        references[p.id] = s.translate(
            (
                p.lateral_offset_m[0] * 1000,
                -p.lateral_offset_m[1] * 1000,
                (p.position_m - 1.01) * 1000,
            )
        )
    solids = {**references, **candidates}
    names = list(solids)
    overlaps = []
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            if a in references and b in references:
                continue
            x, y = solids[a], solids[b]
            bx, by = x.BoundingBox(), y.BoundingBox()
            if any(
                getattr(bx, q + "max") <= getattr(by, q + "min") + 1e-6
                or getattr(by, q + "max") <= getattr(bx, q + "min") + 1e-6
                for q in "xyz"
            ):
                continue
            volume = x.intersect(y).Volume()
            if volume > 0.05:
                overlaps.append({"a": a, "b": b, "intersection_mm3": volume})
    if overlaps:
        save(
            "stopped_positive_intersections",
            intersections=overlaps,
            removed_old_ring_contribution_mm3=removed_volume,
        )
        raise ValueError("Unexplained positive overlap: stop")
    seats = []
    retention = []
    for i, angle in enumerate((60, 180, 300)):
        x, y = point(25.5, angle)
        washer = m3[f"washer_{i}"]
        nut = m3[f"nut_{i}"]
        seats.append(washer.translate((0, 0, 0.001)).intersect(bridge).Volume() / 0.001)
        rotate_overlap = nut.rotate((x, y, 0), (x, y, 1), 5).intersect(keeper).Volume()
        dropout_overlap = nut.translate((0, 0, -0.5)).intersect(keeper).Volume()
        rotation_plus_15 = nut.rotate((x, y, 0), (x, y, 1), 15).intersect(keeper).Volume()
        rotation_minus_15 = nut.rotate((x, y, 0), (x, y, 1), -15).intersect(keeper).Volume()
        retention.append(
            {
                "axis_deg": angle,
                "rotation_5deg_overlap_mm3": rotate_overlap,
                "rotation_plus_15deg_overlap_mm3": rotation_plus_15,
                "rotation_minus_15deg_overlap_mm3": rotation_minus_15,
                "forward_dropout_0p5mm_overlap_mm3": dropout_overlap,
            }
        )
    prior = json.loads(Path("build/wo03-g80-keeper-geometry-v1/progress.json").read_text())
    for observed, recorded in zip(retention, prior["nut_constraints"], strict=True):
        if (
            abs(observed["rotation_5deg_overlap_mm3"] - recorded["rotation_5deg_overlap_mm3"])
            > 1e-7
            or abs(
                observed["forward_dropout_0p5mm_overlap_mm3"]
                - recorded["forward_dropout_0p5mm_overlap_mm3"]
            )
            > 1e-7
        ):
            raise ValueError("Reconstructed 5-degree or dropout result differs from prior")
    (OUT / "nut-observations.json").write_text(
        json.dumps(
            {"original_5_degree_gate_mm3": 0.05, "seats_mm2": seats, "observations": retention},
            indent=2,
        )
        + "\n"
    )
    if min(seats) <= 0 or any(
        r["rotation_plus_15deg_overlap_mm3"] <= 0.05
        or r["rotation_minus_15deg_overlap_mm3"] <= 0.05
        or r["forward_dropout_0p5mm_overlap_mm3"] <= 0.05
        for r in retention
    ):
        save("stopped_missing_seat_or_retention", seats=seats, nut_constraints=retention)
        raise ValueError("Nominal seat or nut constraint absent")
    # Manufacturing sequence: the support/keeper is installed in the bare shell
    # before the fins and motor. Main cap screws are added during motor service.
    # This checks only that stage; it does not qualify later fin bonding/access.
    moving_names = [name for name in candidates if not name.startswith("screw_")]
    assembly = cq.Compound.makeCompound([candidates[name] for name in moving_names])
    blockers = []
    for shift in range(-300, 1, 5):
        moved = assembly.translate((0, 0, shift))
        for name in ("aft_shell",):
            if moved.intersect(references[name]).Volume() > 0.05:
                blockers.append({"shift_mm": shift, "part": name})
                break
        if blockers:
            break
    if blockers:
        save(
            "stopped_pre_shell_insertion",
            blockers=blockers,
            seats=seats,
            nut_constraints=retention,
            removed_old_ring_contribution_mm3=removed_volume,
        )
        raise ValueError("Sampled pre-shell insertion blocked; stop")
    # Remove M3 screws first, then translate the cap aft against unchanged solids.
    cap_blockers = []
    for shift in range(5, 51, 5):
        moved = references["aft_retainer"].translate((0, 0, shift))
        for name, shape in [
            ("motor", references["motor"]),
            ("motor_liner", references["motor_liner"]),
            ("aft_shell", references["aft_shell"]),
            ("fin_set", references["fin_set"]),
            ("modified_mount", mount),
            ("keeper", keeper),
            ("bridge", bridge),
        ]:
            if moved.intersect(shape).Volume() > 0.05:
                cap_blockers.append({"shift_mm": shift, "part": name})
                break
        if cap_blockers:
            break
    if cap_blockers:
        save(
            "stopped_cap_service",
            blockers=cap_blockers,
            seats=seats,
            nut_constraints=retention,
            removed_old_ring_contribution_mm3=removed_volume,
        )
        raise ValueError("Sampled cap service blocked; stop")
    # Cap/screws removed: sampled aftward motor motion against installed keeper,
    # bridge, shell, liner and fin; a sample is not a swept-volume proof.
    motor_blockers = []
    for shift in range(5, 146, 5):
        moved = references["motor"].translate((0, 0, shift))
        for name, s in [
            ("keeper", keeper),
            ("bridge", bridge),
            ("modified_mount", mount),
            ("aft_shell", references["aft_shell"]),
            ("motor_liner", references["motor_liner"]),
            ("fin_set", references["fin_set"]),
        ]:
            if moved.intersect(s).Volume() > 0.05:
                motor_blockers.append({"shift_mm": shift, "part": name})
                break
        if motor_blockers:
            break
    if motor_blockers:
        save(
            "stopped_motor_service",
            blockers=motor_blockers,
            seats=seats,
            nut_constraints=retention,
            removed_old_ring_contribution_mm3=removed_volume,
        )
        raise ValueError("Sampled motor service blocked; stop")
    masses = {
        "removed_old_ring_contribution_g": removed_volume * 0.000715,
        "keeper_g": keeper.Volume() * 0.00185,
        "modified_mount_and_guides_g": (mount.Volume() + sum(g.Volume() for g in guides))
        * 0.000715,
        "source_replan_mount_and_guides_g": (old.Volume() + sum(g.Volume() for g in guides))
        * 0.000715,
        "bridge_after_holes_g": bridge.Volume() * 0.00185,
        "m2_screws_and_nuts_nominal_g": 1.32,
        "m2_washer_mass_g": 0.0,
        "integral_g11_pads_in_keeper_mass": True,
        "net_vehicle_mass_change_g": None,
    }
    for name, s in candidates.items():
        cq.exporters.export(s, str(OUT / (name + ".step")))
    cq.exporters.export(
        cq.Compound.makeCompound(list(solids.values())), str(OUT / "study-assembly.step")
    )
    result = {
        "status": "nominal_geometry_unaccepted",
        "source_identity": cfg["source_identity"],
        "known_fixture": {"wall_mm3": wall, "bore_overlap_mm3": bore, "bearing_mm2": bearing},
        "removed_old_ring_contribution_mm3": removed_volume,
        "candidate_intersections": overlaps,
        "direct_bridge_seat_mm2": seats,
        "nut_constraints": retention,
        "pre_shell_axial_samples": {
            "spacing_mm": 5,
            "blockers": blockers,
            "moving_parts": moving_names,
            "obstacles": ["aft_shell"],
            "not_yet_installed": ["fin_set", "motor", "motor_liner", "main_cap_screws"],
            "limitation": "Liner/shield and fin installation/access are separate unverified stages.",
        },
        "cap_aft_service_samples": {
            "spacing_mm": 5,
            "m3_screws_removed": True,
            "blockers": cap_blockers,
        },
        "motor_aft_service_samples": {
            "spacing_mm": 5,
            "cap_and_m3_screws_removed": True,
            "blockers": motor_blockers,
        },
        "masses": masses,
        "m2_direct_bearing_and_integral_pad_qualification": "unavailable",
        "full_vehicle_regenerated": False,
        "acceptance": False,
        "flight_ready": False,
    }
    (OUT / "record.json").write_text(json.dumps(result, indent=2) + "\n")
    save("complete")
    print(json.dumps(result))


def main():
    if sys.argv[1:] == ["--child"]:
        child()
        return
    cfg, _, _, _, v, inputs, axial = preflight()
    prior_status = json.loads(
        Path("build/wo03-g80-keeper-geometry-v1/execution-status.json").read_text()
    )
    prior_inputs = prior_status["source_sha256_before"]
    if prior_status["source_sha256_after"] != prior_inputs or any(
        not Path(p).is_file() or sha(Path(p)) != h for p, h in prior_inputs.items()
    ):
        raise ValueError("Prior as-run inputs changed")
    original = Path("build/wo03-g80-keeper-geometry-v1/executed.py")
    old_source = original.read_text()
    source_now = Path(__file__).read_text()
    begin = "    def cylinder(r, z, h, x=0.0, y=0.0):"
    finish = '    save("fixture_passed", wall_mm3=wall, bore_overlap_mm3=bore, bearing_mm2=bearing)'
    next_begin = '    prev = Path(cfg["source_replan"])'
    next_end = "    seats = []"
    if (
        old_source.split(begin, 1)[1].split(finish, 1)[0]
        != source_now.split(begin, 1)[1].split(finish, 1)[0]
        or old_source.split(next_begin, 1)[1].split(next_end, 1)[0]
        != source_now.split(next_begin, 1)[1].split(next_end, 1)[0]
    ):
        raise ValueError("Geometry-construction prefix differs from as-run source")
    inputs += [
        original,
        Path("build/wo03-g80-keeper-geometry-v1/progress.json"),
        Path("build/wo03-g80-keeper-geometry-v1/execution-status.json"),
        Path("docs/wo03-g80-nut-rotation-bound.md"),
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    hashes = {str(p): sha(p) for p in inputs}
    (OUT / "preflight.json").write_text(
        json.dumps(
            {
                "source_sha256_before": hashes,
                "nominal_axial_intervals": axial,
                "all_52_source_parts": len(v.parts),
                "m2_washer": "none per primary decision; direct bearing unqualified",
                "m2_pad": "integral G11, nominal geometry; flatness and compression unqualified",
                "prior_keeper_child_cpu_s": prior_status["child_user_cpu_s"]
                + prior_status["child_system_cpu_s"],
                "geometry_recipe_prefix_matches_as_run": True,
                "washer_OD_tolerance": "unavailable",
            },
            indent=2,
        )
        + "\n"
    )
    print("Preflight passed; one nominal geometry child", flush=True)
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
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    started = time.monotonic()
    result = {"returncode": None, "timeout": False}
    try:
        r = subprocess.run(
            [sys.executable, __file__, "--child"], env=env, timeout=cfg["wall_limit_s"], check=False
        )
        result["returncode"] = r.returncode
    except subprocess.TimeoutExpired:
        result["timeout"] = True
    finally:
        after = resource.getrusage(resource.RUSAGE_CHILDREN)
        result.update(
            {
                "wall_s": time.monotonic() - started,
                "child_user_cpu_s": after.ru_utime - before.ru_utime,
                "child_system_cpu_s": after.ru_stime - before.ru_stime,
                "prior_keeper_child_cpu_s": prior_status["child_user_cpu_s"]
                + prior_status["child_system_cpu_s"],
                "packet_cpu_s_known": after.ru_utime
                - before.ru_utime
                + after.ru_stime
                - before.ru_stime
                + prior_status["child_user_cpu_s"]
                + prior_status["child_system_cpu_s"],
                "source_sha256_before": hashes,
                "source_sha256_after": {str(p): sha(p) for p in inputs},
            }
        )
        (OUT / "execution-status.json").write_text(json.dumps(result, indent=2) + "\n")
    if result["timeout"] or result["returncode"] != 0:
        raise SystemExit("Stopped: one attempt only, no retry")


if __name__ == "__main__":
    main()
