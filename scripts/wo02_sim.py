"""Run the shared JAX flight core and independent actual-configuration comparison."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import jax
import jax.numpy as jnp
import numpy as np
import yaml

from src.sim import env
from src.sim.inputs import prepare, source_hashes
from src.sim.reference import reference_flight
from src.sim.telemetry import write_parquet
from src.vehicle.schema import load_vehicle, vehicle_input_paths


def metrics(final: Any, rows: Any, p: Any) -> dict[str, Any]:
    rows = np.asarray(rows)
    finite = bool(np.isfinite(rows).all())
    landed = np.flatnonzero(rows[:, -1] > 0)
    if len(landed):
        rows = rows[: landed[0] + 1]
    apex = int(np.argmax(-rows[:, 3]))
    apogee = float(-rows[apex, 3])
    apogee_t = float(rows[apex, 0])
    powered = (rows[:, 16] > 0) & (rows[:, 0] <= apogee_t)
    proper = np.linalg.norm(rows[:, 20:23], axis=1)
    powered_peak = float(proper[powered].max(initial=0))
    burn = float(p.motor[0] * p.motor[3] + p.motor[4])
    delays = []
    for delay in [3, 5, 6, 7, 9, 10, 12]:
        t = burn + delay
        delays.append(
            {
                "delay_s": delay,
                "time_s": t,
                "relative_to_apogee_s": t - apogee_t,
                "height_agl_m": float(np.interp(t, rows[:, 0], -rows[:, 3])),
                "vertical_velocity_down_mps": float(np.interp(t, rows[:, 0], rows[:, 6])),
                "meaning": "timing probe only; offered delays require exact-variant verification",
            }
        )
    qw, qx, qy, qz = (rows[:, i] for i in [7, 8, 9, 10])
    # Body +x world-down component R[2,0].
    tilt = np.arccos(np.clip(-2 * (qx * qz - qw * qy), -1, 1))
    vertical_specific = (
        2 * (qx * qz - qw * qy) * rows[:, 20]
        + 2 * (qy * qz + qw * qx) * rows[:, 21]
        + (1 - 2 * (qx * qx + qy * qy)) * rows[:, 22]
    )
    net_accel = np.sqrt(np.maximum(0, proper**2 + 9.80665**2 + 2 * 9.80665 * vertical_specific))
    return {
        "effective_loaded_mass_kg": float(p.mass0),
        "effective_depletion_mass_kg": float(p.motor[1]),
        "effective_burnout_mass_kg": float(p.mass0 - p.motor[1]),
        "powered_net_acceleration_peak_g": float(net_accel[powered].max(initial=0) / 9.80665),
        "finite": finite,
        "apogee_agl_m": apogee,
        "apogee_time_s": apogee_t,
        "max_speed_mps": float(np.linalg.norm(rows[:, 4:7], axis=1).max()),
        "guide_exit_s": float(final.rail_exit_time),
        "guide_exit_mps": float(final.rail_exit_speed),
        "powered_specific_force_peak_g": powered_peak / 9.80665,
        "accel_range_exceeded": powered_peak > float(p.sensors[7]),
        "powered_max_mach": float(rows[powered, 17].max(initial=0)),
        "powered_max_alpha_deg": float(np.rad2deg(rows[powered, 18]).max(initial=0)),
        "powered_max_tilt_deg": float(np.rad2deg(tilt[powered]).max(initial=0)),
        "max_dynamic_pressure_pa": float(rows[:, 19].max()),
        "apogee_downrange_m": float(np.linalg.norm(rows[apex, 1:3])),
        "electronic_apogee_trigger_s": (
            float(final.recovery_time) if float(p.recovery[3]) > 0 else None
        ),
        "inflation_complete_s": (
            float(final.recovery_time + p.recovery[1] + p.recovery[2])
            if float(p.recovery[3]) > 0
            else None
        ),
        "impact_time_s": float(rows[-1, 0]) if len(landed) else None,
        "impact_speed_mps": (
            float(np.linalg.norm(rows[-2, 4:7])) if len(landed) and len(rows) > 1 else None
        ),
        "landing_downrange_m": float(np.linalg.norm(rows[-1, 1:3])) if len(landed) else None,
        "recovery_horizon_complete": bool(len(landed)),
        "motor_delay_probes": delays,
        "burnout_s": burn,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/wo02.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    parser.add_argument("--compare", choices=["rocketpy"])
    parser.add_argument("--batch", type=int, default=4096)
    parser.add_argument("--study", action="store_true")
    parser.add_argument("--require-benchmark", action="store_true")
    parser.add_argument("--json-report", action="store_true")
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args()
    start = time.perf_counter()
    settings = yaml.safe_load(args.config.read_text())
    if args.batch <= 0:
        parser.error("batch must be positive")
    run_id = datetime.now(UTC).strftime("wo02-%Y%m%dT%H%M%S%fZ")
    out = Path("runs") / run_id
    out.mkdir()
    dt = 0.005 if args.preset == "tiny" else 0.001
    horizon = 45 if args.preset == "tiny" else float(settings["max_time_s"])
    paths = settings["vehicles"] + (settings["alternatives"] if args.study else [])
    rows = []
    hashes = {str(args.config): hashlib.sha256(args.config.read_bytes()).hexdigest()}
    for config in paths:
        vehicle = load_vehicle(config)
        assert vehicle.motor and vehicle.design
        case = {
            "dt_s": dt,
            "max_time_s": horizon,
            "sensor_noise": True,
            "elevation_m": settings["elevation_m"],
        }
        p = prepare(vehicle, case)
        key = jax.random.PRNGKey(0)
        final, telemetry = env.rollout(p, key, steps=round(horizon / dt))
        final.rigid.block_until_ready()
        result = metrics(final, telemetry, p)
        reference = reference_flight(vehicle, case) if args.compare else None
        deltas = (
            {
                k: abs(result[k] - reference[k]) / max(abs(reference[k]), 1e-9)
                for k in ["apogee_agl_m", "apogee_time_s"]
            }
            if reference
            else {}
        )
        passed = bool(reference and result["finite"] and max(deltas.values()) <= 0.05)
        row = {
            "vehicle": vehicle.id,
            "config": config,
            "case": case,
            "metrics": result,
            "rocketpy": reference,
            "relative_errors": deltas,
            "reference_benchmark_passed": passed,
            "flight_ready": False,
        }
        rows.append(row)
        if not args.summary_only:
            write_parquet(out / (vehicle.id + ".parquet"), np.asarray(telemetry))
        (out / (vehicle.id + "-resolved.json")).write_text(
            vehicle.model_dump_json(by_alias=True, indent=2) + "\n"
        )
        for path in vehicle_input_paths(config):
            hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
        hashes.update(source_hashes(vehicle))
        print(
            f'{vehicle.id}: altitude {result["apogee_agl_m"]:.2f} m, apex {result["apogee_time_s"]:.3f} s; reference_pass={passed}; {deltas}',
            flush=True,
        )
        if args.study:
            ballistic_case = {**case, "recovery_enabled": False}
            ballistic_p = prepare(vehicle, ballistic_case)
            ballistic_final, ballistic_rows = env.rollout(ballistic_p, key, steps=round(40 / dt))
            ballistic_final.rigid.block_until_ready()
            ballistic_metrics = metrics(ballistic_final, ballistic_rows, ballistic_p)
            row["ballistic_motor_delay_probes"] = (
                ballistic_metrics["motor_delay_probes"]
                if "g12" not in vehicle.motor.id.lower()
                else None
            )
            row["plugged_no_motor_recovery"] = "g12" in vehicle.motor.id.lower()
            row["delay_probe_scope"] = (
                "Separate no-canopy ballistic sensitivity; post-apogee aerodynamics unvalidated. Probe delays are not a purchasable-SKU claim."
            )
            for name, overrides in [
                (
                    "growth_low_thrust_high_drag",
                    {
                        "added_mass_kg": 0.05,
                        "thrust_scale": 0.85,
                        "time_scale": 0.95,
                        "drag_scale": 1.2,
                        "rail_friction_n": 0.5,
                    },
                ),
                (
                    "high_thrust_low_drag",
                    {"thrust_scale": 1.15, "time_scale": 1.05, "drag_scale": 0.8},
                ),
                ("wind_1", {"wind_east_mps": 1}),
                *(
                    [
                        (
                            "certificate_propellant_mass_hypothesis",
                            {"depletion_mass_kg": 0.0865 if "g54" in vehicle.id else 0.0791},
                        )
                    ]
                    if "g54" in vehicle.id or "g33" in vehicle.id
                    else []
                ),
                (
                    "wind_3_gust",
                    {"wind_east_mps": 3, "gust_amplitude_mps": 1, "wind_power_exponent": 0.14},
                ),
            ]:
                scenario = {**case, **overrides}
                params = prepare(vehicle, scenario)
                f, t = env.rollout(params, key, steps=round(horizon / dt))
                f.rigid.block_until_ready()
                m = metrics(f, t, params)
                rows.append(
                    {
                        "vehicle": vehicle.id,
                        "scenario": name,
                        "case": scenario,
                        "metrics": m,
                        "flight_ready": False,
                    }
                )
                if not args.summary_only:
                    write_parquet(out / (vehicle.id + "-" + name + ".parquet"), np.asarray(t))
                print(
                    f'  {name}: altitude {m["apogee_agl_m"]:.2f} m; guide {m["guide_exit_mps"]:.2f} m/s; powered tilt {m["powered_max_tilt_deg"]:.2f} deg',
                    flush=True,
                )
    p = prepare(load_vehicle(settings["vehicles"][0]), {"dt_s": dt, "sensor_noise": False})
    keys = jax.random.split(jax.random.PRNGKey(0), args.batch)
    states = jax.vmap(env.reset, in_axes=(None, 0))(p, keys)
    batched = jax.jit(jax.vmap(env.step, in_axes=(0, 0, None, 0)))
    warm, _, _ = batched(states, jnp.zeros((args.batch, 2)), p, keys)
    warm.rigid.block_until_ready()
    timed = time.perf_counter()
    batch, _, _ = batched(states, jnp.zeros((args.batch, 2)), p, keys)
    batch.rigid.block_until_ready()
    elapsed = time.perf_counter() - timed
    checks = {
        "actual_mode_reference_comparisons": all(
            r["reference_benchmark_passed"] for r in rows if "reference_benchmark_passed" in r
        ),
        "4096_envs_cpu_step": args.batch >= 4096
        and bool(np.isfinite(np.asarray(batch.rigid)).all())
        and jax.default_backend() == "cpu",
        "tiny_under_120s": args.preset != "tiny" or time.perf_counter() - start < 120,
    }
    record = {
        "run_id": run_id,
        "work_order": "02",
        "preset": args.preset,
        "protocol": settings["protocol"],
        "platform": platform.platform(),
        "device": str(jax.devices()),
        "versions": {
            n: version(n) for n in ["jax", "jaxlib", "rocketpy", "numpy", "scipy", "pyarrow"]
        },
        "checks": checks,
        "wo02_benchmark_passed": all(checks.values()),
        "flight_ready": False,
        "cost_usd": 0,
        "elapsed_s": time.perf_counter() - start,
        "input_sha256": hashes,
        "code_sha256": hashlib.sha256(
            b"".join(p.read_bytes() for p in sorted(Path("src").rglob("*.py")))
            + Path(__file__).read_bytes()
        ).hexdigest(),
        "batch": {
            "environments": args.batch,
            "seconds_after_compile": elapsed,
            "env_steps_per_second": args.batch / elapsed,
        },
        "cases": rows,
        "limitations": [
            "Numerical source hypotheses; motor identity/classification/lot/stock not frozen",
            "Mass distributions, servo/load/thermal/aerodynamic derivatives unmeasured",
            "Calm apogee/time comparison does not validate wind or attitude accuracy",
            "Parachute point drag/inflation approximation, not opening-load qualification",
            "Finless burnout/recovery transition not validated; no controlled flight here",
            "No physical work, paid run, PID/RL controller or WO-10 gate waived",
        ],
    }
    (out / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"Record: {out}/record.json; checks={checks}", flush=True)
    if args.json_report:
        print("WO02_REPORT_JSON=" + json.dumps(record, separators=(",", ":")), flush=True)
    return int(args.require_benchmark and not all(checks.values()))


if __name__ == "__main__":
    raise SystemExit(main())
