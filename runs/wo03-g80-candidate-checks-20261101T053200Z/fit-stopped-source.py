"""Read-only preflight of the exact active G80 tolerance stack."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import resource
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml
from src.analysis.tolerances import analyze_vehicle
from src.vehicle.schema import load_vehicle, vehicle_input_paths

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-g80-fit-candidate.yaml"
OUTPUT = ROOT / "build/wo03-g80-fit-candidate-v1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    started = time.monotonic()
    cfg = yaml.safe_load(CONFIG.read_text())
    vehicle_path = ROOT / cfg["vehicle"]
    sources = {CONFIG, Path(__file__).resolve(), ROOT / cfg["engineering"],
               ROOT / cfg["tolerance_study"], ROOT / cfg["historical_fit_record"],
               ROOT / "src/analysis/tolerances.py"}
    sources.update(p.resolve() for p in vehicle_input_paths(vehicle_path))
    sources.update(p.resolve() for p in (ROOT / "src/cad").glob("*.py"))
    sources.update(p.resolve() for p in (ROOT / "src/vehicle").glob("*.py"))
    before = {str(p.relative_to(ROOT)): sha(p) for p in sorted(sources)}
    vehicle = load_vehicle(vehicle_path)
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    if identity != cfg["expected_resolved_spec_sha256"]:
        raise ValueError(f"Unexpected current resolved G80 identity: {identity}")
    result = analyze_vehicle(vehicle, yaml.safe_load((ROOT / cfg["engineering"]).read_text()),
                             yaml.safe_load((ROOT / cfg["tolerance_study"]).read_text()), "G80")
    after = {str(p.relative_to(ROOT)): sha(p) for p in sorted(sources)}
    if before != after:
        raise ValueError("Input changed during analysis")
    record = {"status": "current_stack_complete_candidate_not_generated", "identity": identity,
              "part_shape_sha256": {p.id: getattr(getattr(p, "cad_mass", None), "shape_sha256", None) for p in vehicle.parts},
              "source_sha256_before": before, "source_sha256_after": after,
              "tolerance_result": result, "elapsed_s": time.monotonic() - started,
              "resource_self": {"user_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime,
                                "system_s": resource.getrusage(resource.RUSAGE_SELF).ru_stime,
                                "peak_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
              "cpu": "one thread requested via process environment; OS affinity not set",
              "engineering_acceptance": False, "flight_ready": False}
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "preflight-record.json").write_text(json.dumps(record, indent=2) + "\n")
    (OUTPUT / "executed-preflight.py").write_bytes(Path(__file__).read_bytes())
    for row in result["stacks"]:
        if row["interface"] in ("aft_shell_inner_radius_to_motor_mount_outer_radius", "motor_mount_inner_radius_to_liner_outer_radius", "liner_inner_radius_to_motor_case_radius"):
            print(json.dumps(row, indent=2))
    print("identity", identity, "elapsed_s", record["elapsed_s"])


def candidate() -> None:
    """Execute the single specified CAD candidate and bounded hand screens."""
    import math
    from OCP.OSD import OSD_Parallel, OSD_ThreadPool
    OSD_Parallel.SetUseOcctThreads_s(True)
    pool = OSD_ThreadPool.DefaultPool_s()
    pool.Init(1)
    if pool.NbThreads() != 1:
        raise RuntimeError("OCCT pool did not select one thread")
    import cadquery as cq
    from src.cad.parts import local_shape, properties
    from src.analysis.engineering import structural
    from src.analysis.motor_support import motor_support
    from src.vehicle.mass import mass_properties
    from src.vehicle.schema import CADMass

    start = time.monotonic()
    cfg = yaml.safe_load(CONFIG.read_text())
    sources = {CONFIG, Path(__file__).resolve(), ROOT / cfg["engineering"], ROOT / cfg["tolerance_study"], ROOT / "configs/studies/wo03-pressure-seal.yaml", ROOT / "src/analysis/motor_support.py", ROOT / "src/analysis/engineering.py"}
    sources.update(p.resolve() for p in vehicle_input_paths(ROOT / cfg["vehicle"]))
    sources.update(p.resolve() for p in (ROOT / "src/cad").glob("*.py"))
    sources.update(p.resolve() for p in (ROOT / "src/vehicle").glob("*.py"))
    before = {str(p.relative_to(ROOT)): sha(p) for p in sorted(sources)}
    base = load_vehicle(ROOT / cfg["vehicle"])
    if hashlib.sha256(base.model_dump_json(by_alias=True).encode()).hexdigest() != cfg["expected_resolved_spec_sha256"]:
        raise ValueError("Unexpected input identity")
    vehicle = base.model_copy(deep=True)
    mount = next(p for p in vehicle.parts if p.id == "motor_mount")
    if mount.material != "plywood" or mount.geometry["radius_m"] != 0.0323 or not mount.cad.parameters.get("trim_outer_cylinder"):
        raise ValueError("Unexpected mount configuration")
    mount.geometry["radius_m"] = 0.0322
    mount.cad_mass = None
    shape = local_shape(mount)
    if not shape.isValid() or len(shape.Solids()) != 1 or shape.Volume() <= 0:
        raise ValueError("Invalid candidate mount shape")
    prop = properties(mount, shape)
    mount.cad_mass = CADMass.model_validate(prop)
    mount.mass_kg = prop["volume_m3"] * 715.0
    # Charge the extra 0.1 mm radial shell for the entire 190 mm length, as
    # an explicit conservative nominal volume allowance, not a bond layout.
    rho = float(yaml.safe_load((ROOT / "configs/studies/wo03-pressure-seal.yaml").read_text())["epoxy_density_kg_m3"])
    delta = math.pi * (0.0323**2 - 0.0322**2) * mount.geometry["length_m"] * rho
    bond = next(p for p in vehicle.parts if p.id == "fin_bonds")
    bond.mass_kg += delta
    study = yaml.safe_load((ROOT / cfg["tolerance_study"]).read_text())
    eng = yaml.safe_load((ROOT / cfg["engineering"]).read_text())
    fit = analyze_vehicle(vehicle, eng, study, "G80_candidate")
    thrust = structural(base, eng)["peak_scaled_thrust_n"]
    support_base = motor_support(base, eng, thrust)
    support_candidate = motor_support(vehicle, eng, thrust)
    def mass(v):
        x = mass_properties(v)
        return {"mass_kg": x.mass_kg, "cg_station_m": x.cg_m,
                "cg_lateral_m": x.cg_lateral_m, "inertia_kg_m2": x.inertia_kg_m2.tolist(),
                "with_50g_kg": x.mass_kg + 0.05}
    after = {str(p.relative_to(ROOT)): sha(p) for p in sorted(sources)}
    if before != after:
        raise ValueError("Input changed during candidate analysis")
    cq.exporters.export(shape, str(OUTPUT / "motor-mount-candidate.step"))
    (OUTPUT / "resolved-candidate.yaml").write_text(yaml.safe_dump(vehicle.model_dump(mode="json", by_alias=True), sort_keys=False))
    record = {"status": "candidate_evaluated_unaccepted", "source_sha256_before": before, "source_sha256_after": after,
              "source_identity": cfg["expected_resolved_spec_sha256"],
              "candidate_identity": hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest(),
              "candidate_mount_properties": prop, "candidate_mount_mass_kg": mount.mass_kg,
              "incremental_bond_allowance_kg": delta,
              "bond_basis": "Full 0.1 mm radial annulus over 190 mm at 1200 kg/m3, nominal extra-gap allowance only; charged to existing fin_bonds CG/inertia envelope, not a specified bond layout or strength.",
              "mount_original_mass_kg": next(p for p in base.parts if p.id == "motor_mount").mass_kg,
              "tolerance_result": fit, "baseline_support": support_base, "candidate_support": support_candidate,
              "baseline_mass": mass(base), "candidate_mass": mass(vehicle),
              "step_sha256": sha(OUTPUT / "motor-mount-candidate.step"),
              "elapsed_s": time.monotonic()-start,
              "resource_self": {"user_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime, "system_s": resource.getrusage(resource.RUSAGE_SELF).ru_stime, "peak_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss},
              "threads": "OCCT default pool size 1; one thread requested by environment; no OS affinity claimed",
              "intersections": "not evaluated", "acceptance": False, "flight_ready": False}
    (OUTPUT / "candidate-record.json").write_text(json.dumps(record, indent=2) + "\n")
    (OUTPUT / "executed-candidate.py").write_bytes(Path(__file__).read_bytes())
    print(json.dumps({k: record[k] for k in ("status", "candidate_identity", "candidate_mount_mass_kg", "incremental_bond_allowance_kg", "baseline_mass", "candidate_mass", "elapsed_s", "resource_self")}, indent=2))


if __name__ == "__main__":
    candidate() if "--candidate" in sys.argv else main()
