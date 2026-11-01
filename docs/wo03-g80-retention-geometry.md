# G80 retention geometry: nominal fit corrected; capture/access open

The **original** proposed forward washer/nut capture did not fit its nominal
geometry. Its single CAD child stopped at the first conflict gate:
each of the three nominal 9 mm washers intersects the modified mount by
**1.098419 mm³**. No capture, assembly or strength acceptance follows. There was
no automatic retry or cap increase. The separately recorded primary input replan
below clears screened nominal overlaps but leaves capture and access open.

The source was the frozen 52-part integrated G80 candidate
`62e8de9eae802300bd36e5bdfbd08c8d20635d138972bb07708f574103ed7009`.
The study configuration is [wo03-g80-retention-geometry.yaml](../configs/studies/wo03-g80-retention-geometry.yaml)
and the source recipe is [wo03_g80_retention_geometry.py](../scripts/wo03_g80_retention_geometry.py).
The machine-readable [stop record](../build/wo03-g80-retention-geometry-v1/progress.json)
and [execution status](../build/wo03-g80-retention-geometry-v1/execution-status.json)
are local ignored build artifacts, not publication source. The active candidate,
preview assets, and core CAD generators were not modified.

## Exact nominal test and finding

The frozen hardware study supplied the candidate Accu M3 × 35 screw,
5.5 mm across-flats nut, and **9.0 mm OD × 3.2 mm bore × 0.9 mm** washer. The
previous 8.2 mm relief width was corrected to **9.6 mm** before the single
attempt. That gives 0.3 mm nominal tangential clearance on each side for a
centered 9.0 mm washer; washer OD tolerance is unavailable, so a minimum or
manufacturing-tolerance pass is not established.

The source bore axes are at radius 25.5 mm, so the washer reaches inward to
**R21.0 mm**. The proposed radial-open ring relief still begins at **R21.5 mm**.
Those dimensions imply a 0.5 mm nominal radial intrusion at the washer's inner
edge; this explains the observed overlap and identifies a specific candidate
for further investigation. It is a geometric inference from the specified
positions and the recorded intersection, not a separately isolated Boolean
measurement of the contact region. Moving the relief start could reduce the
remaining ring ligament and must be evaluated as a new design proposal; no such
change or follow-up CAD was made here.

The known Boolean fixture produced the specified positive overlap and separated
gap before the attempt proceeded. The eight imported source STEP solids were
checked for validity and volume consistency with source CAD properties. The
bridge was a single valid BRep, and the modified mount, three separate guide
blocks and individual hardware envelopes were valid as solids. That validity
does not establish their mutual fit. The script constructed a separate bridge,
six nominal tabs, shortened block guides, reliefs and hardware envelopes; it
retained source motor, liner, fins, shell and cap locations. The study does not
regenerate the full vehicle or qualify individual ring/rail bonded joints.

The conflict stop occurred before washer-bearing probes, sampled nut/washer
access, mass reconciliation or final STEP export. Therefore those results are
**unavailable**, not zero or pass. An anti-rotation keeper was not modeled;
its access, geometry, retention and mass remain unknown. The available records
do not establish nozzle clearance or a manufacturing-tolerance stack.

## Mass and other limits

The supplier's nominal average mass for three complete proposed fastener stacks
is **8.52 g**, excluding a keeper; no bound is available. The existing **7 g**
hardware allowance is unitemized, so the incremental replacement mass is
**unavailable**. The two are not treated as two installed screw sets. Retain
the separate **50 g growth allowance**, **12 g finish allowance** and
**4.620 g annular upper mass budget**. No replacement bridge/guide mass or
updated mass, CG or inertia is claimed because the attempt stopped before its
mass report.

One child was launched with a 120 s wall limit and a 600 CPU s packet budget;
none timed out and no extra child was launched in the original attempt. The OCCT pool was requested at
one worker and the process environment requested single-thread libraries; OS
affinity was not set. The post-attempt source hashes and an exact copy of the
executed script are retained in `failure-provenance.json` and `executed.py`.
Because the child stopped at the conflict gate before its final provenance
write, before/after source-hash equality was **not recorded**. The new script
passes Ruff and Black checks.

This is an isolated nominal geometry result. Washer tolerance, screw length and
engagement, nut retention, tool access, bridge/rail bonds, shell load path,
thermal and structural qualification, physical tests and flight release remain
open. No FEA, thermal calculation or flight simulation was run.

