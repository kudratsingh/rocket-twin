# Actual material-normal chord screening approximation

This is one explicitly unvalidated, nonbounding local half-wall approximation
for the fitting G54 `69df790e…` candidate. It supplements the frozen material
mapping without converting its unavailable physical paths into qualified ones.
It does not solve gas or material temperatures, change the required 300°C /
ε0.9 / 35°C condition, or establish a 45°C substrate pass.

The original baseline remains
`runs/wo03-surface-materials-20261031T045222607795Z/record.json` and
`docs/wo03-surface-materials.md`. Its 897 unavailable faces stay unavailable for
acceptance. The approximation retains the same actual placed solids, notches,
seams, pads, first material boundaries and original radiation groups.

The single authorized exact-cache restart is supervised at
`runs/wo03-surface-chords-20261031T051623357877Z/`.
It **completed all 97,496 chord queries in 152.39055 seconds**, with unchanged
inputs, within the hard 1,500-second /100,000-query cap. All 141,699 Robin
triangles plus 2,991 prescribed-boundary triangles cover the original 144,690
fine-boundary triangles exactly once. This is complete execution of a screening
map, not validation of the solid-temperature/half-wall approximation.

| Completed artifact | SHA256 |
| --- | --- |
| `record.json` | `1a5174136586ec242e3c91f65d9beb3ec00026a0a05c46d68249d139e2fe649a` |
| `wall-quadrature-screen.npz` | `d1753e8046b06e8a09f241802ed4145241c3dec38bd7effcf5069debda25a284` |
| `wall-map-metadata.json` | `63a9cb397c8923504c27b17c1397d0e11ff39ca81f05b17f1317103bb114faf1` |
| `component-capacity-ledger.json` | `ebc8b6a759523a14ad81f211d5f6399503295a2ec36a23714f7649d1ebd9532d` |
| `component-bulk-parent-map.json` | `0a0889a01e70aa4084fdec9f5b57ac20129804a79be836b49369b82d286c61f9` |
| `wall-algebra-qa.json` | `e8fb0d6ea8df732d0f072091eca16d7424ac0623baf8c2446abb8de9bd5fe09c` |

## Why this approximation and its cost

