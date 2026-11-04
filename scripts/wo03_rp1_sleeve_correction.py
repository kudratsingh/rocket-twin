"""One geometry-only AD1 correction; reuse saved guide and strip calculations."""

from __future__ import annotations

import copy
import hashlib
import json
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
import yaml

from src.vehicle.reference import compare_rocketpy
from src.vehicle.schema import Vehicle, load_vehicle

ROOT = Path(__file__).resolve().parents[1]
PRIOR = ROOT / "runs/wo03-rp1-attachment-definition-20261103-v1/record.json"
SOURCE = ROOT / "configs/vehicle/candidates/g80-f2-rp1-ad1.yaml"
STUDY = ROOT / "configs/studies/rp1-attachment-definition.yaml"
TARGET = ROOT / "configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml"
FINAL_STUDY = ROOT / "configs/studies/rp1-attachment-definition-v2.yaml"
OUT = ROOT / "runs/wo03-rp1-attachment-definition-20261103-v2"


def main() -> None:
    start = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
    if OUT.exists() or TARGET.exists() or FINAL_STUDY.exists():
        raise ValueError("One geometry correction; preserve previous outputs")
    prior = json.loads(PRIOR.read_text())
    if (
        prior["sources"][str(SOURCE.relative_to(ROOT))]
        != hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    ):
        raise ValueError("Changed executed AD1 source")
    before = load_vehicle(SOURCE)
    d = before.model_dump(by_alias=True, exclude_none=True)
    d["parts"][0]["parent"] = None
    d["id"] = "G80-F2-RP1-AD1-definition-v2"
    sleeve = next(x for x in d["parts"] if x["id"] == "ad1_cord_sleeve")
    sleeve["position_m"] = 0.98
    sleeve[
        "learn"
    ] += " Geometrycorrection:980–1060mm ahead of ring; folded8mm sleeve must NOT occupy4.5mmnotch. Barecordonroundedsealedpassage remains thermally/chafeunqualified."
    sleeve["build"]["notes"] = sleeve["learn"]
    sleeve["engineering"]["function"] = sleeve["learn"]
    candidate = Vehicle.model_validate(d)
    TARGET.write_text(yaml.safe_dump(d, sort_keys=False))
    study = yaml.safe_load(STUDY.read_text())
    study["id"] = d["id"]
    study["route"]["heat_abrasion_sleeve"]["axial_station_mm"] = [980, 1060]
    study["route"]["heat_abrasion_sleeve"][
        "notch_occupancy"
    ] = "None: terminate ahead of ring; original through-notch sleeve envelope rejected."
    study["budget"]["correction_cycles_used"] = 1
    FINAL_STUDY.write_text(yaml.safe_dump(study, sort_keys=False))
    record = copy.deepcopy(prior)
    record["identity"] = d["id"]
    # Only2g moves52.2mm forward. External geometry, masses, drag/friction and
    # thrust assumptions unchanged: the scalar guide model is mass-only here.
    delta_moment_kg_m = 0.002 * (1.020 - 1.0722)
    for case in record["cases"]:
        mass = case["total_mass_g"] / 1000
        change_mm = 1000 * delta_moment_kg_m / mass
        case["cg_mm"] += change_mm
        case["margin_cal"] -= change_mm / 66.802
        case["aft_stowage_margin_cal"] -= change_mm / 66.802
        dry_change = 1000 * delta_moment_kg_m / (mass - candidate.motor.propellant_mass_kg)
        case["burnout_cg_mm"] += dry_change
        case["burnout_margin_cal"] -= dry_change / 66.802
    record["ledger"] = [
        {
            "id": x.id,
            "mass_g": x.resolved_mass_kg * 1000,
            "cg_mm": x.cg_station_m * 1000,
            "cost_usd": x.build.cost_usd,
        }
        for x in candidate.parts
    ]
    record["rocketpy_static_reference"] = compare_rocketpy(candidate)
    record["reused_outputs"] = {
        "source": str(PRIOR.relative_to(ROOT)),
        "sha256": hashlib.sha256(PRIOR.read_bytes()).hexdigest(),
        "fields": ["guide_mps", "fin", "method_check", "recovery_connections", "slot_clearance"],
        "reason": "Masses/external shape and all structural inputs unchanged; only nonstructural sleeve stowage location corrected. No repeated guide or fin runs.",
    }
    record["geometry_correction"] = {
        "rejected_sleeve_mm": [1032.2, 1112.2],
        "selected_sleeve_mm": [980, 1060],
        "reason": "Folded8mm sleeve cannot be credited through4.5mm passage",
        "mass_change_g": 0,
        "delta_first_moment_kg_m": delta_moment_kg_m,
        "thermal_acceptance": "open; bare rounded passage and new sleeve end remain in required thermal/chafe tests",
    }
    record["sources"] = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [SOURCE, TARGET, STUDY, FINAL_STUDY, PRIOR, Path(__file__)]
    }
    record["resources"] = {
        "cpu_seconds": time.process_time(),
        "wall_seconds": time.monotonic() - start,
        "thread_env_limit": 1,
        "cpu_affinity_verified": False,
        "new_continuum_solver_runs": 0,
        "guide_cases_reexecuted": 0,
        "strip_cases_reexecuted": 0,
        "correction_cycles_used": 1,
    }
    OUT.mkdir()
    (OUT / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    (OUT / "executed-producer.py").write_bytes(Path(__file__).read_bytes())
    (OUT / "specification.yaml").write_bytes(TARGET.read_bytes())
    print(
        json.dumps(
            {
                "identity": d["id"],
                "resources": record["resources"],
                "geometry_correction": record["geometry_correction"],
            }
        )
    )


if __name__ == "__main__":
    main()
