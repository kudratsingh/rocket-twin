"""One C2 sandwich/captured-socket admission packet; no CAD or native solver."""

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
from pathlib import Path

for name in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ[name] = "1"
START_CPU, START_WALL = time.process_time(), time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
signal.setitimer(signal.ITIMER_REAL, 30)

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "configs/studies/wo03-c2-sandwich-socket.yaml"
OUT = ROOT / "runs/wo03-c2-sandwich-socket-20261102-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def trap(y, x):
    return float(np.sum((y[1:] + y[:-1]) * np.diff(x) / 2))


def rectangle(radial_start, radial_end, half_width, angle):
    a = math.radians(angle)
    return [
        (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))
        for x, y in [
            (radial_start, -half_width),
            (radial_end, -half_width),
            (radial_end, half_width),
            (radial_start, half_width),
        ]
    ]


def polygons_overlap(a, b):
    for polygon in (a, b):
        for p, q in zip(polygon, polygon[1:] + polygon[:1]):
            normal = (p[1] - q[1], q[0] - p[0])
            pa = [x * normal[0] + y * normal[1] for x, y in a]
            pb = [x * normal[0] + y * normal[1] for x, y in b]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return False
    return True


def point_segment(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def polygon_gap(a, b):
    if polygons_overlap(a, b):
        return 0.0
    return min(
        point_segment(p, x, y)
        for p in a + b
        for polygon in (b if p in a else a,)
        for x, y in zip(polygon, polygon[1:] + polygon[:1])
    )


def main():
    if OUT.exists():
        raise FileExistsError(f"Refusing overwrite: {OUT}")
    OUT.mkdir(parents=True)
    shutil.copy2(CFG, OUT / "executed-config.yaml")
    shutil.copy2(Path(__file__), OUT / "executed-script.py")
    cfg = yaml.safe_load(CFG.read_text())
    if sha(ROOT / cfg["source_c1"]) != cfg["source_sha256"]:
        raise ValueError("Frozen C1 record changed")
    c1 = json.loads((ROOT / cfg["source_c1"]).read_text())
    r1 = json.loads((ROOT / cfg["source_r1"]).read_text())
    sources = {
        str(CFG.relative_to(ROOT)): sha(CFG),
        "scripts/wo03_c2_sandwich_socket.py": sha(Path(__file__)),
        **{
            cfg[k]: sha(ROOT / cfg[k])
            for k in ("source_c1", "source_r1", "source_config", "source_spec")
        },
    }
    f, s, j = cfg["fin"], cfg["socket"], cfg["receiver_connections"]
    base = c1["mass_scenario_results"][2]
    adverse = c1["mass_scenario_results"][3]
    force = base["fin_load_screen"]["DF3_once_force_per_fin_N"]
    root_moment = base["fin_load_screen"]["DF3_once_root_moment_per_fin_Nm"]
    socket_moment = root_moment + force * 0.0087
    axis_moment = root_moment + force * 0.033
    positive, negative = (
        2 * socket_moment / 0.012 + force / 2,
        2 * socket_moment / 0.012 - force / 2,
    )
    rows = []

    def add(identifier, grams, station, function, basis):
        rows.append(
            {
                "id": identifier,
                "mass_delta_g": grams,
                "station_mm": station,
                "function": function,
                "basis": basis,
            }
        )

    # Credit only the exact replaced named components, preserving the closed receiver and all end hardware.
    for old in c1["added_c1_components"]:
        if (
            any(
                text in old["id"]
                for text in (
                    "fin_socket_side_plate",
                    "fin_socket_floor",
                    "fin_socket_outer_bridge",
                    "radial_mount_pad",
                )
            )
            or old["id"] == "C1_socket_joint_process_hardware"
        ):
            add(
                "remove_" + old["id"],
                -old["mass_g"],
                old["station_mm"],
                "Replaced by integral cartridge, receiver fasteners and explicit process reserve",
                old["basis"],
            )
    accounting = c1["fin_panel_accounting"]
    old_fin = (
        accounting["new_panel_mass_g"]
        + accounting["original_fin_CAD_residual_retained_g"]
        + sum(x["mass_g"] for x in accounting["S3_deeper_tab_delta_rows_retained_once"])
    )
    old_fin_moment_g_mm = (
        accounting["new_panel_mass_g"] * accounting["new_panel_centroid_mm"]
        + (old_fin - accounting["new_panel_mass_g"]) * 1140
    )
    add(
        "remove_C1_full_fin_set",
        -old_fin,
        old_fin_moment_g_mm / old_fin,
        "Panel/tab/gussets replaced by sandwich, full dense root, captured socket and positive pin; original 8g fin_bonds remains a distinct potting/application reserve",
        "Exact frozen panel+CAD residual+deep-tab increment once",
    )
    if len([x for x in rows if x["id"].startswith("remove_")]) != 20:
        raise ValueError("Expected18socket rows+process row+full fin replacement")
    if f["span_root_tip_sweep_station_mm"] != [90, 120, 60, 40, 1080]:
        raise ValueError("This one packet freezes C1 planform")
    count, rho = f["count"], s["G11_density_kg_m3"]
    span, root, tip, sweep, station = f["span_root_tip_sweep_station_mm"]
    area = span * (root + tip) / 2
    band = f["dense_root_band_mm"]
    band_area = root * band + (tip - root) / span * band**2 / 2
    band_mean_s = (root * band**2 / 2 + (tip - root) / span * band**3 / 3) / band_area
    band_station = station + root / 2 + (sweep / span + (tip - root) / (2 * span)) * band_mean_s
    panel_station = accounting["new_panel_centroid_mm"]
    foam_area = area - band_area
    foam_station = (area * panel_station - band_area * band_station) / foam_area
    tab_area = math.prod(f["dense_tab_axial_radial_mm"])
    add(
        "C2_dense_root_band",
        count
        * band_area
        * f["dense_root_nominal_tolerance_mm"][0]
        * f["dense_density_kg_m3"]
        * 1e-6,
        band_station,
        "Full dense plywood root band distributes skin force",
        "Finished8mm stock/layup unconfirmed; weak-direction properties retained",
    )
    add(
        "C2_dense_through_body_tabs",
        count
        * tab_area
        * f["dense_root_nominal_tolerance_mm"][0]
        * f["dense_density_kg_m3"]
        * 1e-6,
        1140,
        "Dense root through body and existing captive5mm pin",
        "Full new tabs replace original fin residual and deeper-tab mass",
    )
    add(
        "C2_PVC_core",
        count * foam_area * f["core_nominal_tolerance_mm"][0] * f["core_density_kg_m3"] * 1e-6,
        foam_station,
        "Light core separates and supports faces",
        "Typical75kg/m3, no removed foam/edge mass credit",
    )
    for name, a, pos in (("panel", area, panel_station), ("tab", tab_area, 1140)):
        add(
            "C2_carbon_" + name,
            count * 2 * a * 1e-6 * f["skin_areal_mass_kg_m2"] * 1000,
            pos,
            "Continuous0/90 carbon faces on both sides",
            "Supplier0p5mm product0p44+/-0p1; typical areal mass, not measured bound",
        )
        add(
            "C2_face_bond_" + name,
            count
            * 2
            * a
            * f["face_bond_nominal_min_max_mm"][0]
            * f["adhesive_density_kg_m3"]
            * 1e-6,
            pos,
            "Explicit new skin/core and skin/dense-root adhesive",
            "Additional to retained original root potting reserve; no structural socket-bridge adhesive",
        )
    add(
        "C2_edge_finish",
        f["finish_seal_g"],
        panel_station,
        "Cut edge sealing and finishing",
        "Additional explicit allowance",
    )
    _floor_r, floor_w, floor_t = s["floor_radial_start_width_thickness_mm"]
    add(
        "C2_three_integral_floors",
        count * 100 * floor_w * floor_t * rho * 1e-6,
        1140,
        "Cartridge floor joins both cheeks and end attachment links",
        "No overlap or machining removal credit",
    )
    add(
        "C2_six_integral_cheeks",
        count * 2 * 100 * 12 * s["cheek_thickness_nominal_tolerance_mm"][0] * rho * 1e-6,
        1140,
        "Opposing root contact faces",
        "Integral machined G11, no narrow glued bridge strength credit",
    )
    outer, inner = s["brace_outer_radial_tangential_mm"], s["brace_inner_radial_tangential_mm"]
    brace_length = math.dist(outer, inner)
    tangent_fraction = abs(outer[1] - inner[1]) / brace_length
    add(
        "C2_six_integral_diagonal_closures",
        count
        * 2
        * 100
        * brace_length
        * s["brace_axial_width_thickness_tolerance_mm"][1]
        * rho
        * 1e-6,
        1140,
        "Triangular closure carries outer-cheek reaction into floor",
        "Closed structural triangles with fin opening; integral stock not adhesive butt joints",
    )
    lo, hi, width, axial = j["link_radial_interval_tangential_axial_mm"]
    add(
        "C2_twelve_end_links",
        j["link_count"] * (hi - lo) * width * axial * rho * 1e-6,
        1140,
        "Integral cartridge end links connect actual floor corners to receiver boss",
        "R19..28p4 links overlap floor-corner envelope; no rigid-ground substitution",
    )
    boss_ax, boss_tan, boss_rad = j["boss_axial_tangential_radial_mm"]
    add(
        "C2_twelve_boss_increments",
        j["link_count"] * (boss_ax - axial) * boss_tan * boss_rad * rho * 1e-6,
        1140,
        "Finite M3 grip/bearing bosses at cartridge ends",
        "Deduct only explicit link/boss overlap; no hole credit",
    )
    add(
        "C2_twelve_receiver_doublers",
        j["doubler_count"] * math.prod(j["doubler_axial_tangential_radial_mm"]) * rho * 1e-6,
        1140,
        "Interior receiver backing pads",
        "R28p4..30p9 meets boss at28p4; glue30p9..31p2 meets tube with no overlapping air path, no material overlap",
    )
    bond_area = 12 * 12 - math.pi * (j["hole_diameter_mm"] / 2) ** 2
    add(
        "C2_doubler_bonds",
        12 * bond_area * j["doubler_bond_nominal_mm"] * f["adhesive_density_kg_m3"] * 1e-6,
        1140,
        "Doubler-to-receiver adhesive, still an actual load path",
        "Net patch area excludes bolt hole; no duplicate air path in this glued region",
    )
    diameter, length, _ = j["bolt_shaft_diameter_finished_length_tolerance_mm"]
    hd, ht = j["bolt_head_diameter_thickness_mm"]
    wd, wi, wt = j["washer_outer_inner_thickness_mm"]
    nf, nh = j["nut_across_flats_height_mm"]
    hardware_volume = (
        math.pi * (diameter / 2) ** 2 * length
        + math.pi * (hd / 2) ** 2 * ht
        + 2 * math.pi * (wd**2 - wi**2) / 4 * wt
        + (math.sqrt(3) / 2 * nf**2 - math.pi * (diameter / 2) ** 2) * nh
    )
    add(
        "C2_twelve_finished_M3_sets",
        12 * hardware_volume * j["steel_density_kg_m3"] * 1e-6,
        1140,
        "Finished17p5mm screw, nut and two washers at every joint",
        "Geometric solid approximation; exact grade/class/head/torque and measured mass unconfirmed",
    )
    add(
        "C2_locking_service_reserve",
        j["extra_locking_service_reserve_g"],
        1140,
        "Thread locking, tool/service details and remaining process material",
        "Explicit new reserve replaces old C1 process budget",
    )
    tab_min = 7.9 + 2 * 0.34 + 2 * 0.025
    tab_max = 8.1 + 2 * 0.54 + 2 * 0.075
    channel, tol = s["channel_nominal_tolerance_mm"]
    shim_max = channel + tol - tab_min
    add(
        "C2_selected_root_shim_stock",
        3 * 100 * 12 * shim_max * rho * 1e-6,
        1140,
        "Selected root shims bring aggregate play to0p02mm",
        "Maximum full-contact G11 stock charged; source shim reserve retained",
    )
    add(
        "C2_pin_spacer_sleeves",
        6 * math.pi * (8**2 - 5.3**2) / 4 * 1.5 * rho * 1e-6,
        1180,
        "Existing26mm captive pins need added grip spacers",
        "Existing pins/cotters/washers kept; new sleeves charged",
    )
    add(
        "C2_root_band_core_butt_bonds",
        3 * (root + (tip - root) / span * band) * 8 * 0.1 * f["adhesive_density_kg_m3"] * 1e-6,
        band_station,
        "Root-band/core butt-face glue",
        "Additional to skin faces; no foam removal credit",
    )
    added_g = sum(x["mass_delta_g"] for x in rows)
    added_moment = sum(x["mass_delta_g"] * x["station_mm"] * 1e-6 for x in rows)

    for relative, expected in c1["input_sha256"].items():
        if "/checkout/" in relative:
            actual = relative.split("/checkout/", 1)[1]
            if sha(ROOT / actual) != expected:
                raise ValueError(f"Shared guide/source helper changed: {actual}")
            sources[actual] = expected
    sources["src/analysis/fin_design.py"] = sha(ROOT / "src/analysis/fin_design.py")

    # Same distributed-pressure beam equations as prior verified strip, now with core shear.
    levels = []
    pressure = force / 3 / (area * 1e-6)
    tc, ts = 7.7e-3, 0.34e-3
    skin_z = tc / 2 + 0.025e-3 + ts / 2
    rigidity = 2 * f["skin_hot_E_pa"] * (ts**3 / 12 + ts * skin_z**2)
    E, cheek_t = s["G11_hot_E_pa"], 2.8e-3
    brace_A = 0.1 * 2.2e-3
    brace_k = E * brace_A / (brace_length / 1000) * tangent_fraction**2
    for n in cfg["budget"]["integration_points"]:
        x = np.linspace(0, 0.09, n)
        chord = 0.12 - 2 / 3 * x
        remaining = 0.09 - x
        shear = pressure * (chord * remaining - remaining**2 / 3)
        moment = pressure * (chord * remaining**2 / 2 - 2 * remaining**3 / 9)
        bending = trap((0.09 - x) * moment / (chord * rigidity), x)
        core_shear = trap(shear / (5 / 6 * f["core_hot_shear_modulus_pa"] * chord * tc), x)
        z = np.linspace(0, 0.012, n)
        mpos = 0.25 * z - np.maximum(z - 0.006, 0) ** 2 / 0.012
        mneg = 0.75 * z - (np.minimum(z, 0.006) * z - np.minimum(z, 0.006) ** 2 / 2) / 0.006
        EI = E * 0.1 * cheek_t**3 / 12
        cpos, cneg = trap(mpos**2 / EI, z), trap(mneg**2 / EI, z)
        delta_pos = positive / 3 * (cpos + 0.75**2 / brace_k)
        delta_neg = negative / 3 * (cneg + 0.25**2 / brace_k)
        root_added = (delta_pos + delta_neg) / 0.006 * 0.0987
        levels.append(
            {
                "points": n,
                "panel_bending_m": bending,
                "core_shear_m": core_shear,
                "panel_total_m": bending + core_shear,
                "cheek_and_finite_brace_tip_m": root_added,
            }
        )
    refinement = max(
        abs(levels[-1][k] / levels[-2][k] - 1)
        for k in ("panel_total_m", "cheek_and_finite_brace_tip_m")
    )
    if refinement > 0.0001:
        raise ValueError("Hand integration refinement failed")
    # Independently maintained existing implementation, no historical result transfer.
    sys.path.insert(0, str(ROOT))
    from src.analysis.fin_design import distributed_tapered_tip_deflection
    from src.vehicle.benchmark import screen_launch
    from src.vehicle.schema import Vehicle

    reference = distributed_tapered_tip_deflection(
        force / 3, 0.09, 0.12, 0.06, rigidity, f["core_hot_shear_modulus_pa"], tc
    )
    reference_error = abs(reference[2] / levels[-1]["panel_total_m"] - 1)
    if reference_error > 0.0001:
        raise ValueError("Existing distributed beam comparison failed")
    vehicle = Vehicle.model_validate(yaml.safe_load((ROOT / cfg["source_spec"]).read_text()))
    cases = []
    for old, name in ((base, "nominal"), (adverse, "additional20g_motorCG_probe")):
        mass = old["loaded_mass_kg"] + added_g / 1000
        cg = (old["loaded_first_moment_kg_m"] + added_moment) / mass * 1000
        bm = old["burnout_mass_kg"] + added_g / 1000
        bcg = (old["burnout_first_moment_kg_m"] + added_moment) / bm * 1000
        guide = []
        for travel in cfg["budget"]["guide_m"]:
            v = copy.deepcopy(vehicle)
            v.design.rail_length_m = travel
            result = screen_launch(v, study_nominal_mass_kg=mass - 0.05)
            guide.append(
                {
                    "usable_m": travel,
                    "formal_margin_mps": result["rail_exit_speed_mps"] - 15,
                    "planning_margin_mps": result["rail_exit_speed_mps"] - 15.5,
                    **result,
                }
            )
        cases.append(
            {
                "id": name,
                "nominal_plus_optional20g_g": mass * 1000 - 50,
                "separate_full_growth_g": 50,
                "total_g": mass * 1000,
                "cg_mm": cg,
                "burnout_cg_mm": bcg,
                "cp_mm": old["cp_mm"],
                "loaded_margin_cal": (old["cp_mm"] - cg) / 66,
                "burnout_margin_cal": (old["cp_mm"] - bcg) / 66,
                "severe_recovery_DF3_mean_N": 3 * mass * (20.4**2 / 0.6 + 9.80665),
                "formal_1p971m_headroom_g": 1219.953265786171 - mass * 1000,
                "planning_1p971m_headroom_g": 1152.315473556519 - mass * 1000,
                "guides": guide,
                "full_intrinsic_inertia": None,
                "signed_ledger_axial_point_contribution_kg_m2": sum(
                    x["mass_delta_g"] / 1000 * ((x["station_mm"] - cg) / 1000) ** 2 for x in rows
                ),
            }
        )
    axis_force_at_joint = axis_moment / 0.0312
    bond_shear = axis_force_at_joint / (bond_area * 1e-6)
    strut_force = 0.75 * positive / tangent_fraction
    simple_cheek_stress = 6 * (9 * positive * 0.012 / 64) / (0.1 * cheek_t**2)
    floor_I = 1.5e-3 * 0.020**3 / 12
    floor_span = 0.106
    floor_moving = force / 3 * floor_span**3 / (48 * E * floor_I)
    floor_stress = force * floor_span / 4 * 0.01 / floor_I
    # All old source hypotheses retained; only the receiver rotation conversion is corrected.
    datum = {}
    for name, old in r1["structures"].items():
        path = old["attachment"]
        actual_receiver = axis_moment / 3 / path["receiver_hot_upper_stiffness_Nm_rad"] * 0.123
        datum[name] = {
            "axis_torque_DF3_Nm": axis_moment,
            "rocket_axis_to_fin_tip_m": 0.123,
            "receiver_only_tip_m": actual_receiver,
            "panel_socket_play_receiver_only_tip_m": old["panel_states"][1]["levels"][-1]["tip_m"]
            + path["socket_play_only_tip_motion_m"]
            + actual_receiver,
            "status": "Corrected_receiver_axis_radius_conversion_only_original_records_preserved_no_installed_acceptance",
        }
    min_motion = (
        levels[-1]["panel_total_m"]
        + levels[-1]["cheek_and_finite_brace_tip_m"]
        + 0.00002 / 0.012 * 0.0987
        + datum["C1"]["receiver_only_tip_m"]
        + floor_moving
    )
    # Exact 2D nominal link/strap separation, then explicit manufacturing/slack loss.
    strap_width, strap_t = cfg["clearance"]["harness_radial_width_tangent_thickness_mm"]
    harness = []
    for angle in cfg["clearance"]["harness_axes_deg"]:
        for offset in (-9, 9):
            a = math.radians(angle)
            poly = rectangle(24 - strap_width / 2, 24 + strap_width / 2, strap_t / 2, angle)
            harness.append([(x - offset * math.sin(a), y + offset * math.cos(a)) for x, y in poly])
    joint_angle = math.degrees(math.atan2(10, 18.3))
    links = [
        rectangle(19, 28.7, 3, phi + sign * joint_angle)
        for phi in (0, 120, 240)
        for sign in (-1, 1)
    ]
    gaps = [polygon_gap(link, strap) for link in links for strap in harness]
    if not math.isclose(
        polygon_gap(rectangle(0, 1, 0.5, 0), rectangle(2, 3, 0.5, 0)), 1, abs_tol=1e-12
    ):
        raise ValueError("Known rectangle gap check failed")
    fit = {
        "cold_root_min_max_mm": [tab_min, tab_max],
        "cold_channel_min_max_mm": [channel - tol, channel + tol],
        "cold_min_total_root_gap_mm": channel - tol - tab_max,
        "maximum_selected_shim_total_mm": shim_max,
        "nominal_harness_link_min_mm": min(gaps),
        "after0p5mm_slack_and0p2mm_manufacturing_mm": min(gaps) - 0.7,
        "minimum_required_mm": 0.1,
        "bolt_min_finished_length_mm": 17.4,
        "max_grip_plus_nut_plus1mm_protrusion_mm": 0.5 + 0.5 + 0.8 + 0.3 + 2.5 + 8 + 1 + 2.4 + 1,
        "source_motor_tip_min_gap_mm": 33.4 - 17.6 - (15.12 + 0.1 + 0.04),
        "scope": "Analytical stack and nominal 2D polygons only; no full 3D insertion/rotation/service, loop articulation, pressure or hot temperature validation",
    }
    result = {
        "id": cfg["id"],
        "status": "not_admitted_stop_before_CAD_FEA",
        "input_sha256": sources,
        "replacement_ledger": rows,
        "net_added_mass_g": added_g,
        "load_case": {
            "root_DF3_Nm": root_moment,
            "socket_center_DF3_Nm": socket_moment,
            "receiver_axis_DF3_Nm": axis_moment,
            "normal_DF3_N": force,
            "contact_N": [positive, negative],
            "contact_area_each_mm2": 600,
            "DF_applied_once": True,
        },
        "panel_and_finite_root": {
            "levels": levels,
            "final_relative_change": refinement,
            "existing_96point_method_error": reference_error,
            "skin_hot_factored_stress_pa": root_moment
            / (0.12 * rigidity)
            * f["skin_hot_E_pa"]
            * (skin_z + ts / 2),
            "core_hot_factored_mean_shear_pa": force / (0.12 * tc),
            "dense_root_face_bond_mean_pa": (root_moment / (2 * skin_z)) / (band_area * 1e-6),
            "bond_peel_and_face_compression_wrinkling_allowables": None,
            "floor_pin_supported_point_load_stress_pa": floor_stress,
            "floor_service_point_load_translation_m": floor_moving,
            "cheek_min_thickness_simple_support_stress_pa": simple_cheek_stress,
            "brace_min_thickness_factored_stress_pa": strut_force / brace_A,
            "brace_tangential_spring_N_m": brace_k,
            "aggregate_service_motion_proxy_m": min_motion,
            "scope": "Linear strip/frame/contact screening only; real plate coupling, full finite receiver/joints and installed modes unqualified",
        },
        "receiver_joint": {
            "whole_single_fin_torque_one_joint_tangent_N": axis_force_at_joint,
            "doubler_net_bond_area_mm2": bond_area,
            "mean_DF3_hot_bond_shear_pa": bond_shear,
            "hot1MPa_estimate_ratio": 1e6 / bond_shear,
            "M3_mean_shear_pa": axis_force_at_joint / (math.pi * 0.003**2 / 4),
            "G11_boss_mean_bearing_pa": axis_force_at_joint / (0.003 * 0.012),
            "G11_boss_two_flank_tearout_pa": axis_force_at_joint
            / (2 * (0.006 - 0.0034) / 2 * 0.012),
            "bearing_tearout_and_peel_capacity": None,
            "scope": "Unshared full single-fin torque sensitivity; no equal load-sharing or ideal-ground credit. Local pad moves load into remaining doubler/tube bond; fails existing hot screen.",
        },
        "cases": cases,
        "fit": fit,
        "prior_receiver_radius_datum_correction": datum,
        "thermal": "No new solve. Original required burn/soak matrix including300C/dirty foil/35C and45C substrate screen unchanged. New integral braces/pads/12 fasteners alter heat paths; no current temperature field.",
        "recovery_and_service": "Existing independent power, canopy/harness/anchors and cap M3 retention remain counted/unqualified. Access requires twelve finished radial screw sets and retained fin pin ports; actual tools/packing/extraction/arming and bolt-tip sweeps remain unverified.",
        "flutter": "No installed dynamic/modal/flutter result. New sandwich/triangular frame invalidates homogeneous-fin proxy; full torsional stiffness/damping and actual speed envelope needed.",
        "decision": "Reject unchanged C2 before detailed CAD/FEA: receiver-doubler hot bond, finite-root movement and floor bending screens fail. Keep promising sandwich mass/panel evidence separate. Next necessary interface change is continuous moment transfer from socket into a structural receiver sleeve/end joints, not another local glued pad. No next candidate executed.",
        "resources": {
            "cpu_s": time.process_time() - START_CPU,
            "wall_s": time.monotonic() - START_WALL,
            "cpu_limit_s": 20,
            "wall_limit_s": 30,
            "threads": 1,
            "native_CAD_heat_flight_executed": False,
        },
    }
    for relative, digest in sources.items():
        if sha(ROOT / relative) != digest:
            raise ValueError(f"Input changed during packet: {relative}")
    dump(OUT / "record.json", result)
    print(
        json.dumps(
            {
                "status": result["status"],
                "net_added_g": added_g,
                "masses_g": [c["total_g"] for c in cases],
                "hot_bond_MPa": bond_shear / 1e6,
                "service_motion_mm": min_motion * 1000,
                "resources": result["resources"],
            }
        )
    )


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        if OUT.exists():
            import traceback

            dump(
                OUT / "failure.json",
                {
                    "error": str(error),
                    "traceback": traceback.format_exc(),
                    "automatic_retry": False,
                },
            )
        raise
