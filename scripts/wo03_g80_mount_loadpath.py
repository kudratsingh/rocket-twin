"""Check saved G80 mount interfaces with physical gaps retained."""

from __future__ import annotations

import hashlib
import json
import math
import resource
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml
from OCP.OSD import OSD_Parallel, OSD_ThreadPool

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-g80-mount-loadpath.yaml"
OUT = ROOT / "build/wo03-g80-mount-loadpath-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def patch(x0, x1, y, z0, z1):
    import cadquery as cq

    points = [
        cq.Vector(x0, y, z0),
        cq.Vector(x1, y, z0),
        cq.Vector(x1, y, z1),
        cq.Vector(x0, y, z1),
        cq.Vector(x0, y, z0),
    ]
    return cq.Face.makeFromWires(cq.Wire.makePolygon(points))


def face_area_against(shape, face):
    area = 0.0
    for source in shape.Faces():
        result = source.intersect(face)
        area += sum(f.Area() for f in result.Faces())
    return area


def run():
    import cadquery as cq

    from src.vehicle.schema import Vehicle

    start = time.monotonic()
    OSD_Parallel.SetUseOcctThreads_s(True)
    pool = OSD_ThreadPool.DefaultPool_s()
    pool.Init(1)
    if pool.NbThreads() != 1:
        raise ValueError("Could not configure one-thread OCCT pool")
    cfg = yaml.safe_load(CONFIG.read_text())
    tol = float(cfg["max_common_area_error_mm2"])
    a = patch(0, 10, 0, 0, 10)
    fixtures = {
        "full": face_area_against(a, patch(0, 10, 0, 0, 10)),
        "half": face_area_against(a, patch(5, 15, 0, 0, 10)),
        "positive_gap": face_area_against(a, patch(0, 10, 0.1, 0, 10)),
    }
    if any(
        abs(fixtures[k] - expected) > tol
        for k, expected in {"full": 100, "half": 50, "positive_gap": 0}.items()
    ):
        raise ValueError(f"Known geometric fixtures failed: {fixtures}")
    input_paths = [
        CONFIG,
        Path(__file__).resolve(),
        *(
            ROOT / cfg[k]
            for k in (
                "candidate_record",
                "candidate_spec",
                "candidate_step",
                "baseline_manifest",
                "engineering",
            )
        ),
    ]
    part_dir = ROOT / cfg["parts_directory"]
    input_paths += [
        part_dir / f"{name}.step"
        for name in ("aft_shell", "retention", "aft_retainer", "thrust_pads")
    ]
    before = {str(p.relative_to(ROOT)): sha(p) for p in input_paths}
    record = json.loads((ROOT / cfg["candidate_record"]).read_text())
    v = Vehicle.model_validate(yaml.safe_load((ROOT / cfg["candidate_spec"]).read_text()))
    identity = hashlib.sha256(v.model_dump_json(by_alias=True).encode()).hexdigest()
    if (
        identity != cfg["expected_candidate_identity"]
        or identity != record["candidate_identity"]
        or sha(ROOT / cfg["candidate_step"]) != record["step_sha256"]
    ):
        raise ValueError("Candidate or STEP identity mismatch")
    parts = {p.id: p for p in v.parts}

    def placed(shape, part):
        return shape.translate(
            (
                part.lateral_offset_m[0] * 1000,
                -part.lateral_offset_m[1] * 1000,
                part.position_m * 1000,
            )
        )

    mount = placed(
        cq.importers.importStep(str(ROOT / cfg["candidate_step"])).val(), parts["motor_mount"]
    )
    shell = placed(
        cq.importers.importStep(str(part_dir / "aft_shell.step")).val(), parts["aft_shell"]
    )
    plate = placed(
        cq.importers.importStep(str(part_dir / "retention.step")).val(), parts["retention"]
    )
    # Angle-zero rail and one of two opposing finger surfaces. The source
    # dimensions define x=25..sqrt(32^2-6.2^2), z=1060..1078.
    x_end = math.sqrt(32.0**2 - 6.2**2)
    expected_flank = (x_end - 25.0) * 18.0
    rail_patch = patch(25.0, x_end, 6.0, 1060, 1078)
    plate_patch = patch(25.0, x_end, 6.2, 1060, 1078)
    rail_area = face_area_against(mount, rail_patch)
    plate_area = face_area_against(plate, plate_patch)
    if abs(rail_area - expected_flank) > tol or abs(plate_area - expected_flank) > tol:
        raise ValueError(
            f"Ambiguous finger/rail source faces: {rail_area}, {plate_area}, expected {expected_flank}"
        )

    # Last ring occupies stations 1177..1180. A cylinder surface probe on
    # each physical radius preserves the shell slot and fin-channel cutouts.
    def curved_probe(radius):
        cyl = cq.Solid.makeCylinder(radius, 3, cq.Vector(0, 0, 1177))
        return next(face for face in cyl.Faces() if face.geomType() == "CYLINDER")

    mount_ring_area = face_area_against(mount, curved_probe(32.2))
    shell_ring_area = face_area_against(shell, curved_probe(32.5))
    expected_mount_ring = 32.2 * 3 * (2 * math.pi - 6 * math.asin(3.65 / 32.2))
    expected_shell_ring = 32.5 * 3 * (2 * math.pi - 6 * math.asin(3.65 / 32.5))
    if (
        abs(mount_ring_area - expected_mount_ring) > tol
        or abs(shell_ring_area - expected_shell_ring) > tol
    ):
        raise ValueError(
            f"Ambiguous ring surfaces: {mount_ring_area}, {shell_ring_area}, expected {expected_mount_ring}, {expected_shell_ring}"
        )
    # Section is the actual slotted shell BRep, not a gross full circle.
    plane = cq.Face.makePlane(100, 100, basePnt=(0, 0, 1178))
    section = shell.intersect(plane)
    shell_section_area = sum(f.Area() for f in section.Faces())
    if not 0 < shell_section_area < math.pi * (33**2 - 32.5**2):
        raise ValueError(f"Invalid slotted shell cross-section area: {shell_section_area}")
    after = {str(p.relative_to(ROOT)): sha(p) for p in input_paths}
    if before != after:
        raise ValueError("Inputs changed during calculation")
    load = float(record["thrust_n"])
    factor = 3.0
    six_area = 6 * expected_flank
    result = {
        "status": "geometry_and_conditional_screens_complete_not_qualified",
        "candidate_identity": identity,
        "source_sha256_before": before,
        "source_sha256_after": after,
        "fixtures_mm2": fixtures,
        "flank": {
            "rail_area_mm2": rail_area,
            "plate_area_mm2": plate_area,
            "one_pair_projected_area_mm2": expected_flank,
            "six_pair_projected_area_mm2": six_area,
            "physical_gap_mm": 0.2,
            "actual_adhesive_presence_and_coverage": "unavailable",
            "hypothetical_full_area_shear_MPa": load / six_area,
            "hypothetical_full_area_DF3_shear_MPa": factor * load / six_area,
        },
        "last_ring": {
            "mount_surface_area_mm2": mount_ring_area,
            "shell_surface_area_mm2": shell_ring_area,
            "radii_mm": [32.2, 32.5],
            "physical_gap_mm": 0.3,
            "nominal_angular_paired_extent_rad": 2 * math.pi - 6 * math.asin(3.65 / 32.2),
            "actual_adhesive_presence_and_coverage": "unavailable",
        },
        "shell": {
            "slotted_section_area_mm2": shell_section_area,
            "hypothetical_117_53N_full_section_average_MPa": load / shell_section_area,
            "hypothetical_DF3_average_MPa": factor * load / shell_section_area,
            "note": "Entire thrust assumed carried axially at this station solely for sensitivity; actual reaction distribution and branch sharing unknown.",
        },
        "force_assumptions": {
            "forward_thrust_N": load,
            "three_equal_shares_N": load / 3,
            "factor": factor,
            "reverse_N": 150,
            "three_equal_reverse_shares_N": 50,
        },
        "candidate_support": record["candidate_support"],
        "elapsed_s": time.monotonic() - start,
        "resource_self": {
            "user_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime,
            "system_s": resource.getrusage(resource.RUSAGE_SELF).ru_stime,
            "peak_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "threading": "OCCT default pool 1 and one worker requested; no OS affinity claimed",
        "actual_bond_stiffness": "unavailable",
        "acceptance": False,
        "flight_ready": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "record.json").write_text(json.dumps(result, indent=2) + "\n")
    (OUT / "executed.py").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "status",
                    "fixtures_mm2",
                    "flank",
                    "last_ring",
                    "shell",
                    "force_assumptions",
                    "elapsed_s",
                    "resource_self",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    run()
