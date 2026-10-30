"""Render review stills from exported WO-03 assembly GLBs (geometry is never edited)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import textwrap
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", ".cache/matplotlib")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import trimesh
import yaml
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

SHELL_PARTS = {"nose_cone", "body_upper", "interface_coupler", "aft_shell"}
RECOVERY_IDS = (
    "recovery_bulkhead",
    "recovery_anchor",
    "parachute",
    "shock_cord",
    "recovery_protection",
    "independent_recovery",
)
AVIONICS_IDS = (
    "avionics_bay",
    "flight_computer",
    "imu",
    "baro",
    "battery",
    "regulator_5v",
    "pyro_mosfet",
    "arming_switch",
    "micro_sd",
    "high_g_accel",
    "harness",
)
FIXED_AFT_IDS = (
    "aft_interface_hardware",
    "motor_mount",
    "motor_liner",
    "retention",
    "motor",
    "fin_set",
    "fin_bonds",
)
TVC_AFT_IDS = (
    "aft_interface_hardware",
    "motor_mount",
    "motor_liner",
    "retention",
    "motor",
    "fin_set",
    "fin_bonds",
    "tvc_gimbal",
    "gimbal_links",
    "servo_support",
    "thermal_guard",
    "servo_pitch",
    "servo_yaw",
    "gimbal_inner",
    "gimbal_frame",
    "outer_pivots",
    "inner_pivots",
    "servo_horns",
)
TVC_MECHANISM_IDS = {
    "tvc_gimbal",
    "gimbal_links",
    "servo_support",
    "servo_pitch",
    "servo_yaw",
    "gimbal_inner",
    "gimbal_frame",
    "outer_pivots",
    "inner_pivots",
    "servo_horns",
}
GIMBAL_DETAIL_IDS = TVC_MECHANISM_IDS | {"motor"}
GIMBAL_HIDDEN_IDS = {
    "aft_shell",
    "fin_set",
    "fin_bonds",
    "thermal_guard",
    "motor_liner",
}


def _rgba(mesh: trimesh.Trimesh) -> tuple[float, float, float, float]:
    colors = np.asarray(mesh.visual.face_colors)
    if colors.size == 0:
        return (0.58, 0.63, 0.66, 1.0)
    return tuple((colors[0].astype(float) / 255.0).tolist())  # type: ignore[return-value]


def _load_parts(assembly_file: Path) -> tuple[list[tuple[str, trimesh.Trimesh]], float]:
    scene = trimesh.load(assembly_file, force="scene", process=False)
    if not isinstance(scene, trimesh.Scene):
        raise TypeError(f"Expected GLB scene at {assembly_file}")
    maximum_y = float(scene.bounds[1, 1])
    meshes: list[tuple[str, trimesh.Trimesh]] = []
    for node in scene.graph.nodes_geometry:
        transform, geometry_name = scene.graph.get(node)
        mesh = scene.geometry[geometry_name].copy()
        mesh.apply_transform(transform)
        meshes.append((str(node), mesh))
    if not meshes:
        raise ValueError(f"No named part geometry in {assembly_file}")
    return meshes, maximum_y


def _coords(vertices: np.ndarray, maximum_y: float) -> np.ndarray:
    """Map export frame to station, export-Z, export-X for a side-like view."""
    return np.column_stack((maximum_y - vertices[:, 1], vertices[:, 2], vertices[:, 0]))


def _draw_meshes(
    ax: Any,
    parts: list[tuple[str, trimesh.Trimesh]],
    maximum_y: float,
    keep: set[str] | None = None,
    alpha_overrides: dict[str, float] | None = None,
) -> dict[str, tuple[float, float, float, float]]:
    colors: dict[str, tuple[float, float, float, float]] = {}
    for name, mesh in parts:
        if keep is not None and name not in keep:
            continue
        vertices = _coords(np.asarray(mesh.vertices), maximum_y)
        faces = vertices[np.asarray(mesh.faces)]
        color_array = np.asarray(_rgba(mesh), dtype=float)
        if alpha_overrides and name in alpha_overrides:
            color_array[3] = alpha_overrides[name]
        color = tuple(color_array.tolist())
        colors[name] = color
        collection = Poly3DCollection(
            faces,
            facecolors=color,
            edgecolors="none",
            linewidths=0,
            zsort="average",
            rasterized=True,
        )
        ax.add_collection3d(collection)
    return colors


def _style_axis(
    ax: Any,
    bounds: np.ndarray,
    *,
    station_limits: tuple[float, float] | None = None,
    transverse_limits: tuple[float, float] | None = None,
    view: tuple[float, float] = (20.0, -72.0),
    aspect: tuple[float, float, float] = (4.0, 1.0, 1.0),
    tick_count: int = 5,
) -> None:
    ax.set_xlim(*(station_limits or (float(bounds[0, 0]), float(bounds[1, 0]))))
    ax.set_ylim(*(transverse_limits or (float(bounds[0, 1]), float(bounds[1, 1]))))
    zmid = float((bounds[0, 2] + bounds[1, 2]) / 2.0)
    zspan = float(bounds[1, 2] - bounds[0, 2])
    ax.set_zlim(zmid - zspan * 0.62, zmid + zspan * 0.62)
    ax.set_xlabel("Axial station from nose (m)", labelpad=6)
    ax.set_ylabel("Export Z (m)", labelpad=3)
    ax.set_zlabel("Export X (m)", labelpad=3)
    ax.view_init(elev=view[0], azim=view[1])
    ax.set_box_aspect(aspect)
    ax.xaxis.set_major_locator(MaxNLocator(tick_count))
    ax.yaxis.set_major_locator(MaxNLocator(max(2, tick_count - 1)))
    ax.zaxis.set_major_locator(MaxNLocator(max(2, tick_count - 1)))
    ax.grid(False)
    ax.xaxis.pane.set_alpha(0.03)
    ax.yaxis.pane.set_alpha(0.02)
    ax.zaxis.pane.set_alpha(0.02)
    ax.tick_params(labelsize=7, pad=1)


def _component_note(manifest: dict[str, Any], ids: tuple[str, ...]) -> str:
    rows = {row["id"]: row for row in manifest["parts"]}
    available = list(dict.fromkeys(part_id for part_id in ids if part_id in rows))
    return textwrap.fill(", ".join(available), width=39, subsequent_indent="  ")


def _render_gimbal_internal(
    *,
    output: Path,
    mode_id: str,
    mode_name: str,
    meshes: list[tuple[str, trimesh.Trimesh]],
    maximum_y: float,
) -> None:
    available = {name for name, _ in meshes}
    visible = available & GIMBAL_DETAIL_IDS
    hidden = available & GIMBAL_HIDDEN_IDS
    if not visible - {"motor"}:
        return
    detail_parts = [(name, mesh) for name, mesh in meshes if name in visible]
    fig = plt.figure(figsize=(14, 7.5))
    ax = fig.add_axes([0.025, 0.12, 0.72, 0.82], projection="3d")
    _draw_meshes(ax, detail_parts, maximum_y, alpha_overrides={"motor": 0.16})
    # Focus on the gimbal ring/pivots around 0.66-0.73 m, with margin for the
    # exported servo, horn and drive-link geometry upstream of the central ring.
    ax.set_xlim(0.57, 0.785)
    ax.set_ylim(-0.035, 0.035)
    ax.set_zlim(-0.035, 0.035)
    ax.set_xlabel("Station (m; nose origin)", labelpad=12, fontsize=9)
    ax.set_ylabel("Export Z (m)", labelpad=2, fontsize=9)
    ax.set_zlabel("Export X (m)", labelpad=2, fontsize=9)
    ax.view_init(elev=28, azim=-58)
    ax.set_box_aspect((3.0, 1.0, 1.0))
    ax.xaxis.set_major_locator(MaxNLocator(5))
    ax.yaxis.set_major_locator(MaxNLocator(3))
    ax.zaxis.set_major_locator(MaxNLocator(3))
    ax.grid(False)
    ax.tick_params(labelsize=8, pad=1)
    ax.xaxis.pane.set_alpha(0.02)
    ax.yaxis.pane.set_alpha(0.02)
    ax.zaxis.pane.set_alpha(0.02)
    legend_ids = "\n".join(name for name, _ in detail_parts if name != "motor")
    hidden_ids = ", ".join(sorted(hidden))
    fig.text(
        0.77,
        0.92,
        "GIMBAL INTERNAL · EXPORTED PART IDS\n"
        + legend_ids
        + "\n\ncentral rings/pivots: station 0.68-0.703 m"
        + "\nmotor: transparent context envelope\n\nHIDDEN PART IDS\n"
        + textwrap.fill(hidden_ids, width=34),
        va="top",
        family="monospace",
        fontsize=8,
    )
    fig.suptitle(f"{mode_name} — gimbal internal close-up · nominal exported pose", fontsize=13)
    fig.text(
        0.02,
        0.015,
        "Actual exported part meshes; selected fins, shields and liners hidden for visibility. This static neutral/export pose is not motion or tolerance proof.",
        fontsize=8,
    )
    fig.savefig(output / f"{mode_id}_gimbal_internal.png", dpi=160)
    plt.close(fig)


def _render(
    *,
    output: Path,
    mode_id: str,
    mode_name: str,
    preset: str,
    meshes: list[tuple[str, trimesh.Trimesh]],
    manifest: dict[str, Any],
    maximum_y: float,
) -> None:
    vertices = np.concatenate([_coords(np.asarray(mesh.vertices), maximum_y) for _, mesh in meshes])
    bounds = np.stack((vertices.min(axis=0), vertices.max(axis=0)))

    fig = plt.figure(figsize=(14, 6.5))
    ax = fig.add_axes([0.035, 0.14, 0.92, 0.78], projection="3d")
    _draw_meshes(ax, meshes, maximum_y)
    _style_axis(ax, bounds)
    fig.suptitle(f"{mode_name} — assembled GLB · {preset} render", fontsize=14)
    fig.text(
        0.02,
        0.01,
        "Exact exported assembly geometry and per-part colors; station measured from nose, aft positive. 3D view is for inspection, not a dimensioned drawing.",
        fontsize=8,
    )
    fig.savefig(output / f"{mode_id}_assembled.png", dpi=140)
    plt.close(fig)

    hidden = SHELL_PARTS & {name for name, _ in meshes}
    visible = {name for name, _ in meshes} - hidden
    # Use only the actual exported visible parts; no clipping/cutting operation alters geometry.
    cut_vertices = np.concatenate(
        [_coords(np.asarray(mesh.vertices), maximum_y) for name, mesh in meshes if name in visible]
    )
    cut_bounds = np.stack((cut_vertices.min(axis=0), cut_vertices.max(axis=0)))
    fig = plt.figure(figsize=(15, 7.2))
    ax = fig.add_axes([0.025, 0.14, 0.65, 0.78], projection="3d")
    _draw_meshes(ax, meshes, maximum_y, keep=visible)
    _style_axis(ax, cut_bounds)
    ax.set_title(f"{mode_name} — shell-removed visibility view", pad=4, fontsize=12)
    fig.text(
        0.70,
        0.90,
        "SHELL PARTS HIDDEN\n"
        + textwrap.fill(", ".join(sorted(hidden)), width=39)
        + "\n\nRECOVERY PART IDS\n"
        + _component_note(manifest, RECOVERY_IDS)
        + "\n\nAVIONICS PART IDS\n"
        + _component_note(manifest, AVIONICS_IDS)
        + "\n\nAFT MODULE PART IDS\n"
        + _component_note(manifest, FIXED_AFT_IDS + TVC_AFT_IDS),
        va="top",
        ha="left",
        fontsize=7.2,
        family="monospace",
    )
    fig.text(
        0.02,
        0.01,
        "Visibility only: outer shell parts omitted; no section cut, displacement, or geometry redesign. Some hidden/internal boxes remain overlapping in this nominal CAD export.",
        fontsize=8,
    )
    fig.savefig(output / f"{mode_id}_shell_removed.png", dpi=140)
    plt.close(fig)

    tvc_ids = {name for name, _ in meshes} & TVC_MECHANISM_IDS
    detail_ids = (
        {name for name, _ in meshes} & set(TVC_AFT_IDS)
        if tvc_ids
        else {name for name, _ in meshes} & set(FIXED_AFT_IDS)
    )
    detail_parts = [(name, mesh) for name, mesh in meshes if name in detail_ids]
    detail_vertices = np.concatenate(
        [_coords(np.asarray(mesh.vertices), maximum_y) for _, mesh in detail_parts]
    )
    detail_bounds = np.stack((detail_vertices.min(axis=0), detail_vertices.max(axis=0)))
    x0, x1 = float(detail_bounds[0, 0]), float(detail_bounds[1, 0])
    fig = plt.figure(figsize=(12, 7))
    ax = fig.add_axes([0.035, 0.14, 0.68, 0.78], projection="3d")
    _draw_meshes(ax, detail_parts, maximum_y)
    _style_axis(
        ax,
        detail_bounds,
        station_limits=(x0 - 0.01, x1 + 0.01),
        transverse_limits=(float(detail_bounds[0, 1]) - 0.01, float(detail_bounds[1, 1]) + 0.01),
        view=(24.0, -62.0),
    )
    is_tvc = bool(tvc_ids)
    fig.suptitle(
        f"{mode_name} — "
        + ("neutral TVC aft-module close-up" if is_tvc else "fixed-motor aft close-up"),
        fontsize=13,
    )
    labels = "\n".join(name for name, _ in detail_parts)
    fig.text(
        0.75,
        0.90,
        "EXPORTED PART IDs\n" + textwrap.fill(labels.replace("\n", ", "), width=30),
        va="top",
        family="monospace",
        fontsize=8,
    )
    fig.text(
        0.02,
        0.01,
        (
            "Close-up from exported part GLBs; TVC is shown at the CAD export pose, not proof of full motion clearance."
            if is_tvc
            else "Close-up from exported fixed-motor part GLBs; source mesh positions/colors retained."
        ),
        fontsize=8,
    )
    fig.savefig(output / f"{mode_id}_aft_detail.png", dpi=140)
    plt.close(fig)
    if tvc_ids:
        _render_gimbal_internal(
            output=output,
            mode_id=mode_id,
            mode_name=mode_name,
            meshes=meshes,
            maximum_y=maximum_y,
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/platform.yaml"))
    parser.add_argument("--preset", choices=("tiny", "sim"), default="tiny")
    parser.add_argument("--output", type=Path, default=Path("build/wo03-inspection"))
    args = parser.parse_args()

    platform = yaml.safe_load(args.config.read_text())
    args.output.mkdir(parents=True, exist_ok=True)
    rows = []
    for mode_file in platform["vehicles"]:
        mode_path = Path(mode_file)
        mode_data = yaml.safe_load(mode_path.read_text())
        mode_id = str(mode_data["id"])
        build_path = Path("build") / mode_id
        assembly_file = build_path / "assembly.glb"
        manifest_file = build_path / "manifest.json"
        if not assembly_file.is_file() or not manifest_file.is_file():
            raise FileNotFoundError(
                f"Expected existing exported CAD GLB and manifest under {build_path}"
            )
        manifest = json.loads(manifest_file.read_text())
        meshes, maximum_y = _load_parts(assembly_file)
        _render(
            output=args.output,
            mode_id=mode_id,
            mode_name=str(mode_data.get("name", mode_id)),
            preset=args.preset,
            meshes=meshes,
            manifest=manifest,
            maximum_y=maximum_y,
        )
        manifest_identity = manifest.get("identity", {})
        rows.append(
            {
                "mode_id": mode_id,
                "assembly_glb": str(assembly_file),
                "assembly_glb_sha256": hashlib.sha256(assembly_file.read_bytes()).hexdigest(),
                "manifest": str(manifest_file),
                "manifest_sha256": hashlib.sha256(manifest_file.read_bytes()).hexdigest(),
                "resolved_spec_sha256": manifest_identity.get("resolved_spec_sha256"),
                "cad_revision_sha256": manifest_identity.get("cad_revision_sha256"),
                "part_geometry_count": len(meshes),
                "render_preset_label": args.preset,
                "rendered_pngs": sorted(path.name for path in args.output.glob(f"{mode_id}_*.png")),
            }
        )
        print(f"rendered {mode_id}: {len(meshes)} GLB part meshes", flush=True)
    (args.output / "source-index.json").write_text(json.dumps(rows, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
