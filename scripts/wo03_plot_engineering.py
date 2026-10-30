"""Render report plots from a recorded WO-03 engineering screen and exports."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parents[1] / ".cache" / "mpl"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = "runs/wo03-engineering-20261030T163229838627Z/record.json"
TARGETS = {
    "G80": ("modular-performance-v1", "G80 fixed-motor performance"),
    "G54": ("modular-performance-g54-hypothesis", "G54 performance hypothesis"),
    "G12": ("modular-tvc-finned-v1", "G12 finned TVC upper-hot-soak"),
}
PART_LABELS = {
    "motor_liner": "Motor liner",
    "motor_mount": "Motor mount",
    "aft_shell": "Aft shell",
    "fin_bonds": "Fin bonds",
    "tvc_gimbal": "TVC gimbal",
    "gimbal_frame": "Gimbal frame",
    "gimbal_inner": "Inner gimbal",
    "servo_pitch": "Pitch servo",
    "servo_yaw": "Yaw servo",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def vehicle_record(record: dict, vehicle_id: str) -> dict:
    return next(item for item in record["vehicles"] if item["vehicle"] == vehicle_id)


def manifest_data(record_path: Path, vehicle: dict) -> tuple[Path, dict, Path]:
    manifest_path = ROOT / vehicle["analysis_manifest"]
    manifest = load_json(manifest_path)
    return manifest_path, manifest, manifest_path.parent


def field_entry(manifest: dict, field_id: str) -> dict:
    return next(item for item in manifest["fields"] if item["id"] == field_id)


def style() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "figure.dpi": 120,
            "savefig.dpi": 160,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.22,
        }
    )


def thermal_plot(
    label: str, vehicle: dict, manifest: dict, manifest_dir: Path, outdir: Path, hashes: dict
) -> None:
    entry = field_entry(manifest, "upper-hot-soak-temperature")
    asset = manifest_dir / entry["artifact"]
    hashes[str(asset.relative_to(ROOT))] = sha256(asset)
    series = load_json(asset)
    t = np.asarray(entry["times_s"], dtype=float)
    # Each panel groups components by physical role to keep the legend readable.
    groups = [
        ("Motor and aft structure", ["motor_liner", "motor_mount", "aft_shell"]),
        ("Thermal protection and fin joint", ["fin_bonds", "thermal_guard"]),
        (
            "Gimbal and servos",
            ["tvc_gimbal", "gimbal_frame", "gimbal_inner", "servo_pitch", "servo_yaw"],
        ),
    ]
    values = np.asarray(series["values"], dtype=object)
    part_idx = {part: i for i, part in enumerate(series["part_ids"])}
    limits = {}
    for case in vehicle["thermal"]:
        if case["case"] == "upper-hot-soak":
            limits = {p["part_id"]: p["screen_limit_c"] for p in case["peaks"]}
    fig, axes = plt.subplots(1, 3, figsize=(12.2, 4.1), sharex=True, sharey=True)
    palette = plt.get_cmap("tab10")
    for ax, (title, parts) in zip(axes, groups):
        any_line = False
        for n, part in enumerate(parts):
            if part not in part_idx:
                continue
            arr = np.asarray(
                [np.nan if x is None else float(x) - 273.15 for x in values[:, part_idx[part]]]
            )
            if np.all(np.isnan(arr)):
                continue
            color = palette(n)
            ax.plot(
                t,
                arr,
                label=PART_LABELS.get(part, part.replace("_", " ").title()),
                color=color,
                linewidth=2,
            )
            lim = limits.get(part)
            if lim is not None:
                ax.axhline(lim, color=color, linestyle="--", linewidth=1, alpha=0.8)
                ax.text(
                    0.99,
                    lim,
                    f" {lim:g}°C",
                    color=color,
                    fontsize=8,
                    ha="right",
                    va="bottom",
                    transform=ax.get_yaxis_transform(),
                )
            any_line = True
        ax.set_title(title)
        ax.set_xlabel("Time from ignition (s)")
        if any_line:
            ax.legend(loc="best", fontsize=8, frameon=False)
    axes[0].set_ylabel("Uniform part mean temperature (°C)")
    fig.suptitle(
        f"{label}: upper hot-soak temperature histories", y=1.01, fontsize=14, weight="bold"
    )
    fig.text(
        0.5,
        -0.03,
        "Exploratory lumped means from estimated inputs; case boundary 250°C peak, ambient 35°C, τ=120 s. "
        "Dashed lines are recorded part limits. Unvalidated; not measured temperatures.",
        ha="center",
        fontsize=8.5,
    )
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(outdir / f"{label.lower()}-upper-hot-soak.{ext}", bbox_inches="tight")
    plt.close(fig)


def structural_plot(records: dict[str, dict], outdir: Path) -> None:
    labels = list(records)
    entries: list[tuple[str, str, list[float], str]] = []
    entries.append(("Strength margin", "margin", [], "1"))
    entries.append(("Euler buckling margin", "buckling_margin", [], "1"))
    entries.append(("Fin tip deflection / 1 mm screen", "deflection", [], "ratio"))
    for vehicle in records.values():
        rows = vehicle["structural"]["rows"]
        motor = next(row for row in rows if row["part_id"] == "motor_mount")
        fin = next((row for row in rows if row["part_id"] == "fin_set"), None)
        entries[0][2].append(min([r["margin"] for r in rows]))
        entries[1][2].append(motor["buckling_margin"])
        entries[2][2].append(
            float("nan")
            if fin is None
            else fin["tip_deflection_upper_m"] / fin["deflection_limit_m"]
        )
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.0))
    x = np.arange(len(labels))
    for ax, (title, _, vals, unit) in zip(axes, entries):
        vals_array = np.asarray(vals)
        colors = [
            "#c83e4d" if (v > 1 if unit == "ratio" else v < 0) else "#247ba0" for v in vals_array
        ]
        ax.bar(x, vals_array, color=colors, width=0.62)
        ax.axhline(0 if unit == "1" else 1, color="#333333", linewidth=1.2, linestyle="--")
        for xx, value in zip(x, vals_array):
            if np.isfinite(value):
                ax.text(
                    xx,
                    value,
                    f" {value:.2f}",
                    ha="center",
                    va="bottom" if value >= 0 else "top",
                    fontsize=8,
                )
        ax.set_xticks(x, labels, rotation=25, ha="right")
        ax.set_title(title)
        ax.set_ylabel("Margin (pass ≥ 0)" if unit == "1" else "Screen limit multiple (pass ≤ 1)")
    fig.suptitle("Recorded structural screening results", fontsize=14, weight="bold")
    fig.text(
        0.5,
        -0.04,
        "Red indicates a recorded screen failure. Values copied from run summary; no physics recomputed. "
        "Estimated properties; not converged FEA or qualified hardware.",
        ha="center",
        fontsize=8.5,
    )
    fig.tight_layout()
    for ext in ("png", "svg"):
        fig.savefig(outdir / f"structural-screen-margins.{ext}", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_RECORD, help="WO-03 run record JSON")
    parser.add_argument("--preset", choices=("tiny", "sim"), default="sim")
    parser.add_argument("--output", default="build/engineering-plots")
    args = parser.parse_args()
    record_path = (ROOT / args.config).resolve()
    outdir = (ROOT / args.output).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    record = load_json(record_path)
    hashes = {str(record_path.relative_to(ROOT)): sha256(record_path)}
    structural = {}
    manifests = {}
    for label, (vehicle_id, _) in TARGETS.items():
        vehicle = vehicle_record(record, vehicle_id)
        manifest_path, manifest, manifest_dir = manifest_data(record_path, vehicle)
        hashes[str(manifest_path.relative_to(ROOT))] = sha256(manifest_path)
        manifests[label] = {
            "vehicle": vehicle_id,
            "manifest": str(manifest_path.relative_to(ROOT)),
            "manifest_sha256": hashes[str(manifest_path.relative_to(ROOT))],
            "resolved_spec_sha256": manifest["identity"]["resolved_spec_sha256"],
        }
        thermal_plot(label, vehicle, manifest, manifest_dir, outdir, hashes)
        structural[label] = vehicle
    structural_plot(structural, outdir)
    # Record exact hashes for source record, manifests and plotted field assets.
    provenance = {
        "source_record": str(record_path.relative_to(ROOT)),
        "source_record_sha256": hashes[str(record_path.relative_to(ROOT))],
        "run_id": record["run_id"],
        "preset": args.preset,
        "manifests": manifests,
        "hashed_inputs": hashes,
        "history_case": "upper-hot-soak",
        "boundary_inputs": {
            "external_case_peak_c": 250,
            "ambient_c": 35,
            "cooling_tau_s": 120,
            "status": "estimated exploratory scenario inputs",
        },
        "limitations": [
            "Temperatures are calculated uniform part means from estimated lumped-model inputs, not measured temperatures.",
            "The recorded thermal histories have no validated current vehicle identity or hardware correlation.",
            "Structural values are preliminary screens from the source record; no physics is recomputed here.",
            "These plots are not converged rocket FEA, qualification evidence, or release to flight.",
        ],
    }
    (outdir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(f"Wrote report figures and provenance to {outdir}")


if __name__ == "__main__":
    main()
