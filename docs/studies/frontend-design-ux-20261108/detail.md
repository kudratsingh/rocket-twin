# Optional RP1 source-detail layer

The complete 26-asset core was inspected before refining three internal
exemplars. The result is an **optional display layer**, not a changed AD1
design or engineering mesh. Core inspection identity remains
`238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608`, all 55
stable source IDs remain, and no mass/inertia, physical material property or
installed qualification is generated.

The [tracked detail catalog](detail-catalog.json) contains the audit of every
core GLB, source references, supported features, missing details, annotation
primitives and actual detail-asset hashes. Optional static files are under
`web/public/engineering-workbench/rp1-detail/`, served without an API restart.

## What the source legitimately supports

| Exemplar | Delivered detail | Explicit remaining limitation |
| --- | --- | --- |
| Forward ring / recovery passage | Finer source annulus/bore/notch; separate source-recorded 6 mm front stock, 0.2 mm bond reservation and 6 mm aft stock nodes | Proposed 2 mm entrance/exit roundovers lack a fully defined blended-surface topology here and remain omitted. No dressed knot, rope fibers or deformed contact is invented. |
| Motor support / retention | Finer motor-tube bore/wall and aft centering-ring annulus; source dimensions exposed as annotation primitives | Current cap/sleeve split, threads, shoulder, seat, liner and exact closure contacts remain unavailable. Retainer and motor remain the original nominal envelopes. |
| Avionics envelope | Exact source barometer 15×12×3 mm envelope dimensions and edge/dimension endpoints | No source PCB outline, components, connectors, solder, traces, mounting holes or sensor construction is available. The original box is retained. |

The forward ring's frozen source notes explicitly identify two 6 mm stock
layers and a 0.2 mm glue allocation. These are visualized with distinguishable
display colours; they do not describe internal plywood ply layup, real surface
texture, measured bond thickness or bond quality. Source diameter 64.4 mm,
bore 31.9 mm, total length 12.2 mm, and the proposed straight 4.5×5 mm notch at
60° remain the same nominal intent. The finer layer keeps its existing
`simplified_envelope` maturity rather than promoting it to manufacturing CAD.

Motor-tube and aft-ring replacements use the frozen numerical geometry exactly.
Source notes also quote nominal kit/stock descriptions; these are not a
controlled supplier drawing and must not be silently reconciled into a new fit.
No retainer thread or installed contact is guessed to make a more realistic image.

## Core audit and mesh resolution

All 26 actual core GLBs were loaded, fingerprinted and checked before export.
The catalog records vertices, triangles, bounds and a disposition for each.
Twelve simplified box envelopes have 12 triangles each because their source
contains only bounding dimensions. More polygons cannot supply their missing
internals. The fin panels and integral tabs each have 36 triangles: their
recorded planar profiles already have exact flat faces. They remain separate
stable records and retain the existing rigid display-bundle behaviour.

The nose already has 33,600 triangles. Tubes/rings generally have 672; the body
has 804 and root gussets 120. Increasing all of these indiscriminately would
not resolve missing suppliers, joints, construction tolerances or the failed
fin/material findings. This packet refines only the useful internal exemplars.

| Stable parent part ID | Core triangles | Optional detail triangles | Detail nodes |
| --- | ---: | ---: | ---: |
| `forward_ring` | 672 | 8,484 | 3 stock/bond layers |
| `motor_tube` | 672 | 2,880 | 1 source annulus |
| `aft_ring` | 672 | 2,880 | 1 source annulus |

The explicit export uses existing CadQuery 2.8.0, trimesh 4.11.5 and NumPy
2.4.6 with 0.01 mm linear / 0.035 rad angular display tessellation parameters.
These are sampling settings, not manufacturing tolerances. The actual exported
envelopes reconcile with their frozen core part boxes within the numerical
faceting check, and all bores/notch openings are retained. No whole-vehicle CAD,
STEP/STL manufacturing package, FEA, solver or flight run is executed.

## Static contract and exact identities

Packet ID: `rp1-ad1-optional-source-detail-v1`.

```text
specification: 811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660
core geometry: 238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608
detail revision: e4ff19fec90e36d2a97987387572749cf3e11449312d09b3cf7e1c8d15016238
manifest bytes: b3ac3cc62294676d5614eab048bab7111320f61eecaa002a85a7d1469b6e8ac6
```

The detail revision hashes the exact pinned specification/definition/saved
record, new detail generator and exporter. It is separate from the core
inspection geometry, canonical vehicle/CAD identity and presentation-breakdown
identity. No source file in the frozen generator or physical definition changes.

Generate deliberately with:

```sh
.venv/bin/python scripts/wo04_rp1_detail_export.py --record-catalog
```

`src/inspection/rp1_detail.py` writes only three optional static GLBs plus their
manifest. Its source/end checks and 120-second CPU cap stop unsupported or
changed-source exports. The first bounded export succeeded. A future deliberate
generator change requires a new recorded catalog and matching frontend pins;
stale packets are not attached automatically.

`web/src/components/rp1Detail.ts` exposes:

```ts
validateRp1Detail(document, value) // pure structural/source admission
loadRp1Detail(document, signal?)  // static same-origin load + byte verification
```

The returned view has `detailMeshes`, three cases, source-dimension annotations
and missing notes. The loader checks the entire manifest's SHA-256 and all
three actual GLB byte hashes before returning optional URLs. It also requires
the active source/core tuple, original core shape/mesh identities, expected
part IDs and display-only flags. Foreign sources, stale assets, path changes
or engineering-promotion flags fail closed to the unchanged core view.

The primary integration supplies optional display mesh URLs without replacing
`part.mesh_url`. Original URLs continue to admit the source and staged
breakdown. Detail assets are already globally placed in metres; use the same
parent-part display translation **once** for rendering, picking and framing.
Picking retains the existing parent part ID. Preserve per-node asset materials
when displaying the layered ring. Annotation endpoints are also globally
placed, values are explicitly in mm, and they never contribute geometry bounds
or create a new source part.

## Verification and remaining gate

**Four Python tests and four TypeScript tests pass**, with actual local detail
assets present. Checks cover all 26 source fingerprints, three exact exemplars,
unchanged core identity/all 55 records, higher sampling, true bores, the notch,
three source layer thicknesses, declared annotation units and wrong source/path/
shape/adoption rejection. The frontend loader test verifies the actual generated
GLB bytes and rejects changed manifest bytes before requesting assets.
Ruff, Black, strict mypy, ESLint, Prettier and the integrated typecheck pass.

This is source/geometry/code evidence, not a new browser observation. The primary
owns optional-layer integration and alternatives; the designated verifier must
inspect the resulting detail selection, internal views, picking, framing,
sections and return to core in the permitted Chrome window. Missing retainer
and avionics internals remain visible as missingness rather than fabricated
detail. All supplier drafts stay UNSENT. No contact, purchase, physical work,
engineering acceptance or flight release occurs in this packet.
