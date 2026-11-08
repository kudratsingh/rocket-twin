"""Source-owned functional groups and bounded display offsets, never assembly physics."""

from __future__ import annotations

import copy
import hashlib
import math
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from src.api import rp1_inspection
from src.inspection.rp1_geometry import audit

CONFIG = "configs/presentation/rp1-ad1-v2.yaml"
CONFIG_SHA256 = "4ed997e371f8b2473d9da47aee7396562cb9b4d7e031d87f9876025b136c005b"
ID = "rp1-ad1-v2-functional-presentation-v1"
GEOMETRY_SHA256 = "238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608"
GROUP_IDS = (
    "nose_airframe",
    "fins_roots",
    "motor_retention",
    "recovery",
    "avionics_power",
    "launch_finish",
)
SOURCE_PARENT_SEMANTICS = (
    "Recorded source assembly membership only; not a physical attachment, support or strength claim"
)


def _vector(value: Any) -> list[float]:
    if (
        not isinstance(value, list)
        or len(value) != 3
        or any(
            isinstance(v, bool)
            or not isinstance(v, (float, int))
            or not math.isfinite(v)
            or abs(v) > 1
            for v in value
        )
    ):
        raise ValueError(
            "Presentation requires finite authored display vectors within one metre per axis"
        )
    return [float(v) for v in value]


def _source(value: dict[str, Any]) -> None:
    if (
        value.get("path") not in rp1_inspection.PINS
        or value.get("sha256") != rp1_inspection.PINS[value["path"]]
    ):
        raise ValueError("Presentation cross-reference has incompatible source")
    if not isinstance(value.get("locator"), str) or not value["locator"]:
        raise ValueError("Presentation source locator unavailable")


