# Engineering connections workbench

This increment preserves the original inspection, experiment/replay and first
C1 walkthrough, and adds **six graphical views** using a separate versioned
backend document. The browser computes no flight, thermal, structural or mass
result. Full WO-03/04/05 acceptance and every owner/release gate remain open.

Start at the repository root with `make preview`, then open
`http://127.0.0.1:5173/?workspace=engineering`.
`make workbench` prepares both source-checked JSON documents without a solver.
The API endpoint is `/api/engineering/workbench-extended`; only a404 from an
older API permits the explicitly labelled prepared-export fallback.

| View query | Graphic and useful question |
| --- | --- |
| `&view=comparison` |Six candidates/twelve saved cases: C1, R1, C2, C3 and separate A/B concepts. Compare mass, balance, static margin, guide speed, recovery demand and each stop reason. Stop-joint controls select known C1 interfaces; A/B have no invented current-C1 CAD mapping. |
| `&view=recovery` |Directed harness/retained-body topology and selectable packing/extraction storyboards. See which attachment retains each branch and which force/space assumptions lack evidence. |
| `&view=thermal` |Motor boundaries, shielding, solid/contact/adhesive paths and real openings, with current interfaces and39 historical scalar records. Historical layout/campaign results are incompatible with current C1; no spatial map or invented time samples/curves. |
| `&view=electrical` |Recorded power/signal nets, independent recovery power and planned control blocks. Exact pin assignments remain undefined. Topology is not verified wiring, firmware or power qualification. |
| `&view=assembly` |Source-defined joint layers and installation/removal/access sequences. Illustrations do not prove extraction, articulation, packing or tool clearance. |
| `&view=requirements` |Physical requirement/evidence graph organized around structure, heat, recovery, fit/service, stability, guide/equipment and later owner tests. Software checks are not engineering-pass indicators. |

Selecting a mapped node, connection, part link or joint carries selection to the
current inspector; the selected diagram region has a distinct outline. Tab
navigation preserves the current part. Missing/incompatible candidate mappings
remain explicit. Large SVGs scroll horizontally and each figure has an SVG export
control carrying identity/units/status metadata. The original3D viewer retains
camera/visibility/explode/section controls; current C1 has no complete compatible
CAD, so selecting an A/B concept does not substitute archived geometry.

## Provenance and evidence boundaries

The frozen C1 identity remains `C1_closed_receiver_mass_balance`, spec SHA-256
`d76c34c69c64b9281d0e945643b95d79385393ab7d40156c7cdbc6a601f15228`,
with CAD revision unavailable. The first135 allocation/envelope rows are not
manufacturing-ready CAD. New extension values derive from33 pinned sources,
including the immutable A/B screen. Full rotational inertia stays null.

The first four candidate projections are regression-checked unchanged. A/B are
concept/NOT ADMITTED; A's preference is limited to the next bounded connection
study. The new A/B geometry does not replace the frozen C1 recovery diagram or
thermal interfaces. Calculated, estimated, measured, failed, superseded,
historical and unavailable evidence remain distinct. No new measured capacity
or accepted stress/temperature field is supplied.

## Offline images that were actually inspected

The installed AppKit image-document API renders SVG without a window, WebView
or browser. Earlier `sips` and QuickLook failures remain historical; neither
unchanged failed command was repeated. Image review found an exporter marker-ID
bug, then a native marker-rendering limitation. A separately bounded portability
packet converted only recognized project arrow templates using the recorded
endpoint/tangent. A straight/circular fixture and real FBD/topology images then
showed their arrowheads. Unknown patterns stop instead of inventing directions.

- 25 C1/R1 pages: `output/engineering-walkthrough-rendered/contact-sheet.png`.
- 11 new-view pages and index: `output/engineering-workbench-extended/index.html`.
- Two A/B concept images: `output/wo03-architecture/`.

Representative actual images were inspected for labels, units, arrows and
clipping. This does not claim exhaustive full-size inspection of every source
footer or every interactive selection state. Native rasterization is not a
browser screenshot. Retain the separate browser interaction checklist below.

The preserved V3 extension image packet measured75.24 ms React server rendering and
41.71 s native rendering on this host; document242050 bytes, six graph objects
55605 bytes/80 nodes/103 edges. These are recorded **offline timings and sizes**,
not network loading, interaction latency or browser frame rate. Later UI-only
image corrections have separate records; no frame-rate benchmark is claimed.

Maintained export/render commands write disposable records under `build/` so
historical source/observation records are preserved. Exact old exporters are
archived. Generated SVG/PNG/JSON bulk remains local and ignored by Git; the
source generators, small records/manifests and source-only fixtures are published.

## Pending browser interaction checklist

Only the designated frontend agent may use the permitted Chrome window after
runtime ownership is established. The recorded automatic approval rejection
remains unresolved; no alternate agent/window/headless bypass is used.

Still pending actual browser evidence: all configuration/tab switches, node and
keyboard selection, inspector correspondence, hide/isolate/explode, SVG downloads,
responsive layout, real experiment execution/replay/comparison, WebGL and host URL
reachability. Code/API/SSR/image checks support those features but do not replace
click/runtime observations. User startup commands and offline drawings remain
available while that path is blocked.

## Final image and download-provenance corrections

Actual image review found a main-power route drawn through unrelated boxes.
The electrical-only correction separates main avionics and independent recovery
into labelled lanes without changing12nodes/11nets. The V4 image record reports
one38.71s native batch; sampled route checks and direct PNG inspection found no
line through an unrelated component box. Other ten image hashes are unchanged.
A beginner glossary explains baro, IMU, high-g, SPI, MOSFET and AWG in the app
and offline index.

A separate download-provenance correction now passes the extension's full33
sources to the existing browser SVG helper, without mutating the frozen C1
15-source document. Code-level metadata tests pass; the download was not clicked
in a browser. Server rendering proves all11SVG bodies byte-identical to the
actual V4 rendered source; added glossary CSS is confined to an HTML-only sibling.
No native image rerun was needed for that metadata-only change. The initial
whole-CSS-identity check failure and corrected scope reasoning are preserved in
`runs/wo04-export-provenance-20261102-v1`.
