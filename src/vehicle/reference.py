"""WO-01 static-property comparison against installed RocketPy 1.13.0.

RocketPy inputs are assembled from individual spec parts, never from our computed
vehicle CG or CP. RocketPy accepts one aggregate dry airframe, so this validates
motor/airframe assembly and aerodynamic buildup, not individual measured masses.
Coordinates: nose origin, positive aft in both adapters; RocketPy's longitudinal
inertia axis is e3, whereas the twin's body longitudinal axis is x.

A constant-thrust GenericMotor supplies only mass-depletion ENDPOINTS when the
certified curve is absent. It is not a replacement F15 thrust curve, is never
saved as motor data, and must not be used for trajectory validation (WO-02).
No nozzle radius estimate is needed: zero is a placeholder for this static check.
Reference APIs: rocketpy.Rocket, GenericMotor, NoseCone, TrapezoidalFins, Tail.
"""

from __future__ import annotations

from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from src.vehicle.aero import center_of_pressure, fin_geometries
from src.vehicle.mass import mass_properties
from src.vehicle.motors import load_rasp
from src.vehicle.schema import Vehicle


def build_reference(
    vehicle: Vehicle, flight_inertia: bool = False, drag_scale: float = 1.0
) -> tuple[Any, str]:
    # Import only for comparison runs; ordinary tiny runs do not require RocketPy.
    from rocketpy import Function, GenericMotor, Rocket

    motor = vehicle.motor
    if vehicle.scale != "model" or motor is None:
        raise ValueError("WO-01 reference requires a model rocket with one solid motor")
    part = next(p for p in vehicle.parts if p.type == "motor")
    airframe = [p for p in vehicle.parts if p.type != "motor"]
    masses = np.array([p.resolved_mass_kg for p in airframe])
    stations = np.array([p.cg_station_m for p in airframe])
    dry_mass = float(masses.sum())
    dry_cg = float(np.dot(masses, stations) / dry_mass)
    # Inertia does not enter these static quantities. Zero placeholders avoid
    # sharing this project's shape-integration implementation with the reference.
    inertia: tuple[float, ...] = (0, 0, 0)
    motor_inertia: tuple[float, ...] = (0, 0, 0)
    if flight_inertia:
        # Common declared inertial input, not an independent inertia validation.
        aggregate = mass_properties(vehicle.model_copy(update={"parts": airframe, "motor": None}))
        tensor = aggregate.inertia_kg_m2
        inertia = (
            float(tensor[1, 1]),
            float(tensor[2, 2]),
            float(tensor[0, 0]),
            float(tensor[1, 2]),
            float(tensor[0, 1]),
            float(tensor[0, 2]),
        )
        radius, length = part.geometry["radius_m"], part.geometry["length_m"]
        transverse = motor.casing_mass_kg * (3 * radius**2 + length**2) / 12
        motor_inertia = (transverse, transverse, motor.casing_mass_kg * radius**2 / 2)
    drag = vehicle.aero.cd_model
    on_drag = np.column_stack((drag.mach, np.array(drag.cd) * drag_scale)) if flight_inertia else 0
    off_drag = (
        np.column_stack((drag.mach, (np.array(drag.cd) + drag.base_drag_cd) * drag_scale))
        if flight_inertia
        else 0
    )
    rocket = Rocket(
        radius=vehicle.airframe["body_diameter_m"] / 2,
        mass=dry_mass,
        inertia=inertia,
        power_off_drag=Function(off_drag, interpolation="linear", extrapolation="constant"),
        power_on_drag=Function(on_drag, interpolation="linear", extrapolation="constant"),
        center_of_mass_without_motor=dry_cg,
        coordinate_system_orientation="nose_to_tail",
    )
    if motor.curve is not None:
        if not Path(motor.curve).is_file():
            raise FileNotFoundError(motor.curve)
        curve = load_rasp(motor.curve)
        expected = [
            part.geometry["radius_m"] * 2,
            part.geometry["length_m"],
            motor.propellant_mass_kg,
            motor.propellant_mass_kg + motor.casing_mass_kg,
            motor.burn_time_s,
        ]
        actual = [
            curve.diameter_m,
            curve.length_m,
            curve.propellant_mass_kg,
            curve.loaded_mass_kg,
            curve.burn_time_s,
        ]
        if not np.allclose(actual, expected, rtol=1e-6, atol=1e-9):
            raise ValueError("motor curve dimensions, masses or burn time disagree with the spec")
        thrust_source: NDArray[np.float64] | float = curve.samples
        mode = "source curve; static endpoints only"
    else:
        thrust_source = motor.average_thrust_n
        mode = "constant-thrust placeholder; static endpoints only, not a motor validation"
    ref_motor = GenericMotor(
        thrust_source=thrust_source,
        burn_time=motor.burn_time_s,
        chamber_radius=part.geometry["radius_m"],
        chamber_height=part.geometry["length_m"],
        chamber_position=part.cg_offset_m,
        propellant_initial_mass=motor.propellant_mass_kg,
        nozzle_radius=0,
        dry_mass=motor.casing_mass_kg,
        center_of_dry_mass_position=part.cg_offset_m,
        dry_inertia=motor_inertia,
        nozzle_position=part.geometry["length_m"],
        coordinate_system_orientation="combustion_chamber_to_nozzle",
    )
    rocket.add_motor(ref_motor, position=part.position_m)
    for p in vehicle.parts:
        g = p.geometry
        if p.type == "nose_cone":
            rocket.add_nose(
                length=g["length_m"],
                kind=g["shape"],
                position=p.position_m,
                base_radius=g["radius_m"],
            )
        elif p.type == "transition":
            rocket.add_tail(
                top_radius=g["fore_radius_m"],
                bottom_radius=g["radius_m"],
                length=g["length_m"],
                position=p.position_m,
            )
    for fins in fin_geometries(vehicle):
        rocket.add_trapezoidal_fins(
            n=int(fins["count"]),
            root_chord=fins["root_chord_m"],
            tip_chord=fins["tip_chord_m"],
            span=fins["span_m"],
            position=fins["position_m"],
            sweep_length=fins["sweep_m"],
        )
    return rocket, mode


