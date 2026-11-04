"""Prepare separate, unaccepted FP1/FR1 records for the read-only workbench."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml"
SOURCE_SHA = "811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660"
FP = "docs/studies/rp1-fin-precedent-replacement/screen-record.json"
FR = "runs/wo03-rp1-fin-root-20261104-v1/record.json"
JOINT = "runs/wo03-rp1-fin-root-20261104-v1/joint-supplement.json"


def fingerprint(path: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}


def build() -> dict:
    if fingerprint(SOURCE)["sha256"] != SOURCE_SHA:
        raise ValueError("Frozen AD1 changed; do not relabel a different vehicle")
    inputs = [
        SOURCE,
        FP,
        FR,
        JOINT,
        "configs/studies/rp1-fin-precedent-replacement.yaml",
        "configs/studies/rp1-fin-root-replacement.yaml",
    ]
    before = {path: fingerprint(path)["sha256"] for path in inputs}
    fp, fr, joint = [json.loads((ROOT / p).read_text()) for p in [FP, FR, JOINT]]
    if fp["adopted"] or fr["adopted"] or fp["replacement_admitted"]:
        raise ValueError("This comparison supports unaccepted records only")
    if fp["source_sha256"] != SOURCE_SHA or joint["source_sha256"] != fingerprint(FR)["sha256"]:
        raise ValueError("Study source identity mismatch")
    if (
        fp["id"] != "G80-F2-RP1-FP1-carbon-faced-plywood-screen-v1"
        or fr["identity"] != "RP1-FR1-monolithic-carbon-v1"
    ):
        raise ValueError("Unexpected fin study identity")
    fps = fp["component_screens"][-1]
    finite = fr["structural_sensitivity"][0]["finite_roots"]
    studies = []
    descriptions = [
        (
            fp["id"],
            "FP1: carbon-faced plywood",
            FP,
            fps["screen_total_tip_mm"],
            fps["unverified_attachment_reserve_mm"],
            -fp["replacement_ledger"]["net_change_g"],
            "Conditional nominal component point; material sensitivities fail. Additional attachment reserve is an input, not measured movement.",
            "5 mm plywood with carbon faces over the inner 45 mm and through the tabs; perfect composite action unverified.",
            "Skin bonds, core shear and skin-end peeling/delamination remain unqualified.",
            "Motor-side boundary is fixed in the saved component model. No complete tube/body/ring/fillet displacement is established.",
        ),
        (
            fr["identity"],
            "FR1: solid carbon/epoxy",
            FR,
            min(c["total_tip_mm"] for c in finite),
            None,
            -fr["net_mass_change_from_AD1_g"],
            "Best evaluated finite-support sensitivity fails 1 mm; complete installed displacement remains unavailable because the extra aft restraint is unqualified.",
            "Nominal 3.175 mm Rock West 204-11 integral fin/tab; supplier CLT references are not finished hot flexural allowables.",
            f"Actual body-root one-face mean demand {joint['body_single_face_mean_shear_Pa'] / 1e6:.3f} MPa exceeds the retained 1 MPa estimate; sharing/peel unknown.",
            "Tube/body support values are sensitivities. Aft-end restraint is not credited as a rigid support.",
        ),
    ]
    for (
        identity,
        label,
        path,
        displacement,
        reserve,
        credit,
        note,
        material,
        bond,
        support,
    ) in descriptions:
        nodes = [
            {"id": "panel", "label": "Fin panel", "note": material, "status": "unqualified"},
            {
                "id": "tab",
                "label": "Integral tab",
                "note": "Passes through a body slot to the motor tube. Its deformation and material action must be included.",
                "status": "unaccepted",
            },
            {
                "id": "bond",
                "label": "Material / root bonds",
                "note": bond,
                "status": "unknown / failed screen",
            },
            {
                "id": "mount",
                "label": "Motor tube",
                "note": "Fillets and tube deformation form one parallel force route; not fixed ground.",
                "status": "unqualified",
            },
            {"id": "body", "label": "Outer paper body", "note": support, "status": "unqualified"},
            {
                "id": "ring",
                "label": "Rings / aft end",
                "note": "Forward ring is ahead of the tab. The aft 0.4 mm adhesive gap has no direct butt stop or qualified capacity/stiffness.",
                "status": "unknown",
            },
        ]
        studies.append(
            {
                "id": identity,
                "label": label,
                "status": "UNACCEPTED — not adopted",
                "adopted": False,
                "installed_accepted": False,
                "source": fingerprint(path),
                "maturity": "Analytical proposal and concept relationships; no accepted complete CAD or spatial result.",
                "displacement": {
                    "reported_mm": displacement,
                    "attachment_budget_mm": reserve,
                    "limit_mm": 1,
                    "note": note,
                },
                "mass": {
                    "conditional_credit_g": credit,
                    "note": "Proposed alternative replacement ledger only. Removed brace function has not been accepted; do not add the two studies or claim installed savings.",
                },
                "nodes": nodes,
                "edges": [
                    {"from": "panel", "to": "tab", "label": "integral fin/root"},
                    {"from": "panel", "to": "bond", "label": "skin/root joint evidence"},
                    {"from": "tab", "to": "mount", "label": "internal fillets"},
                    {"from": "tab", "to": "body", "label": "external root fillets"},
                    {"from": "tab", "to": "ring", "label": "aft-end adhesive"},
                    {"from": "mount", "to": "ring", "label": "bore bonds"},
                    {"from": "ring", "to": "body", "label": "perimeter bonds"},
                ],
                "unknowns": [
                    material,
                    bond,
                    support,
                    "Finished 55 g/68 g harness mass is unknown; probes are not measured uncertainty bounds.",
                    "Thermal, recovery, installed flutter, physical build and flight gates remain open.",
                ],
                "sources": [
                    fingerprint(path),
                    fingerprint(SOURCE),
                    fingerprint(
                        "configs/studies/rp1-fin-precedent-replacement.yaml"
                        if path == FP
                        else "configs/studies/rp1-fin-root-replacement.yaml"
                    ),
                ],
            }
        )
    if {path: fingerprint(path)["sha256"] for path in inputs} != before:
        raise ValueError("Source changed during export")
    return {
        "schema_version": 1,
        "id": "G80-F2-RP1-FP1-FR1-comparison-v1",
        "status": "Preliminary engineering evidence — both studies unaccepted; WO-03 open",
        "source_configuration": {"id": "G80-F2-RP1-AD1-definition-v2", **fingerprint(SOURCE)},
        "load_definition": {
            "required_moment_Nm": fr["load_trace"]["retained_M_Nm"],
            "proposed_moment_Nm": fr["load_trace"]["direct_40kPa_5deg_DF3_M_Nm"],
            "proposal_adopted": False,
            "note": "8.83 N·m with consistent 331.125 N remains enforced, DF3 already applied once. 2.905 N·m is the current-planform historical 40 kPa/5° formula, not a validated operating envelope or an adopted lower gate.",
        },
        "studies": studies,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "web/public/engineering-workbench/rp1-studies.json"
    )
    args = parser.parse_args()
    value = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temp = args.output.with_suffix(".tmp")
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temp.replace(args.output)
    print(f"Prepared {args.output}: two separate unaccepted study records; no physics run")


if __name__ == "__main__":
    main()
