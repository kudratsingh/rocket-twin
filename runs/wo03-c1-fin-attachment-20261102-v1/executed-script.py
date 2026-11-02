"""One bounded C1/R1 installed-attachment admission screen, not an FE solver."""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import resource
import shutil
import signal
import sys
import time
import traceback
from pathlib import Path

for name in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ[name] = "1"
CPU_START, WALL_START = time.process_time(), time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
signal.setitimer(signal.ITIMER_REAL, 30)

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-c1-fin-attachment.yaml"
OUT = ROOT / "runs/wo03-c1-fin-attachment-20261102-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def integral(y, x):
    return float(np.sum((y[1:] + y[:-1]) * np.diff(x) / 2))


def beam(span, root, tip, pressure, rigidity_per_width, points):
    """Euler-Bernoulli strip, exact distributed-load moment, numerical curvature."""
    s = np.linspace(0, span, points)
    k = (tip - root) / span
    chord = root + k * s
    h = span - s
    moment = pressure * (chord * h**2 / 2 + k * h**3 / 3)
    shear = pressure * (chord * h + k * h**2 / 2)
    curvature = moment / (chord * rigidity_per_width)
    return {
        "tip_m": integral((span - s) * curvature, s),
        "tip_slope_rad": integral(curvature, s),
        "root_moment_Nm": float(moment[0]),
        "force_N": float(shear[0]),
    }


def panel(cfg, state, reinforced, points, pressure):
    f = cfg["fin"]
    span, root, tip, _ = [v / 1000 for v in f["span_root_tip_sweep_mm"]]
    t = f["panel_thickness_nominal_min_mm"][1] / 1000
    ew = f["plywood_E_cold_hot_pa"][state]
    dw = ew * t**3 / 12
    d, ec, face_t, face_z = dw, 0.0, 0.0, 0.0
    if reinforced:
        r = cfg["R1"]
        face_t = r["carbon"]["nominal_actual_min_max_mm"][1] / 1000
        bond = r["face_bond_nominal_min_max_mm"][1] / 1000
        ec = r["carbon"]["E_cold_hot_estimate_pa"][state]
        face_z = t / 2 + bond + face_t / 2
        d += 2 * ec * (face_t**3 / 12 + face_t * face_z**2)
    b = beam(span, root, tip, pressure, d, points)
    factor = f["force_case"]["design_factor_once"]
    curvature = b["root_moment_Nm"] * factor / (root * d)
    b.update(
        {
            "rigidity_per_width_Nm": d,
            "wood_DF3_root_stress_pa": ew * t / 2 * curvature,
            "wood_estimated_strength_ratio": f["plywood_strength_cold_hot_pa"][state]
            / (ew * t / 2 * curvature),
            "carbon_DF3_root_stress_pa": ec * (face_z + face_t / 2) * curvature,
            "carbon_face_bond_DF3_root_sliding_pa": factor
            * b["force_N"]
            * ec
            * face_t
            * face_z
            / (root * d),
            "bond_peel_capacity": None,
            "strip_limitations": "Spanwise linear beam only: sweep/two-dimensional plate coupling, skin wrinkling/delamination, shear compliance and actual root are not qualified.",
        }
    )
    return b


