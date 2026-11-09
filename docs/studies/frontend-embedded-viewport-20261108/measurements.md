# Embedded native screenshot pixel measurements

Only the two immutable native JPEGs below were measured. Coordinates are raster pixels, half-open `[left, top, right, bottom)`. The original images and AX records were not edited. The app is a **nested same-origin real Rocket Twin viewport**, not a top-level Chrome content viewport.

| Native case and SHA-256 | Pink inner app rect | Visible canvas-colored rect | Canvas / inner app width, height |
| --- | --- | --- | --- |
| P28, current RP1 Design, default Overview, no part selected<br>`runs/frontend-embedded-viewport-pilot-native-20261108/ready-1440.jpg`<br>`e8ea8468090adace190b9e74b952e166a5c965074cf3de57fccd0c3355e8e62b` | `[14, 396, 2894, 2196]` | `[672, 578, 2894, 2064]` | 77.1528% (range 77.0139%–77.2917%), 82.5556% (range 82.3333%–82.7778%) |
| P29, same embedded RP1 Design, default Overview, Nose selected<br>`runs/frontend-embedded-viewport-resize-native-20261108/resized-1280.jpg`<br>`6c5d23c41c3d38d942b73adac0fbefa7ee498779f57cd6c24f53d9859881b47b` | `[14, 396, 2574, 1836]` | `[672, 578, 2574, 1704]` | 74.2969% (range 74.1406%–74.4531%), 78.1944% (range 77.9167%–78.4722%) |

The magenta outer frame has an observed 8-raster-pixel band on each side. Its inner rectangle is 2880×1800 or 2560×1440 raster pixels, consistent with the **actual native AX readouts** of 1440×900 or 1280×720 CSS pixels at DPR 2. This is a correspondence check, not a substitution of requested sizes for image measurements. The canvas-colored area begins after visible sidebar/top borders and reaches the inner frame's right edge; no separate right canvas border is visible. Each canvas edge carries ±2 raster pixels of JPEG/antialiasing interpretation uncertainty, propagated to the ratio ranges. The 1280×720 height range straddles 78%; this image alone does not resolve that threshold.

Both screenshots show **Overview**, not Side; P28 has no selected part, while P29 retains Nose selection. No side-fit Q14, focused-width, exact DOM `canvas.clientWidth`, physical/CAD projection, top-level viewport, or full responsive/keyboard criterion is established by these pixels. Primary owns acceptance. [Machine-readable record](measurements.json) retains the hashes, bounds and uncertainty.
