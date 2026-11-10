"""Pure two-reference arrangements, exact cold source catalog and no physics."""

from __future__ import annotations

import builtins
import copy
import math
import shutil
from pathlib import Path

import pytest

from src.api.parts_bank import digest
from src.vehicle import reference_arrangement as arrangement
from src.vehicle import reference_parts

ROOT = Path(__file__).resolve().parents[1]
TUBE, RING = arrangement.DEFINITION_REVISIONS


@pytest.fixture
def catalog(tmp_path):
    # A real source-only build: ignored output is neither required nor constructed.
    for relative in reference_parts.SOURCE_PINS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    for relative in reference_parts.ASSET_PATHS:
        (tmp_path / relative).parent.mkdir(parents=True, exist_ok=True)
    result = reference_parts.build(tmp_path)
    assert all(state["status"] == "unavailable" for state in result["availability"].values())
    return result


def add(plan, reference=TUBE):
    return {
        "type": "add-reference",
        "reference_id": reference,
        "definition_revision_sha256": arrangement.DEFINITION_REVISIONS[reference],
        "base_plan_revision": plan["revision_sha256"],
    }


def translate(plan, coordinates, reference=TUBE):
    return {
        "type": "translate-reference",
        "instance_id": arrangement.INSTANCE_IDS[reference],
        "translation_mm": coordinates,
        "base_plan_revision": plan["revision_sha256"],
    }


def tiny(reference=TUBE, coordinates=None):
    return {
        "reference_id": reference,
        "definition_revision_sha256": arrangement.DEFINITION_REVISIONS[reference],
        "translation_mm": [0, 0, 0] if coordinates is None else coordinates,
    }


def assert_unresolved(plan):
    assert plan["status"] == "geometry_only_unsaved"
    assert plan["physical_inventory"] is None and plan["installed_transform"] is None
    assert plan["checks"]["status"] == "unavailable"
    assert plan["checks"]["mass_credit_kg"] is None
    assert all(value is None for key, value in plan["checks"].items() if key != "status")
    assert all(value is False for value in plan["readiness"].values())
    assert plan["geometry_assets_embedded"] is False
    assert plan["cache_availability_in_plan"] is False
    assert plan["catalog_revision_sha256"] == arrangement.CATALOG_REVISION
    assert plan["definition_revisions"] == arrangement.DEFINITION_REVISIONS
    assert (
        digest({key: value for key, value in plan.items() if key != "revision_sha256"})
        == plan["revision_sha256"]
    )
    for row in plan["instances"]:
        assert row["quantity"] == 1
        assert row["rotation_quaternion_xyzw"] == [0, 0, 0, 1]
        assert row["scale"] == [1, 1, 1] and row["installed_transform"] is None
        assert row["added_to_source"] is False and row["added_to_vehicle"] is False
        assert row["scope"] == "arrangement_display_occurrence_only"


