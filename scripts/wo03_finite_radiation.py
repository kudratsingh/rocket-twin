"""Execute finite coaxial radiation diagnostics on an immutable recorded candidate."""

from __future__ import annotations

import os

# One CPU worker, including numerical libraries. No solver installation or paid run.
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
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.finite_radiation import (
    SIGMA,
    AnnularSolid,
    Patch,
    aggregate_view_interval,
    enclosure_patches,
    known_cases,
    radiosity,
    reciprocal_enclosure,
    sample_view_factors,
)
from src.analysis.thermal_radial import opaque_gap_flux
from src.vehicle.cad_contract import digest
from src.vehicle.schema import Vehicle

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-finite-radiation.yaml"


def geometry_from_record(
    vehicle: Vehicle, patch_length: float
) -> tuple[list[Patch], dict[str, Any]]:
    parts = {part.id: part for part in vehicle.parts}
    liner = parts["motor_liner"]
    mount = parts["motor_mount"]
    assert mount.cad
    if mount.cad.generator != "mount" or vehicle.tvc is not None:
        raise ValueError("Only the fixed neutral G54 geometry is supported")
    start = liner.position_m
    end = start + liner.geometry["length_m"]
    solids = []
    for name in ("motor", "motor_liner", "motor_radiant_shield"):
        part = parts[name]
        solids.append(
            AnnularSolid(
                name,
                part.geometry.get("inner_radius_m", 0.0),
                part.geometry["radius_m"],
                start,
                end,
            )
        )
    for part in vehicle.parts:
        if part.id.startswith(("additional_shield_", "mount_shell_bond_")):
            a = max(start, part.position_m)
            b = min(end, part.position_m + part.geometry["length_m"])
            if b > a:
                solids.append(
                    AnnularSolid(
                        part.id, part.geometry["inner_radius_m"], part.geometry["radius_m"], a, b
                    )
                )
    params = mount.cad.parameters
    stations = params["ring_stations_mm"]
    widths = params.get("ring_thicknesses_mm", [params["ring_thickness_mm"]] * len(stations))
    bores = params.get(
        "ring_inner_radii_mm", [1000 * mount.geometry["inner_radius_m"]] * len(stations)
    )
    included_rings = []
    excluded_rings = []
    for station, width, bore in zip(stations, widths, bores, strict=True):
        a = mount.position_m + station * 0.001
        b = a + width * 0.001
        if b <= start or a >= end:
            excluded_rings.append([a, b])
            continue
        solids.append(
            AnnularSolid(
                "motor_mount", bore * 0.001, mount.geometry["radius_m"], max(a, start), min(b, end)
            )
        )
        included_rings.append([a, b])
    patches = enclosure_patches(
        solids, start, end, parts["aft_shell"].geometry["inner_radius_m"], patch_length
    )
    return patches, {
        "interval_m": [start, end],
        "included_ring_intervals_m": included_rings,
        "outside_ring_intervals_m": excluded_rings,
        "solids": [solid.__dict__ for solid in solids],
        "patch_count": len(patches),
        "max_axial_patch_m": patch_length,
        "missing_boundary_surfaces": [
            "forward ring/thrust plate beyond z=liner front",
            "actual nozzle and motor end faces",
            "aft retainer beyond liner aft",
            "upper bay and end surroundings",
        ],
        "excluded_angular_geometry": [
            "mount rails",
            "ring/bond fin slots and notches",
            "sector mica spacers",
            "foil seams/wrinkles",
            "retention blocks and fasteners",
        ],
        "annular_proxy_is_not_full_cad_bound": True,
    }


def case_temperature_k(thermal: dict[str, Any], burn: float, sample_time: float) -> float:
    ambient = float(thermal["ambient_c"]) + 273.15
    peak = float(thermal["prescribed_case_peak_c"]) + 273.15
    if sample_time <= burn:
        return peak
    return float(
        ambient
        + (peak - ambient) * np.exp(-(sample_time - burn) / thermal["post_burn_cooling_tau_s"])
    )


