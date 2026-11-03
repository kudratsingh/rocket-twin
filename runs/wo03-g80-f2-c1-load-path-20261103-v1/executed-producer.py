"""One coupled F2-C1 connection/fit screen; no field or physical qualification.

Recovery mean proxy: energy m*v^2/2 over stroke, plus weight, DF3 once.
Separate two-free-body snatch comparison uses reduced mass from relative KE;
it does not replace the required whole-case screen or establish a peak load.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import resource
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml

from src.vehicle.aero import center_of_pressure
from src.vehicle.benchmark import screen_launch
from src.vehicle.mass import mass_properties
from src.vehicle.reference import compare_rocketpy
from src.vehicle.schema import Vehicle, load_vehicle

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "configs/vehicle/candidates/g80-f2-ballast.yaml"
CANDIDATE = ROOT / "configs/vehicle/candidates/g80-f2-c1-fit-proposal.yaml"
OUT = ROOT / "runs/wo03-g80-f2-c1-load-path-20261103-v1"
EXPECTED = "7b188941de7fd4061800936c957b962d2165a5965c5cd9e46476d86242ed5a78"
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
    "c1_nose_bond_fill",
}
SOFT = {"parachute", "shock_cord", "recovery_connectors", "recovery_protection", "heat_leader"}
FACTOR = 3 * (20.4**2 / (2 * 0.3) + 9.80665)


def clearance(label, minimum, nominal, maximum, basis):
    return {
        "id": label,
        "minimum_mm": minimum,
        "nominal_mm": nominal,
        "maximum_mm": maximum,
        "criterion_mm": 0.1,
        "conditional_screen_pass": minimum >= 0.1 - 1e-12,
        "basis": basis,
        "measured": False,
        "environmental_bounds_verified": False,
    }


def main():
    start = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError("frozen F2 changed")
    if OUT.exists() or CANDIDATE.exists():
        raise ValueError("preserve frozen result/proposal; no overwrite")
    v = load_vehicle(SOURCE)
    d = v.model_dump(by_alias=True, exclude_none=True)
    d["parts"][0]["parent"] = None
    d["id"] = "G80-F2-C1-fit-proposal-v1"
    d["name"] = "G80-F2-C1 fit proposal — connection strength/adoption held"
    by = {p["id"]: p for p in d["parts"]}
    for pid in ["forward_ring", "aft_ring"]:
        p = by[pid]
        p["geometry"].update(radius_m=0.0322, inner_radius_m=0.01595)
        p["engineering"]["tolerances_mm"].update(outer_diameter=0.05, bore_diameter=0.05)
        p["build"][
            "notes"
        ] += " C1 PROPOSAL:OD64.4±.05,bore31.90±.05mm; original conservative mass allocation retained without removal credit; installed strength/adoption held."
        p["cad"]["mass_basis"] = "supplied_or_estimated"
    by["forward_ring"][
        "learn"
    ] = "Two6mm plywood plies plus0.2mm adhesive make12.2mm total. C1 proposed blindnotches6.6mmwide/7.4mmdeep; four-point-eight-mm frontweb. Recovery pulls the ring noseward: the aft tab does not bear directly on this web in that direction; side/floor bonds must transfer tensile/shear loads. Installed capacity remains unresolved."
    by["nose_anchor_plate"]["geometry"]["radius_m"] = 0.0305
    by["nose_anchor_plate"]["engineering"]["tolerances_mm"]["outer_diameter"] = 0.05
    by["nose_anchor_plate"]["build"][
        "notes"
    ] += " C1 proposed61.0±.05mmOD; original mass retained until strength verification."
    tab = by["fin_tabs"]
    tab["position_m"] = 1.0802
    tab["geometry"]["bbox_m"] = [0.1094, 0.017451, 0.006]
    tab["engineering"]["tolerances_mm"].update(inner_flat=0.025, front_axial=0.05, aft_axial=0.05)
    tab["learn"] = (
        "C1 fit proposal only:innerflat15.950±.025mm;front1080.20±.05/end1189.60±.05mm. Existing mass allocation retained; no source of positive axial recovery capture is introduced by a blind notch. Adhesive tension/side shear and installed flexibility remain open."
    )
    # New positive adhesive quantities only; no removed material/function credit.
    outer_forward = math.pi * (0.0323**2 - 0.0322**2) * 0.0122 - 3 * 0.0065 * 0.0074 * 0.0001
    outer_aft = math.pi * (0.0323**2 - 0.0322**2) * 0.006
    inner = math.pi * (0.01595**2 - 0.0158845**2) * (0.0122 + 0.006) - 3 * 0.0065 * 0.0074 * (
        0.01595 - 0.0158845
    )
    sides = 3 * 0.0001 * 0.017451 * 0.0074
    ends = 2 * 3 * 0.0002 * 0.017451 * 0.006
    flat = 3 * (0.01595 - 0.0158845) * 0.1094 * 0.006
    nose = math.pi * (0.0306**2 - 0.0305**2) * 0.0122
    additions = []
    for pid, z, volume, role in [
        (
            "c1_forward_root_bond_fill",
            1.075,
            outer_forward + inner + sides + ends + flat,
            "matched forward/root gaps",
        ),
        ("c1_aft_bond_fill", 1.19, outer_aft, "aft perimeter gap"),
        ("c1_nose_bond_fill", 0.178, nose, "nose perimeter gap"),
    ]:
        p = copy.deepcopy(by["service_allowance"])
        p.update(
            id=pid,
            parent="nose" if pid == "c1_nose_bond_fill" else "body",
            position_m=z,
            geometry={"bbox_m": [0.0122, 0.004, 0.004]},
            cg_offset_m=0.0061,
            material="epoxy",
            mass_kg=volume * 1200,
            learn="Additional filled epoxy volume for "
            + role
            + ";1200kg/m3 estimated, no parallel air path. No credit for removed original wood/bond material. Thin-film approximation/process excess uncertainty remains.",
            estimate=True,
        )
        p["engineering"]["function"] = p["learn"]
        p["build"]["method"] = "bonded"
        p["build"]["notes"] = p["learn"]
        p["build"]["cost_usd"] = round(volume * 1200 * 1000 * 0.2, 3)
        p["cad"]["role"] = "distributed_budget"
        p["cad"]["mass_basis"] = "supplied_or_estimated"
        additions.append(p)
    d["parts"] += additions
    candidate = Vehicle.model_validate(d)
    CANDIDATE.write_text(yaml.safe_dump(d, sort_keys=False))
    OUT.mkdir()
    rows = []
    for vv, label in [(v, "frozen_F2"), (candidate, "C1_fit_proposal")]:
        props = mass_properties(vv)
        cp = center_of_pressure(vv)
        byp = {p.id: p for p in vv.parts}
        baseline = json.loads(
            (ROOT / "runs/wo03-g80-f2-selected-20261103-v2/record.json").read_text()
        )
        limits = baseline["guide_total_mass_limits_kg"]["1.5"]
        groups = {
            "nose": sum(p.resolved_mass_kg for p in vv.parts if p.id in NOSE),
            "soft": sum(p.resolved_mass_kg for p in vv.parts if p.id in SOFT),
        }
        groups["body"] = props.mass_kg - groups["nose"] - groups["soft"]
        for name, extra, probe in [("nominal", 0, 0), ("adverse", 0.02, 0.0128)]:
            total = props.mass_kg + 0.05 + extra
            cg = (
                props.mass_kg * props.cg_m
                + (0.05 + extra) * vv.airframe["length_m"]
                + byp["motor"].resolved_mass_kg * probe
            ) / total
            guides = {}
            for guide in [1.5, 1.8]:
                q = vv.model_copy(deep=True)
                q.design.rail_length_m = guide
                guides[str(guide)] = screen_launch(q, study_nominal_mass_kg=total - 0.05)[
                    "rail_exit_speed_mps"
                ]
            nose_mass = groups["nose"]
            body_mass = groups["body"] + 0.05 + extra
            mu = nose_mass * body_mass / (nose_mass + body_mass)
            rows.append(
                {
                    "identity": vv.id,
                    "variant": label,
                    "case": name,
                    "total_mass_kg": total,
                    "parts_mass_kg": props.mass_kg,
                    "growth_kg": 0.05,
                    "extra_aft_kg": extra,
                    "motor_cg_probe_m": probe,
                    "cg_m": cg,
                    "cp_m": cp,
                    "margin_cal": (cp - cg) / vv.airframe["body_diameter_m"],
                    "guide_mps": guides,
                    "formal_mass_headroom_g": (limits["15.0"] - total) * 1000,
                    "planning_mass_headroom_g": (limits["15.5"] - total) * 1000,
                    "required_whole_mean_proxy_N": FACTOR * total,
                    "common_acceleration_partition_N": {
                        "nose": FACTOR * nose_mass,
                        "soft": FACTOR * groups["soft"],
                        "body": FACTOR * body_mass,
                    },
                    "two_free_body_comparison": {
                        "nose_mass_kg": nose_mass,
                        "body_mass_kg": body_mass,
                        "reduced_mass_kg": mu,
                        "relative_speed_hypothesis_mps": 20.4,
                        "stroke_hypothesis_m": 0.3,
                        "factored_mean_tension_N": 3 * mu * 20.4**2 / (2 * 0.3),
                        "scope": "derived relative-motion energy comparison, not replacement requirement or peak; soft goods omitted/engagement unknown",
                    },
                    "point_drag_model_full_canopy_comparison_N": (
                        3
                        * 0.5
                        * 1.225
                        * 20.4**2
                        * math.pi
                        * (vv.recovery.canopy_diameter_m / 2) ** 2
                        * vv.recovery.drag_coefficient
                        if vv.recovery
                        else None
                    ),
                }
            )
    fits = [
        clearance(
            "outer_ring_body",
            (64.9 - 64.45) / 2 - 0.05,
            (65.024 - 64.4) / 2,
            (65.15 - 64.35) / 2 + 0.05,
            "proposed incoming bodyID/cutOD/environment bounds",
        ),
        clearance(
            "inner_ring_mount",
            (31.85 - 31.45) / 2 - 0.05,
            (31.9 - 31.369) / 2,
            (31.95 - 31.25) / 2 + 0.05,
            "proposed incoming mountOD31.25–31.45; not supplier tolerance",
        ),
        clearance(
            "nose_plate_shoulder",
            (61.5 - 61.05) / 2 - 0.05,
            (61.6 - 61) / 2,
            (61.7 - 60.95) / 2 + 0.05,
            "proposed printed bore61.5–61.7/cutplate/environment",
        ),
        clearance(
            "tab_inner_flat",
            15.925 - 31.45 / 2 - 0.05,
            15.95 - 31.369 / 2,
            15.975 - 31.25 / 2 + 0.05,
            "proposed tab-cut and receivingOD ranges",
        ),
        clearance(
            "notch_per_flank",
            (6.55 - 6.2) / 2 - 0.05,
            (6.6 - 6) / 2,
            (6.65 - 5.8) / 2 + 0.05,
            "perflank;2flanks sum is total clearance",
        ),
        clearance(
            "front_tab_end",
            1080.15 - 1079.85 - 0.05,
            0.4,
            1080.25 - 1079.75 + 0.05,
            "tabfront/notchfloor axial setup±.05 and differential±.05",
        ),
        clearance(
            "aft_tab_end",
            1189.95 - 1189.65 - 0.05,
            0.4,
            1190.05 - 1189.55 + 0.05,
            "aftringfront/tabend axial setup±.05 and differential±.05",
        ),
    ]
    source_parts = {p.id: p for p in v.parts}
    paper_ids = [
        "upper_body",
        "body_splice",
        "splice_seam_patch",
        "splice_adhesive",
        "rail_buttons",
        "rail_backers",
    ]
    known_fore = (
        sum(source_parts[i].resolved_mass_kg for i in paper_ids)
        + source_parts["body"].resolved_mass_kg * (1.075 - 0.458) / 0.762
    )
    unknown_fore = sum(
        source_parts[i].resolved_mass_kg
        for i in ["finish", "service_allowance", "ring_bonds", "mount_external_shield"]
    )
    area = math.pi * (0.033401**2 - 0.032512**2)
    body_adverse = rows[1]["common_acceleration_partition_N"]["body"]
    footprint = math.pi * (7**2 - 2.25**2)
    audit = {
        "fore_paper_branch": {
            "known_mass_kg": known_fore,
            "uncertain_additional_mass_kg": [0, unknown_fore],
            "force_N_bounds": [FACTOR * known_fore, FACTOR * (known_fore + unknown_fore)],
            "mean_axial_paper_stress_MPa_bounds": [
                FACTOR * known_fore / area / 1e6,
                FACTOR * (known_fore + unknown_fore) / area / 1e6,
            ],
            "branch_definition": "retained upper paper/attached hardware into outer ring bond; excludes nose/soft goods/eyes and front motor-tube stub. Distributed finish/service/bond/shield ownership unresolved.",
            "paper_scalar_screen_MPa": 2,
            "moment_note": "eccentric recovery produces angular acceleration/internal bending; complete inertia/load sharing unresolved. Axial mean alone is not acceptance.",
        },
        "provisional_washer": {
            "contact_area_mm2": footprint,
            "body_adverse_force_N": body_adverse,
            "mean_pressure_MPa_70percent": 0.7 * body_adverse / footprint,
            "mean_pressure_MPa_single": body_adverse / footprint,
            "required_contact_area_mm2_at5MPa": body_adverse / 5,
            "scope": "geometric mean lower bound on max contact pressure, not an orthotropic compression allowable or finished washer capacity",
        },
        "joint_direction": {
            "recovery": "ring pulled noseward; blind notchfrontweb moves away from aft tab, so it cannot provide direct compression bearing for that pull direction. Side/floor adhesive tension/shear transfers it.",
            "motor": "forward thrust and reverse retention need exact motor shoulder/cap contacts; no confirmed liner termination or generic flange credit.",
            "fin": "8.83Nm factored moment retained once; root/bond flexibility and installed flutter unresolved.",
        },
        "fit_source_conflicts": [
            "generic0.1mm tolerance has no diameter/radius datum; original conditioned outerring gap can fall below0.1mm under either interpretation",
            "forward_ring learn narrative says two6.5mm/13mm while actualgeometry/buildnotes say two6mm+.2/12.2mm",
            "paired eye has one purchased-envelope box/offset; it is not an accepted two-instance hardwareCAD assembly",
            "10g shield is a sector reserve; inherited full-annulus display envelope intersects tube and must not be treated as resolved material occupancy",
        ],
    }
    record = {
        "identity": candidate.id,
        "status": "proposed fits pass declared windows; installed recovery/motor/thermal/fin and adoption held",
        "source_spec_sha256": EXPECTED,
        "proposal_spec_sha256": hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases": rows,
        "fits": fits,
        "new_adhesive_mass_g": sum(p["mass_kg"] for p in additions) * 1000,
        "wood_removal_mass_credit_g": 0,
        "stock_removal_credit_basis": "original conservative allocations retained pending structural function verification",
        "audit": audit,
        "static_rocketpy": compare_rocketpy(candidate),
        "physical_full_inertia": None,
        "adopted": False,
        "runtime_wall_s": time.monotonic() - start,
    }
    (OUT / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    (OUT / "executed-producer.py").write_text(Path(__file__).read_text())
    (OUT / "specification.yaml").write_bytes(CANDIDATE.read_bytes())
    print(
        json.dumps(
            {
                "added_adhesive_g": record["new_adhesive_mass_g"],
                "runtime_s": record["runtime_wall_s"],
                "fits": [
                    {"id": f["id"], "min": f["minimum_mm"], "pass": f["conditional_screen_pass"]}
                    for f in fits
                ],
                "proposed_cases": rows[2:],
                "audit": audit,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
