"""Exercise strict multi-step CalculiX output and equilibrium accounting."""

from pathlib import Path

import numpy as np
import pytest

from scripts.wo03_g80_bridge_fea import (
    convergence_changes,
    evaluate_balance,
    external_work_energy,
    parse_native_dat,
    summarize_stresses,
)


def test_two_steps_forces_moments_and_work(tmp_path: Path):
    dat = tmp_path / "case.dat"
    dat.write_text("""
 S T E P       1
 displacements (vx,vy,vz) for set ALL and time 0.1000000E+01
 1 0.000000E+00 0.000000E+00 2.000000E-03
 forces (fx,fy,fz) for set SUPPORT and time 0.1000000E+01
 2 0.000000E+00 0.000000E+00 -1.000000E+02
 stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set BRIDGE and time 0.1000000E+01
 9 1 1.000000E+00 2.000000E+00 3.000000E+00 4.000000E+00 5.000000E+00 6.000000E+00
 S T E P       2
 displacements (vx,vy,vz) for set ALL and time 0.2000000E+01
 1 0.000000E+00 0.000000E+00 3.000000E-03
 forces (fx,fy,fz) for set SUPPORT and time 0.2000000E+01
 2 0.000000E+00 0.000000E+00 -1.000000E+02
 stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set BRIDGE and time 0.2000000E+01
 9 1 1.000000E+00 2.000000E+00 3.000000E+00 4.000000E+00 5.000000E+00 6.000000E+00
 """)
    sections = parse_native_dat(dat)
    assert len(sections) == 6
    nodes = {1: [2.0, 3.0, 0.0], 2: [2.0, 3.0, 0.0]}
    forces = {1: [0.0, 0.0, 100.0]}
    result = evaluate_balance(nodes, forces, sections[(2, "forces", "SUPPORT")])
    assert result["applied_moment_Nmm"] == pytest.approx([300, -200, 0])
    assert result["force_residual_N"] == pytest.approx([0, 0, 0])
    assert result["force_balance_status"] == "unavailable_print_precision"
    assert result["moment_residual_Nmm"] == pytest.approx([0, 0, 0])
    assert external_work_energy(forces, sections[(2, "displacements", "ALL")]) == pytest.approx(
        0.15
    )


def test_stress_and_displacement_convergence_limits_are_distinct():
    assert convergence_changes([1.0, 1.04, 1.09], 0.05)["last_change_status"] == "pass"
    assert convergence_changes([1.0, 1.04, 1.14], 0.10)["last_change_status"] == "pass"
    assert convergence_changes([0.0, 0.0, 1.0], 0.10)["last_change_status"] == "unavailable"
    with pytest.raises(ValueError):
        convergence_changes([1.0, 2.0, np.nan], 0.10)


def test_four_point_stress_coverage_and_extrema():
    rows = [
        {"id": 9, "integration_point": i, "values": [float(i), 0, 0, 0, 0, 0]} for i in range(1, 5)
    ]
    result = summarize_stresses(rows, [9])
    assert result["Sxx"]["minimum_MPa"] == 1.0
    assert result["Sxx"]["maximum_MPa"] == 4.0
    with pytest.raises(ValueError):
        summarize_stresses(rows[:-1], [9])


def test_failed_actual_worker_persists_resource_accounting(tmp_path, monkeypatch):
    import json

    import scripts.wo03_g80_bridge_adapter as adapter
    import scripts.wo03_g80_bridge_fea as driver

    def fail(*_args):
        raise RuntimeError("synthetic input failure")

    monkeypatch.setattr(driver, "OUT", tmp_path)
    monkeypatch.setattr(driver.resource, "setrlimit", lambda *_args: None)
    monkeypatch.setattr(adapter, "build_case", fail)
    cfg = {"worker_cpu_limit_s": 60, "maximum_nodes": 50000, "maximum_tetrahedra": 75000}
    with pytest.raises(RuntimeError, match="synthetic input failure"):
        driver.actual_worker("bridge_1p5mm", cfg)
    record = json.loads((tmp_path / "bridge_1p5mm-resources.json").read_text())
    assert record["name"] == "bridge_1p5mm"
    assert record["worker_user_s"] >= 0
    assert record["worker_peak_rss_bytes_macos"] > 0


def test_geometry_only_worker_blocks_mesh_generation(tmp_path, monkeypatch):
    import gmsh

    import scripts.wo03_g80_bridge_adapter as adapter
    import scripts.wo03_g80_bridge_fea as driver

    def fake_builder(_folder, _mesh_size, _node_cap, _tet_cap, *, geometry_only):
        assert geometry_only is True
        gmsh.model.mesh.generate(3)

    monkeypatch.setattr(driver, "OUT", tmp_path)
    monkeypatch.setattr(driver.resource, "setrlimit", lambda *_args: None)
    monkeypatch.setattr(adapter, "build_case", fake_builder)
    with pytest.raises(RuntimeError, match="mesh generation is forbidden"):
        driver.geometry_only_worker({"maximum_nodes": 50000, "maximum_tetrahedra": 75000})
    assert (tmp_path / "geometry-worker-resources.json").is_file()
