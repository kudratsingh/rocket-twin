"""Verify archived source bytes and distinguish accepted from unresolved motor data.

A certification-derived file is a historical reference, not evidence of current
certification, availability, hardware suitability or flight approval.
"""

from __future__ import annotations

import hashlib
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from src.vehicle.motors import load_rasp
from src.vehicle.schema import Vehicle


def audit_motor_catalog(
    vehicle: Vehicle, root: Path = Path("configs/vehicle/motors")
) -> dict[str, Any]:
    entries = []
    hashes = {}
    default_verified = False
    for path in sorted(root.glob("*.eng")):
        sidecar = path.with_suffix(".yaml")
        metadata = yaml.safe_load(sidecar.read_text())
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != metadata.get("sha256"):
            raise ValueError(f"source hash mismatch for {path}")
        hashes[str(path)] = digest
        hashes[str(sidecar)] = hashlib.sha256(sidecar.read_bytes()).hexdigest()
        curve = load_rasp(path)
        calculated = {
            "diameter_m": curve.diameter_m,
            "length_m": curve.length_m,
            "loaded_mass_kg": curve.loaded_mass_kg,
            "propellant_mass_kg": curve.propellant_mass_kg,
            "burn_time_s": curve.burn_time_s,
            "total_impulse_ns": curve.total_impulse_ns,
            "average_thrust_n": curve.average_thrust_n,
        }
        if any(
            not np.isclose(value, metadata.get(key, float("nan")), rtol=1e-9, atol=1e-12)
            for key, value in calculated.items()
        ):
            raise ValueError(f"source summary mismatch for {path}")
        certification_date = metadata.get("certification_date")
        if certification_date:
            date.fromisoformat(str(certification_date))
        accepted = (
            metadata.get("review_status") == "accepted_for_digital_model"
            and bool(certification_date)
            and bool(metadata.get("certificate_url"))
        )
        if (
            vehicle.motor
            and vehicle.motor.curve
            and path.resolve() == Path(vehicle.motor.curve).resolve()
        ):
            motor = vehicle.motor
            if not np.allclose(
                [
                    curve.loaded_mass_kg,
                    curve.propellant_mass_kg,
                    curve.burn_time_s,
                    curve.total_impulse_ns,
                    curve.average_thrust_n,
                ],
                [
                    motor.casing_mass_kg + motor.propellant_mass_kg,
                    motor.propellant_mass_kg,
                    motor.burn_time_s,
                    motor.total_impulse_ns,
                    motor.average_thrust_n,
                ],
                rtol=1e-9,
                atol=1e-12,
            ):
                raise ValueError("configured motor disagrees with source file")
            default_verified = accepted
        entries.append(
            {
                "file": str(path),
                "sha256": digest,
                "review_status": metadata.get("review_status"),
                "review_note": metadata.get("review_note"),
                "accepted": accepted,
                **calculated,
            }
        )
    return {
        "entries": entries,
        "input_sha256": hashes,
        "default_curve_verified": default_verified,
        "certified_curves_complete": default_verified and sum(e["accepted"] for e in entries) >= 3,
        "scope": "Historical source provenance only; not current certification or flight approval",
    }
