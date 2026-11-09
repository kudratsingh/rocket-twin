# Source-backed desktop inspection tools

This is the capability increment following the owner's saved desktop-first
priority. Current physical RP1/AD1/D1 and core geometry are unchanged. It adds no
fin variant, flight input, assumed hardware detail or engineering qualification.

## What to open

Start the normal host preview from the repository with `make preview`; use
http://127.0.0.1:5173/ (the Python API on8000 is not the frontend).

- **Design → Detail coverage → Inspect modeled detail** selects and frames an
  existing source detail, keeping missing rope, retainer and electronics features
  explicit. The forward ring exposes its recorded annulus, layers and straight
  passage; it does not demonstrate a finished recovery attachment. Restore
  visibility returns the previous display visibility.
- **Adjust section cut** opens Scene tools. Rotate an along-rocket plane, move it
  sideways, reverse the retained side, or choose an across-rocket station in mm
  aft from the recorded nose tip. A station is simply a position along the rocket.
  The default preserves the original X=0 cut. At150degrees the normal gives a
  plane through the recorded60degree radial passage, using the documented GLB
  coordinate mapping. Cuts reveal existing geometry without adding a cut cap or
  missing manufactured surfaces. Fit continues to use full-part bounds.
- Select a source-supported part or group, then **Scene tools → Recorded 3D
  dimensions**. Choose one recorded guide at a time for readability. The segment,
  endpoint marks and nominal value follow that part's display displacement once.
  Source path/hash/locator are retained; the line is not measured from the screen
  or a displaced/exploded gap. Guides may remain visible across cuts and are not
  exposed-solid boundaries. Unselected/hidden parts have no guide.
- **Details → 3D geometry files** supplies the selected part's existing core GLB
  and a separate provenance JSON. Clear part selection for the registered whole
  assembly. The mesh response is checked against the registered SHA-256 before
  requesting a browser save. Files use metres and already include recorded
  assembly placement. The export is the frozen core, not optional detail,
  display separation or manufacturing CAD. Separately registered inspection STEP
  files are now listed below those GLB controls, with independent mm/source-frame
  provenance and response-byte verification. Missing solids, foreign sources,
  stale objects and mismatched identities remain unavailable.

The existing source-labelled 2D board, dimension drawings, part inspector,
experiments, replay, comparison and Analysis remain. Supported experiments use
complete recorded configurations; RP1 has no admitted full flight inertia/aero
model, so it does not acquire a flight prediction from inspection geometry.

## Source identity and detailed coverage

The [audit](source-coverage.md) and [55-record inventory](source-coverage.json)
verify the frozen inputs,26 core GLBs plus assembly,3 optional GLBs,4 joint SVGs
and cached manufacturer Eagle source.10 source-dimensioned shapes,16 envelopes,
25 allowances and4 missing geometries remain distinct. A separately bounded
[STEP export](cad-export.md) now reconstructs the26 existing records/36solids,
plus nine-record joint and full assembly. It supersedes the audit-time absence
of STEP files; manufacturing definition remains missing and no historical CAD
is substituted. More tessellation does not define a
finished knot, cap thread, PCB component height or installed joint stiffness.

An additional source-order correction associates async detail with the exact
loaded document object. New source documents with a reused ID cannot display the
previous document's meshes or guides while the next request is pending. Optional
manifest and actual asset-byte admission remain in place.

## Verification and remaining gates

All301 integrated local frontend tests pass (four preserved unrelated A2 cases
remain excluded from publication), strict TypeScript, lint, formatting and packaged
production build pass. Eighteen focused checks cover actual local GLB verification,
wrong sources/paths/queries, stale selection/document, missing geometry, section
plane signed distances/units/flip, guide source coordinates/offset-once and hidden
coverage. Generated assets are optional on hosted machines and actual-asset skips
must remain explicit. Production retains its existing large-chunk warning.

Native desktop behavior/downloads are not established by those checks. The sole
existing designated verifier owns one separately bounded substantive packet; its
actual findings and screenshots are recorded separately. No mobile or exact-pixel
campaign is required to continue capability development. P26's unqualified full
replay and P31's state-guard stop remain immutable. Engineering, build/physical,
thermal, recovery/flutter, firmware/WO-10 and flight release remain open. All five
supplier/lab inquiries remain UNSENT; no owner hardware measurement is requested.

## Native findings and one bounded visibility correction

