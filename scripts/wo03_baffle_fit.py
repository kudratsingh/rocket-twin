"""One notched shield-end family: real solids, mass, uncertainty and service paths.

The owner-selected source mount bore is unchanged. Custom cuts and sector
rotations are owned by this runner and exported as actual placed STEP/STL solids;
the generic CAD generator alone does not reconstruct these postprocessed parts.
No annular substitute, ray run, thermal transient or acceptance is produced here.
"""

from __future__ import annotations

import os

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_name] = "1"
os.environ.setdefault("XDG_CACHE_HOME", os.path.abspath(".cache"))
os.environ.setdefault("MPLCONFIGDIR", os.path.abspath(".cache/matplotlib"))

import argparse
import hashlib
import json
import math
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import cadquery as cq
import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_multilayer_shield import subtract_intervals
from src.cad.parts import box, local_shape, properties
from src.vehicle.aero import center_of_pressure
from src.vehicle.mass import mass_properties
from src.vehicle.reference import compare_rocketpy
from src.vehicle.schema import CADMass, Part, Vehicle

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-baffle-fit.yaml"


def placed(part: Part, shape: Any) -> Any:
    return shape.translate(
        (1000 * part.lateral_offset_m[0], -1000 * part.lateral_offset_m[1], 1000 * part.position_m)
    )


def bounds_overlap(a: Any, b: Any) -> bool:
    x, y = a.BoundingBox(), b.BoundingBox()
    return not (
        x.xmax < y.xmin
        or y.xmax < x.xmin
        or x.ymax < y.ymin
        or y.ymax < x.ymin
        or x.zmax < y.zmin
        or y.zmax < x.zmin
    )


def common_volume(a: Any, b: Any) -> float:
    return max(0.0, float(a.intersect(b).Volume())) if bounds_overlap(a, b) else 0.0


def reconcile(part: Part, density: float, shape: Any | None = None) -> Any:
    part.cad_mass = None
    shape = local_shape(part) if shape is None else shape
    if not shape.isValid():
        raise ValueError(f"Invalid part solid: {part.id}")
    prop = properties(part, shape)
    part.mass_kg = density * prop["volume_m3"]
    part.density_kg_m3 = None
    part.cad_mass = CADMass.model_validate(prop)
    return shape


