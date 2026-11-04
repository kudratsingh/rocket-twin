# Component dimensions and reproducible experiment exports

This extends the saved43-task preview without changing the graphics engine,
simulator, active vehicle or recorded flight poses. Browser observations remain
unavailable behind the existing designated-agent runtime-ownership prerequisite.
No computer-use retry, alternate window or headless bypass occurred.

In Design, select a component and open **Connections & evidence → Dimensions &
material**. Supplied dimensions now have readable metre/millimetre conversions,
and masses have kilogram/gram conversions. The panel explains radius, diameter,
fin dimensions, box envelopes, coordinate origin, material/estimation basis and
source tolerances. Component mass, CAD mass and subtree mass stay separate.
Missing wall thickness, internal geometry, transverse/mesh frame and tolerances
remain unavailable; the panel does not derive them from another number or CAD.
It distinguishes nominal recorded meshes, source envelopes and absent geometry.

In Experiments/Flight Replay, select saved A/B runs. Each can export its own
**CSV of returned decimated samples** and **metadata JSON**. Timestamps and
coverage are independent; missing/nonfinite values stay blank, malformed time
axes withhold CSV, and no resampling or extrapolation occurs. Metadata retains
the exact run record, configuration/settings/model fields, per-run channel units,
provenance, coverage and comparison differences. These are playback exports,
not full-resolution telemetry, measured flight evidence or compatible spatial
engineering fields. Backend-derived channels remain identified.

**Reuse recorded settings as draft** copies supported wind speed/direction/gust
only when the recorded complete configuration and request match the selected
supported configuration, simulated preset and locked/unguided controller. It
does not switch an active design or run an experiment. Incompatible/missing
fields explain why copying is withheld. Historic model/case/revision fields
are not falsely copied into a new model run.

Integrated typecheck, lint, formatting,81webtests and production build passed.
Checks include source-shaped and missing-data dimension rendering, CSV quoting,
actual timestamps/missing values, metadata preservation and draft isolation.
The existing bundle-size warning and sandbox development-WebSocket EPERM remain;
neither constitutes a browser performance/usability result.

Use the existing preview at `http://127.0.0.1:5173/`; after stopping an old
launcher, restart from the repository with `make preview`. The prior read-only
listener observation does not establish current HTTP or browser reachability.
Actual downloads, draft controls, focus/scroll/navigation and narrow-screen
readability still require the original designated browser owner after supported
ownership is restored. No supported repair command is exposed here. See
[the recorded blocker](frontend-browser-unblock-20261103.md).

FT-014/019/024/025 continue as partial; full acceptance is not inferred from
code checks. No F2/RP1/FR1 concept is mapped to an archived CAD assembly. WO-03,
fullWO04/05, physical work, purchases, paid runs, WO-10 and flight gates remain.
