"""Static fin span/thickness and upper-body length sensitivity grid for WO-03.

All variants are in-memory copies. This screen does not select a design or validate
fin joints, slots, retention, drag, thermal behavior, or aeroelastic behavior.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from copy import deepcopy
from functools import cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / "build" / "fin-trade" / ".mplconfig"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml

from src.cad.parts import local_shape, properties
from src.vehicle.aero import center_of_pressure
from src.vehicle.mass import mass_properties
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import CADMass, Part, Vehicle, load_vehicle, vehicle_input_paths

DEFAULT_CONFIG = "configs/platform.yaml"
SPANS_M = (0.04, 0.05, 0.06, 0.07, 0.08, 0.095)
THICKNESSES_M = (0.002, 0.003, 0.004, 0.005)
EXTENSIONS_M = (0.0, 0.1, 0.2)
GROWTH_NOTE = (
    "Unresolved mount/tab/slot fit and load path; broader slots required by changed thickness "
    "are a design follow-up and are not represented as verified fit. Drag, thermal, material, "
    "joint, and aeroelastic behavior remain unvalidated. Source vehicle/motor identity is "
    "inherited from the named config and is not independently requalified by this static screen."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def with_cad_mass(part: Part, geometry: dict[str, Any]) -> Part:
    updated = part.model_copy(deep=True)
    updated.geometry = geometry
    # Rebuild the precise solid once for each unique geometry; properties are local.
    shape = local_shape(updated)
    props = properties(updated, shape)
    updated.cad_mass = CADMass.model_validate(props)
    updated.mass_kg = props["volume_m3"] * DENSITY_KG_M3[updated.material]
    updated.density_kg_m3 = None
    updated.cg_offset_m = max(0.0, -props["cg_local_body_m"][0])
    return updated


@cache
def cad_solid_stats(
    generator: str, geometry_json: str, parameters_json: str, material: str, mass_basis: str
) -> tuple[float, tuple[float, ...], tuple[tuple[float, ...], ...]]:
    # The actual CAD generation is done by local_shape through a minimal Part object.
    geometry = json.loads(geometry_json)
    parameters = json.loads(parameters_json)
    part = Part.model_validate(
        {
            "id": "grid_part",
            "type": "fin_set" if "span_m" in geometry else "body_tube",
            "parent": None,
            "position_m": 0,
            "geometry": geometry,
            "material": material,
            "mass_kg": 1e-3,
            "estimate": True,
            "learn": "Sensitivity grid geometry for preliminary static analysis.",
            "cad": {
                "generator": generator,
                "parameters": parameters,
                "mass_basis": mass_basis,
                "role": "manufactured",
                "moving_group": "fixed",
                "notes": "Sensitivity grid only.",
            },
        }
    )
    props = properties(part, local_shape(part))
    return (
        props["volume_m3"],
        tuple(props["cg_local_body_m"]),
        tuple(tuple(row) for row in props["inertia_per_kg_m2"]),
    )


def part_with_cached_mass(part: Part, geometry: dict[str, Any]) -> Part:
    updated = part.model_copy(deep=True)
    updated.geometry = geometry
    assert updated.cad is not None
    volume, centroid, inertia = cad_solid_stats(
        updated.cad.generator,
        json.dumps(geometry, sort_keys=True),
        json.dumps(updated.cad.parameters, sort_keys=True),
        updated.material,
        updated.cad.mass_basis,
    )
    # CADMass identity follows the source CAD contract (geometry and generator config).
    from src.vehicle.cad_contract import digest

    updated.cad_mass = CADMass(
        shape_sha256=digest(geometry, updated.cad.model_dump()),
        volume_m3=volume,
        cg_local_body_m=centroid,
        inertia_per_kg_m2=inertia,
        basis="bulk-density manufactured solid",
    )
    updated.mass_kg = volume * DENSITY_KG_M3[updated.material]
    updated.density_kg_m3 = None
    updated.cg_offset_m = max(0.0, -centroid[0])
    return updated


def source_vehicle_paths(config_path: Path) -> dict[str, Path]:
    platform = yaml.safe_load(config_path.read_text())
    paths = {Path(path).name: (ROOT / path).resolve() for path in platform["vehicles"]}
    selected: dict[str, Path] = {}
    for path in paths.values():
        vehicle = load_vehicle(path)
        if vehicle.id == "modular-performance-v1":
            selected["G80"] = path
        elif vehicle.id == "modular-tvc-finned-v1":
            selected["G12 finned"] = path
    g54_path = ROOT / "configs/vehicle/wo02/performance-g54.yaml"
    if g54_path.exists():
        selected["G54 conditional"] = g54_path
    missing = {"G80", "G54 conditional", "G12 finned"} - selected.keys()
    if missing:
        raise ValueError(
            f"platform config does not resolve required screen vehicles: {sorted(missing)}"
        )
    return {
        label: selected[label]
        for label in ("G80", "G54 conditional", "G12 finned")
        if label in selected
    }


def common_part_ids(path: Path) -> set[str]:
    raw = yaml.safe_load(path.read_text())
    shared = raw.get("shared")
    if not shared:
        return set()
    common = yaml.safe_load((path.parent / shared).read_text())
    return {part["id"] for part in common.get("parts", [])}


def variant_vehicle(
    source: Vehicle, common_ids: set[str], span: float, thickness: float, extension: float
) -> Vehicle:
    parts = []
    for original in source.parts:
        part = original.model_copy(deep=True)
        if part.id == "fin_set":
            geometry = dict(part.geometry)
            geometry["span_m"] = span
            geometry["thickness_m"] = thickness
            geometry["length_m"] = max(
                geometry["root_chord_m"], geometry["sweep_m"] + geometry["tip_chord_m"]
            )
            part = part_with_cached_mass(part, geometry)
        elif part.id == "body_upper":
            geometry = dict(part.geometry)
            geometry["length_m"] += extension
            part = part_with_cached_mass(part, geometry)
        if extension and (
            part.id not in common_ids or part.id in {"interface_coupler", "joint_stop"}
        ):
            part.position_m += extension
        parts.append(part)
    airframe = deepcopy(source.airframe)
    airframe["length_m"] += extension
    motor = source.motor.model_copy(deep=True) if source.motor else None
    if motor is not None:
        motor.mount_position_m += extension
    tvc = source.tvc.model_copy(deep=True) if source.tvc else None
    if tvc is not None:
        tvc.pivot_position_m += extension
    return source.model_copy(
        deep=True, update={"parts": parts, "airframe": airframe, "motor": motor, "tvc": tvc}
    )


def static_metrics(vehicle: Vehicle) -> dict[str, float]:
    cp = center_of_pressure(vehicle)
    props0 = mass_properties(vehicle, 0.0)
    props1 = mass_properties(vehicle, 1.0)
    allowance = vehicle.design.mass_allowance_kg if vehicle.design else 0.0
    tail = vehicle.airframe["length_m"]
    nominal_margin = (cp - props0.cg_m) / vehicle.airframe["body_diameter_m"]
    growth = [
        (cp - (p.mass_kg * p.cg_m + allowance * tail) / (p.mass_kg + allowance))
        / vehicle.airframe["body_diameter_m"]
        for p in (props0, props1)
    ]
    return {
        "mass_kg": props0.mass_kg,
        "cg_loaded_m": props0.cg_m,
        "cg_burnout_m": props1.cg_m,
        "cp_m": cp,
        "static_margin_nominal_cal": nominal_margin,
        "static_margin_aft_growth_worst_cal": min(growth),
        "mass_allowance_kg": allowance,
        "growth_station_m": tail,
        "inertia_loaded_xx_kg_m2": float(props0.inertia_kg_m2[0, 0]),
        "inertia_loaded_yy_kg_m2": float(props0.inertia_kg_m2[1, 1]),
        "inertia_loaded_zz_kg_m2": float(props0.inertia_kg_m2[2, 2]),
    }


def cad_part_metrics(part: Part) -> dict[str, Any]:
    if part.cad_mass is None:
        raise ValueError(f"{part.id} lacks recorded CAD mass properties")
    return {
        "volume_m3": part.cad_mass.volume_m3,
        "centroid_local_body_m": list(part.cad_mass.cg_local_body_m),
        "inertia_per_kg_m2": [list(row) for row in part.cad_mass.inertia_per_kg_m2],
    }


def run(config: Path, output: Path, preset: str) -> None:
    source_paths = source_vehicle_paths(config)
    configs: dict[str, tuple[Vehicle, set[str]]] = {}
    for label, path in source_paths.items():
        configs[label] = (load_vehicle(path), common_part_ids(path))
    source_inputs = {
        label: {
            str(input_path.relative_to(ROOT)): sha256(input_path)
            for input_path in vehicle_input_paths(path)
        }
        for label, path in source_paths.items()
    }
    rows: list[dict[str, Any]] = []
    for label, (source, common_ids) in configs.items():
        base_stats = static_metrics(source)
        part_lookup = {part.id: part for part in source.parts}
        base_fin_cad = cad_part_metrics(part_lookup["fin_set"])
        base_body_cad = cad_part_metrics(part_lookup["body_upper"])
        base_fin_mass = part_lookup["fin_set"].resolved_mass_kg
        base_body_mass = part_lookup["body_upper"].resolved_mass_kg
        fin_geometry = part_lookup["fin_set"].geometry
        reference = {
            "vehicle": label,
            "row_type": "current_reference",
            "span_m": fin_geometry["span_m"],
            "thickness_m": fin_geometry["thickness_m"],
            "root_chord_m": fin_geometry["root_chord_m"],
            "tip_chord_m": fin_geometry["tip_chord_m"],
            "sweep_m": fin_geometry["sweep_m"],
            "body_upper_length_m": part_lookup["body_upper"].geometry["length_m"],
            "vehicle_length_m": source.airframe["length_m"],
            "upper_extension_m": 0.0,
            **base_stats,
            "fin_mass_kg": base_fin_mass,
            "body_upper_mass_kg": base_body_mass,
            "delta_fin_mass_kg": 0.0,
            "delta_body_mass_kg": 0.0,
            "fin_cad": base_fin_cad,
            "body_upper_cad": base_body_cad,
            "fin_cad_volume_m3": base_fin_cad["volume_m3"],
            "body_upper_cad_volume_m3": base_body_cad["volume_m3"],
            "delta_inertia_loaded_xx_kg_m2": 0.0,
            "delta_inertia_loaded_yy_kg_m2": 0.0,
            "delta_inertia_loaded_zz_kg_m2": 0.0,
            "source_config": str(source_paths[label].relative_to(ROOT)),
            "source_sha256": sha256(source_paths[label]),
            "motor_id": source.motor.id if source.motor else None,
            "motor_curve": source.motor.curve if source.motor else None,
            "motor_curve_sha256": (
                sha256(ROOT / source.motor.curve)
                if source.motor and (ROOT / source.motor.curve).exists()
                else None
            ),
            "validation_flags": GROWTH_NOTE,
        }
        rows.append(reference)
        for span in SPANS_M:
            for thickness in THICKNESSES_M:
                for extension in EXTENSIONS_M:
                    variant = variant_vehicle(source, common_ids, span, thickness, extension)
                    stats = static_metrics(variant)
                    lookup = {part.id: part for part in variant.parts}
                    row = {
                        "vehicle": label,
                        "row_type": "grid",
                        "span_m": span,
                        "thickness_m": thickness,
                        "root_chord_m": fin_geometry["root_chord_m"],
                        "tip_chord_m": fin_geometry["tip_chord_m"],
                        "sweep_m": fin_geometry["sweep_m"],
                        "body_upper_length_m": lookup["body_upper"].geometry["length_m"],
                        "vehicle_length_m": variant.airframe["length_m"],
                        "upper_extension_m": extension,
                        **stats,
                        "fin_mass_kg": lookup["fin_set"].resolved_mass_kg,
                        "body_upper_mass_kg": lookup["body_upper"].resolved_mass_kg,
                        "delta_fin_mass_kg": lookup["fin_set"].resolved_mass_kg - base_fin_mass,
                        "delta_body_mass_kg": lookup["body_upper"].resolved_mass_kg
                        - base_body_mass,
                        "fin_cad": cad_part_metrics(lookup["fin_set"]),
                        "body_upper_cad": cad_part_metrics(lookup["body_upper"]),
                        "delta_inertia_loaded_xx_kg_m2": stats["inertia_loaded_xx_kg_m2"]
                        - base_stats["inertia_loaded_xx_kg_m2"],
                        "delta_inertia_loaded_yy_kg_m2": stats["inertia_loaded_yy_kg_m2"]
                        - base_stats["inertia_loaded_yy_kg_m2"],
                        "delta_inertia_loaded_zz_kg_m2": stats["inertia_loaded_zz_kg_m2"]
                        - base_stats["inertia_loaded_zz_kg_m2"],
                        "fin_cad_volume_m3": lookup["fin_set"].cad_mass.volume_m3,
                        "body_upper_cad_volume_m3": lookup["body_upper"].cad_mass.volume_m3,
                        "source_config": str(source_paths[label].relative_to(ROOT)),
                        "source_sha256": sha256(source_paths[label]),
                        "motor_id": source.motor.id if source.motor else None,
                        "motor_curve": source.motor.curve if source.motor else None,
                        "motor_curve_sha256": (
                            sha256(ROOT / source.motor.curve)
                            if source.motor and (ROOT / source.motor.curve).exists()
                            else None
                        ),
                        "validation_flags": GROWTH_NOTE,
                    }
                    rows.append(row)
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / "fin-trade-grid.csv"
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(
            {
                key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value
                for key, value in row.items()
            }
            for row in rows
        )
    results = {
        "schema": "rocket-twin.wo03_fin_trade.v1",
        "preset": preset,
        "config": str(config.relative_to(ROOT)),
        "config_sha256": sha256(config),
        "grid": {
            "span_m": SPANS_M,
            "thickness_m": THICKNESSES_M,
            "upper_extension_m": EXTENSIONS_M,
        },
        "row_count": len(rows),
        "reference_row_count": len(configs),
        "grid_row_count": len(rows) - len(configs),
        "source_vehicles": {
            label: {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256(path),
                "vehicle_id": vehicle.id,
                "motor_id": vehicle.motor.id if vehicle.motor else None,
                "motor_curve": vehicle.motor.curve if vehicle.motor else None,
                "motor_curve_sha256": (
                    sha256(ROOT / vehicle.motor.curve)
                    if vehicle.motor and (ROOT / vehicle.motor.curve).exists()
                    else None
                ),
                "input_sha256": source_inputs[label],
            }
            for label, path in source_paths.items()
            for vehicle in [configs[label][0]]
        },
        "method": "Static sensitivity only. CAD local_shape/properties and nominal density update fin_set/body_upper CADMass on in-memory copies; mass/CG/inertia and Barrowman CP/static margin use existing vehicle routines.",
        "limitations": [
            GROWTH_NOTE,
            "No motor/source identity reconciliation or aerodynamic drag recalculation was performed.",
            "This output does not select a design or establish a pass beyond the declared static margin screen.",
            "Motor and gimbal positions, airframe length and shifted aft part stations are modified only in copied vehicle objects.",
        ],
        "csv": str(csv_path.relative_to(ROOT)),
    }
    (output / "summary.json").write_text(json.dumps(results, indent=2, default=list) + "\n")
    plot_rows = [
        row for row in rows if row["row_type"] == "grid" and row["upper_extension_m"] == 0.0
    ]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for ax, label in zip(axes, configs):
        subset = [row for row in plot_rows if row["vehicle"] == label]
        for thickness in THICKNESSES_M:
            selected = [r for r in subset if r["thickness_m"] == thickness]
            selected.sort(key=lambda row: row["span_m"])
            ax.plot(
                [r["span_m"] * 100 for r in selected],
                [r["static_margin_aft_growth_worst_cal"] for r in selected],
                marker="o",
                label=f"{thickness * 1000:g} mm",
            )
        ax.axhline(0, color="#b23a48", linestyle="--", linewidth=1)
        ax.set_title(label)
        ax.set_xlabel("Fin span (cm)")
        ax.grid(alpha=0.25)
        ax.legend(title="Thickness", fontsize=8, frameon=False)
    axes[0].set_ylabel("Worst aft-growth static margin (cal)")
    fig.suptitle("Static margin sensitivity at zero upper extension", weight="bold")
    fig.text(
        0.5,
        -0.02,
        "Reference motor and current layout per configuration; estimated geometry/material inputs. No design selected.",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout()
    fig.savefig(output / "static-margin-span-thickness.png", dpi=160, bbox_inches="tight")
    fig.savefig(output / "static-margin-span-thickness.svg", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for label in configs:
        selected = [
            row
            for row in rows
            if row["vehicle"] == label
            and row["row_type"] == "grid"
            and row["span_m"] == 0.08
            and row["thickness_m"] == 0.002
        ]
        selected.sort(key=lambda row: row["upper_extension_m"])
        ax.plot(
            [row["upper_extension_m"] * 100 for row in selected],
            [row["static_margin_aft_growth_worst_cal"] for row in selected],
            marker="o",
            linewidth=2,
            label=label,
        )
    ax.axhline(0, color="#b23a48", linestyle="--", linewidth=1)
    ax.set_title("Aft-growth static margin vs upper-body extension")
    ax.set_xlabel("Added straight upper-body length (cm)")
    ax.set_ylabel("Worst aft-growth static margin (cal)")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.text(
        0.5,
        -0.01,
        "Current fin span/thickness held at each configuration's 80 mm / 2 mm reference.",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout()
    fig.savefig(output / "static-margin-upper-extension.png", dpi=160, bbox_inches="tight")
    fig.savefig(output / "static-margin-upper-extension.svg", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Platform config YAML")
    parser.add_argument("--preset", choices=("tiny", "sim"), default="tiny")
    parser.add_argument("--output", default="build/fin-trade")
    args = parser.parse_args()
    config = (ROOT / args.config).resolve()
    output = (ROOT / args.output).resolve()
    run(config, output, args.preset)
    print(f"Wrote sensitivity grid to {output}")


if __name__ == "__main__":
    main()
