# Current engineering and inspection checkpoint

**Current recovery decision: [RP1 precedent recommendation](wo03-f2-recovery-precedent-decision.md).**
Carry a motor-tube wrap with a replaceable nylon main forward for definition;
keep the conventional F2 architecture and all earlier records frozen. This is
a research recommendation, not adoption. The single balance correction removes
redundant ballast-only parts and shortens the leader while preserving its route.
Selected balanced-v2 nominal/adverse estimates are931.149/951.149g including
full50g, CG763.302/775.261mm, margins1.439/1.260cal (1.149withaftcordstowage).
Reference1.5m departure15.243988/15.063562m/s passes15; formal headroom27.194/7.194g,
planning deficits27.350/47.350g. Conditional1.8m equipment remains unconfirmed.
Main nylon55g is an estimate; adverse formal maximum62.194g with other budgets
fixed. No growth use, reduced recovery case or detailed FEA is admitted.

The source study compares three kit families/four documented constructions.
The loop removes the proposed body-eye dependency, but moving the ring ahead of
tabs removes their old front support. Finished cord/knots, finite ring/tube/body
and revised root joints, heat and service remain open. [Current drawings](../output/f2-recovery-precedents-balanced/index.html)
are versioned concepts with actual offline images, separate from complete CAD.

The first inspection-slice correction is merged PR70: scroll/content height,
reachable details/search, source isolation, active2D shortcuts and section picking.
Integrated71 web tests/typecheck/lint/format/build and required hosted jobs pass; browser ownership remains
blocked with no exposed supported repair command. [Handoff](wo04-inspection-slice-20261103-v3.md).

[Read-only asset readiness](wo04-inspection-asset-readiness-20261103.md) confirms
source-matching listed mesh inventories: referenceG80 42/42, G54 42/42, finnedG12
53/53 and finlessG12 51/51. These are the older reference designs, not F2/RP1 CAD.
Current mesh bytes were fingerprinted; no independent expected GLB-byte hashes
or browser/WebGL acceptance is claimed. Supplier questions for the unpurchased
nylon/Kevlar are [prepared but unsent](wo03-f2-recovery-supplier-questions.md).

The F2-C2 joint-demand declaration below was superseded before arithmetic. RP1's
new small arithmetic had one preserved ledger-export failure and one declared
setup correction; no stopped F2/C1 solver was repeated. Hardware is unpurchased.

**Previous connection decision: [G80-F2-C1](wo03-g80-f2-c1-decision.md), not adopted.**
Frozen F2 remains the working reference below. The new proposal defines seven
conditional fit stacks and adds1.190g epoxy with zero wood-removal credit.
Nominal/adverse918.750/938.750g, static1.283/1.105cal, reference1.5m
15.359/15.175m/s. Formal speed passes; planning misses. No longer rail adopted.

The critical recovery pull **opens the blind-notch floor gap**, leaving adhesive
tension/side shear as the load route. Finished eyes, actual body/tab/mount support,
peel/wood strength and motor contact remain unresolved. Two numerical grids are
valid; the fine mesh and one defined replan stopped at the unchanged node cap
(last139953>100000). Required3-grid convergence is unavailable; no further retry.

[Verification supplement](../configs/engineering/g80-f2-c1-verification.yaml)
keeps existing requirement IDs and independent G54/G12 tracks. CurrentF2-C1
geometry remains a proposal; its generators are explicitly unadmitted and the
old32.3mm ring fields do not apply to new32.2mm geometry. No prototype/flight gate
or installed strength/thermal requirement closes.

