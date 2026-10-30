"""Independent RocketPy trajectory integration from the same physical inputs.

RocketPy builds surfaces and motor mass independently from the vehicle spec.
The declared dry inertia is shared as an input; its physical correctness is not
validated by an integrator comparison. No twin trajectory enters RocketPy.
Both use identical analytic ISA profiles, g and source breakpoints, zero nozzle
pressure correction (exit area unknown), and usable guide travel. RocketPy's
native ENU output is converted to the project's NED reporting convention.
Calm apogee/time are the completion benchmark; wind/attitude model agreement is
reported separately and cannot be inferred from a vertical trajectory match.
Reference: RocketPy 1.13.0 Flight/Environment API and equations of motion v1 docs.
"""

from typing import Any

import numpy as np

from src.sim.frames import STANDARD_GRAVITY_M_S2 as G
from src.vehicle.reference import build_reference
from src.vehicle.schema import Vehicle


def reference_flight(
    vehicle: Vehicle, case: dict[str, Any], full_recovery: bool = False
) -> dict[str, Any]:
    from rocketpy import Environment, Flight

    rocket, _ = build_reference(
        vehicle, flight_inertia=True, drag_scale=float(case.get("drag_scale", 1))
    )
    elevation = float(case.get("elevation_m", 850))
    env = Environment(gravity=G, elevation=elevation, latitude=34.5, longitude=-116.9)

    def temperature(h: float) -> float:
        return float(288.15 - 0.0065 * np.clip(h, -500, 11000))

    def pressure(h: float) -> float:
        return float(101325 * (temperature(h) / 288.15) ** (G / (287.05287 * 0.0065)))

    env.set_atmospheric_model(
        type="custom_atmosphere",
        pressure=pressure,
        temperature=temperature,
        wind_u=float(case.get("wind_east_mps", 0)),
        wind_v=float(case.get("wind_north_mps", 0)),
    )
    if full_recovery:
        area = (
            np.pi
            * (
                float(
                    case.get(
                        "canopy_diameter_m",
                        vehicle.recovery.canopy_diameter_m if vehicle.recovery else 0.75,
                    )
                )
                / 2
            )
            ** 2
        )
        rocket.add_parachute(
            "independent-electronic",
            area
            * float(
                case.get(
                    "canopy_cd", vehicle.recovery.drag_coefficient if vehicle.recovery else 0.75
                )
            ),
            trigger="apogee",
            sampling_rate=100,
            lag=float(
                case.get(
                    "recovery_lag_s", vehicle.recovery.trigger_lag_s if vehicle.recovery else 0.3
                )
            ),
        )
    flight = Flight(
        rocket,
        env,
        rail_length=vehicle.design.rail_length_m if vehicle.design else 1.5,
        inclination=90 - float(case.get("rail_tilt_deg", 0)),
        heading=float(case.get("heading_deg", 0)),
        terminate_on_apogee=not full_recovery,
        max_time=float(case.get("max_time_s", 240)),
        max_time_step=0.02,
        rtol=1e-8,
        atol=1e-9,
        verbose=False,
    )
    return {
        "reference": "RocketPy 1.13.0",
        "apogee_agl_m": float(flight.apogee - elevation),
        "apogee_time_s": float(flight.apogee_time),
        "max_speed_mps": float(flight.max_speed),
        "guide_exit_s": float(flight.out_of_rail_time),
        "guide_exit_mps": float(flight.out_of_rail_velocity),
        "end_time_s": float(flight.t_final),
        "recovery_full_flight": full_recovery,
        "shared_inertia_input": True,
        "nozzle_pressure_correction": "zero; exit area unknown",
    }
