"""Preliminary motor support load-path screens from resolved vehicle geometry.

These hand calculations expose assumed load sharing and simple-beam bounds. They
are not detailed FEA, allowables, or proof of an assembled load path.
"""

from __future__ import annotations

import math
from itertools import pairwise
from typing import Any, cast

from src.vehicle.schema import Part, Vehicle


def _mm(value: Any, default: float = 0.0) -> float:
    return float(default if value is None else value) * 1e-3


def _part(vehicle: Vehicle, *names: str) -> Part | None:
    return next((p for p in vehicle.parts if p.id in names), None)


def _material(cfg: dict[str, Any], part: Part | None, key: str | None = None) -> dict[str, Any]:
    name = key or (part.material if part else "")
    return cast(dict[str, Any], cfg["materials"].get(name, {}))


def _supported_pad_equivalents(pads: Part | None, relief: dict[str, Any] | None) -> float:
    if pads is None or not pads.cad:
        return 3.0
    if not relief:
        return 3.0
    sector = float(pads.cad.parameters.get("sector_angle_deg", 40))
    rin = float(pads.geometry.get("inner_radius_m", 0)) * 1000
    rout = float(pads.geometry.get("radius_m", 0)) * 1000
    center = float(relief.get("center_deg", 0)) % 360
    width = min(360.0, float(relief.get("width_deg", 0)))
    keep_radius = float(relief.get("keep_radius_mm", rout))
    if keep_radius >= rout or rout <= rin:
        return 3.0
    radial_removed_fraction = max(
        0.0,
        (rout**2 - max(rin, keep_radius) ** 2) / (rout**2 - rin**2),
    )
    step = 0.1
    supported = 0.0
    for pad_center in (0.0, 120.0, 240.0):
        samples = max(1, round(sector / step))
        angular_overlap = (
            sum(
                abs(
                    ((pad_center + ((i + 0.5) / samples - 0.5) * sector - center + 180) % 360) - 180
                )
                < width / 2
                for i in range(samples)
            )
            / samples
        )
        supported += 1.0 - angular_overlap * radial_removed_fraction
    return supported


def _margin(capacity: float, demand: float, factor: float) -> float | None:
    return capacity / (factor * demand) - 1 if demand > 0 else None


def _rail_section_mm(
    rail_r: float,
    radial: float,
    tangential: float,
    cut_r: float,
    cut_radial: float,
    cut_tangential: float,
) -> tuple[float, float, float]:
    """Net rectangle area and centroidal principal inertias after a rectangular slot."""
    rx0, rx1 = rail_r - radial / 2, rail_r + radial / 2
    cx0, cx1 = cut_r - cut_radial / 2, cut_r + cut_radial / 2
    y0, y1 = -tangential / 2, tangential / 2
    cy0, cy1 = -cut_tangential / 2, cut_tangential / 2
    ix0, ix1 = max(rx0, cx0), min(rx1, cx1)
    iy0, iy1 = max(y0, cy0), min(y1, cy1)
    # Signed rectangles: full rail minus the exact intersection of the cut.
    rectangles: list[tuple[float, float, float, float, float]] = [(1.0, rx0, rx1, y0, y1)]
    if ix1 > ix0 and iy1 > iy0:
        rectangles.append((-1.0, ix0, ix1, iy0, iy1))
    area = mx = my = 0.0
    for sign, x0, x1, yy0, yy1 in rectangles:
        a = (x1 - x0) * (yy1 - yy0) * sign
        area += a
        mx += a * (x0 + x1) / 2
        my += a * (yy0 + yy1) / 2
    if area <= 0:
        return 0.0, 0.0, 0.0
    xc, yc = mx / area, my / area
    ix = iy = 0.0
    for sign, x0, x1, yy0, yy1 in rectangles:
        a = (x1 - x0) * (yy1 - yy0) * sign
        ix += sign * (x1 - x0) * (yy1 - yy0) ** 3 / 12 + a * ((yy0 + yy1) / 2 - yc) ** 2
        iy += sign * (yy1 - yy0) * (x1 - x0) ** 3 / 12 + a * ((x0 + x1) / 2 - xc) ** 2
    return area, ix, iy


