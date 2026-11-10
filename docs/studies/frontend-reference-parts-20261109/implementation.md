# Local reference inspection: implementation inventory

**Current state:** The source projection, standalone metadata API and controlled datum guide have their own completed focused checks. Parent wiring now appears in `src/api/workbench_app.py` and the parts-bank template detail, but the combined-source checks pass (153Python/1benchmark skip;411published web/415local). P87 reached the ring preview and datum controls in native AX; its80s input cap stopped before datum selection, so no guide/ghost/camera or graphic acceptance follows. [Native limits](browser.md). The focused portability correction passes all 42 affected tests both normally and from a genuinely source-only temporary mirror with zero registered assets and zero skips. No CAD generation or owner cache change occurred. This document records the code seam; it is not a browser or full-builder closeout.

| Layer | Actual module | Implemented boundary |
| --- | --- | --- |
| Authored source | `configs/parts-bank/reference-local-v1.yaml`; `src/vehicle/reference_parts.py` | Projects only two exact source-nominal definitions from the frozen template manifest; verifies pinned source and four registered local STEP/GLB byte identities; reports missing cache separately; no CAD import or run |
| API | `src/api/reference_parts.py`; mounted by `src/api/workbench_app.py` | GET-only catalog and exact ID/revision detail with server-owned nominal parameters; rejects mutation, client geometry/placement fields, foreign origin and malformed request; serves metadata, not CAD bytes |
| Client admission | `web/src/parts-bank/referencePartsClient.ts`; `referenceDatumGeometry.ts` | One explicit detail GET for the exact template, strict response/source/frame/asset checks, five analytic feature IDs and local CAD-to-viewer conversion |
| Parts-bank display | `TemplateBankPanel.tsx`; `ReferenceLocalPreview.tsx`; `ReferenceDatumGuide.tsx`; `LocalTemplatePreview.tsx` in `web/src/parts-bank/` | Existing nominal template detail opens the local preview; datum buttons/clear and a single selected overlay share its Canvas; registered GLB parse and STEP download independently verify fetched bytes |

The motor tube is OD **31.369**, bore **29.169**, length **165 mm**. The plain aft ring is OD **64.4**, bore **31.9**, thickness **6 mm**. These are the two previously generated annular STEP/GLB representations; this integration does not generate another solid or vary a dimension. STEP coordinates use local front-center millimetres, +Z aft. Viewer metres map as `[cadX/1000, -cadZ/1000, cadY/1000]`, so positive CAD Z becomes negative viewer Y. The local placement is not an installed vehicle station.

Each reference has five analytic datums: axis, bore cylinder, outer cylinder, front/start annular plane and aft/end annular plane. The guide derives its lines and ring from nominal parameters. Its 96-segment circles are **display sampling**, and the +Z plane normals are a local convention. None identifies a CAD-kernel face, GLB triangle, tolerance, contact, joint, mating interface or measured fit. The UI keeps unknown installed transform, mass, cost, inertia, material/stock tolerance, strength and thermal data unavailable/null; no source estimate becomes a new charged mass or price. Add/Replace/Connect, candidate, simulation, engineering, physical and flight status remain false.

The source lane reported 14 focused pytest cases; the API lane reported 23 focused TestClient cases; the standalone frontend guide reported six Node cases. Those are **lane checks**, not the combined gate or actual live interaction. The API recognizes absent local assets as unavailable without regeneration and rejects corrupt/foreign bytes; the parent preview separately verifies the public files before rendering or download. A fresh clone may lack ignored local output assets, so tracked manifest presence alone is not a cold-start geometry promise. No cache reconstruction is part of this packet.

Next evidence is one combined source/API/web verification after root's source freeze, then one bounded designated-browser datum case. Record actual outcomes in a separate native evidence file; do not promote source assertions or the prior STEP readback to that result. Any correction stays within the demonstrated failure and its affected checks. Frozen RP1/AD1/D1, the failed performance criterion, draft source accounting, the five UNSENT inquiries and every engineering/physical/flight gate remain separate.

## Preview path

Run `make preview-dev` in the normal host terminal, then open the5173 frontend.
In Design for current RP1, open **Parts bank → Template recipes → Aft annular
ring** (or **Motor tube cut**). The local preview shows five datum choices.
Choose **Nominal bore cylinder** to ghost the display and highlight its nominal
bore; choose an end datum or **Clear datum guide** to restore the solid.
Use **Move**, **Rotate**, wheel/pinch, zoom buttons and **Fit local part** as usual.
Source/frame/limits details expand without replacing the canvas. **Download
local part STEP** still verifies the original registered bytes in local
millimetre coordinates; datum, camera and opacity settings do not enter export.
The current source conflicts and unknown physical properties remain explicit.
These instructions describe implemented controls; P87 did not execute a datum
selection or prove rendered guide legibility.
