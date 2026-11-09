# P63 PCB local controls — actual desktop result

The actual PCB dialog is recognizable and usable for the scoped face/ruler checks. Confirmed-focus Parts search selected `high_g_accel` from exact RP1/spec811b, then Details opened **Explore PCB structure in3D**. Native images establish the board outline, mounting holes, pads and routed source features; visible26/82/208/26 coverage counts are recorded separately from pixels.

**Top layers only + Top camera** shows top checked/bottom unchecked and gold source routes. Its actual XY rulers have readable5/10/15/20mm horizontal ticks with25.4mm endpoint, and5/10/15mm vertical ticks with17.78mm endpoint. **Bottom layers only + Bottom camera** shows the opposite checkboxes, purple source routes and reversed horizontal ruler orientation. These are distinct rendered states. Some fine-silk source glyphs protrude beyond the board and clip at the canvas edges, particularly in bottom/oblique views; the board/ruler/route evidence does not establish an unclipped artwork pass.

**Reset reference view** restores both layer checkboxes, All nets and the oblique fitted camera. It returns to/defaults **U1·LGA14**, rather than clearing selection. Native state and pixels show U1 retained; source resetReference explicitly sets U1. The task’s no-selection condition is therefore not met. No changed footprint/net was exercised, so restoration of an altered selection is also unexecuted. Initial Fit and post-reset framing are captured; no separate Fit-button action was taken.

The UI retains unknown board thickness and component/package heights, manufacturer XY versus vehicle-envelope differences and the source ADXL343/U1 conflict in the ADXL375/PID5374 file. No populated installed3D board, silicon identity, fit or physical qualification is inferred.

The dialog closed at120.206s native elapsed, with last input119.326s before the140s cutoff. Parent selection remains `high_g_accel` Details/exactspec, Rotate mode and heading−309.2°/tilt61.5°. Normal part selection changed the subsystem to Avionics and power and target to High g accel. No main Whole/reset/visibility command occurred; no exact count/camera-position preservation is claimed. Optional footprint/net/spacing/other zoom controls remain unexecuted.

Source hold is released and native lane is idle. The raw screenshots are unchanged; their raster size is not CSS viewport acceptance. No Run, Play, export, permission/settings, viewport or other-window action occurred.