[P34](../frontend-desktop-cut-native-20261108/browser.md) observed actual normal
RP1 section activation and150degree control/cut change. P35 observed source detail
isolation1/26, forward-ring selection/framing,31.9mm guide selection and a real
registered GLB/provenance browser download. The primary independently verified
the fresh20,000byte GLB against65d3b1e58d0f730966360b2269e2040c4ac14fb382c83e0acd2050d54150c5a5,
and the downloaded JSON's exact config/spec/geometry/part/mesh tuple.

P35 also preserved two usability failures: the open coverage popover obscured the
close-up, and the verbose guide label covered the bore. The one allowed bounded
correction (at most10minutes source effort) closes coverage after Inspect modeled
detail and makes the label compact, shifted away from the line and non-interactive.
The full source/section-cut disclosure remains in the tool text and title. P35's
manual-close/old-label evidence does not verify this corrected source; a new scoped
native observation is pending. No geometry, camera fit, source dimension or numeric
engineering result changes. Stop this correction on a new interaction regression.

## CAD and PCB additions

`make workbench-rp1-step` verifies and copies the **already completed local** STEP
packet into optional static preview assets; it never regenerates CAD. The normal
`make preview` workflow and Python/JAX backend are unchanged. Missing files or
source/hash mismatches stop preparation, and missing optional downloads report
unavailable. The current local packet has been prepared; no host restart is needed.

The existing manufacturer2D high-g board dialog now includes the four nominal
Ø2.5mm drill centres, selected placement and original-source JSON exports. It keeps
manufacturer XY distinct from vehicle datums and preserves attribution. Component
heights, incoming revision/silicon, mating tolerances and installed fit remain
unavailable. No populated3D electronics are fabricated from those2D coordinates.

## Corrected desktop native result

P36 independently observed automatic popover close, a compact31.9mm source label
above the bore, readable annulus/notch/seam, and actual part STEP/provenance export.
[The two fresh files](step-download-verification.json) match registered SHA-256
bytes. P37 observed the manufacturer2D drawing and four-hole table, selected U1
mounting JSON and Escape returning focus to Open PCB layout with source/part retained.
[Fresh board export](board-download-verification.json) matches the source schema,
mm units, four positions/diameters, selected reference and manufacturer SHA.

The initial full301-test run found a STEP copy-assertion mismatch. Two copy edits
preserved the intended CAD-mm/nose-tip/aft wording; the first exact replacement
missed its line wrapping and did not change source. Failed logs remain local.
The final integrated301-test run, build/typecheck, lint and formatting pass; no
criteria, physical quantities or checks were relaxed. Four unpublished A2 tests
stay excluded from publication. Existing large-chunk warning is retained.

Software usability findings closed: coverage no longer obscures the selected
modeled detail, and the source guide no longer covers the central bore. Source
exports and actual downloaded bytes are consistent. **No engineering/physical
requirement is closed by those UI or CAD serialization checks.** Full root behavior,
material/joint/heat/recovery/flutter, exact hardware and flight gates remain open.

## Decision-driving source gap retained

The bounded [next-detail source check](next-detail-sources.md) did not admit a
fully defined populated-board or retainer CAD asset. It also found a frozen
recovery-controller identity conflict: the learn/dimension definition proposes
Eggtimer Apogee, while engineering.function still identifies EasyMini v3.0.
No physical/source definition is silently changed. Its STEP remains a generic
unverified envelope, not detailed CAD for either device. Reconcile the exact
intended controller/revision before a detailed controller model, mount or
power-independence claim. Supplier/lab contacts remain UNSENT.

## Hosted fresh-checkout correction

PR115 first head57bdde7ae4316806f2dc3bb1722837003a20e0d1 failed its required web
Test step in workflow42563350078: source-dimension-overlay.test.mjs opened an
optional generated public manifest absent on the runner (ENOENT). Hosted summary
was294 tests,283pass,1fail,10explicit skips; typecheck/lint passed and later web
steps were skipped. This failed run is retained, not rerun unchanged or merged.

The pure guide tests now read the tracked detail-catalog.json instead. Its33,734
bytes/SHA-256b3ac3cc62294676d5614eab048bab7111320f61eecaa002a85a7d1469b6e8ac6
are identical to the prepared public manifest. A new fixture hash assertion checks
the registered source constant. All four guide tests still execute with their
known endpoints, source identity, offset, hidden/invalid and renderer assertions;
no skip or threshold relaxation was added. Actual generated-byte checks remain
separate and explicitly optional. Runtime/physical code and native results are
unchanged; a new exact-head required run must pass before merge.
