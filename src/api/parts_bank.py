"""Deterministic read-only library projection of the frozen RP1 source records.

Definitions are not installed occurrences, and a source group is one accounting
line regardless of the number of solids it represents. No CAD/physics is run.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from src.api import rp1_geometry, rp1_inspection
from src.inspection.rp1_geometry import MISSING, SOURCE_SOLIDS

ID = "rp1-parts-bank-v1"
MODULE_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATHS = (
    "src/api/parts_bank.py",
    "src/api/rp1_inspection.py",
    "src/api/rp1_geometry.py",
    "src/inspection/rp1_geometry.py",
)
MASS_BASIS = "Source-record group estimate/budget; not measured or per-piece mass"


def digest(value: Any) -> str:
    """Content revision: canonical JSON, excluding the caller's own revision field."""
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode()
    ).hexdigest()


def _snapshot(root: Path) -> dict[str, bytes]:
    data = {path: (root / path).read_bytes() for path in rp1_inspection.PINS}
    data.update({path: (MODULE_ROOT / path).read_bytes() for path in MODULE_PATHS})
    if any(
        hashlib.sha256(data[path]).hexdigest() != pin for path, pin in rp1_inspection.PINS.items()
    ):
        raise ValueError("Parts bank source hash mismatch")
    return data


def _number(value: Any, label: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise TypeError(f"Invalid parts bank {label}")
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"Invalid parts bank {label}")
    return float(value)


def _issues(part: dict[str, Any]) -> list[dict[str, Any]]:
    pid = part["id"]
    locator = f"parts[id={pid}]"
    messages = {
        "motor_retainer": (
            "retainer_product_conflict",
            (
                "learn names AeroTech 19002, while engineering.function names Estes 009750. "
                "Exact product/revision and cap/collar/thread/seat geometry remain unresolved."
            ),
            [f"{locator}.learn", f"{locator}.engineering.function"],
        ),
        "motor_tube": (
            "tube_dimension_conflict",
            (
                "Current geometry is OD31.369/ID29.169 mm, length165 mm, wall1.1 mm; learn "
                "names AeroTech12912/305 mm stock. Legacy build/CAD/service notes retain "
                "1.140in ID/1.210in OD mount-kit dimensions. No supplier fit reconciliation."
            ),
            [f"{locator}.geometry", f"{locator}.learn", f"{locator}.build.notes"],
        ),
        "independent_recovery": (
            "recovery_product_conflict",
            (
                "learn/dimensions propose Eggtimer Apogee, while engineering.function names "
                "Altus Metrum EasyMini v3.0. Exact controller/revision/mount/power unresolved; "
                "the current solid is a generic estimated envelope."
            ),
            [f"{locator}.learn", f"{locator}.engineering.function"],
        ),
        "high_g_accel": (
            "board_reference_limits",
            (
                "Adafruit5374 source XY reference is separate from the installed envelope. "
                "Its Eagle U1 ADXL343 label does not resolve ADXL375 silicon identity; "
                "populated heights, connectors and installed mounting remain unavailable."
            ),
            [f"{locator}.cite", f"{locator}.cad", f"{locator}.engineering.service_notes"],
        ),
    }
    if pid not in messages:
        return []
    issue_id, message, locators = messages[pid]
    return [
        {
            "id": issue_id,
            "severity": "warning",
            "status": "unresolved",
            "message": message,
            "locators": locators,
        }
    ]


