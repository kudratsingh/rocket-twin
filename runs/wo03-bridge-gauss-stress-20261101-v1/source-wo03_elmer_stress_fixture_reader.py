"""Fail-closed reader for source-declared nodal stress components."""

from pathlib import Path

import numpy as np

from scripts.wo03_elmer_stress_fixture import ORDER, check_stress


def read_stress(path: Path, meta: dict):
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy

    vtk.vtkSMPTools.Initialize(1)
    vtk.vtkMultiThreader.SetGlobalMaximumNumberOfThreads(1)
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(path))
    reader.Update()
    grid = reader.GetOutput()
    if grid.GetPoints() is None:
        raise ValueError("Missing VTU points")
    pts = vtk_to_numpy(grid.GetPoints().GetData())
    coords = {int(k): np.asarray(v) * 1e-3 for k, v in meta["node_coordinates_mm"].items()}
    ids = sorted(coords)
    if (
        len(ids) != 593
        or pts.dtype != np.float64
        or pts.shape != (593, 3)
        or not np.isfinite(pts).all()
    ):
        raise ValueError("Invalid node mapping")
    lookup = {tuple(np.round(x, 12)): i for i, x in enumerate(pts)}
    if len(lookup) != 593:
        raise ValueError("Duplicate coordinates")
    order = [lookup[tuple(np.round(coords[n], 12))] for n in ids]
    if np.max(np.abs(pts[order] - np.array([coords[n] for n in ids]))) > 1e-12:
        raise ValueError("Node coordinates mismatch")
    pd, cd = grid.GetPointData(), grid.GetCellData()
    names = [pd.GetArrayName(i) for i in range(pd.GetNumberOfArrays())]
    cnames = [cd.GetArrayName(i) for i in range(cd.GetNumberOfArrays())]
    fields = {}
    for suffix in ORDER:
        name = "Stress_" + suffix
        matches = [n for n in names if n and n.lower() == name.lower()]
        if len(matches) != 1 or any(n and n.lower() == name.lower() for n in cnames):
            raise ValueError("Missing, duplicate or ambiguous association: " + name)
        field = vtk_to_numpy(pd.GetArray(matches[0]))
        if field.dtype != np.float64 or field.shape != (593,) or not np.isfinite(field).all():
            raise ValueError("Invalid Float64 scalar: " + name)
        fields[suffix] = field[order]
    bar = [{int(n) for n in group} for group in meta["bar_node_ids_by_bar"]]
    if (
        len(bar) != 3
        or any(bar[i] & bar[j] for i in range(3) for j in range(i))
        or set.union(*bar) != set(ids)
    ):
        raise ValueError("Invalid bar ownership")
    mask = np.asarray([n in bar[0] for n in ids])
    result = check_stress(fields, mask)
    result["association"] = "PointData"
    result["dtype"] = "float64"
    result["node_count"] = 593
    return result
