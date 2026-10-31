# WO-03 actual CAD first-hit radiation

This study constructs radiation visibility from the actual three-dimensional
opaque solids. It does not assign temperatures or claim thermal, structural,
physical-build or flight acceptance. The primary surface solver owns temperature
grouping, emissivities, reservoirs, transient coupling and integrated acceptance.
Active vehicle specifications are not changed by this study.

The current configuration targets the separate fitting-baffle candidate
`runs/wo03-baffle-fit-20261031T035358211715Z`, identity
`69df790ec9bcba1465be4fa9861a7ad5fbc467091cbf58f44dee069e56e00bac`.
Its resolved JSON SHA256 is
`c80a6d4f563c6c99c92ba7acbbc9ad4b6a0fa0655166f71bbf5a618959e32535`;
its 170-part placed-geometry manifest SHA256 is
`6e0c0b9f421d271d974bf3552721c8756b53cb3ada284c8f946a0e6785a93866`.
The manifest branch checks all 170 STEP/STL pairs, CAD-part completeness,
material/role agreement, frame, solid validity and imported volume. It reads
the supplied **placed STEP** geometry exactly once: no generic generator,
annular substitute, missing notch/seam or second placement transform is used.
The source-owned postprocessor hash remains recorded with this geometry.
Twelve regression tests now pass, including a notched, translated STEP fixture,
rejection of asset tampering and exact zero-hit confidence bounds.

The following completed base results remain frozen and are not inherited by
the baffle candidate. The base explicit source is
`runs/wo03-circular-pad-candidate-20261031T034153884353Z/record.json`, candidate
`e25026cdc3b63f53a01cb4b91f3fb4b7e15c1b3e70e53924e95a639f4c5166b6`, CAD revision
`1193713d0f4a7ad8393a00a0a03e7aaa04e9aa9393d2034691ef7126ae3cdd3b`.
Its parent is the frozen eight-foil G54 candidate
`runs/wo03-multilayer-shield-20261031T022026246942Z/record.json`, identity
`7aecfec03d1197a71be48a466b0530accf46b17a642382ef7ef484af6e6af531`.
The primary agent explicitly reconciled all CAD caches, volume-owned masses,
CG and full inertia after opting only sector pads into exact circular boundaries.
This is a candidate copy; it is not adoption into an active configuration.

The **interior** fluid domain for both separately recorded studies is the cylinder of radius 32.5 mm (the
actual tube inner radius) from station 990 to 1212 mm
minus every intersecting source-owned `manufactured` or `purchased_envelope`
solid. Actual foils, rail/frame, ring ends, finite sector pads, fin bodies, fin
bonds and slotted ring-to-shell bonds participate in the cut. There is no full
annular adhesive replacement for a slotted or sector part. Distributed mass
budgets and flexible envelopes do not become invented opaque solids.
The base provides 106 opaque parts intersecting this domain; the separate
fitting-baffle source provides 138. A purchased
motor cylinder is an estimated envelope; certified closure/nozzle/plume geometry
is unavailable and must remain unresolved in any coupled result.

The fore and aft cuts are explicit black reservoirs with unknown environmental
temperatures. At the radial control cylinder, actual adjacent paper/solid is
assigned only after material-side occupancy verification. Truly uncovered
patches remain a separately named unknown black radial reservoir; they do not
become invented paper. An independent area audit cuts cylindrical surfaces at
0.001/0.0001/0.00001 mm inward offsets through all actual opaque parts and
compares the projected exposed/blocked areas with the actual radial fluid
boundary. This includes portions blocked on their fluid side by finite parts;
they are not falsely counted as exposed air or paper area. Half-covered and
fully paper-covered control-cylinder fixtures verify the assignment and audit.
The primary must decide whether prescribed reservoirs and this enclosing domain
are adequate for a particular heating case.

The original 34.5 mm outer-domain run is preserved separately. It included
external shell/fin radiation and found four genuinely non-manifold CAD contact
edges along tangent flat fin roots at radius 33 mm. Actual BRep edge ancestry,
before coordinate welding, has 3855 edges with two face incidences and four
with four incidences. The primary chose an interior control volume because the
shared thermal solver separately retains external shell convection/radiation;
including those external surfaces in the current radiation coupling would
double count that path. The new domain is an explicit scope choice. It does not
repair the external fin/root contacts, establish installed CAD acceptance or
waive the preserved outer-domain failure.

