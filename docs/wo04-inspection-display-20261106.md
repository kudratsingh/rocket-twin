# FT-015 — recoverable section and exploded inspection

The next bounded task from the existing 43-task backlog adds **Restore assembled
inspection** to the Design viewer. It shows all source parts, clears exploded
spacing, section clipping, transparent-shell mode and wireframe, preserves the
selected part and viewing angle, and requests an assembly fit. Reset camera and
fit remain separate existing controls. No engineering value or camera physics
is changed.

Open `http://127.0.0.1:5173/?workspace=design&design=modular-performance-v1`
after `make preview`. The readout sits below the exploded-view controls in
**3D recorded geometry**. It uses whichever exact inspection document the viewer
received; this route identifies an archived modular reference, not F2/RP1 CAD.

## User-facing behavior

- Compact persistent status states whether section clipping is on, how many
  source parts are hidden, and whether display explosion, transparency or
  wireframe is active. Missing mesh references remain visible as unavailable.
- The restore action clears those display transformations together, so a hidden
  or sliced part cannot silently remain missing after returning to assembly.
  It does not reset selection, source, viewing angle, burn state or annotations.
- **How this display works** is collapsed initially. It explains the fixed cut
  at viewer X = 0, positive-X half hidden, and the difference between display
  triangles and physical construction. No artificial cut surface is manufactured.
- A separate collapsed selected-component dimension panel reads the exact source
  record. Exploded gaps are illustrations, not clearances; dimensions remain
  unchanged. Missing dimensions and foreign part IDs remain unavailable.
- With no recorded component mesh references, the restore action is disabled;
  reference presence is not evidence that GLB files loaded successfully.

These controls do not convert concept envelopes, historical assemblies or
unqualified components into build-ready geometry. Existing source-based 2D
inspection, engineering views, experiments and recorded replay remain in place.

## Evidence and pending browser checklist

Code tests exercise the real inspection store: reset all display modes, preserve
selection/view/labels/markers, trigger fit, repeat safely, and leave source
dimensions unchanged. Actual-component server rendering checks visible status,
collapsed disclosures, source dimensions and unavailable cases. An actual saved
`modular-performance-v1` inspection source has 42 mesh references and records the
selected `body_upper` length as 778 mm; this is an archived source check, not an
as-built measurement or current RP1 assembly.
The inspected saved document SHA-256 is
`6594322d1181853cfe19e53b273c1d92e4892879ddb05dd1c462ed2aee0851cb`.

Integrated checks pass: 93 web tests, TypeScript through the packaged build,
ESLint and formatting. Existing tests emit sandbox-denied Vite socket warnings;
they still complete successfully, and those warnings do not establish a running
service. The existing large-bundle build warning remains. Open the
[static actual React readout](../output/inspection-display-20261106/index.html)
with its [source manifest](../output/inspection-display-20261106/manifest.json).
Static actions are inert. No PNG or visual inspection was produced for this slice.

The designated browser owner/window's runtime prerequisite remains unresolved.
No browser, screenshot, clipboard, mesh-loading or frame-rate acceptance is
claimed. Localhost HTTP probing was denied by the sandbox. The next permitted
browser verification must observe:

1. Hide/isolate a part, enable section and explosion, then restore: all source
   parts reappear and the actual assembly fits without changing viewing angle.
2. Keep the selected component and source identity through reset and source
   switching. Check no foreign dimension or hidden state leaks across sources.
3. Open the two disclosures, verify readable layout/scrolling at ordinary and
   narrow widths, and confirm no-mesh/unavailable behavior.
4. Exercise the original inspector, experiment and replay routes for regression.

Source, store and server-render checks do not satisfy this checklist. FT-015 is
partial; full WO-04/05 and all WO-03, physical and flight gates remain open.
