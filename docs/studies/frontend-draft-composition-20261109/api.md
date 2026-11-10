# Stateless source-fork intent-preview API

`src.api.draft_intents.create_router(root)` returns a standalone router over a
trusted local server root. It is not mounted by this slice. The primary owns
factory routing, origin composition, GUI integration, publication and acceptance.
No existing API/startup/store/client/module/fixture or source YAML is changed.

This endpoint computes **read-only planning previews**. It neither saves intents
nor edits metadata. It supplies no mass-removal credit, accepted replacement
function, geometry, effective candidate, physics result or adoption.

## Requests and results

Both methods use `/api/design-drafts/{exact server UUID4}/intent-preview`:

| Method | Behavior |
| --- | --- |
| `GET` | Read the actual current saved draft and return `create_overlay(current)` with no exclusions |
| `POST` | Read that current saved draft, check its revision, reconstruct the submitted prior exclusion set on the server, then apply one guarded exclude/restore command |
| `OPTIONS` | Exact local-origin preflight for GET/POST and optional Content-Type |

POST requires exactly:

```json
{
  "base_draft_revision": "<saved metadata revision SHA-256>",
  "base_overlay_revision": "<opaque server preview SHA-256>",
  "excluded_occurrence_ids": [],
  "type": "exclude-source-occurrence",
  "occurrence_id": "fin_set"
}
```

The only other supported command type is `restore-source-occurrence`. Revision
strings are lowercase SHA-256. Occurrence IDs are strict strings with a bounded
source-ID spelling; the server also requires exact original occurrence membership.
The exclusion list is required, unique and limited to 55 entries. No source, full
base/overlay JSON, metadata, quantities, filesystem/asset paths, Add, Replace,
Connect, resolve or physics input is accepted. Pydantic forbids unknown keys and
coercion. Repeated JSON names, malformed JSON and POST bodies over 16 KiB are
rejected. GET/OPTIONS accept no body; every method rejects query fields, including
repeated/unknown ones.

A successful POST returns the new complete planning overlay. For the next POST,
the client sends that response's `excluded_occurrence_ids` and opaque
`revision_sha256`, plus its unchanged `source_revision_sha256` as
`base_draft_revision`. It never resubmits the full source or rehashes it in
JavaScript. The server reads the original Python saved snapshot and reconstructs
prior exclusion intentions in **source order** through `apply_command`, using
server-computed intermediate hashes. It then applies the requested command using
the supplied final base-overlay hash.

This avoids Python/JavaScript source-number canonicalization mismatch. Hashes are
content identities, not caller authentication or proof of persistence. The
existing contract's duplicate-exclusion error and guarded restore/no-op semantics
remain intact. Successful content-equivalent previews have the same hash.

## Statelessness and unchanged accounting

GET always starts from the current saved fork with no intents. POST does not
change subsequent GET results. Closing/reloading a future client without keeping
its intent list will lose that temporary preview state; no overlay history or
server persistence is implied. Each request uses its server-read saved snapshot;
this preview does not reserve/lock a metadata head against later concurrent edits.

Every response preserves the original complete 55-record base ledger, raw
quantities, group counts, placements, metadata/source hashes and evidence.
Exclusions expose their removed functions/provenance/issues as blockers. They do
not create a reduced effective mass inventory. `effective_inventory`, total mass,
mass-removal credit, CG and inertia remain null. Resolve availability,
resolved-candidate, simulation eligibility, engineering acceptance and flight
readiness remain literal false. Installed-reference assets remain reference
assets; no reusable local part or geometry is created.

## Rejections and local boundary

Errors retain the existing sanitized `detail.code` / `detail.message` shape,
without raw request values, exception strings or filesystem paths:

- **409 `stale_draft_revision`** includes `current_draft_revision`. Reload the saved
  draft/preview explicitly; do not retry an old intent automatically.
- **409 `stale_overlay_revision`** includes `current_overlay_revision`, the server
  hash of the submitted prior intent set reconstructed on that saved draft.
- **409 `duplicate_exclusion`** rejects repeating an already-excluded occurrence.
- **422 `duplicate_exclusions` / `unknown_occurrence` / `invalid_request`** reject
  duplicate/foreign IDs and unsupported field/type/command/body/query input.
- **404 `draft_not_found`** reports an absent valid UUID/revision; source/storage
  problems retain sanitized unavailable errors, not an invented empty preview.

The router reuses the existing local draft origin/error/no-store boundary. Only
exact HTTP localhost/127.0.0.1 origins on ports 5173/4173 are admitted; another or
repeated Origin receives 403 before source access. Allowed-origin successes and
errors carry exact allow-origin and no-store headers, without wildcard or
credentials permission. Preflight validates UUIDs and permits only GET/POST and
Content-Type; repeated preflight headers or header names are rejected. Requests
without Origin remain usable by local non-browser callers. The host must retain
its existing loopback restrictions; this is not an authentication/deployment
service, and no global CORS/permission setting is changed here.

## Executed isolated verification

Thirty focused API cases pass using real temporary `DraftStore` instances with
only copied pinned inputs. They verify GET/exclude/restore, canonical replay,
all-false/null preview gates, unchanged saved metadata/source and file bytes,
no added files, distinct metadata/overlay stale conflicts, invalid/duplicate/
foreign fields/IDs/commands, repeated JSON/query fields, exact allowed/forbidden
origins, preflight and sanitized errors. Source drift is an explicit failure;
no owner UUID/library was accessed. A focused correction extended strict UUID/
empty-body/repeated-header handling to preflight and read methods.

The separately declared **single worst-case source-JSON timing probe** replayed
all 55 exclusions and then restored one, returning 200 with 54 intent exclusions.
The expected prior identity was prepared directly in Python without a second
55-command replay. Measured request time was **1.994706 seconds wall / 1.952056
seconds CPU**, below the declared **20 wall / 10 CPU second** stop bounds. Saved
file bytes remained unchanged. This is local JSON replay/response timing, not a
CAD/physics or browser-performance claim. The timing case is opt-in via
`RUN_DRAFT_INTENT_REPLAY_PROBE=1`; it is skipped in routine runs to avoid silently
repeating this bounded probe.

Black, Ruff and strict mypy on the router pass. The existing Starlette/httpx
TestClient deprecation warning remains; no dependency was changed. The isolated
suite reports 30 passes plus the separately executed one probe pass. No HTTP
listener/server, native browser, Git/network, new persistence, solver or physical
action was started. Primary integration/GUI/native acceptance remain open;
FW2-025 and effective candidate resolution are not complete. Frozen engineering
and physical gates stay open and all five inquiries remain UNSENT.