Inspection refinement [PR68](https://github.com/kudratsingh/rocket-twin/pull/68)
is merged; both required jobs passed at `798d20ae722549f90648f5a2d709066156630c0b`.
The new [connection-study handoff](wo04-f2-c1-walkthrough-20261103.md) records
separate source-linked graphics, a dimensioned section, the complete coupled
table and offline image observations. Open
`http://127.0.0.1:5173/?workspace=engineering&view=g80-f2-c1` after `make preview`.
The study is not a new flight configuration or a compatible stress overlay.
Browser runtime ownership remains unresolved; read-only host diagnostics do not
bypass it. The owner subsequently confirmed that none of the exact motor,
mount tube, retainer or recovery-anchor hardware has been purchased. Do not ask
for measurements of unavailable hardware; missing mating data remains a supplier
dependency. Components remain budgeted purchases; none is authorized here.

**Current selected G80 follow-up: G80-F2-fixed-stock-ballast-v2.**
[Construction decision](wo03-g80-f2-decision.md) and
[exact-once coupled audit](wo03-g80-f2-coupled-accounting.md).
Actual-stock body splice, blind fin notches and compact retained-nose package
replace F1's unresolved stock/interference layout. F1 remains frozen history.

| Selected case (full separate 50 g included) | Mass | CG from nose | Static margin | Reference 1.5 m speed | Formal / planning mass headroom |
| --- | ---: | ---: | ---: | ---: | ---: |
| Nominal |917.560 g |773.559 mm |1.286 cal |15.370 m/s |+40.784 / -13.761 g |
| Additional 20 g aft + motor-balance probe |937.560 g |785.473 mm |1.107 cal |15.186 m/s |+20.784 / -33.761 g |

The formal 15 m/s and calculated 1-calibre screens pass within the declared
hypothesis; **both cases miss the separate 15.5 m/s planning target**. No longer
equipment is confirmed or adopted. Costs are $458.71 before unquoted shipping/tax;
recovery electronics are budgeted purchases, not assumed owner stock.

**Not admitted for prototype fabrication or flight.** Installed recovery/fin
joints, exact G80/retainer contact, thermal matrix, hot/wet properties and
installed flutter remain open. The local fin/ring CAD has zero solid overlap;
this closes that nominal geometry defect only. The ring diagnostic is stopped:
one inverted element in the middle mesh prevents a three-grid convergence or
strength claim. No retry/new solver or automatic construction revision follows.

New separate walkthrough: `make preview`, then
`http://127.0.0.1:5173/?workspace=engineering&view=g80-f2`.
[Offline drawings](../output/engineering-g80-f2/index.html) include arrangement,
splice/fin/nose layers, recovery branches and signed mass changes. Whole-vehicle
CAD and compatible stress/temperature fields remain unavailable. Offline images
and source/API checks are distinct from pending browser verification.

G80 first, custom fabrication and practical performance remain core goals;
G54 upgrade and G12 PID-to-RL keep their separate committed requirements.

## Frontend delivery checkpoint

The owner-supplied43-task kit is now tracked in
[the backlog](frontend-workbench-backlog.md), with focused workspaces under
[ADR0014](adr/0014-focused-engineering-workspaces.md). Astra MEDIUM implemented
shell/source isolation and linked2D; Terra HIGH delivered camera controls,
replay status and a four-sample saved-record audit. Primary integrated shared
routes/state. [Current usable-code handoff](wo04-focused-preview-20261103.md)
records exact pages, startup and pending browser tests.

F2 engineering PR66 merged after both required jobs passed at55599a2370962f195dea31faee49fb825c7646fe.
Inspection refinement PR68 is merged as recorded above. Launcher preparation
passes, but Vite cannot bind127.0.0.1:5173 in the sandbox (`listen EPERM`).
No live app or browser acceptance is claimed. The original designated-browser
ownership rejection remains unresolved and was not retried/bypassed.

## Historical checkpoints below

**Active follow-up: G80-F2**, [bounded packet](wo03-g80-f2-packet.md). Keep F1 frozen. Use obtainable stock, one fixed bonded splice, connected recovery/fin joints and coupled forward-placement/ballast comparison. G54/G12 remain separate; no new platform architecture. F1 numbers below are historical input, not F2 results.

**G80-F1 dedicated fixed conventional rocket is the delivery direction.**
[Current decision and complete budget](wo03-g80-f1-decision.md),
[bounded packet](wo03-g80-fixed-packet.md), [ADR-0013](adr/0013-dedicated-conventional-g80.md).
Physical interchangeability is optional; no future gimbal/servo hardware in G80.
G54 upgrade and G12/PID-to-RL remain committed separate tracks.

One correction finished: continuous body1060mm,1250mm overall, fixed TTW fins,
fixed paper motor mount and laminated forward ring. Nominal/adverse totals
**817.506/837.506g including separate full50g**, reference1.5m departure
**16.388/16.170m/s**. Both guide thresholds pass, but static margins
**.743/.556cal fail1.0**. The severe recovery ring strip still fails; actual
motor/retainer fit, installed root stiffness/flutter, hot/wet properties and
thermal matrix remain unresolved. A matching one-piece1060mm tube is not sourced; LOC stock is shorter with different bore/OD. **Not admitted to detailed vehicle CAD or
manufacture; no installed engineering requirement closes.** No third revision
or failed/stopped old campaign was started.

The new source-linked graphical snapshot is separate from old C1/A1 assemblies:
`make preview`, then `http://127.0.0.1:5173/?workspace=engineering&view=g80-fixed`.
It shows the42-row concept/envelope ledger, fixed construction/assembly,
recovery/motor/fin routes and failed current/first geometry comparisons. It is
not manufacturing-ready CAD. Backend GETs display saved calculations only.
Offline images and browser interaction acceptance are separately recorded in
[the walkthrough note](wo04-conventional-g80-walkthrough.md).

## Frozen historical checkpoints


**Current priority: G80-F1 dedicated conventional rocket**, under
[ADR-0013](adr/0013-dedicated-conventional-g80.md) and the
[bounded simplification packet](wo03-g80-fixed-packet.md). Physical aft/upper
interchangeability is optional. One fixed paper/plywood architecture is selected;
no G80 control/gimbal provisions. A2 intake stopped before numerical execution.
The A1 and earlier results below are historical, not the design to refine now.

**Current A1 decision: hold detailed admission.** The [connection report](wo03-a1-connection-decision.md)
includes a new [seat/liner occupancy failure](wo03-a1-occupancy-audit.md): proposed
seatz1193–1195 overlaps retained mica/foil ending1200. No automatic trim or move.
The remainder of the report
defines a sleeve, stop, keys, bolts, actual upper bond and routed harness. Bounded
aft clearance0.1171mm passes0.1 only within unmeasured inputs. Full added
hardware/mass is+106.454g versus frozen A:1074.762/1094.762g including separate50g.
Reference1.5m departure14.059/13.912m/s fails; adverse formal/planning deficits
136.364/190.908g. A conservative one-bolt combined demand463.661MPa exceeds
the existing200MPa hot-steel estimate. Paper/peel/bearing/thermal/flutter and
current motor/retainer remain unknown. No whole-vehicle CAD/FEA or next automatic
variant is admitted; no installed engineering requirement closed.

Published C1/A/B below remain frozen history. A1 is a separate snapshot and
changes no active or shared G54/G12 assembly. New external collar/head geometry
makes reused C1 CP/drag only reference hypotheses; full inertia/new CP unavailable.

The separate graphical A1 snapshot is now implemented at
`http://127.0.0.1:5173/?workspace=engineering&view=a1` after `make preview`.
[Offline A1 gallery](../output/engineering-a1-connection/index.html) provides
three actual inspected PNG/SVG drawings: sleeve/stop/key/harness/service and five
separate load paths; radial bolt stack/upper bond/root; and recorded fit, mass
addition and separate formal/planning deficit bars. These are
concept graphics, not CAD or browser screenshots. Current snapshot includes the
previously missing historical0mm fit finding; browser interaction stays blocked
by the designated-agent runtime-ownership prerequisite, with no retry/bypass.

**G80 first. C1 is preliminary. R1/C2/C3 remain rejected.** Substantial custom
construction, maximum practical performance and committed G12 PID-to-RL remain
core goals; G54 remains a separate upgrade. Expanded WO-03 and every build,
purchase, paid-run, firmware-review and flight-release gate stay open.

## Engineering decision

Prefer **A: integrated through-body motor/fin can** for a bounded connection
study; **neither A nor B is admitted to detailed vehicle CAD/FEA**. Both are
separate concept studies, not changes to C1 or the active vehicle.

| Complete case, separate50 g included | Mass | Balance from nose | Stability |1.5 m departure |1.8 m conditional departure |
| --- | ---: | ---: | ---: | ---: | ---: |
| A nominal |968.309 g |844.352 mm |1.856 cal |14.914 m/s |16.341 m/s |
| A additional20g/motor-CG |988.309 g |853.756 mm |1.713 cal |14.743 m/s |16.155 m/s |
| B nominal |995.812 g |852.518 mm |1.732 cal |14.680 m/s |16.086 m/s |
| B additional20g/motor-CG |1015.812 g |861.506 mm |1.596 cal |14.516 m/s |15.907 m/s |

A saves161.498 g from C1 but still needs29.911 g additional saving for the
adverse **formal15 m/s** case on the unchanged1.5 m guide. Separate15.5 planning
needs84.455 g. Longer usable travel remains unconfirmed and conditional.
The retained-upper interface audit also fails the proposed A/B cold-fit stack:
64.0mm model coupler /64.4mm bore gives0mm worst-case radial clearance under
the declared bounds, versus0.1mm required. [Audit](wo03-architecture-interface-audit.md)
records the issue without resizing a part or changing frozen mass results.
The other controlling items are finished hot root/recovery joints, finite
cap/body load spreading, exact G80/retainer fit, heat and installed stiffness.
Full rotational inertia is unavailable. **No installed engineering requirement
closed.** The two-arrangement study is complete and stopped at admission.

- [Decision and complete mass/margin evidence](wo03-architecture-decision.md)
- [Actual function allocation and A/B concept drawings](wo03-architecture-function-allocation.md)
- [Primary-source and later owner-only measurement plan](wo03-architecture-source-packet.md)
- [Unsent ROC/MDARS equipment questions](wo03-launch-owner-confirmation-20261102.md)
- [Bounded work list and responsibilities](wo03-current-worklist.md)

## Open the inspection workbench

Run `make preview` at the repository root, then open:

`http://127.0.0.1:5173/?workspace=engineering`

The preserved arrangement/section/force/mass views now have companion graphical
views selected with `&view=comparison`, `recovery`, `thermal`, `electrical`,
`assembly` or `requirements`. They display versioned backend data and link
selection to the current C1 inspector when a valid part mapping exists.
New A/B concepts have no fabricated C1 part/CAD association.

| Local artifact | What can be inspected |
| --- | --- |
| `output/rocket-twin-review/index.html` and `review-pack.zip` |Self-contained gallery and downloadable pack of recorded drawings/native images |
| `output/engineering-walkthrough/index.html` |25 C1/R1 SVG drawings with units, source/status and configuration metadata |
| `output/engineering-walkthrough-rendered/contact-sheet.png` |25 real offline raster pages; representative labels/arrows actually inspected |
| `output/engineering-workbench-extended/index.html` |New comparison/recovery/thermal/electrical/service/requirement SVGs and actual PNG previews |
| `output/wo03-architecture/architecture-A-motor-fin-can.png` |Dimensioned A concept and protected volumes, not detailed CAD |
| `output/wo03-architecture/architecture-B-outer-captured-roots.png` |Dimensioned B concept and unresolved connections |

The135 C1 source allocation/envelope rows are not a manufacturing-ready CAD
assembly. Archived72-part CAD remains separate. Recorded thermal histories
and failed fixtures stay historical/incompatible with current C1; absent spatial
fields/time samples/pins/inertia stay unavailable. Deployment/service storyboards
are illustrations, not validated mechanism/deployment simulations.

Offline image rendering now works with the installed documented AppKit
image-document API. Actual image inspection identified and corrected exported
arrowhead portability; no browser/window or dependency installation was used.
Raster images do **not** prove browser interactions or frame rate. Host URL
reachability, clicks/downloads, responsive layout and WebGL remain pending the
designated browser agent's runtime-ownership prerequisite. The last automatic
approval rejection is not retried or bypassed.
