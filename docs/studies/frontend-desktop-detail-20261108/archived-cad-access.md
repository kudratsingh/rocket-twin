# Archived configuration CAD access

**A bounded download extension is viable without new CAD or a backend restart.** All four explicit canonical API catalog configurations have source-matching local part GLB/STEP/STL files and assembly GLB/STEP files. The [audit registry](archived-cad-access.json) records the exact configuration, resolved-spec/CAD/part-shape identities, manifest SHA-256, current source pins and every asset byte hash. No files were generated, copied to public storage or borrowed between configurations.

The audit resolved source definitions and checked file identity only; it did not construct API snapshots, run mass/aero/flight calculations, import CAD, execute a solver or inspect the browser. File hashing covers **572 assets / 54,892,740 bytes** across **188 source part records**.

| Catalog configuration | Actual source path | Parts | Existing part files | Existing assembly files | Retained status |
|---|---|---:|---|---|---|
| `modular-performance-v1` | `configs/vehicle/platform/performance.yaml` | 42 | 42 GLB + 42 STEP + 42 STL | GLB + STEP | Archived modular G80 reference/replay fixture; preliminary, engineering acceptance open |
| `modular-performance-g54-hypothesis` | `configs/vehicle/wo02/performance-g54.yaml` | 42 | 42 GLB + 42 STEP + 42 STL | GLB + STEP | Conditional G54 upgrade; thermal/motor-CG findings open |
| `modular-tvc-finned-v1` | `configs/vehicle/platform/tvc-finned.yaml` | 53 | 53 GLB + 53 STEP + 53 STL | GLB + STEP | Preliminary G12 trainer; recovery/guide budget unresolved |
| `modular-tvc-finless-v1` | `configs/vehicle/platform/tvc-finless.yaml` | 51 | 51 GLB + 51 STEP + 51 STL | GLB + STEP | Eventual G12 concept; negative passive stability/control gates open |

All four recorded manifests match the currently resolved specification, CAD revision and complete per-part shape map. The shared CAD revision is `1193713d0f4a7ad8393a00a0a03e7aaa04e9aa9393d2034691ef7126ae3cdd3b`. Each manifest is separate; identical-looking common parts do not authorize cross-configuration substitution. The separately aliased 72-part retention candidate is outside this four-configuration audit.

## Existing contract and the missing download layer

`src/api/app.py` defines the catalog and source/asset admission. Its identity has `configuration_id`, `resolved_spec_sha256`, `cad_revision_sha256` and `part_shape_sha256`. Source inputs include the mode/shared YAML, motor curve/sidecar and relevant backend files. For each part, the current document exposes `source.shape_sha256`, source inputs and `representation.role`; it does not use RP1's optional `inspection_shape_sha256` field.

The existing mesh index route `/api/vehicles/{configuration_id}/meshes` supplies the exact identity and startup-captured per-part GLB byte hashes. The part route `/api/vehicles/{configuration_id}/meshes/{part_id}.glb` checks current source/CAD/manifest identity and response bytes against that captured hash. A bare mesh URL alone is not a registered download identity. The current frontend geometry-access helper deliberately admits only RP1, explaining the unavailable download action on these other rendered models.

No canonical STEP/STL or assembly-file download route is implemented. Adding a route would require a later backend update/restart; a fixed static preparation step can expose the already-existing bytes without that dependency. This is source-contract evidence, not verification of a particular running host.

The legacy manifests record semantic shape hashes and explicit part filenames, **not original per-asset GLB/STEP/STL or assembly byte hashes**. This audit separately pins the current local files. It establishes a frozen byte registry for delivery; it does not newly prove their geometry by STEP readback. A future preparer must verify both the source/manifest tuple and these byte pins before copying.

## Frames must remain distinct

| Format | Actual exporter contract | Required download label |
|---|---|---|
| Part GLB | Source part already placed in assembly, then mapped to viewer metres: `[cadX/1000, length_m − cadZ/1000, cadY/1000]` | Recorded assembled inspection mesh, metres |
| Assembly GLB | Same world-placed viewer metre frame | Recorded whole inspection mesh, metres |
| **Part STEP** | `src/cad/assembly.py` exports the original **local part shape before placement**, in millimetres | Source part CAD, local coordinates; its origin is generator-local rather than the vehicle nose |
| Assembly STEP | Compound of placed source shapes; CAD millimetres with station +Z aft from nose | Recorded assembled CAD, millimetres |
| Part STL | Part-local shape, or print-oriented/bed-packed shape where the row's `print_layout` records transforms | Local/print representation, millimetres; not installed placement or a fabrication approval |
| Assembly STL | **Not exported / absent for all four** | Unavailable |

This differs from the new RP1 part STEP packet, which deliberately retains vehicle assembly placement. Reusing RP1's coordinate wording for these legacy files would mislabel them. Each audited part row records the actual print-layout data and frame disposition.

## One bounded viable extension

Create a small fixed registry/preparer for these four IDs, with allowlisted per-part filenames, assembly GLB/STEP filenames and immutable provenance JSON. Use the audited hashes under a dedicated ignored static prefix such as `/engineering-workbench/archived-cad/{configuration_id}/`; this is a proposed prefix, not an implemented or fetched URL. Before copying, require matching current resolved specification/CAD/part-shape identities, source pins, manifest hash and asset bytes. Serve only the registered set, with no arbitrary file/URL argument or generation fallback.

Then extend desktop Details with **selected/whole archived GLB and part/assembly STEP**, checking the current document tuple, complete stable-ID inventory, exact current selected object, `source.shape_sha256` and representation role. Verify downloaded bytes before saving and return matching provenance. Existing part GLB routes can also be reused if the mesh index/document match the frozen registry and the response matches its audited SHA-256. Keep STL separately labelled as local/print geometry or defer it from the first increment; assembly STL remains unavailable.

Preserve manufactured-intent solids, purchased envelopes, soft stowage and distributed budgets as their recorded roles. The source role `manufactured` denotes model intent, not that an owner built or qualified the part. Some legacy allowance/stowage records have representative solids; their presence does not upgrade their definition to installed hardware. Source code naming an STL or reporting a local print-volume screen does not authorize printing.

The audit rechecked all 572 byte hashes, source/CAD pins and format headers or lengths: GLB v2/header length, STEP ISO header/millimetre declarations and binary STL triangle-count length. No STEP/CAD readback, new analysis, network, browser, install, public copy or physical work occurred. All four designs retain their recorded open/conditional status; nothing clears RP1/AD1/D1, stopped construction findings, engineering/build/flight gates or the separate G54/G12 development requirements.
