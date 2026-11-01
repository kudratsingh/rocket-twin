"""Isolated G80 mount and recovery proposal; no active configuration is modified."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
from scripts.wo03_recovery_packaging import NEW_PART_IDS, copy_sources, state_stats
from src.vehicle.schema import Part, Vehicle, load_vehicle

CONFIG = Path("configs/studies/wo03-g80-integrated-candidate.yaml")
OUT = Path("build/wo03-g80-integrated-candidate-v1")
BUDGET = "incremental_mount_gap_epoxy_upper_budget"
MASS_ADJUSTED = NEW_PART_IDS | {"independent_recovery", "recovery_battery", "recovery_power_switch"}
CHANGED = NEW_PART_IDS | {
    "body_upper",
    "independent_recovery",
    "recovery_battery",
    "recovery_power_switch",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    cfg = yaml.safe_load(CONFIG.read_text())
    mount = load_vehicle(cfg["mount_candidate"])
    identity = hashlib.sha256(mount.model_dump_json(by_alias=True).encode()).hexdigest()
    if identity != cfg["mount_identity"] or len(mount.parts) != 43:
        raise ValueError("Mount candidate identity or part count mismatch")
    source = mount.model_dump(mode="json", by_alias=True)
    study = yaml.safe_load(Path(cfg["recovery_study"]).read_text())
    recovery = yaml.safe_load(Path(cfg["recovery_source"]).read_text())
    raw = copy_sources(source, study)
    a = {p["id"]: p for p in raw["parts"] if p["id"] != BUDGET}
    b = {p["id"]: p for p in recovery["parts"]}
    if a.keys() != b.keys():
        raise ValueError(f"Recovery part IDs differ: {a.keys() ^ b.keys()}")
    differences = {}
    for key in sorted(a):
        left, right = copy.deepcopy(a[key]), copy.deepcopy(b[key])
        left.pop("cad_mass", None)
        right.pop("cad_mass", None)
        left = Part.model_validate(left).model_dump(mode="json", by_alias=True)
        right = Part.model_validate(right).model_dump(mode="json", by_alias=True)
        if key == "motor_mount":
            left["geometry"] = copy.deepcopy(right["geometry"])
            left["mass_kg"] = right["mass_kg"]
        if key in MASS_ADJUSTED:
            left["mass_kg"] = right["mass_kg"]
        fields = sorted(k for k in left.keys() | right.keys() if left.get(k) != right.get(k))
        if fields:
            differences[key] = fields
    if differences:
        raise ValueError(f"Unexpected recovery field differences: {differences}")
    for key in set(raw) | set(recovery):
        left, right = raw.get(key), recovery.get(key)
        if key == "netlist":
            left = [{k: v for k, v in row.items() if v is not None} for row in left]
            right = [{k: v for k, v in row.items() if v is not None} for row in right]
        if key != "parts" and left != right:
            raise ValueError(f"Unexpected top-level difference: {key}")
    for row in raw["parts"]:
        if row["id"] in MASS_ADJUSTED:
            row["mass_kg"] = b[row["id"]]["mass_kg"]
        if row["id"] in CHANGED:
            row.pop("cad_mass", None)
    vehicle = Vehicle.model_validate(raw)
    return cfg, study, mount, vehicle


def child():
    from OCP.OSD import OSD_Parallel, OSD_ThreadPool

    from src.cad.assembly import export_vehicle, rigid_intersections
    from src.cad.parts import local_shape, properties
    from src.vehicle.schema import CADMass

    started = time.monotonic()
    cfg, study, mount, vehicle = prepare()
    OSD_Parallel.SetUseOcctThreads_s(True)
    pool = OSD_ThreadPool.DefaultPool_s()
    pool.Init(1)
    if pool.NbThreads() != 1:
        raise RuntimeError("OCCT pool did not select one thread")
    paths = [
        CONFIG,
        Path(__file__),
        Path(cfg["mount_candidate"]),
        Path(cfg["recovery_source"]),
        Path(cfg["recovery_study"]),
        Path("scripts/wo03_recovery_packaging.py"),
    ]
    paths += sorted(Path("src/cad").glob("*.py")) + sorted(Path("src/vehicle").glob("*.py"))
    hashes = {str(p): digest(p) for p in paths}
    for part in vehicle.parts:
        if part.id in CHANGED:
            shape = local_shape(part)
            if not shape.isValid() or shape.Volume() <= 0:
                raise ValueError(f"Invalid shape {part.id}")
            part.cad_mass = CADMass.model_validate(properties(part, shape))
    # Revalidate all regenerated caches through the normal schema.
    vehicle = Vehicle.model_validate(vehicle.model_dump(mode="json", by_alias=True))
    expected = cfg["expected_recovery_mass_delta_g"]
    from src.vehicle.mass import mass_properties

    delta = (mass_properties(vehicle).mass_kg - mass_properties(mount).mass_kg) * 1000
    if abs(delta - expected) > 0.002:
        raise ValueError(f"Recovery mass increment inconsistent: {delta} g")
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "resolved-candidate.yaml").write_text(
        yaml.safe_dump(vehicle.model_dump(mode="json", by_alias=True), sort_keys=False)
    )
    manifest, solids = export_vehicle(vehicle, OUT, True)
    collisions = rigid_intersections(vehicle, solids, moving_ids=CHANGED)
    allowed = {tuple(sorted(x)) for x in study["verification"]["allowed_contact_pairs"]}
    named = [c for c in collisions if tuple(sorted((c["a"], c["b"]))) in allowed]
    unexplained = [c for c in collisions if tuple(sorted((c["a"], c["b"]))) not in allowed]
    after = {str(p): digest(p) for p in paths}
    if hashes != after:
        raise ValueError("Input changed during execution")
    rec = {
        "status": "candidate_only_unaccepted",
        "mount_identity": cfg["mount_identity"],
        "integrated_identity": identity,
        "source_sha256_before": hashes,
        "source_sha256_after": after,
        "recovery_increment_g": delta,
        "parts": [{"id": p.id, "mass_kg": p.resolved_mass_kg} for p in vehicle.parts],
        "states": state_stats(vehicle),
        "mount_only_states": state_stats(mount),
        "allowed_contacts": study["verification"]["allowed_contact_pairs"],
        "named_contact_intersections": named,
        "unexplained_intersections": unexplained,
        "valid_solids": {r["id"]: r["valid_solid"] for r in manifest["parts"]},
        "annular_budget": "full 4.620 g separate conservative mass upper bound; no bond/contact claim",
        "recovery_geometry": "nominal rigid checks only; no wire, connector or pressure keepout qualification",
        "acceptance": False,
        "flight_ready": False,
        "elapsed_s": time.monotonic() - started,
        "cpu_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime
        + resource.getrusage(resource.RUSAGE_SELF).ru_stime,
    }
    (OUT / "record.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(
        json.dumps(
            {
                "identity": identity,
                "delta_g": delta,
                "unexplained": unexplained,
                "elapsed_s": rec["elapsed_s"],
                "cpu_s": rec["cpu_s"],
            }
        )
    )


def main():
    if sys.argv[1:] == ["--child"]:
        child()
        return
    cfg, _, _, vehicle = prepare()
    print(
        f"Whitelist preflight passed; {len(vehicle.parts)} candidate parts. Starting one child.",
        flush=True,
    )
    OUT.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            k: "1"
            for k in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        }
    )
    try:
        result = subprocess.run(
            [sys.executable, __file__, "--child"],
            env=env,
            timeout=cfg["wall_seconds_per_child"],
            check=False,
        )
        status = {"child_returncode": result.returncode, "timeout": False}
    except subprocess.TimeoutExpired:
        status = {"child_returncode": None, "timeout": True}
    (OUT / "execution-status.json").write_text(json.dumps(status, indent=2) + "\n")
    if status["timeout"] or status["child_returncode"] != 0:
        raise SystemExit("Child failed or hit cap; stop without retry")


if __name__ == "__main__":
    main()
