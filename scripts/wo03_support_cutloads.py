"""Conservative mass-extent axial cut ledger for the exact G54 baffle copy.

The non-motor body is one free body: thrust minus the motor's inertial-plus-weight
demand is applied at an assumed front contact. Every part and the growth allowance occur
exactly once. Cross-section sums include ALL material paths, not shell alone.
Mass intervals follow part bounds and first moments; see the accompanying report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from pathlib import Path

import yaml

STANDARD_GRAVITY_M_S2 = 9.80665  # src/sim/frames.py; standard gravity, m/s²


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fraction_bounds(start: float, end: float, mean: float, cut: float) -> tuple[float, float]:
    """Extremal mass fractions strictly forward, given nonnegative mass and first moment."""
    if not start <= mean <= end or end < start:
        raise ValueError(f"invalid extent or centroid: {start}, {mean}, {end}")
    if cut <= start:
        return 0.0, 0.0
    if cut >= end:
        return 1.0, 1.0
    lower = max(0.0, (cut - mean) / (cut - start))
    upper = min(1.0, (end - mean) / (end - cut))
    return lower, upper


def part_extent(part: dict) -> tuple[float, float, float]:
    start = part["position_m"]
    geometry = part["geometry"]
    length = geometry.get("length_m")
    if length is None:
        length = geometry["bbox_m"][0]
    end = start + length
    mean = start + part["cg_offset_m"]
    if mean < start - 1e-12 or mean > end + 1e-12:
        raise ValueError(f"{part['id']}: centroid outside nominal extent")
    return start, end, min(end, max(start, mean))


def geometry_screen(config_path: Path) -> dict:
    """Screen hash-checked STL vertices; use STEP BRep only on flagged parts."""
    import cadquery as cq
    import numpy as np

    cfg = yaml.safe_load(config_path.read_text())
    source = Path(cfg["candidate"])
    manifest_path = Path(cfg["geometry_manifest"])
    if (
        sha(source) != cfg["candidate_sha256"]
        or sha(manifest_path) != cfg["geometry_manifest_sha256"]
    ):
        raise ValueError("candidate or manifest hash mismatch")
    parts = {p["id"]: p for p in json.loads(source.read_text())["parts"]}
    entries = json.loads(manifest_path.read_text())
    if len(entries) != len(parts) or {e["part_id"] for e in entries} != set(parts):
        raise ValueError("geometry inventory differs from candidate")
    dtype = np.dtype([("normal", "<f4", 3), ("vertices", "<f4", (3, 3)), ("attr", "<u2")])
    rows = []
    for entry in entries:
        part = parts[entry["part_id"]]
        path = manifest_path.parent / entry["stl"]
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != entry["stl_sha256"] or len(raw) < 84:
            raise ValueError(f"STL hash or length mismatch: {path}")
        count = struct.unpack_from("<I", raw, 80)[0]
        if count == 0 or len(raw) != 84 + 50 * count:
            raise ValueError(f"invalid binary STL: {path}")
        z = np.frombuffer(raw, dtype=dtype, offset=84, count=count)["vertices"][:, :, 2]
        if not np.isfinite(z).all():
            raise ValueError(f"invalid STL coordinates: {path}")
        low, high, center = part_extent(part)
        nominal = [1000 * low, 1000 * high]
        mesh = [float(z.min()), float(z.max())]
        excess = max(nominal[0] - mesh[0], mesh[1] - nominal[1], 0.0)
        row = {
            "part_id": part["id"],
            "stl_sha256": entry["stl_sha256"],
            "nominal_extent_mm": nominal,
            "source_centroid_mm": center * 1000,
            "stl_vertex_extent_mm": mesh,
            "excess_mm": excess,
            "step": None,
        }
        if excess > 0.001:
            path = manifest_path.parent / entry["step"]
            if sha(path) != entry["step_sha256"]:
                raise ValueError(f"STEP hash mismatch: {path}")
            shape = cq.importers.importStep(str(path)).val()
            if not shape.isValid():
                raise ValueError(f"invalid STEP: {path}")
            box = shape.BoundingBox()
            if not math.isfinite(box.zmin) or not math.isfinite(box.zmax):
                raise ValueError(f"invalid STEP bounds: {path}")
            row["step"] = {
                "sha256": entry["step_sha256"],
                "valid": True,
                "brep_extent_mm": [box.zmin, box.zmax],
                "fully_forward_of_all_cuts": box.zmax < 1000 * min(cfg["cuts_m"]),
            }
        rows.append(row)
    return {
        "candidate_sha256": sha(source),
        "manifest_sha256": sha(manifest_path),
        "coordinate": "placed CAD Z mm, aft positive",
        "float32_comparison_tolerance_mm": 0.001,
        "stl_tessellation_is_not_a_cad_enclosure": True,
        "entries": rows,
        "flagged_count": sum(r["step"] is not None for r in rows),
        "all_flagged_step_entirely_forward_of_cuts": all(
            r["step"]["fully_forward_of_all_cuts"] for r in rows if r["step"] is not None
        ),
    }


def all_step_bounds(config_path: Path, progress_path: Path) -> dict:
    """Read each source STEP once; append progress before trying the next part."""
    import cadquery as cq

    cfg = yaml.safe_load(config_path.read_text())
    source = Path(cfg["candidate"])
    manifest_path = Path(cfg["geometry_manifest"])
    if (
        sha(source) != cfg["candidate_sha256"]
        or sha(manifest_path) != cfg["geometry_manifest_sha256"]
    ):
        raise ValueError("candidate or geometry manifest hash mismatch")
    parts = {p["id"]: p for p in json.loads(source.read_text())["parts"]}
    entries = json.loads(manifest_path.read_text())
    if len(entries) != len(parts) or {e["part_id"] for e in entries} != set(parts):
        raise ValueError("STEP inventory mismatch")
    bounds = {}
    with progress_path.open("x") as progress:
        for entry in entries:
            path = manifest_path.parent / entry["step"]
            if sha(path) != entry["step_sha256"]:
                raise ValueError(f"STEP hash mismatch: {path}")
            shape = cq.importers.importStep(str(path)).val()
            if not shape.isValid():
                raise ValueError(f"invalid STEP: {path}")
            box = shape.BoundingBox()
            low, high = box.zmin / 1000, box.zmax / 1000
            part = parts[entry["part_id"]]
            mean = part["position_m"] + part["cg_offset_m"]
            if not (math.isfinite(low) and math.isfinite(high) and low <= mean <= high):
                raise ValueError(
                    f"{entry['part_id']}: invalid STEP bounds or centroid outside {low}, {mean}, {high}"
                )
            bounds[part["id"]] = (low, high, mean)
            progress.write(
                json.dumps(
                    {
                        "part_id": part["id"],
                        "step_sha256": entry["step_sha256"],
                        "extent_m": [low, high],
                        "centroid_m": mean,
                    }
                )
                + "\n"
            )
            progress.flush()
    return bounds


def run(config_path: Path, extent_override: dict | None = None) -> dict:
    cfg = yaml.safe_load(config_path.read_text())
    source, record_path, audit_path = map(
        Path, (cfg["candidate"], cfg["candidate_record"], cfg["support_audit"])
    )
    if sha(source) != cfg["candidate_sha256"]:
        raise ValueError("candidate file hash changed")
    vehicle, record, audit = [json.loads(p.read_text()) for p in (source, record_path, audit_path)]
    if record["candidate_identity"] != cfg["candidate_identity"]:
        raise ValueError("candidate identity mismatch")
    if audit["input_sha256_before"][str(source)] != sha(source):
        raise ValueError("audit used different candidate")
    curve_path = Path(vehicle["motor"]["curve"])
    if audit["input_sha256_before"][str(curve_path)] != sha(curve_path):
        raise ValueError("motor curve changed since published audit")
    peak = audit["peak_motor_flank"]
    if not math.isclose(peak["time_s"], 0.135, abs_tol=1e-12):
        raise ValueError("unexpected peak")
    parts = vehicle["parts"]
    if len({p["id"] for p in parts}) != len(parts):
        raise ValueError("duplicate part id")
    motor = next(p for p in parts if p["id"] == "motor")
    nonmotor = [p for p in parts if p["id"] != "motor"]
    loaded_mass = sum(p["mass_kg"] for p in parts)
    total = loaded_mass - motor["mass_kg"] + peak["motor_mass_kg"] + cfg["growth_kg"]
    if not math.isclose(total, peak["mass_with_full_growth_kg"], abs_tol=1e-12):
        raise ValueError("mass ledger mismatch")
    thrust = peak["thrust_n"]
    specific_force = thrust / total
    contact = thrust - peak["motor_mass_kg"] * specific_force
    if not math.isclose(contact, peak["motor_flank_n"], abs_tol=1e-10):
        raise ValueError("motor force mismatch")
    spans = (
        {p["id"]: part_extent(p) for p in nonmotor}
        if extent_override is None
        else {p["id"]: extent_override[p["id"]] for p in nonmotor}
    )
    rows = []
    for cut in cfg["cuts_m"]:
        if math.isclose(cut, cfg["contact_station_m_assumed"], abs_tol=1e-12):
            raise ValueError("cut coincides with unknown traction discontinuity")
        ledger = []
        lo = hi = 0.0
        for p in nonmotor:
            bounds = fraction_bounds(*spans[p["id"]], cut)
            mass = p["mass_kg"]
            lo += mass * bounds[0]
            hi += mass * bounds[1]
            ledger.append(
                {
                    "part_id": p["id"],
                    "mass_kg": mass,
                    "extent_m": list(spans[p["id"]][:2]),
                    "centroid_m": spans[p["id"]][2],
                    "forward_fraction_bounds": list(bounds),
                }
            )
        # Growth has no assigned station: 0 to full 50 g may lie forward.
        contact_forward = contact if cfg["contact_station_m_assumed"] < cut else 0.0
        force_lo = specific_force * lo - contact_forward
        force_hi = specific_force * (hi + cfg["growth_kg"]) - contact_forward
        rows.append(
            {
                "cut_m": cut,
                "forward_nonmotor_mass_kg_without_growth_bounds": [lo, hi],
                "forward_growth_mass_kg_bounds": [0.0, cfg["growth_kg"]],
                "assumed_motor_contact_forward_n": contact_forward,
                "combined_cut_force_n_bounds_noseward_positive": [force_lo, force_hi],
                "df3_force_n_bounds": [
                    cfg["design_factor"] * force_lo,
                    cfg["design_factor"] * force_hi,
                ],
                "shell_share_n": None,
                "rail_share_n": None,
                "part_ledger": ledger,
            }
        )
    return {
        "candidate_identity": cfg["candidate_identity"],
        "input_sha256": {
            str(p): sha(p)
            for p in [
                config_path,
                source,
                record_path,
                audit_path,
                Path(vehicle["motor"]["curve"]),
                Path(__file__),
            ]
        },
        "peak": peak,
        "loaded_mass_kg": loaded_mass,
        "nonmotor_mass_kg": loaded_mass - motor["mass_kg"],
        "full_growth_kg": cfg["growth_kg"],
        "effective_axial_specific_force_m_s2": specific_force,
        "standard_gravity_m_s2": STANDARD_GRAVITY_M_S2,
        "vertical_no_drag_kinematic_acceleration_m_s2": specific_force - STANDARD_GRAVITY_M_S2,
        "assumed_contact_station_m": cfg["contact_station_m_assumed"],
        "assumed_contact_n": contact,
        "whole_nonmotor_balance_residual_n": contact
        - (total - peak["motor_mass_kg"]) * specific_force,
        "motor_balance_residual_n": thrust - contact - peak["motor_mass_kg"] * specific_force,
        "source_flank_all_through_shell_df3_mpa": cfg["design_factor"]
        * contact
        / cfg["shell_section_mm2"],
        "paper_screen_mpa": cfg["paper_strength_mpa"],
        "shell_share_n": None,
        "rail_share_n": None,
        "rows": rows,
        "limitations": [
            "motor contact location/distribution assumed",
            (
                "nominal part extents and first moments"
                if extent_override is None
                else "STEP BRep extents and estimated source first moments"
            ),
            "crossing ledger includes every nonmotor load path",
            "no installed capacity or shell share established",
        ],
        "complete_path_accepted": False,
        "flight_ready": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-support-cutloads.yaml")
    )
    parser.add_argument("--output", type=Path, default=Path("build/wo03-support-cutloads-v1"))
    parser.add_argument("--geometry-screen", action="store_true")
    parser.add_argument("--all-step-screen", action="store_true")
    args = parser.parse_args()
    result = run(args.config)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "cutloads.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    if args.geometry_screen:
        screened = geometry_screen(args.config)
        (args.output / "geometry-screen.json").write_text(
            json.dumps(screened, indent=2, allow_nan=False) + "\n"
        )
    if args.all_step_screen:
        bounds = all_step_bounds(args.config, args.output / "step-progress.jsonl")
        result = run(args.config, bounds)
        (args.output / "step-cutloads.json").write_text(
            json.dumps(result, indent=2, allow_nan=False) + "\n"
        )


if __name__ == "__main__":
    main()
