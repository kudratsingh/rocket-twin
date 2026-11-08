"""Measure designated native PNG pixels; no browser, geometry or camera calculations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "runs/frontend-browser-20261107"
OUTPUT = ROOT / "docs/studies/frontend-release-20261107"

# Rectangles are manually identified visible screenshot boundaries in raster px,
# [left, top, right-exclusive, bottom-exclusive]. They are not camera metadata.
CAPTURES: list[dict[str, Any]] = [
    {
        "file": "rp1-side-tools-open-1440x900.png",
        "viewport_css": [1440, 900],
        "state": "Side preset, rail/context open, Scene tools open; preserved earlier misnamed default",
        "criterion": "inapplicable_tools_open",
        "canvas_raster": [626, 104, 2880, 1176],
        "object_search_raster": [1750, 280, 2000, 1000],
        "object_exclusions_raster": [[1750, 674, 2000, 776]],
        "safe_raster": None,
        "expected_sha256": "5db9aed6c7a7f1b2b4a9418a58e2eda0843135d847519f0d8265051d5b85c86d",
    },
    {
        "file": "rp1-side-tools-closed-default-1440x900.png",
        "viewport_css": [1440, 900],
        "state": "Side preset; rail/context open; Scene tools closed; no selected part; CG/CP off",
        "criterion": "default",
        "canvas_raster": [626, 104, 2880, 1668],
        "object_search_raster": [1750, 280, 2000, 1430],
        "object_exclusions_raster": [],
        "safe_raster": [626, 264, 2880, 1438],
        "expected_sha256": "2b2e0ea3643bb0b8957fbb229d5c61f948e6c6b112f23b61c29c63c30d5bc44d",
    },
    {
        "file": "rp1-side-tools-closed-focus-1440x900.png",
        "viewport_css": [1440, 900],
        "state": "Side preset; Exit focus visible; both columns absent; tools closed; CG/CP off",
        "criterion": "focus",
        "canvas_raster": [0, 104, 2880, 1668],
        "object_search_raster": [1400, 280, 1700, 1430],
        "object_exclusions_raster": [],
        "safe_raster": [0, 238, 2880, 1438],
        "expected_sha256": "1382cd4aabb0007dfce6df5f9feef44fef88bd6aac3ee50adccadf0f5a09eb0c",
    },
    {
        "file": "rp1-side-tools-closed-default-1280x720.png",
        "viewport_css": [1280, 720],
        "state": "Side inherited across resize; both columns open; tools closed; no selected part; CG/CP off",
        "criterion": "default",
        "canvas_raster": [626, 104, 2560, 1308],
        "object_search_raster": [1600, 300, 1800, 1150],
        "object_exclusions_raster": [],
        "safe_raster": [626, 264, 2560, 1078],
        "expected_sha256": "b58644e202f8ac87c7c95877ab3f0943d9f0350bddb32549b24945d45cc5dfd9",
    },
    {
        "file": "rp1-side-tools-closed-focus-1280x720.png",
        "viewport_css": [1280, 720],
        "state": "Side inherited across resize; Exit focus visible; both columns absent; tools closed; CG/CP off",
        "criterion": "focus",
        "canvas_raster": [0, 104, 2560, 1308],
        "object_search_raster": [1300, 300, 1500, 1150],
        "object_exclusions_raster": [],
        "safe_raster": [0, 264, 2560, 1078],
        "expected_sha256": "8ea1662f6999875c27631942ad8c8ee09f9bcdfa7b58a93a93bb6e5388023af6",
    },
    {
        "file": "rp1-side-tools-closed-default-guide-fixed-1440x900.png",
        "viewport_css": [1440, 900],
        "state": "Post-correction Side and explicit Fit; both columns open; tools closed; no selection/CG/CP; visible magenta guide",
        "criterion": "default",
        "visible_guide": True,
        "canvas_raster": [626, 104, 2880, 1668],
        "object_search_raster": [1500, 300, 1800, 1430],
        "object_exclusions_raster": [],
        "safe_raster": None,
        "expected_sha256": "c88f63958f5bdb0995cba8c273305f23c8785498ecdc65b2d15c459ef1bd9143",
    },
    {
        "file": "rp1-side-tools-closed-focus-guide-fixed-1440x900.png",
        "viewport_css": [1440, 900],
        "state": "Post-correction Side and explicit Fit; Exit focus; both columns absent; tools closed; CG/CP off; visible magenta guide",
        "criterion": "focus",
        "visible_guide": True,
        "canvas_raster": [0, 104, 2880, 1668],
        "object_search_raster": [1100, 300, 1500, 1430],
        "object_exclusions_raster": [],
        "safe_raster": None,
        "expected_sha256": "e392b4665001c28f58d82b0a415fcdab82851c1c39a1b9db74a7c6e8d62973ff",
    },
    {
        "file": "rp1-baro-isolated-guide-fixed-1440x900.png",
        "viewport_css": [1440, 900],
        "state": "Post-correction isolated barometer; 1 visible/54 hidden; Frame part; tools closed; selected-part card overlaps the middle/right, bounding extremes remain visible",
        "criterion": "small_part",
        "visible_guide": True,
        "target_kind": "tight_part",
        "canvas_raster": [626, 104, 2880, 1668],
        "object_search_raster": [1500, 350, 1800, 1400],
        "object_exclusions_raster": [[1570, 870, 1800, 1090]],
        "safe_raster": None,
        "expected_sha256": "5f9e74502758945b62678bd0b87d976e20472c9ee8961c2d641e45561602c534",
    },
    {
        "file": "rp1-side-tools-closed-default-guide-fixed-1280x720-verified.png",
        "viewport_css": [1280, 720],
        "state": "True committed1280x720 immediately after resize with prior camera state; NO new explicit Side/Fit after commit; both columns open; tools closed",
        "phase": "after screen-right correction; resize transition before new requested fit; retained threshold misses are not an explicit-after-resize fit result",
        "fit_threshold_applicable": False,
        "criterion": "default",
        "visible_guide": True,
        "canvas_raster": [626, 104, 2560, 1308],
        "object_search_raster": [1350, 280, 1650, 1150],
        "object_exclusions_raster": [],
        "safe_raster": None,
        "expected_sha256": "c97d5a475c4bdcd85efa5f0bc54437d7e9c39c7446fb419f4ea63ec9ef9253de",
    },
    {
        "file": "rp1-side-tools-closed-default-guide-fixed-1280x720-refit.png",
        "viewport_css": [1280, 720],
        "state": "True1280x720; explicit Side and Fit AFTER committed height; both columns restored; tools closed; no selection/CG/CP; visible guide",
        "criterion": "default",
        "visible_guide": True,
        "canvas_raster": [626, 104, 2560, 1308],
        "object_search_raster": [1350, 280, 1650, 1150],
        "object_exclusions_raster": [],
        "safe_raster": None,
        "expected_sha256": "9720ffe6f7d821f794c4170c5df44c3100d6c0ee85815763364f699778f52838",
    },
    {
        "file": "rp1-side-tools-closed-focus-guide-fixed-1280x720-refit.png",
        "viewport_css": [1280, 720],
        "state": "Actual true1280x720 Focus; Exit focus visible, both columns absent, tools closed; guide OFF after remount despite legacy filename; width-only criterion",
        "phase": "after screen-right correction; true Focus; guide absent, no visible-guide fit claim",
        "criterion": "focus",
        "fit_threshold_applicable": False,
        "canvas_raster": [0, 104, 2560, 1308],
        "object_search_raster": [950, 280, 1350, 1150],
        "object_exclusions_raster": [],
        "safe_raster": None,
        "expected_sha256": "8c909cd91385d9ebecfb6ce2af15002ab486a9e4edab5442fbd69a7d45074f24",
    },
]


def rectangle_size(rectangle: list[float]) -> list[float]:
    return [rectangle[2] - rectangle[0], rectangle[3] - rectangle[1]]


def main() -> None:
    results = []
    for source in CAPTURES:
        path = FOLDER / source["file"]
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if source["expected_sha256"] and source["expected_sha256"] != digest:
            raise ValueError(f"Designated capture hash differs: {source['file']}")
        image = np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
        raster = [image.shape[1], image.shape[0]]
        scale = [raster[i] / source["viewport_css"][i] for i in range(2)]
        if scale != [2, 2]:
            raise ValueError("Capture no longer matches confirmed 2x CSS/raster scaling")
        canvas = [value / 2 for value in source["canvas_raster"]]
        canvas_size = rectangle_size(canvas)
        canvas_ratios = [canvas_size[i] / source["viewport_css"][i] for i in range(2)]
        x0, y0, x1, y1 = source["object_search_raster"]
        crop = image[y0:y1, x0:x1]
        red, green, blue = crop[:, :, 0], crop[:, :, 1], crop[:, :, 2]
        # Visible screenshot palette: shaded cyan inspection surface and tan motor.
        mask = ((red > 65) & (green > 100) & (blue > 110) & (green > red + 8)) | (
            (red > 100) & (green > 90) & (blue < red * 0.9)
        )
        if source.get("target_kind") == "tight_part":
            mask = (
                (red > 130)
                & (green > 130)
                & (blue > 110)
                & (np.abs(red - green) < 40)
                & (blue < green + 20)
            )
        for left, top, right, bottom in source["object_exclusions_raster"]:
            mask[
                max(top - y0, 0) : min(bottom - y0, y1 - y0),
                max(left - x0, 0) : min(right - x0, x1 - x0),
            ] = False
        yy, xx = np.where(mask)
        if not len(xx):
            raise ValueError(
                "No target-colored raster pixels in the manually reviewed search region"
            )
        object_raster = [
            int(xx.min()) + x0,
            int(yy.min()) + y0,
            int(xx.max()) + x0 + 1,
            int(yy.max()) + y0 + 1,
        ]
        object_css = [v / 2 for v in object_raster]
        measured = {
            "phase": source.get(
                "phase",
                (
                    "after screen-right basis correction; declared framing guide visible"
                    if source.get("visible_guide")
                    else "before screen-right basis correction; no visible declared safe guide"
                ),
            ),
            "file": str(path.relative_to(ROOT)),
            "sha256": digest,
            "viewport_css_px": source["viewport_css"],
            "raster_px": raster,
            "raster_per_css_px": scale,
            "state": source["state"],
            "canvas_raster_rect": source["canvas_raster"],
            "canvas_css_rect": canvas,
            "canvas_css_size": canvas_size,
            "canvas_viewport_fraction": canvas_ratios,
            "object_search_raster_rect": source["object_search_raster"],
            "excluded_overlay_raster_rects": source["object_exclusions_raster"],
            "visible_object_raster_bbox": object_raster,
            "visible_object_css_bbox": object_css,
            "visible_object_css_size": rectangle_size(object_css),
            "matched_color_pixels": int(mask.sum()),
            "target_kind": source.get("target_kind", "assembly"),
            "fit_threshold_applicable": source.get(
                "fit_threshold_applicable", bool(source.get("visible_guide"))
            ),
            "criterion_applicability": source["criterion"],
            "rv_q10": {
                "default_width_at_least_72pct": (
                    canvas_ratios[0] >= 0.72 if source["criterion"] == "default" else None
                ),
                "default_height_at_least_78pct": (
                    canvas_ratios[1] >= 0.78 if source["criterion"] == "default" else None
                ),
                "focus_width_at_least_95pct": (
                    canvas_ratios[0] >= 0.95 if source["criterion"] == "focus" else None
                ),
            },
            "uncertainty_css_px": {
                "canvas_edge": 1,
                "visible_target_edge": 1,
                "overlay_band_edge": 2,
            },
        }
        if source.get("visible_guide"):
            red, green, blue = image[:, :, 0], image[:, :, 1], image[:, :, 2]
            magenta = (red > 150) & (blue > 130) & (red > green + 50) & (blue > green + 40)
            line_rows = np.where(magenta.sum(axis=1) > raster[0] * 0.2)[0]
            line_cols = np.where(magenta.sum(axis=0) > raster[1] * 0.2)[0]
            row_groups = np.split(line_rows, np.where(np.diff(line_rows) > 1)[0] + 1)
            col_groups = np.split(line_cols, np.where(np.diff(line_cols) > 1)[0] + 1)
            if (
                len(row_groups) != 2
                or len(col_groups) != 2
                or any(not 1 <= len(g) <= 4 for g in [*row_groups, *col_groups])
            ):
                raise ValueError(
                    "Visible guide does not expose two clear horizontal/vertical boundary lines"
                )
            inner = [
                int(col_groups[0][-1]) + 1,
                int(row_groups[0][-1]) + 1,
                int(col_groups[1][0]),
                int(row_groups[1][0]),
            ]
            safe = [v / 2 for v in inner]
            sw, sh = rectangle_size(safe)
            ow, oh = rectangle_size(object_css)
            left, top, right, bottom = object_css
            gaps = {
                "left": left - safe[0],
                "right": safe[2] - right,
                "top": top - safe[1],
                "bottom": safe[3] - bottom,
            }
            clear = {k: value / (sw if k in ("left", "right") else sh) for k, value in gaps.items()}
            clearance_lower = {
                k: (value - 2) / (sw + 2 if k in ("left", "right") else sh + 2)
                for k, value in gaps.items()
            }
            height_interval = [(oh - 2) / (sh + 2), (oh + 2) / (sh - 2)]
            limiting = "height" if oh / sh >= ow / sw else "width"
            dimension = (oh, sh) if limiting == "height" else (ow, sw)
            tight_interval = [
                (dimension[0] - 2) / (dimension[1] + 2),
                (dimension[0] + 2) / (dimension[1] - 2),
            ]
            measured["visible_declared_guide"] = {
                "boundary_core_raster_cols": [g.tolist() for g in col_groups],
                "boundary_core_raster_rows": [g.tolist() for g in row_groups],
                "conservative_inner_raster_rect": inner,
                "conservative_inner_css_rect": safe,
                "conservative_inner_css_size": [sw, sh],
                "method": "Distinct magenta raster pixels; long row/column runs identify dashed guide borders. Interior excludes every solid border pixel; label text does not meet long-run criterion.",
                "object_fraction": {"width": ow / sw, "height": oh / sh},
                "edge_clearance_css_px": gaps,
                "edge_clearance_fraction": clear,
                "conservative_clearance_fraction_lower_bound": clearance_lower,
                "height_fraction_uncertainty_interval": height_interval,
                "limiting_dimension": limiting,
                "limiting_fraction_uncertainty_interval": tight_interval,
                "inside_visible_guide": all(value >= 0 for value in gaps.values()),
                "all_edges_at_least_5pct_with_uncertainty": all(
                    value >= 0.05 for value in clearance_lower.values()
                ),
                "side_height_80_to_90pct_with_uncertainty": (
                    height_interval[0] >= 0.8 and height_interval[1] <= 0.9
                    if source.get("target_kind", "assembly") == "assembly"
                    else None
                ),
                "tight_part_65_to_85pct_with_uncertainty": (
                    tight_interval[0] >= 0.65 and tight_interval[1] <= 0.85
                    if source.get("target_kind") == "tight_part"
                    else None
                ),
                "uncertainty_basis": "±1 CSS px for each target/guide edge; size/gap intervals allow ±2 CSS px, independent of camera values",
                "scope": "Actual visible silhouette versus visible declared guide; no hidden-vertex, interaction or engineering acceptance",
            }
        if source["safe_raster"]:
            safe = [v / 2 for v in source["safe_raster"]]
            sw, sh = rectangle_size(safe)
            ow, oh = rectangle_size(object_css)
            left, top, right, bottom = object_css
            clear = {
                "left": (left - safe[0]) / sw,
                "right": (safe[2] - right) / sw,
                "top": (top - safe[1]) / sh,
                "bottom": (safe[3] - bottom) / sh,
            }
            measured["screenshot_defined_usable_band"] = {
                "raster_rect": source["safe_raster"],
                "css_rect": safe,
                "definition": "Full canvas width below visible source banner and above the first pixels of the bottom-right axes overlay; no camera-derived insets",
                "matches_declared_camera_safe_rectangle": "unmeasured; no such boundary is drawn",
                "object_fraction": {"width": ow / sw, "height": oh / sh},
                "edge_clearance_fraction": clear,
                "all_point_estimates_at_least_5pct": all(v >= 0.05 for v in clear.values()),
                "side_height_80_to_90pct_point_estimate": 0.8 <= oh / sh <= 0.9,
                "rv_q14_acceptance": "unmeasured; screenshot-defined band is not a demonstrated declared camera safe rectangle; borderline edge clearances are not rounded into a pass",
                "remaining_overlay_note": "Local axes/scale overlays are excluded conservatively by the band boundary; target search excludes UI. This does not recover hidden or occluded vertices.",
            }
        results.append(measured)
    result = {
        "date": "2026-11-07",
        "status": "scoped screenshot measurements complete; clean unannotated barometer capture pending",
        "method": "Actual native screenshot raster dimensions, manually identified borders/overlay boundaries, manually reviewed target search regions and RGB segmentation; CSS scale confirmed by sole browser verifier. No camera/geometry math.",
        "source_id": "G80-F2-RP1-AD1-definition-v2",
        "inspection_geometry_sha256": "238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "captures": results,
        "pending_captures": [
            {
                "case": "Same isolated barometer and visible guide with optional selected-part label switched off",
                "purpose": "Unobstructed projected silhouette; annotated capture only establishes exposed bounding extrema",
                "reason": "Sole verifier paused after repeated user-change guards; primary requested current evidence handoff without further browser use",
            }
        ],
        "preserved_nonmatching_captures": [
            {
                "file": str((FOLDER / filename).relative_to(ROOT)),
                "sha256": hashlib.sha256((FOLDER / filename).read_bytes()).hexdigest(),
                "raster_px": list(Image.open(FOLDER / filename).size),
                "reason_not_used_for_fit_acceptance": reason,
            }
            for filename, reason in [
                (
                    "rp1-assembly-fixed-labels-1440x900.png",
                    "Overview and pre-orientation-fix state; not Side preset",
                ),
                (
                    "rp1-baro-framed-1440x900.png",
                    "Selected barometer amid surrounding assembled geometry; not isolated, target bounds/clearance unmeasured",
                ),
                (
                    "rp1-side-tools-closed-default-guide-fixed-1280x900-mis-sized.png",
                    "Named1280x720 but actual raster2560x1800; inconsistent with confirmed uniform2x scaling, not the1280x720 criterion",
                ),
                (
                    "rp1-side-tools-closed-focus-guide-fixed-1280x900-mis-sized.png",
                    "Named1280x720 but actual raster2560x1800; inconsistent with confirmed uniform2x scaling, not the1280x720 criterion",
                ),
                (
                    "rp1-side-tools-closed-focus-guide-fixed-1280x720-verified.png",
                    "True size but Details remains open and header says Focus, not Exit focus; not a Focus layout. Verifier preserved failed interaction/capture state.",
                ),
            ]
        ],
        "limitations": [
            "These are screenshot measurements, separate from interaction observations and engineering acceptance",
            "Visible raster silhouette bounds do not prove every source vertex is visible",
            "Pre-correction captures lack a declared guide; post-correction guide measurements use actual magenta raster boundaries",
            "Canvas/app dimensions use the captured full application viewport; browser chrome is outside these PNGs",
        ],
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "layout-capture-measurements.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            [
                {
                    "file": r["file"],
                    "canvas_css": r["canvas_css_size"],
                    "canvas_fraction": r["canvas_viewport_fraction"],
                    "object_css": r["visible_object_css_size"],
                }
                for r in results
            ]
        )
    )


if __name__ == "__main__":
    main()
