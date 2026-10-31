"""Map actual fluid boundary faces to material paths; never solve temperatures.

Fourier plane-wall R=delta/(k*A), cylinder R=abs(log(r_s/r_b))/(k*phi*L).
Consequently a cylinder's area-based Robin h=k/(r_s*abs(log(r_s/r_b))).
Reference: DOE-HDBK-1012/2-92, HT-02 pp. 7-15, conduction heat transfer,
https://www.energy.gov/documents/doe-hdbk-1012-92vol2 . These are solid
half-wall coefficients, NOT an extra gas-film coefficient. Radiation and the
Robin gas trace use the SAME physical surface temperature. Local normal-chord
samples on complex geometry are diagnostic lengths, not qualified bulk paths.
"""

from __future__ import annotations

import os
from pathlib import Path

for _name in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
    os.environ[_name] = "1"
os.environ.setdefault("XDG_CACHE_HOME", str(Path(__file__).resolve().parents[1] / ".cache"))

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from itertools import pairwise
from typing import Any

import cadquery as cq
import numpy as np
import yaml
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cylindrical_delta(surface_radius_m: float, bulk_radius_m: float) -> float:
    """Area-specific exact cylindrical half resistance, multiplied by k."""
    if min(surface_radius_m, bulk_radius_m) <= 0 or surface_radius_m == bulk_radius_m:
        raise ValueError("Ordered positive distinct surface/bulk radii required")
    return surface_radius_m * abs(math.log(surface_radius_m / bulk_radius_m))


def liner_end_strips(ri: float, ro: float, length: float, cells: int) -> list[dict[str, Any]]:
    """Explicit per-radial-FV axial paths; no average material temperature."""
    if not (0 < ri < ro and length > 0 and cells >= 1):
        raise ValueError("Positive ordered liner geometry and cells required")
    radii = np.linspace(ri, ro, cells + 1)
    return [
        {
            "material_state_id": f"motor_liner.cell_{i}",
            "radial_interval_m": [float(a), float(b)],
            "area_m2": float(math.pi * (b * b - a * a)),
            "delta_halfwall_m": length / 2,
            "h_over_k_per_m": 2 / length,
            "surface_region": "this radial strip on this physical end only",
        }
        for i, (a, b) in enumerate(pairwise(radii))
    ]


def component_at(
    solids: list[Any], point: list[float], normal: list[float], offsets: list[float], tol: float
) -> int:
    """Require unique, consistent material-side component ownership at face interior."""
    owners = []
    for offset in offsets:
        probe = cq.Vector(*(np.asarray(point) + offset * np.asarray(normal)))
        hits = [i for i, solid in enumerate(solids) if solid.isInside(probe, tol)]
        if len(hits) != 1:
            raise ValueError(f"Nonunique interior component ownership: {hits}")
        owners.append(hits[0])
    if len(set(owners)) != 1:
        raise ValueError("Material-side component changes with probe distance")
    return owners[0]


def normal_chord(solid: Any, point: list[float], normal: list[float], maximum: float) -> Any:
    """First actual material-exit distance along the gas-outward normal, in mm."""
    hit = IntCurvesFace_ShapeIntersector()
    hit.Load(solid.wrapped, 1e-8)
    hit.Perform(gp_Lin(gp_Pnt(*point), gp_Dir(*normal)), 0, maximum)
    distances = sorted(hit.WParameter(i) for i in range(1, hit.NbPnt() + 1))
    positive = [value for value in distances if value > 1e-5]
    if not positive:
        return None
    distance = positive[0]
    # A normal may run tangent to another face at a trimmed corner. A sample
    # must stay inside this SAME solid all the way to the proposed first exit.
    for fraction in [0.001, 0.25, 0.5, 0.75, 0.999]:
        p = np.asarray(point) + fraction * distance * np.asarray(normal)
        if not solid.isInside(cq.Vector(*p), 1e-7):
            return None
    return float(distance)


def property_bounds(profile: dict[str, Any], material: str) -> dict[str, Any]:
    k = profile.get("conductivity_w_m_k")
    if k is None:
        return {"nominal_w_m_k": None, "bounds_w_m_k": None, "basis": "unavailable"}
    bounds = profile.get("conductivity_range_w_m_k")
    if bounds is None:
        bounds = [0.15, 0.25] if material == "epoxy" else [0.7 * k, 1.3 * k]
        basis = "existing coherent sensitivity factors; epoxy existing gap-k bounds"
    else:
        basis = "explicit existing profile range takes precedence over coherent factors"
    return {"nominal_w_m_k": k, "bounds_w_m_k": bounds, "basis": basis}


