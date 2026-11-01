"""Exercise mesh, exact field and double-precision VTU I/O without Elmer."""

from pathlib import Path

import numpy as np
import pytest
import vtk
import yaml
from vtk.util.numpy_support import numpy_to_vtk

from scripts.wo03_elmer_thermal_comparison import (
    ROOT,
    continuous_p2_bound,
    enrich_quadratic,
    envelope,
    expected_field,
    exterior,
    find_vtu,
    quadratic_quadrature_check,
    read_deck,
    read_diffusive_flux,
    read_vtu,
    robin_quadrature_error,
    sif,
    write_mesh,
)


def test_retained_mesh_and_spatial_boundary():
    settings = yaml.safe_load(
        (ROOT / "configs/studies/wo03-elmer-thermal-comparison.yaml").read_text()
    )
    cfg = yaml.safe_load((ROOT / settings["reference"]).read_text())
    path = ROOT / settings["meshes"][2]["path"]
    if not path.exists():
        # The archive is deliberately ignored, so test the SIF without claiming it is present.
        assert "HeatSolveVec" in sif("B", cfg)
        return
    nodes, cells = read_deck(path)
    boundary = exterior(nodes, cells, cfg["dimensions_m"])
    assert (len(nodes), len(cells), len(boundary)) == (27, 48, 48)
    assert [sum(side == n for side, _, _ in boundary) for n in range(1, 7)] == [8] * 6
    qnodes, qcells, qboundary = enrich_quadratic(nodes, cells, boundary)
    assert len(qnodes) == 125 and all(len(cell) == 10 for cell in qcells.values())
    assert all(
        len(face) == 6 and set(face).issubset(qcells[parent]) for _, parent, face in qboundary
    )
    assert max(quadratic_quadrature_check().values()) < 1e-13
    assert len(envelope(cfg, 30)) == 2
    assert sif("B", cfg).count("External Temperature At IP = Logical True") == 6


def test_vtu_float64_round_trip(tmp_path: Path):
    cfg = yaml.safe_load((ROOT / "configs/studies/wo03-thermal-error-isolation.yaml").read_text())
    coords = np.array([[0.0, 0.0, 0.0], [0.0002, 0.0, 0.0], [0.0, 0.001, 0.0], [0.0, 0.0, 0.187]])
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(coords, deep=True))
    grid = vtk.vtkUnstructuredGrid()
    grid.SetPoints(points)
    tet = vtk.vtkTetra()
    for i in range(4):
        tet.GetPointIds().SetId(i, i)
    grid.InsertNextCell(tet.GetCellType(), tet.GetPointIds())
    arr = numpy_to_vtk(expected_field(coords, "A", cfg), deep=True)
    arr.SetName("temperature")
    grid.GetPointData().AddArray(arr)
    file = tmp_path / "field.vtu"
    writer = vtk.vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(file))
    writer.SetInputData(grid)
    writer.SetDataModeToAppended()
    assert writer.Write() == 1
    result = read_vtu(file, {i + 1: tuple(p) for i, p in enumerate(coords)}, "A", cfg)
    assert result["field_type"] == "float64"
    assert result["max_nodal_error_k"] == 0
    assert result["global_balance_w"] is None


def test_three_point_rule_exposes_cubic_load_error():
    cfg = {
        "case_b": {"amplitude_k": 1, "base_k": 0},
        "dimensions_m": [1, 1, 1],
        "conductivity_w_m_k": 1,
    }
    nodes = {1: (0.0, 0.0, 0.0), 2: (1.0, 0.0, 0.0), 3: (0.0, 0.0, 1.0)}
    result = robin_quadrature_error(nodes, [(3, 1, (1, 2, 3))], cfg, 1)
    assert abs(result["max_abs_assembled_nodal_load_error_w"] - 1 / 720) < 1e-15
    assert abs(result["signed_net_load_error_w"]) < 1e-15


def test_native_flux_metadata_sign_and_label_guard(tmp_path: Path):
    (tmp_path / "diffusive-flux.dat.names").write_text(
        "\n".join(f"{i}: diffusive flux: temperature over bc {i}" for i in range(1, 7))
    )
    (tmp_path / "diffusive-flux.dat").write_text("1 2 3 4 5 6\n")
    result = read_diffusive_flux(tmp_path)
    assert result["outward_conductive_heat_w"] == {str(i): -float(i) for i in range(1, 7)}


def test_single_tet_quadratic_node_order_and_boundary_tags(tmp_path: Path):
    nodes = {1: (0.0, 0.0, 0.0), 2: (1.0, 0.0, 0.0), 3: (0.0, 1.0, 0.0), 4: (0.0, 0.0, 1.0)}
    cells = {1: (1, 2, 3, 4)}
    boundary = [(1, 1, (1, 4, 3)), (3, 1, (1, 2, 4)), (5, 1, (1, 3, 2))]
    qnodes, qcells, qboundary = enrich_quadratic(nodes, cells, boundary)
    assert qcells[1][:4] == (1, 2, 3, 4)
    assert [qnodes[i] for i in qcells[1][4:]] == [
        (0.5, 0.0, 0.0),
        (0.5, 0.5, 0.0),
        (0.0, 0.5, 0.0),
        (0.0, 0.0, 0.5),
        (0.5, 0.0, 0.5),
        (0.0, 0.5, 0.5),
    ]
    p0, p1, p2, p3 = (np.array(nodes[i]) for i in cells[1])
    assert np.linalg.det(np.stack([p1 - p0, p2 - p0, p3 - p0])) > 0
    assert [side for side, _, _ in qboundary] == [1, 3, 5]
    assert all(set(face).issubset(qcells[parent]) for _, parent, face in qboundary)
    write_mesh(tmp_path / "mesh", qnodes, qcells, qboundary)
    assert (tmp_path / "mesh" / "mesh.header").read_text().splitlines()[2:] == ["306 3", "510 1"]
    assert max(quadratic_quadrature_check().values()) < 1e-13


def test_continuous_quadratic_bound_is_conditional():
    cfg = yaml.safe_load((ROOT / "configs/studies/wo03-thermal-error-isolation.yaml").read_text())
    good = continuous_p2_bound("B_strong", cfg, 1e-7)
    assert good["continuous_error_bound_k"] == 2e-7
    assert good["continuous_envelope_status"] == "certified_by_bound"
    uncertain = continuous_p2_bound("B_strong", cfg, 1e-3)
    assert uncertain["continuous_envelope_status"] == "unavailable_bound_straddles"
    assert (
        continuous_p2_bound("A", cfg, 1e-8)["continuous_envelope_status"]
        == "unavailable_bound_straddles"
    )


def test_vtu_discovery_both_locations_and_ambiguity(tmp_path: Path):
    (tmp_path / "mesh").mkdir()
    with pytest.raises(ValueError, match="found 0"):
        find_vtu(tmp_path)
    root_file = tmp_path / "field_t0001.vtu"
    mesh_file = tmp_path / "mesh" / "field_t0001.vtu"
    root_file.touch()
    assert find_vtu(tmp_path) == root_file
    mesh_file.touch()
    with pytest.raises(ValueError, match="found 2"):
        find_vtu(tmp_path)
    root_file.unlink()
    assert find_vtu(tmp_path) == mesh_file
