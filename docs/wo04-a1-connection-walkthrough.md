# Separate A1 upper connection workbench snapshot

The A1 view is an independent, versioned concept snapshot for the bounded
upper-connection study. It is available at `?workspace=engineering&view=a1` after
`make preview`. It does not revise the frozen C1 walkthrough, A/B screen, original
3D viewer, experiments or replay. Its separate API route is
`/api/engineering/workbench-a1`; only a 404 route absence permits the visibly
labelled prepared `web/public/engineering-workbench/g80-a1.json` fallback.
Other API/source errors stay visible errors.

The [declared A1 packet](wo03-a1-connection-packet.md), [frozen-A ledger
audit](wo03-a1-ledger-audit.md), [A1 source review](wo03-a1-connection-sources.md)
and [executed A1 record](../runs/wo03-a1-connections-20261102-v1/record.json)
supply the content. A drawing does not turn their
estimated geometry and source typical properties into a qualified installation.

The overview drawing shows the intended upper sleeve, axial stop, orientation
index and positive-retention provision, plus protected motor removal and harness
routes. The companion detail shows the nine-layer radial M5 stack, bonded upper
lap and proposed fin-root force interfaces.
It is **schematic and not to scale**. The axial/end drawing and path arrows are
presentation symbols, not an A1 CAD model or a spatial stress field. Numeric
dimensions, fit and mass values come only from the snapshot; null renders as
`Unavailable`. The table carries each recorded source and evidence state.
The former A/B coupler audit remains a separately labelled historical failure:
0 mm worst-case cold radial gap against 0.1 mm required. A1 cannot inherit a
pass from nominal A/B fit or from a drawn sleeve.

The A1 data contract is `web/src/workbench/a1Types.ts`. It requires source
identity, frame/units, `cad_revision: null`, source references and hashes, geometry
scalars, stationed/radial feature rows, fit rows, fin/recovery/motor/upper path
sequences, protected volumes, full mass-delta status, complete recorded cases
and open findings. The new A1 tab has no C1 part or detailed
CAD mapping. It hides the frozen C1 part/inspector sidebars while A1 is selected.

Run `node scripts/wo04_export_a1_drawings.mjs` after preparing the A1 JSON to
save the actual React schematics as standalone SVGs and render PNGs through
the installed AppKit image-document helper. The exporter checks every listed
local source hash. Its output and sidecar are under
`output/engineering-a1-connection/`, with a disposable execution record under
`build/wo04-a1-drawings/`. Both SVGs can be downloaded from the live view
with identity and source metadata. Offline SVG/PNG inspection is separate from
browser interaction evidence; the designated browser ownership restriction
still applies.

## Executed A1 snapshot and image review

The prepared data is `web/public/engineering-workbench/g80-a1.json`, SHA-256
`1dbab9cb2d8c010d680a379e647998337ea3b0139357a81d75abaa9e6ac6a128`.
The [offline gallery](../output/engineering-a1-connection/index.html) contains
the three actual React SVGs, their native PNGs and source sidecars. The earlier
[v3 archived image record](../runs/wo04-a1-drawings-20261102-v3/record.json)
and [source manifest](../runs/wo04-a1-drawings-20261102-v3/archive-manifest.json)
preserve the executed React/types/CSS/exporter and prepared JSON identities;
PNG bulk stays in `output/`. The v3 record reports a **1.205 s** two-image
native batch. The archived v1, bounded v2 and v3 native batches total **4.784 s**
of measured rendering, below the 120 s cap; the earlier initial preview is
recorded separately without a precise native duration. An initial overview image showed
force-path labels touching first nodes and a harness callout that wrongly said
radius unavailable; the focused correction separated the labels and identified
the recorded R21 mm route-centre radius. The [v1 archive](../runs/wo04-a1-drawings-20261102-v1/record.json)
preserves that earlier drawing and source state. Primary inspection then found
that the detail wrongly implied a finished joint and treated a mean normal
force/area scalar as a local peel result; all route nodes were abbreviated.
V2 labels the root **proposed**, calls 0.9145 MPa a **mean normal demand**, and
states local peel is unavailable. Its first wrapped SVG used `<tspan>` elements,
which AppKit ignored; the recorded failed PNG hashes remain in v2 while the
final drawing uses separately positioned `<text>` lines. Both final
1080-pixel-wide PNGs were opened and inspected: source station/radius labels,
three index and retention symbols, the then-four full arrowed force paths, all nine
radial stack layers, upper lap and root dimensions are legible. The
intentionally shortened detail-stop sentence has
its full wording in the JSON and live text. Vite SSR logged a sandbox WebSocket
`EPERM` warning, but SSR and both AppKit images completed; the warning is kept
in the record. This is offline evidence only.

The [v2 archive](../runs/wo04-a1-drawings-20261102-v2/record.json) is also
preserved. A final source-topology correction separated forward motor thrust
from reverse motor retention: the v3 prepared JSON differs from v2 only in
`paths`, expanding four routes to five. The 1080 × 1180 overview PNG was
opened and inspected after that change. It shows all five routes and all 20
full node labels in distinct readable rows. No A1 numerical calculation was
rerun; the separate motor cases remain recorded demand paths, not installed
capacity or flight acceptance.

The final [v4 image record](../runs/wo04-a1-drawings-20261102-v4/record.json)
and [source manifest](../runs/wo04-a1-drawings-20261102-v4/archive-manifest.json)
add a third source-fed SVG/PNG for graphical fit and complete mass screens.
Actual PNG inspection found the historic A/B 0 mm and new A1 0.1171 mm
minimum gaps, the textual 0.1 mm criterion, recorded +106.454 g delta from
frozen A, 1074.762/1094.762 g complete cases, and separate formal 15/planning
15.5 negative headroom bars for both cases legible. The full 50 g remains
included in both case totals; the additional 20 g/motor-CG case stays separate.
Bars normalize recorded values for display and compute no mass limit or physics.
The first v4 preview shortened adverse labels before the formal/planning
distinction; the final image places that distinction first. The previous two
SVG graphic bodies and PNG hashes match v3 exactly. The final three-image
native batch took **1.877 s**, with **8.398 s** total measured across the saved
v1–v4 batches, below the 120 s cap. Earlier archives remain intact. Browser
interactions remain unverified.

The screen preserves the historic A/B 0 mm cold-gap failure. A1's **calculated
bounded** sleeve/can minimum is 0.1171 mm versus the 0.1 mm screen; actual
manufacture and hot/wet qualification remain unavailable. The complete A1
nominal/adverse masses include separate 50 g and are 1074.762/1094.762 g;
the saved reference guide model gives 14.059/13.912 m/s at the unchanged
1.5 m usable baseline, below formal 15 m/s. Its 15.5 m/s planning check is
separate. The conservative combined bolt hand screen is 463.661 MPa against
an estimated 200 MPa hot-steel value, so it fails. Root normal/peel, paper
wall and hot installed capacities remain unqualified. The 0.9145 MPa scalar
is mean normal demand from force divided by root edge area; no local peel
solution or allowable is supplied. External collar and bolt
heads change the aerodynamic envelope; displayed C1 CP and margin are explicit
reference hypotheses, never a validated A1 stability pass.

Open evidence: source and manufactured tolerance, hot/moisture fit, finite
coupler/stop/index/retention load transfer, proposed fin and recovery joints,
motor/retainer exact identity, service/installation sweeps, measured mass and
revalidated aerodynamic model, structural/thermal limits and unchanged launch/flight
criteria. No A1 geometry, capacity, mass delta or active configuration is
admitted merely by this view.
