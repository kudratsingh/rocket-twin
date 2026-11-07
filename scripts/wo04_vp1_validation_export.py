"""Prepare a read-only VP1 inspection snapshot from pinned source records."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "configs/engineering/rp1-vp1-preview.yaml"
PLAN = "configs/studies/rp1-validation-package.yaml"
VEHICLE = "configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml"
ACCOUNTING = "docs/validation/rp1-vp1/accounting.json"
PROTOCOL = "docs/validation/rp1-vp1/protocol.md"
SUMMARY = "docs/validation/rp1-vp1/package-summary.md"
PRODUCER = "scripts/wo03_rp1_vp1_package.py"
REGISTERS = (
    "configs/studies/rp1-vp1-material-sources.yaml",
    "configs/studies/rp1-vp1-equipment-sources.yaml",
)
MESSAGE_PATHS = (
    "docs/validation/rp1-vp1/messages/01-aircraft-spruce.txt",
    "docs/validation/rp1-vp1/messages/02-loc.txt",
    "docs/validation/rp1-vp1/messages/03-aerotech.txt",
    "docs/validation/rp1-vp1/messages/04-west-system.txt",
    "docs/validation/rp1-vp1/messages/05-laboratory-rfq.txt",
)
MESSAGE_IDS = ("aircraft-spruce", "loc", "aerotech", "west-system", "laboratory")
CONFIG_HASH = "811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660"
PACKAGE_ID = "RP1-VP1-plywood-validation-package-v1"
PREVIEW_ID = "RP1-VP1-inspection-preview-v1"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def build(root: Path = ROOT) -> dict:
    """Read each source once, validate its identity, then recheck before returning."""
    manifest_bytes = (root / MANIFEST).read_bytes()
    manifest = yaml.safe_load(manifest_bytes)
    require(
        manifest["schema_version"] == 1 and manifest["id"] == PREVIEW_ID,
        "Unexpected preview identity",
    )
    required = {PLAN, VEHICLE, ACCOUNTING, PROTOCOL, SUMMARY, PRODUCER, *REGISTERS, *MESSAGE_PATHS}
    pins = manifest["source_sha256"]
    require(set(pins) == required, "Incomplete or unexpected source register")
    snapshots = {p: (root / p).read_bytes() for p in sorted(required)}
    require(all(digest(snapshots[p]) == pins[p] for p in required), "Source hash mismatch")
    package = yaml.safe_load(snapshots[PLAN])
    accounting = json.loads(snapshots[ACCOUNTING])
    require(package["id"] == accounting["id"] == PACKAGE_ID, "Package identity mismatch")
    require(
        package["frozen_configuration"] == VEHICLE
        and package["configuration_sha256"] == pins[VEHICLE] == CONFIG_HASH,
        "Configuration identity mismatch",
    )
    vehicle = yaml.safe_load(snapshots[VEHICLE])
    require(vehicle["id"] == "G80-F2-RP1-AD1-definition-v2", "Unexpected vehicle ID")
    require(
        accounting["plan_sha256"] == pins[PLAN] and accounting["producer_sha256"] == pins[PRODUCER],
        "Accounting provenance mismatch",
    )
    require(
        all(
            package[k] is False
            for k in (
                "supplier_contact_authorized",
                "purchase_authorized",
                "physical_work_authorized",
                "paid_service_authorized",
            )
        ),
        "Approval state changed",
    )
    require(all(s["authorized"] is False for s in package["stages"]), "Stage approval changed")
    require(
        accounting["root_method_accepted"] is False
        and accounting["test_material_adopted"] is False
        and accounting["unknown_cost_is_not_zero"] is True,
        "Accounting status changed",
    )
    require(
        accounting["initial_room_material_order_usd"] == "236.75"
        and accounting["published_material_order_usd"] == "269.49"
        and accounting["expected_all_in_total_usd"] is None,
        "Cost record changed",
    )
    preserved = package["preserved"]
    require(
        (
            preserved["fin_force_N"],
            preserved["fin_moment_Nm"],
            preserved["design_factor_already_applied"],
            preserved["tip_movement_limit_mm"],
        )
        == (331.125, 8.83, 3, 1),
        "Engineering limits changed",
    )
    stages, parts, drafts = manifest["stages"], manifest["parts"], manifest["messages"]
    require(
        [s["id"] for s in stages] == ["S0", "S1", "S2a", "S2b"]
        and all(s["status"] == "not-authorized" for s in stages),
        "Stage identity changed",
    )
    part_ids = [p["id"] for p in parts]
    require(
        part_ids
        == [
            "fin_set",
            "fin_tabs",
            "motor_tube",
            "body",
            "forward_ring",
            "aft_ring",
            "test_strips",
            "joint_witnesses",
            "harness_keepout",
        ]
        and all(p["status"] == "unverified" for p in parts),
        "Part identity changed",
    )
    require(
        all(s["part_ids"] and set(s["part_ids"]) <= set(part_ids) for s in stages),
        "Invalid stage part mapping",
    )
    require(
        [d["id"] for d in drafts] == list(MESSAGE_IDS)
        and [d["path"] for d in drafts] == list(MESSAGE_PATHS),
        "Draft identity changed",
    )
    messages = []
    for draft in drafts:
        text = snapshots[draft["path"]].decode("utf-8")
        headers = dict(line.split(": ", 1) for line in text.splitlines()[:4])
        require(
            "DRAFT" in headers["Status"] and "UNSENT" in headers["Status"],
            "Draft is not marked unsent",
        )
        messages.append(
            {
                "id": draft["id"],
                "label": draft["label"],
                "recipient": headers.get("To", headers.get("Recipient")),
                "channel": headers["Channel"],
                "text": text,
                "source": {"path": draft["path"], "sha256": pins[draft["path"]]},
            }
        )
    material_keys = ("id", "sku", "quantity", "unit", "unit_usd", "basis", "availability", "source")
    materials = [{k: m[k] for k in material_keys} for m in package["materials"]]
    result = {
        "schema_version": 1,
        "id": PREVIEW_ID,
        "package": {"id": PACKAGE_ID, "path": PLAN, "sha256": pins[PLAN]},
        "configuration": {"id": vehicle["id"], "sha256": pins[VEHICLE]},
        "protocol": {"path": PROTOCOL, "sha256": pins[PROTOCOL]},
        "status": package["status"],
        "approvals": {
            "supplier_contact": False,
            "purchases": False,
            "physical_work": False,
            "paid_service": False,
        },
        "currency": "USD",
        "price_snapshot_date": "2026-11-04",
        "costs": {
            "room_materials_usd": accounting["initial_room_material_order_usd"],
            "full_materials_usd": accounting["published_material_order_usd"],
            "all_in_usd": None,
            "note": "Archived material prices from 2026-11-04; services, fixtures, calibrated channels, delivery and other costs are unquoted. The planning reservation is not a quote.",
        },
        "limits": {
            "fin_force_N": preserved["fin_force_N"],
            "fin_moment_Nm": preserved["fin_moment_Nm"],
            "design_factor_already_applied": preserved["design_factor_already_applied"],
            "tip_limit_mm": preserved["tip_movement_limit_mm"],
        },
        "stages": stages,
        "parts": parts,
        "links": [
            {
                "stage_id": s["id"],
                "part_id": p,
                "label": next(x["label"] for x in parts if x["id"] == p),
            }
            for s in stages
            for p in s["part_ids"]
        ],
        "messages": messages,
        "materials": materials,
        "limitations": [
            "Bare AD1 fails the estimated screen; this stock is not adopted.",
            "Finished strength and whole-root evidence are unavailable; no installed fin pass is established.",
            "Parts are conceptual and unverified, with no CAD association.",
            "No supplier contact, purchase, paid service, fabrication or test is authorized.",
            "Thermal, recovery, installed flutter, physical inspection and flight release remain open.",
        ],
        "sources": [{"path": p, "sha256": pins[p]} for p in sorted(required)]
        + [{"path": MANIFEST, "sha256": digest(manifest_bytes)}],
    }
    require(
        (root / MANIFEST).read_bytes() == manifest_bytes
        and all((root / p).read_bytes() == snapshots[p] for p in required),
        "Source changed during export",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "web/public/engineering-workbench/rp1-validation.json"
    )
    args = parser.parse_args()
    data = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=args.output.parent, prefix=".rp1-validation-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(name, args.output)
    finally:
        Path(name).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
