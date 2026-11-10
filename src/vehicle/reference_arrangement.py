"""Unsaved geometry-reference display arrangements; no inventory, CAD or physics.

Only the two exact reference-local-v1 definitions are admitted. The Python hash
is an opaque content guard, not persistence, history or cross-tab authority.
"""

from __future__ import annotations

import copy
import re
from decimal import Decimal
from typing import Any, NoReturn

from src.api.parts_bank import digest

ID = "reference-arrangement-v1"
CATALOG_REVISION = "8f6b7bf2f0dcc8dfb2714ba7a28688c820869dc3045060aba6ea5901983b7748"
DEFINITION_REVISIONS = {
    "reference-local-v1:motor-tube-nominal": "fd6c666dfed5d79ed44ed126b85d1de7dca87c1210165808b44f270e2ce2a42c",
    "reference-local-v1:aft-annulus-nominal": "158150615a9c291ce12b3320d535c11151a564d7ad176dda9ca9693025a5d710",
}
INSTANCE_IDS = {reference: f"{ID}:{reference.split(':')[1]}" for reference in DEFINITION_REVISIONS}
TINY_KEYS = {"reference_id", "definition_revision_sha256", "translation_mm"}
INSTANCE_KEYS = TINY_KEYS | {
    "id",
    "quantity",
    "rotation_quaternion_xyzw",
    "scale",
    "installed_transform",
    "scope",
    "added_to_source",
    "added_to_vehicle",
}