def compare_rocketpy(vehicle: Vehicle) -> dict[str, Any]:
    rocket, mode = build_reference(vehicle)
    assert vehicle.motor is not None
    rows = []
    for label, fraction, time_s in [("liftoff", 0, 0), ("burnout", 1, vehicle.motor.burn_time_s)]:
        own = mass_properties(vehicle, fraction)
        own_cp = center_of_pressure(vehicle)
        reference = {
            "mass_kg": float(rocket.total_mass(time_s)),
            "cg_m": float(rocket.center_of_mass(time_s)),
            "cp_m": float(rocket.cp_position(0)),
            "stability_margin_cal": float(rocket.static_margin(time_s)),
        }
        calculated = {
            "mass_kg": own.mass_kg,
            "cg_m": own.cg_m,
            "cp_m": own_cp,
            "stability_margin_cal": (own_cp - own.cg_m) / vehicle.airframe["body_diameter_m"],
        }
        delta = {key: abs(calculated[key] - reference[key]) for key in calculated}
        passed = (
            delta["mass_kg"] <= reference["mass_kg"] * 0.03
            and delta["cg_m"] <= vehicle.airframe["length_m"] * 0.03
            and delta["cp_m"] <= vehicle.airframe["length_m"] * 0.03
            and delta["stability_margin_cal"] <= 0.1
        )
        rows.append(
            {
                "state": label,
                "rocket_twin": calculated,
                "rocketpy": reference,
                "absolute_delta": delta,
                "passed": passed,
            }
        )
    return {
        "reference": "RocketPy",
        "version": version("rocketpy"),
        "motor_mode": mode,
        "scope": "static mass/CG/CP/stability at Mach 0 and burn endpoints; inertia/flight excluded",
        "rows": rows,
        "passed": all(row["passed"] for row in rows),
    }
