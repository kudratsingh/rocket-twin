# WO-03 labelled actual gas volume mesh

This study fills the frozen fitting-baffle gas boundary with linear tetrahedra.
It assigns geometry provenance to every exterior triangle and retains shared
edge/corner nodes for the separate Robin workflow. It does not assign a node to
one material or temperature, assemble a conduction matrix, factor a matrix or
claim thermal/flight acceptance. Only the five new gas-mesh files and ignored
outputs belong to this task; the previous radiation implementation/results and
outer fin/root failure remain frozen.

The source is candidate
`69df790ec9bcba1465be4fa9861a7ad5fbc467091cbf58f44dee069e56e00bac`.
The handoff is
`build/wo03-cad-radiation-fitting-baffle-fine-bounded-v1/gas-boundary-handoff.json`,
SHA256 `f8282389c9ccdff6d68789c01f03fc052c49ebb7c3c2b33a04559bcac644ef26`.
It supplies the actual interior R32.5 mm, station 990–1212 mm fluid STEP,
1,785 original face records, 1,127 suggested radiation groups and the complete
fine boundary mesh. Every selected input hash is verified. No new Boolean or
analytic annulus replaces the actual geometry. All notches, seams, remaining
slots, finite supports, material barriers and unknown reservoir patches remain.

Native Gmsh 4.15.2 import is matched to the original faces by CAD area, bounding
box, actual projected interior point, normal and up to three additional
projected facet samples checked inside the trimmed surface. `Face.Center()` is
not a label sample. Surface tags are deliberately offset above 10,000, so
numeric entity order cannot masquerade as provenance. The mapping must be a
bijection and every surface must bound exactly one gas volume. Automatic CAD
healing, small-edge/face fixing, sewing and scaling are disabled.

The executed mapping at `build/wo03-cad-gas-native-mapping-v1` verifies all
1,785 faces in 2.16 seconds. Maximum exact interior-point residual is
4.81e−13 mm. Native volume is 475,607.907581977 mm³, agreeing with the source
CAD and verifying millimetre units. This is separate from material/half-wall
physics; the later 339-component material mapping does not turn mesh labels
into temperatures or h values.

Volume meshing uses the same closed, labelled piecewise-linear complex (PLC)
as the actual fine radiation boundary: **71,917 vertices and 144,690 triangles**,
with its documented 2 µm geometric approximation. Rebuilding isotropic curved
surfaces could cross 20 µm opaque rims or exceed the resource cap. The primary
therefore authorized retaining this actual boundary tessellation. Gmsh fills a
surface loop containing all original per-face discrete surfaces. No face is
deleted, no hole is filled and no boundary vertex is moved to meet a budget.

The input facets are wound **outward from gas**, into solid/reservoir; the
radiation estimator emitted in the opposite direction, into gas. Output tet
orientation can be corrected by swapping two indices only. Every fixed facet
must point away from its adjacent tet centroid. Any index reversal changes no
coordinate, geometry or face ownership. Gmsh's exported boundary triangles and
the exterior faces of all tets must both match the exact original facet keys
and original CAD face IDs, each exactly once.

Interior spacing is an explicit deterministic lattice at 4/3/2 mm, with 4%
jitter to avoid exact coplanar/cospherical grid degeneracy. Seeds must be inside
the original actual STEP and more than 0.005 mm from the PLC boundary; the
clearance keeps them outside the known boundary-approximation uncertainty.
Omitting a near-boundary seed does not remove that gas region: every boundary
facet still constrains the volume fill. Point/curvature/boundary-derived size
fields are disabled and the nominal automatic size is large; Gmsh can still
insert/remove/relocate interior recovery/refinement points. Final counts, not
initial seed counts, determine acceptance. Background size alone produced
identical interiors in a prototype, so it is not used as false mesh refinement.

Each worker is a separate single-CPU child with a hard **300-second** deadline.
It stops before export/any solve if it exceeds **750,000 tets or 150,000 nodes**.
Mapping is a separate bounded worker. Tet determinants must be nonzero, the
scaled determinant must exceed 1e−14, every internal face must occur twice,
and every exterior face must have its actual label. Tet volume must close to
the fixed PLC within relative 1e−6. Per-face CAD area error must stay below 2%
and per-group error below 0.5%; all individual errors are reported. These are
geometry/mesh checks, not solution-conditioning or thermal acceptance.

