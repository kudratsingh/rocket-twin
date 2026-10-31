"""Prepare checked condensed radiation operators and one ring-baffle diagnostic.

This runner DOES NOT integrate a thermal transient. Radiation and gas conduction
must share correctly coupled unknown physical surface temperatures before a
replacement transient is meaningful. Material-node mappings here are diagnostic.
"""

from __future__ import annotations

import os

for _name in (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "MKL_NUM_THREADS",
):
    os.environ[_name] = "1"

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_finite_radiation import case_temperature_k, geometry_from_record
from src.analysis.finite_radiation import (
    AnnularSolid,
    CondensedRadiation,
    MaterialRadiationAdapter,
    Patch,
    aggregate_view_interval,
    condense_radiosity,
    enclosure_patches,
    radiosity,
    reciprocal_enclosure,
    sample_view_factors,
)
from src.vehicle.cad_contract import digest
from src.vehicle.schema import Part, Vehicle

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-finite-thermal.yaml"


def thermal_node_names(thermal: dict[str, Any]) -> list[str]:
    return [f"motor_liner.cell_{i}" for i in range(thermal["radial_cells"])] + thermal["part_ids"][
        1:
    ]


def patch_temperature_groups(patches: list[Patch], radial_cells: int) -> list[str]:
    """Complete one-patch-to-one-temperature mapping; no unknown material defaults."""
    groups = []
    for patch in patches:
        if patch.part_id == "motor":
            name = "motor_case_boundary"
        elif patch.part_id == "fore_aperture":
            name = "fore_end_reservoir"
        elif patch.part_id == "aft_aperture":
            name = "aft_end_reservoir"
        elif patch.unknown_boundary:
            raise ValueError(f"Unspecified unknown boundary: {patch.part_id}")
        elif patch.part_id == "motor_liner":
            if patch.face == "inner_cylinder":
                name = "motor_liner.cell_0"
            elif patch.face == "outer_cylinder":
                name = f"motor_liner.cell_{radial_cells - 1}"
            else:
                raise ValueError(
                    "A finite liner end face requires its own radial temperature mapping"
                )
        else:
            name = patch.part_id
        groups.append(name)
    return groups


def recorded_ode_temperature(thermal: dict[str, Any], time_index: int) -> np.ndarray:
    return np.array(
        thermal["liner_radial_temperature_k"][time_index] + thermal["temperature_k"][time_index][1:]
    )


def build_material_adapter(
    operator: CondensedRadiation, thermal: dict[str, Any], end_mode: str, provenance: dict[str, Any]
) -> MaterialRadiationAdapter:
    return MaterialRadiationAdapter(
        operator,
        thermal_node_names(thermal),
        {"fore_end_reservoir": end_mode, "aft_end_reservoir": end_mode},
        provenance,
    )


def verify_operator(
    operator: CondensedRadiation, view: Any, areas: Any, emissivities: Any, cfg: dict[str, Any]
) -> dict[str, Any]:
    rng = np.random.default_rng(cfg["random_seed"])
    lo, hi = cfg["arbitrary_temperature_range_k"]
    max_error = 0.0
    max_energy = 0.0
    for _ in range(cfg["random_cases"]):
        temperature = rng.uniform(lo, hi, len(operator.node_names))
        direct = radiosity(view, areas, temperature[operator.patch_node_index], emissivities)
        expected = np.bincount(
            operator.patch_node_index,
            weights=-direct["net_outward_w"],
            minlength=len(operator.node_names),
        )
        actual = operator.heat_rates(temperature)
        max_error = max(max_error, float(np.max(abs(actual - expected))))
        max_energy = max(max_energy, abs(float(sum(actual))))
    isothermal = float(np.max(abs(operator.heat_rates(np.full(len(operator.node_names), 350.0)))))
    matrix = operator.inward_operator_w_k4
    return {
        **operator.checks,
        "random_cases": cfg["random_cases"],
        "arbitrary_temperature_range_k": [lo, hi],
        "max_direct_radiosity_difference_w": max_error,
        "max_total_energy_residual_w": max_energy,
        "isothermal_max_heat_w": isothermal,
        "inward_matrix_max_column_sum_w_k4": float(np.max(abs(matrix.sum(axis=0)))),
        "passed": max_error < cfg["direct_max_error_w"]
        and max_energy < cfg["energy_max_error_w"]
        and isothermal == 0.0,
    }


