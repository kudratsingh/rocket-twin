# A/B architecture function allocation and concept drawings

**Both arrangements remain not admitted.** The one executed
[A/B packet](../runs/wo03-architecture-space-mass-20261102-v1/record.json)
selects A as the preferred **bounded joint-demand direction only**, not detailed
CAD, an accepted construction or a new active configuration. The
[configuration](../configs/studies/wo03-architecture-space-mass.yaml) owns the
dimensions; the drawings replay its concept envelopes and recorded values.

The presentation generator is
[`wo03_architecture_drawings.py`](../scripts/wo03_architecture_drawings.py).
It imports no engineering execution module and launches no physics, CAD, FEA,
thermal or flight calculation. Its unit scaling, coordinates and tabular
formatting are display operations. Source and output SHA-256 identities are in
the [drawing record](../runs/wo03-architecture-drawings-20261102-v1/record.json).

| Arrangement | Dimensioned vector drawing | Native raster preview |
| --- | --- | --- |
| A — integrated motor-fin can | [A SVG](../output/wo03-architecture/architecture-A-motor-fin-can.svg) | [A PNG](../output/wo03-architecture/architecture-A-motor-fin-can.png) |
| B — captured outer roots | [B SVG](../output/wo03-architecture/architecture-B-outer-captured-roots.svg) | [B PNG](../output/wo03-architecture/architecture-B-outer-captured-roots.png) |

Each drawing carries nose origin, station direction, units, exact config/record
hashes and not-admitted status. The displayed section is the aft region,
z900–1227 mm, not a complete detailed rocket. The external panel continues
outside the cut and is deliberately omitted; one representative fin root is
shown. Hatching identifies reserved service volumes, not material or a result
field. Four separate connection chains explain fin, motor, recovery and
contact/bond transfer. Their arrows are schematic, without spatial stress,
thermal contours, computed motion or equal-sharing implications.

## What replaces the old functions

Both records remove the **same83 identified source part/allocation rows**,
gross561.440696 g. The immutable `removed_part_ids` and signed
`replacement_ledger` preserve every original ID, station, basis and mass.
The grouped mapping below explains their replacements; it grants no extra
removal credit beyond that record.

| Replaced source rows / functions | New charged functions in both arrangements, unless noted |
| --- | --- |
| `aft_shell`, `C1_closed_G11_body_annulus` | `A/B_loadbearing_outer_can`, R32.2–33, z922–1212, replaces the paper aft shell plus old structural receiver/body support. Real fin slots remain; intact-tube torsion is only an optimistic reference. |
| `c1_fin_panels`, `fin_source_cad_residual`, three `fin_tab_depth_delta_*`, `fin_bonds` | Full `A/B_fin_*` sandwich ledger: dense root band and complete new tabs, core, panel/tab skins, face bonds, root-core butt bonds and sealing. Original CAD residual and old tab mass are removed once, not credited again. |
| Six C1 side plates, three floors/pads, six outer bridges, socket process/hardware allocation; source selected shims | A: root/tube and root/outer-can bonds, with explicit root/ring bond allocation. B: six100×7×3 cheeks, three100×9.5×1.5 floors, two full-circumference root diaphragms and3 g selected shims. Root-side capture and axial retention are distinct. |
| Source fin axial5 mm pin complete sets | New4 g root axial-pin/washer allocation; config proposes positive axialM2 capture. This is a changed, not qualified hardware detail. It is not credited as the entire fin-normal moment path. |
| C1 motor-key carriers; old front annulus/prongs/keys and three5 mm key-pin sets | Structural motor tube R15.8–17.2 at1069–1195 and two3 mm centering rings at1072/1192 replace the old cassette's forward structural transfer. The commercial thrust-ring/tube/adapter mating remains unverified; old key strength is not transferred. |
| C1 independent arms/keeper; aft hard stops, keeper/spring and locking allocation |20 g independent threaded-retainer reservation plus5 g adapter/bond and explicit service hardware. Recovery is not credited for motor retention. Exact hot mating, occupied dimensions and mass are unknown. |
| Old aft cap; fore cap/skirt; six end nodes; fore/aft M3 cap sets and end-contact shims | New6 mm fore recovery cap, integral40 mm cuff, actual cuff/body bond and service hardware redistribute the load into the new structural can. No old end-node, cap tension or body-joint capacity is inherited. |
| Six old fore/aft saddle lobes; three aft-running raw loops; keeper/chafe/stitch allocation | Three new integralR6 saddles and three **forward** bridle eyes to junction900, plus explicit chafe/stitch reserve. This relocates recovery introduction; finished sewing/bend capacity is unavailable. Retained body/nose branches still need actual terminations. |
| `adhesive_finish`, incremental gap epoxy, fore skirt epoxy and M2 spreader budget | Separate new root/ring bonds20 g, cap/cuff bond5 g, chafe/stitch6 g, thermal isolation6 g, finish/locks8 g and body/retainer service hardware6 g replace named process functions. Skin bonds and finish in the fin ledger remain separately charged. |

