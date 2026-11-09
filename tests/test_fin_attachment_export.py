"""Registered CAD sections and exact source dimensions, not installed qualification."""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

import numpy as np
import pytest

from scripts import wo04_fin_attachment_export as export

ROOT = Path(__file__).resolve().parents[1]


def packet():
    return json.loads((ROOT / export.CATALOG).read_bytes())


def test_catalog_exact_nine_source_records_and_dimension_guides():
    result = packet()
    source = json.loads((ROOT / export.MANIFEST).read_bytes())
    rows = {row["id"]: row for row in source["parts"]}
    assert result["configuration_id"] == export.CONFIGURATION
    assert result["inspection_geometry_sha256"] == export.CORE
    assert tuple(part["id"] for part in result["parts"]) == export.IDS
    assert len(set(result["all55_part_ids"])) == 55
    assert result["frame"] == export.FRAME
    assert result["download"]["included_part_ids"] == list(export.IDS)
    assert result["download"]["sha256"] == export.JOINT_SHA
    assert result["download"]["units"] == "mm"
    assert result["validation"]["joint_readback"]["solids"] == 18
    assert result["engineering_accepted"] is False
    assert result["mass_or_inertia_generated"] is False
    assert result["canonical_vehicle_geometry_changed"] is False
    for part in result["parts"]:
        registered = rows[part["id"]]
        assert part["source"]["path"] == registered["path"]
        assert part["source"]["sha256"] == registered["sha256"]
        assert part["source"]["specification"] == registered["source"]
        assert part["source"]["definition"] == registered["definition_source"]
        assert part["maturity"] == registered["maturity"]
        assert set(part["assets"]) == {"assembled", "longitudinal", "transverse"}
        for asset in part["assets"].values():
            if asset:
                assert asset["closed"] is True
                assert asset["solid_count"] > 0
                if "partition_error_mm3" in asset["validation"]:
                    validation = asset["validation"]
                    assert validation["partition_error_mm3"] <= max(
                        1e-5, validation["source_volume_mm3"] * 1e-7
                    )
    dimensions = {d["id"]: d for d in result["dimensions"]}
    assert dimensions["tab-thickness"]["value_mm"] == 6
    assert dimensions["slot-width"]["value_mm"] == 6.8
    assert dimensions["slot-width"]["tolerance_mm"] == 0.05
    assert dimensions["aft-gap"]["value_mm"] == 0.4
    assert dimensions["aft-gap"]["tolerance_mm"] is None
    for dimension in dimensions.values():
        points = np.asarray(dimension["points_m"])
        assert points.shape == (2, 3)
        assert np.linalg.norm(points[1] - points[0]) * 1000 == pytest.approx(
            dimension["value_mm"], abs=1e-9
        )
    forward = next(p for p in result["parts"] if p["id"] == "forward_ring")
    assert forward["assets"]["transverse"] is None
    assert "outside retained" in forward["section_status"]["transverse"]
    assert "fin_internal_bonds" in result["callout_only_part_ids"]
    assert not set(result["callout_only_part_ids"]) & {p["id"] for p in result["parts"]}
    assert (
        export.revision({k: v for k, v in result.items() if k != "revision_sha256"})
        == result["revision_sha256"]
    )


def test_known_box_half_space_caps_volume_and_coordinate_mapping():
    pytest.importorskip("cadquery")
    result = export.box_case()
    assert result["valid"] is True
    assert len(result["cases"]) == 2
    for case in result["cases"]:
        assert case["source_volume_mm3"] == pytest.approx(480)
        assert case["positive_volume_mm3"] == pytest.approx(240)
        assert case["negative_volume_mm3"] == pytest.approx(240)
    assert export.viewer([25, 3, 1134.9]) == pytest.approx([0.025, 0.1151, 0.003])


