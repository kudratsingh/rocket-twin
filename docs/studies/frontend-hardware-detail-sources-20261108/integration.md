# PCB detail integration and verification boundary

The high-g accelerometer now has a manufacturer-source 2D board drawing in its RP1 Details panel. Exact part/configuration/specification guards exclude other designs. It exposes the real outline, four mounting drills and 26 listed placements, with selectable footprint information, a larger drawing and SVG export. This is a footprint reference, not an invented three-dimensional populated board. The current envelope remains unchanged.

## What was verified

The authorized native Chrome check opened the drawing and observed its dimensions, source identity and U1 discrepancy. Escape failed because the outer sidebar captured the native dialog key; its frozen failure record remains in [browser-high-g.md](browser-high-g.md). Shared modal ownership now protects native-dialog descendants (including SVG focus) from sidebar/Focus/application keyboard handlers. Tests cover that correction; no subsequent native Escape, dropdown or download verification is claimed. The bounded browser packet is exhausted; do not retry automatically.

The actual React SVG was exported offline with configuration/specification/part/drawing identity, source/license and limitations in metadata. An initial native render was incorrectly 30×810 because a percentage CSS width overrode its standalone dimensions. That attempt is preserved under `output/frontend-interiors-20261108/high-g-board/first-native-attempt/`. Removing only the root percentage style produced 900×810. The primary inspected the corrected image: readable outline, pads, four holes, units/title/attribution, without clipping. The final metadata-only re-export has the same PNG hash. Combined native rendering stayed below the declared 90-second allowance. These are offline document images, not browser screenshots.

Open `output/frontend-interiors-20261108/high-g-board/index.html` or its SVG/PNG. Reproduce with `node scripts/wo04_export_high_g_board.mjs --png`; the existing offline helper is optional and no package installation is attempted. Optional raw XML cache permits full Python regeneration; source/cache-dependent checks skip explicitly when it is absent, while tracked-data/source-gate tests remain active.

## Remaining evidence

- Source PCB25.4×17.78mm differs from nominal envelope25.6×17.7mm; datums, tolerances, component heights and incoming revision remain unavailable.
- U1 retains ADXL343 from the official ADXL375/PID5374 file. No installed silicon identity is inferred.
- No source-detailed generic electronics, retainer threads or rope/knot geometry was invented.
- No vehicle, mass, CAD/inertia, thermal, strength, build or flight acceptance changes. All five inquiry drafts remain UNSENT.

The earlier baseline and integrated camera/interior capture inventories remain immutable. The existing DevTools automatic-review rejection still blocks the exact viewport setup; this packet neither retries nor bypasses it.