def _ring_plate(
    plate: Part,
    pads: Part | None,
    force_n: float,
    cfg: dict[str, Any],
    *,
    stop_geometry: dict[str, float] | None = None,
    stop_parameters: dict[str, Any] | None = None,
    active_pad_count: float = 3,
) -> dict[str, Any]:
    g = stop_geometry or plate.geometry
    p = stop_parameters or (plate.cad.parameters if plate.cad else {})
    ro = float(g["radius_m"])
    ri = float(g.get("inner_radius_m", 0))
    t = _mm(p.get("thickness_mm")) or float(g["length_m"])
    f = p.get("rail_notches", {})
    width = _mm(f.get("width_mm")) + 2 * _mm(f.get("side_gap_mm"))
    depth = _mm(f.get("depth_mm")) + 2 * _mm(f.get("side_gap_mm"))
    n = 3
    contact_area = n * width * depth if width and depth else None
    bearing = force_n / contact_area if contact_area else None
    pad_area = None
    pad_pressure = None
    strip = None
    active_area = None
    if pads and pads.cad:
        q = pads.cad.parameters
        rin = float(pads.geometry.get("inner_radius_m", 0))
        rout = float(pads.geometry.get("radius_m", 0))
        angle = math.radians(float(q.get("sector_angle_deg", 40)))
        count = int(q.get("count", 3))
        pad_area = count * angle * (rout**2 - rin**2) / 2
        active_area = pad_area * active_pad_count / count
        pad_pressure = force_n / active_area if active_area else None
        # Conservative independent cantilever sector strip; ignores circumferential
        # plate action and is only a bounding hand screen, not a plate solution.
        b = angle * (rin + rout) / 2
        span = max(ro - rout, 0)
        strip = (
            6 * (force_n / active_pad_count) * span / (b * t**2)
            if b and t and active_pad_count
            else None
        )
    mat = _material(cfg, plate, "G11")
    strength = float(mat.get("strength_pa", 50e6))
    cold_margin = _margin(strength, strip or bearing or 0, float(cfg["loads"]["design_factor"]))
    return {
        "plate_id": plate.id,
        "plate_station_m": plate.position_m,
        "plate_thickness_m": t,
        "outer_radius_m": ro,
        "inner_radius_m": ri,
        "rail_slot_count_assumed": n,
        "rail_slot_footprint_area_m2": contact_area,
        "nominal_slot_footprint_average_pressure_pa": bearing,
        "pad_total_area_m2": pad_area,
        "pad_active_area_m2": active_area,
        "active_pad_count_assumption": active_pad_count,
        "pad_average_compression_pa": pad_pressure,
        "pad_compression_provisional_capacity_pa": 20e6,
        "pad_margin_design_factor_3": _margin(20e6, pad_pressure or 0, 3),
        "plate_sector_cantilever_bending_pa": strip,
        "plate_bending_margin_cold_material_screen": cold_margin,
        "plate_bending_margin_hot_half_strength": _margin(
            float(mat.get("hot_strength_screen_pa", strength / 2)),
            strip or bearing or 0,
            float(cfg["loads"]["design_factor"]),
        ),
        "plate_bending_strength_estimate_pa": strength,
        "method": "Independent radial sector-strip cantilevers from pad edge to outer radius; circumferential ring action omitted. Active pad count reflects the stated support geometry assumption. The fixed notched-slot result is a footprint-average pressure only, not a verified bearing contact area; actual sidewall/base contact and local stress require resolved contact geometry.",
    }


