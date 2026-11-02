"""One CP-only independent RocketPy check; no complete-vehicle or flight claim."""

import hashlib
import json
import os
import resource
import signal
import time
from importlib.metadata import version
from pathlib import Path

resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
signal.alarm(20)
for key in ["OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
    os.environ[key] = "1"
out = Path(__file__).resolve().parent
root = out.parents[1]
os.environ["MPLCONFIGDIR"] = str(root / ".cache/matplotlib")
start, cpu = time.monotonic(), time.process_time()

import yaml
from rocketpy import Function, Rocket

cfg_path = root / "configs/studies/wo03-g80-mass-balance-revision.yaml"
cfg = yaml.safe_load(cfg_path.read_text())
source_path = root / cfg["source_spec"]
source = yaml.safe_load(source_path.read_text())
record_path = out / "record.json"
record = json.loads(record_path.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
inputs = {str(p.relative_to(root)): sha(p) for p in [cfg_path, source_path, record_path]}
assert not source["aero"]["passive_stubs"]["enabled"]
rocket = Rocket(
    radius=source["airframe"]["body_diameter_m"] / 2,
    mass=1,
    inertia=(0, 0, 0),
    power_off_drag=Function(0),
    power_on_drag=Function(0),
    center_of_mass_without_motor=0.5,
    coordinate_system_orientation="nose_to_tail",
)
for p in source["parts"]:
    g = p["geometry"]
    if p["type"] == "nose_cone":
        rocket.add_nose(length=g["length_m"], kind=g["shape"], position=p["position_m"], base_radius=g["radius_m"])
    elif p["type"] == "transition":
        rocket.add_tail(top_radius=g["fore_radius_m"], bottom_radius=g["radius_m"], length=g["length_m"], position=p["position_m"])
g = cfg["fin_option"]["proposed_geometry"]
rocket.add_trapezoidal_fins(
    n=cfg["fin_option"]["count"], root_chord=g["root_mm"] / 1000,
    tip_chord=g["tip_mm"] / 1000, span=g["span_mm"] / 1000,
    position=g["station_mm"] / 1000, sweep_length=g["sweep_mm"] / 1000,
)
cp = float(rocket.cp_position(0))
case = next(x for x in record["mass_scenario_results"] if x["id"] == cfg["selected_preliminary_scenario"])
own = case["cp_mm"] / 1000
limit = source["airframe"]["length_m"] * 0.03
result = {
    "status": "CP_only_comparison_complete_no_flight_or_mass_benchmark",
    "budget": {"cases": 1, "cpu_s": 20, "wall_s": 20, "threads": 1},
    "rocketpy_version": version("rocketpy"),
    "source_nose_transition_and_proposed_fin_inputs": g,
    "input_sha256": inputs,
    "calculated_CP_m": own,
    "rocketpy_CP_at_Mach0_m": cp,
    "absolute_difference_m": abs(own - cp),
    "existing_WO01_CP_limit_m": limit,
    "CP_comparison_passed": abs(own - cp) <= limit,
    "complete_vehicle_mass_CG_inertia_aerodynamic_validity_and_flight_validated": False,
    "note": "Reference mass/inertia/CG are placeholders because they do not affect CP. No reference static-margin or full-vehicle pass follows.",
    "cpu_s_including_RocketPy_import": time.process_time() - cpu,
    "wall_s_including_RocketPy_import": time.monotonic() - start,
}
assert inputs == {str(p.relative_to(root)): sha(p) for p in [cfg_path, source_path, record_path]}
(out / "cp-reference.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
