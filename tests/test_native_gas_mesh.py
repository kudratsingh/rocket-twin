"""Native boundary crossing rejection and split-wall mesh smoke fixture."""

from pathlib import Path

import numpy as np
import yaml

from scripts.wo03_cad_gas_mesh import fixture_source
from src.analysis.cad_gas_mesh import native_face_mapping
from src.analysis.native_gas_mesh import native_mesh, surface_crossings


def test_crossing_detector_distinguishes_shared_vertices_and_intersection() -> None:
    points = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]])
    tri = np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]], dtype=np.int64)
    assert not surface_crossings(points, tri)["crossings"]
    crossing = surface_crossings(
        np.concatenate([points, points + 0.25]), np.concatenate([tri, tri + 4])
    )
    assert crossing["crossings"]


def test_native_split_wall_retains_faces_shared_nodes_and_requires_new_quadrature(
    tmp_path: Path,
) -> None:
    cfg = yaml.safe_load(Path("configs/studies/wo03-native-gas-mesh.yaml").read_text())
    frozen = yaml.safe_load(Path(cfg["frozen_source_config"]).read_text())
    source = fixture_source("split_wall", tmp_path / "split")
    source["paths"] = {"step": source["step"]}
    mapping = native_face_mapping(
        source["step"], source["faces"], source["boundary"], frozen["mapping"]
    )
    arrays, audit = native_mesh(source, mapping, cfg, tmp_path / "split")
    assert audit["mesh_checks"]["new_wall_quadrature_required"]
    assert audit["mesh_checks"]["optical_facet_transfer_forbidden"]
    assert not audit["mesh_checks"]["global_geometry_fidelity_validated"]
    assert set(arrays["boundary_face_ids"]) == set(range(1, 11))
    left = set(arrays["boundary_triangles"][arrays["boundary_group_ids"] == 0].ravel())
    right = set(arrays["boundary_triangles"][arrays["boundary_group_ids"] == 1].ravel())
    assert left & right