def _rails(mount: Part, force_n: float, cfg: dict[str, Any]) -> dict[str, Any]:
    g = mount.geometry
    p = mount.cad.parameters if mount.cad else {}
    cassette = mount.cad.generator == "motor_cassette" if mount.cad else False
    if cassette:
        n = int(p.get("forward_load_bearing_rails", 3))
        a = float(p.get("rail_radial_width_mm", 4))
        b = float(p.get("rail_tangential_width_mm", 6))
        length = float(g.get("length_m", 0)) * 1e3
        stop = p.get("fore_thrust_stop", {})
        grip_start = float(p.get("grip_start_mm", 55))
        grip_end = grip_start + float(p.get("grip_length_mm", 18))
        rear = p.get("rear_retainer_blocks", {}).get("block", {})
        rear_start = float(rear.get("station_mm", length - 10))
        rear_end = rear_start + float(rear.get("axial_length_mm", 10))
        supports_mm = sorted(
            {
                0.0,
                float(stop.get("station_mm", 0)) + float(stop.get("thickness_mm", 5)),
                grip_start,
                grip_end,
                rear_start,
                min(length, rear_end),
                length,
            }
        )
        euler_length = max((y - x for x, y in pairwise(supports_mm)), default=length) * 1e-3
        stations = [x * 1e-3 for x in supports_mm]
        family = "G11"
    else:
        n = 3
        a = float(p.get("rail_depth_mm", 3))
        b = float(p.get("rail_width_mm", 12))
        family = mount.material
        ring_stations = [float(x) for x in p.get("ring_stations_mm", [])]
        length = float(g.get("length_m", 0)) * 1e3
        # Include the actual mount endpoints with configured ring support stations.
        stations_mm = sorted({0.0, length, *ring_stations})
        spans = [max(0.0, y - x) * 1e-3 for x, y in pairwise(stations_mm)]
        euler_length = max(spans, default=length * 1e-3)
        stations = [x * 1e-3 for x in stations_mm]
    area_mm2 = a * b
    inertia_mm4 = min(a * b**3, b * a**3) / 12
    channel_info: dict[str, Any] | None = None
    if not cassette and p.get("fin_channels"):
        area_mm2, ix_mm4, iy_mm4 = _rail_section_mm(
            float(p.get("rail_radius_mm", 28.5)),
            a,
            b,
            float(p.get("fin_channel_radius_mm", 30)),
            float(p.get("fin_channel_depth_mm", 5)),
            float(p.get("fin_slot_width_mm", 2.4)),
        )
        inertia_mm4 = min(ix_mm4, iy_mm4)
        channel_info = {
            "cut_center_radius_mm": float(p.get("fin_channel_radius_mm", 30)),
            "cut_radial_depth_mm": float(p.get("fin_channel_depth_mm", 5)),
            "cut_tangential_width_mm": float(p.get("fin_slot_width_mm", 2.4)),
            "net_single_rail_section_area_mm2": area_mm2,
            "net_single_rail_inertias_mm4": {"axis_x": ix_mm4, "axis_y": iy_mm4},
            "method": "Rail cross-section rectangle minus the intersecting fin-channel rectangle. This ideal net section omits notch-root concentration and local plate/rail restraint.",
        }
    area = area_mm2 * 1e-6
    mat = _material(cfg, mount, family)
    e = float(mat.get("youngs_pa", 2e9))
    strength = float(mat.get("strength_pa", 10e6))
    hot_strength = float(mat.get("hot_strength_screen_pa", strength / 2))
    # The weaker of the two rectangular-section axes bounds unknown rotation.
    inertia = inertia_mm4 * 1e-12
    pcr_one = math.pi**2 * e * inertia / euler_length**2 if euler_length else 0.0
    rail_stress = force_n / (n * area) if area else math.inf
    return {
        "mount_id": mount.id,
        "generator": mount.cad.generator if mount.cad else None,
        "rail_count": n,
        "rail_cross_section_mm": [a, b],
        "net_single_rail_section_area_mm2": area_mm2,
        "channel_net_section": channel_info,
        "rail_total_area_m2": n * area,
        "rail_axial_stress_pa": rail_stress,
        "rail_axial_margin_cold": _margin(strength, rail_stress, 3),
        "rail_axial_margin_hot_half_strength": _margin(hot_strength, rail_stress, 3),
        "support_stations_m": stations,
        "maximum_assumed_unsupported_span_m": euler_length,
        "weak_axis_inertia_m4": inertia,
        "single_rail_pinned_euler_load_n": pcr_one,
        "forward_rail_euler_margin_cold": _margin(n * pcr_one, force_n, 3),
        "forward_rail_euler_margin_hot_E_half": _margin(n * pcr_one * 0.5, force_n, 3),
        "youngs_modulus_pa": e,
        "strength_screen_pa": strength,
        "method": f"Equal forward load share over {n} configured load-bearing rail(s); weakest net rectangular-axis Euler column. Fixed mount uses configured ring stations as lateral supports. TVC cassette assumes rail support at the integral fore stop, grip collar and aft blocks; the longest inter-support span governs. Actual rail restraint is uncertain.",
    }


