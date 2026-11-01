"""Bound whole-vehicle axial free-body cuts without assuming shell load share."""

from __future__ import annotations

import hashlib
import json
import resource
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml
from OCP.OSD import OSD_Parallel, OSD_ThreadPool

from src.vehicle.mass import mass_properties
from src.vehicle.schema import Vehicle, load_vehicle, vehicle_input_paths

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-g80-axial-cuts.yaml"
OUTPUT = ROOT / "build/wo03-g80-axial-cuts-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fraction_bounds(a, b, mean, cut):
    """Bounds for forward mass fraction from support interval and first moment."""
    if b <= a or not a - 1e-7 <= mean <= b + 1e-7:
        raise ValueError(f"Invalid mass extent/CG: {a} {mean} {b}")
    mean = min(max(mean, a), b)
    if cut <= a:
        return 0.0, 0.0
    if cut >= b:
        return 1.0, 1.0
    lo = max(0.0, (cut - mean) / (cut - a))
    hi = min(1.0, (b - mean) / (b - cut))
    return lo, hi


def run():
    import cadquery as cq

    start = time.monotonic()
    OSD_Parallel.SetUseOcctThreads_s(True)
    pool = OSD_ThreadPool.DefaultPool_s()
    pool.Init(1)
    if pool.NbThreads() != 1:
        raise ValueError("OCCT thread pool is not one")
    cfg = yaml.safe_load(CONFIG.read_text())
    candidate_record = json.loads((ROOT / cfg["candidate_record"]).read_text())
    candidate = Vehicle.model_validate(yaml.safe_load((ROOT / cfg["candidate_spec"]).read_text()))
    identity = hashlib.sha256(candidate.model_dump_json(by_alias=True).encode()).hexdigest()
    if (
        identity != cfg["expected_candidate_identity"]
        or identity != candidate_record["candidate_identity"]
    ):
        raise ValueError("Candidate identity mismatch")
    if sha(ROOT / cfg["candidate_step"]) != candidate_record["step_sha256"]:
        raise ValueError("Candidate STEP mismatch")
    baseline = load_vehicle(ROOT / cfg["baseline_spec"])
    manifest = json.loads((ROOT / cfg["manifest"]).read_text())
    if manifest["identity"]["resolved_spec_sha256"] != candidate_record["source_identity"]:
        raise ValueError("Baseline identity mismatch")
    input_paths = {
        CONFIG,
        Path(__file__).resolve(),
        *(
            ROOT / cfg[k]
            for k in (
                "candidate_spec",
                "candidate_record",
                "candidate_step",
                "baseline_spec",
                "manifest",
                "engineering",
            )
        ),
    }
    input_paths.update(p.resolve() for p in vehicle_input_paths(ROOT / cfg["baseline_spec"]))
    input_paths.update(p.resolve() for p in (ROOT / "src/vehicle").glob("*.py"))
    for p in baseline.parts:
        input_paths.add(ROOT / cfg["parts_directory"] / f"{p.id}.step")
    before = {str(p.relative_to(ROOT)): sha(p) for p in sorted(input_paths)}
    extents = {}
    for p in baseline.parts:
        f = ROOT / cfg["parts_directory"] / f"{p.id}.step"
        shape = cq.importers.importStep(str(f)).val()
        b = shape.BoundingBox()
        extents[p.id] = (p.position_m + b.zmin / 1000, p.position_m + b.zmax / 1000)
    cm = next(p for p in candidate.parts if p.id == "motor_mount")
    b = cq.importers.importStep(str(ROOT / cfg["candidate_step"])).val().BoundingBox()
    candidate_extents = dict(extents)
    candidate_extents["motor_mount"] = (
        cm.position_m + b.zmin / 1000,
        cm.position_m + b.zmax / 1000,
    )
    budget = next(p for p in candidate.parts if p.id == "incremental_mount_gap_epoxy_upper_budget")
    candidate_extents[budget.id] = (
        budget.position_m,
        budget.position_m + budget.geometry["length_m"],
    )
    thrust = float(candidate_record["thrust_n"])
    growth = float(cfg["growth_allowance_kg"])
    ins0, ins1 = cfg["force_insertion_station_bounds_m"]
    results = {}
    for label, vehicle, spans in (
        ("baseline", baseline, extents),
        ("candidate_upper_annular_budget", candidate, candidate_extents),
    ):
        m = mass_properties(vehicle).mass_kg
        fullmass = m + growth
        detailed = []
        for p in vehicle.parts:
            a, b = spans[p.id]
            if not a - 1e-7 <= p.cg_station_m <= b + 1e-7:
                raise ValueError(
                    f"Mass centroid outside saved envelope: {p.id}: {a} {p.cg_station_m} {b}"
                )
            detailed.append(
                {
                    "id": p.id,
                    "mass_kg": p.resolved_mass_kg,
                    "extent_m": [a, b],
                    "centroid_m": p.cg_station_m,
                    "source": (
                        "candidate STEP"
                        if p.id == "motor_mount" and label.startswith("candidate")
                        else (
                            "declared annular budget"
                            if p.id == budget.id
                            else "saved baseline STEP"
                        )
                    ),
                }
            )
        rows = []
        for name, cut in cfg["cuts_m"].items():
            low = high = 0.0
            crossing = []
            for p in vehicle.parts:
                a, b = spans[p.id]
                lo, hi = fraction_bounds(a, b, p.cg_station_m, cut)
                low += p.resolved_mass_kg * lo
                high += p.resolved_mass_kg * hi
                if a < cut < b:
                    crossing.append(p.id)
            high += growth
            if not (0 <= low <= high <= fullmass + 1e-10):
                raise ValueError("Invalid forward mass bound")
            local_fraction = [0.0, 0.0] if cut < ins0 else [1.0, 1.0] if cut > ins1 else [0.0, 1.0]
            force_bounds = [
                thrust * low / fullmass - thrust * local_fraction[1],
                thrust * high / fullmass - thrust * local_fraction[0],
            ]
            rows.append(
                {
                    "name": name,
                    "station_m": cut,
                    "forward_mass_min_kg": low,
                    "forward_mass_max_kg": high,
                    "crossing_parts": crossing,
                    "growth_forward_min_kg": 0,
                    "growth_forward_max_kg": growth,
                    "thrust_ahead_fraction_bounds": local_fraction,
                    "drag_free_total_axial_force_signed_N": force_bounds,
                    "shell_only_force": "unavailable; load sharing through parallel cut components is not determined",
                }
            )
        results[label] = {
            "loaded_mass_kg": m,
            "loaded_plus_growth_kg": fullmass,
            "parts": detailed,
            "cuts": rows,
        }
    # Uniform bar with length 1, mass 2, T=10: at x=.25, known
    # forward acceleration force is 10 * (2*.25)/2 = 2.5 N.
    bar_expected = 2.5
    bar_value = 10.0 * (2.0 * 0.25) / 2.0
    lo, hi = fraction_bounds(0, 1, 0.5, 0.25)
    if abs(bar_value - bar_expected) > 1e-12 or not lo <= 0.25 <= hi:
        raise ValueError("Uniform distributed-bar known case failed")
    after = {str(p.relative_to(ROOT)): sha(p) for p in sorted(input_paths)}
    if before != after:
        raise ValueError("Input changed")
    out = {
        "candidate_identity": identity,
        "source_sha256_before": before,
        "source_sha256_after": after,
        "thrust_N": thrust,
        "mass_source": "loaded full-mass snapshot, full separate 50 g growth; no depletion simulation",
        "thrust_insertion_bounds_m": [ins0, ins1],
        "insertion_basis": cfg["force_insertion_basis"],
        "gravity": "uniform vehicle-parallel gravity cancels from ideal instantaneous axial free-body equation",
        "drag": "zero in numeric rows; for arbitrary drag use F = m_forward*(T-D)/M + D_forward - T_forward; no bounded source for drag partition",
        "sign": "positive compressive cut resultant under stated axis; negative reverse sense",
        "known_case": {
            "uniform_bar_expected_N": bar_expected,
            "computed_N": bar_value,
            "moment_only_fraction_bounds": [lo, hi],
            "exact_forward_fraction": 0.25,
        },
        "results": results,
        "elapsed_s": time.monotonic() - start,
        "resource_self": {
            "user_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime,
            "system_s": resource.getrusage(resource.RUSAGE_SELF).ru_stime,
            "peak_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "threading": "OCCT pool size 1 requested; no OS affinity claimed",
        "accepted": False,
        "flight_ready": False,
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "record.json").write_text(json.dumps(out, indent=2) + "\n")
    (OUTPUT / "executed.py").write_bytes(Path(__file__).read_bytes())
    print(
        json.dumps(
            {
                "known_case": out["known_case"],
                "results": {
                    k: {"mass_kg": v["loaded_plus_growth_kg"], "cuts": v["cuts"]}
                    for k, v in results.items()
                },
                "elapsed_s": out["elapsed_s"],
                "resource_self": out["resource_self"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    run()
