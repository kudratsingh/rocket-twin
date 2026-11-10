"""Existing registered bytes and analytic datums; no CAD or physical calculation."""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from src.vehicle import reference_parts as references

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def source_root(tmp_path):
    for relative in references.SOURCE_PINS:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    # Ignored cache is optional on a clean checkout; never replace corrupt bytes.
    for relative in references.ASSET_PATHS:
        source = ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        assert not source.is_symlink(), "Registered cache fixture must not follow a symlink"
        if source.exists():
            shutil.copyfile(source, destination)
    return tmp_path


def test_actual_registered_projection_and_bytes_are_exact_deterministic_and_source_read_only():
    before = {path: (ROOT / path).read_bytes() for path in references.SOURCE_PINS}
    result = references.build(ROOT)
    assert result == references.build(ROOT)
    assert result["scope"] == "geometry_only_planning"
    assert result["source_catalog_changed"] is False
    assert result["add_replace_connect_implemented"] is False
    assert result["engineering_accepted"] is False
    assert result["simulation_eligible"] is False
    assert result["flight_ready"] is False
    assert (
        references.digest(
            {k: v for k, v in result.items() if k not in ("revision_sha256", "availability")}
        )
        == result["revision_sha256"]
    )
    assert len(result["definitions"]) == 2
    for row in result["definitions"]:
        assert row["id"].startswith("reference-local-v1:")
        assert row["exact_product"] is None
        assert row["stock_adoption"] is False
        assert all(value is None for value in row["unknown_properties"].values())
        assert all(value is False for value in row["readiness"].values())
        assert row["installed_geometry_adoption"] is False
        assert row["interfaces"] is None
        assert row["representation"]["installed_transform"] is None
        revision = row["revision_sha256"]
        assert (
            references.digest({k: v for k, v in row.items() if k != "revision_sha256"}) == revision
        )
        assets = row["representation"]["assets"]
        missing = [ext for ext in ("step", "glb") if not (ROOT / assets[ext]["path"]).exists()]
        availability = result["availability"][row["id"]]
        assert availability["missing_formats"] == missing
        assert availability["geometry_available"] is (not missing)
        assert availability["status"] == (
            "unavailable" if missing else "verified_registered_local_cache"
        )
        assert availability["public_url_cache_verified"] is False
        assert availability["generation_attempted"] is False
        for ext, asset in assets.items():
            if ext in missing:
                assert not (ROOT / asset["path"]).exists()
                continue
            data = (ROOT / asset["path"]).read_bytes()
            assert hashlib.sha256(data).hexdigest() == asset["sha256"]
            assert len(data) == asset["bytes"]
            assert data.startswith(b"glTF" if ext == "glb" else b"ISO-10303-21;")
    assert before == {path: (ROOT / path).read_bytes() for path in before}
    manifest = json.loads(before[references.MANIFEST_PATH])
    assert manifest["draft_admission"] is False and manifest["vehicle_adoption"] is False


def test_nominal_dimensions_frames_features_and_recorded_bore_readback(source_root):
    result = references.build(source_root)
    for row, case in zip(result["definitions"], references.CASES, strict=True):
        reference_id, _, source_id, outer, inner, length = case
        assert row["id"] == reference_id and row["source_part_id"] == source_id
        assert row["frames"]["local_cad_mm"] == references.CAD_FRAME
        assert row["frames"]["viewer"] == references.VIEWER_FRAME
        assert (
            row["frames"]["viewer"]["mapping"] == "viewer[X,Y,Z]=[cadX/1000,-cadZ/1000,cadY/1000]"
        )
        assert row["parameters_mm"] == {
            "outer_radius_mm": outer,
            "inner_radius_mm": inner,
            "length_mm": length,
        }
        features = {feature["id"]: feature for feature in row["analytic_features"]}
        assert set(features) == {"axis", "bore", "outer_cylinder", "start_plane", "end_plane"}
        assert features["axis"]["origin_mm"] == [0, 0, 0]
        assert features["axis"]["direction"] == [0, 0, 1]
        assert features["bore"]["radius_mm"] == inner
        assert features["outer_cylinder"]["radius_mm"] == outer
        assert features["start_plane"]["origin_mm"] == [0, 0, 0]
        assert features["end_plane"]["origin_mm"] == [0, 0, length]
        assert features["start_plane"]["radial_range_mm"] == [inner, outer]
        for feature in features.values():
            assert feature["cad_face_ids"] is None and feature["mesh_triangle_ids"] is None
            assert feature["tolerance_mm"] is None and feature["mating_admitted"] is False
            assert feature["frame"] == "local_cad_mm"
        assert row["representation"]["kernel_execution_performed"] is False
        availability = result["availability"][row["id"]]
        missing = [
            ext
            for ext in ("step", "glb")
            if not (source_root / row["representation"]["assets"][ext]["path"]).exists()
        ]
        assert availability["missing_formats"] == missing
        assert availability["geometry_available"] is (not missing)
        if missing:
            # Historical manifest readback does not make absent geometry available.
            assert availability["status"] == "unavailable"
        else:
            readback = row["representation"]["recorded_readback"]
            assert readback["valid"] is True and readback["closed"] is True
            assert readback["solid_count"] == 1 and readback["annular_bore"] is True
            assert readback["bounds_mm"] == [[-outer, -outer, 0], [outer, outer, length]]


