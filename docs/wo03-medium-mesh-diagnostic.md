# Original optical-PLC medium mesh: one raw diagnostic replay

This study separates **run completion, mesh validity, solution accuracy and
temperature acceptance**. A resource cap establishes an incomplete run, not a
numerical failure. The historical fine attempt stopped at 300 seconds before a
mesh was returned; its validity and accuracy remain unavailable. The valid
coarse mesh does not establish medium/fine validity, mesh convergence or thermal
acceptance.

The single deterministic medium replay is recorded at
`runs/wo03-medium-mesh-diagnostic-20261031T054315503972Z/record.json`.
It completed in **145.15 seconds** supervised /141.05 seconds worker time and
reproduced the original 90,580-node /549,653-tetrahedron counts. The medium mesh
is **invalid: five exact zero-volume tetrahedra** were retained and diagnosed.
No tetrahedron is removed, node moved, mesh optimized or geometry repaired by
this diagnostic. No heat calculation is performed. Root owns the subsequent
mesh-method decision; this is not the new native-boundary pilot.

## Frozen source and one-attempt method

The original `configs/studies/wo03-cad-gas-mesh.yaml` is unchanged, SHA256
`cf7ffd260915fbb0666dc65bea061072d5f45a00aa8f39f63e1d325a385aee71`.
It uses the actual fitting `69df790e…` source STEP and the original 71,917-node /
144,690-triangle optical PLC, the verified native-face mapping, and the original
3 mm interior lattice. The axes start at fractions 0.371/0.217/0.413 of lattice
spacing; NumPy generator seed 319451 adds the same ±4% jitter. Seeds must be
inside the actual CAD fluid and clear the fixed PLC by the original 0.005 mm.
No new random seed, boundary, size field, Gmsh algorithm or optimization option
is selected.

The replay calls existing `interior_seeds`, `tetrahedralize` and
`verify_volume_mesh` in `src/analysis/cad_gas_mesh.py`. The current shared module
hash `acc1e735…` differs from the historical `c9780fd7…`; that difference remains
explicit. The original raw arrays were lost, so original mesh connectivity and
offending indices cannot be recovered by assertion. Matching settings, counts
and failure pattern can be demonstrated by replay; bitwise identity with the
lost original arrays cannot.

Before the actual run, a small deterministic diagnostic distinguishes:

- Four distinct coplanar vertices, with zero exact binary-coordinate determinant.
- A repeated node index.
- Distinct node indices with identical coordinates.
- A proper nonzero-volume tetrahedron.

Those checks require no Gmsh attempt. The one actual worker is supervised at
300 seconds, one CPU worker, at most 150,000 nodes and 750,000 tetrahedra.
There is no retry. Timeout retains the current phase, log and available atomic
artifacts and reports validity/accuracy as unavailable unless their checks
actually returned.

## Raw data preservation before validation

Read-only observers on Gmsh's `getNodes` and three-dimensional `getElements`
save their original return arrays without changing them. All node tags,
coordinates, element tags and tetrahedral node tags are saved **before** the
shared extractor's fixed-boundary validation. The extractor's full returned
arrays are then saved before `verify_volume_mesh` is called on a copy; original
tetrahedral ordering/orientation is never overwritten by the validator.

| Artifact | Meaning |
| --- | --- |
| `Gmsh-raw-nodes.npz` | Original Gmsh node tags and full coordinates in mm |
| `Gmsh-raw-volume-elements.npz` | Original 3D element types, tags and tag-based connectivity |
| `raw-mesh-BEFORE-validation.npz` | All sorted SI nodes, zero-based tetrahedra and labelled/fixed surface arrays returned by the existing extractor |
| `raw-mesh-settings.json` | Actual unchanged Gmsh settings and source-boundary count |
| `retained-seeds.npz`, `seed-info.json` | Exact deterministic input seeds and their source classification counts |
| `all-raw-determinants.npz` | Every production-form signed determinant and all exact floating-zero indices |
| `all-zero-cell-classification.json` | Every floating-zero cell's raw IDs/coordinates, local coordinates, SVD, distances and exact binary-rational diagnostic |
| `detailed-zero-cells.json` | Bounded detailed source-facet/CAD-face/group ancestry and nearest actual solid clearances |
| `progress.json`, `worker.log`, `record.json` | Explicit phase, engine output, outcome axes, provenance and completeness |

