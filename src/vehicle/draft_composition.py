"""Pure source-fork exclusion intent; no effective vehicle or accounting credit.

The immutable base remains the complete saved source fork. Exclusion is a planning
annotation with unresolved function/evidence, never removal from its source ledger.
No store, filesystem, CAD, physics, resolver or network operation is performed.
"""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any, NoReturn

from src.api import parts_bank, rp1_inspection
from src.vehicle import design_drafts

# Exact server-canonical snapshots admitted by the frozen source-fork contract.
SOURCES = {
    "7f04cbeb5d4c2aa96a61fac41a1f2b0f1f52ad54e68c9dd3856f7363f52ded44": "bd69971e461251b843e24b4f2ec93c8d56e693bcbfa2d121697399a4510761cc",
    "754cc2ae24c3d3f20e53bc919457f5b09f3982d7fc4cf7610dea72d4c2368fd1": "7508b1f4361d3bada13ad23d11f6e997cda4aa3a476d33d847898425b2367e36",
}
KINDS = {"exclude-source-occurrence", "restore-source-occurrence"}
UNSUPPORTED = {
    "add": "Reusable local definition, units/frame, parameters, interfaces and complete counted inventory are not admitted; installed-reference assets are not reusable parts.",
    "replace": "Replacement function, interfaces, required hardware and complete candidate accounting/validation are not admitted.",
    "connect": "Named mating features, installation transforms, retention/process/tolerance and joint evidence are unavailable; tree parentage is not a physical connection.",
    "set-position": "Placement editing, candidate mass moments/fit and dependent-check invalidation are not admitted.",
    "set-parameter": "Allowlisted parameter editing, backend model generation and coupled invalidation are not admitted.",
    "resolve": "No effective candidate resolver or complete mass/inertia/geometry/physics admission is implemented.",
}
BASE_KEYS = {
    "schema_version",
    "draft_id",
    "source_sha256",
    "base_configuration_id",
    "parent_revision_sha256",
    "sequence",
    "created_at",
    "label",
    "notes",
    "operation",
    "readiness",
    "capabilities",
    "revision_sha256",
    "source",
}