def _retainer(vehicle: Vehicle, cfg: dict[str, Any], reverse_load_n: float) -> dict[str, Any]:
    cap = _part(vehicle, "aft_retainer", "aft_cap", "retainer")
    hardware = _part(vehicle, "retention_hardware")
    mount = _part(vehicle, "motor_mount")
    p = mount.cad.parameters if mount and mount.cad else {}
    blocks = p.get("rear_retainer_blocks", {}).get("block", {}) if mount else {}
    fixed = p.get("retainer_blocks", []) if mount else []
    count = int(blocks.get("count", len(fixed) or 3))
    if fixed:
        diam = _mm(fixed[0].get("bolt_hole_mm", 3.4))
        engage = _mm(fixed[0].get("size_mm", [0, 0, 0])[2])
        nut_capture = bool(fixed[0].get("nut_pocket_size_mm"))
        block_bearing_area = _mm(fixed[0].get("size_mm", [12, 12, 20])[0]) * _mm(
            fixed[0].get("size_mm", [12, 12, 20])[1]
        )
    else:
        diam = _mm(blocks.get("bolt_hole_diameter_mm", 3.4))
        engage = _mm(blocks.get("axial_length_mm", 10))
        nut_capture = False
        block_bearing_area = _mm(blocks.get("radial_width_mm", 6)) * _mm(
            blocks.get("tangential_width_mm", 8)
        )
    # M3 nominal tensile stress area is 5.03 mm^2; use nominal d for a conservative
    # simple cylindrical G11 internal-thread shear cylinder, not a thread standard.
    m3_area = 5.03e-6
    per = reverse_load_n / max(count, 1)
    g11 = _material(cfg, mount, "G11")
    plywood = _material(cfg, mount, "plywood")
    capacity_strength = float(g11.get("strength_pa", 50e6))
    hot_g11 = float(g11.get("hot_strength_screen_pa", capacity_strength / 2))
    cold_block_strength = (
        capacity_strength if not fixed else float(plywood.get("strength_pa", 10e6))
    )
    hot_block_strength = hot_g11 if not fixed else cold_block_strength / 2
    thread_area = 0.0 if nut_capture else math.pi * 0.003 * engage
    screw_lengths = []
    if hardware and hardware.cad:
        screw_lengths = [
            float(pin["length_mm"])
            for pin in hardware.cad.parameters.get("pins", [])
            if float(pin.get("radius_mm", 0)) <= 1.6 and "length_mm" in pin
        ]
    return {
        "cap_id": cap.id if cap else None,
        "reverse_case_load_n": reverse_load_n,
        "fastener_count_assumed": count,
        "hardware_envelope_id": hardware.id if hardware else None,
        "hardware_estimated_mass_kg": hardware.mass_kg if hardware else None,
        "M3_screw_shank_lengths_mm": screw_lengths,
        "individual_fastener_load_n": per,
        "hole_or_shank_diameter_m": diam,
        "M3_nominal_diameter_m": 0.003,
        "nominal_M3_tensile_area_m2": m3_area,
        "nominal_M3_tensile_stress_pa": per / m3_area,
        "thread_engagement_m_assumed": None if nut_capture else engage,
        "captive_nut_pocket_present": nut_capture,
        "G11_thread_cylinder_area_m2": thread_area or None,
        "G11_thread_shear_stress_pa": per / thread_area if thread_area else None,
        "G11_thread_cylinder_margin_DF3": _margin(
            capacity_strength, per / thread_area if thread_area else 0, 3
        ),
        "G11_thread_cylinder_margin_DF3_hot": _margin(
            hot_g11, per / thread_area if thread_area else 0, 3
        ),
        "block_cross_section_area_m2": block_bearing_area,
        "block_cross_section_average_stress_pa": (
            per / block_bearing_area if block_bearing_area else None
        ),
        "block_cross_section_margin_DF3_cold": _margin(
            cold_block_strength, per / block_bearing_area if block_bearing_area else 0, 3
        ),
        "block_cross_section_margin_DF3_hot_half_strength": _margin(
            hot_block_strength, per / block_bearing_area if block_bearing_area else 0, 3
        ),
        "plywood_strength_screen_pa": float(plywood.get("strength_pa", 10e6)),
        "method": "Equal load share across configured blocks/bolts. Nominal M3 tensile area is a bolt-demand indicator only. Fixed-mode captive-nut pockets are assumed from CAD; nut grade/retention and plywood block bearing are unverified. TVC G11 tapped-thread stripping uses a simple cylindrical shear-area hypothesis. Washer bearing, pocket breakout, block splitting, edge distance and eccentricity are unverified.",
    }