def test_recorded_annular_cap_retains_motor_tube_bore():
    result = packet()
    source = json.loads((ROOT / export.MANIFEST).read_bytes())
    row = next(p for p in source["source_records"] if p["id"] == "motor_tube")
    dimensions = row["source_dimensions"]
    expected_area = math.pi * (
        (dimensions["radius_m"] * 1000) ** 2 - (dimensions["inner_radius_m"] * 1000) ** 2
    )
    tube = next(p for p in result["parts"] if p["id"] == "motor_tube")
    cap = tube["assets"]["transverse"]
    assert cap["cap_url"] is not None
    assert sum(face["area_mm2"] for face in cap["cut_faces"]) == pytest.approx(
        expected_area, rel=1e-8
    )
    # A full filled disk would erase the source bore and have a much larger area.
    assert expected_area < math.pi * (dimensions["radius_m"] * 1000) ** 2


def test_registered_mesh_bytes_bounds_and_real_cap_planes():
    trimesh = pytest.importorskip("trimesh")
    result = packet()
    files = export.registered_files(result)
    cache = ROOT / export.CACHE
    if any(not (cache / url[len(export.PREFIX) :]).exists() for url in files):
        pytest.skip("Derived inspection GLBs are optional generated cache assets")
    sections = {s["id"]: s for s in result["sections"]}
    cap_count = 0
    for url, pin in files.items():
        assert export.sha((cache / url[len(export.PREFIX) :]).read_bytes()) == pin
    for part in result["parts"]:
        for variant, asset in part["assets"].items():
            if asset is None:
                continue
            mesh = trimesh.load(
                cache / asset["url"][len(export.PREFIX) :], force="scene"
            ).to_geometry()
            np.testing.assert_array_equal(mesh.bounds, asset["bounds_m"])
            if asset["cap_url"]:
                cap_count += 1
                cap = trimesh.load(
                    cache / asset["cap_url"][len(export.PREFIX) :], force="scene"
                ).to_geometry()
                plane = sections[variant]["viewerplane"]
                distances = cap.vertices @ np.asarray(plane["normal"]) + plane["constant"]
                assert np.max(np.abs(distances)) < 1e-7
                assert asset["cut_faces"]
                assert all(f["planar"] and f["area_mm2"] > 0 for f in asset["cut_faces"])
                for face in asset["cut_faces"]:
                    assert np.all(
                        np.asarray(face["bounds_m"])[0] <= np.asarray(face["bounds_m"])[1]
                    )
                for line in asset["cut_edges_m"]:
                    assert (
                        np.max(
                            np.abs(
                                np.asarray(line) @ np.asarray(plane["normal"]) + plane["constant"]
                            )
                        )
                        < 1e-7
                    )
    assert cap_count > 0


def test_prepare_only_registered_bytes_and_preserves_unrelated_files(tmp_path):
    result = packet()
    files = export.registered_files(result)
    if any(not (ROOT / export.CACHE / url[len(export.PREFIX) :]).exists() for url in files):
        pytest.skip("Derived inspection cache optional; no reconstruction in tests")
    destination = tmp_path / "preview"
    response = export.prepare(ROOT, destination)
    assert response["status"] == "prepared"
    assert export.prepare(ROOT, destination)["status"] == "verified_existing"
    assert {p.name for p in destination.iterdir()} == {u[len(export.PREFIX) :] for u in files}
    unrelated = destination / "owner.txt"
    unrelated.write_text("preserve")
    with pytest.raises(ValueError, match="Unregistered"):
        export.prepare(ROOT, destination)
    assert unrelated.read_text() == "preserve"


def test_unregistered_download_or_asset_and_source_drift_rejected(tmp_path):
    result = packet()
    bad = copy.deepcopy(result)
    bad["parts"][0]["assets"]["assembled"]["url"] = export.PREFIX + "../foreign.glb"
    with pytest.raises(ValueError, match="Unregistered"):
        export.registered_files(bad)
    bad = copy.deepcopy(result)
    bad["download"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="Unregistered"):
        export.registered_files(bad)
    path = tmp_path / "source.step"
    path.write_bytes(b"saved")
    expected = export.sha(path.read_bytes())
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        export.checked(tmp_path, "source.step", expected)
    with pytest.raises(ValueError, match="unavailable"):
        export.checked(tmp_path, "../foreign.step", expected)
