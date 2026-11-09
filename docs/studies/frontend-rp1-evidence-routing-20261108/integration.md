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

## Verification boundary

Nine focused connection/navigation checks and the combined315-test frontend
suite pass, along with TypeScript, lint, formatting and the packaged build. Four
unrelated preserved A2 tests remain outside publication. The existing large-chunk
build warning remains; no frame-rate claim follows. New native round-trip and disclosure observations remain pending:
the sole browser agent is paused after P46 automatic approval rejection of a
persistent local-site multiple-download permission. Do not close the compound
RV acceptance rows or infer browser behavior from generated markup. The existing
native P40–45 observations retain their original scope and failures.

After an explicit permission decision, the bounded browser continuation can
finish the pending metadata export, restore Design, and separately exercise this
new route. That future packet needs its own actual observations; this document
claims none. All five inquiries remain UNSENT and engineering/physical/flight
gates remain unchanged.
