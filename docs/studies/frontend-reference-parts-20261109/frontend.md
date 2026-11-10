# Standalone analytic datum guide for two local references

This lane adds a controlled datum list and optional R3F overlay for the two
frozen geometry-only references in [the source contract](source-contract.md).
The tube uses **outer radius 15.6845 mm, bore radius 14.5845 mm and length
165 mm**. The aft annulus uses **outer radius 32.2 mm, bore radius 15.95 mm and
thickness 6 mm**. No model, asset, dimension, installed RP1 record or source
property is changed.

## Parent integration seam

`referenceDatumGeometry.ts` exports `admitReferenceDefinition(raw)`, returning
`ReferenceDefinition | null`. It admits only the complete two known definition
DTOs: exact namespaced IDs/revisions, source/template identity, nominal parameters,
frames, all five ordered analytic features, null unknowns, false gates, original
identity limits, provenance and exact STEP/GLB asset identities. Extra fields,
missing features, fabricated topology IDs and altered readback are rejected.
The existing bundled geometry manifest supplies the recorded readback and GLB
bounds; its identity and actual asset pins are checked against the two frozen
cases. Python revisions are pinned identities, not JavaScript rehashes of
floating-point JSON. Runtime asset availability is separate from definition
identity and never becomes a substitute for parent asset-byte verification.

The default `ReferenceDatumGuide` and named `ReferenceDatumOverlay` accept the
same controlled props:

```tsx
{
  definition: ReferenceDefinition;
  selectedFeature: DatumFeatureId | null;
  onSelect: (feature: DatumFeatureId | null) => void;
}
```

`DatumFeatureId` is exactly `axis`, `bore`, `outer_cylinder`, `start_plane` or
`end_plane`. The parent owns definition admission/loading, selected state and
reset behavior. The components defensively recheck the supplied definition.
A foreign/incomplete definition shows a DOM unavailable notice and draws no
scene guide. Null or unknown selection draws no geometry. No automatic request,
selection, transport, persistence or camera action occurs.

Place `ReferenceDatumGuide` beside the existing local reference preview. It
provides five ordinary keyboard buttons with `aria-pressed`, an explicit Clear
button, source dimensions and missingness notices. Parent integration may mount
`ReferenceDatumOverlay` **inside the existing local Canvas**, beside the verified
CAD object. It creates no nested Canvas, loader, light, controls or camera and
never changes the parent scene, source materials, CAD bytes or geometry bounds.
The parent must verify the matching asset bytes before showing an overlay with
that asset; local cache availability alone does not prove public URL availability.
Do not mount it on the installed rocket or infer an installed transform.

The selected guide alone is drawn. Its lines/annulus disable raycasting so they
do not capture model selection. One selected-feature HTML button names the
analytic reference and calls the controlled `onSelect` callback; its pointer
handler stops propagation. Use the DOM list to choose a different guide. Labels
may be occluded/overlap in an actual view; native legibility and pointer behavior
remain unobserved. The parent may explicitly ghost its solid to expose the bore
or internal axis. This lane does not change shared materials or add ghost controls.

## Frame and display construction

STEP is millimetres at local front center, CAD +Z aft. The recorded mapping is:

```text
point:     viewer[X,Y,Z] = [cadX/1000, -cadZ/1000, cadY/1000]
direction: viewer[X,Y,Z] = [cadX,      -cadZ,      cadY]
```

Direction vectors are dimensionless; their transform rotates axes without the
length-unit scale. Thus positive CAD Z maps to viewer negative Y. No nose-tip
station or placement transform is inferred. Exported `cadPointToViewer` and
`cadDirectionToViewer` reject nonfinite or incomplete coordinates.

`referenceDatumGeometry(definition, selectedFeature)` derives display geometry
only from the admitted analytic feature fields. The axis spans its original
origin/direction and axial range. A selected cylinder uses 96-segment circular
outlines plus four axial guide lines at the exact nominal radius. This sampling
is a display guide, not a new mesh or accepted manufacturing tolerance. A selected
annular datum uses its original radii and axial origin; the transparent ring is
rotated so its display normal maps to viewer negative Y.

Both plane normals are the **arbitrary positive local-axis convention**, not
extracted kernel/outward face normals. Guides are analytic parameter-derived
references, never CAD face or triangle IDs. `cad_face_ids`, `mesh_triangle_ids`,
`tolerance_mm`, installed transform, interfaces and all unknown physical
properties remain null. Mating, Add-instance, Connect, simulation, engineering,
physical and flight readiness remain false. No fit/strength/FEA calculation,
source adoption or complete-builder capability is introduced.

## Pure actual-build fixture

`web/tests/fixtures/reference-parts.json` was generated by the frozen actual
`src.vehicle.reference_parts.build(root)` and formatted with the existing
Prettier. Its `catalog` holds static core/definitions; `availability` is a separate
object. No owner data is read. The producer reads its pinned source inputs and
exactly the four registered existing STEP/GLB paths; it performs no directory
scan, geometry regeneration, CAD/kernel import or process execution.

Fixture SHA256:
`5db095fc80474ce25b1c0bb70087ca9c49abe4d696227a5b4810e4e6abfcd838`.
Producer SHA256:
`e37ab77fc8c1d6d0d7d6819ac3426d4cf08e86aeb6078bf6ec22b2067b1f3778`.
The catalog revision stays
`8f6b7bf2f0dcc8dfb2714ba7a28688c820869dc3045060aba6ea5901983b7748`.

Reproduce from repository root with the installed local tools:

```sh
.venv/bin/python - <<'PY'
import hashlib, json
from pathlib import Path
from src.vehicle.reference_parts import build
actual = build(Path.cwd())
fixture = {
    'schema_version': 1,
    'generator': 'src.vehicle.reference_parts.build',
    'module_sha256': hashlib.sha256(Path('src/vehicle/reference_parts.py').read_bytes()).hexdigest(),
    'catalog': {key: value for key, value in actual.items() if key != 'availability'},
    'availability': actual['availability'],
}
Path('web/tests/fixtures/reference-parts.json').write_text(json.dumps(fixture, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
PY
web/node_modules/.bin/prettier --write web/tests/fixtures/reference-parts.json
```

Node CI uses the frozen fixture and recorded readback; it requires no Python,
local output assets, server or CAD kernel. Tests verify the fixture, producer and
all catalog source-pin byte hashes. Availability records are historical fixture
facts, not a fresh runtime availability assertion.

## Scoped validation and remaining evidence

Six reported Node tests (one parent, five substantive subtests) pass using Vite
middleware/SSR without binding a listener. They verify both actual definitions,
independent availability, dimensionless-vector versus point transforms, exact
nominal radii/endpoints/annular planes against recorded STEP readback and GLB
bounds, source/frame/revision/feature/asset/null/false rejection, known selection,
controlled keyboard markup and no automatic requests or selection. The recorded
STEP/GLB checks are existing readback evidence, not a new CAD execution.

Project TypeScript, scoped ESLint and scoped Prettier checks pass. The focused
correction pins the formatted fixture bytes in the Node test. A Three dependency
emits its existing CommonJS deprecation warning during SSR; no test fails.
Only this lane's six new files were written. Shared imports,
`LocalTemplatePreview`, API, CAD/source modules, owner data and existing browser
state were untouched. No server/network/browser/Git action occurred. Primary
owns later UI/Canvas integration, planning admission, backend routing and actual
designated-window acceptance after PR128. Frozen RP1/AD1/D1, dedicated G80 first,
G54/G12 PID-to-RL, UNSENT inquiries and all physical/flight gates remain unchanged.
