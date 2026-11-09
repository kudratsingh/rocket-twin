# PCB source-layer controls — implementation handoff

The current RP1 high-g board reference remains gated to part `high_g_accel`, configuration `G80-F2-RP1-AD1-definition-v2`, specification SHA `811b3bed…1660`, Adafruit Eagle source SHA `7c089eb8…d68c`, and the frozen `high-g-pcb-layout.json`. No extracted source record, vehicle state, physics, mass, installation or manufacture data changed.

## Implemented in the existing viewer

- Source XY millimetre rulers now sit outside the actual 25.4 × 17.78 mm board outline, with 5 mm intermediate ticks and exact boundary marks. The ruler is an inspection aid drawn from recorded source coordinates. It is not a vehicle datum or Z measurement. Fit framing leaves space for the labels. HTML glyphs retain fixed screen size so orthographic zoom does not recreate the P56 giant-label obstruction.
- Camera controls say **View top (camera)** and **View bottom (camera)**. Separate **Show top layers only**, **Show bottom layers only**, and **Restore both layers** buttons change source-face visibility; the corresponding checkboxes remain available. Camera orientation and layer visibility are deliberately independent.
- Turning on **Footprint outlines and pick points** exposes small selectable locators at the 26 recorded placement XY positions. They are interaction targets, not package outlines or package heights. The selected locator ring follows the recorded top/bottom face and is hidden if that face is filtered. Selecting a pad, pick point or list footprint clears the previous net highlight so the new footprint context is unambiguous.
- The selected footprint shows recorded pad count, number of pads without a source net, and buttons for its distinct recorded nets. Choosing one highlights the existing source pads/traces/via drill positions and retains the existing net summary. No connectivity, pour, continuity or electrical-test result is inferred.
- **Reset reference view** restores the local PCB inspector to U1, all nets, both source faces, silk/fine artwork on, footprint outlines off, zero display spacing and Fit camera. It does not mutate RP1 selection, saved configuration, hardware or a run.

The official Eagle U1 value remains ADXL343 while the actual incoming silicon identity is unverified. Board thickness, package heights, via copper outer diameters, poured ground fill, vehicle mounting datum, mating tolerance, and installed fit remain unavailable. The upstream CC BY-SA 3.0 notice remains visible.

## Checks and native scope

On this source packet, three focused tests passed, including exact source admission, known XY ruler ticks, U1's 14 pads/3 unassigned pads/distinct source nets, planar conversion and rendered control/disclosure text. `npm run typecheck`, focused ESLint, Prettier check and `npm run build` passed. These are code/source checks only; no agent in this lane used the browser.

The sole designated Chrome verifier can check the following as one bounded fresh-source packet after integrated runtime checks: Fit shows the board and legible XY rulers; View top/bottom changes camera only; Top-only/Bottom-only/Restore changes visible source faces without moving the vehicle; enable pick points and select a source footprint by canvas and list; choose one of its recorded nets and see corresponding highlighted copper/summary; hide the selected face and see the hidden-selection notice; Reset restores U1/clear net/both faces/zero display spread/Fit. Capture actual source identity, visible graphic and result or failure. Existing P56 failure and P57 correction evidence remain historical and do not automatically qualify these controls.