def _pivot_pins(vehicle: Vehicle, thrust_n: float) -> dict[str, Any] | None:
    parts = {p.id: p for p in vehicle.parts}
    rows = []
    for pin_id, lug_id, gap_m in (
        ("outer_pivots", "tvc_gimbal", None),
        ("inner_pivots", "gimbal_inner", None),
    ):
        pins = parts.get(pin_id)
        lug = parts.get(lug_id)
        if not pins or not lug or not pins.cad:
            continue
        pin_defs = pins.cad.parameters.get("pins", [])
        if not pin_defs:
            continue
        d = 2 * float(pin_defs[0].get("radius_mm", 1.5)) * 1e-3
        count = len(pin_defs)
        per_pin = thrust_n / count
        hole_d = 3.4e-3
        wall = float(lug.geometry.get("radius_m", 0)) - float(lug.geometry.get("inner_radius_m", 0))
        t = float(lug.geometry.get("length_m", 0))
        edge = max(0.0, (t - hole_d) / 2)
        area = math.pi * d**2 / 4
        # Nominal radial clearances from the two concentric G11 envelopes.
        if pin_id == "outer_pivots":
            frame = parts.get("gimbal_frame")
            gap_m = (
                float(frame.geometry.get("inner_radius_m", 0))
                - float(lug.geometry.get("radius_m", 0))
                if frame
                else 1.3e-3
            )
        else:
            outer = parts.get("tvc_gimbal")
            gap_m = (
                float(outer.geometry.get("inner_radius_m", 0))
                - float(lug.geometry.get("radius_m", 0))
                if outer
                else 1e-3
            )
        moment = per_pin * gap_m / 2
        rows.append(
            {
                "pin_set": pin_id,
                "lug_part": lug_id,
                "pin_count": count,
                "pin_diameter_m": d,
                "load_per_pin_n": per_pin,
                "single_shear_stress_pa": per_pin / area,
                "double_shear_stress_pa": per_pin / (2 * area),
                "nominal_inter_ring_clearance_m": gap_m,
                "cantilever_bending_moment_nm": moment,
                "pin_bending_stress_pa": 32 * moment / (math.pi * d**3),
                "lug_axial_thickness_m": t,
                "lug_projected_bearing_stress_pa": per_pin / (d * wall) if d and wall else None,
                "gross_radial_wall_m": wall,
                "bore_diameter_assumed_m": hole_d,
                "bore_center_axial_station_m": t / 2,
                "axial_edge_ligament_estimate_m": edge,
                "lug_two_plane_shearout_stress_pa": (
                    per_pin / (2 * edge * wall) if edge and wall else None
                ),
                "method": "Each opposed pin shares one half of axial thrust. Shear stress is reported for single and double shear. Bending treats radial clearance as a conservative simply-overhung gap (M=Fpin*g/2). The bore is radial through the concentric ring wall; projected bearing length is radial wall (Ro−Ri), and axial edge ligament is (6 mm axial thickness−3.4 mm bore)/2. Bore center lies at z=t/2 in CAD. Pin material strength, positive axial retention, hot load capacity and contact remain unverified.",
            }
        )
    return {"load_n": thrust_n, "pin_sets": rows} if rows else None


