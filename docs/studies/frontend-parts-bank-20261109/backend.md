# FW2-005/006 read-only RP1 parts bank

`src/api/parts_bank.py:build(root)` now returns **55 reusable source definitions and55 installed source instances**, derived from the frozen RP1 specification, AD1 definition and saved record. `definition(root, definition_id)` accepts only an exact registered definition ID. Primary owns HTTP routing, Design integration and native verification. This packet implements no builder commands, candidate resolution, CAD or flight computation.

The source tuple remains configuration `G80-F2-RP1-AD1-definition-v2`, specification `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`, definition `e9db49f2cafc89b1f77bf9d7396434297bc8bb8754085fdcf74d3b0242012555`, record `bc349a24fe1cfaa4d883b9e00dc5b75387638a7be5cd4b05d9f32112ee8bd95b`. Whole-source drift is a failure. Inputs and executing module bytes are rechecked at the end of every build.

## Concrete contract

The schema is version1, ID `rp1-parts-bank-v1`, with `configuration_id`, exact `identity`, `revision_sha256`, `definitions[]`, `instances[]`, `summary`, `module_sources` and `capabilities:{editable:false,draft_builder:false}`. Revisions are SHA-256 of UTF-8 Python canonical JSON: sorted keys, compact separators, `ensure_ascii=False`, `allow_nan=False`, excluding the object's own `revision_sha256`. Native float serialization is Python's; naive JavaScript serialization need not produce identical hash bytes.

Each definition has ID `rp1:<original-part-id>`, its own content revision, `source_part_id`, name/type/material/function/learn, source nominal dimensions in metres, recorded group mass/basis, manufacturing description, geometry maturity/mesh status, source-budget price, provenance path/hash/locator, explicit issues, reuse status and unknown interfaces. It contains no instance placement. Missing optional numeric values remain `null`; zero is preserved only when the source actually records zero.

Each instance retains its original55-record part ID, definition ID/revision, configuration, source position/lateral offset/parent, `quantity:1`, `counting_basis:source_record` and separate `group_count`. For `fin_set`, source `geometry.count:3` is metadata: the source group mass and price are **not multiplied by three** or divided into a fictitious per-fin quote. An absent count means one accounting record; it is not a new physical-piece-count claim. Parentage supplies no inferred joint or mate.

Price is a dated source group budget, not a current unit price, purchase quote or owner stock. `current_verified:false` and `owner_stock_credit:false` are explicit. Every zero source budget has a `zero_source_budget` warning: shared stock may be charged elsewhere or cost may be unresolved. No free-parts or inventory credit follows.

Known source discrepancies remain readable unresolved issues:

- `motor_retainer`: AeroTech19002 in learn versus Estes009750 in engineering.function; cap/collar/thread/seat geometry undefined.
- `motor_tube`: current31.369/29.169mm OD/ID and165mm cut versus legacy1.210/1.140in OD/ID notes; no silent reconciliation.
- `independent_recovery`: Eggtimer Apogee proposal versus EasyMini v3.0 function; generic envelope, exact revision/mount/power unresolved.
- `high_g_accel`: manufacturer XY reference versus installed envelope; U1 ADXL343/ADXL375 discrepancy and missing populated heights/mount registration remain explicit.

Distributed allowances retain mass-allowance maturity and no solid. Missing cord/rail/shield geometry is not reconstructed from budget boxes. Source-dimensioned inspection geometry is not physical or manufacturing qualification.

## Optional geometry and prepared snapshot

The catalog uses the existing **read-only** `src.api.rp1_geometry.build` verifier for optional assets. Admission is atomic: matching sources/manifests/all assets admit26 meshes with geometry identity `238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`. Missing supplies produce `inspection_geometry_sha256:null`,55 mesh-unavailable entries, and explicit unavailable reasons while retaining all source dimensions and maturity. Existing corrupt/foreign geometry raises rather than silently degrading or borrowing another configuration.

`scripts/wo04_parts_bank_export.py` uses the same catalog function and writes only ignored `web/public/engineering-workbench/rp1-parts-bank.json`. Optional `--output` must identify that exact project path. It computes first, refuses unrelated existing files/symlinks, stages and reads back the JSON, rebuilds to recheck source/module/asset consistency, then atomically replaces the registered snapshot. Identical output is not rewritten. It never runs an asset exporter, downloads data, installs dependencies or starts/restarts a service.

The authorized local preparation completed with55 definitions/instances and26 verified meshes:

- Prepared file:218,673bytes; SHA-256 `fc2429af4139f6f432abda40887dedc10527cfbdff36e1dfa7fda1cbc2ef3c9d`.
- Catalog revision:`7508b1f4361d3bada13ad23d11f6e997cda4aa3a476d33d847898425b2367e36`.
- Backend module SHA:`5515a6adc6b62ea7d6ed8490ed832590de8cef1b52db44ae6a42611104cc48e1`.

A source-only fixture was computed from a temporary root containing **only the three frozen inputs**, using the actual executing tracked modules. It has55 definitions/instances, all geometry unavailable, and10 source-dimensioned/16 envelope/25 allowance/4 missing-geometry maturity records. The frontend owner may copy `.cache/rp1-parts-bank-source-only-fixture.json` into its authorized tracked test fixture:213,466bytes, SHA `93e0743bd8f1c7460132b13415b77425ac0a8f1ea62d98e1e871cfaa23fd85b3`, revision `bd69971e461251b843e24b4f2ec93c8d56e693bcbfa2d121697399a4510761cc`. Fresh-checkout tests must not require the ignored public snapshot. Source-only and asset-admitted catalog revisions differ honestly because their geometry availability differs.

## Completed checks and limits

Seven focused tests passed in2.63seconds: actual deterministic source/accounting/read-only behavior, source-only optional geometry and product conflicts, absent-number nulls, duplicate/group/source drift rejection, corrupt optional geometry failure, fixed-path atomic snapshot/foreign-file preservation, and module-change-during-read rejection. Full `make check` passed Ruff, Black on447 files and mypy on96 source files. The first source-only test attempt exposed the audit helper's extra source-code dependency; the correction now projects existing maturity categories without generated assets or a test-only runtime flag.

This establishes backend/source/export behavior. It does not establish live API response from an already-running process, browser navigation, drawing quality, alternative-build compatibility, installed hardware, electrical deployment, physical test or flight acceptance. All five inquiries remain UNSENT. The existing frozen vehicle, mass/inertia and engineering gates are unchanged.

## Installed-reference frame correction

Primary integration identified that current core GLBs are globally placed RP1 inspection meshes, not reusable local definition CAD. The bounded metadata correction adds `geometry.mesh_scope:installed_reference` and the admitted manifest viewer frame (`X=body+y, Y=length-station, Z=body-z`) only for available meshes; both fields are explicit null when unavailable. Every entry records `reusable_local_geometry:false` and `registered_instance_id:<source-part-id>`. No vertices, transforms, source geometry, placements or physics changed. Focused assertions cover exact frame, scope, instance linkage and false native-reuse claims; all seven tests and full repository checks passed. Both snapshots and frontend fixture supply were refreshed after final formatting.