The independent fixture run is
`build/wo03-cad-gas-fixtures-v1/report.json`. All nine meshes pass:

| Fixture | Coarse nodes/tets | Medium nodes/tets | Fine nodes/tets |
| --- | ---: | ---: | ---: |
| Split wall | 39 / 168 | 48 / 222 | 137 / 770 |
| Closed cavity | 77 / 350 | 234 / 1,227 | 504 / 2,746 |
| 20 µm barrier with window | 149 / 772 | 365 / 2,113 | 1,024 / 6,379 |

The split wall retains common edge nodes with two different facet labels.
The closed cavity has no tets in the opaque interior. The finite thin barrier
and its window remain present. All exact source facets/labels, positive tet
volumes, outward normals, known volumes and complete exterior coverage pass.

The first actual coarse mesh at `build/wo03-cad-gas-actual-v1/coarse` completes
in 62.76 seconds: **80,186 nodes = 71,917 boundary + 8,269 interior**, with
**427,940 tet4**. There are 7,590 initial actual-fluid seeds; Gmsh's final
interior population differs. All 144,690 boundary facets and all 1,785 original
faces are retained exactly. The PLC volume residual is 1.18e−14 relative.
The fixed-boundary approximation remains 0.3099% maximum per-face area error
and 0.06191% per-group error against CAD.

The coarse result SHA256 is
`415fa9c983b3c53ecc4a908355996b83b1476eec3a6dbf08f08b0a577ad061f4`;
its `mesh.npz` SHA256 is
`aefc71e318393ae781fefb5e5d2195eb6383dc32214f292eb4445f1de86b4351`.
Minimum coarse tet volume is 1.13427e−18 m³ and minimum scaled determinant is
2.00784e−12. These expose very thin/sliver cells; no good conditioning or
solution accuracy is inferred from positivity. The 25,000-free-DOF Robin
guard cannot accommodate 80,186 potential gas unknowns before the primary's
prescriptions. No facet is discarded to make a solver budget pass.

The bounded refinement result is **partial and failed overall**:

| Actual volume level | Generated nodes | Generated tets | Outcome |
| --- | ---: | ---: | --- |
| 4 mm coarse | 80,186 | 427,940 | Geometry/coverage/positive-tet checks pass |
| 3 mm medium | 90,580 | 549,653 | Rejected: zero-volume tet |
| 2 mm fine | Unavailable | Unavailable | Hard 300-second cap; no accepted volume mesh |

The medium worker fails in 119.70 seconds before exterior-facet validation.
Counts come from its preserved Gmsh log. Its initial failure path retained the
error and logs but not raw arrays, so offending cell indices,
boundary/interior membership, repeated-coordinate status and true/near
coplanarity **cannot be recovered from that record**. They are not invented.
Raw-failure capture is added for future explicitly authorized attempts.
The primary declined a diagnostic replay at this stage.

The separate fine attempt at `build/wo03-cad-gas-actual-fine-v1/report.json`
is killed at 300.05 seconds before any Gmsh meshing messages or completed seed
count. It is a capped failure, not a zero-node/zero-tet result. Both records
report unchanged source inputs during their executions. No subsequent actual
mesh attempt, bad-cell removal or solve is performed. The valid coarse export
does not establish refinement, conditioning or engineering acceptance.

`build/wo03-cad-gas-actual-v1/compact-summary.json` avoids the full per-face
area arrays while linking all original fixture/mapping/coarse/medium/fine
reports. Its SHA256 is
`d621a81842dff5a660bc5a68c8fc69d36091501b43d0665cbb6579cf6e2eeab7`.
The recommended next primary decision is **constrained volume-only quality
optimization before fine seed acceleration**: the known medium zero-tet already
blocks refinement. One candidate is Gmsh's standard 3D volume optimizer using
edge/face swaps and interior relocation, with every original PLC boundary
coordinate/facet immutable and every existing post-check retained. No surface
optimization or dropping bad cells is proposed. It has not been executed or
shown to fix this case; a separately approved raw medium diagnostic replay is
needed first to classify the offending cell.

The file contract accepted by the Robin agent is non-pickled `mesh.npz`:

