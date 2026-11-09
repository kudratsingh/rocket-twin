"""Read back the supplied registered joint STEP; never generate or substitute CAD.

CLI: --step supplied-file.step [--provenance supplied.json] --output report.json.
Browser origin is a separate observation; a successful file check does not assert it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROVENANCE = ROOT / "docs/studies/frontend-desktop-detail-20261108/cad-export.json"
PROVENANCE_SHA = "a7af1fadc431dea8958a212e2a552cf2ee833b068dbeaf51dc151d6d7fbbf731"
JOINT_SHA = "2ea1796f0b506ce382e1f7f9d25280b21c2f30d2119bb3aa52f257c0e2cff119"
JOINT_BYTES = 339487
SOURCE_STEP = ROOT / "output/rp1-inspection-step/critical_motor_fin_ring_joint.step"
SPEC = "811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660"
CORE = "238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def bounds(shape: Any) -> list[list[float]]:
    b = shape.BoundingBox()
    result = [[b.xmin, b.ymin, b.zmin], [b.xmax, b.ymax, b.zmax]]
    if not all(math.isfinite(v) for corner in result for v in corner):
        raise ValueError("Nonfinite STEP bounds")
    return result


def error(a: list[list[float]], b: list[list[float]]) -> float:
    return max(abs(x - y) for ca, cb in zip(a, b, strict=True) for x, y in zip(ca, cb, strict=True))


def unique_solid(solids: list[Any], expected: list[list[float]], label: str) -> Any:
    candidates = [s for s in solids if error(bounds(s), expected) < 1e-5]
    if len(candidates) != 1:
        raise ValueError(f"No unique actual STEP solid matches registered {label} bounds")
    return candidates[0]


def readback(path: Path, provenance: dict[str, Any]) -> dict[str, Any]:
    import cadquery as cq

    # Import the supplied file itself. No original path is used as a CAD fallback.
    shape = cq.Compound.makeCompound(cq.importers.importStep(str(path), unit="MM").vals())
    solids = shape.Solids()
    if not shape.isValid() or len(solids) != 18 or any(not s.isValid() for s in solids):
        raise ValueError("Supplied STEP is not a valid registered18-solid assembly")
    registered = next(
        a for a in provenance["assemblies"] if a["id"] == "critical_motor_fin_ring_joint"
    )
    read_bounds = bounds(shape)
    bounds_error = error(read_bounds, registered["readback"]["bounds_mm"])
    if bounds_error > 1e-5:
        raise ValueError("Supplied STEP assembly bounds mismatch")
    rows = {r["id"]: r for r in provenance["parts"]}
    first_tab = unique_solid(
        solids, [[15.95, -3.0, 1080.2], [33.401, 3.0, 1189.6]], "first fin tab"
    )
    tab_bounds = bounds(first_tab)
    thickness = tab_bounds[1][1] - tab_bounds[0][1]
    tab_length = tab_bounds[1][2] - tab_bounds[0][2]
    aft_ring = unique_solid(solids, rows["aft_ring"]["cad_bounds_mm"], "aft ring")
    ring_bounds = bounds(aft_ring)
    gap = ring_bounds[0][2] - tab_bounds[1][2]
    if abs(thickness - 6) > 1e-5 or abs(tab_length - 109.4) > 1e-5 or abs(gap - 0.4) > 1e-5:
        raise ValueError("Actual first-tab/ring representative dimensions mismatch")
    body = unique_solid(solids, rows["body"]["cad_bounds_mm"], "body")
    slot_planes = []
    for face in body.Faces():
        if face.geomType() != "PLANE":
            continue
        b = bounds(face)
        n = face.normalAt().toTuple()
        if (
            abs(abs(n[1]) - 1) < 1e-8
            and b[0][0] > 0
            and abs(b[1][1] - b[0][1]) < 1e-5
            and abs(b[0][2] - 1075) < 1e-5
            and abs(b[1][2] - 1205) < 1e-5
        ):
            slot_planes.append({"y_mm": (b[0][1] + b[1][1]) / 2, "bounds_mm": b})
    slot: dict[str, Any] = {
        "status": "source_defined_not_independently_extracted",
        "source_nominal_mm": 6.8,
        "source_proposed_cut_tolerance_mm": 0.05,
        "measured_from_step_mm": None,
        "basis": "AD1 fin_joints.external_slot_width_mm; whole-STEP extraction not uniquely resolved",
    }
    if len(slot_planes) == 2:
        measured = abs(slot_planes[1]["y_mm"] - slot_planes[0]["y_mm"])
        if abs(measured - 6.8) > 1e-5:
            raise ValueError("Actual planar slot-wall separation differs from registered6.8mm")
        slot.update(
            status="readback_planar_slot_faces",
            measured_from_step_mm=measured,
            faces=slot_planes,
            basis="Two unique parallel first-slot side faces on actual imported body, stations1075–1205mm",
        )
    return {
        "valid": True,
        "solids": len(solids),
        "bounds_mm": read_bounds,
        "maximum_registered_bounds_error_mm": bounds_error,
        "cadquery_version": cq.__version__,
        "representative_dimensions": {
            "tab": {
                "solid_bounds_mm": tab_bounds,
                "thickness_mm": thickness,
                "axial_length_mm": tab_length,
                "aft_station_mm": tab_bounds[1][2],
            },
            "aft_ring": {"solid_bounds_mm": ring_bounds, "front_station_mm": ring_bounds[0][2]},
            "nominal_aft_gap_mm": gap,
            "body_slot": slot,
        },
    }


def verify(step: Path, provenance_path: Path | None = None) -> dict[str, Any]:
    started_wall, started_cpu = time.monotonic(), time.process_time()
    actual = step.resolve(strict=True)
    data = actual.read_bytes()
    digest = sha(data)
    if len(data) != JOINT_BYTES or digest != JOINT_SHA:
        raise ValueError(
            "Supplied STEP bytes do not match registered joint SHA/size; no CAD import"
        )
    text = data.decode("ascii")
    if (
        not text.startswith("ISO-10303-21;")
        or "HEADER;" not in text
        or "END-ISO-10303-21;" not in text
    ):
        raise ValueError("Invalid registered STEP exchange header")
    units = re.findall(r"\(\s*LENGTH_UNIT\(\)\s+NAMED_UNIT\(\*\)\s+SI_UNIT\(([^)]*)\)", text)
    if not units or any(re.sub(r"\s", "", unit) != ".MILLI.,.METRE." for unit in units):
        raise ValueError("STEP length-unit declarations are not consistently millimetres")
    provenance_file = (provenance_path or PROVENANCE).resolve(strict=True)
    provenance_bytes = provenance_file.read_bytes()
    if sha(provenance_bytes) != PROVENANCE_SHA:
        raise ValueError("Supplied/registered provenance bytes mismatch")
    provenance = json.loads(provenance_bytes)
    identity = provenance["identity"]
    registered = next(
        a for a in provenance["assemblies"] if a["id"] == "critical_motor_fin_ring_joint"
    )
    if (
        identity["specification_sha256"] != SPEC
        or identity["inspection_geometry_sha256"] != CORE
        or registered["sha256"] != JOINT_SHA
        or registered["bytes"] != JOINT_BYTES
    ):
        raise ValueError("Foreign STEP provenance/configuration identity")
    result = readback(actual, provenance)
    if actual.read_bytes() != data or provenance_file.read_bytes() != provenance_bytes:
        raise ValueError("Supplied file/provenance changed during readback")
    return {
        "schema_version": 1,
        "id": "rp1-critical-fin-joint-file-readback-v1",
        "status": "verified_file_readback",
        "file": {"realpath": str(actual), "sha256": digest, "bytes": len(data)},
        "source_verification_only": actual == SOURCE_STEP.resolve(),
        "browser_origin": "Not asserted by this tool; supplied file path and bytes only",
        "provenance": {
            "realpath": str(provenance_file),
            "sha256": PROVENANCE_SHA,
            "kind": "supplied_file" if provenance_path else "registered_repository_record",
        },
        "identity": identity,
        "units": "mm",
        "millimetre_length_unit_declarations": len(units),
        "readback": result,
        "runtime": {
            "wall_seconds": time.monotonic() - started_wall,
            "cpu_seconds": time.process_time() - started_cpu,
        },
        "limitations": [
            "Readback verifies the supplied registered inspection file, not browser download provenance",
            "Source nominal geometry and motor/retainer envelopes are not manufactured/qualified hardware",
            "No physical fit, adhesive/contact, strength, mass/inertia or flight qualification",
        ],
    }


def main() -> int:
    import resource
    import signal

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", type=Path, required=True)
    parser.add_argument("--provenance", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.resolve() in {args.step.resolve(), (args.provenance or PROVENANCE).resolve()}:
        parser.error("Report output cannot overwrite STEP or provenance input")
    resource.setrlimit(resource.RLIMIT_CPU, (59, 60))
    signal.signal(signal.SIGALRM, lambda *_: sys.exit("Readback90s wall cap; no retry"))
    signal.alarm(90)
    try:
        result = verify(args.step, args.provenance)
    except (OSError, ValueError, KeyError, StopIteration) as exc:
        result = {"status": "rejected", "reason": str(exc), "supplied_path": str(args.step)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"status": result["status"], "report": str(args.output)}))
    return 0 if result["status"] == "verified_file_readback" else 1


if __name__ == "__main__":
    raise SystemExit(main())
