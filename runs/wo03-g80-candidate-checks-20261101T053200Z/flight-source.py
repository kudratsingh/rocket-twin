"""Run three bounded, source-pinned G80 candidate flight comparisons."""

from __future__ import annotations

import hashlib
import json
import resource
import sys
import time
from importlib.metadata import version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import jax
import numpy as np
import yaml

from scripts.wo02_sim import metrics
from scripts.wo03_integrated_report import add_growth
from src.sim import env
from src.sim.inputs import prepare, source_hashes
from src.sim.reference import reference_flight
from src.sim.telemetry import write_parquet
from src.vehicle.aero import center_of_pressure
from src.vehicle.mass import mass_properties
from src.vehicle.schema import Vehicle

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-g80-candidate-flight.yaml"
OUT = ROOT / "build/wo03-g80-candidate-flight-v1"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    started = time.monotonic()
    cfg = yaml.safe_load(CONFIG.read_text())
    candidate_record = json.loads((ROOT / cfg["candidate_record"]).read_text())
    vehicle = Vehicle.model_validate(yaml.safe_load((ROOT / cfg["candidate_spec"]).read_text()))
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    if identity != cfg["expected_identity"] or identity != candidate_record["candidate_identity"]:
        raise ValueError("Candidate identity mismatch")
    if len(vehicle.parts) != 43 or vehicle.design.mass_allowance_kg != cfg["growth_kg"]:
        raise ValueError("Candidate parts or growth allowance mismatch")
    settings = yaml.safe_load((ROOT / cfg["benchmark_config"]).read_text())
    paths = {
        CONFIG,
        Path(__file__).resolve(),
        ROOT / cfg["candidate_spec"],
        ROOT / cfg["candidate_record"],
        ROOT / cfg["benchmark_config"],
        ROOT / "scripts/wo02_sim.py",
        ROOT / "scripts/wo03_integrated_report.py",
    }
    for folder in ("src/sim", "src/vehicle", "src/cad"):
        paths.update((ROOT / folder).glob("*.py"))
    paths.update(ROOT / p for p in source_hashes(vehicle))
    before = {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}
    cp = center_of_pressure(vehicle)
    diameter = vehicle.airframe["body_diameter_m"]
    static = {}
    for fraction in (0.0, 1.0):
        mass = mass_properties(vehicle, fraction)
        base = {
            "mass_kg": mass.mass_kg,
            "cg_station_m": mass.cg_m,
            "cg_lateral_m": mass.cg_lateral_m,
            "inertia_kg_m2": mass.inertia_kg_m2.tolist(),
            "static_margin_cal": (cp - mass.cg_m) / diameter,
        }
        growth = add_growth(mass, float(cfg["growth_kg"]), float(cfg["growth_station_m"]))
        growth["static_margin_cal"] = (cp - growth["cg_station_m"]) / diameter
        static["loaded" if fraction == 0 else "burnout"] = {
            "candidate": base,
            "full_growth_at_1_212m": growth,
        }
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, overrides in cfg["cases"].items():
        case = {
            "dt_s": float(cfg["step_s"]),
            "max_time_s": float(cfg["horizon_s"]),
            "sensor_noise": False,
            "elevation_m": float(settings["elevation_m"]),
            "wind_north_mps": 0.0,
            "wind_east_mps": 0.0,
            "gust_amplitude_mps": 0.0,
            **overrides,
        }
        if case["added_mass_kg"] and case.get("added_mass_station_m") != cfg["growth_station_m"]:
            raise ValueError("Growth station not explicit")
        p = prepare(vehicle, case)
        final, telemetry = env.rollout(
            p, jax.random.PRNGKey(0), steps=round(case["max_time_s"] / case["dt_s"])
        )
        final.rigid.block_until_ready()
        t = np.asarray(telemetry)
        result = metrics(final, t, p)
        result["motor_delay_probes"] = None
        if not result["finite"] or result["guide_exit_s"] < 0:
            raise ValueError(f"Invalid or no guide departure in {name}")
        # Reconstruction is the existing aero.forces axial-drag formula evaluated
        # on recorded q/mach, not an independently computed trajectory or a drag partition.
        burn = float(p.motor[0] * p.motor[3] + p.motor[4])
        powered = t[:, 0] < burn
        cd = np.interp(t[:, 17], np.asarray(p.mach), np.asarray(p.cd)) + (~powered) * float(
            p.aero[2]
        )
        drag = t[:, 19] * float(p.aero[0]) * cd * float(p.aero[3])
        powered_idx = np.flatnonzero(powered)
        if not len(powered_idx) or not np.isfinite(drag).all():
            raise ValueError("Invalid powered telemetry")
        it = int(powered_idx[np.argmax(t[powered_idx, 16])])
        idrag = int(powered_idx[np.argmax(drag[powered_idx])])
        samples = {
            "peak_powered_thrust": {
                "time_s": float(t[it, 0]),
                "thrust_N": float(t[it, 16]),
                "axial_drag_magnitude_N": float(drag[it]),
                "dynamic_pressure_Pa": float(t[it, 19]),
            },
            "peak_powered_axial_drag": {
                "time_s": float(t[idrag, 0]),
                "thrust_N": float(t[idrag, 16]),
                "axial_drag_magnitude_N": float(drag[idrag]),
                "dynamic_pressure_Pa": float(t[idrag, 19]),
            },
            "basis": "Recorded dynamic pressure/mach and existing aero.forces Cd expression; no spatial drag partition.",
        }
        reference = reference_flight(vehicle, case) if name == "nominal_calm" else None
        errors = (
            {
                k: abs(result[k] - reference[k]) / max(abs(reference[k]), 1e-9)
                for k in ("apogee_agl_m", "apogee_time_s")
            }
            if reference
            else None
        )
        if reference and not all(
            np.isfinite(v) for v in reference.values() if isinstance(v, (int, float))
        ):
            raise ValueError("Nonfinite reference output")
        row = {
            "case_name": name,
            "case": case,
            "metrics": result,
            "rocketpy": reference,
            "reference_relative_errors": errors,
            "reference_pass": (
                bool(max(errors.values()) <= cfg["reference_relative_tolerance"])
                if errors
                else None
            ),
            "guide_target_mps": vehicle.design.minimum_rail_exit_mps,
            "guide_pass": result["guide_exit_mps"] >= vehicle.design.minimum_rail_exit_mps,
            "powered_telemetry": samples,
        }
        write_parquet(OUT / f"{name}.parquet", t)
        rows.append(row)
        (OUT / "partial-rows.json").write_text(json.dumps(rows, indent=2) + "\n")
        print(
            name,
            json.dumps(
                {
                    "apogee_m": result["apogee_agl_m"],
                    "guide_exit_mps": result["guide_exit_mps"],
                    "reference_pass": row["reference_pass"],
                }
            ),
            flush=True,
        )
    after = {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}
    if before != after:
        raise ValueError("Flight source inputs changed")
    record = {
        "status": "completed_not_qualified",
        "candidate_identity": identity,
        "source_sha256_before": before,
        "source_sha256_after": after,
        "versions": {x: version(x) for x in ("jax", "jaxlib", "rocketpy", "numpy")},
        "cases": rows,
        "center_of_pressure_m": cp,
        "static_properties": static,
        "elapsed_s": time.monotonic() - started,
        "resource_self": {
            "user_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime,
            "system_s": resource.getrusage(resource.RUSAGE_SELF).ru_stime,
            "peak_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "threading": "one CPU and one library thread requested; no OS affinity claimed",
        "flight_ready": False,
        "acceptance": False,
    }
    (OUT / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    (OUT / "executed.py").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {
                "status": record["status"],
                "elapsed_s": record["elapsed_s"],
                "resource_self": record["resource_self"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
