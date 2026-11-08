"""Source-owned55-record membership and presentation-only geometry boundaries."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path

import pytest
import yaml

from src.api import rp1_geometry, rp1_inspection, rp1_inspection_view, rp1_presentation
from src.inspection.rp1_geometry import EVIDENCE, sources

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def source_root(tmp_path):
    for relative in [*sources(ROOT), rp1_presentation.CONFIG]:
        dest = tmp_path / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, dest)
    return tmp_path


@pytest.fixture
def geometry():
    # Recorded actual inspection mesh bounds; no CAD or geometry regeneration.
    return json.loads((ROOT / EVIDENCE).read_bytes())


def test_all55_functional_memberships_statuses_quantities_and_parent_provenance(geometry):
    presentation = rp1_presentation.build(ROOT, geometry=geometry)
    source = rp1_inspection.build(ROOT)
    groups = presentation["groups"]
    assert [g["id"] for g in groups] == list(rp1_presentation.GROUP_IDS)
    assert [g["record_count"] for g in groups] == [6, 9, 8, 12, 16, 4]
    assert [g["mesh_count"] for g in groups] == [4, 3, 5, 6, 8, 0]
    ids = [pid for group in groups for pid in group["part_ids"]]
    assert len(ids) == len(set(ids)) == 55
    assert set(ids) == {p["id"] for p in source["parts"]}
    assert presentation["breakdown"]["manufacturing_clearance"] is False
    for part in source["parts"]:
        row = presentation["parts"][part["id"]]
        assert row["source_parent"] == part["parent"]
        assert "not a physical attachment" in row["source_parent_semantics"]
        assert (
            row["source_tuple"]["specification_sha256"] == rp1_inspection.PINS[rp1_inspection.SPEC]
        )
        assert row["maturity"] in (
            "source_dimensioned",
            "simplified_envelope",
            "mass_allowance",
            "missing_geometry",
        )
    quantities = {
        pid: p["quantity"]["value"] for pid, p in presentation["parts"].items() if p["quantity"]
    }
    assert quantities == {"fin_set": 3, "fin_tabs": 3, "root_gussets": 6}
    assert (
        presentation["parts"]["fin_set"]["detail_offset_m"]
        == presentation["parts"]["fin_tabs"]["detail_offset_m"]
    )
    for link in presentation["cross_links"]:
        assert link["source"]["sha256"] == rp1_inspection.PINS[link["source"]["path"]]
        assert set(link["part_ids"]) <= set(ids)


def test_source_only_groups_remain_usable_without_fabricating_meshes(source_root):
    result = rp1_presentation.build(source_root)
    assert result["geometry_compatible"] is False
    assert result["source_tuple"]["inspection_geometry_sha256"] is None
    assert sum(g["record_count"] for g in result["groups"]) == 55
    assert all(g["mesh_count"] == 0 for g in result["groups"])
    assert all(not p["has_mesh"] for p in result["parts"].values())


def test_authored_full_separation_reveals_recorded_nested_envelopes_not_all_clearance(geometry):
    presentation = rp1_presentation.build(ROOT, geometry=geometry)
    rows = {p["id"]: p for p in geometry["parts"]}

    def transformed(pid, opened):
        p = presentation["parts"][pid]
        delta = [
            a + (d if p["group_id"] == opened else 0)
            for a, d in zip(p["assembly_offset_m"], p["detail_offset_m"], strict=True)
        ]
        return [[v + delta[i] for i, v in enumerate(corner)] for corner in rows[pid]["bounds_m"]]

    def separate(a, b):
        return any(a[1][i] < b[0][i] or b[1][i] < a[0][i] for i in range(3))

    assert separate(
        transformed("motor", "motor_retention"), transformed("motor_tube", "motor_retention")
    )
    for pid in ("parachute", "shock_cord", "recovery_connectors", "recovery_protection"):
        assert separate(transformed(pid, "recovery"), transformed("upper_body", "recovery"))
    assert not separate(transformed("motor", None), transformed("motor_tube", None))
    assert not separate(transformed("fin_set", "fins_roots"), transformed("fin_tabs", "fins_roots"))
    assert presentation["breakdown"]["manufacturing_clearance"] is False


def test_projection_attaches_metadata_without_changing_source_geometry(monkeypatch, geometry):
    before = rp1_inspection.build(ROOT)
    monkeypatch.setattr(rp1_geometry, "build", lambda root: copy.deepcopy(geometry))
    after = rp1_inspection_view.build(ROOT)
    assert after["summary"]["presentation"]["presentation_sha256"] == rp1_presentation.CONFIG_SHA256
    for old, new in zip(before["parts"], after["parts"], strict=True):
        assert old["parent"] == new["parent"]
        assert old["geometry"] == new["geometry"]
        assert old["location"] == new["location"]
        assert old["mass_kg"] == new["mass_kg"]
        assert old["raw"] == new["raw"]
        assert new["representation"]["presentation"]["group_id"] in rp1_presentation.GROUP_IDS
    assert after["identity"]["resolved_spec_sha256"] is None
    assert after["identity"]["cad_revision_sha256"] is None
    assert after["summary"]["physical_inertia"] is None


def test_config_drift_foreign_ids_and_nonfinite_offsets_fail_closed(source_root, monkeypatch):
    path = source_root / rp1_presentation.CONFIG
    original = path.read_bytes()
    path.write_bytes(original + b"\n# drift\n")
    with pytest.raises(ValueError, match="configuration hash"):
        rp1_presentation.build(source_root)
    for mutation in ("foreign", "duplicate", "nonfinite"):
        config = yaml.safe_load(original)
        if mutation == "foreign":
            config["groups"][0]["part_ids"][0] = "foreign-part"
        elif mutation == "duplicate":
            config["groups"][0]["part_ids"][1] = "nose"
        else:
            config["groups"][0]["assembly_offset_m"][0] = float("inf")
        path.write_text(yaml.safe_dump(config))
        monkeypatch.setattr(
            rp1_presentation, "CONFIG_SHA256", hashlib.sha256(path.read_bytes()).hexdigest()
        )
        with pytest.raises(ValueError):
            rp1_presentation.build(source_root)


def test_foreign_source_or_geometry_cannot_attach(source_root, geometry):
    wrong = copy.deepcopy(geometry)
    wrong["identity"]["inspection_geometry_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="geometry tuple"):
        rp1_presentation.build(source_root, geometry=wrong)
    spec = source_root / rp1_inspection.SPEC
    spec.write_bytes(spec.read_bytes() + b"\n# changed\n")
    with pytest.raises(ValueError, match="source hash"):
        rp1_presentation.build(source_root, geometry=geometry)


def test_missing_presentation_retains_inspector_with_explicit_unavailability(source_root):
    (source_root / rp1_presentation.CONFIG).unlink()
    document = rp1_inspection_view.build(source_root)
    assert len(document["parts"]) == 55
    assert document["summary"]["presentation"]["status"] == "unavailable"
    assert not any("presentation" in p["representation"] for p in document["parts"])
