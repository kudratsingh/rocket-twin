"""Bounded guide-only comparison using the pinned existing screen_launch function.

No free flight or new physics. Newton's law and source conservative assumptions
remain in src/vehicle/benchmark.py. Recovery mean force is DF*m*(v²/(2s)+g),
work-energy with gravity; it is not a measured transient peak.
"""

from __future__ import annotations

import hashlib
import json
import os
import resource
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-launch-guide-motor-trade.yaml"
OUT = ROOT / "runs/wo03-launch-guide-motor-trade-20261102-v1"


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def opening(mass, speed, recovery):
    return (
        recovery["design_factor"]
        * mass
        * (speed**2 / (2 * recovery["stopping_distance_m"]) + 9.80665)
    )


def main():
    start, cpu_start = time.monotonic(), time.process_time()
    cfg = yaml.safe_load(CONFIG.read_text())
    lim = cfg["limits"]
    resource.setrlimit(resource.RLIMIT_CPU, (lim["packet_cpu_s"], lim["packet_cpu_s"] + 1))
    OUT.mkdir(parents=True, exist_ok=True)
    staged = ROOT / cfg["staged_checkout"]
    sys.path.insert(0, str(staged))
    os.chdir(staged)
    from src.vehicle.benchmark import screen_launch
    from src.vehicle.motors import load_rasp
    from src.vehicle.schema import Vehicle

    v = Vehicle.model_validate(yaml.safe_load((ROOT / cfg["source_spec"]).read_text()))
    a = cfg["assumptions"]
    assert [
        v.design.thrust_scale_lower,
        v.design.rail_friction_n,
        v.design.drag_coefficient_upper,
        v.airframe["body_diameter_m"],
    ] == [
        a["thrust_scale_lower"],
        a["rail_friction_n"],
        a["drag_coefficient_upper"],
        a["body_diameter_m"],
    ]
    assert v.design.mass_allowance_kg == cfg["separate_growth_kg"]
    parts = {p.id: p for p in v.parts}
    source_mass = sum(p.mass_kg for p in v.parts)
    bundle_cfg = yaml.safe_load((ROOT / cfg["source_bundle_config"]).read_text())
    removed = {k: parts[k].mass_kg for k in bundle_cfg["remove_source_ids"]}
    assert abs(source_mass - cfg["source_nominal_kg"]) < 1e-12
    assert abs(sum(removed.values()) - cfg["source_bundle_removed_kg"]) < 1e-9
    retained = source_mass - sum(removed.values()) + cfg["separate_growth_kg"]
    paths = [
        CONFIG,
        Path(__file__).resolve(),
        ROOT / cfg["source_spec"],
        ROOT / cfg["source_bundle_config"],
        staged / "src/vehicle/benchmark.py",
        staged / "src/vehicle/schema.py",
        staged / "src/vehicle/motors.py",
        staged / "src/cad/parts.py",
    ]
    paths += [ROOT / m["curve"] for m in cfg["motors"]]
    hashes = {str(p.relative_to(ROOT)): digest(p) for p in paths}
    results, motor_records = [], []
    count = len(cfg["motors"]) * len(cfg["usable_travel_m"])
    assert count <= lim["combinations"]
    assert len(cfg["references"]) <= lim["candidate_probes_per_combination"]

    def guard(case_start):
        if (
            time.process_time() - case_start > lim["individual_case_cpu_s"]
            or time.process_time() - cpu_start > lim["packet_cpu_s"]
            or time.monotonic() - start > lim["packet_wall_s"]
        ):
            raise RuntimeError("Declared comparison resource budget reached; stop")

    for motor in cfg["motors"]:
        assert digest(ROOT / motor["curve"]) == motor["sha256"]
        curve = load_rasp(ROOT / motor["curve"])
        assert abs(curve.loaded_mass_kg - motor["assembled_mass_kg"]) < 1e-12
        assert abs(curve.length_m - motor["length_m"]) < 1e-12
        delta = motor["assembled_mass_kg"] - parts["motor"].mass_kg
        fixed = retained + delta
        motor_records.append(
            {
                **motor,
                "curve_impulse_Ns": curve.total_impulse_ns,
                "curve_terminal_s": curve.burn_time_s,
                "retained_with_motor_and_full_growth_kg": fixed,
                "motor_CG_station_m_assumption": 1.2 - motor["length_m"] / 2,
            }
        )
        for length in cfg["usable_travel_m"]:
            case_start = time.process_time()
            model = v.model_copy(deep=True)
            model.motor.curve = str(ROOT / motor["curve"])
            model.design.rail_length_m = length

            def screen(total, case_start=case_start, model=model):
                guard(case_start)
                return screen_launch(
                    model, dt=a["dt_s"], study_nominal_mass_kg=total - cfg["separate_growth_kg"]
                )

            row = {"motor": motor["id"], "usable_travel_m": length, "roots": {}, "probes": []}
            for label, target in (
                ("formal", cfg["formal_speed_mps"]),
                ("planning", cfg["separate_planning_speed_mps"]),
            ):
                lo, hi = cfg["root_bracket_kg"]
                assert (screen(lo)["rail_exit_speed_mps"] or 0) > target
                assert (screen(hi)["rail_exit_speed_mps"] or 0) < target
                for _ in range(lim["root_bisection_iterations"]):
                    mid = (lo + hi) / 2
                    if (screen(mid)["rail_exit_speed_mps"] or 0) >= target:
                        lo = mid
                    else:
                        hi = mid
                root = lo
                ceiling = min(root, cfg["policy_total_launch_mass_strictly_below_kg"])
                row["roots"][label] = {
                    "target_mps": target,
                    "total_launch_mass_kg": root,
                    "bracket_width_kg": hi - lo,
                    "policy_capped_kg_exclusive_if_1p5": ceiling,
                    "gross_complete_replacement_assembly_budget_kg": ceiling - fixed,
                    "receiver_budget_after_motor_specific_support_reserve_kg": (
                        ceiling - fixed - motor["support_delta_reserve_kg"]
                    ),
                    "factored_severe_mean_opening_N_at_policy_capped_mass": opening(
                        ceiling, 20.4, cfg["recovery"]
                    ),
                    "factored_nominal_mean_opening_N_at_policy_capped_mass": opening(
                        ceiling, 5, cfg["recovery"]
                    ),
                }
            for ref in cfg["references"]:
                total = ref["full_g80_launch_mass_kg"] + delta + motor["support_delta_reserve_kg"]
                row["probes"].append(
                    {
                        "id": ref["id"],
                        "complete_installed": ref["complete_installed"],
                        "total_launch_mass_kg": total,
                        "screen": (screen_result := screen(total)),
                        "formal_margin_mps": screen_result["rail_exit_speed_mps"]
                        - cfg["formal_speed_mps"],
                        "planning_margin_mps": screen_result["rail_exit_speed_mps"]
                        - cfg["separate_planning_speed_mps"],
                        "factored_severe_mean_opening_N": opening(total, 20.4, cfg["recovery"]),
                        "factored_nominal_mean_opening_N": opening(total, 5, cfg["recovery"]),
                    }
                )
            row["cpu_s"] = time.process_time() - case_start
            results.append(row)
    assert hashes == {str(p.relative_to(ROOT)): digest(p) for p in paths}
    record = {
        "status": "completed_conditional_guide_only_not_accepted",
        "flight_ready": False,
        "limits": lim,
        "combination_count": count,
        "inputs_sha256": hashes,
        "source_nominal_kg": source_mass,
        "removed_bundle_kg": removed,
        "retained_with_full_separate_growth_kg": retained,
        "motors": motor_records,
        "results": results,
        "actual_process_cpu_s_including_imports_setup": time.process_time() - cpu_start,
        "actual_wall_s_including_imports_setup": time.monotonic() - start,
        "setup_scope": "existing venv; imports plus YAML/hash validation; no install; no CAD import/solver",
        "model_limits": "fixed full mass, 0.85 thrust, vertical, source drag/friction, no wind load or mass loss; guide only; no structural or launch approval",
    }
    initial = OUT / "initial-record.json"
    if initial.exists():
        prior = json.loads(initial.read_text())
        record["prior_execution"] = {
            "record": str(initial.relative_to(ROOT)),
            "sha256": digest(initial),
            "reason": "one code-only closure-binding and formatting correction; same 12 hypotheses; initial numerical packet succeeded",
            "cpu_s": prior["actual_process_cpu_s_including_imports_setup"],
            "wall_s": prior["actual_wall_s_including_imports_setup"],
        }
        record["cumulative_numerical_process_cpu_s"] = (
            record["actual_process_cpu_s_including_imports_setup"]
            + record["prior_execution"]["cpu_s"]
        )
        record["cumulative_numerical_process_wall_s"] = (
            record["actual_wall_s_including_imports_setup"] + record["prior_execution"]["wall_s"]
        )
    preformat = OUT / "preformat-record.json"
    if preformat.exists():
        prior_format = json.loads(preformat.read_text())
        record["preformat_execution"] = {
            "record": str(preformat.relative_to(ROOT)),
            "sha256": digest(preformat),
            "reason": "formatting only after correcting missing executable wrapper to python -m black; same cases",
        }
        record["cumulative_numerical_process_cpu_s"] += prior_format[
            "actual_process_cpu_s_including_imports_setup"
        ]
        record["cumulative_numerical_process_wall_s"] += prior_format[
            "actual_wall_s_including_imports_setup"
        ]
    (OUT / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: record[k]
                for k in (
                    "status",
                    "combination_count",
                    "actual_process_cpu_s_including_imports_setup",
                    "actual_wall_s_including_imports_setup",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        OUT.mkdir(parents=True, exist_ok=True)
        (OUT / "stopped.json").write_text(
            json.dumps({"status": "stopped_no_retry", "error": repr(exc)}, indent=2) + "\n"
        )
        raise
