"""Actual frozen test source fork, pure exclusion intent and no accounting credit."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest

from src.api.parts_bank import digest
from src.vehicle import design_drafts
from src.vehicle import draft_composition as planning

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "web/tests/fixtures/rp1-draft-library.json"


@pytest.fixture
def saved(tmp_path):
    isolated = tmp_path / "actual-test-fixture.json"
    shutil.copyfile(FIXTURE, isolated)
    data = isolated.read_bytes()
    assert (
        hashlib.sha256(data).hexdigest()
        == "b2339838a42a6426d535a533df7c021211362e3dd4e643a933e5c4562d0cded0"
    )
    fixture = json.loads(data)
    item = fixture["revisions"]["saved"]
    return {
        **item["metadata"],
        "revision_sha256": item["revision_sha256"],
        "source": fixture["source"],
    }


def command(overlay, kind, occurrence):
    return {
        "type": kind,
        "occurrence_id": occurrence,
        "base_overlay_revision": overlay["revision_sha256"],
    }


def resign_saved(value):
    value["revision_sha256"] = digest(
        {key: item for key, item in value.items() if key not in ("revision_sha256", "source")}
    )
    return value


def assert_unresolved(overlay):
    assert overlay["status"] == "planning_intent_only"
    assert overlay["preview"]["source_occurrences"] == 55
    assert overlay["preview"]["effective_inventory"] is None
    assert overlay["checks"]["status"] == "unavailable"
    assert all(
        overlay["checks"][key] is None
        for key in ("total_mass_kg", "mass_removal_credit_kg", "cg_m", "inertia_kg_m2")
    )
    assert all(
        overlay["readiness"][key] is False
        for key in (
            "resolve_available",
            "resolved_candidate",
            "simulation_eligible",
            "engineering_accepted",
            "flight_ready",
        )
    )
    assert (
        digest({key: item for key, item in overlay.items() if key != "revision_sha256"})
        == overlay["revision_sha256"]
    )


def test_exclude_restore_are_source_preserving_intent_with_function_and_evidence_blockers(saved):
    before = copy.deepcopy(saved)
    initial = planning.create_overlay(saved)
    assert initial == planning.create_overlay(saved)
    assert initial["base"] == saved
    assert initial["source_sha256"] == saved["source_sha256"]
    assert initial["source_revision_sha256"] == saved["revision_sha256"]
    assert_unresolved(initial)
    excluded = planning.apply_command(
        initial, command(initial, "exclude-source-occurrence", "fin_set")
    )
    assert saved == before and initial["excluded_occurrence_ids"] == []
    assert excluded["excluded_occurrence_ids"] == ["fin_set"]
    original = next(
        row for row in saved["source"]["parts_bank"]["instances"] if row["id"] == "fin_set"
    )
    assert original["quantity"] == 1 and original["group_count"] == 3
    removed = excluded["preview"]["removed_functions"][0]
    assert removed["source_occurrence"] == original
    assert removed["function"]
    assert removed["status"] == "excluded_intent_function_unresolved"
    assert removed["source_evidence"]["provenance"]
    assert removed["source_evidence"]["physical_verification"] == "open"
    assert removed["source_evidence"]["geometry"]["reusable_local_geometry"] is False
    assert any("fin_set" in blocker for blocker in excluded["readiness"]["blockers"])
    assert excluded["base"] == before
    assert len(excluded["base"]["source"]["parts_bank"]["instances"]) == 55
    assert excluded["base"]["source"]["inspection"]["summary"]["physical_inertia"] is None
    assert (
        excluded["base"]["source"]["inspection"]["evidence"]["fin"][
            "bonded_panel_stress_screen_pass_only"
        ]
        is False
    )
    assert_unresolved(excluded)
    restored = planning.apply_command(
        excluded, command(excluded, "restore-source-occurrence", "fin_set")
    )
    assert restored == initial
    assert restored is not initial
    assert restored["base"] is not saved
    assert_unresolved(restored)


def test_multiple_exclusions_are_source_ordered_not_command_order_and_keep_original_placements(
    saved,
):
    start = planning.create_overlay(saved)
    left = planning.apply_command(
        start, command(start, "exclude-source-occurrence", "motor_retainer")
    )
    left = planning.apply_command(left, command(left, "exclude-source-occurrence", "fin_set"))
    right = planning.apply_command(start, command(start, "exclude-source-occurrence", "fin_set"))
    right = planning.apply_command(
        right, command(right, "exclude-source-occurrence", "motor_retainer")
    )
    assert left == right
    assert left["excluded_occurrence_ids"] == ["fin_set", "motor_retainer"]
    assert (
        left["base"]["source"]["parts_bank"]["instances"]
        == saved["source"]["parts_bank"]["instances"]
    )
    retainer = next(
        row
        for row in left["preview"]["removed_functions"]
        if row["occurrence_id"] == "motor_retainer"
    )
    assert retainer["source_evidence"]["issues"][0]["id"] == "retainer_product_conflict"
    assert_unresolved(left)


def test_stale_duplicate_unknown_ids_and_unknown_fields_fail_without_mutating(saved):
    start = planning.create_overlay(saved)
    changed = planning.apply_command(start, command(start, "exclude-source-occurrence", "body"))
    before = copy.deepcopy(changed)
    with pytest.raises(planning.CompositionError) as stale:
        planning.apply_command(changed, command(start, "restore-source-occurrence", "body"))
    assert stale.value.code == "stale_overlay_revision"
    assert stale.value.current_revision == changed["revision_sha256"]
    for payload, code in [
        (command(changed, "exclude-source-occurrence", "body"), "duplicate_exclusion"),
        (command(changed, "exclude-source-occurrence", "../body"), "unknown_occurrence"),
        (command(changed, "restore-source-occurrence", "unknown"), "unknown_occurrence"),
        (
            {
                **command(changed, "exclude-source-occurrence", "motor"),
                "base_overlay_revision": "bad",
            },
            "invalid_command",
        ),
        (
            {**command(changed, "exclude-source-occurrence", "motor"), "quantity": 0},
            "invalid_command",
        ),
        ({"type": "fly"}, "unknown_command"),
        ({"type": None}, "invalid_command"),
    ]:
        with pytest.raises(planning.CompositionError) as error:
            planning.apply_command(changed, payload)
        assert error.value.code == code
        assert changed == before


def test_restore_already_included_is_guarded_noop_and_return_values_are_independent(saved):
    start = planning.create_overlay(saved)
    noop = planning.apply_command(start, command(start, "restore-source-occurrence", "body"))
    assert noop == start and noop is not start
    noop["base"]["source"]["parts_bank"]["instances"][0]["quantity"] = 99
    assert start["base"]["source"]["parts_bank"]["instances"][0]["quantity"] == 1
    assert saved["source"]["parts_bank"]["instances"][0]["quantity"] == 1
    with pytest.raises(planning.CompositionError, match="Reload"):
        planning.apply_command(
            start,
            {
                **command(start, "restore-source-occurrence", "body"),
                "base_overlay_revision": "0" * 64,
            },
        )


@pytest.mark.parametrize("kind", list(planning.UNSUPPORTED))
def test_future_commands_report_specific_missing_admission(saved, kind):
    overlay = planning.create_overlay(saved)
    with pytest.raises(planning.CompositionError) as error:
        planning.apply_command(overlay, {"type": kind})
    assert error.value.code == "unsupported_command"
    assert str(error.value) == planning.UNSUPPORTED[kind]
    assert overlay["excluded_occurrence_ids"] == []
    assert_unresolved(overlay)


def test_tampered_saved_metadata_source_schema_ids_readiness_and_ledger_are_rejected(saved):
    def corrupt_source(value, change):
        change(value["source"])
        value["source_sha256"] = digest(value["source"])
        resign_saved(value)

    mutations = [
        lambda row: row.update(label="unsaved without metadata hash"),
        lambda row: resign_saved({**row, "schema_version": True}),
        lambda row: resign_saved({**row, "sequence": True}),
        lambda row: resign_saved({**row, "draft_id": "../owner"}),
        lambda row: resign_saved({**row, "base_configuration_id": "historical"}),
        lambda row: resign_saved({**row, "parent_revision_sha256": "invalid"}),
        lambda row: resign_saved(
            {**row, "capabilities": {"save_metadata": True, "compose": True, "resolve": False}}
        ),
        lambda row: resign_saved({**row, "readiness": {**row["readiness"], "flight_ready": True}}),
        lambda row: resign_saved({**row, "readiness": {**row["readiness"], "flight_ready": 0}}),
        lambda row: corrupt_source(row, lambda source: source["parts_bank"]["instances"].pop()),
        lambda row: corrupt_source(
            row,
            lambda source: source["parts_bank"]["instances"][1].update(
                id=source["parts_bank"]["instances"][0]["id"]
            ),
        ),
        lambda row: corrupt_source(
            row, lambda source: source["parts_bank"]["instances"][0].update(quantity=0)
        ),
        lambda row: corrupt_source(
            row, lambda source: source["specification"].update(name="foreign source metadata")
        ),
        lambda row: row.update(source=None),
    ]
    for mutate in mutations:
        value = copy.deepcopy(saved)
        result = mutate(value)
        if isinstance(result, dict):
            value = result
        with pytest.raises(planning.CompositionError):
            planning.create_overlay(value)


def test_tampered_overlay_hash_source_preview_duplicates_and_false_gates_rejected(saved):
    original = planning.create_overlay(saved)
    changed = planning.apply_command(
        original, command(original, "exclude-source-occurrence", "body")
    )
    for mutate in [
        lambda row: row.update(revision_sha256="0" * 64),
        lambda row: row["base"].update(notes="not the saved metadata"),
        lambda row: row["excluded_occurrence_ids"].append("body"),
        lambda row: row["preview"].update(effective_inventory=[]),
        lambda row: row["preview"].update(source_occurrences=54),
        lambda row: row["checks"].update(total_mass_kg=0),
        lambda row: row["readiness"].update(flight_ready=True),
        lambda row: row["readiness"].update(flight_ready=0),
    ]:
        value = copy.deepcopy(changed)
        mutate(value)
        with pytest.raises(planning.CompositionError):
            planning.apply_command(value, command(value, "restore-source-occurrence", "body"))


def test_pure_commands_never_open_files_or_call_a_store(saved, monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("Planning overlay must not perform persistence")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(design_drafts.DraftStore, "read", forbidden)
    monkeypatch.setattr(design_drafts.DraftStore, "fork_rp1", forbidden)
    monkeypatch.setattr(design_drafts.DraftStore, "save_metadata", forbidden)
    overlay = planning.create_overlay(saved)
    for kind in ("exclude-source-occurrence", "restore-source-occurrence"):
        overlay = planning.apply_command(overlay, command(overlay, kind, "rp1_kevlar_wrap"))
    assert overlay["excluded_occurrence_ids"] == []
