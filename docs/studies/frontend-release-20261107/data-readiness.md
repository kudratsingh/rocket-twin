# Frontend release data readiness — 2026-11-07

**A saved representative long-run dataset exists.**
`exp-ab60bd4ac5c2412a9dd85f712072bca2` contains 132,856 samples at a recorded
1 ms step and spans T+0.001 to T+132.8560000002703 s. Its saved configuration,
resolved-specification hash, CAD revision and all 42 saved resolved part-shape
identities match the current archived G54 mesh manifest. Its five recorded
input-file hashes match current local source bytes. No new flight run is
needed to supply a candidate dataset for RV-Q30.

This establishes dataset readiness for the separate conditional G54 fixture.
It does not establish RP1 replay compatibility, physical recovery validity or
browser performance acceptance. The JSON evidence and exact file/mesh/analysis
hash inventory are in [data-readiness.json](data-readiness.json).

## Representative dataset and exact identity

| Property | Saved value / verified comparison |
| --- | --- |
| Run ID | `exp-ab60bd4ac5c2412a9dd85f712072bca2` |
| Configuration | `modular-performance-g54-hypothesis` |
| Raw rows / columns | 132,856 rows; original column names retained in JSON |
| Raw time window | `[0.001, 132.8560000002703]` s; 132.8550000002703 s between endpoints |
| Sample-rate basis | `record.case.dt_s = 0.001` s declares 1,000 Hz; footer count/range are consistent with that declaration |
| Time missingness | Parquet footer reports zero null `time_s` values; interval uniformity, monotonicity and all-channel missingness were not independently reread |
| Saved completion | `status: complete`, `trajectory_complete: true`; saved landing event is T+132.8560000002703 s |
| Record file SHA-256 | `a21d8edd08c452f0b21a94c039971c5bfcd6145ee29330afd66c086da50ff49b` |
| Raw telemetry bytes / SHA-256 | 33,818,386 bytes; `7bad495686018a6f97c6ccd19b87a7388cb1290540489a44b83629e2e052c845` |
| Saved resolved JSON file SHA-256 | `a7d339654888ac8795c523eefc3d0f61d9a140fd97f850aa6cd34019ac6f0eb9` |
| Recorded canonical resolved-specification SHA-256 | `481706d1c4768d944ad42fd917ef4216196de50a277743b1cedb76954940e45f` |
| Recorded CAD SHA-256 | `1193713d0f4a7ad8393a00a0a03e7aaa04e9aa9393d2034691ef7126ae3cdd3b` |
| Recorded simulation-code SHA-256 | `dde080e919510712c4a1daa1175cc76f8ca1bfafd46135cbdaae0448a3e71a90` |
| Matching archived mesh manifest SHA-256 | `8ec617de9cacc356867627a5bbff73e286cdd87c1ee06e75086b826ea15f0bf1` |

The raw saved resolved JSON file hash and the recorded canonical resolved-model
hash name different serializations. They must not be substituted for each
other. Saved resolved JSON geometry/CAD dictionaries reproduce all 42 manifest
part-shape hashes. The archived traceability record also matches current
source-file bytes, the canonical resolved hash, the current legacy CAD revision
and the full part-shape map. All 42 listed G54 GLBs are present; current byte
fingerprints are recorded. Original manifests did not record expected GLB byte
digests, so current fingerprints do not independently attest to original export
bytes.

The additive RP1 inspection exporter is outside `src/cad/`, so the legacy CAD
revision remains unchanged. RP1's new inspection identity remains separate
from this archived G54 configuration and its saved simulation-code identity.

## Other long dataset and saved status examples

`exp-da02d58e35af404faf2802bea54c942b` also has 136,637 rows, a declared 1 ms
step, zero footer-null time values and a T+0.001–136.63700000028837 s window.
Its 34,123,758-byte telemetry SHA-256 is
`d05547372bcd36216a2d2807ed946bdee69529b37346c9d44286b7904f3b6981`.
Its recorded resolved hash is
`766ef7768e98f9256bce9628aa5002a30e53143debf2ec26bef5ab374141eb51`,
CAD hash is
`671116b6a3e90d111b37d7e6dcab7cb17a20821eb6ff6b52475dcb5a27bbf80f`,
and simulation-code hash is
`64f3cb1d69f35cd87094938393d4391e044cb49e4121b6352a0b84bf95638f8e`.
The configuration name and saved part-shape map match, but its resolved/CAD
hashes and two current source-file comparisons fail. It must not be attached
to the current G54 model merely because the name or part geometry agrees.

