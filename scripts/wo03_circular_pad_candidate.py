"""Explicitly regenerate a candidate with exact circular mica-pad boundaries.

Historical source caches belong to their original CAD code. This creates a new
resolved copy, rebuilds every CAD cache, recalculates volume-owned masses and
checks that no non-pad geometry changed. Active specifications are not edited.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_thermal_matrix import mass_record
from src.cad.parts import local_shape, properties
from src.vehicle.cad_contract import digest
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import CADMass, Vehicle

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runs/wo03-multilayer-shield-20261031T022026246942Z/record.json"


def main() -> int:
    started = time.perf_counter()
    source = json.loads(SOURCE.read_bytes())
    candidate = SOURCE.parent / "resolved-candidate.json"
    raw = json.loads(candidate.read_bytes())
    # Only the new copy loses its incompatible caches; all geometry and supplied
    # masses retain source ownership. Old caches/records are preserved verbatim.
    old_parts = {p["id"]: p for p in json.loads(candidate.read_bytes())["parts"]}
    changed = []
    for p in raw["parts"]:
        p["cad_mass"] = None
        if p.get("cad", {}).get("generator") == "sector_pads":
            p["cad"]["parameters"]["circular_boundaries"] = True
            changed.append(p["id"])
    vehicle = Vehicle.model_validate(raw)
    paths = [
        SOURCE,
        candidate,
        Path(__file__),
        ROOT / "src/vehicle/schema.py",
        ROOT / "src/vehicle/materials.py",
        ROOT / "src/vehicle/mass.py",
        ROOT / "src/vehicle/cad_contract.py",
        *sorted((ROOT / "src/cad").glob("*.py")),
    ]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    run_id = "wo03-circular-pad-candidate-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "runs" / run_id
    folder.mkdir()
    for name in hashes:
        target = folder / "source-snapshot" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    shapes = {}
    rows = []
    for part in vehicle.parts:
        if part.cad is None:
            raise ValueError(f"Part lacks CAD: {part.id}")
        shape = local_shape(part)
        if not shape.isValid() or shape.Volume() <= 0:
            raise ValueError(f"Invalid corrected candidate solid: {part.id}")
        props = properties(part, shape)
        part.cad_mass = CADMass.model_validate(props)
        if part.cad.mass_basis == "volume_density":
            density = part.density_kg_m3 or DENSITY_KG_M3[part.material]
            part.mass_kg = props["volume_m3"] * density
            part.density_kg_m3 = None
        part.cg_offset_m = max(0, -props["cg_local_body_m"][0])
        old = old_parts[part.id]
        old_volume = old["cad_mass"]["volume_m3"]
        volume_delta = (props["volume_m3"] - old_volume) * 1e9
        if part.id not in changed and abs(volume_delta) > 1e-5:
            raise ValueError(f"Unexpected non-pad geometry change {part.id}: {volume_delta}mm3")
        rows.append(
            {
                "part_id": part.id,
                "circular_pad_correction": part.id in changed,
                "volume_change_mm3": volume_delta,
                "mass_before_kg": old.get("mass_kg"),
                "mass_after_kg": part.resolved_mass_kg,
                "shape_sha256": props["shape_sha256"],
            }
        )
        shapes[part.id] = shape.translate(
            (
                1000 * part.lateral_offset_m[0],
                -1000 * part.lateral_offset_m[1],
                1000 * part.position_m,
            )
        )
    checks = []
    for part in vehicle.parts:
        if part.id not in changed:
            continue
        if not part.id.startswith("shield_spacer_"):
            continue
        other = part.id.removeprefix("shield_spacer_").rsplit("_", 1)[0]
        for name in (part.parent, other):
            if name not in shapes:
                raise ValueError("Missing physical adjacent foil identity")
            volume = float(shapes[part.id].intersect(shapes[name]).Volume())
            checks.append({"pad": part.id, "adjacent": name, "overlap_mm3": volume})
            if volume > 1e-7:
                raise ValueError(f"Corrected pad still overlaps adjacent foil: {checks[-1]}")
    resolved = folder / "resolved-candidate.json"
    resolved.write_text(vehicle.model_dump_json(by_alias=True, indent=2) + "\n")
    Vehicle.model_validate_json(resolved.read_bytes())
    record = {
        "run_id": run_id,
        "configuration_id": vehicle.id,
        "candidate_identity": hashlib.sha256(
            vehicle.model_dump_json(by_alias=True).encode()
        ).hexdigest(),
        "source_candidate_record": str(SOURCE.relative_to(ROOT)),
        "source_candidate_identity": source["candidate_identity"],
        "source_cad_revision_sha256": source["cad_revision_sha256"],
        "cad_revision_sha256": hashlib.sha256(
            b"".join(p.read_bytes() for p in sorted((ROOT / "src/cad").glob("*.py")))
        ).hexdigest(),
        "part_shape_sha256": {
            p.id: digest(p.geometry, p.cad.model_dump() if p.cad else None) for p in vehicle.parts
        },
        "resolved_candidate": str(resolved.relative_to(ROOT)),
        "resolved_candidate_sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
        "all_cad_caches_regenerated": True,
        "changed_geometry_part_ids": changed,
        "part_reconciliation": rows,
        "adjacent_foil_checks": checks,
        "mass_before": source["geometry"]["candidate_mass_cg_inertia"],
        "mass_after": mass_record(vehicle),
        "source_sha256": hashes,
        "inputs_unchanged": all(
            hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in hashes.items()
        ),
        "elapsed_s": time.perf_counter() - started,
        "cost_usd": 0,
        "active_adoption": False,
        "thermal_results_compatible": False,
        "engineering_acceptance_passed": False,
        "flight_ready": False,
    }
    (folder / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(folder / "record.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
