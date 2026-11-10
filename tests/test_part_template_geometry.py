"""Focused source admission and nominal annulus readback for local template CAD."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from scripts import wo04_part_template_geometry as geometry
from src.vehicle.part_templates import build, prepare_local_geometry_request


@pytest.fixture
def prepared_catalog(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Use source-derived bytes without requiring or writing an owner public cache."""
    target = tmp_path / "rp1-part-templates.json"
    target.write_text(
        json.dumps(build(geometry.ROOT), indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
    monkeypatch.setattr(geometry, "PREPARED", target)


def test_two_exact_nominal_requests_and_unsupported_rejection(prepared_catalog: None) -> None:
    catalog = geometry.source_catalog()
    requests = geometry.nominal_requests(catalog)
    assert [row["template_id"] for row in requests] == [
        "rp1-template:motor-tube-cut",
        "rp1-template:aft-annular-ring",
    ]
    assert requests[0]["parameters_mm"] == {
        "outer_radius_mm": 15.6845,
        "inner_radius_mm": 14.5845,
        "length_mm": 165.0,
    }
    assert requests[1]["parameters_mm"] == {
        "outer_radius_mm": 32.2,
        "inner_radius_mm": 15.95,
        "length_mm": 6.0,
    }
    assert all(row["mass_kg"] is None and row["draft_admission"] is False for row in requests)
    templates = {row["id"]: row for row in catalog["templates"]}
    tube = templates["rp1-template:motor-tube-cut"]
    nominal = {row["key"]: row["value"] for row in tube["parameters"]}
    altered = copy.deepcopy(nominal)
    altered["length_mm"] += 0.01
    with pytest.raises(ValueError, match="exact source-nominal"):
        prepare_local_geometry_request(
            geometry.ROOT, catalog, tube["id"], tube["revision_sha256"], altered
        )
    with pytest.raises(ValueError, match="stale"):
        prepare_local_geometry_request(geometry.ROOT, catalog, tube["id"], "0" * 64, nominal)
    body = templates["rp1-template:slotted-body-tube"]
    with pytest.raises(ValueError, match="blocked"):
        prepare_local_geometry_request(
            geometry.ROOT,
            catalog,
            body["id"],
            body["revision_sha256"],
            {row["key"]: row["value"] for row in body["parameters"]},
        )


def test_closed_one_solid_has_true_annular_bore_and_nominal_dimensions() -> None:
    from src.cad.parts import tube

    shape = tube(15.6845, 14.5845, 165.0)
    checked = geometry.validate_step(shape, outer=15.6845, inner=14.5845, length=165.0)
    assert checked["valid"] is True
    assert checked["closed"] is True
    assert checked["solid_count"] == 1
    assert checked["annular_bore"] is True
    assert checked["outer_diameter_mm"] == pytest.approx(31.369)
    assert checked["inner_diameter_mm"] == pytest.approx(29.169)
    assert checked["length_mm"] == pytest.approx(165.0)
    with pytest.raises(ValueError, match="annular"):
        geometry.validate_step(
            tube(15.6845, 13.0, 165.0), outer=15.6845, inner=14.5845, length=165.0
        )


def test_manifest_and_public_cache_are_exact_when_present(prepared_catalog: None) -> None:
    if not geometry.DOCUMENT.exists() or not geometry.OUTPUT.exists():
        pytest.skip(
            "Ignored actual CAD cache unavailable; no cache/readback acceptance on this host"
        )
    manifest = geometry.check(public=geometry.PUBLIC.exists())
    assert manifest["mass_or_inertia_generated"] is False
    assert manifest["vehicle_adoption"] is False
    assert manifest["step_units"] == "mm"
    assert manifest["viewer_units"] == "m"
    assert len(manifest["representations"]) == 2
    assert json.loads(Path(geometry.DOCUMENT).read_bytes()) == manifest
