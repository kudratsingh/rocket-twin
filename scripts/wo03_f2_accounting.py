"""One bounded F2 accounting and free-body screen; no engineering acceptance."""

from __future__ import annotations

import hashlib
import json
import math
import resource
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml

from src.vehicle.benchmark import screen_launch
from src.vehicle.schema import load_vehicle

F1 = ROOT / "runs/wo03-g80-f1-preflight-20261102-v2/record.json"
F2 = ROOT / "runs/wo03-g80-f2-selected-20261103-v2/record.json"
SPEC = ROOT / "configs/vehicle/candidates/g80-f2-ballast.yaml"
OUT = ROOT / "runs/wo03-g80-f2-accounting-20261103-v1/record.json"

NOSE = {
    "nose",
    "nose_anchor_plate",
    "nose_recovery_eye",
    "flight_computer",
    "imu",
    "baro",
    "high_g_accel",
    "micro_sd",
    "battery",
    "independent_recovery",
    "recovery_battery",
    "avionics_sled",
    "logger_power_switch",
    "logger_regulator",
    "recovery_carrier",
    "electrical_harness",
    "recovery_harness_wiring",
    "recovery_output_mount",
    "nose_service_hardware",
    "ballast_capsule",
    "nose_ballast",
}
SOFT = {"parachute", "shock_cord", "recovery_connectors", "recovery_protection", "heat_leader"}
ZERO_BUNDLES = {
    "fin_tabs": "same purchased birch sheet as fin_set",
    "forward_ring": "same purchased birch sheet as fin_set",
    "aft_ring": "same purchased birch sheet as fin_set",
    "nose_anchor_plate": "same purchased birch sheet as fin_set",
    "root_gussets": "same purchased birch sheet as fin_set",
    "upper_body": "second LOC body-tube blank charged to body",
    "body_splice": "second LOC body-tube blank offcut charged to body",
    "splice_seam_patch": "second LOC body-tube blank offcut charged to body",
}
UNCERTAIN_CUT_IDS = {
    "body_recovery_eye",  # physical envelope straddles plane
    "mount_external_shield",  # reserved distributed layer, unfinished ends
    "finish",  # distributed budget with display box only
    "service_allowance",  # distributed budget with display box only
    "ring_bonds",  # process allocation lacks installed spatial split
}
G = 9.80665
S = 0.3
DF = 3.0
CUT_M = 1.075


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def force_factor(speed: float) -> float:
    return DF * (speed * speed / (2 * S) + G)


def part_span(part: dict) -> tuple[float, float] | None:
    geom = part.get("geometry") or {}
    length = geom.get("length_m")
    if length is None:
        box = geom.get("bbox_m")
        length = box[0] if box else None
    if length is None:
        return None
    front = part["position_m"]
    return front, front + length


