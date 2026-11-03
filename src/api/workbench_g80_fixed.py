"""Recorded F1 projection only; GETs never execute physics or CAD."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC = "configs/vehicle/candidates/g80-f1.yaml"
RECORD = "runs/wo03-g80-f1-preflight-20261102-v2/record.json"
SOURCES = {
    "spec": SPEC,
    "result": RECORD,
    "first": "runs/wo03-g80-f1-preflight-20261102-v1/record.json",
    "construction": "docs/wo03-g80-fixed-construction-references.md",
    "recovery": "docs/wo03-g80-f1-recovery-review.md",
    "decision": "docs/wo03-g80-f1-decision.md",
    "packet": "docs/wo03-g80-fixed-packet.md",
    "supply": "docs/wo03-g80-f1-supply-holds.md",
}


def build_conventional_g80(root: Path = ROOT) -> dict[str, Any]:
    raw = {k: (root / p).read_bytes() for k, p in SOURCES.items()}
    cfg = yaml.safe_load(raw["spec"])
    rec = json.loads(raw["result"])
    if (
        hashlib.sha256(raw["spec"]).hexdigest() != rec["spec_sha256"]
        or rec["identity"] != "G80_F1_fixed_conventional_v2"
    ):
        raise ValueError("F1 source/result revision mismatch")
    src = [
        {
            "id": k,
            "path": SOURCES[k],
            "sha256": hashlib.sha256(v).hexdigest(),
            "description": k + " F1 source; no display-side calculation",
        }
        for k, v in raw.items()
    ]
    rows = []
    for p in cfg["parts"]:
        g = p["geometry"]
        role = p["cad"]["role"]
        box = g.get("bbox_m")
        cat = (
            "motor"
            if p["id"] in ["motor", "motor_tube", "motor_retainer", "retainer_adhesive"]
            else (
                "fin"
                if p["id"] in ["fin_set", "fin_tabs", "fin_internal_bonds", "outer_fin_fillets"]
                else (
                    "thermal"
                    if p["id"] == "mount_external_shield"
                    else (
                        "airframe"
                        if p["id"] in ["nose", "body", "forward_ring", "aft_ring"]
                        else (
                            "recovery"
                            if p["id"]
                            in [
                                "heat_leader",
                                "shock_cord",
                                "parachute",
                                "body_recovery_eye",
                                "nose_anchor_plate",
                                "nose_recovery_eye",
                                "recovery_connectors",
                                "recovery_protection",
                            ]
                            else "avionics"
                        )
                    )
                )
            )
        )
        rows.append(
            {
                "id": p["id"],
                "dimensions": {
                    **{
                        key[:-2] + "_mm": value * 1000
                        for key, value in g.items()
                        if key.endswith("_m") and isinstance(value, (int, float))
                    },
                    **{
                        key: value
                        for key, value in p["cad"]["parameters"].items()
                        if key.endswith("_mm") and isinstance(value, (int, float))
                    },
                },
                "label": p["id"].replace("_", " ").capitalize(),
                "category": cat,
                "function": p["learn"],
                "construction": p["build"]["method"],
                "material": p["material"],
                "mass_g": p["mass_kg"] * 1000,
                "z_start_mm": p["position_m"] * 1000,
                "z_end_mm": (p["position_m"] + g.get("length_m", box[0] if box else 0)) * 1000,
                "inner_radius_mm": g.get("inner_radius_m", 0) * 1000 if not box else None,
                "outer_radius_mm": g.get("radius_m", 0) * 1000 if not box else None,
                "maturity": (
                    "undefined"
                    if p["id"] == "mount_external_shield"
                    else (
                        "envelope"
                        if role in ["purchased_envelope", "soft_stowage", "distributed_budget"]
                        else "concept"
                    )
                ),
                "state": "estimated",
                "source_ids": ["spec"],
                "note": p["cad"]["notes"] + " Not manufacturing-ready CAD.",
            }
        )

    # Display-only radial projection from the same integral-fin CAD parameters.
    fin = next(p for p in cfg["parts"] if p["id"] == "fin_set")
    tab = next(p for p in rows if p["id"] == "fin_tabs")
    tab["outer_radius_mm"] = fin["geometry"]["radius_m"] * 1000
    tab["inner_radius_mm"] = tab["outer_radius_mm"] - fin["cad"]["parameters"]["tab_depth_mm"]

    def connection(
        id: str, label: str, a: str, b: str, kind: str, note: str, state: str = "unavailable"
    ) -> dict[str, Any]:
        return {
            "id": id,
            "label": label,
            "from_id": a,
            "to_id": b,
            "kind": kind,
            "state": state,
            "note": note,
            "source_ids": ["spec", "result", "decision"],
        }

    conn = [
        connection(
            "fin-tab",
            "Fin bending enters integral tab",
            "fin_set",
            "fin_tabs",
            "contact",
            "One cut blank,6.5mm nominal; hot panel screen only. Actual root stiffness and flutter unknown.",
        ),
        connection(
            "tab-mount",
            "Continuous tab/mount fillets",
            "fin_tabs",
            "motor_tube",
            "bond",
            "110mm tab length ×17.9705mm radial depth. Both faces bonded; average shear does not establish peel or body flexibility.",
        ),
        connection(
            "tab-forward",
            "Tab end → forward ring",
            "fin_tabs",
            "forward_ring",
            "bond",
            "Forward tab station1080 overlaps forward ring1075–1088: notch/tab termination undefined. This occupancy finding remains open.",
        ),
        connection(
            "tab-aft",
            "Tab end → aft ring",
            "fin_tabs",
            "aft_ring",
            "bond",
            "Tab110mm ends1190; ring1190–1196.5. End face epoxy gap/tolerance to be defined.",
        ),
        connection(
            "rings-body",
            "Rings bond into continuous body",
            "forward_ring",
            "body",
            "bond",
            "Outer radial gap.205mm nominal, inner.200mm; finished fit/moisture unknown. Paper local and circumferential support not ideal fixed.",
        ),
        connection(
            "recovery-eye",
            "Parachute → main harness",
            "parachute",
            "shock_cord",
            "harness",
            "Deployment/inflation/line-stretch differ. Loop capacity and slack unmeasured.",
        ),
        connection(
            "leader",
            "Harness → heat leader",
            "shock_cord",
            "heat_leader",
            "connector",
            "Two-metre cord plus0.6m leader budgets; actual product/force-extension unspecified.",
        ),
        connection(
            "ring-eye",
            "Heat leader → closed eye → ring",
            "heat_leader",
            "body_recovery_eye",
            "harness",
            "M4 closed-eye/nuts/two14mm washers at radius23mm; installed eye/bend/washer capacity unavailable.",
        ),
        connection(
            "anchor-ring",
            "Eye → reinforced forward ring",
            "body_recovery_eye",
            "forward_ring",
            "fastener",
            "13mm laminated plywood. Historical severe ring strip fails; inflation-only sensitivity is not full recovery acceptance.",
            "failed",
        ),
        connection(
            "nose-branch",
            "Harness → nose eye/plate",
            "shock_cord",
            "nose_recovery_eye",
            "harness",
            "Nose branch carries separated nose/payload inertia, not an arbitrary full-force split.",
        ),
        connection(
            "nose-plate",
            "Eye/plate → nose shoulder",
            "nose_recovery_eye",
            "nose_anchor_plate",
            "fastener",
            "14mm washers and M4 eye/nuts; plate radius30.6, shoulder ID30.8. Bond, positive retention and service order unresolved.",
        ),
        connection(
            "plate-nose",
            "Nose plate → printed shoulder",
            "nose_anchor_plate",
            "nose",
            "bond",
            "6.5mm plate at178–184.5; .2mm radial adhesive gap. No printed-loop capacity credited.",
        ),
        connection(
            "motor-thrust",
            "Motor shoulder → purchased retainer/tube",
            "motor",
            "motor_retainer",
            "thrust",
            "Current SKU78010 shoulder/nozzle and retainer lip drawing unavailable. No internal seat/liner overlap is inherited.",
        ),
        connection(
            "retainer-tube",
            "Independent motor retention",
            "motor_retainer",
            "motor_tube",
            "bond",
            "Purchased sleeve/cap are schematic envelopes. Exact contact, bond, thermal limit and removal envelope unverified. No parachute load assigned to cap.",
        ),
        connection(
            "mount-rings",
            "Mount → rings → body",
            "motor_tube",
            "aft_ring",
            "bond",
            "Motor thrust/reverse load separate from recovery. Fixed joints; motor removed aft through open bore.",
        ),
        connection(
            "guide-body",
            "Guide buttons/backers → body",
            "rail_buttons",
            "body",
            "fastener",
            "Two button station/fastener details remain conceptual;1.5m is usable travel reference, not a confirmed rail.",
        ),
    ]

    conn.append(
        connection(
            "aft-ring-body",
            "Aft ring bond into continuous body",
            "aft_ring",
            "body",
            "bond",
            "Aft ring/body adhesive included in ring_bonds. Nominal radial gap .205mm; installed stiffness, peel and conditioned paper strength not established.",
        )
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

    cases = []
    for record, label in [
        (rec, "F1 corrected geometry"),
        (json.loads(raw["first"]), "F1 first geometry — failed historical screen"),
    ]:
        for c in record["cases"]:
            q = c["guides"]["1.5"]
            cases.append(
                {
                    "id": record["identity"] + "-" + c["id"],
                    "label": label + " / " + c["id"],
                    "total_mass_g": c["mass_kg"] * 1000,
                    "loaded_cg_mm": c["cg_m"] * 1000,
                    "reference_cp_mm": c["cp_m"] * 1000,
                    "margin_cal": c["margin_cal"],
                    "guide_speed_mps": q["speed_mps"],
                    "usable_guide_m": 1.5,
                    "formal_headroom_g": q["formal_headroom_g"],
                    "planning_headroom_g": q["planning_headroom_g"],
                    "source_ids": ["result" if record is rec else "first"],
                    "note": "Full separate50g growth. Adverse also20g aft and12.8mm motor-CG probe. Stability below1.0 fails. Recorded model estimate; historical case never mapped onto current geometry.",
                }
            )
    findings = [
        (
            "admission",
            "Not admitted to detailed CAD",
            "failed",
            "Single correction completed. Static stability remains below1cal; severe ring strip remains failed. No prototype/flight release.",
        ),
        (
            "fin",
            "Installed fin behavior",
            "unavailable",
            "Panel stress3.174MPa; distributed-load tip movement.932mm with an ideal local root, requiring root stiffness2573Nm/rad to retain1mm total. At6.1mm stock thickness panel movement exceeds1mm. No installed flutter evidence.",
        ),
        (
            "recovery",
            "Recovery mechanisms and anchor",
            "failed",
            "Retained20.4/.3/DF3 mean sensitivity not a proven peak. Ring fails it; inflation estimate excludes snatch. No criterion reduced.",
        ),
        (
            "thermal",
            "No compatible F1 temperature result",
            "unavailable",
            "45°C substrate screen and required matrix retained. Thermal allowance has undefined relief/end geometry; no previous failed baffle map transferred.",
        ),
        (
            "motor-fit",
            "Motor/tube/retainer fit",
            "unavailable",
            "Current supplier dimensions/tolerances absent; model retains historical29×128mm/128.2g source hypothesis. Seat/liner removed but compatible replacement not verified.",
        ),
        (
            "packing",
            "Packing and service",
            "estimated",
            "65×47×47mm chute envelope, full cord mass, controller/cell/wiring included. Extraction and arm access not physically verified.",
        ),
        (
            "inertia",
            "Physical full inertia unavailable",
            "unavailable",
            "Diagnostic tensor uses this candidate simplified envelopes. Integral tabs/supports and hardware lack resolved 3D geometry, so CAD-reconciled physical full inertia is unavailable. No flight uses a borrowed tensor.",
        ),
        (
            "cost",
            "Estimated parts use, not checkout total",
            "estimated",
            "Recorded consumed-parts estimate333.95USD includes34USD motor hypothesis. Stock pack sizes, shipping/tax/tools/spares and supplier quotations not verified.",
        ),
    ]
    findings.append(
        (
            "body-supply",
            "One-piece body supply hold",
            "unavailable",
            "No exact1060mm ×66.675OD/64.77ID stock found. LOC762mm is shorter and has different bore/OD. No silent splice or dimension substitution.",
        )
    )
    return {
        "schema_version": "1.0.0",
        "id": "G80_F1_fixed_conventional_v2",
        "label": "G80-F1 dedicated fixed conventional design",
        "status": "Preliminary — not admitted; engineering acceptance open",
        "identity": {
            "candidate_id": "G80-F1",
            "source_identity": rec["identity"],
            "specification_sha256": rec["spec_sha256"],
            "cad_revision": None,
            "frame": "Axial station z=0 at nose tip; positive aft. Units mm and g in display; SI in spec. Body +x points toward nose.",
            "units": "mm, g, m/s, N, calibre",
        },
        "generated_from": src,
        "components": rows,
        "sections": [
            {
                "id": i,
                "label": l,
                "station_mm": z,
                "component_ids": ids,
                "note": n,
                "source_ids": ["spec", "decision"],
            }
            for i, l, z, ids, n in [
                (
                    "nose",
                    "Nose/positive anchor",
                    180,
                    ["nose", "nose_anchor_plate", "nose_recovery_eye"],
                    "Concept joint, positive axial retention unresolved.",
                ),
                (
                    "electronics",
                    "Useful instrumentation",
                    450,
                    [
                        "flight_computer",
                        "battery",
                        "imu",
                        "high_g_accel",
                        "independent_recovery",
                        "recovery_battery",
                    ],
                    "Separate logger and recovery batteries; no control/gimbal hardware.",
                ),
                (
                    "root",
                    "Fixed through-wall fin/motor assembly",
                    1100,
                    ["body", "fin_set", "fin_tabs", "motor_tube", "forward_ring", "aft_ring"],
                    "Integral tabs and fixed rings, no removable aft joint; forward-tab overlap needs local notch detail.",
                ),
                (
                    "motor",
                    "Motor and aft removal",
                    1220,
                    ["motor", "motor_retainer", "motor_tube", "mount_external_shield"],
                    "Exact supplier seat/lip and shield termination unavailable; protect full removal path.",
                ),
            ]
        ],
        "connections": conn,
        "sequences": {
            "assembly": [
                step(
                    "cut",
                    "Cut and dry-fit custom parts",
                    ["body", "fin_set", "forward_ring", "aft_ring"],
                    "Do not manufacture from concept view. Confirm stock, grain, slots and required clearances.",
                ),
                step(
                    "anchor",
                    "Install and inspect forward anchor",
                    ["body_recovery_eye", "forward_ring", "heat_leader"],
                    "Anchor nuts accessible before closing motor/fin bay. Finished proof test required.",
                ),
                step(
                    "fixed-bonds",
                    "Bond mount/rings and through-wall fins",
                    ["motor_tube", "forward_ring", "aft_ring", "fin_set", "body"],
                    "Staged aft-ring installation exposes internal fillets; cure/adhesive and notch details need closure.",
                ),
                step(
                    "instrument",
                    "Install removable instrumentation",
                    ["avionics_sled", "battery", "independent_recovery", "recovery_battery"],
                    "Separate recovery power retained; pins/arming access not qualified.",
                ),
                step(
                    "motor-service",
                    "Remove cap and slide motor aft",
                    ["motor", "motor_retainer"],
                    "Illustrative sequence only; exact purchased mating and nozzle keep-out undefined.",
                ),
            ],
            "recovery": [
                step(
                    "separate",
                    "Separate nose at apogee",
                    ["nose", "body", "shock_cord"],
                    "Illustration, not deployment simulation. Independent electronic apogee primary; motor backup delay unvalidated for F1.",
                ),
                step(
                    "extract",
                    "Extract harness and canopy",
                    ["parachute", "shock_cord", "heat_leader"],
                    "Line slack, extraction friction and stretch unmeasured.",
                ),
                step(
                    "inflate",
                    "Inflate canopy, retain both sections",
                    ["parachute", "body_recovery_eye", "nose_recovery_eye"],
                    "Inflation and line-snatch forces require separate cases; no load-sharing assumption.",
                ),
            ],
        },
        "cases": cases,
        "uncertainties": [
            {
                "id": i,
                "label": l,
                "state": st,
                "note": n,
                "source_ids": ["result", "decision", "spec"],
            }
            for i, l, st, n in findings
        ],
        "cad_manifest": None,
    }