Open and glued area is decided by the actual Boolean. The primary's independent
occupancy record
`runs/wo03-interface-occupancy-20261031T032856133441Z/record.json` found
606.201718 mm² full ring-gap midradius area: bonds 0/1 fully glue; bonds 2/3/4
each 540.359846 mm² glue, 57.243246 mm² fin and 8.598626 mm² genuinely open air.
This tracer preserves the remaining openings, solid blockers and exposed fin
surfaces rather than substituting either a fully open or a fully glued annulus.
The corrected source changes pad boundaries, so the source identities of these
two evidence records must remain explicit; the occupancy numbers are not
silently treated as a new-source numerical result.

Every original source face is traced through any same-part contact union and
the fluid cut using OCP Boolean history. A compound of touching screw shank and
head cylinders requires an actual solid union: otherwise their internal contact
disk can survive as a non-physical face in a multi-tool cut. The union must be
valid and change source volume by no more than max(1e-5 mm³, 1e-10 of the part
volume); larger changes stop the study. Original face ancestry is retained.
Internal contacts are removed by actual solids, with no area deletion or
material-priority rule.

Ownership uses projected triangle-interior samples on trimmed CAD faces,
verified by the face classifier. `Face.Center()` is never used as a surface
point. Material-side probes at 1e-4, 1e-5 and 1e-6 mm must identify the same
single ancestral material, and the opposite side must be fluid. Truly
ambiguous or unowned area stops execution before candidate meshing/rays.

All fluid faces and every nonzero-area triangle are retained for first-hit
visibility. Suggested radiating groups combine only the same part and physical
surface family: cylinders retain radius, axis and normal sign; planes retain
oriented normal and station; spheres retain radius, center and normal sign;
other surface types keep their face ID. Distinct materials, opposite sides and
reservoir identities remain distinct. These groups suggest possible isothermal
unknowns; no temperature field or half-wall mapping is inferred. The complete
face inventory and triangle-to-face mapping permit the primary to regroup.

The three requested meshes are rebuilt independently, clearing cached
triangulations so that an earlier finer mesh cannot make all levels identical.
The bounded deflections are 0.005/0.0025/0.0015 mm and angular tolerances
0.15/0.10/0.085 rad. The originally requested fine mesh (0.00125 mm, 0.07 rad)
exceeded the 150,000-triangle cap and is preserved as a failed attempt. The
explicit 1.5 µm correction retains every actual face and slot, and stops again
if it cannot meet the same triangle cap. Every triangle winding must agree with the actual oriented
CAD surface normal. Projected interior samples on every face verify outward
normal points out of fluid. Welded undirected edges must each occur twice, and
signed mesh volume must agree with CAD fluid volume within 0.5%. OCP's exactly
collapsed pole triangles on sphere fixtures are explicitly counted; they have
zero area. No finite material face is removed to fit a budget.

The first-hit engine uses the already installed VTK 9.6.2
`vtkStaticCellLocator`. No new dependency or acceleration package is installed.
Each source group samples triangles in proportion to mesh area, uniform
barycentric points, and a cosine-weighted diffuse hemisphere into fluid.
The first opaque triangle supplies the target group. The estimator is
`F_ij = hit_count_ij / source_ray_count_i`; group areas are recorded separately.
This directly estimates the diffuse cosine view-factor integral. All rows,
raw hit counts and trace hashes are retained. There is no reciprocity projection
or row renormalization. Escaped rays and near-origin hits are failures.

Candidate ray counts are 100,000/300,000/750,000, with a minimum of 24 rays
per preserved physical group and the rest allocated by area. The exact total
including independent known cases and previous fixture development is bounded
by 2.5 million rays. The initial interior run executed 653,024 rays (253,024
known + 100,000 coarse + 300,000 medium), then hit the fine triangle cap.
The bounded fine-only continuation reuses those exact known-case operator
hashes and the unchanged core tracer implementation; it does not repeat the
earlier rays. Its conservative prior-execution allowance is 1,655,000 rays,
including development/failed fixtures, so 750,000 fine rays give a maximum
2,405,000 aggregate budget. The runner records actual rays in the current
execution separately from this prior-budget upper bound. Each mesh is
bounded by 150,000 triangles and VTK/BLAS use one CPU thread. The ray loop has a
600-second limit per call. CAD meshing/Boolean timing is recorded; the configured
600-second geometry target is not an asynchronous kernel cancellation promise.

