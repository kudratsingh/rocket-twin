# G12 nominal root contact-face audit

**Each curved foot has only 281.731 mm² of coincident area with the current
slotted shell, versus 355.097 mm² on its inner cylindrical face.** The difference
is 73.366 mm², or 20.66%, for each foot. The earlier ideal full-foot foundation
therefore does not represent this nominal shell coverage; its contact sharing
and stiffness must be reassessed. This is geometric coincidence, not measured
wet bond or a strength calculation.

The result applies to the first fin of the historical layered G12 candidate
`4ff75b8f…`, not the 69df G54 candidate. It uses the hash-pinned original
layered-fin STEP and rounded G11-frame STEP, the validated 60-solid material
map, and the **current-source-generated** `aft_shell` from the refrozen copy.
The historical shell's original separate BRep has not been established as
identical to that current generated shape. No CAD generator, active vehicle,
source geometry, mass model or preview asset was changed.

## Method and fixtures

The tool intersects pairs of actual BRep **boundary faces** and sums positive
common-face areas; it does not infer bond area from minimum distance or zero
solid overlap. It uses the geometry kernel's existing tolerances without an
added fuzzy gap, mesh expansion or face movement. Each patch records both source
face indices, surface type, placed bounding box, centroid, common area and one
pair of outward-normal samples. Samples on every reported patch opposed to
within the configured dot-product threshold. A single normal sample is not a
proof of everywhere-consistent normals or complete interface ownership.
Overlapping common patches within one interface stop the audit to prevent area
double counting.

The independent fixtures passed before the actual audit:

| Known case | Expected area mm² | Computed area mm² |
| --- | ---: | ---: |
| 10 × 10 mm planar full overlap | 100 | 100 |
| Planar half overlap | 50 | 50 |
| Parallel planes with a physical 0.1 mm gap | 0 | 0 |
| Two actual radius-10 mm cylindrical faces, 10 mm long, with 45° overlap | 78.53981634 | 78.53981634 |

The positive-gap check verifies that this declared gap is not turned into
contact; it does not characterize the minimum distinguishable gap at every
scale. The curved fixture is physically cylindrical, not merely a curved
numerical field on a straight surface.

## First-fin results

The selected tab, potting, gap-pad, foot and gusset solids come from the
unique 60-solid identity map. The original frame and current-generated shell
are placed at their source stations. Surface areas below are nominal common
areas; “opposed” refers only to the sample on each common patch.

| Interface | Common area mm² | Common patches | Normal samples |
| --- | ---: | ---: | --- |
| Foot bond − → gusset − | 353.261079 | 1 | Opposed |
| Foot bond − → slotted shell | 281.731344 | 1 | Opposed |
| Foot bond + → gusset + | 353.261079 | 1 | Opposed |
| Foot bond + → slotted shell | 281.731344 | 1 | Opposed |
| Root insert/tab → tab potting | 780.438856 | 3 | Opposed |
| Tab potting → frame | 1,028.230886 | 3 | Opposed |
| Frame/shell gap pad → frame | 716.981592 | 2 | Opposed |
| Frame/shell gap pad → shell | 716.764585 | 2 | Opposed |

The gusset-facing and shell-facing foot surfaces lie on different radii, so
their complete geometric face areas need not be equal. The gusset-facing
common area equals its own 353.261 mm² face. The shell-facing common area is
compared with its own **355.097301 mm²** foot face, not with the opposing
surface's area. The partial shell result is consistent with the actual finite
slot cutting through the footprint; the audit did not substitute a full curved
foundation across that slot. It does not quantify any alternative load path
for the unsupported region.

The root/insert-to-potting common area consists of a **500.000 mm²** inner end
face and **140.219 mm²** on each of the two tab sides. Each of those original
tab side faces is 250 mm², so only its common portion is credited here. The
potting-to-frame result includes a **730.000 mm²** floor and two **149.115 mm²**
side patches. These are areas on different surfaces, not a series-strength
calculation. They should be mapped into the next contact model with their
actual geometry and without assuming a single full-area shear joint. The pad
has separate frame-facing and shell-facing surfaces with slightly different
radii; their measured areas should not be forced to match.

The earlier ideal three-DOF contact audit used a full-foot idealization. This
new coverage result does not retroactively supply a corrected moment split,
peel stress or stiffness: the loading distribution and support response must
be recomputed with the actual coincident portions and exposed edges. No
unbonded gap is silently filled. The separate material-map and force-routing
identities remain useful bookkeeping, but neither establishes installed
strength or a complete frame/rail/shell path.

## Reproduction and limits

The completed local evidence is `build/wo03-root-contact-faces-v1/fixtures.json`,
`actual.json` and `completion.json`. The actual record includes per-patch
locators and before/after hashes for the candidate, original STEPs, material
map, code and current CAD sources; those inputs remained unchanged. Face indices
are zero-based for the recorded import and placement and are accompanied by
geometric descriptors and source hashes; they are not promised stable across
CAD-kernel versions. The current-source shell geometry should be independently
matched to an authoritative historical shell if such correspondence is needed.

The fixture child took 2.986 s wall / 2.544 CPU s; the one actual child took
4.708 s wall / 4.816 CPU s. Their aggregate child CPU time was 7.361 s, and the
reported cumulative child peak RSS was 512,868,352 bytes. One worker and one
thread were requested; because actual-child CPU time exceeded wall time,
single-core execution was not demonstrated. No cap increase or actual retry
occurred. Black, Ruff and the focused fixture test pass.

Full wetting, voids, bond thickness variation, adhesion, cure, peel capacity,
partial failure, actual shell material and temperature, frame deformation,
attachment into the forward joint, tolerance and continuous mechanism motion
remain unqualified. The previous fixed-shaft/horn conflicts and installed
structural/flutter gates remain open. No FEA, flight calculation, thermal
analysis, physical fabrication or acceptance claim is made here.

The [published compact evidence](../runs/wo03-root-contact-correction-20261101T012547878277Z/record.json) preserves both
completed packets and the executed clipped-contact sources. Bulk geometry remains
local; reproduction requires the named hash-matching archives. No active design
or frontend CAD/flight identity changed.

Before any adoption, the historical candidate also needs its metadata reconciled:
`fin_set.build.notes` still describes the older 6.35 mm plywood construction,
while the mapped solids describe the 5.64 mm carbon/PVC/wood assembly. The
retained historical cost estimate is not a reconciled procurement price. This
packet does not edit the frozen candidate or grant build readiness.
