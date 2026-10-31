"""Verify Package A sections against unchanged motor-support screening loads.

CAD sections include cylindrical trimming and the fin channel. Elementary column
and beam-column checks use Roark/Euler pinned-column equations with an explicit
initial eccentricity. These are analytical design screens with estimated hot
properties, not proof of adhesive, contact or assembled restraint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any

import cadquery as cq
import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.engineering import structural
from src.analysis.motor_support import motor_support
from src.cad.parts import local_shape
from src.vehicle.schema import Part, Vehicle, load_vehicle, vehicle_input_paths


def section(part: Part, station_mm: float, angle_deg: float = 0) -> dict[str, Any]:
    """BRep integral of a 0.1 mm axial slice of one rail, in its local axes."""
    assert part.cad
    p = part.cad.parameters
    is_cassette = part.cad.generator == "motor_cassette"
    radial = float(p["rail_radial_width_mm"] if is_cassette else p["rail_depth_mm"])
    tangential = float(p["rail_tangential_width_mm"] if is_cassette else p["rail_width_mm"])
    center = float(p["rail_center_radius_mm"] if is_cassette else p["rail_radius_mm"])
    depth = 0.1
    shape = local_shape(part).rotate((0, 0, 0), (0, 0, 1), -angle_deg)
    cutter = cq.Solid.makeBox(
        radial,
        tangential,
        depth,
        cq.Vector(center - radial / 2, -tangential / 2, station_mm - depth / 2),
    )
    cut = shape.intersect(cutter)
    area = cut.Volume() / depth
    if area <= 0:
        raise ValueError("Requested rail section is empty")
    matrix = np.asarray(cq.Shape.matrixOfInertia(cut))
    # Subtract the axial slice's depth contribution before dividing by depth.
    ixx = float(matrix[0, 0] / depth - area * depth**2 / 12)
    iyy = float(matrix[1, 1] / depth - area * depth**2 / 12)
    xy = float(-matrix[0, 1] / depth)
    eigenvalues = np.linalg.eigvalsh([[ixx, -xy], [-xy, iyy]])
    bounds = cut.BoundingBox()
    centroid = cut.Center()
    extreme_fibre = math.hypot(
        max(abs(bounds.xmin - centroid.x), abs(bounds.xmax - centroid.x)),
        max(abs(bounds.ymin - centroid.y), abs(bounds.ymax - centroid.y)),
    )
    return {
        "station_mm": station_mm,
        "rail_angle_deg": angle_deg,
        "area_mm2": area,
        "principal_second_moments_mm4": eigenvalues.tolist(),
        "section_centroid_mm": [cut.Center().x, cut.Center().y],
        "extreme_fibre_upper_bound_mm": extreme_fibre,
        "basis": "Exact CAD BRep volume/moments of constant rail section; 0.1 mm slice, depth inertia removed",
    }


def beam_column(
    area_mm2: float,
    inertia_mm4: float,
    length_mm: float,
    force_n: float,
    modulus_mpa: float,
    strength_mpa: float,
    eccentricity_mm: float,
    extreme_fibre_mm: float,
    factor: float,
) -> dict[str, Any]:
    pcr = math.pi**2 * modulus_mpa * inertia_mm4 / length_mm**2
    factored = factor * force_n
    ratio = factored / pcr
    # Geometric-series amplification is an explicitly conservative first-mode
    # eccentricity sensitivity, not an exact nonlinear imperfection solution.
    amplification = 1 / (1 - ratio) if ratio < 1 else None
    sigma = (
        factored / area_mm2
        + factored * eccentricity_mm * extreme_fibre_mm / inertia_mm4 * amplification
        if amplification is not None
        else None
    )
    return {
        "per_rail_service_force_n": force_n,
        "design_factor_applied_once": factor,
        "effective_pinned_span_mm": length_mm,
        "youngs_modulus_mpa": modulus_mpa,
        "strength_screen_mpa": strength_mpa,
        "euler_capacity_n": pcr,
        "factored_load_to_euler_ratio": ratio,
        "euler_margin": pcr / factored - 1,
        "initial_eccentricity_mm": eccentricity_mm,
        "first_mode_amplification": amplification,
        "factored_compression_plus_bending_mpa": sigma,
        "strength_margin": strength_mpa / sigma - 1 if sigma else None,
        "factored_lateral_displacement_increment_mm": (
            eccentricity_mm * (amplification - 1) if amplification else None
        ),
        "passed": ratio < 1 and sigma is not None and sigma <= strength_mpa,
    }


def make_candidate(v: Vehicle, package: dict[str, Any], brace: bool) -> Vehicle:
    raw = v.model_dump(by_alias=True)
    for part in raw["parts"]:
        if part["id"] != "motor_mount":
            continue
        part["cad_mass"] = None
        if v.tvc:
            part["cad"]["parameters"]["rail_radial_width_mm"] = package["tvc_rail_radial_width_mm"]
        else:
            part["geometry"]["radius_m"] = package["fixed_mount_outer_radius_mm"] / 1000
            if brace:
                p = part["cad"]["parameters"]
                old = p["ring_stations_mm"]
                p["ring_stations_mm"] = sorted(old + [old[1] / 2, (old[1] + old[2]) / 2])
                p["ring_thicknesses_mm"] = [p["ring_thickness_mm"]] * len(p["ring_stations_mm"])
    return Vehicle.model_validate(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-fit-correction.yaml")
    )
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    args = parser.parse_args()
    study = yaml.safe_load(args.config.read_text())
    cfg_path = Path(study["engineering_config"])
    cfg = yaml.safe_load(cfg_path.read_text())
    package = next(p for p in study["packages"] if p["id"] == "fit-package-a")
    sources = {args.config, cfg_path, Path(__file__), Path("src/analysis/motor_support.py")}
    sources.update(Path("src/cad").glob("*.py"))
    for p in study["vehicle_configs"].values():
        sources.update(vehicle_input_paths(p))

    def hashes() -> dict[str, str]:
        return {
            str(p.resolve().relative_to(Path.cwd())): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(sources)
        }

    before = hashes()
    results = []
    for label, path in study["vehicle_configs"].items():
        original = load_vehicle(path)
        for name, brace in [("package-a", False), ("package-a-braced", True)]:
            if original.tvc and brace:
                continue
            v = make_candidate(original, package, brace)
            force = float(structural(v, cfg)["peak_scaled_thrust_n"])
            support = motor_support(v, cfg, force)
            rail = support["screens"]["rails"]
            mount = next(p for p in v.parts if p.id == "motor_mount")
            assert mount.cad
            p = mount.cad.parameters
            stations = rail["support_stations_m"]
            samples = [(a + b) * 500 for a, b in pairwise(stations) if b - a > 0.005]
            # Include actual fin-channel sections; the pre-channel rail is stronger.
            if not v.tvc:
                samples += [float(p["tab_slot_start_mm"]) + 15]
            sections = [section(mount, z, 150 if v.tvc else 0) for z in samples]
            weakest = min(sections, key=lambda s: s["principal_second_moments_mm4"][0])
            material = cfg["materials"][mount.material]
            variants = []
            for eccentricity in [0, 0.1, 0.2]:
                variants.append(
                    beam_column(
                        min(s["area_mm2"] for s in sections),
                        weakest["principal_second_moments_mm4"][0],
                        rail["maximum_assumed_unsupported_span_m"] * 1000,
                        force / rail["rail_count"],
                        material["youngs_pa"] * 0.5e-6,
                        material.get("hot_strength_screen_pa", material["strength_pa"] * 0.5)
                        * 1e-6,
                        eccentricity,
                        weakest["extreme_fibre_upper_bound_mm"],
                        float(cfg["loads"]["design_factor"]),
                    )
                )
            results.append(
                {
                    "configuration": label,
                    "candidate": name,
                    "sections": sections,
                    "beam_column_hot": variants,
                    "support": support,
                }
            )
    # Independent closed-form rectangle fixture catches CAD integral units/axes.
    fixture = cq.Solid.makeBox(4, 6, 0.1)
    matrix = np.asarray(cq.Shape.matrixOfInertia(fixture))
    expected = sorted([6 * 4**3 / 12, 4 * 6**3 / 12])
    actual = sorted([float(matrix[i, i] / 0.1 - 24 * 0.1**2 / 12) for i in [0, 1]])
    known_error = max(abs(a / e - 1) for a, e in zip(actual, expected))
    run = datetime.now(UTC).strftime("wo03-fit-structure-%Y%m%dT%H%M%S%fZ")
    out = Path("runs") / run
    out.mkdir(parents=True)
    payload = {
        "run_id": run,
        "source_hashes": before,
        "inputs_unchanged": before == hashes(),
        "known_rectangle_relative_error": known_error,
        "known_case_passed": known_error < 1e-9,
        "results": results,
        "acceptance_closed": False,
        "flight_ready": False,
        "limitations": [
            "Pinned spans require real ring/frame restraint; exact shell/bond/brace flexibility and imperfect support are not proved.",
            "Column sections include actual cylinder trimming. Rings, foreplate, pins, bonds and retention retain their individual screening limitations in support output.",
            "Extreme-fibre distance is the centroid to the most distant bounding-box corner, bounding any principal bending direction; eccentricity and equal rail load share are assumptions.",
            "No new FEA or physical test is claimed by this analytical check.",
        ],
    }
    (out / "record.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    print(out / "record.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