def material_temperatures(
    patches: list[Patch], thermal: dict[str, Any], time_index: int, case_k: float, hot: bool
) -> np.ndarray:
    """No missing part temperatures become zeros or ambient material defaults."""
    recorded = dict(zip(thermal["part_ids"], thermal["temperature_k"][time_index], strict=True))
    ambient = float(thermal["ambient_c"]) + 273.15
    result = []
    for patch in patches:
        if patch.unknown_boundary:
            value = case_k if hot else ambient
        elif patch.part_id == "motor":
            value = case_k
        elif patch.part_id == "motor_liner" and patch.face == "inner_cylinder":
            value = thermal["liner_radial_temperature_k"][time_index][0]
        elif patch.part_id == "motor_liner" and patch.face == "outer_cylinder":
            value = thermal["liner_radial_temperature_k"][time_index][-1]
        else:
            value = recorded[patch.part_id]
        result.append(float(value))
    return np.array(result)


def long_cylinder_comparison(thermal: dict[str, Any], time_index: int) -> dict[str, Any]:
    """Radiation alone, same recorded material nodes; also report old half-wall flux.

    The first column is the controlled geometry comparison. The second reconstructs
    the original solver's surface temperatures behind the recorded half walls and
    includes its gas conduction in the reconstruction, but reports radiation alone.
    They must not be confused with one another or compared as identical boundaries.
    """
    parts = dict(zip(thermal["part_ids"], thermal["temperature_k"][time_index], strict=True))
    parts["motor_liner"] = thermal["liner_radial_temperature_k"][time_index][-1]
    incoming: dict[str, float] = {name: 0.0 for name in parts}
    old_incoming: dict[str, float] = {name: 0.0 for name in parts}
    for interface in thermal["interfaces"]:
        if interface["model"] != "opaque_gap":
            continue
        source = interface["source_part_id"]
        target = interface["target_part_id"]
        a, b = float(parts[source]), float(parts[target])
        ra, rb = interface["source_surface_radius_m"], interface["target_surface_radius_m"]
        length = interface["length_m"]
        eps_a, eps_b = (
            interface["source_surface_emissivity"],
            interface["target_surface_emissivity"],
        )
        coefficient = SIGMA * 2 * np.pi * ra * length / (1 / eps_a + ra / rb * (1 / eps_b - 1))
        q = coefficient * (a**4 - b**4)
        incoming[source] -= q
        incoming[target] += q
        total_flux = opaque_gap_flux(
            a,
            b,
            interface["source_half_wall_resistance_k_w"],
            interface["target_half_wall_resistance_k_w"],
            ra,
            rb,
            length,
            thermal["air_conductivity_w_m_k"],
            eps_a,
            inner_surface_emissivity=eps_a,
            outer_surface_emissivity=eps_b,
        )
        sa = a - total_flux * interface["source_half_wall_resistance_k_w"]
        sb = b + total_flux * interface["target_half_wall_resistance_k_w"]
        old_q = coefficient * (sa**4 - sb**4)
        old_incoming[source] -= old_q
        old_incoming[target] += old_q
    return {
        "same_node_temperature_net_incoming_w": incoming,
        "old_solver_reconstructed_halfwall_net_incoming_radiation_w": old_incoming,
    }


