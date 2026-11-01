# G80 bridge bulk-refinement strategy assessment

**The 3.0 / 2.0 / 1.5 mm triad is a testable mesh-only proposal, not yet a
refinement study.** The current adapter sets Gmsh `Mesh.MeshSizeMin` and
`Mesh.MeshSizeMax` to the bulk size, then generates quadratic tetrahedra. The
separate boundary helper applies fixed 48 outer and 24 inner full-circle
segments to each of the three exact washer circles. Thus bulk size can affect
unconstrained mesh regions, while these washer boundary curves retain their
sampling. Geometry thickness, film interfaces, patch boundaries and other
mesher constraints can dominate locally. Existing evidence does not show how
the proposed 3.0 or 2.0 settings affect any region, so meaningful local
refinement and compliance with the caps are unproven.

The retained 1.5 mm mesh provides a measurable baseline. For each tetrahedron,
the following table reports the median of its maximum **straight corner-edge**
length and its integrated volume; it does not treat the maximum edge as the
0.1 mm film-thickness resolution. The washer zone is the fixed physical region
whose tetrahedron centroid is within 6 mm of any washer center and at local
z ≥ 168.1 mm. The [read-only baseline record](../build/wo03-g80-bridge-mesh-strategy-v1/record.json)
includes 10th and 90th percentiles, source hash and precise definitions.

| Region | Tets | Median maximum corner edge | Median tet volume |
| --- | ---: | ---: | ---: |
| G11, all | 20,409 | 1.730 mm | 0.23873 mm³ |
| G11, washer zone | 6,475 | 1.246 mm | 0.06251 mm³ |
| Six epoxy films | 2,086 | 1.511 mm | 0.02939 mm³ |

The proposed two pilots would set **only** the bulk size to 3.0 then 2.0 mm,
retain fixed 48/24 boundaries and the exact source geometry, material
partition, six rail-back support faces, units and load construction, and use
the existing accepted 1.5 mm case as the finest level. Each new attempt would
be a separate mesh-only child, capped at 60 CPU / 60 wall seconds, with a
2 GiB supervised-root RSS limit, 50,000 declared-node and 75,000 tetrahedron
guards, one requested CPU, and stop on the first invalid or capped result.
Thirty CPU seconds are reserved for setup: planned total 150 CPU seconds,
below 600. This proposal grants no authority to generate either mesh.

The same verified source/STEP hashes, G11 and epoxy material definitions,
physical face ownership, mesh-to-CAD material volume within 1%, per-patch
absolute area error within 0.0002 mm², positive Jacobians, connectivity,
node/tet caps, exact load serialization and force/moment checks remain
mandatory. The already selected 0.5% maximum affine pressure correction is
unchanged. Each mesh must record applied resultant and moment and correction
range. The discrete affine pressure correction is recomputed on each mesh to
reproduce the same CAD-centered resultant; therefore its coefficients may
differ. A comparison must report those differences and assess their influence;
the source defines the same resultant construction, not a measured or
necessarily identical physical pressure distribution.

Before calling the sequence a refinement, compare all three levels in the
same fixed physical G11 washer, web and tab-root regions and separately in each
film: element count; distributions of maximum corner-edge length and element
volume; shortest edge and thickness-direction/layer resolution; and relevant
quality/Jacobian statistics. Report literal values and whether changes progress
consistently from 3.0 to 2.0 to 1.5 mm in every region used for convergence.
Retain the fixed washer sampling explicitly. If a region is unchanged,
nonmonotonic or too poorly resolved, its stress result cannot be claimed
converged simply from three bulk labels. No arbitrary new numerical acceptance
threshold is asserted here.

The initial read-only measurement script encountered a Python standard-library
name collision (`inspect.py` shadowed `inspect`); renaming that local
measurement script resolved it. No native case or mesh was attempted. One
saved finest level cannot establish resource scaling, and thinner or more
refined boundary-controlled regions may make a full-volume triad infeasible.
If the pilots do not produce meaningful local progression under the existing
caps, stop this approach and return to a separately defined bounded local
structural representation with independently verified loads and boundary
conditions; it is a new physical approximation requiring known-case checks,
not an automatic substitute or a relaxed acceptance gate.

## Admitted mesh-only pilot stop

The 3.0 mm child generated a mesh whose adapter preflight recorded 21,341 nodes,
10,864 tetrahedra, three patch areas of approximately 54.53809825 mm² and
positive sampled Jacobians (minimum 0.03248658 mm³). The new wrapper then
stopped before its regional report and the independent input validation:
its metrics reader used a string connectivity key against the adapter's
in-memory integer material keys (`KeyError: '7770'`). The child exited 1 after
2.821 wall seconds and 2.612 child CPU seconds. Source and physical pins were
unchanged; the 2.0 mm pilot was not launched and no solver was invoked.
Intermediate adapter preflight is not a pass of the complete input gates.
The [compact stopped packet](../runs/wo03-g80-bridge-mesh-pilots-20261101-v1/summary.json)
preserves the source and output hashes. No mesh refinement or convergence is
claimed from this stopped attempt.

## Read-only recovery and second pilot

The primary authorized one JSON-key normalization correction. The saved
3.0 mm mesh was **not regenerated**: separate read-only evaluation passed the
unchanged independent input checks and recorded the original workflow failure
separately. The 2.0 mm mesh was then generated once and passed its unchanged
input checks. Both cases have the same pinned source identities and applied
SINGLE resultant 150 N and moment `[3312.5471695, −1912.5, 0] N·mm`; no solver
ran. Their declared/used node counts and tet counts are respectively
21,341/21,206 and 10,864 at 3.0 mm, and 30,384/30,249 and 15,656 at 2.0 mm.
The 2.0 mm child used 6.448728 CPU seconds and 6.750468 wall seconds; the
3.0 mm read-only recovery used 1.728693 CPU and 1.730778 wall seconds.

The sequence **is not uniformly monotonic**. At 3.0 / 2.0 / 1.5 mm, median
G11-wide maximum corner edges are 1.813 / 2.004 / 1.730 mm and median tet
volumes 0.24949 / 0.32764 / 0.23873 mm³. In the fixed washer zone, median
maximum edges are 1.289 / 1.276 / 1.246 mm but median volumes are
0.06465 / 0.06474 / 0.06251 mm³. Every film's median maximum edge decreases
from about 2.909 to 1.89 to 1.51 mm, but its median thickness-normal span
remains approximately 0.1 mm at all three levels. These summaries are not a
proof of regionwise convergence or of multiple layers through the film.

The largest bounded affine pressure correction was approximately `1.78e-15`
of mean pressure at each level. The adapter did not retain the affine
coefficients, so their differences are unavailable; the bounds are not a
claim that the coefficients are identical. The [comparison packet](../runs/wo03-g80-bridge-mesh-recovery-20261101-v1/summary.json)
contains regional distributions, input checks and hashes. The primary must
assess the nonmonotonic G11 sampling before choosing any subsequent analysis;
no convergence or strength pass is claimed.
