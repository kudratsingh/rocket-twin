"""Complete labelled PLC boundaries, shared Robin nodes and resource failures."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import yaml

from scripts.wo03_cad_gas_mesh import fixture_source
from src.analysis.cad_gas_mesh import (
    interior_seeds,
    native_face_mapping,
    source_facet_correspondence,
    tetrahedralize,
    verify_volume_mesh,
)


@pytest.mark.parametrize("kind", ["split_wall", "cavity", "thin_barrier_window"])
def test_labelled_actual_PLC_fixture_and_failure_gates(tmp_path: Path, kind: str) -> None:
    cfg = yaml.safe_load(Path("configs/studies/wo03-cad-gas-mesh.yaml").read_text())
    source = fixture_source(kind, tmp_path / kind)
    mapping = native_face_mapping(
        source["step"], source["faces"], source["boundary"], cfg["mapping"]
    )
    assert mapping["all_faces_bijective"]
    assert min(row["native_entity_tag"] for row in mapping["rows"]) > 10000
    seeds, _ = interior_seeds(source["step"], source["boundary"], 4, 0.005, 150000)
    mesh = tetrahedralize(source["boundary"], mapping, seeds)
    arrays, checks = verify_volume_mesh(
        mesh,
        source["boundary"],
        source["faces"],
        source["groups"],
        source["face_to_group"],
        cfg["caps"],
    )
    assert checks["all_exterior_facets_exactly_once"]
    assert checks["all_fixed_boundary_coordinates_and_facets_preserved"]
    assert checks["tetra_volume_mm3"] == pytest.approx(source["expected_volume_mm3"])
    assert arrays["points_m"].max() <= 0.020000001
    assert set(arrays["boundary_face_ids"]) == set(range(1, len(source["faces"]) + 1))
    assert checks["minimum_tet_volume_m3"] > 0
    assert not checks["prescribed_gas_node_ownership_assigned"]
    correspondence = source_facet_correspondence(arrays, source["boundary"])
    assert np.array_equal(
        correspondence["boundary_source_triangle_ids"], np.arange(len(arrays["boundary_triangles"]))
    )
    assert (correspondence["boundary_source_vertex_permutation"] == [0, 1, 2]).all()
    if kind == "split_wall":
        left = set(arrays["boundary_triangles"][arrays["boundary_group_ids"] == 0].ravel())
        right = set(arrays["boundary_triangles"][arrays["boundary_group_ids"] == 1].ravel())
        assert left & right
    bad = {**mesh, "gmsh_boundary_triangles": mesh["gmsh_boundary_triangles"][:-1]}
    with pytest.raises(ValueError, match="split/deleted/added"):
        verify_volume_mesh(
            bad,
            source["boundary"],
            source["faces"],
            source["groups"],
            source["face_to_group"],
            cfg["caps"],
        )
    wrong_labels = mesh["gmsh_boundary_face_ids"].copy()
    wrong_labels[0] = len(source["faces"]) if wrong_labels[0] != len(source["faces"]) else 1
    with pytest.raises(ValueError, match="provenance"):
        verify_volume_mesh(
            {**mesh, "gmsh_boundary_face_ids": wrong_labels},
            source["boundary"],
            source["faces"],
            source["groups"],
            source["face_to_group"],
            cfg["caps"],
        )
    with pytest.raises(RuntimeError, match="resource cap"):
        verify_volume_mesh(
            mesh,
            source["boundary"],
            source["faces"],
            source["groups"],
            source["face_to_group"],
            {**cfg["caps"], "max_nodes": 0},
        )
    zero = mesh["tetrahedra"].copy()
    zero[0, 1] = zero[0, 0]
    with pytest.raises(ValueError, match="Zero-volume"):
        verify_volume_mesh(
            {**mesh, "tetrahedra": zero},
            source["boundary"],
            source["faces"],
            source["groups"],
            source["face_to_group"],
            cfg["caps"],
        )
    if kind == "cavity":
        center_mm = arrays["points_m"][arrays["tetrahedra"]].mean(axis=1) * 1000
        assert not ((center_mm > 2) & (center_mm < 18)).all(axis=1).any()