def recipe_path(
    part: dict[str, Any], family: dict[str, Any], face: dict[str, Any], cells: int
) -> dict[str, Any]:
    """Return an explicit recipe-based half path or named unavailable reason."""
    name, geom = part["id"], part["geometry"]
    generator = part["cad"]["generator"]
    kind = family["kind"]
    axial = kind == "PLANE" and abs(family["normal"][2]) > 0.999999
    ri, ro, length = geom.get("inner_radius_m"), geom.get("radius_m"), geom["length_m"]
    radius = family.get("radius_mm", 0) / 1000
    if name == "motor_liner":
        if kind == "CYLINDER":
            radii = np.linspace(ri, ro, cells + 1)
            if math.isclose(radius, ri, abs_tol=1e-9):
                index = 0
            elif math.isclose(radius, ro, abs_tol=1e-9):
                index = cells - 1
            else:
                return {"available": False, "reason": "liner cylinder radius not a FV boundary"}
            mid = math.sqrt(radii[index] * radii[index + 1])
            return {
                "available": True,
                "method": "exact cylindrical radial-FV half resistance",
                "delta_m": cylindrical_delta(radius, mid),
                "bulk_state_override": f"motor_liner.cell_{index}",
                "bulk_radius_m": mid,
            }
        if axial:
            return {
                "available": True,
                "method": "radial strip at each boundary quadrature point to corresponding radial FV bulk cell",
                "delta_m": length / 2,
                "requires_radial_strip_integration": True,
                "axial_resolution": "one axial cell, half-length L/2; coarse hypothesis, not convergence",
                "explicit_axial_FV_paths": liner_end_strips(ri, ro, length, cells),
                "whole_end_material_temperature_average": None,
            }
    simple_tube = generator in {"liner", "tube", "sector_pads"} or name.startswith(
        "mount_shell_bond_"
    )
    if simple_tube and ri is not None:
        if kind == "CYLINDER" and any(
            math.isclose(radius, value, abs_tol=1e-9) for value in [ri, ro]
        ):
            mid = math.sqrt(ri * ro)
            return {
                "available": True,
                "method": "exact cylindrical radial half resistance to geometric-mean bulk radius",
                "delta_m": cylindrical_delta(radius, mid),
                "bulk_radius_m": mid,
                "approximation": "uniform bulk state for this connected component; no spatial hotspot bound",
            }
        if axial:
            return {
                "available": True,
                "method": "actual physical axial thickness /2",
                "delta_m": length / 2,
                "approximation": "uniform component bulk state at axial midplane",
            }
        if generator == "sector_pads" and kind == "PLANE":
            angle = math.radians(part["cad"]["parameters"]["sector_angle_deg"]) / 2
            r = math.hypot(*face["ownership_interior_point_mm"][:2]) / 1000
            return {
                "available": False,
                "reason": "sector side spans a clipped outer corner; no single resolved halfwall-to-bulk map over the entire physical face",
                "conditional_sample_method": "normal from actual side point to sector bisector: r*tan(half sector angle)",
                "conditional_sample_delta_m": r * math.tan(angle),
                "unclipped_radial_interval_m": [ri, ro * math.cos(angle)],
                "outer_corner_requires_local_2D_or_medial_solid_map": True,
                "conditional_sample_path_inside_solid": r <= ro * math.cos(angle),
                "requires_spatial_h": True,
            }
    return {
        "available": False,
        "reason": "complex rail/notch/tab/hole/fastener region lacks qualified local bulk-state and spreading map; sampled chord is not that map",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/studies/wo03-surface-materials.yaml")
    args = parser.parse_args()
    os.chdir(ROOT)
    started = time.monotonic()
    cfg = yaml.safe_load(Path(args.config).read_text())
    snapshots = {
        str(Path(args.config)): sha(Path(args.config)),
        str(Path(__file__).relative_to(ROOT)): sha(Path(__file__)),
    }
    for key, expected in cfg["expected_sha256"].items():
        p = Path(cfg[key])
        if sha(p) != expected:
            raise ValueError(f"Pinned input changed: {key}")
        snapshots[str(p)] = expected
    handoff = json.loads(Path(cfg["handoff"]).read_text())
    historical_method_dependencies = {}
    for path, expected in handoff["files_sha256"].items():
        if path.startswith("src/"):
            historical_method_dependencies[path] = {
                "handoff_declared_sha256": expected,
                "current_sha256": sha(Path(path)),
                "imported_or_used_by_this_mapping": False,
            }
            continue
        if sha(Path(path)) != expected:
            raise ValueError(f"Handoff input changed: {path}")
        snapshots[path] = expected
    report = json.loads(Path(handoff["source_record"]).read_text())
    snapshots[handoff["source_record"]] = sha(Path(handoff["source_record"]))
    if report["candidate_identity"] != handoff["candidate_identity"]:
        raise ValueError("Candidate identities disagree")
    boundary_dir = Path(cfg["handoff"]).parent
    faces = json.loads((boundary_dir / "face-inventory.json").read_text())
    groups = json.loads((boundary_dir / "surface-groups.json").read_text())
    if len(faces) != 1785 or len(groups) != 1127:
        raise ValueError("Unexpected frozen boundary inventory")
    by_face = {face_id: group for group in groups for face_id in group["fluid_face_ids"]}
    if len(by_face) != len(faces) or sum(len(g["fluid_face_ids"]) for g in groups) != len(faces):
        raise ValueError("Boundary face coverage is missing or duplicated")
    parts = {p["id"]: p for p in json.loads(Path(cfg["candidate"]).read_text())["parts"]}
    manifest = {p["part_id"]: p for p in json.loads(Path(cfg["manifest"]).read_text())}
    materials = yaml.safe_load(Path(cfg["engineering"]).read_text())["materials"]
    topology = yaml.safe_load(Path(cfg["existing_topology"]).read_text())
    old_states = set(topology["part_ids"])
    old_states |= {
        name
        for name in parts
        if name.startswith(("additional_shield_", "shield_spacer_", "mount_shell_bond_"))
    }
    output = (
        ROOT / "runs" / ("wo03-surface-materials-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"))
    )
    output.mkdir(parents=True)
    components: dict[str, list[Any]] = {}
    component_table = []
    symmetry_tests = []
    for name in sorted({f["part_id"] for f in faces if not f["reservoir"]}):
        m = manifest[name]
        p = Path(cfg["manifest"]).parent / m["step"]
        if sha(p) != m["step_sha256"]:
            raise ValueError(f"Actual placed STEP changed: {name}")
        snapshots[str(p)] = m["step_sha256"]
        shape = cq.importers.importStep(str(p)).val()
        if abs(shape.Volume() - m["volume_m3"] * 1e9) > max(1e-6, 1e-7 * shape.Volume()):
            raise ValueError(f"Actual placed volume mismatch: {name}")
        solids = sorted(shape.Solids(), key=lambda s: (*s.Center().toTuple(), s.Volume()))
        components[name] = solids
        if name in cfg["symmetry_test_part_ids"]:
            rotated = shape.rotate((0, 0, 0), (0, 0, 1), 120)
            difference = shape.cut(rotated).Volume() + rotated.cut(shape).Volume()
            symmetry_tests.append(
                {
                    "part_id": name,
                    "rotation_deg": 120,
                    "BRep_symmetric_difference_mm3": difference,
                    "tolerance_mm3": cfg["symmetry_test_volume_tolerance_mm3"],
                    "part_geometry_test_passed": difference
                    <= cfg["symmetry_test_volume_tolerance_mm3"],
                    "same_declared_material_profile_for_components": True,
                    "independent_manufacture_equivalent": None,
                    "full_domain_boundaries_and_all_inputs_symmetry_verified": False,
                    "shared_temperature_approved": False,
                }
            )
        for i, solid in enumerate(solids):
            component_table.append(
                {
                    "part_id": name,
                    "component_id": f"{name}.component_{i}",
                    "volume_m3": solid.Volume() * 1e-9,
                    "volume_fraction": solid.Volume() / shape.Volume(),
                    "homogeneous_part_capacity_fraction_proposal": solid.Volume() / shape.Volume(),
                    "center_CAD_mm": list(solid.Center().toTuple()),
                    "separate_BRep_solid_not_proof_of_thermal_disconnect": True,
                    "same_part_source_bulk_state": name if name in old_states else None,
                    "shared_component_temperature_approved": len(solids) == 1,
                    "threefold_symmetry_may_be_hypothesis": len(solids) == 3,
                }
            )
    rows = []
    for face in faces:
        name = face["part_id"]
        group = by_face[face["fluid_face_id"]]
        row = {
            **face,
            "radiation_group_id": group["group_id"],
            "physical_surface_family": group["physical_surface_family"],
        }
        row["shared_gas_solid_surface_temperature"] = True
        row["radiation_same_surface_temperature"] = True
        if face["reservoir"]:
            row.update(
                mapping_kind="external_opening",
                gas_temperature_id=cfg["opening_gas_temperature_ids"][name],
                radiative_brightness_id=cfg["opening_brightness_ids"][name],
                gas_and_brightness_temperatures_implicitly_equal=False,
                boundary_values_available=False,
                halfwall=None,
                material=None,
            )
            rows.append(row)
            continue
        part = parts[name]
        profile_id = part["engineering"]["material_profile"]
        row.update(
            material=part["material"],
            material_profile=profile_id,
            conductivity=property_bounds(materials[profile_id], profile_id),
        )
        component = component_at(
            components[name],
            face["ownership_interior_point_mm"],
            face["void_outward_normal"],
            cfg["component_probe_offsets_mm"],
            cfg["geometry_tolerance_mm"],
        )
        component_id = f"{name}.component_{component}"
        row.update(
            component_id=component_id,
            source_part_bulk_state=name if name in old_states else None,
            proposed_separate_bulk_state=component_id if len(components[name]) > 1 else name,
            shared_bulk_temperature_approved=len(components[name]) == 1,
        )
        if name == "motor":
            family = group["physical_surface_family"]
            which = (
                "cylinder"
                if family["kind"] == "CYLINDER"
                else "fore_end" if face["ownership_interior_point_mm"][2] < 1100 else "aft_end"
            )
            row.update(
                mapping_kind="prescribed_motor_surface",
                temperature_id=cfg["motor_temperature_ids"][which],
                halfwall=None,
                source_temperature_available=which == "cylinder",
                exact_measured_motor_temperature_available=False,
                end_closure_nozzle_geometry_and_history_available=False,
            )
            rows.append(row)
            continue
        path = recipe_path(part, group["physical_surface_family"], face, cfg["radial_cells"])
        chord = normal_chord(
            components[name][component],
            face["ownership_interior_point_mm"],
            face["void_outward_normal"],
            cfg["normal_chord_max_mm"],
        )
        row.update(
            mapping_kind=(
                "finite_solid_halfwall" if path["available"] else "unavailable_halfwall_mapping"
            ),
            halfwall=path,
            sampled_normal_material_chord_mm=chord,
            sampled_chord_is_qualified_halfwall=False,
            whole_part_bbox_used=False,
            geometry_tolerance_bounds_available=False,
        )
        if path["available"]:
            delta = path["delta_m"]
            prop = row["conductivity"]
            row.update(
                material_state_id=(
                    None
                    if path.get("requires_radial_strip_integration")
                    else path.get("bulk_state_override", row["proposed_separate_bulk_state"])
                ),
                h_nominal_w_m2_k=prop["nominal_w_m_k"] / delta,
                h_material_bounds_w_m2_k=[k / delta for k in prop["bounds_w_m_k"]],
                face_integrated_G_nominal_w_k=prop["nominal_w_m_k"]
                / delta
                * face["cad_area_mm2"]
                * 1e-6,
                h_is_gas_film_coefficient=False,
            )
            row["requires_new_bulk_state_or_primary_mapping"] = (
                row["material_state_id"] is not None
                and row["material_state_id"] not in old_states
                and not row["material_state_id"].startswith("motor_liner.cell_")
            )
            if path.get("requires_radial_strip_integration"):
                row["mapping_kind"] = "radial_FV_end_strips_coarse_axial_hypothesis"
                row["material_state_ids"] = [
                    p["material_state_id"] for p in path["explicit_axial_FV_paths"]
                ]
                for strip in path["explicit_axial_FV_paths"]:
                    strip["G_nominal_w_k"] = (
                        prop["nominal_w_m_k"] * strip["area_m2"] / strip["delta_halfwall_m"]
                    )
                row["axial_half_length_sensitivity"] = [
                    {
                        "fraction_of_total_length": fraction,
                        "delta_m": fraction * part["geometry"]["length_m"],
                        "whole_end_G_nominal_w_k": prop["nominal_w_m_k"]
                        * face["cad_area_mm2"]
                        * 1e-6
                        / (fraction * part["geometry"]["length_m"]),
                        "interpretation": "alternate penetration/axial discretization hypothesis; requires consistent axial capacity/state refinement before transient, not permission to change h alone",
                    }
                    for fraction in cfg["liner_end_axial_half_length_fractions_of_total_length"]
                ]
        else:
            row.update(material_state_id=None, h_nominal_w_m2_k=None, h_material_bounds_w_m2_k=None)
        rows.append(row)
    grouped = []
    for group in groups:
        subset = [r for r in rows if r["radiation_group_id"] == group["group_id"]]
        ids = sorted({r["component_id"] for r in subset if "component_id" in r})
        states = sorted(
            {
                state
                for r in subset
                for state in (
                    [r["material_state_id"]]
                    if r.get("material_state_id")
                    else r.get("material_state_ids", [])
                )
            }
        )
        grouped.append(
            {
                **group,
                "component_ids": ids,
                "candidate_material_state_ids": states,
                "merges_multiple_BRep_components": len(ids) > 1,
                "surface_temperature_group_is_isothermal": False,
                "single_Robin_bulk_id_loadable": len(states) == 1
                and all((r.get("halfwall") or {}).get("available", False) for r in subset),
                "unavailable_face_ids": [
                    r["fluid_face_id"]
                    for r in subset
                    if r["mapping_kind"] == "unavailable_halfwall_mapping"
                ],
                "area_sum_check_mm2": sum(r["cad_area_mm2"] for r in subset)
                - group["cad_area_mm2"],
            }
        )
    for filename, data in [
        ("face-material-map.json", rows),
        ("group-material-map.json", grouped),
        ("component-state-proposals.json", component_table),
    ]:
        (output / filename).write_text(json.dumps(data, indent=2) + "\n")
    with (output / "connection-table.csv").open("w") as file:
        columns = [
            "fluid_face_id",
            "radiation_group_id",
            "part_id",
            "component_id",
            "material",
            "mapping_kind",
            "material_state_id",
            "cad_area_mm2",
            "h_nominal_w_m2_k",
            "face_integrated_G_nominal_w_k",
            "sampled_normal_material_chord_mm",
        ]
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    summary = []
    for name in sorted({r["part_id"] for r in rows}):
        subset = [r for r in rows if r["part_id"] == name]
        hs = [r["h_nominal_w_m2_k"] for r in subset if r.get("h_nominal_w_m2_k") is not None]
        summary.append(
            {
                "part_id": name,
                "faces": len(subset),
                "groups": len({r["radiation_group_id"] for r in subset}),
                "area_m2": sum(r["cad_area_mm2"] for r in subset) * 1e-6,
                "BRep_solids": len(components.get(name, [])),
                "mapping_kinds": dict(Counter(r["mapping_kind"] for r in subset)),
                "nominal_h_range_w_m2_k": [min(hs), max(hs)] if hs else None,
                "sum_recipe_G_w_k": sum(r.get("face_integrated_G_nominal_w_k", 0) for r in subset),
            }
        )
    result = {
        "run_id": output.name,
        "status": "MAPPING_BLOCKED_BEFORE_TEMPERATURE_SOLVE",
        "candidate_identity": handoff["candidate_identity"],
        "source_cad_revision": handoff["source_cad_revision"],
        "input_sha256": snapshots,
        "inputs_unchanged": all(sha(Path(p)) == v for p, v in snapshots.items()),
        "historical_handoff_method_dependencies_not_used": historical_method_dependencies,
        "face_count": len(rows),
        "radiation_group_count": len(groups),
        "mapping_counts": dict(Counter(r["mapping_kind"] for r in rows)),
        "CAD_boundary_area_mm2_by_mapping_kind": {
            kind: sum(r["cad_area_mm2"] for r in rows if r["mapping_kind"] == kind)
            for kind in sorted({r["mapping_kind"] for r in rows})
        },
        "groups_merging_multiple_BRep_components": sum(
            g["merges_multiple_BRep_components"] for g in grouped
        ),
        "maximum_group_area_residual_mm2": max(abs(g["area_sum_check_mm2"]) for g in grouped),
        "part_connection_summary": summary,
        "selected_actual_120deg_BRep_symmetry_tests": symmetry_tests,
        "physical_feature_thickness_proposals_not_assigned_to_faces": {
            "motor_mount": {
                "source": "candidate motor_mount.cad.parameters; actual imported BRep normal chords in face table",
                "ring_thickness_m": [0.003] * 5,
                "rail_width_depth_m": [0.012, 0.007],
                "retainer_block_stock_m": [0.012, 0.012, 0.020],
                "reason_unavailable": "intersecting rails/rings, channels, holes, pockets, trim and common bulk averaging; local feature axis and material path must be resolved, not whole assembly bbox",
            },
            "retention": {
                "source": "candidate retention.cad.parameters",
                "physical_plate_thickness_m": 0.009,
                "finger_wall_m": 0.002,
                "finger_length_m": 0.018,
                "reason_unavailable": "plate and fingers have different normal half paths and interact with notches; geometry length0.018m is not the plate thickness",
            },
            "aft_retainer": {
                "source": "candidate aft_retainer geometry and actual bolt-hole BRep",
                "plate_thickness_m": 0.004,
                "axial_face_halfwall_candidate_m": 0.002,
                "axial_h_candidate_nominal_w_m2_k": materials["G11"]["conductivity_w_m_k"] / 0.002,
                "reason_unavailable": "axial broad-face candidate can be separately resolved; radial bore/OD/bolt-hole side faces need local spreading map",
            },
            "fin_set": {
                "source": "this G54 candidate native plywood fin_set, not trainer layered-fin study",
                "wood_tab_thickness_m": 0.00635,
                "tab_depth_m": 0.006,
                "root_gusset_base_m": 0.003,
                "reason_unavailable": "fluid sees partial tab/gusset end and side patches; separate fin component bulk states and directional thickness/spreading needed",
            },
            "retention_hardware": {
                "source": "candidate dimensioned purchased pins envelope; not exact supplier hardware geometry",
                "shaft_diameter_m": 0.003,
                "head_diameter_m": 0.0055,
                "head_thickness_m": 0.003,
                "reason_unavailable": "six BRep solids represent three shaft/head assemblies; thermal joining, exact alloy and bulk state grouping require explicit physical identities",
            },
        },
        "liner_end_radial_FV_mapping_available_as_explicit_proposal": True,
        "liner_end_common_surface_approximation_accepted": False,
        "node_ownership_at_material_edges_assigned": False,
        "gas_and_solid_boundary_temperatures_continuous": True,
        "radiation_uses_same_boundary_trace": True,
        "radiation_area_mean_T_is_mean_T4": False,
        "full_nodal_trace_or_true_area_mean_T4_needed_before_radiation_coupling": True,
        "constant_group_radiosity_and_irradiation_is_separate_spatial_approximation": True,
        "existing_solid_contacts_retained_separately": True,
        "parallel_air_support_bookkeeping": handoff["parallel_air_support_bookkeeping"],
        "replace_old_air_estimates_when_actual_gas_domain_covers_them": True,
        "blocked_by": [
            "complex mount/retention/fin/hardware halfwall-to-bulk spreading unresolved",
            "liner annular end radial strip assembly, coarse axial-length sensitivity and radiation grouping unresolved",
            "disconnected component states or justified global symmetry unresolved",
            "opening and motor end temperature inputs unavailable",
            "material/thickness/contact/anisotropy uncertainty unmeasured",
            "actual Robin/radiation surface projection and nodal reconstruction not yet integrated",
        ],
        "temperature_solve_executed": False,
        "thermal_acceptance": False,
        "active_adoption": False,
        "flight_ready": False,
        "cpu_workers": 1,
        "cost_usd": 0,
        "elapsed_s": time.monotonic() - started,
    }
    if not result["inputs_unchanged"]:
        raise ValueError("Inputs changed during mapping; no final record")
    (output / "record.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: result[k]
                for k in [
                    "run_id",
                    "status",
                    "face_count",
                    "mapping_counts",
                    "groups_merging_multiple_BRep_components",
                    "inputs_unchanged",
                    "elapsed_s",
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
