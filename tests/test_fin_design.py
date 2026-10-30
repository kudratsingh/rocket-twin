"""Unit checks for the preliminary fin construction trade equations."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.analysis.fin_design import (
    cantilever_tip_deflection,
    construction_mass,
    constructions,
    distributed_tapered_tip_deflection,
    planform_geometry,
    rectangular_beam_ei,
    rectangular_root_stress,
    run_trade,
    sandwich_ei,
    timoshenko_tip_deflection,
)
from src.vehicle.schema import load_vehicle

ROOT = Path(__file__).resolve().parents[1]


def test_rectangular_cantilever_known_solution() -> None:
    young, width, thickness = 2.0e9, 0.08, 0.004
    force, span = 12.0, 0.16
    ei = rectangular_beam_ei(young, width, thickness)
    assert ei == pytest.approx(0.8533333333333333)
    assert ei == pytest.approx(young * width * thickness**3 / 12)
    stress = rectangular_root_stress(force * span, width, thickness)
    deflection = cantilever_tip_deflection(force, span, ei)
    assert stress == pytest.approx(9.0e6)
    assert stress == pytest.approx(6 * force * span / (width * thickness**2))
    assert deflection == pytest.approx(0.0192)
    assert deflection == pytest.approx(force * span**3 / (3 * ei))


def test_sandwich_zero_core_limit_matches_solid_double_skin_and_shear_limit() -> None:
    young, width, skin = 3.0e9, 0.07, 0.001
    sandwich_limit = sandwich_ei(young, width, skin, 0.0)
    solid_double_skin = rectangular_beam_ei(young, width, 2 * skin)
    assert sandwich_limit == pytest.approx(solid_double_skin)

    force, span = 8.0, 0.08
    ei = sandwich_ei(young, width, skin, 0.003)
    bend, shear, combined = timoshenko_tip_deflection(force, span, ei, 1.0e20, width * 0.003)
    assert shear < bend * 1.0e-12
    assert combined == pytest.approx(bend)


def test_distributed_rectangle_known_solution_and_solid_thickness_scaling() -> None:
    young, width, thickness, force, span = 2.0e9, 0.08, 0.004, 12.0, 0.16
    ei_per_width = young * thickness**3 / 12.0
    _, _, deflection = distributed_tapered_tip_deflection(force, span, width, width, ei_per_width)
    ei = rectangular_beam_ei(young, width, thickness)
    assert deflection == pytest.approx(force * span**3 / (8 * ei))
    doubled_ei_per_width = young * (2 * thickness) ** 3 / 12.0
    _, _, doubled_thickness_deflection = distributed_tapered_tip_deflection(
        force, span, width, width, doubled_ei_per_width
    )
    assert deflection / doubled_thickness_deflection == pytest.approx(8.0)


def test_distributed_sandwich_high_core_shear_modulus_limit() -> None:
    force, span, chord = 8.0, 0.08, 0.07
    skin, core = 0.001, 0.003
    ei_per_width = sandwich_ei(3.0e9, 1.0, skin, core)
    bend, shear, combined = distributed_tapered_tip_deflection(
        force, span, chord, chord, ei_per_width, 1.0e24, core
    )
    ei_full = sandwich_ei(3.0e9, chord, skin, core)
    assert bend == pytest.approx(force * span**3 / (8 * ei_full))
    assert shear < bend * 1.0e-12
    assert combined == pytest.approx(bend)


def test_fin_design_trade_builds_all_candidates_and_four_mode_static_overlays() -> None:
    config_path = ROOT / "configs/studies/wo03-fin-design.yaml"
    config = yaml.safe_load(config_path.read_text())
    assert len(constructions(config)) == 20
    result = run_trade(config_path, ROOT)
    assert len(result["architecture_rows"]) == 40
    assert len(result["load_rows"]) == 80
    assert len(result["static_rows"]) == 320
    assert {row["dynamic_pressure_pa"] for row in result["load_rows"]} == {25000.0, 40000.0}
    current_ply = next(
        row
        for row in result["load_rows"]
        if row["architecture"] == "G80-performance-solid-plywood-2mm"
        and row["load_case_id"] == "current-25kpa-5deg"
    )
    assert current_ply["force_per_fin_n"] == pytest.approx(39.843676889364424)
    assert current_ply["root_moment_nm"] == pytest.approx(1.4166640671774018)
    assert current_ply["root_skin_stress_pa"] == pytest.approx(13_281_225.62978814)
    assert current_ply["tip_total_deflection_m"] == pytest.approx(0.03187494151149154)
    assert current_ply["distributed_tip_total_deflection_m"] == pytest.approx(0.01127039081241226)
    assert current_ply["screen_status_basis"].startswith("conservative tip-load upper")
    comparison = result["reference_2d_comparison"]
    if comparison["status"].startswith("identity and load checks match"):
        assert comparison["fea_max_displacement_m"] == pytest.approx(0.01205316)
        assert comparison["distributed_beam_displacement_m"] == pytest.approx(0.01127039081241226)
    finless = [row for row in result["static_rows"] if row["mode"] == "G12-finless"]
    assert len(finless) == 80
    assert all(row["applicability"].startswith("not applicable") for row in finless)
    assert all(row["growth_allowance_kg"] == pytest.approx(0.05) for row in finless)
    assert not any("von Mises" in row["criteria"] for row in result["load_rows"])


def test_trapezoid_and_tab_material_volumes_are_exact() -> None:
    vehicle = load_vehicle("configs/vehicle/platform/performance.yaml")
    fin = next(part for part in vehicle.parts if part.type == "fin_set")
    config = yaml.safe_load((ROOT / "configs/studies/wo03-fin-design.yaml").read_text())
    ply = next(item for item in constructions(config) if item.name == "solid-plywood-2mm")
    geometry = planform_geometry(fin)
    mass = construction_mass(fin, ply, geometry)
    expected_tab = (
        fin.cad.parameters["tab_depth_mm"]
        * fin.geometry["thickness_m"]
        * fin.cad.parameters["tab_length_mm"]
        * fin.geometry["count"]
        * 1e-6
    )
    expected_tab *= ply.thickness_m / fin.geometry["thickness_m"]
    expected_planform = geometry["area_per_fin_m2"] * fin.geometry["count"] * 0.002
    assert mass["tab_volume_m3"] == pytest.approx(expected_tab)
    assert mass["planform_volume_m3"] == pytest.approx(expected_planform)
    assert mass["fin_mass_kg"] == pytest.approx(
        (expected_planform + expected_tab) * ply.density_kg_m3
    )
