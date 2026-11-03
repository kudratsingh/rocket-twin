"""Reconcile explicit proposal CAD/learn metadata, reusing unchanged numeric results."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml

from src.vehicle.aero import center_of_pressure
from src.vehicle.mass import mass_properties
from src.vehicle.schema import Vehicle

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runs/wo03-g80-f2-c1-load-path-20261103-v2"
TARGET = ROOT / "runs/wo03-g80-f2-c1-definition-20261103-v1"
CANDIDATE = ROOT / "configs/vehicle/candidates/g80-f2-c1-fit-proposal.yaml"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    if TARGET.exists():
        raise ValueError("preserve existing definition record")
    before = Vehicle.model_validate(yaml.safe_load((SOURCE / "specification.yaml").read_text()))
    d = before.model_dump(by_alias=True, exclude_none=True)
    d["parts"][0]["parent"] = None
    d["id"] = "G80-F2-C1-fit-proposal-v2"
    by = {p["id"]: p for p in d["parts"]}
    for pid in ["forward_ring", "aft_ring", "nose_anchor_plate"]:
        p = by[pid]
        p["cad"]["parameters"].update(
            proposal_adopted=False, complete_geometry_available=False, diameter_tolerance_m=0.00005
        )
        p["cad"][
            "notes"
        ] += " C1 candidate only; dimensions do not constitute a generated/accepted assembly."
    by["forward_ring"]["cad"]["generator"] = "unadmitted_f2_c1_notched_ring"
    by["forward_ring"]["cad"]["parameters"].update(
        notch_width_m=0.0066,
        notch_depth_m=0.0074,
        front_web_m=0.0048,
        notch_angles_deg=[0, 120, 240],
        eye_hole_diameter_m=0.0045,
        eye_radius_m=0.023,
        eye_angles_deg=[30, 210],
    )
    by["forward_ring"]["build"]["notes"] = by["forward_ring"]["build"]["notes"].replace(
        "6.5mmwide", "6.6mmwide"
    )
    by["forward_ring"]["engineering"]["tolerances_mm"].update(
        notch_width=0.05, notch_floor_axial=0.05
    )
    by["fin_tabs"]["cad"]["parameters"].update(
        inner_flat_m=0.01595,
        front_station_m=1.0802,
        aft_station_m=1.1896,
        angles_deg=[0, 120, 240],
        complete_geometry_available=False,
        proposal_adopted=False,
    )
    by["fin_tabs"]["cad"]["generator"] = "unadmitted_f2_c1_integral_tabs"
    by["body_recovery_eye"]["cad"]["parameters"].update(
        pair_radius_m=0.023,
        pair_angles_deg=[30, 210],
        finished_part_verified=False,
        display_box_is_not_pair_geometry=True,
    )
    by["body_recovery_eye"]["cad"][
        "notes"
    ] += " Pair-position intent is explicit; the inherited single box is only a budget envelope, not actual two-eye CAD."
    after = Vehicle.model_validate(d)
    a, b = mass_properties(before), mass_properties(after)
    if (
        a.mass_kg != b.mass_kg
        or a.cg_m != b.cg_m
        or (a.inertia_kg_m2 != b.inertia_kg_m2).any()
        or center_of_pressure(before) != center_of_pressure(after)
    ):
        raise ValueError("numeric inputs changed; cannot reuse results")
    record = copy.deepcopy(json.loads((SOURCE / "record.json").read_text()))
    record["identity"] = after.id
    for row in record["cases"]:
        if row["variant"] == "C1_fit_proposal":
            row["identity"] = after.id
    TARGET.mkdir()
    CANDIDATE.write_text(yaml.safe_dump(d, sort_keys=False))
    (TARGET / "specification.yaml").write_bytes(CANDIDATE.read_bytes())
    record["proposal_spec_sha256"] = digest(CANDIDATE)
    record["audit"]["source_variant"] = "frozen_F2"
    record["reuse"] = {
        "record_path": str((SOURCE / "record.json").relative_to(ROOT)),
        "record_sha256": digest(SOURCE / "record.json"),
        "source_spec_sha256": digest(SOURCE / "specification.yaml"),
        "reason": "explicit CAD parameters/generator-unavailable/learn metadata only; exact mass,CG,diagnostic inertia andCP unchanged; no guide/FEA/flight recomputed",
        "checked_numeric_equivalence": True,
        "producer_sha256": digest(Path(__file__)),
    }
    record["status"] = (
        "explicit candidate definition; conditional fit screens only; installed joints/motor/thermal/flutter unresolved; NOT adopted"
    )
    (TARGET / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    (TARGET / "executed-producer.py").write_bytes(Path(__file__).read_bytes())
    print(after.id, record["proposal_spec_sha256"], "reused same numeric cases without rerun")