| Array | Meaning |
| --- | --- |
| `points_m` | Float64 SI node coordinates, N×3 |
| `tetrahedra` | Int64 positive tet4 connectivity, M×4, zero-based |
| `boundary_triangles` | All outward gas boundary facets, B×3, zero-based |
| `boundary_group_ids` | Original integer radiation group per facet, 0–1126 |
| `boundary_face_ids` | Original CAD fluid face per facet, 1–1785 |
| `boundary_entity_tags` | Independently matched Gmsh entity, for audit |
| `boundary_area_m2` | Facet areas in m² |
| `boundary_outward_normal` | Unit outward-from-gas facet normals |

`boundary-groups.json` contains canonical `groups` rows with integer group IDs
and original part/family/face provenance, plus complete source hashes, native
mapping evidence, seed definition and diagnostics. No node-group ownership is
provided. The separate material mapper supplies kind/material/half-wall physics
by original face ID; sharing a gas node does not imply sharing h. Unknown gas
reservoir temperature and black radiation brightness remain separate physics.
Unlisted exterior faces are an error, never silent insulation.

Exact Robin quadrature transfer additionally uses
`boundary-source-correspondence.npz`:

| Array | Meaning |
| --- | --- |
| `boundary_source_triangle_ids` | Int64 original optical fine-boundary triangle row, zero-based |
| `boundary_source_vertex_permutation` | Int8 B×3, gas local j → original local permutation[j] |

For the current exporter, source facet rows and their outward-fluid order
are retained: IDs are identity and permutations are `[0,1,2]`. This is an
executed bitwise coordinate assertion, not an assumption about Gmsh ordering:
`points_m[gas_triangle[j]]` equals the original source vertex times 0.001,
and every source facet/original face ID appears exactly once. The module API is
`source_facet_correspondence(arrays, boundary)`; it rejects rounding/reordering
rather than guessing a map. Transfer both matrix axes and vector entries:
`Mgas[j,k]=Msource[source_id,perm[j],perm[k]]`,
`Bgas[j]=Bsource[source_id,perm[j]]`.

The existing coarse mesh hash remains unchanged. Its verified correspondence
NPZ SHA256 is
`cb020bcc3fe8de1d10e0cfe2574f1a2b456b58f1e067a42d449ecfef297dce0d`;
the companion JSON links it to the accepted gas mesh and source boundary
SHA256 `fc435123d45a21aefacea906b259d1a5298895092374ba12bc489c868c1c948e`.
Only coarse has full accepted validation; failed medium/capped fine do not
inherit it. Later code adds the same exact sidecar export and raw-failure
retention without changing volume generation or any recorded mesh.

Three focused fixture tests pass, including missing-boundary rejection,
wrong-original-face rejection, zero-tet rejection, resource rejection and exact
facet/local-basis correspondence. Black, Ruff and strict mypy pass for the
owned source and runner.

The three bulk meshes refine volume interiors on one fixed boundary. They do
not establish all-mesh/thermal convergence. The separate source boundary levels
5/2.8/2 µm and their CAD area/volume/radiation diagnostics remain in the frozen
actual-radiation records. Radiation changes also contain Monte Carlo error.
Both boundary and volume response must stabilize before any later solution
convergence claim. This task executes no conduction response.

Commands use the existing pinned environment and no installation:

```sh
.venv/bin/python scripts/wo03_cad_gas_mesh.py --stage fixtures \
  --output build/wo03-cad-gas-fixtures-v1
.venv/bin/python scripts/wo03_cad_gas_mesh.py --stage mapping \
  --output build/wo03-cad-gas-native-mapping-v1
.venv/bin/python scripts/wo03_cad_gas_mesh.py --stage meshes \
  --mapping-cache build/wo03-cad-gas-native-mapping-v1/mapping \
  --output build/wo03-cad-gas-actual-v1
.venv/bin/python scripts/wo03_cad_gas_mesh.py --stage meshes --level fine \
  --mapping-cache build/wo03-cad-gas-native-mapping-v1/mapping \
  --output build/wo03-cad-gas-actual-fine-v1
```

Choose fresh output directories for replay. Failed workers, logs, partial stages
and resource limits remain recorded. No active specification, shared physics,
CAD core, Git or UI writes are part of this task.