## One authorized input replan: nominal clearance improves, access remains blocked

The primary authorized exactly one input-layout replan after the stopped attempt.
The original script, configuration, stop record and status were copied before
editing into the local `build/wo03-g80-retention-geometry-replan-v1/failed-attempt-snapshot/`.
The revised relief starts at **R20.7 mm**, ends at R34.5 mm, and retains the
9.6 mm nominal width. The nominal 9 mm washer reaches inward to R21.0 mm, so
the nominal radial margin is 0.3 mm. The idealized remaining inner plywood
ligament is **4.9 mm** (20.7−15.8), before adjacent geometry and tolerances;
this is not a stress or strength pass. Missing washer OD tolerance still prevents
a minimum-clearance acceptance claim.

Before the kernel child, the study checked the complete nominal extents at all
three unchanged axes: washer R21.0–30.0 mm, z169.2–170.1 mm; nut bounding radius
R22.325–28.675 mm, z166.8–169.2 mm; and the shank's ring segment R24–27 mm,
z167–170 mm, within the relief R20.7–34.5 mm, 9.6 mm width, z166.1–170.1 mm.
The full shank spans z162–197 mm and its head z197–200 mm. The nominal 3 mm
shank is smaller than the 3.2 mm washer bore and 3.4 mm component bores. These
are nominal extents, not a tolerance proof or a demonstrated installation path.
All axial distances are local to the mount's 1.010 m station.

The single reconstruction's known overlap/gap fixture passed, its source solids
passed validity and saved-volume checks, and its newly made bridge and separate
components were valid BReps. No positive-volume intersections above 0.05 mm³
were found among the screened candidate/reference pairs. Three nominal washer
bearing probes on the bridge each measured **54.538 mm²**, using a 0.001 mm
surface-probe thickness. The result is a numerical geometric area, not evidence
of washer seating, load distribution or capacity. The tab-to-rail bond area and
joint load transfer were not measured by this run; no finite bonded interface,
ring/rail joint qualification or full-vehicle regenerated CAD is claimed.

The sampled radial removal path for each nut/washer pair, with the aft shell
installed, encountered **the aft shell**. Samples were spaced 1 mm along a
straight radial path; the result shows this particular path is blocked, not that
all possible assembly sequences are impossible. No keeper was modeled. Thus
positive capture, anti-rotation, access and service remain unresolved, despite
the nominal interference screen and washer probes. The STEP study assembly
contains the checked candidate and reference solids in the mount-local frame;
it is **not** an exported complete vehicle or a new active specification.

The geometry-derived plywood mount plus separate guide blocks is **44.5075 g**
versus **45.4623 g** for the source mount, and the bridge is **10.2190 g**, at
unchanged estimated densities. Three candidate fastener stacks are separately
listed at the supplier nominal **8.52 g**; the source 7 g hardware allowance is
unitemized, so the replacement increment and keeper mass remain unavailable.
Do not sum the two as two physical installed sets. The 50 g growth allowance,
12 g finish and 4.620 g annular upper budget remain separate. No total candidate
mass, CG, inertia, adhesive sufficiency or flight result is established.

The [replan record](../build/wo03-g80-retention-geometry-replan-v1/record.json),
[study STEP](../build/wo03-g80-retention-geometry-replan-v1/study-assembly.step),
[preflight](../build/wo03-g80-retention-geometry-replan-v1/preflight.json), and
[execution status](../build/wo03-g80-retention-geometry-replan-v1/execution-status.json)
are local ignored build artifacts. The child was subject to both a 120 s wall
cap and 120 CPU s hard cap. Parent-observed wall was **6.31 s** and child CPU
**5.40 s**, with before/after input hashes matching. OCCT pool one and single
thread library environment were requested; affinity was not set. The initial
failed child's CPU usage was not recorded, so aggregate packet CPU is unknown,
not zero. No third attempt, FEA, heat or flight work was performed. The current
source script passes Ruff and Black.

[Published compact attempt evidence](../runs/wo03-g80-retention-20261101T060234513931Z/record.json) preserves the original stop, exact source snapshots, replan and resource limitations. Partial CAD remains local; no capture, tolerance or complete-vehicle acceptance follows.