Motor, liner and shielding mass, independent recovery electronics/power, upper
body/nose connections and the remaining retained source rows stay in the full
ledger. There is no permission to delete a function because a source row was
removed. A adds399.942808 g; B adds427.446255 g, giving recorded net changes
−161.497888/−133.994441 g. These are complete preliminary allocations, not
measured installed masses or upper uncertainty bounds.

## Real geometric interfaces and finite joints

Both drawings reserve the same **R15.8 motor/liner volume at1069–1195** and
**R23 retainer/service volume at1195–1227**. The20 g retainer and its envelope
are **not manufacturer-verified**. Removing the threaded cap before the motor
is an intended service sequence, not a demonstrated extraction path.

Recovery legs occupy900–1016 at60/180/300°, r24 and t±6 in their own frames,
with actual12.7 radial ×0.55 tangential section. The drawing's transverse inset
shows the three real cuff windows at1010–1018, each±30° around those axes.
These are open volumes; they cannot simultaneously be solid shielding or
full-area adhesive. Gross cuff mass takes no window removal credit.

The6 mm fore cap at1004–1010 feeds the integral cuff R30.8–31.8 over1010–1050,
then the actual0.2–0.6 mm radial body lap. Finite cap spreading, windowed cuff,
ring flexure, bond peel, body/coupler stiffness and retained component joints
remain serial load paths, not ideal ground. The recorded minimum cap effective
spread111.229/114.325 mm is a **demand**; actual effective width is unavailable.
FinishedR6 saddles and50 mm sewn laps have no qualified capacity. No equal
loop, root or joint sharing is assumed.

For A, roots extend15.8 mm with support radii17.2/32.2 and100×12 mm effective
bond patches. Recorded0.684 MPa mean interface demand does not supply normal
peel capacity. For B,7 mm roots atR26–33 feed shallow sockets and3 mm rings
at1090/1190. Recorded8.155 MPa mean contact has no qualified hot bearing
allowable; it must not be compared to25 MPa as though that bending scalar
were a bearing capacity. A/B ideal panel/play/tube proxies0.882/1.226 mm
do not establish installed movement; B's optimistic proxy already exceeds1 mm.

## Recorded coupled cases — no acceptance implied

All totals retain full separate50 g. The adverse cases add another20 g and
the existing motor-CG probe. CP is966.827598 mm; full intrinsic inertia is null.

| Case | Total, g | Loaded / burnout CG, mm | Loaded / burnout margin, cal | Speed1.5 /1.8 /1.971 m, m/s | Severe recovery mean, N |
| --- | ---: | --- | --- | --- | ---: |
| A nominal |968.309 |844.352 /824.229 |1.856 /2.161 |14.914 /16.341 /17.103 |2043.345 |
| A adverse |988.309 |853.756 /833.838 |1.713 /2.015 |14.743 /16.155 /16.908 |2085.549 |
| B nominal |995.812 |852.518 /833.534 |1.732 /2.020 |14.680 /16.086 /16.837 |2101.383 |
| B adverse |1015.812 |861.506 /842.671 |1.596 /1.881 |14.516 /15.907 /16.650 |2143.587 |

Both still fail formal15 m/s on the unchanged1.5 m baseline. Longer-guide
numbers depend on hypothetical equipment; no pad, button setup or usable
travel is confirmed. Favorable static arithmetic or a mean shear screen is
not complete engineering acceptance. Hot joint direction/moisture data,
qualified root peel/socket bearing, finite cap/body spreading, exact motor and
retainer fit, the full thermal matrix, installed modes/flutter and complete
service remain open. No physical requirement, WO-03 completion, purchase,
build, paid run or flight gate closes. G54 and G12/PID-to-RL remain separate.

## Offline presentation verification

The existing Swift/AppKit image helper rendered both SVGs to1600×1440 PNGs.
Both initial PNGs were inspected with `view_image`. One presentation correction
replaced unsupported native marker arrowheads with explicit polygons and moved
reservation labels off geometry borders. This is offline image inspection,
not browser interaction, CAD verification or engineering validation. Final
observations and hashes are saved in the drawing-run record; no new renderer,
dependency or browser window was used.
