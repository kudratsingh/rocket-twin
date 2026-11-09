"""Measure two immutable native JPEGs by visible pixel edges; no browser or DOM use."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/studies/frontend-embedded-viewport-20261108"
CAPTURES = (
    {
        "image": "runs/frontend-embedded-viewport-pilot-native-20261108/ready-1440.jpg",
        "ax": "runs/frontend-embedded-viewport-pilot-native-20261108/ready-1440.ax.txt",
        "sha256": "e8ea8468090adace190b9e74b952e166a5c965074cf3de57fccd0c3355e8e62b",
        "viewport_css_px": [1440, 900],
        "state": "P28, current RP1 Design, default Overview, no part selected",
    },
    {
        "image": "runs/frontend-embedded-viewport-resize-native-20261108/resized-1280.jpg",
        "ax": "runs/frontend-embedded-viewport-resize-native-20261108/after.ax.txt",
        "sha256": "6c5d23c41c3d38d942b73adac0fbefa7ee498779f57cd6c24f53d9859881b47b",
        "viewport_css_px": [1280, 720],
        "state": "P29, same embedded RP1 Design, default Overview, Nose selected",
    },
)
EDGE_UNCERTAINTY_PX = 2  # JPEG antialiasing and visible-edge interpretation, each edge.


def size(rect: list[int]) -> list[int]:
    return [rect[2] - rect[0], rect[3] - rect[1]]


def measure(entry: dict) -> dict:
    image_path = ROOT / entry["image"]
    raw = image_path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != entry["sha256"]:
        raise ValueError(f"Capture hash changed: {entry['image']}")
    image = np.asarray(Image.open(image_path).convert("RGB"), dtype=np.int16)
    raster = [int(image.shape[1]), int(image.shape[0])]
    if raster != [4480, 2460]:
        raise ValueError(f"Unexpected native raster: {entry['image']}: {raster}")

    # Magenta fixture outline, observed as four uninterrupted ~8-raster-pixel bands.
    red, green, blue = image[:, :, 0], image[:, :, 1], image[:, :, 2]
    pink = (red > 180) & (blue > 100) & (red > green * 1.7) & (blue > green * 1.4)
    ys, xs = np.where(pink)
    outer = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    left_band = np.where(pink[(outer[1] + outer[3]) // 2, outer[0] : outer[0] + 20])[0]
    top_band = np.where(pink[outer[1] : outer[1] + 20, (outer[0] + outer[2]) // 2])[0]
    right_band = np.where(pink[(outer[1] + outer[3]) // 2, outer[2] - 20 : outer[2]])[0]
    bottom_band = np.where(pink[outer[3] - 20 : outer[3], (outer[0] + outer[2]) // 2])[0]
    if not all(len(band) == 8 for band in (left_band, top_band, right_band, bottom_band)):
        raise ValueError(f"Magenta outline thickness ambiguous: {entry['image']}")
    inner = [outer[0] + 8, outer[1] + 8, outer[2] - 8, outer[3] - 8]

    ax = (ROOT / entry["ax"]).read_text()
    width, height = entry["viewport_css_px"]
    expected_readout = (
        f"Requested {width}×{height} CSS; actual inner {width}×{height}, "
        f"document client {width}×{height}, frame rect {width}×{height}, DPR 2; size match yes"
    )
    if expected_readout not in ax or size(inner) != [width * 2, height * 2]:
        raise ValueError(f"Native readout/pink inner rectangle mismatch: {entry['image']}")

    # At y=700..1000 the left scene edge is a long, uniform sidebar-to-dark-canvas
    # transition. Find the strongest median horizontal step only in that reviewed band.
    horizontal = np.median(image[700:1000, 650:700], axis=0)
    steps = np.linalg.norm(np.diff(horizontal, axis=0), axis=1)
    canvas_left = 650 + int(np.argmax(steps)) + 1
    if canvas_left != 672:
        raise ValueError(f"Canvas left transition moved: {entry['image']}: {canvas_left}")

    # The top scene border is two broad gray rows. Its following row begins the
    # uniform dark canvas. Use a clean strip away from the camera toolbar.
    top_strip = np.median(image[570:590, 800:1000], axis=1)
    top_rows = np.where(np.max(np.abs(top_strip - [65, 79, 90]), axis=1) <= 4)[0] + 570
    if top_rows.tolist() != [576, 577]:
        raise ValueError(f"Canvas top border ambiguous: {entry['image']}: {top_rows}")
    canvas_top = int(top_rows[-1]) + 1

    # The bottom scene border is the last two contiguous full-width gray rows
    # above the tools strip. A selected-part card may introduce an earlier one-row
    # false candidate, so require consecutive rows and two separated x probes.
    y0, y1 = inner[3] - 200, inner[3] - 80
    bottom_strip = np.median(
        np.concatenate([image[y0:y1, 800:1000], image[y0:y1, 2000:2200]], axis=1),
        axis=1,
    )
    candidates = set(
        (np.where(np.max(np.abs(bottom_strip - [44, 53, 60]), axis=1) <= 4)[0] + y0).tolist()
    )
    starts = [y for y in candidates if y + 1 in candidates]
    if len(starts) != 1:
        raise ValueError(f"Canvas bottom border ambiguous: {entry['image']}: {starts}")
    canvas_bottom = int(starts[0])

    # At a clean mid-scene row the dark canvas reaches the inner right fixture
    # edge. There is no separate right canvas border to detect in these captures.
    canvas_right = inner[2]
    edge_pixel = image[1000, canvas_right - 2].tolist()
    if max(abs(edge_pixel[i] - [23, 28, 34][i]) for i in range(3)) > 5:
        raise ValueError(f"Canvas-colored region does not reach frame edge: {entry['image']}")
    canvas = [canvas_left, canvas_top, canvas_right, canvas_bottom]
    dimensions = size(canvas)
    ratios = [dimensions[0] / size(inner)[0], dimensions[1] / size(inner)[1]]
    ratio_ranges = [
        [
            (dimension - 2 * EDGE_UNCERTAINTY_PX) / denominator,
            (dimension + 2 * EDGE_UNCERTAINTY_PX) / denominator,
        ]
        for dimension, denominator in zip(dimensions, size(inner))
    ]
    return {
        "image": entry["image"],
        "sha256": digest,
        "ax_source": entry["ax"],
        "state": entry["state"],
        "native_raster_px": raster,
        "reported_embedded_viewport_css_px": entry["viewport_css_px"],
        "reported_dpr": 2,
        "outer_magenta_rect_raster_px_half_open": outer,
        "magenta_thickness_raster_px": 8,
        "inner_app_rect_raster_px_half_open": inner,
        "visible_canvas_region_rect_raster_px_half_open": canvas,
        "visible_canvas_region_size_raster_px": dimensions,
        "canvas_to_inner_app_size_ratio": ratios,
        "canvas_to_inner_app_size_ratio_uncertainty_range": ratio_ranges,
        "edge_uncertainty_raster_px_each": EDGE_UNCERTAINTY_PX,
        "canvas_right_boundary_basis": "dark scene reaches inner app's right magenta boundary; no separate canvas border",
        "scope": "Native screenshot pixel transitions in an embedded real app; not DOM client bounds, side-fit, top-level viewport, or RV acceptance",
    }


def main() -> None:
    rows = [measure(entry) for entry in CAPTURES]
    report = {
        "schema_version": "rocket-twin.embedded-native-pixel-measurements.v1",
        "method": "unchanged JPEG pixels; half-open rectangles; 8px magenta outline; two CSS px per raster scale verified against native AX readout",
        "measurements": rows,
        "acceptance": None,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "measurements.json").write_text(json.dumps(report, indent=2) + "\n")
    lines = [
        "# Embedded native screenshot pixel measurements",
        "",
        "Only the two immutable native JPEGs below were measured. Coordinates are raster pixels, half-open `[left, top, right, bottom)`. The original images and AX records were not edited. The app is a **nested same-origin real Rocket Twin viewport**, not a top-level Chrome content viewport.",
        "",
        "| Native case and SHA-256 | Pink inner app rect | Visible canvas-colored rect | Canvas / inner app width, height |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        width_ratio, height_ratio = row["canvas_to_inner_app_size_ratio"]
        width_range, height_range = row["canvas_to_inner_app_size_ratio_uncertainty_range"]
        lines.append(
            f"| {row['state']}<br>`{row['image']}`<br>`{row['sha256']}` | "
            f"`{row['inner_app_rect_raster_px_half_open']}` | "
            f"`{row['visible_canvas_region_rect_raster_px_half_open']}` | "
            f"{width_ratio:.4%} (range {width_range[0]:.4%}–{width_range[1]:.4%}), "
            f"{height_ratio:.4%} (range {height_range[0]:.4%}–{height_range[1]:.4%}) |"
        )
    lines += [
        "",
        "The magenta outer frame has an observed 8-raster-pixel band on each side. Its inner rectangle is 2880×1800 or 2560×1440 raster pixels, consistent with the **actual native AX readouts** of 1440×900 or 1280×720 CSS pixels at DPR 2. This is a correspondence check, not a substitution of requested sizes for image measurements. The canvas-colored area begins after visible sidebar/top borders and reaches the inner frame's right edge; no separate right canvas border is visible. Each canvas edge carries ±2 raster pixels of JPEG/antialiasing interpretation uncertainty, propagated to the ratio ranges. The 1280×720 height range straddles 78%; this image alone does not resolve that threshold.",
        "",
        "Both screenshots show **Overview**, not Side; P28 has no selected part, while P29 retains Nose selection. No side-fit Q14, focused-width, exact DOM `canvas.clientWidth`, physical/CAD projection, top-level viewport, or full responsive/keyboard criterion is established by these pixels. Primary owns acceptance. [Machine-readable record](measurements.json) retains the hashes, bounds and uncertainty.",
        "",
    ]
    (OUT / "measurements.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
