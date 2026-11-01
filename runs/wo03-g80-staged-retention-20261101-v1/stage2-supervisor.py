"""Run one bounded static child and one four-case flight child in staged checkout."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path

import yaml

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
from scripts.wo03_owned_process import OwnedProcessError, darwin_process_callbacks, run_owned
from src.vehicle.schema import Vehicle


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def finite_tree(obj):
    if isinstance(obj, float):
        return math.isfinite(obj)
    if isinstance(obj, dict):
        return all(finite_tree(v) for v in obj.values())
    if isinstance(obj, list):
        return all(finite_tree(v) for v in obj)
    return True


def main():
    out = root / "build/wo03-g80-stage2-supervision"
    out.mkdir(parents=True, exist_ok=False)
    cfg = yaml.safe_load((root / "configs/studies/wo03-g80-stage2-flight.yaml").read_text())
    spec = root / cfg["candidate_spec"]
    record_path = root / cfg["candidate_record"]
    manifest = root / "inputs/stage2/stage1-manifest.json"
    original = root.parent / "stage1-result-metadata-final-v2"
    for copy, origin in (
        (spec, original / "resolved-candidate.yaml"),
        (record_path, original / "record.json"),
        (manifest, original / "manifest.json"),
    ):
        if sha(copy) != sha(origin):
            raise ValueError(f"Stage1 copied input differs: {copy.name}")
    vehicle = Vehicle.model_validate(yaml.safe_load(spec.read_text()))
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    stage1 = json.loads(record_path.read_text())
    m = json.loads(manifest.read_text())
    if (
        identity != cfg["expected_identity"]
        or identity != stage1["identity"]
        or identity != m["identity"]["resolved_spec_sha256"]
        or len(vehicle.parts) != 72
    ):
        raise ValueError("72-part staged identity mismatch")
    cad_revision = hashlib.sha256(
        b"".join(p.read_bytes() for p in sorted((root / "src/cad").glob("*.py")))
    ).hexdigest()
    if cad_revision != m["identity"]["cad_revision_sha256"] or vehicle.tvc is not None:
        raise ValueError("Staged CAD revision or fixed-control configuration mismatch")
    if (
        cfg["step_s"] != 0.005
        or cfg["horizon_s"] != 180
        or cfg["growth_kg"] != 0.05
        or cfg["growth_station_m"] != 1.212
        or len(cfg["cases"]) != 4
        or vehicle.design.rail_length_m != 1.5
        or vehicle.design.minimum_rail_exit_mps != 15
    ):
        raise ValueError("Declared case/benchmark settings changed")
    expected_cases = {
        "nominal_calm": {
            "thrust_scale": 1.0,
            "time_scale": 1.0,
            "drag_scale": 1.0,
            "added_mass_kg": 0.0,
            "rail_friction_n": 0.0,
        },
        "growth_low_thrust_high_drag": {
            "thrust_scale": 0.85,
            "time_scale": 0.95,
            "drag_scale": 1.2,
            "added_mass_kg": 0.05,
            "added_mass_station_m": 1.212,
            "rail_friction_n": 0.5,
        },
        "growth_high_thrust": {
            "thrust_scale": 1.15,
            "time_scale": 1.05,
            "drag_scale": 1.0,
            "added_mass_kg": 0.05,
            "added_mass_station_m": 1.212,
            "rail_friction_n": 0.0,
        },
        "nominal_steady_east_3mps": {
            "thrust_scale": 1.0,
            "time_scale": 1.0,
            "drag_scale": 1.0,
            "added_mass_kg": 0.0,
            "rail_friction_n": 0.0,
            "wind_east_mps": 3.0,
            "gust_amplitude_mps": 0.0,
        },
    }
    if cfg["cases"] != expected_cases or cfg["reference_relative_tolerance"] != 0.05:
        raise ValueError("Declared case definitions or reference tolerance changed")
    files = {
        Path(__file__).resolve(),
        spec,
        record_path,
        manifest,
        original / "resolved-candidate.yaml",
        original / "record.json",
        original / "manifest.json",
        root / "configs/studies/wo03-g80-stage2-flight.yaml",
        root / "configs/wo02.yaml",
        root / "configs/sim-model.yaml",
        root / vehicle.motor.curve,
        (root / vehicle.motor.curve).with_suffix(".yaml"),
    }
    for d in ("src/sim", "src/vehicle", "src/cad"):
        files.update((root / d).glob("*.py"))
    for n in (
        "wo03_g80_stage2_static.py",
        "wo03_g80_stage2_flight.py",
        "wo03_g80_candidate_flight.py",
        "wo03_integrated_report.py",
        "wo02_sim.py",
        "wo03_owned_process.py",
    ):
        files.add(root / "scripts" / n)
    before = {str(p): sha(p) for p in sorted(files)}
    env = dict(os.environ)
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "BLIS_NUM_THREADS",
    ):
        env[name] = "1"
    rss, children = darwin_process_callbacks()
    rec = {
        "status": "started",
        "candidate_identity": identity,
        "cad_revision": cad_revision,
        "source_before": before,
        "limits": {
            "setup_reserved_cpu_s": 30,
            "static_cpu_and_wall_s": 60,
            "flight_cpu_and_wall_s": 120,
            "packet_planned_cpu_s": 210,
            "packet_ceiling_cpu_s": 600,
            "rss_bytes": 2147483648,
        },
        "cases": 4,
        "acceptance": False,
    }

    def persist():
        (out / "record.json").write_text(json.dumps(rec, indent=2) + "\n")

    persist()
    failure = None
    try:
        for name, cap in [("static", 60), ("flight", 120)]:
            path = root / "scripts" / f"wo03_g80_stage2_{name}.py"
            launch = (
                "import os,resource,sys;resource.setrlimit(resource.RLIMIT_CPU,("
                + str(cap)
                + ","
                + str(cap)
                + "));os.execv(sys.executable,[sys.executable,"
                + repr(str(path))
                + "])"
            )
            rec[name + "_status"] = run_owned(
                [sys.executable, "-c", launch],
                log_path=out / (name + ".log"),
                status_path=out / (name + "-status.json"),
                wall_limit_s=cap,
                rss_callback=rss,
                descendants_callback=children,
                rss_limit_bytes=2147483648,
                cwd=root,
                env=env,
            )
            resultpath = root / (
                "build/wo03-g80-stage2-static/record.json"
                if name == "static"
                else "build/wo03-g80-stage2-flight/record.json"
            )
            result = json.loads(resultpath.read_text())
            if not finite_tree(result):
                raise ValueError(f"{name} returned nonfinite values")
            if name == "flight" and (
                len(result["cases"]) != 4
                or any(not r["metrics"]["finite"] for r in result["cases"])
            ):
                raise ValueError("Missing or nonfinite flight case")
            rec[name + "_record_sha256"] = sha(resultpath)
            if name == "flight":
                landing_path = root / "build/wo03-g80-stage2-flight/landing-screens.json"
                landing = json.loads(landing_path.read_text())
                if len(landing) != 4 or not finite_tree(landing):
                    raise ValueError("Missing or nonfinite landing metrics")
                rec["landing_screens_sha256"] = sha(landing_path)
            persist()
        rec["status"] = "completed_not_qualified"
    except (OwnedProcessError, OSError, ValueError, KeyError) as exc:
        failure = f"{type(exc).__name__}: {exc}"
        rec.update(status="stopped", error=failure)
    finally:
        for name in ("static", "flight"):
            p = out / (name + "-status.json")
            if p.exists():
                rec[name + "_status"] = json.loads(p.read_text())
        rec["source_after"] = {str(p): sha(p) for p in files}
        rec["source_unchanged"] = rec["source_before"] == rec["source_after"]
        if not rec["source_unchanged"]:
            rec.update(status="stopped", error="Source changed during stage 2")
        persist()
    if failure or not rec["source_unchanged"]:
        raise RuntimeError(f'Stage2 stopped: {rec.get("error")}')
    print(
        json.dumps(
            {
                "status": rec["status"],
                "identity": identity,
                "static": rec["static_record_sha256"],
                "flight": rec["flight_record_sha256"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