def summarize_sample(
    patches: list[Patch],
    sample: dict[str, Any],
    thermal: dict[str, Any],
    selected: list[float],
    burn: float,
) -> tuple[dict[str, Any], Any]:
    view, balancing = reciprocal_enclosure(sample["raw_view_factors"], sample["areas_m2"])
    emissivity = np.array([1.0 if patch.unknown_boundary else 0.9 for patch in patches])
    foil = np.array(
        [p.part_id == "motor_radiant_shield" and p.face == "outer_cylinder" for p in patches]
    )
    mount_ends = np.array([p.part_id == "motor_mount" and p.kind == "annulus" for p in patches])
    mount_any = np.array([p.part_id == "motor_mount" for p in patches])
    shell = np.array([p.part_id == "aft_shell" for p in patches])
    outer_foils = np.array(
        [
            p.part_id.startswith("additional_shield_")
            and not p.part_id.startswith("additional_shield_1_")
            for p in patches
        ]
    )
    unknown = np.array([p.unknown_boundary for p in patches])
    views = {
        "original_foil_to_mount_end_faces": aggregate_view_interval(sample, foil, mount_ends),
        "original_foil_to_mount_all_faces": aggregate_view_interval(sample, foil, mount_any),
        "original_foil_to_shell": aggregate_view_interval(sample, foil, shell),
        "original_foil_to_nonadjacent_added_foils": aggregate_view_interval(
            sample, foil, outer_foils
        ),
        "original_foil_to_unknown_ends": aggregate_view_interval(sample, foil, unknown),
    }
    rows = []
    all_parts = sorted({p.part_id for p in patches})
    masks = {name: np.array([p.part_id == name for p in patches]) for name in all_parts}
    for requested in selected:
        time_index = thermal["times_s"].index(float(requested))
        case_k = case_temperature_k(thermal, burn, requested)
        baseline = long_cylinder_comparison(thermal, time_index)
        for hot in (False, True):
            temperatures = material_temperatures(patches, thermal, time_index, case_k, hot)
            result = radiosity(view, sample["areas_m2"], temperatures, emissivity)
            incoming = {
                name: float(-sum(result["net_outward_w"][mask])) for name, mask in masks.items()
            }
            direct_foil_mount = float(sum(sum(result["pair_net_outward_w"][foil][:, mount_any])))
            direct_foil_mount_ends = float(
                sum(sum(result["pair_net_outward_w"][foil][:, mount_ends]))
            )
            old = baseline["same_node_temperature_net_incoming_w"]
            rows.append(
                {
                    "time_s": requested,
                    "temperature_record_index": time_index,
                    "missing_end_boundary": (
                        "prescribed_case_temperature" if hot else "ambient_temperature"
                    ),
                    "missing_end_boundary_k": (
                        case_k if hot else float(thermal["ambient_c"]) + 273.15
                    ),
                    "case_temperature_k": case_k,
                    "finite_net_incoming_w_by_part": incoming,
                    "long_cylinder_same_node_temperature_net_incoming_w_by_part": baseline[
                        "same_node_temperature_net_incoming_w"
                    ],
                    "old_solver_reconstructed_halfwall_radiation_w_by_part": baseline[
                        "old_solver_reconstructed_halfwall_net_incoming_radiation_w"
                    ],
                    "finite_minus_band_net_incoming_w": {
                        name: incoming[name] - old[name] for name in ("motor_mount", "aft_shell")
                    },
                    "original_foil_to_mount_net_exchange_w": direct_foil_mount,
                    "original_foil_to_mount_end_faces_net_exchange_w": direct_foil_mount_ends,
                    "energy_residual_w_including_end_reservoirs": result["energy_residual_w"],
                    "maximum_radiosity_equation_residual_w_m2": result[
                        "max_equation_residual_w_m2"
                    ],
                    "temperature_evidence": "recorded old-transient nodes held fixed; prescribed case profile evaluated at recorded time; diagnostic only",
                }
            )
    return {
        "sampling": sample["sampling"],
        "balancing": balancing,
        "direct_views": views,
        "snapshots": rows,
    }, view


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--preset", choices=("tiny", "sim"), default="tiny")
    args = parser.parse_args()
    started = time.perf_counter()
    cfg = yaml.safe_load(args.config.read_text())
    if cfg["surface_emissivity"] != 0.9 or cfg["unknown_end_boundary_emissivity"] != 1.0:
        raise ValueError(
            "This bounded diagnostic supports only contaminated eps=0.9 and black end brackets"
        )
    source = ROOT / cfg["source_record"]
    original = json.loads(source.read_text())
    candidate_path = source.parent / "resolved-candidate.json"
    thermal_path = source.parent / "thermal-results.json"
    vehicle = Vehicle.model_validate_json(candidate_path.read_bytes())
    thermal = json.loads(thermal_path.read_bytes())
    if any(
        interface[side] != cfg["surface_emissivity"]
        for interface in thermal["interfaces"]
        for side in ("source_surface_emissivity", "target_surface_emissivity")
    ):
        raise ValueError("Recorded thermal surfaces do not match the diagnostic emissivity")
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    if identity != original["candidate_identity"] or identity != cfg["expected_candidate_identity"]:
        raise ValueError("Candidate identity mismatch")
    if original["cad_revision_sha256"] != cfg["expected_cad_revision_sha256"]:
        raise ValueError("CAD identity mismatch")
    for part in vehicle.parts:
        if (
            digest(part.geometry, part.cad.model_dump() if part.cad else None)
            != original["part_shape_sha256"][part.id]
        ):
            raise ValueError(f"Recorded shape identity mismatch: {part.id}")
    # The old record has source hashes, not hashes of generated history/candidate.
    # Verify its immutable source snapshot too, then pin all generated inputs here.
    for path, expected in original["source_sha256"].items():
        snapshot = source.parent / "source-snapshot" / path
        if hashlib.sha256(snapshot.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Old source snapshot mismatch: {path}")
    inputs = [
        source,
        candidate_path,
        thermal_path,
        args.config.resolve(),
        Path(__file__).resolve(),
        ROOT / "src/analysis/finite_radiation.py",
        ROOT / "src/analysis/thermal_radial.py",
    ]
    hashes = {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in inputs
    }
    settings = cfg["numerics"]
    levels = settings["tiny_levels"] if args.preset == "tiny" else settings["levels"]
    total_rays = 2 * settings["known_case_rays"] + sum(row["ray_budget"] for row in levels)
    if total_rays > settings["max_total_rays"]:
        raise ValueError("Requested diagnostic exceeds the configured total ray cap")
    run_id = "wo03-finite-radiation-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "runs" / run_id
    folder.mkdir(parents=True)
    for path in inputs:
        target = folder / "source-snapshot" / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    verification = known_cases(settings["known_case_rays"])
    if not verification["passed"]:
        raise RuntimeError("Finite geometry/radiosity known cases failed")
    output = []
    assert vehicle.motor
    for level in levels:
        patches, geometry = geometry_from_record(vehicle, level["max_axial_patch_m"])
        sample = sample_view_factors(
            patches,
            level["ray_budget"],
            settings["seed"] + level["seed_offset"],
            settings["chunk_size"],
        )
        if sample["sampling"]["escaped_rays"]:
            raise RuntimeError("An opaque enclosure ray escaped; geometry diagnostic is invalid")
        summary, view = summarize_sample(
            patches, sample, thermal, cfg["selected_times_s"], vehicle.motor.burn_time_s
        )
        np.savez_compressed(
            folder / (level["id"] + "-view-factors.npz"),
            raw_view_factors=sample["raw_view_factors"],
            reciprocal_view_factors=view,
            counts=sample["counts"],
            hits=sample["hits"],
            areas_m2=sample["areas_m2"],
        )
        (folder / (level["id"] + "-patches.json")).write_text(
            json.dumps([p.record() for p in patches], indent=2) + "\n"
        )
        output.append({"id": level["id"], "geometry": geometry, **summary})
        print(
            json.dumps(
                {
                    "completed_level": level["id"],
                    "patches": len(patches),
                    "rays": sample["sampling"]["ray_count"],
                    "foil_to_ring_end_fraction": summary["direct_views"][
                        "original_foil_to_mount_end_faces"
                    ]["fraction"],
                    "elapsed_s": time.perf_counter() - started,
                }
            ),
            flush=True,
        )
    unchanged = all(
        hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
        for path, expected in hashes.items()
    )
    if not unchanged:
        raise ValueError("Diagnostic inputs changed during execution")
    record = {
        "run_id": run_id,
        "model": "finite_opaque_neutral_coaxial_diffuse_gray_static_diagnostic_v1",
        "source_run_id": original["run_id"],
        "candidate_identity": identity,
        "cad_revision_sha256": original["cad_revision_sha256"],
        "case_id": original["thermal"]["case_id"],
        "input_sha256": hashes,
        "source_snapshot": "source-snapshot/ contains immutable bytes of the record, generated candidate/history and diagnostic sources",
        "inputs_unchanged": unchanged,
        "known_cases": verification,
        "levels": output,
        "ray_count_total_including_known_cases": total_rays,
        "cpu_workers": 1,
        "cost_usd": 0,
        "elapsed_s": time.perf_counter() - started,
        "limits": cfg["limitations"],
        "transient_temperatures_recalculated": False,
        "full_cad_upper_or_lower_bound": False,
        "thermal_acceptance_available": False,
        "active_adoption": False,
        "flight_ready": False,
    }
    (folder / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "record": str(folder / "record.json"),
                "total_rays": total_rays,
                "thermal_acceptance_available": False,
                "cost_usd": 0,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
