# RP1 inspection geometry — offline visual QA

The [six-view contact sheet](../../../output/frontend-release-20261107/rp1-inspection-contact-sheet.png)
renders the **actual 26 verified GLBs** for frozen
`G80-F2-RP1-AD1-definition-v2`. It contains two orthogonal elevations, the
motor-end view, an oblique projection, a body-hidden interior and a cropped
body-hidden aft detail. The original saved preview is unchanged.

The image was generated with existing trimesh and Matplotlib Agg, then inspected
with `view_image`. It is an **offline geometry
projection**, not a browser screenshot, product camera-fit acceptance,
interaction observation, manufacturing release or physical validation. No CAD,
physics, field, knot, joint or missing hardware geometry was generated.

## Source and representation identity

Inspection geometry SHA-256:
`238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`.
The read-only `src.api.rp1_geometry.build` adapter first verifies the exact source
and saved/generated manifests and all mesh bytes. Each GLB is then reread,
rehashed and loaded with its actual node transforms. Actual bounds are checked
against the manifest within 0.2 micrometres of numeric conversion tolerance;
that is a file/frame check, not a manufacturing tolerance.

The frame is the existing viewer convention: X=body+y, Y=vehicle length minus
station, Z=body−z. GLB coordinates are metres; plotted axes are millimetres.
Viewer Y=0 is the aft length datum, and the nose tip is at Y=1250 mm.
The script does not apply source stations a second time.

The 55 source records retain **10 source-dimensioned estimates, 16 simplified
envelopes, 25 mass allowances and four missing-geometry records**. The first
two categories supply the 26 actual meshes. Source-dimensioned surfaces are
opaque; simplified envelopes are translucent. The script projects actual
triangles, uses centroid depth ordering and simple face-normal display lighting.
This is a display approximation, without new surfaces, shadows or field values.

The interior/detail views hide exactly `nose`, `body` and `upper_body`; the
remaining 23 mesh parts retain their exported positions. The aft detail also
crops the plot to viewer Y=0–235 mm and X=−105–105 mm. It is not a newly cut
solid or manufactured section. All 25 allowances remain without solids. The
four missing representations—thermal shield sectors, actual Kevlar wrap/knots,
rail buttons and rail backers—remain absent and explicit in the figure manifest.

## Quantitative actual-mesh checks and visual observations

The whole assembly's loaded GLB bounds, in metres, are:

```text
minimum [-0.04929857701063156, 0.0,  -0.08238764107227325]
maximum [ 0.09340099990367890, 1.25,  0.08238764107227325]
```

These agree with the saved inspection bounds after GLB float conversion.
The longitudinal span is 1250 mm; the other spans and every part's bounds,
triangle count and mesh hash are retained in the
[figure manifest](../../../output/frontend-release-20261107/rp1-inspection-figure-manifest.json).
The three-fin footprint is asymmetric in X as expected from the recorded
0/120/240-degree arrangement; no symmetric replacement box was used.

The opened contact sheet shows the pointed nose above the continuous body,
three distinct radial fin directions in the motor-end view, and the aft
motor/retainer envelope at the Y=0 datum. The interior view exposes the actual
source avionics/pack envelopes and the separate aft mesh groups; it does not
fill the missing route or hardware. The aft crop makes the separate fin-panel,
tab/gusset and ring/tube representations visible. Full elevations preserve
physical aspect ratio, so the long slender vehicle occupies a narrow plot.
These observations concern this static exported representation only.

The model still lacks actual installed joint geometry, supplier details and
physical attachment/thermal/recovery/flutter acceptance. In particular, a
translucent source envelope does not establish clearance, the forward notch
still omits proposed edge roundovers, and visually adjacent parts do not
establish a load path or bonded fit. Canonical resolved vehicle/CAD identities
and RP1 inertia remain unavailable.

## Reproduction and bounded result

```sh
.venv/bin/python scripts/wo04_rp1_inspection_figures.py
```

The script sets a 20-second CPU timer and 30-second wall timer, verifies the
existing assets and writes only the new ignored release-output directory.
The final render completed in **1.414 CPU seconds / 1.617 wall seconds**.
One display correction improved lighting and title spacing; mesh content,
coordinates and source identities did not change. No backend/renderer failure,
new dependency, native renderer, computer-use session or browser was involved.
Ruff and Black checks passed for the new script.

Final contact sheet: 2400×1800 pixels, SHA-256
`3dcd47de137def39c684214be35a91dc2f28854750b8c6585276c454a84c0aa2`.
The generated figure manifest records the exact raw script SHA-256, source
manifest SHA-256, installed tool versions, all 26 actual asset hashes/bounds,
omitted records and timing. The raw script is provided as
`scripts/wo04_rp1_inspection_figures.py`, SHA-256
`ba4fef27fd1dbb4d19b6d29492b2e9abf5677d9379b0014e58b1fdcfb89704e0`;
the PNG and figure manifest remain
local generated artifacts. All browser, engineering and physical gates remain
unchanged.
