# One default volume-only optimization of the old medium PLC

This is one primary-authorized mesh-method trial, following the completed
[five-cell medium diagnosis](wo03-medium-mesh-diagnostic.md). It changes only
Gmsh's volume connectivity/interior mesh through one default optimizer call.
It does not alter source CAD, the optical PLC, seed spacing/jitter, material
properties, validity thresholds or any thermal parameter. No PDE or heat
calculation is performed. Completion, geometric validity, numerical solution
accuracy and temperature acceptance remain separate outcomes.

Executed directory:
`runs/wo03-optimized-plc-mesh-20261031T055336322017Z/`.
The actual trial **completed but remains invalid**. One optimizer call removed
the five zero-volume cells while preserving every fixed boundary coordinate bit
and labelled facet, but produced duplicate volume connectivity and nonmanifold
tetrahedral face incidence. The unchanged validator rejected it. No accepted
medium mesh was exported. There is no retry or next optimizer in this study.

## Exact authorized method

The frozen original source is the fitting `69df790e…` candidate, with its original
71,917 boundary vertices, 144,690 labelled optical facets, actual STEP, verified
face mapping and 3 mm deterministic lattice with ±4% jitter /RNG seed 319451.
The baseline configuration SHA256 remains `cf7ffd260915fbb0666dc65bea061072d5f45a00aa8f39f63e1d325a385aee71`.
The shared source module, fixture builder and medium diagnostic are hash-pinned
and unedited.

A local wrapper calls the existing `mesh.generate(3)` once. After it returns,
the wrapper saves complete pre-optimization raw node tags/coordinates, tetrahedron
tags/connectivity and all surface node tags/face/entity labels. It then calls:

`gmsh.model.mesh.optimize(method="", force=False, niter=1, dimTags=[(3, volumeTag)])`.

