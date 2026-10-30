"""Source data must remain traceable and unresolved candidates must not pass a gate."""

import shutil
from pathlib import Path

import pytest

from src.vehicle.catalog import audit_motor_catalog
from src.vehicle.motors import load_rasp
from src.vehicle.schema import load_vehicle


def test_archived_sources_are_verified_without_accepting_bad_variants(tmp_path: Path) -> None:
    vehicle = load_vehicle("configs/vehicle/tvc-ascent-v1.yaml")
    audit = audit_motor_catalog(vehicle)
    assert audit["default_curve_verified"]
    assert not audit["certified_curves_complete"]
    assert len(audit["entries"]) == 4
    assert sum(entry["accepted"] for entry in audit["entries"]) == 1
    # A real source-byte change must fail, not silently produce a new approved curve.
    source = Path("configs/vehicle/motors/Estes_F15.eng")
    shutil.copy2(source, tmp_path / source.name)
    shutil.copy2(source.with_suffix(".yaml"), tmp_path / source.with_suffix(".yaml").name)
    (tmp_path / source.name).write_bytes(source.read_bytes() + b"\n; changed\n")
    with pytest.raises(ValueError, match="hash mismatch"):
        audit_motor_catalog(vehicle, tmp_path)


def test_source_curve_depletion_matches_reference_between_endpoints() -> None:
    pytest.importorskip("rocketpy")
    from src.vehicle.mass import mass_properties
    from src.vehicle.reference import build_reference

    vehicle = load_vehicle("configs/vehicle/tvc-ascent-v1.yaml")
    assert vehicle.motor is not None and vehicle.motor.curve is not None
    curve = load_rasp(vehicle.motor.curve)
    rocket, _ = build_reference(vehicle)
    for t in [0.5, 1.5, 2.5]:
        own = mass_properties(vehicle, curve.burned_fraction(t))
        # RocketPy's published mass Function interpolates 100 sampled integrals.
        # Our piecewise-linear thrust integral is exact between source samples.
        assert own.mass_kg == pytest.approx(float(rocket.total_mass(t)), abs=1e-5)
        direct_mass = (
            rocket.mass
            + vehicle.motor.casing_mass_kg
            + vehicle.motor.propellant_mass_kg
            + rocket.motor.total_mass_flow_rate.integral(0, t)
        )
        assert own.mass_kg == pytest.approx(direct_mass, abs=1e-10)
        assert own.cg_m == pytest.approx(float(rocket.center_of_mass(t)), abs=1e-5)
