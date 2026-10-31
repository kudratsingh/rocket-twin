"""Refresh exact fitting-baffle stills and explicitly unavailable Analysis fields."""

from __future__ import annotations

import os

os.environ.setdefault("MPLCONFIGDIR", ".cache/matplotlib")

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
import yaml
from matplotlib.patches import Patch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.records import AnalysisRecord, export_record, load_compatible
from src.vehicle.schema import Vehicle

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/studies/wo03-cad-radiation.yaml"
    )
    parser.add_argument("--preset", choices=("tiny", "sim", "rl", "real"), default="tiny")
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    resolved, manifest = ROOT / cfg["source_resolved"], ROOT / cfg["source_geometry_manifest"]
    if (
        sha(resolved) != cfg["expected_resolved_file_sha256"]
        or sha(manifest) != cfg["expected_manifest_sha256"]
    ):
        raise ValueError("Candidate specification/placed geometry identity changed")
    vehicle = Vehicle.model_validate_json(resolved.read_bytes())
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    if identity != cfg["expected_candidate_identity"]:
        raise ValueError("Candidate identity mismatch")
    rows = json.loads(manifest.read_text())
    parts = {p.id: p for p in vehicle.parts}
    if len(rows) != len(parts) or {r["part_id"] for r in rows} != parts.keys():
        raise ValueError("Actual geometry manifest is incomplete")
    meshes = []
    hashes = {
        str(p.relative_to(ROOT)): sha(p) for p in [args.config, resolved, manifest, Path(__file__)]
    }
    for row in rows:
        path = manifest.parent / row["stl"]
        if sha(path) != row["stl_sha256"]:
            raise ValueError("Actual candidate mesh changed")
        hashes[str(path.relative_to(ROOT))] = row["stl_sha256"]
        mesh = trimesh.load(path, force="mesh", process=False)
        if not isinstance(mesh, trimesh.Trimesh):
            raise TypeError("Expected actual placed STL mesh")
        meshes.append((row["part_id"], mesh))
    output = ROOT / "build/wo03-fitting-baffle-preview"
    output.mkdir(parents=True, exist_ok=True)
    colors = {
        "motor": "#383f47",
        "wood": "#c6985d",
        "foil": "#41bdd2",
        "mica": "#edc561",
        "glue": "#d2698e",
        "other": "#8096a3",
    }

    def category(name: str) -> str:
        material = parts[name].material.lower()
        if name == "motor":
            return "motor"
        if material == "aluminum":
            return "foil"
        if material == "mica":
            return "mica"
        if material == "epoxy":
            return "glue"
        if "plywood" in material or material == "kraft":
            return "wood"
        return "other"

    fig = plt.figure(figsize=(15, 7), facecolor="#f4f6f8")
    for i, detail in enumerate((False, True), 1):
        ax: Any = fig.add_subplot(1, 2, i, projection="3d")
        for name, mesh in meshes:
            if detail and not name.startswith("fitting_baffle_1_front"):
                continue
            # Hide casing to inspect inner geometry; crop only display triangles.
            if name in {"aft_shell", "body_upper", "interface_coupler", "fin_set", "fin_bonds"}:
                continue
            triangles = np.asarray(mesh.vertices)[np.asarray(mesh.faces)]
            lo, hi = (1039.0, 1053.0) if detail else (985.0, 1215.0)
            keep = (triangles[:, :, 2].max(axis=1) >= lo) & (triangles[:, :, 2].min(axis=1) <= hi)
            triangles = triangles[keep]
            if not len(triangles):
                continue
            # Actual CAD frame: X,Y transverse, Z station. Display station first.
            xyz = triangles[:, :, [2, 0, 1]]
            ax.add_collection3d(
                Poly3DCollection(
                    xyz,
                    facecolors=colors[category(name)],
                    linewidths=0,
                    edgecolors="none",
                    rasterized=True,
                )
            )
        ax.set_xlim(lo, hi)
        ax.set_ylim(-34, 34)
        ax.set_zlim(-34, 34)
        ax.set_box_aspect((2.8 if not detail else 1.3, 1, 1))
        ax.view_init(elev=24 if not detail else 15, azim=-66 if not detail else -24)
        ax.set_xlabel("Distance aft from nose (mm)", labelpad=10)
        ax.set_ylabel("CAD X (mm)")
        ax.set_zlabel("CAD Y (mm)")
        ax.set_title(
            (
                "Actual aft assembly — outer body hidden"
                if not detail
                else "Separate baffle detail — mount hidden to expose seams/notches"
            ),
            fontsize=11,
        )
        ax.tick_params(labelsize=7)
        ax.grid(False)
    fig.suptitle(
        "G54 fitting-baffle candidate 69df790… | Preliminary; thermal acceptance open", fontsize=14
    )
    fig.legend(
        handles=[Patch(color=v, label=k.title()) for k, v in colors.items()],
        loc="lower center",
        ncol=6,
        bbox_to_anchor=(0.5, 0.045),
    )
    fig.text(
        0.5,
        0.015,
        "Material colors only; no temperature field. Actual placed STL geometry. Body/fins hidden for inspection; display clipping does not alter CAD.",
        ha="center",
        fontsize=9,
    )
    fig.subplots_adjust(left=0.02, right=0.96, bottom=0.13, top=0.89, wspace=0.05)
    image = output / "actual-baffle-layout.png"
    fig.savefig(image, dpi=150)
    plt.close(fig)
    shape_ids = {p.id: p.cad_mass.shape_sha256 for p in vehicle.parts if p.cad_mass is not None}
    if not shape_ids:
        raise ValueError("No recorded per-part shape identity")
    fields = []
    for quantity, units in (("temperature", "K"), ("design_margin", "1")):
        row = {
            "id": "corrected-baffle-" + quantity.replace("_", "-") + "-unavailable",
            "case_id": "required-matrix-pending",
            "quantity": quantity,
            "component": "No compatible corrected-candidate recorded result",
            "units": units,
            "association": "part",
            "part_ids": sorted(shape_ids),
            "sample_count": 0,
            "unavailable_reason": "Corrected actual-CAD gas/radiation transient matrix has not been accepted or exported for this exact candidate.",
            "coverage_notes": "No parent/proxy temperatures, zero values, invented time samples or local hot spots are substituted.",
            "evidence": {
                "provenance": "unavailable",
                "validation": "unavailable",
                "assumptions": [
                    "Actual notched/seamed geometry; motor envelope and material/contact histories remain uncertain."
                ],
                "limits": [
                    "Fit/static checks are not thermal acceptance.",
                    "Earlier coaxial temperatures belong to a different configuration.",
                ],
                "sources": [cfg["source_record"], cfg["source_geometry_manifest"]],
                "uncertainty": "Boundary/material/contact and spatial convergence remain open.",
                "required_physical_tests": [
                    "Instrumented case/substrate/attachment soak after design acceptance."
                ],
            },
        }
        if quantity == "design_margin":
            row["margin_definition"] = (
                "Dimensionless thermal screen margin M=(318.15 K - calculated T_K)/318.15 K; M>=0 passes the provisional45 degC substrate screen at the stated result resolution only."
            )
        fields.append(row)
    analysis = AnalysisRecord.model_validate(
        {
            "run_id": "wo03-fitting-baffle-layout-preview",
            "identity": {
                "configuration_id": vehicle.id,
                "resolved_spec_sha256": identity,
                "cad_revision_sha256": cfg["expected_source_cad_revision"],
                "part_shape_sha256": shape_ids,
            },
            "cases": {
                "required-matrix-pending": {
                    "status": "unavailable",
                    "substrate_screen_c": 45,
                    "includes_combined_300C_contaminated_foil_35C": True,
                }
            },
            "fields": fields,
            "tools": {"producer": "offline_CAD_preview_no_thermal_solve"},
            "input_sha256": hashes,
        }
    )
    exported = export_record(output / "analysis", analysis, {})
    compatible = load_compatible(exported, analysis.identity)
    record = {
        "candidate_identity": identity,
        "cad_revision_sha256": cfg["expected_source_cad_revision"],
        "input_sha256": hashes,
        "preview": str(image.relative_to(ROOT)),
        "preview_sha256": sha(image),
        "analysis_manifest": str(exported.relative_to(ROOT)),
        "analysis_manifest_sha256": sha(exported),
        "compatible_consumer_passed": len(compatible.fields) == 2,
        "all_result_fields_unavailable": True,
        "geometry_only_preview": True,
        "active_registration": False,
        "thermal_acceptance": False,
        "flight_ready": False,
    }
    (output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: record[k]
                for k in [
                    "candidate_identity",
                    "preview",
                    "analysis_manifest",
                    "compatible_consumer_passed",
                ]
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