The installed Gmsh 4.15.2 API documents the empty method as its default
tetrahedral optimizer, with `dimTags` restricting the selected entities.
See the [Gmsh reference manual](https://gmsh.info/doc/texinfo/). Exactly one volume
must exist. No Netgen, `force=True`, 2D optimizer, additional optimizer call,
manual cell removal or manual point relocation is used. Algorithm-internal
operations are retained in the raw Gmsh log, not presented as unchanged volume
connectivity.

Post-optimization raw data are saved before immutable-boundary or production
mesh validation. The optimizer's own native error, if any, is preserved and
stops the trial. All generation, optimization, raw I/O and actual validation fit
within one supervised **300-second**, one-CPU worker, capped at 150,000 nodes
and 750,000 tetrahedra. Timeout means incomplete; it does not establish numerical
failure or a mesh pass.

## Immutable boundary and unchanged validity guards

The boundary guard uses the original Gmsh node tags, not array position alone.
For every original tag 1…71,917, its pre-optimization IEEE-754 coordinate bits
must equal the source PLC and its post-optimization bits must equal the pre bits.
The comparison includes signed-zero bits; it is not a tolerance test. Missing
tags or any bit change stop the trial without resetting the point.

All labelled triangle-node-tag triples and original CAD-face/entity labels are
compared as exact multisets before and after optimization. Reordering is not a
new surface, but any split, removed, added or differently labelled facet fails.
The existing source-coordinate, fixed/exterior facet correspondence, original
face ownership, outward winding, face/group area, PLC volume closure, positive
volume and minimum scaled determinant checks remain unchanged. No zero-volume
cell is dropped, and a tiny positive replacement still has to pass the original
scaled-determinant criterion.

If validity passes, a mesh is exported with the existing exact original-facet
correspondence. Geometry/coverage passage does not establish gas conditioning,
PDE accuracy, refinement convergence, temperature acceptance or physical release.

## Fixtures before the actual attempt

The exact flattened/repeated-index/coincident-coordinate classifier checks run
first without Gmsh. Two small existing PLC fixtures then receive the same one-
call volume optimization at the single fixed 3 mm spacing:

| Fixture | Independent check |
| --- | --- |
| Cavity | 3,904 mm³ analytic fluid volume; immutable boundaries; complete unchanged production checks; no tetrahedron centroid in the excluded inner cavity |
| 20 µm barrier with a 2×2 mm window | 7,992.08 mm³ analytic fluid volume; immutable boundaries; complete production checks; tetrahedron edge intersections at x=9.995, 10 and 10.005 mm remain within the actual window |

These are method fixtures, not a mesh-size sweep. Both passed in the fixture
worker before the one actual attempt was launched. The barrier section checks
retain their explicit geometric scope and do not constitute a heat-flow test.
No failed fixture is waived to reach the actual geometry.

## Artifacts and outcome

The top record contains separate fixture and actual stages. Each stage retains
its worker log and phase record. Every case has:

- `pre-optimization-raw.npz` and `post-optimization-raw.npz` with all raw node,
  volume-element and labelled surface arrays.
- `optimizer-call.json` with the exact native call, selected volume, count and
  elapsed time.
- `immutable-boundary-check.json` when that guard returns successfully.
- `returned-post-mesh-BEFORE-validation.npz` before the original validator can
  change orientation indices on its copy.
- `post-raw-determinants.npz` and `post-counts-and-zero-cells.json` with every
  signed determinant and all zero-cell indices.
- A normal mesh/group/correspondence export only if all existing checks pass.

The completed actual worker took **250.07 seconds**, or **256.16 seconds** under
its supervisor, below the 300-second cap. The single default optimizer call took
**14.1642 seconds**. Both fixtures passed first; their worker took 1.129 seconds.
All pinned inputs and frozen physical source hashes remain unchanged.

| Evidence axis | Actual result |
| --- | --- |
| Completion | Complete within the one authorized cap |
| Mesh validity | **Invalid**, rejected for nonmanifold tetrahedral face incidence |
| PDE/solution accuracy | Unavailable; no PDE or heat calculation |
| Temperature acceptance | Unavailable; no thermal result or margin |

| Quantity | Before optimizer | After optimizer |
| --- | ---: | ---: |
| Nodes | 90,580 | 90,580 |
| Tetrahedra | 549,653 | 502,251 |
| Floating zero-volume tetrahedra | 5 | 0 |
| Duplicate tetrahedron occurrences beyond unique vertex sets | 0 | 2 |
| Faces with incidence greater than two | 0 | 3, each with incidence four |
| Raw exterior faces | 144,692 | 144,692 |

All **71,917 original coordinates are bitwise identical** before/after and to
the source PLC; maximum coordinate delta is zero. All **144,690 original
labelled surface facets** are unchanged. These boundary checks are necessary,
but they do not make an invalid volume mesh usable. In particular, the raw
exterior count still exceeds the fixed PLC count by two; the production
validator stops at nonmanifold incidence before its complete exterior check.
No implication that the later guards passed is made.

The three offending post-optimization face triples, expressed in **original
Gmsh node tags**, are `[7388,9928,91171]`, `[7388,25205,91171]` and
`[7388,91171,91434]`. Each belongs to four tetrahedra. All bad-face and duplicate-
tet vertex sets are retained in `pre-face-incidence-diagnostic.npz` and
`post-face-incidence-diagnostic.npz`; nothing is removed. This read-only follow-up
took 4.95 seconds and generated no mesh. Pre-optimization node tags, coordinate
bits and tetrahedral node-tag connectivity match the immediately preceding
unoptimized diagnostic **bitwise**, demonstrating that this optimizer acted on
that same captured mesh. Exact identity with the much older lost original raw
arrays remains unavailable.

The native optimizer log reports 122,676 edge swaps, 964 node relocations and
a warning that 71,790 ill-shaped cells remain. These are native method messages,
not a successful geometry or accuracy criterion. The explicit production
topology rejection controls the result.

| Artifact | SHA256 |
| --- | --- |
| Top `record.json` | `4af013776468648739999e5c6aede1ebbf67750f7c7787198dbf7e8343207ee7` |
| Top `outcome-summary.json` | `f87f56fbc43fad04e1ae7d8fcc10304ca31c65cdc1c3c09aadca6157a81de1c5` |
| Actual `pre-optimization-raw.npz` | `43701b5cf6d839470b6610d2e4a7f7bbc980847b6c599d57a09ab3c436b9f858` |
| Actual `post-optimization-raw.npz` | `7d3fb6b74982e295b209d753dfe9138e78aa3b9c8ff7db69affab30a423f688d` |
| Actual `immutable-boundary-check.json` | `0371c022e738677ea1fe43c6a7c22c72a1d863ee887c555833e63c6018426d8d` |
| Actual `validation-failure-diagnostic.json` | `5054fdd8100c3c3b443da5a686f9ae0535beb967fbb3a9c146e0badbf7c60a5c` |

Actual case artifacts are under `actual/actual_medium/`. The actual worker's
general error field is refined by the top `outcome-summary.json` and the exact
post-failure diagnostics above: execution is complete and mesh validity is
invalid, while accuracy and temperature acceptance are unavailable.

This failed validity result ends the trial. The original unoptimized medium
failure and incomplete fine attempt remain historical evidence; neither is
overwritten. The separate primary-owned coarse temperature diagnostic has its
own source, solve and accuracy boundaries. No manual cell deletion, further
optimizer, changed threshold or additional actual generation follows here.

The runner is `.venv/bin/python scripts/wo03_optimized_plc_mesh.py`; executing it
again requires new explicit authorization. Ruff/Black checks pass. No shared/core,
active configuration, Git or UI files are edited; paid compute cost is $0.