Seven experiment records are saved locally. All have a stored terminal status
of `complete`; one explicitly has an incomplete trajectory. No saved `failed`,
`cancelled`, `interrupted`, queued or running record is available as a real
status-state fixture. This absence is recorded without creating an artificial
run or mutating an existing record.

| Saved run ID | Configuration | Rows | Declared step | Last footer time | Trajectory complete |
| --- | --- | ---: | ---: | ---: | --- |
| `exp-0dcdfdf88d40435189a678dc77f5773f` | G80 archived reference | 9,000 | 5 ms | 45.00000000000457 s | **false**; landing unavailable |
| `exp-173525a242be493e8e3268471b8e16aa` | G80 archived reference | 116,029 | 1 ms | 116.02900000018997 s | true |
| `exp-1f2178e749f049f18181e123078679bd` | G80 archived reference | 116,502 | 1 ms | 116.50200000019223 s | true |
| `exp-ab60bd4ac5c2412a9dd85f712072bca2` | G54 conditional hypothesis | 132,856 | 1 ms | 132.8560000002703 s | true |
| `exp-c6af2dc4871942dc97632ae44d6613c9` | G80 archived reference | 116,029 | 1 ms | 116.02900000018997 s | true |
| `exp-cf9e47a650074144856caf50775846d2` | G80 archived reference | 116,029 | 1 ms | 116.02900000018997 s | true |
| `exp-da02d58e35af404faf2802bea54c942b` | Older G54 hypothesis | 136,637 | 1 ms | 136.63700000028837 s | true |

`exp-0dcdfdf88d40435189a678dc77f5773f` is a real saved incomplete-trajectory
example, despite a complete worker status. Its record SHA-256 is
`e4b2bf259405a109c7f1d2ff2aec6d2378aeb5a5e9d74c4db98979f6e9fe0305`.
Its 45 s horizon and null landing must remain distinct from completed recovery.
The 116.029 s replay diagnostic is below RV-Q30's duration requirement; that
fact does not negate the separate 132.856 s compatible G54 fixture.

## Analysis compatibility inventory

The four archived configuration directories contain 27 registered analysis
manifests. Every referenced artifact file is present and matches its recorded
SHA-256. **None of these 27 analysis identities matches the current archived
mesh identity for its configuration.** This is an unavailable-compatible-field
state, not permission to repin old results or invent a field.

| Configuration | Registered manifests | Identity and artifact-hash compatible |
| --- | ---: | ---: |
| `modular-performance-v1` | 8 | 0 |
| `modular-performance-g54-hypothesis` | 7 | 0 |
| `modular-tvc-finned-v1` | 7 | 0 |
| `modular-tvc-finless-v1` | 5 | 0 |

The JSON retains every registered manifest/run ID, identity, field quantity,
association, recorded sample count, provenance, validation label, unavailable
reason and artifact hash comparison. Some old records label fields
`numerically_verified`; most label them `unvalidated`; G12 records also carry
explicit unavailable fields. These labels describe the saved source records
and do not resolve their geometry identity mismatch. No field-payload values
or spatial sample schema were recomputed or revalidated in this audit.

## Remaining RV-Q30 evidence and audit bounds

The existing telemetry endpoint returns at most 3,000 uniformly selected native
samples plus recorded event neighbours, retaining endpoints without interpolation.
It therefore does not send all 132,856 raw rows to the current browser path.
Any playback profile must declare the payload actually exercised. A long raw
dataset alone does not prove that the frontend processes full-rate telemetry,
meets 60 fps or has acceptable load, memory and scrub behavior.

Still missing: permitted runtime observations, actual host/profile and viewport,
frame-time distribution, the measured 60 fps criterion, load time, memory and
scrub metrics. Strict timing confirmation would also require a separate bounded
read of actual time samples; this metadata-only packet did not read arrays.
No browser performance pass is claimed.

Reproduce the source/hash inventory with:

```sh
.venv/bin/python scripts/wo04_frontend_release_readiness.py
```

The audit enforces 10 CPU seconds and 20 wall seconds and completed in
**0.263 CPU seconds / 0.454 wall seconds**. It read saved JSON, Parquet footer
metadata and file bytes for hashes. It did not instantiate a vehicle, call
`build_snapshot`, read telemetry arrays, generate CAD, execute flight or
engineering solvers, invoke API `_record` (which can mutate stale statuses),
perform browser/computer use, or contact anyone. Ruff and Black checks passed
for the new inventory script. Sequential local files are not an atomic runtime
snapshot, Git revision, hosted-check result or physical qualification.
