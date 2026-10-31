"""Run finite-ring/end radiation with correctly coupled material surface temperatures.

Replays one hash-pinned candidate, retains its explicit serial contacts and
physical capacities, and replaces its opaque-gap model through the shared offline
solver hook. The coaxial view-factor geometry remains a disclosed proxy; angular
CAD coverage and the full required configuration matrix remain acceptance items.
"""

from __future__ import annotations

import os

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
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

from scripts.wo03_finite_radiation import geometry_from_record
from scripts.wo03_thermal_matrix import case_config, make_topology
from src.analysis.engineering import material_profile
from src.analysis.finite_radiation import Patch
from src.analysis.finite_surface_adapter import FiniteSurfaceAdapter
from src.analysis.thermal_topology import run_thermal_topology
from src.vehicle.schema import Vehicle

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-finite-transient.yaml"


def candidate_topology(base: dict[str, Any], vehicle: Vehicle, contact: float) -> dict[str, Any]:
    """Reconstruct explicit adjacent-layer contacts from the recorded part identities."""
    result = make_topology(base, vehicle, contact)
    ids = {p.id for p in vehicle.parts}
    for part in vehicle.parts:
        if part.id.startswith("additional_shield_"):
            result["part_ids"].append(part.id)
            result["annular_barrier_part_ids"].append(part.id)
        elif part.id.startswith("shield_spacer_additional_shield_"):
            target = part.id.removeprefix("shield_spacer_").rsplit("_", 1)[0]
            if part.parent not in ids or target not in ids:
                raise ValueError(f"Missing actual adjacent-shield contact for {part.id}")
            result["part_ids"].append(part.id)
            result["pad_conduction_part_ids"].append(part.id)
            result.setdefault("pad_conduction_thickness_m", {})[part.id] = (
                part.geometry["radius_m"] - part.geometry["inner_radius_m"]
            )
            for a, b in ((part.parent, part.id), (part.id, target)):
                result["contact_pairs"].append([a, b])
                result.setdefault("contact_pair_conductance_w_k", {})[f"{a}->{b}"] = contact
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--all-required", action="store_true")
    parser.add_argument("--end", choices=("ambient", "case", "both"), default="both")
    parser.add_argument("--case", default=None)
    parser.add_argument("--corner", default=None)
    parser.add_argument("--cells", type=int, default=None)
    parser.add_argument("--max-step-s", type=float, default=None)
    args = parser.parse_args()
    started = time.perf_counter()
    cfg = yaml.safe_load(args.config.read_text())
    source_path = ROOT / cfg["candidate_record"]
    source = json.loads(source_path.read_bytes())
    finite_path = ROOT / cfg["finite_record"]
    finite = json.loads(finite_path.read_bytes())
    candidate = source_path.parent / "resolved-candidate.json"
    vehicle = Vehicle.model_validate_json(candidate.read_bytes())
    actual_identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    if actual_identity != source["candidate_identity"]:
        raise ValueError("Recorded candidate identity disagrees with resolved specification")
    if finite["candidate_identity"] not in {
        actual_identity,
        source.get("source_candidate_identity"),
    }:
        raise ValueError("Finite source is not this candidate or its explicit recorded parent")
    level = cfg["finite_level"]
    patch_path = finite_path.parent / (level + "-patches.json")
    matrix_path = finite_path.parent / (level + "-view-factors.npz")
    patches = [
        Patch(**{k: v for k, v in row.items() if k != "area_m2"})
        for row in json.loads(patch_path.read_bytes())
    ]
    view = np.load(matrix_path)["reciprocal_view_factors"]
    # The explicit circular-pad correction changes actual sector geometry. It
    # does not change the annular PROJECTION (which excludes those pads). Reuse
    # an old sampled matrix only after checking every projected physical patch,
    # and retain both source identities. This is not a full-CAD compatibility pass.
    level_geometry = next(row["geometry"] for row in finite["levels"] if row["id"] == level)
    projected, _ = geometry_from_record(vehicle, level_geometry["max_axial_patch_m"])
    if len(projected) != len(patches) or any(
        a != b for a, b in zip(projected, patches, strict=True)
    ):
        raise ValueError("Recorded radiation matrix has incompatible projected geometry")
    projection_reuse = {
        "sampled_source_candidate_identity": finite["candidate_identity"],
        "actual_candidate_identity": actual_identity,
        "every_projected_patch_equal": True,
        "actual_sector_geometry_coverage": "unavailable in this coaxial projection",
        "source_cad_revision_sha256": finite["cad_revision_sha256"],
        "actual_cad_revision_sha256": source["cad_revision_sha256"],
    }
    acceptance_path = ROOT / cfg["acceptance_matrix"]
    acceptance = yaml.safe_load(acceptance_path.read_text())
    engineering_path = ROOT / acceptance["engineering_inputs"]
    topology_path = ROOT / acceptance["thermal_topology"]
    engineering = yaml.safe_load(engineering_path.read_text())
    topology = yaml.safe_load(topology_path.read_text())
    construction_path = ROOT / cfg["construction"]
    construction = yaml.safe_load(construction_path.read_text())
    scope = construction["scope"]
    study = candidate_topology(topology, vehicle, scope["interface_contact_conductance_w_k"])
    n = cfg["numerics"]
    if args.cells is not None:
        n["radial_cells"] = args.cells
    if args.max_step_s is not None:
        n["max_step_s"] = args.max_step_s
    if n["radial_cells"] < 2 or n["max_step_s"] <= 0:
        raise ValueError("At least two radial cells and positive time step required")
    cases = [
        c
        for c in acceptance["cases"]
        if (
            c["id"] == (args.case or cfg["default_case"])
            if not args.all_required
            else (
                c["role"].startswith("required_")
                or c["role"] == "configured_lower_boundary_reference"
            )
        )
    ]
    corners = [
        c
        for c in acceptance["material_property_uncertainty"]["factors"]
        if args.all_required or c["id"] == (args.corner or cfg["default_corner"])
    ]
    modes = cfg["end_boundary_modes"] if args.end == "both" else [args.end]
    if not cases or not corners:
        raise ValueError("Requested case or material-property corner is not in the existing matrix")
    inputs = [
        args.config.resolve(),
        source_path,
        candidate,
        finite_path,
        patch_path,
        matrix_path,
        acceptance_path,
        engineering_path,
        topology_path,
        construction_path,
        Path(__file__),
        ROOT / "scripts/wo03_thermal_matrix.py",
        ROOT / "scripts/wo03_finite_radiation.py",
        ROOT / "src/analysis/engineering.py",
        ROOT / "src/analysis/thermal_topology.py",
        ROOT / "src/analysis/thermal_radial.py",
        ROOT / "src/analysis/finite_radiation.py",
        ROOT / "src/analysis/finite_surface_adapter.py",
        ROOT / "src/analysis/surface_thermal.py",
        ROOT / "src/vehicle/schema.py",
    ]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    run_id = "wo03-finite-transient-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "runs" / run_id
    folder.mkdir()
    for path, digest in hashes.items():
        raw = (ROOT / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError("Input changed during source snapshot")
        target = folder / "source-snapshot" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    rows = []
    for case in cases:
        for corner in corners:
            current = case_config(engineering, case, scope["adhesive_conductivity_w_m_k"], corner)
            scenario = int(case["source_scenario_index"])
            parts = {p.id: p for p in vehicle.parts}
            emissivities = []
            for p in patches:
                if p.unknown_boundary:
                    emissivities.append(1.0)
                    continue
                profile = current["materials"][material_profile(parts[p.part_id])]
                e = profile.get(
                    "surface_emissivity_by_scenario",
                    profile.get("surface_emissivity", current["thermal"]["emissivity"]),
                )
                emissivities.append(float(e[scenario] if isinstance(e, list) else e))
            for mode in modes:
                label = f"{case['id']}_{corner['id']}_{mode}"
                adapter = FiniteSurfaceAdapter(
                    vehicle,
                    current["materials"],
                    patches,
                    view,
                    emissivities,
                    end_boundary_modes={"fore_end_reservoir": mode, "aft_end_reservoir": mode},
                    provenance={
                        "candidate_identity": actual_identity,
                        "finite_source": cfg["finite_record"],
                        "projection_reuse": projection_reuse,
                    },
                    surface_tolerance_w=n["common_surface_residual_w"],
                )
                output = run_thermal_topology(
                    vehicle,
                    current,
                    study,
                    False,
                    cells=n["radial_cells"],
                    max_step_s=n["max_step_s"],
                    scenario_index=scenario,
                    heat_flow_step_s=n["heat_flow_step_s"],
                    surface_exchange=adapter,
                )
                path = folder / (label + ".json")
                path.write_text(json.dumps(output))
                worst = min(
                    (r for r in output["peaks"] if r["margin_k"] is not None),
                    key=lambda r: r["margin_k"],
                )
                rows.append(
                    {
                        "case": case,
                        "corner": corner,
                        "end_reservoir_mode": mode,
                        "worst": worst,
                        "peaks": output["peaks"],
                        "energy_residual_j": output["energy_residual_j"],
                        "surface_exchange": output["surface_exchange"],
                        "output": str(path.relative_to(ROOT)),
                        "output_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                )
                print(
                    json.dumps(
                        {"case": label, "worst": worst, "elapsed_s": time.perf_counter() - started}
                    ),
                    flush=True,
                )
                (folder / "partial-summary.json").write_text(json.dumps(rows, indent=2))
    record = {
        "run_id": run_id,
        "source_sha256": hashes,
        "candidate_identity": actual_identity,
        "projection_reuse": projection_reuse,
        "numerical_settings": n,
        "cad_revision_sha256": source["cad_revision_sha256"],
        "inputs_unchanged": all(
            hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in hashes.items()
        ),
        "rows": rows,
        "matrix_scope": "fixed G54 coaxial proxy only; actual angular geometry and other configurations remain open",
        "full_existing_required_matrix_complete": False,
        "elapsed_s": time.perf_counter() - started,
        "cost_usd": 0,
        "engineering_acceptance_passed": False,
        "active_adoption": False,
        "flight_ready": False,
    }
    (folder / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(folder / "record.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
