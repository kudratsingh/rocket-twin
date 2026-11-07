"""Bounded, local single-flight experiments using the shared WO-02 JAX model."""

from __future__ import annotations

import hashlib
import json
import math
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "runs"
CONFIGS = {
    "modular-performance-v1": "configs/vehicle/platform/performance.yaml",
    "modular-tvc-finned-v1": "configs/vehicle/platform/tvc-finned.yaml",
    "modular-performance-g54-hypothesis": "configs/vehicle/wo02/performance-g54.yaml",
}
router = APIRouter()
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="experiment")
_busy = threading.Lock()
_state = threading.RLock()
_SESSION = uuid4().hex
_cancel: dict[str, threading.Event] = {}
_TERMINAL = {"complete", "failed", "cancelled", "interrupted"}


class _Cancelled(Exception):
    """Cooperative stop at an explicit model boundary, never a forced JAX kill."""


def _check_cancel(run_id: str) -> None:
    if _cancel.get(run_id, threading.Event()).is_set():
        raise _Cancelled("Cancellation acknowledged at a safe boundary; no result admitted")


class Request(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    configuration: str

    @field_validator("configuration")
    @classmethod
    def supported_configuration(cls, value: str) -> str:
        if value == "modular-tvc-finless-v1":
            raise ValueError("Finless unguided flight is unsupported; no controller is available")
        if value not in CONFIGS:
            raise ValueError("Choose an allowlisted complete vehicle and motor configuration")
        return value

    wind_mps: float = Field(default=0, ge=0, le=10)
    wind_direction_deg: float = Field(default=0, ge=0, lt=360)
    gust_mps: float = Field(default=0, ge=0, le=5)
    preset: Literal["tiny", "sim"] = "sim"
    seed: int = Field(default=0, ge=0, le=4294967295, strict=True)


class BatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    cases: list[Request] = Field(min_length=2, max_length=4)
    concurrency: Literal[1] = 1
    resource: Literal["local-cpu"] = "local-cpu"


def _resources(req: Request) -> dict[str, Any]:
    return {
        "backend": "cpu",
        "concurrency": 1,
        "dt_s": 0.005 if req.preset == "tiny" else 0.001,
        "max_time_s": 45 if req.preset == "tiny" else 360,
        "max_steps": 9000 if req.preset == "tiny" else 360000,
        "seed": req.seed,
        "storage": "One record/resolved snapshot and at most max_steps rows of Parquet per member; retained locally without automatic deletion. Compressed bytes and JAX compilation memory vary by host.",
        "cancellation": "cooperative before/after JAX rollout; an in-flight compiled rollout is not forcibly terminated",
    }


def _save(folder: Path, record: dict[str, Any]) -> None:
    with _state:
        target = folder / "record.json"
        if target.exists():
            previous = json.loads(target.read_text())
            if previous.get("cancel_requested_at"):
                record.setdefault("cancel_requested_at", previous["cancel_requested_at"])
        tmp = folder / "record.tmp"
        tmp.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
        os.replace(tmp, target)


def _record(run_id: str) -> dict[str, Any]:
    if (
        not run_id.startswith("exp-")
        or len(run_id) != 36
        or any(c not in "0123456789abcdef" for c in run_id[4:])
    ):
        raise HTTPException(404, "Experiment not found")
    try:
        with _state:
            record = cast(dict[str, Any], json.loads((RUNS / run_id / "record.json").read_text()))
            if record.get("status") not in _TERMINAL and record.get("worker_session") != _SESSION:
                record.update(
                    status="interrupted",
                    progress="Interrupted: owning API process is no longer present",
                    error="API process ended before a terminal result was saved; retry creates a new attempt",
                    finished_at=datetime.now(UTC).isoformat(),
                )
                _save(RUNS / run_id, record)
            return record
    except (FileNotFoundError, ValueError):
        raise HTTPException(404, "Experiment not found") from None


def _execute(run_id: str, req: Request) -> None:
    folder = RUNS / run_id
    record = _record(run_id)
    try:
        _check_cancel(run_id)
        record.update(
            status="running",
            progress="Preparing the complete vehicle and compiling the CPU simulation",
        )
        _save(folder, record)
        from importlib import import_module

        import jax
        import numpy as np

        wo02 = import_module("scripts.wo02_sim")
        code_digest, metrics = wo02.code_digest, wo02.metrics
        from src.sim import env
        from src.sim.inputs import prepare, source_hashes
        from src.sim.telemetry import write_parquet
        from src.vehicle.schema import load_vehicle, vehicle_input_paths

        path = CONFIGS[req.configuration]
        vehicle = load_vehicle(ROOT / path)
        inputs = {
            str(p.relative_to(ROOT) if p.is_absolute() else p): hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
            for p in vehicle_input_paths(ROOT / path)
        }
        inputs.update(source_hashes(vehicle))
        resolved = vehicle.model_dump_json(by_alias=True, indent=2) + "\n"
        (folder / "resolved.json").write_text(resolved)
        angle = math.radians(req.wind_direction_deg)
        case = {
            "dt_s": 0.005 if req.preset == "tiny" else 0.001,
            "max_time_s": 45 if req.preset == "tiny" else 360,
            "sensor_noise": True,
            "elevation_m": 850,
            "wind_north_mps": req.wind_mps * math.cos(angle),
            "wind_east_mps": req.wind_mps * math.sin(angle),
            "gust_amplitude_mps": req.gust_mps,
        }
        code_hash = code_digest()
        p = prepare(vehicle, case)
        if jax.default_backend() != "cpu":
            raise RuntimeError("Experiment requires the CPU JAX backend")
        record.update(
            progress="Running shared JAX rollout; compilation may take a moment",
            case=case,
            vehicle_id=vehicle.id,
            input_sha256=inputs,
            code_sha256=code_hash,
            resolved_sha256=hashlib.sha256(
                vehicle.model_dump_json(by_alias=True).encode()
            ).hexdigest(),
            random_seed=req.seed,
            rng="jax.random.PRNGKey; sensor noise enabled",
            effective_settings={**req.model_dump(), **case, "controller": "locked, unguided"},
            cad_revision_sha256=hashlib.sha256(
                b"".join(path.read_bytes() for path in sorted((ROOT / "src/cad").glob("*.py")))
            ).hexdigest(),
        )
        _save(folder, record)
        _check_cancel(run_id)
        final, rows = env.rollout(
            p, jax.random.PRNGKey(req.seed), steps=round(case["max_time_s"] / case["dt_s"])
        )
        final.rigid.block_until_ready()
        _check_cancel(run_id)
        rows = np.asarray(rows)
        result = metrics(final, rows, p)
        if not result["finite"]:
            raise RuntimeError("The simulation produced non-finite telemetry; no replay was saved")
        if code_digest() != code_hash or any(
            hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest
            for name, digest in inputs.items()
        ):
            raise RuntimeError(
                "Simulation inputs or model changed during the run; result discarded"
            )
        landed = np.flatnonzero(rows[:, -1] > 0)
        if len(landed):
            rows = rows[: landed[0] + 1]
        write_parquet(folder / "telemetry.parquet", rows)
        apex = float(final.recovery_time)
        record.update(
            status="complete",
            progress="Complete",
            metrics=result,
            events={
                "ignition": 0.0,
                "guide_exit": result["guide_exit_s"] if result["guide_exit_s"] >= 0 else None,
                "burnout": (
                    result["burnout_s"] if result["burnout_s"] <= float(rows[-1, 0]) else None
                ),
                "apogee": apex if apex >= 0 else None,
                "deployment": (
                    apex + float(p.recovery[1])
                    if apex >= 0 and apex + float(p.recovery[1]) <= float(rows[-1, 0])
                    else None
                ),
                "landing": result["impact_time_s"],
            },
            trajectory_complete=bool(len(landed)),
            result_state="full_trajectory" if len(landed) else "partial_trajectory",
            telemetry_samples=len(rows),
            validity=[
                (
                    f"Free-flight powered angle of attack: {result['powered_max_alpha_deg']:.1f}°; "
                    + (
                        "exceeds the 15° small-angle screening bound."
                        if result["powered_max_alpha_deg"] > 15
                        else "within the 15° screening bound; aerodynamic derivatives remain unvalidated."
                    )
                    if result["guide_exit_s"] >= 0
                    else "Free-flight powered angle of attack unavailable: guide exit not recorded."
                ),
                (
                    f"Peak powered Mach: {result['powered_max_mach']:.3f}; "
                    + (
                        "exceeds the 0.8 subsonic screening bound."
                        if result["powered_max_mach"] > 0.8
                        else "within the 0.8 screening bound; this is not physical validation."
                    )
                ),
                (
                    f"Steady wind {req.wind_mps:g} m/s, gust {req.gust_mps:g} m/s: "
                    + (
                        "exceeds the magnitude of the archived 3 m/s plus 1 m/s gust sensitivity case; this is not an operational wind envelope."
                        if req.wind_mps > 3 or req.gust_mps > 1
                        else "wind and attitude remain unvalidated; the archived sensitivity case used a different height profile."
                    )
                ),
                (
                    "G54 motor identity and source correspondence remain conditional."
                    if req.configuration == "modular-performance-g54-hypothesis"
                    else "Motor source is a preliminary numerical hypothesis."
                ),
                (
                    "G12 finned trainer assumes 5 m usable guide travel; actual guide equipment and travel are unconfirmed. The motor is plugged and lacks motor-ejection backup."
                    if req.configuration == "modular-tvc-finned-v1"
                    else "Guide conditions are assumptions, not an installed hardware or site validation."
                ),
                (
                    "Modeled accelerometer range was exceeded; sensor observations clip."
                    if result["accel_range_exceeded"]
                    else "Accelerometer model range was not exceeded in the powered portion; sensor behavior remains unvalidated."
                ),
            ],
        )
        with _state:
            _check_cancel(run_id)
            record["finished_at"] = datetime.now(UTC).isoformat()
            _save(folder, record)
    except _Cancelled as exc:
        record.update(
            status="cancelled",
            progress="Cancelled",
            error=str(exc),
            finished_at=datetime.now(UTC).isoformat(),
        )
        _save(folder, record)
    except Exception as exc:  # noqa: BLE001 - report any worker failure to the caller
        record.update(
            status="failed",
            progress="Experiment failed",
            error=f"{type(exc).__name__}: {exc}",
            finished_at=datetime.now(UTC).isoformat(),
        )
        _save(folder, record)


def _create_record(req: Request, batch_id: str | None = None) -> str:
    RUNS.mkdir(exist_ok=True)
    run_id = "exp-" + uuid4().hex
    folder = RUNS / run_id
    folder.mkdir()
    _cancel[run_id] = threading.Event()
    record = {
        "run_id": run_id,
        "status": "queued",
        "progress": "Queued",
        "created_at": datetime.now(UTC).isoformat(),
        "worker_session": _SESSION,
        "configuration": req.configuration,
        "configuration_path": CONFIGS[req.configuration],
        "settings": req.model_dump(),
        "normalized_request_sha256": hashlib.sha256(req.model_dump_json().encode()).hexdigest(),
        "resources": _resources(req),
        "random_seed": req.seed,
        "batch_id": batch_id,
        "controller": "locked, unguided",
        "flight_ready": False,
        "limitations": [
            "Preliminary numerical source hypothesis; no hardware or flight approval.",
            "Wind and attitude predictions are not independently validated; high angle of attack exceeds the supported aerodynamic model.",
            "Recovery is a simplified point-drag and inflation model; structural, thermal and motion gates remain open.",
            "G54 source identity remains conditional; G12 is plugged and lacks motor ejection backup.",
        ],
    }
    _save(folder, record)
    return run_id


def _run_members(run_ids: list[str], cases: list[Request]) -> None:
    try:
        for run_id, req in zip(run_ids, cases, strict=True):
            _execute(run_id, req)
    finally:
        for run_id in run_ids:
            try:
                record = _record(run_id)
                if record["status"] not in _TERMINAL:
                    record.update(
                        status="interrupted",
                        progress="Worker ended without a terminal result",
                        error="Batch worker exited early; retry creates a new attempt",
                        finished_at=datetime.now(UTC).isoformat(),
                    )
                    _save(RUNS / run_id, record)
            finally:
                _cancel.pop(run_id, None)
        _busy.release()


def _existing_submission(key: str | None, payload: str) -> dict[str, Any] | None:
    if not key:
        return None
    if not 8 <= len(key) <= 100 or not all(c.isalnum() or c in "-_" for c in key):
        raise HTTPException(
            422, "Idempotency-Key must be 8–100 letters, numbers, dashes or underscores"
        )
    for path in RUNS.glob("exp-*/record.json"):
        record = _record(path.parent.name)
        if record.get("submission_key") == key:
            if record.get("submission_payload") != payload:
                raise HTTPException(409, "Idempotency key already identifies different inputs")
            return record
    return None


def _submit(cases: list[Request], key: str | None, batch: bool) -> dict[str, Any]:
    payload = json.dumps(
        {"cases": [req.model_dump() for req in cases], "batch": batch}, sort_keys=True
    )
    with _state:
        previous = _existing_submission(key, payload)
        if previous:
            ids = previous.get("batch_members") or [previous["run_id"]]
            return {
                "run_id": previous["run_id"],
                "status": previous["status"],
                "batch_id": previous.get("batch_id"),
                "run_ids": ids,
            }
        if not _busy.acquire(blocking=False):
            raise HTTPException(409, "Another experiment or batch owns the single local CPU slot")
        run_ids: list[str] = []
        try:
            batch_id = "batch-" + uuid4().hex if batch else None
            for req in cases:
                run_ids.append(_create_record(req, batch_id))
            for run_id in run_ids:
                record = _record(run_id)
                record.update(
                    submission_key=key,
                    submission_payload=payload,
                    batch_members=run_ids if batch else None,
                )
                _save(RUNS / run_id, record)
            _executor.submit(_run_members, run_ids, cases)
            return {
                "run_id": run_ids[0],
                "status": "queued",
                "batch_id": batch_id,
                "run_ids": run_ids,
            }
        except Exception:
            for run_id in run_ids:
                record = _record(run_id)
                record.update(
                    status="failed",
                    progress="Submission failed",
                    error="Worker could not be submitted",
                )
                _save(RUNS / run_id, record)
                _cancel.pop(run_id, None)
            _busy.release()
            raise


@router.post("/api/experiments", status_code=202)
def start_experiment(
    req: Request, idempotency_key: str | None = Header(default=None)
) -> dict[str, Any]:
    return _submit([req], idempotency_key, False)


@router.post("/api/experiment-batches", status_code=202)
def start_batch(
    req: BatchRequest, idempotency_key: str | None = Header(default=None)
) -> dict[str, Any]:
    return _submit(req.cases, idempotency_key, True)


@router.post("/api/experiments/{run_id}/cancel", status_code=202)
def cancel_experiment(run_id: str) -> dict[str, Any]:
    with _state:
        first = _record(run_id)
        ids = first.get("batch_members") or [run_id]
        for member in ids:
            record = _record(member)
            if record["status"] in _TERMINAL:
                continue
            event = _cancel.get(member)
            if event is not None:
                event.set()
                record.update(
                    status="cancel_requested",
                    progress="Cancellation requested; awaiting safe model boundary",
                    cancel_requested_at=datetime.now(UTC).isoformat(),
                )
                _save(RUNS / member, record)
        return {
            "run_ids": ids,
            "members": [_record(member) for member in ids],
            "acknowledgement": "Request saved; running JAX work terminates only at a safe boundary",
        }


@router.get("/api/experiments/{run_id}")
def experiment(run_id: str) -> dict[str, Any]:
    return _record(run_id)


@router.get("/api/runs")
def runs() -> list[dict[str, Any]]:
    if not RUNS.exists():
        return []
    result = []
    for path in sorted(RUNS.glob("exp-*/record.json"), reverse=True):
        try:
            record = _record(path.parent.name)
            result.append(record)
        except HTTPException:
            continue
    return sorted(result, key=lambda x: x["created_at"], reverse=True)


@router.get("/api/runs/{run_id}")
def run_record(run_id: str) -> dict[str, Any]:
    return _record(run_id)


# Explicit meanings for the present telemetry schema. Unknown future columns remain
# selectable, but carry no assumed unit or comparison semantics.
_RAW_UNITS = {
    **dict.fromkeys(("time_s", "sensor_time_s"), "s"),
    **dict.fromkeys(("north_m", "east_m", "down_m", "cg_station_m", "baro_agl_m"), "m"),
    **dict.fromkeys(("vn_mps", "ve_mps", "vd_mps"), "m/s"),
    **dict.fromkeys(("qw", "qx", "qy", "qz", "mach", "landed"), "dimensionless"),
    **dict.fromkeys(
        ("wx_rad_s", "wy_rad_s", "wz_rad_s", "gyro_x_rad_s", "gyro_y_rad_s", "gyro_z_rad_s"),
        "rad/s",
    ),
    "mass_kg": "kg",
    "thrust_n": "N",
    "dynamic_pressure_pa": "Pa",
    **dict.fromkeys(
        ("alpha_rad", "gimbal_pitch_rad", "gimbal_yaw_rad", "encoder_pitch_rad", "encoder_yaw_rad"),
        "rad",
    ),
    **dict.fromkeys(
        (
            "specific_x_mps2",
            "specific_y_mps2",
            "specific_z_mps2",
            "imu_ax_mps2",
            "imu_ay_mps2",
            "imu_az_mps2",
            "high_g_ax_mps2",
            "high_g_ay_mps2",
            "high_g_az_mps2",
        ),
        "m/s²",
    ),
}
_DERIVED = {
    "height_m": ("m", "Height above launch"),
    "height_ft": ("ft", "Height above launch"),
    "speed_mps": ("m/s", "Speed magnitude"),
    "speed_mph": ("mph", "Speed magnitude"),
    "specific_force_mps2": ("m/s²", "Specific-force magnitude, excluding gravity"),
    "net_acceleration_mps2": ("m/s²", "Net acceleration magnitude, including gravity"),
    "tilt_deg": ("°", "Tilt from vertical"),
    "downrange_m": ("m", "Horizontal distance from launch"),
    "downrange_ft": ("ft", "Horizontal distance from launch"),
}


def _channel_metadata(raw_names: set[str], names: Any) -> dict[str, dict[str, Any]]:
    result = {}
    for name in names:
        derived = name in _DERIVED and name not in raw_names
        unit, description = (
            _DERIVED[name] if derived else (_RAW_UNITS.get(name), name.replace("_", " "))
        )
        known = derived or (name in raw_names and name in _RAW_UNITS)
        result[name] = {
            "source": "backend-derived" if derived else "recorded-parquet",
            "unit": unit,
            "description": (
                description if known else "Unknown channel; meaning and units unavailable"
            ),
            "semantic_id": f"wo05-v1:{name}" if known else None,
        }
    return result


@router.get("/api/runs/{run_id}/telemetry")
def telemetry(
    run_id: str, playback: Literal["bounded", "full-rate-benchmark"] = "bounded"
) -> dict[str, Any]:
    record = _record(run_id)
    if record["status"] != "complete":
        raise HTTPException(409, "Telemetry is available only after completion")
    import numpy as np
    import pyarrow.parquet as pq

    from src.sim.frames import STANDARD_GRAVITY_M_S2

    path = RUNS / run_id / "telemetry.parquet"
    if playback == "full-rate-benchmark":
        import pyarrow as pa

        source = pq.ParquetFile(path)
        if source.metadata.num_rows > 150000:
            raise HTTPException(
                413,
                "Full-rate benchmark is capped at 150000 native rows; no decimation or truncated benchmark is substituted",
            )
        if len(source.schema_arrow) > 64 or not all(
            pa.types.is_integer(field.type)
            or pa.types.is_floating(field.type)
            or pa.types.is_boolean(field.type)
            for field in source.schema_arrow
        ):
            raise HTTPException(
                413, "Full-rate benchmark requires at most 64 scalar numeric/boolean raw channels"
            )
    table = pq.read_table(path)
    # Derived display columns must never overwrite a recorded field of the same name.
    if set(table.column_names) & set(_DERIVED):
        raise HTTPException(409, "Recorded telemetry conflicts with derived display channels")
    # Keep endpoints and event-adjacent samples in addition to uniform decimation.
    times = table["time_s"].to_numpy()
    if not len(times) or not np.isfinite(times).all() or (np.diff(times) <= 0).any():
        raise HTTPException(
            409, "Recorded telemetry time axis is empty, nonfinite or not increasing"
        )
    if playback == "full-rate-benchmark":
        indices = None
        selected = table.to_pydict()
    else:
        indices = set(np.linspace(0, len(times) - 1, min(len(times), 3000), dtype=int).tolist())
        for event in record["events"].values():
            if event is not None:
                i = int(np.searchsorted(times, event))
                indices.update(max(0, min(len(times) - 1, j)) for j in (i - 1, i))
        selected = table.take(sorted(indices)).to_pydict()
    c = selected
    c["height_m"] = (-np.array(c["down_m"])).tolist()
    c["speed_mps"] = np.linalg.norm(
        np.array([c["vn_mps"], c["ve_mps"], c["vd_mps"]]), axis=0
    ).tolist()
    c["specific_force_mps2"] = np.linalg.norm(
        np.array([c["specific_x_mps2"], c["specific_y_mps2"], c["specific_z_mps2"]]), axis=0
    ).tolist()
    qw, qx, qy, qz = (np.asarray(c[name]) for name in ("qw", "qx", "qy", "qz"))
    sx, sy, sz = (
        np.asarray(c[name]) for name in ("specific_x_mps2", "specific_y_mps2", "specific_z_mps2")
    )
    # Rotate the measured body-frame specific-force vector into NED and add
    # the gravity acceleration, as in WO-02's powered net-acceleration metric.
    down_specific = (
        2 * (qx * qz - qw * qy) * sx
        + 2 * (qy * qz + qw * qx) * sy
        + (1 - 2 * (qx * qx + qy * qy)) * sz
    )
    gravity = STANDARD_GRAVITY_M_S2
    c["net_acceleration_mps2"] = np.sqrt(
        np.maximum(0, sx * sx + sy * sy + sz * sz + gravity * gravity + 2 * gravity * down_specific)
    ).tolist()
    c["tilt_deg"] = np.degrees(
        np.arccos(
            np.clip(
                -2
                * (np.array(c["qx"]) * np.array(c["qz"]) - np.array(c["qw"]) * np.array(c["qy"])),
                -1,
                1,
            )
        )
    ).tolist()
    c["downrange_m"] = np.hypot(c["north_m"], c["east_m"]).tolist()
    # Unit conversions are computed server-side alongside the recorded telemetry.
    c["height_ft"] = (np.asarray(c["height_m"]) / 0.3048).tolist()
    c["speed_mph"] = (np.asarray(c["speed_mps"]) * 2.2369362920544).tolist()
    c["downrange_ft"] = (np.asarray(c["downrange_m"]) / 0.3048).tolist()
    return {
        "run_id": run_id,
        "frame": "NED; body x forward; quaternion scalar first",
        "source_identity": {
            key: record.get(key)
            for key in (
                "configuration",
                "vehicle_id",
                "configuration_path",
                "code_sha256",
                "resolved_sha256",
                "cad_revision_sha256",
                "input_sha256",
                "random_seed",
                "settings",
                "effective_settings",
            )
        },
        "full_sample_count": len(times),
        "returned_sample_count": len(times) if indices is None else len(indices),
        "sampling": {
            "mode": playback,
            "policy": (
                "Explicit full-rate benchmark: every native row returned, without temporal decimation or interpolation"
                if playback == "full-rate-benchmark"
                else "At most 3000 uniform recorded samples plus two neighbours per finite recorded event; endpoints retained"
            ),
            "benchmark_bounds": {
                "max_native_rows": 150000,
                "max_raw_channels": 64,
                "max_returned_channels": 64 + len(_DERIVED),
                "returned_channels": len(selected),
                "numeric_float64_bytes": (len(times) if indices is None else len(indices))
                * len(selected)
                * 8,
                "numeric_json_envelope_bytes": (len(times) if indices is None else len(indices))
                * len(selected)
                * 32,
                "estimate_scope": "Numeric cell storage/JSON envelope estimates only; metadata, parsing, CAD, derived arrays and browser heap add overhead. Not measured wire transfer or peak memory.",
            },
            "uniform_limit": None if playback == "full-rate-benchmark" else 3000,
            "event_count": sum(value is not None for value in record["events"].values()),
            "interpolated": False,
            "peak_metrics": "Full-rate backend metrics in record.json; playback extrema are not authoritative",
        },
        "channel_metadata": _channel_metadata(set(table.column_names), selected),
        "columns": selected,
    }


@router.get("/api/runs/{run_id}/telemetry.arrow")
def telemetry_arrow(run_id: str) -> Response:
    """The same bounded native samples, with provenance in Arrow schema metadata."""
    import pyarrow as pa
    from pyarrow import ipc

    payload = telemetry(run_id)
    columns = payload.pop("columns")
    table = pa.Table.from_pydict(columns)
    table = table.replace_schema_metadata(
        {b"rocket-twin-playback": json.dumps(payload, allow_nan=False).encode()}
    )
    sink = pa.BufferOutputStream()
    with ipc.new_stream(sink, table.schema) as writer:
        writer.write_table(table)
    return Response(
        content=sink.getvalue().to_pybytes(),
        media_type="application/vnd.apache.arrow.stream",
        headers={"Content-Disposition": f'attachment; filename="{run_id}-playback.arrow"'},
    )
