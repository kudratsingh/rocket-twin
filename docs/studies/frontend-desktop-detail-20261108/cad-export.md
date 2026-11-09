# RP1 inspection STEP export

The single bounded packet exported and read back **all 26 existing mesh-bearing source records**, plus a nine-record motor/fin/ring joint and a full inspection assembly. The 26 records contain **36 solids**; they are not 26 manufactured parts. Runtime was **9.866 s worker wall / 5.522 s worker CPU**, or **10.187 s parent wall**, within the 120 s wall / 60 s CPU limits. Cost was **$0**; no dependencies were installed, no retry occurred and no source geometry changed.

This is an **inspection CAD reconstruction from the fixed nominal definition**. It introduces no threads, roundovers, cord topology, bond geometry, new physical design, mass/inertia or manufacturing release. It supersedes the earlier [source audit](source-coverage.md) statement that matching RP1 STEP artifacts were absent: the new STEP representation is now locally available, while its missing physical definition remains missing.

## Available files and identity

The [tracked evidence](cad-export.json) contains exact source hashes, all 55 stable records and their maturity/material/dimensions, 26 individual STEP hashes and checks, both assembly hashes and checks, tool versions, runtime and limitations. Generated files remain under ignored `output/rp1-inspection-step/`; no bulk CAD output is proposed for a commit.

| Export | Coverage | Bytes | SHA-256 |
|---|---|---:|---|
| `critical_motor_fin_ring_joint.step` | Nine records / 18 solids: motor tube, forward/aft rings, fin panels/tabs/gussets, body, motor and retainer envelopes | 339,487 | `2ea1796f0b506ce382e1f7f9d25280b21c2f30d2119bb3aa52f257c0e2cff119` |
| `rp1_ad1_v2_inspection_26_records.step` | All 26 represented records / 36 solids | 1,022,462 | `4af4940429dec381445f939d762edb1359881c5d61a8658c93a90308c34125c3` |
| `parts/{stable_id}.step` | One source record per file; compound records retain their multiple solids | See manifest | See manifest |

All 28 STEP files total 2,376,007 bytes. Assembly child/product labels retain stable IDs; source maturity and material stay explicit in the manifest. The 10 source-dimensioned records remain nominal estimates, the 16 envelope records remain envelopes, and the 25 allowances plus four missing-geometry records have no fabricated STEP solid. Forward-ring proposed 2 mm edge roundovers, retainer cap/thread/seat details, rope/knots, installed bond/contact geometry and unknown electronics internals remain absent. FP1/FR1 and historical G80/G54/G12 CAD remain separate.

Configuration is `G80-F2-RP1-AD1-definition-v2`, specification SHA-256 `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`, core inspection geometry SHA-256 `238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`. Export script SHA-256 is `63edd7cd49b0b68b9c51fc0c7aa0eedf4b6dab874e78b4398fee109cc451b972`. All seven frozen core inputs, core GLB hashes and saved/output manifest identity were verified before and after the packet. No core GLB, historical STEP, physical ledger or source YAML was overwritten.

## Frame and validation

STEP coordinates are **millimetres**, with origin at the nose tip: CAD X = body +y, CAD Y = body −z, CAD Z = station aft from nose. Each existing `_local(raw, definition, originals)` shape receives exactly the original placement `[lateral[0], −lateral[1], station] × 1000`. These are assembled source coordinates, without exploded-display transforms or print-bed packing.

The mapping to frozen GLB viewer metres is `[cadX/1000, length_m − cadZ/1000, cadY/1000]`. The packet compares mapped CAD bounds against the actual hash-verified core GLB vertices. The declared threshold is strictly less than 0.2 mm, reflecting a representation comparison with the existing 0.15 mm tessellation settings; it is **not an engineering fit tolerance**. Maximum observed difference was **0.00005723 mm**.

CadQuery 2.8.0 read every STEP back as valid geometry in millimetres, preserving each record/assembly's solid count and finite bounds. Maximum readback bounds difference from the exact generated source shape was **0.00000000001733 mm**, below the 0.00001 mm serialization check. A subsequent static byte/hash check confirmed all file hashes, `SI_UNIT(.MILLI.,.METRE.)` declarations and expected stable-ID product labels. No interference, assembly clearance, contact, strength, thermal, mass/inertia or manufactured-dimension acceptance is inferred from these checks. No visual/browser inspection was performed.

## Next integration route

Primary can add an explicit **Download inspection STEP** action beside the source GLB/provenance actions. A new read-only allowlisted route could serve `parts/{part_id}.step` and the two named assemblies only after checking active configuration, specification/core geometry tuple, immutable export manifest linkage and the requested STEP hash. Suggested shape: `/api/design/{configuration}/inspection-step/{part_id}?spec=…&geometry=…&step=…`. This route is proposed, not implemented or live evidence. Return the matching provenance JSON and label it inspection CAD; meshless records remain unavailable. Do not substitute the historical generic STEP route or promote this packet to canonical CAD/inertia.

The source script is `scripts/wo04_rp1_inspection_step.py`. Its existing output directory prevents a repeat or overwrite; the completed execution was `.venv/bin/python scripts/wo04_rp1_inspection_step.py --execute`. A worker enforces a 60 s CPU hard limit and a parent subprocess enforces 120 s wall time, with earlier cooperative reserve checks. The successful packet is closed; no new attempt follows automatically.

Engineering/build, thermal/recovery/flutter, WO-10 and flight gates remain open. All five inquiries remain UNSENT. G54 and G12 PID-to-RL remain unchanged separate tracks.
