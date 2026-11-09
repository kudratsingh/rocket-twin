# Downloaded CSV source verification

**The previously completed CSV verification remains valid and was reused rather than repeated.** Its downloaded CSV, saved experiment record and matching Parquet all still match their recorded SHA-256 values. The [verification JSON](csv-download-verification.json) preserves the original cell/timestamp results and adds an explicit integrity/reuse audit.

The downloaded file is `exp-c174705a75b8474290b523e8fb7c1267-playback.csv` (**2,518,644 bytes**), SHA-256:

`6f181fc80c8b3f402ebc62383c3a55466a40d8cc6e8079d16d07c2e2c9b27d34`

Its exact saved source is `runs/exp-c174705a75b8474290b523e8fb7c1267/telemetry.parquet`, SHA-256:

`852dc15107622bc69c4d4764550faec257e5c768b8ee11a364468aec95a5a277`

The saved `record.json` also matches the identity in the existing [run-source evidence](source-verification.json):

`ea22ffc8aeeaef6098b14ee2f3a44782ba9593d0d6503d40c6cea59bfcd43d1b`

## Preserved comparison result and limits

- Source Parquet: **9,000 rows**. Downloaded bounded CSV: **3,006 rows**.
- The prior check found **117,234 exact numeric values across 39 shared raw channels**, equal to 3,006 × 39. This does not claim a new check of backend-derived display channels.
- Every exported timestamp was an exact source sample; timestamps were strictly increasing from **0.005 s** through **45.00000000000457 s**. No interpolation or synthetic boundary sample is established by this evidence.
- The export retains a bounded subset with source/event-neighbour samples. It is **not full-resolution telemetry**, even though its selected range spans the Tiny window.
- The actual run remains a **partial trajectory** with **landing null**. This CSV result does not establish a completed landing, physical flight, independently validated wind response or engineering acceptance.

The original verification artifact's SHA-256 before the reuse annotation was `c057e119190cdad1d3fb45f46fef43a9f8568ebfe9dffbfc56088bd74990d02d`. The new audit checked current bytes and the saved result's consistency; it **did not reload Parquet data or repeat the row-level comparison**. One integrity-check execution used approximately **0.0055 s wall / 0.0042 s CPU**, within the 60 CPU-second allowance.

The separate P45 browser metadata-export action remains blocked by the recorded multiple-download permission/automatic-review boundary. This existing-CSV validation does not substitute for it or change that permission. No browser, download, simulation, cancellation, metadata workaround, permission action, network/contact or unrelated edit occurred. Primary retains publication; all physical/build/flight gates remain unchanged.
