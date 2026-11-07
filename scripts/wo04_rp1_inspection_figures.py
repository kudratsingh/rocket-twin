"""One bounded Matplotlib rendering of verified actual RP1 inspection GLB faces.

This is an offline geometry projection, not browser observation, a screenshot,
camera-fit acceptance, manufacturing CAD or physical evidence.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUTPUT = ROOT / "output/frontend-release-20261107"
OUTER = {"nose", "body", "upper_body"}


def main() -> None:
    cpu_start, wall_start = time.process_time(), time.monotonic()

    def expired(signum: int, frame: Any) -> None:
        raise TimeoutError("Offline geometry figure exceeded 20 CPU / 30 wall seconds; stop")

    signal.signal(signal.SIGALRM, expired)
    signal.signal(signal.SIGPROF, expired)
    signal.setitimer(signal.ITIMER_REAL, 30)
    signal.setitimer(signal.ITIMER_PROF, 20)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    import trimesh
    from matplotlib.collections import PolyCollection

    from src.api.rp1_geometry import build

    def budget() -> None:
        if time.process_time() - cpu_start > 20 or time.monotonic() - wall_start > 30:
            raise TimeoutError("Offline geometry figure exceeded 20 CPU / 30 wall seconds; stop")

    document = build(ROOT)
    rows = []
    groups = []
    for part in document["parts"]:
        if part["mesh"] is None:
            continue
        path = ROOT / part["mesh"]["path"]
        raw = path.read_bytes()
        actual_hash = hashlib.sha256(raw).hexdigest()
        if actual_hash != part["mesh"]["sha256"]:
            raise ValueError("Verified GLB changed before figure read")
        scene = trimesh.load(io.BytesIO(raw), file_type="glb", force="scene")
        actual = scene.to_geometry()  # Apply all actual GLB node transforms.
        actual_bounds = actual.bounds
        if not np.allclose(actual_bounds, part["bounds_m"], atol=2e-7, rtol=0):
            raise ValueError(f"Loaded GLB bounds disagree with recorded geometry: {part['id']}")
        triangles = np.asarray(actual.triangles)
        color = np.asarray(actual.visual.face_colors[0], dtype=float) / 255
        if part["maturity"] == "simplified_envelope":
            color[3] = 0.38
        else:
            color[3] = 1.0
        groups.append(
            {
                "id": part["id"],
                "triangles_m": triangles,
                "face_normals": np.asarray(actual.face_normals),
                "color": color,
            }
        )
        rows.append(
            {
                "id": part["id"],
                "maturity": part["maturity"],
                "mesh": part["mesh"],
                "actual_glb_bounds_m": actual_bounds.tolist(),
                "triangle_count": len(triangles),
            }
        )
        budget()
    aggregate = np.array([r["actual_glb_bounds_m"] for r in rows])
    bounds = np.array([aggregate[:, 0, :].min(axis=0), aggregate[:, 1, :].max(axis=0)])
    if not np.allclose(bounds, document["bounds_m"], atol=2e-7, rtol=0):
        raise ValueError("Actual assembly bounds disagree with inspection manifest")

    fig, axes = plt.subplots(2, 3, figsize=(16, 12), facecolor="#f5f7fa")

    def draw(
        ax: Any,
        title: str,
        horizontal: Any,
        vertical: Any,
        depth: Any,
        *,
        hidden: bool = False,
        crop: bool = False,
        labels: tuple[str, str],
    ) -> None:
        polys, colors, depths = [], [], []
        for group in groups:
            if hidden and group["id"] in OUTER:
                continue
            triangles = group["triangles_m"]
            projected = np.stack((triangles @ horizontal, triangles @ vertical), axis=-1) * 1000
            polys.append(projected)
            rgba = np.tile(group["color"], (len(triangles), 1))
            light = np.asarray(depth) * 0.7 + np.asarray(vertical) * 0.3
            light /= np.linalg.norm(light)
            intensity = 0.52 + 0.48 * np.abs(group["face_normals"] @ light)
            rgba[:, :3] *= intensity[:, None]
            colors.append(rgba)
            depths.append((triangles @ depth).mean(axis=1))
        triangles_2d = np.concatenate(polys)
        rgba = np.concatenate(colors)
        order = np.argsort(np.concatenate(depths), kind="stable")
        collection = PolyCollection(
            triangles_2d[order],
            facecolors=rgba[order],
            edgecolors="none",
            linewidths=0,
            antialiased=False,
        )
        ax.add_collection(collection)
        if crop:
            ax.set_xlim(-105, 105)
            ax.set_ylim(0, 235)
        else:
            extent = triangles_2d.reshape(-1, 2)
            lo, hi = extent.min(axis=0), extent.max(axis=0)
            span = hi - lo
            ax.set_xlim(lo[0] - span[0] * 0.12, hi[0] + span[0] * 0.12)
            ax.set_ylim(lo[1] - span[1] * 0.035, hi[1] + span[1] * 0.035)
        ax.set_aspect("equal", adjustable="box")
        ax.set_title(title, fontsize=10, loc="left", pad=9, fontweight="bold")
        ax.set_xlabel(labels[0], fontsize=8)
        ax.set_ylabel(labels[1], fontsize=8)
        ax.set_facecolor("white")
        ax.tick_params(labelsize=7)
        ax.grid(color="#dce2ea", linewidth=0.45, zorder=-1)
        for spine in ax.spines.values():
            spine.set_color("#c4ceda")
        budget()

    x, y, z = np.eye(3)
    draw(
        axes[0, 0],
        "A  Side elevation / viewed from +Z",
        x,
        y,
        z,
        labels=("Viewer X / body+y (mm)", "Viewer Y = length − station (mm)"),
    )
    draw(
        axes[0, 1],
        "B  Front elevation / viewed from −X",
        z,
        y,
        -x,
        labels=("Viewer Z / body−z (mm)", "Viewer Y = length − station (mm)"),
    )
    draw(
        axes[0, 2],
        "C  Motor-end / viewed from aft",
        x,
        z,
        -y,
        labels=("Viewer X / body+y (mm)", "Viewer Z / body−z (mm)"),
    )
    normal = np.array([0.9, 0.25, 1.0])
    normal /= np.linalg.norm(normal)
    horizontal = np.cross(y, normal)
    horizontal /= np.linalg.norm(horizontal)
    vertical = np.cross(normal, horizontal)
    draw(
        axes[1, 0],
        "D  Oblique / orthographic projection",
        horizontal,
        vertical,
        normal,
        labels=("Projected horizontal (mm)", "Projected vertical (mm)"),
    )
    draw(
        axes[1, 1],
        "E  Interior / three outer parts hidden",
        x,
        y,
        z,
        hidden=True,
        labels=("Viewer X / body+y (mm)", "Viewer Y = length − station (mm)"),
    )
    draw(
        axes[1, 2],
        "F  Aft detail crop / outer body hidden",
        x,
        y,
        z,
        hidden=True,
        crop=True,
        labels=("Viewer X / body+y (mm)", "Viewer Y (mm); aft datum = 0"),
    )
    axes[0, 0].annotate(
        "Nose tip: Y = 1250 mm",
        xy=(0, 1250),
        xytext=(0.03, 0.98),
        textcoords="axes fraction",
        fontsize=7,
        va="top",
        arrowprops={"arrowstyle": "-", "lw": 0.6},
    )
    axes[0, 0].annotate(
        "Aft datum: Y = 0",
        xy=(0, 0),
        xytext=(0.03, 0.02),
        textcoords="axes fraction",
        fontsize=7,
        va="bottom",
        arrowprops={"arrowstyle": "-", "lw": 0.6},
    )
    axes[1, 2].text(
        0.03,
        0.97,
        "Only existing meshes shown.\nNo installed joint, knot or\nguide hardware is invented.",
        transform=axes[1, 2].transAxes,
        fontsize=7,
        va="top",
        bbox={"facecolor": "white", "alpha": 0.85, "edgecolor": "#ccd5df", "pad": 4},
    )
    geometry_hash = document["identity"]["inspection_geometry_sha256"]
    fig.suptitle(
        "RP1 AD1 v2 — actual GLB offline geometry projections",
        fontsize=15,
        fontweight="bold",
        y=0.988,
    )
    fig.text(
        0.5,
        0.942,
        f"{document['id']}\nInspection geometry SHA-256: {geometry_hash}",
        ha="center",
        fontsize=8,
        linespacing=1.6,
    )
    fig.text(
        0.5,
        0.021,
        "26 mesh parts: 10 source-dimensioned estimates (opaque) + 16 simplified envelopes (translucent).\n25 mass allowances and 4 missing-geometry records have no solid. GLB units: metres; plot axes: millimetres.\nOFFLINE PROJECTION — not a browser screenshot, camera-fit acceptance, manufacturing release or physical validation.",
        ha="center",
        fontsize=8,
        color="#334155",
        linespacing=1.5,
    )
    fig.subplots_adjust(top=0.88, bottom=0.095, left=0.045, right=0.985, hspace=0.27, wspace=0.22)
    image_path = OUTPUT / "rp1-inspection-contact-sheet.png"
    fig.savefig(image_path, dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    budget()
    manifest = {
        "id": document["id"],
        "inspection_geometry_sha256": geometry_hash,
        "source_manifest": "docs/studies/rp1-inspection-geometry-20261107/manifest.json",
        "source_manifest_sha256": hashlib.sha256(
            (ROOT / "docs/studies/rp1-inspection-geometry-20261107/manifest.json").read_bytes()
        ).hexdigest(),
        "script_path": str(Path(__file__).relative_to(ROOT)),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "render": {
            "path": str(image_path.relative_to(ROOT)),
            "sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
            "pixels": [2400, 1800],
        },
        "renderer": {
            "matplotlib": matplotlib.__version__,
            "backend": matplotlib.get_backend(),
            "trimesh": trimesh.__version__,
            "numpy": np.__version__,
        },
        "projection_method": "Actual GLB triangles with orthographic projection, centroid depth ordering and face-normal display lighting; source-dimensioned opaque, envelopes translucent. No new surfaces or solver fields.",
        "source_coverage": document["coverage"],
        "actual_glb_assembly_bounds_m": bounds.tolist(),
        "actual_glb_assembly_span_mm": ((bounds[1] - bounds[0]) * 1000).tolist(),
        "parts": rows,
        "hidden_outer_ids_in_views_e_f": sorted(OUTER),
        "unrepresented": [
            {"id": p["id"], "maturity": p["maturity"], "description": p["description"]}
            for p in document["parts"]
            if p["mesh"] is None
        ],
        "status": "Offline actual-mesh projection only; not browser screenshot or camera-fit acceptance",
        "browser_observed": False,
        "engineering_accepted": False,
        "timing": {
            "cpu_seconds": time.process_time() - cpu_start,
            "wall_seconds": time.monotonic() - wall_start,
            "limits": {"cpu_seconds": 20, "wall_seconds": 30},
        },
    }
    (OUTPUT / "rp1-inspection-figure-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    signal.setitimer(signal.ITIMER_REAL, 0)
    signal.setitimer(signal.ITIMER_PROF, 0)
    print(
        json.dumps(
            {
                "render": manifest["render"],
                "bounds_m": bounds.tolist(),
                "timing": manifest["timing"],
            }
        )
    )


if __name__ == "__main__":
    main()
