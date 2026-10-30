"""WO-01 CPU report. Run from the repository root; no GPU or network required."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

# Allow direct `python scripts/wo01_vehicle.py` without installing the project.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.sim.frames import STANDARD_GRAVITY_M_S2
from src.vehicle.aero import center_of_pressure
from src.vehicle.catalog import audit_motor_catalog
from src.vehicle.mass import mass_properties
from src.vehicle.schema import load_vehicle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/vehicle/tvc-ascent-v1.yaml")
    parser.add_argument("--preset", choices=["tiny", "sim", "rl", "real"], default="tiny")
    parser.add_argument("--compare", choices=["rocketpy"])
    parser.add_argument(
        "--require-benchmark",
        action="store_true",
        help="exit nonzero unless every WO-01 benchmark is met",
    )
    args = parser.parse_args()
    start = time.perf_counter()
    config = Path(args.config)
    try:
        vehicle = load_vehicle(config)
        catalog = audit_motor_catalog(vehicle)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    cp = center_of_pressure(vehicle)
    launch = mass_properties(vehicle)
    burnout = mass_properties(vehicle, 1)
    if vehicle.motor is None or vehicle.limits is None:
        parser.error("WO-01 report currently requires a model rocket with a solid motor")
    twr = vehicle.motor.average_thrust_n / (launch.mass_kg * STANDARD_GRAVITY_M_S2)
    run_id = datetime.now(UTC).strftime("wo01-%Y%m%dT%H%M%S%fZ")
    output = Path("runs") / run_id
    output.mkdir(parents=True)
    states = {}
    for name, props in [("liftoff", launch), ("burnout", burnout)]:
        states[name] = {
            **asdict(props),
            "inertia_kg_m2": props.inertia_kg_m2.tolist(),
            "cp_m": cp,
            "stability_margin_cal": (cp - props.cg_m) / vehicle.airframe["body_diameter_m"],
        }
    comparisons = {}
    comparison_error = None
    if args.compare:
        try:
            from src.vehicle.reference import compare_rocketpy

            comparisons["configured"] = compare_rocketpy(vehicle)
            alternate = type(vehicle).model_validate(vehicle.model_dump(by_alias=True))
            alternate.aero.passive_stubs.enabled = not vehicle.aero.passive_stubs.enabled
            comparisons["stub_geometry_sensitivity"] = compare_rocketpy(alternate)
            comparisons["stub_geometry_sensitivity"]["note"] = (
                "Aerodynamic geometry cross-check only; no physical fins or fin mass added. "
                "passive_stubs.enabled=" + str(alternate.aero.passive_stubs.enabled)
            )
        except (ImportError, ValueError, OSError) as exc:
            comparison_error = str(exc)
    checks = {
        "spec_valid": True,
        "liftoff_mass_within_spec_cap": launch.mass_kg <= vehicle.limits.max_liftoff_mass_kg,
        "propellant_within_spec_cap": vehicle.motor.propellant_mass_kg
        <= vehicle.limits.max_propellant_kg,
        "impulse_within_spec_cap": vehicle.motor.total_impulse_ns
        <= vehicle.limits.max_total_impulse_ns,
        "average_thrust_to_weight_ge_3": twr >= 3,
        "burn_time_ge_3s": vehicle.motor.burn_time_s >= 3,
        "reference_comparison_complete": bool(comparisons)
        and comparison_error is None
        and all(result["passed"] for result in comparisons.values()),
        "default_curve_verified": catalog["default_curve_verified"],
        "certified_curves_complete": catalog["certified_curves_complete"],
        "cpu_runtime_under_120s": time.perf_counter() - start < 120,
    }
    report = {
        "vehicle": vehicle.id,
        "validation_status": "unvalidated",
        "states": states,
        "motor_catalog": catalog,
        "reference_comparisons": comparisons,
        "reference_comparison_error": comparison_error,
        "validation_scope": "static properties only; component masses, inertia and flight remain unvalidated",
        "average_thrust_to_weight": twr,
        "checks": checks,
        "inertia_status": "nose shell integrals and equivalent shapes; CAD validation pending",
        "depletion_model": "uniform mass fraction; not time or impulse fraction",
    }
    (output / "vehicle.json").write_text(json.dumps(report, indent=2) + "\n")
    record = {
        "run_id": run_id,
        "work_order": "01",
        "preset": args.preset,
        "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
        "code_sha256": hashlib.sha256(
            b"".join(p.read_bytes() for p in sorted(Path("src/vehicle").glob("*.py")))
            + Path(__file__).read_bytes()
        ).hexdigest(),
        "seed": 0,
        "device": "cpu",
        "cost_usd": 0,
        "elapsed_s": time.perf_counter() - start,
        **report,
    }
    (output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    for part, mass in launch.budget_kg.items():
        print(f"{part:24s} {mass*1000:7.1f} g")
    for name, state in states.items():
        print(
            f"{name}: mass={state['mass_kg']:.4f} kg CG={state['cg_m']:.4f} m "
            f"CP={cp:.4f} m margin={state['stability_margin_cal']:.3f} cal"
        )
    print(f"Average-thrust / liftoff-weight = {twr:.3f} (target >= 3)")
    for check, passed in checks.items():
        print(f"{'PASS' if passed else 'PENDING/FAIL'}: {check}")
    print(f"Unvalidated preliminary model. Record: {output}/record.json")
    for case, result in comparisons.items():
        print(f"RocketPy {result['version']} / {case}: {'PASS' if result['passed'] else 'FAIL'}")
        for row in result["rows"]:
            delta = row["absolute_delta"]
            print(
                f"  {row['state']}: mass delta={delta['mass_kg']:.3g} kg, "
                f"CG delta={delta['cg_m']:.3g} m, CP delta={delta['cp_m']:.3g} m, "
                f"margin delta={delta['stability_margin_cal']:.3g} cal"
            )
        print(f"  Scope: {result['motor_mode']}")
    if comparison_error:
        print("Reference comparison unavailable: " + comparison_error, file=sys.stderr)
        return 2
    if args.compare and not checks["reference_comparison_complete"]:
        return 1
    if args.require_benchmark and not all(checks.values()):
        print(
            "WO-01 benchmark NOT met: " + ", ".join(k for k, v in checks.items() if not v),
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
