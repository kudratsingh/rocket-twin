"""Finish candidate descriptions without regenerating or editing CAD geometry."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import yaml

checkout = Path(__file__).resolve().parent
stage = checkout.parent
sys.path.insert(0, str(checkout))
from src.vehicle.mass import mass_properties
from src.vehicle.schema import Vehicle

source = stage / "stage1-result"
dest = stage / "stage1-result-metadata-final-v2"
if dest.exists():
    raise FileExistsError(dest)
raw = yaml.safe_load((source / "resolved-candidate.yaml").read_text())
before = copy.deepcopy(raw)
parts = {p["id"]: p for p in raw["parts"]}
texts = {
    "motor_mount": (
        "Modified plywood frame carries the fixed motor support through forward rings and longitudinal rails. The original aft ring contribution and block material are removed; rail bonds and load sharing remain unqualified.",
        "configs/studies/wo03-g80-retention-geometry.yaml",
    ),
    "service_keeper": (
        "Machined G11 keeper captures the M3 nuts against rotation and stows them before the shell is assembled. Its integral pads and M2 closure may carry load; this is not a qualified strength path.",
        "configs/studies/wo03-g80-captive-retention-plan.yaml",
    ),
    "service_bridge": (
        "Slotted G11 bridge receives reverse retention loads through the three M3 nut and washer bearings and transfers them toward the rails through six tabs. Bearing, bending, tab bonds and hot properties remain unqualified.",
        "configs/studies/wo03-g80-mount-fabrication.yaml",
    ),
    "retention_locking_materials_reserve": (
        "One gram of estimated retention locking or assembly material is reserved separately. Its precise mechanism, location, mass and qualification are not selected.",
        "configs/studies/wo03-g80-retention-integration.yaml",
    ),
}
urls = {
    "m3_screw": "https://www.accu.co.uk/metric-cap-head-screws/642043-SSCF-M3-35-A2",
    "m3_nut": "https://www.accu.co.uk/hexagon-nuts/7888-HPN-M3-A2",
    "m3_washer": "https://www.accu.co.uk/metric-flat-washers/406770-HPW-M3-V2-A2",
    "m2_screw": "https://www.accu.co.uk/metric-cap-head-screws/152179-SSCF-M2-10-A2-BL",
    "m2_nut": "https://www.accu.co.uk/hexagon-nuts/7884-HPN-M2-A2",
}
for i in range(3):
    texts[f"service_guide_{i}"] = (
        f"Plywood guide {i+1} locates an aft M3 screw while preserving the source fin and rail clearances. The guide is not credited as a primary tensile retention joint.",
        "configs/studies/wo03-g80-retention-geometry.yaml",
    )
for kind, url in urls.items():
    for i in range(3):
        purpose = {
            "m3_screw": "Through screw transfers the retainer load in tension to the captured nut and bridge.",
            "m3_nut": "Captured nut bears on its washer and bridge to transfer reverse retention load.",
            "m3_washer": "Washer spreads captured-nut bearing onto the G11 bridge.",
            "m2_screw": "M2 closure screw holds the keeper and bridge together for nut stowage.",
            "m2_nut": "M2 closure nut retains the keeper closure screw.",
        }[kind]
        texts[f"service_{kind}_{i}"] = (
            f"{purpose} Source nominal envelope and supplier-average mass are estimates; engagement, grade and service qualification remain open.",
            url,
        )
for pid, (description, citation) in texts.items():
    row = parts[pid]
    row["learn"] = description
    row["cite"] = citation
    if pid.startswith(("service_m3_", "service_m2_")):
        row["build"][
            "notes"
        ] = "A2 stainless supplier nominal mass; simplified unthreaded CAD envelope. Orderability, grade, engagement and preload are unverified."
    elif pid.startswith("service_guide_") or pid == "motor_mount":
        row["build"][
            "notes"
        ] = "Cut plywood, nominal 715 kg/m³; source-identical unmeasured geometry. Bonding, joints and manufacture are unqualified."
    elif pid in ("service_keeper", "service_bridge"):
        row["build"][
            "notes"
        ] = "Machined G11, estimated 1850 kg/m³; source-identical geometry. Directional and hot properties, contact and joints are unqualified."
    else:
        row["build"][
            "notes"
        ] = "One gram estimated reserve only; not a selected or qualified locking mechanism."
for pid in texts:
    if pid != "motor_mount":
        parts[pid]["build"][
            "notes"
        ] += " Cost USD 0 is an unpriced schema placeholder, not a purchase quote."

old = {p["id"]: p for p in before["parts"]}
new = {p["id"]: p for p in raw["parts"]}
for pid, current in new.items():
    for key in set(old[pid]) | set(current):
        if key not in ("learn", "cite", "build") and old[pid].get(key) != current.get(key):
            raise ValueError(f"Non-metadata changed: {pid}/{key}")
    if any(
        old[pid]["build"].get(k) != current["build"].get(k)
        for k in ("method", "generator", "cost_usd")
    ):
        raise ValueError("Manufacturing field changed")
v = Vehicle.model_validate(raw)
identity = hashlib.sha256(v.model_dump_json(by_alias=True).encode()).hexdigest()
previous = json.loads((source / "record.json").read_text())
m = mass_properties(v)
if (
    abs(m.mass_kg - previous["states"][0]["mass_kg"]) > 1e-12
    or abs(m.cg_m - previous["states"][0]["cg_station_m"]) > 1e-12
    or not np.allclose(m.inertia_kg_m2, previous["states"][0]["inertia_kg_m2"], atol=1e-14, rtol=0)
):
    raise ValueError("Metadata altered mass properties")
shutil.copytree(source, dest)
(dest / "resolved-candidate.yaml").write_text(
    yaml.safe_dump(v.model_dump(mode="json", by_alias=True), sort_keys=False)
)
manifest = json.loads((dest / "manifest.json").read_text())
manifest["identity"]["resolved_spec_sha256"] = identity
for row in manifest["parts"]:
    part = parts[row["id"]]
    row["learn"] = part["learn"]
    row["notes"] = part["cad"]["notes"]
(dest / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
(dest / "parts.md").write_text(
    "# "
    + v.name
    + "\n\nPreliminary CAD; no structural, thermal or flight release.\n\n"
    + "\n\n".join(
        "## "
        + p.id
        + "\n\n"
        + p.learn
        + "\n\nMass basis: "
        + p.cad.mass_basis
        + "; "
        + p.build.notes
        for p in v.parts
    )
    + "\n"
)
for folder in ("parts",):
    for original in (source / folder).iterdir():
        target = dest / folder / original.name
        if (
            hashlib.sha256(original.read_bytes()).digest()
            != hashlib.sha256(target.read_bytes()).digest()
        ):
            raise ValueError("Export changed during metadata copy")
for name in ("assembly.step", "assembly.glb"):
    if (
        hashlib.sha256((source / name).read_bytes()).digest()
        != hashlib.sha256((dest / name).read_bytes()).digest()
    ):
        raise ValueError("Assembly export changed")
record = copy.deepcopy(previous)
record.update(
    identity=identity,
    metadata_only_reconciliation=True,
    prior_geometry_identity=previous["identity"],
    prior_record_sha256=hashlib.sha256((source / "record.json").read_bytes()).hexdigest(),
    metadata_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    description_and_source_updated_ids=sorted(texts),
    geometry_and_part_exports_unchanged=True,
    schema_revalidated=True,
    native_cad_rerun=False,
)
(dest / "record.json").write_text(json.dumps(record, indent=2) + "\n")
print(
    json.dumps(
        {
            "status": "metadata_final_no_new_CAD",
            "identity": identity,
            "mass_kg": m.mass_kg,
            "parts": len(v.parts),
            "updated": len(texts),
        }
    )
)
