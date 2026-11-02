# Offline walkthrough export v2

Regenerate with: `node scripts/wo04_export_walkthrough_drawings.mjs`.

Local drawings and accessible index: `output/engineering-walkthrough/index.html`. Generated SVG bulk is a local artifact; publish the script, small record and source manifest instead.

V2 wraps every standalone header to width-aware lines capped at120characters and derives drawing/footer vertical positions from the header height. This is a source-observed presentation correction, not a visual acceptance claim.

The preserved v1 record, manifest and exact exporter source are in `runs/wo04-walkthrough-export-20261102-v1`. V2 makes no native renderer attempts. Historical native PNG failures remain recorded; no PNG or browser observations are claimed.
