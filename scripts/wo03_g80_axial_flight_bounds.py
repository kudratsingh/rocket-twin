"""Postprocess saved G80 flight rows into conditional axial-cut bounds."""

from __future__ import annotations

import hashlib
import json
import math
import resource
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import yaml

from src.vehicle.schema import Vehicle

ROOT = Path(__file__).resolve().parents[1]
FLIGHT = ROOT / "build/wo03-g80-candidate-flight-v1/record.json"
CUTS = ROOT / "build/wo03-g80-axial-cuts-v1/record.json"
SPEC = ROOT / "build/wo03-g80-fit-candidate-v1/resolved-candidate-io-replan.yaml"
OUT = ROOT / "build/wo03-g80-axial-flight-bounds-v1"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def freebody_bounds(m_lo, m_hi, total_m, thrust, resistance):
    """Bounds when 0 <= resistance ahead <= total resistance and thrust is aft."""
    if not 0 <= m_lo <= m_hi <= total_m or total_m <= 0 or resistance < 0 or thrust < 0:
        raise ValueError("Invalid free-body inputs")
    drive = thrust - resistance
    lo_mass, hi_mass = (m_lo, m_hi) if drive >= 0 else (m_hi, m_lo)
    return lo_mass / total_m * drive, hi_mass / total_m * drive + resistance


