# Open and use the updated inspector

Run `make preview` in the normal terminal from the repository root. The launcher prepares the core model and optional source-detail assets; absent optional detail leaves the core view available. Open http://127.0.0.1:5173/?workspace=design&design=G80-F2-RP1-AD1-definition-v2 . No backend restart is currently pending.

1. Drag the main canvas to orbit. Use scroll/pinch or labelled Zoom in/out. Fit assembly frames the complete model; Frame selection focuses a chosen component. Right/Shift-drag and the camera pan buttons provide panning; modifier-drag itself was not exercised by the native verifier.
2. Click **Inspect interior**, then choose Motor and retention, Recovery, Avionics and power or Fins and roots. The shell is hidden and the selected assembly is framed without finding a drawer toggle.
3. Leave **Source detail** enabled. Select the forward ring and Frame selection to inspect the bore, straight cord passage and source-recorded stock/bond layers. Motor-tube and aft-ring bores have finer geometry. Detail coverage explains which features exist and which do not.
4. Open **Fin alternatives**. Switch the separate fin schematic between AD1, FP1 and FR1. FP1 can spread its core, adhesive and carbon faces apart. The active rocket and simulation configuration are preserved. Finished replacement assemblies/attachments remain unavailable and unadopted.
5. **Restore visibility** returns the prior hidden/display set and frames the restored assembly at the current angle. **Restore assembly**, then Reset view/Fit, returns the standard assembled inspection view.

[Actual integrated gallery](integrated-gallery.html) · [scoped browser outcomes](integrated-results.csv) · [baseline comparison](baseline-observation.md) · [source/report](report.md).

The final observed app was assembled RP1,26/26 meshrecords visible, no individualpart selected, Motor group highlight retained, interioroff,sourcedetailon, bothpanels/Partsopen, tools/dialogclosed,45/54.7/0 Assembly target. Exact viewport measurements remain blocked under the earlier DevTools rejection. The final preview-first modal ordering and selected-label wording refinements were made after captures and have source checks, not a new browser pass.

Twelve source box envelopes still lack finished hardware geometry. PCB internals, retainer threads/seat/cap, actual knot/rope topology and unspecified roundovers are not fabricated. Source dimensions or manufacturer CAD for the exact selected product are needed before those representations can legitimately gain detail. No owner hardware measurement is requested while components remain unpurchased.

All source GLBs, AD1/D1 records and engineering gates remain unchanged. No purchase/contact/physical test, approved construction or flight release follows from the viewer.
