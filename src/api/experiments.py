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

from fastapi import APIRouter, HTTPException
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


def _save(folder: Path, record: dict[str, Any]) -> None:
    tmp = folder / "record.tmp"
    tmp.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    os.replace(tmp, folder / "record.json")


def _record(run_id: str) -> dict[str, Any]:
    if (
        not run_id.startswith("exp-")
        or len(run_id) != 36
        or any(c not in "0123456789abcdef" for c in run_id[4:])
    ):
        raise HTTPException(404, "Experiment not found")
    try:
        return cast(dict[str, Any], json.loads((RUNS / run_id / "record.json").read_text()))
    except (FileNotFoundError, ValueError):
        raise HTTPException(404, "Experiment not found") from None


def _execute(run_id: str, req: Request) -> None:
    folder = RUNS / run_id
    record = _record(run_id)
    try:
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
            cad_revision_sha256=hashlib.sha256(
                b"".join(path.read_bytes() for path in sorted((ROOT / "src/cad").glob("*.py")))
            ).hexdigest(),
        )
        _save(folder, record)
        final, rows = env.rollout(
            p, jax.random.PRNGKey(0), steps=round(case["max_time_s"] / case["dt_s"])
        )
        final.rigid.block_until_ready()
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
        _save(folder, record)
    except Exception as exc:  # noqa: BLE001 - report any worker failure to the caller
        record.update(
            status="failed", progress="Experiment failed", error=f"{type(exc).__name__}: {exc}"
        )
        _save(folder, record)
    finally:
        _busy.release()


@router.post("/api/experiments", status_code=202)
def start_experiment(req: Request) -> dict[str, Any]:
    if not _busy.acquire(blocking=False):
        raise HTTPException(409, "Another experiment is running; wait for it to finish")
    try:
        RUNS.mkdir(exist_ok=True)
        run_id = "exp-" + uuid4().hex
        folder = RUNS / run_id
        folder.mkdir()
        record = {
            "run_id": run_id,
            "status": "queued",
            "progress": "Queued",
            "created_at": datetime.now(UTC).isoformat(),
            "configuration": req.configuration,
            "configuration_path": CONFIGS[req.configuration],
            "settings": req.model_dump(),
            "controller": "locked, unguided",
            "flight_ready": False,
            "limitations": [
                "Preliminary numerical source hypothesis; no hardware or flight approval.",
                "Wind and attitude predictions are not independently validated; high angle of attack exceeds the supported aerodynamic model.",
                "Recovery is a simplified point-drag and inflation model; structural, thermal and motion gates remain open.",
                "G54 source identity remains conditional; G12 is plugged and has no motor ejection backup.",
            ],
        }
        _save(folder, record)
        _executor.submit(_execute, run_id, req)
        return {"run_id": run_id, "status": "queued"}
    except Exception:
        _busy.release()
        raise


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


@router.get("/api/runs/{run_id}/telemetry")
def telemetry(run_id: str) -> dict[str, Any]:
    record = _record(run_id)
    if record["status"] != "complete":
        raise HTTPException(409, "Telemetry is available only after completion")
    import numpy as np
    import pyarrow.parquet as pq

    from src.sim.frames import STANDARD_GRAVITY_M_S2

    table = pq.read_table(RUNS / run_id / "telemetry.parquet")
    # Keep endpoints and event-adjacent samples in addition to uniform decimation.
    times = table["time_s"].to_numpy()
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
        "full_sample_count": len(times),
        "columns": selected,
    }
