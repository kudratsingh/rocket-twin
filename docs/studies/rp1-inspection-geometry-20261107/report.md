# RP1 AD1 v2 inspection geometry packet

The frozen `G80-F2-RP1-AD1-definition-v2` now has a separately identified
inspection representation: 26 mesh-bearing parts from 55 audited source records.
Ten have ideal source-dimensioned solids, 16 have simplified nominal envelopes,
25 are scalar/process mass allowances without a solid, and four have explicitly
missing installed geometry. The [complete coverage table](coverage.md) and
[source/asset manifest](manifest.json) retain every source part ID.

This is an inspection export, not canonical resolved vehicle CAD. The existing
`resolved_spec_sha256` and `cad_revision_sha256` remain null. The distinct
`inspection_geometry_sha256`, per-part `inspection_shape_sha256` and actual GLB
SHA-256 values identify this representation. No vehicle resolution, mass,
inertia, physics, FEA or solver is run. The failed fin screen, unverified joints,
unadopted configuration and all original engineering gates remain unchanged.

## Sources and model decisions

The frozen specification SHA-256 is
`811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`.
The pinned AD1 definition and saved record are verified before export and by
the read-only adapter. Generator and reused CAD/mesh helper source hashes also
identify the export. Historical modular-performance meshes are never loaded.

The existing CadQuery and trimesh tools produce GLB meshes with no new
dependencies. The nose uses the existing sampled ogive/shoulder generator.
Tube dimensions, stations and fin planform come from the frozen source.
AD1's explicit 6.8 mm slot definition supersedes the stale 6.5 mm CAD parameter.
The fin panel, corrected 109.4 mm integral tabs and six root wedges are separate
source IDs; the legacy combined fin generator's old tabs/gussets are disabled.
Wedges use the existing generator's ideal cylindrical saddle construction,
including its 1 mm construction inset; actual bevel, adhesive and fitted saddle
geometry remain unverified. This construction convention is not a new measured
dimension or an alteration to the frozen specification.

The forward-ring U-notch uses the documented 4.5 mm width, 5 mm radial depth
and 60 degree location. Its proposed 2 mm entrance/exit roundovers are omitted
and the part is classified as a simplified envelope. The motor and retainer
show nominal envelopes without invented supplier closure, cap, thread, seat
or liner details. Purchased electronics and recovery packing are featureless
source boxes/cylinders; mounting holes, connector details and pack topology are
unavailable. Estimated zero lateral offsets are displayed as recorded.

There is no solid for the thermal shield's undefined sectors, actual dressed
Kevlar wrap/knots/route, or unconfirmed rail buttons/backers. The Kevlar source
stowage box is deliberately withheld from installed geometry: it does not
describe the forward-ring choker. Bond, coating and service allowances are
listed and selectable by source ID without coincident invented solids.

## Frame, units and reproducibility

CAD uses millimetres: X=body+y, Y=body-z, Z=station aft. GLB uses metres:
X=body+y, Y=vehicle length minus station, Z=body-z. The viewer origin is at the
aft length datum; the nose tip is `[0, length_m, 0]`. Source station and lateral
offsets are absolute, independent of assembly membership. Every mesh is
already placed in that frame; consumers must not apply its source position
again. Bounds describe full exported geometry, not a tight sectioned surface.

Generate the ignored local assets using:

```sh
.venv/bin/python scripts/wo04_rp1_geometry_export.py
```

The read-only `src.api.rp1_geometry.build(root)` validates the generated manifest
against the tracked evidence, exact sources, all 55 classifications and each
asset's bytes. `asset(root, part_id)` returns an allowlisted GLB path and verified
hash; `assembly` returns the complete display scene. Missing output remains
unavailable and is never generated inside an API request. An intentional code
or source change requires a deliberate `--record-evidence` regeneration and
new verification. Public API integration and UI mesh URLs are separate work.

## Bounded execution and verification

