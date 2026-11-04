"""One declared mass/balance correction of the same RP1 recovery topology."""

from __future__ import annotations

import hashlib
import json
import os
import resource
import sys
import time
from pathlib import Path

for variable in [
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
]:
    os.environ[variable] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml

from scripts.wo03_f2_c1_load_path import FACTOR, NOSE
from src.vehicle.aero import center_of_pressure
from src.vehicle.benchmark import screen_launch
from src.vehicle.mass import mass_properties
from src.vehicle.reference import compare_rocketpy
from src.vehicle.schema import Vehicle, load_vehicle

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "configs/vehicle/candidates/g80-f2-rp1-wrap.yaml"
INPUT = ROOT / "runs/wo03-f2-recovery-precedent-20261103-v1/record.json"
CANDIDATE = ROOT / "configs/vehicle/candidates/g80-f2-rp1-balanced.yaml"
OUT = ROOT / "runs/wo03-f2-recovery-balanced-20261103-v2"


def main() -> None:
    start = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (6, 6))
    if OUT.exists() or CANDIDATE.exists():
        raise ValueError("One correction only; preserve outputs")
    prior = json.loads(INPUT.read_text())
    if (
        hashlib.sha256(SOURCE.read_bytes()).hexdigest()
        != prior["sources"][str(SOURCE.relative_to(ROOT))]
    ):
        raise ValueError("RP1 input changed")
    before = load_vehicle(SOURCE)
    d = before.model_dump(by_alias=True, exclude_none=True)
    d["parts"][0]["parent"] = None
    d["id"] = "G80-F2-RP1-balanced-v2"
    d["name"] = "RP1 wrap/nylon with redundant ballast removed — unadopted"
    removed = [p for p in d["parts"] if p["id"] in {"nose_ballast", "ballast_capsule"}]
    d["parts"] = [p for p in d["parts"] if p["id"] not in {"nose_ballast", "ballast_capsule"}]
    by = {p["id"]: p for p in d["parts"]}
    cord = by["rp1_kevlar_wrap"]
    cord.update(position_m=0.55, cg_offset_m=0.05, mass_kg=0.015)
    cord["cad"]["parameters"]["raw_length_m"] = 1.8288
    cord["learn"] = (
        "RP1 balanced:6ft raw30327 Kevlar,15g budget from2g assumed per foot+25percent. "
        "Purchase10ft minimum;4ftspare excluded from flight mass. Total loop/termination/tails "
        "reservation.45m and guarded axial route.93m leave.4488m outside body mouth, above "
        "provisional.3m service-junction target. These are unverified manufacturing/route "
        "allocations, not measured knot length or insertion clearance. StowedCG.600m estimated."
    )
    cord["build"]["notes"] = cord["learn"]
    cord["engineering"]["function"] = cord["learn"]
    candidate = Vehicle.model_validate(d)
    CANDIDATE.write_text(yaml.safe_dump(d, sort_keys=False))
    props = mass_properties(candidate)
    cp = center_of_pressure(candidate)
    p = {x.id: x for x in candidate.parts}
    baseline = json.loads(
        (ROOT / "runs/wo03-g80-f2-c1-definition-20261103-v1/record.json").read_text()
    )
    base_cases = [c for c in baseline["cases"] if c["variant"] == "C1_fit_proposal"]
    limits = json.loads((ROOT / "runs/wo03-g80-f2-selected-20261103-v2/record.json").read_text())[
        "guide_total_mass_limits_kg"
    ]["1.5"]
    soft = {
        "parachute",
        "shock_cord",
        "recovery_connectors",
        "recovery_protection",
        "rp1_kevlar_wrap",
    }
    body_mass = props.mass_kg - sum(
        x.resolved_mass_kg for x in candidate.parts if x.id in NOSE | soft
    )
    rows = []
    for name, extra, probe in [("nominal", 0.0, 0.0), ("adverse", 0.02, 0.0128)]:
        total = props.mass_kg + 0.05 + extra
        moment = (
            props.mass_kg * props.cg_m + (0.05 + extra) * 1.25 + p["motor"].resolved_mass_kg * probe
        )
        cg = moment / total
        guides = {}
        for guide in [1.5, 1.8]:
            q = candidate.model_copy(deep=True)
            q.design.rail_length_m = guide
            guides[str(guide)] = screen_launch(q, study_nominal_mass_kg=total - 0.05)[
                "rail_exit_speed_mps"
            ]
        dry = total - candidate.motor.propellant_mass_kg
        dry_cg = (moment - candidate.motor.propellant_mass_kg * p["motor"].cg_station_m) / dry
        # Bounding stowage illustration only; same mass/guide results are reused.
        aft_cord_moment = 0.015 * (0.85 - 0.60) + 0.055 * (0.40 - 0.34)
        stow_cg = cg + aft_cord_moment / total
        rows.append(
            {
                "case": name,
                "total_mass_kg": total,
                "growth_kg": 0.05,
                "extra_aft_kg": extra,
                "motor_cg_probe_m": probe,
                "cg_m": cg,
                "cp_m": cp,
                "margin_cal": (cp - cg) / 0.066802,
                "burnout_mass_kg": dry,
                "burnout_cg_m": dry_cg,
                "burnout_margin_cal": (cp - dry_cg) / 0.066802,
                "guide_mps": guides,
                "formal_mass_headroom_g": (limits["15.0"] - total) * 1000,
                "planning_mass_headroom_g": (limits["15.5"] - total) * 1000,
                "required_whole_mean_proxy_N": FACTOR * total,
                "required_body_proxy_N": FACTOR * (body_mass + 0.05 + extra),
                "aft_stowage_sensitivity": {
                    "kevlar_cg_m": 0.85,
                    "nylon_cg_m": 0.40,
                    "cg_m": stow_cg,
                    "margin_cal": (cp - stow_cg) / 0.066802,
                    "verified": False,
                },
            }
        )
    ledger = [
        {
            "id": x.id,
            "mass_g": x.resolved_mass_kg * 1000,
            "cg_mm": x.cg_station_m * 1000,
            "cost_usd": x.build.cost_usd,
            "basis": x.learn,
        }
        for x in candidate.parts
    ]
    r = {
        "identity": candidate.id,
        "adopted": False,
        "status": "one topology correction; conditional formal pass, planning and installed acceptance open",
        "sources": {
            str(SOURCE.relative_to(ROOT)): hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            str(INPUT.relative_to(ROOT)): hashlib.sha256(INPUT.read_bytes()).hexdigest(),
            str(CANDIDATE.relative_to(ROOT)): hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        },
        "cases": rows,
        "baseline_cases": base_cases,
        "previous_rp1_cases": prior["cases"],
        "ledger": ledger,
        "delta_mass_g": (props.mass_kg - (base_cases[0]["total_mass_kg"] - 0.05)) * 1000,
        "removal_credit_g": prior["removal_credit_g"]
        + sum(x["mass_kg"] for x in removed) * 1000,
        "addition_mass_g": prior["addition_mass_g"] - 5,
        "correction_removals": {
            "ballast_and_sole_carrier_g": sum(x["mass_kg"] for x in removed) * 1000,
            "shorter_cord_g": 5,
            "nose_service_hardware_retained_g": p["nose_service_hardware"].resolved_mass_kg * 1000,
        },
        "functional_replacement": {
            "balance": "Forward harness mass retains >=1cal under loaded/burnout/adverse/statedstowage bounds; ballast-only capsule removed, nose carrier/service retained",
            "leader_length": "6ft raw less.45m loop/ends and.93mroute leaves.4488m; provisional service target.3m. Actual end/path lengths unknown",
        },
        "maximum_main_cord_mass_g_adverse_formal": 55 + rows[1]["formal_mass_headroom_g"],
        "maximum_main_cord_mass_g_adverse_planning": 55 + rows[1]["planning_mass_headroom_g"],
        "complete_cost_estimate_usd": sum(x.build.cost_usd for x in candidate.parts),
        "physical_full_inertia": None,
        "label_only_strength_N": prior["label_only_strength_N"],
        "static_rocketpy": compare_rocketpy(candidate),
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "resources": {
            "cpu_limit_s": 6,
            "wall_limit_s": 10,
            "library_threads_requested": 1,
            "cpu_s": time.process_time(),
            "main_wall_s": time.monotonic() - start,
            "peak_rss_platform_units": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "cpu_affinity_verified": False,
        },
    }
    OUT.mkdir()
    (OUT / "record.json").write_text(json.dumps(r, indent=2) + "\n")
    (OUT / "executed-producer.py").write_bytes(Path(__file__).read_bytes())
    (OUT / "specification.yaml").write_bytes(CANDIDATE.read_bytes())
    print(
        json.dumps(
            {
                k: r[k]
                for k in ["identity", "delta_mass_g", "correction_removals", "cases", "resources"]
            }
        )
    )


if __name__ == "__main__":
    main()
