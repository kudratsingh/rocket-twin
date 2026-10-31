"""Checks on fixture input generation; no solver or acceptance claim."""

import pytest
import yaml

from scripts.wo03_ccx_thermal_comparison import SOURCE, make_deck, parse_temperature, run_annular


def test_affine_deck_and_output_parser():
    cfg = yaml.safe_load(SOURCE.read_text())
    deck, nodes = make_deck(cfg, 2)
    assert len(nodes) == 27
    assert "*ELEMENT,TYPE=C3D4" in deck
    assert "308.15,36030.6" in deck
    assert parse_temperature("temperatures\n\n  1 5.731500E+02\n\n") == {1: 573.15}


def test_existing_failed_or_completed_annular_evidence_is_never_overwritten(tmp_path):
    record = tmp_path / "record.json"
    original = '{"annular": [{"returncode": 201}], "acceptance": "not established"}\n'
    record.write_text(original)
    with pytest.raises(FileExistsError, match="Preserve existing"):
        run_annular(tmp_path)
    assert record.read_text() == original
