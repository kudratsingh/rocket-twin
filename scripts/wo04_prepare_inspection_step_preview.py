"""Verify and optionally copy only the registered completed inspection STEP packet.

No CAD generation, backend change or dependency installation. Public preparation
requires the primary's separate browser-hold release before invoking --prepare.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs/studies/frontend-desktop-detail-20261108/cad-export.json"
MANIFEST_SHA256 = "a7af1fadc431dea8958a212e2a552cf2ee833b068dbeaf51dc151d6d7fbbf731"
CONFIGURATION = "G80-F2-RP1-AD1-definition-v2"
SPEC = "811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660"
GEOMETRY = "238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608"
ASSEMBLY = "rp1_ad1_v2_inspection_26_records"
PUBLIC = ROOT / "web/public/engineering-workbench/rp1-step"
PARTS = (
    "motor_tube",
    "forward_ring",
    "aft_ring",
    "fin_set",
    "fin_tabs",
    "root_gussets",
    "body",
    "motor",
    "motor_retainer",
    "nose",
    "nose_anchor_plate",
    "nose_recovery_eye",
    "shock_cord",
    "recovery_connectors",
    "parachute",
    "recovery_protection",
    "flight_computer",
    "imu",
    "baro",
    "high_g_accel",
    "micro_sd",
    "battery",
    "independent_recovery",
    "recovery_battery",
    "upper_body",
    "body_splice",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registered_files() -> list[tuple[Path, str, str]]:
    if sha(MANIFEST) != MANIFEST_SHA256:
        raise ValueError("Completed STEP evidence bytes changed; no preparation or regeneration")
    packet = json.loads(MANIFEST.read_bytes())
    identity = packet["identity"]
    if (
        packet["status"] != "complete_inspection_reconstruction"
        or identity["configuration_id"] != CONFIGURATION
        or identity["specification_sha256"] != SPEC
        or identity["inspection_geometry_sha256"] != GEOMETRY
        or packet["units"]["step"] != "mm"
        or packet["engineering_accepted"] is not False
        or packet["manufacturing_clearance"] is not False
        or len(packet["source_records"]) != 55
        or tuple(row["id"] for row in packet["parts"]) != PARTS
    ):
        raise ValueError("Registered STEP source/status/coverage mismatch")
    for relative, expected in packet["source_hashes"].items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"Frozen export input changed: {relative}; no recomputation")
    script = packet["script"]
    if (
        script["path"] != "scripts/wo04_rp1_inspection_step.py"
        or sha(ROOT / script["path"]) != script["sha256"]
    ):
        raise ValueError("Executed exporter code changed, including formatting; no recomputation")
    core_path = ROOT / "docs/studies/rp1-inspection-geometry-20261107/manifest.json"
    if sha(core_path) != packet["core_manifest_sha256"]:
        raise ValueError("Frozen core manifest changed")
    if (
        ROOT / "output/rp1-inspection-geometry/manifest.json"
    ).read_bytes() != core_path.read_bytes():
        raise ValueError("Core output and saved manifest differ")
    core = json.loads(core_path.read_bytes())
    for row in core["parts"]:
        if row["mesh"] and sha(ROOT / row["mesh"]["path"]) != row["mesh"]["sha256"]:
            raise ValueError("Existing core mesh changed")
    if sha(ROOT / core["assembly"]["path"]) != core["assembly"]["sha256"]:
        raise ValueError("Existing core assembly changed")
    assets = []
    for row in packet["parts"]:
        relative = f"parts/{row['id']}.step"
        if row["path"] != f"output/rp1-inspection-step/{relative}":
            raise ValueError("Unregistered STEP path")
        assets.append((ROOT / row["path"], relative, row["sha256"]))
    assembly = next(row for row in packet["assemblies"] if row["id"] == ASSEMBLY)
    if assembly["path"] != f"output/rp1-inspection-step/{ASSEMBLY}.step":
        raise ValueError("Unregistered assembly STEP path")
    assets.append((ROOT / assembly["path"], f"{ASSEMBLY}.step", assembly["sha256"]))
    for path, _, expected in assets:
        if sha(path) != expected:
            raise ValueError(f"Completed STEP bytes changed: {path.name}")
    return [*assets, (MANIFEST, "provenance.json", MANIFEST_SHA256)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prepare",
        action="store_true",
        help="Copy verified registered assets after browser-hold release",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=PUBLIC,
        help="Fixed public folder, or a temporary test folder",
    )
    args = parser.parse_args()
    destination = args.destination.resolve()
    if destination != PUBLIC.resolve() and not destination.is_relative_to(
        Path(tempfile.gettempdir()).resolve()
    ):
        raise ValueError("Destination must be the fixed preview folder or a temporary test folder")
    files = registered_files()
    if args.prepare:
        if destination.exists() and any(destination.iterdir()):
            raise ValueError("Destination is nonempty; no overwrite or mixed packet")
        destination.mkdir(parents=True, exist_ok=True)
        for source, relative, expected in files:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            if sha(target) != expected:
                raise ValueError(f"Copied STEP/provenance bytes differ: {relative}")
    print(
        json.dumps(
            {
                "status": "prepared" if args.prepare else "verified_no_copy",
                "files": len(files),
                "manifest_sha256": MANIFEST_SHA256,
                "destination": str(destination) if args.prepare else None,
            }
        )
    )


if __name__ == "__main__":
    main()
