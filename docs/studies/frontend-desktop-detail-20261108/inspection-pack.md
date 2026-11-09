# Local desktop inspection pack

The existing RP1 inspection assets now form one **local folder and ZIP**, with a linked file index and plain README. This makes the verified CAD, meshes, drawings and source coverage usable together in ordinary CAD/3D viewers without locating individual repository outputs. The index links files; it does not embed a renderer or claim visual/browser acceptance.

- Folder: `output/rp1-desktop-inspection-pack/`
- Start: `output/rp1-desktop-inspection-pack/index.html` or `README.md`
- ZIP: `output/rp1-desktop-inspection-pack.zip`
- ZIP size: **967,408 bytes**, containing **66 files**
- ZIP SHA-256: `b02b6568e80a001c75b5f9e13f754f12c9c05281f0f1594cf87364de67d15d81`
- Package manifest SHA-256: `9df1bdd9fbf8d9ac63046f7b906806077e37626bbe6204ee3c95391fde124f53`

The [tracked evidence](inspection-pack.json) records every file hash, archive identity, original source pins and completed integrity checks. Bulk outputs stay ignored and local; no ZIP/public copy or generated-asset commit is made.

## Included files

| Directory | Actual content |
|---|---|
| `glb/` | All 26 core part meshes under stable IDs, plus the original assembly GLB |
| `step/` | All 26 reconstructed source part STEP files, the nine-record critical motor/fin/ring joint and full 26-record assembly |
| `drawings/` | Four exact saved AD1 SVGs: local attachment, load paths, test article and coupled cases |
| `metadata/` | Unchanged core geometry, completed STEP execution, source-coverage and joint-connection JSON; copied read-only |
| Root | Plain README, linked HTML file index and per-file SHA-256 manifest |

The highest-value starting files are `step/critical_motor_fin_ring_joint.step` (**nine records / 18 solids**), `step/rp1_ad1_v2_inspection_26_records.step` (**26 records / 36 solids**) and `glb/assembly.glb`. The index lists all **55 stable source IDs**, including the 29 records without solids. No private history, broad study collection, optional finer meshes or unrelated source assets enter the ZIP.

## Coordinates and engineering meaning

STEP uses **CAD millimetres**, origin at nose tip: X = body +y, Y = body −z, Z = station aft from nose. GLB uses **metres** in the existing viewer frame:

`viewer = [cadX/1000, length_m − cadZ/1000, cadY/1000]`

GLB +Y points toward the nose; STEP +Z points aft. The pack keeps original assembled source placements. It applies no display explode, camera transform, printing layout or silent scale correction.

Coverage remains **10 source-dimensioned nominal shapes, 16 envelopes, 25 allowances and four missing geometries**. The 29 meshless records remain metadata rather than invented solids. Inspection reconstruction does not define retainer threads/seat/closures, finished cord/knots, ring edge roundovers, unknown electronics internals, installed bonds or guide hardware.

Frozen AD1's saved wood-fin component screen fails. FR1 fails evaluated finite movement/body-bond screens; FP1's nominal movement depends on an unverified attachment input and fails material sensitivities. FP1/FR1 remain unadopted studies and are not replacement assemblies in this package. D1's retained load/attachment decision and source/whole-root evidence requirements remain unchanged. This is **not a manufacturing, build or flight pack**. Physical/build, thermal/recovery/flutter, WO-10 and flight-release gates remain open; all five inquiries stay UNSENT. G54 and G12 PID-to-RL remain separate tracks.

## Completed delivery checks

`scripts/wo04_rp1_inspection_pack.py` ran once, packaging existing bytes in **0.143 s wall / 0.137 s CPU**, costing **$0**. It verified all registered metadata, frozen source/code inputs and included GLB/STEP/SVG assets before copying and again after ZIP validation. It checked copied bytes, exact ZIP entry inventory, every decompressed entry SHA-256 and ZIP CRCs. Stable paths and fixed ZIP timestamps preserve an inspectable deterministic archive layout. Existing output/report paths prevent an automatic repeat or overwrite.

No CAD generation/export, solver, package installation, source geometry change, backend/UI change or browser action occurred. These checks establish file-delivery integrity; STEP readback/source comparisons remain those of the separately preserved [CAD export packet](cad-export.md).
