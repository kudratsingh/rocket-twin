"""Source-pinned F2 construction projection; never executes CAD/physics on GET."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "spec": "configs/vehicle/candidates/g80-f2-ballast.yaml",
    "record": "runs/wo03-g80-f2-selected-20261103-v2/record.json",
    "span65": "runs/wo03-g80-f2-preflight-20261103-v2/record.json",
    "first": "runs/wo03-g80-f2-preflight-20261103-v1/record.json",
    "joints": "runs/wo03-g80-f2-joints-20261103-v1/report.json",
    "supplier": "docs/wo03-g80-f2-suppliers.md",
    "decision": "docs/wo03-g80-f2-decision.md",
    "f1": "runs/wo03-g80-f1-preflight-20261102-v2/record.json",
    "ring_diagnostic": "runs/wo03-g80-f2-ring-20261103-v1/record.json",
    "accounting": "runs/wo03-g80-f2-accounting-20261103-v1/record.json",
}


def build_f2(root: Path = ROOT) -> dict[str, Any]:
    raw = {k: (root / p).read_bytes() for k, p in SOURCES.items()}
    cfg = yaml.safe_load(raw["spec"])
    r = json.loads(raw["record"])
    joint = json.loads(raw["joints"])
    sha = hashlib.sha256(raw["spec"]).hexdigest()
    if r["spec_sha256"] != sha or joint["spec_sha256"] != sha:
        raise ValueError("F2 spec/result/local-joint revision mismatch")
    sources = [
        {
            "id": k,
            "path": SOURCES[k],
            "sha256": hashlib.sha256(v).hexdigest(),
            "description": k + " F2 source",
        }
        for k, v in raw.items()
    ]
    rows = []
    record_parts = {p["id"]: p for p in r["parts"]}
    for p in cfg["parts"]:
        g = p["geometry"]
        box = g.get("bbox_m")
        role = p["cad"]["role"]
        cat = (
            "recovery"
            if p["type"] == "recovery"
            or p["id"] in ["body_recovery_eye", "nose_recovery_eye", "nose_anchor_plate"]
            else (
                "motor"
                if p["id"] in ["motor", "motor_retainer", "motor_tube"]
                else (
                    "fin"
                    if p["id"] in ["fin_set", "fin_tabs", "root_gussets", "root_extra_bond_finish"]
                    else (
                        "airframe"
                        if p["id"]
                        in ["body", "upper_body", "body_splice", "nose", "forward_ring", "aft_ring"]
                        else "thermal" if "shield" in p["id"] else "avionics"
                    )
                )
            )
        )
        ro = g.get("radius_m")
        ri = g.get("inner_radius_m", 0) if ro else None
        if p["type"] == "fin_set":
            ri = ro
            ro = ro + g["span_m"]
        if p["id"] == "fin_tabs":
            ri = 0.0158845
            ro = 0.033401
        rows.append(
            {
                "id": p["id"],
                "label": p["id"].replace("_", " ").capitalize(),
                "category": cat,
                "function": p["learn"],
                "construction": p["build"]["method"],
                "material": p["material"],
                "mass_g": record_parts[p["id"]]["mass_kg"] * 1000,
                "z_start_mm": p["position_m"] * 1000,
                "z_end_mm": (p["position_m"] + g.get("length_m", box[0] if box else 0)) * 1000,
                "inner_radius_mm": None if ri is None else ri * 1000,
                "outer_radius_mm": None if ro is None else ro * 1000,
                "dimensions": {
                    k[:-2] + "_mm": v * 1000
                    for k, v in g.items()
                    if k.endswith("_m") and isinstance(v, (int, float))
                },
                "maturity": (
                    "envelope"
                    if role in ["purchased_envelope", "distributed_budget", "soft_stowage"]
                    else "concept"
                ),
                "state": "estimated",
                "source_ids": ["spec", "record"],
                "note": p["build"]["notes"] + " Whole assembly is not accepted CAD.",
            }
        )

    def layer(
        id: str, z1: float, z2: float, ri: float | None, ro: float | None, note: str
    ) -> dict[str, Any]:
        return {
            "component_id": id,
            "label": id.replace("_", " "),
            "z_start_mm": z1,
            "z_end_mm": z2,
            "inner_radius_mm": ri,
            "outer_radius_mm": ro,
            "state": "calculated",
            "note": note,
            "source_ids": ["spec", "joints"],
        }

    joints: list[dict[str, Any]] = [
        {
            "id": "fixed-splice",
            "label": "Permanent bonded stock splice",
            "kind": "bonded_splice",
            "station_mm": 458,
            "clearance_mm": 0.15,
            "layers": [
                layer("body", 458, 508, 32.512, 33.401, "LOC stock nominal"),
                layer("upper_body", 408, 458, 32.512, 33.401, "Cut298mm upper"),
                layer(
                    "body_splice",
                    408,
                    508,
                    31.336,
                    32.225,
                    "Custom split sleeve,50mm overlap each end",
                ),
                layer(
                    "splice_seam_patch",
                    408,
                    508,
                    30.347,
                    31.236,
                    "Internal seam patch;0.1mm glue gap",
                ),
                layer(
                    "splice_adhesive",
                    408,
                    508,
                    32.225,
                    32.512,
                    "Filled epoxy annulus, not parallel air",
                ),
            ],
            "state": "calculated",
            "note": "Local geometry passed only. Min/nom/max conditioned radial gap .15/.287/.425mm under declared receiving requirements. Strength/peel/humidity need verification.",
            "source_ids": ["spec", "joints"],
        },
        {
            "id": "blind-fin-notch",
            "label": "Blind fin-tab seat and mount bond",
            "kind": "notched_ring",
            "station_mm": 1080,
            "clearance_mm": 0.2,
            "layers": [
                layer(
                    "forward_ring",
                    1075,
                    1087.2,
                    15.8845,
                    32.3,
                    "4.8mm front web, three6.5mm wide blind notches",
                ),
                layer("fin_tabs", 1080, 1189.8, 15.8845, 33.401, "6mm nominal fin;0.2mm front gap"),
                layer(
                    "motor_tube",
                    1055,
                    1220,
                    14.5845,
                    15.6845,
                    "Manufacturer tube nominal; no current motor contact proof",
                ),
                layer("aft_ring", 1190, 1196, 15.8845, 32.3, "0.2mm tab end gap"),
            ],
            "state": "calculated",
            "note": "BRep ring/tab intersection0; side gap.25mm nominal. No strength or motion release.",
            "source_ids": ["spec", "joints"],
        },
        {
            "id": "nose-carrier",
            "label": "Serviceable nose instrumentation and ballast",
            "kind": "nose_service",
            "station_mm": 185,
            "clearance_mm": 1.1135,
            "layers": [
                layer(
                    "nose_anchor_plate",
                    178,
                    190.2,
                    22.5,
                    30.6,
                    "45mm aperture; small-eye hardware supplier held",
                ),
                layer(
                    "ballast_capsule",
                    40,
                    75,
                    0,
                    8.5,
                    "7g captive carrier/bolt, illustrative envelope",
                ),
                layer("nose_ballast", 45, 59.4, 2.65, 7.5, "12M5 washers,17.816g estimate"),
            ],
            "state": "estimated",
            "note": "Eight sampled corner envelopes pass; no connector/continuous insertion or deployed-motion proof.",
            "source_ids": ["spec", "joints"],
        },
    ]
    defs = [
        ("parachute", "shock_cord", "Parachute opening into main harness"),
        ("shock_cord", "heat_leader", "Main harness to two0.3m leader branches"),
        ("heat_leader", "body_recovery_eye", "Unequal70/30 and single-leg anchor cases"),
        ("body_recovery_eye", "forward_ring", "Closed eyes/washers into notched ring"),
        ("forward_ring", "fin_tabs", "Ring/tab end/side bonds; finite support unknown"),
        ("forward_ring", "body", "Ring outer bond into thin paper body"),
        ("forward_ring", "motor_tube", "Ring inner bond into motor mount"),
        ("fin_tabs", "aft_ring", "Tab end/bonds into aft ring"),
        ("aft_ring", "body", "Fixed aft-ring/body bond"),
        ("motor", "motor_retainer", "Motor shoulder and reverse retention; exact contact held"),
        ("motor_retainer", "motor_tube", "Manufacturer matched tube/retainer; installed bond held"),
        ("shock_cord", "nose_recovery_eye", "Separate retained nose branch"),
        ("nose_recovery_eye", "nose_anchor_plate", "Nose eye and plywood annulus"),
        ("nose_anchor_plate", "nose", "Perimeter lap into printed shoulder"),
        ("upper_body", "body_splice", "Upper fixed50mm lap"),
        ("body_splice", "body", "Lower fixed50mm lap"),
        ("nose_ballast", "ballast_capsule", "Captive washer stack through central bolt"),
        ("ballast_capsule", "avionics_sled", "Carrier to retained nose assembly"),
    ]
    connections = [
        {
            "id": f"edge-{i}",
            "label": l,
            "from_id": a,
            "to_id": b,
            "kind": "recorded proposed connection",
            "state": "unavailable",
            "note": "Geometry/load route defined; installed capacity is not established.",
            "source_ids": ["spec", "decision", "joints"],
        }
        for i, (a, b, l) in enumerate(defs)
    ]
    cases = []
    for key, label in [
        ("record", "Selected60mm fins + captive ballast"),
        ("span65", "Lighter65mm-span alternative"),
        ("first", "Initial stock layout — superseded"),
    ]:
        rr = json.loads(raw[key])
        for c in rr["cases"]:
            q = c["guides"]["1.5"]
            cases.append(
                {
                    "id": rr["identity"] + "-" + c["id"],
                    "label": label + " / " + c["id"],
                    "total_mass_g": c["mass_kg"] * 1000,
                    "loaded_cg_mm": c["cg_m"] * 1000,
                    "reference_cp_mm": c["cp_m"] * 1000,
                    "margin_cal": c["margin_cal"],
                    "guide_speed_mps": q["speed_mps"],
                    "usable_guide_m": 1.5,
                    "formal_headroom_g": q["formal_headroom_g"],
                    "planning_headroom_g": q["planning_headroom_g"],
                    "source_ids": [key],
                    "note": "Full50g included; adverse also20g aft+12.8mm motor-CG probe. Planning target15.5 separate from formal15. No case is build/flight release.",
                }
            )
    f1 = {p["id"]: p for p in json.loads(raw["f1"])["parts"]}
    current = record_parts
    ledger = []
    for id in sorted(set(f1) | set(current)):
        a = current.get(id)
        b = f1.get(id)
        delta = (a["mass_kg"] if a else 0) - (b["mass_kg"] if b else 0)
        part = a or b
        assert part is not None
        ledger.append(
            {
                "id": id,
                "label": id.replace("_", " "),
                "mass_g": delta * 1000,
                "station_mm": part["cg_m"] * 1000,
                "role": (
                    "added"
                    if b is None
                    else "removed" if a is None else "changed" if abs(delta) > 1e-9 else "retained"
                ),
                "replaces_id": id if b else None,
                "state": "estimated",
                "note": "Signed F1→selected F2 mass change; source stock purchased once, no owner inventory assumed.",
                "source_ids": ["record", "f1"],
            }
        )

    def finding(id: str, label: str, state: str, note: str) -> dict[str, Any]:
        return {
            "id": id,
            "label": label,
            "state": state,
            "note": note,
            "source_ids": ["record", "joints", "decision"],
        }

    findings = [
        finding(
            "stability",
            "Calculated static stability",
            "calculated",
            "Selected nominal/adverse1.286/1.107cal meet1.0, with full50g and additional20g probe. Geometry/model hypothesis, not flight validation.",
        ),
        finding(
            "planning",
            "Adverse planning-speed target missed",
            "failed",
            "Selected1.5m adverse15.186m/s passes formal15, misses15.5. Planning deficit33.761g; no longer guide adopted.",
        ),
        finding(
            "recovery",
            "Severe recovery path remains open",
            "unavailable",
            "Whole severe factored mean1936/1978N; real annular ring/support/eye/body/bonds and snatch need evidence, strip alone does not establish installed strength.",
        ),
        finding(
            "root",
            "Installed root flexibility and flutter",
            "unavailable",
            "Minimum5.8mm panel.599mm leaves.401mm root allowance; requiredK≈435Nm/rad. Installed stiffness/damping and swept-fin flutter not validated.",
        ),
        finding(
            "thermal",
            "No accepted F2 temperature map",
            "unavailable",
            "45°C substrate screen unchanged; sector/contact/end geometry needs required thermal matrix. Shield10g is a reserve.",
        ),
        finding(
            "motor",
            "Current motor/retainer mating dimensions",
            "unavailable",
            "AeroTech12912+19002 selected candidate family,78010 shoulder/nozzle/lip/temperature/tolerances absent; no blind trim.",
        ),
        finding(
            "cost",
            "Recovery items carry purchase cost",
            "estimated",
            "Apogee34USD kit+cell/charger allocation, supply unconfirmed; no owner-owned stock evidence. Overall allowance458.71USD plus shipping/tax/other unquoted costs.",
        ),
        finding(
            "inertia",
            "Physical full inertia",
            "unavailable",
            "Diagnostic tensor uses own envelopes; detailed joints/distributed supports not full CAD-reconciled. No borrowed zero or historical flight.",
        ),
    ]
    findings.append(
        {
            "id": "ring-mesh",
            "label": "Ring diagnostic stopped — invalid middle mesh",
            "state": "failed",
            "note": "All3 solver runs finished; the2mm mesh has1 inverted quadratic element. Coarse/fine geometry passes sampled quality, but3-grid convergence and installed strength are unavailable. No stress overlay or retry is accepted.",
            "source_ids": ["ring_diagnostic", "decision"],
        }
    )

    def step(id: str, label: str, ids: list[str], note: str) -> dict[str, Any]:
        return {
            "id": id,
            "label": label,
            "acts_on_ids": ids,
            "state": "estimated",
            "note": note,
            "source_ids": ["spec", "decision"],
        }

    return {
        "schema_version": "1.0.0",
        "id": r["identity"],
        "label": "G80-F2 supplier-stock fixed conventional construction",
        "status": "Preliminary construction — full engineering admission open",
        "identity": {
            "candidate_id": "G80-F2",
            "source_identity": r["identity"],
            "specification_sha256": sha,
            "cad_revision": None,
            "frame": "z=0 nose tip;positive aft. Local joint CAD millimetres, flight SI. Radial drawings may be exaggerated.",
            "units": "mm,g,N,m/s,calibre",
        },
        "generated_from": sources,
        "components": rows,
        "sections": [
            {
                "id": j["id"],
                "label": j["label"],
                "station_mm": j["station_mm"],
                "component_ids": [l["component_id"] for l in j["layers"]],
                "note": j["note"],
                "source_ids": j["source_ids"],
            }
            for j in joints
        ],
        "joints": joints,
        "connections": connections,
        "cases": cases,
        "ledger": ledger,
        "uncertainties": findings,
        "cad_manifest": None,
        "sequences": {
            "assembly": [
                step(
                    "stock",
                    "Condition/measure/cut stock",
                    ["body", "upper_body", "body_splice"],
                    "Receiving dimensions are acceptance windows, not supplier tolerances.",
                ),
                step(
                    "splice",
                    "Form seam-patched sleeve; bond fixed splice",
                    ["body_splice", "splice_seam_patch", "splice_adhesive"],
                    "Mandrel alignment,50mm overlap each side, meter8g full-film/seam/fillet adhesive; no dry parallel air route.",
                ),
                step(
                    "root",
                    "Cut blind notches; inspect end gaps",
                    ["forward_ring", "fin_tabs", "motor_tube"],
                    "0.2mm end/centre bond gap,.25mm nominal side gap. Keep aft access for internal fillets.",
                ),
                step(
                    "nose",
                    "Install retained nose carrier and captive ballast",
                    ["avionics_sled", "ballast_capsule", "nose_ballast"],
                    "Two independent supplies; secure steel stack beforeclosing; no loose mass.",
                ),
                step(
                    "motor",
                    "Verify actual motor/retainer then install/remove aft",
                    ["motor", "motor_retainer"],
                    "Current controlled dimensions needed; retainer cap removal envelope not yet accepted.",
                ),
            ],
            "recovery": [
                step(
                    "release",
                    "Nose and its electronics separate",
                    ["nose", "avionics_sled", "independent_recovery"],
                    "Illustrative sequence; entire instrument pod retained with nose, no fixed obstruction in canopy path.",
                ),
                step(
                    "extract",
                    "Line slack pays out then canopy extracts",
                    ["parachute", "shock_cord", "heat_leader"],
                    "Packed50mm cylinder above splice; actual extraction/relative speed/stretch unmeasured.",
                ),
                step(
                    "load",
                    "Separate nose/body branches engage",
                    ["body_recovery_eye", "nose_recovery_eye"],
                    "Unequal and single-branch cases; no equal-sharing or validated deployment simulation.",
                ),
            ],
        },
    }
