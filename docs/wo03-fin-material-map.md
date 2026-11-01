# G12 layered-fin solid ownership map

**All 60 saved fin solids have a unique, geometry-checked nominal material
and fin-angle mapping.** This closes the solid-identity ambiguity in the
[ownership preflight](wo03-root-source-ownership.md) for the exact historical
STEP and the validated G12 `4ff75b8f…` candidate. It does **not** identify
contact faces or establish a bond, installed-root, strength or flutter pass.

The source STEP SHA-256 is
`74a4a92bc27034ca1d1a2bda893e3ce4fe7e37a70fc1e74c0ba92ca689534285`;
the resolved candidate file is `8528d3f5…`, and its canonical resolved identity
is `4ff75b8f…`. The recorded
`configs/studies/wo03-trainer-fin-package.yaml` `root_closure` matches the
candidate's embedded layered-study parameters exactly. The resulting mapping,
all input and code hashes, source and regenerated centroid/bounding box/volume,
matched source STEP index and two-way Boolean differences are in
`build/wo03-fin-material-map-v1/record.json`.

## Method and result

`src/analysis/layered_fin_geometry.py` contains only the two needed geometry
functions, with unchanged ASTs from the original historical driver
`479e1f2035ca71d65af1f28316a4f3af4dc2684eac1def04703e9107a674e5e4`.
The `_part` AST hash is `df0fbfda…`; `layered_shapes` is `e6aa54c0…`.
The new helper imports the existing published CAD primitives and vehicle
schema, not the unpublished historical driver. It lives outside `src/cad`, so
no extra CAD-generator file is introduced into the saved preview's CAD-source
revision. Input/source/config hashes were recorded before and after the child
and were unchanged.

The recipe generates 20 named aggregate groups, each with three fin sectors.
For each generated solid, the comparison first identified a unique source STEP
solid using centroid, bounding box and volume; it then computed both
`generated − source` and `source − generated` BRep volumes. Each of 60 solids
had exactly one candidate, no source solid was reused, and all two-way Boolean
symmetric differences were reported as **0 mm³** by the geometry kernel, below
the existing 1e-4 mm³ threshold. The one-to-one solid comparison accounts for
the entire 60-solid source; source STEP indices in the record are locators for
this exact hash, not an assumed importer-order identity. Angles 0°, 120° and
240° identify the fin sectors, and the recipe's names retain the ± sides.

The resulting nominal ownership is 9 plywood, 3 PVC foam, 6 carbon sheet,
24 epoxy and 18 fiberglass solids. Those names and densities describe the
historical geometry/mass recipe; they do not establish measured material
properties, cure or hot allowables. **193** solid pairs with
positive-volume bounding-box overlap were checked by Boolean intersection;
the maximum reported overlap was 0 mm³. A separate read-only arithmetic check
of the other **1,577** pairs bounds their possible intersection by their
bounding-box intersection: the largest bound is 3.84e-11 mm³, below 1e-4 mm³.
Its source-record hash and method are in `overlap-bounds-postprocess.json`.
These are kernel/tolerance-based checks, not a proof of zero physical
manufacturing defects or complete bond contact.

## Remaining prerequisites

The exact G11 rounded-frame STEP is still one separate source solid; this packet
only maps fin-compound material solids. It does not map the specific tab,
curved-foot, pad, shell or frame **faces**, establish interface normals/areas,
prove bonding, classify local adjacency, or verify the shell's original exact
BRep. Full material ownership at contacts, compatible physical boundary
conditions, hot directional constants and peel allowables remain open. The
proposed installed-root case remains blocked before meshing until those
prerequisites are resolved. There is no new FEA, thermal simulation, flight
simulation, design change or release claim.

The one attempted child completed within the declared 120 s wall cap: parent
elapsed 5.436 s; worker 5.118 s wall and 7.495 CPU s; peak process RSS was
513,458,176 bytes. One worker and one-thread environment variables were
requested, but CPU time exceeded worker wall time, so single-core execution
was **not demonstrated**. The packet did not repeat any attempt. Black, Ruff
and a focused AST/prefilter/material-name test passed; these checks do not
qualify the engineering model.

Reproduction needs the exact source STEP and reconciled candidate, which remain
ignored local artifacts and are not supplied by the published recipe alone.
Use a private hash-pinned archive for those dependencies rather than assuming a
clean checkout contains them or committing bulk generated geometry.

The [published compact record](../runs/wo03-output-solid-map-20261101T011408613691Z/record.json) includes the
solid map, overlap bounds and as-run helper source. A later typing-suppression
comment leaves both extracted function ASTs unchanged; no CAD rerun or geometry
change was made. Private STEP/resolved artifacts remain reproduction inputs.
