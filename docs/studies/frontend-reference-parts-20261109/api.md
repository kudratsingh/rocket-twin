# Read-only local reference-parts API

`src.api.reference_parts.create_router(root)` is a standalone router factory.
It declares routes without reading or writing source/cache files during
construction. Primary integration owns mounting it in the loopback workbench
and any active preview-dev reload. No existing factory, launcher, store, source,
client or UI is edited here; no owner restart is requested by this slice.

This API exposes **geometry-only planning reference metadata** for the two
already reviewed nominal definitions. It creates no part/instance, serves no
CAD/mesh file bytes and supplies no Add/Replace/Connect or candidate admission.
The frozen v1 source/template registry remains inspect-only and unchanged.

## Routes and exact DTOs

| Route | Response |
| --- | --- |
| `GET /api/reference-parts` | Exact `src.vehicle.reference_parts.build(root)` catalog, including both definitions, source/catalog revision and separate cache availability |
| `GET /api/reference-parts/{reference_id}/{revision}` | Exact nominal selected definition, its separate availability and the catalog revision |
| `OPTIONS` on either route | Exact-origin preflight permitting **GET only** |

IDs are bounded namespaced strings and must match a definition produced by the
source module. The two current IDs are `reference-local-v1:motor-tube-nominal`
and `reference-local-v1:aft-annulus-nominal`. Revisions must be lowercase
SHA-256 strings and must equal that definition's current revision.

The detail response is:

```text
{
  definition: <complete source reference definition>,
  availability: <that definition's separate cache availability>,
  action: "inspect_geometry_reference",
  instance_created: false,
  engineering_accepted: false,
  simulation_eligible: false,
  flight_ready: false,
  catalog_id: "reference-local-v1",
  catalog_revision_sha256: <source catalog hash>,
  scope: "geometry_only_planning"
}
```

The router looks up the current definition, validates the requested revision,
then invokes `select_reference` with **server-owned exact nominal parameters**.
It accepts no client parameter values, source JSON, placement, tolerances or
geometry requests. Every GET/OPTIONS body and every query key is rejected,
including repeated/unknown query fields. No endpoint exposes the referenced STEP
or GLB bytes; existing registered paths/URLs remain metadata/provenance only.
POST and other mutation methods are unsupported.

Definitions retain the documented local STEP millimetre/GLB metre frames,
analytic datum-only features, null installed transform and null mating contract.
Unknown mass, procurement cost, inertia, stock tolerances, material allowables
and thermal capability remain null. All Add-instance/Connect, candidate,
simulation, engineering, physical and flight gates stay false. Neither source
nominal geometry nor file availability qualifies a purchased product, stock,
installed fit or load path.

## Availability and failures

Absent local cache files return **200 with unavailable geometry**, retaining
stable definitions/revisions and `generation_attempted=false`. No alternate file,
installed RP1 mesh or new generated solid is substituted. The separate public URL
cache is explicitly unverified by this API. No directory scan, CAD/kernel call,
process launch or regeneration is performed.

A corrupt asset, changed source/frame/hash or missing critical source prevents
catalog/detail admission. Errors have sanitized `detail.code` and
`detail.message`, without raw filesystem paths, exception text or input values:

- **404 `reference_not_found`**: syntactically valid but unknown namespaced ID.
- **409 `reference_revision_mismatch`**: valid-shaped stale/foreign revision;
  `current_revision` identifies the current definition for explicit reload.
- **409 `reference_source_unavailable`**: pinned source, frame or registered asset
  evidence cannot be verified; nothing is generated or admitted instead.
- **422 `invalid_request`**: malformed ID/revision or forbidden body/query fields.
- **503 `storage_unavailable`**: filesystem access failure, sanitized through the
  existing local route boundary.

Each request revalidates source/cache data rather than trusting a prior caller
object. Catalog revision covers source/definition content, while cache presence
is separate. A detail lookup rechecks nominal selection; changed evidence during
that operation fails visibly. It does not reserve the filesystem against later
external changes or assert that a metadata URL will remain reachable.

## Origin and preflight boundary

The router reuses the existing `_LocalDraftRoute`, `_error` and revision contract.
Supported route names admit no query fields. Exact HTTP localhost/127.0.0.1
origins on ports **5173/4173** are the only browser origins admitted. Other or
repeated Origin headers receive 403 before field validation/source access.
Allowed-origin successes and errors carry the exact allow-origin header and
`Cache-Control: no-store`, without wildcard or credential permission.

OPTIONS validates the detail ID/revision shape, requires an allowed Origin,
permits only GET and optional Content-Type, and rejects unknown/repeated
preflight headers. Preflight performs no source reads. Local non-browser GET
requests without Origin remain usable. This is not an authentication/deployment
service; primary mounting retains the existing loopback/origin restrictions and
changes no global browser permission or CORS setting.

## Executed source/API checks and remaining acceptance

Twenty-three focused FastAPI/TestClient cases pass on temporary copies of the
exact source registry/pins and the four registered local assets, or those same
sources with cache files removed. They cover list/detail/source revisions,
server-only nominal selection, null properties/false gates, unavailable cold
caches, corrupt/missing critical evidence, body/parameter/query/path rejection,
allowed/forbidden origins before source access, GET-only preflight, sanitized
errors and unchanged filesystem file sets/bytes. Tests forbid CAD subprocesses;
the source module itself imports no CAD generator/kernel and runs none.

Black, Ruff and strict router mypy pass. The existing Starlette/httpx TestClient
deprecation warning remains; no dependency changed. No actual HTTP listener,
browser, network, Git, CAD, solver, physical work or owner draft/library access
occurred. Primary mounting, GUI annotations, actual rendering/interaction and
publication checks remain separate. This source/API result closes no mating,
Add/Connect, material, thermal, installed, engineering or flight gate. All five
inquiries remain UNSENT.