def cut_accounting(source: dict, by_id: dict[str, dict], speed: float, extra_aft_kg: float) -> dict:
    """Near-forward-ring paper cut, with uniform tubes and unknown budget ranges."""
    known = []
    uncertain = []
    fore = []
    for item in source["parts"]:
        pid = item["id"]
        if pid in NOSE or pid in SOFT:
            continue
        mass = by_id[pid]["mass_kg"]
        span = part_span(item)
        if pid in {"body", "motor_tube"}:
            assert span is not None and span[0] < CUT_M < span[1]
            fraction = (span[1] - CUT_M) / (span[1] - span[0])
            known.append({"id": pid, "mass_kg": mass * fraction, "basis": "uniform tube portion"})
            fore.append(
                {"id": pid, "mass_kg": mass * (1 - fraction), "basis": "uniform tube portion"}
            )
        elif pid in UNCERTAIN_CUT_IDS or span is None or (span[0] < CUT_M < span[1]):
            uncertain.append({"id": pid, "mass_range_kg": [0.0, mass], "span_m": span})
        elif span[0] >= CUT_M:
            known.append({"id": pid, "mass_kg": mass, "basis": "source envelope wholly aft"})
        else:
            fore.append({"id": pid, "mass_kg": mass, "basis": "source envelope wholly fore"})
    full_growth = 0.05 + extra_aft_kg
    lower = sum(x["mass_kg"] for x in known) + full_growth
    upper = lower + sum(x["mass_range_kg"][1] for x in uncertain)
    ro, ri = 0.066802 / 2, 0.065024 / 2
    area = math.pi * (ro * ro - ri * ri)
    inertia = math.pi * (ro**4 - ri**4) / 4
    factor = force_factor(speed)
    demands = []
    for label, m in [("known_aft_lower", lower), ("all_uncertain_aft_upper", upper)]:
        f = factor * m
        moment_70_30 = 0.4 * f * 0.023
        moment_single = f * 0.023
        demands.append(
            {
                "id": label,
                "mass_kg": m,
                "axial_force_N": f,
                "paper_axial_stress_Pa": f / area,
                "70_30_eccentric_moment_Nm": moment_70_30,
                "70_30_bending_stress_Pa": moment_70_30 * ro / inertia,
                "single_eye_moment_Nm": moment_single,
                "single_eye_bending_stress_Pa": moment_single * ro / inertia,
                "axial_plus_70_30_proxy_Pa": f / area + moment_70_30 * ro / inertia,
                "axial_plus_single_eye_proxy_Pa": f / area + moment_single * ro / inertia,
            }
        )
    return {
        "cut_z_m": CUT_M,
        "paper_outer_diameter_m": 2 * ro,
        "paper_inner_diameter_m": 2 * ri,
        "paper_area_m2": area,
        "paper_second_moment_m4": inertia,
        "estimated_paper_axial_screen_Pa": 2e6,
        "known_aft_rows": known,
        "known_fore_rows": fore,
        "unknown_spatial_rows": uncertain,
        "full_growth_and_extra_aft_kg": full_growth,
        "demand_bounds": demands,
        "scope": "Ideal serial axial/eccentric beam proxies; actual ring-to-paper load split, local hole/peel/buckling and hot capacity unknown",
    }


def guide_root(vehicle, mass_kg: float, target_mps: float) -> dict:
    low, high = 0.25, 1.971
    calls = 0

    def speed(length: float) -> float:
        nonlocal calls
        vv = vehicle.model_copy(deep=True)
        vv.design.rail_length_m = length
        calls += 1
        return screen_launch(vv, study_nominal_mass_kg=mass_kg - 0.05)["rail_exit_speed_mps"]

    low_speed, high_speed = speed(low), speed(high)
    if not (low_speed < target_mps <= high_speed):
        raise ValueError("target not bracketed by declared 0.25–1.971 m guide range")
    for _ in range(24):
        middle = (low + high) / 2
        if speed(middle) >= target_mps:
            high = middle
        else:
            low = middle
    return {
        "target_mps": target_mps,
        "lower_usable_m": low,
        "upper_usable_m": high,
        "lower_speed_mps": speed(low),
        "upper_speed_mps": speed(high),
        "screen_calls": calls,
        "source": "src.vehicle.benchmark.screen_launch; fixed selected adverse loaded mass and full 50 g already included",
    }


