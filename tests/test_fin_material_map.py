"""Mapping prefilters and source-AST identity, without CAD or build artifacts."""

from pathlib import Path

from scripts.wo03_fin_material_map import candidate, function_hashes, material


def test_matching_and_source_identity():
    source = Path("src/analysis/layered_fin_geometry.py")
    assert function_hashes(source)["layered_shapes"] == (
        "e6aa54c044af9ddcbe5db1a425779425c152649358df0df7801114d8810bc5b4"
    )
    tol = {"candidate_volume_abs_mm3": 1e-4, "bbox_and_centroid_abs_mm": 1e-5}
    item = {
        "volume_mm3": 1.0,
        "centroid_mm": [0.0, 0.0, 0.0],
        "bbox_mm": [0.0, 1.0, 0.0, 1.0, 0.0, 1.0],
    }
    assert candidate(item, item, tol)
    assert not candidate(item, {**item, "centroid_mm": [0.1, 0.0, 0.0]}, tol)
    assert material("gusset_face_bond_-1") == "epoxy"
    assert material("gusset_-1") == "plywood"
