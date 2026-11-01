import json
from pathlib import Path

import numpy as np
import pytest
import vtk
from vtk.util.numpy_support import numpy_to_vtk

from scripts.wo03_elmer_structural_fixture import evaluate_vtu, sif


@pytest.fixture
def meta():
    p = Path("build/wo03-ccx-reaction-fixture-preflight-v6-b/mesh-meta.json")
    if not p.exists():
        pytest.skip("Saved fixture metadata is local-only")
    return json.loads(p.read_text())


def make_vtu(path, meta, *, include_load=True, bad_displacement=False, bad_sign=False):
    coords = {int(k): np.asarray(v) * 1e-3 for k, v in meta["node_coordinates_mm"].items()}
    ids = sorted(coords)
    idx = {n: i for i, n in enumerate(ids)}
    u = np.zeros((len(ids), 3))
    f = np.zeros((len(ids), 3))
    forces = (50.0, 50.0, 50.0)
    for b, nodes in enumerate(meta["bar_node_ids_by_bar"]):
        for n in nodes:
            z = coords[n][2] * 1000
            u[idx[n], 2] = forces[b] / 16 * (min(z, 10) / 100 + max(z - 10, 0) / 10000) * 1e-3
        for n in meta["support_node_ids_by_bar"][b]:
            f[idx[n], 2] = (
                (-1 if not bad_sign else 1) * forces[b] / len(meta["support_node_ids_by_bar"][b])
            )
    if bad_displacement:
        u[idx[2], 0] = 1e-6
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(np.array([coords[n] for n in ids]), deep=True))
    grid = vtk.vtkUnstructuredGrid()
    grid.SetPoints(points)
    for name, values in [("Displacement", u), ("Displacement Loads", f)]:
        if name == "Displacement Loads" and not include_load:
            continue
        arr = numpy_to_vtk(values, deep=True)
        arr.SetName(name)
        grid.GetPointData().AddArray(arr)
    writer = vtk.vtkXMLUnstructuredGridWriter()
    writer.SetFileName(str(path))
    writer.SetInputData(grid)
    assert writer.Write() == 1


def test_sif_uses_physical_si_tractions():
    text = sif(Path("/tmp/StressSolve.dylib"), (50.0, 50.0, 50.0))
    assert text.count("Force 3 = Real 3125000") == 3
    assert "Calculate Loads = Logical True" in text


def test_reader_respects_known_answer_and_missing_force(tmp_path, meta):
    f = tmp_path / "field.vtu"
    make_vtu(f, meta)
    r = evaluate_vtu(f, meta, (50.0, 50.0, 50.0))
    assert r["force_status"] == "pass"
    make_vtu(f, meta, include_load=False)
    with pytest.raises(ValueError, match="Displacement Loads"):
        evaluate_vtu(f, meta, (50.0, 50.0, 50.0))
    make_vtu(f, meta, bad_displacement=True)
    with pytest.raises(ValueError, match="displacement gate"):
        evaluate_vtu(f, meta, (50.0, 50.0, 50.0))
    make_vtu(f, meta, bad_sign=True)
    r = evaluate_vtu(f, meta, (50.0, 50.0, 50.0))
    assert r["force_status"] == "fail"
