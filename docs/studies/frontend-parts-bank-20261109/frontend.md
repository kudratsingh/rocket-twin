# RP1 parts bank frontend slice

This Phase 1 panel is a read-only source catalog for the frozen RP1 configuration. It shows 55 source definitions beside 55 installed source records. A definition describes the recorded part; its installed occurrence carries the original stable part ID, source position, parent, and group count. The panel does not create a draft, replace a part, or alter the active vehicle.

## User path

The Design header opens a large Parts bank dialog while the existing 3D viewer remains mounted behind it. Search and Kind, Material, and Representation filters narrow the source list. Selecting a row shows the recorded function, nominal source dimensions, material, manufacturing description, group mass estimate, dated source budget, provenance and unresolved issues. The axial diagram displays source stations only; it is not a CAD silhouette or a center of gravity calculation. The **Inspect installed part and available CAD/evidence** action passes that occurrence's exact stable ID to the existing Design inspector. Available viewer/CAD actions are scoped there to the current source.

An available GLB is a globally placed **installed inspection reference**, not a reusable part in its own local coordinate frame. Catalog metadata gives its registered occurrence and original viewer frame and explicitly marks local geometry reuse false. It cannot be dropped into another assembly with an assumed transform. A local template or native frame and connection data remain later builder work. Source records with no mesh remain visible and are marked unavailable. Source budget zero means neither a free part nor an owner stock credit. No displayed amount is a current unit quote.

## Admission and transport

The client admits only `rp1-parts-bank-v1` for `G80-F2-RP1-AD1-definition-v2`, with exact pinned specification, AD1 definition, record, backend module, and (when available) inspection geometry identities. Every definition and installed occurrence must match the current 55-part vehicle, including source content, roles, links, group counts and positions. Read-only, physical-open and unresolved conflict statuses are checked. The catalog's Python revision is pinned; the client does not attempt to reproduce Python float serialization in JavaScript.

The panel requests `GET /api/parts-bank`. Only a 404 switches to the prepared `/engineering-workbench/rp1-parts-bank.json` export from the same Python builder, and the panel labels which transport it used. A server error, network failure, invalid JSON, foreign identity or incomplete catalog shows an unavailable state; it never substitutes a different source. Generated mesh availability is atomic: the source-only export has no mesh assets and the prepared current export has 26, while both retain all 55 source records.

## Evidence and limits

The tracked test fixture is the Python source-only build from the three exact RP1 inputs, with no optional generated assets: `web/tests/fixtures/rp1-parts-bank.json`. Its SHA-256 is recorded in the focused test. Source tests check the tracked input hashes, 55-way links, filtering, known conflict and zero-budget warnings, and 404-only fallback. Type, lint, format and build checks are code evidence. Browser interaction has not been observed in this packet. The catalog does not establish installed construction, current prices, manufacturing readiness, full CAD coverage, engineering acceptance or flight readiness. Frozen RP1 geometry, mass and inertia, the active design and all owner gates remain unchanged.
