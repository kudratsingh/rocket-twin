"""One bounded S3 connected-receiver hand screen; no CAD, FEA, heat, or flight."""

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

for _name in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ[_name] = "1"

CPU_PROCESS_START = time.process_time()
WALL_PROCESS_START = time.monotonic()
resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
signal.setitimer(signal.ITIMER_REAL, 30)

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-g80-connected-receiver.yaml"
OUT = ROOT / "runs/wo03-g80-connected-receiver-20261102-v2"
CPU_LIMIT_S = 20
WALL_LIMIT_S = 30


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def mm3_to_g(volume_mm3: float, density_kg_m3: float) -> float:
    return volume_mm3 * density_kg_m3 * 1e-6


def rect_subtraction(
    outer_radial_mm: float,
    outer_tangential_mm: float,
    channel_radial_mm: float,
    channel_tangential_mm: float,
) -> dict[str, float]:
    """Uniform C-section computed from configured outer and open-channel dimensions."""
    ox, oy = outer_radial_mm, outer_tangential_mm
    hx, hy = channel_radial_mm, channel_tangential_mm
    hole_x0 = ox - hx
    a0, a1 = ox * oy, hx * hy
    area = a0 - a1
    cx0, cx1 = ox / 2, hole_x0 + hx / 2
    cx = (a0 * cx0 - a1 * cx1) / area
    # Cross section is symmetric about its tangential centerline.
    ix = ox * oy**3 / 12 - hx * hy**3 / 12
    iy = ox * oy * ((ox**2 / 12) + (cx0 - cx) ** 2) - hx * hy * ((hx**2 / 12) + (cx1 - cx) ** 2)
    return {
        "outer_radial_mm": ox,
        "outer_tangential_mm": oy,
        "channel_radial_mm": hx,
        "channel_tangential_mm": hy,
        "channel_radial_inner_mm": hole_x0,
        "net_area_mm2": area,
        "radial_centroid_from_inner_mm": cx,
        "tangential_centroid_mm": 0.0,
        "I_about_radial_axis_mm4": ix,
        "I_about_tangential_axis_mm4": iy,
        "weak_centroidal_I_mm4": min(ix, iy),
        "no_fastener_hole_credit": True,
    }