The independent fixtures use three mesh/ray levels (12,000/24,000/48,000 rays
each) and a separately known answer:

| Fixture | Independent expected value |
| --- | ---: |
| Opposite faces of a unit cube | 0.199824895698387 from a 64×64 Gauss integral |
| Equal parallel disks, separation = radius | (3−√5)/2 = 0.381966011250105 |
| Concentric spheres, radius ratio 1/2, outer to inner | 1/4 |
| Convex inner sphere to outer | 1; finite-facet self-hit error recorded |

For the cube, the independent integral is four times the integral over
`x,y in [0,1]` of `(1−x)(1−y)/(pi*(1+x*x+y*y)^2)`.
The sphere area-ratio result follows from reciprocity and the convex inner
sphere seeing only its enclosure. Analytic comparisons allow five binomial
standard errors plus an explicit 0.002 finite-facet allowance. A sphere fixture
can expose a small spurious self-hit probability from a non-convex triangulated
approximation; it is recorded, never reassigned. The inner-to-outer result must
remain at least 0.998 at every fixture level.

Four actual Boolean slab fixtures trace 256 deterministic rays each: fully open,
fully glued, partly glued and two opaque barriers. Expected target identity and
distance are checked for every ray. A full slab makes two disconnected fluid
volumes; all four glue-to-enclosure contact faces disappear, and its two exposed
faces remain. A partial slab passes exactly half the grid rays. With two slabs,
all rays hit the nearer slab, proving that a downstream surface is not counted
through an opaque barrier. A separate regression fixture rejects actual
two-material overlap, and another preserves original ancestry while removing
the touching shank/head internal contact.

The mesh volume, group areas, row closure, raw area-weighted reciprocity,
successive-mesh changes and Monte Carlo uncertainty are numerical diagnostics.
They do not certify that every small opening has enough rays. In particular,
zero hits from a source with `n` rays only bounds an unseen target probability
at approximately `−ln(0.05)/n` for 95% confidence. At the minimum 24 rays this
bound is about 0.125; tiny-group pathways may therefore remain unresolved.
The saved operator is raw evidence for the primary, not an automatically
accepted thermal exchange matrix. Three levels alone are not a convergence pass.

Earlier failed evidence is preserved:

| Artifact | Decisive finding |
| --- | --- |
| `build/wo03-cad-radiation-geometry-first/report.json` | Original polygonal pads: 4059 faces, 1224 foil/pad aliases over 0.425027665 mm²; stopped before mesh/rays. |
| `build/wo03-cad-radiation-material-owners/report.json` | Correct rejection of old CAD caches after shared generator changed. |
| `build/wo03-cad-radiation-circular-preflight/report.json` | Corrected pads: 1243 faces, zero ancestry aliases; three non-fluid screw contact disks rejected. Runner source was edited during this preflight, so its `inputs_unchanged` is false; physical CAD/spec hashes stayed unchanged. |
| `build/wo03-cad-radiation-known-v1/report.json` | Collapsed sphere-pole triangles exposed; zero-area handling added and retained in mesh diagnostics. |
| `build/wo03-cad-radiation-known-v2/report.json` | A coarse faceted inner-sphere self hit exposed; finite-facet error recorded explicitly rather than relabelled. |
| `build/wo03-cad-radiation-known-v3/report.json` | All analytic and opaque-barrier fixtures pass; 253,024 rays. |
| `build/wo03-cad-radiation-circular-rays-v1/report.json` | Contact union succeeds, 1240 faces and unique owners, unchanged inputs; coarse mesh fails non-manifold external fin/body tangency. Zero candidate rays. |
| `build/wo03-cad-radiation-edge-diagnostic-v1/report.json` | Cached actual STEP localizes four four-incidence welded edges; physical source hashes unchanged. |
| `build/wo03-cad-radiation-interior-preflight-v1/report.json` | Explicit interior domain:1153 faces, all material/reservoir owners verified,3646 actual BRep edges each with two incidences,759 physical groups. Radial coverage audit passes; inputs unchanged. |
| `build/wo03-cad-radiation-interior-rays-v1/report.json` | Coarse80798/medium113666 triangles trace without escapes; fine1.25µm exceeds150k cap. Earlier known/coarse/medium raw results remain valid and preserved; the execution is failed overall. |
| `build/wo03-cad-radiation-interior-fine-bounded-v1/report.json` | Fine1.5µm completes with144600 triangles and750000 new rays; all inputs unchanged. Raw operator available; no thermal acceptance. |

