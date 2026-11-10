# Source-backed template bank and system map

This autonomous follow-up to PR122 adds two read-only workbench paths. It does
not change frozen RP1, admit a fin replacement, or send any of the five inquiries.

## Try the two paths

Use `make preview` from the repository root and open <http://127.0.0.1:5173/>.
The existing running preview needs no API restart for this increment. Its new
template data can be prepared separately with `make part-templates`; this reads
the frozen source contract and generates no CAD or flight result.

1. In current RP1 Design, open **Parts bank → Template recipes**. Choose a named
   recipe, select a recorded parameter to highlight its related feature rows,
   read units, source locators, proposed tolerances and missing contact evidence.
   **Inspect installed …** returns to that exact stable part in Design. The
   installed source catalog remains available in the adjacent section.
   Motor tube and aft ring additionally offer **Local CAD preview** with explicit
   Move/Rotate/Fit/zoom and **Download local part STEP**. The downloaded geometry
   is the local source solid, independent of camera or the installed assembly.
2. Open **Engineering → Physics & control system map**. Select an actual diagram
   block to see units, coordinate frame, source and implementation limits.
   **Current G80 · unguided** explains shared simulator and source-defined hardware
   roles; **Future G12 · PID → RL** explains the committed separate control track.
   It does not install a gimbal or controller in G80. Reference links point to the
   exact merged source checkpoint, not mutable `main`.

## What the source establishes

The registry accounts for 55 stable source records, five named template groups
and 14 feature-source relationships. A source-nominal motor-tube cut and plain
aft annulus have allowlisted local geometry recipes. Three other groups remain
unadmitted as reusable local templates. Geometry recipes, installed inspection
assets and finished physical connections are distinct. Template features add no
mass line, and associated gussets remain separate supports from integral fins/tabs.

The prepared JSON is explicitly labeled a source contract, not a live API. Its
whole-file SHA-256 is checked before parsing; matching design/spec/geometry and
all 55 source IDs are required. Corrupt bytes, wrong identities or transport errors
stay unavailable. There is no fallback to historical hardware, altered source,
missing stiffness, zero mass or a passing result.

The two separately admitted CAD cases completed in10.277wall/9.408childCPU seconds.
Both actual STEP readbacks are one valid closed annular solid with the expected
bore/OD/length. Metre GLB bounds agree. The optional local preview verifies GLB
bytes before parsing; the download verifies STEP bytes before requesting a save.
[Geometry evidence and cache limits](../frontend-template-bank-20261109/geometry.md)
are separate from browser observations. This completed current-host cache is not
a fresh-clone reconstruction path: absent ignored outputs remain unavailable.

The system diagram records independent source/model/planned/unavailable statuses.
Motor data feeds forces, and mass/CG/inertia feeds the rigid-body plant directly.
Recovery hardware identity, exact wiring, installed behavior and complete RP1
flight/inertia inputs remain unresolved. The shared simulator's existence is not
evidence of a complete RP1 run. G12 estimation/guidance/PID/RL and physical
actuation qualification remain their own work orders.

## Evidence and remaining work

[Template source contract](../frontend-template-bank-20261109/source-contract.md)
and [system-map source audit](../frontend-system-map-20261109/source-audit.md)
explain the supporting repository evidence. Focused source/SSR and integrated
checks are separate from [native readiness](browser-readiness.md) and later actual
browser observations. Native results and exact publication checks are appended
after execution; no pending observation is a pass.

P71 actually observed the template catalog, selected109.4mm Tab Length, rendered
the local annular bore, invoked Fit, downloaded its STEP and returned to exact
RP1/spec/aft_ring in Design. It did not exercise local orbit/pan/zoom gestures or
the motor-tube preview. Native inputs ended145.883s and observation164.398s;
record/inventory closeout190.572s exceeded the180s packet by10.572s. Those scoped
observations are retained, but the whole packet does not receive a budget pass.
No automatic retake was started.

Independent [actual download readback](../frontend-template-bank-20261109/download-readback.json)
matches all9,599registeredbytes/SHA, explicit millimetre STEP units, one closed
annular solid,64.4mmOD,31.9mmID and6mmthickness in local front-center coordinates.
Camera/display transforms were not exported. This is actual-source geometric
proof, not physical stock, strength or manufacturing acceptance.

Supporting checks:360localwebcases pass (four preserved unpublished A2 cases;
356in publication scope),15focusedtemplate/map/routing cases,18Pythonregistry/
geometry cases and the current whole-tree Ruff/Black/mypy checks. Type/lint/
format/build pass. The small template-geometry cache check skips explicitly on a
clean host without the ignored outputs; that host receives no CAD readback claim.
Required hosted checks must be tied to the final published head.

P72 observed both system branches, selection and exact Design return within its
budget, but the real images had crowded flow labels and below-fold details.
One declared display correction retains the same source graph and adds compact
E1… markers, a complete flow key, bounded graph size and an adjacent detail card.
P73's two actual screenshots visibly verify both full graphs/keys/cards, G80
units/source paths and planned G12/null-gain/source details at the current window.
Its native work ended54.130s, last input52.533s, and record/inventory85.314s, within
the180s packet and80s input limit. Exact-source Design/aft_ring return was verified
by AX; there was no third return image. P72 and P71 limitations stay historical.
No external source link was followed or controller/physics validation inferred.
The window is free; no owner input is needed for these two read-only capabilities.

FW2-009/010 and FW2-020/A15 are scoped workbench progress. Arbitrary template
parameters, local CAD for the other source groups, part Add/Replace/Connect, draft resolution,
mechanism motion, full recovery-packing/electrical diagrams and detailed
manufacturing readiness are not delivered by this slice. Installed fin strength,
total movement, recovery, thermal and flutter acceptance stay open. D1 loads,
1mm movement, separate50g/20g and55/68g harness probes and15/15.5m/s guide criteria
remain unchanged. No purchase, physical test, paid run, WO-10 or flight release.
