# Two local geometry-only reference definitions

This source/data increment introduces two separately identified **geometry-only
planning references** from the already executed PR123 nominal local cases. It
runs no CAD/kernel, creates no instance and adopts no vehicle/product/stock.
The existing 55-record source bank, inspect-only template registry, frozen RP1,
AD1/D1 and existing engineering/physical gates remain unchanged. Five inquiries
remain UNSENT.

Authored definitions live in `configs/parts-bank/reference-local-v1.yaml`, actual
SHA-256 `a95d6147d1614c0939b266a297e43ec9d265585c30c445f1297554381713de07`.
The projection is `src.vehicle.reference_parts`; no existing producer, manifest,
store, API, UI or source YAML is modified.

| New definition ID | Original source link | Exact nominal geometry | Definition SHA-256 |
| --- | --- | --- | --- |
| `reference-local-v1:motor-tube-nominal` | `motor_tube`; `rp1-template:motor-tube-cut` | OD 31.369 / bore 29.169 / length 165 mm | `fd6c666dfed5d79ed44ed126b85d1de7dca87c1210165808b44f270e2ce2a42c` |
| `reference-local-v1:aft-annulus-nominal` | `aft_ring`; `rp1-template:aft-annular-ring` | OD 64.4 / bore 31.9 / thickness 6 mm | `158150615a9c291ce12b3320d535c11151a564d7ad176dda9ca9693025a5d710` |

The namespaced IDs identify nominal geometry, not installed RP1 occurrences,
exact purchased tube stock or a complete installed ring proposal. The motor-tube
product/dimension conflict remains explicit. The annulus does not acquire the
missing installed ring construction or qualified bonds.

## Source and file admission

The exact existing [geometry manifest](../frontend-template-bank-20261109/geometry.json)
is pinned at
`6316ccef56c168e14d8a14a6570d162f35eb43bcadf4bd6132226b51d91799d2`.
It records original registry revision
`cb43e923df940ba0a1f9ec80216a194bd1cbc85e92b1eac5c77f3e18b55fd9be`,
prepared snapshot identity, per-template revisions, frozen RP1 source pins,
generator/exporter code, exact frames and the executed STEP/GLB readback.
The projection verifies the actual known source/code/manifest byte hashes and
source nominal dimensions before emitting definitions.

| Existing local asset | Bytes | Actual SHA-256 |
| --- | ---: | --- |
| `motor-tube-cut.step` | 9,654 | `339faa3de20f1e0fef905831403de7450af78dedeb743ed8d5b32d946d69953f` |
| `motor-tube-cut.glb` | 19,864 | `f90c129bc300767b228e0195a6a528bc9e19bdd5a1f8d7752ab2f6eac4114336` |
| `aft-annular-ring.step` | 9,599 | `c006c932f7353b82cef9e7cc280bb0d46839b7442af141bcc81c39df40910c33` |
| `aft-annular-ring.glb` | 19,860 | `ca2a1f86438ea079d6b3433df9e9d275a4911639a1a6aaa5e9be408a4535e6b3` |

Only those four exact `output/rp1-template-geometry-v1/` asset paths are read.
The separate old public URLs are retained as provenance, but this new projection
does **not** verify the public cache or promise URL availability. It never scans
other files, searches alternate caches or regenerates missing outputs. Known
paths use bounded no-follow directory/file reads and reject symlinks, hardlinks,
nonregular files, foreign paths and changed byte/size hashes.

A missing local STEP or GLB gives `availability.status="unavailable"`, with the
missing formats and `generation_attempted=false`. The reference definitions and
their revisions remain stable; they do not borrow installed geometry or fill a
missing asset with a new mesh. Corrupt/foreign assets fail closed rather than
being hidden as absence. Missing or changed source/frame evidence makes the
projection unavailable rather than guessing a frame.

## Frames and analytic features

Native STEP uses **millimetres**, front-center origin, X = body +y,
Y = body −z and +Z aft along the local part. The unchanged generator's exact
operation is an XY annulus extruded from Z=0 to the stated length.
GLB uses **metres**, with the recorded mapping:

```text
viewer[X,Y,Z] = [cadX/1000, -cadZ/1000, cadY/1000]
```

This is a local reference frame. `installed_transform` remains null; the nose-tip
station frame and a new placement are not inferred. Recorded local CAD/GLB bounds
and old readback remain associated with their exact files. The original
readback/graphic error bounds are representation checks, not stock/fit tolerances.

Each definition owns exactly five scoped analytic references:

- `axis`: origin (0,0,0), direction +Z, axial range 0…L.
- `bore`: analytic cylinder of the exact nominal inner radius over 0…L.
- `outer_cylinder`: the exact nominal outer-radius cylinder over 0…L.
- `start_plane`: annular datum at Z=0 with radii Ri…Ro.
- `end_plane`: annular datum at Z=L with radii Ri…Ro.

Plane normals use a documented +Z datum convention, **not** an asserted CAD face
orientation. Feature IDs are scoped by their owning definition. They are
analytic names, not guessed persistent B-rep face or GLB triangle identifiers;
`cad_face_ids`, `mesh_triangle_ids` and `tolerance_mm` stay null. Every feature has
`mating_admitted=false`. `interfaces` stays null: overlap, annular dimensions and
matching-looking axes do not establish retention, contact, fit, strength or a
Connect contract.

## Callable seam and stable revisions

`build(root)` returns both definitions, source pins and separate per-definition
availability. `select_reference(root, reference_id, revision_sha256,
parameters_mm)` accepts only the exact known namespaced ID, definition revision
and three nominal radius/length parameters. Unsupported dimensions, parameter
names or stale revisions fail; neither selection nor a slider runs a generator.
The result explicitly says `instance_created=false`.

Definition hashes cover their complete metadata except their own revision field.
The catalog revision
`8f6b7bf2f0dcc8dfb2714ba7a28688c820869dc3045060aba6ea5901983b7748`
covers source/definition content, excluding its own hash and separate availability.
Both use the existing canonical Python JSON digest. Cache presence never changes
the geometry definition revision. Returned data is independent of later calls.

Mass, procurement cost, inertia, stock tolerances, strength allowables, thermal
capability and qualified material remain **null**, not zero. Original source
budget estimates are referenced only as qualified provenance and never become
new installed mass or procurement values. Add-instance/Connect API availability,
resolved-candidate, simulation, engineering, physical and flight readiness remain
false. There is no Add/Replace/Connect endpoint or existing-draft admission in
this increment. Later controlled planning-instance admission requires primary
review of this contract and its separate counted-function/interface boundaries.

## Verification and limits

Fourteen focused pytest cases pass. They check the actual registered host bytes,
source/code/manifest pins, nominal dimensions/frame/mapping, existing bore/closed-
solid readback, analytic datum geometry, null properties/false gates, exact-only
selection, independent returns, source/asset/frame/hash rejection and unavailable
cold caches with process execution/directory scans forbidden. Generator source is
parsed as text/AST only; `src.cad.parts`, CadQuery and a CAD kernel are not invoked.
Black, Ruff and strict module mypy pass.

A focused correction made installed-transform/mating missingness explicit and
kept the catalog revision scope inside the hashed source content while leaving
runtime availability separate. No old registry/manifest/exporter, shared module,
owner library or source was edited; no CAD/physics/FEA, browser/server/network,
contact, purchase or Git action occurred. Existing STEP readback is reused as
recorded evidence, not claimed as a new geometric or physical execution. API/UI
integration, actual rendering, complete installed construction and all
engineering/physical acceptance remain separate/open.
