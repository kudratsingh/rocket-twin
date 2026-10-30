"""Candidate acceptance must analyze its own minimum manufactured thickness."""

import pytest

from scripts.wo03_fin_acceptance import _minimum_thickness_copy
from src.vehicle.schema import load_vehicle


def test_thinner_candidate_never_inherits_historical_6mm_minimum() -> None:
    vehicle = load_vehicle("configs/vehicle/platform/tvc-finned.yaml")
    fin = next(part for part in vehicle.parts if part.type == "fin_set").model_copy(deep=True)
    fin.geometry["thickness_m"] = 0.005
    minimum = _minimum_thickness_copy(fin)
    assert minimum.geometry["thickness_m"] == pytest.approx(0.0047)
    assert minimum.cad_mass is None
    assert fin.geometry["thickness_m"] == 0.005
    fin.engineering.tolerances_mm.pop("thickness")
    with pytest.raises(ValueError, match="spec-owned thickness tolerance"):
        _minimum_thickness_copy(fin)
