"""Build one source-driven correction copy and evaluate integrated mass/static gates.

No active design is changed. Ring bridges use supported tube geometry and explicit
adhesive material, not a study-only shape that the normal CAD path cannot rebuild.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_fit_correction_study import _reconcile_copy
from scripts.wo03_fit_structure import make_candidate
from src.cad.assembly import export_vehicle, rigid_intersections
from src.vehicle.benchmark import evaluate_preliminary
from src.vehicle.schema import Part, Vehicle, load_vehicle, vehicle_input_paths


def package_copy(
    vehicle: Vehicle, cfg: dict[str, Any], fit: dict[str, Any], span: float
) -> Vehicle:
    candidate = make_candidate(vehicle, fit, True)
    parts = {part.id: part for part in candidate.parts}
    mount, shell = parts["motor_mount"], parts["aft_shell"]
    assert mount.cad and shell.cad
    if candidate.tvc:
        for name in ("tvc_gimbal", "gimbal_inner", "gimbal_frame"):
            part = parts[name]
            assert part.cad and part.engineering
            part.cad.parameters["pivot_bore_diameter_mm"] = cfg["pivots"]["bore_diameter_mm"]
            part.engineering.tolerances_mm["hole_diameter"] = cfg["pivots"][
                "bore_tolerance_diameter_mm"
            ]
            if part.cad.parameters.get("link_bore"):
                part.cad.parameters["link_bore"]["diameter_mm"] = cfg["linkage"]["bore_diameter_mm"]
            part.cad_mass = None
        for name in ("outer_pivots", "inner_pivots"):
            part = parts[name]
            assert part.cad and part.engineering
            for pin in part.cad.parameters["pins"]:
                # Preserve each center while replacing both pairs by one exact
                # seven-millimetre commercial dowel hypothesis.
                change = (pin["length_mm"] - cfg["pivots"]["pin_length_mm"]) / 2
                pin["start_mm"] = [
                    float(a) + change * float(b) for a, b in zip(pin["start_mm"], pin["axis"])
                ]
                pin["length_mm"] = cfg["pivots"]["pin_length_mm"]
                pin["radius_mm"] = cfg["pivots"]["pin_diameter_mm"] / 2
            part.engineering.tolerances_mm["diameter"] = cfg["pivots"]["pin_tolerance_diameter_mm"]
            part.cite = cfg["pivots"]["pin_source"]
            part.learn = cfg["pivots"]["pin_identity"] + ". " + cfg["pivots"]["note"]
            part.cad_mass = None
    else:
        mount.geometry["radius_m"] = cfg["fixed_mount"]["outer_radius_mm"] / 1000
        for index, (station, width) in enumerate(
            zip(
                mount.cad.parameters["ring_stations_mm"],
                mount.cad.parameters["ring_thicknesses_mm"],
                strict=True,
            )
        ):
            start = mount.position_m + station / 1000
            slot_start = shell.position_m + shell.cad.parameters["fin_slot_start_mm"] / 1000
            slot_end = slot_start + shell.cad.parameters["fin_slot_length_mm"] / 1000
            lo, hi = max(start, slot_start), min(start + width / 1000, slot_end)
            raw = shell.model_dump(by_alias=True)
            raw.update(
                {
                    "id": f"mount_shell_bond_{index}",
                    "parent": "motor_mount",
                    "type": "commercial",
                    "position_m": start,
                    "geometry": {
                        "length_m": width / 1000,
                        "radius_m": shell.geometry["inner_radius_m"],
                        "inner_radius_m": mount.geometry["radius_m"],
                        "wall_m": cfg["fixed_mount"]["bond_gap_m"],
                    },
                    "material": "epoxy",
                    "mass_kg": 1e-6,
                    "density_kg_m3": None,
                    "cad_mass": None,
                    "cg_offset_m": width / 2000,
                    "learn": "Controlled-gap epoxy ring bridges the mount OD to the shell. Fin openings remain cut; bond wetting, peel, creep and hot strength require verification.",
                    "build": {
                        "method": "bonded",
                        "cost_usd": 0.5,
                        "generator": "tube",
                        "notes": "Estimated cured adhesive, not purchased rigid stock; inspect and weigh representative joints.",
                    },
                    "cad": {
                        "generator": "tube",
                        "parameters": {
                            "fin_slots": hi > lo,
                            "fin_slot_start_mm": max(0, (lo - start) * 1000),
                            "fin_slot_length_mm": max(0, (hi - lo) * 1000),
                            "fin_slot_width_mm": shell.cad.parameters["fin_slot_width_mm"],
                        },
                        "mass_basis": "volume_density",
                        "role": "manufactured",
                        "moving_group": "fixed",
                        "color": "#bfa174",
                        "notes": "Actual adhesive-volume estimate; no strength inferred from a solid.",
                    },
                }
            )
            raw["engineering"].update(
                material_profile="epoxy",
                function="Mount-to-shell adhesive load and thermal bridge",
                tolerances_mm={"linear": 0.18},
            )
            candidate.parts.append(Part.model_validate(raw))
        # Fillets are additional to the existing shared finish and glue budget.
        raw = parts["adhesive_finish"].model_dump(by_alias=True)
        raw.update(
            id="mount_bond_fillets",
            parent="motor_mount",
            position_m=mount.position_m,
            mass_kg=cfg["fixed_mount"]["additional_fillet_mass_kg"],
            cad_mass=None,
            cg_offset_m=mount.geometry["length_m"] / 2,
        )
        raw["learn"] = (
            "Additional mount-ring fillet mass allowance; geometry and mass distribution require coupon/assembly measurements. Not deducted from general finish."
        )
        candidate.parts.append(Part.model_validate(raw))
    if "g54" in candidate.id:
        parts["fin_set"].geometry["span_m"] = span
        parts["fin_set"].cad_mass = None
        candidate.aero.passive_stubs.span_m = span
    # The full normal loader validates the copy after source edits; stale caches
    # on edited geometry must never be carried into the reference adapters.
    return Vehicle.model_validate(candidate.model_dump(by_alias=True))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-correction-package.yaml")
    )
    p.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    args = p.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    fit_cfg = yaml.safe_load(Path(cfg["fit_study"]).read_text())
    fit = next(row for row in fit_cfg["packages"] if row["id"] == "fit-package-a")
    inputs = {
        args.config,
        Path(cfg["fit_study"]),
        Path(__file__),
        Path("src/analysis/motor_support.py"),
    }
    inputs.update(Path("src/cad").glob("*.py"))
    inputs.update(Path("src/vehicle").glob("*.py"))
    for path in cfg["configurations"].values():
        inputs.update(vehicle_input_paths(path))

    def hashes() -> dict[str, str]:
        return {
            str(path.resolve().relative_to(Path.cwd())): hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            for path in sorted(inputs)
        }

    before = hashes()
    run = datetime.now(UTC).strftime("wo03-correction-package-%Y%m%dT%H%M%S%fZ")
    out = Path("build") / run
    out.mkdir(parents=True)
    results = []
    for label, path in cfg["configurations"].items():
        for span in cfg["g54_fin_span_candidates_m"] if label == "G54" else [0.07]:
            original = load_vehicle(path)
            vehicle = package_copy(original, cfg, fit, float(span))
            folder = out / f"{label}-{span:.3f}"
            manifest, solids = export_vehicle(vehicle, folder / "cad", export=False)
            vehicle = _reconcile_copy(vehicle, {part.id for part in vehicle.parts}, manifest)
            # Check the reconciled specification, rather than retaining the
            # pre-reconciliation comparison against the superseded masses.
            manifest, solids = export_vehicle(vehicle, folder / "cad", export=False)
            copy_path = folder / "resolved-candidate.yaml"
            copy_path.write_text(yaml.safe_dump(vehicle.model_dump(by_alias=True), sort_keys=False))
            alias = Path("build/wo03-correction-package/latest") / folder.name
            alias.mkdir(parents=True, exist_ok=True)
            alias_path = alias / copy_path.name
            shutil.copyfile(copy_path, alias_path)
            screen = evaluate_preliminary(vehicle, compare=True)
            results.append(
                {
                    "configuration": label,
                    "g54_span_m": span if label == "G54" else None,
                    "candidate_path": str(copy_path),
                    "candidate_alias_path": str(alias_path),
                    "candidate_sha256": hashlib.sha256(copy_path.read_bytes()).hexdigest(),
                    "static": screen,
                    "neutral_intersections": rigid_intersections(vehicle, solids),
                    "nominal_cad_mass_passed": manifest["mass_benchmark_passed"],
                    "active_adoption": False,
                }
            )
            print(
                label,
                span,
                round(screen["nominal_mass_kg"] * 1000, 3),
                screen["static_margins_with_aft_mass_allowance_cal"],
                screen["launch_screen"]["rail_exit_speed_mps"],
                flush=True,
            )
    payload = {
        "run_id": run,
        "source_hashes": before,
        "inputs_unchanged": before == hashes(),
        "results": results,
        "active_adoption": False,
        "expanded_wo03_passed": False,
        "flight_ready": False,
    }
    record = Path("runs") / run / "record.json"
    record.parent.mkdir(parents=True)
    record.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    # A portable rebuild entry point. The immutable run retains its original
    # paths and hashes; consumers verify the alias bytes against that record.
    latest = Path("build/wo03-correction-package/latest-record.json")
    latest.parent.mkdir(parents=True, exist_ok=True)
    latest.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    print(record)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
