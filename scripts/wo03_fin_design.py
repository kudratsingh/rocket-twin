"""Run the bounded WO-03 fin construction mass/stiffness screen."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.fin_design import run_trade
from src.vehicle.schema import load_vehicle, vehicle_input_paths


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def provenance_inputs(config_path: Path) -> dict[str, str]:
    """Hash only the fin-study source, vehicle identities and calculation closure."""
    config = yaml.safe_load(config_path.read_text())
    paths = {config_path.resolve()}
    for key in ("evidence_file", "engineering_inputs"):
        paths.add((ROOT / config["source_notes"][key]).resolve())
    paths.add((ROOT / "docs/wo03-material-evidence.md").resolve())
    paths.update(
        (ROOT / source).resolve()
        for source in (
            "scripts/wo03_fin_design.py",
            "src/analysis/fin_design.py",
            "src/cad/parts.py",
            "src/vehicle/cad_contract.py",
            "src/vehicle/geometry.py",
            "src/vehicle/schema.py",
            "src/vehicle/aero.py",
            "src/vehicle/mass.py",
        )
    )
    for entry in config["vehicles"]:
        vehicle_path = (ROOT / entry["path"]).resolve()
        paths.update(path.resolve() for path in vehicle_input_paths(vehicle_path))
        vehicle = load_vehicle(vehicle_path)
        if vehicle.motor:
            for source in (vehicle.motor.curve, vehicle.motor.cite):
                if source:
                    paths.add((ROOT / source).resolve())
    missing = sorted(str(path) for path in paths if not path.is_file())
    if missing:
        raise FileNotFoundError(f"Missing fin-study provenance inputs: {missing}")
    return {str(path.relative_to(ROOT)): file_sha256(path) for path in sorted(paths)}


def artifact_hashes(output: Path) -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): file_sha256(path)
        for path in sorted(output.iterdir())
        if path.is_file()
    }


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f"No rows to write: {path}")
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (
                        json.dumps(value, sort_keys=True)
                        if isinstance(value, (dict, list))
                        else value
                    )
                    for key, value in row.items()
                }
            )


def write_report(output: Path, result: dict[str, Any], preset: str) -> None:
    architecture_rows = result["architecture_rows"]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in architecture_rows:
        grouped.setdefault(row["screen_feasibility"], []).append(row)
    order = [
        "within both modeled load screens",
        "within 25 kPa screen only",
        "within 40 kPa screen only",
        "outside both modeled load screens",
    ]
    text = [
        "# WO-03 fin construction screen",
        "",
        f"Preset: `{preset}`. Config SHA-256: `{result['config_sha256']}`.",
        "",
        "This is a bounded static panel screen. It does not select or adopt a construction.",
        "The 40 kPa case is a 5 degree sensitivity bound, not all-alpha loading or an actual high-alpha G12 condition.",
        "No flutter, root joint/bond, skin wrinkling, core crushing, thermal derating, or manufacturing qualification is established.",
        "",
        "## Screen feasibility groups",
        "",
        "Groups below use the retained conservative tip-load upper displacement together with DF3 stress screens.",
        "The new distributed-load tapered-beam deflection is reported separately; it does not replace the tip-load upper screen.",
        "Neither status is a hardware pass or material selection.",
        "",
    ]
    for label in order:
        rows = sorted(grouped.get(label, []), key=lambda row: row["architecture"])
        text.append(f"### {label} ({len(rows)} constructions)")
        text.append("")
        if rows:
            text.append("| Construction | Mass (kg, 3 fins) | EI (N·m²/fin) | EI/mass |")
            text.append("|---|---:|---:|---:|")
            for row in rows:
                text.append(
                    f"| {row['architecture']} | {row['fin_mass_kg']:.4f} | "
                    f"{row['ei_n_m2_per_fin']:.3g} | {row['ei_per_fin_mass_n_m2_kg']:.3g} |"
                )
        else:
            text.append("No construction in this group.")
        text.append("")
    text.extend(
        [
            "## Static overlays",
            "",
            "`mode-static.csv` reports each candidate fin mass substituted into each finned mode, plus a separate 50 g tail-growth overlay at loaded and burnout mass states.",
            "The finless mode is retained as a non-applicable baseline with only the 50 g tail-growth overlay.",
            "Original vehicle objects/specifications are not modified.",
            "",
            "Material properties remain estimates or unsupported thickness transfers as stated in the study YAML and `docs/wo03-material-evidence.md`.",
            "CSV and JSON files retain per-case details, input identities, mass/centroid calculations, deflection decomposition, component stress and screen bounds.",
        ]
    )
    comparison = result["reference_2d_comparison"]
    text.extend(["## Archived 2D fin screen comparison", ""])
    if comparison["status"].startswith("identity and load checks match"):
        text.extend(
            [
                f"The matched archived S6 screen reports maximum displacement **{comparison['fea_max_displacement_m'] * 1000:.2f} mm**; the distributed tapered-beam diagnostic is **{comparison['distributed_beam_displacement_m'] * 1000:.2f} mm** ({comparison['relative_difference_model_minus_fea'] * 100:+.1f}%).",
                f"The archived material density is {comparison['fea_density_kg_m3']:.0f} kg/m³ and the candidate plywood mass density is {comparison['study_plywood_density_kg_m3']:.0f} kg/m³. Linear static displacement at fixed E, geometry, and force is independent of density; density changes candidate mass/CG and modal inertia/frequencies.",
                "This is one numerical screen comparison, not physical validation, calibration, or material qualification.",
                f"Source report: `{comparison['report_path']}` (SHA-256 `{comparison['report_sha256']}`).",
                "",
            ]
        )
    else:
        text.extend([f"No comparison was used: {comparison['status']}.", ""])
    rankings = result["trade_rankings"]
    text.extend(
        [
            "## Top three distributed-load trade ranks",
            "",
            "Ranks sum unweighted ordinal ranks for lower distributed deflection, higher DF3 stress margin, and higher worst 50 g aft-growth static margin. The conservative tip-load upper screen is shown but does not filter this comparative list.",
            "",
        ]
    )
    for mode in sorted({row["mode"] for row in rankings}):
        for load_case in sorted({row["load_case_id"] for row in rankings if row["mode"] == mode}):
            selected = [
                row
                for row in rankings
                if row["mode"] == mode and row["load_case_id"] == load_case and row["top_three"]
            ]
            text.append(f"### {mode} / {load_case}")
            text.append("")
            text.append(
                "| Rank | Construction | Distributed deflection (mm) | DF3 stress margin | Worst 50 g static margin (cal) | Tip-load upper screen |"
            )
            text.append("|---:|---|---:|---:|---:|---|")
            for row in selected:
                text.append(
                    f"| {row['trade_rank']} | {row['architecture']} | "
                    f"{row['distributed_tip_deflection_m'] * 1000:.2f} | "
                    f"{row['minimum_df3_stress_margin']:.3f} | "
                    f"{row['worst_50g_aft_growth_static_margin_cal']:.3f} | "
                    f"{'within' if row['upper_tip_load_screen_feasible'] else 'outside'} |"
                )
            text.append("")
    (output / "report.md").write_text("\n".join(text) + "\n")


def write_plot(output: Path, rows: list[dict[str, Any]]) -> None:
    colors = {
        "solid_plywood": "#247ba0",
        "solid_g10": "#e07a28",
        "plywood_balsa_sandwich": "#4c956c",
    }
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for category, color in colors.items():
        for geometry_ref, marker in (("G80-performance", "o"), ("G12-finned", "^")):
            selected = [
                row
                for row in rows
                if row["category"] == category and row["geometry_reference_mode"] == geometry_ref
            ]
            span_mm = round(selected[0]["span_m"] * 1000) if selected else 0
            ax.scatter(
                [row["fin_mass_kg"] for row in selected],
                [row["ei_n_m2_per_fin"] for row in selected],
                c=color,
                marker=marker,
                label=f"{category.replace('_', ' ')} ({span_mm} mm span)",
                s=46,
                alpha=0.85,
            )
    ax.set_xlabel("Candidate mass (kg, three fins including tabs/adhesive allowance)")
    ax.set_ylabel("Root-section EI (N·m² per fin)")
    ax.set_title("Candidate fin construction mass and bending stiffness")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.text(
        0.5,
        -0.02,
        "Ingredient-property estimates only; unresolved root/joint, flutter and thermal effects are not shown.",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout()
    fig.savefig(output / "fin-mass-stiffness.png", dpi=160, bbox_inches="tight")
    fig.savefig(output / "fin-mass-stiffness.svg", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/studies/wo03-fin-design.yaml")
    parser.add_argument("--preset", choices=("tiny", "sim"), default="tiny")
    parser.add_argument("--output", default="build/fin-design")
    args = parser.parse_args()
    config_path = (ROOT / args.config).resolve()
    output = (ROOT / args.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    inputs_before = provenance_inputs(config_path)
    result = run_trade(config_path, ROOT)
    write_csv(output / "fin-load-screen.csv", result["load_rows"])
    write_csv(output / "mode-static.csv", result["static_rows"])
    write_csv(output / "distributed-trade-rankings.csv", result["trade_rankings"])
    (output / "summary.json").write_text(
        json.dumps(
            {
                "schema": "rocket-twin.wo03_fin_design.v1",
                "preset": args.preset,
                "config": args.config,
                "config_sha256": result["config_sha256"],
                "source_identities": result["source_identities"],
                "material_input_sha256": result["material_input_sha256"],
                "reference_2d_comparison": result["reference_2d_comparison"],
                "constructions": result["architecture_rows"],
                "trade_rankings": result["trade_rankings"],
                "limitations": result["limitations"],
                "ranking_basis": "Modeled panel screen feasibility only; not a design selection.",
            },
            indent=2,
            allow_nan=False,
        )
        + "\n"
    )
    write_report(output, result, args.preset)
    write_plot(output, result["architecture_rows"])
    inputs_after = provenance_inputs(config_path)
    inputs_unchanged = inputs_before == inputs_after
    if not inputs_unchanged:
        changed = sorted(
            key
            for key in set(inputs_before) | set(inputs_after)
            if inputs_before.get(key) != inputs_after.get(key)
        )
        raise RuntimeError(f"Fin-study inputs changed during run: {changed}")
    now = datetime.now(UTC)
    run_id = f"wo03-fin-design-{now.strftime('%Y%m%dT%H%M%S%fZ')}"
    top_rank_rows = [row for row in result["trade_rankings"] if row["top_three"]]
    artifacts = artifact_hashes(output)
    record = {
        "schema": "rocket-twin.wo03_fin_design_run.v1",
        "work_order": "03",
        "run_id": run_id,
        "created_utc": now.isoformat(),
        "preset": args.preset,
        "study_config": str(config_path.relative_to(ROOT)),
        "input_sha256": inputs_before,
        "input_sha256_after": inputs_after,
        "inputs_unchanged": inputs_unchanged,
        "artifacts": artifacts,
        "counts": {
            "architectures": len(result["architecture_rows"]),
            "load_cases": len(result["load_rows"]),
            "static_overlays": len(result["static_rows"]),
            "trade_rank_rows": len(result["trade_rankings"]),
        },
        "reference_2d_comparison": result["reference_2d_comparison"],
        "top_three_distributed_trade_ranks": top_rank_rows,
        "acceptance": "open",
        "engineering_benchmark_passed": False,
        "flight_ready": False,
        "active_adoption": False,
        "cost_usd": 0,
        "limitations": result["limitations"],
    }
    run_folder = ROOT / "runs" / run_id
    run_folder.mkdir(parents=True, exist_ok=False)
    record_path = run_folder / "record.json"
    record_path.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    print(f"Wrote WO-03 fin construction screen to {output}")
    print(record_path)


if __name__ == "__main__":
    main()
