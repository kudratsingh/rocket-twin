"""Analytical limits verify the slice integration independently of its loops."""

from math import pi
from pathlib import Path

import numpy as np
import pytest
import yaml

from src.vehicle.geometry import nose_cp_offset, shape_properties
from src.vehicle.schema import Vehicle


def test_slice_integrals_match_analytical_shapes() -> None:
    cylinder = shape_properties(
        "body_tube", {"radius_m": 0.04, "inner_radius_m": 0.03, "length_m": 0.5}
    )
    assert cylinder.volume_m3 == pytest.approx(pi * (0.04**2 - 0.03**2) * 0.5)
    assert cylinder.cg_offset_m == pytest.approx(0.25)
    assert cylinder.inertia_per_kg_m2[0, 0] == pytest.approx((0.04**2 + 0.03**2) / 2)
    assert cylinder.inertia_per_kg_m2[1, 1] == pytest.approx(
        (3 * (0.04**2 + 0.03**2) + 0.5**2) / 12
    )
    cone = shape_properties("nose_cone", {"shape": "conical", "length_m": 0.3, "radius_m": 0.04})
    assert cone.volume_m3 == pytest.approx(pi * 0.04**2 * 0.3 / 3)
    assert cone.cg_offset_m == pytest.approx(3 * 0.3 / 4)
    assert cone.inertia_per_kg_m2[0, 0] == pytest.approx(3 * 0.04**2 / 10)
    assert cone.inertia_per_kg_m2[1, 1] == pytest.approx(3 * 0.04**2 / 20 + 3 * 0.3**2 / 80)
    for shape, cp in [("conical", 0.2), ("elliptical", 0.1)]:
        assert nose_cp_offset(0.3, 0.04, shape) == pytest.approx(cp)
    # The tangent-ogive volume integral has an independent closed form.
    length, radius = 0.16, 0.039
    rho = (length**2 + radius**2) / (2 * radius)
    volume = pi * (
        length * rho**2 - length**3 / 3 - (rho - radius) * rho**2 * np.arcsin(length / rho)
    )
    assert nose_cp_offset(length, radius, "ogive") == pytest.approx(
        length - volume / (pi * radius**2)
    )


def test_density_mass_survives_spec_roundtrip() -> None:
    data = yaml.safe_load(Path("configs/vehicle/tvc-ascent-v1.yaml").read_text())
    body = data["parts"][1]
    body.pop("mass_kg", None)
    body["density_kg_m3"] = 1270
    body.pop("cg_offset_m")
    vehicle = Vehicle.model_validate(data)
    expected = pi * (0.039**2 - 0.0374**2) * 0.25 * 1270
    assert vehicle.parts[1].resolved_mass_kg == pytest.approx(expected)
    assert vehicle.parts[1].cg_offset_m == pytest.approx(0.125)
    restored = Vehicle.model_validate(vehicle.model_dump(by_alias=True))
    assert restored.parts[1].resolved_mass_kg == pytest.approx(expected)
