# Inspection evidence and synchronized replay readouts

This increment extends the saved inspection slice. Code and synthetic rendering
checks are complete; actual browser interaction and layout acceptance remain
blocked by the existing designated runtime-ownership prerequisite. No browser,
new window, headless session or unsupported repair was attempted.

## Usable code paths

After `make preview` from the repository in a normal host terminal, open
`http://127.0.0.1:5173/?workspace=design&design=modular-performance-v1`.
The sandbox previously rejected the listener with `EPERM`; this increment does
not assert that a server is running or that the host has been tested.

Select a component, then **Connections & evidence** in the selection controls.
The disclosure opens, scrolls into view and receives focus in code. Its sections
show declared parent/child hierarchy, source interface endpoints, failure records,
requirements, verification needs and evidence states. Mapped endpoints use the
existing shared selection; unmapped ones stay explicit. Selecting a hidden part
does not silently show it. Assembly hierarchy is not a demonstrated load path.
Missing electrical metadata does not produce inferred wiring.

In Flight Replay, choose one or two existing runs, scrub time and choose a graph.
The selected-channel readouts now show each run's nearest **actual decimated
sample**, its actual timestamp and its recorded unit. They do not interpolate,
extrapolate, substitute zeros or claim full-rate extrema. Missing/nonfinite values,
invalid time axes and time outside a run's coverage remain unavailable. Existing
flight/recovery model limitations, phase/event controls, incompatible-channel
withholding and configuration/environment comparison remain in place.

The four reference CAD assemblies retain their own sources. F2, RP1 and AD1 are
separate concept/study identities; these changes do not fabricate meshes or
compatible analysis fields for them. Failed historical thermal results remain
failed and cannot become accepted active-vehicle overlays.

## Evidence and pending acceptance

Integrated TypeScript, lint, formatting, all76 web tests and production build
passed. The tests include source guards, synthetic React server rendering,
connection mapping and actual-sample coverage cases. Vite emitted its existing
large-chunk warning; test output also recorded a development WebSocket listener
`EPERM`. Neither is evidence of browser usability or performance.

The designated browser owner still needs to observe disclosure opening/focus,
section-link scrolling, 2D/3D component selection, hidden-state preservation,
narrow layout and two unequal-duration replay runs with channel/unit changes.
No supported runtime repair/handoff action is exposed in this session. The
original automatic approval rejection and missing retained full reviewer text
are recorded in [the unblock note](frontend-browser-unblock-20261103.md).
Do not retry through another agent or browser. No screenshot is claimed.

FT-009/014/018 remain partial until their browser and full acceptance criteria
are met. WO-03/04/05, physical work, purchases, paid runs, WO-10 owner review and
flight-release gates are unchanged.
