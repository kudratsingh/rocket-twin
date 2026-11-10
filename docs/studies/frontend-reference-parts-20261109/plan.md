# Two nominal local references: bounded integration plan

## Decision and scope

Expose **two existing, source-pinned local annuli** in the parts bank as geometry-only planning references. This is a read-only inspection and datum-selection path. It neither creates a draft occurrence nor changes frozen RP1, its 55 source records, saved drafts, CAD generation, the kernel, template registry, physics or engineering decisions. [Source contract](source-contract.md), [API contract](api.md) and [frontend datum contract](frontend.md) define the completed independent lanes. PR128 is merged at `95fddb209197c6a412900c903b22061925f57172` after its required CI passed; that publication is a predecessor, not native acceptance for this increment.

| Reference definition | Existing template | Exact source nominal | Identity limit |
| --- | --- | --- | --- |
| `reference-local-v1:motor-tube-nominal` | `rp1-template:motor-tube-cut` | OD **31.369 mm**, bore **29.169 mm**, length **165 mm** | Nominal tube geometry; neither purchased stock nor installed fit |
| `reference-local-v1:aft-annulus-nominal` | `rp1-template:aft-annular-ring` | OD **64.4 mm**, bore **31.9 mm**, thickness **6 mm** | Plain annular reference; no complete installed ring construction or bond |

The existing STEP files use millimetres in a **local front-center CAD frame**: X = body +y, Y = body −z, +Z aft. The viewer uses metres with `viewer[X,Y,Z] = [cadX/1000, -cadZ/1000, cadY/1000]`; CAD +Z therefore appears along viewer −Y. No installed transform or nose-tip placement is supplied. The five named features per definition are `axis`, `bore`, `outer_cylinder`, `start_plane` and `end_plane`. They are **parameter-derived analytic datums**, not persistent kernel faces, GLB triangle IDs, measured tolerances or mating contracts. The planes' +Z normals are a datum convention, not extracted face orientations.

All mass, inertia, procurement cost, stock tolerance, strength, material qualification and thermal capability fields remain null. Add-instance, Connect, resolved candidate, simulation, engineering, physical and flight readiness remain false. Geometry availability is separate from source identity and does not fill those gaps.

## One integration packet

1. Keep the source/API/frontend definitions pinned to their actual registry, manifest, template revisions and four existing STEP/GLB byte identities. Mount the read-only `GET /api/reference-parts` list/detail router on the existing loopback workbench; preserve exact-origin, GET-only and no-body/no-query validation. A missing local asset reports unavailable without generation; changed registered bytes fail closed.
2. In the existing parts-bank template detail, offer the matching local CAD preview and five keyboard-selectable analytic guides only for an admitted definition and its matching template representation. The overlay lives inside the existing Canvas and follows the local CAD-to-viewer mapping. The parent verifies public GLB/STEP bytes before parse/download; the API's local-cache flag does not certify the public URL. A bore selection may ghost the displayed solid without changing source geometry. Errors and absent cache remain visible.
3. Run the full source, API and web checks **once after integrated source freeze**, including the reference-focused cases, type/lint/format/build and the repository's required gates. Correct only a demonstrated defect in this packet and repeat the affected checks once. Do not start CAD/kernel export, a variant search, alternative transport or a broad test/native campaign.
4. After root declares the integrated source frozen and the sole designated browser owner has the authorized Chrome window, execute **one bounded native datum case**: open a registered nominal template, verify source/revision and local-versus-installed labels, select one datum from the list, inspect its overlay against the loaded solid, clear it, and verify local controls/STEP provenance and return state. Record actual source identity, viewport, action sequence, screenshot/readout and elapsed time. Preserve a failure or unavailable outcome; a retry is limited to a scoped, demonstrated defect after correction. Root owns that native packet and acceptance.

## Stop and acceptance boundary

Stop on source/revision mismatch, missing or corrupt asset, foreign frame, unavailable browser context, changed window/transport, timing cap or an unexplained interaction. Report the exact condition rather than substituting an installed mesh, cached preview or another browser path. The source/API/frontend lanes are implemented, and parent wiring is present, but **integrated checks and the native datum observation are pending** for this packet. Passing those checks would establish only a scoped inspectable reference. It would not finish the full builder, admit mating/placement, qualify a material or open any physical or flight gate. Five supplier/lab inquiries remain UNSENT.