class ArrangementError(ValueError):
    """A bounded arrangement request cannot be admitted."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        field: str | None = None,
        current_revision: str | None = None,
    ) -> None:
        self.code = code
        self.field = field
        self.current_revision = current_revision
        super().__init__(message)


def _reject(code: str, message: str, field: str | None = None) -> NoReturn:
    raise ArrangementError(code, message, field=field)


def _hash(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _catalog(catalog: Any) -> dict[str, Any]:
    try:
        if type(catalog) is not dict:
            return _reject("invalid_catalog", "An exact registered reference catalog is required")
        core = {
            key: item
            for key, item in catalog.items()
            if key not in ("revision_sha256", "availability")
        }
        if catalog["revision_sha256"] != CATALOG_REVISION or digest(core) != CATALOG_REVISION:
            return _reject(
                "invalid_catalog",
                "Reference catalog/source content differs from its pinned revision",
            )
        definitions = catalog["definitions"]
        if [row["id"] for row in definitions] != list(DEFINITION_REVISIONS):
            return _reject("invalid_catalog", "Only the two exact nominal references are admitted")
        for row in definitions:
            if (
                row["revision_sha256"] != DEFINITION_REVISIONS[row["id"]]
                or digest({key: item for key, item in row.items() if key != "revision_sha256"})
                != row["revision_sha256"]
            ):
                return _reject("invalid_catalog", "Reference definition identity differs")
        availability = catalog["availability"]
        if type(availability) is not dict or set(availability) != set(DEFINITION_REVISIONS):
            return _reject("invalid_catalog", "Separate reference cache availability is required")
        for state in availability.values():
            missing = state["missing_formats"]
            if type(missing) is not list or missing not in ([], ["step"], ["glb"], ["step", "glb"]):
                return _reject("invalid_catalog", "Reference cache availability is malformed")
            expected = {
                "status": "unavailable" if missing else "verified_registered_local_cache",
                "missing_formats": missing,
                "geometry_available": not missing,
                "public_url_cache_verified": False,
                "generation_attempted": False,
                "reason": (
                    "Required local cache absent; no regeneration"
                    if missing
                    else "Exact existing STEP/GLB bytes verified; no new CAD readback or physical acceptance"
                ),
            }
            if digest(state) != digest(expected):
                return _reject(
                    "invalid_catalog", "Reference cache status differs; no geometry is inferred"
                )
        return copy.deepcopy(catalog)
    except ArrangementError:
        raise
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
        return _reject("invalid_catalog", "Reference catalog is malformed or unverifiable")


def _translation(value: Any) -> list[int | float]:
    if type(value) is not list or len(value) != 3:
        return _reject(
            "invalid_translation",
            "translation_mm must contain exactly three numbers",
            "translation_mm",
        )
    result: list[int | float] = []
    for item in value:
        if type(item) not in (int, float):
            return _reject(
                "invalid_translation",
                "Translation coordinates must be finite numbers, never booleans",
                "translation_mm",
            )
        number = Decimal(str(item))
        if not number.is_finite() or abs(number) > 500:
            return _reject(
                "invalid_translation",
                "Each translation coordinate must be finite and within ±500 mm",
                "translation_mm",
            )
        normalized = number.normalize()
        exponent = normalized.as_tuple().exponent
        if not isinstance(exponent, int) or exponent < -3:
            return _reject(
                "invalid_translation",
                "Translation input permits at most three decimal places; this is not a tolerance",
                "translation_mm",
            )
        result.append(int(number) if number == number.to_integral_value() else float(number))
    return result


def _tiny(value: Any) -> dict[str, Any]:
    if type(value) is not dict or set(value) != TINY_KEYS:
        return _reject(
            "invalid_instance",
            "Only exact reference identity, revision and translation are accepted",
        )
    reference = value["reference_id"]
    if not isinstance(reference, str) or reference not in DEFINITION_REVISIONS:
        return _reject(
            "unknown_reference",
            "Choose one of the two registered nominal reference IDs",
            "reference_id",
        )
    if value["definition_revision_sha256"] != DEFINITION_REVISIONS[reference]:
        return _reject(
            "definition_revision_mismatch",
            "The exact registered definition revision is required",
            "definition_revision_sha256",
        )
    return {
        "reference_id": reference,
        "definition_revision_sha256": DEFINITION_REVISIONS[reference],
        "translation_mm": _translation(value["translation_mm"]),
    }


def _assemble(catalog: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_reference = {row["reference_id"]: row for row in rows}
    instances = [
        {
            **by_reference[reference],
            "id": INSTANCE_IDS[reference],
            "quantity": 1,
            "rotation_quaternion_xyzw": [0, 0, 0, 1],
            "scale": [1, 1, 1],
            "installed_transform": None,
            "scope": "arrangement_display_occurrence_only",
            "added_to_source": False,
            "added_to_vehicle": False,
        }
        for reference in DEFINITION_REVISIONS
        if reference in by_reference
    ]
    result = {
        "schema_version": 1,
        "id": ID,
        "status": "geometry_only_unsaved",
        "catalog_id": catalog["id"],
        "catalog_revision_sha256": catalog["revision_sha256"],
        "source_pins": copy.deepcopy(catalog["source_pins"]),
        "definition_revisions": copy.deepcopy(DEFINITION_REVISIONS),
        "frame": {
            "units": "mm",
            "origin": "uninstalled_arrangement_origin",
            "axes": "Parallel to registered local CAD X/Y/Z; +Z along nominal part length",
        },
        "instances": instances,
        "physical_inventory": None,
        "installed_transform": None,
        "geometry_assets_embedded": False,
        "cache_availability_in_plan": False,
        "checks": {
            "status": "unavailable",
            "total_mass_kg": None,
            "mass_credit_kg": None,
            "cg_mm": None,
            "inertia_kg_m2": None,
            "procurement_cost_usd": None,
            "results": None,
        },
        "readiness": {
            "resolved_candidate": False,
            "simulation_eligible": False,
            "engineering_accepted": False,
            "physically_verified": False,
            "flight_ready": False,
            "mating_accepted": False,
            "connect_available": False,
        },
        "limits": [
            "Uninstalled geometry arrangement only; source inventory and vehicle are unchanged",
            "Translation granularity is input precision, not stock or mating tolerance",
            "No physical identity, fit, collision, load, mass or inertia result is calculated",
            "Read fresh catalog availability separately; missing assets remain unavailable",
            "Content hash is an opaque Python guard, not saved history or cross-tab authority",
        ],
    }
    result["revision_sha256"] = digest(result)
    return result


def reconstruct_plan(catalog: Any, instances: Any) -> dict[str, Any]:
    """Reconstruct from at most two tiny rows, never client source/transform JSON."""
    admitted = _catalog(catalog)
    if type(instances) is not list or len(instances) > 2:
        return _reject(
            "instance_limit", "At most two distinct registered reference occurrences are allowed"
        )
    rows = [_tiny(row) for row in instances]
    ids = [row["reference_id"] for row in rows]
    if len(set(ids)) != len(ids):
        return _reject(
            "duplicate_reference", "Only one display occurrence per exact reference is allowed"
        )
    return _assemble(admitted, rows)


def create_plan(catalog: Any) -> dict[str, Any]:
    """Create an empty unsaved geometry-only plan; perform no I/O or generation."""
    return reconstruct_plan(catalog, [])


def admit_plan(catalog: Any, plan: Any) -> dict[str, Any]:
    """Reject changed derived fields, gates, transforms, source pins or hash."""
    if (
        type(plan) is not dict
        or type(plan.get("instances")) is not list
        or len(plan["instances"]) > 2
    ):
        return _reject("invalid_plan", "A bounded canonical arrangement plan is required")
    rows = []
    for row in plan["instances"]:
        if type(row) is not dict or set(row) != INSTANCE_KEYS:
            return _reject("invalid_plan", "Arrangement occurrence fields differ")
        rows.append({key: row[key] for key in TINY_KEYS})
    expected = reconstruct_plan(catalog, rows)
    try:
        if not _hash(plan.get("revision_sha256")) or digest(plan) != digest(expected):
            return _reject(
                "invalid_plan", "Arrangement content, fixed transforms or revision hash differs"
            )
    except (ValueError, TypeError, OverflowError):
        return _reject("invalid_plan", "Arrangement content cannot be verified")
    return expected


def apply_command(catalog: Any, plan: Any, command: Any) -> dict[str, Any]:
    """Apply one guarded command; translating to the same location is a fresh no-op."""
    current = admit_plan(catalog, plan)
    if type(command) is not dict or not isinstance(command.get("type"), str):
        return _reject("invalid_command", "An explicit arrangement command is required", "type")
    kind = command["type"]
    fields = {
        "add-reference": {
            "type",
            "reference_id",
            "definition_revision_sha256",
            "base_plan_revision",
        },
        "translate-reference": {"type", "instance_id", "translation_mm", "base_plan_revision"},
    }
    if kind not in fields:
        return _reject(
            "unsupported_command",
            "Only add-reference and translate-reference display commands are supported; no Replace, Connect, scale, rotation or physical composition",
            "type",
        )
    if set(command) != fields[kind] or not _hash(command.get("base_plan_revision")):
        return _reject("invalid_command", "Command fields or base plan SHA-256 differ")
    if command["base_plan_revision"] != current["revision_sha256"]:
        raise ArrangementError(
            "stale_plan_revision",
            "Reconstruct the current unsaved plan before applying this command",
            field="base_plan_revision",
            current_revision=current["revision_sha256"],
        )
    rows = [{key: row[key] for key in TINY_KEYS} for row in current["instances"]]
    if kind == "add-reference":
        added = _tiny(
            {
                "reference_id": command["reference_id"],
                "definition_revision_sha256": command["definition_revision_sha256"],
                "translation_mm": [0, 0, 0],
            }
        )
        if any(row["reference_id"] == added["reference_id"] for row in rows):
            return _reject(
                "duplicate_reference",
                "This reference already has its one display occurrence",
                "reference_id",
            )
        rows.append(added)
    else:
        instance_id = command["instance_id"]
        selected = next(
            (row for row in rows if INSTANCE_IDS[row["reference_id"]] == instance_id), None
        )
        if not isinstance(instance_id, str) or selected is None:
            return _reject(
                "unknown_instance",
                "Choose an existing arrangement display occurrence",
                "instance_id",
            )
        selected["translation_mm"] = _translation(command["translation_mm"])
    return reconstruct_plan(catalog, rows)
