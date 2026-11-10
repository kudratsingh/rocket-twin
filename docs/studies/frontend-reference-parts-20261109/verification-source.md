# Reference-parts workbench composition — source/API verification

Five focused tests in `tests/test_reference_workbench_composition.py` pass
against the **actual `src.api.workbench_app.create_app` factory** after the primary
mounted the reference router. There is no injected test-only router, synthetic
composition or temporary skip. The source/API implementation files remain frozen
and were not edited by this verification lane.

## What executed

Each runtime fixture copies every exact pinned source input into temporary
storage, creates the four known asset parent paths, and copies a registered
STEP/GLB file only when that exact cache path exists. It does not scan for
substitutes, regenerate geometry or require ignored output on a clean checkout.
A symlink at an optional source cache path rejects fixture setup; corrupt regular
bytes are copied unchanged and must fail source admission. Both the actual
wrapper and the unchanged base inspection factory are constructed with an empty
archived runtime catalog. FastAPI/TestClient calls execute in process: no HTTP
listener, owner service, browser or network is involved.

The executed assertions establish:

- The wrapper serves `/api/reference-parts` and both exact-revision details before
  the base-app mount. Responses equal the source projection, retain the exact
  source/catalog/definition identities and separate cache availability, keep
  unknown physical properties null and every physical/mating/Add/Connect gate
  false, and create no files or draft library.
- Representative legacy responses are byte-equivalent between the wrapper and
  base factories for health, vehicle catalog, the 55-record source parts bank,
  unknown-vehicle rejection, docs and OpenAPI. The existing OpenAPI remains the
  base app's schema; this comparison does not replace it with a new wrapper
  document. The archived catalog declaration/alias still exposes the same four
  entries, without resolving their models in this fixture.
- Reference GET/preflight/errors at origin `http://127.0.0.1:4173` retain the
  route-specific exact origin and GET-only boundary, rather than being intercepted
  by base CORS. Foreign reference origins fail 403. The legacy vehicle route's
  5173/4173 header behavior and PATCH preflight rejection remain equivalent to
  the original base middleware; no global permission expansion is inferred.
- Removing any present temporary reference cache files with
  `unlink(missing_ok=True)` produces unavailable
  reference geometry without changing definition/catalog revisions, regenerating
  files or altering the legacy source parts-bank response. The base health result
  remains flight-ready false.
- The actual frozen archived registry and catalog-equivalence evidence retain
  their pinned bytes. The existing `verify_catalog_equivalence` check accepts the
  current `src/api/app.py` body against its recorded original identity and exact
  admitted parts-bank-route difference, with geometry/assets unchanged.

The temporary fixture file sets/bytes remain unchanged during read-only requests;
no owner draft UUID/library is opened or enumerated. The runtime test forbids
subprocess execution. Empty archived snapshots avoid CAD/geometry creation and
model calculations; source equivalence uses the existing static proof, not new
archive-generation or solver work.

## Clean-checkout branches

Missing cache is an executed assertion branch, never a whole-suite skip. Source,
API and actual-wrapper catalog/detail assertions compute the missing formats
from the exact registered paths and require `unavailable`,
`geometry_available: false`, the corresponding `missing_formats`, and
`generation_attempted: false`. Definition/catalog revisions, nominal analytic
datums, source identity, null unknown properties and false gates remain checked
with no cache. Present registered bytes alone receive byte-count/hash/header
assertions; the historical recorded-readback bounds/validity assertions are
associated only with a fully available case. The manifest's historical readback
metadata does not establish current cache availability or a new kernel readback.

Corrupt-file tests write explicitly invalid bytes at a known temporary cache
path and require rejection, including through catalog and detail HTTP errors.
The symlink case uses an explicitly invalid temporary target and requires unsafe
path rejection. Neither branch invents a valid asset, changes a pinned hash or
converts corruption into a missing-file success.

A second isolated run copies these three test files, all pinned source inputs and
the existing base API body into a fresh temporary source-only mirror. Its four
known asset directories exist, but all four registered cache files are absent
before and after the run. Pytest executes the copied tests with importlib mode;
the unchanged implementation is imported from this repository via `PYTHONPATH`,
while each copied test's `ROOT` and every fixture source come from the cold
mirror. The existing static archive-equivalence module still reads only its
known tracked proof/registry inputs. No owner output is deleted, moved, scanned
for replacements or regenerated. This verifies the clean source-only test
branches, rather than claiming a fresh dependency installation or hosted CI run.
The source-only run reports **42 passed in 10.14s**; the normal scoped run reports
**42 passed in 10.38s**. Both have only the existing TestClient deprecation
warning. No tests were skipped.

## Evidence limits and ownership

The normal scoped run reports **42 passed** across the source, router and actual
wrapper tests (14/23/5), with the existing Starlette/httpx TestClient deprecation
warning. Scoped Black and Ruff pass. The focused portability correction changes
only `tests/test_reference_parts.py`, `tests/test_reference_parts_api.py`,
`tests/test_reference_workbench_composition.py` and this verification document.
No source/API implementation, registry, launcher, UI, fixture, owner cache or
shared ledger was changed.

These are local source/in-process integration checks. Because the fixture uses
an empty archived runtime catalog, it does **not** establish full archived mesh,
analysis, mass-model or saved-run runtime acceptance. Those retain their existing
independent evidence. Likewise this result does not observe native rendering,
annotation selection, camera/focus, asset downloads, live-host availability or
physical fit/strength.

Primary retains actual routing integration, exact-head publication checks,
preview-dev reload, designated-browser acceptance and any further admission.
The read-only reference metadata is not Add/Replace/Connect, a new physical
variant, a resolved candidate, a mass/inertia result or vehicle adoption. Frozen
RP1/AD1/D1 and all physical/engineering/flight gates remain open, and all five
inquiries remain UNSENT. No stopped attempt was resumed or repeated.
