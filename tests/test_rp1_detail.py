"""Optional detail improves supported display surfaces without inventing internals."""

import copy
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from src.api import rp1_geometry, rp1_inspection
from src.inspection import rp1_detail

ROOT = Path(__file__).resolve().parents[1]


def packet():
    return json.loads((ROOT / rp1_detail.CATALOG).read_bytes())


def test_recorded_packet_pins_sources_all26_audit_and_only_supported_exemplars():
    data = packet()
    assert data["source_tuple"]["inspection_geometry_sha256"] == rp1_detail.CORE_GEOMETRY
    assert data["core_source_records"] == 55 and len(data["core_asset_audit"]) == 26
    assert sum(row["box_envelope"] for row in data["core_asset_audit"]) == 12
    assert [c["id"] for c in data["cases"]] == [
        "forward-ring-recovery",
        "motor-support-retention",
        "avionics-envelope",
    ]
    assert {p["part_id"] for p in data["parts"]} == set(rp1_detail.REPLACEMENTS)
    for path, wanted in data["sources"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == wanted
    assert data["mass_or_inertia_generated"] is False
    assert data["engineering_accepted"] is False
    assert data["manufacturing_clearance"] is False
    assert data["cases"][2]["replacement_part_ids"] == []
    assert any("roundovers" in note for note in data["cases"][0]["missing"])
    assert any("threads" in note for note in data["cases"][1]["missing"])
    assert any("PCB" in note for note in data["cases"][2]["missing"])
    assert all(
        a["annotation_only"] and not a["contributes_geometry_bounds"] for a in data["annotations"]
    )


def test_real_optional_meshes_have_bores_layers_and_unchanged_core():
    trimesh = pytest.importorskip("trimesh")
    data = packet()
    folder = ROOT / rp1_detail.FOLDER
    if not (folder / "manifest.json").exists():
        pytest.skip(
            "Optional local display assets not exported; recorded source packet remains available"
        )
    assert (folder / "manifest.json").read_bytes() == (ROOT / rp1_detail.CATALOG).read_bytes()
    expected = {
        "forward_ring": (0.01595, 0.0322),
        "motor_tube": (0.0145845, 0.0156845),
        "aft_ring": (0.01595, 0.0322),
    }
    for row in data["parts"]:
        path = folder / "parts" / (row["part_id"] + ".glb")
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row["asset_sha256"]
        scene = trimesh.load(path, force="scene")
        mesh = scene.to_geometry()
        assert len(mesh.faces) > row["core_triangles"] * 4
        radii = np.linalg.norm(mesh.vertices[:, [0, 2]], axis=1)
        inner, outer = expected[row["part_id"]]
        assert radii.min() >= inner - 2e-7 and radii.max() <= outer + 2e-7
        assert np.allclose(mesh.bounds, row["bounds_m"], atol=1e-8)
        if row["part_id"] == "forward_ring":
            assert len(scene.geometry) == 3
            assert [layer["thickness_mm"] for layer in row["layers"]] == [6, 0.2, 6]
            centers = mesh.triangles_center
            angle = np.deg2rad(60)
            radial = centers[:, 0] * 1000 * np.cos(angle) + centers[:, 2] * 1000 * np.sin(angle)
            tangential = -centers[:, 0] * 1000 * np.sin(angle) + centers[:, 2] * 1000 * np.cos(
                angle
            )
            assert not (
                (radial > 15.9501) & (radial < 20.9499) & (np.abs(tangential) < 2.2499)
            ).any()
    core = rp1_geometry.build(ROOT)
    assert core["identity"]["inspection_geometry_sha256"] == rp1_detail.CORE_GEOMETRY
    assert len(core["parts"]) == 55
    assert {p["id"]: p["mesh"]["sha256"] for p in core["parts"] if p["mesh"]} == {
        p["id"]: p["mesh_sha256"] for p in data["core_asset_audit"]
    }


def test_foreign_core_tuple_rejected_before_any_detail_generation(monkeypatch):
    wrong = copy.deepcopy(packet())
    wrong["identity"] = {"inspection_geometry_sha256": "0" * 64}
    monkeypatch.setattr(rp1_geometry, "build", lambda root: wrong)
    with pytest.raises(ValueError, match="tuple mismatch"):
        rp1_detail.catalog(ROOT)


def test_source_nominal_annotation_units_and_locations_stay_explicit():
    data = packet()
    annotations = {a["id"]: a for a in data["annotations"]}
    assert annotations["ring-bore"]["value"] == 31.9
    assert annotations["notch-width"]["value"] == 4.5
    assert [annotations[k]["value"] for k in ("baro-axial", "baro-width", "baro-thickness")] == [
        15,
        12,
        3,
    ]
    assert all(
        a["units"] == "mm" and a["source"]["sha256"] == rp1_inspection.PINS[a["source"]["path"]]
        for a in data["annotations"]
    )
    assert all(len(a["from_m"]) == len(a["to_m"]) == 3 for a in data["annotations"])