def extend_windows(vehicle: Vehicle, cfg: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    parts = {p.id: p for p in vehicle.parts}
    mount, original = parts["motor_mount"], parts["motor_radiant_shield"]
    assert mount.cad
    params = mount.cad.parameters
    widths = params.get(
        "ring_thicknesses_mm", [params["ring_thickness_mm"]] * len(params["ring_stations_mm"])
    )
    clearance = cfg["segment_ring_clearance_m"]
    cuts = [
        (
            mount.position_m + station * 0.001 - clearance,
            mount.position_m + (station + width) * 0.001 + clearance,
        )
        for station, width in zip(params["ring_stations_mm"], widths, strict=True)
    ]
    changed = []
    intervals = {}
    for layer in range(1, 8):
        members = sorted(
            [p for p in vehicle.parts if p.id.startswith(f"additional_shield_{layer}_")],
            key=lambda p: p.position_m,
        )
        radius = members[0].geometry["radius_m"]
        start = original.position_m + 0.002
        end = original.position_m + original.geometry["length_m"]
        for block in params["retainer_blocks"]:
            if radius >= (block["position_mm"][0] - block["size_mm"][0] / 2) * 0.001 - 0.0003:
                end = min(end, mount.position_m + block["position_mm"][2] * 0.001 - 0.002)
        spans = subtract_intervals(start, end, cuts)
        if len(spans) != len(members):
            raise ValueError("Window change alters source segment identities")
        for part, (a, b) in zip(members, spans, strict=True):
            if b - a <= 2 * cfg["spacer_axial_length_m_unchanged"]:
                raise ValueError("Window creates unsupported short segment")
            part.position_m = a
            part.geometry["length_m"] = b - a
            part.cg_offset_m = (b - a) / 2
            reconcile(part, 2700.0)
            changed.append(part.id)
            intervals[part.id] = [a, b]
            for side, z in (("front", a), ("aft", b - cfg["spacer_axial_length_m_unchanged"])):
                spacer = parts[f"shield_spacer_{part.id}_{side}"]
                spacer.position_m = z
                changed.append(spacer.id)
    return {"ring_exclusion_intervals_m": cuts, "new_shield_intervals_m": intervals}, changed


def baffle_shape(part: Part, mount: Part, cfg: dict[str, Any], *, edge_error_m: float = 0.0) -> Any:
    """Actual rail/block notches and three through radial seams, in local mm."""
    assert mount.cad
    if edge_error_m:
        shape = (
            cq.Workplane("XY")
            .circle((part.geometry["radius_m"] + edge_error_m) * 1000)
            .circle((part.geometry["inner_radius_m"] - edge_error_m) * 1000)
            .extrude(part.geometry["length_m"] * 1000)
            .val()
        )
    else:
        shape = local_shape(part)
    margin = (cfg["source_hardware_xy_notch_inflation_m"] - edge_error_m) * 1000
    options = mount.cad.parameters
    for angle in (0, 120, 240):
        cutter = (
            box(options["rail_depth_mm"] + 2 * margin, options["rail_width_mm"] + 2 * margin, 3)
            .translate((options["rail_radius_mm"], 0, -1))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        shape = shape.cut(cutter)
    for block in options["retainer_blocks"]:
        # These openings also permit a common manufacturing pattern and expose
        # the real retention-sector leakage to the CAD radiation tracer.
        cutter = (
            box(block["size_mm"][0] + 2 * margin, block["size_mm"][1] + 2 * margin, 3)
            .translate((block["position_mm"][0], block["position_mm"][1], -1))
            .rotate((0, 0, 0), (0, 0, 1), block["angle_deg"])
        )
        shape = shape.cut(cutter)
    for angle in cfg["seam_angles_deg"]:
        cutter = (
            box(60, (cfg["radial_seam_width_m"] - 2 * edge_error_m) * 1000, 3)
            .translate((30, 0, -1))
            .rotate((0, 0, 0), (0, 0, 1), angle)
        )
        shape = shape.cut(cutter)
    if len(shape.Solids()) != 3:
        raise ValueError("The baffle must have exactly three real separate panels")
    return shape


def create_parts(
    vehicle: Vehicle, cfg: dict[str, Any]
) -> tuple[list[Part], dict[str, Any], list[dict[str, Any]]]:
    g = cfg["geometry"]
    density = cfg["mass"]["density_kg_m3"]
    parts = {p.id: p for p in vehicle.parts}
    mount = parts["motor_mount"]
    template = parts["motor_radiant_shield"]
    liner = parts["motor_liner"]
    assert mount.cad
    if abs(mount.geometry["inner_radius_m"] - g["source_mount_bore_radius_m_unchanged"]) > 1e-12:
        raise ValueError("Source bore differs from preserved15.8mm")
    p = mount.cad.parameters
    widths = p.get("ring_thicknesses_mm", [p["ring_thickness_mm"]] * len(p["ring_stations_mm"]))
    new = []
    shapes = {}
    contacts = []
    stack = g["mica_thickness_m"] + 2 * g["adhesive_thickness_m_each"]
    if abs(stack - g["stand_off_m"]) > 1e-12:
        raise ValueError("Contact stack does not fill stand-off")

    def append(
        name: str, z: float, length: float, ri: float, ro: float, material: str, sector: bool
    ) -> Part:
        raw = template.model_dump(by_alias=True)
        raw.update(
            id=name,
            parent="motor_mount",
            position_m=z,
            cad_mass=None,
            material=material,
            cg_offset_m=length / 2,
        )
        raw["geometry"] = {
            "length_m": length,
            "inner_radius_m": ri,
            "radius_m": ro,
            "wall_m": ro - ri,
        }
        raw["engineering"]["material_profile"] = material
        raw["engineering"][
            "function"
        ] = "Notched finite shield-end panel or bonded mica support; heat/strength acceptance remains open."
        raw["cad"]["generator"] = "sector_pads" if sector else "liner"
        raw["cad"]["parameters"] = (
            {
                "sector_angle_deg": g["pad_sector_angle_deg"],
                "study_rotation_deg": 30.0,
                "circular_boundaries": True,
            }
            if sector
            else {"study_notches_and_seams": g, "study_postprocessor": "scripts/wo03_baffle_fit.py"}
        )
        raw["cad"][
            "notes"
        ] = "Actual shape requires the recorded study postprocessor; use exported STEP/STL for radiation, never an annular replacement."
        part = Part.model_validate(raw)
        shape = (
            local_shape(part).rotate((0, 0, 0), (0, 0, 1), 30)
            if sector
            else baffle_shape(part, mount, g)
        )
        reconcile(part, density[material], shape)
        new.append(part)
        shapes[name] = shape
        return part

    for index, (station, width) in enumerate(zip(p["ring_stations_mm"], widths, strict=True)):
        front = mount.position_m + station * 0.001
        aft = front + width * 0.001
        if front < liner.position_m or aft > liner.position_m + liner.geometry["length_m"]:
            continue
        for side, z, sign in (("front", front, -1), ("aft", aft, 1)):
            name = f"fitting_baffle_{index}_{side}"
            gap = g["stand_off_m"]
            bond = g["adhesive_thickness_m_each"]
            mica = g["mica_thickness_m"]
            foil_z = z - gap - g["foil_wall_m"] if sign < 0 else z + gap
            foil = append(
                name,
                foil_z,
                g["foil_wall_m"],
                g["baffle_clearance_opening_radius_m"],
                g["baffle_outer_radius_m"],
                "aluminum",
                False,
            )
            ring_z = z - bond if sign < 0 else z
            mica_z = z - bond - mica if sign < 0 else z + bond
            foil_bond_z = z - gap if sign < 0 else z + gap - bond
            rb = append(
                name + "_ring_bond",
                ring_z,
                bond,
                g["pad_inner_radius_m"],
                g["pad_outer_radius_m"],
                "epoxy",
                True,
            )
            mp = append(
                name + "_mica_pads",
                mica_z,
                mica,
                g["pad_inner_radius_m"],
                g["pad_outer_radius_m"],
                "mica",
                True,
            )
            fb = append(
                name + "_foil_bond",
                foil_bond_z,
                bond,
                g["pad_inner_radius_m"],
                g["pad_outer_radius_m"],
                "epoxy",
                True,
            )
            pad_area = mp.cad_mass.volume_m3 / mica
            foil_projected_area = foil.cad_mass.volume_m3 / g["foil_wall_m"]
            contacts.append(
                {
                    "baffle_id": name,
                    "ring_index": index,
                    "side": side,
                    "ring_face_m": z,
                    "path": ["motor_mount", rb.id, mp.id, fb.id, foil.id],
                    "pad_angles_deg": g["support_angles_deg"],
                    "bulk_support_conductance_w_k_estimate": 1
                    / ((mica / 0.45 + 2 * bond / 0.15) / pad_area),
                    "actual_notched_foil_projected_area_m2": foil_projected_area,
                    "actual_sector_support_area_m2": pad_area,
                    "parallel_axial_air_gap_area_m2_estimate": foil_projected_area - pad_area,
                    "parallel_axial_air_gap_conductance_w_k_estimate": g[
                        "parallel_gap_air_conductivity_w_m_k_estimate"
                    ]
                    * (foil_projected_area - pad_area)
                    / gap,
                    "parallel_air_path_must_be_added_at_same_solved_surfaces": True,
                    "temperatures_unavailable_for_new_parts": True,
                }
            )
    if len(contacts) != 8:
        raise ValueError("Exactly eight shield-end baffles required")
    return new, shapes, contacts


def clearance_budget(
    vehicle: Vehicle, cfg: dict[str, Any], windows: dict[str, Any]
) -> dict[str, Any]:
    g, u = cfg["geometry"], cfg["uncertainty_assumptions"]
    spans = windows["new_shield_intervals_m"].values()
    length = max(b - a for a, b in spans)
    foil_dT = u["foil_temperature_probe_c"] - u["ambient_c"]
    wood_dT = u["hardware_temperature_probe_c"] - u["ambient_c"]
    foil_radial = g["baffle_outer_radius_m"] * u["foil_cte_per_k_estimate"] * foil_dT
    foil_axial = length * u["foil_cte_per_k_estimate"] * foil_dT
    mount = next(p for p in vehicle.parts if p.id == "motor_mount")
    p = mount.cad.parameters
    spacing = (
        max(
            b - a
            for a, b in zip(p["ring_stations_mm"][:-1], p["ring_stations_mm"][1:], strict=True)
        )
        * 0.001
    )
    wood_axial = spacing * u["source_plywood_cte_per_k"] * wood_dT
    wood_radial = mount.geometry["radius_m"] * u["source_plywood_cte_per_k"] * wood_dT
    axial_nom = g["segment_ring_clearance_m"] - g["stand_off_m"] - g["foil_wall_m"]
    axial_min = (
        axial_nom
        - u["source_foil_edge_error_m"]
        - u["source_hardware_linear_error_m"]
        - u["stand_off_stack_error_m"]
        - foil_axial
        - wood_axial
    )
    notch_min = (
        g["source_hardware_xy_notch_inflation_m"]
        - u["source_foil_edge_error_m"]
        - u["source_hardware_linear_error_m"]
        - u["assembly_eccentricity_m"]
        - foil_radial
        - wood_radial
    )
    original = next(p for p in vehicle.parts if p.id == "motor_radiant_shield")
    hot_original = original.geometry["radius_m"] * u["foil_cte_per_k_estimate"] * foil_dT
    inner_min = (
        g["baffle_clearance_opening_radius_m"]
        - u["source_foil_edge_error_m"]
        - original.geometry["radius_m"]
        - u["source_foil_edge_error_m"]
        - hot_original
        - u["assembly_eccentricity_m"]
    )
    seam_min = g["radial_seam_width_m"] - 2 * u["source_foil_edge_error_m"] - 2 * foil_radial
    values = {
        "axial_foil_end_to_baffle": axial_min,
        "inflated_rail_block_notches": notch_min,
        "baffle_opening_to_original_foil": inner_min,
        "panel_seam": seam_min,
    }
    return {
        "maximum_changed_foil_segment_length_m": length,
        "full_segment_foil_axial_growth_m": foil_axial,
        "foil_radial_growth_m": foil_radial,
        "source_frame_relative_station_growth_m": wood_axial,
        "source_frame_radial_growth_m": wood_radial,
        "nominal_axial_foil_end_to_baffle_m": axial_nom,
        "minimum_clearance_m_by_case": values,
        "required_clearance_m": u["required_clearance_m"],
        "all_declared_scalar_bounds_passed": all(
            v >= u["required_clearance_m"] for v in values.values()
        ),
        "new_pad_profile_tolerance_is_unmeasured_proposal_m": u["support_cut_profile_error_m"],
        "sampled_or_scalar_bounds_are_not_continuous_CAD_thermal_deformation_validation": True,
        "hardware_65C_probe_does_not_raise_45C_screen": True,
    }


def staged_panel_paths(
    vehicle: Vehicle,
    new: list[Part],
    new_shapes: dict[str, Any],
    solids: dict[str, Any],
    contacts: list[dict[str, Any]],
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """One owner-directed baffle-first rigid route, retaining integral hardware.

    Failed straight radial routes remain separate evidence. This sequence never
    removes the mount's rails, rings or integral retention blocks. The body has
    not yet been permanently bonded; wrap/motor removal is a stated condition.
    """
    spec = cfg["service_path"]["staged_baffle_first_sequence"]
    parts = {p.id: p for p in vehicle.parts}
    mount = parts["motor_mount"]
    assert mount.cad
    params = mount.cad.parameters
    widths = params.get(
        "ring_thicknesses_mm", [params["ring_thickness_mm"]] * len(params["ring_stations_mm"])
    )
    rings = [
        (mount.position_m + s * 0.001, mount.position_m + (s + w) * 0.001)
        for s, w in zip(params["ring_stations_mm"], widths, strict=True)
    ]
    retained_ids = {"motor_mount", "retention", "thrust_pads"}
    obstacles = {name: solids[name] for name in retained_ids if name in solids}
    # All support compounds are explicit actual solids, including supports for
    # the panel being installed and for previously/future installed panels.
    obstacles.update({p.id: solids[p.id] for p in new if p.material != "aluminum"})
    tolerance = cfg["numerics"]["collision_volume_tolerance_mm3"]
    row_by_id = {row["baffle_id"]: row for row in contacts}
    rows = []
    for part in new:
        if part.material != "aluminum":
            continue
        contact = row_by_id[part.id]
        ring = contact["ring_index"]
        side = contact["side"]
        rear = ring == len(rings) - 1 and side == "aft"
        if not rear:
            if side == "front":
                lo, hi = rings[ring - 1][1], rings[ring][0]
                if ring == 1:
                    plate = parts["retention"]
                    assert plate.cad
                    # The web blocks the full bay; integral fingers remain in
                    # the exact collision geometry even beyond this web plane.
                    lo = max(
                        lo, plate.position_m + float(plate.cad.parameters["thickness_mm"]) * 0.001
                    )
            else:
                lo, hi = rings[ring][1], rings[ring + 1][0]
            middle = (lo + hi) / 2
        else:
            lo, hi, middle = rings[ring][1], mount.position_m + mount.geometry["length_m"], 0.0
        target = part.position_m + part.geometry["length_m"] / 2
        for panel_number, panel in enumerate(new_shapes[part.id].Solids()):
            centre = panel.Center()
            angle = math.degrees(math.atan2(centre.y, centre.x)) % 360
            support = min(
                cfg["geometry"]["support_angles_deg"],
                key=lambda a: abs(
                    math.atan2(math.sin(math.radians(angle - a)), math.cos(math.radians(angle - a)))
                ),
            )
            yaw = spec["panel_yaw_to_open_rail_window_deg"]
            entry = math.radians(support + yaw)
            base = panel.translate((0, 0, -part.geometry["length_m"] * 500))

            def pose(
                tilt: float,
                yaw_angle: float,
                radial: float,
                z: float,
                base: Any = base,
                entry: float = entry,
            ) -> Any:
                shape = base.rotate((0, 0, 0), (0, 0, 1), yaw_angle)
                if tilt:
                    shape = shape.rotate((0, 0, 0), (math.cos(entry), math.sin(entry), 0), tilt)
                return shape.translate(
                    (radial * 1000 * math.cos(entry), radial * 1000 * math.sin(entry), z * 1000)
                )

            steps = []
            if rear:
                steps = [
                    ("aft_axial_approach", pose(0, 0, 0, z))
                    for z in [*spec["aft_approach_stations_m"], target]
                ]
                tilted_span = 0.0
            else:
                tilted = pose(spec["panel_tilt_deg"], yaw, 0, middle)
                tilted_span = tilted.BoundingBox().zlen * 0.001
                steps += [
                    ("tilted_midbay_radial_entry", pose(spec["panel_tilt_deg"], yaw, r, middle))
                    for r in spec["midbay_radial_shifts_m"]
                ]
                steps += [
                    (
                        "flatten_in_central_workspace",
                        pose(t, yaw, spec["central_workspace_radial_shift_m"], middle),
                    )
                    for t in spec["flatten_angles_deg"]
                ]
                steps += [
                    ("recenter_midbay", pose(0, yaw, r, middle))
                    for r in spec["recenter_radial_shifts_m"]
                ]
                steps += [
                    ("restore_final_yaw_midbay", pose(0, y, 0, middle))
                    for y in spec["restore_yaw_angles_deg"]
                ]
                steps += [
                    ("translate_axially_to_ring", pose(0, 0, 0, middle + f * (target - middle)))
                    for f in spec["final_axial_fractions"]
                ]
            failure = None
            for index, (stage, trial) in enumerate(steps):
                hits = [
                    name
                    for name, shape in obstacles.items()
                    if common_volume(trial, shape) > tolerance
                ]
                if hits:
                    failure = {"stage": stage, "sample_index": index, "colliding_part_ids": hits}
                    break
            rows.append(
                {
                    "baffle_id": part.id,
                    "panel_number": panel_number,
                    "support_angle_deg": support,
                    "entry_yaw_deg": yaw,
                    "entry_window_angle_deg": support + yaw,
                    "open_bay_interval_m": [lo, hi],
                    "bay_length_m": hi - lo,
                    "midbay_m": None if rear else middle,
                    "tilted_axial_span_m": tilted_span,
                    "declared_pose_count": len(steps),
                    "evaluated_pose_count": (
                        len(steps) if failure is None else failure["sample_index"] + 1
                    ),
                    "route": "aft_axial" if rear else "tilt45_midbay_radial_flatten_recenter_axial",
                    "sampled_path_passed": failure is None,
                    "first_collision": failure,
                    "already_installed_obstacle_count": len(obstacles),
                }
            )
            if failure is None:
                obstacles[f"installed_panel:{part.id}:{panel_number}"] = placed(part, panel)
    return {
        "sequence": spec,
        "retained_integral_part_ids": sorted(retained_ids),
        "body_bonding_not_yet_performed": True,
        "all_support_compounds_present": True,
        "panels": rows,
        "all_sampled_staged_paths_passed": all(row["sampled_path_passed"] for row in rows),
        "continuous_or_tolerance_deformed_sweep_validated": False,
        "failed_original_straight_paths_remain_valid_findings": True,
    }


def mass_stability_delta(source: Vehicle, candidate: Vehicle) -> dict[str, Any]:
    cp = center_of_pressure(candidate)
    diameter = candidate.airframe["body_diameter_m"]
    allowance = candidate.design.mass_allowance_kg if candidate.design else 0.0
    rows = []
    for name, fraction in (("liftoff", 0.0), ("burnout", 1.0)):
        old, new = mass_properties(source, fraction), mass_properties(candidate, fraction)
        shifted = (new.mass_kg * new.cg_m + allowance * candidate.airframe["length_m"]) / (
            new.mass_kg + allowance
        )
        rows.append(
            {
                "state": name,
                "source_mass_kg": old.mass_kg,
                "candidate_mass_kg": new.mass_kg,
                "delta_mass_kg": new.mass_kg - old.mass_kg,
                "source_cg_m": old.cg_m,
                "candidate_cg_m": new.cg_m,
                "delta_cg_m": new.cg_m - old.cg_m,
                "source_cg_lateral_m": list(old.cg_lateral_m),
                "candidate_cg_lateral_m": list(new.cg_lateral_m),
                "source_full_inertia_kg_m2": old.inertia_kg_m2.tolist(),
                "candidate_full_inertia_kg_m2": new.inertia_kg_m2.tolist(),
                "delta_full_inertia_kg_m2": (new.inertia_kg_m2 - old.inertia_kg_m2).tolist(),
                "candidate_static_margin_cal": (cp - new.cg_m) / diameter,
                "candidate_full_aft_allowance_static_margin_cal": (cp - shifted) / diameter,
            }
        )
    margins = []
    for fraction in np.linspace(0, 1, 101):
        prop = mass_properties(candidate, float(fraction))
        shifted = (prop.mass_kg * prop.cg_m + allowance * candidate.airframe["length_m"]) / (
            prop.mass_kg + allowance
        )
        margins.append((cp - shifted) / diameter)
    return {
        "configuration_id": candidate.id,
        "scope": "fixed G54 candidate only; no G12 mass credit or shield compatibility",
        "cp_m": cp,
        "external_aerodynamic_geometry_unchanged": cp == center_of_pressure(source),
        "mass_allowance_kg_at_aft_station": allowance,
        "endpoint_rows": rows,
        "minimum_static_margin_with_full_aft_allowance_over_101_depletion_samples_cal": min(
            margins
        ),
        "depletion_sampling_is_not_continuous_or_flight_validation": True,
        "independent_rocketpy_static_comparison": compare_rocketpy(candidate),
        "flight_reference_recomputed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    args = parser.parse_args()
    started = time.perf_counter()
    cfg = yaml.safe_load(args.config.read_bytes())
    source = ROOT / cfg["source_record"]
    paths = [
        source,
        source.parent / "resolved-candidate.json",
        args.config.resolve(),
        Path(__file__).resolve(),
        ROOT / "scripts/wo03_multilayer_shield.py",
        ROOT / "src/vehicle/schema.py",
        ROOT / "src/vehicle/cad_contract.py",
        ROOT / "src/vehicle/mass.py",
        ROOT / "src/vehicle/aero.py",
        ROOT / "src/vehicle/reference.py",
        ROOT / "src/vehicle/motors.py",
        ROOT / "tests/test_baffle_fit.py",
        *sorted((ROOT / "src/cad").glob("*.py")),
    ]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    run_id = "wo03-baffle-fit-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "runs" / run_id
    folder.mkdir(parents=True)
    (folder / "parts").mkdir()
    for p in paths:
        dest = folder / "source-snapshot" / p.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(p.read_bytes())
    original = Vehicle.model_validate_json((source.parent / "resolved-candidate.json").read_bytes())
    if (
        hashlib.sha256(original.model_dump_json(by_alias=True).encode()).hexdigest()
        != cfg["expected_candidate_identity"]
    ):
        raise ValueError("Baffle source identity mismatch")
    v = original.model_copy(deep=True)
    if original.motor and original.motor.curve:
        curve_path = ROOT / original.motor.curve
        hashes[str(curve_path.relative_to(ROOT))] = hashlib.sha256(
            curve_path.read_bytes()
        ).hexdigest()
        target = folder / "source-snapshot" / curve_path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(curve_path.read_bytes())
    windows, changed = extend_windows(v, cfg["geometry"])
    new, new_shapes, contacts = create_parts(v, cfg)
    source_parts = list(v.parts)
    v.parts.extend(new)
    solids = {
        p.id: placed(p, new_shapes[p.id] if p.id in new_shapes else local_shape(p))
        for p in v.parts
        if p.cad
    }
    tolerance = cfg["numerics"]["collision_volume_tolerance_mm3"]
    # Full actual applicable rigid hardware. Budget/flexible envelopes are
    # explicitly excluded; adhesive volumes and purchased motor envelope remain.
    hardware = [
        p
        for p in source_parts
        if p.cad
        and p.cad.role not in {"distributed_budget", "soft_stowage"}
        and p.cad.generator != "budget"
    ]
    collisions = []
    for p in new:
        for other in hardware:
            overlap = common_volume(solids[p.id], solids[other.id])
            if overlap > tolerance:
                collisions.append(
                    {"new_part_id": p.id, "source_part_id": other.id, "overlap_mm3": overlap}
                )
    for i, p in enumerate(new):
        for other in new[:i]:
            overlap = common_volume(solids[p.id], solids[other.id])
            if overlap > tolerance:
                collisions.append(
                    {"new_part_id": p.id, "source_part_id": other.id, "overlap_mm3": overlap}
                )
    print(
        json.dumps(
            {
                "stage": "nominal_actual_hardware",
                "new_parts": len(new),
                "collisions": len(collisions),
                "elapsed_s": time.perf_counter() - started,
            }
        ),
        flush=True,
    )
    # A specified straight radial panel path in the open cage. This is a sampled
    # service screen; failure is preserved, never bypassed by flexible deflection.
    path_rows = []
    cage_hardware = [
        p
        for p in hardware
        if p.id
        in {
            "motor_mount",
            "retention",
            "aft_retainer",
            "retention_hardware",
            "motor",
            "motor_liner",
            "motor_radiant_shield",
        }
    ]
    for p in new:
        if p.material != "aluminum":
            continue
        local = new_shapes[p.id]
        for panel in local.Solids():
            centre = panel.Center()
            angle = math.atan2(centre.y, centre.x)
            direction = min(
                cfg["geometry"]["support_angles_deg"],
                key=lambda a: abs(
                    math.atan2(math.sin(angle - math.radians(a)), math.cos(angle - math.radians(a)))
                ),
            )
            first_collision = None
            for shift in cfg["service_path"]["radial_panel_translation_m"]:
                trial = placed(p, panel).translate(
                    (
                        shift * 1000 * math.cos(math.radians(direction)),
                        shift * 1000 * math.sin(math.radians(direction)),
                        0,
                    )
                )
                hits = [
                    q.id for q in cage_hardware if common_volume(trial, solids[q.id]) > tolerance
                ]
                if hits:
                    first_collision = {"radial_translation_m": shift, "hardware": hits}
                    break
            path_rows.append(
                {
                    "baffle_id": p.id,
                    "panel_center_angle_deg": math.degrees(angle) % 360,
                    "specified_translation_direction_deg": direction,
                    "sampled_path_passed": first_collision is None,
                    "first_collision": first_collision,
                }
            )
    motor_rows = []
    removed = set(cfg["service_path"]["motor_extraction_removed_part_ids"]) | {"motor"}
    motor_hardware = [p for p in (*hardware, *new) if p.id not in removed]
    for shift in cfg["service_path"]["motor_extraction_aft_translation_m"]:
        trial = solids["motor"].translate((0, 0, shift * 1000))
        hits = [p.id for p in motor_hardware if common_volume(trial, solids[p.id]) > tolerance]
        motor_rows.append(
            {"aft_translation_m": shift, "colliding_part_ids": hits, "passed": not hits}
        )
    staged = staged_panel_paths(v, new, new_shapes, solids, contacts, cfg)
    mass_stability = mass_stability_delta(original, v)
    manifest = []
    for p in v.parts:
        if p.id not in solids:
            continue
        step = folder / "parts" / (p.id + ".step")
        stl = folder / "parts" / (p.id + ".stl")
        cq.exporters.export(solids[p.id], str(step))
        cq.exporters.export(
            solids[p.id],
            str(stl),
            tolerance=cfg["numerics"]["stl_tolerance_mm"],
            angularTolerance=cfg["numerics"]["stl_angular_tolerance_rad"],
        )
        manifest.append(
            {
                "part_id": p.id,
                "material": p.material,
                "cad_role": p.cad.role,
                "cad_generator": p.cad.generator,
                "new_part": p in new,
                "custom_postprocessing_required": p.id in new_shapes,
                "step": str(step.relative_to(folder)),
                "step_sha256": hashlib.sha256(step.read_bytes()).hexdigest(),
                "stl": str(stl.relative_to(folder)),
                "stl_sha256": hashlib.sha256(stl.read_bytes()).hexdigest(),
                "placed_frame": "CAD_mm_X_body_y_Y_minus_body_z_Z_aft_station",
                "volume_m3": solids[p.id].Volume() * 1e-9,
                "mass_kg": p.resolved_mass_kg,
                "valid": bool(solids[p.id].isValid()),
            }
        )
    nominal_delta = sum(p.resolved_mass_kg for p in v.parts) - sum(
        p.resolved_mass_kg for p in original.parts
    )
    new_mass = sum(p.resolved_mass_kg for p in new)
    if new_mass > cfg["mass"]["additional_mass_reserve_kg"]:
        raise ValueError("One baffle family exceeds mass reserve")
    (folder / "resolved-candidate.json").write_text(v.model_dump_json(by_alias=True, indent=2))
    (folder / "geometry-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    unchanged = all(
        hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in hashes.items()
    )
    if not unchanged:
        raise ValueError("Baffle input or CAD source changed during generation/check/export")
    record = {
        "run_id": run_id,
        "source_candidate_identity": cfg["expected_candidate_identity"],
        "candidate_identity": hashlib.sha256(v.model_dump_json(by_alias=True).encode()).hexdigest(),
        "cad_revision_sha256": hashlib.sha256(
            b"".join(p.read_bytes() for p in sorted((ROOT / "src/cad").glob("*.py")))
        ).hexdigest(),
        "study_postprocessor_sha256": hashes[str(Path(__file__).resolve().relative_to(ROOT))],
        "input_sha256": hashes,
        "inputs_unchanged": unchanged,
        "geometry": cfg["geometry"],
        "changed_windows": windows,
        "changed_source_part_ids": changed,
        "contact_ledger": contacts,
        "all_new_nominal_intersections": collisions,
        "new_nominal_collision_check_passed": not collisions,
        "excluded_source_collision_envelopes": [p.id for p in source_parts if p not in hardware],
        "clearance_budget": clearance_budget(v, cfg, windows),
        "sampled_radial_panel_paths": path_rows,
        "sampled_radial_paths_all_passed": all(r["sampled_path_passed"] for r in path_rows),
        "staged_baffle_first_assembly": staged,
        "new_part_mass_kg": new_mass,
        "net_whole_copy_mass_delta_kg": nominal_delta,
        "mass_reserve_kg": cfg["mass"]["additional_mass_reserve_kg"],
        "fixed_G54_mass_cg_full_inertia_and_stability": mass_stability,
        "actual_notched_seamed_step_stl_manifest": "geometry-manifest.json",
        "standalone_generic_CAD_regeneration_matches_postprocessed_parts": False,
        "radial_service_condition": cfg["service_path"]["assembly_condition"],
        "motor_extraction_sampled_path": motor_rows,
        "motor_extraction_sampled_path_passed": all(row["passed"] for row in motor_rows),
        "motor_extraction_removed_part_ids": sorted(removed - {"motor"}),
        "actual_supplier_closure_nozzle_envelope_and_continuous_sweep": "unavailable; nominal vendor-cylinder extraction only",
        "continuous_or_deformed_CAD_clearance_validated": False,
        "original_engineering_failures_preserved": True,
        "thermal_acceptance_available": False,
        "active_adoption": False,
        "flight_ready": False,
        "elapsed_s": time.perf_counter() - started,
        "cpu_workers": 1,
        "ray_count": 0,
        "cost_usd": 0,
    }
    (folder / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "record": str(folder / "record.json"),
                "new_mass_g": new_mass * 1000,
                "net_mass_delta_g": nominal_delta * 1000,
                "nominal_collisions": len(collisions),
                "radial_paths_passed": record["sampled_radial_paths_all_passed"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
