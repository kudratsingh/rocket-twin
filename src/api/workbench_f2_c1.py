"""Read-only F2-C1 connection-study projection; no analysis/CAD/flight on GET."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SOURCES = {
    "spec": "configs/vehicle/candidates/g80-f2-c1-fit-proposal.yaml",
    "definition": "runs/wo03-g80-f2-c1-definition-20261103-v1/record.json",
    "numeric_record": "runs/wo03-g80-f2-c1-load-path-20261103-v2/record.json",
    "numeric_spec": "runs/wo03-g80-f2-c1-load-path-20261103-v2/specification.yaml",
    "frozen_f2": "configs/vehicle/candidates/g80-f2-ballast.yaml",
    "method": "runs/wo03-g80-f2-c1-method-20261103-v1/record.json",
    "boundary": "runs/wo03-g80-f2-c1-boundary-20261103-v1/record.json",
    "node_stop": "runs/wo03-g80-f2-c1-boundary-20261103-v1/node-budget-stop.json",
    "burnout": "runs/wo03-g80-f2-c1-burnout-20261103-v1/record.json",
    "field_export": "runs/wo03-g80-f2-c1-field-export-20261103-v1/metadata.json",
    "decision": "docs/wo03-g80-f2-c1-decision.md",
    "suppliers": "docs/wo03-g80-f2-c1-supplier-evidence.md",
    "mechanisms": "docs/wo03-f2-c1-recovery-mechanisms.md",
}


def build_f2_c1(root: Path = ROOT) -> dict[str, Any]:
    raw = {k: (root / p).read_bytes() for k, p in SOURCES.items()}
    r = json.loads(raw["definition"])
    cfg = yaml.safe_load(raw["spec"])
    method = json.loads(raw["method"])
    boundary = json.loads(raw["boundary"])
    stop = json.loads(raw["node_stop"])
    field = json.loads(raw["field_export"])
    burnout = json.loads(raw["burnout"])
    sha = hashlib.sha256(raw["spec"]).hexdigest()
    if burnout["sources"][SOURCES["spec"]] != sha:
        raise ValueError("Burnout source identity mismatch")
    burnout_cases = {(c["variant"], c["case"]): c for c in burnout["cases"]}
    cases = [
        {
            **c,
            **{
                k: v
                for k, v in burnout_cases[(c["variant"], c["case"])].items()
                if k.startswith("burnout_")
            },
        }
        for c in r["cases"]
    ]
    if sha != r["proposal_spec_sha256"] or cfg["id"] != r["identity"] or r["adopted"]:
        raise ValueError("F2-C1 proposal/record identity mismatch or unexpected adoption")
    if (
        hashlib.sha256(raw["numeric_record"]).hexdigest() != r["reuse"]["record_sha256"]
        or hashlib.sha256(raw["numeric_spec"]).hexdigest() != r["reuse"]["source_spec_sha256"]
        or not r["reuse"]["checked_numeric_equivalence"]
    ):
        raise ValueError("F2-C1 numeric reuse provenance mismatch")
    if hashlib.sha256(raw["frozen_f2"]).hexdigest() != r["source_spec_sha256"]:
        raise ValueError("Frozen F2 changed")
    if (
        field["active_vehicle_compatible"]
        or field["installed_strength_accepted"]
        or boundary["method_refinement_pass"]
    ):
        raise ValueError("Unexpected field/strength status; update explicit study contract first")
    parts: list[dict[str, Any]] = []
    for p in cfg["parts"]:
        dimensions: dict[str, Any] = {}
        for k, v in p["geometry"].items():
            if k.endswith("_m") and isinstance(v, (int, float)):
                dimensions[k[:-2].replace("_", " ") + " (mm)"] = v * 1000
            elif k == "bbox_m":
                dimensions["box axial/transverse dimensions (mm)"] = [x * 1000 for x in v]
            else:
                dimensions[k.replace("_", " ")] = v
        parts.append(
            {
                "id": p["id"],
                "label": p["id"].replace("_", " ").capitalize(),
                "function": p["learn"],
                "material": p["material"],
                "mass_g": p.get("mass_kg", 0) * 1000 if p.get("mass_kg") is not None else None,
                "z_mm": p["position_m"] * 1000,
                "dimensions": dimensions,
                "parameters": p["cad"].get("parameters", {}),
                "state": "estimated",
                "notes": p["build"]["notes"]
                + " Source allocation/concept only; installed strength/adoption remains open.",
            }
        )

    def node(id: str, label: str, part_ids: list[str], note: str) -> dict[str, Any]:
        return {
            "id": id,
            "label": label,
            "part_ids": part_ids,
            "note": note,
            "state": "unavailable",
        }

    nodes = [
        node(
            "harness",
            "Canopy and harness",
            ["parachute", "shock_cord", "heat_leader"],
            "Inflation, relative snatch and severe arrest are distinct; finished harness unknown.",
        ),
        node(
            "eyes",
            "Paired finished eyes",
            ["body_recovery_eye"],
            "18g paired budget; stock envelope/closure/finished capacity unavailable.",
        ),
        node(
            "ring",
            "Forward ring",
            ["forward_ring"],
            "12.2mm laminated ring bends/shears; installed supports unresolved.",
        ),
        node(
            "outer",
            "Outer bond → fore paper",
            ["body", "upper_body", "body_splice", "ring_bonds"],
            "Mean axial bound only; angular response/peel/local wall strength unresolved.",
        ),
        node(
            "inner",
            "Inner bond → motor tube",
            ["motor_tube", "ring_bonds"],
            "Finite tube/joint support; no rigid-ground or confirmed motor contact.",
        ),
        node(
            "tabs",
            "Blind-notch bonds → fin tabs",
            ["fin_tabs", "fin_internal_bonds", "aft_ring"],
            "Ring pull opens floor gap; axial recovery transfer is bonded tension/side shear.",
        ),
        node(
            "nose",
            "Separate retained nose branch",
            ["nose_recovery_eye", "nose_anchor_plate", "avionics_sled"],
            "Eye/annulus/perimeter/printed shoulder and equipment retention need proof.",
        ),
        node(
            "motor",
            "Independent motor support",
            ["motor", "motor_retainer"],
            "Exact shoulder/nozzle/cap/mount thermal and removal envelope held.",
        ),
        node(
            "fins",
            "Fin/root loads",
            ["fin_set", "root_gussets"],
            "Existing8.83Nm factored starting screen; installed root and flutter remain open.",
        ),
    ]
    defs = [
        (
            "harness",
            "eyes",
            "Body bridle",
            "Unequal and single-eye cases; no equal-sharing capacity credit.",
        ),
        (
            "eyes",
            "ring",
            "Aft washer/nut contact",
            "Provisional14OD/4.5ID footprint, not selected finished hardware.",
        ),
        (
            "ring",
            "outer",
            "Perimeter bond",
            "Force allocation not the component fixture spring reaction.",
        ),
        ("ring", "inner", "Inner bore bond", "Paper tube plus distributed bonded tab load route."),
        (
            "ring",
            "tabs",
            "Floor tension / side shear",
            "No positive bearing across a gap that opens under this pull.",
        ),
        (
            "harness",
            "nose",
            "Independent nose branch",
            "All nose equipment retained with nose; separate anchor demand.",
        ),
        (
            "motor",
            "inner",
            "Thrust / reverse retention",
            "Distinct load cases; exact contact unavailable.",
        ),
        ("fins", "tabs", "Bending and twist", "Do not apply the existing design factor twice."),
    ]
    edges = [
        {"from": a, "to": b, "label": c, "note": d, "state": "unavailable"} for a, b, c, d in defs
    ]

    def finding(id: str, label: str, state: str, note: str, part_ids: list[str]) -> dict[str, Any]:
        return {"id": id, "label": label, "state": state, "note": note, "part_ids": part_ids}

    findings = [
        finding(
            "notch",
            "Recovery notch is a bonded pull connection",
            "unavailable",
            "Noseward ring motion increases floor-to-tab gap. Tension/shear/peel and finite installed stiffness need verification.",
            ["forward_ring", "fin_tabs"],
        ),
        finding(
            "fit",
            "Conditional cut/stock fit proposal",
            "estimated",
            "Seven declared minima exceed0.1mm only under unverified incoming/conditioning windows. No manufacturing guarantee or adoption.",
            ["forward_ring", "aft_ring", "nose_anchor_plate", "fin_tabs"],
        ),
        finding(
            "paper",
            "Fore-paper adverse axial bound exceeds screen",
            "failed",
            "Frozen F2 mean1.700–2.135MPa versus estimated2MPa. Unknown distributed mass and bending mean this is a conditional adverse bound, not physical test failure.",
            ["body", "upper_body", "ring_bonds"],
        ),
        finding(
            "washer",
            "Finished eye/contact capacity unavailable",
            "unavailable",
            "Frozen mean contact pressure7.144/10.206MPa at70percent/single-eye. Generic wood screen is not a supplier bearing allowable.",
            ["body_recovery_eye", "forward_ring"],
        ),
        finding(
            "motor",
            "Motor/retainer exact contact unavailable",
            "unavailable",
            "Manufacturer instructions establish class/sequence; current78010/12912/19002 controlled mating dimensions remain missing.",
            ["motor", "motor_retainer", "motor_tube"],
        ),
        finding(
            "mesh",
            "Fine mesh stopped before solver",
            "failed",
            "Boundary-only fine mesh139953nodes exceeds100000cap. Two valid solves exist; required3-grid convergence is unavailable.",
            ["forward_ring"],
        ),
        finding(
            "shield",
            "Thermal sector layout unavailable",
            "unavailable",
            "10g reserved sector is not a resolved full annulus. Inherited annular display overlaps tube and cannot define heat occupancy.",
            ["mount_external_shield", "motor_tube"],
        ),
        finding(
            "recovery",
            "Opening mechanisms remain unresolved",
            "estimated",
            "Required severe screen retained; smaller free-body/drag comparisons do not replace it or validate peaks.",
            ["parachute", "shock_cord", "body_recovery_eye"],
        ),
    ]
    return {
        "schema_version": "1.0.0",
        "id": cfg["id"],
        "status": r["status"],
        "identity": {
            "candidate_id": "G80-F2-C1",
            "source_identity": cfg["id"],
            "specification_sha256": sha,
            "cad_revision": None,
        },
        "sources": [
            {"id": k, "path": SOURCES[k], "sha256": hashlib.sha256(v).hexdigest()}
            for k, v in raw.items()
        ],
        "parts": parts,
        "cases": cases,
        "fits": r["fits"],
        "audit": r["audit"],
        "numerical": {
            "completed_grids": len(method["reports"]),
            "required_grids": 3,
            "status": "stopped_node_budget",
            "fine_nodes": stop["nodes"],
            "node_limit": stop["limit"],
            "installed_strength_accepted": False,
        },
        "field_export": {
            "active_compatible": False,
            "three_grid_convergence": False,
            "metadata_path": SOURCES["field_export"],
            "status": field["status"],
        },
        "graph": {"nodes": nodes, "edges": edges},
        "findings": findings,
        "units": "mm, g, N, MPa, m/s,calibre",
        "coordinate_frame": "station0 nose tip;positive aft; schematic local sections, not fullCAD",
    }
