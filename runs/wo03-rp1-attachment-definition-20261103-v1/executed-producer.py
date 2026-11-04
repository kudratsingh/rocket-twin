"""Bounded RP1 definition arithmetic; no continuum solver or strength qualification."""

from __future__ import annotations

import hashlib
import json
import math
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
import numpy as np
import yaml

from scripts.wo03_f2_c1_load_path import FACTOR, NOSE
from src.vehicle.aero import center_of_pressure
from src.vehicle.benchmark import screen_launch
from src.vehicle.mass import mass_properties
from src.vehicle.reference import compare_rocketpy
from src.vehicle.schema import Vehicle, load_vehicle

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "configs/studies/rp1-attachment-definition.yaml"
CANDIDATE = ROOT / "configs/vehicle/candidates/g80-f2-rp1-ad1.yaml"
OUT = ROOT / "runs/wo03-rp1-attachment-definition-20261103-v1"


def plate_displacement(n: int, thickness: float, gussets: bool = True) -> dict:
    """Independent strip integration; clamp is a lower displacement bound only."""
    x = np.linspace(0.0, 0.06, n)
    chord = 0.13 + (0.065 - 0.13) * x / 0.06
    area = 0.06 * (0.13 + 0.065) / 2
    ar = 2 * 0.06**2 / area
    slope = 2 * math.pi * ar / (2 + math.sqrt(4 + ar * ar))
    p = 40000 * slope * math.radians(5) * 3
    a, b = p * 0.13, p * (0.065 - 0.13) / 0.06
    moment = a * (0.06 - x) ** 2 / 2 + b * (0.06**3 / 3 - x * 0.06**2 / 2 + x**3 / 6)
    # Rescale the tiny rounding difference to the declared already-factored8.83Nm.
    moment *= 8.83 / moment[0]
    h = thickness + (0.012 * np.maximum(0, 1 - x / 0.015) if gussets else 0)
    ei = 1e9 * chord * h**3 / 12
    delta = float(np.trapezoid(moment * (0.06 - x) / ei, x))
    return {
        "divisions": n - 1,
        "deflection_m": delta,
        "maximum_bending_Pa": float(np.max(6 * moment / (chord * h**2))),
    }