This packet permits 45 minutes of implementation plus one correction, with at
most five minutes CPU geometry generation. Unsupported sources or a CAD/tool
failure stop generation; no architecture variant, solver retry or dependency
install follows. The exporter checks its CPU cap between parts and after the
assembly, and source drift prevents manifest publication. The first export
completed without a CAD/tool failure. Source and code checks are distinct from
the designated-runtime browser gate.

Focused tests generate actual GLBs in a temporary repository and check source
coverage, all represented bounds, source scale/placement, corrected slot edges,
separate fin solids, null canonical identities, omitted geometry, source/asset
drift rejection and unavailable-output behavior. Ruff, Black and strict mypy
checks apply to the new Python code. Browser interaction and visual acceptance
are not established by these checks.

Local result: **5 focused tests passed in 10.49 seconds**; Ruff, Black and strict
mypy for the two new source modules passed. A second normal export reproduced
the saved manifest and all GLB hashes exactly; the read-only adapter verified
the regenerated assets. Inspection geometry identity:
`238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`.
CadQuery's transitive ezdxf import emitted an unavailable user-cache warning;
geometry generation itself succeeded, with no dependency install or retry of
a failed CAD operation. All actual generation completed well below five minutes
CPU. The tracked manifest, source table and test output support offline source
and geometry evidence only.

## Later measurement plan

Hardware is unpurchased. This is a planning list for a later separately
authorized inspection; no owner hardware measurement is required now.

| Part / location | Future measurement and units | What it would unlock |
| --- | --- | --- |
| Body, splice and motor tube; stations 160–1220 mm | OD, ID, ovality, lengths, wall and seam thickness in mm; labelled lot | Replace nominal tube envelopes and bound actual radial bond gaps. |
| Fin panels, integral tabs and slots; 1075–1205 mm | Thickness, chord/span, tab length/flat radius, slot width and stations in mm; grain direction | Replace ideal planform/tab geometry and inspect actual slot clearances. |
| Root wedges; three fin roots | Saddle radius/bevel, height/base, adhesive film and coverage in mm / photographs | Replace ideal fitted-saddle convention and locate actual joint geometry; no strength pass follows. |
| Forward ring and notch; 1060–1072.2 mm at 60 degrees | OD/bore/thickness, notch width/depth, roundovers and bonded gaps in mm | Replace the simplified annulus/notch and bound actual passage fit. |
| Finished leader/knot/sleeve; 980–1127 mm and body mouth | Dressed radial/tangential/axial bounds, passage clearance, tails/reach and sleeve thickness in mm; installed mass in g | Replace the withheld route/knot geometry and verify inspectable routing/packing. |
| Exact motor, sleeve and retainer; 1092–1250 mm | Controlled exact-product drawing or actual OD/length, shoulders/threads/seat and axial engagement in mm | Replace supplier envelopes and inspect exact installed motor/retainer fit. |
| Rail buttons/backers; stations unconfirmed | Actual two guide stations, radial stand-off, fastener/backer dimensions in mm; mass in g | Define the currently missing guide geometry and separately revisit usable guide travel. |
| Nose electronics/recovery pack; 82–400 mm | Board/connector/mount/pack bounding dimensions and clearances in mm; individual masses in g | Replace generic boxes with source-supported installed geometry and later measured accounting. |

Measurements alone do not qualify conditioned bonds, finished attachment
capacity, thermal/chafe behavior, installed flutter or flight release. All five
supplier/lab drafts remain UNSENT. No contact, purchase, fabrication, loading,
physical test or paid service occurred in this packet.

Packaging correction: the additive inspection exporter lives under `src/inspection/`, outside the physical CAD generator directory. All 26 part GLB hashes and the assembly hash remained byte-for-byte unchanged after this move. The legacy generator hash remains `1193713d0f4a7ad8393a00a0a03e7aaa04e9aa9393d2034691ef7126ae3cdd3b`; only the separate inspection source identity changed.