The existing nominal recipe paths are retained. Only the unavailable material
faces use `δ(x)=d_first_exit(x)/2`, where d is the distance through the **same
actual material component** along the material-inward/gas-outward normal. The
mid-chord point is connected to that component's proposed bulk temperature.
The scalar solid coefficient is `h(x)=k/δ(x)`, following the Fourier plane-wall
resistance in [DOE-HDBK-1012/2-92, HT-02](https://www.energy.gov/documents/doe-hdbk-1012-92vol2).
This selects a geometric local length; it does not derive the true three-
dimensional spreading resistance or prove an isothermal component.

The first 1,000 actual source queries completed successfully in 11.67794 seconds.
The 24,374 unresolved fine-boundary triangles require four samples each, or
97,496 queries. The measured 1,138.55-second projection exceeded the initial
300-second limit. The capped benchmark is preserved unchanged at
`runs/wo03-surface-chords-20261031T045941742893Z/record.json`, including its
historical source snapshot. Primary then explicitly authorized one same-family
full run at 1,500 seconds / 100,000 queries / one CPU / $0 paid compute. There
was no new geometry family or silent cap change.

The original full attempt at
`runs/wo03-surface-chords-20261031T050725220253Z/` was stopped by primary for a
specific exact API caching comparison. Its last complete checkpoint was 12,000
queries /347.316 seconds; attempted queries after that checkpoint are explicitly
unavailable, not invented as an exact final count. Source/config snapshots,
worker interruption, logs, capacity and liner ledgers are preserved. It supplies
no complete operator.

Inspection found that CadQuery creates a fresh `BRepClass3d_SolidClassifier`
for each `solid.isInside` call—seven calls per chord. The intersector was already
cached. Primary authorized one paired classifier-cache benchmark, preserving
the installed predicate `State()==TopAbs_IN or IsOnAFace()` and 10⁻⁸ mm tolerance.
The benchmark at `runs/wo03-surface-chords-20261031T051544047634Z/record.json`
compared the same 1,000 source points: original **10.938008 seconds**, cached
**0.863027 seconds**, **zero chord/projection difference**, and identical all-seven
classification signatures. Both APIs passed slab/ring/reversed-normal fixtures.
The conservative 153.418-second full projection includes the larger prior
64.276-second preflight overhead plus five seconds of serialization allowance,
meeting the primary's ≤1,200-second restart gate. One cache restart was authorized
at the existing 1,500-second /100,000-query cap; source geometry, h formula,
quadrature points, material inputs and tolerances are unchanged.

Every query projects an interior triangle sample to its hash-checked original
material source face. Its gas-outward normal is the **negative material outward
normal**. The direction must align with the triangle normal and enter exactly
the assigned source component; the reverse side must be outside that component.
The first positive CAD intersection supplies d. Interior points along the chord
must remain within that same material; the path stops at its first exit even if
another part or adhesive lies beyond it. Projection error may not exceed the
pinned 2 µm source deflection plus 10⁻⁷ mm numerical tolerance.

No ray is bent or auto-flipped, no solid is treated as transparent, and no
missing, zero, ambiguous or failed query becomes h=0, an insulated boundary or
a clipped positive coefficient. Such a failure blocks the complete field.
The whole-part bounding box is never a thermal length.

## Positive variable-h wall quadrature

Each unresolved triangle has one centroid diagnostic sample plus the three
interior barycentric points `(2/3,1/6,1/6)` and its permutations. Only the three
interior values enter the wall operator, with positive area weights A/3:

`M = Σ wq hq Nq Nqᵀ`, `B = Σ wq hq Nq`, `D = Σ wq hq`.

The local wall energy is `Σ wq hq (Nq·Tsurface − Tbulk)²`, so the raw augmented
wall form is positive semidefinite by construction. M's row sums equal B and
sum(B)=D; heat exchanges conserve energy. For constant h, this exactly recovers
the linear-triangle wall mass matrix `hA/12*(I+11ᵀ)`. The centroid is not used
as a substitute constant h.

Three-point chord ratios, percentiles, projection distances and raw chord ranges
are diagnostics of spatial variation. Three points do not establish quadrature
convergence or bound sharp local changes. Conductivity uses the unchanged
material ranges/sensitivity factors from the frozen baseline, with explicit
isotropic-direction assumptions; actual grain, laminate direction, temperature
dependence and manufactured thickness are unmeasured.

The completed unavailable-face chord samples range **0.342729–210 mm**; their
largest CAD projection is **0.947154 µm**, below the pinned bound. Three-point
within-triangle chord ratios are median **1.0**, 90th percentile **1.02935**,
95th **1.56243**, 99th **2.92282**, and maximum **21**. The maximum demonstrates
that large local variation remains even though every sampled ray is geometrically
valid. Neither the quadrature nor the common component-bulk assumption is
qualified by completing these samples. No missing reliable physical half-wall
map from the baseline is relabeled accepted.

Radiation acts on the same physical boundary trace as gas/solid conduction.
The original 1,127-group optical reduction remains; no finer irradiation or
radiosity is invented. An area-mean temperature raised to the fourth power is
not an area integral of the fourth power. Any groupwise irradiation/radiosity,
temperature averaging or field transfer remains a separate declared screening
approximation owned by the primary coupling code.

## Liner ends: full facet coverage without centroid cell assignment

Both exposed liner annular ends retain their 16 radial material states. Each
flat end triangle is partitioned by radial FV strip intersections. Signed
triangle/circular-sector integrals give its planar area and first moments in
each strip; these integrate the three linear basis functions. Thus the bulk
load for cell j is `Bj=h*∫strip_j N dA` and `Dj=h*area(strip_j)`. The full wall
matrix remains exact constant-h `M=hA/12*(I+11ᵀ)`.

These are **planar facet** integrals, not exact curved CAD annulus areas.
Primary explicitly permits nearest first/last radial-cell ownership for measured
faceting slivers only when the radial excursion stays within 2 µm +10⁻⁷ mm.
Every facet area is assigned once; no sliver is discarded, no centroid chooses
the whole triangle's material cell, and no material ownership is imposed on
shared gas nodes. Beyond the bound, the run stops.

The independent preflight at
`runs/wo03-surface-chords-20261031T050517069088Z/record.json` covered all 1,086
liner end facets. Maximum radial excursion was **0.995072 µm**, assigned endpoint
projection area **0.122541654 mm²** over the two ends, and the maximum basis-sum
residual was **1.11×10⁻²¹ m²**. Signed and absolute area errors are retained
separately in the final facet ledger. This does not establish boundary-assignment
or axial transient convergence.

The baseline's axial half-length remains L/2=93.5 mm, a coarse one-axial-cell
hypothesis. The documented L/4 and L/8 sensitivities need consistent axial
capacity refinement before use. The local chord rule does not overwrite that
explicit primary-selected liner mapping or collapse its radial temperatures.

## Physical mass and component identities

The capacity ledger keeps **339 BRep component identities** and actual source-part
mass totals. Each homogeneous component gets a proposed mass fraction from its
actual volume; those fractions sum the source mass once. The liner's one physical
component retains 16 radial substate fractions. The motor's physical mass remains
recorded, but its prescribed surface does not receive an invented finite thermal
capacity. This gives **353 proposed finite-capacity bulk IDs**.

The preflight covered-part source mass is 0.511872354475 kg, allocated once with
maximum per-part residual 8.67×10⁻¹⁹ kg. The whole candidate is 0.846009911213 kg;
parts outside the selected gas domain are listed explicitly, not deleted from
vehicle mass. Purchased-envelope internal mass fractions are hypotheses, not
measured shaft/head distributions. The ledger includes material/cp ranges,
original STEP hashes, all component source-face indices and exact component
bounding boxes **only for primary contact-query culling**.

Connected-solid identity is sufficient for geometry ancestry, not for internal
isothermality. In particular, the long sparse mount is one connected body with
potentially large internal gradients. Six purchased shaft/head BRep solids do
not establish six physically isolated fasteners. No component temperatures are
automatically shared through threefold geometry or equal material names.

Primary may separately test the historical parent-part mean-temperature
approximation. With component-to-parent incidence S, `Bparent=Bcomponent*S` and
`Dparent=SᵀDcomponent*S`, and parent heat is `SᵀQcomponent`. Source-part capacity
is then counted once. This is mathematically compatible, but imposes identical
component bulk temperatures/infinite redistribution within each parent. It does
not justify local temperatures, contact allocation or an acceptance claim. The
16 liner cells and distinct prescribed motor boundaries must remain distinct.

The separately generated `component-bulk-parent-map.json` explicitly maps all
353 finite bulk IDs to **152 parent thermal IDs**, preserving the 16 liner cells.
It supplies projected parent masses/capacities, original part totals and operator/
capacity hashes for the primary's optional diagnostic. It does not adopt that
projection or allocate contacts. Physical motor mass remains in the ledger;
its prescribed surface is not a finite bulk state.

Existing direct/lumped solid contacts stay separate. Contact routing requires
actual touching-component/area evidence; no old part-level contact is blindly
replicated or divided by three. `ChordField(cfg, frozen_face_rows).solids[id]`
exposes the exact placed source `cq.Solid`; `source_faces[part_id]` retains the
original source-face order for primary geometry contact queries. This script
does not implement a contact solver.

## Output contract and limits

On complete execution, `wall-quadrature-screen.npz` contains only Robin material
rows plus their original fine-boundary triangle indices and CAD-face/group IDs.
`wall_matrix_w_k`, `bulk_load_vector_w_k`, `bulk_diagonal_w_k` and `bulk_index`
describe ordinary one-bulk rows. Index −1 specifically means an explicit liner
multi-bulk row; its separate `liner_bulk_load_vectors_w_k` and
`liner_bulk_diagonals_w_k` arrays and 16 bulk indices supply all connections.
Unused scalar/B/D fields are NaN sentinels with declared meanings, never zero
conductance or missing insulation. JSON resolves bulk IDs, independent motor
end/opening temperature inputs and independent radiative brightness inputs.

These preintegrated matrices belong to the **exact original fine optical
triangles and vertices**. A differently triangulated Gmsh gas boundary cannot
copy them merely by matching CAD-face IDs. It needs explicit CAD-face/component-
constrained field transfer and boundary quadrature, or new source queries. No
such mesh transfer or gas/ODE coupling is performed here.

Verification checks known slab and inner/outer ring chord lengths, material-
outward versus gas-outward normals, reversed-normal rejection, independent disk/
triangle area and moment integrals, full facet strip coverage, constant-h triangle
mass recovery, wall conservation and the positive quadratic energy. One targeted
pytest fixture, Ruff and Black pass before the full run. Geometry, material and
solver acceptance remain distinct.

Post-run algebra checks retain raw matrices without clipping. Maximum ordinary
row/B/D conservation residual is **5.68×10⁻¹⁴ W/K**; liner row residual is
**5.39×10⁻²¹ W/K**, and per-cell B/D residual **5.76×10⁻²² W/K**. After positive
local scaling, minimum raw augmented-wall eigenvalues are −2.33×10⁻¹⁶ ordinary
and −7.37×10⁻¹⁵ liner, within the declared 10⁻¹² relative roundoff tolerance.
Those tiny negatives are recorded, not clipped. All boundary triangles are
covered exactly once. These checks establish the assembled wall algebra only;
they do not establish physical conduction, temperature convergence or a
conservative complete-CAD thermal bound.

Replay the exact API comparison with
`.venv/bin/python scripts/wo03_surface_chords.py --stage cache-benchmark`.
`--stage benchmark` records the current configured implementation's bounded
timing; it does not overwrite the historical original 300-second capped record.
The separately authorized full stage uses `--stage full --supervise`. Keep the
original capped record and consult final input hashes/status before consuming any output. No
physical work, purchase, active/core edit, Git action or flight release occurs.
