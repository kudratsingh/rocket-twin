import numpy as np
import pytest
import vtk
from vtk.util.numpy_support import numpy_to_vtk

from scripts.wo03_elmer_bridge_diagnostic import analyze_arrays, read_vtu, reciprocal


def test_force_gate_and_invalid_vectors():
    ids = [1, 2]
    coords = {1: np.array([0.0, 0.0, 0.0]), 2: np.array([0.0, 0.0, 1.0])}
    u = {1: np.zeros(3), 2: np.array([0.0, 0.0, 0.001])}
    R = {1: np.array([0.0, 0.0, -150.0]), 2: np.zeros(3)}
    loads = {2: "150"}
    assert analyze_arrays(ids, coords, u, R, [1], loads)["strict_force_status"] == "pass"
    assert (
        analyze_arrays(ids, coords, u, {1: np.zeros(3), 2: np.zeros(3)}, [1], loads)[
            "strict_force_status"
        ]
        == "fail"
    )
    with pytest.raises(ValueError):
        analyze_arrays(ids, coords, {1: u[1]}, R, [1], loads)
    with pytest.raises(ValueError):
        analyze_arrays(ids, coords, {1: u[1], 2: np.array([0.0, 0.0, np.nan])}, R, [1], loads)


def test_missing_reaction_field_rejected(tmp_path):
    nodes = {1: np.array([0.0, 0.0, 0.0]), 2: np.array([0.0, 0.0, 1.0])}
    pts = vtk.vtkPoints()
    pts.SetData(numpy_to_vtk(np.array(list(nodes.values())), deep=True))
    grid = vtk.vtkUnstructuredGrid()
    grid.SetPoints(pts)
    arr = numpy_to_vtk(np.zeros((2, 3)), deep=True)
    arr.SetName("displacement")
    grid.GetPointData().AddArray(arr)
    path = tmp_path / "missing.vtu"
    writer = vtk.vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    assert writer.Write() == 1
    with pytest.raises(ValueError, match="displacement loads"):
        read_vtu(path, nodes, [1], {2: "150"})


def test_reciprocity_reports_difference_without_invented_tolerance():
    loads = {1: "10"}
    u1 = {1: np.array([0.0, 0.0, 0.2])}
    u2 = {1: np.array([0.0, 0.0, 0.3])}
    r = reciprocal(loads, u1, loads, u2)
    assert r["status"] == "outside_output_encoding_bound"
    assert r["absolute_difference_Nm"] == pytest.approx(1.0)
    assert reciprocal(loads, u1, loads, u1)["status"] == "consistent_with_output_encoding"


def test_original_decimal_token_rounding_bound():
    from scripts.wo03_elmer_bridge_diagnostic import decimal_token_half_width

    assert decimal_token_half_width("1.230e+1") == pytest.approx(0.005)
    assert decimal_token_half_width("10") == pytest.approx(0.5)