def load_checked_inputs(cfg: dict[str, Any]) -> tuple[Any, Any, Any, Any, Any, list[Path]]:
    source_path = ROOT / cfg["candidate_source_record"]
    finite_path = ROOT / cfg["finite_source_record"]
    source = json.loads(source_path.read_bytes())
    finite = json.loads(finite_path.read_bytes())
    candidate_path = source_path.parent / "resolved-candidate.json"
    thermal_path = source_path.parent / "thermal-results.json"
    vehicle = Vehicle.model_validate_json(candidate_path.read_bytes())
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    if (
        identity != cfg["expected_candidate_identity"]
        or identity != source["candidate_identity"]
        or identity != finite["candidate_identity"]
    ):
        raise ValueError("Resolved candidate identity mismatch")
    if (
        source["cad_revision_sha256"] != cfg["expected_cad_revision_sha256"]
        or finite["cad_revision_sha256"] != source["cad_revision_sha256"]
    ):
        raise ValueError("CAD source identity mismatch")
    for part in vehicle.parts:
        if (
            digest(part.geometry, part.cad.model_dump() if part.cad else None)
            != source["part_shape_sha256"][part.id]
        ):
            raise ValueError(f"Candidate part identity mismatch: {part.id}")
    for path, expected in finite["input_sha256"].items():
        snapshot = finite_path.parent / "source-snapshot" / path
        if hashlib.sha256(snapshot.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Historical finite source snapshot mismatch: {path}")
    level_name = cfg["finite_source_level"]
    patch_path = finite_path.parent / (level_name + "-patches.json")
    matrix_path = finite_path.parent / (level_name + "-view-factors.npz")
    patches = [
        Patch(**{key: value for key, value in row.items() if key != "area_m2"})
        for row in json.loads(patch_path.read_bytes())
    ]
    with np.load(matrix_path) as stored:
        matrix = {key: stored[key].copy() for key in stored.files}
    if not np.array_equal(matrix["raw_view_factors"], matrix["hits"] / matrix["counts"][:, None]):
        raise ValueError("Stored raw view factors disagree with first-hit counts")
    rebuilt, _ = reciprocal_enclosure(matrix["raw_view_factors"], matrix["areas_m2"])
    if not np.allclose(rebuilt, matrix["reciprocal_view_factors"], atol=1e-14, rtol=1e-12):
        raise ValueError("Stored reciprocal view factors do not reproduce")
    if not np.allclose([p.area_m2 for p in patches], matrix["areas_m2"], atol=1e-16, rtol=1e-12):
        raise ValueError("Stored patch areas disagree with geometric dimensions")
    return (
        vehicle,
        json.loads(thermal_path.read_bytes()),
        patches,
        matrix,
        source,
        [source_path, finite_path, candidate_path, thermal_path, patch_path, matrix_path],
    )


def make_baffle_parts(vehicle: Vehicle, cfg: dict[str, Any]) -> tuple[list[Part], dict[str, Any]]:
    """One fully specified eight-baffle family, sector supports and bonded contacts.

    Only the foil annuli enter coaxial rays. Real three-sector mica/epoxy pads
    retain their exact volumes/contact path in this ledger and normal-generator
    candidate parts; they are not replaced by full opaque annular disks.
    """
    parts = {part.id: part for part in vehicle.parts}
    mount = parts["motor_mount"]
    original = parts["motor_radiant_shield"]
    liner = parts["motor_liner"]
    assert mount.cad
    options = mount.cad.parameters
    widths = options.get(
        "ring_thicknesses_mm", [options["ring_thickness_mm"]] * len(options["ring_stations_mm"])
    )
    bores = options.get(
        "ring_inner_radii_mm",
        [1000 * mount.geometry["inner_radius_m"]] * len(options["ring_stations_mm"]),
    )
    thickness = cfg["foil_wall_m"]
    stand_off = cfg["ring_face_to_foil_near_surface_m"]
    mica_thickness = cfg["mica_pad_thickness_m"]
    bond_thickness = cfg["adhesive_layer_thickness_m_each_interface"]
    if abs(stand_off - mica_thickness - 2 * bond_thickness) > 1e-12:
        raise ValueError("Pad/bond stack does not fill the actual baffle stand-off")
    if cfg["pads_per_baffle"] != 3 or cfg["pad_start_angles_deg"] != [0.0, 120.0, 240.0]:
        raise ValueError("Existing sector-pad CAD requires the three explicit 120 degree stations")
    new_parts = []
    rows = []

    # Existing normal-generator sector pads use an inscribed polygon with at
    # least eight subdivisions, rather than circular arcs. Match its true area.
    sector_angle_rad = np.deg2rad(cfg["pad_sector_angle_deg"])
    sector_steps = max(8, int(np.ceil(cfg["pad_sector_angle_deg"] / 3)))
    sector_polygon_area_factor = float(
        np.sin(sector_angle_rad / sector_steps) / (sector_angle_rad / sector_steps)
    )

    def add_part(
        name: str, a: float, b: float, ri: float, ro: float, material: str, sectors: bool
    ) -> Part:
        raw = original.model_dump(by_alias=True)
        area = np.pi * (ro**2 - ri**2)
        if sectors:
            area *= (
                cfg["pads_per_baffle"]
                * cfg["pad_sector_angle_deg"]
                / 360
                * sector_polygon_area_factor
            )
        raw.update(
            id=name,
            parent="motor_mount",
            position_m=a,
            material=material,
            mass_kg=area * (b - a) * cfg["density_kg_m3"][material],
            density_kg_m3=None,
            cg_offset_m=(b - a) / 2,
            cad_mass=None,
        )
        raw["geometry"] = {
            "inner_radius_m": ri,
            "radius_m": ro,
            "length_m": b - a,
            "wall_m": ro - ri,
        }
        raw["cad"]["generator"] = "sector_pads" if sectors else "liner"
        raw["cad"]["parameters"] = (
            {"sector_angle_deg": cfg["pad_sector_angle_deg"]} if sectors else {}
        )
        raw["engineering"]["material_profile"] = material
        raw["engineering"][
            "function"
        ] = "Isolated ring-face radiation baffle or its explicitly bonded mica support; thermal benefit and assembly integrity unverified."
        raw["learn"] = (
            "This isolated ring-face baffle intercepts finite-end radiation. Its mica and adhesive support carries heat into the ring; narrow air gaps can also conduct strongly. No thermal or tolerance pass is established."
        )
        part = Part.model_validate(raw)
        new_parts.append(part)
        return part

    for ring_index, (station, width, bore) in enumerate(
        zip(options["ring_stations_mm"], widths, bores, strict=True)
    ):
        front = mount.position_m + station * 0.001
        aft = front + width * 0.001
        if front < liner.position_m or aft > liner.position_m + liner.geometry["length_m"]:
            continue
        ri = bore * 0.001
        if abs(ri - 0.0158) > 1e-12:
            raise ValueError("This one candidate preserves the source R15.8 mm ring bore")
        ro = cfg["outer_radius_m"]
        for side, z, direction in (("front", front, -1), ("aft", aft, 1)):
            name = f"ring_end_baffle_{ring_index}_{side}"
            if direction < 0:
                foil_a, foil_b = z - stand_off - thickness, z - stand_off
                ring_bond = (z - bond_thickness, z)
                mica = (z - bond_thickness - mica_thickness, z - bond_thickness)
                foil_bond = (z - stand_off, z - stand_off + bond_thickness)
            else:
                foil_a, foil_b = z + stand_off, z + stand_off + thickness
                ring_bond = (z, z + bond_thickness)
                mica = (z + bond_thickness, z + bond_thickness + mica_thickness)
                foil_bond = (z + stand_off - bond_thickness, z + stand_off)
            foil = add_part(name, foil_a, foil_b, ri, ro, "aluminum", False)
            pad_ri, pad_ro = cfg["pad_inner_radius_m"], cfg["pad_outer_radius_m"]
            pad = add_part(name + "_mica_pads", *mica, pad_ri, pad_ro, "mica", True)
            adhesive_ring = add_part(name + "_ring_bond", *ring_bond, pad_ri, pad_ro, "epoxy", True)
            adhesive_foil = add_part(name + "_foil_bond", *foil_bond, pad_ri, pad_ro, "epoxy", True)
            pad_area = (
                np.pi
                * (pad_ro**2 - pad_ri**2)
                * cfg["pads_per_baffle"]
                * cfg["pad_sector_angle_deg"]
                / 360
                * sector_polygon_area_factor
            )
            resistance = (
                mica_thickness / cfg["conductivity_w_m_k"]["mica"]
                + 2 * bond_thickness / cfg["conductivity_w_m_k"]["epoxy"]
            ) / pad_area
            face_area = np.pi * (ro**2 - ri**2)
            air_area = face_area - pad_area
            clearance = 0.0005 - stand_off - thickness
            rows.append(
                {
                    "id": name,
                    "ring_index": ring_index,
                    "side": side,
                    "ring_face_m": z,
                    "foil_interval_m": [foil_a, foil_b],
                    "source_ring_bore_radius_m": ri,
                    "remaining_nominal_foil_end_gap_m": clearance,
                    "foil_mass_kg": foil.resolved_mass_kg,
                    "mica_mass_kg": pad.resolved_mass_kg,
                    "epoxy_mass_kg": adhesive_ring.resolved_mass_kg
                    + adhesive_foil.resolved_mass_kg,
                    "support_sector_area_m2": pad_area,
                    "support_bulk_series_resistance_k_w": resistance,
                    "support_bulk_conductance_w_k": 1 / resistance,
                    "support_contact_resistance": "not measured; bulk series result excludes extra interface resistance",
                    "parallel_air_gap_estimate_w_k": cfg["assumed_gap_air_conductivity_w_m_k"]
                    * air_area
                    / stand_off,
                    "contact_parts_in_series": [
                        "motor_mount",
                        adhesive_ring.id,
                        pad.id,
                        adhesive_foil.id,
                        foil.id,
                    ],
                    "coaxial_ray_geometry_includes": [foil.id],
                    "angular_ray_geometry_excludes": [pad.id, adhesive_ring.id, adhesive_foil.id],
                }
            )
    if len(rows) != 8:
        raise ValueError("The single candidate requires exactly eight in-span ring-face baffles")
    total_mass = sum(part.resolved_mass_kg for part in new_parts)
    if total_mass > cfg["added_mass_reserve_kg"]:
        raise ValueError("The baffle family exceeds its declared mass reserve")
    return new_parts, {
        "candidate_id": cfg["id"],
        "baffles": rows,
        "new_part_count": len(new_parts),
        "sector_pad_polygon_steps": sector_steps,
        "sector_pad_area_relative_to_circular_sector": sector_polygon_area_factor,
        "nominal_added_mass_kg": total_mass,
        "added_mass_reserve_kg": cfg["added_mass_reserve_kg"],
        "mass_reserve_is_not_full_vehicle_budget_acceptance": True,
        "ring_bores_unchanged": True,
        "normal_generator_cad": "fully specified parts; local shapes verified separately by runner",
        "new_temperature_data_available": False,
    }


def baffle_geometry(
    vehicle: Vehicle, new_parts: list[Part], patch_length: float
) -> tuple[list[Patch], dict[str, Any]]:
    _, geometry = geometry_from_record(vehicle, patch_length)
    solids = [AnnularSolid(**solid) for solid in geometry["solids"]]
    for part in new_parts:
        if part.material == "aluminum":
            solids.append(
                AnnularSolid(
                    part.id,
                    part.geometry["inner_radius_m"],
                    part.geometry["radius_m"],
                    part.position_m,
                    part.position_m + part.geometry["length_m"],
                )
            )
    start, end = geometry["interval_m"]
    shell = next(part for part in vehicle.parts if part.id == "aft_shell")
    patches = enclosure_patches(solids, start, end, shell.geometry["inner_radius_m"], patch_length)
    return patches, {
        **geometry,
        "solids": [asdict(solid) for solid in solids],
        "patch_count": len(patches),
        "real_sector_supports_excluded_from_rays": True,
    }


def candidate_cad_checks(new_parts: list[Part]) -> list[dict[str, Any]]:
    from src.cad.parts import local_shape

    rows = []
    for part in new_parts:
        shape = local_shape(part)
        cad_volume = shape.Volume() * 1e-9
        analytic_volume = (
            part.resolved_mass_kg
            / {"aluminum": 2700.0, "mica": 2100.0, "epoxy": 1200.0}[part.material]
        )
        if not shape.isValid() or abs(cad_volume / analytic_volume - 1) > 1e-8:
            raise ValueError(f"Baffle part CAD/volume verification failed: {part.id}")
        rows.append(
            {
                "id": part.id,
                "shape_sha256": digest(part.geometry, part.cad.model_dump() if part.cad else None),
                "valid": bool(shape.isValid()),
                "cad_volume_m3": cad_volume,
                "analytic_volume_m3": analytic_volume,
                "mass_kg": part.resolved_mass_kg,
            }
        )
    return rows


def candidate_mount_fit_checks(vehicle: Vehicle, new_parts: list[Part]) -> dict[str, Any]:
    """Actual mount rails are excluded optically but cannot be ignored for fit."""
    from src.cad.parts import local_shape

    mount = next(part for part in vehicle.parts if part.id == "motor_mount")
    mount_shape = local_shape(mount).translate((0, 0, 1000 * mount.position_m))
    rows = []
    for part in new_parts:
        shape = local_shape(part).translate((0, 0, 1000 * part.position_m))
        volume = max(0.0, float(mount_shape.intersect(shape).Volume()))
        rows.append(
            {
                "part_id": part.id,
                "overlap_with_actual_mount_mm3": volume,
                "part_volume_mm3": float(shape.Volume()),
                "nominal_mount_fit_passed": volume <= 1e-3,
            }
        )
    return {
        "source_mount_shape_identity": digest(
            mount.geometry, mount.cad.model_dump() if mount.cad else None
        ),
        "method": "normal-generator solids; actual mount including rails; common intersection volume",
        "rows": rows,
        "passed": all(row["nominal_mount_fit_passed"] for row in rows),
        "other_parts_clearance_or_tolerance_pass": False,
    }


def geometry_views(
    patches: list[Patch], sample: dict[str, Any], has_baffles: bool
) -> dict[str, Any]:
    original = [p.part_id == "motor_radiant_shield" and p.face == "outer_cylinder" for p in patches]
    ring_ends = [p.part_id == "motor_mount" and p.kind == "annulus" for p in patches]
    result = {"original_foil_to_ring_ends": aggregate_view_interval(sample, original, ring_ends)}
    if has_baffles:
        baffles = [p.part_id.startswith("ring_end_baffle_") for p in patches]
        result["original_foil_to_new_baffles"] = aggregate_view_interval(sample, original, baffles)
        result["new_baffles_to_ring_ends"] = aggregate_view_interval(sample, baffles, ring_ends)
    return result


def baffle_temperature_probes(
    operator: CondensedRadiation,
    thermal: dict[str, Any],
    selected: list[float],
    burn: float,
    ledger: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    for requested in selected:
        index = thermal["times_s"].index(float(requested))
        recorded = dict(zip(thermal["part_ids"], thermal["temperature_k"][index], strict=True))
        recorded["motor_liner.cell_0"] = thermal["liner_radial_temperature_k"][index][0]
        recorded["motor_case_boundary"] = case_temperature_k(thermal, burn, requested)
        for end_mode in ("ambient", "case"):
            end_k = (
                thermal["ambient_c"] + 273.15
                if end_mode == "ambient"
                else recorded["motor_case_boundary"]
            )
            recorded.update(fore_end_reservoir=end_k, aft_end_reservoir=end_k)
            for probe_source in ("motor_mount", "motor_radiant_shield"):
                baffle_k = recorded[probe_source]
                values = np.array(
                    [
                        baffle_k if name.startswith("ring_end_baffle_") else recorded[name]
                        for name in operator.node_names
                    ]
                )
                heat = operator.heat_rates(values)
                mapped = dict(zip(operator.node_names, heat.tolist(), strict=True))
                baffle_to_ring_rad = sum(
                    flux if a.startswith("ring_end_baffle_") else -flux
                    for a, b, flux in operator.pair_fluxes(values)
                    if (a.startswith("ring_end_baffle_") and b == "motor_mount")
                    or (b.startswith("ring_end_baffle_") and a == "motor_mount")
                )
                delta = baffle_k - recorded["motor_mount"]
                rows.append(
                    {
                        "time_s": requested,
                        "missing_end_mode": end_mode,
                        "baffle_temperature_probe_source": probe_source,
                        "assumed_baffle_temperature_k": baffle_k,
                        "new_baffle_temperature_history_available": False,
                        "mount_net_inward_radiation_w": mapped["motor_mount"],
                        "baffle_to_ring_net_radiation_w": baffle_to_ring_rad,
                        "all_baffles_net_inward_radiation_w": sum(
                            value
                            for name, value in mapped.items()
                            if name.startswith("ring_end_baffle_")
                        ),
                        "support_bulk_conduction_probe_w": delta
                        * sum(row["support_bulk_conductance_w_k"] for row in ledger["baffles"]),
                        "parallel_air_gap_conduction_probe_w": delta
                        * sum(row["parallel_air_gap_estimate_w_k"] for row in ledger["baffles"]),
                        "probe_is_not_a_coupled_surface_or_energy_balanced_baffle_temperature_solution": True,
                    }
                )
    return rows


def save_operator(
    folder: Path,
    label: str,
    operator: CondensedRadiation,
    patches: list[Patch],
    view: Any,
    areas: Any,
    emissivity: Any,
) -> None:
    np.savez_compressed(
        folder / (label + "-operator.npz"),
        inward_operator_w_k4=operator.inward_operator_w_k4,
        node_names=np.array(operator.node_names),
        patch_node_index=operator.patch_node_index,
        patch_radiosity_response_w_m2_k4=operator.radiosity_response_w_m2_k4,
        reciprocal_view_factors=view,
        areas_m2=areas,
        emissivities=emissivity,
    )
    (folder / (label + "-patches.json")).write_text(
        json.dumps([p.record() for p in patches], indent=2) + "\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--geometry", choices=("baseline", "ring_end_baffles"), default="baseline")
    args = parser.parse_args()
    started = time.perf_counter()
    cfg = yaml.safe_load(args.config.read_bytes())
    vehicle, thermal, patches, matrix, source, inputs = load_checked_inputs(cfg)
    inputs += [
        args.config.resolve(),
        Path(__file__).resolve(),
        ROOT / "src/analysis/finite_radiation.py",
        ROOT / "scripts/wo03_finite_radiation.py",
        ROOT / "src/vehicle/materials.py",
    ]
    inputs += list((ROOT / "src/cad").glob("*.py"))
    hashes = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in inputs
    }
    run_id = "wo03-finite-thermal-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "runs" / run_id
    folder.mkdir(parents=True)
    for path in inputs:
        target = folder / "source-snapshot" / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    groups = patch_temperature_groups(patches, thermal["radial_cells"])
    emissivity = np.array([1.0 if patch.unknown_boundary else 0.9 for patch in patches])
    baseline = condense_radiosity(
        matrix["reciprocal_view_factors"], matrix["areas_m2"], emissivity, groups
    )
    verification = verify_operator(
        baseline,
        matrix["reciprocal_view_factors"],
        matrix["areas_m2"],
        emissivity,
        cfg["operator_verification"],
    )
    if not verification["passed"]:
        raise ValueError("Condensed baseline radiation operator failed direct verification")
    adapter = build_material_adapter(
        baseline,
        thermal,
        "ambient",
        {
            "source_candidate_identity": source["candidate_identity"],
            "source_cad_revision_sha256": source["cad_revision_sha256"],
        },
    )
    snapshots = []
    assert vehicle.motor
    for requested in cfg["selected_times_s"]:
        i = thermal["times_s"].index(float(requested))
        q, external, links = adapter.rates(
            recorded_ode_temperature(thermal, i),
            case_temperature_k=case_temperature_k(thermal, vehicle.motor.burn_time_s, requested),
            ambient_temperature_k=thermal["ambient_c"] + 273.15,
        )
        snapshots.append(
            {
                "time_s": requested,
                "mount_radiation_w": float(q[thermal_node_names(thermal).index("motor_mount")]),
                "external_net_radiation_into_material_nodes_w": external,
                "pair_link_count": len(links),
                "only_diagnostic_material_node_temperatures": True,
            }
        )
    save_operator(
        folder,
        "baseline-material",
        baseline,
        patches,
        matrix["reciprocal_view_factors"],
        matrix["areas_m2"],
        emissivity,
    )
    surface_groups = [
        f"surface_{i}:{patch.part_id}:{patch.face}:{patch.lo_m:.12g}:{patch.hi_m:.12g}"
        for i, patch in enumerate(patches)
    ]
    surface_operator = condense_radiosity(
        matrix["reciprocal_view_factors"], matrix["areas_m2"], emissivity, surface_groups
    )
    surface_verification = verify_operator(
        surface_operator,
        matrix["reciprocal_view_factors"],
        matrix["areas_m2"],
        emissivity,
        cfg["operator_verification"],
    )
    if not surface_verification["passed"]:
        raise ValueError("Separately coupled surface operator failed verification")
    save_operator(
        folder,
        "baseline-surfaces",
        surface_operator,
        patches,
        matrix["reciprocal_view_factors"],
        matrix["areas_m2"],
        emissivity,
    )
    baffle_rows = []
    ledger = None
    total_rays = 0
    if args.geometry == "ring_end_baffles":
        total_rays = sum(level["ray_budget"] for level in cfg["numerics"]["baffle_levels"])
        if total_rays > cfg["numerics"]["max_additional_rays"]:
            raise ValueError("The single baffle diagnostic exceeds its ray cap")
        new_parts, ledger = make_baffle_parts(vehicle, cfg["baffle_candidate"])
        ledger["cad_checks"] = candidate_cad_checks(new_parts)
        ledger["actual_mount_fit_checks"] = candidate_mount_fit_checks(vehicle, new_parts)
        (folder / "baffle-parts.json").write_text(
            json.dumps([part.model_dump(by_alias=True) for part in new_parts], indent=2) + "\n"
        )
        permitted_levels = (
            cfg["numerics"]["baffle_levels"] if ledger["actual_mount_fit_checks"]["passed"] else []
        )
        if not permitted_levels:
            total_rays = 0
            ledger["candidate_status"] = "REJECTED_NOMINAL_ACTUAL_MOUNT_INTERSECTION_NO_RAYS_RUN"
        for level in permitted_levels:
            bp, bg = baffle_geometry(vehicle, new_parts, level["max_axial_patch_m"])
            sample = sample_view_factors(
                bp,
                level["ray_budget"],
                cfg["numerics"]["seed"] + level["seed_offset"],
                cfg["numerics"]["chunk_size"],
            )
            if (
                sample["sampling"]["escaped_rays"]
                or not sample["sampling"][
                    "raw_reciprocity_simultaneous_99pct_exact_binomial_intervals_overlap"
                ]
            ):
                raise ValueError("Baffle opaque geometry closure/reciprocity failed")
            view, balancing = reciprocal_enclosure(sample["raw_view_factors"], sample["areas_m2"])
            eps = np.array([1.0 if patch.unknown_boundary else 0.9 for patch in bp])
            op = condense_radiosity(
                view, sample["areas_m2"], eps, patch_temperature_groups(bp, thermal["radial_cells"])
            )
            checked = verify_operator(
                op, view, sample["areas_m2"], eps, cfg["operator_verification"]
            )
            if not checked["passed"]:
                raise ValueError("Baffle operator failed direct verification")
            save_operator(folder, level["id"] + "-baffles", op, bp, view, sample["areas_m2"], eps)
            np.savez_compressed(
                folder / (level["id"] + "-raw-rays.npz"),
                raw_view_factors=sample["raw_view_factors"],
                hits=sample["hits"],
                counts=sample["counts"],
                areas_m2=sample["areas_m2"],
            )
            row = {
                "id": level["id"],
                "geometry": bg,
                "sampling": sample["sampling"],
                "balancing": balancing,
                "operator_verification": checked,
                "direct_views": geometry_views(bp, sample, True),
                "assumed_temperature_probes": baffle_temperature_probes(
                    op, thermal, cfg["selected_times_s"], vehicle.motor.burn_time_s, ledger
                ),
            }
            baffle_rows.append(row)
            print(
                json.dumps(
                    {
                        "completed": level["id"],
                        "patches": len(bp),
                        "rays": level["ray_budget"],
                        "foil_to_ring_end_fraction": row["direct_views"][
                            "original_foil_to_ring_ends"
                        ]["fraction"],
                    }
                ),
                flush=True,
            )
    unchanged = all(
        hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
        for path, expected in hashes.items()
    )
    if not unchanged:
        raise ValueError("Condensation/baffle inputs changed during execution")
    record = {
        "run_id": run_id,
        "status": "condensed_operator_and_static_geometry_diagnostic_only",
        "source_candidate_identity": source["candidate_identity"],
        "source_cad_revision_sha256": source["cad_revision_sha256"],
        "input_sha256": hashes,
        "inputs_unchanged": unchanged,
        "baseline_material_operator_verification": verification,
        "baseline_surface_operator_verification": surface_verification,
        "baseline_adapter": adapter.metadata(),
        "baseline_recorded_temperature_diagnostics": snapshots,
        "baffle_candidate_ledger": ledger,
        "baffle_levels": baffle_rows,
        "additional_ray_count": total_rays,
        "cpu_workers": 1,
        "cost_usd": 0,
        "elapsed_s": time.perf_counter() - started,
        "transient_integrated": False,
        "common_surface_conduction_radiation_coupling_available_in_this_runner": False,
        "thermal_acceptance_available": False,
        "full_cad_conservative_bound": False,
        "active_adoption": False,
        "flight_ready": False,
        "limitations": cfg["limitations"],
    }
    (folder / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "record": str(folder / "record.json"),
                "additional_rays": total_rays,
                "transient_integrated": False,
                "nominal_baffle_mass_kg": (
                    None if ledger is None else ledger["nominal_added_mass_kg"]
                ),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
