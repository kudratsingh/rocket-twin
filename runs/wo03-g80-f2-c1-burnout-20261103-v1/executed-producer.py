"""Complete the omitted static burnout sensitivity; no flight simulation."""

from __future__ import annotations

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.vehicle.aero import center_of_pressure
from src.vehicle.mass import mass_properties
from src.vehicle.schema import load_vehicle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/wo03-g80-f2-c1-burnout-20261103-v1"
if __name__ == "__main__":
    OUT.mkdir(exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    start = time.monotonic()
    rows = []
    sources = {}
    for name, path in [
        ("frozen_F2", "configs/vehicle/candidates/g80-f2-ballast.yaml"),
        ("C1_fit_proposal", "configs/vehicle/candidates/g80-f2-c1-fit-proposal.yaml"),
    ]:
        v = load_vehicle(ROOT / path)
        sources[path] = hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        b = mass_properties(v, 1)
        cp = center_of_pressure(v)
        motor = next(p for p in v.parts if p.id == "motor")
        for case, extra, probe in [("nominal", 0, 0), ("adverse", 0.02, 0.0128)]:
            mass = b.mass_kg + 0.05 + extra
            cg = (
                b.mass_kg * b.cg_m
                + (0.05 + extra) * v.airframe["length_m"]
                + motor.resolved_mass_kg * probe
            ) / mass
            rows.append(
                {
                    "identity": v.id,
                    "variant": name,
                    "case": case,
                    "burnout_mass_kg": mass,
                    "burnout_cg_m": cg,
                    "burnout_cp_m": cp,
                    "burnout_margin_cal": (cp - cg) / v.airframe["body_diameter_m"],
                    "growth_kg": 0.05,
                    "extra_aft_kg": extra,
                    "probe_m": probe,
                }
            )
    record = {
        "id": "G80-F2-C1-burnout-v1",
        "sources": sources,
        "cases": rows,
        "criterion_cal": 1,
        "calculated_screen_pass": all(r["burnout_margin_cal"] >= 1 for r in rows),
        "probe_basis": "Retains saved loaded-motor mass times12.8mm moment probe at burnout, conservative versus translating dry motor alone; actual motorCG remains unverified.",
        "scope": "static hypothesis only; no aerodynamic/flight/physical validation",
        "wall_s": time.monotonic() - start,
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (OUT / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    (OUT / "executed-producer.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps(record, indent=2))
