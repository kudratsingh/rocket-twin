"""Read-only preflight of the exact active G80 tolerance stack."""

from __future__ import annotations

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

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
    sources = {
        CONFIG,
        Path(__file__).resolve(),
        ROOT / cfg["engineering"],
        ROOT / cfg["tolerance_study"],
        ROOT / cfg["historical_fit_record"],
        ROOT / "src/analysis/tolerances.py",
    }
    sources.update(p.resolve() for p in vehicle_input_paths(vehicle_path))
    sources.update(p.resolve() for p in (ROOT / "src/cad").glob("*.py"))
    sources.update(p.resolve() for p in (ROOT / "src/vehicle").glob("*.py"))
    before = {str(p.relative_to(ROOT)): sha(p) for p in sorted(sources)}
    vehicle = load_vehicle(vehicle_path)
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    if identity != cfg["expected_resolved_spec_sha256"]:
        raise ValueError(f"Unexpected current resolved G80 identity: {identity}")
    result = analyze_vehicle(
        vehicle,
        yaml.safe_load((ROOT / cfg["engineering"]).read_text()),
        yaml.safe_load((ROOT / cfg["tolerance_study"]).read_text()),
        "G80",
    )
    after = {str(p.relative_to(ROOT)): sha(p) for p in sorted(sources)}
    if before != after:
        raise ValueError("Input changed during analysis")
    record = {
        "status": "current_stack_complete_candidate_not_generated",
        "identity": identity,
        "part_shape_sha256": {
            p.id: getattr(getattr(p, "cad_mass", None), "shape_sha256", None) for p in vehicle.parts
        },
        "source_sha256_before": before,
        "source_sha256_after": after,
        "tolerance_result": result,
        "elapsed_s": time.monotonic() - started,
        "resource_self": {
            "user_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime,
            "system_s": resource.getrusage(resource.RUSAGE_SELF).ru_stime,
            "peak_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "cpu": "one thread requested via process environment; OS affinity not set",
        "engineering_acceptance": False,
        "flight_ready": False,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "preflight-record.json").write_text(json.dumps(record, indent=2) + "\n")
    (OUTPUT / "executed-preflight.py").write_bytes(Path(__file__).read_bytes())
    for row in result["stacks"]:
        if row["interface"] in (
            "aft_shell_inner_radius_to_motor_mount_outer_radius",
            "motor_mount_inner_radius_to_liner_outer_radius",
            "liner_inner_radius_to_motor_case_radius",
        ):
            print(json.dumps(row, indent=2))
    print("identity", identity, "elapsed_s", record["elapsed_s"])


def prepare():
    """Validate the complete non-CAD input path before starting the CAD child."""
    import math

    from src.analysis.engineering import structural
    from src.analysis.motor_support import motor_support
    from src.vehicle.materials import DENSITY_KG_M3
    from src.vehicle.schema import Part

    cfg = yaml.safe_load(CONFIG.read_text())
    assert isinstance(cfg, dict)
    for key in ("vehicle", "engineering", "tolerance_study", "expected_resolved_spec_sha256"):
        assert isinstance(cfg[key], str)
    paths = [ROOT / cfg[k] for k in ("vehicle", "engineering", "tolerance_study")]
    density_path = ROOT / "configs/studies/wo03-pressure-seal.yaml"
    pressure = yaml.safe_load(density_path.read_text())
    rho = float(pressure["material_estimates"]["epoxy_density_kg_m3"])
    assert rho == 1200 and DENSITY_KG_M3["plywood"] == 715
    study = yaml.safe_load(paths[2].read_text())
    eng = yaml.safe_load(paths[1].read_text())
    base = load_vehicle(paths[0])
    assert (
        hashlib.sha256(base.model_dump_json(by_alias=True).encode()).hexdigest()
        == cfg["expected_resolved_spec_sha256"]
    )
    assert len(base.parts) == 42 and base.design.mass_allowance_kg == 0.05
    mount = next(p for p in base.parts if p.id == "motor_mount")
    assert mount.material == "plywood" and mount.geometry["radius_m"] == 0.0323
    assert mount.cad and mount.cad.parameters["trim_outer_cylinder"] is True
    assert mount.geometry["length_m"] == 0.19000000000000017
    manifest = json.loads((ROOT / "build/modular-performance-v1/manifest.json").read_text())
    assert manifest["identity"]["resolved_spec_sha256"] == cfg["expected_resolved_spec_sha256"]
    for name in ("motor_mount", "aft_shell", "fin_set", "retention"):
        assert (ROOT / f"build/modular-performance-v1/parts/{name}.step").is_file()
        part = next(p for p in base.parts if p.id == name)
        assert part.cad_mass.shape_sha256 == manifest["identity"]["part_shape_sha256"][name]
    candidate = base.model_copy(deep=True)
    changed = next(p for p in candidate.parts if p.id == "motor_mount")
    changed.geometry["radius_m"] = 0.0322
    changed.cad_mass = None
    delta = math.pi * (0.0323**2 - 0.0322**2) * mount.geometry["length_m"] * rho
    budget = next(p for p in candidate.parts if p.id == "fin_bonds").model_dump(
        mode="json", by_alias=True
    )
    budget.update(
        id="incremental_mount_gap_epoxy_upper_budget",
        position_m=mount.position_m,
        lateral_offset_m=[0.0, 0.0],
        geometry={
            "length_m": mount.geometry["length_m"],
            "radius_m": 0.0323,
            "inner_radius_m": 0.0322,
        },
        mass_kg=delta,
        density_kg_m3=None,
        cg_offset_m=mount.geometry["length_m"] / 2,
        cad_mass=None,
        learn="Upper budget for additional mount annulus adhesive; actual occupancy and attachment remain unverified.",
    )
    budget["cad"].update(
        generator="tube",
        parameters={},
        mass_basis="supplied_or_estimated",
        role="distributed_budget",
        notes="Incremental full annulus upper mass budget, not a proposed full bonded interface.",
    )
    candidate.parts.append(Part.model_validate(budget))
    fit = analyze_vehicle(candidate, eng, study, "G80_candidate")
    row = next(
        v
        for v in fit["stacks"]
        if v["interface"] == "aft_shell_inner_radius_to_motor_mount_outer_radius"
    )
    assert row["status"] == "pass" and abs(row["minimum_mm"] - 0.12102) < 1e-8
    thrust = structural(base, eng)["peak_scaled_thrust_n"]
    before_support = motor_support(base, eng, thrust)
    after_support = motor_support(candidate, eng, thrust)
    assert (
        before_support["screens"]["rails"]["channel_net_section"]
        and after_support["screens"]["rails"]["channel_net_section"]
    )
    return cfg, base, candidate, fit, thrust, before_support, after_support, delta


def candidate():
    """Run one input-corrected 32.2 mm CAD reconstruction, with no retry."""
    import cadquery as cq
    from OCP.OSD import OSD_Parallel, OSD_ThreadPool

    from src.cad.parts import local_shape, properties
    from src.vehicle.mass import mass_properties
    from src.vehicle.materials import DENSITY_KG_M3
    from src.vehicle.schema import CADMass

    start = time.monotonic()
    cfg, base, v, fit, thrust, support_old, support_new, delta = prepare()
    OSD_Parallel.SetUseOcctThreads_s(True)
    pool = OSD_ThreadPool.DefaultPool_s()
    pool.Init(1)
    if pool.NbThreads() != 1:
        raise RuntimeError("OCCT pool did not select one thread")
    inputs = {
        CONFIG,
        Path(__file__).resolve(),
        ROOT / cfg["engineering"],
        ROOT / cfg["tolerance_study"],
        ROOT / "configs/studies/wo03-pressure-seal.yaml",
        ROOT / "src/analysis/motor_support.py",
        ROOT / "src/analysis/engineering.py",
        ROOT / "build/modular-performance-v1/manifest.json",
        ROOT / base.motor.curve,
    }
    inputs.update(p.resolve() for p in vehicle_input_paths(ROOT / cfg["vehicle"]))
    inputs.update(p.resolve() for p in (ROOT / "src/cad").glob("*.py"))
    inputs.update(p.resolve() for p in (ROOT / "src/vehicle").glob("*.py"))
    inputs.update(
        ROOT / f"build/modular-performance-v1/parts/{name}.step"
        for name in ("motor_mount", "aft_shell", "fin_set", "retention")
    )
    before = {str(p.relative_to(ROOT)): sha(p) for p in sorted(inputs)}
    mount = next(p for p in v.parts if p.id == "motor_mount")
    shape = local_shape(mount)
    if not shape.isValid() or len(shape.Solids()) != 1 or shape.Volume() <= 0:
        raise ValueError("Invalid candidate mount shape")
    original = cq.importers.importStep(
        str(ROOT / "build/modular-performance-v1/parts/motor_mount.step")
    ).val()
    original_mount = next(p for p in base.parts if p.id == "motor_mount")
    if abs(original.Volume() * 1e-9 - original_mount.cad_mass.volume_m3) > 1e-10:
        raise ValueError("Saved original mount volume does not match cached source")
    outside_mm3 = shape.cut(original).Volume()
    if outside_mm3 > 1e-4:
        raise ValueError("Candidate not a geometric subset of saved original")
    prop = properties(mount, shape)
    mount.cad_mass = CADMass.model_validate(prop)
    mount.mass_kg = prop["volume_m3"] * DENSITY_KG_M3["plywood"]
    placed = shape.translate(
        (
            mount.lateral_offset_m[0] * 1000,
            -mount.lateral_offset_m[1] * 1000,
            mount.position_m * 1000,
        )
    )
    intersections = {}
    for name in ("aft_shell", "fin_set", "retention"):
        part = next(p for p in base.parts if p.id == name)
        other = (
            cq.importers.importStep(str(ROOT / f"build/modular-performance-v1/parts/{name}.step"))
            .val()
            .translate(
                (
                    part.lateral_offset_m[0] * 1000,
                    -part.lateral_offset_m[1] * 1000,
                    part.position_m * 1000,
                )
            )
        )
        intersections[name] = placed.intersect(other).Volume()

    def mass(vehicle):
        m = mass_properties(vehicle)
        return {
            "mass_kg": m.mass_kg,
            "cg_station_m": m.cg_m,
            "cg_lateral_m": m.cg_lateral_m,
            "inertia_kg_m2": m.inertia_kg_m2.tolist(),
            "with_50g_kg": m.mass_kg + 0.05,
        }

    zero = v.model_copy(deep=True)
    zero.parts = [p for p in zero.parts if p.id != "incremental_mount_gap_epoxy_upper_budget"]
    after = {str(p.relative_to(ROOT)): sha(p) for p in sorted(inputs)}
    if before != after:
        raise ValueError("Input changed during candidate analysis")
    cq.exporters.export(shape, str(OUTPUT / "motor-mount-candidate-io-replan.step"))
    (OUTPUT / "resolved-candidate-io-replan.yaml").write_text(
        yaml.safe_dump(v.model_dump(mode="json", by_alias=True), sort_keys=False)
    )
    record = {
        "status": "candidate_evaluated_unaccepted",
        "source_sha256_before": before,
        "source_sha256_after": after,
        "original_failed_attempt": "candidate-failure.json",
        "reconstruction": "One authorized input-only replan; no valid prior STEP saved",
        "source_identity": cfg["expected_resolved_spec_sha256"],
        "candidate_identity": hashlib.sha256(v.model_dump_json(by_alias=True).encode()).hexdigest(),
        "original_mount_volume_mm3": original.Volume(),
        "candidate_mount_volume_mm3": shape.Volume(),
        "candidate_outside_original_mm3": outside_mm3,
        "candidate_mount_properties": prop,
        "candidate_mount_mass_kg": mount.mass_kg,
        "original_mount_mass_kg": original_mount.mass_kg,
        "incremental_bond_allowance_kg": delta,
        "bond_basis": "43rd part: full 0.1 mm annular increment over 190 mm, 1200 kg/m3; upper budget, not actual occupancy or bond stiffness.",
        "tolerance_result": fit,
        "thrust_n": thrust,
        "baseline_support": support_old,
        "candidate_support": support_new,
        "baseline_mass": mass(base),
        "candidate_zero_added_bond_mass": mass(zero),
        "candidate_upper_bond_budget_mass": mass(v),
        "intersections_mm3": intersections,
        "step_sha256": sha(OUTPUT / "motor-mount-candidate-io-replan.step"),
        "elapsed_s": time.monotonic() - start,
        "resource_self": {
            "user_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime,
            "system_s": resource.getrusage(resource.RUSAGE_SELF).ru_stime,
            "peak_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "threads": "OCCT pool 1; environment requests one thread; no OS affinity claimed",
        "acceptance": False,
        "flight_ready": False,
    }
    (OUTPUT / "candidate-record-io-replan.json").write_text(json.dumps(record, indent=2) + "\n")
    (OUTPUT / "executed-candidate-io-replan.py").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {
                k: record[k]
                for k in (
                    "status",
                    "candidate_identity",
                    "candidate_mount_mass_kg",
                    "incremental_bond_allowance_kg",
                    "baseline_mass",
                    "candidate_zero_added_bond_mass",
                    "candidate_upper_bond_budget_mass",
                    "intersections_mm3",
                    "candidate_outside_original_mm3",
                    "elapsed_s",
                    "resource_self",
                )
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    if "--validate" in sys.argv:
        data = prepare()
        print(
            "Validated all non-CAD inputs and 43-part upper-budget model; predicted minimum 0.12102 mm; adhesive upper kg",
            data[-1],
        )
    elif "--candidate" in sys.argv:
        candidate()
    else:
        main()