def attachment(cfg, moment, force, reinforced):
    s, r = cfg["socket"], cfg["receiver"]
    depth, width = s["depth_mm"] / 1000, s["width_mm"] / 1000
    # Root at body R33; socket contact 18.3..30.3, centroid R24.3.
    arm = (33 - 24.3) / 1000
    transmitted = moment + force * arm
    positive, negative = 2 * transmitted / depth + force / 2, 2 * transmitted / depth - force / 2
    area = width * depth / 2
    thickness = s["R1_cheek_thickness_mm" if reinforced else "C1_cheek_thickness_mm"] / 1000
    # Most loaded cheek, uniform contact over outer half-depth.
    # Simply-supported end reactions F/4,3F/4; Mmax=9 F L/64.
    ss_moment, cantilever_moment = 9 * positive * depth / 64, positive * 3 * depth / 4
    cheek_ss_stress = 6 * ss_moment / (width * thickness**2)
    cheek_cantilever_stress = 6 * cantilever_moment / (width * thickness**2)
    output = {
        "reference_root_moment_DF3_Nm": moment,
        "extra_root_to_contact_center_m": arm,
        "socket_center_moment_DF3_Nm": transmitted,
        "contact_positive_negative_N": [positive, negative],
        "half_depth_contact_area_m2": area,
        "contact_mean_pressures_pa": [positive / area, negative / area],
        "contact_peak_pressure_and_directional_capacity": None,
        "force_residual_N": positive - negative - force,
        "moment_residual_Nm": (positive + negative) * depth / 4 - transmitted,
        "cheek_ideal_simply_supported_bending_pa": cheek_ss_stress,
        "cheek_outer_support_lost_bending_pa": cheek_cantilever_stress,
        "cheek_hot_estimate_ratios_ss_support_lost": [
            s["strength_cold_hot_pa"][1] / cheek_ss_stress,
            s["strength_cold_hot_pa"][1] / cheek_cantilever_stress,
        ],
        "outer_bridge_reaction_DF3_N": 0.75 * positive,
        "inner_floor_reaction_DF3_N": 0.25 * positive,
        "cheek_to_bridge_min_mean_hot_bond_shear_pa": 0.75 * positive / (width * thickness),
        "bridge_or_receiver_peel_and_bending": "Unavailable: finite attachment/contact solution needed; no grounded bridge.",
    }
    rt = r["R1_thickness_mm" if reinforced else "C1_thickness_mm"] / 1000
    ro, ri = r["radius_mm"] / 1000, r["radius_mm"] / 1000 - rt
    j = math.pi * (ro**4 - ri**4) / 2
    left, right = (1140 - 1010) / 1000, (1211.8 - 1140) / 1000
    eh = s["E_cold_hot_pa"][1]
    gh = eh / (2 * (1 + s["poisson"]))
    upper_k = gh * j * (1 / left + 1 / right)
    play = s["R1_total_finished_play_mm" if reinforced else "C1_total_finished_play_mm"] / 1000
    lever = 0.09 + arm
    output.update(
        {
            "receiver_unslotted_torsional_J_m4": j,
            "receiver_hot_upper_stiffness_Nm_rad": upper_k,
            "receiver_ideal_end_fixed_service_tip_motion_m": moment / 3 / upper_k * lever,
            "socket_play_only_tip_motion_m": play / depth * lever,
            "old_M3_radial_freeplay_m": (r["M3_bore_shaft_mm"][0] - r["M3_bore_shaft_mm"][1])
            / 2000,
            "old_M3_end_freeplay_tip_motion_m": (
                r["M3_bore_shaft_mm"][0] - r["M3_bore_shaft_mm"][1]
            )
            / 2000
            / (r["end_bolt_radius_mm"] / 1000)
            * lever,
            "support_flexibility": "Tube stiffness is an upper bound for uncut tube and rigid ends, not installed strength. End-joint and local ring/socket compliance remain finite and unknown.",
            "single_fin_factored_transverse_end_reactions_N": [
                force * right / (left + right),
                force * left / (left + right),
            ],
            "single_fin_end_torques_ideal_stiffness_share_Nm": [
                transmitted * right / (left + right),
                transmitted * left / (left + right),
            ],
            "bond_peel_capacity": None,
        }
    )
    return output


