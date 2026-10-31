"""Physical coverage guards for the isolated multilayer thermal correction."""

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from scripts.wo03_multilayer_shield import construct_candidate, subtract_intervals
from src.vehicle.schema import load_vehicle


def test_ring_windows_remain_uncovered_even_when_cuts_overlap() -> None:
    # A nested cut, a touching cut and out-of-span cuts must neither duplicate
    # foil material nor restore opacity across a physical ring window.
    assert subtract_intervals(1, 10, [(4, 6), (5, 7), (2, 3), (3, 4), (-2, 0), (11, 12)]) == [
        (1, 2),
        (7, 10),
    ]
    assert subtract_intervals(1, 10, [(0, 11)]) == []


def test_fixed_shield_correction_cannot_be_applied_to_a_moving_cassette() -> None:
    vehicle = load_vehicle("configs/vehicle/platform/tvc-finned.yaml")
    before = vehicle.model_dump_json()
    cfg = yaml.safe_load(Path("configs/studies/wo03-multilayer-shield.yaml").read_text())
    with pytest.raises(ValueError, match="fixed mounts only"):
        construct_candidate(vehicle, deepcopy(cfg), [0.018, 0.022], {})
    assert vehicle.model_dump_json() == before