def main() -> None:
    start = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    if OUT.exists() or CANDIDATE.exists():
        raise ValueError("Preserve executed records; no automatic rerun or overwrite")
    s = yaml.safe_load(STUDY.read_text())
    source = ROOT / s["source"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != s["source_sha256"]:
        raise ValueError("Frozen balancedRP1 changed")
    v = load_vehicle(source)
    d = v.model_dump(by_alias=True, exclude_none=True)
    d["parts"][0]["parent"] = None
    d.update(id=s["id"], name="RP1 AD1 cord/fin test definition — unadopted")
    by = {p["id"]: p for p in d["parts"]}
    leader = by["rp1_kevlar_wrap"]
    leader["mass_kg"] = 0.01625
    leader["cad"]["parameters"].update(
        raw_length_m=1.9812,
        knot_reserved_box_m=[0.05, 0.02, 0.014],
        knot_radial_min_m=0.0165,
        knot_radial_max_m=0.0305,
    )
    leader["learn"] = (
        "AD1:6.5ft raw30327,16.25g estimate; two figure-eight eyes and reeved proximal choker,300mmrawreserved eachtermination; knotcapacity/actualenvelopeunknown. Frozen6ftRP1 unchanged."
    )
    leader["build"]["notes"] = leader["learn"]
    leader["engineering"]["function"] = leader["learn"]
    main_cord = by["shock_cord"]
    main_cord["build"]["cost_usd"] = 12.39
    main_cord["learn"] = (
        "LOC NW-12 variant39778657730751; uncut12ft3/8in tubular nylon factoryends;55g remains estimate, price12.39 observed manufacturer. Finishedmass/strength and bearinglength unknown; commerceweight68 is sensitivity only."
    )
    by["fin_set"]["engineering"][
        "function"
    ] = "AD1 through-wall fin, continuous tab/mount, external wedges/body and aft-ring adhesive only; no moved front-ring support."
    by["fin_set"]["build"][
        "notes"
    ] = "Spruce02-20850 nominal6mm; proposed incoming5.8–6.2mm, not supplier guarantee. Spanwise face grain."
    by["fin_set"]["cad"]["notes"] = by["fin_set"]["build"]["notes"]
    # Existing body geometry stays fixed. This is a cut-width definition, not new CAD.
    by["body"]["cad"]["parameters"]["ad1_fin_slot_width_m"] = 0.0068
    for pid, mass, station, geometry, note in [
        (
            "ad1_cord_sleeve",
            0.002,
            1.0322,
            [0.08, 0.008, 0.002],
            "80mm folded aramid heat/chafe sleeve, exactstock unknown; no thermalcapacity credited;2gcountedonce.",
        ),
        (
            "ad1_slot_fill",
            0.00015,
            1.075,
            [0.13, 0.0003, 0.000889],
            "Additionalslotepoxy0.15g above frozenbudgets for6.8mmcuts;0.125gminimumvolumeestimate; no removedpapercredit.",
        ),
    ]:
        part = json.loads(json.dumps(by["rp1_notch_sealer"]))
        part.update(
            id=pid,
            mass_kg=mass,
            position_m=station,
            cg_offset_m=geometry[0] / 2,
            geometry={"bbox_m": geometry},
            learn=note,
        )
        part["build"].update(cost_usd=2.0 if pid == "ad1_cord_sleeve" else 0.25, notes=note)
        part["engineering"]["function"] = note
        part["cad"]["notes"] = note
        d["parts"].append(part)
    candidate = Vehicle.model_validate(d)
    CANDIDATE.write_text(yaml.safe_dump(d, sort_keys=False))
    p = mass_properties(candidate)
    cp = center_of_pressure(candidate)
    motor = next(x for x in candidate.parts if x.id == "motor")
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
    body_mass = p.mass_kg - sum(x.resolved_mass_kg for x in candidate.parts if x.id in NOSE | soft)
    cases = []
    for main_g in [55, 68]:
        for name, extra, probe in [("nominal", 0.0, 0.0), ("adverse", 0.02, 0.0128)]:
            correction = (main_g - 55) / 1000
            total = p.mass_kg + 0.05 + extra + correction
            moment = (
                p.mass_kg * p.cg_m
                + (0.05 + extra) * 1.25
                + motor.resolved_mass_kg * probe
                + correction * 0.34
            )
            cg = moment / total
            guide = {}
            for length in [1.5, 1.8]:
                q = candidate.model_copy(deep=True)
                q.design.rail_length_m = length
                guide[str(length)] = screen_launch(q, study_nominal_mass_kg=total - 0.05)[
                    "rail_exit_speed_mps"
                ]
            dry = total - candidate.motor.propellant_mass_kg
            dry_cg = (moment - candidate.motor.propellant_mass_kg * motor.cg_station_m) / dry
            stow = cg + (0.01625 * (0.85 - 0.60) + main_g / 1000 * (0.40 - 0.34)) / total
            cases.append(
                {
                    "case": name,
                    "nylon_mass_probe_g": main_g,
                    "probe_is_bound": False,
                    "total_mass_g": total * 1000,
                    "growth_g": 50,
                    "extra_aft_g": extra * 1000,
                    "motor_cg_probe_mm": probe * 1000,
                    "cg_mm": cg * 1000,
                    "cp_mm": cp * 1000,
                    "margin_cal": (cp - cg) / 0.066802,
                    "burnout_cg_mm": dry_cg * 1000,
                    "burnout_margin_cal": (cp - dry_cg) / 0.066802,
                    "aft_stowage_margin_cal": (cp - stow) / 0.066802,
                    "guide_mps": guide,
                    "formal_speed_margin_mps": guide["1.5"] - 15,
                    "planning_speed_margin_mps": guide["1.5"] - 15.5,
                    "formal_mass_headroom_g": (limits["15.0"] - total) * 1000,
                    "planning_mass_headroom_g": (limits["15.5"] - total) * 1000,
                    "whole_mean_proxy_N": FACTOR * total,
                    "body_proxy_N": FACTOR * (body_mass + 0.05 + extra),
                }
            )
    r = s["route"]
    circumference = math.pi * (r["tube_od_mm"] + s["cord"]["kevlar"]["proposed_max_diameter_mm"])
    route = r["forward_ring_mm"][1] - r["mouth_station_mm"] + r["route_detour_mm"]
    reach = s["cord"]["kevlar"]["installed_raw_cut_m"] * 1000 - 600 - circumference - route
    refinements = [plate_displacement(n, 0.0058) for n in [101, 401, 1601]]
    delta = refinements[-1]["deflection_m"]
    load = 8.83 / (0.06 * (0.13 + 2 * 0.065) / (3 * (0.13 + 0.065)))
    body_demand = cases[1]["body_proxy_N"]
    areas = {
        "ring_outer_mm2": math.pi * 64.4 * 12.2,
        "ring_inner_mm2": math.pi * 31.9 * 12.2 - 4.5 * 12.2,
        "tab_flat_mm2_per_fin": 109.4 * 5.8,
        "gusset_fin_face_mm2_one_side": 130 * 15,
        "gusset_body_base_mm2_one_side": 130 * 6,
        "aft_tab_end_mm2": 17.451 * 5.8,
    }
    couple = 8.83 / 0.015
    outer_knot_radius = math.hypot(30.5, 10)
    record = {
        "identity": s["id"],
        "adopted": False,
        "decision": "test_definition_only; finishedcapacity/rootnormalpeel/stiffness/thermalunknown;planningmiss",
        "cases": cases,
        "ledger": [
            {
                "id": x.id,
                "mass_g": x.resolved_mass_kg * 1000,
                "cg_mm": x.cg_station_m * 1000,
                "cost_usd": x.build.cost_usd,
            }
            for x in candidate.parts
        ],
        "net_addition_to_balanced_g": (p.mass_kg - mass_properties(v).mass_kg) * 1000,
        "estimated_cost_usd": sum(x.build.cost_usd for x in candidate.parts),
        "physical_inertia": None,
        "full_flight": "not run; physical inertia/source/motor unresolved",
        "cord_geometry": {
            "wrap_centerline_circumference_mm": circumference,
            "guarded_route_mm": route,
            "termination_reservation_each_mm": 300,
            "available_external_reach_mm": reach,
            "minimum_reach_mm": 300,
            "reach_pass": reach >= 300,
            "notch_min_per_flank_mm": (4.5 - 0.05 - 3.8 - 0.05) / 2,
            "knot_box_cold_body_clearance_mm": 32.512 - outer_knot_radius,
            "knot_box_not_a_verified_knot": True,
        },
        "fin": {
            "factored_moment_Nm": 8.83,
            "factored_force_N": load,
            "no_second_factor": True,
            "actual_root_support": "no front-ring contact; finite tab/tube/body/gusset and aft-end adhesive",
            "ideal_composite_strip_lower_deflection_only": refinements,
            "relative_delta_last_two": abs(
                refinements[-1]["deflection_m"] / refinements[-2]["deflection_m"] - 1
            ),
            "bonded_panel_stress_screen_pass_only": refinements[-1]["maximum_bending_Pa"] <= 5e6,
            "bare_panel": plate_displacement(1601, 0.0058, False),
            "required_joint_rotation_stiffness_Nm_rad": (
                8.83 * 0.06 / (0.001 - delta) if delta < 0.001 else None
            ),
            "root_spring_examples": [
                {"K_Nm_rad": k, "total_tip_mm": 1000 * (delta + 8.83 * 0.06 / k)}
                for k in [200, 500, 1000, 3000]
            ],
            "couple_force_at_15mm_N": couple,
            "areas": areas,
            "gusset_fin_face_mean_Pa": couple / (areas["gusset_fin_face_mm2_one_side"] * 1e-6),
            "gusset_body_normal_mean_Pa": couple / (areas["gusset_body_base_mm2_one_side"] * 1e-6),
            "tab_flat_mean_if_whole_couple_Pa": couple / (areas["tab_flat_mm2_per_fin"] * 1e-6),
            "aft_end_mean_if_whole_force_Pa": load / (areas["aft_tab_end_mm2"] * 1e-6),
            "normal_peel_capacity": None,
            "installed_displacement": None,
            "installed_flutter": "unavailable; changed joint stiffness/inertia not validated",
        },
        "recovery_connections": {
            "areas": areas,
            "adverse_body_proxy_N": body_demand,
            "outer_ring_mean_shear_Pa": body_demand / (areas["ring_outer_mm2"] * 1e-6),
            "inner_ring_mean_shear_if_full_force_Pa": body_demand
            / (areas["ring_inner_mm2"] * 1e-6),
            "body_full_route_axial_stress_Pa": body_demand
            / (math.pi * (33.401**2 - 32.512**2) * 1e-6),
            "scope": "separate full-route envelopes, not equalsharing or summed simultaneous independent loads; peel/crush/ropepressure/annularbending unresolved",
            "finished_attachment_capacity_N": None,
        },
        "slot_clearance": {
            "previous_min_per_flank_mm": (6.5 - 0.1 - 6.2 - 0.05) / 2,
            "proposed_min_per_flank_mm": (6.8 - 0.05 - 6.2 - 0.05) / 2,
            "criterion_mm": 0.1,
            "conditional_only": True,
            "added_epoxy_g": 0.15,
            "removal_credit_g": 0,
        },
        "rocketpy_static_reference": compare_rocketpy(candidate),
        "sources": {
            str(x.relative_to(ROOT)): hashlib.sha256(x.read_bytes()).hexdigest()
            for x in [source, STUDY, CANDIDATE, Path(__file__)]
        },
        "resources": {
            "cpu_seconds": time.process_time(),
            "wall_seconds": time.monotonic() - start,
            "thread_env_limit": 1,
            "cpu_affinity_verified": False,
            "new_continuum_solver_runs": 0,
        },
    }
    # Independent closed-form uniform-beam verification of the quadrature only.
    x = np.linspace(0, 0.06, 1601)
    ei = 1e9 * 0.13 * 0.0058**3 / 12
    calculated = float(np.trapezoid((load / 0.06) * (0.06 - x) ** 3 / (2 * ei), x))
    exact = load * 0.06**3 / (8 * ei)
    record["method_check"] = {
        "uniform_beam_numerical_m": calculated,
        "closed_form_m": exact,
        "relative_error": abs(calculated / exact - 1),
        "scope": "integration only, not installed root or material validation",
    }
    OUT.mkdir()
    (OUT / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    (OUT / "executed-producer.py").write_bytes(Path(__file__).read_bytes())
    (OUT / "specification.yaml").write_bytes(CANDIDATE.read_bytes())
    print(
        json.dumps(
            {
                key: record[key]
                for key in ["identity", "cases", "cord_geometry", "fin", "resources"]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
