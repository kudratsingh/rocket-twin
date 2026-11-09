"""Narrow API-route compatibility; original archive registry/geometry remain pinned."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from scripts.wo04_prepare_archived_cad_preview import (
    CATALOG_EQUIVALENCE,
    CATALOG_EQUIVALENCE_SHA256,
    REGISTRY,
    REGISTRY_SHA256,
    verify_catalog_equivalence,
)

ROOT = Path(__file__).resolve().parents[1]


def packet():
    data = CATALOG_EQUIVALENCE.read_bytes()
    assert hashlib.sha256(data).hexdigest() == CATALOG_EQUIVALENCE_SHA256
    assert hashlib.sha256(REGISTRY.read_bytes()).hexdigest() == REGISTRY_SHA256
    return json.loads(data)


def test_exact_new_routes_leave_existing_module_and_catalogue_semantically_unchanged():
    proof = packet()
    source = (ROOT / "src/api/app.py").read_bytes()
    verify_catalog_equivalence(source, proof, proof["original"]["sha256"])
    assert proof["compatible_source"]["removed_new_route_functions"] == [
        "source_parts_bank",
        "source_part_definition",
    ]
    assert proof["geometry_or_asset_changed"] is False


def test_unrecorded_source_edit_is_rejected_even_if_it_only_adds_whitespace():
    proof = packet()
    with pytest.raises(ValueError, match="outside the exact recorded"):
        verify_catalog_equivalence(
            (ROOT / "src/api/app.py").read_bytes() + b"\n", proof, proof["original"]["sha256"]
        )


def test_changed_catalogue_is_rejected_independently_of_the_full_source_hash():
    proof = packet()
    source = (
        (ROOT / "src/api/app.py")
        .read_bytes()
        .replace(b"Archived G80 reference", b"Changed G80 reference", 1)
    )
    changed = copy.deepcopy(proof)
    changed["compatible_source"]["sha256"] = hashlib.sha256(source).hexdigest()
    with pytest.raises(ValueError, match="catalogue declaration changed"):
        verify_catalog_equivalence(source, changed, proof["original"]["sha256"])


def test_unrelated_existing_route_change_and_foreign_registry_are_rejected():
    proof = packet()
    source = (
        (ROOT / "src/api/app.py")
        .read_bytes()
        .replace(b'"mode": "read-only recorded inspection"', b'"mode": "changed inspection"', 1)
    )
    assert source != (ROOT / "src/api/app.py").read_bytes()
    changed = copy.deepcopy(proof)
    changed["compatible_source"]["sha256"] = hashlib.sha256(source).hexdigest()
    with pytest.raises(ValueError, match="Existing API behavior changed"):
        verify_catalog_equivalence(source, changed, proof["original"]["sha256"])
    foreign = copy.deepcopy(proof)
    foreign["registry"]["sha256"] = "b" * 64
    with pytest.raises(ValueError, match="outside the exact recorded"):
        verify_catalog_equivalence(
            (ROOT / "src/api/app.py").read_bytes(), foreign, proof["original"]["sha256"]
        )
