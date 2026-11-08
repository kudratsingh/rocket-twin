# Native browser capture measurements

Current captured default canvases clear the 72% width/78% height thresholds at
1440×900 and 1280×720; actual Focus captures clear 95% width at both sizes.
Explicit Side fits with visible guides measure 83.03% and 83.25% height with
conservative minimum clearances of 7.92% and 7.63%. The annotated isolated
barometer's exposed bounding extent clears the tight-part raster thresholds;
its clean, unannotated counterpart remains pending.

This packet measures actual native Chrome PNG pixels. The sole browser verifier
confirmed 100% zoom and full application viewports. Raster dimensions are exactly
twice the named CSS viewport in both axes: 2880×1800 for 1440×900 CSS pixels,
and 2560×1440 for 1280×720. All rectangles below use half-open bounds. Canvas
edges are identified from visible panel/border colour changes; target contours
use manually reviewed raster regions and cyan/tan pixel segmentation. No camera
projection, source bounds or source fit ratio supplies a measurement.

The accompanying [JSON](layout-capture-measurements.json) retains image SHA-256,
state, raster and CSS rectangles, segmentation regions, overlay exclusions and
uncertainty. Reproduce with
`scripts/wo04_browser_capture_measurements.py`. The measured source is
`G80-F2-RP1-AD1-definition-v2`, inspection identity
`238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`.

## Before the screen-right basis correction

The following captures precede the primary's screen-right camera-basis
correction and do not show a declared framing guide. Their layout measurements
remain valid evidence of their exact captured states. An overview, a Side
preset and a selected part amid an assembled rocket are distinct states.

| Exact PNG filename | Captured state | Canvas CSS px | Width / viewport | Height / viewport | Layout threshold result |
| --- | --- | ---: | ---: | ---: | --- |
| `rp1-side-tools-open-1440x900.png` | Side, both columns open, Scene tools **open** | 1127×536 | 78.264% | 59.556% | Inapplicable to tools-closed default; observed values retained |
| `rp1-side-tools-closed-default-1440x900.png` | Side, both columns open, tools closed, no selection/CG/CP | 1127×782 | 78.264% | 86.889% | Clears ≥72% width and ≥78% height |
| `rp1-side-tools-closed-focus-1440x900.png` | Side, Exit focus visible, both columns absent, tools closed | 1440×782 | 100% | 86.889% | Clears ≥95% focus width |
| `rp1-side-tools-closed-default-1280x720.png` | Side inherited across resize, both columns open, tools closed | 967×602 | 75.547% | 83.611% | Clears ≥72% width and ≥78% height |
| `rp1-side-tools-closed-focus-1280x720.png` | Side, Exit focus visible, both columns absent, tools closed | 1280×602 | 100% | 83.611% | Clears ≥95% focus width |

Canvas-border uncertainty is approximately ±1 CSS pixel per edge. These layout
passes are comfortably away from their thresholds. The open-tools capture was
originally named `rp1-side-default-1440x900.png`; it was preserved and given an
explicit state name. Its short canvas is not evidence that the tools-closed
default fails. The earlier `rp1-assembly-fixed-labels-1440x900.png` is an overview
with a pre-orientation-fix state and cannot establish Side framing.

Observed target silhouettes are 65×501.5 CSS px at 1440×900 and 45.5×353.5 CSS px
at 1280×720. The open-tools silhouette is 39×298.5 CSS px and has excluded CG/CP
label overlays. Approximate contour uncertainty is ±1 CSS pixel per edge.

For descriptive comparison only, a conservative screenshot-defined rectangular
band spans the canvas width between the bottom of the visible source banner
and the first pixels of the bottom-right axes widget. This is explicitly
**not** a demonstrated camera-safe rectangle. The 1440 default target occupies
about 85.4% of this band's height, but its lower gap is only about 4.8% with
roughly half a percentage point uncertainty. No ≥5% clearance pass follows.
The full per-edge values and other states are in JSON. No pre-guide image
establishes formal fit acceptance against the unshown declared safe rectangle.

## After the correction: visible framing guide

The post-correction screenshots draw a magenta dashed rectangle explicitly
labelled “Framing area · display guide, not a rocket part.” Its boundaries are
measured from distinctive magenta pixel runs, not helper fractions. Solid guide
pixels are excluded to form a conservative interior rectangle. The guide label
does not meet the long-row/column detection threshold, and its colour is
excluded from the target mask.

| Post-correction PNG | Guide interior CSS rectangle | Visible target CSS rectangle | Target / guide height | Smallest edge clearance |
| --- | --- | --- | ---: | ---: |
| `rp1-side-tools-closed-default-guide-fixed-1440x900.png` | `[330,137,1309,741]` | `[789,189.5,854,691]` | **83.03%** | **8.28%**, bottom |
| `rp1-side-tools-closed-focus-guide-fixed-1440x900.png` | `[17,137,1309,741]` | `[632.5,189.5,697.5,691]` | **83.03%** | **8.28%**, bottom |
| `rp1-side-tools-closed-default-guide-fixed-1280x720-refit.png` | `[330,137,1149,561]` | `[718,173.5,764,526.5]` | **83.25%** | **8.14%**, bottom |
| `rp1-baro-isolated-guide-fixed-1440x900.png` | `[330,137,1309,741]` | `[771,202.5,868,675.5]` | **78.31%**, limiting height | **10.84%**, top/bottom |

