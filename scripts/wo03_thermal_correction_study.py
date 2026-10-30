"""Bounded in-memory aft thermal correction trade; no active vehicle edits."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import yaml

from scripts.wo03_fit_structure import make_candidate
from src.analysis.thermal_topology import run_thermal_topology
from src.cad.parts import box as cad_box
from src.cad.parts import compound as cad_compound
from src.cad.parts import local_shape, properties
from src.cad.parts import tube as cad_tube
from src.sim.inputs import source_hashes
from src.vehicle.mass import mass_properties
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import CADMass, Part, load_vehicle, vehicle_input_paths


def encoded_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def secondary_foil(vehicle: Any, study_cfg: dict[str, Any]) -> Part:
    """Construct a 20um foil ring with CAD-integrated volume and inertia."""
    parts = {part.id: part for part in vehicle.parts}
    liner = parts["motor_liner"]
    existing_foil = parts["motor_radiant_shield"]
    mount = parts["motor_mount"]
    geometry_cfg = study_cfg["secondary_foil"]
    thickness = float(geometry_cfg["thickness_m"])
    inner = float(existing_foil.geometry["radius_m"]) + float(
        geometry_cfg["radial_clearance_from_existing_foil_m"]
    )
    outer = inner + thickness
    mount_inner = float(mount.geometry["inner_radius_m"])
    expected_outer_clearance = float(geometry_cfg["radial_clearance_to_mount_bore_m"])
    if not np.isclose(mount_inner - outer, expected_outer_clearance, atol=1e-12):
        raise ValueError(
            f"{vehicle.id}: foil/mount clearance differs from the study's reconciled geometry"
        )
    base = existing_foil.model_dump(by_alias=True)
    base.update(
        {
            "id": str(geometry_cfg["id"]),
            "parent": "aft_shell",
            "position_m": float(liner.position_m),
            "geometry": {
                "length_m": float(liner.geometry["length_m"]),
                "radius_m": outer,
                "inner_radius_m": inner,
            },
            "material": str(geometry_cfg["material"]),
            "mass_kg": None,
            "density_kg_m3": float(geometry_cfg["density_kg_m3"]),
            "cg_offset_m": None,
            "learn": (
                "Candidate secondary opaque radiant shield in the radial annulus between the "
                "existing foil and motor-support bore. It is an in-memory correction-study "
                "part; forming, seams, restraint, tolerances and heat-test behavior remain unverified."
            ),
            "build": {
                "method": "cut",
                "cost_usd": 0,
                "generator": "study_only_tube",
                "notes": "Parametric study-only foil sleeve; not adopted or released for manufacture.",
            },
            "cad": {
                "generator": "tube",
                "parameters": {},
                "mass_basis": "volume_density",
                "role": "manufactured",
                "moving_group": "fixed",
                "color": "#c7ccd1",
                "notes": "Study-only 20um continuous annulus; nominal fit is not tolerance-qualified.",
            },
            "cad_mass": None,
            "engineering": {
                "function": "Candidate secondary radiant shield between existing foil and motor-support bore.",
                "material_profile": str(geometry_cfg["material"]),
                "tolerances_mm": {},
                "load_cases": [],
                "thermal_cases": ["case_120C", "case_250C", "case_300C", "contaminated_foil"],
                "property_basis": "estimated",
                "service_notes": "Study only; no adoption or manufacturing release.",
                "required_physical_verification": [
                    "Verify concentric clearance, assembly sequence and foil restraint.",
                    "Instrument temperature and emissivity through burn, soak, vibration and contamination exposure.",
                ],
            },
        }
    )
    provisional = Part.model_validate(base)
    shape = local_shape(provisional)
    cad_properties = properties(provisional, shape)
    mass = float(cad_properties["volume_m3"]) * float(geometry_cfg["density_kg_m3"])
    base["mass_kg"] = mass
    base["density_kg_m3"] = None
    base["cad_mass"] = cad_properties
    return Part.model_validate(base)


def first_mount_bridge(
    vehicle: Any, study_cfg: dict[str, Any]
) -> tuple[Part | None, dict[str, Any]]:
    """Build a CAD-sized bridge only where a mount ring nearly touches the shell."""
    parts = {part.id: part for part in vehicle.parts}
    mount = parts["motor_mount"]
    shell = parts["aft_shell"]
    cfg = study_cfg["first_mount_bridge"]
    stations = mount.cad.parameters.get("ring_stations_mm", [])
    widths = mount.cad.parameters.get("ring_thicknesses_mm", [])
    if not stations or not widths:
        return None, {"status": "not_applicable", "reason": "mount has no discrete ring station"}
    inner = float(mount.geometry["radius_m"])
    outer = float(shell.geometry["inner_radius_m"])
    gap = outer - inner
    z = float(mount.position_m) + float(stations[0]) * 0.001
    width = float(widths[0]) * 0.001
    slot_start = (
        mount.position_m
        + float(
            mount.cad.parameters.get(
                "fin_slot_start_mm", mount.cad.parameters.get("tab_slot_start_mm", 1e6)
            )
        )
        * 0.001
    )
    geometry = {
        "radial_gap_m": gap,
        "axial_interval_m": [z, z + width],
        "fin_slot_start_m": slot_start,
    }
    if gap <= 0 or gap > float(cfg["maximum_radial_gap_m"]):
        return None, {
            "status": "not_applicable",
            "reason": "gap outside bounded bridge geometry",
            **geometry,
        }
    if z + width > slot_start:
        return None, {
            "status": "not_applicable",
            "reason": "bridge intersects fin-slot interval",
            **geometry,
        }
    base = parts["motor_radiant_shield"].model_dump(by_alias=True)
    base.update(
        {
            "id": str(cfg["id"]),
            "parent": "aft_shell",
            "position_m": z,
            "geometry": {"length_m": width, "radius_m": outer, "inner_radius_m": inner},
            "material": str(cfg["material"]),
            "mass_kg": None,
            "density_kg_m3": float(cfg["density_kg_m3"]),
            "cg_offset_m": None,
            "learn": "Study-only CAD-sized annular heat bridge at the first motor-mount ring; contact area and fit are estimates.",
            "build": {
                "method": "cut",
                "cost_usd": 0,
                "generator": "study_only_tube",
                "notes": "Not adopted or released.",
            },
            "cad": {
                "generator": "tube",
                "parameters": {},
                "mass_basis": "volume_density",
                "role": "manufactured",
                "moving_group": "fixed",
                "color": "#c7ccd1",
                "notes": "Study-only bridge ring.",
            },
            "cad_mass": None,
            "engineering": {
                "function": "Candidate narrow thermal bridge between shell and first fixed mount support ring.",
                "material_profile": str(cfg["material"]),
                "tolerances_mm": {},
                "load_cases": [],
                "thermal_cases": ["case_120C", "case_250C", "case_300C", "contaminated_foil"],
                "property_basis": "estimated",
                "service_notes": "Study only; contact conductance and fit are unvalidated.",
                "required_physical_verification": [
                    "Measure radial/axial fit and contact pressure.",
                    "Instrument ring, mount and shell through burn and post-soak.",
                ],
            },
        }
    )
    provisional = Part.model_validate(base)
    props = properties(provisional, local_shape(provisional))
    mass = float(props["volume_m3"]) * float(cfg["density_kg_m3"])
    base["mass_kg"] = mass
    base["density_kg_m3"] = None
    base["cad_mass"] = props
    bridge = Part.model_validate(base)
    return bridge, {
        "status": "geometry_created",
        **geometry,
        "inner_radius_m": inner,
        "outer_radius_m": outer,
        "volume_m3": props["volume_m3"],
        "shape_sha256": props["shape_sha256"],
        "mass_kg": mass,
    }


def candidate_vehicle(
    vehicle: Any, candidate: dict[str, Any], study_cfg: dict[str, Any]
) -> tuple[Any, dict[str, Any]]:
    copy_vehicle = vehicle.model_copy(deep=True)
    added_part: Part | None = None
    bridge: Part | None = None
    if candidate["add_secondary_foil"]:
        added_part = secondary_foil(vehicle, study_cfg)
        copy_vehicle.parts.append(added_part)
    bridge_check: dict[str, Any] = {"status": "not_requested"}
    if candidate.get("add_first_mount_bridge", False):
        bridge, bridge_check = first_mount_bridge(vehicle, study_cfg)
        if bridge is not None:
            copy_vehicle.parts.append(bridge)
    geometry_checks: dict[str, Any] = {
        "added_part": None,
        "removed_thermal_contact_pairs": [],
        "first_mount_bridge": bridge_check,
    }
    if added_part:
        parts = {part.id: part for part in vehicle.parts}
        mount = parts["motor_mount"]
        old_foil = parts["motor_radiant_shield"]
        geometry_checks["added_part"] = {
            "part_id": added_part.id,
            "axial_interval_m": [
                added_part.position_m,
                added_part.position_m + added_part.geometry["length_m"],
            ],
            "radial_interval_m": [
                added_part.geometry["inner_radius_m"],
                added_part.geometry["radius_m"],
            ],
            "clearance_from_existing_foil_m": (
                added_part.geometry["inner_radius_m"] - old_foil.geometry["radius_m"]
            ),
            "clearance_to_mount_bore_m": (
                mount.geometry["inner_radius_m"] - added_part.geometry["radius_m"]
            ),
            "volume_m3": added_part.cad_mass.volume_m3 if added_part.cad_mass else None,
            "shape_sha256": added_part.cad_mass.shape_sha256 if added_part.cad_mass else None,
            "mass_kg": added_part.resolved_mass_kg,
        }
    study = copy.deepcopy(study_cfg["reference_study"])
    if added_part:
        study["part_ids"].append(added_part.id)
        study["annular_barrier_part_ids"].append(added_part.id)
    if bridge is not None:
        study["part_ids"].append(bridge.id)
        study["annular_barrier_part_ids"].append(bridge.id)
        study["contact_pairs"].extend([["motor_mount", bridge.id], [bridge.id, "aft_shell"]])
    remove_edge = bool(candidate["remove_motor_mount_aft_shell_contact"])
    if candidate.get("add_first_mount_bridge", False) and bridge is None:
        remove_edge = False
    if remove_edge:
        before = [list(pair) for pair in study["contact_pairs"]]
        study["contact_pairs"] = [
            pair for pair in study["contact_pairs"] if set(pair) != {"motor_mount", "aft_shell"}
        ]
        geometry_checks["removed_thermal_contact_pairs"] = [
            pair for pair in before if set(pair) == {"motor_mount", "aft_shell"}
        ]
    return copy_vehicle, {"study": study, "geometry_checks": geometry_checks}


def mass_delta(reference: Any, candidate: Any) -> dict[str, Any]:
    base = mass_properties(reference)
    changed = mass_properties(candidate)
    return {
        "reference_mass_kg": base.mass_kg,
        "candidate_mass_kg": changed.mass_kg,
        "delta_mass_g": (changed.mass_kg - base.mass_kg) * 1000,
        "reference_cg_m": base.cg_m,
        "candidate_cg_m": changed.cg_m,
        "delta_cg_mm": (changed.cg_m - base.cg_m) * 1000,
        "reference_inertia_kg_m2": base.inertia_kg_m2.tolist(),
        "candidate_inertia_kg_m2": changed.inertia_kg_m2.tolist(),
        "delta_inertia_kg_m2": (changed.inertia_kg_m2 - base.inertia_kg_m2).tolist(),
    }


def reconciled_fit_candidate(vehicle: Any, package: dict[str, Any]) -> Any:
    """Apply braced Package A and reconcile its changed mount with CAD and material density."""
    candidate = make_candidate(vehicle, package, True)
    mount = next(part for part in candidate.parts if part.id == "motor_mount")
    assert mount.cad
    shape = local_shape(mount)
    props = properties(mount, shape)
    mount.cad_mass = CADMass.model_validate(props)
    mount.mass_kg = float(props["volume_m3"]) * float(DENSITY_KG_M3[mount.material])
    mount.density_kg_m3 = None
    mount.cg_offset_m = max(0.0, -float(props["cg_local_body_m"][0]))
    return candidate


def reconciled_bonded_candidate(
    vehicle: Any,
    package: dict[str, Any],
    bond_cfg: dict[str, Any],
    conductivity_w_m_k: float,
    gap_m: float,
) -> tuple[Any, list[Part], dict[str, Any]]:
    """Build Package A with CAD-reconciled mount and slotted CAD epoxy ring solids."""
    candidate = make_candidate(vehicle, package, True)
    mount = next(part for part in candidate.parts if part.id == "motor_mount")
    shell = next(part for part in candidate.parts if part.id == "aft_shell")
    assert mount.cad and shell.cad
    mount.geometry["radius_m"] = float(shell.geometry["inner_radius_m"]) - gap_m
    mount.cad_mass = None
    mount_props = properties(mount, local_shape(mount))
    mount.cad_mass = CADMass.model_validate(mount_props)
    mount.mass_kg = float(mount_props["volume_m3"]) * float(DENSITY_KG_M3[mount.material])
    mount.density_kg_m3 = None
    mount.cg_offset_m = max(0.0, -float(mount_props["cg_local_body_m"][0]))

    ring_stations = [float(v) for v in mount.cad.parameters["ring_stations_mm"]]
    ring_widths = [float(v) for v in mount.cad.parameters["ring_thicknesses_mm"]]
    slot_width = float(shell.cad.parameters.get("fin_slot_width_mm", 0.0))
    slot_start_global_mm = float(shell.position_m) * 1000.0 + float(
        shell.cad.parameters.get("fin_slot_start_mm", 0.0)
    )
    slot_end_global_mm = slot_start_global_mm + float(
        shell.cad.parameters.get("fin_slot_length_mm", 0.0)
    )
    mount_start_global_mm = float(mount.position_m) * 1000.0
    outer_radius_mm = float(shell.geometry["inner_radius_m"]) * 1000.0
    inner_radius_mm = float(mount.geometry["radius_m"]) * 1000.0
    shell_radius_mm = float(shell.geometry["radius_m"]) * 1000.0
    gap_area_rows = []
    bonds = []
    for index, (station_mm, width_mm) in enumerate(zip(ring_stations, ring_widths, strict=True)):
        ring_start_global_mm = mount_start_global_mm + station_mm
        ring_end_global_mm = ring_start_global_mm + width_mm
        overlap_start = max(ring_start_global_mm, slot_start_global_mm)
        overlap_end = min(ring_end_global_mm, slot_end_global_mm)
        ring_shape = cad_tube(outer_radius_mm, inner_radius_mm, width_mm)
        overlap_length_mm = max(0.0, overlap_end - overlap_start)
        if overlap_length_mm > 1e-9 and slot_width > 0:
            local_overlap_start_mm = overlap_start - ring_start_global_mm
            for angle in [0.0, 120.0, 240.0]:
                cutter = cad_box(6.0, slot_width, overlap_length_mm).translate(
                    (shell_radius_mm, 0.0, local_overlap_start_mm)
                )
                cutter = cutter.rotate((0, 0, 0), (0, 0, 1), angle)
                ring_shape = ring_shape.cut(cutter)
        bond_id = f"{bond_cfg['id']}_{index}"
        base = shell.model_dump(by_alias=True)
        base.update(
            {
                "id": bond_id,
                "type": "commercial",
                "parent": "motor_mount",
                "position_m": float(mount.position_m) + station_mm * 0.001,
                "geometry": {
                    "length_m": width_mm * 0.001,
                    "radius_m": outer_radius_mm * 0.001,
                    "inner_radius_m": inner_radius_mm * 0.001,
                    "wall_m": gap_m,
                },
                "material": "commercial",
                "mass_kg": None,
                "density_kg_m3": float(bond_cfg["density_kg_m3"]),
                "cg_offset_m": None,
                "learn": "Study-only epoxy bond annulus between Package A mount ring and aft shell. Its CAD volume includes the fin-slot cutouts; interface and strength behavior remain unqualified.",
                "build": {
                    "method": "bonded",
                    "cost_usd": 0,
                    "generator": "study_only_bond_ring",
                    "notes": "CAD ring solids used for mass/area; no fillet allowance or mechanical allowable is included.",
                },
                "cad": {
                    "generator": "study_only_bond_ring",
                    "parameters": {
                        "ring_station_mm": station_mm,
                        "ring_width_mm": width_mm,
                        "inner_radius_mm": inner_radius_mm,
                        "outer_radius_mm": outer_radius_mm,
                        "slot_start_global_mm": slot_start_global_mm,
                        "slot_end_global_mm": slot_end_global_mm,
                        "slot_width_mm": slot_width,
                        "gap_m": gap_m,
                    },
                    "mass_basis": "volume_density",
                    "role": "manufactured",
                    "moving_group": "fixed",
                    "color": "#e8cf7a",
                    "notes": "Exact CadQuery compound for one ring with intersecting 3-slot cuts; ring is a study helper, not adopted active CAD.",
                },
                "cad_mass": None,
                "engineering": {
                    "function": "Conditional adhesive thermal bridge and retention-ring bond screen.",
                    "material_profile": str(bond_cfg["thermal_profile_key"]),
                    "tolerances_mm": {},
                    "load_cases": ["mount_retention"],
                    "thermal_cases": [
                        "upper_hot_soak",
                        "case_300c_sensitivity",
                        "contaminated_foil",
                    ],
                    "property_basis": "estimated",
                    "service_notes": "Study only. No bond shear/peel strength, fatigue or hot durability is inferred.",
                    "required_physical_verification": [
                        "Verify bond gap, surface preparation, cure and wetting around fin-slot interruptions.",
                        "Measure representative bond conductivity and hot interface behavior.",
                        "Perform ground proof, thermal-cycle and vibration testing of the bonded mount/shell assembly.",
                    ],
                },
            }
        )
        provisional = Part.model_validate(base)
        props = properties(provisional, cad_compound([ring_shape]))
        mass = float(props["volume_m3"]) * float(bond_cfg["density_kg_m3"])
        base["mass_kg"] = mass
        base["density_kg_m3"] = None
        base["cg_offset_m"] = max(0.0, -float(props["cg_local_body_m"][0]))
        base["cad_mass"] = props
        bond = Part.model_validate(base)
        bonds.append(bond)
        gap_area_rows.append(
            {
                "bond_part_id": bond_id,
                "ring_station_m": float(mount.position_m) + station_mm * 0.001,
                "ring_width_m": width_mm * 0.001,
                "slot_intersection_length_mm": overlap_length_mm,
                "slot_cut_area_m2": overlap_length_mm * slot_width * 3 * 1e-6,
                "cad_volume_m3": props["volume_m3"],
                "cad_area_m2": props["volume_m3"] / gap_m,
                "conductance_w_k": conductivity_w_m_k * props["volume_m3"] / gap_m**2,
                "mass_kg": mass,
                "shape_sha256": props["shape_sha256"],
            }
        )
    candidate.parts.extend(bonds)
    return (
        candidate,
        bonds,
        {
            "nominal_radial_gap_m": gap_m,
            "mount_outer_radius_m": mount.geometry["radius_m"],
            "shell_inner_radius_m": shell.geometry["inner_radius_m"],
            "ring_stations_mm": ring_stations,
            "ring_widths_mm": ring_widths,
            "slot_interval_global_m": [slot_start_global_mm * 0.001, slot_end_global_mm * 0.001],
            "slot_width_mm": slot_width,
            "ring_bond_area_m2": sum(row["cad_area_m2"] for row in gap_area_rows),
            "total_conductance_w_k": sum(row["conductance_w_k"] for row in gap_area_rows),
            "bond_mass_kg": sum(row["mass_kg"] for row in gap_area_rows),
            "bond_volume_m3": sum(row["cad_volume_m3"] for row in gap_area_rows),
            "fillet_allowance_included": False,
            "rings": gap_area_rows,
        },
    )


def build_skin(vehicle: Any, skin_cfg: dict[str, Any], thickness: float) -> Part:
    """Create a slotted fin-can skin part with CAD-integrated mass properties."""
    shell = next(part for part in vehicle.parts if part.id == "aft_shell")
    end = min(
        shell.position_m + float(shell.geometry["length_m"]),
        float(skin_cfg["maximum_axial_end_m"]),
    )
    start = max(shell.position_m, float(skin_cfg["axial_start_m"]))
    if end <= start:
        raise ValueError(f"{vehicle.id}: no aft shell interval remains for fin-can skin")
    inner = float(shell.geometry["radius_m"])
    outer = inner + thickness
    base = shell.model_dump(by_alias=True)
    base.update(
        {
            "id": str(skin_cfg["id"]),
            "parent": "aft_shell",
            "position_m": start,
            "geometry": {
                "length_m": end - start,
                "radius_m": outer,
                "inner_radius_m": inner,
                "wall_m": thickness,
            },
            "material": str(skin_cfg["material"]),
            "mass_kg": None,
            "density_kg_m3": float(skin_cfg["density_range_kg_m3"][1]),
            "cg_offset_m": None,
            "learn": "Study-only slotted glass-epoxy fin-can skin geometry. No structural benefit, bond capacity or thermal shielding is qualified.",
            "build": {
                "method": "bonded",
                "cost_usd": 0,
                "generator": "study_only_slotted_tube",
                "notes": "Candidate only; layup, slot fit and bond process are not selected.",
            },
            "cad": {
                "generator": "tube",
                "parameters": {
                    "fin_slots": True,
                    "fin_slot_width_mm": float(skin_cfg["cad_slot_width_mm"]),
                    "fin_slot_length_mm": 100.0,
                    "fin_slot_start_mm": (1.09 - start) * 1000.0,
                },
                "mass_basis": "volume_density",
                "role": "manufactured",
                "moving_group": "fixed",
                "color": "#b6c8d7",
                "notes": "Mass integrates CAD-cut slots: 6 mm radial cutter depth and 7.3 mm tangential slot width. Thermal radial solver does not resolve these angular openings.",
            },
            "cad_mass": None,
            "engineering": {
                "function": "Conditional exterior laminate over slotted aft shell; possible fin-root load-sharing concept, unverified.",
                "material_profile": str(skin_cfg["thermal_profile_key"]),
                "tolerances_mm": {},
                "load_cases": ["fin_bending"],
                "thermal_cases": ["case_300c_sensitivity", "contaminated_foil"],
                "property_basis": "estimated",
                "service_notes": "Study only; no adoption or structural capacity claim.",
                "required_physical_verification": [
                    "Confirm exact laminate/layup, density, through-thickness conductivity and heat capacity.",
                    "Verify fin-slot clearance, bond preparation, thermal expansion and vibration durability.",
                    "Test instrumented full assembly through burn and post-soak.",
                ],
            },
        }
    )
    provisional = Part.model_validate(base)
    shape = local_shape(provisional)
    props = properties(provisional, shape)
    mass = float(props["volume_m3"]) * float(skin_cfg["density_range_kg_m3"][1])
    base["mass_kg"] = mass
    base["density_kg_m3"] = None
    base["cad_mass"] = props
    return Part.model_validate(base)


def skin_mass_sensitivity(
    vehicle: Any, skin_cfg: dict[str, Any], thickness: float
) -> dict[str, Any]:
    skin = build_skin(vehicle, skin_cfg, thickness)
    assert skin.cad_mass is not None and skin.cad is not None
    cad_mass = skin.cad_mass
    cad = skin.cad
    density_rows = []
    for density in skin_cfg["density_range_kg_m3"]:
        part = skin.model_copy(
            update={"mass_kg": cad_mass.volume_m3 * float(density), "density_kg_m3": None}
        )
        candidate = vehicle.model_copy(deep=True)
        candidate.parts.append(part)
        density_rows.append(
            {
                "density_kg_m3": float(density),
                "mass_delta_cg_inertia": mass_delta(vehicle, candidate),
            }
        )
    g = skin.geometry
    slot_start = skin.position_m + float(cad.parameters["fin_slot_start_mm"]) * 0.001
    slot_end = slot_start + float(cad.parameters["fin_slot_length_mm"]) * 0.001
    actual_tangential_slot_width_mm = float(cad.parameters["fin_slot_width_mm"])
    radial_slot_cut_depth_mm = 6.0  # x cutter dimension; y carries configured tangential width.
    covered_length = float(g["length_m"])
    fin = next((part for part in vehicle.parts if part.type == "fin_set"), None)
    fin_root_interference_mm = None
    fin_root_thickness_mm = None
    if fin is not None:
        fin_root_thickness_mm = float(fin.geometry["thickness_m"]) * 1000.0
        fin_root_interference_mm = max(
            0.0, (float(g["radius_m"]) - float(fin.geometry["radius_m"])) * 1000.0
        )
    slot_area_fraction = min(
        1.0,
        3.0 * actual_tangential_slot_width_mm / (2.0 * np.pi * (float(g["radius_m"]) * 1000.0)),
    )
    return {
        "thickness_m": thickness,
        "axial_interval_m": [skin.position_m, skin.position_m + float(g["length_m"])],
        "radial_interval_m": [float(g["inner_radius_m"]), float(g["radius_m"])],
        "nominal_slot_interval_m": [slot_start, slot_end],
        "cad_slot_width_mm": float(cad.parameters["fin_slot_width_mm"]),
        "actual_tangential_slot_width_mm": actual_tangential_slot_width_mm,
        "radial_slot_cut_depth_mm": radial_slot_cut_depth_mm,
        "radial_cut_depth_margin_over_skin_mm": radial_slot_cut_depth_mm - thickness * 1000.0,
        "source_shell_slot_width_mm": float(skin_cfg["physical_slot_width_mm"]),
        "slot_open_fraction_of_local_circumference_estimate": slot_area_fraction,
        "continuous_wrap_fraction_after_axial_slot_intersection": max(
            0.0, 1 - (slot_end - slot_start) / covered_length
        ),
        "fin_root_thickness_mm": fin_root_thickness_mm,
        "skin_radial_intrusion_past_fin_root_mm": fin_root_interference_mm,
        "total_fin_root_slot_clearance_mm": (
            actual_tangential_slot_width_mm - fin_root_thickness_mm
            if fin_root_thickness_mm is not None
            else None
        ),
        "nominal_fin_root_clearance_per_flank_mm": (
            (actual_tangential_slot_width_mm - fin_root_thickness_mm) / 2
            if fin_root_thickness_mm is not None
            else None
        ),
        "fin_root_clearance_status": (
            "nominal clearance from configured tangential slot width; assembly tolerance, adhesive and angular alignment unverified"
            if fin_root_thickness_mm is not None
            else "not_applicable"
        ),
        "volume_m3": cad_mass.volume_m3,
        "shape_sha256": cad_mass.shape_sha256,
        "density_mass_cg_inertia_sensitivities": density_rows,
        "thermal_simulation_status": "not_modeled: radial solver would incorrectly seal the real fin slots",
        "clearance_screen": "outer-body/fin-root/slot/adhesive tolerance not verified; geometric overlap screen only",
    }


def solve_case(
    vehicle: Any,
    engineering_cfg: dict[str, Any],
    study: dict[str, Any],
    scenario: int,
    ambient_c: float,
    *,
    case_peak_override_c: float | None = None,
    cells: int = 16,
) -> dict[str, Any]:
    cfg = copy.deepcopy(engineering_cfg)
    cfg["thermal"]["ambient_c"][scenario] = float(ambient_c)
    if case_peak_override_c is not None:
        cfg["thermal"]["external_case_peak_c"][scenario] = float(case_peak_override_c)
    result = run_thermal_topology(
        vehicle,
        cfg,
        study,
        False,
        cells=cells,
        scenario_index=scenario,
    )
    shell = next((row for row in result["peaks"] if row["part_id"] == "aft_shell"), None)
    return {
        "case_id": result["case"],
        "scenario_index": scenario,
        "ambient_c": float(ambient_c),
        "prescribed_case_peak_c": float(cfg["thermal"]["external_case_peak_c"][scenario]),
        "post_burn_cooling_tau_s": float(cfg["thermal"]["post_burn_cooling_tau_s"][scenario]),
        "aft_shell_peak_c": shell["peak_c"] if shell else None,
        "aft_shell_peak_time_s": shell["peak_time_s"] if shell else None,
        "screen_limit_c": shell["screen_limit_c"] if shell else None,
        "screen_margin_k": shell["margin_k"] if shell else None,
        "parts": result["peaks"],
        "energy_residual_j": result["energy_residual_j"],
        "radial_bands": result["radial_bands"],
        "cells": cells,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/platform.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    args = parser.parse_args()

    study_cfg_path = Path("configs/studies/wo03-thermal-correction.yaml")
    reference_study_path = Path("configs/studies/wo03-thermal-topology.yaml")
    fit_structure_config_path = Path("configs/studies/wo03-fit-correction.yaml")
    fit_structure_script_path = Path("scripts/wo03_fit_structure.py")
    engineering_path = Path("configs/engineering/wo03.yaml")
    study_cfg = yaml.safe_load(study_cfg_path.read_text())
    study = yaml.safe_load(reference_study_path.read_text())
    cfg = yaml.safe_load(engineering_path.read_text())
    fit_structure_cfg = yaml.safe_load(fit_structure_config_path.read_text())
    fit_package = next(
        package for package in fit_structure_cfg["packages"] if package["id"] == "fit-package-a"
    )
    platform = yaml.safe_load(args.config.read_text())
    paths = [Path(path) for path in platform["vehicles"]]
    g54_path = Path("configs/vehicle/wo02/performance-g54.yaml")
    if g54_path not in paths:
        paths.append(g54_path)

    run_id = datetime.now(UTC).strftime("wo03-thermal-correction-%Y%m%dT%H%M%S%fZ")
    out = Path("runs") / run_id
    out.mkdir(parents=True, exist_ok=False)
    input_paths: set[Path] = {
        args.config,
        study_cfg_path,
        reference_study_path,
        fit_structure_config_path,
        fit_structure_script_path,
        engineering_path,
        Path(__file__).resolve().relative_to(Path.cwd()),
        Path("src/analysis/thermal_topology.py"),
        Path("src/analysis/thermal_radial.py"),
        Path("src/analysis/engineering.py"),
        Path("src/vehicle/mass.py"),
        Path("src/vehicle/schema.py"),
        Path("src/cad/parts.py"),
        Path("src/vehicle/materials.py"),
    }
    vehicles = []
    for path in paths:
        input_paths.update(vehicle_input_paths(path))
        vehicles.append((path, load_vehicle(path)))
    hashes = {
        path.resolve()
        .relative_to(Path.cwd())
        .as_posix(): hashlib.sha256(path.read_bytes())
        .hexdigest()
        for path in sorted(input_paths)
    }
    for _, vehicle in vehicles:
        hashes.update(source_hashes(vehicle))

    cells = 16 if args.preset == "tiny" else 24
    scenario_results: list[dict[str, Any]] = []

    def evaluate(
        vehicle: Any,
        mode_name: str,
        case_name: str,
        scenario: int,
        ambient: float,
        peak: float | None = None,
    ) -> dict[str, Any]:
        row = solve_case(
            vehicle, cfg, study, scenario, ambient, case_peak_override_c=peak, cells=cells
        )
        row.update({"mode": mode_name, "evaluation": case_name, "case_peak_override_c": peak})
        return row

    # Exact original 35 C scenario rows remain the frozen-reference baseline.
    for _, vehicle in vehicles:
        for scenario in range(4):
            scenario_results.append(
                evaluate(vehicle, vehicle.id, "original_35C_reference", scenario, 35.0)
            )

    # Preserve the declared lower boundary exactly: 15 C ambient, 120 C case,
    # and its configured cooling history, across all four configurations.
    for _, vehicle in vehicles:
        scenario_results.append(
            evaluate(
                vehicle,
                vehicle.id,
                "lower_case_15C_120C_reference",
                0,
                15.0,
            )
        )

    # Hold the harsh 300 C case history and 120 s tau while raising outer foil
    # emissivity to 0.9. This combines source and contamination bounds explicitly.
    contaminated_scenario = 3
    for _, vehicle in vehicles:
        scenario_results.append(
            evaluate(
                vehicle,
                vehicle.id,
                "300C_case_eps0.9_at_35C",
                contaminated_scenario,
                35.0,
                peak=300.0,
            )
        )

    # Combined case at a candidate 25 C ambient, separately reported for every
    # vehicle. This is an operating-envelope probe, not a changed source case.
    for _, vehicle in vehicles:
        scenario_results.append(
            evaluate(
                vehicle,
                vehicle.id,
                "combined_300C_eps0.9_at25C",
                contaminated_scenario,
                25.0,
                peak=300.0,
            )
        )

    g54 = next(vehicle for _, vehicle in vehicles if "g54" in vehicle.id.lower())
    for ambient in study_cfg["conditional_ambient_points_c"]:
        for scenario in [2, 3]:
            scenario_results.append(
                evaluate(
                    g54,
                    g54.id,
                    f"conditional_{ambient:g}C",
                    scenario,
                    float(ambient),
                    peak=300.0 if scenario == 3 else None,
                )
            )

    # Find the highest ambient retaining the requested 3 K margin for both the
    # existing 300 C/epsilon=.3 and combined 300 C/epsilon=.9 sensitivities.
    search = study_cfg["ambient_search"]
    searches = []
    for target_margin in [0.0, float(search["target_margin_k"])]:
        low = float(search["lower_c"])
        high = float(search["upper_c"])
        search_trace = []
        for iteration in range(int(search["iterations"])):
            midpoint = (low + high) / 2
            rows = [
                evaluate(
                    g54,
                    g54.id,
                    f"ambient_search_{target_margin:g}K_iteration_{iteration + 1}",
                    scenario,
                    midpoint,
                    peak=300.0 if scenario == 3 else None,
                )
                for scenario in search["scenarios"]
            ]
            worst_peak = max(float(row["aft_shell_peak_c"]) for row in rows)
            margin = float(study_cfg["fixed_screen_limit_c"]) - worst_peak
            passed_target_margin = margin >= target_margin
            search_trace.append(
                {
                    "ambient_c": midpoint,
                    "rows": rows,
                    "worst_peak_c": worst_peak,
                    "screen_margin_k": margin,
                    "target_margin_k": target_margin,
                    "target_margin_met": passed_target_margin,
                }
            )
            if passed_target_margin:
                low = midpoint
            else:
                high = midpoint
        searches.append(
            {
                "search_interval_c": [float(search["lower_c"]), float(search["upper_c"])],
                "iterations": int(search["iterations"]),
                "estimated_max_ambient_c": low,
                "target_margin_k": target_margin,
                "screen_limit_c": float(study_cfg["fixed_screen_limit_c"]),
                "cases": ["scenario 2: 300 C, eps=.3", "scenario 3 override: 300 C, eps=.9"],
                "trace": search_trace,
            }
        )
    search_summary = {
        "max_ambient_at_zero_margin_c": searches[0]["estimated_max_ambient_c"],
        "max_ambient_at_target_margin_c": searches[1]["estimated_max_ambient_c"],
        "target_margin_k": float(search["target_margin_k"]),
        "screen_limit_c": float(study_cfg["fixed_screen_limit_c"]),
        "searches": searches,
    }

    heat_flow_rows = []
    heat_flow_cases: list[dict[str, Any]] = [
        {"id": "lower_case_15C_120C", "scenario": 0, "peak_override_c": None},
        {"id": "upper_hot_soak_250C_eps0.3", "scenario": 1, "peak_override_c": None},
        {"id": "case_300C_eps0.3", "scenario": 2, "peak_override_c": None},
        {"id": "contaminated_250C_eps0.9", "scenario": 3, "peak_override_c": None},
        {"id": "combined_300C_eps0.9", "scenario": 3, "peak_override_c": 300.0},
        {
            "id": "combined_300C_eps0.9_at25C_candidate_ambient",
            "scenario": 3,
            "peak_override_c": 300.0,
            "ambient_override_c": 25.0,
        },
    ]
    for topology_name in ["baseline", "remove_mount_shell_lumped_contact"]:
        heat_study = copy.deepcopy(study)
        if topology_name == "remove_mount_shell_lumped_contact":
            heat_study["contact_pairs"] = [
                pair
                for pair in heat_study["contact_pairs"]
                if set(pair) != {"motor_mount", "aft_shell"}
            ]
        for case in heat_flow_cases:
            case_cfg = copy.deepcopy(cfg)
            scenario = int(case["scenario"])
            if case["peak_override_c"] is not None:
                case_cfg["thermal"]["external_case_peak_c"][scenario] = float(
                    case["peak_override_c"]
                )
            if case.get("ambient_override_c") is not None:
                case_cfg["thermal"]["ambient_c"][scenario] = float(case["ambient_override_c"])
            thermal_output = run_thermal_topology(
                g54,
                case_cfg,
                heat_study,
                False,
                cells=cells,
                scenario_index=scenario,
            )
            shell_peak_row = next(
                row for row in thermal_output["peaks"] if row["part_id"] == "aft_shell"
            )
            flows = thermal_output["heat_flow"]
            mount_shell = next(
                (
                    item
                    for item in flows["connections"]
                    if item["connection"] == "lumped_contact:motor_mount->aft_shell"
                ),
                None,
            )
            heat_flow_rows.append(
                {
                    "mode": g54.id,
                    "topology": topology_name,
                    "case": case["id"],
                    "case_peak_c": thermal_output["prescribed_case_peak_c"],
                    "ambient_c": thermal_output["ambient_c"],
                    "cooling_tau_s": thermal_output["post_burn_cooling_tau_s"],
                    "aft_shell_peak_c": shell_peak_row["peak_c"],
                    "aft_shell_screen_margin_k": shell_peak_row["margin_k"],
                    "mount_shell_contact_status": ("absent" if mount_shell is None else "present"),
                    "mount_shell_contact_energy_from_mount_to_shell_j": (
                        None if mount_shell is None else mount_shell["net_energy_j"]
                    ),
                    "mount_shell_contact_energy_extracted_from_shell_to_mount_j": (
                        None if mount_shell is None else mount_shell["negative_energy_j"]
                    ),
                    "aft_shell_temperature_at_peak_c": shell_peak_row["peak_c"],
                    "motor_mount_temperature_at_shell_peak_c": float(
                        np.asarray(thermal_output["temperature_k"])[
                            int(
                                np.argmin(
                                    np.abs(
                                        np.asarray(thermal_output["times_s"])
                                        - shell_peak_row["peak_time_s"]
                                    )
                                )
                            ),
                            thermal_output["part_ids"].index("motor_mount"),
                        ]
                        - 273.15
                    ),
                    "shell_peak_connection_flows": [
                        {
                            "connection": edge["connection"],
                            "source": edge["source"],
                            "target": edge["target"],
                            "flux_at_shell_peak_time_w": edge["flux_w_by_time"][
                                int(
                                    np.argmin(
                                        np.abs(
                                            np.asarray(flows["times_s"])
                                            - shell_peak_row["peak_time_s"]
                                        )
                                    )
                                )
                            ],
                            "net_energy_j": edge["net_energy_j"],
                        }
                        for edge in flows["connections"]
                        if "aft_shell" in edge["source"] or "aft_shell" in edge["target"]
                    ],
                    "heat_flow": flows,
                }
            )

    package_a_rows = []
    bond_cfg = study_cfg["mount_shell_bond"]
    bond_variants: list[dict[str, Any]] = [
        {"id": "open_gap", "gap_m": 0.0005, "conductivity_w_m_k": None},
        {"id": "bond_low_conductance_bound", "gap_m": 0.00068, "conductivity_w_m_k": 0.15},
        {"id": "bond_nominal", "gap_m": 0.0005, "conductivity_w_m_k": 0.20},
        {"id": "bond_high_conductance_bound", "gap_m": 0.00032, "conductivity_w_m_k": 0.25},
    ]
    reference_case_names = [
        "lower_case_15C_120C_reference",
        "original_35C_reference",
        "original_35C_reference",
        "original_35C_reference",
        "300C_case_eps0.9_at_35C",
        "combined_300C_eps0.9_at25C",
    ]
    for reference_vehicle in [vehicle for _, vehicle in vehicles]:
        if (
            "g54" not in reference_vehicle.id.lower()
            and "performance" not in reference_vehicle.id.lower()
        ):
            continue
        for variant in bond_variants:
            profile_key = f"thermal_correction_mount_bond_{variant['id']}"
            if variant["conductivity_w_m_k"] is None:
                candidate = reconciled_fit_candidate(reference_vehicle, fit_package)
                bonds: list[Part] = []
                bond_geometry = None
            else:
                candidate, bonds, bond_geometry = reconciled_bonded_candidate(
                    reference_vehicle,
                    fit_package,
                    {**bond_cfg, "thermal_profile_key": profile_key},
                    float(variant["conductivity_w_m_k"]),
                    float(variant["gap_m"]),
                )
            candidate_mount = next(part for part in candidate.parts if part.id == "motor_mount")
            candidate_shell = next(part for part in candidate.parts if part.id == "aft_shell")
            assert candidate_mount.cad and candidate_mount.cad_mass
            candidate_study = copy.deepcopy(study)
            removed_pairs = [
                pair
                for pair in candidate_study["contact_pairs"]
                if set(pair) == {"motor_mount", "aft_shell"}
            ]
            candidate_study["contact_pairs"] = [
                pair
                for pair in candidate_study["contact_pairs"]
                if set(pair) != {"motor_mount", "aft_shell"}
            ]
            if bonds:
                candidate_study["part_ids"].extend(part.id for part in bonds)
                candidate_study["pad_conduction_part_ids"].extend(part.id for part in bonds)
                candidate_study.setdefault("pad_conduction_thickness_m", {}).update(
                    {part.id: float(variant["gap_m"]) for part in bonds}
                )
                candidate_study["required_case_coupled_part_ids"].extend(part.id for part in bonds)
                interface_g = float(bond_cfg["interface_conductance_w_k"])
                for bond in bonds:
                    candidate_study["contact_pairs"].extend(
                        [["motor_mount", bond.id], [bond.id, "aft_shell"]]
                    )
                    candidate_study.setdefault("contact_pair_conductance_w_k", {})[
                        f"motor_mount->{bond.id}"
                    ] = [interface_g] * 4
                    candidate_study["contact_pair_conductance_w_k"][f"{bond.id}->aft_shell"] = [
                        interface_g
                    ] * 4
            candidate_cases = []
            for case_index, case in enumerate(heat_flow_cases):
                scenario = int(case["scenario"])
                case_cfg = copy.deepcopy(cfg)
                if bonds:
                    profile = copy.deepcopy(cfg["materials"]["epoxy"])
                    conductivity = float(variant["conductivity_w_m_k"])
                    profile["conductivity_w_m_k"] = conductivity
                    profile["conductivity_range_w_m_k"] = [conductivity, conductivity]
                    case_cfg["materials"][profile_key] = profile
                if case["peak_override_c"] is not None:
                    case_cfg["thermal"]["external_case_peak_c"][scenario] = float(
                        case["peak_override_c"]
                    )
                if case.get("ambient_override_c") is not None:
                    case_cfg["thermal"]["ambient_c"][scenario] = float(case["ambient_override_c"])
                thermal_output = run_thermal_topology(
                    candidate,
                    case_cfg,
                    candidate_study,
                    False,
                    cells=cells,
                    scenario_index=scenario,
                    heat_flow_step_s=0.02,
                )
                shell_row = next(
                    row for row in thermal_output["peaks"] if row["part_id"] == "aft_shell"
                )
                reference_row = next(
                    row
                    for row in scenario_results
                    if row["mode"] == reference_vehicle.id
                    and row["evaluation"] == reference_case_names[case_index]
                    and row["scenario_index"] == scenario
                    and (case_index not in (4, 5) or row["prescribed_case_peak_c"] == 300.0)
                )
                candidate_cases.append(
                    {
                        "case": case["id"],
                        "case_peak_c": thermal_output["prescribed_case_peak_c"],
                        "ambient_c": thermal_output["ambient_c"],
                        "cooling_tau_s": thermal_output["post_burn_cooling_tau_s"],
                        "reference_aft_shell_peak_c": reference_row["aft_shell_peak_c"],
                        "candidate_aft_shell_peak_c": shell_row["peak_c"],
                        "delta_aft_shell_peak_c": shell_row["peak_c"]
                        - float(reference_row["aft_shell_peak_c"]),
                        "screen_limit_c": shell_row["screen_limit_c"],
                        "screen_margin_k": shell_row["margin_k"],
                        "part_peaks": thermal_output["peaks"],
                        "energy_residual_j": thermal_output["energy_residual_j"],
                        "max_abs_node_balance_residual_j": thermal_output["heat_flow"][
                            "maximum_abs_node_balance_residual_fine_j"
                        ],
                        "heat_flow": thermal_output["heat_flow"],
                    }
                )
            package_a_rows.append(
                {
                    "mode": reference_vehicle.id,
                    "candidate": "Package A braced fixed mount",
                    "thermal_variant": variant["id"],
                    "reference_resolved_identity_sha256": hashlib.sha256(
                        reference_vehicle.model_dump_json(by_alias=True).encode()
                    ).hexdigest(),
                    "candidate_resolved_identity_sha256": hashlib.sha256(
                        candidate.model_dump_json(by_alias=True).encode()
                    ).hexdigest(),
                    "mount_geometry": {
                        "outer_radius_m": float(candidate_mount.geometry["radius_m"]),
                        "shell_inner_radius_m": float(candidate_shell.geometry["inner_radius_m"]),
                        "radial_gap_m": float(
                            candidate_shell.geometry["inner_radius_m"]
                            - candidate_mount.geometry["radius_m"]
                        ),
                        "ring_stations_mm": candidate_mount.cad.parameters["ring_stations_mm"],
                        "ring_thicknesses_mm": candidate_mount.cad.parameters[
                            "ring_thicknesses_mm"
                        ],
                        "cad_volume_m3": candidate_mount.cad_mass.volume_m3,
                        "cad_shape_sha256": candidate_mount.cad_mass.shape_sha256,
                        "reconciled_mount_mass_kg": candidate_mount.resolved_mass_kg,
                    },
                    "bond_geometry": bond_geometry,
                    "mass_cg_inertia_delta": mass_delta(reference_vehicle, candidate),
                    "candidate_thermal_topology_removed_pairs": removed_pairs,
                    "bond_topology_pairs": [["motor_mount", part.id] for part in bonds]
                    + [[part.id, "aft_shell"] for part in bonds],
                    "bond_model_basis": (
                        "No bond: open 0.5 mm radial gap"
                        if not bonds
                        else "Per-ring CAD bond area with fin-slot cuts; epoxy node heat capacity and two half-thickness conduction resistances; high interface conductance is an ideal-wetted assumption, not peel/shear qualification."
                    ),
                    "bond_material_assumptions": {
                        "conductivity_w_m_k": variant["conductivity_w_m_k"],
                        "conductivity_bounds_w_m_k": bond_cfg["conductivity_range_w_m_k"],
                        "density_kg_m3": bond_cfg["density_kg_m3"],
                        "specific_heat_j_kg_k": cfg["materials"]["epoxy"]["cp_j_kg_k"],
                        "radial_gap_bounds_m": bond_cfg["radial_gap_bounds_m"],
                        "interface_conductance_w_k": bond_cfg["interface_conductance_w_k"],
                        "fillet_allowance_included": False,
                    },
                    "cases": candidate_cases,
                    "active_adoption": False,
                    "thermal_acceptance_passed": False,
                    "flight_ready": False,
                }
            )

    # CAD mass-only skin rows. The skin has real fin slots and exact cut geometry;
    # no thermal result is fabricated because the radial model would seal those slots.
    skin_rows = []
    for _, vehicle in vehicles:
        for thickness in study_cfg["skin"]["thicknesses_m"]:
            skin_rows.append(
                {
                    "mode": vehicle.id,
                    "reference_identity_sha256": hashlib.sha256(
                        vehicle.model_dump_json(by_alias=True).encode()
                    ).hexdigest(),
                    **skin_mass_sensitivity(vehicle, study_cfg["skin"], float(thickness)),
                    "thermal_properties_screen": {
                        "density_range_kg_m3": study_cfg["skin"]["density_range_kg_m3"],
                        "conductivity_range_w_m_k": study_cfg["skin"]["conductivity_range_w_m_k"],
                        "cp_range_j_kg_k": study_cfg["skin"]["cp_range_j_kg_k"],
                        "nominal_k_w_m_k": study_cfg["skin"]["nominal_conductivity_w_m_k"],
                        "nominal_cp_j_kg_k": study_cfg["skin"]["nominal_cp_j_kg_k"],
                        "basis": "user-requested estimate ranges; not yet matched to an exact thin wet-layup laminate TDS",
                    },
                }
            )

    detail = {
        "scenario_results": scenario_results,
        "ambient_search": search_summary,
        "g54_connection_heat_flows": heat_flow_rows,
        "package_a_braced_fixed_mount_thermal_comparison": package_a_rows,
        "package_a_vehicle_applicability": [
            {
                "mode": vehicle.id,
                "status": (
                    "evaluated_fixed_mount_candidate"
                    if not vehicle.tvc
                    else "not_applicable_to_tvc_motor_cassette"
                ),
                "reason": (
                    "Package A changes the discrete fixed-mount rings and shell bond gap."
                    if not vehicle.tvc
                    else "TVC mode uses a cassette and rails rather than the discrete fixed mount; applying Package A ring changes would not represent its hardware."
                ),
            }
            for _, vehicle in vehicles
        ],
        "heat_flow_units": {
            "instantaneous_connection_flow": "W",
            "integrated_connection_energy": "J",
            "temperature": "K",
            "time": "s",
            "sign": "positive source to target; negative energy is reverse-flow magnitude",
        },
        "skin_mass_geometry_rows": skin_rows,
        "source_case_assumptions": {
            "ambient_reference_c": 35.0,
            "scenario2": {"case_peak_c": 300.0, "tau_s": 120.0, "outer_foil_emissivity": 0.3},
            "scenario3_original": {
                "case_peak_c": 250.0,
                "tau_s": 120.0,
                "outer_foil_emissivity": 0.9,
            },
            "scenario3_combined_sensitivity": {
                "case_peak_c": 300.0,
                "tau_s": 120.0,
                "outer_foil_emissivity": 0.9,
            },
            "screen_limit_c": float(study_cfg["fixed_screen_limit_c"]),
        },
        "skin_thermal_simulation": "withheld: annular thermal solver would make slotted skin a false continuous opaque barrier",
    }
    detail_path = out / "candidate-results.json"
    detail_bytes = encoded_json(detail)
    detail_path.write_bytes(detail_bytes)
    record = {
        "run_id": run_id,
        "preset": args.preset,
        "study_config": str(study_cfg_path),
        "reference_topology_config": str(reference_study_path),
        "source_inputs": hashes,
        "inputs_unchanged": all(
            hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest
            for path, digest in hashes.items()
        ),
        "modes_count": len(vehicles),
        "scenario_result_count": len(scenario_results),
        "skin_mass_geometry_rows_count": len(skin_rows),
        "ambient_search": {
            "max_ambient_at_zero_margin_c": search_summary["max_ambient_at_zero_margin_c"],
            "max_ambient_at_target_margin_c": search_summary["max_ambient_at_target_margin_c"],
            "target_margin_k": search_summary["target_margin_k"],
            "screen_limit_c": search_summary["screen_limit_c"],
            "search_interval_c": [float(search["lower_c"]), float(search["upper_c"])],
            "iterations_per_target": int(search["iterations"]),
        },
        "detail_artifact": str(detail_path),
        "detail_artifact_sha256": hashlib.sha256(detail_bytes).hexdigest(),
        "active_adoption": False,
        "thermal_acceptance_passed": False,
        "flight_ready": False,
        "cost_usd": 0,
        "limitations": study_cfg["limitations"],
    }
    record_path = out / "record.json"
    record_path.write_bytes(encoded_json(record))
    print("record", record_path)
    print("inputs_unchanged", record["inputs_unchanged"])
    print("ambient_search_max_c_zero_margin", search_summary["max_ambient_at_zero_margin_c"])
    print("ambient_search_max_c_target_margin", search_summary["max_ambient_at_target_margin_c"])
    print("record_sha256", hashlib.sha256(record_path.read_bytes()).hexdigest())
    print("candidate_results_sha256", record["detail_artifact_sha256"])
    return 0 if record["inputs_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
