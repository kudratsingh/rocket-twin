"""Run nominal-geometry fin fields and export source-identity-bound records.

This complements minimum-thickness screens: it uses the actual resolved 6.35 mm
fin geometry so the AnalysisRecord can match active CAD shape identity. One mesh
is a calculated, unvalidated field case; no mesh convergence or attachment pass
is inferred. Identical local fin shapes may share solver fields while each mode
gets a separate vehicle-identity-bound AnalysisRecord.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_fin_acceptance import ORTHOTROPIC, panel_force_n
from src.analysis.fin_fea import run_shell
from src.analysis.fin_fields import export_fin_fields
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import Part, Vehicle, load_vehicle, vehicle_input_paths


def _hashes(paths: set[Path], root: Path) -> dict[str, str]:
    return {
        path.resolve()
        .relative_to(root.resolve())
        .as_posix(): hashlib.sha256(path.read_bytes())
        .hexdigest()
        for path in sorted(paths)
        if path.is_file()
    }


def _fin(vehicle: Vehicle) -> Part:
    part = next((part for part in vehicle.parts if part.type == "fin_set"), None)
    if part is None or part.cad_mass is None or part.cad is None:
        raise ValueError(f"{vehicle.id}: resolved fin_set with CAD identity is required")
    return part


def _shape_hash(fin: Part) -> str:
    if fin.cad_mass is None:
        raise ValueError(f"{fin.id}: CAD shape identity is unavailable")
    return fin.cad_mass.shape_sha256


def _same_local_panel(parent: Part, target: Part) -> dict[str, bool]:
    return {
        "same_cad_shape_sha256": parent.cad_mass is not None
        and target.cad_mass is not None
        and parent.cad_mass.shape_sha256 == target.cad_mass.shape_sha256,
        "same_fin_material": parent.material == target.material,
        "same_geometry": parent.geometry == target.geometry,
        "same_cad_parameters": parent.cad is not None
        and target.cad is not None
        and parent.cad.parameters == target.cad.parameters,
        "same_material_density": DENSITY_KG_M3.get(parent.material)
        == DENSITY_KG_M3.get(target.material),
        "same_40kpa_5deg_panel_force": math.isclose(
            panel_force_n(parent, 40_000.0, 5.0),
            panel_force_n(target, 40_000.0, 5.0),
            rel_tol=1e-12,
            abs_tol=1e-12,
        ),
    }


def run_nominal_fields(vehicle_paths: list[Path], output_root: Path) -> list[Path]:
    root = Path.cwd()
    loaded = [
        (
            path if path.is_absolute() else root / path,
            load_vehicle(path if path.is_absolute() else root / path),
        )
        for path in vehicle_paths
    ]
    run_id = "wo03-fin-nominal-fields-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    computed: dict[str, tuple[Part, Path, dict[str, Any], str]] = {}
    reports: list[Path] = []
    inputs_common = {
        Path("scripts/wo03_fin_nominal_fields.py"),
        Path("scripts/wo03_fin_acceptance.py"),
        Path("src/analysis/fin_fea.py"),
        Path("src/analysis/fin_fields.py"),
        Path("src/vehicle/materials.py"),
        Path("src/vehicle/schema.py"),
        Path("src/cad/parts.py"),
        Path("src/cad/assembly.py"),
        Path("configs/engineering/wo03.yaml"),
    }
    for config_path, vehicle in loaded:
        fin = _fin(vehicle)
        if fin.cad_mass is None:
            raise ValueError(f"{vehicle.id}: resolved fin CAD mass identity is missing")
        cad_shape_sha256 = fin.cad_mass.shape_sha256
        force = panel_force_n(fin, 40_000.0, 5.0)
        cache_key = cad_shape_sha256
        parent = computed.get(cache_key)
        mode_dir = output_root / vehicle.id / run_id
        mode_dir.mkdir(parents=True, exist_ok=False)
        source_paths = set(vehicle_input_paths(config_path)) | {config_path} | inputs_common
        hash_before = _hashes(source_paths, root)
        if parent is None:
            fea_folder = mode_dir / "nominal-actual-geometry" / "5.0mm"
            result = run_shell(
                fea_folder,
                fin,
                5.0,
                force_n=force,
                orthotropic=ORTHOTROPIC,
            )
            computed[cache_key] = (fin, fea_folder, result, run_id)
            parent_checks = {"solver_run_performed_for_this_vehicle": True}
            parent_vehicle_id = vehicle.id
            parent_fea_run_id = run_id
        else:
            parent_fin, fea_folder, result, parent_fea_run_id = parent
            parent_checks = _same_local_panel(parent_fin, fin)
            if not all(parent_checks.values()):
                raise ValueError(
                    f"{vehicle.id}: shape cache key matched but panel equivalence checks failed"
                )
            parent_vehicle_id = next(
                item.id for _, item in loaded if item.parts and _shape_hash(_fin(item)) == cache_key
            )
        identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
        record = export_fin_fields(
            vehicle,
            fea_folder,
            mode_dir / "analysis-record",
            run_id,
            hash_before,
            known_case_verified=False,
            mesh_converged=False,
        )
        hash_after = _hashes(source_paths, root)
        report = {
            "run_id": run_id,
            "vehicle_id": vehicle.id,
            "source_config": config_path.resolve().relative_to(root.resolve()).as_posix(),
            "resolved_spec_sha256": identity,
            "actual_fin_shape_sha256": cad_shape_sha256,
            "nominal_geometry": {
                "thickness_m": float(fin.geometry["thickness_m"]),
                "span_m": float(fin.geometry["span_m"]),
                "root_chord_m": float(fin.geometry["root_chord_m"]),
                "tip_chord_m": float(fin.geometry["tip_chord_m"]),
                "sweep_m": float(fin.geometry["sweep_m"]),
                "material": fin.material,
                "density_kg_m3": float(DENSITY_KG_M3[fin.material]),
            },
            "load_case": {
                "pressure_pa": 40_000.0,
                "angle_deg": 5.0,
                "force_per_fin_n": force,
                "basis": "Independent bounded nominal panel case; not the actual coincident flight force.",
            },
            "mesh_target_mm": 5.0,
            "mesh_result": result,
            "analysis_record": record.model_dump(mode="json"),
            "analysis_record_export": {
                "status": "exported exact nominal CAD identity",
                "configuration_id": vehicle.id,
                "resolved_spec_sha256": identity,
                "part_shape_sha256": cad_shape_sha256,
                "mesh_converged": False,
                "known_case_verified": False,
                "physical_validation": "unvalidated",
                "coverage": "Registered 2D S6 midsurface mesh, nodal displacement magnitude and element spanwise-stress component only; no CAD faces or attachment stress are fabricated.",
            },
            "panel_cache": {
                "parent_vehicle_id": parent_vehicle_id,
                "parent_nominal_fea_run_id": parent_fea_run_id,
                "checks": parent_checks,
                "scope": "Reuse covers only the identical local fin panel solver fields; each AnalysisRecord uses this target vehicle's resolved spec and CAD identity.",
            },
            "acceptance": "open",
            "acceptance_passed": False,
            "flight_ready": False,
            "input_sha256_before": hash_before,
            "input_sha256_after": hash_after,
            "inputs_unchanged": hash_before == hash_after,
            "cost_usd": 0,
        }
        report_path = mode_dir / "report.json"
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
        reports.append(report_path)
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vehicle", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, default=Path("build/wo03-fin-nominal-fields"))
    args = parser.parse_args()
    reports = run_nominal_fields(args.vehicle, args.output)
    print("\n".join(str(path) for path in reports))
    return 0 if all(json.loads(path.read_text())["inputs_unchanged"] for path in reports) else 2


if __name__ == "__main__":
    raise SystemExit(main())
