"""Existing finite Robin-like elastic springs with the actual shell-slot mask.

Rigid root 2-D DOFs [u_x,u_y,theta_z]; a 0.5 mm frame/body foundation,
adhesive bridging and edge failure are not solved. Face area is checked against
independently recorded BRep before the clipped sensitivity is run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
for key in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[key] = "1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def supported_area(
    radius: float, y0: float, y1: float, slot_half: float, full: float, slot: float
) -> float:
    """Analytic area for two uncut end strips and the truncated slot strip."""
    if not 0 < y0 < slot_half < y1 < radius or not 0 < slot < full:
        raise ValueError("Unexpected slot/foot geometry; no inferred clipping")
    return radius * (
        (full - slot) * (math.asin(y1 / radius) - math.asin(y0 / radius))
        + slot * (math.asin(y1 / radius) - math.asin(slot_half / radius))
    )


def operator(x: float, y: float) -> Any:
    import numpy as np

    return np.array([[1.0, 0.0, -y], [0.0, 1.0, x]])


def foot_matrix(
    radius: float,
    y0: float,
    y1: float,
    pieces: list[tuple[float, float]],
    young: float,
    poisson: float,
    thickness: float,
    n: int,
) -> tuple[Any, list[Any]]:
    """Circumferential Gauss quadrature over explicit (start-y, axial length) regions."""
    import numpy as np

    matrix = np.zeros((3, 3))
    patches = []
    shear = young / (2 * (1 + poisson))
    points, weights = np.polynomial.legendre.leggauss(n)
    for ymin, length in pieces:
        lo, hi = math.asin(ymin / radius), math.asin(y1 / radius)
        for side in (-1, 1):
            for point, weight in zip(points, weights, strict=True):
                angle = side * ((lo + hi) / 2 + point * (hi - lo) / 2)
                normal = np.array([math.cos(angle), math.sin(angle)])
                tangent = np.array([-normal[1], normal[0]])
                x, y = radius * normal - np.array([radius, 0.0])
                basis = operator(float(x), float(y))
                constitutive = (
                    young * np.outer(normal, normal) + shear * np.outer(tangent, tangent)
                ) / thickness
                area = weight * (hi - lo) / 2 * radius * length
                matrix += basis.T @ constitutive @ basis * area
                patches.append((basis, constitutive, normal, tangent, float(area)))
    return matrix, patches


def traction_extrema(
    radius: float,
    intervals: list[tuple[float, float]],
    young: float,
    poisson: float,
    thickness: float,
    motion: Any,
) -> dict[str, float]:
    import numpy as np

    peak_n = peak_s = 0.0
    shear = young / (2 * (1 + poisson))
    for lo, hi in intervals:
        a, b = math.asin(lo / radius), math.asin(hi / radius)
        for side in (-1, 1):
            for angle in side * np.linspace(a, b, 257):
                normal = np.array([math.cos(angle), math.sin(angle)])
                tangent = np.array([-normal[1], normal[0]])
                x, y = radius * normal - np.array([radius, 0.0])
                d = (
                    young * np.outer(normal, normal) + shear * np.outer(tangent, tangent)
                ) / thickness
                stress = d @ operator(float(x), float(y)) @ motion
                peak_n = max(peak_n, abs(float(normal @ stress)))
                peak_s = max(peak_s, abs(float(tangent @ stress)))
    return {
        "peak_normal_pa": peak_n,
        "peak_shear_pa": peak_s,
        "required_normal_DF3_pa": 3 * peak_n,
        "required_shear_DF3_pa": 3 * peak_s,
        "scope": "smooth spring traction, includes supported patch endpoints; not adhesive-edge singularity",
    }


def tab_traction_extrema(
    faces: list[dict[str, Any]], young: float, shear: float, motion: Any
) -> dict[str, float]:
    import numpy as np

    normal_max = shear_max = 0.0
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
            stress = stiffness @ operator(x, y) @ motion
            normal_max = max(normal_max, abs(float(normal @ stress)))
            shear_max = max(shear_max, abs(float(tangent @ stress)))
    return {
        "peak_normal_pa": normal_max,
        "peak_shear_pa": shear_max,
        "required_normal_DF3_pa": 3 * normal_max,
        "required_shear_DF3_pa": 3 * shear_max,
    }


def worker(cfg: dict[str, Any], out: Path, hashes: dict[str, str]) -> None:
    begin = time.monotonic()
    cpu = time.process_time()
    import numpy as np

    sys.path.insert(0, str(ROOT))
    from src.analysis.fin_contact import finite_contact_matrix
    from src.vehicle.schema import Vehicle

    v = Vehicle.model_validate_json((ROOT / cfg["candidate"]).read_text())
    ident = hashlib.sha256(v.model_dump_json(by_alias=True).encode()).hexdigest()
    if ident != "4ff75b8f2c6ab47ddf90b546761d7fa6d4a72c3af9f382e6b3790cbeb19c1287":
        raise ValueError("Candidate identity mismatch")
    prior = json.loads((ROOT / cfg["prior_contact"]).read_text())
    old = json.loads((ROOT / cfg["prior_root"]).read_text())
    fin_rec = json.loads((ROOT / cfg["fin_record"]).read_text())
    brep = json.loads((ROOT / cfg["face_audit"]).read_text())
    if not brep["inputs_unchanged"] or brep["candidate_identity"] != ident:
        raise ValueError("BRep identity mismatch")
    parts = {p.id: p for p in v.parts}
    fin, shell = (parts[x] for x in ("fin_set", "aft_shell"))
    geometry = fin.geometry
    params = fin.cad.parameters
    mat = params["layered_study"]
    s = shell.cad.parameters
    radius = geometry["radius_m"]
    chord = geometry["root_chord_m"]
    span = geometry["span_m"]
    start = fin.position_m
    slot0 = shell.position_m + s["fin_slot_start_mm"] / 1000
    slotlen = s["fin_slot_length_mm"] / 1000
    slotend = slot0 + slotlen
    half = s["fin_slot_width_mm"] / 2000
    foot = fin_rec["curved_foot_bond_upper_stiffness_sensitivity"][0]
    y0, y1 = foot["foot_tangential_y_interval_m"]
    if not (
        math.isclose(shell.geometry["radius_m"], radius, abs_tol=1e-12)
        and start < slot0 < slotend < start + chord
    ):
        raise ValueError("Unexpected shell/slot geometry")
    lengths = [slot0 - start, start + chord - slotend]
    measured = supported_area(radius, y0, y1, half, chord, slotlen) * 1e6
    expected = {
        x["a"]: x["coincident_area_mm2"]
        for x in brep["interfaces"]
        if x["b"] == "shell" and x["a"].startswith("foot_bond_")
    }
    if (
        set(expected) != {"foot_bond_-1", "foot_bond_1"}
        or max(abs(measured - v) for v in expected.values()) > cfg["area_tolerance_mm2"]
    ):
        raise ValueError("Analytic clipped area disagrees with BRep")
    faces = old["source_tab_potting_rigid_frame_proxy"]["actual_tab_faces"]
    force = fin_rec["selected_force_n"]
    load = np.array([0.0, force, force * span / 2])
    young = mat["hot_adhesive_youngs_pa_estimate"]
    poisson = mat["adhesive_poisson_estimate"]
    shear = young / (2 * (1 + poisson))
    df = mat["design_factor"]
    if df != 3 or not np.allclose(
        load, prior["load_coordinates"]["resultants_Fx_Fy_Mz"], rtol=0, atol=1e-10
    ):
        raise ValueError("Historical load or factor mismatch")
    # Independently known rectangle: axial width W, in-plane depth D.
    W, D, gap = 0.1, 0.005, 0.0002
    matrix, _ = finite_contact_matrix(
        [
            {
                "varying_axis": "y",
                "interval_m": [-D / 2, D / 2],
                "fixed_coordinate_m": 0.0,
                "normal": [1, 0],
                "gap_m": gap,
                "axial_width_m": W,
            }
        ],
        young,
        shear,
        16,
    )
    exact = np.diag([young * W * D / gap, shear * W * D / gap, young * W * D**3 / (12 * gap)])
    fixture = float(np.max(np.abs(matrix - exact)) / np.max(np.abs(exact)))
    if fixture > 1e-12:
        raise ValueError("Known planar patch failed")
    rows = []
    for foot in fin_rec["curved_foot_bond_upper_stiffness_sensitivity"]:
        thickness = foot["bondline_m"]
        for n in cfg["quadrature_levels"]:
            tab, _ = finite_contact_matrix(faces, young, shear, n)
            full, full_patches = foot_matrix(
                radius, y0, y1, [(y0, chord)], young, poisson, thickness, n
            )
            clipped, patches = foot_matrix(
                radius, y0, y1, [(y0, sum(lengths)), (half, slotlen)], young, poisson, thickness, n
            )
            archival = next(
                x
                for x in prior["contact_matrix_levels"]
                if math.isclose(x["bondline_m"], thickness, abs_tol=1e-12)
                and x["quadrature_per_patch"] == n
            )
            matrix_error = float(
                np.max(np.abs(full - np.array(archival["foot_K"])))
                / np.max(np.abs(archival["foot_K"]))
            )
            tab_error = float(
                np.max(np.abs(tab - np.array(archival["tab_K"])))
                / np.max(np.abs(archival["tab_K"]))
            )
            full_u = np.linalg.solve(full + tab, load)
            clip_u = np.linalg.solve(clipped + tab, load)
            prior_u = np.array(archival["root_motion"])
            motion_error = float(np.max(np.abs(full_u - prior_u)) / np.max(np.abs(prior_u)))
            if (
                max(matrix_error, tab_error, motion_error)
                > cfg["history_reproduction_relative_tolerance"]
            ):
                raise ValueError("Original matrix or motion did not reproduce")
            branch_f = clipped @ clip_u
            branch_t = tab @ clip_u
            res = branch_f + branch_t - load
            if max(abs(res)) > cfg["balance_absolute_tolerance"]:
                raise ValueError("Clipped force/moment balance failed")
            rows.append(
                {
                    "bondline_m": thickness,
                    "quadrature_points": n,
                    "full_foot_matrix": full.tolist(),
                    "clipped_foot_matrix": clipped.tolist(),
                    "tab_matrix": tab.tolist(),
                    "full_motion": full_u.tolist(),
                    "clipped_motion": clip_u.tolist(),
                    "full_foot_resultant": (full @ full_u).tolist(),
                    "full_tab_resultant": (tab @ full_u).tolist(),
                    "clipped_foot_resultant": branch_f.tolist(),
                    "clipped_tab_resultant": branch_t.tolist(),
                    "clipped_force_moment_residual": res.tolist(),
                    "full_reproduction": {
                        "foot_matrix_relative_error": matrix_error,
                        "tab_matrix_relative_error": tab_error,
                        "motion_relative_error": motion_error,
                    },
                    "full_integrated_area_each_mm2": sum(p[-1] for p in full_patches) / 2 * 1e6,
                    "clipped_integrated_area_each_mm2": sum(p[-1] for p in patches) / 2 * 1e6,
                    "clipped_smooth_foot_traction": traction_extrema(
                        radius, [(y0, y1), (half, y1)], young, poisson, thickness, clip_u
                    ),
                    "full_smooth_tab_traction": tab_traction_extrema(faces, young, shear, full_u),
                    "clipped_smooth_tab_traction": tab_traction_extrema(
                        faces, young, shear, clip_u
                    ),
                    "full_smooth_foot_traction": traction_extrema(
                        radius, [(y0, y1)], young, poisson, thickness, full_u
                    ),
                    "full_added_tip_m": float(full_u[1] + span * full_u[2]),
                    "clipped_added_tip_m": float(clip_u[1] + span * clip_u[2]),
                }
            )
    for foot in fin_rec["curved_foot_bond_upper_stiffness_sensitivity"]:
        levels = [
            r for r in rows if math.isclose(r["bondline_m"], foot["bondline_m"], abs_tol=1e-12)
        ]
        u64, u32 = (np.array(levels[-i]["clipped_motion"]) for i in (1, 2))
        rel = float(np.max(np.abs(u64 - u32)) / np.max(np.abs(u64)))
        if rel > cfg["quadrature_relative_tolerance"]:
            raise ValueError("Clipped quadrature did not converge")
        levels[-1]["final_two_motion_relative_change"] = rel
    result = {
        "status": "clipped_ideal_sensitivity_completed_not_installed_acceptance",
        "accepted": False,
        "flight_ready": False,
        "input_sha256_before": hashes,
        "input_sha256_after": {p: sha(ROOT / p) for p in hashes},
        "candidate_identity": ident,
        "geometry": {
            "radius_m": radius,
            "foot_y_interval_m": [y0, y1],
            "root_interval_m": [start, start + chord],
            "slot_interval_m": [slot0, slotend],
            "slot_half_width_m": half,
            "two_uncut_end_lengths_m": lengths,
            "analytic_supported_area_each_mm2": measured,
            "brep_common_area_each_mm2": expected,
            "source_shell_is_current_generated_historical_brep_unproved": True,
        },
        "known_planar_matrix_relative_error": fixture,
        "force_Fx_Fy_Mz": load.tolist(),
        "young_pa": young,
        "poisson": poisson,
        "DF_strength_only": df,
        "levels": rows,
        "base_panel_tip_m": fin_rec["layered_panel_quadrature_levels"][-1][
            "panel_only_tip_deflection_m"
        ],
        "actual_body_frame_compliance": None,
        "edge_peel_allowable": None,
        "adhesive_bridging": None,
        "conservative_full_3d_bound": False,
        "face_bond_actual_wetting": None,
        "wall_s": time.monotonic() - begin,
        "cpu_s": time.process_time() - cpu,
        "peak_rss_bytes_macos": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    result["inputs_unchanged"] = result["input_sha256_before"] == result["input_sha256_after"]
    if not result["inputs_unchanged"]:
        raise ValueError("Inputs changed")
    write(out / "record.json", result)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/studies/wo03-clipped-foot-contact.yaml"
    )
    parser.add_argument("--preset", choices=["tiny"], default="tiny")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    out = args.output or ROOT / cfg["default_output"]
    paths = [
        args.config,
        Path(__file__),
        ROOT / "src/analysis/fin_contact.py",
        ROOT / "src/vehicle/schema.py",
        ROOT / "src/vehicle/cad_contract.py",
        ROOT / "src/vehicle/geometry.py",
        *sorted((ROOT / "src/cad").glob("*_parts.py")),
        ROOT / "src/cad/parts.py",
    ] + [
        ROOT / cfg[k]
        for k in ("candidate", "fin_record", "prior_contact", "prior_root", "face_audit")
    ]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    for key, expected in cfg["expected_sha256"].items():
        if sha(ROOT / cfg[key]) != expected:
            raise ValueError(f"Source hash mismatch: {key}")
    if args.worker:
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (cfg["budget"]["child_cpu_seconds"], cfg["budget"]["child_cpu_seconds"]),
        )
        worker(cfg, out, hashes)
        return
    out.mkdir(parents=True, exist_ok=False)
    before = resource.getrusage(resource.RUSAGE_CHILDREN)
    start = time.monotonic()
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--worker",
                "--config",
                str(args.config),
                "--output",
                str(out),
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=cfg["budget"]["child_wall_seconds"],
            check=False,
        )
        (out / "worker.log").write_text(proc.stdout)
        code = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as e:
        (out / "worker.log").write_bytes(e.stdout or b"")
        code = None
        timed_out = True
    after = resource.getrusage(resource.RUSAGE_CHILDREN)
    used = after.ru_utime + after.ru_stime - before.ru_utime - before.ru_stime
    write(
        out / "completion.json",
        {
            "returncode": code,
            "timed_out": timed_out,
            "wall_s": time.monotonic() - start,
            "child_cpu_s": used,
            "child_max_rss_bytes_macos": after.ru_maxrss,
            "complete": code == 0 and not timed_out,
        },
    )
    if code != 0 or timed_out or used > cfg["budget"]["packet_cpu_seconds"]:
        raise SystemExit("Stopped; preserve evidence, no automatic retry")


if __name__ == "__main__":
    main()
