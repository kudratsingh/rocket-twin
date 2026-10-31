"""Create inspectable, unadopted G80 fin-planform CAD and static comparisons."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.cad.assembly import export_vehicle, rigid_intersections
from src.cad.parts import cq, local_shape, properties
from src.vehicle.aero import center_of_pressure
from src.vehicle.mass import mass_properties
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import CADMass, load_vehicle, vehicle_input_paths


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gusset_outside_panel(fin) -> dict:
    """Compare generated gusset material to the full tapered panel footprint."""
    full = local_shape(fin)
    plain = fin.model_copy(deep=True)
    for key in ("root_gusset_span_mm", "root_gusset_base_mm", "root_gusset_inset_mm"):
        plain.cad.parameters.pop(key, None)
    gussets = full.cut(local_shape(plain))
    g = fin.geometry
    r, span, root, tip, sweep = [
        float(g[k]) * 1000 for k in ("radius_m", "span_m", "root_chord_m", "tip_chord_m", "sweep_m")
    ]
    panel = (
        cq.Workplane("XZ")
        .polyline([(r - 1, 0), (r + span, sweep), (r + span, sweep + tip), (r - 1, root)])
        .close()
        .extrude(20, both=True)
        .val()
    )
    mask = cq.Compound.makeCompound(
        [panel.rotate((0, 0, 0), (0, 0, 1), i * 360 / g["count"]) for i in range(g["count"])]
    )
    outside = gussets.cut(mask)
    return {
        "generated_gusset_volume_mm3": gussets.Volume(),
        "outside_panel_footprint_mm3": outside.Volume(),
        "interpretation": "Gusset outside a 1 mm root-extended panel projection; root extension admits cylindrical body feet. This is not a fillet, strength model or fit proof.",
    }


def run(config: Path, output: Path) -> None:
    cfg = yaml.safe_load(config.read_text())
    base_path = Path(cfg["base_vehicle"])
    inputs = {config, base_path, Path(__file__), *vehicle_input_paths(base_path)}
    inputs.update(Path("src/cad").glob("*.py"))
    inputs.update(Path("src/vehicle").glob("*.py"))
    before = {str(p): sha(p) for p in sorted(inputs) if p.is_file()}
    base = load_vehicle(base_path)
    assert base.design and base.motor and base.motor.curve
    inputs.update([Path(base.motor.curve), Path(base.motor.curve).with_suffix(".yaml")])
    before = {str(p): sha(p) for p in sorted(inputs) if p.is_file()}
    output.mkdir(parents=True, exist_ok=True)
    index = []
    for option in cfg["candidates"]:
        v = base.model_copy(deep=True)
        v.id = option["id"]
        v.name = option["label"] + " — experimental G80 fin study"
        fin = next(part for part in v.parts if part.id == "fin_set")
        assert fin.cad
        fin.geometry.update(
            span_m=option["span_m"],
            tip_chord_m=option["tip_chord_m"],
            sweep_m=option["leading_edge_sweep_m"],
        )
        fin.cad_mass = None
        props = properties(fin, local_shape(fin))
        fin.cad_mass = CADMass.model_validate(props)
        fin.mass_kg = props["volume_m3"] * DENSITY_KG_M3[fin.material]
        fin.cg_offset_m = -props["cg_local_body_m"][0]
        folder = output / option["id"]
        folder.mkdir(parents=True, exist_ok=True)
        resolved_path = folder / "resolved-candidate.yaml"
        resolved_path.write_text(yaml.safe_dump(v.model_dump(by_alias=True), sort_keys=False))
        reloaded = load_vehicle(resolved_path)
        manifest, solids = export_vehicle(reloaded, folder / "cad", True)
        intersections = rigid_intersections(reloaded, solids, moving_ids={"fin_set"})
        props_load = mass_properties(reloaded, 0)
        props_burn = mass_properties(reloaded, 1)
        cp = center_of_pressure(reloaded)
        allowance = reloaded.design.mass_allowance_kg
        margins = [
            (
                cp
                - (p.mass_kg * p.cg_m + allowance * reloaded.airframe["length_m"])
                / (p.mass_kg + allowance)
            )
            / reloaded.airframe["body_diameter_m"]
            for p in (props_load, props_burn)
        ]
        fin_current = next(p for p in reloaded.parts if p.id == "fin_set")
        geom = fin_current.geometry
        extents = {
            "fin_front_station_m": fin_current.position_m,
            "root_end_station_m": fin_current.position_m + geom["root_chord_m"],
            "tip_front_station_m": fin_current.position_m + geom["sweep_m"],
            "tip_end_station_m": fin_current.position_m + geom["sweep_m"] + geom["tip_chord_m"],
            "body_aft_station_m": reloaded.airframe["length_m"],
            "tip_within_body_aft_envelope": fin_current.position_m
            + geom["sweep_m"]
            + geom["tip_chord_m"]
            <= reloaded.airframe["length_m"] + 1e-12,
            "tab_and_mount_parameters_unchanged": all(
                fin_current.cad.parameters[k]
                == next(p for p in base.parts if p.id == "fin_set").cad.parameters[k]
                for k in ("tab_depth_mm", "tab_length_mm", "tab_offset_mm")
            ),
        }
        stats = {
            "configuration_id": v.id,
            "accepted": False,
            "role": "experimental",
            "spec_sha256": sha(resolved_path),
            "mass_kg": props_load.mass_kg,
            "burnout_mass_kg": props_burn.mass_kg,
            "cg_station_m": props_load.cg_m,
            "burnout_cg_station_m": props_burn.cg_m,
            "inertia_kg_m2": props_load.inertia_kg_m2.tolist(),
            "burnout_inertia_kg_m2": props_burn.inertia_kg_m2.tolist(),
            "cp_station_m": cp,
            "full_50g_aft_growth_static_margin_cal": margins,
            "fin_mass_kg": fin_current.resolved_mass_kg,
            "one_fin_planform_area_m2": geom["span_m"]
            * (geom["root_chord_m"] + geom["tip_chord_m"])
            / 2,
            "fin_tip_root_ratio": geom["tip_chord_m"] / geom["root_chord_m"],
            "fin_geometry": geom,
            "geometry_bounds": extents,
            "gusset_footprint": gusset_outside_panel(fin_current),
            "fin_related_rigid_intersections": intersections,
            "intersection_method": "Only rigid pairs touching fin_set; existing intentional contact is not excluded; no tolerance, bond or manufacturing verification.",
            "cad_mass_reconciled": manifest["mass_benchmark_passed"],
            "fin_solid_valid": next(
                p["valid_solid"] for p in manifest["parts"] if p["id"] == "fin_set"
            ),
            "bevel_and_roundover": "not modeled; native generator creates square edges",
            "drag_difference": None,
            "altitude_difference": None,
            "engineering_status": "unvalidated study; panel/root strength, flutter, drag, heat and recovery remain open",
        }
        report_path = folder / "comparison.json"
        report_path.write_text(json.dumps(stats, indent=2, allow_nan=False) + "\n")
        manifest_path = folder / "cad" / "manifest.json"
        entry = {
            "id": v.id,
            "label": option["label"],
            "path": str(resolved_path),
            "manifest_path": str(manifest_path),
            "role": "experimental",
            "accepted": False,
            "spec_sha256": sha(resolved_path),
            "resolved_spec_sha256": manifest["identity"]["resolved_spec_sha256"],
            "cad_revision_sha256": manifest["identity"]["cad_revision_sha256"],
            "fin_shape_sha256": manifest["identity"]["part_shape_sha256"]["fin_set"],
            "fin_glb_sha256": sha(folder / "cad" / "parts" / "fin_set.glb"),
            "assembly_glb_sha256": sha(folder / "cad" / "assembly.glb"),
            "comparison_path": str(report_path),
        }
        index.append(entry)
        print(
            v.id,
            "mass_g",
            round(props_load.mass_kg * 1000, 3),
            "cp_m",
            round(cp, 6),
            "growth_margin",
            [round(x, 4) for x in margins],
            "outside_gusset_mm3",
            round(stats["gusset_footprint"]["outside_panel_footprint_mm3"], 2),
            "fin_intersections",
            len(intersections),
            flush=True,
        )
    after = {str(p): sha(p) for p in sorted(inputs) if p.is_file()}
    payload = {
        "status": "experimental candidates, not adopted",
        "accepted": False,
        "flight_ready": False,
        "input_sha256": before,
        "inputs_unchanged": before == after,
        "candidates": index,
    }
    (output / "latest.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    print(output / "latest.json", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-aerodynamic-fin-trade.yaml")
    )
    parser.add_argument("--preset", choices=["tiny", "sim", "rl", "real"], default="tiny")
    parser.add_argument("--output", type=Path, default=Path("build/wo03-aerodynamic-fin-trade"))
    args = parser.parse_args()
    run(args.config, args.output)


if __name__ == "__main__":
    main()