def reinforcement_ledger(cfg):
    r, s = cfg["R1"], cfg["socket"]
    rho = s["G11_density_kg_m3"]
    rows = []

    def add(identifier, grams, station, basis):
        rows.append({"id": identifier, "mass_g": grams, "station_mm": station, "basis": basis})

    # Full panel faces and full root tab faces, no removal credit for overlap.
    panel_area, tab_area = 3 * 0.09 * (0.12 + 0.06) / 2, 3 * 0.1 * 0.0147
    panel_station = 1144.4444444444443
    for identifier, area, station in (
        ("panel", panel_area, panel_station),
        ("tab", tab_area, 1140),
    ):
        add(
            f"R1_carbon_{identifier}_faces",
            2 * area * r["carbon"]["areal_mass_kg_m2"] * 1000,
            station,
            "Two full faces; supplier typical areal mass, not a measured bound",
        )
        add(
            f"R1_{identifier}_face_bond",
            2
            * area
            * r["face_bond_nominal_min_max_mm"][0]
            / 1000
            * r["adhesive_density_kg_m3"]
            * 1000,
            station,
            "Separate controlled adhesive layers, no double credit of source bond allocation",
        )
    add(
        "R1_face_finish",
        r["finish_g"],
        panel_station,
        "Additional sealing/finishing, original finish retained",
    )
    delta = s["R1_cheek_thickness_mm"] - s["C1_cheek_thickness_mm"]
    add(
        "R1_six_cheek_thickness_increments",
        6 * 100 * 12 * delta * rho * 1e-6,
        1140,
        "Original 2 mm cheeks retained in base; charge 1 mm added",
    )
    gap = r["socket_gap_nominal_tolerance_mm"][0]
    old_outer, new_outer = 10.95, gap + 2 * s["R1_cheek_thickness_mm"]
    add(
        "R1_three_wider_floors",
        3 * 100 * (new_outer - old_outer) * 2 * rho * 1e-6,
        1140,
        "Preserve full support floor under wider socket",
    )
    add(
        "R1_three_wider_pads",
        3 * 100 * (new_outer - old_outer) * 0.9 * rho * 1e-6,
        1140,
        "No thickness reduction credit before actual geometry",
    )
    add(
        "R1_six_wider_outer_bridges",
        6 * 100 * 2 * delta * rho * 1e-6,
        1140,
        "Bridge footprint widened with cheek, still needs actual bending/peel solution",
    )
    ro, length = cfg["receiver"]["radius_mm"], cfg["receiver"]["length_mm"]
    old_t, new_t = cfg["receiver"]["C1_thickness_mm"], cfg["receiver"]["R1_thickness_mm"]
    add(
        "R1_closed_receiver_thickness_increment",
        math.pi * ((ro - old_t) ** 2 - (ro - new_t) ** 2) * length * rho * 1e-6,
        1110.9,
        "Outer radius fixed; no hole or slot mass credit",
    )
    keys = r["end_keys"]
    for end in range(2):
        add(
            f"R1_three_end_keys_{end}",
            3 * math.prod(keys["axial_radial_tangential_mm"]) * rho * 1e-6,
            keys["station_mm"][end],
            "Three positive cap/receiver antirotation keys per end, actual attachment unqualified",
        )
    add(
        "R1_added_key_retention_bond",
        r["extra_key_retention_and_bond_g"],
        1110.9,
        "Added to existing screw and process allocations; no credit for removed holes",
    )
    add(
        "R1_selectable_shim_stock",
        3 * 100 * 12 * r["max_selectable_shim_total_mm"] * rho * 1e-6,
        1140,
        "Maximum aggregate thickness at each of three roots, source shims retained without credit",
    )
    return rows


