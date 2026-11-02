"""One C3 geometric admission/coupled-budget packet; no CAD/FEA/heat solver.

Reuses saved C2 fin-construction masses only, not its rejected joint results.
Guide calculation: existing src.vehicle.benchmark.screen_launch (frozen context).
Opening load: unchanged energy-equivalent mean, DF3 once, v=20.4m/s, s=0.3m.
Polygon distances use separating axes and point/segment Euclidean distances.
"""

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

for _name in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ[_name] = "1"
resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
signal.setitimer(signal.ITIMER_REAL, 15)
START_CPU, START_WALL = time.process_time(), time.monotonic()
import yaml

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "configs/studies/wo03-c3-continuous-connection.yaml"
OUT = ROOT / "runs/wo03-c3-continuous-connection-20261102-v1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def rectangle(x0, x1, y0, y1, angle=0):
    c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    return [(x * c - y * s, x * s + y * c) for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]


def overlap(a, b):
    for poly in (a, b):
        for p, q in zip(poly, poly[1:] + poly[:1]):
            n = (p[1] - q[1], q[0] - p[0])
            pa = [x * n[0] + y * n[1] for x, y in a]
            pb = [x * n[0] + y * n[1] for x, y in b]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return False
    return True


def point_segment(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = min(1, max(0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def gap(a, b):
    if overlap(a, b):
        return 0.0
    return min(
        point_segment(p, x, y)
        for vertices, edges in ((a, b), (b, a))
        for p in vertices
        for x, y in zip(edges, edges[1:] + edges[:1])
    )


def main():
    if OUT.exists():
        raise FileExistsError(f"Refusing overwrite: {OUT}")
    OUT.mkdir(parents=True)
    cfg = yaml.safe_load(CFG.read_text())
    shutil.copy2(CFG, OUT / "executed-config.yaml")
    shutil.copy2(Path(__file__), OUT / "executed-script.py")
    sources = {
        str(CFG.relative_to(ROOT)): sha(CFG),
        "scripts/wo03_c3_continuous_connection.py": sha(Path(__file__)),
    }
    for key in ("c1", "c2"):
        p = ROOT / cfg["sources"][key]
        if sha(p) != cfg["sources"][key + "_sha256"]:
            raise ValueError(f"Changed frozen {key} record")
        sources[cfg["sources"][key]] = sha(p)
    c1 = json.loads((ROOT / cfg["sources"]["c1"]).read_text())
    c2 = json.loads((ROOT / cfg["sources"]["c2"]).read_text())
    ch, nodes = cfg["channels"], cfg["end_nodes"]
    rho, count = ch["density_kg_m3"], ch["count"]
    length = ch["start_end_mm"][1] - ch["start_end_mm"][0]
    rows = []

    def add(identifier, grams, station, function, basis):
        rows.append(
            dict(
                id=identifier,
                mass_delta_g=grams,
                station_mm=station,
                function=function,
                basis=basis,
            )
        )

    for row in c2["replacement_ledger"]:
        if row["id"].startswith("remove_") or row["id"] in (
            "C2_dense_root_band",
            "C2_dense_through_body_tabs",
            "C2_PVC_core",
            "C2_carbon_panel",
            "C2_carbon_tab",
            "C2_face_bond_panel",
            "C2_face_bond_tab",
            "C2_edge_finish",
            "C2_root_band_core_butt_bonds",
            "C2_selected_root_shim_stock",
            "C2_pin_spacer_sleeves",
        ):
            rows.append({**row, "id": row["id"].replace("C2_", "C3_saved_fin_")})
    # Do not credit receiver/body support, caps, six original complete end sets,
    # recovery straps/electronics, 8g original fin potting or motor retention.
    for row in c1["added_c1_components"]:
        if "integral_end_hardpoint" in row["id"] or "forward_motor_key_carrier" in row["id"]:
            add(
                "remove_" + row["id"],
                -row["mass_g"],
                row["station_mm"],
                "Function replaced by continuous integral channels with filled barrel nodes/backstops",
                row["basis"],
            )
    floor_area = (
        ch["floor_radial_start_width_thickness_mm"][1]
        * ch["floor_radial_start_width_thickness_mm"][2]
    )
    cheek_depth = (
        ch["cheeks_radial_start_end_thickness_mm"][1]
        - ch["cheeks_radial_start_end_thickness_mm"][0]
    )
    cheek_area = 2 * cheek_depth * ch["cheeks_radial_start_end_thickness_mm"][2]
    a, b = ch["brace_outer_radial_tangential_mm"], ch["brace_inner_radial_tangential_mm"]
    brace_length = math.dist(a, b)
    brace_area = 2 * brace_length * ch["brace_thickness_mm"]
    for label, area in (("floor", floor_area), ("cheeks", cheek_area), ("diagonals", brace_area)):
        add(
            "C3_continuous_" + label,
            count * area * length * rho * 1e-6,
            sum(ch["start_end_mm"]) / 2,
            "Integral end-to-end closed-cell cartridge material",
            "Gross prismatic stock; no overlaps, holes, corner trim or cap-pocket material-removal credit",
        )
    fill_area = (
        nodes["fill_radial_start_end_mm"][1] - nodes["fill_radial_start_end_mm"][0]
    ) * nodes["fill_tangential_width_mm"]
    for i, (z0, z1) in enumerate(nodes["fill_regions_mm"]):
        add(
            f"C3_integral_barrel_core_{i}",
            count * fill_area * (z1 - z0) * rho * 1e-6,
            (z0 + z1) / 2,
            "Solid central cavity fill carries axial screw/barrel and shoulder reactions",
            "Fill only inner channel cavity, no overlap with cheek/floor stock; bore mass not credited",
        )
    t0, t1, tw, tl = nodes["cap_tenon_radial_start_end_width_length_mm"]
    for i, interval in enumerate((nodes["fore_tenon_interval_mm"], nodes["aft_tenon_interval_mm"])):
        add(
            f"C3_integral_cap_tenon_{i}",
            count * (t1 - t0) * tw * tl * rho * 1e-6,
            sum(interval) / 2,
            "Positive contact with finite cap pocket, not adhesive or fixed ground",
            "3mm engagement; no cap pocket credit",
        )
    front = cfg["motor_front"]
    z0, z1 = front["integral_backstop_interval_mm"]
    r0, r1, width = front["radial_start_end_tangential_width_mm"]
    add(
        "C3_integral_motor_front_backstops",
        count * (z1 - z0) * (r1 - r0) * width * rho * 1e-6,
        (z0 + z1) / 2,
        "Forward keys bear axially against integrated ledges; original keys/pins counted",
        "New contacts, stiffness, bearing and hot properties not qualified",
    )
    add(
        "C3_motor_key_selected_shims",
        front["additional_shim_reserve_g"],
        1057,
        "Centre original6.6mm keys in9.5mm channel",
        "Original hardware/shims remain counted; new full process allocation",
    )
    add(
        "C3_locking_bond_finish_service_reserve",
        cfg["mass"]["replacement_process_locking_service_reserve_g"],
        1110,
        "All new thread locking, secondary retention, finish and local strain relief",
        "Replaces original8g socket allocation; original8g fin_bonds remains separate",
    )
    net = sum(row["mass_delta_g"] for row in rows)
    first_delta = sum(row["mass_delta_g"] * row["station_mm"] * 1e-6 for row in rows)
    if not any("carbon_panel" in row["id"] for row in rows):
        raise ValueError("Saved complete fin replacement missing")
    # Source context is copied/hash-checked, never regenerated against newer CAD.
    staged = ROOT / cfg["sources"]["staged_checkout"]
    for relative, expected in c2["input_sha256"].items():
        if "/checkout/" in relative:
            p = ROOT / relative
            if sha(p) != expected:
                raise ValueError(f"Frozen source changed: {relative}")
            sources[relative] = expected
    p = ROOT / cfg["sources"]["source_spec"]
    sources[str(p.relative_to(ROOT))] = sha(p)
    sys.path.insert(0, str(staged))
    os.chdir(staged)
    from src.vehicle.benchmark import screen_launch
    from src.vehicle.schema import Vehicle

    vehicle = Vehicle.model_validate(yaml.safe_load(p.read_text()))
    cases = []
    for old, label in zip(
        c1["mass_scenario_results"][2:4], ("nominal", "additional20g_motorCG_probe")
    ):
        mass = old["loaded_mass_kg"] + net / 1000
        cg = (old["loaded_first_moment_kg_m"] + first_delta) / mass * 1000
        bm = old["burnout_mass_kg"] + net / 1000
        bcg = (old["burnout_first_moment_kg_m"] + first_delta) / bm * 1000
        guides = []
        for travel in cfg["budget"]["usable_guide_probes_m"]:
            v = copy.deepcopy(vehicle)
            v.design.rail_length_m = travel
            screen = screen_launch(v, study_nominal_mass_kg=mass - 0.05)
            guides.append(
                dict(
                    usable_m=travel,
                    formal_margin_mps=screen["rail_exit_speed_mps"] - 15,
                    planning_margin_mps=screen["rail_exit_speed_mps"] - 15.5,
                    **screen,
                )
            )
        cases.append(
            dict(
                id=label,
                nominal_plus_optional20g_g=mass * 1000 - 50,
                separate_full_growth_g=50,
                total_g=mass * 1000,
                cg_mm=cg,
                burnout_cg_mm=bcg,
                cp_mm=old["cp_mm"],
                loaded_margin_cal=(old["cp_mm"] - cg) / 66,
                burnout_margin_cal=(old["cp_mm"] - bcg) / 66,
                guides=guides,
                severe_recovery_DF3_mean_N=3 * mass * (20.4**2 / 0.6 + 9.80665),
                formal_1p971m_headroom_g=1219.953265786171 - mass * 1000,
                planning_1p971m_headroom_g=1152.315473556519 - mass * 1000,
                full_intrinsic_inertia=None,
                signed_ledger_axial_point_contribution_kg_m2=sum(
                    row["mass_delta_g"] / 1000 * ((row["station_mm"] - cg) / 1000) ** 2
                    for row in rows
                ),
            )
        )
    # Complete nominal cross-section surfaces, not centroid-ray harness clearances.
    h = cfg["harness"]
    harness = [
        rectangle(
            h["centre_radius_mm"] - h["width_radial_mm"] / 2,
            h["centre_radius_mm"] + h["width_radial_mm"] / 2,
            offset - h["thickness_tangential_mm"] / 2,
            offset + h["thickness_tangential_mm"] / 2,
            angle,
        )
        for angle in h["axes_deg"]
        for offset in h["tangential_leg_offsets_mm"]
    ]
    parts = [
        rectangle(16.8, 18.3, -10, 10),
        rectangle(18.3, 30.3, 4.75, 7.75),
        rectangle(18.3, 30.3, -7.75, -4.75),
        rectangle(18.3, 30.3, -4.75, 4.75),
    ]
    for sign in (-1, 1):
        dx, dy = a[0] - b[0], sign * (a[1] - b[1])
        nx, ny = -dy / brace_length * 1.2, dx / brace_length * 1.2
        parts.append(
            [
                (b[0] + nx, sign * b[1] + ny),
                (a[0] + nx, sign * a[1] + ny),
                (a[0] - nx, sign * a[1] - ny),
                (b[0] - nx, sign * b[1] - ny),
            ]
        )
    polygons = [
        [
            (
                x * math.cos(math.radians(phi)) - y * math.sin(math.radians(phi)),
                x * math.sin(math.radians(phi)) + y * math.cos(math.radians(phi)),
            )
            for x, y in poly
        ]
        for phi in ch["azimuths_deg"]
        for poly in parts
    ]
    min_gap = min(gap(a, b) for a in polygons for b in harness)
    known = gap(rectangle(0, 1, 0, 1), rectangle(2, 3, 0, 1))
    if not math.isclose(known, 1, abs_tol=1e-12) or not overlap(
        rectangle(0, 2, 0, 2), rectangle(1, 3, 1, 3)
    ):
        raise ValueError("Known rectangle separation/overlap check failed")
    aft = cfg["motor_aft"]
    az0, az1 = aft["retained_arm_interval_mm"]
    nz0, nz1 = nodes["fill_regions_mm"][1]
    axial_overlap = min(az1, nz1) - max(az0, nz0)
    radial_overlap = min(30.3, 30.3) - max(18.3, 12)
    tangent_overlap = min(4.75, 3.3) - max(-4.75, -3.3)
    collision = axial_overlap > 0 and radial_overlap > 0 and tangent_overlap > 0
    result = dict(
        id=cfg["id"],
        status="not_admitted_stop_before_CAD_FEA",
        input_sha256=sources,
        replacement_ledger=rows,
        gross_removed_g=-sum(min(0, r["mass_delta_g"]) for r in rows),
        gross_added_g=sum(max(0, r["mass_delta_g"]) for r in rows),
        net_added_mass_g=net,
        cases=cases,
        geometry=dict(
            harness_nominal_min_gap_mm=min_gap,
            harness_after_motion_manufacturing_mm=min_gap
            - h["motion_mm"]
            - h["manufacturing_loss_mm"],
            required_clearance_mm=0.1,
            aft_node_motor_arm_collision=collision,
            nominal_overlap_axial_radial_tangent_mm=[
                axial_overlap,
                radial_overlap,
                tangent_overlap,
            ],
            motor_radial_gap_proxy_mm=16.8 - (15.12 + 0.1 + 0.04) - 0.1,
            independent_motor_travel_residual_mm=aft["allowed_aft_travel_mm"]
            - aft["manufacturing_loss_mm"]
            - aft["required_thermal_travel_mm"],
            pocket_flank_nominal_clearance_mm=0.02,
            screw_lengths_mm=[27, 19.5],
            screw_min_lengths_mm=[26.9, 19.4],
            screw_max_stack_plus1mm_thread_mm=[6 + 0.5 + 14 + 3 + 1, 6 + 0.5 + 8 + 3 + 1],
            scope="Nominal2D channel/harness plus explicit3D orthogonal node/retainer overlap; not full sampled or continuous sweep, hot-fit or service acceptance",
        ),
        load_case=c2["load_case"],
        connection_checks=dict(
            primary_pad_bond_removed_from_proposed_load_path=True,
            full_G11_receiver_body_foundation_retained_g=59.29933570803816,
            whole_single_fin_end_tangent_force_at_R24_N=c2["load_case"]["receiver_axis_DF3_Nm"]
            / 0.024,
            one_tenon_face_area_mm2=8 * 3,
            one_face_contact_demand_pa=(c2["load_case"]["receiver_axis_DF3_Nm"] / 0.024)
            / (8 * 3 * 1e-6),
            qualified_G11_bearing_tearout_peel_allowables=None,
            finite_cap_and_skirt_compliance=None,
            whole_opening_force_at_one_M3_tension_demand_pa=cases[-1]["severe_recovery_DF3_mean_N"]
            / (math.pi * 0.003**2 / 4),
            hot_steel_estimate_pa=200e6,
            global_channel_torsion_and_root_floor_motion=None,
            installed_flutter=None,
            statement="Dimensional continuity is not installed strength. No equal load sharing, rigid cap, full-tube torsion across fin slots, or C2 isolated-root result transferred.",
        ),
        thermal=cfg["thermal"],
        decision="Not admitted: aft central integral barrel nodes overlap independent motor-retention arms. Complete charged mass also misses conditional guide planning and may fail stability. Stop before detailed analysis; next interface must separate aft end-fastener/support volumes from independently removable motor retention and retain a credible continuous torsional path, rather than adding local pads.",
        resources=dict(
            cpu_s=time.process_time() - START_CPU,
            wall_s=time.monotonic() - START_WALL,
            cpu_limit_s=10,
            wall_limit_s=15,
            threads=1,
            CAD_FEA_thermal_freeflight_executed=False,
        ),
    )
    for relative, expected in sources.items():
        if sha(ROOT / relative) != expected:
            raise ValueError(f"Source changed during packet: {relative}")
    dump(OUT / "record.json", result)
    print(
        json.dumps(
            {
                k: result[k]
                for k in (
                    "status",
                    "gross_removed_g",
                    "gross_added_g",
                    "net_added_mass_g",
                    "geometry",
                    "resources",
                )
            }
        )
    )
    print(json.dumps(result["cases"]))


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        if OUT.exists():
            import traceback

            dump(
                OUT / "failure.json",
                dict(error=str(error), traceback=traceback.format_exc(), automatic_retry=False),
            )
        raise
