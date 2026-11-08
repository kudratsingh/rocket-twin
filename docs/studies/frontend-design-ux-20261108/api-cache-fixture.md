# Deterministic missing-display API fixture

A broader local RP1 API check found an existing test whose premise depended on whether the developer had already prepared the RP1 display assets. Thirteen checks passed, but `test_current_ad1_endpoints_preserve_source_and_withhold_missing_models` expected no mesh URLs while the real local cache correctly supplied26. This was a test-fixture assumption, not a failure of the display API or an engineering result.

The missing-display case now explicitly makes `rp1_geometry.build` report unavailable. It retains all source identity,55-record, canonical-inertia, mass409 and empty-analysis assertions, and adds explicit unavailable-geometry and incompatible-presentation assertions. Existing generated-root projection tests separately exercise available display meshes and exact asset/source mismatch handling. No cached exports are deleted or changed, and no product behavior is altered to satisfy the test.

After correction, the combined source inspection, missing-display API, generated projection API and connection API selection passes14tests in15.79seconds. The focused case passes independently; Ruff/Black pass. A FastAPI/Starlette deprecation warning remains; this packet does not change pinned dependencies.

This test-only follow-up is separate from frontend browser acceptance. Frozen AD1/D1, supplier drafts and all engineering/physical/flight gates remain unchanged.
