# Stateless local arrangement API

`src/api/reference_arrangement.py` declares a separate loopback metadata route.
It uses the existing exact local-origin boundary and the verified reference
catalog. It never opens the saved draft library, creates a listener, runs CAD,
contacts a supplier or writes a source or plan file.

- `GET /api/reference-arrangement` explicitly prepares an empty unsaved plan.
- `POST /api/reference-arrangement` accepts exactly `{instances, command}`.
  `instances` contains at most two tiny rows: `reference_id`, exact
  `definition_revision_sha256` and `translation_mm`. The core reconstructs the
  base from trusted catalog data, checks the command's opaque
  `base_plan_revision` and applies one Add or translation command.
- Both responses contain `{catalog, plan, action, persisted:false,
  source_vehicle_changed:false}`. Catalog availability is fresh and separate
  from the content identity. No geometry or arbitrary source JSON is submitted.
- `OPTIONS` admits only GET/POST and Content-Type at the existing four local
  preview origins. Foreign/repeated origins, other query/body fields, GET bodies,
  duplicate/third instances, invalid numeric values and unsupported operations
  reject. POST bodies are limited to 4096 bytes.

A stale reconstructed-state guard returns 409 and its current content revision.
Other invalid commands return safe 422 errors; source verification failures
remain unavailable. This is stateless content validation, not a persistent
server head, cross-tab lock or saved history. A later GET is empty regardless of
prior POSTs. There is no automatic retry or source migration.

The core and API tests report 40 passes (31 core and nine API cases), with the
existing TestClient deprecation warning. The API fixture is deliberately
source-only: catalog assets remain unavailable, no output directory is created,
and commands still demonstrate metadata reconstruction without inventing a
model. The tests exercise two Adds, a valid translation, fresh preparation,
no writes, duplicate/stale/foreign fields, numeric/nonfinite failures, size and
origin/preflight boundaries. Scoped Ruff and mypy pass. These are in-process
checks, not live-host or browser observations.

The route is mounted in the actual workbench after PR129 merged. The ninth API
case exercises that factory, preserved legacy source routes and the absence of
a saved arrangement head. The combined check and native acceptance are recorded
separately in the integration report. Existing source
flags, all 55 RP1 accounting rows, D1 and physical/flight gates stay unchanged.
