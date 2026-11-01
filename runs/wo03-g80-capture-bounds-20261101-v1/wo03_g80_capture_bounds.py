"""Hand screens of rejected capture envelopes; no CAD or thermal/flight solver.

Units in beam arithmetic are N, mm, MPa; conductance is converted to SI.
Fixed-end beam cases are conditional sensitivities, not installed bounds.
"""

from __future__ import annotations

import hashlib
import json
import math
import resource
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-g80-capture-bounds.yaml"
OUT = ROOT / "runs/wo03-g80-capture-bounds-20261101-v1"


def beam(force, eccentricity, length, area, inertia, youngs):
    moment = force * eccentricity
    rotation = moment * length / (youngs * inertia)
    return {
        "axial_mm": force * length / (youngs * area),
        "radial_mm": moment * length**2 / (2 * youngs * inertia),
        "rotation_rad": rotation,
        "loadpoint_axial_mm": force * length / (youngs * area) + eccentricity * rotation,
    }


def conductance(k, area_mm2, length_mm, count):
    return count * k * area_mm2 * 1e-6 / (length_mm * 1e-3)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    start = time.monotonic()
    cfg = yaml.safe_load(CONFIG.read_text())
    props = yaml.safe_load((ROOT / cfg["materials"]).read_text())["materials"]
    inventory = yaml.safe_load((ROOT / cfg["comparison"]).read_text())
    stock = json.loads((ROOT / cfg["stock_record"]).read_text())
    paths = [
        CONFIG,
        Path(__file__).resolve(),
        *(ROOT / cfg[k] for k in ("materials", "comparison", "stock_record")),
    ]
    before = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    # Independent closed-form arithmetic checks, including mm-to-m conversion.
    known = beam(10, 5, 100, 100, 2000, 200000)
    assert math.isclose(known["radial_mm"], 0.000625, rel_tol=1e-12)
    assert math.isclose(known["rotation_rad"], 0.0000125, rel_tol=1e-12)
    assert math.isclose(known["axial_mm"], 0.00005, rel_tol=1e-12)
    assert math.isclose(conductance(1, 10000, 100, 1), 0.1, rel_tol=1e-12)
    assert math.isclose(10 * (2 * 100 - 100) / 8, 125)  # fully loaded pin span
    assert math.isclose(10 * (2 * 100) / 8, 250)  # point-load limit
    b = cfg["B"]
    force = cfg["retention_service_n"] * cfg["design_factor"]
    recovery = cfg["recovery_already_factored_n"]
    area = b["rail_radial_mm"] * b["rail_tangential_mm"]
    inertia = b["rail_tangential_mm"] * b["rail_radial_mm"] ** 3 / 12
    eccentricity = b["rail_centroid_radius_mm"] - b["bolt_radius_mm"]
    bending = force * eccentricity / (inertia / (b["rail_radial_mm"] / 2))
    cases = []
    for length in b["support_length_cases_mm"]:
        for factor in b["stiffness_factors"]:
            result = beam(
                force,
                eccentricity,
                length,
                area,
                inertia,
                props["plywood"]["youngs_pa"] / 1e6 * factor,
            )
            cases.append(
                {
                    "length_mm": length,
                    "E_factor": factor,
                    **result,
                    "small_rotation_0p1rad_diagnostic": abs(result["rotation_rad"]) < 0.1,
                }
            )
    span = b["lug_centers_mm"][1] - b["lug_centers_mm"][0]
    loaded_width = b["rail_tangential_mm"]
    pin_moment = force * (2 * span - loaded_width) / 8
    required_span = span + b["lug_thickness_mm"] + 2 * b["washer_thickness_mm"]
    c = cfg["C"]
    fit_width = (
        math.sqrt(c["coupler_bore_radius_mm"] ** 2 - c["strip_outer_tangential_coordinate_mm"] ** 2)
        - c["strip_inner_radial_coordinate_mm"]
    )
    fit_area = c["strips"] * c["tangential_mm"] * fit_width
    weak_I = c["radial_mm"] * c["tangential_mm"] ** 3 / 12
    euler = math.pi**2 * props["G11"]["youngs_pa"] / 1e6 * weak_I / c["full_length_mm"] ** 2
    heat = {}
    for name, element in cfg["thermal_elements"].items():
        a = element.get("area_each_mm2", math.pi * element.get("diameter_mm", 0) ** 2 / 4)
        heat[name] = {
            "conductance_W_K": conductance(
                props[element["material"]]["conductivity_w_m_k"],
                a,
                element["length_mm"],
                element["count"],
            ),
            "interpretation": "isolated axial element; no contact/radiation or temperature bound",
        }
    record = {
        "status": "both_as_specified_screened_out_no_CAD_admission",
        "inputs_sha256": before,
        "retention_factored_N": force,
        "recovery_already_factored_N": recovery,
        "growth_kg_separate": cfg["growth_kg"],
        "B": {
            "rail_gross_area_mm2": area,
            "rail_second_moment_mm4": inertia,
            "eccentricity_mm": eccentricity,
            "gross_axial_MPa": force / area,
            "gross_bending_MPa": bending,
            "gross_combined_MPa": force / area + bending,
            "fixed_end_sensitivities_not_installed_bounds": cases,
            "pin_blank_length_mm": b["pin_blank_length_mm"],
            "minimum_outer_washer_span_mm_without_retention": required_span,
            "pin_blank_cannot_engage_both_lugs": b["pin_blank_length_mm"]
            < span + b["lug_thickness_mm"],
            "hypothetical_long_enough_pin_double_shear_MPa": force
            / (2 * math.pi * b["pin_diameter_mm"] ** 2 / 4),
            "hypothetical_uniform_rail_pin_bending_MPa": pin_moment
            / (math.pi * b["pin_diameter_mm"] ** 3 / 32),
            "hypothetical_lug_projected_bearing_MPa": force
            / (2 * b["lug_thickness_mm"] * b["pin_diameter_mm"]),
            "pin_values_not_joint_allowables": True,
        },
        "C": {
            "coupler_limited_radial_width_mm": fit_width,
            "coupler_limited_area_mm2": fit_area,
            "ideal_uniform_recovery_MPa": recovery / fit_area,
            "unbraced_975mm_strip_Euler_pinned_N": euler,
            "unbraced_975mm_strip_Euler_fixed_N": 4 * euler,
            "Euler_note": "conditional compression only; recovery is tension; bracing unverified",
        },
        "thermal_elements": heat,
        "thermal_temperatures": None,
        "thermal_acceptance": "unavailable; required matrix and 45C screen unchanged",
        "stock_mass_record_sha256": sha(ROOT / cfg["stock_record"]),
        "stock_not_installed": stock["results"],
        "verification": {
            "known_arithmetic_checks": 6,
            "passed": True,
            "not_a_native_mesh_or_strength_validation": True,
        },
        "source_unchanged": before == {str(p.relative_to(ROOT)): sha(p) for p in paths},
        "native_solver_cad_flight_calls": 0,
        "cpu_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime
        + resource.getrusage(resource.RUSAGE_SELF).ru_stime,
        "wall_s": time.monotonic() - start,
    }
    assert record["source_unchanged"]
    assert record["cpu_s"] < cfg["budget"]["cpu_s"]
    assert record["wall_s"] < cfg["budget"]["wall_s"]
    assert inventory["service_retention_N"] == cfg["retention_service_n"]
    assert inventory["recovery_already_factored_N"] == recovery
    OUT.mkdir(exist_ok=False)
    (OUT / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"B": record["B"], "C": record["C"], "cpu_s": record["cpu_s"]}, indent=2))


if __name__ == "__main__":
    main()
