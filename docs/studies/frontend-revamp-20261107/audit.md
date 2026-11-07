# Frontend revamp asset and source audit — 2026-11-07

Local file baseline only; no CAD, simulation, rendering, network, browser, or telemetry reread. No current remote revision is established. Source details and exact hashes: [asset-source-audit.json](asset-source-audit.json).

| Configuration | Saved manifest | Listed / present / actual GLB | Total bytes |
| --- | --- | ---: | ---: |
| `modular-performance-v1` | `build/modular-performance-v1/manifest.json` | 42 / 42 / 42 | 1,554,284 |
| `modular-performance-g54-hypothesis` | `build/modular-performance-g54-hypothesis/manifest.json` | 42 / 42 / 42 | 1,554,284 |
| `modular-tvc-finned-v1` | `build/modular-tvc-finned-v1/manifest.json` | 53 / 53 / 54 | 1,968,504 |
| `modular-tvc-finless-v1` | `build/modular-tvc-finless-v1/manifest.json` | 51 / 51 / 52 | 1,955,808 |

The G12 directories each include an extra unlisted `retention.glb`; the kit counts correspond to listed coverage, not all files physically present. All four manifest hashes match the kit inventory; saved November 3 readiness reports matching source identities and listed coverage. Current stat counts are not runtime/API verification. The manifests lack original expected GLB byte digests; selected current byte hashes are fingerprints, not original-export attestation.

## Design fixtures

Use the separate older `modular-performance-v1` reference with exact source and CAD identities in JSON, never as current RP1/F2 CAD. Recorded part IDs are `nose_cone`, `body_upper`, `fin_set`, `motor`, `recovery_bulkhead` (internal disc), `joint_stop` (ring-like interface), `recovery_mount_hardware_allowance` and `baro`. The minimum product of saved bounding-box dimensions is `recovery_mount_hardware_allowance`, 2 × 2 × 85 mm; `baro`, 12 × 3 × 15 mm, is a compact additional scale test. Saved envelopes are not measured transformed mesh bounds. Traverse nested visible meshes with their world transforms and fit against the final canvas; actual interaction and geometry clearance remain unverified.

## Source boundaries and replay

The prepared RP1 study packet names frozen AD1 and separate unadopted FP1/FR1 screens; VP1 is an unperformed review of conceptual parts and unsent drafts. No complete RP1/F2 vehicle CAD or Design/replay registration is established by the saved readiness record. Exact source and packet hashes are in JSON.

Saved diagnostic `exp-cf9e47a650074144856caf50775846d2` binds an older G80 reference and recorded data hashes. At T+11.15 s it reports +5.456039 m/s NED-down velocity while the nose is 4.076303° from up. The simplified recovery model does not model suspended-body attitude; this fact alone does not establish a renderer defect. No telemetry was re-read here.

The kit verification report covers packaging and offline checks, not live application acceptance. The saved snapshot records no local Git identity; current main and hosted checks require independent verification. Browser interaction, all 37 revamp criteria, engineering and flight acceptance remain open.

Read/hash audit timing: 0.015 s CPU, 0.065 s wall; limits 10 s CPU and 20 s wall.
