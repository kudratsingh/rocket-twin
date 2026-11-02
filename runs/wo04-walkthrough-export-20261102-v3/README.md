# Offline walkthrough export v3

Regenerate with: `node scripts/wo04_export_walkthrough_drawings.mjs`.

Local drawings and accessible index: `output/engineering-walkthrough/index.html`. Generated SVG bulk is a local artifact; publish the script, small record and source manifest instead.

V3 retains the wrapped standalone headers to width-aware lines capped at120characters and derives drawing/footer vertical positions from the header height. This is a source-observed presentation correction, not a visual acceptance claim.

The preserved previous record, manifest and exact exporter source are in `runs/wo04-walkthrough-export-20261102-v2`. This exporter makes no renderer attempts. Companion native AppKit rendering is recorded separately; no browser observations are claimed. V3 fixes normalized marker references after missing arrowheads were observed in actual offline PNGs.
