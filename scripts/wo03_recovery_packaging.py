"""Build four read-only recovery mounting package copies and CAD-check their envelopes.

This is an isolated packaging candidate, not an active spec change or hardware
release. All unverified contact, service, and electrical assumptions are retained
in the YAML and run record.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cadquery as cq
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.cad.assembly import export_vehicle, rigid_intersections
from src.cad.parts import local_shape
from src.vehicle.aero import center_of_pressure
from src.vehicle.benchmark import evaluate_preliminary
from src.vehicle.mass import mass_properties
from src.vehicle.schema import Vehicle, load_vehicle_data, vehicle_input_paths

MODE_PATHS = {
    "modular-performance-v1": Path("configs/vehicle/platform/performance.yaml"),
    "modular-performance-g54-hypothesis": Path("configs/vehicle/wo02/performance-g54.yaml"),
    "modular-tvc-finned-v1": Path("configs/vehicle/platform/tvc-finned.yaml"),
    "modular-tvc-finless-v1": Path("configs/vehicle/platform/tvc-finless.yaml"),
}
OLD_MOUNT_IDS = {
    "recovery_mount_carrier",
    "recovery_alignment_pins",
    "recovery_mount_hardware_allowance",
}
NEW_PART_IDS = {
    "recovery_mount_carrier",
    "recovery_battery_tray",
    "recovery_battery_band",
    "recovery_standoffs",
    "recovery_fasteners",
    "recovery_nuts",
    "recovery_sled_fasteners",
    "recovery_sled_nuts",
    "recovery_easymini_components",
    "recovery_switch_g11_doubler",
    "recovery_sled_reinforcement",
    "recovery_mount_hardware_allowance",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def part_row(
    part_id: str,
    *,
    parent: str,
    position: float,
    lateral: list[float],
    bbox_mm: list[float],
    mass_kg: float,
    material: str,
    generator: str,
    parameters: dict[str, Any],
    role: str = "manufactured",
    color: str = "#658c9b",
    description: str,
    density: float | None = None,
    method: str = "assembled",
    estimate: bool = True,
) -> dict[str, Any]:
    return {
        "id": part_id,
        "type": "commercial",
        "parent": parent,
        "position_m": position,
        "lateral_offset_m": lateral,
        "geometry": {"bbox_m": [x / 1000 for x in bbox_mm]},
        "material": material,
        "mass_kg": mass_kg,
        "estimate": estimate,
        "learn": description,
        "build": {
            "method": method,
            "cost_usd": 0,
            "generator": generator,
            "notes": "Copy-only packaging proposal; source dimensions, fabrication and strength are not qualified.",
        },
        "cad": {
            "generator": generator,
            "parameters": parameters,
            "mass_basis": "supplied_or_estimated",
            "role": role,
            "moving_group": "fixed",
            "color": color,
            "notes": "Nominal candidate geometry. Interference-free CAD does not prove manufactured fit.",
        },
        "engineering": {
            "function": description,
            "material_profile": material,
            "tolerances_mm": {"linear": 0.25, "hole_diameter": 0.2},
            "load_cases": ["handling", "vibration"],
            "thermal_cases": ["G80", "G54", "G12"],
            "property_basis": "estimated",
            "service_notes": "Physical fit, preload, retention and insertion path remain unverified.",
            "required_physical_verification": [
                "Verify dimensions and material against manufactured and purchased parts.",
                "Inspect insertion, tool access, restraint and wiring service paths.",
                "Ground-test the independent battery and controller to manufacturer procedures under WO-09/10.",
            ],
        },
    }


def new_parts(cfg: dict[str, Any]) -> list[dict[str, Any]]:
    lay = cfg["layout"]
    hx, stations = (
        cfg["cad_geometry"]["controller_hole_x_mm"],
        cfg["cad_geometry"]["controller_hole_stations_from_carrier_mm"],
    )
    holes_plate = []
    for x in hx:
        for z in stations:
            holes_plate.append(
                {"start_mm": [x, -0.8, z], "axis": [0, 1, 0], "diameter_mm": 3.2, "length_mm": 1.6}
            )
    for x, z in cfg["cad_geometry"]["sled_mount_holes_from_carrier_mm"]:
        holes_plate.append(
            {"start_mm": [x, -0.8, z], "axis": [0, 1, 0], "diameter_mm": 2.8, "length_mm": 1.6}
        )
    plate = part_row(
        "recovery_mount_carrier",
        parent="avionics_bay",
        position=lay["carrier_front_station_m"],
        lateral=lay["carrier_body_lateral_yz_m"],
        bbox_mm=lay["carrier_bbox_mm_axial_width_thickness"],
        mass_kg=0.001,
        material="commercial",
        generator="envelope",
        parameters={"machining_holes": holes_plate},
        description="G11 mounting plate, 92 x 26 x 1 mm, with EasyMini/standoff and six sled fastener clearance holes.",
        density=cfg["mass"]["g11_density_kg_m3_estimate"],
        color="#a7a7a7",
    )

    # A 30 x 20 x 1 mm floor and four low rails make a tray that captures the
    # cell at its existing body-Z station while leaving the JST end accessible.
    tray = part_row(
        "recovery_battery_tray",
        parent="recovery_mount_carrier",
        position=lay["battery"]["front_station_m"],
        lateral=[0.0, 0.011],
        bbox_mm=lay["battery"]["tray_bbox_mm"],
        mass_kg=0.0005,
        material="ASA",
        generator="brackets",
        parameters={
            "blocks": [
                {"size_mm": [17.5, 1.0, 31.5], "position_mm": [0, 0, 0]},
                {"size_mm": [0.5, 1.5, 31.5], "position_mm": [-8.5, -0.25, 0]},
                {"size_mm": [0.5, 1.5, 31.5], "position_mm": [8.5, -0.25, 0]},
                {"size_mm": [14.5, 1.5, 1.0], "position_mm": [0, -0.25, 0]},
            ],
            "pockets": [],
        },
        description="Printed cradle floor and three perimeter rails for the dedicated 1S cell; open at JST lead end.",
        color="#be8f5b",
        method="printed",
    )
    band = part_row(
        "recovery_battery_band",
        parent="recovery_battery_tray",
        position=lay["battery"]["front_station_m"],
        lateral=lay["battery"]["body_lateral_yz_m"],
        bbox_mm=[8.0, 0.3, 0.8],
        mass_kg=0.00035,
        material="nylon",
        generator="envelope",
        parameters={},
        role="soft_stowage",
        description="8 mm woven nylon retaining band over the cell. Band path/closure remains an estimated flexible restraint.",
        color="#806548",
    )

    # Four actual nylon standoff envelopes with 5.4 mm component reliefs from
    # the board side and 3.2 mm through bores for M3 hardware.
    pinlist, reliefs = [], []
    for x in hx:
        for z in cfg["cad_geometry"]["controller_holes_local_mm"]:
            pinlist.append(
                {"start_mm": [x, -3.2, z], "axis": [0, 1, 0], "radius_mm": 2.5, "length_mm": 6.4}
            )
            reliefs.extend(
                [
                    {
                        "start_mm": [x, -3.2, z],
                        "axis": [0, 1, 0],
                        "diameter_mm": 5.4,
                        "length_mm": 4.4,
                    },
                    {
                        "start_mm": [x, -3.2, z],
                        "axis": [0, 1, 0],
                        "diameter_mm": 3.2,
                        "length_mm": 6.4,
                    },
                ]
            )
    standoffs = part_row(
        "recovery_standoffs",
        parent="recovery_mount_carrier",
        position=lay["board_front_station_m"],
        lateral=lay["standoffs_body_lateral_yz_m"],
        bbox_mm=[38.1, 13.97, 6.4],
        mass_kg=0.0003,
        material="nylon",
        generator="pins",
        parameters={"pins": pinlist, "machining_holes": reliefs},
        description="Four nylon M3 spacers, 5 mm OD x 3.2 mm bore x 6.4 mm long, with 5.4 x 4.4 mm component-side reliefs.",
        color="#8879aa",
    )

    # Cylinders model four M3x12 screw shanks and three-mm head envelopes.
    screws = []
    nuts = []
    for x in hx:
        for z in cfg["cad_geometry"]["controller_holes_local_mm"]:
            screws.extend(
                [
                    {
                        "start_mm": [x, -3.8, z],
                        "axis": [0, 1, 0],
                        "radius_mm": 2.6,
                        "length_mm": 3.0,
                    },
                    {
                        "start_mm": [x, -0.8, z],
                        "axis": [0, 1, 0],
                        "radius_mm": 1.5,
                        "length_mm": 12.0,
                    },
                ]
            )
            nuts.append({"size_mm": [5.5, 2.4, 5.5], "position_mm": [x, 0.0, z - 2.75]})
    fasteners = part_row(
        "recovery_fasteners",
        parent="independent_recovery",
        position=lay["board_front_station_m"],
        lateral=lay["fasteners_body_lateral_yz_m"],
        bbox_mm=[38.1, 5.5, 15.0],
        mass_kg=0.0012,
        material="nylon",
        generator="pins",
        parameters={"pins": screws},
        description="Four nylon M3 x 12 screws; 5.5 mm head and shank geometry is estimated, exact head/thread fit and preload unknown.",
        color="#aaa0bd",
    )
    board_nuts = part_row(
        "recovery_nuts",
        parent="recovery_mount_carrier",
        position=lay["board_front_station_m"],
        lateral=[0, 0.0057],
        bbox_mm=[38.1, 13.97, 2.4],
        mass_kg=0.00035,
        material="nylon",
        generator="brackets",
        parameters={
            "blocks": nuts,
            "pockets": [],
            "machining_holes": [
                {"start_mm": [x, -1.2, z], "axis": [0, 1, 0], "diameter_mm": 3.2, "length_mm": 2.4}
                for x in hx
                for z in cfg["cad_geometry"]["controller_holes_local_mm"]
            ],
        },
        description="Four nylon square-nut envelopes behind carrier plate; captive geometry and thread engagement not specified.",
        color="#a69abc",
    )

    sled_screws = []
    sled_nuts = []
    for x, z in cfg["cad_geometry"]["sled_mount_holes_from_carrier_mm"]:
        sled_screws.extend(
            [
                {"start_mm": [x, -2.5, z], "axis": [0, 1, 0], "radius_mm": 2.3, "length_mm": 2.0},
                {"start_mm": [x, -0.5, z], "axis": [0, 1, 0], "radius_mm": 1.25, "length_mm": 12.0},
            ]
        )
        sled_nuts.append({"size_mm": [4.5, 2.0, 4.5], "position_mm": [x, 0.0, z - 2.25]})
    mount_screws = part_row(
        "recovery_sled_fasteners",
        parent="recovery_mount_carrier",
        position=lay["carrier_front_station_m"],
        lateral=lay["carrier_body_lateral_yz_m"],
        bbox_mm=[92.0, 4.6, 14.0],
        mass_kg=0.0012,
        material="nylon",
        generator="pins",
        parameters={"pins": sled_screws},
        description="Six nylon M2.5 x 12 fastener envelopes through G11 plate and three sled crossbars; estimated 4.6 mm head radius leaves 0.6 mm nominal axial clearance to the controller aft end at station 0.421 m.",
        color="#c6ae8a",
    )
    mount_nuts = part_row(
        "recovery_sled_nuts",
        parent="avionics_bay",
        position=lay["carrier_front_station_m"],
        lateral=[0, -0.002],
        bbox_mm=[92, 4.5, 2.0],
        mass_kg=0.00045,
        material="nylon",
        generator="brackets",
        parameters={
            "blocks": sled_nuts,
            "pockets": [],
            "machining_holes": [
                {"start_mm": [x, -1, z], "axis": [0, 1, 0], "diameter_mm": 2.8, "length_mm": 2}
                for x, z in cfg["cad_geometry"]["sled_mount_holes_from_carrier_mm"]
            ],
        },
        description="Four nylon nut envelopes at the far side of the sled crossbars; crossbar reinforcement and captive retention are proposed, not active geometry.",
        color="#c6ae8a",
    )

    pads = part_row(
        "recovery_sled_reinforcement",
        parent="avionics_bay",
        position=0.356,
        lateral=[0.0, 0.0015],
        bbox_mm=[69.0, 29.0, 1.0],
        mass_kg=0.0002,
        material="ASA",
        generator="brackets",
        parameters={
            "blocks": [
                {
                    "size_mm": [8.0, 1.0, 8.0],
                    "position_mm": [
                        x,
                        0.0,
                        z + (lay["carrier_front_station_m"] - 0.356) * 1000 - 4.0,
                    ],
                }
                for x, z in cfg["cad_geometry"]["sled_mount_holes_from_carrier_mm"]
            ],
            "machining_holes": [
                {
                    "start_mm": [
                        x,
                        -0.5,
                        z + (lay["carrier_front_station_m"] - 0.356) * 1000,
                    ],
                    "axis": [0, 1, 0],
                    "diameter_mm": 2.8,
                    "length_mm": 1.0,
                }
                for x, z in cfg["cad_geometry"]["sled_mount_holes_from_carrier_mm"]
            ],
            "pockets": [],
        },
        description="Six 8 x 8 x 1 mm ASA pads proposed on the sled underside at three crossbars to spread M2.5 clamping load; active sled is unchanged.",
        color="#9b7959",
        method="printed",
    )

    # Controller PCB and a separate component-side envelope; total published
    # mass remains split as an explicit unmeasured allocation summing to 6.5 g.
    components = []
    for x in hx:
        for z in cfg["cad_geometry"]["controller_component_holes_local_mm"]:
            components.append(
                {"start_mm": [x, -2.2, z], "axis": [0, 1, 0], "diameter_mm": 5.4, "length_mm": 4.4}
            )
    return [plate, tray, band, standoffs, fasteners, board_nuts, mount_screws, mount_nuts, pads]


def copy_sources(source: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    data = copy.deepcopy(source)
    parts = {p["id"]: p for p in data["parts"]}
    data["parts"] = [p for p in data["parts"] if p["id"] not in OLD_MOUNT_IDS]
    # Split board into its physical 1.6 mm PCB and a distinct component keepout.
    board = parts["independent_recovery"]
    board.pop("cad_mass", None)
    board["geometry"]["bbox_m"] = [0.0381, 0.02032, 0.0016]
    board["lateral_offset_m"] = cfg["layout"]["pcb_body_lateral_yz_m"]
    board["mass_kg"] = 0.0030
    board["estimate"] = True
    board["cad"]["parameters"] = {
        "mount_holes_mm": [[x, z] for x in (-6.985, 6.985) for z in (3.175, 34.925)],
        "hole_diameter_mm": 3.2,
    }
    board["engineering"]["property_basis"] = "estimated"
    components = part_row(
        "recovery_easymini_components",
        parent="independent_recovery",
        position=0.380,
        lateral=cfg["layout"]["components_body_lateral_yz_m"],
        bbox_mm=[38.1, 20.32, 4.4],
        mass_kg=0.0035,
        material="commercial",
        generator="envelope",
        parameters={
            "machining_holes": [
                {
                    "start_mm": [x, -2.2, z],
                    "axis": [0, 1, 0],
                    "diameter_mm": 5.4,
                    "length_mm": 4.4,
                }
                for x in cfg["cad_geometry"]["controller_hole_x_mm"]
                for z in cfg["cad_geometry"]["controller_component_holes_local_mm"]
            ]
        },
        role="purchased_envelope",
        color="#628c6c",
        description="Estimated 4.4 mm component keepout over the EasyMini PCB; only the four 5.4 mm reliefs are represented, exact component locations require board revision drawing/inspection.",
    )
    data["parts"].append(components)
    recovery_battery = parts["recovery_battery"]
    recovery_battery["lateral_offset_m"] = cfg["layout"]["battery"]["body_lateral_yz_m"]
    # Switch wall hole is a single radial bore in the study copy of body_upper.
    upper = parts["body_upper"]
    upper.pop("cad_mass", None)
    upper["cad"].setdefault("parameters", {})["machining_holes"] = [
        {
            "start_mm": [0.0, -34.0, 330.0],
            "axis": [0.0, 1.0, 0.0],
            "diameter_mm": 15.875,
            "length_mm": 3.5,
        }
    ]
    switch = parts["recovery_power_switch"]
    switch.pop("cad_mass", None)
    switch["position_m"] = 0.4557125
    switch["lateral_offset_m"] = [0.0, 0.02875]
    switch["geometry"]["bbox_m"] = [0.028575, 0.015875, 0.0127]
    switch["cad"]["parameters"] = {}
    switch["learn"] = (
        "Schurter SWA1 family switch envelope mounted through the proposed 15.875 mm radial body port. Exact 0033.4518 revision and DC rating unconfirmed."
    )
    doubler = part_row(
        "recovery_switch_g11_doubler",
        parent="body_upper",
        position=0.455,
        lateral=[0.0, 0.0338],
        bbox_mm=[30.0, 30.0, 1.6],
        mass_kg=0.00266,
        material="commercial",
        generator="envelope",
        parameters={"mount_holes_mm": [[0.0, 15.0]], "hole_diameter_mm": 15.875},
        description="30 x 30 x 1.6 mm G11 switch doubler envelope bonded over the radial panel port; local curved fit is not developed.",
        color="#aaaaaa",
    )
    data["parts"].extend([doubler, *new_parts(cfg)])
    data["parts"].append(
        part_row(
            "recovery_mount_hardware_allowance",
            parent="avionics_bay",
            position=0.333,
            lateral=[0.0, -0.021],
            bbox_mm=[86.0, 2.0, 2.0],
            mass_kg=0.0035,
            material="commercial",
            generator="budget",
            parameters={},
            role="distributed_budget",
            description="Residual of the active 6.283 g generic mount allowance after subtracting explicit CAD-derived replacement cradle, restraint and fastener masses.",
            color="#c89b4f",
        )
    )
    # Use only the dedicated recovery functional edges in the isolated copies.
    data["netlist"] = [
        n for n in data.get("netlist", []) if not str(n.get("net", "")).startswith("RECOVERY_")
    ]
    data["netlist"].extend(copy.deepcopy(cfg["netlist"]["required_edges"]))
    return data


def state_stats(vehicle: Vehicle) -> dict[str, Any]:
    states = []
    for burn in (0.0, 1.0):
        mp = mass_properties(vehicle, burn)
        states.append(
            {
                "burn_fraction": burn,
                "mass_kg": mp.mass_kg,
                "cg_station_m": mp.cg_m,
                "cg_lateral_m": list(mp.cg_lateral_m),
                "inertia_kg_m2": mp.inertia_kg_m2.tolist(),
            }
        )
    cp = center_of_pressure(vehicle)
    margins = []
    for s in states:
        allowance = vehicle.design.mass_allowance_kg
        m = s["mass_kg"]
        cg = (m * s["cg_station_m"] + allowance * vehicle.airframe["length_m"]) / (m + allowance)
        margins.append(
            {
                "burn_fraction": s["burn_fraction"],
                "cp_station_m": cp,
                "cg_with_50g_aft_growth_m": cg,
                "static_margin_cal": (cp - cg) / vehicle.airframe["body_diameter_m"],
            }
        )
    return {
        "states": states,
        "margins_with_full_50g_aft_growth": margins,
        "preliminary_screen": evaluate_preliminary(vehicle),
        "flight_ready": False,
    }


def mount_beam_screen(cfg: dict[str, Any]) -> dict[str, Any]:
    q = cfg["structural_mount_screen"]
    width = float(q["carrier_width_mm"])
    thickness = float(q["carrier_thickness_mm"])
    inertia = width * thickness**3 / 12.0
    modulus = float(q["hot_modulus_gpa_estimate"]) * 1000.0  # GPa to N/mm^2
    span = float(q["board_span_mm"])
    force_board = float(q["board_row_load_n_including_project_factor"])
    length_cell = float(q["cell_overhang_mm"])
    force_cell = float(q["cell_overhang_load_n_including_project_factor"])
    board_delta = force_board * span**3 / (48.0 * modulus * inertia)
    cell_delta = force_cell * length_cell**3 / (3.0 * modulus * inertia)
    return {
        "material": q["material"],
        "hot_modulus_gpa_estimate": modulus / 1000.0,
        "support_rows_station_m": q["support_rows_station_m"],
        "mount_row_count": len(q["support_rows_station_m"]),
        "carrier_length_m": q["carrier_length_m"],
        "carrier_width_mm": width,
        "carrier_thickness_mm": thickness,
        "rectangular_section_I_mm4": inertia,
        "board_point_load_n_including_project_factor": force_board,
        "board_supported_span_mm": span,
        "board_simply_supported_deflection_mm": board_delta,
        "cell_overhang_load_n_including_project_factor": force_cell,
        "cell_cantilever_overhang_mm": length_cell,
        "cell_cantilever_deflection_mm": cell_delta,
        "additional_factor_applied": False,
        "interpretation": "Linear-elastic beam screen using estimated hot modulus and specified point loads; load path, restraint, fasteners, laminate property and thermal qualification remain unverified.",
    }


def _bounds(shape: Any) -> tuple[float, float, float, float, float, float]:
    b = shape.BoundingBox()
    return b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax


def _bounds_overlap(
    a: tuple[float, float, float, float, float, float],
    b: tuple[float, float, float, float, float, float],
    expansion_mm: float = 0.0,
) -> bool:
    return all(
        a[2 * i] - expansion_mm < b[2 * i + 1] + expansion_mm
        and b[2 * i] - expansion_mm < a[2 * i + 1] + expansion_mm
        for i in range(3)
    )


def _max_radial_bound_mm(shape: Any) -> float:
    x0, x1, y0, y1, _, _ = _bounds(shape)
    return math.hypot(max(abs(x0), abs(x1)), max(abs(y0), abs(y1)))


def swept_clearance(
    solids: dict[str, Any],
    *,
    moving_ids: set[str],
    obstacle_ids: set[str],
    translation: tuple[float, float, float],
    steps: int,
    label: str,
    source_tolerance_mm: float = 0.25,
    tolerance_obstacle_ids: set[str] | None = None,
    start_offset_mm: tuple[float, float, float] = (0.0, 0.0, 0.0),
    expected_start_contacts: set[tuple[str, str]] | None = None,
    analytic_obstacles: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Check path with BReps; accept explicit radial-containment proof for rings."""
    moved = [pid for pid in moving_ids if pid in solids]
    analytic_obstacles = analytic_obstacles or {}
    obstacles = [pid for pid in obstacle_ids if pid in solids and pid not in moving_ids]
    analytic_obstacles = {
        pid: proof for pid, proof in analytic_obstacles.items() if pid in obstacles
    }
    obstacles = [pid for pid in obstacles if pid not in analytic_obstacles]
    tolerance_obstacles = (
        set(obstacles)
        if tolerance_obstacle_ids is None
        else set(obstacles) & tolerance_obstacle_ids
    )
    nominal_hit: dict[str, Any] | None = None
    tolerance_hit: dict[str, Any] | None = None
    min_pair_clearance: float | None = None
    expected_start_contacts = expected_start_contacts or set()
    observed_start_contacts: set[tuple[str, str]] = set()
    for i in range(steps + 1):
        fraction = i / steps if steps else 0.0
        dx, dy, dz = (start_offset_mm[j] + translation[j] * fraction for j in range(3))
        for moving_id in moved:
            base = solids[moving_id]
            shifted = base.translate(cq.Vector(dx, dy, dz))
            shifted_bounds = _bounds(shifted)
            for obstacle_id in obstacles:
                obstacle = solids[obstacle_id]
                obstacle_bounds = _bounds(obstacle)
                nominal_aabb = _bounds_overlap(shifted_bounds, obstacle_bounds)
                tolerance_aabb = obstacle_id in tolerance_obstacles and _bounds_overlap(
                    shifted_bounds, obstacle_bounds, 2 * source_tolerance_mm
                )
                if nominal_aabb and nominal_hit is None:
                    overlap_volume = shifted.intersect(obstacle).Volume()
                    if overlap_volume > 0.05:
                        nominal_hit = {
                            "step": i,
                            "fraction": fraction,
                            "moving_part": moving_id,
                            "obstacle_part": obstacle_id,
                            "intersection_volume_mm3": overlap_volume,
                        }
                if tolerance_aabb:
                    separation = shifted.distance(obstacle)
                    pair = tuple(sorted((moving_id, obstacle_id)))
                    expected_start_contact = (
                        i == 0 and pair in expected_start_contacts and separation < 0.05
                    )
                    min_pair_clearance = (
                        separation
                        if min_pair_clearance is None
                        else min(min_pair_clearance, separation)
                    )
                    if expected_start_contact:
                        observed_start_contacts.add(pair)
                    elif tolerance_hit is None and separation < 2 * source_tolerance_mm:
                        tolerance_hit = {
                            "step": i,
                            "fraction": fraction,
                            "moving_part": moving_id,
                            "obstacle_part": obstacle_id,
                            "measured_brep_separation_mm": separation,
                            "required_two_sided_separation_mm": 2 * source_tolerance_mm,
                            "basis": "BRep minimum-distance check with 0.25 mm applied to both parts",
                        }
        if nominal_hit and tolerance_hit:
            break
    return {
        "path_id": label,
        "translation_mm": list(translation),
        "start_offset_mm": list(start_offset_mm),
        "sample_step_count": steps,
        "sample_spacing_mm_max": max(abs(v) for v in translation) / max(steps, 1),
        "source_tolerance_mm_each": source_tolerance_mm,
        "nominal_brep_collision": nominal_hit,
        "nominal_brep_clear": nominal_hit is None,
        "expanded_bound_collision_candidate": tolerance_hit,
        "expanded_bound_clear": tolerance_hit is None,
        "minimum_checked_brep_separation_mm": min_pair_clearance,
        "expected_start_contact_pairs": sorted([list(x) for x in observed_start_contacts]),
        "moving_parts": sorted(moved),
        "checked_obstacle_parts": sorted(obstacles + list(analytic_obstacles)),
        "analytic_radial_obstacle_proofs": analytic_obstacles,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--config", type=Path, default=Path("configs/platform.yaml"))
    p.add_argument(
        "--study", type=Path, default=Path("configs/studies/wo03-recovery-packaging.yaml")
    )
    p.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    a = p.parse_args()
    start = time.perf_counter()
    cfg = yaml.safe_load(a.study.read_text())
    platform = yaml.safe_load(a.config.read_text())
    if set(MODE_PATHS) != set(cfg["included_modes"]):
        raise ValueError("Study modes differ from copy source list")
    if (
        Path(platform["shared_upper"]).resolve()
        != Path("configs/vehicle/platform/common-upper.yaml").resolve()
    ):
        raise ValueError("Expected current shared upper")
    hashes = {
        a.config.as_posix(): sha(a.config),
        a.study.as_posix(): sha(a.study),
        Path(__file__).as_posix(): sha(Path(__file__)),
    }
    for src in MODE_PATHS.values():
        for item in vehicle_input_paths(src):
            hashes[item.as_posix()] = sha(item)
    outdir = Path("build/wo03-recovery-packaging")
    outdir.mkdir(parents=True, exist_ok=True)
    rows, collisions_all = [], []
    allowed = {tuple(x) for x in cfg["verification"]["allowed_contact_pairs"]}
    for mode, src in MODE_PATHS.items():
        baseline = Vehicle.model_validate(load_vehicle_data(src))
        raw = copy_sources(load_vehicle_data(src), cfg)
        draft = Vehicle.model_validate(raw)
        # Geometry-derived candidate masses, using explicit material density estimates.
        density = {
            "commercial": cfg["mass"]["g11_density_kg_m3_estimate"],
            "nylon": 1150.0,
            "ASA": 1070.0,
        }
        derived_ids = NEW_PART_IDS | {"recovery_easymini_components", "recovery_switch_g11_doubler"}
        refreshed_shape_ids = derived_ids | {
            "body_upper",
            "independent_recovery",
            "recovery_power_switch",
        }
        for part in draft.parts:
            if part.id in derived_ids:
                part.mass_kg = (
                    local_shape(part).Volume() * 1e-9 * density.get(part.material, 1200.0)
                )
        # Preserve published board/cell/switch masses while assigning the
        # EasyMini total between board PCB and estimated component envelope.
        draft_by_id = {p.id: p for p in draft.parts}
        draft_by_id["independent_recovery"].mass_kg = 0.0030
        draft_by_id["recovery_easymini_components"].mass_kg = 0.0035
        draft_by_id["recovery_battery_band"].mass_kg = 0.00035
        draft_by_id["recovery_power_switch"].mass_kg = (
            cfg["source_facts"]["rotary_switch"]["mass_g_estimate"] / 1000
        )
        draft_by_id["recovery_battery"].mass_kg = cfg["source_facts"]["cell"]["mass_g"] / 1000
        explicit_hardware_ids = {
            "recovery_battery_tray",
            "recovery_battery_band",
            "recovery_fasteners",
            "recovery_nuts",
            "recovery_sled_fasteners",
            "recovery_sled_nuts",
            "recovery_sled_reinforcement",
        }
        explicit_hardware_g = (
            sum(p.mass_kg for p in draft.parts if p.id in explicit_hardware_ids) * 1000
        )
        old_generic_allowance_g = cfg["mass"]["old_generic_recovery_mount_allowance_g"]
        residual_allowance_g = max(0.0, old_generic_allowance_g - explicit_hardware_g)
        draft_by_id["recovery_mount_hardware_allowance"].mass_kg = residual_allowance_g / 1000
        # Save pre-export source identity; exported CAD mass hashes feed subsequent real loads.
        folder = outdir / mode
        manifest, solids = export_vehicle(draft, folder, True)
        allowed_collisions = []
        unexpected = []
        for c in rigid_intersections(draft, solids):
            pair = tuple(sorted((c["a"], c["b"])))
            if pair in {tuple(sorted(x)) for x in allowed}:
                allowed_collisions.append(c)
            else:
                unexpected.append(c)
        # Nominal 6 mm arming-tool corridor from the exterior through the switch
        # port. It is a clearance probe, not a physical tool or verified access.
        tool_corridor = cq.Solid.makeCylinder(
            3.0, 25.0, cq.Vector(0.0, -34.6, 330.0), cq.Vector(0.0, -1.0, 0.0)
        )
        tool_blockers = []
        for part_id, solid in solids.items():
            if part_id in {"body_upper", "recovery_switch_g11_doubler", "recovery_power_switch"}:
                continue
            if tool_corridor.intersect(solid).Volume() > 0.05:
                tool_blockers.append(part_id)
        manifest_rows = {x["id"]: x for x in manifest["parts"]}
        final = draft.model_dump(by_alias=True)
        for row in final["parts"]:
            if row["id"] in refreshed_shape_ids:
                row["cad_mass"] = manifest_rows[row["id"]]["properties"]
        vehicle = Vehicle.model_validate(final)
        manifest, solids = export_vehicle(vehicle, folder, True)
        # Three-row carrier and service sweeps are checked on the actual copied
        # CAD solids. Fasteners are removed and electrical leads disconnected
        # before carrier extraction; the flexible battery band is released first.
        body = next(p for p in vehicle.parts if p.id == "body_upper")
        body_end_station = body.position_m + float(body.geometry["length_m"])
        body_inner_radius = float(body.geometry["inner_radius_m"]) * 1000.0
        carrier_group = {
            "recovery_mount_carrier",
            "recovery_battery_tray",
            "recovery_battery",
            "recovery_standoffs",
            "recovery_fasteners",
            "recovery_nuts",
            "independent_recovery",
            "recovery_easymini_components",
        }
        service_removed_or_disconnected = {
            "recovery_sled_fasteners",
            "recovery_output_harness",
            "recovery_battery_band",
            "recovery_mount_hardware_allowance",
        }
        aft_module_parts = {
            "aft_shell",
            "aft_interface_hardware",
            "aft_retainer",
            "aft_thrust_pads",
            "cassette_mount_screws",
            "fin_bonds",
            "fin_set",
            "gimbal_frame",
            "gimbal_inner",
            "gimbal_links",
            "inner_pivots",
            "motor",
            "motor_liner",
            "motor_mount",
            "motor_radiant_shield",
            "outer_pivots",
            "retention",
            "retention_hardware",
            "servo_horns",
            "servo_pitch",
            "servo_support",
            "servo_yaw",
            "thrust_pads",
        }
        removed_aft_module = set(solids) & aft_module_parts
        shell_ids = {"body_upper", "aft_shell", "interface_coupler", "nose_cone"}
        carrier_obstacles = (
            set(solids) - carrier_group - service_removed_or_disconnected - removed_aft_module
        )
        carrier_tolerance_obstacles = carrier_obstacles - shell_ids
        carrier_radial_max = max(_max_radial_bound_mm(solids[part_id]) for part_id in carrier_group)
        part_specs = {part.id: part for part in vehicle.parts}
        radial_bores: dict[str, dict[str, Any]] = {}
        for obstacle_id in ("body_upper", "interface_coupler", "joint_stop"):
            obstacle = part_specs[obstacle_id]
            bore_mm = float(obstacle.geometry["inner_radius_m"]) * 1000.0
            if obstacle_id == "joint_stop":
                parameters = obstacle.cad.parameters
                keyed_bore = float(parameters["key_radius_mm"]) - float(parameters["key_depth_mm"])
                bore_mm = min(bore_mm, keyed_bore)
            clearance = bore_mm - carrier_radial_max
            radial_bores[obstacle_id] = {
                "minimum_bore_radius_mm": bore_mm,
                "moving_package_outer_radial_bound_mm": carrier_radial_max,
                "nominal_radial_clearance_mm": clearance,
                "clearance_after_two_0p25mm_source_tolerances_mm": clearance - 0.5,
                "passed": clearance - 0.5 > 0,
            }
        # Remove the aft module at its existing joint, then draw the complete
        # carrier aft through the coupler opening and clear the upper bay.
        carrier_translation_z = (
            body_end_station - cfg["layout"]["carrier_front_station_m"]
        ) * 1000.0
        carrier_sweep = swept_clearance(
            solids,
            moving_ids=carrier_group,
            obstacle_ids=carrier_obstacles,
            tolerance_obstacle_ids=carrier_tolerance_obstacles,
            translation=(0.0, 0.0, carrier_translation_z),
            steps=math.ceil(abs(carrier_translation_z) / 2.0),
            label="remove_aft_module_disconnect_leads_remove_mounts_then_slide_carrier_aft_through_coupler",
            analytic_obstacles=radial_bores,
        )
        carrier_tube_clearance = radial_bores["body_upper"]["nominal_radial_clearance_mm"]
        carrier_tube_clearance_tolerance = carrier_tube_clearance - 0.5

        cell_id = "recovery_battery"
        # The carrier is now outside the rocket. Check cell release inside that
        # withdrawn assembly, rather than pretending it can pass through the
        # installed aft coupler.
        withdrawn_group = {
            part_id: solids[part_id].translate(cq.Vector(0.0, 0.0, carrier_translation_z))
            for part_id in carrier_group
        }
        cell_obstacles = set(carrier_group) - {
            cell_id,
            "recovery_battery_band",
        }
        cell_tolerance_obstacles = cell_obstacles
        cell_lift_mm = 8.0
        radial_lift = swept_clearance(
            withdrawn_group,
            moving_ids={cell_id},
            obstacle_ids=cell_obstacles,
            tolerance_obstacle_ids=cell_tolerance_obstacles,
            translation=(0.0, -cell_lift_mm, 0.0),
            steps=math.ceil(cell_lift_mm / 0.5),
            label="after_carrier_withdrawal_unplug_release_band_then_lift_cell_outward_from_tray",
            expected_start_contacts={("recovery_battery", "recovery_battery_tray")},
        )
        cell_lane_shape = withdrawn_group[cell_id].translate(cq.Vector(0, -cell_lift_mm, 0))
        cell_radial_max = _max_radial_bound_mm(cell_lane_shape)
        cell_tube_clearance = body_inner_radius - cell_radial_max
        cell_tube_clearance_tolerance = cell_tube_clearance - 0.5
        battery_extraction_clear = (
            radial_lift["nominal_brep_clear"] and radial_lift["expanded_bound_clear"]
        )
        carrier_removal_clear = (
            carrier_sweep["nominal_brep_clear"]
            and carrier_sweep["expanded_bound_clear"]
            and carrier_tube_clearance_tolerance > 0.0
            and all(proof["passed"] for proof in radial_bores.values())
        )
        package_sweeps = {
            "carrier_removal": {
                **carrier_sweep,
                "active_body_upper_aft_end_station_m": body_end_station,
                "carrier_front_station_m": cfg["layout"]["carrier_front_station_m"],
                "axial_translation_mm_through_coupler_opening": carrier_translation_z,
                "removed_aft_module_parts_before_sweep": sorted(removed_aft_module),
                "max_package_radial_extent_mm": carrier_radial_max,
                "body_inner_radius_mm": body_inner_radius,
                "nominal_tube_radial_clearance_mm": carrier_tube_clearance,
                "tube_radial_clearance_after_two_source_tolerances_mm": carrier_tube_clearance_tolerance,
                "minimum_radial_bore_clearances": radial_bores,
                "clear_under_screened_assumptions": carrier_removal_clear,
                "requires_removing_aft_module_six_carrier_screws_and_controller_output_disconnection": True,
            },
            "battery_extraction": {
                "path_segments": [radial_lift],
                "carrier_withdrawal_translation_mm": carrier_translation_z,
                "outward_cell_lift_mm": cell_lift_mm,
                "max_cell_radial_extent_mm": cell_radial_max,
                "body_inner_radius_mm": body_inner_radius,
                "nominal_tube_radial_clearance_mm": cell_tube_clearance,
                "tube_radial_clearance_after_two_source_tolerances_mm": cell_tube_clearance_tolerance,
                "main_battery_geometry_part_checked": False,
                "connector_or_lead_protrusion_modeled": False,
                "clear_under_screened_assumptions": battery_extraction_clear,
            },
        }
        beam_screen = mount_beam_screen(cfg)
        resolved = folder / "resolved-copy.yaml"
        resolved.write_text(yaml.safe_dump(vehicle.model_dump(by_alias=True), sort_keys=False))
        stats, baseline_stats = state_stats(vehicle), state_stats(baseline)
        inserted = [
            c
            for c in rigid_intersections(vehicle, solids)
            if c["a"] in NEW_PART_IDS
            or c["b"] in NEW_PART_IDS
            or c["a"] in {"recovery_easymini_components", "recovery_switch_g11_doubler"}
            or c["b"] in {"recovery_easymini_components", "recovery_switch_g11_doubler"}
        ]
        filtered = [
            c
            for c in inserted
            if tuple(sorted((c["a"], c["b"]))) not in {tuple(sorted(x)) for x in allowed}
        ]
        collisions_all.extend({"mode": mode, **c} for c in filtered)
        new_masses = {p.id: p.resolved_mass_kg * 1000 for p in vehicle.parts if p.id in derived_ids}
        old_mount_mass = (
            sum(p.resolved_mass_kg for p in baseline.parts if p.id in OLD_MOUNT_IDS) * 1000
        )
        mount_component_ids = NEW_PART_IDS - {"recovery_easymini_components"}
        new_mount_mass = sum(m for pid, m in new_masses.items() if pid in mount_component_ids)
        recovery_topology = [
            n.model_dump(by_alias=True, exclude_none=True)
            for n in vehicle.netlist
            if n.net.startswith("RECOVERY_")
        ]
        expected_recovery_topology = sorted(
            (n["net"], n["from"], n["to"]) for n in cfg["netlist"]["required_edges"]
        )
        observed_recovery_topology = sorted(
            (n["net"], n["from"], n["to"]) for n in recovery_topology
        )
        recovery_topology_passed = observed_recovery_topology == expected_recovery_topology and all(
            not n["net"].startswith("RECOVERY_INDEPENDENT") for n in recovery_topology
        )
        if not recovery_topology_passed:
            raise ValueError(f"{mode}: isolated recovery netlist differs from required boundary")
        delta = stats["states"][0]["mass_kg"] - baseline_stats["states"][0]["mass_kg"]
        rows.append(
            {
                "mode": mode,
                "resolved_copy": resolved.as_posix(),
                "assembly_glb": (folder / "assembly.glb").as_posix(),
                "assembly_step": (folder / "assembly.step").as_posix(),
                "package_mass_and_inertia": stats,
                "baseline_mass_and_inertia": baseline_stats,
                "candidate_mass_delta_g": delta * 1000,
                "replaced_active_mount_mass_g": old_mount_mass,
                "candidate_component_masses_g": new_masses,
                "new_modeled_mount_and_retention_mass_g": new_mount_mass,
                "candidate_mass_delta_vs_previous_two_row_candidate_g": delta * 1000.0
                - float(cfg["previous_candidate_mass_delta_g"]),
                "old_allowance_reduction": {
                    "old_generic_allowance_g": old_generic_allowance_g,
                    "explicit_new_hardware_deducted_g": explicit_hardware_g,
                    "residual_allowance_g": residual_allowance_g,
                    "calculation": "max(0, old 6.283 g allowance - CAD-derived tray/band/screw/nut/reinforcement masses)",
                },
                "inserted_pair_intersections": inserted,
                "unexplained_candidate_intersections": filtered,
                "named_contact_pair_intersections": allowed_collisions,
                "cad_solid_validity": {x["id"]: x["valid_solid"] for x in manifest["parts"]},
                "recovery_topology": recovery_topology,
                "recovery_topology_passed": recovery_topology_passed,
                "switch_tool_corridor": {
                    "diameter_mm": 6.0,
                    "depth_mm": 25.0,
                    "intersects_other_copied_parts": tool_blockers,
                    "clear_of_other_copied_parts": not tool_blockers,
                    "actuator_tool_interface_verified": False,
                },
                "service_sweeps": package_sweeps,
                "three_row_mount_beam_screen": beam_screen,
                "axial_service_clearances_mm": {
                    "battery_end_to_board_front": round((0.380 - (0.333 + 0.030)) * 1000, 3),
                    "board_end_to_switch_front": round((0.4557125 - (0.380 + 0.0381)) * 1000, 3),
                    "battery_end_to_switch_front": round((0.4557125 - (0.333 + 0.030)) * 1000, 3),
                    "carrier_to_sled_face_nominal": cfg["layout"]["sled_attachment"][
                        "carrier_to_sled_clearance_mm"
                    ],
                    "carrier_aft_end_station_m": cfg["layout"]["sled_attachment"][
                        "carrier_aft_end_station_m"
                    ],
                    "previous_mount_row_to_carrier_aft_end_mm": cfg["layout"]["sled_attachment"][
                        "previous_two_row_rear_overhang_mm"
                    ],
                    "third_mount_row_to_carrier_aft_end_mm": cfg["layout"]["sled_attachment"][
                        "aft_end_overhang_after_third_row_mm"
                    ],
                    "controller_end_to_third_screwhead_axial_clearance_mm": cfg["layout"][
                        "sled_attachment"
                    ]["third_row_to_board_end_axial_clearance_mm"],
                },
                "flight_ready": False,
            }
        )
        print(
            f"{mode}: mass delta {delta*1000:+.2f} g; unexplained overlaps {len(filtered)}",
            flush=True,
        )
    after = {name: sha(Path(name)) for name in hashes}
    run_id = datetime.now(UTC).strftime("wo03-recovery-packaging-%Y%m%dT%H%M%S%fZ")
    runpath = Path("runs") / run_id
    runpath.mkdir(parents=True, exist_ok=False)
    record = {
        "run_id": run_id,
        "study": cfg["id"],
        "preset": a.preset,
        "elapsed_s": time.perf_counter() - start,
        "source_hashes_before": hashes,
        "source_hashes_after": after,
        "inputs_unchanged": hashes == after,
        "modes": rows,
        "collision_exceptions": sorted([list(x) for x in allowed]),
        "previous_candidate_reference": {
            "record_id": cfg["previous_candidate_record"],
            "package_mass_delta_g": cfg["previous_candidate_mass_delta_g"],
            "new_package_mass_delta_g": rows[0]["candidate_mass_delta_g"],
            "mass_delta_reduction_g": cfg["previous_candidate_mass_delta_g"]
            - rows[0]["candidate_mass_delta_g"],
        },
        "three_row_mount_beam_screen": mount_beam_screen(cfg),
        "portable_copy_output": {
            "latest_json": (outdir / "latest.json").as_posix(),
            "mode_copy_root": outdir.as_posix(),
            "resolved_spec_filenames": [row["resolved_copy"] for row in rows],
            "assembly_glb_filenames": [row["assembly_glb"] for row in rows],
        },
        "source_deployment_or_hardware_qualification": False,
        "acceptance_passed": False,
        "flight_ready": False,
        "open_questions": cfg["open_questions"],
    }
    (runpath / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    (outdir / "latest-record.json").write_text(json.dumps(record, indent=2) + "\n")
    (outdir / "latest.json").write_text(json.dumps(record, indent=2) + "\n")
    print(runpath / "record.json")
    return 0 if record["inputs_unchanged"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
