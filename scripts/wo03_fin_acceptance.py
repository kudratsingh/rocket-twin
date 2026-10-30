"""Run a minimum-thickness orthotropic plywood fin screen on an explicit vehicle copy.

This script is deliberately not invoked until the selected active fin is adopted.
It neither edits source specifications nor qualifies the root attachment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.fin_fea import orthotropic_compliance, run_shell
from src.cad.parts import shape_digest
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import Part, load_vehicle, vehicle_input_paths

ORTHOTROPIC = {
    "E1_pa": 2.0e9,
    "E2_pa": 2.0e9,
    "E3_pa": 0.5e9,
    "nu12": 0.2,
    "nu13": 0.2,
    "nu23": 0.2,
    "G12_pa": 0.2e9,
    "G13_pa": 0.2e9,
    "G23_pa": 0.2e9,
}
STRENGTH_PA = {"sxx_spanwise": 10.0e6, "syy_chordwise": 10.0e6, "tauxy_in_plane": 2.0e6}
MESH_LEVELS_MM = [10.0, 7.0, 5.0, 3.5, 2.5]
MINIMUM_THICKNESS_MM = 6.05
TEMPERATURE_STIFFNESS_AND_STRENGTH_FRACTION = 0.5
DESIGN_FACTOR = 3.0


def panel_force_n(
    part: Part, q_pa: float, alpha_deg: float, coefficient_bound: float | None = None
) -> float:
    geometry = part.geometry
    span = float(geometry["span_m"])
    root = float(geometry["root_chord_m"])
    tip = float(geometry["tip_chord_m"])
    area = span * (root + tip) / 2
    aspect_ratio = 2 * span**2 / area
    cn_alpha = 2 * math.pi * aspect_ratio / (2 + math.sqrt(4 + aspect_ratio**2))
    cn = coefficient_bound if coefficient_bound is not None else cn_alpha * math.radians(alpha_deg)
    return q_pa * area * cn


def _minimum_thickness_copy(fin: Part) -> Part:
    geometry = dict(fin.geometry)
    geometry["thickness_m"] = MINIMUM_THICKNESS_MM / 1000
    return fin.model_copy(update={"geometry": geometry, "cad_mass": None})


def _convergence(levels: list[dict[str, Any]]) -> dict[str, Any]:
    if len(levels) < 3:
        raise ValueError("Convergence reporting requires at least three mesh levels")
    coarse, middle, fine = levels[0], levels[-2], levels[-1]

    def change(key: str) -> float:
        a, b = float(middle[key]), float(fine[key])
        return abs(b / a - 1) if a else math.inf

    stress_keys = ["regional_abs_sxx_pa", "regional_abs_syy_pa", "regional_abs_tau_xy_pa"]
    stress_changes = {key: change(key) for key in stress_keys}
    displacement_change = change("max_displacement_m")
    frequency_change = max(
        abs(float(b) / float(a) - 1)
        for a, b in zip(middle["frequencies_hz"][:3], fine["frequencies_hz"][:3], strict=True)
    )
    df3_limits = {
        "regional_abs_sxx_pa": STRENGTH_PA["sxx_spanwise"] / DESIGN_FACTOR,
        "regional_abs_syy_pa": STRENGTH_PA["syy_chordwise"] / DESIGN_FACTOR,
        "regional_abs_tau_xy_pa": STRENGTH_PA["tauxy_in_plane"] / DESIGN_FACTOR,
    }
    low_stress_scope = {
        key: {
            "fine_stress_pa": float(fine[key]),
            "df3_allowable_pa": limit,
            "fraction_of_df3_allowable": float(fine[key]) / limit,
            "below_1pct_of_df3_allowable": float(fine[key]) < 0.01 * limit,
        }
        for key, limit in df3_limits.items()
    }
    return {
        "levels_mm": [row["size_mm"] for row in levels],
        "element_counts": [row["elements"] for row in levels],
        "comparison_levels_mm": [middle["size_mm"], fine["size_mm"]],
        "displacement_fine_vs_middle_fraction": displacement_change,
        "stress_component_fine_vs_middle_fraction": stress_changes,
        "fine_component_stress_scope": low_stress_scope,
        "low_absolute_stress_note": "A component below 1% of its DF3 directional allowable can be reported as low absolute stress; this does not waive the regional component mesh-convergence criterion.",
        "frequency_first_three_fine_vs_middle_fraction": frequency_change,
        "displacement_converged_lt_5pct": displacement_change < 0.05,
        "regional_components_converged_lt_10pct": all(
            value < 0.10 for value in stress_changes.values()
        ),
        "first_three_frequencies_converged_lt_5pct": frequency_change < 0.05,
        "converged": displacement_change < 0.05
        and all(value < 0.10 for value in stress_changes.values())
        and frequency_change < 0.05,
        "all_mesh_levels_retained": True,
        "coarse_level_retained_for_history": coarse["size_mm"] == 10.0,
    }


def _component_screen(result: dict[str, Any], strength_fraction: float) -> dict[str, Any]:
    component_map = {
        "sxx_spanwise": ("regional_abs_sxx_pa", STRENGTH_PA["sxx_spanwise"]),
        "syy_chordwise": ("regional_abs_syy_pa", STRENGTH_PA["syy_chordwise"]),
        "tauxy_in_plane": ("regional_abs_tau_xy_pa", STRENGTH_PA["tauxy_in_plane"]),
    }
    rows = {}
    for name, (field, basis) in component_map.items():
        stress = float(result[field])
        allowable = basis * strength_fraction
        margin = allowable / DESIGN_FACTOR / stress - 1 if stress > 0 else math.inf
        rows[name] = {
            "regional_peak_absolute_stress_pa": stress,
            "directional_bound_pa": basis,
            "temperature_strength_fraction": strength_fraction,
            "allowable_after_DF3_pa": allowable / DESIGN_FACTOR,
            "screen_margin": margin,
            "status": "screen-pass" if margin >= 0 else "screen-fail",
        }
    return {
        "components": rows,
        "status": (
            "screen-pass"
            if all(r["status"] == "screen-pass" for r in rows.values())
            else "screen-fail"
        ),
        "criterion": "Independent directional component bounds |Sxx|<=10 MPa, |Syy|<=10 MPa, |tauXY|<=2 MPa; allowable divided by DF=3. Not a validated plywood failure envelope; no von Mises failure criterion is used.",
    }


def run_acceptance(
    vehicle_path: Path,
    output_root: Path,
    flight_record_path: Path | None = None,
) -> Path:
    root = Path.cwd()
    vehicle_path = vehicle_path if vehicle_path.is_absolute() else root / vehicle_path
    vehicle = load_vehicle(vehicle_path)
    fin = next((part for part in vehicle.parts if part.type == "fin_set"), None)
    if fin is None:
        raise ValueError(f"{vehicle.id}: selected vehicle has no physical fin_set")
    minimum_fin = _minimum_thickness_copy(fin)
    constants = dict(ORTHOTROPIC)
    orthotropic_compliance(constants)
    inputs = set(vehicle_input_paths(vehicle_path))
    inputs.update(
        {
            root / "configs/engineering/wo03.yaml",
            root / "src/analysis/fin_fea.py",
            root / "scripts/wo03_fin_acceptance.py",
            root / "src/cad/parts.py",
            root / "src/cad/assembly.py",
            root / "src/vehicle/materials.py",
        }
    )
    flight = None
    if flight_record_path:
        flight_record_path = (
            flight_record_path if flight_record_path.is_absolute() else root / flight_record_path
        )
        inputs.add(flight_record_path)
        flight = json.loads(flight_record_path.read_text())
    hash_before = {
        str(path.resolve().relative_to(root.resolve())): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(inputs)
        if path.exists()
    }
    run_id = "wo03-fin-acceptance-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    mode_dir = output_root / vehicle.id / run_id
    mode_dir.mkdir(parents=True, exist_ok=False)
    force_static = panel_force_n(minimum_fin, 40_000.0, 5.0)
    cold_levels = [
        run_shell(
            mode_dir / "static-cold" / str(size),
            minimum_fin,
            size,
            force_n=force_static,
            orthotropic=constants,
        )
        for size in MESH_LEVELS_MM
    ]
    cold_convergence = _convergence(cold_levels)
    cold_criterion = _component_screen(cold_levels[-1], 1.0)
    hot_result = run_shell(
        mode_dir / "static-hot" / "5.0",
        minimum_fin,
        5.0,
        force_n=force_static,
        stiffness_fraction=TEMPERATURE_STIFFNESS_AND_STRENGTH_FRACTION,
        orthotropic=constants,
    )
    hot_criterion = _component_screen(hot_result, TEMPERATURE_STIFFNESS_AND_STRENGTH_FRACTION)

    large_alpha: dict[str, Any] = {
        "status": "unavailable",
        "reason": "No matching current flight record supplied.",
    }
    flight_case = None
    if flight is not None:
        flight_case = next(
            (case for case in flight.get("cases", []) if case.get("vehicle") == vehicle.id), None
        )
        if flight_case is not None:
            max_q = float(flight_case["metrics"]["max_dynamic_pressure_pa"])
            force_high = panel_force_n(minimum_fin, max_q, 0.0, coefficient_bound=2.0)
            high_cold = run_shell(
                mode_dir / "large-alpha-cold" / "5.0",
                minimum_fin,
                5.0,
                force_n=force_high,
                orthotropic=constants,
            )
            high_hot = run_shell(
                mode_dir / "large-alpha-hot" / "5.0",
                minimum_fin,
                5.0,
                force_n=force_high,
                stiffness_fraction=TEMPERATURE_STIFFNESS_AND_STRENGTH_FRACTION,
                orthotropic=constants,
            )
            large_alpha = {
                "status": "screened; flight envelope identity not independently qualified",
                "flight_record": str(flight_record_path),
                "flight_run_id": flight.get("run_id"),
                "flight_case_vehicle": vehicle.id,
                "maximum_dynamic_pressure_pa": max_q,
                "normal_coefficient_bound": 2.0,
                "force_per_fin_n": force_high,
                "cold_fine_mesh": high_cold,
                "hot_fine_mesh": high_hot,
                "cold_strength_screen": _component_screen(high_cold, 1.0),
                "hot_strength_screen": _component_screen(
                    high_hot, TEMPERATURE_STIFFNESS_AND_STRENGTH_FRACTION
                ),
            }
    hash_after = {
        str(path.resolve().relative_to(root.resolve())): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(inputs)
        if path.exists()
    }
    report = {
        "run_id": run_id,
        "vehicle_id": vehicle.id,
        "source_config": str(vehicle_path.resolve().relative_to(root.resolve())),
        "resolved_spec_sha256": hashlib.sha256(
            vehicle.model_dump_json(by_alias=True).encode()
        ).hexdigest(),
        "source_fin_shape_sha256": fin.cad_mass.shape_sha256 if fin.cad_mass else None,
        "minimum_thickness_copy_shape_sha256": shape_digest(minimum_fin),
        "fin_geometry_copy": {
            "span_m": minimum_fin.geometry["span_m"],
            "root_chord_m": minimum_fin.geometry["root_chord_m"],
            "tip_chord_m": minimum_fin.geometry["tip_chord_m"],
            "sweep_m": minimum_fin.geometry["sweep_m"],
            "nominal_thickness_m": fin.geometry["thickness_m"],
            "minimum_thickness_m": minimum_fin.geometry["thickness_m"],
            "root_attachment": "Ideal clamp at/below body tangent; bonded tab/shell load transfer is not represented or qualified.",
        },
        "material": {
            "model": "3D orthotropic engineering constants, used in S6 shell with explicit in-plane orientation",
            "axes": {
                "1": "span/face grain",
                "2": "chord/in-plane transverse",
                "3": "plate normal/thickness",
            },
            "engineering_constants": constants,
            "compliance_eigenvalues_per_pa": np_eigenvalues(constants),
            "compliance_positive_definite": True,
            "density_kg_m3": float(DENSITY_KG_M3[minimum_fin.material]),
            "density_basis": "Resolved material density from src.vehicle.materials; no local duplicate.",
            "property_status": "Estimated preliminary lower-bound assumptions, not measured lot/coupon values.",
        },
        "strength_basis_pa": STRENGTH_PA,
        "design_factor": DESIGN_FACTOR,
        "static_40kpa_5deg": {
            "pressure_pa": 40_000.0,
            "angle_deg": 5.0,
            "force_per_fin_n": force_static,
            "cold_levels": cold_levels,
            "cold_convergence": cold_convergence,
            "cold_strength_screen": cold_criterion,
            "hot_stiffness_and_strength_fraction": TEMPERATURE_STIFFNESS_AND_STRENGTH_FRACTION,
            "hot_fine_mesh": hot_result,
            "hot_strength_screen": hot_criterion,
        },
        "large_alpha_g12_bound": large_alpha,
        "flight_source_scope": (
            "Flight record is optional, historical/identity-sensitive and not a validated adopted-fin envelope; max-q CN=2 load is a separate high-alpha sensitivity, not covered by 40 kPa/5 deg."
            if flight_case
            else "No flight-derived large-alpha case available; do not infer 40 kPa/5 deg covers stall/high-alpha."
        ),
        "root_loadpath_status": "open: ideal clamp is not a bond/root-joint qualification; requires separate root/plywood-to-shell interface analysis and proof test.",
        "validation": {
            "mesh_convergence": cold_convergence["converged"],
            "known_case": "Use orthotropic strip test with analytical spanwise-E deflection; independent from this vehicle fin.",
            "acceptance": "open",
            "acceptance_passed": False,
            "active_adoption": False,
            "flight_ready": False,
        },
        "input_sha256_before": hash_before,
        "input_sha256_after": hash_after,
        "inputs_unchanged": hash_before == hash_after,
        "cost_usd": 0,
    }
    report_path = mode_dir / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return report_path


def np_eigenvalues(constants: dict[str, float]) -> list[float]:
    return [float(value) for value in np.linalg.eigvalsh(orthotropic_compliance(constants))]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vehicle",
        type=Path,
        required=True,
        help="Path to one resolved vehicle-mode YAML (not a vehicle ID), e.g. configs/vehicle/platform/tvc-finned.yaml.",
    )
    parser.add_argument("--output", type=Path, default=Path("build/wo03-fin-acceptance"))
    parser.add_argument("--flight-record", type=Path)
    args = parser.parse_args()
    report = run_acceptance(args.vehicle, args.output, args.flight_record)
    print(report)
    return 0 if json.loads(report.read_text())["inputs_unchanged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