def test_generator_source_establishes_xy_extrusion_but_is_not_imported_or_executed(source_root):
    data = (source_root / "src/cad/parts.py").read_bytes()
    assert hashlib.sha256(data).hexdigest() == references.SOURCE_PINS["src/cad/parts.py"]
    tree = ast.parse(data)
    tube = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "tube"
    )
    assert (
        ast.unparse(tube.body[0])
        == "return cq.Workplane('XY').circle(ro).circle(ri).extrude(length).val()"
    )
    exporter = (source_root / "scripts/wo04_part_template_geometry.py").read_text()
    assert "STEP_BOUNDS_TOLERANCE_MM = 1e-5" in exporter
    assert "GLB_BOUNDS_TOLERANCE_M = 0.00025" in exporter
    assert "[-outer / 1000, -length / 1000, -outer / 1000]" in exporter


def test_exact_selection_does_not_admit_instances_or_product_or_mass(source_root):
    catalog = references.build(source_root)
    for row in catalog["definitions"]:
        selected = references.select_reference(
            source_root, row["id"], row["revision_sha256"], row["parameters_mm"]
        )
        assert selected["action"] == "inspect_geometry_reference"
        assert selected["instance_created"] is False
        assert selected["definition"] == row
        assert selected["engineering_accepted"] is False
        assert selected["simulation_eligible"] is False
        assert selected["flight_ready"] is False
        assert selected["definition"]["unknown_properties"]["mass_kg"] is None
        selected["definition"]["parameters_mm"]["length_mm"] = 0
        assert references.build(source_root) == catalog
    tube, annulus = catalog["definitions"]
    assert (
        "conflicts" in tube["identity_limit"]
        and "not exact purchased tube" in tube["identity_limit"]
    )
    assert "complete installed ring proposal" in annulus["identity_limit"]


@pytest.mark.parametrize(
    "change",
    [
        {"length_mm": 165.000000001},
        {"length_mm": -1},
        {"length_mm": "165"},
        {"outer_radius_mm": 16.0},
        {"inner_radius_mm": True},
        {"tolerance_mm": 0.1},
    ],
)
def test_changed_parameters_never_generate_or_silently_accept(source_root, change):
    row = references.build(source_root)["definitions"][0]
    with pytest.raises(references.ReferencePartsError, match="exact nominal"):
        references.select_reference(
            source_root, row["id"], row["revision_sha256"], {**row["parameters_mm"], **change}
        )


def test_unknown_id_stale_revision_and_foreign_path_rejected(source_root):
    row = references.build(source_root)["definitions"][0]
    with pytest.raises(references.ReferencePartsError, match="Unknown"):
        references.select_reference(
            source_root, "../../source", row["revision_sha256"], row["parameters_mm"]
        )
    with pytest.raises(references.ReferencePartsError, match="revision"):
        references.select_reference(source_root, row["id"], "0" * 64, row["parameters_mm"])
    with pytest.raises(references.ReferencePartsError, match="exact registered"):
        references._read(source_root, "/Users/owner/other.step")


def test_missing_cold_cache_is_unavailable_without_regeneration_or_revision_change(
    source_root, monkeypatch
):
    before = references.build(source_root)
    for relative in references.ASSET_PATHS:
        (source_root / relative).unlink(missing_ok=True)

    def no_execution(*args, **kwargs):
        raise AssertionError("No generation or scan is authorized")

    monkeypatch.setattr(subprocess, "run", no_execution)
    monkeypatch.setattr(Path, "glob", no_execution)
    monkeypatch.setattr(Path, "rglob", no_execution)
    monkeypatch.setattr(Path, "iterdir", no_execution)
    after = references.build(source_root)
    assert after["definitions"] == before["definitions"]
    assert after["revision_sha256"] == before["revision_sha256"]
    for status in after["availability"].values():
        assert status["status"] == "unavailable" and status["geometry_available"] is False
        assert status["missing_formats"] == ["step", "glb"]
        assert status["generation_attempted"] is False


def test_corrupt_asset_or_symlink_cannot_be_hidden_as_missing(source_root):
    path = source_root / "output/rp1-template-geometry-v1/motor-tube-cut.glb"
    # Explicitly invalid bytes also exercise fail-closed behavior on a cold checkout.
    path.write_bytes(b"intentionally invalid GLB test bytes")
    with pytest.raises(references.ReferencePartsError, match="hash differ"):
        references.build(source_root)
    path.unlink()
    outside = source_root / "unrelated.glb"
    outside.write_bytes(b"invalid symlink target; not a registered asset")
    path.symlink_to(outside)
    with pytest.raises(references.ReferencePartsError, match="Unsafe"):
        references.build(source_root)


def test_frame_status_or_source_hash_drift_rejected_not_reinterpreted(source_root):
    config = yaml.safe_load((source_root / references.CONFIG_PATH).read_bytes())
    manifest = json.loads((source_root / references.MANIFEST_PATH).read_bytes())
    for mutate in [
        lambda data: data.update(step_units="m"),
        lambda data: data.update(viewer_mapping="identity"),
        lambda data: data.update(local_cad_frame_mm="installed nose-tip origin"),
        lambda data: data.update(draft_admission=True),
    ]:
        altered = copy.deepcopy(manifest)
        mutate(altered)
        with pytest.raises(references.ReferencePartsError, match="frame or false-gate"):
            references._check_manifest(config, altered)
    path = source_root / references.MANIFEST_PATH
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(references.ReferencePartsError, match="pinned identities"):
        references.build(source_root)
