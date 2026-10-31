"""Execute a copy-only positive modular-joint/indexing correction.

Normal CAD generators own every prototype solid. Basic bearing, shear, tearout,
eccentric fastener bending and bond average-shear equations follow NASA RP-1228
and elementary static equilibrium. Bounds are declared study estimates, never
hardware allowables. A missing captive-nut feature and failed recovery cases stay
open; no generated cylinder is treated as a captive nut or a bypass harness.
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

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_correction_package import package_copy
from src.cad.parts import local_shape, properties, shape_digest
from src.vehicle.benchmark import evaluate_preliminary
from src.vehicle.mass import mass_properties
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import CADMass, Part, Vehicle, load_vehicle, vehicle_input_paths


def radial(radius: float, angle: float, z: float = 0) -> list[float]:
    a = math.radians(angle)
    return [radius * math.cos(a), radius * math.sin(a), z]


def drill(radius: float, angle: float, z: float, diameter: float, length: float) -> dict[str, Any]:
    return {
        "start_mm": radial(radius, angle, z),
        "axis": radial(-1, angle),
        "diameter_mm": diameter,
        "length_mm": length,
    }


def new_part(
    template: Part,
    name: str,
    station: float,
    length: float,
    ri: float,
    ro: float,
    material: str,
    parameters: dict[str, Any],
    function: str,
) -> Part:
    raw = template.model_dump(by_alias=True)
    raw.update(
        id=name,
        parent="interface_coupler",
        type="commercial",
        position_m=station / 1000,
        lateral_offset_m=[0, 0],
        geometry={"length_m": length / 1000, "radius_m": ro / 1000, "inner_radius_m": ri / 1000},
        material=material,
        mass_kg=0.000001,
        density_kg_m3=None,
        cad_mass=None,
        cg_offset_m=length / 2000,
        learn=function,
        print=None,
        cite=None,
        estimate=True,
    )
    raw["cad"].update(
        generator="tube",
        parameters=parameters,
        mass_basis="volume_density",
        role="manufactured",
        moving_group="fixed",
        notes=function,
    )
    raw["build"].update(
        method="bonded" if material == "epoxy" else "cut", generator="tube", notes=function
    )
    raw["engineering"].update(
        material_profile=material,
        function=function,
        tolerances_mm={"linear": 0.05, "hole_diameter": 0.05},
    )
    return Part.model_validate(raw)


def passages(cfg: dict[str, Any], station: float, length: float) -> list[dict[str, Any]]:
    k, d = cfg["keys"], cfg["datums_mm"]
    return [
        {
            "start_mm": radial(k["radius_mm"], a, d["aft_start"] - station - 0.01),
            "axis": [0, 0, 1],
            "diameter_mm": diameter,
            "length_mm": length + 0.02,
        }
        for a, diameter in zip(d["key_angles_deg"], k["slot_diameters_mm"], strict=True)
    ]


def make_candidate(vehicle: Vehicle, cfg: dict[str, Any]) -> tuple[Vehicle, set[str]]:
    """Mutate only a deep resolved copy; all geometry uses the normal CAD contract."""
    candidate = vehicle.model_copy(deep=True)
    parts = {p.id: p for p in candidate.parts}
    d, k, f = cfg["datums_mm"], cfg["keys"], cfg["fasteners"]
    changed = {"interface_coupler", "joint_stop", "aft_shell"}
    coupler, stop, shell = (parts[p] for p in ("interface_coupler", "joint_stop", "aft_shell"))
    assert coupler.cad and stop.cad and shell.cad
    coupler.cad.parameters.update(
        key_depth_mm=k["coupler_slot_depth_mm"], key_widths_mm=k["coupler_slot_widths_mm"]
    )
    stop.cad.parameters.update(
        key_radius_mm=k["radius_mm"],
        key_depth_mm=k["depth_mm"],
        key_widths_mm=k["widths_mm"],
        key_length_mm=k["length_mm"],
    )
    shell.cad.parameters.setdefault("machining_holes", []).extend(
        passages(cfg, shell.position_m * 1000, k["passage_length_mm"])
    )
    added: list[Part] = []
    b = cfg["upper_bond"]
    added.append(
        new_part(
            coupler,
            "joint_upper_bond",
            b["front_mm"],
            b["length_mm"],
            b["inner_radius_mm"],
            b["outer_radius_mm"],
            "epoxy",
            {},
            "Explicit upper-shell/coupler annular bond; paper peel and wet/hot coupons remain open.",
        )
    )
    lands = cfg["bearing_lands"]
    for i, z in enumerate(lands["fronts_mm"]):
        params = {"machining_holes": passages(cfg, z, k["passage_length_mm"])} if i == 0 else {}
        for suffix, ri, ro, material in (
            ("g11", lands["inner_radius_mm"], lands["outer_radius_mm"], "G11"),
            ("bond", lands["bond_inner_radius_mm"], lands["inner_radius_mm"], "epoxy"),
        ):
            added.append(
                new_part(
                    coupler,
                    f"joint_land_{i}_{suffix}",
                    z,
                    lands["length_mm"],
                    ri,
                    ro,
                    material,
                    params.copy(),
                    "Overlap bearing land/bond; distributed paper contact and ovalisation require installed analysis.",
                )
            )
    pads = cfg["local_pads"]
    for side in ("inner", "outer"):
        cuts = [
            {
                "start_mm": radial(pads[f"{side}_profile_cut_center_radius_mm"], a, -1),
                "axis": [0, 0, 1],
                "diameter_mm": pads[f"{side}_profile_cut_diameter_mm"],
                "length_mm": d["pad_length"] + 2,
            }
            for a in pads["profile_cut_angles_deg"]
        ]
        for suffix, material in (("g11", "G11"), ("bond", "epoxy")):
            ri, ro = pads[f"{side}_{suffix}_radii_mm"]
            added.append(
                new_part(
                    coupler,
                    f"joint_{side}_{suffix}",
                    d["pad_front"],
                    d["pad_length"],
                    ri,
                    ro,
                    material,
                    {"machining_holes": [dict(c) for c in cuts]},
                    "Three curved local saddles; axial cylindrical profile cuts define cut-stock contours, not a 56 mm drilling process.",
                )
            )
    for p in [coupler, shell, *[p for p in added if "_inner_" in p.id or "_outer_" in p.id]]:
        assert p.cad
        p.cad.parameters.setdefault("machining_holes", []).extend(
            drill(40, a, d["fastener_station"] - p.position_m * 1000, f["hole_diameter_mm"], 15)
            for a in d["bolt_angles_deg"]
        )
    # Purchased envelopes: shaft/head, annular washer, circumscribed nut cylinder.
    # Threads, drive sockets and hex flats are not represented or qualified.
    for name, mass, pins, holes in (
        (
            "joint_screws",
            f["mass_kg"] * 0.65,
            [
                {
                    "start_mm": radial(r, a),
                    "axis": radial(-1, a),
                    "radius_mm": dia / 2,
                    "length_mm": length,
                }
                for a in d["bolt_angles_deg"]
                for r, dia, length in (
                    (f["head_inner_radius_mm"], f["diameter_mm"], 10),
                    (
                        f["head_inner_radius_mm"] + f["head_height_mm"],
                        f["head_diameter_mm"],
                        f["head_height_mm"],
                    ),
                )
            ],
            [],
        ),
        (
            "joint_washers",
            f["mass_kg"] * 0.1,
            [
                {
                    "start_mm": radial(f["head_inner_radius_mm"], a),
                    "axis": radial(-1, a),
                    "radius_mm": f["washer_diameter_mm"] / 2,
                    "length_mm": f["washer_thickness_mm"],
                }
                for a in d["bolt_angles_deg"]
            ],
            [drill(40, a, 0, f["hole_diameter_mm"], 15) for a in d["bolt_angles_deg"]],
        ),
        (
            "joint_nuts",
            f["mass_kg"] * 0.25,
            [
                {
                    "start_mm": radial(f["nut_outer_radius_mm"], a),
                    "axis": radial(-1, a),
                    "radius_mm": f["nut_circumscribed_diameter_mm"] / 2,
                    "length_mm": f["nut_height_mm"],
                }
                for a in d["bolt_angles_deg"]
            ],
            [drill(40, a, 0, f["hole_diameter_mm"], 16) for a in d["bolt_angles_deg"]],
        ),
    ):
        raw = parts["aft_interface_hardware"].model_dump(by_alias=True)
        raw.update(
            id=name,
            parent="interface_coupler",
            position_m=d["fastener_station"] / 1000,
            lateral_offset_m=[0, 0],
            geometry={"length_m": 0.003, "radius_m": 0.04},
            mass_kg=mass,
            density_kg_m3=None,
            cad_mass=None,
            cg_offset_m=0,
            cite=f["source"],
            learn=f["hypothesis"],
        )
        raw["cad"].update(
            generator="pins",
            parameters={"pins": pins, "machining_holes": holes},
            notes="Estimated purchased envelope; positive nut capture is absent.",
        )
        added.append(Part.model_validate(raw))
    raw = parts["aft_interface_hardware"].model_dump(by_alias=True)
    raw.update(
        id="joint_unresolved_capture_and_key_bond",
        parent="interface_coupler",
        position_m=d["fastener_station"] / 1000,
        cg_offset_m=0,
        cad_mass=None,
        mass_kg=f["nut_capture_mass_allowance_kg"] + k["additional_bond_allowance_kg"],
        learn="Explicit unmodeled capture/key adhesive mass allowance; no retention or antirotation credit.",
    )
    raw["cad"].update(
        role="distributed_budget",
        notes="Unresolved positive nut capture, never a structural solid.",
    )
    added.append(Part.model_validate(raw))
    candidate.parts = [p for p in candidate.parts if p.id != "aft_interface_hardware"] + added
    changed.update(p.id for p in added)
    for p in candidate.parts:
        if p.id in changed:
            p.cad_mass = None
    return Vehicle.model_validate(candidate.model_dump(by_alias=True)), changed


def reconcile(
    vehicle: Vehicle, changed: set[str]
) -> tuple[Vehicle, dict[str, Any], dict[str, Any]]:
    solids, rows = {}, {}
    for p in vehicle.parts:
        shape = local_shape(p)
        solids[p.id] = shape.translate(
            (p.lateral_offset_m[0] * 1000, -p.lateral_offset_m[1] * 1000, p.position_m * 1000)
        )
        if p.id not in changed:
            continue
        props = properties(p, shape)
        rows[p.id] = {
            "shape_sha256": shape_digest(p),
            "valid": shape.isValid(),
            "solids": len(shape.Solids()),
            "volume_mm3": shape.Volume(),
        }
        p.cad_mass = CADMass.model_validate(
            {
                key: props[key]
                for key in (
                    "shape_sha256",
                    "volume_m3",
                    "cg_local_body_m",
                    "inertia_per_kg_m2",
                    "basis",
                )
            }
        )
        p.cg_offset_m = max(0, -props["cg_local_body_m"][0])
        assert p.cad
        if p.cad.mass_basis == "volume_density":
            p.mass_kg = props["volume_m3"] * DENSITY_KG_M3[p.material]
        rows[p.id]["mass_kg"] = p.resolved_mass_kg
    return Vehicle.model_validate(vehicle.model_dump(by_alias=True)), solids, rows


def intervals(cfg: dict[str, Any]) -> dict[str, Any]:
    k, t, heat = cfg["keys"], cfg["tolerances_mm"], cfg["thermal_fit"]
    delta = heat["joint_max_c"] - heat["reference_c"]
    key_rows = []
    for width, diameter in zip(k["widths_mm"], k["slot_diameters_mm"], strict=True):
        corner = math.hypot(width / 2, k["depth_mm"] / 2)
        worst_corner = math.hypot(
            (width + t["key_width"]) / 2, (k["depth_mm"] + t["key_depth"]) / 2
        )
        minimum = (
            (diameter - t["slot_diameter"]) / 2
            - worst_corner
            - t["key_radius"]
            - t["passage_radius"]
            - corner * heat["asa_cte_per_k"] * delta
        )
        key_rows.append(
            {
                "width_mm": width,
                "passage_diameter_mm": diameter,
                "corner_clearance_min_nom_max_mm": [
                    minimum,
                    diameter / 2 - corner,
                    (diameter + t["slot_diameter"]) / 2
                    - math.hypot((width - t["key_width"]) / 2, (k["depth_mm"] - t["key_depth"]) / 2)
                    + t["key_radius"]
                    + t["passage_radius"]
                    + diameter / 2 * heat["paper_cte_per_k"] * delta,
                ],
                "screen_passed": minimum > 0,
            }
        )
    nominal = 32.5 - cfg["bearing_lands"]["outer_radius_mm"]
    variation = t["paper_radius"] + t["g11_radius"]
    minimum = (
        nominal
        - variation
        - cfg["bearing_lands"]["outer_radius_mm"] * max(heat["g11_cte_per_k"]) * delta
    )
    return {
        "key_corner_clearances": key_rows,
        "bearing_radial_clearance_min_nom_max_mm": [
            minimum,
            nominal,
            nominal + variation + 32.5 * heat["paper_cte_per_k"] * delta,
        ],
        "wide_key_rejected_by_small_passage_minimum_mm": (
            k["widths_mm"][0] - t["key_width"] - k["slot_diameters_mm"][1] - t["slot_diameter"]
        )
        / 2,
        "bolt_radial_clearance_min_nom_max_mm": [0.165, 0.2, 0.235],
        "key_radial_overlap_with_shell_wall_min_nom_max_mm": [0.3, 0.5, 0.7],
        "key_axial_engagement_min_nom_max_mm": [24.8, 25, 25.2],
        "scope": heat["note"],
        "as_built_fit_qualified": False,
    }


def checks(vehicle: Vehicle, cfg: dict[str, Any], engineering: dict[str, Any]) -> dict[str, Any]:
    d, f, limits = cfg["datums_mm"], cfg["fasteners"], cfg["strength_screens_mpa"]
    loads, factor = engineering["loads"], engineering["loads"]["design_factor"]
    mass = mass_properties(vehicle)
    assert vehicle.design
    upper_mass = sum(
        p.resolved_mass_kg
        for p in vehicle.parts
        if p.position_m < d["aft_start"] / 1000
        or p.id.startswith("joint_land")
        or p.id in ("joint_inner_g11", "joint_inner_bond", "joint_nuts")
    )
    cases = [
        {
            "id": "front_axial",
            "design_force_n": cfg["load_cases"]["axial_design_n"],
            "service_force_n": cfg["load_cases"]["axial_service_n"],
            "conditional": False,
        }
    ]
    for speed in loads["recovery_velocity_mps"]:
        for travel in loads["recovery_stopping_distance_m"]:
            for label, kg in (("full", mass.mass_kg), ("upper_assigned", upper_mass)):
                service = (kg + vehicle.design.mass_allowance_kg) * (
                    speed**2 / (2 * travel) + 9.80665
                )
                cases.append(
                    {
                        "id": f"recovery_{label}_{speed}_{travel}",
                        "service_force_n": service,
                        "design_force_n": factor * service,
                        "conditional": label != "full",
                    }
                )
    # Straight single-lap pin: conservatively resolve P at bearing centroids and
    # use M=P*centroid_distance/2; no friction, preload or unthreaded-shank credit.
    inner_thickness = (
        cfg["local_pads"]["inner_g11_radii_mm"][1] - cfg["local_pads"]["inner_g11_radii_mm"][0]
    )
    outer_thickness = (
        cfg["local_pads"]["outer_g11_radii_mm"][1] - cfg["local_pads"]["outer_g11_radii_mm"][0]
    )
    spacing = (
        sum(cfg["local_pads"]["outer_g11_radii_mm"]) / 2
        - sum(cfg["local_pads"]["inner_g11_radii_mm"]) / 2
    )
    for case in cases:
        p = case["design_force_n"] / f["count"]
        shear = p / (math.pi * f["root_diameter_mm"] ** 2 / 4)
        bending = 32 * p * spacing / 2 / (math.pi * f["root_diameter_mm"] ** 3)
        edge = min(
            d["fastener_station"] - d["pad_front"],
            d["pad_front"] + d["pad_length"] - d["fastener_station"],
        )
        ligament = edge - f["hole_diameter_mm"] / 2
        stresses = {
            "bolt_von_mises": math.sqrt(bending**2 + 3 * shear**2),
            "bolt_shear": shear,
            "inner_g11_bearing": p / (f["diameter_mm"] * inner_thickness),
            "outer_g11_bearing": p / (f["diameter_mm"] * outer_thickness),
            "inner_g11_tearout": p / (2 * ligament * inner_thickness),
            "outer_g11_tearout": p / (2 * ligament * outer_thickness),
            "outer_pad_average_bond": p / (10 * d["pad_length"]),
            "inner_pad_average_bond": p / (10 * d["pad_length"]),
            "nut_thread_shear": p / (math.pi * f["root_diameter_mm"] * f["nut_height_mm"] / 2),
        }
        bounds = {
            "bolt_von_mises": f["strength_bound_mpa"],
            "bolt_shear": f["shear_bound_mpa"],
            "inner_g11_bearing": limits["g11_bearing"],
            "outer_g11_bearing": limits["g11_bearing"],
            "inner_g11_tearout": limits["g11_tearout"],
            "outer_g11_tearout": limits["g11_tearout"],
            "outer_pad_average_bond": limits["paper_bond"],
            "inner_pad_average_bond": limits["paper_bond"],
            "nut_thread_shear": f["nut_thread_shear_bound_mpa"],
        }
        case["fastener_design_force_each_n"] = p
        case["stresses_mpa"] = stresses
        case["strength_bound_mpa"] = bounds
        case["margins"] = {key: bounds[key] / value - 1 for key, value in stresses.items()}
        case["hand_screen_passed"] = min(case["margins"].values()) >= 0
    fin_cases = []
    for part in vehicle.parts:
        if part.type != "fin_set":
            continue
        g = part.geometry
        area = g["span_m"] * (g["root_chord_m"] + g["tip_chord_m"]) / 2
        ar = 2 * g["span_m"] ** 2 / area
        slope = 2 * math.pi * ar / (2 + math.sqrt(4 + ar**2))
        force = (
            loads["fin_dynamic_pressure_pa"] * area * slope * math.radians(loads["fin_alpha_deg"])
        )
        # Explicit conservative station bound: all panel forces act at aftmost
        # axial extent, and all three align laterally; no vector cancellation.
        arm = part.position_m + g["length_m"] - d["aft_start"] / 1000
        service_force = g["count"] * force
        design_moment = factor * service_force * arm
        separation = (
            cfg["bearing_lands"]["fronts_mm"][1] - cfg["bearing_lands"]["fronts_mm"][0]
        ) / 1000
        reaction = design_moment / separation + factor * service_force / 2
        # Full projected area is an optimistic contact lower stress bound;
        # quarter projected contact is a declared sensitivity, not a closure.
        projected_area = (
            2 * cfg["bearing_lands"]["outer_radius_mm"] * cfg["bearing_lands"]["length_mm"]
        )
        fin_cases.append(
            {
                "force_per_fin_n": force,
                "joint_design_moment_nm": design_moment,
                "bearing_land_peak_reaction_n": reaction,
                "paper_bearing_full_projected_mpa": reaction / projected_area,
                "paper_bearing_quarter_projected_mpa": 4 * reaction / projected_area,
                "paper_strength_bound_mpa": limits["paper_bearing"],
                "bolt_only_peak_design_force_n": cases[0]["design_force_n"] / 3
                + 2 * design_moment * 1000 / (3 * 32),
                "status": "open: contact arc, ring flexure and paper ovalisation not established",
            }
        )
    upper_bond_area = (
        2 * math.pi * cfg["upper_bond"]["inner_radius_mm"] * cfg["upper_bond"]["length_mm"]
    )
    for case in cases:
        case["upper_bond_average_shear_mpa"] = case["design_force_n"] / upper_bond_area
        case["upper_bond_average_margin"] = (
            limits["paper_bond"] / case["upper_bond_average_shear_mpa"] - 1
        )
    return {
        "cases": cases,
        "fin_moment_cases": fin_cases,
        "guide_design_force_n": factor * loads["guide_side_force_n"],
        "pad_axial_edge_distance_mm": 16,
        "pad_edge_distance_over_hole_diameter": 16 / f["hole_diameter_mm"],
        "nut_thread_engagement_mm": f["nut_height_mm"],
        "nut_thread_turns_at_0p5_pitch": f["nut_height_mm"] / 0.5,
        "minimum_complete_coupler_bore_radius_mm": f["nut_outer_radius_mm"] - f["nut_height_mm"],
        "upper_assigned_mass_kg": upper_mass,
        "limitations": [
            "No nut captivity, locking or torque qualified; no pretension/friction credit.",
            "Average bond shear omits eccentric peel, shear lag, paper delamination, humidity and cure defects.",
            "Fin bearing couple requires contact arc and shell/ring deformation analysis; no full-area contact pass.",
            "Index keys provide orientation only; no torque or recovery load capacity is credited.",
            "Upper-only recovery assignment is conditional; no separate harness branch is implemented.",
        ],
        "expanded_wo03_passed": False,
        "flight_ready": False,
    }


def fit_checks(vehicle: Vehicle, solids: dict[str, Any], cfg: dict[str, Any]) -> dict[str, Any]:
    keys = solids["joint_stop"]
    shell = solids["aft_shell"]
    insertion = []
    for distance in (0, 1, 5, 10, 25, 50, 55):
        # Aft module approaches from aft: shell translates positive Z while
        # withdrawn. Stop/ring stays on common upper.
        shape = shell.translate((0, 0, distance))
        insertion.append(
            {
                "withdrawal_mm": distance,
                "key_shell_intersection_mm3": keys.intersect(shape).Volume(),
            }
        )
    wrong = [
        {
            "rotation_deg": angle,
            "key_shell_intersection_mm3": keys.intersect(
                shell.rotate((0, 0, 0), (0, 0, 1), angle)
            ).Volume(),
        }
        for angle in (120, 240)
    ]
    selected = [
        "interface_coupler",
        "joint_stop",
        "aft_shell",
        "joint_upper_bond",
        "joint_land_0_g11",
        "joint_land_1_g11",
        "joint_inner_g11",
        "joint_outer_g11",
    ]
    collisions = []
    for i, name in enumerate(selected):
        for other in selected[i + 1 :]:
            volume = solids[name].intersect(solids[other]).Volume()
            if volume > 0.001:
                collisions.append({"parts": [name, other], "volume_mm3": volume})
    # Check candidate parts against the remaining real vehicle; deliberately
    # exclude purchased bolt/nut envelopes and their intended threaded mating.
    other_collisions = []
    changed_names = [
        name
        for name in solids
        if name.startswith("joint_")
        and name
        not in (
            "joint_screws",
            "joint_nuts",
            "joint_washers",
            "joint_unresolved_capture_and_key_bond",
        )
    ]
    for name in changed_names:
        for part in vehicle.parts:
            if (
                part.id in selected
                or part.id.startswith("joint_")
                or not part.cad
                or part.cad.role == "distributed_budget"
            ):
                continue
            if (
                solids[name].BoundingBox().zmax < solids[part.id].BoundingBox().zmin
                or solids[name].BoundingBox().zmin > solids[part.id].BoundingBox().zmax
            ):
                continue
            volume = solids[name].intersect(solids[part.id]).Volume()
            if volume > 0.001:
                other_collisions.append({"parts": [name, part.id], "volume_mm3": volume})
    return {
        "nominal_joint_intersections": collisions,
        "adjacent_part_intersections": other_collisions,
        "sampled_shell_withdrawal": insertion,
        "wrong_angular_index_cases": wrong,
        "nominal_passed": not collisions
        and not other_collisions
        and all(row["key_shell_intersection_mm3"] < 0.001 for row in insertion)
        and all(row["key_shell_intersection_mm3"] > 0.001 for row in wrong),
        "service_access": "External radial drivers have open air to all three heads; screws remove radially. Internal captive nut/cap is unimplemented; continuous complete-module withdrawal, wiring and packing clearance are not qualified.",
        "nut_capture_positive": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-modular-joint.yaml")
    )
    parser.add_argument("--base", choices=("active", "correction-package"), default="active")
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    engineering = yaml.safe_load(Path(cfg["engineering_config"]).read_text())
    package = yaml.safe_load(Path(cfg["correction_package_config"]).read_text())
    fit_cfg = yaml.safe_load(Path(package["fit_study"]).read_text())
    fit = next(row for row in fit_cfg["packages"] if row["id"] == "fit-package-a")
    inputs = {
        args.config,
        Path(__file__),
        Path(cfg["engineering_config"]),
        Path(cfg["correction_package_config"]),
        Path(package["fit_study"]),
    }
    inputs.update(Path("src/cad").glob("*.py"))
    inputs.update(Path("src/vehicle").glob("*.py"))
    inputs.update(
        Path("scripts") / p
        for p in (
            "wo03_correction_package.py",
            "wo03_fit_structure.py",
            "wo03_fit_correction_study.py",
        )
    )
    for path in cfg["configurations"].values():
        inputs.update(vehicle_input_paths(path))

    def hashes() -> dict[str, str]:
        return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(inputs)}

    before = hashes()
    run = datetime.now(UTC).strftime("wo03-modular-joint-%Y%m%dT%H%M%S%fZ")
    out = Path("build") / run
    out.mkdir(parents=True)
    rows = []
    for label, path in cfg["configurations"].items():
        base = load_vehicle(path)
        if args.base == "correction-package":
            base = package_copy(base, package, fit, 0.077 if label == "G54" else 0.07)
            base, _, _ = reconcile(base, {p.id for p in base.parts})
        vehicle, changed = make_candidate(base, cfg)
        vehicle, solids, part_rows = reconcile(vehicle, changed)
        folder = out / label
        folder.mkdir()
        resolved = folder / "resolved-candidate.yaml"
        resolved.write_text(yaml.safe_dump(vehicle.model_dump(by_alias=True), sort_keys=False))
        baseline, candidate = mass_properties(base), mass_properties(vehicle)
        result = {
            "configuration": label,
            "base": args.base,
            "candidate_path": str(resolved),
            "candidate_sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
            "baseline_mass_kg": baseline.mass_kg,
            "candidate_mass_kg": candidate.mass_kg,
            "delta_mass_kg": candidate.mass_kg - baseline.mass_kg,
            "candidate_cg_m": candidate.cg_m,
            "candidate_inertia_kg_m2": candidate.inertia_kg_m2.tolist(),
            "parts": part_rows,
            "tolerances": intervals(cfg),
            "hand_checks": checks(vehicle, cfg, engineering),
            "cad_fit": fit_checks(vehicle, solids, cfg),
            "static": evaluate_preliminary(vehicle, compare=True),
            "active_adoption": False,
        }
        rows.append(result)
        print(
            label,
            f"delta={result['delta_mass_kg'] * 1000:.3f}g",
            f"fit={result['cad_fit']['nominal_passed']}",
            flush=True,
        )
    payload = {
        "run_id": run,
        "config_version": cfg["version"],
        "base": args.base,
        "source_hashes_before": before,
        "source_hashes_after": hashes(),
        "inputs_unchanged": before == hashes(),
        "results": rows,
        "nut_capture_status": cfg["fasteners"]["nut_capture_status"],
        "nut_capture_required_parameters": cfg["fasteners"]["nut_capture_required_parameters"],
        "active_adoption": False,
        "expanded_wo03_passed": False,
        "flight_ready": False,
    }
    (out / "report.json").write_text(json.dumps(payload, indent=2) + "\n")
    alias = Path("build/wo03-modular-joint")
    alias.mkdir(exist_ok=True)
    (alias / f"latest-{args.base}.json").write_text(
        json.dumps({"report_path": str(out / "report.json")}, indent=2) + "\n"
    )
    print(out / "report.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
