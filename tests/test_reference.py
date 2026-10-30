"""Exercise the real optional reference; never mock a successful validation."""

import pytest

from src.vehicle.reference import compare_rocketpy
from src.vehicle.schema import load_vehicle


@pytest.mark.parametrize(
    "shape,stubs", [("ogive", False), ("ogive", True), ("conical", True), ("elliptical", False)]
)
def test_static_properties_against_rocketpy(shape: str, stubs: bool) -> None:
    pytest.importorskip("rocketpy")
    vehicle = load_vehicle("configs/vehicle/tvc-ascent-v1.yaml")
    vehicle.aero.passive_stubs.enabled = stubs
    vehicle.airframe["nose"]["shape"] = shape
    next(p for p in vehicle.parts if p.type == "nose_cone").geometry["shape"] = shape
    result = compare_rocketpy(vehicle)
    assert result["passed"], result
    assert "static endpoints only" in result["motor_mode"]
    assert all(row["absolute_delta"]["stability_margin_cal"] < 1e-10 for row in result["rows"])


def test_transition_against_rocketpy() -> None:
    pytest.importorskip("rocketpy")
    from src.vehicle.schema import Part

    vehicle = load_vehicle("configs/vehicle/tvc-ascent-v1.yaml")
    vehicle.parts.append(
        Part.model_validate(
            {
                "id": "reference_tail",
                "type": "transition",
                "parent": "body_lower",
                "position_m": 0.58,
                "geometry": {"fore_radius_m": 0.039, "radius_m": 0.03, "length_m": 0.1},
                "material": "PETG",
                "mass_kg": 0.01,
                "estimate": True,
                "learn": "Synthetic geometry for the reference comparison; not part of the physical vehicle.",
            }
        )
    )
    result = compare_rocketpy(vehicle)
    assert result["passed"], result
