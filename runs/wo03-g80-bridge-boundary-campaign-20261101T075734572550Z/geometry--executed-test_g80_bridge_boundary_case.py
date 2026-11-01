"""Stage wiring and durable geometry-only boundary evidence."""

import inspect
import json
from types import SimpleNamespace

import pytest

from scripts.wo03_g80_bridge_adapter import build_case
from scripts.wo03_g80_bridge_boundary_case import inspect_and_apply


def fake_gmsh():
    occ = SimpleNamespace(getMass=lambda dim, tag: 54.0 if dim == 2 else 6.0)
    model = SimpleNamespace(
        occ=occ,
        getBoundary=lambda faces, **kwargs: [(1, faces[0][1] + 100)],
        getType=lambda dim, tag: "Circle",
    )
    return SimpleNamespace(model=model)


def test_adapter_callback_is_optional_and_disabled_by_default():
    assert inspect.signature(build_case).parameters["boundary_callback"].default is None


def test_success_inventory_persists_patches_and_assignments(tmp_path, monkeypatch):
    patches = [{"face_tags": [i], "center_xyz_mm": [i, 0, 0]} for i in range(3)]
    spec = {
        "patch_outer_radius_mm": 4.5,
        "patch_inner_radius_mm": 1.7,
        "full_circle_equivalent_segments": {"outer": 96, "inner": 32},
        "curve_match_tolerance_mm": 1e-5,
    }
    monkeypatch.setattr(
        "scripts.wo03_g80_bridge_boundary_case.apply_washer_boundary",
        lambda _g, p, **kwargs: {"patches": p, "sized_curve_tags": [100, 101, 102]},
    )
    path = tmp_path / "inventory.json"
    report = inspect_and_apply(fake_gmsh(), patches, spec, path)
    assert report["status"] == "controls_applied_no_mesh"
    assert json.loads(path.read_text()) == report
    assert len(report["patches"]) == 3
    assert report["patches"][0]["boundary_curves"][0]["type"] == "Circle"


def test_failure_inventory_survives_strict_rejection(tmp_path, monkeypatch):
    patches = [{"face_tags": [1], "center_xyz_mm": [0, 0, 0]}]
    spec = {
        "patch_outer_radius_mm": 4.5,
        "patch_inner_radius_mm": 1.7,
        "full_circle_equivalent_segments": {"outer": 96, "inner": 32},
        "curve_match_tolerance_mm": 1e-5,
    }

    def reject(*args, **kwargs):
        raise ValueError("unsupported curve")

    monkeypatch.setattr("scripts.wo03_g80_bridge_boundary_case.apply_washer_boundary", reject)
    path = tmp_path / "inventory.json"
    with pytest.raises(ValueError, match="unsupported curve"):
        inspect_and_apply(fake_gmsh(), patches, spec, path)
    result = json.loads(path.read_text())
    assert result["status"] == "selection_failed"
    assert result["patches"][0]["face_area_mm2"] == 54
    assert "unsupported curve" in result["error"]