def build(root: Path, *, geometry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate exact source membership and attach only separately identified display data."""
    source = rp1_inspection.build(root)
    raw = (root / CONFIG).read_bytes()
    if hashlib.sha256(raw).hexdigest() != CONFIG_SHA256:
        raise ValueError("Presentation configuration hash mismatch")
    config = yaml.safe_load(raw)
    if (
        config["id"] != ID
        or config["schema_version"] != 1
        or config["configuration_id"] != rp1_inspection.ID
        or config["expected_source_records"] != 55
        or config["inspection_geometry_sha256"] != GEOMETRY_SHA256
        or any(
            config[key] != {"path": path, "sha256": rp1_inspection.PINS[path]}
            for key, path in (
                ("specification", rp1_inspection.SPEC),
                ("definition", rp1_inspection.DEFINITION),
                ("record", rp1_inspection.RECORD),
            )
        )
    ):
        raise ValueError("Presentation source identity mismatch")
    originals = {p["id"]: p for p in source["parts"]}
    ids = set(originals)
    groups = config["groups"]
    memberships = [pid for group in groups for pid in group["part_ids"]]
    if (
        tuple(group["id"] for group in groups) != GROUP_IDS
        or len(memberships) != 55
        or len(set(memberships)) != 55
        or set(memberships) != ids
    ):
        raise ValueError("Presentation must give all55 exact source IDs one primary membership")
    group_by_part = {pid: group for group in groups for pid in group["part_ids"]}
    offsets = {group["id"]: _vector(group["assembly_offset_m"]) for group in groups}
    classification = {p["id"]: p for p in audit(root)["parts"]}
    supported = {
        pid
        for pid, row in classification.items()
        if row["maturity"] in ("source_dimensioned", "simplified_envelope")
    }
    if set(config["detail_offsets_m"]) != supported:
        raise ValueError(
            "Presentation detail offsets must cover exactly the supported inspection shapes"
        )
    details = {pid: _vector(value) for pid, value in config["detail_offsets_m"].items()}
    breakdown = config["breakdown"]
    if (
        breakdown["kind"] != "staged-display-illustration"
        or breakdown["assembly_stage_end"] != 0.5
        or breakdown["units"] != "m"
        or breakdown["manufacturing_clearance"] is not False
    ):
        raise ValueError("Presentation cannot claim manufacturing or clearance qualification")
    bundle_by_part = {}
    for bundle in config["rigid_bundles"]:
        _source(bundle["source"])
        members = bundle["part_ids"]
        if members != ["fin_set", "fin_tabs"] or any(pid in bundle_by_part for pid in members):
            raise ValueError("Presentation integral-fin bundle mismatch")
        if (
            group_by_part[members[0]]["id"] != group_by_part[members[1]]["id"]
            or details[members[0]] != details[members[1]]
        ):
            raise ValueError("Integral fin panels and tabs must keep the same display transform")
        bundle_by_part.update({pid: bundle["id"] for pid in members})
    if set(bundle_by_part) != {"fin_set", "fin_tabs"}:
        raise ValueError("Integral-fin presentation bundle unavailable")
    if set(config["quantities"]) != {"fin_set", "fin_tabs", "root_gussets"}:
        raise ValueError("Presentation quantity coverage changed without source definition")
    quantities = {}
    for pid, quantity in config["quantities"].items():
        _source(quantity["source"])
        expected = (
            originals[pid]["geometry"]["count"]
            if pid == "fin_set"
            else {"fin_tabs": 3, "root_gussets": 6}[pid]
        )
        if quantity["value"] != expected or quantity["source"].get("part_id") != pid:
            raise ValueError("Presentation quantity is not source recorded")
        if (
            pid != "fin_set"
            and quantity.get("source_text", "") not in originals[pid]["cad"]["notes"]
        ):
            raise ValueError("Presentation quantity source text mismatch")
        quantities[pid] = {
            key: copy.deepcopy(quantity[key]) for key in ("value", "unit", "basis", "source")
        }
    links = config["cross_links"]
    if len({link["id"] for link in links}) != len(links):
        raise ValueError("Duplicate presentation cross-reference")
    for link in links:
        _source(link["source"])
        if (
            not set(link["part_ids"]) <= ids
            or not set(link["group_ids"]) <= set(GROUP_IDS)
            or not {group_by_part[pid]["id"] for pid in link["part_ids"]} <= set(link["group_ids"])
        ):
            raise ValueError("Presentation cross-reference contains foreign IDs or groups")
    geometry_rows = {}
    if geometry is not None:
        identity = geometry["identity"]
        if (
            geometry["id"] != rp1_inspection.ID
            or identity["specification_sha256"] != rp1_inspection.PINS[rp1_inspection.SPEC]
            or identity["inspection_geometry_sha256"] != GEOMETRY_SHA256
            or {p["id"] for p in geometry["parts"]} != ids
        ):
            raise ValueError("Presentation inspection geometry tuple mismatch")
        geometry_rows = {p["id"]: p for p in geometry["parts"]}
    source_tuple = {
        "configuration_id": rp1_inspection.ID,
        "specification_sha256": rp1_inspection.PINS[rp1_inspection.SPEC],
        "inspection_geometry_sha256": GEOMETRY_SHA256 if geometry is not None else None,
    }
    parts = {}
    for pid, original in originals.items():
        group = group_by_part[pid]
        row = geometry_rows.get(pid)
        has_mesh = bool(row and row["mesh"])
        parts[pid] = {
            "id": pid,
            "group_id": group["id"],
            "source_parent": original["parent"],
            "source_parent_semantics": SOURCE_PARENT_SEMANTICS,
            "maturity": classification[pid]["maturity"],
            "has_mesh": has_mesh,
            "quantity": quantities.get(pid),
            "cross_link_ids": [link["id"] for link in links if pid in link["part_ids"]],
            "assembly_offset_m": offsets[group["id"]],
            "detail_offset_m": details.get(pid, [0.0, 0.0, 0.0]),
            "rigid_bundle_id": bundle_by_part.get(pid),
            "source_tuple": source_tuple,
            "inspection_shape_sha256": row["inspection_shape_sha256"] if row else None,
            "mesh_sha256": row["mesh"]["sha256"] if has_mesh and row else None,
            "presentation_sha256": CONFIG_SHA256,
        }
    public_groups = []
    for group in groups:
        public_groups.append(
            {
                **{
                    key: copy.deepcopy(group[key])
                    for key in ("id", "label", "description", "part_ids")
                },
                "record_count": len(group["part_ids"]),
                "mesh_count": sum(parts[pid]["has_mesh"] for pid in group["part_ids"]),
                "maturity_counts": dict(
                    Counter(parts[pid]["maturity"] for pid in group["part_ids"])
                ),
            }
        )
    result = {
        "id": ID,
        "schema_version": 1,
        "presentation_sha256": CONFIG_SHA256,
        "source": {"path": CONFIG, "sha256": CONFIG_SHA256},
        "source_tuple": source_tuple,
        "geometry_compatible": geometry is not None,
        "status": "Functional source grouping; staged display illustration, not physical attachment or clearance evidence",
        "groups": public_groups,
        "cross_links": copy.deepcopy(links),
        "breakdown": copy.deepcopy(breakdown),
        "parts": parts,
    }
    if (root / CONFIG).read_bytes() != raw:
        raise ValueError("Presentation source changed during projection")
    return result


def attach(document: dict[str, Any], root: Path, geometry: dict[str, Any] | None) -> None:
    """Add source-owned grouping without replacing parent, dimensions or source coordinates."""
    try:
        presentation = build(root, geometry=geometry)
    except (OSError, ValueError, KeyError, TypeError) as error:
        document["summary"]["presentation"] = {
            "id": ID,
            "schema_version": 1,
            "status": "unavailable",
            "reason": str(error),
            "geometry_compatible": False,
            "groups": [],
            "cross_links": [],
        }
        return
    document["summary"]["presentation"] = {
        key: value for key, value in presentation.items() if key != "parts"
    }
    for part in document["parts"]:
        part["representation"] = {
            **part["representation"],
            "presentation": presentation["parts"][part["id"]],
        }
