# Standalone source intent preview

`SourceIntentPreview.tsx` accepts `{vehicle: InspectionDocument, snapshot:
DraftRevision}` and presents a normal-flow details panel for one **current saved
metadata revision**. It remains standalone in this lane; primary owns its later
import into Saved drafts after the independent reviewJSON publication and owns
normal API startup and designated-window verification.

The only initial request follows **Prepare intent preview**. Opening the details
panel, rendering, mounting and creating a client cause no requests. Prepare sends
`GET /api/design-drafts/{UUID}/intent-preview`; an actual source-pinned response
must match the loaded parent UUID, metadata revision, source and all 55 records.
A moved server head requires explicit metadata reload. A 404 explains that the
normal-host backend needs restarting with the intent router enabled; there is no
prepared fallback.

After preparation, keyboard-accessible source selection exposes the recorded
function, unresolved issues, geometry scope, physical/interface missingness and
source provenance. **Mark exclusion intent** and **Restore source occurrence
intent** request one stateless planning operation. These affect only the unsaved
preview. The original source occurrence remains in the immutable 55-record base;
excluded functions and their original evidence remain visible blockers. A
three-fin source group remains one source occurrence, with its original group
count retained. No source or owner-library data is modified.

The component keys its inner state by parent UUID, metadata revision and source
hash. Changing that parent revision or leaving/unmounting this page discards the
unsaved state, as the visible caption states. Failed requests retain the current
admitted overlay, selected source occurrence and exclusion IDs. Stale metadata
locks commands and preparation until the parent metadata is reloaded. A stale
overlay locks commands until explicit fresh preparation; the button states that
this discards unsaved intents. No automatic retry or reload occurs.

## Admission and request boundary

`sourceIntentClient.ts` reuses `admitDraftRevision` and compares the complete
returned base with the loaded saved snapshot. It reconstructs the expected
nonphysical preview structurally from the admitted bank and expected exclusion
IDs, in original source order. Kind, schema, status, all-55 preservation, exact
function/occurrence/evidence, null checks, literal-false readiness, unsupported
capabilities, blockers and absence of extra fields must match. This is admission
of an intent preview, not a candidate resolver.

The Python overlay SHA is an **opaque server identity**. JavaScript checks its
SHA shape but does not rehash a full source or overlay: Python `1.0` and JavaScript
`1` canonicalization differ. A POST contains exactly these five fields:

```json
{
  "base_draft_revision": "<loaded saved metadata SHA256>",
  "base_overlay_revision": "<opaque returned Python overlay SHA256>",
  "excluded_occurrence_ids": ["<original source ID>"],
  "type": "exclude-source-occurrence",
  "occurrence_id": "<original source ID>"
}
```

The other supported type is `restore-source-occurrence`. No full client source,
overlay, path, generated geometry, metadata or physical calculation is sent. The
server independently reads its trusted current store and reconstructs the prior
intent set before applying one command. The requests use only the existing
relative local API path and `no-store`; the new router owns the existing four
local-origin policy. Safe 409 messages expose only validated current revision
hashes. Backend messages, filesystem paths and transport exception details are
not displayed.

Total mass, removal credit, CG, inertia and effective inventory remain null.
Resolve availability, resolved candidate, simulation eligibility, engineering
acceptance and flight readiness remain literal false. There is no physical
removal/replacement, CAD change, Add/Replace/Connect, parameter/position editing,
blank draft, undo/history, intent persistence, adoption or complete-builder
claim. Frozen RP1/AD1/D1, dedicated G80 first, G54/G12 PID-to-RL and the five UNSENT
inquiries remain unchanged.

## Actual pure-function fixture

The original actual-store fixture is read-only:
`web/tests/fixtures/rp1-draft-library.json`, SHA256
`b2339838a42a6426d535a533df7c021211362e3dd4e643a933e5c4562d0cded0`.
Only its `saved` test revision is used; no owner UUID or owner library is read.

`rp1-source-intents.json` contains four real pure-function results: base, fin
exclusion, fin plus motor-retainer exclusion, and fin restore. Each overlay omits
its duplicate `base`, referring instead to the existing fixture and revision.
Generation uses `src.vehicle.draft_composition.create_overlay/apply_command` from
module SHA256
`54629731eb40d0e2d8cfd8e80fae8bf35f8e95e5e4b3fe94c0e841d1599a1c2b`.
The formatted fixture is 17,391 bytes, SHA256
`e0d2bd1797f5df6014713f6c7ad13a1e6ff77c00a21ca68fa69572b57b5f7ad1`.

To reproduce from repository root using the installed local Python and web tools:

```sh
.venv/bin/python - <<'PY'
import hashlib, json
from pathlib import Path
from src.vehicle.draft_composition import create_overlay, apply_command
fixture_path = Path('web/tests/fixtures/rp1-draft-library.json')
data = fixture_path.read_bytes()
assert hashlib.sha256(data).hexdigest() == 'b2339838a42a6426d535a533df7c021211362e3dd4e643a933e5c4562d0cded0'
fixture = json.loads(data)
row = fixture['revisions']['saved']
base = {**row['metadata'], 'revision_sha256': row['revision_sha256'], 'source': fixture['source']}
initial = create_overlay(base)
def command(overlay, kind, pid):
    return apply_command(overlay, {'type': kind, 'occurrence_id': pid, 'base_overlay_revision': overlay['revision_sha256']})
fin = command(initial, 'exclude-source-occurrence', 'fin_set')
both = command(fin, 'exclude-source-occurrence', 'motor_retainer')
restored = command(fin, 'restore-source-occurrence', 'fin_set')
value = {
    'schema_version': 1,
    'generator': 'src.vehicle.draft_composition.create_overlay/apply_command',
    'module_sha256': hashlib.sha256(Path('src/vehicle/draft_composition.py').read_bytes()).hexdigest(),
    'base_fixture': {'path': 'rp1-draft-library.json', 'sha256': hashlib.sha256(data).hexdigest(), 'revision': 'saved'},
    'overlays': {name: {k: v for k, v in overlay.items() if k != 'base'} for name, overlay in [('initial', initial), ('fin', fin), ('both', both), ('restored', restored)]},
}
Path('web/tests/fixtures/rp1-source-intents.json').write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
PY
web/node_modules/.bin/prettier --write web/tests/fixtures/rp1-source-intents.json
```

Node CI requires no Python runtime: the test checks both fixture byte hashes and
the recorded Python module hash, then hydrates the base only in memory. Python
fixture generation is a local pure-data operation; no server, store, CAD,
physics/solver or network operation is involved.

## Scoped validation and remaining evidence

Seven reported Node tests (one parent and six substantive subtests) pass through
Vite middleware/SSR without binding a listener. They cover actual base/exclude/
restore source preservation, exact tiny request shapes and opaque hashes,
tampered source/functions/evidence/order/counts/flags, stale metadata/overlay and
safe revision hashes, 404/restart, transport/bad JSON, invalid commands, no retry,
input-state preservation and no automatic fetch during SSR. The existing actual
fixture and every shared source/client/store file remain unchanged.

Project TypeScript checking, scoped ESLint and scoped Prettier checks pass. The
only correction after the initial implementation updated the new fixture byte
pin following its formatter output. This is code/source/SSR evidence; no browser
interaction, live API/startup, persistence, complete candidate, engineering,
physical or flight acceptance is established here. Primary owns integration and
new native evidence, with the existing sole designated Chrome owner.
