"""Calculate complete recovery budget from the unchanged G12 departure screen.

Every dedicated part is counted once; existing shared load-path structure is
reported separately and stays in fixed vehicle mass. New reinforcement must be
added, not hidden by relabeling an existing budget. The current guide is a design
assumption, not confirmed launch equipment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cad.parts import local_shape, properties
from src.vehicle.benchmark import screen_launch
from src.vehicle.mass import mass_properties
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import CADMass, Vehicle, load_vehicle, vehicle_input_paths


def budget(vehicle: Vehicle, dedicated: list[str], steps: list[float]) -> dict[str, Any]:
    parts = {part.id: part for part in vehicle.parts}
    if len(set(dedicated)) != len(dedicated):
        raise ValueError("Duplicate dedicated part identity")
    dedicated_mass = sum(parts[name].resolved_mass_kg for name in dedicated)
    total = mass_properties(vehicle).mass_kg
    assert vehicle.design
    # Vary a dedicated mass without changing the growth reserve or any launch
    # condition. The guide solver depends on total mass, not its chosen CG.
    limits = []
    for dt in steps:
        lo, hi = 0.5 * total, 1.2
        for _ in range(40):
            trial = (lo + hi) / 2
            result = screen_launch(vehicle, dt, study_nominal_mass_kg=trial)
            speed = result["rail_exit_speed_mps"]
            if speed is not None and speed >= vehicle.design.minimum_rail_exit_mps:
                lo = trial
            else:
                hi = trial
        limits.append(
            {
                "dt_s": dt,
                "maximum_nominal_vehicle_kg": lo,
                "maximum_total_recovery_kg": dedicated_mass + lo - total,
            }
        )
    maximum = min(item["maximum_total_recovery_kg"] for item in limits)
    return {
        "nominal_vehicle_mass_kg": total,
        "dedicated_recovery_mass_kg": dedicated_mass,
        "fixed_nonrecovery_mass_kg": total - dedicated_mass,
        "growth_allowance_kg": vehicle.design.mass_allowance_kg,
        "guide_length_m": vehicle.design.rail_length_m,
        "minimum_departure_mps": vehicle.design.minimum_rail_exit_mps,
        "current_screen": screen_launch(vehicle),
        "limits_by_timestep": limits,
        "maximum_total_recovery_kg": maximum,
        "maximum_increment_kg": maximum - dedicated_mass,
        "numerical_mass_limit_spread_kg": max(i["maximum_total_recovery_kg"] for i in limits)
        - maximum,
        "guide_availability_confirmed": False,
        "flight_ready": False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-recovery-mass-budget.yaml")
    )
    p.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    args = p.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    inputs = {args.config, Path(__file__), *vehicle_input_paths(cfg["vehicle"])}
    inputs.update(Path("src/vehicle").glob("*.py"))
    inputs.update(Path("src/cad").glob("*.py"))

    def hashes() -> dict[str, str]:
        return {
            str(q.resolve().relative_to(Path.cwd())): hashlib.sha256(q.read_bytes()).hexdigest()
            for q in sorted(inputs)
        }

    before = hashes()
    v = load_vehicle(cfg["vehicle"])
    ids = cfg["dedicated_recovery_part_ids"]
    if set(ids) & set(cfg["shared_loadpath_part_ids"]):
        raise ValueError("Shared structure double counted")
    rows = [{"candidate": "active", "budget": budget(v, ids, cfg["numerical_timestep_s"])}]
    battery_cfg = cfg["main_battery_trade"]
    candidate = v.model_copy(deep=True)
    battery = next(part for part in candidate.parts if part.id == "battery")
    battery.geometry = {"bbox_m": battery_cfg["envelope_m"]}
    battery.mass_kg = battery_cfg["supplied_mass_kg"]
    battery.cad_mass = None
    battery.cg_offset_m = battery_cfg["envelope_m"][0] / 2
    assert battery.electrical
    battery.electrical.capacity_mah = battery_cfg["capacity_mah"]
    battery.electrical.max_discharge_a = (
        battery_cfg["capacity_mah"] / 1000 * battery_cfg["stated_discharge_c"]
    )
    rows.append(
        {
            "candidate": "main-pack-only",
            "budget": budget(candidate, ids, cfg["numerical_timestep_s"]),
        }
    )
    fin = next(part for part in candidate.parts if part.id == "fin_set")
    fin.geometry["thickness_m"] = cfg["fin_trade"]["nominal_thickness_m"]
    fin.cad_mass = None
    props = properties(fin, local_shape(fin))
    fin.cad_mass = CADMass.model_validate(props)
    fin.mass_kg = props["volume_m3"] * DENSITY_KG_M3[fin.material]
    rows.append(
        {
            "candidate": "main-pack-and-6mm-trainer-fins",
            "budget": budget(candidate, ids, cfg["numerical_timestep_s"]),
            "fin_shape_sha256": props["shape_sha256"],
            "fin_new_mass_kg": fin.resolved_mass_kg,
            "fin_strength_flutter_validated": False,
        }
    )
    reinforced = cfg["reinforced_fin_trade"]
    fin.geometry["thickness_m"] = reinforced["nominal_thickness_m"]
    assert fin.cad
    fin.cad.parameters["root_gusset_span_mm"] = reinforced["root_gusset_span_mm"]
    fin.cad_mass = None
    props = properties(fin, local_shape(fin))
    fin.cad_mass = CADMass.model_validate(props)
    fin.mass_kg = props["volume_m3"] * DENSITY_KG_M3[fin.material]
    rows.append(
        {
            "candidate": "main-pack-and-5mm-trainer-fins-with-20mm-gussets",
            "budget": budget(candidate, ids, cfg["numerical_timestep_s"]),
            "fin_shape_sha256": props["shape_sha256"],
            "fin_new_mass_kg": fin.resolved_mass_kg,
            "fin_strength_flutter_validated": False,
        }
    )
    duty = battery_cfg["energy_budget"]
    load_j = duty["main_bus_v"] * sum(
        duty[f"{phase}_s"] * duty[f"{phase}_current_a"]
        for phase in ["prearm", "flight_peak", "postflight"]
    )
    available_j = (
        battery_cfg["nominal_voltage_v"]
        * battery_cfg["capacity_mah"]
        / 1000
        * 3600
        * duty["minimum_capacity_fraction"]
        * duty["conversion_efficiency"]
    )
    peak_input_a = (
        duty["main_bus_v"]
        * duty["flight_peak_current_a"]
        / (duty["minimum_pack_v"] * duty["conversion_efficiency"])
    )
    run = datetime.now(UTC).strftime("wo03-recovery-budget-%Y%m%dT%H%M%S%fZ")
    record = Path("runs") / run / "record.json"
    record.parent.mkdir(parents=True)
    parts = {part.id: part for part in v.parts}
    payload = {
        "run_id": run,
        "source_sha256": before,
        "inputs_unchanged": before == hashes(),
        "dedicated_parts": [
            {"part_id": name, "mass_kg": parts[name].resolved_mass_kg} for name in ids
        ],
        "shared_structure_already_in_fixed_mass": [
            {"part_id": name, "mass_kg": parts[name].resolved_mass_kg}
            for name in cfg["shared_loadpath_part_ids"]
        ],
        "candidates": rows,
        "battery_duty_screen": {
            "required_output_energy_j": load_j,
            "available_output_energy_j": available_j,
            "energy_margin": available_j / load_j - 1,
            "peak_pack_current_a": peak_input_a,
            "supplier_stated_continuous_a": battery.electrical.max_discharge_a,
            "basis": duty["note"],
            "bench_qualified": False,
        },
        "active_adoption": False,
        "expanded_wo03_passed": False,
        "flight_ready": False,
    }
    record.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    print(record)
    for row in rows:
        print(
            row["candidate"],
            row["budget"]["maximum_total_recovery_kg"],
            row["budget"]["maximum_increment_kg"],
        )
    print(payload["battery_duty_screen"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