def _classification(raw: dict[str, Any]) -> dict[str, Any]:
    """Source-only counterpart to the existing inspection categories, without assets."""
    pid = raw["id"]
    if pid in MISSING:
        maturity, explanation = "missing_geometry", MISSING[pid]
    elif pid in SOURCE_SOLIDS:
        maturity = "source_dimensioned"
        explanation = "Ideal source-dimensioned inspection solid; estimated dimensions and unverified installed joints."
    elif raw["cad"]["role"] == "distributed_budget":
        maturity = "mass_allowance"
        explanation = "Separate source mass/process allowance; no unique installed solid or qualified spatial distribution."
    else:
        maturity = "simplified_envelope"
        explanation = (
            "Nominal source bounding envelope; supplier details, fit and installed form unverified."
        )
    if pid == "forward_ring":
        explanation = "Ideal notched annulus; proposed 2 mm edge roundovers omitted. Not a finished passage or fit model."
    if pid == "motor_retainer":
        explanation = "Historical nominal annular envelope only; cap/sleeve details and current exact motor fit unavailable."
    return {"id": pid, "maturity": maturity, "description": explanation, "mesh": None}


def build(root: Path) -> dict[str, Any]:
    """Return 55 source definitions/instances, or reject the whole source drift.

    Generated geometry is optional and admitted atomically by its existing verifier.
    Missing cache supplies yield explicit unavailable geometry, never generation.
    Corrupt or foreign existing assets raise rather than silently degrading.
    """
    root = root.resolve()
    before = _snapshot(root)
    source = rp1_inspection.build(root)
    parts = source["parts"]
    ids = [p["id"] for p in parts]
    if len(ids) != 55 or len(set(ids)) != 55:
        raise ValueError("Parts bank duplicate or incomplete source inventory")
    classified = [_classification(p["raw"]) for p in parts]
    verified: dict[str, Any] | None = None
    unavailable: str | None = None
    try:
        verified = rp1_geometry.build(root)
    except FileNotFoundError:
        unavailable = "Matching generated inspection assets unavailable; no generation attempted"
    if verified is not None and [p["id"] for p in verified["parts"]] != ids:
        raise ValueError("Parts bank admitted geometry inventory mismatch")
    geometry_rows = (
        {p["id"]: p for p in verified["parts"] if verified}
        if verified
        else {p["id"]: p for p in classified}
    )
    if verified and any(geometry_rows[p["id"]]["maturity"] != p["maturity"] for p in classified):
        raise ValueError("Parts bank geometry maturity mismatch")
    definitions = []
    instances = []
    for part in parts:
        raw = part["raw"]
        pid = part["id"]
        geometry = geometry_rows[pid]
        count = raw["geometry"].get("count", 1)
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError("Invalid parts bank source group count")
        build_source = raw.get("build") or {}
        issues = _issues(raw)
        source_cost = _number(build_source.get("cost_usd"), "price")
        if source_cost == 0:
            issues.append(
                {
                    "id": "zero_source_budget",
                    "severity": "warning",
                    "status": "unresolved",
                    "message": (
                        "The recorded source budget is zero; shared stock may be charged "
                        "elsewhere or cost may be unresolved. This is not a free part, "
                        "current unit quote or owner-stock credit."
                    ),
                    "locators": [f"parts[id={pid}].build.cost_usd"],
                }
            )
        role = raw["cad"]["role"]
        maturity = geometry["maturity"]
        mesh = copy.deepcopy(geometry["mesh"]) if verified else None
        reuse_status = (
            "identity_unresolved"
            if pid in ("motor_retainer", "independent_recovery")
            else (
                "allowance_only"
                if maturity == "mass_allowance"
                else (
                    "geometry_unavailable"
                    if maturity == "missing_geometry"
                    else "source_reference_only"
                )
            )
        )
        provenance = [
            {
                "path": path,
                "sha256": rp1_inspection.PINS[path],
                "locator": f"parts[id={pid}]" if path == rp1_inspection.SPEC else "$",
                "role": source_role,
            }
            for path, source_role in (
                (rp1_inspection.SPEC, "frozen source record"),
                (rp1_inspection.DEFINITION, "unadopted attachment definition"),
                (rp1_inspection.RECORD, "saved AD1 evidence; not physical qualification"),
            )
        ]
        row: dict[str, Any] = {
            "id": f"rp1:{pid}",
            "source_part_id": pid,
            "name": part["name"],
            "kind": part["type"],
            "material": part["material"],
            "function": part["function"],
            "learn": part["learn"],
            "dimensions": {
                "units": "m",
                "values": copy.deepcopy(raw["geometry"]),
                "basis": "source_nominal; count is dimensionless and angles use named units",
            },
            "mass_kg": _number(raw.get("mass_kg"), "mass"),
            "mass_basis": MASS_BASIS if raw.get("mass_kg") is not None else "unavailable",
            "manufacturing": {
                "method": build_source.get("method"),
                "generator": build_source.get("generator"),
                "notes": build_source.get("notes"),
                "status": "source description; not manufacturing authorization",
            },
            "geometry": {
                "maturity": maturity,
                "mesh_available": mesh is not None,
                "mesh": mesh,
                "mesh_scope": "installed_reference" if mesh is not None else None,
                "frame": verified["viewer_frame"] if verified and mesh is not None else None,
                "reusable_local_geometry": False,
                "registered_instance_id": pid,
                "reason": (
                    unavailable
                    if unavailable
                    else geometry["description"] if mesh is None else None
                ),
                "description": geometry["description"],
            },
            "price": {
                "amount_usd": source_cost,
                "basis": "source_budget",
                "current_verified": False,
                "counting_basis": "source_record",
                "owner_stock_credit": False,
                "notes": "Dated source group budget; not a current unit price or quote",
            },
            "provenance": provenance,
            "issues": issues,
            "reuse_status": reuse_status,
            "source_cad_role": role,
            "source_estimate": raw.get("estimate", True),
            "physical_verification": "open",
            "interfaces": None,
            "interfaces_status": "Not defined by this catalog; parentage is not an attachment",
        }
        row["revision_sha256"] = digest(row)
        definitions.append(row)
        instances.append(
            {
                "id": pid,
                "definition_id": row["id"],
                "definition_revision_sha256": row["revision_sha256"],
                "configuration_id": source["id"],
                "position_m": raw["position_m"],
                "lateral_offset_m": copy.deepcopy(raw["lateral_offset_m"]),
                "source_parent_id": raw.get("parent"),
                "quantity": 1,
                "counting_basis": "source_record",
                "group_count": count,
                "group_count_basis": (
                    "source geometry.count"
                    if "count" in raw["geometry"]
                    else "one source record; physical piece count not separately defined"
                ),
            }
        )
    result: dict[str, Any] = {
        "schema_version": 1,
        "id": ID,
        "configuration_id": source["id"],
        "identity": {
            **source["identity"],
            "inspection_geometry_sha256": (
                verified["identity"]["inspection_geometry_sha256"] if verified else None
            ),
        },
        "definitions": definitions,
        "instances": instances,
        "summary": {
            "source_records": 55,
            "definitions": 55,
            "installed_instances": 55,
            "mesh_available": sum(d["geometry"]["mesh_available"] for d in definitions),
            "by_maturity": dict(Counter(d["geometry"]["maturity"] for d in definitions)),
            "mass_basis": MASS_BASIS,
            "price_basis": "Recorded group budgets, not current unit prices or owned stock",
            "geometry_status": "verified inspection assets" if verified else unavailable,
            "engineering_accepted": False,
            "flight_ready": False,
        },
        "capabilities": {"editable": False, "draft_builder": False},
        "module_sources": {path: hashlib.sha256(before[path]).hexdigest() for path in MODULE_PATHS},
        "revision_algorithm": "sha256 canonical JSON UTF-8; sorted keys; compact separators; ensure_ascii=false; excluding own revision_sha256",
    }
    if _snapshot(root) != before:
        raise ValueError("Parts bank source or module changed during read")
    result["revision_sha256"] = digest(result)
    return result


def definition(root: Path, definition_id: str) -> dict[str, Any]:
    """Only exact registered IDs; the caller can map an unknown ID to HTTP404."""
    document = build(root)
    for row in document["definitions"]:
        if row["id"] == definition_id:
            return dict(row)
    raise KeyError("Unknown parts bank definition ID")
