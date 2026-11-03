"""Read-only declared annular material overlap; no geometry correction or rerun."""

from __future__ import annotations

import hashlib
import json
import math
import resource
import shutil
import signal
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / "runs/wo03-a1-occupancy-audit-20261102-v1"
    if out.exists():
        raise FileExistsError("Preserve first occupancy audit")
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
    signal.setitimer(signal.ITIMER_REAL, 5)
    start = time.process_time()
    cfg_path = ROOT / "configs/studies/wo03-a1-connections.yaml"
    parts_path = ROOT / "web/public/engineering-workbench/g80-c1.json"
    cfg = yaml.safe_load(cfg_path.read_text())
    parts = json.loads(parts_path.read_text())["parts"]
    seat = cfg["motor"]["seat_insert"]
    results = []
    for pid in ("motor_liner", "motor_radiant_shield"):
        p = next(p for p in parts if p["id"] == pid)
        z = [
            max(seat["z_mm"][0], p["start_mm"]),
            min(seat["z_mm"][1], p["start_mm"] + p["length_mm"]),
        ]
        radius = [max(seat["ri_mm"], p["inner_radius_mm"]), min(seat["ro_mm"], p["radius_mm"])]
        overlap = z[1] > z[0] and radius[1] > radius[0]
        volume = math.pi * (radius[1] ** 2 - radius[0] ** 2) * (z[1] - z[0]) if overlap else 0
        results.append(
            {
                "part_id": pid,
                "source_z_mm": [p["start_mm"], p["start_mm"] + p["length_mm"]],
                "source_r_mm": [p["inner_radius_mm"], p["radius_mm"]],
                "overlap_z_mm": z,
                "overlap_r_mm": radius,
                "intersection_mm3": volume,
                "declared_coaxial_material_overlap": overlap,
            }
        )
    paths = [
        cfg_path,
        parts_path,
        ROOT / "runs/wo03-a1-connections-20261102-v1/record.json",
        Path(__file__),
    ]
    record = {
        "id": "A1_retained_material_occupancy_audit_v1",
        "status": "failed_declared_seat_liner_foil_overlap",
        "input_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths
        },
        "seat": seat,
        "intersections": results,
        "geometry_basis": "Declared concentric annular material dimensions; not a full CAD or motion check",
        "geometry_mass_or_thermal_correction_executed": False,
        "original_A1_results_rerun": False,
        "decision": "Hold_A1. Do_not_trim_liner_or_shift_motor_automatically; exact_supplier_thrust_interface_and_heat_barrier_termination_need_one_explicit_followup.",
        "cpu_s": time.process_time() - start,
        "cpu_limit_s": 1,
        "wall_limit_s": 5,
    }
    out.mkdir(parents=True)
    shutil.copyfile(Path(__file__), out / "executed-script.py")
    (out / "record.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(json.dumps(record["intersections"], indent=2))


if __name__ == "__main__":
    main()
