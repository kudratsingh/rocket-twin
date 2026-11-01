"""No-solver checks for reaction-fixture mechanics and native output labels."""

import numpy as np
import pytest

from scripts.wo03_ccx_reaction_fixture import (
    _area,
    _emit_deck,
    assess_native_fixture,
    nonnative_preflight,
)
from scripts.wo03_g80_bridge_fea import parse_native_dat


def test_analytic_references_and_explicit_step_reset():
    assert _area("A") == 16
    nodes = {1: np.array([-10.0, 0.0, 0.0]), 2: np.array([-10.0, 0.0, 20.0])}
    deck = _emit_deck(
        "A", nodes, {1: [1] * 10}, {"MAT": {1}}, {1}, [{2: np.array([0, 0, 150.0])}] * 2
    )
    assert deck.count("*CLOAD,OP=NEW") == 2
    assert deck.count("*NODE PRINT,NSET=ALL\nRF") == 2
    assert deck.count("*NODE PRINT,NSET=SUPPORT\nRF") == 2
    assert "*MPC" not in deck


def test_parser_keeps_all_and_support_force_blocks_distinct(tmp_path):
    data = """ S T E P 1
 forces (fx,fy,fz) for set ALL and time 0.1000000E+01
 1 0.000000E+00 0.000000E+00 1.500000E+02

 forces (fx,fy,fz) for set SUPPORT and time 0.1000000E+01
 1 0.000000E+00 0.000000E+00 -1.500000E+02
"""
    p = tmp_path / "tiny.dat"
    p.write_text(data)
    blocks = parse_native_dat(p)
    assert blocks[(1, "forces", "ALL")][0]["values"][2] == 150
    assert blocks[(1, "forces", "SUPPORT")][0]["values"][2] == -150


def test_preflight_rejects_wrong_known_moment():
    meta = {
        "step_nodal_forces_N": [{"1": [0, 0, 150]}, {"1": [0, 0, 150]}],
        "step_applied_moment_about_global_origin_Nmm": [[0, 0, 0], [0, 1499, 0]],
    }
    deck = (
        "*BOUNDARY\nSUPPORT,1,3,0\n"
        + "*STEP\n*CLOAD,OP=NEW\n" * 2
        + "*NODE PRINT,NSET=ALL\nU\n*NODE PRINT,NSET=ALL\nRF\n*NODE PRINT,NSET=SUPPORT\nRF\n"
    )
    with pytest.raises(ValueError, match="moment"):
        nonnative_preflight(meta, deck)


def test_reader_rejects_false_equilibrium_and_wrong_deflection(monkeypatch, tmp_path):
    coords = {
        1: [-10, 0, 0],
        2: [-10, 0, 20],
        3: [0, 0, 0],
        4: [0, 0, 20],
        5: [10, 0, 0],
        6: [10, 0, 20],
    }
    meta = {
        "node_coordinates_mm": {str(k): v for k, v in coords.items()},
        "support_node_ids": [1, 3, 5],
        "top_node_ids_by_bar": [[2], [4], [6]],
        "expected_free_end_displacement_mm_by_step_bar": [[0.0625] * 3, [0.1875, 0, 0]],
        "step_nodal_forces_N": [
            {"2": [0, 0, 50], "4": [0, 0, 50], "6": [0, 0, 50]},
            {"2": [0, 0, 150]},
        ],
    }

    def row(n, z):
        return {"id": n, "values": [0.0, 0.0, z], "rounding_half_width": [1e-10] * 3}

    sections = {}
    for step in (1, 2):
        uz = {2: 0.0625, 4: 0.0625, 6: 0.0625} if step == 1 else {2: 0.1875, 4: 0, 6: 0}
        sections[(step, "displacements", "ALL")] = [row(n, uz.get(n, 0)) for n in coords]
        sections[(step, "forces", "ALL")] = [row(n, 0) for n in coords]
        sections[(step, "forces", "SUPPORT")] = [
            row(n, -50 if step == 1 else -150 if n == 1 else 0) for n in [1, 3, 5]
        ]
    monkeypatch.setattr("scripts.wo03_g80_bridge_fea.parse_native_dat", lambda _path: sections)
    assert assess_native_fixture(meta, tmp_path / "none")["status"] == "passed"
    sections[(1, "forces", "SUPPORT")][0]["values"][2] = -49
    assert assess_native_fixture(meta, tmp_path / "none")["status"] == "failed_or_unavailable"
    sections[(1, "forces", "SUPPORT")][0]["values"][2] = -50
    sections[(1, "displacements", "ALL")][1]["values"][2] = 0.05
    assert assess_native_fixture(meta, tmp_path / "none")["status"] == "failed_or_unavailable"
