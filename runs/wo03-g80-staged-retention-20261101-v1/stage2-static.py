"""Stage-2 exact-identity static benchmark using the existing RocketPy comparison."""

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.vehicle.aero import center_of_pressure
from src.vehicle.benchmark import evaluate_preliminary
from src.vehicle.mass import mass_properties
from src.vehicle.schema import Vehicle

start = time.monotonic()
root = Path(__file__).resolve().parents[1]
spec = root / "inputs/stage2/resolved-candidate.yaml"
manifest = json.loads((root / "inputs/stage2/stage1-manifest.json").read_text())
r = json.loads((root / "inputs/stage2/stage1-record.json").read_text())
v = Vehicle.model_validate(yaml.safe_load(spec.read_text()))
identity = hashlib.sha256(v.model_dump_json(by_alias=True).encode()).hexdigest()
if (
    identity != r["identity"]
    or identity != manifest["identity"]["resolved_spec_sha256"]
    or len(v.parts) != 72
):
    raise ValueError("Candidate identity mismatch")
result = evaluate_preliminary(v, compare=True)
m = mass_properties(v)
cp = center_of_pressure(v)
motor = next(p for p in v.parts if p.type == "motor")
shift = 0.1 * motor.geometry["length_m"]
if abs(shift - 0.0128) > 1e-12:
    raise ValueError("Motor length sensitivity is not 12.8 mm")
cg = (m.mass_kg * m.cg_m + motor.resolved_mass_kg * shift + 0.05 * 1.212) / (m.mass_kg + 0.05)
sensitivity = {
    "motor_cg_shift_m": shift,
    "basis": "unsourced +10% motor-length sensitivity; not measured or a certification tolerance",
    "growth_kg": 0.05,
    "growth_station_m": 1.212,
    "cg_station_m": cg,
    "margin_cal": (cp - cg) / v.airframe["body_diameter_m"],
}
u = resource.getrusage(resource.RUSAGE_SELF)
record = {
    "candidate_identity": identity,
    "reference": result,
    "motor_cg_sensitivity": sensitivity,
    "cpu_s": u.ru_utime + u.ru_stime,
    "wall_s": time.monotonic() - start,
    "peak_rss_bytes_macos": u.ru_maxrss,
    "acceptance": False,
}
out = root / "build/wo03-g80-stage2-static"
out.mkdir(parents=True, exist_ok=False)
(out / "record.json").write_text(json.dumps(record, indent=2) + "\n")
print(
    json.dumps({"identity": identity, "checks": result["checks"], "sensitivity": sensitivity}),
    flush=True,
)
