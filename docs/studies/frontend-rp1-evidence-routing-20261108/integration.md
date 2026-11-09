# Choose the fin or recovery connection from a part

## Useful inspection change

A forward ring has more than one structural function. Its Design inspector now
exposes separate recorded **Fin root** and **Recovery attachment** routes, each
with the exact frozen design, specification, part and connection in the URL.
This avoids silently choosing the first graph merely because the ring belongs
to both. Other parts receive only their recorded routes; parts with no matching
connection show an explicit unavailable state.

Engineering’s return link preserves the selected part and the applicable
connection context after checking that the part belongs to that route. Changed
sources and graph membership must not acquire a source-pinned link. These are
navigation improvements, not new geometry or a connection-strength calculation.

The archive CAD panel also puts its long format/coordinate/model explanations
behind a clearly labeled disclosure, leaving download controls earlier in the
inspector. Units and file-specific frame information remain present. Existing
Design, Engineering, experiments and replay are retained.

## Source and evidence

This increment follows the [source reconciliation](../frontend-desktop-detail-20261108/next-evidence-navigation.md)
and uses frozen`G80-F2-RP1-AD1-definition-v2`, specification
`811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`
and inspection geometry
`238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`.
The tracked compact connection fixture preserves the actual exporter’s metadata;
it is not a synthetic physics case or a replacement solid. Fresh hosted tests
must not depend on an optional prepared public file.

Implementation is limited to one navigation correction and one scoped correction
cycle, with a15minute agent budget. No new fin construction, custom solver, full
vehicle CAD, simulation, supplier contact or physical work is admitted. If source
or mapping is missing, show unavailable rather than infer a connection.

## Verification and the actual correction

P47 stopped before native input because an evidence helper binding had reset.
That wrapper failure is preserved; a separate documented binding restoration
used no UI input. P48 then actually verified both route links and Recovery
content, but its settled Design return dropped the selected part. The source
explains how null selection was written to the URL; the initiating callback was
not observed and is not claimed known. [Source trace](selection-trace.md).

One bounded correction now distinguishes explicit selection intent from source/
loading resets when writing URLs. A valid incoming selected part survives an
internal reset; deliberate X/Escape/group/focus actions still update selection.
Overview routes hydrate no selection. Empty-canvas pointer misses no longer clear
the inspector. This is not a new geometry or physics model.

The combined318 local tests, TypeScript, lint, formatting and packaged build pass;
four preserved unrelated A2 cases remain outside publication. Real-store tests
exercise reset/rehydration versus explicit clear, part/group/focus actions and
stale-source rejection. They are not a mounted StrictMode or browser test.

P50 separately verifies the actual Recovery→Design round trip: the top URL,
forward-ring inspector and selection survive settling and later asset loading.
Frame targets the ring, and explicit Clear removes the part/opens summary; Whole
returns the assembly. The ring is still occluded inside the body when merely
framed: this is not a clean-detail visibility pass. Existing interior/isolation
controls remain separate. No compound RV row or full frontend acceptance is
promoted by this scoped check. Strict performance failure remains unchanged.

[Failed P48](../frontend-evidence-route-verified-native-20261108/browser.md) ·
[Corrected P50](../frontend-selection-correction-native-20261108/browser.md) ·
[Correction budget](selection-correction-plan.md).

Metadata export completed in P49 after explicit local-site authorization, without
an actual permission/settings change. All five inquiries remain UNSENT; no owner
measurement is requested for unpurchased hardware. Engineering/physical/flight
gates remain separate.

## Further scoped desktop observations

P51 activated the actual accessible SVG group for forward_ring and retained its
exact part/spec, inspector and scene annotation after switching to3D. It is not a
coordinate pointer-pick or all55-part test. P51 exposed lower annotations covered
by the selected-part action card. One2D-only CSS change moves that card into normal
flow, keeping3D layout unchanged. P53 shows the nose datum,1060.00–1072.20mm/source
role and station-direction annotation without that obstruction, with no zoom/Fit
adjustment. P51's original obstruction remains frozen. Formatting and packaged
build pass after thisCSS change; the318-test JavaScript result remains separate.

P52 also verifies changed draft wind does not alter the saved result, and Reuse A
restores its recorded wind/direction/gust/Tiny/seed settings without Run. Independent
saved-record SHA remains unchanged. This is draft workflow evidence, not a new
simulation, worker-error case or physical measurement.

[2D→3D](../frontend-2d-3d-selection-native-20261108/browser.md) ·
[Readable drawing](../frontend-drawing-readability-native-20261108/browser.md) ·
[Draft reuse](../frontend-draft-reuse-native-20261108/browser.md).
