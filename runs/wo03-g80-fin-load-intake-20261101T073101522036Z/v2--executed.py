"""Extract a diagnostic scalar G80 fin-load estimate from saved telemetry.

This reads the hash-pinned 52-part candidate and three existing flight Parquets.
It launches no simulator, CAD generator or structural solver. The coefficient
and uniform span load are unvalidated panel estimates, not simulator-recorded
per-fin forces or a validated aerodynamic/load envelope.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import shutil
import signal
import sys
import time
from pathlib import Path
from typing import Any

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
resource.setrlimit(resource.RLIMIT_CPU, (10, 10))


class WallLimit(Exception):
    pass


def _wall_timeout(_signum: int, _frame: Any) -> None:
    raise WallLimit("20 second wall-time limit reached")


signal.signal(signal.SIGALRM, _wall_timeout)
signal.alarm(20)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import pyarrow.parquet as pq
import yaml

from src.analysis.fin_attachment import normal_force_coefficient_per_radian
from src.analysis.fin_design import planform_geometry
from src.vehicle.schema import Vehicle


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve(root: Path, path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else root / p


def actual_hash_map(root: Path, hashes: dict[str, str]) -> dict[str, str]:
    actual: dict[str, str] = {}
    for name, expected in hashes.items():
        path = resolve(root, name)
        if not path.is_file():
            raise FileNotFoundError(f"Hash-pinned source is missing: {name}")
        got = sha256(path)
        if got != expected:
            raise ValueError(f"Source hash mismatch for {name}: {got} != {expected}")
        actual[name] = got
    return actual


def finite_columns(table, names: list[str]) -> dict[str, np.ndarray]:
    columns: dict[str, np.ndarray] = {}
    for name in names:
        values = np.asarray(table[name].to_numpy(), dtype=np.float64)
        if values.ndim != 1 or not np.isfinite(values).all():
            raise ValueError(f"Nonfinite or malformed telemetry column: {name}")
        columns[name] = values
    return columns


def extrema(values: np.ndarray, indices: np.ndarray, times: np.ndarray) -> dict[str, float | int]:
    if indices.size == 0:
        return {"count": 0}
    local = values[indices]
    i = int(indices[int(np.argmax(local))])
    return {"count": int(indices.size), "time_s": float(times[i]), "value": float(values[i])}


def summarize_phase(
    name: str,
    indices: np.ndarray,
    *,
    times: np.ndarray,
    q: np.ndarray,
    alpha: np.ndarray,
    thrust: np.ndarray,
    cn: np.ndarray,
    force: np.ndarray,
    moment: np.ndarray,
    cutoff_rad: float,
) -> dict[str, Any]:
    if indices.size == 0:
        return {"phase": name, "sample_count": 0, "small_angle_diagnostic": {"cutoff_deg": 10.0, "samples_over_cutoff": 0}}
    peak_i = int(indices[int(np.argmax(force[indices]))])
    alpha_i = int(indices[int(np.argmax(np.abs(alpha[indices])))])
    q_i = int(indices[int(np.argmax(q[indices]))])
    return {
        "phase": name,
        "sample_count": int(indices.size),
        "peak_estimated_load": {
            "time_s": float(times[peak_i]),
            "dynamic_pressure_pa": float(q[peak_i]),
            "alpha_deg_signed": float(np.rad2deg(alpha[peak_i])),
            "c_n_capped": float(cn[peak_i]),
            "normal_force_per_fin_N": float(force[peak_i]),
            "root_moment_magnitude_per_fin_Nm": float(moment[peak_i]),
            "thrust_N": float(thrust[peak_i]),
        },
        "max_dynamic_pressure": {
            "time_s": float(times[q_i]),
            "value_pa": float(q[q_i]),
            "alpha_deg_signed": float(np.rad2deg(alpha[q_i])),
        },
        "max_absolute_alpha": {
            "time_s": float(times[alpha_i]),
            "value_deg": float(abs(np.rad2deg(alpha[alpha_i]))),
        },
        "small_angle_diagnostic": {
            "cutoff_deg": float(np.rad2deg(cutoff_rad)),
            "samples_over_cutoff": int(np.count_nonzero(np.abs(alpha[indices]) > cutoff_rad)),
            "meaning": "Reporting cutoff only; no validated small-angle domain or acceptance requirement is asserted.",
        },
    }


def run(config_path: Path, output: Path) -> dict[str, Any]:
    started = time.monotonic()
    cfg = yaml.safe_load(config_path.read_text())
    output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(config_path, output / "study-config.yaml")
    shutil.copy2(Path(__file__).resolve(), output / "executed.py")

    candidate_path = resolve(ROOT, cfg["candidate_spec"])
    candidate_record_path = resolve(ROOT, cfg["candidate_record"])
    flight_record_path = resolve(ROOT, cfg["flight_record"])
    telemetry_root = resolve(ROOT, cfg["telemetry_dir"])
    candidate_record = json.loads(candidate_record_path.read_text())
    flight_record = json.loads(flight_record_path.read_text())
    candidate = Vehicle.model_validate(yaml.safe_load(candidate_path.read_text()))
    identity = hashlib.sha256(candidate.model_dump_json(by_alias=True).encode()).hexdigest()
    if identity != cfg["expected_candidate_identity"]:
        raise ValueError(f"Candidate spec identity mismatch: {identity}")
    if identity != candidate_record.get(cfg["candidate_identity_field"]):
        raise ValueError("Candidate record identity mismatch")
    if identity != flight_record.get(cfg["flight_record_identity_field"]):
        raise ValueError("Flight record identity mismatch")
    if len(candidate.parts) != int(cfg["candidate_part_count"]):
        raise ValueError("Candidate part count mismatch")
    if candidate_record.get("status") != "candidate_only_unaccepted":
        raise ValueError("Unexpected candidate source status")
    if flight_record.get("status") != "completed_not_qualified":
        raise ValueError("Unexpected saved flight status")
    if flight_record.get("source_sha256_before") != flight_record.get("source_sha256_after"):
        raise ValueError("Flight run source hashes changed during its original execution")
    if candidate_record.get("source_sha256_before") != candidate_record.get("source_sha256_after"):
        raise ValueError("Candidate source hashes changed during its original execution")

    # Recheck every recorded upstream source against the current preserved bytes.
    candidate_source_hashes = actual_hash_map(ROOT, candidate_record["source_sha256_after"])
    flight_source_hashes = actual_hash_map(ROOT, flight_record["source_sha256_after"])
    inputs = {
        config_path.resolve(),
        Path(__file__).resolve(),
        candidate_path,
        candidate_record_path,
        flight_record_path,
        *[telemetry_root / p for p in cfg["cases"].values()],
    }
    input_hashes_before = {str(p.relative_to(ROOT)): sha256(p) for p in sorted(inputs)}

    fin = next((part for part in candidate.parts if part.type == "fin_set"), None)
    if fin is None:
        raise ValueError("Current candidate has no fin_set")
    geometry = planform_geometry(fin)
    span = float(geometry["span_m"])
    area = float(geometry["area_per_fin_m2"])
    cna = normal_force_coefficient_per_radian(
        float(fin.geometry["span_m"]),
        float(fin.geometry["root_chord_m"]),
        float(fin.geometry["tip_chord_m"]),
    )
    if not all(math.isfinite(v) and v > 0 for v in (span, area, cna)):
        raise ValueError("Fin geometry or coefficient is unsupported/nonfinite")
    cutoff_rad = math.radians(float(cfg["small_angle_diagnostic"]["cutoff_deg"]))
    recovery_lag = float(candidate.recovery.trigger_lag_s)
    inflation_s = float(candidate.recovery.inflation_s)

    flight_cases = {row["case_name"]: row for row in flight_record["cases"]}
    if set(flight_cases) != set(cfg["cases"]):
        raise ValueError("Saved flight cases do not match the configured three-case set")
    cases: dict[str, Any] = {}
    all_speeds: dict[str, float] = {}
    expected_columns = {
        "time_s", "down_m", "vn_mps", "ve_mps", "vd_mps", "thrust_n",
        "alpha_rad", "dynamic_pressure_pa", "landed",
    }
    for case_name, parquet_name in cfg["cases"].items():
        path = telemetry_root / parquet_name
        table = pq.read_table(path)
        if not expected_columns.issubset(set(table.column_names)):
            raise ValueError(f"Telemetry columns missing in {parquet_name}")
        col = finite_columns(table, sorted(expected_columns - {"landed"}))
        landed_raw = np.asarray(table["landed"].to_numpy(), dtype=np.float64)
        if not np.isfinite(landed_raw).all() or not set(np.unique(landed_raw)).issubset({0.0, 1.0}):
            raise ValueError(f"Invalid landed column in {parquet_name}")
        landed = landed_raw.astype(bool)
        times = col["time_s"]
        if len(times) != table.num_rows or len(times) == 0 or np.any(np.diff(times) <= 0):
            raise ValueError(f"Invalid or nonincreasing time column in {parquet_name}")
        live = np.flatnonzero(~landed)
        if live.size == 0:
            raise ValueError(f"No airborne samples in {parquet_name}")
        q = col["dynamic_pressure_pa"]
        alpha = col["alpha_rad"]
        thrust = col["thrust_n"]
        if np.any(q < 0) or np.any(thrust < 0):
            raise ValueError(f"Negative q or thrust in {parquet_name}")

        case_record = flight_cases[case_name]
        metrics = case_record["metrics"]
        apex_t = metrics.get("electronic_apogee_trigger_s")
        inflation_complete_t = metrics.get("inflation_complete_s")
        if not isinstance(apex_t, (int, float)) or not math.isfinite(float(apex_t)):
            raise ValueError(f"No finite saved apogee trigger event for {case_name}")
        deploy_start = float(apex_t) + recovery_lag
        expected_complete = deploy_start + inflation_s
        if not isinstance(inflation_complete_t, (int, float)) or abs(float(inflation_complete_t) - expected_complete) > 1e-8:
            raise ValueError(f"Saved recovery timing does not match candidate for {case_name}")
        apex_idx = int(live[int(np.argmin(col["down_m"][live]))])
        if abs(float(times[apex_idx]) - float(apex_t)) > float(case_record["case"]["dt_s"]) + 1e-9:
            raise ValueError(f"Telemetry apex disagrees with saved trigger event for {case_name}")

        tmax = float(metrics["max_speed_mps"])
        speed = np.sqrt(col["vn_mps"] ** 2 + col["ve_mps"] ** 2 + col["vd_mps"] ** 2)
        speed_from_rows = float(np.max(speed[live]))
        if abs(speed_from_rows - tmax) > 1e-5:
            raise ValueError(f"Saved speed metric and Parquet disagree for {case_name}")
        all_speeds[case_name] = speed_from_rows

        cn = np.minimum(cna * np.abs(alpha), 2.0)
        force = q * cn * area
        moment = force * span / 2.0
        if not all(np.isfinite(x).all() for x in (cn, force, moment)):
            raise ValueError(f"Nonfinite derived scalar loads for {case_name}")

        predeploy = live[times[live] < deploy_start]
        postdeploy = live[times[live] >= deploy_start]
        powered = predeploy[thrust[predeploy] > 0.0]
        coast = predeploy[thrust[predeploy] <= 0.0]
        if powered.size + coast.size + postdeploy.size != live.size:
            raise ValueError(f"Stage partition incomplete for {case_name}")

        phase_rows = [
            summarize_phase(
                label, idx, times=times, q=q, alpha=alpha, thrust=thrust, cn=cn,
                force=force, moment=moment, cutoff_rad=cutoff_rad,
            )
            for label, idx in (
                ("powered_predeployment", powered),
                ("coast_predeployment", coast),
                ("postdeployment_opening_and_descent", postdeploy),
            )
        ]
        if any(row["sample_count"] == 0 for row in phase_rows):
            raise ValueError(f"One required flight phase has no samples in {case_name}")

        qmax_i = int(live[int(np.argmax(q[live]))])
        qmax = float(q[qmax_i])
        envelope_f = qmax * 2.0 * area
        max_abs_alpha_i = int(live[int(np.argmax(np.abs(alpha[live])))])
        q_max_record = float(metrics["max_dynamic_pressure_pa"])
        if abs(qmax - q_max_record) > max(1e-6, qmax * 1e-9):
            raise ValueError(f"Parquet qmax and saved metric disagree for {case_name}")
        cases[case_name] = {
            "flight_case": case_record["case"],
            "parquet": parquet_name,
            "parquet_sha256": sha256(path),
            "sample_count_total": int(table.num_rows),
            "sample_count_landed_excluded": int(np.count_nonzero(landed)),
            "apogee_trigger_time_s": float(apex_t),
            "canopy_opening_start_inferred_s": deploy_start,
            "canopy_inflation_complete_s": float(inflation_complete_t),
            "canopy_timing_basis": "Saved flight metrics plus candidate trigger lag/inflation; Parquet contains no explicit deployment state.",
            "phase_loads": phase_rows,
            "overall_alpha_diagnostic": {
                "max_abs_alpha_time_s": float(times[max_abs_alpha_i]),
                "max_abs_alpha_deg": float(abs(np.rad2deg(alpha[max_abs_alpha_i]))),
                "samples_over_10deg": int(np.count_nonzero(np.abs(alpha[live]) > cutoff_rad)),
                "provisional_cutoff_deg": float(np.rad2deg(cutoff_rad)),
                "status": "diagnostic reporting only; the 10 degree cutoff is not a validated method domain or requirement change",
            },
            "maximum_q_times_cn2_envelope": {
                "qmax_pa": qmax,
                "qmax_time_s": float(times[qmax_i]),
                "alpha_at_qmax_deg": float(np.rad2deg(alpha[qmax_i])),
                "assumed_cn": 2.0,
                "force_per_fin_N": envelope_f,
                "root_moment_magnitude_per_fin_Nm": envelope_f * span / 2.0,
                "status": "noncoincident qmax*CN=2 envelope sensitivity; not a physical maximum or validated load bound",
            },
            "peak_speed_mps": speed_from_rows,
            "speed_metric_recorded_mps": tmax,
        }

    historical = cfg["historical_panel_case"]
    design_alpha = math.radians(float(historical["alpha_deg"]))
    design_cn = min(cna * abs(design_alpha), 2.0)
    design_force = float(historical["dynamic_pressure_pa"]) * design_cn * area
    known_case_force = 49.8071294055704
    if not math.isclose(design_force, known_case_force, rel_tol=1e-9, abs_tol=1e-9):
        raise ValueError(f"Historical 40 kPa / 5 deg formula check failed: {design_force}")

    input_hashes_after = {str(p.relative_to(ROOT)): sha256(p) for p in sorted(inputs)}
    if input_hashes_before != input_hashes_after:
        raise ValueError("Input bytes changed during read-only extraction")
    result = {
        "status": "completed_diagnostic_only",
        "candidate_identity": identity,
        "candidate_part_count": len(candidate.parts),
        "fin_load_method": "Unvalidated scalar panel-load estimate from saved q(t), alpha(t), CNa and uniform span/2 resultant; not a recovered simulator per-fin force, validated aero model or validated load bound.",
        "cad_orientation": {
            "base_fin_plane": "XZ, normal -Y in CAD generator before 120 degree sector rotations",
            "local_first_fin_axes": {"X": "radial/outward span", "Y": "tangential/fin-normal", "Z": "rocket axial"},
            "moment": "Magnitude uses F*(span/2). For a positive +Y normal force on the +X fin, r_X cross F_Y gives +M_Z, an axial root torque; alpha magnitude does not recover the physical load sign.",
        },
        "geometry": {
            "area_per_fin_m2": area,
            "span_m": span,
            "count": int(geometry["count"]),
            "planform_centroid_station_m": float(geometry["planform_centroid_station_m"]),
            "CNa_per_rad": cna,
            "coefficient_cap": 2.0,
        },
        "historical_40kPa_5deg_panel_design_case": {
            "q_pa": float(historical["dynamic_pressure_pa"]),
            "alpha_deg": float(historical["alpha_deg"]),
            "c_n": design_cn,
            "force_per_fin_N": design_force,
            "root_moment_magnitude_per_fin_Nm": design_force * span / 2.0,
            "df3_applied": False,
            "known_case_check": "Matches retained historical 49.8071294055704 N formula result; arithmetic sanity only.",
        },
        "cases": cases,
        "peak_speed_for_flutter_input": {
            "case_speeds_mps": all_speeds,
            "maximum_saved_case_speed_mps": max(all_speeds.values()),
            "meaning": "Candidate-specific kinematic speed input for a later flutter screen only; it is not a flutter pass or validated flight envelope.",
        },
        "design_factor": 1.0,
        "DF3_applied": False,
        "identity_and_source_validation": {
            "candidate_record_source_hashes_rechecked": len(candidate_source_hashes),
            "flight_record_source_hashes_rechecked": len(flight_source_hashes),
            "flight_record_before_after_equal": True,
            "candidate_record_before_after_equal": True,
            "input_sha256_before": input_hashes_before,
            "input_sha256_after": input_hashes_after,
        },
        "acceptance": False,
        "flight_ready": False,
        "elapsed_s": time.monotonic() - started,
        "resource_self": {
            "user_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime,
            "system_s": resource.getrusage(resource.RUSAGE_SELF).ru_stime,
            "peak_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
    }
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "configs/studies/wo03-g80-fin-loads.yaml")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cfg_path = args.config.resolve()
    cfg = yaml.safe_load(cfg_path.read_text())
    output = args.output.resolve() if args.output else resolve(ROOT, cfg["output_dir"])
    if output.exists():
        print(f"Output already exists; refusing to overwrite: {output}", file=sys.stderr)
        return 2
    cpu_limit = int(cfg["limits"]["max_cpu_s"])
    wall_limit = int(cfg["limits"]["max_wall_s"])
    if cpu_limit != 10 or wall_limit != 20:
        print("Configured limits must remain the declared 10 CPU s / 20 wall s", file=sys.stderr)
        return 2
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
    signal.signal(signal.SIGALRM, _wall_timeout)
    signal.alarm(wall_limit)
    failure_started = time.monotonic()
    try:
        result = run(cfg_path, output)
        signal.alarm(0)
        print(json.dumps({"status": result["status"], "elapsed_s": result["elapsed_s"], "peak_speed_mps": result["peak_speed_for_flutter_input"]["maximum_saved_case_speed_mps"]}))
        return 0
    except Exception as exc:
        signal.alarm(0)
        if not output.exists():
            output.mkdir(parents=True, exist_ok=False)
            shutil.copy2(cfg_path, output / "study-config.yaml")
            shutil.copy2(Path(__file__).resolve(), output / "executed.py")
        failure = {
            "status": "incomplete",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "elapsed_s": time.monotonic() - failure_started,
            "acceptance": False,
            "flight_ready": False,
        }
        (output / "failure.json").write_text(json.dumps(failure, indent=2) + "\n")
        print(json.dumps(failure), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
