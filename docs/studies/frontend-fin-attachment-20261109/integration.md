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
   Fit joint / Fit selected and separate Parts / Evidence sidebar toggles.
3. Choose **Longitudinal cut**, then **Transverse cut**. Amber surfaces and edges
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
7. Choose **Return to rocket**. Original whole-rocket selection and actual
   camera pose are restored; a joint inspection does not change the vehicle.

## Evidence and limits

[CAD derivation and numerical representation checks](cad.md),
[route contract](navigation.md), [bounded scope](plan.md), and
[browser readiness](browser-readiness.md) separate their evidence scopes.
Native journey observations and actual downloaded-file readback will be added
after execution. Code/source success alone does not establish those observations.

The failed frozen fin calculation remains visible alongside unknown installed
root movement, adhesive peel, hot/conditioned material capacity and flutter.
WO-03, full WO-04/05, prototype-build, thermal/recovery and flight gates remain
open. Five supplier/lab inquiries remain UNSENT.
