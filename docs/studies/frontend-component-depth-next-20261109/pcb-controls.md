# PCB inspection handoff for the full revamp plan

## Existing source and delivered view

The current high-g accelerometer manufacturer reference is the pinned Adafruit PID 5374 Eagle board in `../frontend-component-depth-20261108/high-g-pcb-layout.json`. It records a 25.4 × 17.78 mm source XY board, four mounting holes, 26 placements, 82 pads, 208 routed trace segments, 26 via drill locations, 14 nets, silk and documentation layers. The 3D layer viewer uses the existing React Three scene and preserves the exact RP1 configuration/specification/part gate. It renders planar source layers; layer spread is explicitly display spacing. The original P56 native graphic failure and subsequent P57 native correction are separate evidence and must remain recorded as such.

Before this planning handoff, the viewer already offered orbit, pan, fit, top/bottom camera views, zoom, independent top/bottom/silk/documentation visibility, placement selection by list/pad, and net highlight by list/trace/via. Camera orientation buttons do **not** change layer visibility. Source XY is manufacturer board space, not a vehicle installation datum.

## Code-only work interrupted by the new planning direction

Two files contain partial, unverified local edits from the paused PCB usability task:

- `web/src/components/highGPcbReference.ts` now has `pcbAxisTicks` and `footprintConnectionSummary` pure helpers. The latter reports recorded pads, unassigned pads, and distinct source net names for one known placement.
- `web/src/components/HighGPcbReference3D.tsx` now draws source XY axis lines/ticks and fixed-size millimetre labels, fits the camera with room for those labels, and provides visible placement pick markers when the documentation layer is enabled. The markers are interface locators at source placement XY, not package geometry. The selected ring is moved to the selected source face and hidden when that face is filtered.

The attempted follow-on UI patch did **not** apply. There are no Top-only/Bottom-only/Restore shortcut buttons, Reset reference view button, or visible footprint-net summary yet. The import of `footprintConnectionSummary` is currently unused. **This partial code has not passed focused tests, typecheck, lint, format, build, or native inspection after the new edits.** It should be finished or backed out under the new phase ownership before publication; do not treat this handoff as a completed PCB-controls feature.

## Source requirements for deeper product detail

The full revamp should keep four distinct layers of evidence in the interface:

| View | Available now | Needed before claiming more detail |
| --- | --- | --- |
| Manufacturer board XY / circuit diagram | Eagle outline, drill/pad/trace/net/placement/silk data and CC BY-SA 3.0 attribution | Native readability and selection check of the new axes/markers; exact source pin for any additional revision or schematic |
| Populated product component | Planar footprint positions and source values | Manufacturer package models or measured board assembly with revision, dimensions, orientation, and component heights; U1's Eagle value is ADXL343 while actual incoming silicon identity remains unverified |
| Vehicle installation / connection | RP1 part identity and separate simplified vehicle envelope | Actual mounting datum, orientation, fastener/connector details, cable route, tolerances, and verified installed clearance; no source XY-to-vehicle transform may be inferred from the board file |
| Physical build / system test | Existing engineering documents, preliminary simulation and separately recorded tests | Purchased hardware identification, assembly measurements, wiring continuity/electrical evidence, fit and environmental results, and owner-authorized build/test work |

For diagram modes, keep a source XY layer/circuit view, an independently source-pinned product/package view, and a vehicle installation/connection view with explicit unavailable fields. A source-labelled interaction can cross-link the same refdes/net/part across those views only where identifiers and coordinate transforms are recorded. Graphics, source coverage, native interaction, engineering acceptance, and physical test evidence must each have their own status. The current board has no supported finished PCB thickness, component/package heights, via copper outer diameter, ground pour fill, actual incoming U1 silicon confirmation, or vehicle mounting transform; the viewer must not fill those with display Z, generic blocks, or inferred dimensions.

## Native check when this phase resumes

After finishing and source-checking the paused controls, the sole designated Chrome verifier should inspect one actual top and bottom camera path, Top-only/Bottom-only/Restore visibility if implemented, source XY ruler legibility at Fit and zoom, one placement marker/list selection, one recorded net connection, and Reset returning the local reference state. Capture exact source identity and actual screenshots. This is a new bounded graphic/interaction observation, not retroactive repair of P56/P57 or physical qualification.
