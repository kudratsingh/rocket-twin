# Existing-source mechanical component close-up

The single export produced **18 selectable GLB children from seven existing source records**: three fin panels, three tabs, six gusset wedges, the slotted body, motor tube, aft ring and three already-named forward-ring layers. The [compact catalog](mechanical-detail-layout.json) carries all 55 stable source IDs, parent/source identity, material/function/maturity, child IDs, actual hashes, bounds and fixed static URLs. The children let the frontend show and pick the intricate existing joint pieces individually instead of treating each compound record as one solid.

| Parent | Actual children | Source |
|---|---|---|
| `fin_set` | `panel-01`…`panel-03` | Frozen core GLB |
| `fin_tabs` | `tab-01`…`tab-03` | Frozen core GLB, corrected AD1 dimensions |
| `root_gussets` | `gusset-01`…`gusset-06` | Frozen core GLB |
| `body` | `source-01` | Existing source body with AD1-corrected slots |
| `motor_tube`, `aft_ring` | One `source-01` each | Existing optional finer annular GLBs |
| `forward_ring` | `stock_front`, `bond_reservation`, `stock_aft` | Existing named optional GLB geometries; two 6 mm stock layers / 0.2 mm visual bond reservation |

All children retain the **original viewer metre coordinates**, `X=body+y, Y=length-station, Z=body-z`. No centring, translation, scaling, new extrusion, CAD operation or physical shape change was applied. Child files are named `{parent}--{sub_id}.glb` under ignored `output/rp1-component-detail/`, with hash-verified static copies at `/engineering-workbench/rp1-component-detail/`. The catalog's core tuple remains RP1 AD1 v2/specification `811b3bed…31660`/inspection geometry `238d01e5…28b608`.

The script `scripts/wo04_rp1_mechanical_detail_export.py` reconnects only **exactly coincident vertex coordinates** to identify meaningful connected components across CAD face seams. It does not use a spatial snap tolerance. Oriented triangle-coordinate fingerprints confirm that separation retains every original triangle, including winding. The exact child union bounds equal the selected source bounds. Export/readback checks preserve each child's coordinates and oriented triangles; optional source bounds also remain within the pre-existing core-envelope comparison tolerance. All frozen source/code/GLB pins were checked again after extraction.

One actual export took **1.250 s wall / 0.928 s CPU**, within the 120 s / 90 CPU-second bounds. A metadata-only correction labels the existing middle ring layer **Unspecified bond reservation (display only)** while retaining `source_parent_material`; no GLB was regenerated. Final catalog SHA-256 is `1044bc7aeacad0802fe74add1fecbc77aeddcd0ed09f493c685bb639d271eda1`.

Adhesive allowances `fin_internal_bonds`, `outer_fin_fillets`, `ring_bonds` and `ad1_slot_fill` are **callouts only**, with no generated solids. The middle ring layer is an existing display reservation, not a qualified adhesive or new material definition. The records do not prove manufactured fin/tab continuity, contact, bond quality, installed movement, strength or flutter. Body cutaway and any exploded separation belong to the frontend display only. There are no new fin variants, dimensions, mass/inertia, physical CAD adoption or engineering/build/flight acceptance changes. Existing core assets are not overwritten; inquiries remain UNSENT.

Focused checks cover catalog/source coverage, real GLB readback and exact oriented-triangle/bounds retention, meaningful three-fin splitting without mutating the source arrays, and unchanged source hashes. These are source/asset checks, not browser visual or physical acceptance.
