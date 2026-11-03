"""Strict fixture coverage for the diagnostic CCX exporter."""

import pytest

from scripts.wo03_f2_c1_export_fields import read_deck, read_fields


def fixture(tmp_path):
    deck = tmp_path / "case.inp"
    deck.write_text(
        "*NODE\n"
        + "".join(f"{i},{i},0,0\n" for i in range(1, 11))
        + "*ELEMENT,TYPE=C3D10,ELSET=WOOD\n17,1,2,3,4,5,6,7,8,9,10\n*MATERIAL,NAME=OTHER\n"
    )
    node_section = "".join(f"{i} 0.1 0.2 0.3\n" for i in range(1, 11))
    stress_section = "".join(f"17 {ip} 1 2 3 4 5 {ip}\n" for ip in range(1, 5))
    fields = "".join(
        f" S T E P {phase}\n displacements (vx,vy,vz) for set ALLN and time {phase}.0\n{node_section} stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set WOOD and time {phase}.0\n{stress_section}"
        for phase in (1, 2)
    )
    dat = tmp_path / "case.dat"
    dat.write_text(fields)
    return deck, dat, fields


def test_exact_ccx_order_and_two_full_phases(tmp_path):
    deck, dat, _ = fixture(tmp_path)
    nodes, elements = read_deck(deck)
    u, stress = read_fields(dat, nodes, elements)
    assert elements[17] == list(range(1, 11))
    assert u.shape == (2, 10, 3)
    assert stress.shape == (2, 1, 4, 6)
    assert stress[1, 0, 3, 5] == 4


@pytest.mark.parametrize(
    "old,new",
    [
        ("17 4 1 2 3 4 5 4\n", ""),
        ("10 0.1 0.2 0.3\n", ""),
        ("17 4 1 2 3 4 5 4\n", "17 3 1 2 3 4 5 4\n"),
        (" S T E P 2", " S T E P 3"),
    ],
)
def test_incomplete_duplicate_or_wrong_phase_fails_closed(tmp_path, old, new):
    deck, dat, data = fixture(tmp_path)
    dat.write_text(data.replace(old, new, 1))
    with pytest.raises(ValueError):
        read_fields(dat, *read_deck(deck))


def test_missing_connectivity_node_fails_closed(tmp_path):
    deck, _, _ = fixture(tmp_path)
    deck.write_text(deck.read_text().replace(",9,10\n", ",9,99\n"))
    with pytest.raises(ValueError, match="connectivity"):
        read_deck(deck)


def test_recorded_metadata_retains_diagnostic_boundaries():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    metadata = json.loads(
        (root / "runs/wo03-g80-f2-c1-field-export-20261103-v1/metadata.json").read_text()
    )
    assert metadata["active_vehicle_compatible"] is False
    assert metadata["installed_strength_accepted"] is False
    assert "three-grid convergence unavailable" in metadata["status"]
    assert "32.3" in metadata["geometry"] and "32.2" in metadata["geometry"]
    assert metadata["array_shapes"]["stress_mpa"] == [2, 51503, 4, 6]
    assert metadata["integration_points"] == [1, 2, 3, 4]