def main() -> None:
    started = WALL_PROCESS_START
    proc_started = CPU_PROCESS_START
    if OUT.exists():
        raise FileExistsError(f"Refusing to overwrite prior packet: {OUT}")
    OUT.mkdir(parents=True)
    executed_script = OUT / "executed-script.py"
    executed_config = OUT / "executed-config.yaml"
    shutil.copy2(Path(__file__), executed_script)
    shutil.copy2(CONFIG, executed_config)

    cfg = yaml.safe_load(CONFIG.read_text())
    bundle_path = ROOT / cfg["source_bundle"]
    bundle = yaml.safe_load(bundle_path.read_text())
    source_path = ROOT / cfg["source_spec"]
    staged = ROOT / cfg["staged_checkout"]
    source_text = source_path.read_text()
    source = yaml.safe_load(source_text)
    sys.path.insert(0, str(staged))
    os.chdir(staged)
    from src.vehicle.aero import center_of_pressure
    from src.vehicle.benchmark import screen_launch
    from src.vehicle.mass import mass_properties
    from src.vehicle.schema import Vehicle

    vehicle = Vehicle.model_validate(source)
    parts_by_id = {p.id: p for p in vehicle.parts}
    remove_ids = list(bundle["remove_source_ids"])
    missing_remove_ids = sorted(set(remove_ids) - set(parts_by_id))
    if missing_remove_ids:
        raise ValueError(f"Configured source removals missing: {missing_remove_ids}")
    removed = {part_id: parts_by_id[part_id].resolved_mass_kg for part_id in remove_ids}
    removed_g = sum(removed.values()) * 1000
    if not math.isclose(removed_g, 139.060536, abs_tol=0.001):
        raise ValueError(
            f"Named source bundle mass differs from expected 139.060536 g: {removed_g}"
        )

    retained = copy.deepcopy(vehicle)
    retained.parts = [p for p in vehicle.parts if p.id not in set(remove_ids)]
    retained_props = mass_properties(retained)
    burnout_props = mass_properties(retained, burn_fraction=1.0)
    if not math.isclose(
        retained_props.mass_kg + removed_g / 1000,
        sum(p.resolved_mass_kg for p in vehicle.parts),
        abs_tol=1e-9,
    ):
        raise ValueError("Count-once retained/source mass reconciliation failed")

    points: list[dict[str, object]] = []

    def add(
        name: str,
        mass_g: float,
        station_mm: float,
        *,
        x_mm: float = 0.0,
        y_mm: float = 0.0,
        basis: str,
    ) -> None:
        if not math.isfinite(mass_g) or mass_g < 0 or not math.isfinite(station_mm):
            raise ValueError(f"Invalid mass row {name}: {mass_g} g at {station_mm} mm")
        points.append(
            {
                "id": name,
                "mass_g": float(mass_g),
                "station_mm": float(station_mm),
                "radial_x_mm": float(x_mm),
                "radial_y_mm": float(y_mm),
                "basis": basis,
            }
        )

    def polar(radius_mm: float, azimuth_deg: float, tangent_mm: float = 0.0) -> tuple[float, float]:
        a = math.radians(azimuth_deg)
        return (
            radius_mm * math.cos(a) - tangent_mm * math.sin(a),
            radius_mm * math.sin(a) + tangent_mm * math.cos(a),
        )

    # Continuous three-rail C-section staves, net geometry only; no hole mass credit.
    f = cfg["rails"]
    cs = rect_subtraction(
        f["radial_outer_mm"] - f["radial_inner_mm"],
        f["tangential_width_mm"],
        f["channel_radial_depth_mm"],
        f["full_length_channel_width_mm"],
    )
    rail_len = f["end_mm"] - f["start_mm"]
    rail_mass_g = mm3_to_g(
        cs["net_area_mm2"] * rail_len * 3, cfg["materials"]["G11"]["density_kg_m3"]
    )
    rail_radius = f["radial_inner_mm"] + cs["radial_centroid_from_inner_mm"]
    for i, angle in enumerate(f["azimuths_deg"]):
        x, y = polar(rail_radius, angle)
        add(
            f"{f['ids'][i]}_continuous_net_C_stave",
            rail_mass_g / 3,
            (f["start_mm"] + f["end_mm"]) / 2,
            x_mm=x,
            y_mm=y,
            basis="Net uniform C section from outer rectangle minus open channel; no fastener-hole mass credit; source-config density estimate",
        )

    caps = cfg["end_caps"]
    ro, ri = caps["outer_radius_mm"], caps["bore_radius_mm"]
    cap_t = caps["thickness_mm"]
    annulus_vol = math.pi * (ro**2 - ri**2) * cap_t
    half_cyl_vol_each = math.pi * caps["saddle_radius_mm"] ** 2 / 2 * caps["saddle_radial_width_mm"]
    for label, cap_front, outward_sign in (
        ("fore", caps["front_stations_mm"][0], -1),
        ("aft", caps["front_stations_mm"][1], 1),
    ):
        add(
            f"{label}_integral_G11_annular_cap",
            mm3_to_g(annulus_vol, cfg["materials"]["G11"]["density_kg_m3"]),
            cap_front + cap_t / 2,
            basis="Gross annular cylinder, no hole/port/overlap deductions",
        )
        lobe_axial = caps["saddle_radius_mm"] * 4 / (3 * math.pi)
        for j, angle in enumerate(caps["saddle_azimuths_deg"]):
            x, y = polar(caps["saddle_radial_center_mm"], angle)
            cap_outboard_face = cap_front + cap_t if label == "aft" else cap_front
            add(
                f"{label}_half_cylinder_saddle_lobe_{j}",
                mm3_to_g(half_cyl_vol_each, cfg["materials"]["G11"]["density_kg_m3"]),
                cap_outboard_face + outward_sign * lobe_axial,
                x_mm=x,
                y_mm=y,
                basis="Gross half-cylinder, 12.7 mm radial-axis width; semicircle centroid 4r/(3pi) from cap face; not CAD reconciled",
            )

    # Cap strap slots are real specified openings but receive no material-mass credit
    # per the owner config; record them explicitly as unresolved openings.
    strap_slots = caps["strap_leg_slots"]

    skirt = caps["fore_integral_body_skirt"]
    skirt_z0, skirt_z1 = skirt["start_end_mm"]
    skirt_ri, skirt_ro = skirt["inner_outer_radius_mm"]
    skirt_cross_area = math.pi * (skirt_ro**2 - skirt_ri**2)
    windows = skirt["bight_clearance_windows"]
    win_z0, win_z1 = windows["start_end_mm"]
    windowed_length_equivalent = (skirt_z1 - skirt_z0) - windows[
        "removed_circumference_fraction"
    ] * (win_z1 - win_z0)
    skirt_volume = skirt_cross_area * windowed_length_equivalent
    full_z_center = (skirt_z0 + win_z0) / 2
    window_z_center = (win_z0 + win_z1) / 2
    skirt_cg_z = (
        (win_z0 - skirt_z0) * full_z_center
        + (1 - windows["removed_circumference_fraction"]) * (win_z1 - win_z0) * window_z_center
    ) / windowed_length_equivalent
    add(
        "fore_integral_body_skirt",
        mm3_to_g(skirt_volume, cfg["materials"]["G11"]["density_kg_m3"]),
        skirt_cg_z,
        basis="Annular cylinder with only configured half-circumference 995-1004 mm windows removed; equivalent full-circumference length 25.5 mm",
    )

    # Motor front and aft plates, radial prongs, keys, and travel hard-stop spacers.
    mf = cfg["motor_front"]
    z0, z1 = mf["plate_start_end_mm"]
    r0, r1 = mf["annulus_inner_outer_radius_mm"]
    add(
        "motor_front_annulus",
        mm3_to_g(math.pi * (r1**2 - r0**2) * (z1 - z0), cfg["materials"]["G11"]["density_kg_m3"]),
        (z0 + z1) / 2,
        basis="Gross annular plate; notches/overlap not deducted",
    )
    pr0, pr1 = mf["prong_radial_start_end_mm"]
    prong_volume = (pr1 - pr0) * mf["prong_width_mm"] * mf["prong_thickness_mm"]
    for i, angle in enumerate(f["azimuths_deg"]):
        x, y = polar((pr0 + pr1) / 2, angle)
        add(
            f"motor_front_prong_{i}",
            mm3_to_g(prong_volume, cfg["materials"]["G11"]["density_kg_m3"]),
            (z0 + z1) / 2,
            x_mm=x,
            y_mm=y,
            basis="Gross radial rectangular prong; no overlap/cut deductions",
        )
    key = mf["stop_keys"]
    kr, kt, kz = key["radial_tangential_axial_mm"]
    kz0, kz1 = key["start_end_mm"]
    for i, angle in enumerate(f["azimuths_deg"]):
        x, y = polar(
            (mf["prong_radial_start_end_mm"][0] + mf["prong_radial_start_end_mm"][1]) / 2, angle
        )
        add(
            f"motor_front_stop_key_{i}",
            mm3_to_g(kr * kt * kz, cfg["materials"]["G11"]["density_kg_m3"]),
            (kz0 + kz1) / 2,
            x_mm=x,
            y_mm=y,
            basis="Gross rectangular positive stop key; no pin-hole or overlap deduction",
        )

    ma = cfg["motor_aft"]
    az0, az1 = ma["central_plate_start_end_mm"]
    ar0, ar1 = ma["annulus_inner_outer_radius_mm"]
    add(
        "motor_aft_floating_annulus",
        mm3_to_g(
            math.pi * (ar1**2 - ar0**2) * (az1 - az0), cfg["materials"]["G11"]["density_kg_m3"]
        ),
        (az0 + az1) / 2,
        basis="Gross floating annular plate; no holes/overlap deductions",
    )
    apr0, apr1 = ma["prong_radial_start_end_mm"]
    aft_prong_vol = (apr1 - apr0) * ma["prong_width_mm"] * ma["prong_thickness_mm"]
    for i, angle in enumerate(f["azimuths_deg"]):
        x, y = polar((apr0 + apr1) / 2, angle)
        add(
            f"motor_aft_prong_{i}",
            mm3_to_g(aft_prong_vol, cfg["materials"]["G11"]["density_kg_m3"]),
            (az0 + az1) / 2,
            x_mm=x,
            y_mm=y,
            basis="Gross radial rectangular prong with configured 4 mm axial thickness; exact CAD omitted",
        )
    spacer_r, spacer_t = ma["hard_stop_radial_tangential_mm"]
    spacer_axial = ma["hard_stop_spacer_axial_mm"]
    aft_cap_front = caps["front_stations_mm"][1]
    aft_cap_end = aft_cap_front + caps["thickness_mm"]
    spacer_mid = az1 + ma["allowed_aft_travel_mm"] + spacer_axial / 2
    for i, angle in enumerate(f["azimuths_deg"]):
        x, y = polar((apr0 + apr1) / 2, angle)
        add(
            f"motor_aft_hard_stop_spacer_{i}",
            mm3_to_g(spacer_r * spacer_t * spacer_axial, cfg["materials"]["G11"]["density_kg_m3"]),
            spacer_mid,
            x_mm=x,
            y_mm=y,
            basis="Gross 12x6.6x1.6 mm spacer at floating-plate full-aft stop position",
        )
    add(
        "motor_keeper_spring_locking_allocation",
        ma["guide_keeper_spring_locking_allowance_g"],
        (az1 + aft_cap_end) / 2,
        basis="Explicit mass allowance; no spring selected or temperature capability established",
    )

    # Cap-to-stave M3 sets, three per end.
    cc = cfg["cap_connections"]
    bolt_r = cc["radial_center_mm"]
    tangent = cc["tangential_center_mm"]
    cap_stations = cc["barrel_centers_station_mm"]
    for end_name, z in (("fore", cap_stations[0]), ("aft", cap_stations[1])):
        for i, angle in enumerate(f["azimuths_deg"]):
            x, y = polar(bolt_r, angle, tangent)
            add(
                f"{end_name}_cap_M3_complete_set_{i}",
                cc["screw_nut_washer_locking_mass_each_g"],
                z,
                x_mm=x,
                y_mm=y,
                basis="Complete unselected set allocation from study config, 4 g each; not supplier verified",
            )

    # Six finite pin/washer/retainer sets: 3 motor keys and 3 fin axial pins.
    cpins = cfg["cross_pins"]
    pin_mass = cpins["pin_washers_cotter_shim_mass_each_g"]
    steel_density = cfg["materials"]["steel"]["density_kg_m3"]
    pin_shaft_d, pin_shaft_l = cpins["shaft_diameter_mm"], cpins["shaft_length_mm"]
    head_d, head_t = cpins["head_diameter_thickness_mm"]
    washer_od, washer_id, washer_t = cpins["washer_od_id_thickness_mm"]
    shim_od, shim_id = cpins["shim_od_id_mm"]
    shim_max_t = max(cpins["selected_transverse_shim_mm"])
    cotter_d, cotter_total_l = cpins["cotter_wire_diameter_total_length_mm"]
    pin_envelope_volume_mm3 = (
        math.pi * (pin_shaft_d / 2) ** 2 * pin_shaft_l
        + math.pi * (head_d / 2) ** 2 * head_t
        + 2 * math.pi / 4 * (washer_od**2 - washer_id**2) * washer_t
        + math.pi / 4 * (shim_od**2 - shim_id**2) * shim_max_t
        + math.pi * (cotter_d / 2) ** 2 * cotter_total_l
    )
    pin_gross_component_sum_g = mm3_to_g(pin_envelope_volume_mm3, steel_density)
    for group, station, radial in (
        ("motor_front_key", mf["stop_keys"]["pin_station_mm"], 24.3),
        (
            "fin_axial_retention",
            cfg["fins"]["positive_axial_pins"]["pin_station_mm"],
            cfg["fins"]["positive_axial_pins"]["pin_radial_mm"],
        ),
    ):
        for i, angle in enumerate(f["azimuths_deg"]):
            x, y = polar(radial, angle)
            add(
                f"{group}_5mm_cross_pin_complete_set_{i}",
                pin_mass,
                station,
                x_mm=x,
                y_mm=y,
                basis="Complete pin/washer/cotter/shim allowance 6.5 g; exact hardware grade/mass unselected",
            )

    # Deeper-tab-only plywood delta; external fin planform and remaining source fins stay.
    fin = cfg["fins"]
    tab_delta_mm = fin["new_tab_depth_mm"] - fin["source_tab_depth_mm"]
    tab_volume_each = tab_delta_mm * fin["tab_length_mm"] * 6.35
    tab_delta_g = mm3_to_g(3 * tab_volume_each, cfg["materials"]["plywood"]["density_kg_m3"])
    fin_station = sum(fin["tab_start_end_mm"]) / 2
    fin_radius = sum(fin["tab_radial_start_end_mm"]) / 2
    for i, angle in enumerate(f["azimuths_deg"]):
        x, y = polar(fin_radius, angle)
        add(
            f"fin_tab_depth_delta_{i}",
            tab_delta_g / 3,
            fin_station,
            x_mm=x,
            y_mm=y,
            basis="Delta only: configured depth difference x 100 x 6.35 mm source fin thickness, plywood density estimate; original fins/gussets retained",
        )

    # Three raw webbing loops; no finished seam strength or weight credit from raw tensile.
    rec = cfg["recovery"]
    loop_len_mm = (
        rec["axial_legs_per_loop"] * rec["fore_aft_bight_separation_mm"]
        + rec["curved_length_per_loop_mm"]
        + rec["sewn_lap_per_loop_mm"]
    )
    max_g_per_m = rec["maximum_raw_oz_per_yard"] * 28.349523125 / 0.9144
    total_webbing_g = rec["closed_loops_count"] * loop_len_mm / 1000 * max_g_per_m
    loop_station = (caps["saddle_protrusions_mm"][0][0] + caps["saddle_protrusions_mm"][1][1]) / 2
    for i, angle in enumerate(rec["loop_azimuths_deg"]):
        x, y = polar(rec["loop_leg_local_radial_mm"], angle)
        add(
            f"raw_Bally_2745_loop_{i}",
            total_webbing_g / rec["closed_loops_count"],
            loop_station,
            x_mm=x,
            y_mm=y,
            basis="Two legs plus curved length and 50 mm sewn lap; maximum raw oz/yard converted to mass; not finished assembly rating",
        )
    backbone_g = rec["backbone_extra_mass_kg"] * 1000
    backbone_station = (
        rec["primary_junction_station_mm"] + rec["fore_bight_station_for_angle_mm"]
    ) / 2
    bx, by = (
        polar(
            sum(rec["loop_leg_local_radial_mm"]) / len(rec["loop_leg_local_radial_mm"]),
            rec["loop_azimuths_deg"][0],
        )
        if isinstance(rec["loop_leg_local_radial_mm"], list)
        else polar(rec["loop_leg_local_radial_mm"], rec["loop_azimuths_deg"][0])
    )
    add(
        "recovery_backbone_extra_mass",
        backbone_g,
        backbone_station,
        x_mm=bx,
        y_mm=by,
        basis="Configured extra backbone mass; station is midpoint of primary junction and fore bight for point-mass bookkeeping",
    )

    # Connector mass is allocated only once via additional_items.S3_connector.
    # Body-spreader/fastener assembly and bond use separate declared budgets.
    body = cfg["body_connection"]
    body_station = skirt_cg_z
    add(
        "fore_skirt_to_paper_extra_epoxy_budget",
        body["extra_bond_budget_g"],
        body_station,
        basis="Explicit additional epoxy allocation for the one fore skirt/body interface",
    )
    add(
        "fore_skirt_M2_spreader_fastener_assembly_budget",
        body["assembly_mass_budget_g"],
        body_station,
        basis="Complete body locator/spreader assembly allowance; no primary paper-wall capacity credited",
    )
    add(
        "service_port_covers",
        cfg["service_ports"]["covers_g"],
        sum(cfg["service_ports"]["axial_stations_mm"]) / 2,
        basis="Explicit service-port cover allowance, counted separately from other additional items",
    )

    # Every configured extra allowance is explicit. S3_connector is the sole 12 g connector mass.
    for item in cfg["additional_items"]:
        add(
            item["id"],
            item["mass_g"],
            item["station_mm"],
            basis=item.get("basis", "Explicit planning allocation from connected-receiver config"),
        )

    # Source hashes and mass properties remain tied to the source identity.
    curve_rel = Path(vehicle.motor.curve)
    curve_path = curve_rel if curve_rel.is_absolute() else staged / curve_rel
    input_paths = [
        CONFIG,
        bundle_path,
        source_path,
        ROOT / "configs/engineering/wo03.yaml",
        ROOT / "configs/studies/wo03-g80-fin-loads.yaml",
        Path(__file__).resolve(),
        staged / "src/vehicle/schema.py",
        staged / "src/vehicle/mass.py",
        staged / "src/vehicle/benchmark.py",
        staged / "src/vehicle/aero.py",
        staged / "src/vehicle/motors.py",
        staged / "src/sim/frames.py",
        curve_path,
    ]
    input_hashes_before = {
        str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): sha256(p)
        for p in input_paths
    }

    source_cp_m = center_of_pressure(vehicle)
    new_mass_g = sum(float(p["mass_g"]) for p in points)
    new_first_moment_g_mm = sum(float(p["mass_g"]) * float(p["station_mm"]) for p in points)
    growth_g = cfg["separate_growth_kg"] * 1000
    source_loaded_g = retained_props.mass_kg * 1000
    source_burnout_g = burnout_props.mass_kg * 1000
    loaded_total_g = source_loaded_g + new_mass_g + growth_g
    burnout_total_g = source_burnout_g + new_mass_g + growth_g
    growth_z = cfg["growth_station_m"] * 1000
    loaded_cg_mm = (
        source_loaded_g * retained_props.cg_m * 1000 + new_first_moment_g_mm + growth_g * growth_z
    ) / loaded_total_g
    burnout_cg_mm = (
        source_burnout_g * burnout_props.cg_m * 1000 + new_first_moment_g_mm + growth_g * growth_z
    ) / burnout_total_g
    loaded_margin_cal = (source_cp_m * 1000 - loaded_cg_mm) / (
        vehicle.airframe["body_diameter_m"] * 1000
    )
    burnout_margin_cal = (source_cp_m * 1000 - burnout_cg_mm) / (
        vehicle.airframe["body_diameter_m"] * 1000
    )

    # Point-mass-only inertia contribution of new items about loaded candidate CG.
    # Baseline source has full inertia from mass.py; a full combined tensor is withheld
    # because most new hardware/loop/bond geometry is an unselected envelope/allocation.
    tensor_added = np.zeros((3, 3), dtype=float)
    for p in points:
        m_kg = float(p["mass_g"]) / 1000
        rel = np.array(
            [
                (float(p["radial_x_mm"]) / 1000),
                (float(p["radial_y_mm"]) / 1000),
                (float(p["station_mm"]) / 1000 - loaded_cg_mm / 1000),
            ]
        )
        tensor_added += m_kg * (np.dot(rel, rel) * np.eye(3) - np.outer(rel, rel))
    growth_rel = np.array([0.0, 0.0, growth_z / 1000 - loaded_cg_mm / 1000])
    tensor_added += (growth_g / 1000) * (
        np.dot(growth_rel, growth_rel) * np.eye(3) - np.outer(growth_rel, growth_rel)
    )

    # Exactly the existing shared source guide model; only rail usable length varies.
    guide_rows = []
    for usable_m in [cfg["baseline_usable_m"], *cfg["conditional_probe_usable_m"]]:
        candidate = copy.deepcopy(retained)
        candidate.design.rail_length_m = float(usable_m)
        screen = screen_launch(
            candidate, study_nominal_mass_kg=(source_loaded_g + new_mass_g) / 1000
        )
        guide_rows.append({"usable_m": usable_m, **screen})

    # Solve only the two specified single-new-mass roots at the illustrative 1.971 m probe.
    def speed_at_full_mass(full_mass_g: float) -> float | None:
        candidate = copy.deepcopy(retained)
        candidate.design.rail_length_m = cfg["budget"]["root_travel_m"]
        result = screen_launch(candidate, study_nominal_mass_kg=(full_mass_g - growth_g) / 1000)
        return result["rail_exit_speed_mps"]

    roots = {}
    for target in cfg["budget"]["single_new_mass_root_targets"]:
        lo_g, hi_g = 400.0 + growth_g, 1500.0
        lo_v, hi_v = speed_at_full_mass(lo_g), speed_at_full_mass(hi_g)
        lo_speed = 0.0 if lo_v is None else lo_v
        hi_speed = 0.0 if hi_v is None else hi_v
        if lo_speed < target or hi_speed >= target:
            roots[str(target)] = {
                "status": "target_not_bracketed",
                "low_mass_g": lo_g,
                "low_speed_mps": lo_v,
                "high_mass_g": hi_g,
                "high_speed_mps": hi_v,
            }
            continue
        for _ in range(24):
            mid = (lo_g + hi_g) / 2
            mid_v = speed_at_full_mass(mid)
            if mid_v is not None and mid_v >= target:
                lo_g = mid
            else:
                hi_g = mid
        roots[str(target)] = {
            "status": "screen_root",
            "full_mass_g_interval": [lo_g, hi_g],
            "speed_bracket_mps": [speed_at_full_mass(lo_g), speed_at_full_mass(hi_g)],
            "includes_growth_once": True,
        }

    # Recovery and retention demand screens.
    recovery = cfg["recovery"]
    severe_accel = recovery["design_factor"] * (
        recovery["severe_velocity_mps"] ** 2 / (2 * recovery["stopping_travel_m"]) + 9.80665
    )
    nominal_accel = recovery["design_factor"] * (
        recovery["nominal_velocity_mps"] ** 2 / (2 * recovery["stopping_travel_m"]) + 9.80665
    )
    severe_n = max(recovery.get("prior_factored_floor_n", 0), severe_accel * loaded_total_g / 1000)
    nominal_n = nominal_accel * loaded_total_g / 1000
    burnout_severe_n = severe_accel * burnout_total_g / 1000

    # Rail one-member demand and pinned Euler sensitivity, without sharing credit.
    rails = cfg["rails"]
    rail_i = cs["weak_centroidal_I_mm4"]
    rail_len_m = (rails["end_mm"] - rails["start_mm"]) / 1000
    young = cfg["materials"]["G11"]["youngs_lower_pa"]
    euler_n = math.pi**2 * young * rail_i * 1e-12 / rail_len_m**2
    rail_full_force_mpa = severe_n / (cs["net_area_mm2"] * 1e-6) / 1e6
    contact_rows = []
    for fraction in cfg["end_caps"]["end_contact_fraction_sensitivity"]:
        single_area = cs["net_area_mm2"] * fraction
        aggregate_area = 3 * single_area
        contact_rows.append(
            {
                "fraction": fraction,
                "single_rail_end_area_mm2": single_area,
                "one_rail_carrying_full_recovery_mpa": severe_n / (single_area * 1e-6) / 1e6,
                "three_rail_geometric_area_mm2": aggregate_area,
                "mean_if_all_three_are_engaged_and_force_is_distributed_mpa": severe_n
                / (aggregate_area * 1e-6)
                / 1e6,
            }
        )

    # Reverse motor retention, one complete cap connection carries full 450 N.
    cc = cfg["cap_connections"]
    reverse_n = cc["reverse_service_n"] * cc["design_factor"]
    m3_area = 5.03
    washer_area = (
        math.pi
        / 4
        * (
            cc["ring_washer_od_id_thickness_mm"][0] ** 2
            - cc["ring_washer_od_id_thickness_mm"][1] ** 2
        )
    )
    ear_width_total = rails["tangential_width_mm"] - rails["full_length_channel_width_mm"]
    one_ear_width = ear_width_total / 2
    barrel_d = cc["barrel_diameter_length_mm"][0]
    barrel_projected = barrel_d * one_ear_width
    tearout_rows = []
    for end_name, edge in zip(("fore", "aft"), cc["end_to_barrel_center_mm"], strict=True):
        ligament = edge - barrel_d / 2
        area = 2 * ligament * one_ear_width
        tearout_rows.append(
            {
                "end": end_name,
                "edge_distance_mm": edge,
                "barrel_radius_mm": barrel_d / 2,
                "net_edge_ligament_mm": ligament,
                "one_loaded_ear_width_mm": one_ear_width,
                "one_joint_two_plane_tearout_area_mm2": area,
                "one_joint_full_450N_mean_tearout_mpa": reverse_n / (area * 1e-6) / 1e6,
            }
        )
    cap_joint = {
        "service_n": cc["reverse_service_n"],
        "design_factor_once": cc["design_factor"],
        "single_cap_single_M3_joint_demand_n": reverse_n,
        "M3_tensile_area_mm2": m3_area,
        "M3_tensile_demand_MPa": reverse_n / m3_area,
        "washer_annulus_area_mm2": washer_area,
        "washer_mean_bearing_MPa": reverse_n / washer_area,
        "barrel_diameter_mm": barrel_d,
        "C_rail_two_ear_width_total_mm": ear_width_total,
        "one_loaded_ear_width_mm": one_ear_width,
        "barrel_projected_one_loaded_ear_area_mm2": barrel_projected,
        "barrel_mean_bearing_MPa": reverse_n / barrel_projected,
        "end_tearout_screens": tearout_rows,
        "material_mode_allowables": "Unavailable; scalar demand arithmetic only",
    }

    # Motor front key pin: full reverse load on one cross-pin, no equal sharing.
    mf_key = mf["stop_keys"]
    pin_d = cpins["shaft_diameter_mm"]
    pin_area = math.pi * pin_d**2 / 4
    pin_span = cs["channel_tangential_mm"]
    pin_moment_nmm = reverse_n * pin_span / 4
    pin_modulus_mm3 = math.pi * pin_d**3 / 32
    key_t = mf_key["radial_tangential_axial_mm"][1]
    key_bearing_area = pin_d * key_t
    motor_key_screen = {
        "one_key_pin_full_reverse_load_n": reverse_n,
        "pin_diameter_mm": pin_d,
        "ideal_double_shear_area_mm2": 2 * pin_area,
        "ideal_double_shear_MPa": reverse_n / (2 * pin_area),
        "unsupported_span_mm": pin_span,
        "simple_center_load_bending_moment_Nmm": pin_moment_nmm,
        "pin_bending_section_modulus_mm3": pin_modulus_mm3,
        "pin_bending_MPa": pin_moment_nmm / pin_modulus_mm3,
        "one_G11_key_projected_bearing_area_mm2": key_bearing_area,
        "one_key_mean_bearing_MPa": reverse_n / key_bearing_area,
        "no_strength_allowables": True,
    }

    # Paper/body and skirt arithmetic: diagnostic only; no assumption that full recovery enters paper.
    bc = cfg["body_connection"]
    bond_outer_radius = skirt_ro
    effective_bond_length = bc["bonded_length_mm"] - windows["removed_circumference_fraction"] * (
        win_z1 - win_z0
    )
    skirt_area_full = 2 * math.pi * bond_outer_radius * effective_bond_length
    paper_ro, paper_ri = (
        bc["source_paper_inner_outer_radius_mm"][1],
        bc["source_paper_inner_outer_radius_mm"][0],
    )
    paper_area = math.pi * (paper_ro**2 - paper_ri**2)
    body_rows = []
    for force_name, force in (
        ("reverse_450N", reverse_n),
        ("full_loaded_severe_recovery", severe_n),
    ):
        row = {
            "force_case": force_name,
            "force_n": force,
            "paper_annulus_area_mm2": paper_area,
            "paper_uniform_MPa_if_entire_force_enters_serial_tube": force / paper_area,
            "paper_estimated_screen_MPa": bc["source_paper_axial_strength_pa"] / 1e6,
            "skirt_coverage_cases": [],
        }
        for fraction in bc["covered_area_fraction"]:
            area = skirt_area_full * fraction
            row["skirt_coverage_cases"].append(
                {"coverage_fraction": fraction, "area_mm2": area, "mean_shear_MPa": force / area}
            )
        body_rows.append(row)

    # Existing 40 kPa/5 degree engineering.py fin panel formula; external fin unchanged.
    fin_part = next(p for p in vehicle.parts if p.id == "fin_set")
    gfin = fin_part.geometry
    span, root, tip = gfin["span_m"], gfin["root_chord_m"], gfin["tip_chord_m"]
    fin_area = span * (root + tip) / 2
    ar = 2 * span**2 / fin_area
    slope = 2 * math.pi * ar / (2 + math.sqrt(4 + ar**2))
    panel = yaml.safe_load((ROOT / "configs/studies/wo03-g80-fin-loads.yaml").read_text())[
        "historical_panel_case"
    ]
    alpha_rad = math.radians(panel["alpha_deg"])
    fin_force = panel["dynamic_pressure_pa"] * fin_area * slope * alpha_rad
    fin_arm = span * (root + 2 * tip) / (3 * (root + tip))
    fin_moment = fin_force * fin_arm
    factored_fin_force = fin_force * recovery["design_factor"]
    factored_fin_moment = fin_moment * recovery["design_factor"]
    contact_depth = rails["channel_radial_depth_mm"] / 1000
    root_couple_n = factored_fin_moment / contact_depth
    contact_area_one_side_mm2 = rails["channel_radial_depth_mm"] * fin["tab_length_mm"]
    fin_total_gap = fin["finished_total_clearance_mm"][1]
    fin_freeplay_tip_mm = fin_total_gap * (span * 1000) / rails["channel_radial_depth_mm"]
    fin_delta_per_fin_g = tab_delta_g / 3
    original_fin_each_kg = fin_part.resolved_mass_kg / 3
    updated_fin_each_kg = original_fin_each_kg + fin_delta_per_fin_g / 1000
    own_fin_inertia_force_n = updated_fin_each_kg * severe_accel
    fin_pin_d = cpins["shaft_diameter_mm"]
    fin_t = gfin["thickness_m"] * 1000
    fin_edge = fin["positive_axial_pins"]["axial_distance_to_tab_end_mm"]
    fin_pin_bearing_area = fin_pin_d * fin_t
    fin_pin_edge_ligament = fin_edge - fin_pin_d / 2
    fin_pin_tearout_area = 2 * fin_pin_edge_ligament * fin["new_tab_depth_mm"]
    fin_results = {
        "source_fin_part_id": fin_part.id,
        "external_fin_geometry_unchanged": True,
        "panel_case": panel,
        "planform_area_per_fin_m2": fin_area,
        "aspect_ratio": ar,
        "normal_force_slope_per_rad": slope,
        "normal_force_per_fin_n_unfactored": fin_force,
        "root_arm_m": fin_arm,
        "root_moment_per_fin_Nm_unfactored": fin_moment,
        "design_factor_once": recovery["design_factor"],
        "root_force_per_fin_N_after_DF3": factored_fin_force,
        "root_moment_per_fin_Nm_after_DF3": factored_fin_moment,
        "direct_side_contact_couple_arm_m": contact_depth,
        "one_side_contact_force_for_moment_couple_n": root_couple_n,
        "nominal_side_contact_area_per_face_mm2_if_full_12x100_contact": contact_area_one_side_mm2,
        "average_side_contact_MPa_if_full_contact": root_couple_n / contact_area_one_side_mm2,
        "no_ideal_clamp_credit": True,
        "maximum_finished_total_gap_mm": fin_total_gap,
        "geometric_tip_freeplay_mm_from_gap_over_12mm_embedment": fin_freeplay_tip_mm,
        "source_fin_mass_per_fin_g": original_fin_each_kg * 1000,
        "tab_depth_delta_per_fin_g": fin_delta_per_fin_g,
        "updated_fin_mass_per_fin_g": updated_fin_each_kg * 1000,
        "severe_factored_acceleration_m_s2": severe_accel,
        "own_fin_mass_severe_inertia_force_n": own_fin_inertia_force_n,
        "5mm_axial_pin_bearing_area_mm2": fin_pin_bearing_area,
        "own_mass_pin_bearing_demand_MPa": own_fin_inertia_force_n / fin_pin_bearing_area,
        "axial_pin_edge_distance_mm": fin_edge,
        "axial_pin_hole_radius_mm": fin_pin_d / 2,
        "axial_pin_net_edge_ligament_mm": fin_pin_edge_ligament,
        "two_plane_tearout_area_mm2": fin_pin_tearout_area,
        "tearout_projected_tab_depth_mm": fin["new_tab_depth_mm"],
        "own_mass_pin_tearout_demand_MPa": own_fin_inertia_force_n / fin_pin_tearout_area,
        "panel_strength_flutter_and_installed_root_acceptance": "Open; no panel/flutter result transferred",
    }

    # Tolerance, shell, thermal-growth, and motor-travel checks.
    cl = cfg["clearances"]
    shell_inner_min = cl["shell_inner_radius_mm"] - cl["shell_radius_tolerance_mm"]
    receiver_rmax_cold = caps["outer_radius_mm"] + cl["receiver_radius_tolerance_mm"]
    cold_radial_clearance = shell_inner_min - receiver_rmax_cold - cl["mounting_eccentricity_mm"]
    delta_t = cl["receiver_temperature_sensitivity_c"] - cl["ambient_c"]
    radial_growth = caps["outer_radius_mm"] * cfg["materials"]["G11"]["cte_upper_per_k"] * delta_t
    hot_screen_clearance = cold_radial_clearance - radial_growth
    source_min_clearance = cl["minimum_radial_mm"]
    source_interference = cl["source_thermal_endplay_range_mm"][0]
    archived_interference_screen = source_min_clearance - source_interference
    travel_nominal = ma["allowed_aft_travel_mm"]
    travel_loss = cl["new_axial_travel_manufacturing_loss_mm"]
    travel_usable = travel_nominal - travel_loss
    min_nominal_travel = archived_interference_screen + travel_loss

    # Verify the declared source/config/helper inputs did not change during this packet.
    input_hashes_after = {
        str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p): sha256(p)
        for p in input_paths
    }
    if input_hashes_after != input_hashes_before:
        raise RuntimeError("One or more declared inputs changed during the single packet execution")
    input_hashes = input_hashes_before
    elapsed = time.monotonic() - started
    cpu_elapsed = time.process_time() - proc_started
    if elapsed > WALL_LIMIT_S or cpu_elapsed > CPU_LIMIT_S:
        raise TimeoutError(f"Declared budget exceeded: wall={elapsed:.3f}s cpu={cpu_elapsed:.3f}s")

    full_tensor = None
    record = {
        "status": "one_candidate_preliminary_hand_screen_not_accepted",
        "candidate_id": cfg["id"],
        "active_spec_changed": False,
        "native_or_flight_execution": False,
        "input_sha256": input_hashes,
        "source_73_nominal_mass_g": sum(p.resolved_mass_kg for p in vehicle.parts) * 1000,
        "named_source_bundle_removed_once_g": removed_g,
        "removed_source_parts_g": {k: v * 1000 for k, v in removed.items()},
        "retained_source_mass_properties": {
            "loaded_mass_g": source_loaded_g,
            "burnout_mass_g": source_burnout_g,
            "loaded_cg_station_mm": retained_props.cg_m * 1000,
            "burnout_cg_station_mm": burnout_props.cg_m * 1000,
            "loaded_full_inertia_tensor_kg_m2_about_retained_cg": retained_props.inertia_kg_m2.tolist(),
            "burnout_full_inertia_tensor_kg_m2_about_retained_cg": burnout_props.inertia_kg_m2.tolist(),
            "source_helper": "staged checkout src.vehicle.mass.mass_properties",
        },
        "growth": {"mass_g": growth_g, "station_mm": growth_z, "counted_once": True},
        "new_component_mass_ledger": points,
        "new_component_mass_total_g": new_mass_g,
        "clevis_set_gross_steel_component_sum_diagnostic": {
            "shaft_diameter_length_mm": [pin_shaft_d, pin_shaft_l],
            "head_diameter_thickness_mm": [head_d, head_t],
            "two_washer_od_id_thickness_mm": [washer_od, washer_id, washer_t],
            "shim_od_id_max_thickness_mm": [shim_od, shim_id, shim_max_t],
            "cotter_wire_diameter_total_length_mm": [cotter_d, cotter_total_l],
            "gross_steel_component_sum_g_each": pin_gross_component_sum_g,
            "configured_budget_g_each": pin_mass,
            "margin_to_budget_g_each": pin_mass - pin_gross_component_sum_g,
            "basis": "Geometric steel volume estimate only; not selected/purchased clevis hardware, tolerances, or verified assembly mass.",
        },
        "complete_preliminary_budget": {
            "loaded_full_mass_g": loaded_total_g,
            "motor_burnout_full_mass_g": burnout_total_g,
            "loaded_cg_station_mm": loaded_cg_mm,
            "burnout_cg_station_mm": burnout_cg_mm,
            "loaded_source_barrowman_cp_station_mm": source_cp_m * 1000,
            "loaded_static_margin_cal": loaded_margin_cal,
            "burnout_static_margin_cal": burnout_margin_cal,
            "full_candidate_tensor": full_tensor,
            "tensor_status": "Full candidate tensor unavailable: new loops, custom hardware and mass allocations have point/envelope locations but no exact intrinsic inertia geometry. Added parts are represented as points only for this ledger.",
            "new_items_point_mass_tensor_about_loaded_candidate_cg_frame_X_radial_Y_tangential_Z_aft_kg_m2": tensor_added.tolist(),
            "no_mass_bounds_claimed": True,
        },
        "c_section": cs,
        "fore_skirt_geometry_and_windows": {
            "start_end_mm": [skirt_z0, skirt_z1],
            "inner_outer_radius_mm": [skirt_ri, skirt_ro],
            "window_start_end_mm": [win_z0, win_z1],
            "removed_circumference_fraction_in_window": windows["removed_circumference_fraction"],
            "equivalent_full_circumference_length_mm": windowed_length_equivalent,
            "volume_mm3_after_only_configured_window_removal": skirt_volume,
            "axial_centroid_mm": skirt_cg_z,
        },
        "specified_cap_strap_leg_openings_no_mass_credit": {
            "count_per_cap": strap_slots["count_per_cap"],
            "opening_dimensions_mm": strap_slots["radial_length_tangential_width_mm"],
            "radial_center_mm": strap_slots["radial_center_mm"],
            "tangential_centers_mm": strap_slots["tangential_centers_mm"],
            "nominal_removed_area_per_cap_mm2_not_subtracted_from_mass": strap_slots[
                "count_per_cap"
            ]
            * math.prod(strap_slots["radial_length_tangential_width_mm"]),
            "note": "Geometry openings are explicit; config forbids crediting their removed stock in this gross mass budget.",
        },
        "rail_screens": {
            "full_recovery_force_in_one_rail_axial_MPa": rail_full_force_mpa,
            "one_rail_pinned_Euler_N_E_lower_5GPa_L201p8mm": euler_n,
            "no_equal_sharing_or_support_credit": True,
            "cap_end_contact_sensitivities": contact_rows,
        },
        "recovery_demands": {
            "nominal_5m_s_0p3m_DF3_N": nominal_n,
            "severe_20p4m_s_0p3m_DF3_N": severe_n,
            "motor_burnout_severe_N": burnout_severe_n,
            "prior_1782p253N_floor_N": recovery.get("prior_factored_floor_n"),
            "formula": "DF3*m*(v^2/(2*0.3m)+9.80665); full 50g growth and all corrected source mass included once; this is a mean energy-equivalent screen, not a measured peak",
        },
        "reverse_motor_retention_screen": cap_joint,
        "motor_front_key_pin_screen": motor_key_screen,
        "body_and_paper_diagnostics": {
            "bond_outer_radius_mm": bond_outer_radius,
            "bonded_length_gross_mm": bc["bonded_length_mm"],
            "windowed_bond_length_removed_mm": bc["bonded_length_mm"] - effective_bond_length,
            "bonded_length_after_actual_windows_mm": effective_bond_length,
            "body_skirt_full_circumferential_area_mm2": skirt_area_full,
            "cases": body_rows,
            "paper_results_are_diagnostic_only": True,
            "do_not_assume_whole_recovery_enters_paper_or_reduce_load_to_pass": True,
        },
        "fin_root_screen": fin_results,
        "radial_and_motor_travel_screens": {
            "shell_inner_min_radius_mm": shell_inner_min,
            "receiver_cold_max_radius_mm": receiver_rmax_cold,
            "mounting_eccentricity_mm": cl["mounting_eccentricity_mm"],
            "minimum_cold_radial_clearance_mm": cold_radial_clearance,
            "G11_radial_growth_at_150C_screen_mm": radial_growth,
            "conditional_radial_clearance_after_growth_mm": hot_screen_clearance,
            "G11_CTE_per_K": cfg["materials"]["G11"]["cte_upper_per_k"],
            "temperature_delta_K": delta_t,
            "motor_source_interference_excursion_mm": source_interference,
            "source_minimum_free_clearance_mm": source_min_clearance,
            "source_thermal_endplay_min_mm": source_interference,
            "combined_closure_screen_mm_minimum_free_gap_preserved": archived_interference_screen,
            "configured_nominal_motor_free_travel_mm": travel_nominal,
            "manufacturing_loss_mm": travel_loss,
            "usable_free_travel_mm": travel_usable,
            "minimum_nominal_travel_to_cover_screen_mm": min_nominal_travel,
            "conditional_residual_free_gap_mm": travel_usable - archived_interference_screen,
            "closure_formula": "0.1 mm minimum source free clearance - (-1.9352 mm source minimum endplay) = 2.0352 mm; new usable travel 3.2-0.5=2.7 mm; conditional free gap 0.6648 mm",
            "nozzle_bore_radius_mm": ma["annulus_inner_outer_radius_mm"][0],
            "nozzle_fit": "Unavailable; exact case/nozzle/closure drawing and tolerance not in source packet",
            "no_temperature_prediction_or_case_compression_credit": True,
        },
        "guide_screens": guide_rows,
        "full_mass_roots_at_1p971m": roots,
        "decision_boundary": "Preliminary hand screen only; actual geometry, joint allowables, capacity, thermal history, exact motor/nozzle fit, installed fin dynamics, and flight acceptance remain open. No automatic refinement.",
        "resource": {
            "cpu_s": cpu_elapsed,
            "wall_s": elapsed,
            "requested_threads": 1,
            "declared_cpu_limit_s": CPU_LIMIT_S,
            "declared_wall_limit_s": WALL_LIMIT_S,
        },
    }
    dump_json(OUT / "record.json", record)
    output_hashes = {
        p.name: sha256(p) for p in (executed_config, executed_script, OUT / "record.json")
    }
    dump_json(
        OUT / "manifest.json",
        {"input_sha256": input_hashes, "output_sha256": output_hashes, "status": record["status"]},
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # preserve the one attempt; no automatic retry
        OUT.mkdir(parents=True, exist_ok=True)
        if CONFIG.exists() and not (OUT / "executed-config.yaml").exists():
            shutil.copy2(CONFIG, OUT / "executed-config.yaml")
        if Path(__file__).exists() and not (OUT / "executed-script.py").exists():
            shutil.copy2(Path(__file__), OUT / "executed-script.py")
        dump_json(
            OUT / "record.json",
            {
                "status": "stopped_failure_preserved_no_retry",
                "error": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        try:
            artifacts = [
                OUT / "executed-config.yaml",
                OUT / "executed-script.py",
                OUT / "record.json",
            ]
            dump_json(
                OUT / "manifest.json",
                {
                    "output_sha256": {p.name: sha256(p) for p in artifacts if p.exists()},
                    "status": "stopped_failure_preserved_no_retry",
                },
            )
        except Exception:  # noqa: BLE001, S110
            pass
        raise
