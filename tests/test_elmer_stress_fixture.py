import numpy as np
import pytest

from scripts.wo03_elmer_stress_fixture import ORDER, check_stress


def test_named_stress_components_and_missing_field():
    values = {key: np.zeros(4) for key in ORDER}
    values["zz"][:2] = 9_375_000
    result = check_stress(values, [True, True, False, False])
    assert result["original_axial_criterion_pass"]
    assert result["all_components_primary_2pct_scale_pass"]
    values["xz"][2] = 200_000
    assert not check_stress(values, [True, True, False, False])[
        "all_components_primary_2pct_scale_pass"
    ]
    del values["yz"]
    with pytest.raises(ValueError):
        check_stress(values, [True, True, False, False])


def test_wrong_voigt_component_fails():
    fields = {key: np.zeros(2) for key in ORDER}
    fields["yz"][0] = 9_375_000
    assert not check_stress(fields, [True, False])["original_axial_criterion_pass"]


def test_vtu_stress_fields_are_named_point_scalars(tmp_path):
    import vtk
    from vtk.util.numpy_support import numpy_to_vtk

    from scripts.wo03_elmer_stress_fixture_reader import read_stress

    grid = vtk.vtkUnstructuredGrid()
    points = vtk.vtkPoints()
    points.SetData(
        numpy_to_vtk(
            np.column_stack((np.arange(593, dtype=np.float64), np.zeros((593, 2)))), deep=True
        )
    )
    grid.SetPoints(points)
    for suffix in ORDER:
        data = np.zeros(593, dtype=np.float64)
        if suffix == "zz":
            data[:200] = 9_375_000
        array = numpy_to_vtk(data, deep=True)
        array.SetName("Stress_" + suffix)
        grid.GetPointData().AddArray(array)
    meta = {
        "node_coordinates_mm": {str(i + 1): [i * 1000, 0, 0] for i in range(593)},
        "bar_node_ids_by_bar": [list(range(1, 201)), list(range(201, 401)), list(range(401, 594))],
    }
    path = tmp_path / "sample.vtu"
    writer = vtk.vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    assert writer.Write() == 1
    assert read_stress(path, meta)["all_components_primary_2pct_scale_pass"]
    for suffix in ORDER:
        grid.GetPointData().GetArray("Stress_" + suffix).SetName("stress_" + suffix)
    writer.SetInputData(grid)
    assert writer.Write() == 1
    assert read_stress(path, meta)["all_components_primary_2pct_scale_pass"]
    duplicate = numpy_to_vtk(np.zeros(593, dtype=np.float64), deep=True)
    duplicate.SetName("Stress_xx")
    grid.GetPointData().AddArray(duplicate)
    writer.SetInputData(grid)
    assert writer.Write() == 1
    with pytest.raises(ValueError, match="Stress_xx"):
        read_stress(path, meta)
    grid.GetPointData().RemoveArray("Stress_xx")
    grid.GetPointData().RemoveArray("stress_xz")
    writer.SetInputData(grid)
    assert writer.Write() == 1
    with pytest.raises(ValueError, match="Stress_xz"):
        read_stress(path, meta)
