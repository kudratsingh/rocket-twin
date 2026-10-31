"""Audit existing layered-fin root load sharing; no installed acceptance.

Reuses frozen finite-contact quadrature and the actual recorded tab/foot
dimensions. K=int(B.T D B dA), B=[[1,0,-y],[0,1,x]], about the body tangent.
The three root DOFs are radial X, tangential Y and axial-Z rotation. Optional
rotational foundation springs expose missing frame/body compliance without
inventing measured support properties. All geometry and material files are read
only. The parent process enforces one 120-second, one-worker calculation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

for _thread_variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[_thread_variable] = "1"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import numpy as np
import yaml

from scripts.wo03_trainer_fin_root import layered_panel
from src.analysis.fin_contact import finite_contact_matrix
from src.vehicle.schema import load_vehicle, vehicle_input_paths

FIN_RECORD = Path("build/wo03-trainer-fin-root/pvc5-forward25-backed-reconciled/record.json")
ROOT_RECORD = Path("runs/wo03-installed-root-20261031T041923712847Z/record.json")
HOOP_RECORD = Path("build/wo03-recovery-clearance/hoop/record.json")
INSTALLED_RECORD = Path(
    "build/wo03-fin-installed-current/modular-tvc-finned-v1/"
    "wo03-fin-installed-20261030T210211507451Z/report.json"
)
VIBRATION_RECORD = Path(
    "build/wo03-vibration-20261030T205443545391Z/modular-tvc-finned-v1/report.json"
)
SOURCE = Path("build/wo03-recovery-clearance/hoop/resolved-candidate.yaml")
ACTIVE = Path("configs/vehicle/platform/tvc-finned.yaml")


def sha(path: Path) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def read(path: Path) -> Any:
    return json.loads((ROOT / path).read_text())


def current_schema_validation(path: Path) -> dict[str, Any]:
    """Report stale historical caches, never clear them to load a stand-in."""
    try:
        vehicle = load_vehicle(path)
    except ValueError as error:
        return {
            "passed": False,
            "reason": str(error).splitlines()[0],
            "stale_CAD_properties_reported": "stale CAD properties" in str(error),
            "cache_bypass_or_rebuild": False,
        }
    return {
        "passed": True,
        "resolved_spec_sha256": hashlib.sha256(
            vehicle.model_dump_json(by_alias=True).encode()
        ).hexdigest(),
        "cache_bypass_or_rebuild": False,
    }


def operator(x: float, y: float) -> np.ndarray:
    return np.array([[1.0, 0.0, -y], [0.0, 1.0, x]])


def foot_matrix(
    foot: dict[str, Any], radius: float, chord: float, young: float, poisson: float, n: int
) -> tuple[np.ndarray, list[tuple[Any, ...]], list[tuple[Any, ...]]]:
    """Integrate the recorded circular foot, retaining both curved normals."""
    a, b = np.arcsin(np.asarray(foot["foot_tangential_y_interval_m"]) / radius)
    gauss, weights = np.polynomial.legendre.leggauss(n)
    matrix = np.zeros((3, 3))
    patches = []
    extrema = []
    shear = young / (2 * (1 + poisson))
    for side in (-1, 1):
        angles = side * ((a + b) / 2 + gauss * (b - a) / 2)
        for angle, weight in zip(angles, weights, strict=True):
            normal = np.array([math.cos(angle), math.sin(angle)])
            tangent = np.array([-normal[1], normal[0]])
            x, y = radius * normal - np.array([radius, 0.0])
            basis = operator(x, y)
            stiffness = (
                young * np.outer(normal, normal) + shear * np.outer(tangent, tangent)
            ) / foot["bondline_m"]
            area = weight * (b - a) / 2 * radius * chord
            matrix += basis.T @ stiffness @ basis * area
            patches.append((basis, stiffness, normal, tangent, float(area)))
        # Resolve smooth traction extrema along the arc independently of the
        # integration points. Real adhesive edge singularities are not modeled.
        for angle in side * np.linspace(a, b, 257):
            normal = np.array([math.cos(angle), math.sin(angle)])
            tangent = np.array([-normal[1], normal[0]])
            x, y = radius * normal - np.array([radius, 0.0])
            stiffness = (
                young * np.outer(normal, normal) + shear * np.outer(tangent, tangent)
            ) / foot["bondline_m"]
            extrema.append((operator(x, y), stiffness, normal, tangent, 0.0))
    return matrix, patches, extrema


def tab_extrema(faces: list[dict[str, Any]], young: float, shear: float) -> list[tuple[Any, ...]]:
    points = []
    for face in faces:
        normal = np.asarray(face["normal"])
        tangent = np.array([-normal[1], normal[0]])
        stiffness = (young * np.outer(normal, normal) + shear * np.outer(tangent, tangent)) / face[
            "gap_m"
        ]
        for coordinate in face["interval_m"]:
            x, y = (
                (coordinate, face["fixed_coordinate_m"])
                if face["varying_axis"] == "x"
                else (face["fixed_coordinate_m"], coordinate)
            )
            points.append((operator(x, y), stiffness, normal, tangent, 0.0))
    return points


def condensed(matrix: np.ndarray) -> float:
    return float(matrix[2, 2] - matrix[2, :2] @ np.linalg.solve(matrix[:2, :2], matrix[:2, 2]))


def solve_foundations(
    foot: np.ndarray, tab: np.ndarray, load: np.ndarray, supports: tuple[float | None, ...]
) -> tuple[np.ndarray, list[np.ndarray], list[float]]:
    """Only support rotation is flexible; support translations are ideal fixed.

    None means ideal rigid rotation, zero means no rotational restraint. These
    are named hypotheses, not estimates of the actual body or frame.
    """
    size = 3 + sum(value is not None for value in supports)
    matrix = np.zeros((size, size))
    transforms = []
    index = 3
    for branch, stiffness in zip((foot, tab), supports, strict=True):
        transform = np.zeros((3, size))
        transform[:, :3] = np.eye(3)
        if stiffness is not None:
            transform[2, index] = -1
            matrix[index, index] += stiffness
            index += 1
        matrix += transform.T @ branch @ transform
        transforms.append(transform)
    rhs = np.zeros(size)
    rhs[:3] = load
    solution = np.linalg.solve(matrix, rhs)
    motions = [transform @ solution for transform in transforms]
    residual = matrix @ solution - rhs
    return solution[:3], motions, residual.tolist()


def tractions(patches: list[tuple[Any, ...]], motion: np.ndarray, df: float) -> dict[str, float]:
    return {
        "required_hot_normal_strength_DF3_pa": df
        * max(
            abs(float(normal @ stiffness @ basis @ motion))
            for basis, stiffness, normal, _, _ in patches
        ),
        "required_hot_shear_strength_DF3_pa": df
        * max(
            abs(float(tangent @ stiffness @ basis @ motion))
            for basis, stiffness, _, tangent, _ in patches
        ),
    }


def fixtures(young: float, shear: float) -> dict[str, Any]:
    width, depth, gap = 0.1, 0.005, 0.0002
    faces = [
        {
            "varying_axis": "y",
            "interval_m": [-depth / 2, depth / 2],
            "fixed_coordinate_m": 0.0,
            "normal": [1, 0],
            "gap_m": gap,
            "axial_width_m": width,
        }
    ]
    actual, _ = finite_contact_matrix(faces, young, shear, 16)
    expected = np.diag(
        [
            young * width * depth / gap,
            shear * width * depth / gap,
            young * width * depth**3 / (12 * gap),
        ]
    )
    error = float(np.max(np.abs(actual - expected)) / np.max(np.abs(expected)))
    root, _, residual = solve_foundations(
        np.diag([1.0, 1.0, 100.0]),
        np.diag([1.0, 1.0, 200.0]),
        np.array([0.0, 0.0, 1.0]),
        (50.0, 80.0),
    )
    parallel_series = 100 * 50 / (100 + 50) + 200 * 80 / (200 + 80)
    series_error = abs(float(root[2] * parallel_series - 1))
    if error > 1e-12 or series_error > 1e-12 or max(map(abs, residual)) > 1e-12:
        raise ValueError("Finite-patch or series/parallel foundation known case failed")
    return {
        "finite_planar_patch_matrix_relative_error": error,
        "independent_series_parallel_rotation_relative_error": series_error,
        "passed": True,
        "scope": "Algebra and quadrature fixtures, not installed structural qualification",
    }


def worker(output: Path) -> None:
    started = time.monotonic()
    fin, old, hoop, installed, vibration = map(
        read, [FIN_RECORD, ROOT_RECORD, HOOP_RECORD, INSTALLED_RECORD, VIBRATION_RECORD]
    )
    raw = yaml.safe_load((ROOT / SOURCE).read_text())
    parts = {part["id"]: part for part in raw["parts"]}
    geometry = parts["fin_set"]["geometry"]
    cfg = parts["fin_set"]["cad"]["parameters"]["layered_study"]
    source_paths = {
        Path(__file__).relative_to(ROOT),
        FIN_RECORD,
        ROOT_RECORD,
        HOOP_RECORD,
        INSTALLED_RECORD,
        VIBRATION_RECORD,
        SOURCE,
        Path(fin["resolved_copy"]),
        Path(fin["cad_exports"]["fin-layers.step"]["path"]),
        Path(hoop["frame_step"]["path"]),
        Path("src/analysis/fin_contact.py"),
        Path("scripts/wo03_trainer_fin_root.py"),
        Path("src/analysis/fin_attachment.py"),
        Path("configs/engineering/wo03.yaml"),
        Path("src/vehicle/benchmark.py"),
        Path("src/vehicle/schema.py"),
        Path("src/vehicle/cad_contract.py"),
        *[path.relative_to(ROOT) for path in (ROOT / "src/cad").glob("*.py")],
        *vehicle_input_paths(ACTIVE),
    }
    before = {str(path): sha(path) for path in sorted(source_paths)}
    for path, expected in [
        (
            Path(fin["cad_exports"]["fin-layers.step"]["path"]),
            fin["cad_exports"]["fin-layers.step"]["sha256"],
        ),
        (Path(hoop["frame_step"]["path"]), hoop["frame_step"]["sha256"]),
        (SOURCE, hoop["resolved_copy_sha256"]),
        (Path(fin["resolved_copy"]), fin["resolved_copy_sha256"]),
    ]:
        if sha(path) != expected:
            raise ValueError(f"Frozen actual source identity mismatch: {path}")
    if (
        old["actual_source_reconciliation"][
            "fin_STEP_vs_density_weighted_layers_symmetric_difference_mm3"
        ]
        > 1e-4
    ):
        raise ValueError("Historical actual fin STEP reconciliation did not pass")
    force = fin["selected_force_n"]
    span, chord, radius = (geometry[key] for key in ("span_m", "root_chord_m", "radius_m"))
    load = np.array([0.0, force, force * span / 2])
    df = cfg["design_factor"]
    young = cfg["hot_adhesive_youngs_pa_estimate"]
    shear = young / (2 * (1 + cfg["adhesive_poisson_estimate"]))
    known = fixtures(young, shear)
    panels = [layered_panel(cfg, force, span, chord, n) for n in (16, 32, 64)]
    panel = panels[-1]
    original_panel = fin["layered_panel_quadrature_levels"][-1]
    if not math.isclose(
        panel["panel_only_tip_deflection_m"],
        original_panel["panel_only_tip_deflection_m"],
        rel_tol=1e-12,
    ):
        raise ValueError("Frozen panel result was not reproduced")
    faces = old["source_tab_potting_rigid_frame_proxy"]["actual_tab_faces"]
    rows = []
    matrix_levels = []
    all_patch_results = []
    required = panel["required_bending_root_rotation_stiffness_nm_rad_if_no_translation"]
    for foot in fin["curved_foot_bond_upper_stiffness_sensitivity"]:
        for n in (16, 32, 64):
            kf, pf, ef = foot_matrix(
                foot, radius, chord, young, cfg["adhesive_poisson_estimate"], n
            )
            kt, pt = finite_contact_matrix(faces, young, shear, n)
            et = tab_extrema(faces, young, shear)
            if not math.isclose(
                condensed(kf), foot["rigid_backing_condensed_Ktheta_nm_rad"], rel_tol=1e-12
            ):
                raise ValueError("Frozen curved-foot stiffness was not reproduced")
            if not math.isclose(
                condensed(kt),
                old["source_tab_potting_rigid_frame_proxy"]["levels"][-1][
                    "rigid_frame_condensed_Ktheta_nm_rad"
                ],
                rel_tol=1e-12,
            ):
                raise ValueError("Frozen tab stiffness was not reproduced")
            root, relative, residual = solve_foundations(kf, kt, load, (None, None))
            matrix_levels.append(
                {
                    "bondline_m": foot["bondline_m"],
                    "quadrature_per_patch": n,
                    "foot_K": kf.tolist(),
                    "tab_K": kt.tolist(),
                    "root_motion": root.tolist(),
                    "residual": residual,
                }
            )
            if n != 64:
                continue
            hypotheses = [
                ("ideal_rigid_body_and_frame", (None, None)),
                ("paper_body_free_rotation_frame_rigid", (0.0, None)),
                ("frame_free_rotation_paper_body_rigid", (None, 0.0)),
                *[
                    (
                        f"both_supports_{factor:g}_times_required_rotation_K",
                        (factor * required, factor * required),
                    )
                    for factor in (0.1, 1.0, 10.0)
                ],
            ]
            for name, supports in hypotheses:
                root, relative, residual = solve_foundations(kf, kt, load, supports)
                branch_rows = []
                for ident, matrix, patches, extrema, displacement in zip(
                    ("curved_foot_to_paper_body", "three_face_tab_potting_to_G11_frame"),
                    (kf, kt),
                    (pf, pt),
                    (ef, et),
                    relative,
                    strict=True,
                ):
                    resultant = matrix @ displacement
                    branch_rows.append(
                        {
                            "branch": ident,
                            "resultant_Fx_Fy_Mz_N_N_Nm": resultant.tolist(),
                            "moment_fraction": float(resultant[2] / load[2]),
                            "relative_motion_m_m_rad": displacement.tolist(),
                            **tractions(patches + extrema, displacement, df),
                            "normal_peel_allowable_pa": None,
                            "normal_peel_margin": None,
                        }
                    )
                recovered = sum(
                    (np.asarray(branch["resultant_Fx_Fy_Mz_N_N_Nm"]) for branch in branch_rows),
                    np.zeros(3),
                )
                if np.max(np.abs(recovered - load)) > 1e-8 or max(map(abs, residual)) > 1e-8:
                    raise ValueError("Common-root branch equilibrium failed")
                added = float(root[1] + span * root[2])
                rows.append(
                    {
                        "hypothesis": name,
                        "foot_bondline_m": foot["bondline_m"],
                        "assumed_support_rotation_K_body_frame_nm_rad": list(supports),
                        "base_translation_ideal_fixed": True,
                        "root_motion_m_m_rad": root.tolist(),
                        "root_added_tip_motion_m": added,
                        "total_panel_plus_root_tip_motion_m": panel["panel_only_tip_deflection_m"]
                        + added,
                        "deflection_screen_under_hypothesis": panel["panel_only_tip_deflection_m"]
                        + added
                        <= 0.001,
                        "branches": branch_rows,
                        "force_moment_residual": (recovered - load).tolist(),
                        "actual_installed_support_property": False,
                    }
                )
                if name == "ideal_rigid_body_and_frame":
                    remaining = panel["root_translation_and_rotation_compliance_budget_m"] - added
                    all_patch_results.append(
                        {
                            "foot_bondline_m": foot["bondline_m"],
                            "root_adhesive_tip_motion_m": added,
                            "remaining_common_foundation_tip_budget_m": remaining,
                            "necessary_common_rotation_K_nm_rad_if_translation_zero": float(
                                load[2] * span / remaining
                            ),
                            "necessary_common_translation_K_n_m_if_rotation_zero": float(
                                force / remaining
                            ),
                            "simultaneous_constraint": "F_y/K_y + M_z*span/K_theta <= remaining; translations and rotations of the shared support are assumed uncoupled",
                            "installed_foundation_lower_bound_available": False,
                        }
                    )
    convergence = []
    for bond in cfg["root_bond_thickness_sensitivity_m"]:
        levels = [row for row in matrix_levels if math.isclose(row["bondline_m"], bond)]
        relative = np.max(
            np.abs(np.asarray(levels[-1]["root_motion"]) - levels[-2]["root_motion"])
        ) / np.max(np.abs(levels[-1]["root_motion"]))
        convergence.append(
            {
                "foot_bondline_m": bond,
                "last_two_root_motion_relative_change": float(relative),
                "passed_lt_1e-10": bool(relative < 1e-10),
            }
        )
        if relative >= 1e-10:
            raise ValueError("Contact quadrature did not converge")
    design = raw["design"]
    if not (
        design["mass_allowance_kg"] == 0.05
        and design["rail_length_m"] == 5
        and design["minimum_rail_exit_mps"] == 10
    ):
        raise ValueError("G12 full-growth guide criteria changed")
    conservative_mass = old["guide_mass_basis"]["used_nominal_mass_kg"]
    guide = []
    capture_mass = old["one_family_capture_mass"]["incremental_mass_kg"]
    # The exact recorded guide limit already has two timestep levels. Reuse it
    # rather than claiming a new guide method from another mass binary search.
    headroom = (
        next(
            row
            for row in hoop["guide_mass_hypotheses"]
            if row["thermal_addition_g"] == 0 and row["rail_saving_hypothesis_g"] == 0
        )["mass_margin_g"]
        / 1000
    )
    for label, root_mass, thermal_mass in [
        ("source_no_new_thermal", 0.0, 0.0),
        ("source_plus_existing_8g_thermal_hypothesis", 0.0, 0.008),
        ("rejected_cheek_no_new_thermal", capture_mass, 0.0),
        ("rejected_cheek_plus_8g_thermal_hypothesis", capture_mass, 0.008),
    ]:
        guide.append(
            {
                "hypothesis": label,
                "added_root_mass_kg": root_mass,
                "added_thermal_mass_kg": thermal_mass,
                "remaining_guide_mass_headroom_kg": headroom - root_mass - thermal_mass,
                "screens": next(
                    row
                    for row in old["guide_and_full_growth"]
                    if math.isclose(row["additional_thermal_mass_kg"], thermal_mass)
                )["source_screens" if root_mass == 0 else "with_capture_screens"],
                "screen_provenance": "Frozen installed-root record, two timesteps; not recomputed from stale current CAD caches",
                "thermal_or_root_solution_accepted": False,
            }
        )
    source_validation = current_schema_validation(SOURCE)
    active_validation = current_schema_validation(ACTIVE)
    active_raw = yaml.safe_load((ROOT / ACTIVE).read_text())
    active_fin = next(p for p in active_raw["parts"] if p["id"] == "fin_set")
    after = {str(path): sha(path) for path in sorted(source_paths)}
    if before != after:
        raise ValueError("Read-only source changed during audit")
    record = {
        "status": "completed_installed_path_requirements_unclosed",
        "accepted": False,
        "flight_ready": False,
        "active_adoption": False,
        "input_sha256": before,
        "inputs_unchanged": before == after,
        "source_identity": {
            "vehicle_id": raw["id"],
            "hoop_resolved_spec_sha256": hoop["resolved_spec_sha256"],
            "hoop_resolved_copy_sha256": hoop["resolved_copy_sha256"],
            "layered_fin_step_sha256": fin["cad_exports"]["fin-layers.step"]["sha256"],
            "actual_frame_step_sha256": hoop["frame_step"]["sha256"],
            "historical_reconciled_actual_identity": old["source_reconciled_identity"],
            "no_new_CAD_or_cache_recomputed": True,
            "actual_layered_fin_never_replaced_by_native_plate": True,
            "current_schema_validation": source_validation,
        },
        "active_identity": {
            "vehicle_id": active_raw["id"],
            "active_fin_geometry": active_fin["geometry"],
            "current_schema_validation": active_validation,
            "historical_installed_report_identity": installed["resolved_spec_sha256"],
            "historical_active_report_is_current_identity": active_validation.get(
                "resolved_spec_sha256"
            )
            == installed["resolved_spec_sha256"],
            "historical_report_is_not_layered_fin": True,
        },
        "scope": {
            "load": "existing transferred maximum historical q*CN2 sensitivity, not a validated same-candidate operational envelope",
            "minimum_dimensions": {
                "skin_m": panel["minimum_skin_thickness_m"],
                "core_m": panel["minimum_core_thickness_m"],
            },
            "hot_property_fraction": cfg["hot_property_fraction"],
            "design_factor_strength_only": df,
            "substrate_screen_c_unchanged": 45.0,
            "contact_solid_root_and_gusset_rigid": True,
            "gap_pads_frame_rings_shell_body_foundation": "explicitly unresolved; represented only by named rotational hypotheses, base translations ideal fixed",
            "normal_peel_strength": "unavailable; no generic shear/paper strength relabelled as peel allowable",
            "no_new_FEA": True,
        },
        "load_coordinates": {
            "CAD_axes": ["X radial", "Y tangential", "Z axial nose-to-aft"],
            "root_DOF": ["u_X_m", "u_Y_m", "theta_Z_rad"],
            "resultants_Fx_Fy_Mz": load.tolist(),
            "warning": "Historical fin_attachment rail radial-X bending screen applies the span-root moment to another axis without an explicit frame/ring load transformation; retain as surrogate, not actual installed closure.",
        },
        "known_cases": known,
        "panel_reproduction": panels,
        "contact_matrix_levels": matrix_levels,
        "contact_quadrature_convergence": convergence,
        "common_root_load_sharing": rows,
        "necessary_common_foundation_requirements": all_patch_results,
        "historical_cheek_decisive_failure_retained": old["mechanical_necessary_conditions"],
        "historical_actual_source_mass_ledger": old["guide_mass_basis"],
        "G12_complete_package_guide": {
            "guide_length_m": 5.0,
            "minimum_speed_mps": 10.0,
            "full_growth_kg": 0.05,
            "guide_availability_confirmed": False,
            "source_nominal_mass_used_kg": conservative_mass,
            "source_headroom_no_thermal_or_unaccepted_rail_credit_kg": headroom,
            "no_mass_change_from_audit_kg": 0.0,
            "cases": guide,
        },
        "flutter": {
            "existing_layered_static_torsion_requirements": fin["torsion_and_flutter"],
            "historical_base_panel_acceptance": vibration["flutter"][
                "quantitative_flutter_acceptance_passed"
            ],
            "root_compliance_modal_sensitivity_ratio_at_1mm_limit": math.sqrt(
                panel["panel_only_tip_deflection_m"] / 0.001
            ),
            "modal_ratio_scope": "sqrt(k_installed/k_panel) only for fixed mass and identical single static load shape; not an installed eigenfrequency or flutter speed",
            "installed_modes_damping_and_body_fin_TVC_coupling_available": False,
            "dynamic_flutter_acceptance": False,
        },
        "specific_closed_subitem": "Common-coordinate equilibrium and hot finite-contact sharing of the existing three-face tab and both curved feet are reproduced and quadrature-converged, conditional on rigid root/gussets and the named foundation hypotheses.",
        "decisive_design_failure_preserved": "Existing 8.459 g cheek family K<=40 vs required358.700 N m/rad and hot generic bearing screen fails; do not adopt or rescale it silently.",
        "acceptance_blockers": [
            "No measured hot normal/peel capacities for curved foot/paper, potting/wood or G11 interfaces",
            "No installed frame/ring/shell/pad compliance or complete load-routing transformation",
            "Actual flexible solid root and gusset transfer, face compression/wrinkling and edge concentrations unresolved",
            "Regional stress refinement failures retained, not replaced by contact quadrature convergence",
            "Installed torsional stiffness, modal shapes, damping, body-pitch/TVC coupling and same-candidate envelope missing",
            "Complete compatible G12 thermal/retention/motion and guide budget remain open",
        ],
        "historical_regional_FEA_failures_retained": fin["historical_FEA_failures_retained"],
        "cpu_workers": 1,
        "solver_child_cap_s": 120,
        "cost_usd": 0,
        "elapsed_s": time.monotonic() - started,
    }
    (output / "record.json").write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    with (output / "connection-table.csv").open("w", newline="") as stream:
        fields = [
            "hypothesis",
            "foot_bondline_m",
            "branch",
            "Fx_n",
            "Fy_n",
            "Mz_nm",
            "moment_fraction",
            "normal_DF3_pa",
            "shear_DF3_pa",
            "total_tip_m",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            for branch in row["branches"]:
                fx, fy, mz = branch["resultant_Fx_Fy_Mz_N_N_Nm"]
                writer.writerow(
                    dict(
                        zip(
                            fields,
                            [
                                row["hypothesis"],
                                row["foot_bondline_m"],
                                branch["branch"],
                                fx,
                                fy,
                                mz,
                                branch["moment_fraction"],
                                branch["required_hot_normal_strength_DF3_pa"],
                                branch["required_hot_shear_strength_DF3_pa"],
                                row["total_panel_plus_root_tip_motion_m"],
                            ],
                            strict=True,
                        )
                    )
                )
    print(
        json.dumps(
            {
                "record": str(output / "record.json"),
                "status": record["status"],
                "elapsed_s": record["elapsed_s"],
            }
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("build/wo03-installed-fin-closure-audit-v1")
    )
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        worker(args.output)
        return 0
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    with (args.output / "worker.log").open("w") as log:
        try:
            process = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--worker",
                    "--output",
                    str(args.output),
                ],
                cwd=ROOT,
                env=os.environ.copy(),
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=120,
                check=False,
            )
        except subprocess.TimeoutExpired:
            (args.output / "completion.json").write_text(
                json.dumps(
                    {
                        "status": "incomplete_child_cap",
                        "elapsed_s": time.monotonic() - started,
                        "accepted": False,
                    },
                    indent=2,
                )
                + "\n"
            )
            return 2
    (args.output / "completion.json").write_text(
        json.dumps(
            {
                "status": "completed" if process.returncode == 0 else "calculation_error",
                "child_returncode": process.returncode,
                "elapsed_s": time.monotonic() - started,
                "accepted": False,
            },
            indent=2,
        )
        + "\n"
    )
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
