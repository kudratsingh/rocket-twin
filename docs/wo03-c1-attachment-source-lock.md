# WO-03 C1 attachment source lock

**Status:** Frozen source identity for one preliminary C1 mass-balance case. This is a traceability record, not active configuration, design acceptance, qualification, or an as-built/purchased parts list.

## Selected case identity

- Candidate: `C1_closed_receiver_mass_balance`; selected scenario: `C1_clipped_fins_no_ballast`.
- Saved mass result: **1129.806750976539 g loaded**, comprising **1079.806750976539 g nominal plus the separate 50 g growth allowance at 1227 mm counted once**.
- Saved loaded CG: **879.797912 mm**. Saved CP: **966.827598 mm**. Saved loaded static margin: **1.318632 cal**.
- Separate scenario D remains separate: C1 clipped fins plus 20 g at 1227 mm and an illustrative +12.8 mm motor-CG probe. It is not part of selected C1.
- C1 selected fin geometry is span 90, root 120, tip 60, sweep 40, station 1080, thickness 6.35 mm. The source fin geometry was 70/120/120/0/1080/6.35 mm.
- Fin load values at q=40 kPa and alpha=5° use the existing finite-aspect-ratio formula. **8.830347836 Nm per fin and 220.758695902 N per fin already include DF3 once.** The archived CP comparison is CP-only; its placeholder mass/inertia do not validate the full vehicle.

## Attached geometry and component trace

C1 replaces three S3 C-channel staves (1010–1211.8 mm; 16.2–30.3 mm radial envelope; C section 14.1 mm radial by 19.5 mm tangential, 12 mm channel depth, 6.95 mm channel width) with a continuous G11 annulus from 1010 to 1211.8 mm, radii 31.2–32 mm, thickness 0.8 mm. Six 100×12×2 mm socket side plates, three 100×10.95×2 mm floors, six 100×2×2 mm bridges, and three 100×10.95×0.9 mm radial pads form the saved local fin socket allocation at station 1140 mm.

The saved C1 cap/end interface has a 25 g total allowance for six integral end hardpoints at stations 1024 and 1203.8 mm, plus a 12 g allowance for three forward key carriers at 1057 mm and an 8 g joint/process/hardware allocation at 1110 mm. The C1 aft service cap uses a 15.8 mm bore, 32 mm outer radius and 6 mm thickness; three separate 18.3×6.6×4 mm aft keeper arms are allocated at 1205 mm with 3 g keeper hardware. S3 cap references are 6 mm thick, 32 mm outer radius, 12 mm bore, with 9 mm radius half-cylinder saddle lobes; fore/aft cap stations 1004/1211.8 mm and barrel nut stations 1024/1203.8 mm. The fore body skirt spans 974–1004 mm at radii 31–32 mm and has strap-clearance windows at 995–1004 mm.

The S3 fin-root interface was a 6 mm source tab deepened to 14.7 mm across a 100 mm tab length, stations 1090–1190 mm, in 6.9–7.0 mm channels, with three axial pin stations at 1180 mm. The selected C1 fin panel replacement changes only the saved rectangular-panel mass rows; source fin CAD residual, gussets and S3 deeper-tab delta remain counted once.

Every retained, removed, added and selected-change ledger row carries its stable part ID and source config field, alongside the saved mass, station and basis where available. Stable part IDs, mass rows, basis descriptions and exact source-field links are in [the JSON source lock](../configs/studies/wo03-c1-attachment-source-lock.json). Its resolved ledger preserves the 50 S3 custom-component rows, removes exactly eight listed S3 rows, then applies the exact selected-C1 saved mass-change rows. All the listed masses are CAD-derived source inputs, geometric estimates or explicit allocations as identified in those rows. They are not a measured or purchased C1 bill of materials, and the proposed receiver/socket geometry is not CAD-reconciled or physically built.

## Frozen source/version identity

| Role | Path | SHA-256 |
|---|---|---|
| Selected configuration | `configs/studies/wo03-g80-mass-balance-revision.yaml` | `d76c34c69c64b9281d0e945643b95d79385393ab7d40156c7cdbc6a601f15228` |
| Selected execution record | `runs/wo03-g80-mass-balance-revision-20261102-v2/record.json` | `a22dc418ea4fdfb9d91f145180a0e1024f53d3b51b3d61d7d1c18b82fb960276` |
| Exact executed script | `runs/wo03-g80-mass-balance-revision-20261102-v2/executed-script.py` | `7584ae51560f768e7dd8eb6c5ca2ea4b30b9a3dc5a8168f7ae0a0bb024d3bfd3` |
| Exact executed config | `runs/wo03-g80-mass-balance-revision-20261102-v2/executed-config.yaml` | `d76c34c69c64b9281d0e945643b95d79385393ab7d40156c7cdbc6a601f15228` |
| Canonical formatted script | `scripts/wo03_g80_mass_balance_revision.py` | `8117e3405b2c7c5bafdf83288ecff03dab5c31a8e8bdb384f348c649709d1052` |
| Formatting provenance | `runs/wo03-g80-mass-balance-revision-20261102-v2/maintenance-formatting.json` | `7675763dbfef12dfec59522147ad285c0c3b8a1007b1fec94e9c8244033e1ff0` |
| CP comparison | `runs/wo03-g80-mass-balance-revision-20261102-v2/cp-reference.json` | `835f21ee3187b25f4c1cd4ec7f9069ea3001a4b8b7abc48ee6348f1f16cbf740` |
| S3 mass ledger source | `runs/wo03-g80-connected-receiver-20261102-v2/record.json` | `0686d2f4603847c12e12a4e0aceb81f18e3c9993c36650a8a8dacd5fdeb456c7` |
| S3 dimension source | `configs/studies/wo03-g80-connected-receiver.yaml` | `14f7b125dc4b32e0a1bde0b115d24f22d17f852c090348d0bf8306b372998a78` |
| Source 73 specification | `runs/wo03-g80-canopy-stage3-20261101-v1/sensitivity.yaml` | `6962dda2e123ac3528f75136f62b065d742e917712fc2dcef2dfc0a40a675967` |

The maintenance record states that the canonical script differs from the executed source by Black whitespace formatting only (`python_AST_equal: true`); the saved numerical record hash remained unchanged. This source lock points to the exact executed script and config separately. The mass-balance packet was not rerun for this freeze.

## Boundary

This lock records preliminary mass, CG and CP identities and their source rows. It does not accept C1, establish physical fit, qualify a joint or material, establish motor/thermal/recovery/fin performance, or change active specifications. Full evidence limits are recorded in the JSON `evidence_boundary` and execution record.
