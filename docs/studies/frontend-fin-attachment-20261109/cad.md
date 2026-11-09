# Fin attachment: registered CAD assembly and true half-sections

The new packet supplies **nine existing source parts**, their assembled inspection meshes, two true CAD half-section choices, actual planar cut-face meshes/edges, and three source-dimension guides. It imports the already registered STEP files; it does not rerun the closed RP1 STEP exporter or reconstruct the physical vehicle. The [tracked catalog](geometry.json) is the frontend contract and asset byte registry.

The packet covers `motor_tube`, `forward_ring`, `aft_ring`, `fin_set`, `fin_tabs`, `root_gussets`, `body`, `motor` and `motor_retainer`. These are the **same nine parts /18 source solids** in the downloadable registered `critical_motor_fin_ring_joint.step`; the assembled view does not substitute the optional three-layer forward-ring display asset. `motor` and `motor_retainer` retain their nominal-envelope maturity and undefined supplier mating details. Fin panels/tabs and six gussets retain their original parent records and source placements.

## Sources, datums and scope

- Configuration: `G80-F2-RP1-AD1-definition-v2`.
- Frozen specification: `configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml`, SHA `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`.
- Attachment definition: `configs/studies/rp1-attachment-definition-v2.yaml`, SHA `e9db49f2cafc89b1f77bf9d7396434297bc8bb8754085fdcf74d3b0242012555`.
- Frozen inspection geometry: `238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`; all55 source IDs remain recorded.
- Registered STEP evidence: `docs/studies/frontend-desktop-detail-20261108/cad-export.json`, SHA `a7af1fadc431dea8958a212e2a552cf2ee833b068dbeaf51dc151d6d7fbbf731`. All original input/code/core pins and nine part STEP/core-GLB hashes are checked before and after the execution.
- Whole joint:339,487bytes, SHA `2ea1796f0b506ce382e1f7f9d25280b21c2f30d2119bb3aa52f257c0e2cff119`. Download reuses `/engineering-workbench/rp1-step/critical_motor_fin_ring_joint.step` and the original `provenance.json`; the existing STEP preparer supplies those bytes without regeneration.

STEP coordinates are globally placed CAD **millimetres**, with Z increasing aft from the nose. GLBs/guide endpoints use globally placed viewer **metres**: `[CADx/1000, 1.25−CADz/1000, CADy/1000]`. No recentering or placement transform is applied again. These are installed-reference inspection representations, not reusable local product CAD. The source body extends from458 to1220mm; `focus_bounds_m` is only a camera suggestion around the known mount/fin region, not a cropped source body or a new physical boundary.

## Real retained solids and cut faces

| View | CAD half-space | Viewer half-space | Expected source behavior |
|---|---|---|---|
| Assembled | No cut | No cut | All nine original registered part shapes |
| Longitudinal | Keep **Y≥0**, plane through first fin/tab | Keep **Z≥0** | True half-solids expose the first panel/tab and tube/ring/body walls. Entire disconnected gussets can survive without being cut. |
| Transverse | Keep **Z≥1134.9mm**, aft half at tab midpoint | Keep **Y≤0.1151m** | Caps expose tube bore, slotted body and source fin/tab/gusset section. Forward ring1060–1072.2mm is outside this half and explicitly has no solid/cap. Aft ring/retainer can remain whole. |

The tab occupies1080.2–1189.6mm, so its source midpoint is exactly1134.9mm. Each retained shape is a BRep intersection with a half-space box extending beyond source bounds. A complementary intersection verifies that the two geometric volumes partition the original within `max(1e-5mm³, source_volume×1e-7)`. Validity, closed shells, bounds and planar intersection faces are checked. Volume is a representation diagnostic only; no physical mass or inertia is calculated.

Section GLBs **include the actual BRep caps**. Separate `cap_url` assets duplicate only those same planar faces for highlight/picking; a viewer overlay may use display depth bias, without changing geometry. Boundary polylines come from the cap faces' BRep edges, sampled with0.15mm deflection. Annular holes and slot voids remain holes, rather than opaque disks over a shader clip. A source piece lying entirely outside the retained side has `null` asset and an explicit reason; a whole surviving piece has no invented cap.