def compute() -> dict:
    f1 = json.loads(F1.read_text())
    f2 = json.loads(F2.read_text())
    spec = yaml.safe_load(SPEC.read_text())
    assert sha(SPEC) == f2["spec_sha256"]
    old = {x["id"]: x for x in f1["parts"]}
    new = {x["id"]: x for x in f2["parts"]}
    assert len(old) == 42 and len(new) == 50
    assert set(new) == {x["id"] for x in spec["parts"]}
    assert not (NOSE & SOFT) and (NOSE | SOFT) <= set(new)
    body = set(new) - NOSE - SOFT
    groups = {}
    for label, ids in [("nose_retained", NOSE), ("soft_recovery", SOFT), ("body_retained", body)]:
        groups[label] = {
            "ids": sorted(ids),
            "row_count": len(ids),
            "parts_mass_kg": sum(new[i]["mass_kg"] for i in ids),
            "point_first_moment_kg_m": sum(new[i]["mass_kg"] * new[i]["cg_m"] for i in ids),
        }
    assert sum(x["parts_mass_kg"] for x in groups.values()) == sum(
        x["mass_kg"] for x in new.values()
    ) or math.isclose(
        sum(x["parts_mass_kg"] for x in groups.values()),
        f2["nominal_parts_mass_kg"],
        abs_tol=1e-12,
    )
    deltas = []
    for pid in sorted(set(old) | set(new)):
        a, b = old.get(pid), new.get(pid)
        dm = (b["mass_kg"] if b else 0) - (a["mass_kg"] if a else 0)
        dq = (b["mass_kg"] * b["cg_m"] if b else 0) - (a["mass_kg"] * a["cg_m"] if a else 0)
        dc = (b["cost_usd"] if b else 0) - (a["cost_usd"] if a else 0)
        if abs(dm) > 1e-12 or abs(dq) > 1e-12 or abs(dc) > 1e-12:
            deltas.append(
                {
                    "id": pid,
                    "action": "add" if not a else "remove" if not b else "change_or_relocate",
                    "F1_mass_kg": a["mass_kg"] if a else 0,
                    "F2_mass_kg": b["mass_kg"] if b else 0,
                    "signed_mass_delta_kg": dm,
                    "signed_point_moment_delta_kg_m": dq,
                    "F1_cost_usd": a["cost_usd"] if a else 0,
                    "F2_cost_usd": b["cost_usd"] if b else 0,
                    "signed_cost_delta_usd": dc,
                }
            )
    assert math.isclose(
        sum(x["signed_mass_delta_kg"] for x in deltas),
        f2["nominal_parts_mass_kg"] - f1["nominal_parts_mass_kg"],
        abs_tol=1e-12,
    )
    assert math.isclose(
        sum(x["signed_cost_delta_usd"] for x in deltas),
        f2["estimated_consumed_parts_cost_usd"] - f1["estimated_consumed_parts_cost_usd"],
        abs_tol=1e-9,
    )
    zero = [
        {"id": i, "mass_kg": x["mass_kg"], "basis": ZERO_BUNDLES[i], "owner_stock_evidenced": False}
        for i, x in sorted(new.items())
        if x["cost_usd"] == 0
    ]
    assert {x["id"] for x in zero} == set(ZERO_BUNDLES)
    cases = []
    for case in f2["cases"]:
        extra = case["additional_aft_kg"]
        masses = {
            "nose_retained": groups["nose_retained"]["parts_mass_kg"],
            "soft_recovery": groups["soft_recovery"]["parts_mass_kg"],
            "body_retained": groups["body_retained"]["parts_mass_kg"] + 0.05 + extra,
        }
        assert math.isclose(sum(masses.values()), case["mass_kg"], abs_tol=1e-12)
        demands = {k: force_factor(20.4) * m for k, m in masses.items()}
        whole = force_factor(20.4) * case["mass_kg"]
        assert math.isclose(sum(demands.values()), whole, abs_tol=1e-9)
        body_force = demands["body_retained"]
        eye = {
            "two_eye_radius_m": 0.023,
            "body_branch_70_30_N": [0.7 * body_force, 0.3 * body_force],
            "body_branch_70_30_eccentric_moment_Nm": 0.4 * body_force * 0.023,
            "body_branch_single_eye_N": body_force,
            "body_branch_single_eye_moment_Nm": body_force * 0.023,
            "whole_force_single_eye_sensitivity_N": whole,
            "whole_force_single_eye_moment_Nm": whole * 0.023,
            "nose_eye_radius_m": 0.0265,
            "nose_branch_single_eye_moment_Nm": demands["nose_retained"] * 0.0265,
        }
        cases.append(
            {
                "id": case["id"],
                "mass_kg": case["mass_kg"],
                "growth_kg": 0.05,
                "additional_aft_kg": extra,
                "severe_factor_N_per_kg": force_factor(20.4),
                "group_masses_kg": masses,
                "equivalent_group_inertial_demands_N": demands,
                "whole_equivalent_mean_DF3_N": whole,
                "eye_sensitivities": eye,
                "forward_ring_paper_cut": cut_accounting(spec, new, 20.4, extra),
            }
        )
    ballast_mass = new["ballast_capsule"]["mass_kg"] + new["nose_ballast"]["mass_kg"]
    vehicle = load_vehicle(SPEC)
    adverse = next(x for x in f2["cases"] if x["additional_aft_kg"] > 0)
    guide = [guide_root(vehicle, adverse["mass_kg"], speed) for speed in (15.0, 15.5)]
    return {
        "id": "G80_F2_coupled_accounting_20261103_v1",
        "status": "arithmetic/source-linked screen only; no installed or flight acceptance",
        "source_sha256": {"F1_record": sha(F1), "F2_record": sha(F2), "F2_spec": sha(SPEC)},
        "source_identity": {"F1": f1["identity"], "F2": f2["identity"]},
        "rows": {"F1": len(old), "F2": len(new), "signed_deltas": len(deltas)},
        "mass_kg": {
            "F1_parts": f1["nominal_parts_mass_kg"],
            "F2_parts": f2["nominal_parts_mass_kg"],
            "signed_delta": sum(x["signed_mass_delta_kg"] for x in deltas),
        },
        "cost_usd": {
            "F1_estimate": f1["estimated_consumed_parts_cost_usd"],
            "F2_estimate": f2["estimated_consumed_parts_cost_usd"],
            "signed_delta": sum(x["signed_cost_delta_usd"] for x in deltas),
            "zero_price_rows": zero,
            "owner_stock_evidence": "none in inspected F2 supplier/selection sources",
        },
        "signed_part_deltas": deltas,
        "physical_retained_groups": groups,
        "membership_warning": "source parent field and point CG do not prove physical retention or force transfer; nose carrier/output well extend into body and need positive capture and service proof",
        "recovery_cases": cases,
        "ballast_capture": {
            "nose_ballast_kg": new["nose_ballast"]["mass_kg"],
            "capsule_and_fastener_budget_kg": new["ballast_capsule"]["mass_kg"],
            "combined_kg": ballast_mass,
            "severe_common_acceleration_DF3_N": force_factor(20.4) * ballast_mass,
            "required_evidence": [
                "M5 washer/bolt material and nonstructural metal legality",
                "retained capsule fastener/ASA/plywood bearing and pull-through",
                "tolerance and positive anti-loosening",
                "nose separation/ejection/shock capture",
                "cold/hot/wet and repeated handling",
                "actual finished washer/capsule mass",
            ],
        },
        "adverse_required_usable_guide": guide,
        "guide_baseline_m": 1.5,
        "limitations": [
            "20.4 m/s and 0.3 m are prescribed historical probes, not F2 telemetry or measured stroke",
            "DF3 applied once; common-acceleration branch demands are mass-allocation proxies, not measured simultaneous tensions or inflation/snatch peaks",
            "paper 2 MPa is an estimated scalar screen, not installed hot/wet/bending/peel capacity",
            "F2 motor/retainer, eyes, ballast capture, full spatial fields and owner stock remain unverified",
        ],
    }


def main() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    signal.alarm(20)
    start = time.monotonic()
    result = compute()
    result["resources"] = {
        "declared_cpu_count": 1,
        "cpu_cap_s": 10,
        "wall_cap_s": 20,
        "wall_used_s": time.monotonic() - start,
    }
    result["script_sha256"] = sha(Path(__file__))
    OUT.parent.mkdir(parents=True, exist_ok=False)
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "id": result["id"],
                "resources": result["resources"],
                "mass_kg": result["mass_kg"],
                "cost_usd": {k: v for k, v in result["cost_usd"].items() if k != "zero_price_rows"},
                "guide": result["adverse_required_usable_guide"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