The production criterion is the existing SI floating-point scalar triple
product divided by six. A separate exact rational determinant uses each stored
binary coordinate as an exact rational number; it diagnoses exact coplanarity
versus cancellation/near-coplanarity. It does not repair a cell or overrule the
production validator. Local translated coordinates and singular values are
diagnostics, not perturbed mesh inputs. The linear-tetrahedron determinant
definition follows the existing module's Zienkiewicz–Taylor reference; API
readback follows the [Gmsh reference manual](https://gmsh.info/doc/texinfo/).

Boundary-node ancestry remains set-valued at edges: all incident original source
facets, original CAD-face IDs, radiation group IDs and part histories are
reported. No shared node receives an invented single material owner. Interior
nodes are compared against exact retained input seed positions; unmatched nodes
are identified as Gmsh-created. Nearest solid distances use hash-checked actual
placed STEP parts, including finite notches/seams, without regeneration or a
second placement transform.

## Outcome and limits

| Evidence axis | Result |
| --- | --- |
| Completion | Complete within the single 300-second cap; unchanged inputs |
| Medium mesh validity | Invalid: five zero-volume cells; subsequent complete exterior/area/volume validity checks cannot pass this mesh |
| PDE/temperature solution accuracy | Unavailable; no PDE or heat calculation |
| Temperature acceptance | Unavailable; no temperature field or required-case matrix |
| Historical fine attempt | Incomplete at its 300-second cap; numerical validity/accuracy were not returned |

All original count targets match: **17,901 seeds, 90,580 nodes and 549,653 tets**.
Gmsh 4.15.2 also repeats all recorded non-timing event counts: 89,818 initial
tetrahedrization nodes, 89,826 after tetrahedrization, 1,721 Steiner points,
91,539 pre-final refinement nodes, nine star-shapeness cavity changes, 25,918
nodes not inserted, and 797 algorithm-internal relocations. The original and
replay settings both disable optional optimization; these internal algorithm
messages are reported, not new repair actions. Timing/log instrumentation and
the enriched validator error text differ. Matching counts and zero-cell failure
pattern are demonstrated; exact original-cell identity is unavailable because
the original arrays were not saved. No original bad-cell IDs are invented.

The replay zero-cell indices below are **zero-based**. Every one has four
distinct node IDs, four distinct coordinate triples and exact binary-rational
determinant **zero**. None is a repeated-ID or coincident-coordinate cell;
none is merely a floating-zero determinant with a nonzero exact determinant.

| Replay tet ID | Node indices | Observed flat connectivity / ancestry |
| --- | --- | --- |
| 523697 | 10055, 7387, 9927, 90343 | Three original boundary points have identical X/Y at Z=1187.4, 1200 and 1190.4 mm; fourth point is Gmsh-created |
| 523698 | 7387, 10055, 9927, 90344 | Same collinear original triple; another Gmsh-created fourth point |
| 529277 | 8936, 5827, 5828, 3142 | All original boundary; three points share X/Y at Z=1141.5, 1177 and 1180 mm |
| 530853 | 5828, 29191, 8936, 3142 | Same collinear mount-bore triple plus an original foil-edge boundary point at Z=1200 mm |
| 544064 | 9927, 7386, 9926, 7387 | All original boundary; two X/Y positions ×two Z stations form a coplanar four-corner patch |

The first, second and fifth cells are associated with the actual **R1.7 mm
retainer bolt-clearance hole** in the mount, centred at CAD X/Y=
12.75/22.0836478 mm (radiation group 99). Their boundary labels also retain the
adjacent Z-plane groups; no edge node is assigned only one face. The third and
fourth involve **R15.8 mm mount bore** group 62 at distinct ring stations; the
fourth additionally includes original foil outer R15.12 mm /aft-end groups
524/555. That is a geometric connectivity observation, not proof of the internal
Gmsh algorithmic cause or a guarantee that another method fixes it.

The two non-boundary fourth vertices are Gmsh-created indices **90343 and
90344**, not retained jittered input seeds. Their nearest actual mount-solid
distances are **0.000643793 mm** and **0.000003391 mm**. All five cells contain
no retained seed vertex: there are 18 original-boundary vertex occurrences and
two Gmsh-created occurrences across their 20 vertex slots. Thus coincident
jittered input seeds are not the observed mechanism of these five cells.
Smallest pair distances per bad cell are 3.0, 3.0, 0.354544, 3.0 and
0.0847644 mm. Local SVD minima remain in floating roundoff while the separate
exact determinants establish coplanarity of the stored data.

All five receive full detailed ancestry/clearance records, below the diagnostic
cap of twelve. For every original boundary vertex, the record lists all
incident original facets, CAD-face/group IDs and part histories. Node and
centroid nearest-solid distances are calculations against the actual CAD,
not manufactured clearance measurements. Frozen physical STEP/PLC/inventory/
group sources were hash-checked again after completion and remain unchanged.

| Preserved artifact | SHA256 |
| --- | --- |
| `record.json` | `a667347c1f10ddaee9b49438b62e9585dd549fd4f95fb672574fb4638fb96084` |
| `Gmsh-raw-nodes.npz` | `5c732e84e4382d7caded1c3d51ef8464706055397522d103b0537be8a2c58692` |
| `Gmsh-raw-volume-elements.npz` | `ee779f68313aef1156ec2796d53a1b538d2084f8028087512622a267ae31cdcb` |
| `raw-mesh-BEFORE-validation.npz` | `da5378bf641eee16e4cc79d1cf1b78fc1ec39adb961157e9df110f60ab50f0e5` |
| `all-zero-cell-classification.json` | `4e89ef5fa506947491005bb9e9de368db7a0a1c30ed4598277007f0ccdcec94a` |
| `detailed-zero-cells.json` | `24f64f4f6b79a4472542f04ccc4621b93d4392b04bc015d5d26bb0d40dbc1e20` |
| `replay-comparison-and-ancestry-summary.json` | `ff1371c3e5b90e83b58ab80d4ee6a37f6a918bbd70320a9e392245a469ebb3a5` |

Mesh validity requires every stated production geometry check. Execution
completion alone cannot pass it. Solution accuracy would additionally require
appropriate PDE/energy/reference checks and mesh convergence; no PDE is solved
here. Temperature acceptance additionally requires the actual required case/
property/boundary matrix and its model-validity limits. No missing result is
replaced by zero, a coarse pass, or a thermal margin.

Reproduce only under a new explicit one-attempt authorization with
`.venv/bin/python scripts/wo03_medium_mesh_diagnostic.py`. The study does not edit
shared analysis, active configurations, Git or UI, and uses $0 paid compute.
The known flattened/duplicate/coincident fixture, Ruff and Black pass. The one
authorized actual attempt is complete; no subsequent mesh generation, geometry
change, seed change, bad-cell removal or optimization is performed.