class CompositionError(ValueError):
    """Stable recoverable command/admission error; contains no filesystem data."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        field: str | None = None,
        current_revision: str | None = None,
    ):
        self.code = code
        self.field = field
        self.current_revision = current_revision
        super().__init__(message)


def _reject(code: str, message: str, field: str | None = None) -> NoReturn:
    raise CompositionError(code, message, field=field)


def _saved(value: Any) -> dict[str, Any]:
    """Verify original Python canonical source/metadata, never a JS review copy."""
    try:
        if not isinstance(value, dict) or set(value) != BASE_KEYS:
            return _reject(
                "invalid_saved_revision", "An exact saved source-fork revision is required"
            )
        design_drafts._id(value["draft_id"])
        design_drafts._hash(value["revision_sha256"])
        design_drafts._hash(value["source_sha256"])
        design_drafts._text(value["label"], "label", 160, required=True)
        design_drafts._text(value["notes"], "notes", 8000)
        sequence = value["sequence"]
        if type(value["schema_version"]) is not int or value["schema_version"] != 1:
            return _reject("invalid_saved_revision", "Unsupported saved revision schema")
        if type(sequence) is not int or not 1 <= sequence <= 1000:
            return _reject("invalid_saved_revision", "Invalid saved revision sequence")
        if value["base_configuration_id"] != rp1_inspection.ID:
            return _reject(
                "source_unavailable", "Only the frozen current RP1 source fork is admitted"
            )
        if datetime.fromisoformat(value["created_at"]).utcoffset() is None:
            return _reject("invalid_saved_revision", "Saved timestamp must include its timezone")
        parent = value["parent_revision_sha256"]
        if sequence == 1:
            if parent is not None or value["operation"] != "fork_rp1":
                return _reject("invalid_saved_revision", "Invalid initial saved revision lineage")
        elif (
            design_drafts._hash(parent) == value["revision_sha256"]
            or value["operation"] != "save_metadata"
        ):
            return _reject("invalid_saved_revision", "Invalid saved metadata revision lineage")
        if (
            value["readiness"] != design_drafts.READINESS
            or any(
                value["readiness"][key] is not False
                for key in (
                    "resolved_candidate",
                    "simulation_eligible",
                    "engineering_accepted",
                    "flight_ready",
                )
            )
            or value["capabilities"] != {"save_metadata": True, "compose": False, "resolve": False}
            or value["capabilities"]["save_metadata"] is not True
            or value["capabilities"]["compose"] is not False
            or value["capabilities"]["resolve"] is not False
        ):
            return _reject(
                "invalid_saved_revision", "Saved source-fork readiness/capabilities differ"
            )
        unsigned = {
            key: item for key, item in value.items() if key not in ("revision_sha256", "source")
        }
        if parts_bank.digest(unsigned) != value["revision_sha256"]:
            return _reject("invalid_saved_revision", "Saved metadata revision hash mismatch")
        source = value["source"]
        source_sha = value["source_sha256"]
        if (
            not isinstance(source, dict)
            or source_sha not in SOURCES
            or parts_bank.digest(source) != source_sha
        ):
            return _reject("source_unavailable", "Frozen server source snapshot hash mismatch")
        bank = source["parts_bank"]
        identity = bank["identity"]
        expected_refs = [{"path": path, "sha256": pin} for path, pin in rp1_inspection.PINS.items()]
        if (
            source["configuration_id"] != rp1_inspection.ID
            or source["source_refs"] != expected_refs
            or source["parts_bank_revision_sha256"] != SOURCES[source_sha]
            or bank["revision_sha256"] != SOURCES[source_sha]
            or parts_bank.digest({k: v for k, v in bank.items() if k != "revision_sha256"})
            != bank["revision_sha256"]
            or bank["schema_version"] != 1
            or bank["configuration_id"] != rp1_inspection.ID
            or bank["id"] != parts_bank.ID
            or identity["specification_sha256"] != rp1_inspection.PINS[rp1_inspection.SPEC]
            or identity["definition_sha256"] != rp1_inspection.PINS[rp1_inspection.DEFINITION]
            or identity["record_sha256"] != rp1_inspection.PINS[rp1_inspection.RECORD]
            or bank["capabilities"] != {"editable": False, "draft_builder": False}
            or bank["summary"]["engineering_accepted"] is not False
            or bank["summary"]["flight_ready"] is not False
            or source["inspection"]["summary"]["flight_ready"] is not False
            or source["inspection"]["summary"]["inertia_status"] != "unavailable"
        ):
            return _reject(
                "source_unavailable", "Frozen RP1 bank/source identity or readiness differs"
            )
        instances, definitions = bank["instances"], bank["definitions"]
        ids = [row["id"] for row in instances]
        source_ids = [row["id"] for row in source["specification"]["parts"]]
        definition_ids = [row["source_part_id"] for row in definitions]
        if len(ids) != 55 or len(set(ids)) != 55 or source_ids != ids or definition_ids != ids:
            return _reject(
                "source_unavailable",
                "Exactly 55 unique original accounting occurrences are required",
            )
        for occurrence, definition in zip(instances, definitions, strict=True):
            if (
                occurrence["definition_id"] != definition["id"]
                or occurrence["definition_revision_sha256"] != definition["revision_sha256"]
                or type(occurrence["quantity"]) is not int
                or occurrence["quantity"] != 1
                or occurrence["counting_basis"] != "source_record"
                or definition["geometry"]["reusable_local_geometry"] is not False
            ):
                return _reject(
                    "source_unavailable",
                    "Source group accounting or installed-reference scope differs",
                )
        return copy.deepcopy(value)
    except CompositionError:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        return _reject(
            "invalid_saved_revision", "Saved source-fork data is malformed or unverifiable"
        )


def _assemble(base: dict[str, Any], excluded: list[str]) -> dict[str, Any]:
    bank = base["source"]["parts_bank"]
    occurrences = bank["instances"]
    definitions = {row["source_part_id"]: row for row in bank["definitions"]}
    ordered = [row["id"] for row in occurrences if row["id"] in excluded]
    removed_functions = []
    for occurrence in occurrences:
        if occurrence["id"] not in ordered:
            continue
        definition = definitions[occurrence["id"]]
        removed_functions.append(
            {
                "occurrence_id": occurrence["id"],
                "definition_id": definition["id"],
                "function": definition["function"],
                "status": "excluded_intent_function_unresolved",
                "source_occurrence": copy.deepcopy(occurrence),
                "source_evidence": {
                    key: copy.deepcopy(definition[key])
                    for key in (
                        "provenance",
                        "issues",
                        "physical_verification",
                        "interfaces_status",
                        "geometry",
                    )
                },
                "blocker": "Source function would be removed by this planning intent; no replacement, mass credit or effective candidate has been resolved",
            }
        )
    value: dict[str, Any] = {
        "schema_version": 1,
        "kind": "rp1-source-fork-planning-overlay",
        "status": "planning_intent_only",
        "base": copy.deepcopy(base),
        "source_revision_sha256": base["revision_sha256"],
        "source_sha256": base["source_sha256"],
        "excluded_occurrence_ids": ordered,
        "preview": {
            "source_occurrences": 55,
            "source_ledger_preserved": True,
            "exclusion_intents": len(ordered),
            "removed_functions": removed_functions,
            "effective_inventory": None,
            "reason": "Intent only; every original occurrence remains in the immutable source ledger",
        },
        "checks": {
            "status": "unavailable",
            "total_mass_kg": None,
            "mass_removal_credit_kg": None,
            "cg_m": None,
            "inertia_kg_m2": None,
            "reason": "No effective candidate, replacement-function accounting, CAD or engineering calculation is admitted",
        },
        "readiness": {
            "resolve_available": False,
            "resolved_candidate": False,
            "simulation_eligible": False,
            "engineering_accepted": False,
            "flight_ready": False,
            "blockers": [
                "Planning overlay is not an effective vehicle; exclusion never credits source mass",
                "Source estimates/conflicts, failed fin findings, unavailable installed geometry/inertia and all physical gates remain unchanged",
                *[row["blocker"] + ": " + row["occurrence_id"] for row in removed_functions],
            ],
        },
        "capabilities": {
            "exclude_source_occurrence": True,
            "restore_source_occurrence": True,
            **{key: False for key in UNSUPPORTED},
        },
    }
    value["revision_sha256"] = parts_bank.digest(value)
    return value


def create_overlay(saved_revision: dict[str, Any]) -> dict[str, Any]:
    """New independent planning value; no new UUID, timestamp, source or store write."""
    return _assemble(_saved(saved_revision), [])


def _validated_overlay(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("excluded_occurrence_ids"), list):
        return _reject("invalid_overlay", "A complete source-fork planning overlay is required")
    base = _saved(value.get("base"))
    try:
        actual_hash = parts_bank.digest({k: v for k, v in value.items() if k != "revision_sha256"})
    except (ValueError, TypeError):
        return _reject("invalid_overlay", "Overlay must contain finite JSON source/intent values")
    if actual_hash != value.get("revision_sha256"):
        return _reject("invalid_overlay", "Submitted overlay content hash differs")
    ids = [row["id"] for row in base["source"]["parts_bank"]["instances"]]
    excluded = value["excluded_occurrence_ids"]
    if any(not isinstance(pid, str) or pid not in ids for pid in excluded) or len(
        set(excluded)
    ) != len(excluded):
        return _reject("invalid_overlay", "Excluded intent IDs must be unique original occurrences")
    expected = _assemble(base, excluded)
    if value != expected:
        return _reject(
            "invalid_overlay", "Overlay content, derived blockers, source or revision hash differs"
        )
    return expected


def apply_command(overlay: dict[str, Any], command: dict[str, Any]) -> dict[str, Any]:
    """Guard one intent command against current overlay hash; return a fresh value.

    Duplicate exclusion errors. Restoring an already-included occurrence is a
    guarded no-op: same content/hash, independent returned object. Exclude then
    restore returns the initial content hash; no event/history store is implied.
    """
    current = _validated_overlay(overlay)
    if not isinstance(command, dict) or not isinstance(command.get("type"), str):
        return _reject("invalid_command", "An explicit intent command is required", "type")
    kind = command["type"]
    if kind in UNSUPPORTED:
        return _reject("unsupported_command", UNSUPPORTED[kind], "type")
    if kind not in KINDS:
        return _reject(
            "unknown_command", "Unknown planning command; no command was applied", "type"
        )
    if set(command) != {"type", "occurrence_id", "base_overlay_revision"}:
        return _reject(
            "invalid_command", "Only type, occurrence_id and base_overlay_revision are allowed"
        )
    try:
        design_drafts._hash(command["base_overlay_revision"])
    except ValueError:
        return _reject(
            "invalid_command",
            "A SHA-256 base overlay revision is required",
            "base_overlay_revision",
        )
    if command["base_overlay_revision"] != current["revision_sha256"]:
        raise CompositionError(
            "stale_overlay_revision",
            "Reload the overlay before applying this intent",
            field="base_overlay_revision",
            current_revision=current["revision_sha256"],
        )
    part_id = command["occurrence_id"]
    ids = [row["id"] for row in current["base"]["source"]["parts_bank"]["instances"]]
    if not isinstance(part_id, str) or part_id not in ids:
        return _reject(
            "unknown_occurrence", "Choose an exact original source occurrence ID", "occurrence_id"
        )
    excluded = current["excluded_occurrence_ids"]
    if kind == "exclude-source-occurrence":
        if part_id in excluded:
            return _reject(
                "duplicate_exclusion",
                "This occurrence already has an exclusion intent",
                "occurrence_id",
            )
        excluded.append(part_id)
    elif part_id not in excluded:
        return copy.deepcopy(current)
    else:
        excluded.remove(part_id)
    return _assemble(current["base"], excluded)
