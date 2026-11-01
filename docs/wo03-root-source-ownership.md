# G12 installed-root source ownership preflight

**Solid ownership is mapped and selected nominal contact patches are audited.** The
[subsequent material map](wo03-fin-material-map.md) uniquely matches all 60
historical fin solids using the preserved construction recipe and geometry
comparisons. The installed-root case still stops before meshing because its
complete load path and relevant hot properties remain unverified. The later
[face audit](wo03-root-contact-faces.md) establishes selected first-fin common
patches, including partial shell coverage; it does not establish physical bonds,
the complete interface mapping or installed strength. The initial preflight below is retained as historical evidence;
its solid-identity warning is superseded by the subsequent result.

## Initial preflight (historical)

## What exists locally

The G12 source is the refrozen `4ff75b8f…` resolved identity, not the 69df G54
candidate. Its ignored local artifacts include:

- `build/wo03-trainer-fin-root/pvc5-forward25-backed-reconciled/fin-layers.step`,
  SHA-256 `74a4a92bc27034ca1d1a2bda893e3ce4fe7e37a70fc1e74c0ba92ca689534285`;
- the matching `record.json`, SHA-256
  `59d4877ecda8aca354608093231a34f5dcf6eae8dacc06d1f237f6c85b147f97`;
- `build/wo03-recovery-clearance/hoop/recovery-cap-frame.step`, SHA-256
  `d012f27912f1c1c28c4d63bf9ef03c78c31c6abab61029d04e5e66c511221b54`;
- `runs/wo03-installed-root-20261031T041923712847Z/reconciled-source-only.json`,
  SHA-256 `8528d3f550ab31f53e51dcd894ce4dced1f3e6acec26f322d6f047270de192af`.

A read-only CadQuery import in one child took under 10 seconds elapsed and made
no geometry, mesh or solver changes. The fin STEP imports as a compound with
**20 immediate child compounds and 60 solids**, three solids per child. The
20 child volumes match the 20 aggregate layer volumes in the historical
ledger in their observed order to STEP import precision. The frame STEP imports
as **one valid solid**; the source proposal calls it G11. These checks establish
that the geometry can be decomposed into imported child objects, not that all
60 solids have been assigned and validated as analysis regions.

The ledger names the three-fin aggregates as root inserts/tabs, foam core,
two skins, two skin/core bond layers, two gusset sets, two curved-foot bond
sets, two gusset-face bond sets, tab potting, frame/shell gap pads, and six
front/rear cap-web or cap-lap groups. It records each aggregate's density,
volume, total mass, centroid and solid count. The recorded material recipe and
source code show how these named groups were constructed and exported in a
compound. The input STEP text, however, uses generic Open CASCADE product names;
searches for the layer names and standard material property/designation labels
found none. No per-solid material labels or face-to-interface IDs were found in
the saved evidence examined here.

Matching order and volume is useful supporting evidence, **not an ownership
proof**. Symmetric pairs have the same volumes, and each group is an aggregate
of three fins. The ledger's combined centroids do not by themselves identify the
first-fin side, individual solid, or its contacting face. STEP entity/order
stability across importers has not been verified. In particular, there is no
saved mapping from the first fin's tab, left/right foot bonds, and gap pads to
specific imported solid and face identities. The historical minimum-distance
checks show nominal contact somewhere for named pairs, not complete bond area,
continuity, wetting, adjacency or disjoint material ownership. The separate
mass allowance for cap bonding, tip seal and remaining root fillets is not an
identified physical solid merely because it appears in a mass ledger.

The frame's single imported solid can be assigned the proposed G11 **material
identity**, with its laminate orientation and hot directional properties
still unresolved. It does not specify which individual faces carry tab potting,
pads or support reaction. The shell's current generated representation and its
historical cached mass properties exist, but a historical separate shell STEP
and explicit common-face map were not established by the refreeze. The assembly
STEP is a display/assembly compound; it is not a material-labeled mesh or proof
of all physical connections. Neither source supports replacing unverified bond
regions with a full-area tie.

## Publication and minimum handoff

The primary agent checked the GitHub base tree: `configs/studies/wo03-installed-root.yaml`,
`scripts/wo03_installed_root.py`, the historical reconciled JSON and the
trainer-fin-root driver are **not published there**. The latter local driver
has SHA-256 `479e1f2035ca71d65af1f28316a4f3af4dc2684eac1def04703e9107a674e5e4`;
its presence here is not evidence of availability in a clean checkout. The
CAD parts/schema, recovery-budget configuration and finite-contact helper are
published, but those alone neither reconstruct the multi-material fin/frame
nor provide the missing ownership map. The STEP and large build artifacts are
local ignored files; do not commit generated bulk files merely to conceal that
dependency.

The minimum reproducible handoff is:

1. A private, accessible, hash-pinned archive containing the exact validated
   G12 resolved JSON, original fin and rounded frame STEPs, named layer ledger,
   relevant source/config snapshots, and the recorded frame/fin placements.
   Preserve both the stale original and the reconciled identity; no re-labeling
   of a generic export as this proposal.
2. Either a published, appropriately scoped, dependency-complete reconstruction
   of the historical layer recipe at matching source/config identities **or**
   hash-pinned separately labeled solids with a verifiable importer-independent
   material/first-fin/side mapping. A reference to an unpublished driver or
   numerical child order alone is insufficient.
3. A checked interface manifest that maps specific root/tab/foot/pad/frame/shell
   surfaces, units, outward normals and spatial extents, with complete and
   nonoverlapping material/face ownership, justified geometric tolerances and
   provenance. Verify the mapped objects against recorded layer volumes,
   placements, expected contact pairs and the source compound; matching volume
   alone is not enough. Report any overlaps, slivers, missing surfaces or
   ambiguity as failures, not clipped or silently tied.

The 0.1 mm foot, tab potting and 0.5 mm frame/shell pads are material geometry
hypotheses, not proof of real full-wet bonding. Even with an ownership manifest,
hot interface moduli/allowables and the actual joint support remain separate
open inputs. The proposed case in
[wo03-installed-root-next-case.md](wo03-installed-root-next-case.md) remains
**blocked at ownership/reproducibility preflight**, rather than being described
as ready for FEA. No new mesh, analysis, design adoption or release is implied.


## Subsequent solid-map result

The bounded follow-up in [wo03-fin-material-map.md](wo03-fin-material-map.md)
resolved the earlier solid-identity ambiguity for this exact input: an
AST-preserved historical recipe produced 60 uniquely matched material/angle
solids, verified by centroid, bounding-box and two-way Boolean comparisons.
The original warning above records the preflight state, not the current status
of solid identity. Interface/face ownership, shell correspondence, physical
contact, hot allowables and privately available hash-pinned source artifacts
remain unresolved; the installed-root case is still blocked before meshing.