## Three dimension guides

| ID | Recorded value | Source locator and meaning |
|---|---|---|
|`tab-thickness`|6mm|Specification `parts[id=fin_set].geometry.thickness_m`; source nominal first-fin/tab thickness, not an incoming measurement.|
|`slot-width`|6.80±0.05mm|AD1 `fin_joints.external_slot_width_mm` and `slot_cut_tolerance_mm`; corrected source cut proposal, not a supplier tolerance or measured clearance.|
|`aft-gap`|0.40mm|1190mm aft-ring front minus1189.6mm tab end; computed nominal station difference. No direct butt support or installed clearance qualification.|

The catalog provides two viewer endpoints for each segment, exact source hash/locator, feature IDs, basis and nullable tolerance. Dimension segment length agrees with the recorded value. Undefined `fin_internal_bonds`, `outer_fin_fillets`, `ring_bonds` and `ad1_slot_fill` remain relationship callouts, without adhesive solids or inferred load sharing. No new roundovers, fasteners, retainer threads/seat, cord knots or contact geometry are supplied.

## One completed execution and checked supply

The declared bound was one worker, **120wall/90CPU seconds**, with9×3 representation slots plus cap data and one known-box method check. One execution completed: **4.8068wall /4.9347CPU seconds, $0**. It produced26 nonempty part representations and14 cap assets: **40 GLBs /323,420bytes**. The one empty slot is the transverse forward ring. The box check verifies complementary240mm³ halves of a480mm³ box and the expected planar cap areas. Registered whole-joint STEP readback verifies18 valid solids, bounds and summed part geometric volume.

- Catalog:118,309bytes, SHA `046cf7aac77cdd53882a6577f7585c44532068e23cef467126434adbd38e442c`.
- Geometry revision: `1b81037624a4a6bd59c5d2b89b053b598d1dffae56e94140d6f899d7d6506c42`.
- Frozen new exporter SHA: `24bfbb672b02ff88c191499c144535d6099a37c52e198f152ba54c0139d94dcd`.
- Ignored asset cache: `.cache/rp1-fin-attachment/`; fixed public prefix `/engineering-workbench/rp1-fin-attachment/`. Bulk is excluded from publication.

`scripts/wo04_fin_attachment_export.py --export` records the initial packet and refuses an existing catalog/cache. That initial export is now closed. `--prepare` verifies source/catalog/asset hashes, copies only registered derived GLB/cap files, and preserves unrelated destination files. Existing valid public assets take a fast verification path. If the derived cache is absent, a bounded worker may reproduce only the exact recorded bytes from matching existing registered STEP supplies; any mismatch stops without changing the catalog. It does not invoke the old exporter or generate missing parent/core STEP files. Prepare the original verified STEP download supply separately before exposing downloads.

Six focused tests passed in6.09seconds: exact nine-source admission/dimensions/revision, known-box half-sections and mapping, actual annular-cap area preserving the motor-tube bore, all40 asset byte/bounds/cap-plane/edge checks, temporary verified preparation/repeat/unrelated-file preservation, and foreign-asset/download/source-drift rejection. Owned files pass Ruff and Black. The initial full repository check passed Ruff but stopped on formatting of the primary-owned STEP preparer being integrated concurrently; no unrelated file was edited to resolve it. Integrated checks/native evidence are primary-owned and recorded separately.

No public copy or browser observation was performed by this lane. Geometry/section/source checks do not establish joint capacity, installed fit, thermal or recovery behavior, manufacturing readiness or flight permission. Frozen physical sources, canonical mass/inertia, D1 and all existing engineering/build/flight gates remain unchanged; all five inquiries remain UNSENT.

After these lane checks, primary reported successful preparation of all40 registered GLBs into the fixed public prefix. No additional copy or CAD run was performed by this lane. Actual browser download/readback and integrated interaction acceptance remain separately owned by primary and the designated verifier.