The completed base interior preflight took 140.24 seconds. The full radial
control-cylinder area is 45,333.181991 mm²: 37,822.573512 mm² actual adjacent
paper, 2,737.029109 mm² genuinely uncovered unknown reservoir, and
4,773.579370 mm² opaque blockage on the fluid side. Independent inward
surface-cut residuals converge as −0.0527955, −0.00527940 and
−0.000527939 mm², versus a 0.05 mm² finest-probe tolerance. Nine raw Boolean
ancestry aliases are coincident paper/control-cylinder faces, uniquely resolved
by actual material-side occupancy; zero ambiguous area remains.
The actual STEP SHA256 is
`07683bb0f06c2a485ebdcec18373a9c4704f29e604528eeb835309365ace35a3`.
This establishes geometry/topology/coverage only; the separate outer-domain
failure remains open.

The bounded continuation completes the three numerical levels across the two
preserved records. The group-map SHA256 is byte-identical at all levels:
`824ba0040c03f794e05f1b359f328d9c53f39e4b8c8eade027653fa9426658a2`.
All use the same exact checked input STEP, part shapes and source candidate.
Re-exported STEP file hashes can differ because their headers change; their
geometric DATA payloads are compared in the separate summary artifact.

| Level | Boundary triangles | Rays | Relative mesh-volume error | Raw reciprocity L1 | Area-weighted raw F change |
| --- | ---: | ---: | ---: | ---: | ---: |
| Coarse,5µm | 80,798 | 100,000 | −0.00006010 | 0.031413 | — |
| Medium,2.5µm | 113,666 | 300,000 | −0.00003290 | 0.019972 | 0.054314 |
| Fine,1.5µm | 144,600 | 750,000 | −0.00001794 | 0.012440 | 0.033084 |

Every completed level has zero escaped/near-origin rays, a two-manifold closed
mesh and maximum row-closure error 2.22e−16. Fine mesh volume is
475,574.784570 mm³ versus actual CAD fluid volume 475,583.318223 mm³.
The raw reciprocity L1 is
`sum(abs(A_i*F_ij − A_j*F_ji))/(2*sum(A_i))`; maximum fine exchange mismatch
is 7.07684e−5 m². No reciprocity correction is applied. The reduced global
change is evidence of improving aggregate estimates, not a local convergence
or coupled-temperature pass. Maximum medium-to-fine local F change is 0.49231;
the smallest fine source group receives only 26 rays, its zero-hit 95% upper
probability is 0.11522, and maximum estimated binomial standard error is 0.09806.
Those unresolved local pathways remain explicit limitations. Thermal coupling
must propagate sampling/geometry error and any reciprocity correction.

Fine execution takes 119.87 seconds, including 7.71 seconds for its 750,000
rays. Its report SHA256 is
`6c8676425e54c9448a66eb9bb18559625ffc8a9cc5732e9270b8f3e1d8f5983c`;
the raw operator SHA256 is
`c323775ba6bd3a4e16a4a859b777cfe89d848b5cddf37eba22a1391a67d56de2`.
`three-level-summary.json` in the same directory links both records and retains
their different overall statuses, with local convergence/thermal acceptance
explicitly false. `actual-brep-topology.json` in the outer diagnostic directory
records the four actual CAD contact-edge failures independently of meshing.

The fine `fine-operator.npz` contains raw `hits`, `counts`,
`raw_view_factors`, `group_area_m2` and zero-hit probability bounds; matrix axes
are source group then target group. `surface-groups.json` gives the group IDs,
part IDs, physical sides/families and all retained fluid face IDs.
`fine-boundary.npz` gives every triangle, outward fluid normal and its
zero-based `triangle_face_index` (the JSON face IDs are one-based), plus CAD and
mesh face areas. Geometry coordinates are millimetres; exchange areas are m².
No emissivity, temperature or thermal contact is assigned by these files.