def motor_support(
    vehicle: Vehicle, cfg: dict[str, Any], thrust_n: float, reverse_load_n: float = 150.0
) -> dict[str, Any]:
    """Compute preliminary forward and reverse axial support screens."""
    parts = {p.id: p for p in vehicle.parts}
    mount = parts.get("motor_mount")
    if mount is None:
        raise ValueError("resolved vehicle has no motor_mount")
    plate = _part(vehicle, "retention", "thrust_plate", "motor_stop")
    pads = _part(vehicle, "mica_compression_pads", "mica_pads", "thrust_pads")
    factor = float(cfg["loads"].get("design_factor", 3))
    result: dict[str, Any] = {
        "configuration_id": vehicle.id,
        "mode": vehicle.design.mode if vehicle.design else None,
        "thrust_n": thrust_n,
        "reverse_load_n": reverse_load_n,
        "design_factor": factor,
        "acceptance_closed": False,
        "flight_ready": False,
        "forward_path": "motor case shoulder -> mica sector pads -> fixed G11 thrust plate or TVC integral G11 stop -> rails -> fixed shell joints or radial screws into inner gimbal -> pivots/frame",
        "reverse_path": "motor case aft closure -> retainer/cap -> three M3 blocks/bolts -> fixed frame or TVC cassette",
        "screens": {},
        "unresolved": [
            "Exact motor case front shoulder/nozzle 24 mm opening geometry and closure capture are supplier dependencies.",
            "Properties are preliminary estimates, not material or joint allowables; no physical proof test is represented.",
            "Contact, local stress concentrations, manufacturing tolerances and assembly preload are not solved.",
        ],
    }
    result["screens"]["rails"] = _rails(mount, thrust_n, cfg)
    pin_screen = _pivot_pins(vehicle, thrust_n)
    if pin_screen:
        result["screens"]["gimbal_pins_and_ligaments"] = pin_screen
    cad = mount.cad
    is_cassette = bool(cad and cad.generator == "motor_cassette")
    if is_cassette and cad:
        fore = cad.parameters.get("fore_thrust_stop", {})
        if fore.get("enabled", False):
            relief = fore.get("rod_relief")
            active_pads = _supported_pad_equivalents(pads, relief)
            stop_geometry = {
                "radius_m": float(fore["outer_radius_mm"]) * 1e-3,
                "inner_radius_m": float(fore["inner_radius_mm"]) * 1e-3,
                "length_m": float(fore["thickness_mm"]) * 1e-3,
            }
            screen = _ring_plate(
                mount,
                pads,
                thrust_n,
                cfg,
                stop_geometry=stop_geometry,
                stop_parameters={},
                active_pad_count=max(1.0, active_pads),
            )
            screen["plate_station_m"] = mount.position_m + float(fore.get("station_mm", 0)) * 1e-3
            screen["integral_stop"] = True
            screen["rod_relief"] = relief
            screen["loaded_sector_equivalents_before_rounding"] = active_pads
            screen[
                "method"
            ] += " The rod relief is a partial annular cut; this is not a full-ring pass and does not resolve load redistribution or local stress at the relief edge."
            result["screens"]["thrust_plate_and_pads"] = screen
        else:
            result["screens"]["thrust_plate_and_pads"] = {
                "available": False,
                "reason": "TVC cassette has no enabled fore thrust stop in its CAD parameters.",
            }
    elif plate:
        result["screens"]["thrust_plate_and_pads"] = _ring_plate(plate, pads, thrust_n, cfg)
    else:
        result["screens"]["thrust_plate_and_pads"] = {
            "available": False,
            "reason": "No discrete fixed thrust plate; TVC integral cassette stop is screened only through rail section.",
        }
    result["screens"]["reverse_retainer"] = _retainer(vehicle, cfg, reverse_load_n)
    # Fixed plate/rail slot bearing and nominal circumferential mount-to-shell bond proxy.
    if plate and mount.cad and not is_cassette:
        params = mount.cad.parameters
        ro = float(mount.geometry.get("radius_m", 0))
        ring_t = _mm(params.get("ring_thickness_mm", 3))
        bond_area = 2 * math.pi * ro * ring_t
        result["screens"]["fixed_mount_bond_proxy"] = {
            "assumed_bond_area_m2": bond_area,
            "average_shear_pa": thrust_n / bond_area if bond_area else None,
            "strength_screens_pa": {"cold": 2e6, "hot": 1e6},
            "margin_DF3_cold": _margin(2e6, thrust_n / bond_area if bond_area else 0, factor),
            "margin_DF3_hot": _margin(1e6, thrust_n / bond_area if bond_area else 0, factor),
            "method": "A single 360-degree bond around the last mount ring is assumed; neither bond gap/land nor actual plywood-to-shell joint is modeled as a verified connection.",
        }
        notch = plate.cad.parameters.get("rail_notches", {}) if plate.cad else {}
        plate_t = _mm(plate.cad.parameters.get("thickness_mm")) if plate.cad else 0.0
        plate_t = plate_t or float(plate.geometry.get("length_m", 0))
        plate_ro = float(plate.geometry.get("radius_m", 0))
        fingers = plate.cad.parameters.get("bond_fingers", {}) if plate.cad else {}
        finger_depth = float(fingers.get("radial_depth_mm", 0))
        finger_length = float(fingers.get("length_mm", 0))
        finger_start = float(fingers.get("radius_mm", 0)) - finger_depth / 2
        side_y = float(fingers.get("side_center_mm", 0)) - float(fingers.get("wall_mm", 0)) / 2
        clipped_depth_geometry = (
            max(
                0.0,
                min(
                    finger_depth,
                    math.sqrt(max((plate_ro * 1000) ** 2 - side_y**2, 0)) - finger_start,
                ),
            )
            if finger_depth and finger_start < plate_ro * 1000
            else _mm(notch.get("depth_mm")) * 1000
        )
        clipped_depth = min(clipped_depth_geometry, 6.2) if fingers else clipped_depth_geometry
        finger_count = 6 if fingers else 0
        slot_bond_area = finger_count * clipped_depth * finger_length * 1e-6
        shell_bond_area = 2 * math.pi * plate_ro * plate_t
        result["screens"]["fixed_thrust_plate_bond_sensitivities"] = {
            "slot_sidewall_bond_area_m2_assumed": slot_bond_area,
            "bond_finger_count": finger_count,
            "bond_finger_clipped_radial_contact_width_mm": clipped_depth,
            "bond_finger_geometry_clip_width_mm": clipped_depth_geometry,
            "bond_finger_length_mm": finger_length,
            "slot_sidewall_average_shear_pa": thrust_n / slot_bond_area if slot_bond_area else None,
            "outer_plate_to_shell_bond_area_m2_assumed": shell_bond_area,
            "outer_plate_to_shell_average_shear_pa": (
                thrust_n / shell_bond_area if shell_bond_area else None
            ),
            "cold_epoxy_shear_screen_pa_estimated": 2e6,
            "hot_epoxy_shear_screen_pa_estimated": 1e6,
            "slot_margin_DF3_cold": _margin(
                2e6, thrust_n / slot_bond_area if slot_bond_area else 0, factor
            ),
            "slot_margin_DF3_hot": _margin(
                1e6, thrust_n / slot_bond_area if slot_bond_area else 0, factor
            ),
            "outer_bond_margin_DF3_cold": _margin(
                2e6, thrust_n / shell_bond_area if shell_bond_area else 0, factor
            ),
            "outer_bond_margin_DF3_hot": _margin(
                1e6, thrust_n / shell_bond_area if shell_bond_area else 0, factor
            ),
            "method": "Fixed six-finger estimate uses clipped radial contact width times 18 mm axial finger length for each slot flank, and a full circumferential plate OD bond over 9 mm web thickness. Adhesive geometry is not modeled; 0.2 mm flank gaps, peel, termination, wetting, cure and actual load split remain unresolved. Uniform-shear sensitivity only.",
        }
    # TVC radial fastener load transfer into gimbal, with fastener material capacity
    # intentionally omitted; compute only demand and substrate bearing.
    cad = mount.cad
    screws = cad.parameters.get("radial_mount_screws", []) if cad else []
    if screws:
        screw_count = len(screws)
        d = _mm(screws[0].get("diameter_mm", 2.7))
        engagement = _mm(screws[0].get("depth_mm", 8))
        mat = _material(cfg, mount, "G11")
        bearing = thrust_n / (screw_count * d * engagement) if d and engagement else None
        shear_area = math.pi * d**2 / 4
        screw_shear = thrust_n / (screw_count * shear_area) if shear_area else None
        result["screens"]["TVC_radial_screw_bearing"] = {
            "screw_count": screw_count,
            "nominal_hole_diameter_m": d,
            "configured_radial_hole_depth_m": engagement,
            "per_screw_axial_load_n": thrust_n / screw_count,
            "gross_shank_single_shear_area_m2": shear_area,
            "gross_shank_single_shear_stress_pa": screw_shear,
            "G11_bearing_stress_pa": bearing,
            "G11_hot_strength_screen_pa": mat.get("hot_strength_screen_pa"),
            "G11_hot_bearing_margin_DF3": _margin(
                float(mat.get("hot_strength_screen_pa", 25e6)), bearing or 0, factor
            ),
            "method": "Three radial screws share axial load equally. Gross shank single-shear and an upper-bound G11 projected bearing screen use configured screw-hole depth as engagement. Actual shear planes, wall thickness, thread stripping, countersink and gimbal ligaments require detailed geometry and fastener data; no screw strength capacity is assigned.",
        }
    return result
