# Exact application viewports inside the permitted Chrome window

## Purpose and source

The native runtime can operate the permitted Chrome window but exposes no exact
window-bounds setter. Do not retry the denied DevTools route, use another browser/
transport or ask the owner to chase pixels. This bounded alternative uses ordinary
first-party development HTML to display the actual running app inside an unscaled,
same-origin iframe. It does not create a prototype, copy its layout, resize Chrome,
change zoom or drive the app with injected automation.

An iframe has its own actual browsing-context viewport. Media queries and viewport
units inside it use that viewport, as described by [MDN's viewport concepts](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/CSSOM_view/Viewport_concepts).
The browser's [innerWidth](https://developer.mozilla.org/en-US/docs/Web/API/Window/innerWidth)
can report that frame's layout viewport. These are real browser properties, not
requested values substituted for observations.

## Method limits

The DEV-only host offers1440×900,1280×720 and900×720CSS presets. Resizing changes
only the existing iframe element dimensions; its app window/document/source is
not recreated. The parent reads actual frame viewport/client dimensions, DPR and
visible frame rectangle. It never reads app stores, clicks inner controls, replaces
fetch responses, creates synthetic analysis/telemetry or changes browser settings.
The actual app still loads its real API, CAD and recorded data. The sole designated
native verifier performs every actual app interaction in the authorized window.

Every artifact must say **embedded, unscaled actual-app viewport**. Parent Chrome
remains at its separately reported size. This method can establish app CSS layout,
media/container breakpoints, canvas client ratios and state-preserving app-viewport
resize. It cannot establish top-level window-manager behavior, Chrome page zoom,
full-browser history/download behavior or representative top-level FPS. Those retain
their own evidence. No original top-level observation is relabelled.

Thresholds/sizes are unchanged. Credit only the relevant application-viewport
criteria after the native pilot proves the real app, actual measured sizes and
ordinary interaction. Do not silently convert remaining broader/host criteria into
passes. Source checks alone are not a native pilot.

## Bounded admission pilot

One15-minute source implementation plus one scoped correction. Fixed loopback DEV
origin and source URLs, no arbitrary external frame, scaling or new dependency.
Production entry/build behavior stays unchanged. Existing CSP/frame restrictions
are respected; no security relaxation to force the fixture.

Then one separately declared native pilot: target80s, hard90native/120overall,
no action after70. Verify requested versus actual1440×900, the exact current RP1
source with rendered geometry, and one actual inner-app selection/control. Change
one preset on the same frame and confirm actual resize plus retained state. Record
images/readouts and source hashes. Stop unknown/mismatched size, clipped outer
frame, stale source, guard/context change, error, review denial or low reserve;
no method cascade, hidden driver, unauthorized window or retake.

Only after pilot admission may the full relevant matrix proceed in bounded native
slices. Independent native pixel measurements retain original whole-window images,
identify the visible frame boundary and calculate actual Canvas/frame ratios. A
requested size, computed CAD projection or resized screenshot is not acceptance.