The separate 170-part baffle-fit candidate
`runs/wo03-baffle-fit-20261031T035358211715Z` has a separate identity and
script-owned placed-geometry manifest. It is not the traced base candidate and
does not inherit this operator. Its custom notches/seams must be loaded from
the exact manifest/postprocessor, never regenerated as bare annuli or generic
source shapes. Its fresh source/Boolean/mesh/operator records must pass their
own gates. The owner-authorized cumulative ray cap is extended to five million
for base plus baffle development. The baffle configuration reserves 2,420,000
prior rays (base's 2,405,000 conservative allowance plus regression allowance)
and initially plans 150,000/450,000/1,150,000 new rays: 4,170,000 total budgeted
rays if all levels complete. The initial 5/2.8/1.8 µm attempt completes the first
two levels, then exceeds the same 150,000-triangle cap before any fine rays.
That failed execution is retained at
`build/wo03-cad-radiation-fitting-baffle-rays-v1/report.json` (273.91 seconds,
unchanged inputs). Coarse has 93,502 triangles, medium 123,724; both have zero
escaped/near-origin rays and raw row closure within 2.22e−16. Their raw
reciprocity L1 values are 0.034813 and 0.019149; weighted F change is 0.055079.
The current configuration makes one explicitly recorded fine-only continuation
at 2.0 µm/0.10 rad, preserving every actual face/notch. Its prior-ray bound is
3,020,000 (including those 600,000 new coarse/medium rays); 1,150,000 fine rays
retain the same 4,170,000 total budget. A second fine cap failure stops the study
with an honest partial result. No ray/operator is inherited from the base.

Known-case reuse is anchored before adding the manifest loader: the companion
`known-kernel-hashes.json` is bound to the frozen base report/module/runner
hashes and records exact source hashes of every tested tracing/geometry kernel
function and analytic fixture builder. The loader addition changes the module
file hash but none of those kernel functions. The new run checks the anchored
function hashes and raw known-case operator hashes; a changed tested function
requires fresh validation rather than automatic reuse.

The fitting-baffle geometry preflight is separately executed at
`build/wo03-cad-radiation-fitting-baffle-preflight-v1/report.json`: all 340
asset hashes verify, 138 opaque source parts produce 1,785 verified fluid faces
and 1,127 suggested physical groups. Every one of the 5,174 finite BRep edges
has two face incidences; no unowned or ambiguous material area remains.
The CAD fluid volume is 475,607.907582 mm³. Independent radial coverage again
finds 37,822.573512 mm² paper, 2,737.029109 mm² unknown reservoir and
4,773.579370 mm² opaque blockage; the finest residual is −0.000527939 mm².
This is an executed new-source result, not inheritance from the base.
Its source inputs remain unchanged during the 232.55-second execution.
The actual fluid STEP SHA256 is
`95a71ae452598b6e460a10246e2a0a2e2b8a8fd9b95f10056e2610e149f1c4ac`;
the group-map SHA256 is
`17e438947d2aa7c745b0a6c1a4c3317a61015eaaf840e22e41b31deb19cfd3ed`.

The before/after comparison uses the actual eight ring-end stations and sides
in the fitting study's contact ledger. A front ring face has outward fluid
normal +Z; an aft ring face has outward fluid normal −Z. Target groups must
match `motor_mount`, the actual plane station and that normal; unavailable
exposed geometry is an error, not a zero. Comparisons include the motor envelope,
each common exposed motor/shield surface, and all longitudinal shield-cylinder
sides with their actual sampled areas. Multiple baffle/shortened-wrap changes
are evaluated as one combined candidate; no isolated effect is attributed to
the baffles alone. No temperature is assigned to either side of a foil.

For each source group, hits into the target-group union are binomial counts.
The comparison computes exact Clopper-Pearson component bounds with tail
`0.05/(2*m)`, where `m` is the total number of source groups across the before
and after estimate. Weighting those bounds by actual source area and taking
`[after_lower−before_upper, after_upper−before_lower]` gives a conservative
joint 95% bound for that reported comparison, without assuming independence
between candidate samples. This is not a simultaneous claim over every
reported ring/source row. Mesh error, source uncertainty and unresolved
temperature mapping are explicitly separate. A zero-hit source retains a
positive upper bound. Raw F, source/target areas and direct exchange area
`sum(A_i*F_i,target)` are all recorded, so changed foil area is visible.

The new baffle faces are reported separately as after-only sources toward their
adjacent actual ring end. Their surfaces did not exist in the base and are
never represented by a fabricated zero baseline. The physical parallel air
path 0.0534872434 W/K and bulk support path 0.00251038663 W/K are references
**once per physical baffle**, with the actual contact ledger retained. Those
estimated paths remain obligations of the primary temperature solver; a
visibility change does not waive them or establish a heat-flow benefit.

The bounded fitting-baffle continuation **completes** at
`build/wo03-cad-radiation-fitting-baffle-fine-bounded-v1/report.json`:
144,690 triangles, 1,150,000 new rays and all source inputs unchanged.
The raw operator has zero escaped/near-origin rays and row closure within
2.22e−16. The complete executed baffle levels are:

| Level | Boundary triangles | New rays | Relative mesh-volume error | Raw reciprocity L1 | Weighted raw F change |
| --- | ---: | ---: | ---: | ---: | ---: |
| Coarse,5µm | 93,502 | 150,000 | −0.00006080 | 0.034813 | — |
| Medium,2.8µm | 123,724 | 450,000 | −0.00003692 | 0.019149 | 0.055079 |
| Fine,2.0µm | 144,690 | 1,150,000 | −0.00002502 | 0.011947 | 0.031836 |

The fine record takes 154.68 seconds, including 9.73 seconds tracing its rays.
Its conservative aggregate ray budget is 4,170,000, below the authorized five
million. The initial 1.8 µm cap failure is retained; the corrected fine run
does not repeat the earlier 600,000 candidate rays or known fixtures.
Group-map hashes match exactly across all three baffle levels; coarse/medium
and fine STEP geometric DATA payloads are byte-identical. Every one of the
1,785 faces remains represented. There is no reciprocity projection.

Local convergence is still not established: maximum medium-to-fine raw F
change is 0.5, minimum source sample count is 24, maximum binomial standard
error is 0.10206, and maximum zero-hit 95% probability bound is 0.12482.
The global weighted change decreases to 3.18%; this is not a temperature or
local-path convergence pass.

Fine direct visibility from all longitudinal-shield cylinder sides to the eight
ring ends has these point estimates and conservative Monte Carlo bounds:

| Ring end | Base F | Combined-candidate F | Joint95% bound on after−before |
| --- | ---: | ---: | --- |
| 1 front | 0.00431819 | 0.00199989 | [−0.00506318, +0.00009654] |
| 1 aft | 0.00425214 | 0.00202866 | [−0.00496592, +0.00018541] |
| 2 front | 0.00436820 | 0.00210399 | [−0.00504242, +0.00018062] |
| 2 aft | 0.00430173 | 0.00187246 | [−0.00515129, −0.00003813] |
| 3 front | 0.00432864 | 0.00210255 | [−0.00499593, +0.00021230] |
| 3 aft | 0.00441581 | 0.00203297 | [−0.00514840, +0.00005163] |
| 4 front | 0.00409260 | 0.00201589 | [−0.00479789, +0.00031139] |
| 4 aft | 0.00172210 | 0.00056743 | [−0.00276679, +0.00012716] |

The points decrease approximately 51–67%, but seven of eight conservative
aggregate intervals include zero change. The strictly negative ring-2-aft
interval concerns Monte Carlo sampling only; it excludes mesh/source/material
uncertainty and is not a general reduction claim. All 528 source/ring
comparisons, raw hit counts, areas and bounds remain in
`fine-ring-end-visibility.json`; no missing or zero-hit route is turned into
physical certainty.

The new ring-facing baffle main faces see their adjacent rings at
F = 0.96358–0.97835. Their opposite faces retain separately reported zero-hit
probability bounds. Adding the adjacent baffle main faces to the remaining
longitudinal shields gives a useful **geometric common-radiosity benchmark**:
exchange-area points are 1.019–1.098 times the base at seven ends and 1.822
times the base at ring 4 aft. For example, ring 1 front changes from
1,286.36 to 1,338.45 mm² exchange area; ring 4 aft changes from 513.00 to
934.77 mm². All eight conservative exchange-area delta intervals include zero.
This benchmark assumes a common radiosity solely to expose the new geometry;
actual radiosities and temperatures are unknown and unequal. It is not actual
heat flow. Baffle edge emission is retained in the full operator and excluded
only from this explicitly named main-face summary. Direct-path shielding
therefore does not establish a net radiation or temperature benefit.

The final baffle report SHA256 is
`04fd0a54cf4f0ad752ca3a1319262416d5e74b933fc787234154ef74d044458e`;
raw operator SHA256 is
`45cf710d8be814dda708514385f82ec68332140f75d0252ee9d41cff7f7da4b8`;
fine ring-end comparison SHA256 is
`c9ce808037324b5acf75d62920d749a977e0749c99e388e5d4da1a3b74c7869b`.
The same directory contains `three-level-summary.json` (SHA256
`cffb4adc26c2e8089d3159946e1015cf20607059dd3db346e1762e8501ea743d`)
and `uniform-radiosity-exchange-area-benchmark.json` (SHA256
`ca832e9cbdcd443ea0f7379568a798e21d6152fa7f2d486699acd92a6ba0373f`).

The gas-conduction handoff is prepared without making any gas mesh or gas
operator: `gas-boundary-handoff.json` in the same directory, SHA256
`f8282389c9ccdff6d68789c01f03fc052c49ebb7c3c2b33a04559bcac644ef26`.
It hashes the actual final fluid STEP, face inventory, all 1,127 suggested
groups, boundary tessellation and `src/analysis/gas_conduction.py`. The final
fluid STEP SHA256 is
`1400eb53b79afdb41784aa06c5e0b45f8dc717027041fa6fc4f96d42d3b7fec0`.
Every face is covered exactly once. CAD coordinates are mm; `GasMesh.points_m`
requires scaling by 0.001. Gmsh face enumeration cannot be assumed to match
the CAD inventory; actual ancestry/projected interior samples, normal and area
must verify remapping. The primary must define temperature/half-wall grouping,
unknown reservoir conditions and disjoint boundary-node edge ownership before
meshing. Missing labels must not become invented insulation.

The future actual gas solve of the 0.6 mm gaps must replace their corresponding
estimated parallel air edges rather than add both. Solid support conduction
remains separate. Radiation counts aggregate the current physical groups;
finer temperature grouping would require new ray binning/tracing, not invented
subdivision of those counts. No gas mesh, gas conductivity assumption or gas
temperature result is supplied by this task. The primary retains that next
assignment and all coupled engineering acceptance.

Ten focused regression tests pass. Black, Ruff and strict mypy pass for the
owned implementation/runner. The suite includes actual opaque barriers,
two-material overlap rejection, same-part screw contact removal, diffuse cube
integral/closure, full/half paper boundary coverage and an independently
constructed genuinely non-manifold tangent-root rejection.

Replay the base with its frozen configuration (choose a fresh output directory):

```sh
.venv/bin/python scripts/wo03_cad_radiation.py --stage rays \
  --config build/wo03-cad-radiation-interior-fine-bounded-v1/study-config.yaml \
  --level fine \
  --geometry-cache build/wo03-cad-radiation-interior-preflight-v1 \
  --known-cache build/wo03-cad-radiation-interior-fine-bounded-v1 \
  --previous-level-operator build/wo03-cad-radiation-interior-rays-v1/medium-operator.npz \
  --output build/wo03-cad-radiation-base-fine-replay
.venv/bin/python -m pytest -q tests/test_cad_radiation.py
```

The selected fitting-baffle fine-only continuation uses the current source
configuration (the initial full attempt retains its own config snapshot):

```sh
.venv/bin/python scripts/wo03_cad_radiation.py --stage rays \
  --level fine \
  --geometry-cache build/wo03-cad-radiation-fitting-baffle-preflight-v1 \
  --known-cache build/wo03-cad-radiation-fitting-baffle-rays-v1 \
  --previous-level-operator build/wo03-cad-radiation-fitting-baffle-rays-v1/medium-operator.npz \
  --output build/wo03-cad-radiation-fitting-baffle-fine-bounded-v1
```

`--stage known` executes only source-independent fixtures. `--stage geometry`
stops after actual Boolean ownership/grouping; `--stage mesh` adds the three
boundary meshes. `--geometry-cache` accepts a prior actual STEP only after exact
candidate/STEP/physical-source hashes and face order/areas are checked. It does
not bypass current schema, source shape identity or material-side verification.

`--level` permits a bounded continuation after a recorded mesh/ray failure.
`--known-cache` verifies the exact unchanged core tracer module, passed fixture
record and every cached raw operator hash; analytic fixture construction stays
unchanged while the runner adds execution-selection/cache plumbing. The reused
rays are covered by the prior budget and are not counted as newly executed.
`--previous-level-operator` records and hashes the retained prior operator used
for cross-record resolution comparison. Each new record snapshots its complete
study configuration; old records are never overwritten.
