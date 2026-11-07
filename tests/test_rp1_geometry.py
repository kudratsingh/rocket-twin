"""Source linkage, honest omissions and actual exported metre/location checks."""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from src.api import rp1_geometry, rp1_inspection
from src.inspection.rp1_geometry import EVIDENCE, FOLDER, audit, export, sha, sources

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    pytest.importorskip("cadquery")
    root = tmp_path_factory.mktemp("rp1-geometry")
    for relative in sources(ROOT):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    result = export(root)
    evidence = root / EVIDENCE
    evidence.parent.mkdir(parents=True)
    evidence.write_text(json.dumps(result, indent=2) + "\n")
    return root, result


def test_all_55_source_records_have_one_explicit_classification():
    result = audit(ROOT)
    source = rp1_inspection.build(ROOT)
    assert [p["id"] for p in result["parts"]] == [p["id"] for p in source["parts"]]
    assert len({p["id"] for p in result["parts"]}) == 55
    rows = {p["id"]: p for p in result["parts"]}
    assert rows["fin_tabs"]["maturity"] == "source_dimensioned"
    assert rows["rp1_kevlar_wrap"]["maturity"] == "missing_geometry"
    assert rows["ad1_slot_fill"]["maturity"] == "mass_allowance"
    assert rows["motor_retainer"]["maturity"] == "simplified_envelope"
    assert "roundovers omitted" in rows["forward_ring"]["description"]


def test_generated_meshes_match_source_scale_location_and_separate_parts(generated):
    import trimesh

    root, result = generated
    assert result["coverage"] == {
        "source_parts": 55,
        "mesh_parts": 26,
        "by_maturity": {
            "source_dimensioned": 10,
            "simplified_envelope": 16,
            "mass_allowance": 25,
            "missing_geometry": 4,
        },
        "complete_installed_geometry": False,
    }
    assert result["identity"]["cad_revision_sha256"] is None
    assert result["identity"]["resolved_spec_sha256"] is None
    assert result["mass_or_inertia_generated"] is False
    rows = {p["id"]: p for p in result["parts"]}
    length = result["length_m"]
    expected = {
        "motor_tube": [
            [-0.0156845, length - 1.220, -0.0156845],
            [0.0156845, length - 1.055, 0.0156845],
        ],
        "battery": [[-0.015, length - 0.140, -0.0155], [0.015, length - 0.085, -0.0005]],
    }
    for pid, bounds in expected.items():
        loaded = trimesh.load(root / rows[pid]["mesh"]["path"], force="scene")
        assert np.allclose(loaded.bounds, bounds, atol=2e-7)
        assert np.allclose(loaded.bounds, rows[pid]["bounds_m"], atol=2e-7)
    # Fin panels own the external planform only; tabs/gussets are separate source IDs.
    panels = trimesh.load(root / rows["fin_set"]["mesh"]["path"], force="scene").to_geometry()
    radial = np.linalg.norm(panels.vertices[:, [0, 2]], axis=1)
    assert radial.min() >= 0.033400
    tabs = rows["fin_tabs"]["bounds_m"]
    assert np.isclose(tabs[1][1] - tabs[0][1], 0.1094, atol=1e-7)
    assert np.isclose(tabs[1][1], length - 1.0802, atol=1e-7)
    for row in rows.values():
        if row["maturity"] in ("mass_allowance", "missing_geometry"):
            assert row["mesh"] is None and row["bounds_m"] is None
        else:
            loaded = trimesh.load(root / row["mesh"]["path"], force="scene")
            assert np.allclose(loaded.bounds, row["bounds_m"], atol=2e-7)
            assert np.isfinite(loaded.bounds).all()
    body = trimesh.load(root / rows["body"]["mesh"]["path"], force="scene").to_geometry()
    # Mesh edge locations establish corrected 6.8 mm slots, not legacy 6.5 mm.
    slot_flank = (body.vertices[:, 0] > 0.032) & np.isclose(
        np.abs(body.vertices[:, 2]), 0.0034, atol=1e-8
    )
    assert slot_flank.any()
    assert np.isclose(result["bounds_m"][1][1], length, atol=1e-7)
    assert rp1_geometry.build(root) == result


def test_verified_asset_allowlist_and_drift_rejection(generated, tmp_path):
    original, manifest = generated
    root = tmp_path / "fixture"
    shutil.copytree(original, root)
    path, expected = rp1_geometry.asset(root, "fin_tabs")
    assert sha(path.read_bytes()) == expected
    with pytest.raises(ValueError, match="Unknown or unavailable"):
        rp1_geometry.asset(root, "rail_buttons")
    with pytest.raises(ValueError, match="Unknown or unavailable"):
        rp1_geometry.asset(root, "../../motor")
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="mesh hash mismatch"):
        rp1_geometry.build(root)
    shutil.copyfile(original / FOLDER / "parts/fin_tabs.glb", path)
    changed = copy.deepcopy(manifest)
    changed["parts"][0]["id"] = "invented"
    (root / FOLDER / "manifest.json").write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="differs from saved evidence"):
        rp1_geometry.build(root)


def test_missing_output_is_unavailable_not_generated(tmp_path):
    for relative in sources(ROOT):
        dest = tmp_path / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, dest)
    with pytest.raises(FileNotFoundError):
        rp1_geometry.build(tmp_path)
    assert not (tmp_path / FOLDER).exists()


def test_frozen_source_drift_rejected_before_asset_access(generated, tmp_path):
    original, _ = generated
    root = tmp_path / "fixture"
    shutil.copytree(original, root)
    spec = root / rp1_inspection.SPEC
    spec.write_bytes(spec.read_bytes() + b"\n# drift\n")
    with pytest.raises(ValueError, match="source hash mismatch"):
        rp1_geometry.asset(root, "nose")
