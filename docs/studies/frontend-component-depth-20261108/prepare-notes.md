# Repeatable component-detail preparation

`scripts/wo04_prepare_component_detail.py` prepares the **18 already registered mechanical child GLBs** without rerunning the original closed exporter or any CAD generation. It preserves catalog SHA-256 `1044bc7aeacad0802fe74add1fecbc77aeddcd0ed09f493c685bb639d271eda1`, frozen core/source hashes and the original exporter code pin. It never rewrites the catalog, core assets or evidence.

Run the read-only default check with:

```sh
.venv/bin/python scripts/wo04_prepare_component_detail.py --verify
```

Normal preview preparation can call this **after matching core and optional-detail preparation**:

```sh
.venv/bin/python scripts/wo04_prepare_component_detail.py --prepare
```

The fixed public destination is `web/public/engineering-workbench/rp1-component-detail/`. The existing output cache is `output/rp1-component-detail/`. A temporary `--destination` is supported for focused tests; arbitrary external destinations are refused.

## Startup paths

1. **Already prepared:** verify immutable catalog, original exporter code, every source pin and all public child byte hashes; report `verified_existing_public`, with **zero reconstruction and zero writes**.
2. **Public folder absent/partial, child cache valid:** stage only registered cache files, verify each child's recorded SHA-256, oriented triangles and bounds, recheck source pins and atomically publish the fixed folder.
3. **Child cache missing on a fresh host:** reconstruct only missing registered children in temporary staging from matching existing parent GLBs. Reuse the original frozen `split_exact` algorithm and source component ordering; reuse the existing named forward-ring layers. Require exact child byte hashes, oriented-triangle fingerprints and bounds before publication. No new geometry, dimensions, material or tolerance is introduced.

Fresh reconstruction requires the source supplies listed in the immutable catalog: core fin/tab/gusset/body GLBs, existing optional motor-tube/aft-ring/forward-ring GLBs, the optional manifest, frozen specification/definition/record, feature map and source-code pins. **A fresh Git checkout alone does not contain all these ignored generated files.** Missing sources report explicit unavailable status and a nonzero exit. This script does not generate parent/core CAD, download data or install dependencies. The normal preview pipeline must first supply the exact matching parent assets; changed hashes remain a stop, not an invitation to update pins.

There is no fallback after source, cache-byte or reconstruction mismatch. Unregistered destination files are preserved and cause refusal. Staging is removed on failure, and a replaced folder is rolled back if publication fails. A valid existing folder is never rewritten merely for startup. Missing dependencies and resource failures are reported without installation/retry. Reconstruction has a **90 CPU-second / 120 wall-second** limit, with earlier cooperative reserves.

## Completed checks

Four focused tests passed in **4.82 s**: read-only verification plus repeatable cache copying, one empty-cache reconstruction in a temporary directory reproducing **all 18 exact child byte hashes**, explicit missing-parent-source refusal, and changed-catalog/corrupt-cache/unregistered-file preservation. The fresh-host test did not touch actual output/public caches or invoke the original export entry point. Ruff lint and formatting pass.

The authorized actual `--prepare` call found the existing fixed public folder valid and returned `verified_existing_public`: **18 children, zero reconstructed, zero public writes**. The original successful export remains closed. No browser action, source/CAD regeneration, mass/inertia, engineering acceptance, purchase/contact or physical work occurred.
