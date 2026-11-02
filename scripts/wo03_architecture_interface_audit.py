"""One read-only retained-interface audit, not a third construction variant."""

from __future__ import annotations

import hashlib
import json
import resource
import shutil
import signal
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/wo03-architecture-interface-audit-20261102-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
    signal.setitimer(signal.ITIMER_REAL, 5)
    start = time.process_time()
    if OUT.exists():
        raise FileExistsError("Preserve the previous audit; no automatic rerun")
    paths = [
        "configs/studies/wo03-architecture-space-mass.yaml",
        "runs/wo03-architecture-space-mass-20261102-v1/record.json",
        "web/public/engineering-workbench/g80-c1.json",
        "configs/studies/wo03-c2-sandwich-socket.yaml",
        "scripts/wo03_architecture_interface_audit.py",
    ]
    cfg = yaml.safe_load((ROOT / paths[0]).read_text())
    record = json.loads((ROOT / paths[1]).read_text())
    source = json.loads((ROOT / paths[2]).read_text())
    previous = yaml.safe_load((ROOT / paths[3]).read_text())
    coupler = next(p for p in source["parts"] if p["id"] == "interface_coupler")
    stop = next(p for p in source["parts"] if p["id"] == "joint_stop")
    bore = cfg["common"]["outer_can"]["r_inner_outer_mm"][0]
    tolerance = previous["clearance"]["radial_tolerance_each_mm"]
    required = previous["clearance"]["minimum_mm"]
    nominal = bore - coupler["radius_mm"]
    minimum = nominal - 2 * tolerance
    maximum_od_for_bound = 2 * (bore - 2 * tolerance - required)
    OUT.mkdir(parents=True)
    shutil.copy2(Path(__file__), OUT / "executed-script.py")
    result = {
        "id": "retained_upper_joint_A_B_read_only_audit",
        "status": "calculated_cold_fit_screen_failed_no_geometry_changed",
        "input_sha256": {p: sha(ROOT / p) for p in paths},
        "arrangements": record["selected_before_execution"],
        "source_coupler_id": coupler["id"],
        "source_coupler_maturity": coupler["geometry_maturity"],
        "nominal_coupler_od_mm": 2 * coupler["radius_mm"],
        "proposed_bore_diameter_mm": 2 * bore,
        "nominal_radial_gap_mm": nominal,
        "screening_radial_tolerance_each_mm": tolerance,
        "minimum_radial_gap_mm": minimum,
        "required_radial_gap_mm": required,
        "deficit_mm": required - minimum,
        "maximum_nominal_coupler_od_for_same_bore_and_bounds_mm": maximum_od_for_bound,
        "hot_fit_and_actual_supplier_or_manufacturing_tolerances": None,
        "joint_stop_envelope": {
            "radius_mm": stop["radius_mm"],
            "start_mm": stop["start_mm"],
            "length_mm": stop["length_mm"],
            "actual_CAD_interference": None,
            "note": "Source envelope includes stops/keys; cannot treat it as a complete solid collision result.",
        },
        "decision": "Hold_A_B_admission. Specify_a_compatible_shared_upper_mating_interface_before_next_CAD;_63p8mm_is_a_dimensional_bound_not_an_adopted_or_strength_qualified_coupler. No_third_variant_or_new_mass_flight_run.",
        "engineering_or_geometry_changed": False,
        "previous_stopped_calculation_repeated": False,
        "cpu_s": time.process_time() - start,
        "cpu_limit_s": 1,
        "wall_limit_s": 5,
    }
    (OUT / "record.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
