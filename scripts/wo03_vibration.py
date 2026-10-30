"""Execute known-case, fin-shell, body-mode and preliminary flutter screening."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import yaml

from src.analysis.beam_modes import free_free_beam_modes
from src.analysis.engineering import structural
from src.analysis.fea import axial_bar
from src.analysis.fin_fea import run_shell
from src.analysis.fin_fields import export_fin_fields
from src.analysis.vibration import body_modes, flutter_screen, gimbal_sensor_screen
from src.vehicle.schema import load_vehicle, vehicle_input_paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/platform.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    parser.add_argument("--flight-record", type=Path)
    parser.add_argument("--require-benchmark", action="store_true")
    args = parser.parse_args()
    cfgpath = Path("configs/engineering/wo03.yaml")
    cfg = yaml.safe_load(cfgpath.read_text())
    platform = yaml.safe_load(args.config.read_text())
    paths = platform["vehicles"] + ["configs/vehicle/wo02/performance-g54.yaml"]
    run = datetime.now(UTC).strftime("wo03-vibration-%Y%m%dT%H%M%S%fZ")
    root = Path("build") / run
    root.mkdir()
    inputs = {args.config, cfgpath}
    for path in paths:
        inputs.update(vehicle_input_paths(path))
    if args.flight_record:
        inputs.add(args.flight_record)
    inputs.update(Path("src").rglob("*.py"))
    inputs.add(Path(__file__).resolve().relative_to(Path.cwd()))
    hashes = {
        p.resolve().relative_to(Path.cwd()).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(inputs)
    }
    bar = [axial_bar(root / "known-axial" / str(h), h) for h in [2.0, 1.5, 1.0]]
    strip = [run_shell(root / "known-strip" / str(h), None, h) for h in [5.0, 3.5, 2.5]]
    beam = []
    for n in [10, 20, 40]:
        b = free_free_beam_modes(np.linspace(0, 1, n + 1).tolist(), [100.0] * n, [1.0] * n)
        expected = np.array([4.7300407449, 7.8532046241, 10.9956078380]) ** 2 / (2 * np.pi) * 10
        beam.append(
            {
                "elements": n,
                "frequencies_hz": b.frequencies_hz.tolist(),
                "expected_hz": expected.tolist(),
                "max_relative_error": float(np.max(np.abs(b.frequencies_hz / expected - 1))),
            }
        )
    known = {
        "axial": bar,
        "shell_strip": strip,
        "body_beam": beam,
        "passed": all(r.get("passed", False) for r in bar)
        and all(r.get("known_case_passed", False) for r in strip)
        and all(r["max_relative_error"] < 0.01 for r in beam),
    }
    flight = json.loads(args.flight_record.read_text()) if args.flight_record else None
    vehicles = []
    fin_cache = {}
    for path in paths:
        v = load_vehicle(path)
        body = []
        for young, joint in product(
            cfg["vibration"]["youngs_fraction"], cfg["vibration"]["joint_stiffness_fraction"]
        ):
            levels = [body_modes(v, cfg, n, young, joint) for n in [20, 40, 80]]
            delta = float(
                np.max(
                    np.abs(
                        np.array(levels[-1]["frequencies_hz"][:3])
                        / levels[-2]["frequencies_hz"][:3]
                        - 1
                    )
                )
            )
            body.append(
                {
                    "stiffness_fraction": young,
                    "joint_fraction": joint,
                    "levels": levels,
                    "final_relative_frequency_change": delta,
                    "converged_first_three": delta < 0.05,
                }
            )
        s = structural(v, cfg)
        part = next((p for p in v.parts if p.type == "fin_set"), None)
        fin = None
        if part:
            force = float(next(r["force_per_fin_n"] for r in s["rows"] if r["part_id"] == part.id))
            assert part.cad_mass
            key = (part.cad_mass.shape_sha256, force)
            if key not in fin_cache:
                folder = root / v.id / "fin"
                levels = [
                    run_shell(folder / str(h), part, h, force_n=force) for h in [10.0, 7.0, 5.0]
                ]
                hot = run_shell(folder / "half-E", part, 5.0, force_n=force, stiffness_fraction=0.5)
                medium, fine = levels[-2:]
                du = abs(fine["max_displacement_m"] / medium["max_displacement_m"] - 1)
                ds = abs(fine["regional_von_mises_pa"] / medium["regional_von_mises_pa"] - 1)
                df = float(
                    np.max(
                        np.abs(
                            np.array(fine["frequencies_hz"][:3]) / medium["frequencies_hz"][:3] - 1
                        )
                    )
                )
                fin_cache[key] = {
                    "levels": levels,
                    "half_stiffness": hot,
                    "relative_changes": {
                        "displacement": du,
                        "regional_stress": ds,
                        "first_three_frequencies": df,
                    },
                    "mesh_converged": du < 0.05 and ds < 0.1 and df < 0.05,
                    "field_directory": str(folder),
                    "acceptance": "Convergence verifies this calculation; current thin-fin strength/deflection and root/thermal/aeroelastic release remain open.",
                }
            fin = fin_cache[key]
            field_folder = Path("build") / v.id / "analysis" / run
            export_fin_fields(
                v,
                Path(fin["field_directory"]) / "5.0",
                field_folder,
                run + "-" + v.id,
                hashes,
                known_case_verified=bool(known["passed"]),
                mesh_converged=bool(fin["mesh_converged"]),
            )
        else:
            field_folder = None
        matching = [c for c in flight["cases"] if c["vehicle"] == v.id] if flight else []
        current = False
        if flight:
            current = all(
                flight.get("input_sha256", {}).get(str(p))
                == hashlib.sha256(p.read_bytes()).hexdigest()
                for p in vehicle_input_paths(path)
            )
        envelope = {
            "record": str(args.flight_record) if args.flight_record else None,
            "current_spec_source_hashes_match": current,
            "mode_cases": len(matching),
            "max_speed_mps": max((c["metrics"]["max_speed_mps"] for c in matching), default=None),
            "max_dynamic_pressure_pa": max(
                (c["metrics"]["max_dynamic_pressure_pa"] for c in matching), default=None
            ),
            "limitation": "Matching source hashes do not validate unmodeled body/fin/control coupling or measured damping/excitation.",
        }
        identity = {
            "configuration": v.id,
            "resolved_spec_sha256": hashlib.sha256(
                v.model_dump_json(by_alias=True).encode()
            ).hexdigest(),
            "part_shape_sha256": {
                p.id: p.cad_mass.shape_sha256 if p.cad_mass else None for p in v.parts
            },
            "cad_revision_sha256": hashlib.sha256(
                b"".join(p.read_bytes() for p in sorted(Path("src/cad").glob("*.py")))
            ).hexdigest(),
        }
        row = {
            "identity": identity,
            "body_modes": body,
            "fin_shell": fin,
            "analysis_manifest": str(field_folder / "manifest.json") if field_folder else None,
            "export_consumer_check_passed": field_folder is not None,
            "flutter": flutter_screen(v, cfg),
            "gimbal_sensor": gimbal_sensor_screen(v, cfg),
            "flight_envelope": envelope,
            "vibration_flutter_acceptance_passed": False,
            "open_items": [
                "Attachment/contact and temperature-dependent properties unmeasured",
                "Full aeroelastic body/fin/control and large-alpha/stall domain not cleared",
                "Propulsion spectrum, damping, sensor mount/filter/aliasing and loaded actuator data unavailable",
            ],
        }
        (root / v.id).mkdir(exist_ok=True)
        (root / v.id / "report.json").write_text(json.dumps(row, indent=2) + "\n")
        vehicles.append(row)
        print(
            v.id,
            "body first mode range",
            min(b["levels"][-1]["frequencies_hz"][0] for b in body),
            max(b["levels"][-1]["frequencies_hz"][0] for b in body),
            "fin converged",
            fin["mesh_converged"] if fin else "N/A",
            flush=True,
        )
    result = {
        "run_id": run,
        "work_order": "03",
        "known_cases": known,
        "vehicles": vehicles,
        "input_sha256": hashes,
        "inputs_unchanged": all(
            hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items()
        ),
        "vibration_flutter_acceptance_passed": False,
        "expanded_wo03_benchmark_passed": False,
        "cost_usd": 0,
        "flight_ready": False,
    }
    out = Path("runs") / run
    out.mkdir()
    (out / "record.json").write_text(json.dumps(result, indent=2) + "\n")
    print(out / "record.json")
    return int(args.require_benchmark or not known["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