def test_add_translate_two_references_preserves_catalog_and_inputs_without_io(catalog, monkeypatch):
    original = copy.deepcopy(catalog)

    def forbidden(*args, **kwargs):
        raise AssertionError("Pure arrangement functions may not read files or execute CAD")

    monkeypatch.setattr(builtins, "open", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    empty = arrangement.create_plan(catalog)
    assert empty == arrangement.create_plan(catalog) and empty["instances"] == []
    first = arrangement.apply_command(catalog, empty, add(empty))
    assert empty["instances"] == []
    assert first["instances"][0]["translation_mm"] == [0, 0, 0]
    assert first["instances"][0]["id"] == arrangement.INSTANCE_IDS[TUBE]
    before = copy.deepcopy(first)
    command = translate(first, [500, -500, 0.125])
    copied_command = copy.deepcopy(command)
    moved = arrangement.apply_command(catalog, first, command)
    assert moved["instances"][0]["translation_mm"] == [500, -500, 0.125]
    assert command == copied_command and first == before
    complete = arrangement.apply_command(catalog, moved, add(moved, RING))
    assert len(complete["instances"]) == 2
    assert [row["reference_id"] for row in complete["instances"]] == [TUBE, RING]
    for plan in (empty, first, moved, complete):
        assert_unresolved(plan)
        assert arrangement.admit_plan(catalog, plan) == plan
        assert plan["source_pins"] == catalog["source_pins"]
    complete["source_pins"].clear()
    complete["instances"][0]["translation_mm"][0] = 4
    assert catalog == original and first == before


def test_reconstruction_is_source_ordered_and_normalizes_numbers_and_negative_zero(catalog):
    forward = arrangement.reconstruct_plan(catalog, [tiny(TUBE, [1.0, -0.0, 0.001]), tiny(RING)])
    reverse = arrangement.reconstruct_plan(catalog, [tiny(RING), tiny(TUBE, [1, 0, 0.001])])
    assert forward == reverse
    assert forward["instances"][0]["translation_mm"] == [1, 0, 0.001]
    assert all(type(value) is int for value in forward["instances"][0]["translation_mm"][:2])
    again = arrangement.apply_command(catalog, forward, translate(forward, [1.0, -0.0, 0.001]))
    assert again == forward and again is not forward
    assert again["instances"] is not forward["instances"]
    moved = arrangement.apply_command(catalog, again, translate(again, [2, 0, 0]))
    restored = arrangement.apply_command(catalog, moved, translate(moved, [1, 0, 0.001]))
    assert restored == forward  # Content identity, not monotonic event history.


def test_actual_known_cache_state_does_not_change_plan_identity(catalog):
    actual = reference_parts.build(ROOT)  # Existing exact paths only, hot or cold.
    assert arrangement.create_plan(actual) == arrangement.create_plan(catalog)
    assert arrangement.reconstruct_plan(actual, [tiny()]) == arrangement.reconstruct_plan(
        catalog, [tiny()]
    )
    assert all(row["readiness"]["add_instance_api"] is False for row in actual["definitions"])


@pytest.mark.parametrize(
    "coordinates",
    [
        [True, 0, 0],
        [0, False, 0],
        [math.inf, 0, 0],
        [math.nan, 0, 0],
        [-math.inf, 0, 0],
        [500.001, 0, 0],
        [-500.001, 0, 0],
        [0.0001, 0, 0],
        [1.2345, 0, 0],
        ["1", 0, 0],
        [None, 0, 0],
        [0, 0],
        [0, 0, 0, 0],
        (0, 0, 0),
        None,
    ],
)
def test_invalid_translation_never_rounds_clamps_or_admits(catalog, coordinates):
    plan = arrangement.reconstruct_plan(catalog, [tiny()])
    before = copy.deepcopy(plan)
    with pytest.raises(arrangement.ArrangementError) as failure:
        arrangement.apply_command(catalog, plan, translate(plan, coordinates))
    assert failure.value.code == "invalid_translation"
    assert plan == before


def test_stale_bad_base_duplicate_foreign_reference_revision_and_third_rejected(catalog):
    empty = arrangement.create_plan(catalog)
    first = arrangement.apply_command(catalog, empty, add(empty))
    with pytest.raises(arrangement.ArrangementError) as stale:
        arrangement.apply_command(catalog, first, add(empty, RING))
    assert stale.value.code == "stale_plan_revision"
    assert stale.value.current_revision == first["revision_sha256"]
    for mutation, code in [
        ({"base_plan_revision": "bad"}, "invalid_command"),
        ({"reference_id": "../../foreign"}, "unknown_reference"),
        ({"definition_revision_sha256": "0" * 64}, "definition_revision_mismatch"),
        ({"scale": [2, 2, 2]}, "invalid_command"),
        ({"translation_mm": [0, 0, 0]}, "invalid_command"),
        ({}, "duplicate_reference"),
    ]:
        with pytest.raises(arrangement.ArrangementError) as error:
            arrangement.apply_command(catalog, first, {**add(first), **mutation})
        assert error.value.code == code
    with pytest.raises(arrangement.ArrangementError, match="At most two"):
        arrangement.reconstruct_plan(catalog, [tiny(TUBE), tiny(RING), tiny(TUBE)])
    with pytest.raises(arrangement.ArrangementError) as duplicate:
        arrangement.reconstruct_plan(catalog, [tiny(), tiny()])
    assert duplicate.value.code == "duplicate_reference"
    with pytest.raises(arrangement.ArrangementError) as unknown:
        arrangement.apply_command(catalog, empty, translate(empty, [0, 0, 0]))
    assert unknown.value.code == "unknown_instance"
    for kind in ("Connect", "replace-reference", "rotate-reference", "scale-reference", "resolve"):
        with pytest.raises(arrangement.ArrangementError) as unsupported:
            arrangement.apply_command(catalog, first, {"type": kind})
        assert unsupported.value.code == "unsupported_command"


@pytest.mark.parametrize(
    "change",
    [
        lambda plan: plan.update(flight_ready=True),
        lambda plan: plan["readiness"].update(resolved_candidate=True),
        lambda plan: plan["checks"].update(total_mass_kg=0),
        lambda plan: plan["source_pins"].clear(),
        lambda plan: plan.update(revision_sha256="0" * 64),
        lambda plan: plan["instances"][0].update(scale=[1, 1, 2]),
        lambda plan: plan["instances"][0].update(rotation_quaternion_xyzw=[0, 0, 1, 0]),
        lambda plan: plan["instances"][0].update(quantity=True),
        lambda plan: plan["instances"][0].update(id="foreign"),
        lambda plan: plan["instances"][0].update(installed_transform=[0, 0, 0]),
        lambda plan: plan["instances"][0].update(translation_mm=[1.0, 0, 0]),
    ],
)
def test_reconstructed_state_rejects_tampering_even_if_rehashed(catalog, change):
    plan = arrangement.reconstruct_plan(catalog, [tiny()])
    change(plan)
    # A re-signed client transform/gate does not become an admitted plan.
    if plan["revision_sha256"] != "0" * 64:
        plan["revision_sha256"] = digest(
            {key: value for key, value in plan.items() if key != "revision_sha256"}
        )
    with pytest.raises(arrangement.ArrangementError):
        arrangement.admit_plan(catalog, plan)


def test_catalog_source_frames_assets_false_gates_and_availability_fail_closed(catalog):
    for mutate in (
        lambda value: value.update(revision_sha256="0" * 64),
        lambda value: value["source_pins"].clear(),
        lambda value: value["definitions"][0]["frames"]["local_cad_mm"].update(units="m"),
        lambda value: value["definitions"][0]["representation"]["assets"]["glb"].update(
            sha256="0" * 64
        ),
        lambda value: value["definitions"][0]["readiness"].update(flight_ready=True),
        lambda value: value["availability"][TUBE].update(geometry_available=True),
    ):
        bad = copy.deepcopy(catalog)
        mutate(bad)
        with pytest.raises(arrangement.ArrangementError) as error:
            arrangement.create_plan(bad)
        assert error.value.code == "invalid_catalog"
    for malformed in (None, {}, [], {"instances": [{}]}):
        with pytest.raises(arrangement.ArrangementError):
            arrangement.admit_plan(catalog, malformed)
    for malformed in ({**tiny(), "scale": [1, 1, 1]}, {**tiny(), "reference_id": []}):
        with pytest.raises(arrangement.ArrangementError):
            arrangement.reconstruct_plan(catalog, [malformed])
