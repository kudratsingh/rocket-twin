"""Source and safety contract for the RP1 read-only template registry."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from src.api import rp1_inspection
from src.vehicle import part_templates

ROOT = Path(__file__).resolve().parents[1]


def _source_root(tmp_path: Path) -> Path:
    for relative in (*rp1_inspection.PINS, part_templates.STEP_SOURCE):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    return tmp_path


@pytest.fixture(scope="module")
def catalog() -> dict:
    return part_templates.build(ROOT)


def test_exact_current_source_coverage_and_installed_reference_scope(catalog: dict) -> None:
    assert catalog["schema_version"] == 1
    assert catalog["configuration_id"] == rp1_inspection.ID
    assert len(catalog["all55_part_ids"]) == len(set(catalog["all55_part_ids"])) == 55
    assert [row["id"] for row in catalog["templates"]] == [
        f"rp1-template:{short}" for short, *_ in part_templates.TEMPLATE_SPECS
    ]
    assert len(catalog["feature_sources"]) == 14
    assert len(catalog["dispositions"]) == 55
    assert {row["source_part_id"] for row in catalog["dispositions"]} == set(
        catalog["all55_part_ids"]
    )
    assert catalog["capabilities"] == {
        "browse": True,
        "inspect": True,
        "draft_admission": False,
        "cad_job_execution": False,
    }
    assert all(
        row["geometry"]["installed_step_is_local_template"] is False for row in catalog["templates"]
    )
    assert all(
        reference["asset_scope"] == "installed_reference_only"
        for row in catalog["templates"]
        for reference in row["installed_references"]
    )
    assert all(row["physical_verification"] == "open" for row in catalog["templates"])
    assert all(row["installed_contact_status"] == "unknown" for row in catalog["feature_sources"])


def test_named_source_parameters_interfaces_and_mass_lines(catalog: dict) -> None:
    templates = {row["id"].split(":", 1)[1]: row for row in catalog["templates"]}
    tube = templates["motor-tube-cut"]
    assert {p["key"]: p["value"] for p in tube["parameters"]} == {
        "outer_diameter_mm": 31.369,
        "inner_diameter_mm": 29.169,
        "length_mm": 165.0,
    }
    ring = templates["aft-annular-ring"]
    assert {p["key"]: p["value"] for p in ring["parameters"]} == {
        "outer_diameter_mm": 64.4,
        "bore_diameter_mm": 31.9,
        "thickness_mm": 6.0,
    }
    assert all(p["tolerance"]["plus_minus"] == 0.05 for p in ring["parameters"][:2])
    body = templates["slotted-body-tube"]
    assert next(p for p in body["parameters"] if p["key"] == "slot_width_mm")["value"] == 6.8
    assert "historical 6.5 mm" in body["reuse"]["reason"]
    assert "already replaces" in body["reuse"]["reason"]
    fin = templates["continuous-fin-tab"]
    assert "separate root gussets" in fin["label"]
    assert {p["key"]: p["value"] for p in fin["parameters"]}["tab_length_mm"] == 109.4
    assert [
        row["template_role"]
        for row in catalog["dispositions"]
        if row["source_part_id"] in ("fin_set", "fin_tabs", "root_gussets")
    ] == [
        "primary",
        "integral_child",
        "associated_support",
    ]
    assert all(row["mass_accounting"]["template_mass_kg"] is None for row in catalog["templates"])
    assert all(
        row["mass_accounting"]["incremental_charge"] is False for row in catalog["templates"]
    )
    assert all(
        row["accounting_line"] == "existing_source_record_only" for row in catalog["dispositions"]
    )


def test_ad1_installed_projection_is_distinct_from_stale_generic_cad_fields(catalog: dict) -> None:
    spec = yaml.safe_load((ROOT / rp1_inspection.SPEC).read_bytes())
    definition = yaml.safe_load((ROOT / rp1_inspection.DEFINITION).read_bytes())
    parts = {row["id"]: row for row in spec["parts"]}
    templates = {row["id"].split(":", 1)[1]: row for row in catalog["templates"]}
    projection = (ROOT / part_templates.PROJECTION_SOURCE).read_bytes()
    assert hashlib.sha256(projection).hexdigest() == part_templates.PROJECTION_SHA256
    assert catalog["identity"]["installed_projection_source"] == {
        "path": part_templates.PROJECTION_SOURCE,
        "sha256": part_templates.PROJECTION_SHA256,
    }
    assert all(
        row["geometry"]["installed_projection_source"]
        == catalog["identity"]["installed_projection_source"]
        for row in catalog["templates"]
    )
    assert parts["body"]["cad"]["parameters"]["fin_slot_width_mm"] == 6.5
    assert definition["fin_joints"]["external_slot_width_mm"] == 6.8
    assert b'projected["cad"]["parameters"]["fin_slot_width_mm"]' in projection
    assert b'"external_slot_width_mm"' in projection
    assert parts["fin_set"]["cad"]["parameters"]["tab_length_mm"] == 109.8
    assert definition["fin_joints"]["tab_length_mm"] == 109.4
    assert b'dims["tab_length_mm"]' in projection
    assert templates["slotted-body-tube"]["reuse"]["geometry"] == "blocked"
    assert templates["continuous-fin-tab"]["reuse"]["geometry"] == "blocked"
    notch = templates["forward-notched-ring"]
    params = {row["key"]: row for row in notch["parameters"]}
    assert params["notch_width_mm"]["value"] == definition["route"]["passage_width_mm"]
    assert params["notch_depth_mm"]["value"] == definition["route"]["passage_depth_mm"]
    assert params["notch_angle_deg"]["value"] == definition["route"]["passage_angle_deg"]
    assert params["notch_width_mm"]["source"]["locator"] == "route.passage_width_mm"
    assert params["notch_width_mm"]["tolerance"]["plus_minus"] == 0.05
    feature = next(
        row
        for row in catalog["feature_sources"]
        if row["id"] == "rp1-feature:forward_ring:cord_notch"
    )
    assert feature["source"]["locator"] == "route.passage_width_mm"


def test_read_only_selection_and_nominal_geometry_request(catalog: dict) -> None:
    for name in ("motor-tube-cut", "aft-annular-ring"):
        template = next(row for row in catalog["templates"] if row["id"] == f"rp1-template:{name}")
        selected = part_templates.select_template(
            ROOT, catalog, template["id"], template["revision_sha256"]
        )
        assert selected["action"] == "inspect"
        assert selected["draft_admission"] is False
        parameters = {row["key"]: row["value"] for row in template["parameters"]}
        recipe = part_templates.prepare_local_geometry_request(
            ROOT, catalog, template["id"], template["revision_sha256"], parameters
        )
        assert recipe["generator"] == "src.cad.parts.tube"
        assert recipe["cad_execution"] is False
        assert recipe["draft_admission"] is False
        assert recipe["mass_kg"] is None
        changed = {**parameters, next(iter(parameters)): next(iter(parameters.values())) + 0.01}
        with pytest.raises(ValueError, match="source-nominal"):
            part_templates.prepare_local_geometry_request(
                ROOT, catalog, template["id"], template["revision_sha256"], changed
            )
    with pytest.raises(ValueError, match="read-only"):
        part_templates.select_template(
            ROOT,
            catalog,
            catalog["templates"][0]["id"],
            catalog["templates"][0]["revision_sha256"],
            action="add",
        )
    with pytest.raises(ValueError, match="stale"):
        part_templates.select_template(ROOT, catalog, catalog["templates"][0]["id"], "0" * 64)
    for template in catalog["templates"][2:]:
        assert template["reuse"]["geometry"] == "blocked"
        assert template["geometry"]["local_recipe_supported"] is False
        with pytest.raises(ValueError, match="blocked"):
            part_templates.prepare_local_geometry_request(
                ROOT,
                catalog,
                template["id"],
                template["revision_sha256"],
                {row["key"]: row["value"] for row in template["parameters"]},
            )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda data: data["all55_part_ids"].__setitem__(0, "foreign"),
        lambda data: data["templates"][0].__setitem__("revision_sha256", "0" * 64),
        lambda data: data["templates"][0]["local_frame"].__setitem__("origin", "nose_tip"),
        lambda data: data["templates"][0]["mass_accounting"].__setitem__(
            "incremental_charge", True
        ),
        lambda data: data["templates"][2]["reuse"].__setitem__("geometry", "supported_nominal"),
        lambda data: data["feature_sources"][0]["source"].__setitem__("sha256", "0" * 64),
        lambda data: data["dispositions"][0].__setitem__("template_id", "rp1-template:foreign"),
    ],
)
def test_catalog_rejects_tampered_identity_revision_frame_reuse_and_mass(
    catalog: dict, mutate
) -> None:
    altered = copy.deepcopy(catalog)
    mutate(altered)
    with pytest.raises(ValueError, match="differs"):
        part_templates.validate_catalog(ROOT, altered)


def test_frozen_source_drift_rejected(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    assert (
        part_templates.build(source)["revision_sha256"]
        == part_templates.build(ROOT)["revision_sha256"]
    )
    spec = source / rp1_inspection.SPEC
    spec.write_bytes(spec.read_bytes() + b"\n# tamper\n")
    with pytest.raises(ValueError, match="source hash"):
        part_templates.build(source)


def test_preparer_writes_deterministic_snapshot(tmp_path: Path, catalog: dict) -> None:
    from scripts.prepare_part_templates import OUTPUT

    source = _source_root(tmp_path)
    destination = source / OUTPUT
    script = ROOT / "scripts/prepare_part_templates.py"
    subprocess.run(
        [sys.executable, str(script), "--root", str(source), "--output", str(destination)],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    first = destination.read_bytes()
    assert json.loads(first) == catalog
    assert hashlib.sha256(first).hexdigest() == hashlib.sha256(destination.read_bytes()).hexdigest()
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--root",
            str(source),
            "--output",
            str(destination),
            "--check",
        ],
        check=True,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert destination.read_bytes() == first


def test_preparer_rejects_foreign_output_and_symlink(tmp_path: Path) -> None:
    from scripts.prepare_part_templates import OUTPUT, prepare

    source = _source_root(tmp_path)
    target = source / OUTPUT
    with pytest.raises(ValueError, match="fixed registered"):
        prepare(source, str(tmp_path / "foreign.json"))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('{"id":"foreign"}')
    with pytest.raises(ValueError, match="foreign"):
        prepare(source)
    assert target.read_text() == '{"id":"foreign"}'
    target.unlink()
    outside = tmp_path / "other.json"
    outside.write_text("preserve")
    target.symlink_to(outside)
    with pytest.raises(ValueError, match="fixed registered"):
        prepare(source)
    assert outside.read_text() == "preserve"


def test_preparer_check_does_not_modify_stale_snapshot(tmp_path: Path) -> None:
    from scripts.prepare_part_templates import OUTPUT, prepare

    source = _source_root(tmp_path)
    target = source / OUTPUT
    prepare(source)
    document = json.loads(target.read_bytes())
    document["templates"][0]["label"] = "stale"
    target.write_text(json.dumps(document))
    prior = target.read_bytes()
    with pytest.raises(ValueError, match="differs"):
        prepare(source, check=True)
    assert target.read_bytes() == prior
    prepare(source)
    assert target.read_bytes() != prior