def main():
    if OUT.exists():
        raise FileExistsError(f"Refusing overwrite: {OUT}")
    OUT.mkdir(parents=True)
    shutil.copy2(CONFIG, OUT / "executed-config.yaml")
    shutil.copy2(Path(__file__), OUT / "executed-script.py")
    cfg = yaml.safe_load(CONFIG.read_text())
    src_path = ROOT / cfg["source_record"]
    if sha(src_path) != cfg["source_record_sha256"]:
        raise ValueError("Selected C1 record hash mismatch")
    src = json.loads(src_path.read_text())
    baseline = {x["id"]: x for x in src["mass_scenario_results"]}
    nominal = baseline["C1_clipped_fins_no_ballast"]
    adverse = baseline["C1_clipped_fins_plus20g_and_motorCG_probe"]
    if not math.isclose(nominal["loaded_mass_kg"], 1.1298067509765393, abs_tol=1e-12):
        raise ValueError("C1 mass identity mismatch")
    if cfg["criteria"]["growth_g"] != 50:
        raise ValueError("Separate full 50 g allowance changed")
    inputs = {
        str(CONFIG.relative_to(ROOT)): sha(CONFIG),
        cfg["source_record"]: sha(src_path),
        cfg["source_lock"]: sha(ROOT / cfg["source_lock"]),
        "scripts/wo03_c1_fin_attachment.py": sha(Path(__file__)),
    }
    points = cfg["budget"]["integration_points"]
    # Independent textbook uniform rectangular cantilever result q L^4/(8 E I).
    length, width, thickness, young, pressure = 0.1, 0.08, 0.006, 1e9, 1000
    exact = 1.5 * pressure * length**4 / (young * thickness**3)
    known = [
        {
            "points": n,
            "tip_m": beam(length, width, width, pressure, young * thickness**3 / 12, n)["tip_m"],
        }
        for n in points
    ]
    known_error = abs(known[-1]["tip_m"] / exact - 1)
    if known_error > cfg["criteria"]["known_answer_relative_error"]:
        raise ValueError("Known rectangular strip failed")
    loads = nominal["fin_load_screen"]
    force, moment = loads["DF3_once_force_per_fin_N"], loads["DF3_once_root_moment_per_fin_Nm"]
    pressure = loads["normal_force_per_fin_unfactored_N"] / loads["planform_area_per_fin_m2"]
    structures = {}
    for identifier, reinforced in (("C1", False), ("R1", True)):
        states = []
        for state in range(2):
            levels = [panel(cfg, state, reinforced, n, pressure) for n in points]
            change = abs(levels[-1]["tip_m"] / levels[-2]["tip_m"] - 1)
            if change > cfg["criteria"]["quadrature_final_change_fraction"]:
                raise ValueError("Fin strip quadrature refinement failed")
            states.append(
                {
                    "state": cfg["budget"]["material_states"][state],
                    "levels": levels,
                    "final_relative_change": change,
                }
            )
        path = attachment(cfg, moment, force, reinforced)
        if abs(path["force_residual_N"]) > 1e-9 or abs(path["moment_residual_Nm"]) > 1e-9:
            raise ValueError("Contact force/moment balance failed")
        minimum_tip = (
            states[1]["levels"][-1]["tip_m"]
            + path["socket_play_only_tip_motion_m"]
            + path["receiver_ideal_end_fixed_service_tip_motion_m"]
        )
        path["hot_panel_plus_socket_play_plus_ideal_receiver_tip_m"] = minimum_tip
        path["remaining_1mm_for_all_other_support_motion_m"] = 0.001 - minimum_tip
        rt, ro = (
            cfg["receiver"]["R1_thickness_mm" if reinforced else "C1_thickness_mm"] / 1000,
            cfg["receiver"]["radius_mm"] / 1000,
        )
        ideal_buckle = (
            cfg["socket"]["E_cold_hot_pa"][1]
            / math.sqrt(3 * (1 - cfg["socket"]["poisson"] ** 2))
            * rt
            / (ro - rt / 2)
        )
        structures[identifier] = {
            "panel_states": states,
            "attachment": path,
            "receiver_unslotted_ideal_axial_buckling_pa": ideal_buckle,
            "exploratory_knocked_down_buckling_pa": [
                ideal_buckle * k for k in cfg["receiver"]["buckling_imperfection_factors"]
            ],
            "installed_strength_deflection_and_flutter_accepted": False,
        }
    rows = reinforcement_ledger(cfg)
    extra_g = sum(x["mass_g"] for x in rows)
    extra_moment = sum(x["mass_g"] / 1000 * x["station_mm"] / 1000 for x in rows)
    staged = ROOT / cfg["staged_checkout"]
    for rel, expected in src["input_sha256"].items():
        if rel.startswith(cfg["staged_checkout"] + "/") and sha(ROOT / rel) != expected:
            raise ValueError(f"Saved guide helper changed: {rel}")
    inputs.update(
        {p: v for p, v in src["input_sha256"].items() if p.startswith(cfg["staged_checkout"] + "/")}
    )
    source_spec = ROOT / cfg["source_spec"]
    inputs[cfg["source_spec"]] = sha(source_spec)
    sys.path.insert(0, str(staged))
    os.chdir(staged)
    from src.vehicle.benchmark import screen_launch
    from src.vehicle.schema import Vehicle

    vehicle = Vehicle.model_validate(yaml.safe_load(source_spec.read_text()))
    cases = []
    for base, reinforced in ((nominal, False), (adverse, False), (nominal, True), (adverse, True)):
        mass = base["loaded_mass_kg"] + (extra_g / 1000 if reinforced else 0)
        first = base["loaded_first_moment_kg_m"] + (extra_moment if reinforced else 0)
        burnout_mass = base["burnout_mass_kg"] + (extra_g / 1000 if reinforced else 0)
        burnout_first = base["burnout_first_moment_kg_m"] + (extra_moment if reinforced else 0)
        cg, burnout_cg = 1000 * first / mass, 1000 * burnout_first / burnout_mass
        guides = copy.deepcopy(base["guide_screens"])
        if reinforced:
            guides = []
            for usable in cfg["budget"]["guide_probes_m"]:
                candidate = copy.deepcopy(vehicle)
                candidate.design.rail_length_m = usable
                guide = screen_launch(candidate, study_nominal_mass_kg=mass - 0.05)
                guides.append({"usable_m": usable, **guide})
        for guide in guides:
            speed = guide["rail_exit_speed_mps"]
            guide.update(
                {"formal_speed_margin_mps": speed - 15, "planning_speed_margin_mps": speed - 15.5}
            )
        severe = 3 * mass * (20.4**2 / (2 * 0.3) + 9.80665)
        area = math.pi * ((0.032) ** 2 - (0.032 - (0.001 if reinforced else 0.0008)) ** 2)
        path = structures["R1" if reinforced else "C1"]["attachment"]
        # Full load at one end screw is explicit unequal-load sensitivity, not an asserted installed reaction.
        cap_stress = severe / (math.pi * 0.003**2 / 4)
        base_fin_mass = (110.328075 + 17.210 + 11.850) / 3000
        face_fin_extra = (
            sum(
                x["mass_g"]
                for x in rows
                if "face" in x["id"] or "bond" in x["id"] and "key" not in x["id"]
            )
            / 3000
            if reinforced
            else 0
        )
        fin_axial = severe / mass * (base_fin_mass + face_fin_extra)
        cases.append(
            {
                "id": ("R1" if reinforced else "C1")
                + ("_plus20g_motorCG_probe" if base is adverse else "_nominal"),
                "nominal_without_growth_g": mass * 1000 - 50,
                "separate_growth_g": 50,
                "extra_aft_g": 20 if base is adverse else 0,
                "total_with_growth_g": mass * 1000,
                "cg_mm": cg,
                "burnout_cg_mm": burnout_cg,
                "cp_mm": base["cp_mm"],
                "static_margin_cal": (base["cp_mm"] - cg) / 66,
                "burnout_static_margin_cal": (base["cp_mm"] - burnout_cg) / 66,
                "guide_screens": guides,
                "illustrative_1p971m_formal_headroom_g": 1219.953265786171 - mass * 1000,
                "illustrative_1p971m_planning_headroom_g": 1152.315473556519 - mass * 1000,
                "headroom_basis": "Reused lower-pass endpoints of saved S3/Sol same guide-model mass roots; no new rail equipment claim",
                "severe_recovery_DF3_mean_N": severe,
                "nominal_5m_s_recovery_DF3_mean_N": 3 * mass * (5**2 / 0.6 + 9.80665),
                "fin_axial_recovery_DF3_inertia_N": fin_axial,
                "fin_pin_5mm_double_shear_pa": fin_axial / (2 * math.pi * 0.005**2 / 4),
                "fin_tab_pin_bearing_pa": fin_axial / (0.005 * 0.0063),
                "fin_tab_axial_end_tearout_pa": fin_axial / (2 * (0.010 - 0.0053 / 2) * 0.0063),
                "fin_pin_capacity": "Unavailable: direction/hot ply bearing and tearout, pin grade and finished fit are not qualified",
                "receiver_full_recovery_mean_axial_stress_pa": severe / area,
                "receiver_half_effective_section_stress_pa": severe / (area * 0.5),
                "single_M3_full_recovery_tensile_pa": cap_stress,
                "single_M3_200MPa_estimate_ratio": 200e6 / cap_stress,
                "body_0p5mm_full_load_membrane_pa": severe / (2 * math.pi * 0.03275 * 0.0005),
                "body_path_status": "Full-load value is a conservative sensitivity; exact participating component branches and body/upper connections remain unresolved, not automatically all parachute tension in paper.",
                "full_intrinsic_inertia_kg_m2": None,
                "added_item_axial_point_distribution_transverse_I_kg_m2": (
                    sum(
                        x["mass_g"] / 1000 * (x["station_mm"] / 1000 - cg / 1000) ** 2 for x in rows
                    )
                    if reinforced
                    else 0
                ),
                "inertia_status": "Added-item axial point contribution only; source intrinsic and radial tensors unavailable, not a full vehicle inertia",
                "installed_acceptance": False,
            }
        )
    r = cfg["R1"]
    c_min, c_max = cfg["fin"]["controlled_tab_min_max_mm"]
    t_min, t_max = r["carbon"]["nominal_actual_min_max_mm"][1:]
    b_min, b_max = r["face_bond_nominal_min_max_mm"][1:]
    gap, tolerance = r["socket_gap_nominal_tolerance_mm"]
    fit = {
        "finished_root_min_max_mm": [c_min + 2 * t_min + 2 * b_min, c_max + 2 * t_max + 2 * b_max],
        "socket_min_max_mm": [gap - tolerance, gap + tolerance],
        "minimum_cold_total_gap_mm": gap - tolerance - c_max - 2 * t_max - 2 * b_max,
        "maximum_cold_total_gap_mm": gap + tolerance - c_min - 2 * t_min - 2 * b_min,
        "hot_and_assembly_acceptance": "Unavailable: adhesive/carbon transverse expansion, hot creep, shim retention, actual key/socket alignment and assembly not verified",
    }
    record = {
        "id": cfg["id"],
        "status": "preflight_complete_R1_not_admitted_no_active_change",
        "input_sha256": inputs,
        "known_rectangular_beam": {
            "exact_tip_m": exact,
            "levels": known,
            "final_relative_error": known_error,
        },
        "load_case": {
            "q_pa": 40000,
            "alpha_deg": 5,
            "force_unfactored_N": force / 3,
            "moment_unfactored_Nm": moment / 3,
            "force_DF3_once_N": force,
            "moment_DF3_once_Nm": moment,
            "load_validity": "Retained starting static screen, not a C1 trajectory maximum. No factor applied twice; installed gust/large-angle dynamics remain open.",
        },
        "structures": structures,
        "R1_added_ledger": rows,
        "R1_added_mass_g": extra_g,
        "coupled_cases": cases,
        "R1_fit": fit,
        "decision": "STOP_R1_before_CAD_native_analysis: conditional planning budget exceeded, finite bridge/body/end and thermal/flutter evidence unresolved. One next scoped correction is a lightweight sandwich fin with dense root insert, not thinner unsupported root or relaxed loads.",
        "thermal_packing_motor_service": "No new temperature/clearance result. Thicker receiver moves inner wall inward 0.2 mm; wider socket, new end keys and root skins need actual motor/strap/baffle/wiring clearance. Existing required thermal matrix, 300C/dirty foil/35C and 45C screen unchanged. New glue/skin/key heat routes have no compatible overlay.",
        "flutter": "Unavailable for C1/R1 installed geometry; changed span/sweep/root/receiver and layered R1 invalidate transfer of older isolated panel/NACA screen. Need installed bending/torsion modes, root compliance, damping and speed envelope before flutter acceptance.",
        "resources": {
            "cpu_s": time.process_time() - CPU_START,
            "wall_s": time.monotonic() - WALL_START,
            "cpu_limit_s": 20,
            "wall_limit_s": 30,
            "requested_threads": 1,
            "CAD_FEA_heat_free_flight_executed": False,
        },
    }
    if any(sha(ROOT / path) != value for path, value in inputs.items()):
        raise ValueError("Input changed during packet")
    dump(OUT / "record.json", record)
    print(
        json.dumps(
            {
                "status": record["status"],
                "added_g": extra_g,
                "resources": record["resources"],
                "output": str(OUT),
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        if OUT.exists():
            dump(
                OUT / "failure.json",
                {
                    "traceback": traceback.format_exc(),
                    "cpu_s": time.process_time() - CPU_START,
                    "wall_s": time.monotonic() - WALL_START,
                    "automatic_retry": False,
                },
            )
        raise
