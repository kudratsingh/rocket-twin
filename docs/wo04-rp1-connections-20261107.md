# RP1 parts, connections and replay-pose evidence — RV-08 / RV-11

This increment keeps `G80-F2-RP1-AD1-definition-v2` as the current 55-part
source/drawing design. It adds read-only inspection of existing evidence. It
changes no vehicle, material, load, mass, recovery, control or launch requirement.
All five supplier/lab inquiry drafts remain UNSENT. No reply is needed for this
frontend work. G80 custom construction remains first, with G54 and G12 PID-to-RL
as separate committed tracks.

## Open the two Engineering examples

```sh
cd /Users/kudratsingh/Machine-Learning-Projects/rocket-twin
make workbench-rp1-connections
make preview
```

Start at `http://127.0.0.1:5173/?workspace=design&design=G80-F2-RP1-AD1-definition-v2`.
Select **fin tabs** or **RP1 Kevlar wrap**, then use **Open matching Engineering
connections and findings** in Details. Engineering also opens directly at
`http://127.0.0.1:5173/?workspace=engineering&view=rp1-connections`.
The source revision, part and selected connection are retained in generated URLs;
**Inspect this exact AD1 part in Design** returns to its source selection. Native
links support reload, new-tab and ordinary history behavior. Their browser behavior
still needs observation.

The **fin-root** graphic shows the panel/tab and parallel internal-bond,
external-fillet/wedge, motor-tube, ring and paper-body routes. It does not prescribe
equal load sharing or rigid supports. The saved optimistic fin-screen failure
(7.301 MPa / 1.805 mm) stays separate from the installed attachment's UNKNOWN
strength, compliance, peel and flutter evidence. D1 retains 8.83 N·m / 331.125 N,
with the factor of three already applied once and the 1 mm movement limit.

The **recovery** graphic shows the canopy/junction, nylon, leader, tube wrap,
local ring/mount contacts, body and separate nose branch. Finished knots, loops,
contact pressure and force partition remain unverified. Dimensions and contact
notes come from AD1 v2; station pairs are not mislabeled as rectangular sizes.
Both examples show named sources and hashes, status, units and the later
measurement or test that could resolve each unknown. Raw cord ratings do not
establish finished attachment capacity.

All 55 stable part IDs are recognized. A part outside these two connection
mappings has **Connection evidence unavailable**; no relationship or historical
result is invented. Archived G80 drawings stay in their historical topics.
Missing or mismatched design/specification/CAD/part identities fail explicitly.
Four saved source SVGs are hash-checked by the backend before serving the same
verified bytes. A missing/altered source cannot silently use another drawing.

## Replay validation

[RV-11 independent reference and report](studies/replay-pose-20261107/report.md)
compare the actual production pose helper with independently calculated scalar
quaternion/matrix results from saved run
`exp-cf9e47a650074144856caf50775846d2`. The archived
`modular-performance-v1` CAD is used only with matching run/specification/CAD
identities. RP1 has no matching complete CAD/inertia/run and receives no borrowed
flight actor or performance claim.

At T+11.150 s, the recorded rocket points approximately **4.076° from straight up**
while descending **5.456 m/s**. These facts coexist. The recovery attitude is
approximate: canopy/line and suspended-body dynamics are absent. The viewer does
not rotate the rocket to match its velocity. Valid position plus invalid attitude
or centre of gravity produces a labeled position marker. Invalid position or time
outside either run's recorded interval produces no actor.

Position/axis conversion, centre-of-gravity pivot, interpolation, quaternion sign
equivalence, event brackets, invalid input and unequal run windows have automated
checks. The optional gap threshold has no recorded production requirement and is
not silently imposed. One bounded saved-data read completed in 0.240 CPU / 0.350
wall seconds; no simulation or stopped solver was rerun.

## Evidence and remaining acceptance

Local checks: 133 frontend tests (zero skips), TypeScript/packaged build, ESLint and formatting pass; 12 new source/API tests, Ruff and Black pass. The existing chunk-size warning remains. Repository evidence covers source/hash checks, both actual React graph exports,
part-link round trips and rejection cases, API payload/drawing bytes, independent
pose arithmetic and the packaged frontend checks. These do not establish rendered
pixels, image loading, clicks, history restoration or Three.js actor/camera behavior.
The revamp ledger keeps RV-08/RV-11 **partial**, browserObserved false and accepted
false. Hosted checks must pass at each exact PR head before merge.

The supported browser path remains the original designated Terra owner and the
Chrome window containing Atlas Fibre G11. Its runtime-ownership prerequisite is
unresolved. No alternate window, browser, headless/CDP path or native-rendering
retry was used. Pending browser checks: Design → connection → Design selection,
Back/Forward/reload, keyboard node selection, graph readability, saved SVG loading
and error states, exact-event replay, invalid-attitude marker and unequal-window
actor/camera visibility. No new owner engineering decision is needed for this code
increment; browser acceptance needs that supported ownership handoff.

`make workbench-rp1-connections` generates
`output/rp1-connections-20261107/index.html`, two actual React HTML exports,
two relationship SVGs, four pinned saved SVGs and a hash manifest. These are
portable source artifacts, **not screenshots**. Their selection buttons are inert;
links and source drawings can be inspected independently. Generated bulk stays
excluded from Git; the source exporter reproduces it. Startup commands identify
normal host endpoints, not a claim that this sandbox opened a listening server.

Later authorized owner measurements could establish stock thickness, the actual
cord/knot envelope, slot/liner/retainer dimensions and finished masses. Installed
joint movement/capacity, hot behavior and flutter require their defined tests;
a dimension measurement alone cannot close them. WO-03/04/05 acceptance, prototype
build authorization and flight release remain separate and open.
