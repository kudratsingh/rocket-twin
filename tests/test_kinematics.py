"""Spec-owned fixed shafts, real horn arms and frozen flat-linkage positions."""

import math

import numpy as np
import pytest

from src.cad.kinematics import linkage
from src.vehicle.schema import load_vehicle


def test_flat_horn_position_regression() -> None:
    v = load_vehicle("configs/vehicle/platform/tvc-finned.yaml")
    # Recorded pre-correction outputs. These check unchanged assembly kinematics,
    # not servo authority, strength or physical motion clearance.
    for p, y, expected in [
        (0, 0, [0, 0]),
        (5, 5, [8.653141016611759, 18.73500357472679]),
        (5, -5, [-9.688994008618437, 18.73500357472679]),
        (-5, 5, [8.653141016611759, -15.82460244009097]),
        (-5, -5, [-9.688994008618437, -15.82460244009097]),
    ]:
        assert [a["shaft_deg"] for a in linkage(v, p, y)["axes"]] == pytest.approx(expected)


def test_canted_horn_keeps_declared_shaft_and_six_mm_arm() -> None:
    v = load_vehicle("configs/vehicle/platform/tvc-finned.yaml")
    parts = {p.id: p for p in v.parts}
    horns, rods = parts["servo_horns"], parts["gimbal_links"]
    assert horns.cad and rods.cad
    for i, axis in enumerate([0, 1]):
        shaft, tip = horns.cad.parameters["segments_mm"][i]
        tip[axis] = shaft[axis] + 3
        tip[2] = shaft[2] + math.sqrt(27)
        rod_start = rods.cad.parameters["segments_mm"][i][0]
        rod_start[:] = [*tip[:2], tip[2] + 1000 * (horns.position_m - rods.position_m)]
    for p, y in [(0, 0), (0.5, -0.5), (-0.5, 0.5)]:
        result = linkage(v, p, y)
        for i, axis in enumerate(result["axes"]):
            assert axis["shaft_mm"] == pytest.approx([22, 0, 1012] if i == 0 else [0, 22, 1012])
            assert np.linalg.norm(np.array(axis["start_mm"]) - axis["shaft_mm"]) == pytest.approx(6)
            assert np.linalg.norm(np.array(axis["end_mm"]) - axis["start_mm"]) == pytest.approx(
                axis["rod_length_mm"]
            )
    rods.cad.parameters["segments_mm"][0][0][2] += 1
    with pytest.raises(ValueError, match="match the spec-owned"):
        linkage(v, 0, 0)
