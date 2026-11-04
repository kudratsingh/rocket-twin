"""One declared RP1 recommendation screen; no solver, flight or adoption."""

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

from scripts.wo03_f2_c1_load_path import FACTOR, NOSE
from src.vehicle.aero import center_of_pressure
from src.vehicle.benchmark import screen_launch
from src.vehicle.mass import mass_properties
from src.vehicle.reference import compare_rocketpy
from src.vehicle.schema import Vehicle, load_vehicle

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "configs/vehicle/candidates/g80-f2-c1-fit-proposal.yaml"
CANDIDATE = ROOT / "configs/vehicle/candidates/g80-f2-rp1-wrap.yaml"
OUT = ROOT / "runs/wo03-f2-recovery-precedent-20261103-v1"
EXPECTED = "f4f62b8c2051bc1f50bad5738ad8597d63671d953a1da2a70c18ec6f8bd75201"


def main() -> None:
    start = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    if OUT.exists():
        raise ValueError("Preserve executed recommendation; refuse overwrite")
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != EXPECTED:
        raise ValueError("Frozen C1 proposal changed")
    before = load_vehicle(SOURCE)
    d = before.model_dump(by_alias=True, exclude_none=True)
    d["parts"][0]["parent"] = None
    d["id"] = "G80-F2-RP1-wrap-recommendation-v1"
    d["name"] = "F2 RP1 motor-tube wrap recommendation — not adopted"
    removed_ids = {"body_recovery_eye", "heat_leader"}
    removed = [p for p in d["parts"] if p["id"] in removed_ids]
    d["parts"] = [p for p in d["parts"] if p["id"] not in removed_ids]
    by = {p["id"]: p for p in d["parts"]}
    ring = by["forward_ring"]
    # Fill old three blind slots and two holes; zero credit for the new cord notch.
    fill_mm3 = 3 * 6.6 * 7.4 * (32.2 - 15.95) + 2 * math.pi * 2.25**2 * 12.2
    fill_kg = fill_mm3 * 800e-9  # Explicit unmeasured conservative wood mass budget.
    ring["mass_kg"] += fill_kg
    ring["position_m"] = 1.060
    ring["cad"]["generator"] = "unadmitted_rp1_cord_notched_annulus"
    ring["cad"]["parameters"] = {
        "complete_geometry_available": False,
        "proposal_adopted": False,
        "cord_notch_angle_deg": 60,
        "cord_notch_width_m": 0.0045,
        "cord_notch_radial_depth_m": 0.005,
        "cut_tolerance_m": 0.00005,
        "front_station_m": 1.060,
        "aft_station_m": 1.0722,
    }
    ring["learn"] = (
        "RP1 proposed fixed ring ahead of tabs, 1060–1072.2mm. Two6mm plies+.2mm glue. "
        "No eye holes or blind fin slots. One4.5x5mm inner-edge cord notch at60deg. "
        "Retain old wood budget plus all filled voids at800kg/m3 estimate; no new-cut credit. "
        "Recovery wrap bears against aft ring/tube interface. Actual contact/peel/strength unknown."
    )
    ring["engineering"]["function"] = ring["learn"]
    ring["build"]["notes"] = ring["learn"]
    ring["cad"]["notes"] = ring["learn"]
    by["fin_tabs"]["learn"] += (
        " RP1: forward ring moved ahead of tabs. Old front end/side ring bonds no longer exist. "
        "Fin forces use continuous tab-to-mount/root/body bonds and aft-ring connection; "
        "their finite installed stiffness/strength must be revalidated. No older result transferred."
    )
    by["fin_tabs"]["cad"]["parameters"]["front_ring_support_available"] = False
    main_cord = by["shock_cord"]
    main_cord["mass_kg"] = 0.055
    main_cord["position_m"] = 0.28
    main_cord["cg_offset_m"] = 0.06
    main_cord["geometry"] = {"bbox_m": [0.12, 0.04, 0.04]}
    main_cord["build"]["cost_usd"] = 20.0
    main_cord["learn"] = (
        "RP1 proposed LOC3/8in tubular nylon12ft with sewn loops,1020lb advertised tensile. "
        "55g installed mass and$20 are estimates, not this variant's published mass/price. "
        "Mass analogy: different Apogee1/2in nylon5.68g per foot times.75width times12ft, "
        "rounded upward; no same weave/linear density claim. Supplier test scope, finished "
        "sewn-loop/connector/knot/hot-wet capacity and force-extension curve unavailable."
    )
    main_cord["engineering"]["function"] = main_cord["learn"]
    main_cord["build"]["notes"] = main_cord["learn"]
    template = by["service_allowance"]
    additions = [
        (
            "rp1_kevlar_wrap",
            0.47,
            0.020,
            17.10,
            "purchased",
            "commercial",
            (
                "8ft raw Apogee30327 1500lb braided Kevlar;20g estimate from2g listing per priced-foot unit plus25percent. "
                "Listing mass basis unconfirmed. Buy10ft minimum, install8ft, spare2ft excluded from flight mass. "
                "Loop/knot, radial clearance and end strength unqualified; flexible knot is not glued."
            ),
        ),
        (
            "rp1_wrap_lock_bond",
            1.066,
            0.004,
            0.8,
            "bonded",
            "epoxy",
            (
                "Additional4g installation/anti-slip fillet budget at ring/tube, not a glue-only tensile anchor. "
                "No glue on working rope or knot; actual finished process must be tested."
            ),
        ),
        (
            "rp1_notch_sealer",
            1.060,
            0.001,
            0.2,
            "bonded",
            "epoxy",
            "1g rounded-notch sealing/finishing budget; edge radius and conditioned chafe capacity unknown.",
        ),
        (
            "rp1_lip_guard",
            0.16,
            0.004,
            8.0,
            "assembled",
            "commercial",
            (
                "Custom soft aramid-textile mouth/chafe guard4g budget,60x20mm envelope; not a qualified load-spreading anchor. "
                "Existing canopy protector remains separately counted. Apogee29187 is not selected: stated fit is100/300lb cord, not30327."
            ),
        ),
    ]
    for pid, z, mass, cost, method, material, note in additions:
        p = copy.deepcopy(template)
        p.update(
            id=pid,
            parent="body",
            position_m=z,
            cg_offset_m=0.05 if z == 0.47 else 0.0061,
            geometry={"bbox_m": [0.1, 0.03, 0.025]},
            material=material,
            mass_kg=mass,
            learn=note,
            estimate=True,
        )
        p["cad"].update(
            generator="envelope", role="soft_stowage" if "kevlar" in pid else "distributed_budget"
        )
        p["build"].update(method=method, cost_usd=cost, notes=note)
        p["engineering"]["function"] = note
        if pid == "rp1_kevlar_wrap":
            p["cad"]["parameters"] = {
                "complete_geometry_available": False,
                "raw_length_m": 2.4384,
                "proposed_max_cord_diameter_m": 0.0038,
                "wrap_axial_min_m": 1.0722,
                "wrap_axial_max_m": 1.0770,
                "exit_angle_deg": 60,
                "knot_envelope_verified": False,
                "knot_reserved_box_m": [0.018, 0.014, 0.010],
                "knot_radial_min_m": 0.0205,
                "knot_radial_max_m": 0.0305,
            }
        d["parts"].append(p)
    for pid in ["ring_bonds", "fin_internal_bonds", "c1_forward_root_bond_fill"]:
        by[pid]["learn"] += (
            " RP1 retains the full existing mass as counted installation reserve; "
            "old blind-notch/end film occupancy is superseded, no adhesive bridge across the new front gap is credited."
        )
    candidate = Vehicle.model_validate(d)
    definition = yaml.safe_dump(d, sort_keys=False)
    if CANDIDATE.exists():
        if CANDIDATE.read_text() != definition:
            raise ValueError("Saved recommendation differs; do not overwrite")
    else:
        CANDIDATE.write_text(definition)
    props = mass_properties(candidate)
    cp = center_of_pressure(candidate)
    parts = {p.id: p for p in candidate.parts}
    previous = json.loads(
        (ROOT / "runs/wo03-g80-f2-c1-definition-20261103-v1/record.json").read_text()
    )
    baseline = [c for c in previous["cases"] if c["variant"] == "C1_fit_proposal"]
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
        p.resolved_mass_kg for p in candidate.parts if p.id in NOSE | soft
    )
    rows = []
    for name, extra, probe in [("nominal", 0.0, 0.0), ("adverse", 0.02, 0.0128)]:
        total = props.mass_kg + 0.05 + extra
        moment = (
            props.mass_kg * props.cg_m
            + (0.05 + extra) * 1.25
            + parts["motor"].resolved_mass_kg * probe
        )
        cg = moment / total
        guides = {}
        for length in [1.5, 1.8]:
            q = candidate.model_copy(deep=True)
            q.design.rail_length_m = length
            guides[str(length)] = screen_launch(q, study_nominal_mass_kg=total - 0.05)[
                "rail_exit_speed_mps"
            ]
        burnout_mass = total - 0.0625
        burnout_cg = (moment - 0.0625 * (1.092 + 0.064)) / burnout_mass
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
                "burnout_mass_kg": burnout_mass,
                "burnout_cg_m": burnout_cg,
                "burnout_margin_cal": (cp - burnout_cg) / 0.066802,
                "guide_mps": guides,
                "formal_mass_headroom_g": (limits["15.0"] - total) * 1000,
                "planning_mass_headroom_g": (limits["15.5"] - total) * 1000,
                "required_whole_mean_proxy_N": FACTOR * total,
                "required_body_proxy_N": FACTOR * (body_mass + 0.05 + extra),
            }
        )
    ledger = [
        {
            "id": p.id,
            "mass_g": p.resolved_mass_kg * 1000,
            "cg_mm": p.cg_station_m * 1000,
            "cost_usd": p.build.cost_usd,
            "basis": p.learn,
        }
        for p in candidate.parts
    ]
    delta = (props.mass_kg - mass_properties(before).mass_kg) * 1000
    record = {
        "identity": candidate.id,
        "adopted": False,
        "status": "recommended topology; complete admission held",
        "sources": {
            str(SOURCE.relative_to(ROOT)): EXPECTED,
            str(CANDIDATE.relative_to(ROOT)): hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),
        },
        "cases": rows,
        "baseline_cases": baseline,
        "ledger": ledger,
        "delta_mass_g": delta,
        "removal_credit_g": sum(p["mass_kg"] for p in removed) * 1000,
        "removal_functions": {
            "body_recovery_eye": "motor-tube wrap supplies body anchor function; capacity still unqualified",
            "heat_leader": "8ft30327 heat-resistant leader includes wrap/termination raw length",
        },
        "addition_mass_g": delta + sum(p["mass_kg"] for p in removed) * 1000,
        "filled_old_wood_mass_g": fill_kg * 1000,
        "new_cut_mass_credit_g": 0,
        "complete_cost_estimate_usd": sum(p.build.cost_usd for p in candidate.parts),
        "maximum_main_cord_mass_g_adverse_formal": 55 + rows[1]["formal_mass_headroom_g"],
        "maximum_main_cord_mass_g_adverse_planning": 55 + rows[1]["planning_mass_headroom_g"],
        "label_only_strength_N": {
            "apogee30327": 1500 * 4.4482216152605,
            "LOC3/8nylon": 1020 * 4.4482216152605,
            "LOC3/16nylon": 375 * 4.4482216152605,
            "MadcowP183nylon": 550 * 4.4482216152605,
        },
        "physical_full_inertia": None,
        "static_rocketpy": compare_rocketpy(candidate),
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "runtime_wall_s": time.monotonic() - start,
    }
    OUT.mkdir()
    (OUT / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    (OUT / "specification.yaml").write_bytes(CANDIDATE.read_bytes())
    (OUT / "executed-producer.py").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {
                k: record[k]
                for k in [
                    "identity",
                    "delta_mass_g",
                    "maximum_main_cord_mass_g_adverse_formal",
                    "cases",
                    "runtime_wall_s",
                ]
            }
        )
    )


if __name__ == "__main__":
    main()
