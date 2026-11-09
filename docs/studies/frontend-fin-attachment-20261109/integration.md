# RP1 fin attachment inspector

Current scope is the frozen G80 RP1 / AD1 v2 inspection definition, not a new fin
construction. Nine registered part records / 18 original CAD solids are presented
in assembled coordinates. Motor and retainer are simplified envelopes; undefined
adhesive is an annotated relationship. No supplier threads, adhesive bead shape,
installed stiffness, thermal field or acceptable strength is invented.

## Preparation and preview

```sh
cd /Users/kudratsingh/Machine-Learning-Projects/rocket-twin
make workbench-rp1-fin-attachment
make preview
```

Open http://127.0.0.1:5173/ . Port8000 is the Python API, not the frontend.
The preparation command verifies/copies the existing registered joint STEP and
derived section meshes. It needs the original local STEP supply; it does not
rerun the closed STEP exporter or alter the frozen vehicle. Missing/changed
supplies fail explicitly. No dependency installation or physics run is required.

## User path

1. Choose G80 RP1 / AD1 v2 in Design; select Fin tabs (`fin_tabs`) or Fin set.
2. Choose **Inspect fin attachment**. The large view has its own orbit/pan/zoom,
   Fit joint / Fit selected, Rotate drag / Move view and separate Parts / Evidence sidebar toggles.
3. Choose **Longitudinal through fin**, then **Transverse at slot**. Amber surfaces and edges
   are actual CAD-derived material intersections, not a flat sheet over empty
   bores. A plane marker explains each cut; Assembled restores the full solids.
4. Select a dimension in3D or the keyboard-accessible list. Values are source
   nominal6mm, slot6.80±0.05mm, and **calculated nominal0.40mm** tab/ring gap.
   Recorded tolerance is not proof of manufactured fit.
5. Open Root drawing or Load path drawing. Matching configuration, part and
   revision travel with the link. Use **Return to fin attachment** to recover
   the same section, dimension, selection and locally saved camera.
6. Choose **Download joint STEP**, optionally download its provenance. The
   registered file is always the full assembled9-record joint, millimetres,
   regardless of visible parts, section, camera or isolation.
7. Choose **Return to rocket**. The implementation preserves the original whole-rocket
   selection and actual camera pose (P68 settled browser verification passes); a joint inspection does not change the vehicle.

## Evidence and limits

[CAD derivation and numerical representation checks](cad.md),
[route contract](navigation.md), [bounded scope](plan.md), and
[browser readiness](browser-readiness.md) separate their evidence scopes.
[Actual browser observations](browser.md) preserve P64, P65 and P66 separately.
P64 verified both CAD cuts, source dimensions, sidebar controls and isolation.
P65 verified separated labels, actual orbit/zoom, the root-drawing round trip and
Chrome's STEP Done receipt. P66 verified explicit Move-view translation but its
load-path navigation ended in a native-runtime timeout/kernel reset. A subsequent
supported readiness call found another CAD site active; no input was sent there.

The [actual Downloads STEP readback](download-readback.json) matches the registered
339,487 bytes/hash, millimetres and18 valid solids, including6mm tab thickness,
109.4mm tab length and0.40000000000009mm nominal aft gap. Slot6.80±0.05mm remains
source-defined, not an independently extracted or manufactured tolerance.
[Actual downloaded provenance](download-provenance.json) matches its registered
hash. The readback tool does not assert browser origin; P65 supplies that receipt.

P65's immediate return-camera mismatch was followed by a decisive P67 failure:
the entire Design frame remounted during the Engineering round trip. Both
records remain historical evidence. The final correction keeps the actual
source-bound Design frame, layout provider, renderer and controls mounted
(hidden and inert while the exact joint Engineering view is active), rather
than trying to recreate a lost camera from a transient cache. Ordinary
Engineering, Analysis, Experiments, Replay and other-source routes are unchanged.

**P68 passes the scoped final return journey.** A fresh custom baseline
H−29.7° / T44.1° / R0°, Rotate mode, exactfin_tabs/spec selection survives
Design → joint → load-path Engineering → joint → actual Return-to-rocket.
A later capture21.738seconds after Return matches the original visible rocket
projection, position and scale. The joint's transverse section, selected piece
and0.40mm nominal-gap dimension also survive. P67 separately verified the
drag-release guard keepsfin_tabs selected during Move view.

The matching load-path image is auto-open in nativeAX and its route/return is
verified. Full lower-drawing pixel-legibility coverage is not newly claimed.
P67's unnecessary disclosure toggle is a preserved verifier branch issue, not
a drawing-opening defect. No numeric camera-vector dump,26-mesh live count,
frame-rate benchmark or complete responsive matrix is inferred.

Browser verification for this slice is finished and the designated Chrome
window is free. No immediate owner input is needed.

The failed frozen fin calculation remains visible alongside unknown installed
root movement, adhesive peel, hot/conditioned material capacity and flutter.
WO-03, full WO-04/05, prototype-build, thermal/recovery and flight gates remain
open. Five supplier/lab inquiries remain UNSENT.

## Checks, publication and remaining acceptance

PR [121](https://github.com/kudratsingh/rocket-twin/pull/121) is the single focused
publication. Initial headb07229839b7474df8701264fad036c0297b9bf7c passed the hosted
web job; final-source checks are reported in the publication receipt. Local final
web checks347cases pass, including four preserved unpublished A2 cases (343 in
publication scope); typecheck/lint/build/format pass. Python makecheck and nine
focused CAD/readback tests pass. The existing Make preparation command verifies
29 STEP/provenance files and40 derived GLBs without a new CAD run. These support
software/representation claims only.

[Scoped acceptance](slice-acceptance.csv) maps this slice to FW2-A07/A10–A14.
The broader rows stay partial: nine source records and STEP-only scope do not
close all component detail, all formats, all force paths or full frontend phases.
[Corrected longitudinal browser image](../../../output/frontend-fin-attachment-20261109/P65-longitudinal.jpg)
and the P64 transverse-ready image are local artifacts; see browser.md for their
actual filenames, source hashes and observation limits. Generated mesh/STEP and
screenshot bulk is excluded from Git.

## Owner visual target preserved

The separately supplied25-image reference set is saved unchanged in the
[local gallery](../../../output/frontend-reference-set-20261109/index.html),
with [versioned goals/manifest](../../frontend-design-workbench-v2/reference-set-20261109.md).
FW2-020/FW2-A15 now explicitly require a source-linked physics, guidance and
PID/RL system map. These references set presentation/detail goals; they do not
adopt pictured motors, controllers, airbrakes or structural hardware into RP1.
