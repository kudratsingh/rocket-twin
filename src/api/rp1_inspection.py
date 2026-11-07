"""Read-only AD1-v2 inspection document from frozen source and saved evidence.

No vehicle model is instantiated and no geometry, mass, or flight solve is run.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

ID = "G80-F2-RP1-AD1-definition-v2"
SPEC = "configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml"
DEFINITION = "configs/studies/rp1-attachment-definition-v2.yaml"
RECORD = "runs/wo03-rp1-attachment-definition-20261103-v2/record.json"
PINS = {
    SPEC: "811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660",
    DEFINITION: "e9db49f2cafc89b1f77bf9d7396434297bc8bb8754085fdcf74d3b0242012555",
    RECORD: "bc349a24fe1cfaa4d883b9e00dc5b75387638a7be5cd4b05d9f32112ee8bd95b",
}


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read(root: Path) -> dict[str, bytes]:
    data = {path: (root / path).read_bytes() for path in PINS}
    if any(_digest(data[path]) != expected for path, expected in PINS.items()):
        raise ValueError("AD1 source hash mismatch")
    return data


def catalog_entry(root: Path) -> dict[str, Any]:
    """Expose this source only when all pinned records validate."""
    build(root)
    return {
        "id": ID,
        "name": "G80 RP1 / AD1 v2",
        "label": "G80 RP1 / AD1 v2 — source definition",
        "role": "Unadopted test definition; no matching complete CAD or run",
        "status": "engineering acceptance open",
        "candidate": True,
        "design_status": "unadopted",
        "available": True,
    }


def build(root: Path) -> dict[str, Any]:
    """Prepare source envelopes and archived results; fail closed on provenance drift."""
    data = _read(root)
    spec = yaml.safe_load(data[SPEC])
    definition = yaml.safe_load(data[DEFINITION])
    record = json.loads(data[RECORD])
    if (
        spec["id"] != ID
        or definition["id"] != ID
        or record["identity"] != ID
        or definition["adopted"] is not False
        or record["adopted"] is not False
        or record["sources"].get(SPEC) != PINS[SPEC]
        or record["sources"].get(DEFINITION) != PINS[DEFINITION]
    ):
        raise ValueError("AD1 identity or source linkage mismatch")
    originals = spec["parts"]
    ids = [p["id"] for p in originals]
    if len(ids) != 55 or len(set(ids)) != 55:
        raise ValueError("AD1 source part coverage mismatch")
    source = {"spec_path": SPEC, "spec_inputs": [{"path": SPEC, "sha256": PINS[SPEC]}]}
    parts = []
    for part in originals:
        geometry = part.get("geometry")
        location = {"position_m": part["position_m"]}
        if "lateral_offset_m" in part:
            location["lateral_offset_m"] = part["lateral_offset_m"]
        if "explode_offset" in part:
            location["explode_offset"] = part["explode_offset"]
        row = {
            "id": part["id"],
            "name": part["id"].replace("_", " ").capitalize(),
            "type": part["type"],
            "parent": part.get("parent"),
            "position_m": part["position_m"],
            "location": location,
            "geometry": geometry,
            "dimensions": geometry,
            "material": part["material"],
            "learn": part["learn"],
            "function": part.get("engineering", {}).get("function", part["learn"]),
            "estimate": part.get("estimate", True),
            "build": part.get("build"),
            "manufacturing": part.get("build"),
            "engineering": part.get("engineering"),
            "electrical": part.get("electrical"),
            "cad": part.get("cad"),
            "cite": part.get("cite"),
            "source": source,
            "raw": part,
            "mass_basis": "Source recorded estimate; not a measured part mass",
            "evidence_status": {"provenance": "source estimate", "physical_verification": "open"},
            "representation": {
                "role": "source envelope / concept",
                "description": "Simplified source dimensions; not manufacturing CAD or measured geometry.",
            },
            "outer_body": part["id"] in ("nose", "body", "upper_body"),
            "nose": part["id"] == "nose",
        }
        failures = part.get("engineering", {}).get("failure_modes")
        if isinstance(failures, list) and all(isinstance(item, str) for item in failures):
            row["failure_modes"] = failures
        if "mass_kg" in part:
            row["mass_kg"] = part["mass_kg"]
        else:
            row["mass_basis"] = "Unavailable in source"
        parts.append(row)
    document = {
        "snapshot_only": True,
        "id": ID,
        "name": spec["name"],
        "label": "G80 RP1 / AD1 v2 — source definition",
        "role": "Unadopted engineering test definition",
        "status": "Source envelope / concept; engineering acceptance open",
        "description": "Exact frozen specification and saved AD1 evidence; no matching complete assembly CAD or replay.",
        "identity": {
            "configuration_id": ID,
            "specification_path": SPEC,
            "specification_sha256": PINS[SPEC],
            "resolved_spec_sha256": None,
            "cad_revision_sha256": None,
            "record_path": RECORD,
            "record_sha256": PINS[RECORD],
            "definition_path": DEFINITION,
            "definition_sha256": PINS[DEFINITION],
        },
        "geometry": {
            "length_m": spec["airframe"]["length_m"],
            "diameter_m": spec["airframe"]["body_diameter_m"],
        },
        "airframe": spec["airframe"],
        "parts": parts,
        "motor": spec.get("motor"),
        "summary": {
            "length_m": spec["airframe"]["length_m"],
            "diameter_m": spec["airframe"]["body_diameter_m"],
            "engineering_acceptance": "open",
            "flight_ready": False,
            "mass_basis": "Saved AD1 cases are estimates with separate 55 g and 68 g nylon probes and full 50 g growth; not a measured vehicle.",
            "mass_cases": record["cases"],
            "saved_static_reference": record["rocketpy_static_reference"],
            "physical_inertia": record["physical_inertia"],
            "inertia_status": "unavailable",
            "source": {"path": RECORD, "sha256": PINS[RECORD]},
        },
        "evidence": {
            "specification_basis": "Direct frozen source YAML bytes; no new canonical vehicle resolution.",
            "axis": spec["axis"],
            "drawing_datum": definition["route"]["datum"],
            "definition": {"path": DEFINITION, "sha256": PINS[DEFINITION]},
            "record": {"path": RECORD, "sha256": PINS[RECORD]},
            "connections": record["recovery_connections"],
            "cord_geometry": record["cord_geometry"],
            "fin": record["fin"],
            "status": record["decision"],
            "representation": "Source envelopes and concepts only; not complete CAD or flight qualification.",
        },
        "engineering_open": [
            "Finished attachment strength and displacement",
            "Whole-body inertia and installed geometry",
            "Thermal, recovery and installed flutter",
            "Physical inspection, WO-10 and flight release",
        ],
        "mass_samples": [],
    }
    if _read(root) != data:
        raise ValueError("AD1 source changed during export")
    return document