def main():
    started = time.monotonic()
    pa.set_cpu_count(1)
    pa.set_io_thread_count(1)
    flight = json.loads(FLIGHT.read_text())
    cuts = json.loads(CUTS.read_text())
    vehicle = Vehicle.model_validate(yaml.safe_load(SPEC.read_text()))
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    if identity != flight["candidate_identity"] or identity != cuts["candidate_identity"]:
        raise ValueError("Input candidate identities disagree")
    cut = next(
        x
        for x in cuts["results"]["candidate_upper_annular_budget"]["cuts"]
        if x["name"] == "forward_of_mount"
    )
    if (
        cut["station_m"] != 1.009
        or cut["crossing_parts"] != ["aft_shell"]
        or cut["thrust_ahead_fraction_bounds"] != [0.0, 0.0]
    ):
        raise ValueError("Cut geometry or aft thrust insertion differs")
    growth_forward = cut["growth_forward_max_kg"]
    mass_lo = cut["forward_mass_min_kg"]
    mass_hi = cut["forward_mass_max_kg"] - growth_forward
    paths = {FLIGHT, CUTS, SPEC, Path(__file__).resolve()}
    for row in flight["cases"]:
        paths.add(FLIGHT.parent / f"{row['case_name']}.parquet")
    before = {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}
    if freebody_bounds(0.2, 0.3, 1.0, 10.0, 2.0) != (1.6, 4.4):
        raise ValueError("Known positive-drive free-body check failed")
    neg = freebody_bounds(0.2, 0.3, 1.0, 2.0, 10.0)
    if abs(neg[0] + 2.4) > 1e-12 or abs(neg[1] - 8.4) > 1e-12:
        raise ValueError("Known negative-drive free-body check failed")
    area = math.pi * (33**2 - 32.5**2)
    results = []
    for row in flight["cases"]:
        case = row["case"]
        if case["added_mass_kg"] and (
            case.get("added_mass_station_m") != 1.212
            or case["added_mass_station_m"] <= cut["station_m"]
        ):
            raise ValueError("Growth mass location not proven aft")
        telemetry = pq.read_table(
            FLIGHT.parent / f"{row['case_name']}.parquet",
            columns=["time_s", "mass_kg", "thrust_n", "mach", "dynamic_pressure_pa"],
        ).to_pydict()
        arr = {key: np.asarray(value, dtype=float) for key, value in telemetry.items()}
        if any(not np.isfinite(a).all() for a in arr.values()) or not np.all(
            np.diff(arr["time_s"]) > 0
        ):
            raise ValueError("Malformed telemetry")
        powered = (arr["time_s"] < row["metrics"]["burnout_s"]) & (arr["thrust_n"] >= 0)
        ids = np.flatnonzero(powered)
        if not len(ids) or not np.all(
            (arr["mass_kg"][ids] >= row["metrics"]["effective_burnout_mass_kg"] - 1e-8)
            & (arr["mass_kg"][ids] <= row["metrics"]["effective_loaded_mass_kg"] + 1e-8)
        ):
            raise ValueError("Unusable time-varying mass")
        model = vehicle.aero.cd_model
        S = math.pi * (vehicle.airframe["body_diameter_m"] / 2) ** 2
        drag = (
            arr["dynamic_pressure_pa"]
            * S
            * np.interp(arr["mach"], model.mach, model.cd)
            * case["drag_scale"]
        )
        if not np.isfinite(drag).all() or np.any(drag < 0):
            raise ValueError("Unusable drag data")
        it = int(ids[np.argmax(arr["thrust_n"][ids])])
        ip = int(ids[np.argmax(drag[ids])])
        saved = row["powered_telemetry"]
        if (
            abs(drag[it] - saved["peak_powered_thrust"]["axial_drag_magnitude_N"]) > 1e-8
            or abs(drag[ip] - saved["peak_powered_axial_drag"]["axial_drag_magnitude_N"]) > 1e-8
        ):
            raise ValueError("Reconstructed drag does not match saved flight summary")
        if (
            row["metrics"]["powered_max_tilt_deg"] > 5
            or row["metrics"]["powered_max_alpha_deg"] > 5
        ):
            raise ValueError("Powered flight exceeds declared small-angle scope")
        lo = []
        hi = []
        extended_lo = []
        extended_hi = []
        for i in ids:
            args = (mass_lo, mass_hi, arr["mass_kg"][i], arr["thrust_n"][i])
            x, y = freebody_bounds(*args, drag[i])
            lo.append(x)
            hi.append(y)
            # Guide-friction resultant location is bounded anywhere along vehicle.
            f = (
                case["rail_friction_n"]
                if arr["time_s"][i] <= row["metrics"]["guide_exit_s"]
                else 0.0
            )
            x, y = freebody_bounds(*args, drag[i] + f)
            extended_lo.append(x)
            extended_hi.append(y)
        lo = np.asarray(lo)
        hi = np.asarray(hi)
        extended_lo = np.asarray(extended_lo)
        extended_hi = np.asarray(extended_hi)
        magnitude = np.maximum(np.abs(lo), np.abs(hi))
        emagnitude = np.maximum(np.abs(extended_lo), np.abs(extended_hi))
        j = int(np.argmax(magnitude))
        je = int(np.argmax(emagnitude))
        idx = int(ids[j])
        idxe = int(ids[je])

        def sample(i, jj, lower, upper, arr=arr, drag=drag):
            return {
                "time_s": float(arr["time_s"][i]),
                "mass_kg": float(arr["mass_kg"][i]),
                "thrust_N": float(arr["thrust_n"][i]),
                "drag_N": float(drag[i]),
                "force_bounds_N": [float(lower[jj]), float(upper[jj])],
                "DF3_max_abs_stress_MPa": 3 * float(max(abs(lower[jj]), abs(upper[jj]))) / area,
            }

        results.append(
            {
                "case_name": row["case_name"],
                "powered_samples": len(ids),
                "drag_only_worst": sample(idx, j, lo, hi),
                "including_unallocated_guide_friction_worst": sample(
                    idxe, je, extended_lo, extended_hi
                ),
                "small_angle_scope": {
                    "powered_max_tilt_deg": row["metrics"]["powered_max_tilt_deg"],
                    "powered_max_alpha_deg": row["metrics"]["powered_max_alpha_deg"],
                },
                "criterion_2MPa_pass_drag_only": bool(3 * magnitude[j] / area <= 2.0),
                "criterion_2MPa_pass_with_friction": bool(3 * emagnitude[je] / area <= 2.0),
                "negative_thrust_minus_drag_samples": int(
                    np.count_nonzero(arr["thrust_n"][ids] - drag[ids] < 0)
                ),
            }
        )
    after = {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}
    if before != after:
        raise ValueError("Postprocessing source changed")
    out = {
        "status": "completed_conditional_sampled_bound_not_qualified",
        "identity": identity,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "cut_station_m": cut["station_m"],
        "area_mm2": area,
        "forward_mass_bounds_kg": [mass_lo, mass_hi],
        "growth_interpretation": "50 g at 1.212 m is aft; not included forward; remains in telemetry total mass",
        "criterion_MPa": 2.0,
        "design_factor": 3.0,
        "source_drag_model": "existing powered aero force: q * reference area * interpolated source Cd * drag scale",
        "force_sign": "compression positive; one-dimensional near-vertical idealization",
        "results": results,
        "elapsed_s": time.monotonic() - started,
        "resource_self": {
            "user_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime,
            "system_s": resource.getrusage(resource.RUSAGE_SELF).ru_stime,
            "peak_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "threads": "one worker requested; no OS affinity claim",
        "acceptance": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "record.json").write_text(json.dumps(out, indent=2) + "\n")
    (OUT / "executed.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