For the 1440 Side captures, allowing ±1 CSS pixel per target/guide edge gives
an 82.43–83.64% height interval. The conservative minimum clearance lower bound
is 7.92%. These measured silhouettes therefore clear the scoped 80–90% Side
height and ≥5% edge criteria. The matching default canvas remains 1127×782 CSS
pixels and Focus remains 1440×782, clearing the layout criteria above.

The isolated barometer has a 97×473 CSS-pixel silhouette, with a 77.72–78.90%
limiting-dimension interval and a conservative minimum clearance lower bound
of 10.48%. Its measured bounding extent clears the scoped 65–85% tight-part
and ≥5% edge criteria. A selected-part label card overlaps the middle/right of
the part. All four bounding extremes remain visible above/below/beside the
card, and its pixels are excluded from segmentation; the screenshot does not
establish an unobscured entire surface or hidden-vertex visibility.

The first post-correction files named `*guide-fixed-1280x720.png` were actually
2560×1800 raster pixels. They cannot establish the 1280×720 criterion under the
confirmed uniform 2× scaling. They are preserved as
`*guide-fixed-1280x900-mis-sized.png` with hashes in JSON. No anisotropic scaling,
crop or filename-based inference turns them into valid 720-high captures.
No passing value is substituted from source math.

The verifier subsequently supplied a distinct true-size capture,
`rp1-side-tools-closed-default-guide-fixed-1280x720-verified.png`, SHA-256
`c97d5a475c4bdcd85efa5f0bc54437d7e9c39c7446fb419f4ea63ec9ef9253de`.
Its header is confirmed 2560×1440. The canvas remains 967×602 CSS pixels and
passes the layout thresholds. **Its retained Side framing does not pass the
measured fit thresholds:** the guide interior is `[330,137,1149,561]`, while
the silhouette is `[729,158,779,543.5]` CSS pixels. Height fill is 90.92%, top
clearance 4.95% and bottom clearance 4.13%. These values are retained as a
failure/transition observation. The initial capture message confirmed the
committed viewport height. The verifier subsequently confirmed that it retained
the prior camera state immediately after resize, with **no new Side/Fit after
the height commit**. Its threshold misses are therefore a preserved resize
transition, not an explicit-after-resize Fit result. Neither filename nor a
mathematically passing test replaces these raster results.

The distinct explicit-after-resize capture,
`rp1-side-tools-closed-default-guide-fixed-1280x720-refit.png`, is confirmed
2560×1440, SHA-256
`9720ffe6f7d821f794c4170c5df44c3100d6c0ee85815763364f699778f52838`.
It restores the unfiltered Parts tree, both columns and closed tools, and the
verifier confirms Side/Fit after the true 720-high viewport committed. Its
83.25% height estimate has an 82.39–84.12% uncertainty interval; the smallest
clearance lower bound is 7.63%. It therefore clears the scoped Side raster
thresholds. Its 967×602 CSS-pixel canvas clears 72% width/78% height as well.
The earlier transition remains separate evidence and is not rewritten as a
passing refit.

The true 1280 Focus capture is
`rp1-side-tools-closed-focus-guide-fixed-1280x720-refit.png`, SHA-256
`8c909cd91385d9ebecfb6ce2af15002ab486a9e4edab5442fbd69a7d45074f24`.
Its 2560×1440 raster visibly shows Exit focus, both columns absent and closed
tools. Canvas interior `[0,52,1280,654]` is **1280×602 CSS pixels, 100% viewport
width**, clearing the ≥95% Focus-width criterion. Its legacy filename contains
“guide,” but the guide is actually off after remount. No visible-guide fit ratio
is inferred for this capture. The earlier purported Focus image ending
`1280x720-verified.png`, SHA beginning `d9daf1fd`, visibly retained Details and
a “Focus” button; it is preserved in JSON as a nonmatching state, not counted
as Focus evidence.

These screenshot measurements are separate from keyboard/pointer interaction
evidence, hidden-vertex visibility, engineering acceptance and physical release.

## Handoff limit

The sole verifier paused after repeated user-change guards on the browser
window. At the primary's direction, this packet is finalized from the existing
captures. The clean same-target barometer capture with its optional selected-part
label switched off is **pending**, so no unobstructed-part screenshot is claimed.
It can be appended after the owner returns the permitted window to the verifier.
The annotated counterpart, wrong-size captures, wrong-Focus capture and
pre-refit resize transition remain immutable evidence with their original hashes.
No further browser/computer use occurred in this measurement lane.

The new measurement script passes Ruff and Black. It uses existing Pillow and
NumPy, measures known native pixels and writes only these new report artifacts;
no package installation, CAD, simulation, renderer, camera calculation or shared
ledger edit was performed.
