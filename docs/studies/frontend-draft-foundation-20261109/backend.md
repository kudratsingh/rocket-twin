# Source-preserving local draft store and API

This focused backend increment forks the frozen RP1 source into a separately
identified local record and saves labels/notes with immutable history. It includes
the store, bounded HTTP router, composition wrapper and normal preview launcher.
The frontend library follows in a separate increment. FW2-024 and FW2-A18 remain
partial; this is not a complete rocket builder or an engineering admission.

## Contract

`DraftStore(root)` accepts a trusted server root, never a client filesystem path.
Its `fork_rp1`, `read`, `save_metadata` and `list_drafts` preserve source and
accounting. `src.api.workbench_app.create_app` places the new routes ahead of
the unchanged base inspection app; existing API endpoints, docs, catalog pins
and base CORS behavior remain intact. `scripts/wo04_api.py` uses this wrapper.

| Route | Required behavior |
| --- | --- |
| `POST /api/design-drafts` | Exact current RP1 configuration/specification, label and optional notes; server UUID4 and initial content-hashed revision |
| `GET /api/design-drafts?limit=25&after=…` | Bounded summary page, maximum 100, opaque UUID cursor; no snapshot/assets in summaries |
| `GET /api/design-drafts/{id}?revision=…` | Current or exact historical SHA-256 revision, recorded source and readiness |
| `PATCH /api/design-drafts/{id}` | Required `base_revision` and label and/or notes; stale writes409; omitted metadata preserved |

The complete source specification, read-only bank and inspection snapshot are
saved once. All 55 original source accounting occurrences, estimates, product
conflicts, failed findings,25 allowances and4 missing geometries are preserved.
No source record is installed twice for a display child. Labels/notes do not
change mass, placement, geometry, material or motor. Resolved-candidate, simulation,
engineering and flight readiness stay false. No Add/Replace/Connect, blank rocket,
parameter editing, CAD job, physics calculation or adoption is provided.

## Persistence and request boundaries

Private local records live under ignored `output/design-drafts/<UUID>/`. Source
and revisions are immutable; the head pointer changes atomically after a revision
is durably written. A per-draft lock serializes saves. An interrupted head update
leaves the previous head readable; an interrupted initial fork can leave a visibly
incomplete directory. There is no automatic deletion or repair of owner data.

IDs/revisions, unknown fields, repeated query values, control characters and
request bounds are validated. Source/storage/snapshot symlinks, hardlinks, FIFOs,
oversized files and corrupted hashes fail visibly. Limits are 8 MiB per JSON file,
1,000 drafts and1,000 history entries. Server root and asset paths are never request
data. Errors do not echo filesystem paths or raw input. File-level atomicity is
not a power-loss qualification of the owner's filesystem.

Draft routes admit only exact HTTP localhost/127.0.0.1 origins on 5173/4173 and
route-specific methods/Content-Type. No wildcard or credential permission is
added. Requests and preflight receive the same scoped boundary; the mounted
base API keeps its existing GET/POST CORS policy. Construction/listing of a
pristine library writes no storage. There is no automatic POST or retry.

## Evidence and runtime status

Twenty isolated store cases,39 FastAPI/TestClient cases and2 composition cases
pass. They cover source-preserving fork/save/reload/history, source drift,
concurrent stale saves, interrupted publication, filesystem/path bounds, exact
origins, safe errors and existing API/docs preservation. Ruff/Black/mypy pass.
No production draft or owner data was written.

The actual temporary-store protocol fixture is stored once at
`web/tests/fixtures/rp1-draft-library.json` (491,602 bytes, SHA256
`b2339838a42a6426d535a533df7c021211362e3dd4e643a933e5c4562d0cded0`).
Python checks its source and metadata revisions against the current generator.
The future web tests can use this file without a Python runtime dependency.
It contains test labels/notes and public frozen source, not an owner library.

One isolated loopback startup check on 8001 failed with PermissionError / errno 1.
No server was started, no other port/transport was retried, and the owner's
5173/8000 services/data were untouched. Native mutations remain unavailable until
the normal-host preview restarts. This is an access block, not a demonstrated
store failure. When ready, stop the current preview in its normal terminal with
Ctrl-C and run `make preview` from the repository root.

Required hosted checks apply to the exact published head. All five inquiries
remain UNSENT. Frozen RP1/AD1/D1, G54/G12 PID-to-RL and every physical/build,
thermal/recovery/flutter, paid-run, WO-10 and flight gate remain unchanged.
