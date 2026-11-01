# Compact saved-field stress diagnostic

Dataset reference: **wo03-bridge-gauss-stress-20261101-v1**. These are completed
coarse numerical stress diagnostics, with no strength, convergence or joint
acceptance. See [the report](../../docs/wo03-bridge-gauss-stress.md).

`equal.json`, `single.json`, `verify.json`, `executed-verify.json` and
`artifact-manifest.json` are byte-identical copies from the local ignored
`build/wo03-bridge-gauss-stress-v1/` directory. Their original absolute paths and
hashes retain the execution context. In particular, the copied artifact manifest
still names original build paths and hashes of the local, deliberately omitted
NPZ sample arrays. Publication does not rewrite or recompute those records.
`record.json` maps every published source/record to its original path and hash
and lists all retained original dataset dependencies by path/hash.

The actual computation worker was the direct Python module invocation below.
There was no separate one-off worker or generated launcher. Its exact executed
source is included as `executed-postprocessor.py` and matches the source hash
inside all three phase records. `source-wo03_elmer_bridge_input.py` contains the
exact hash-pinned derivative/ordering statements used by the worker;
`source-wo03_elmer_bridge_diagnostic.py` contains the unchanged pure SINGLE
mapping/reader functions. The two stress-fixture source snapshots supply the
native B crosscheck. The exact eight-test verification source is included as
`executed-test_bridge_gauss_stress.py`. Current maintained code/tests remain in
`scripts/wo03_bridge_gauss_stress.py` and `tests/test_bridge_gauss_stress.py`.
The maintained source differs from the executed snapshot only by Black formatting
and a citation docstring correction, verified computational-AST identical.

## Reproduction context and commands

These commands are recorded for a future separately authorized reproduction;
**none was run during publication**. Use an isolated repository checkout and the
pinned environment from `docs/ENVIRONMENT.md`, `pyproject.toml` and `uv.lock`
(Python, NumPy, Gmsh, VTK, PyYAML and pytest are required). Obtain the exact local
raw input dataset files listed in `record.json` and verify their SHA256 values
before computing. Original bridge deck/metadata, prepared node map/mesh nodes,
recovery records, the saved EQUAL mapped U archive, saved SINGLE VTU, known B
deck/metadata/VTU and the B native record are required. This compact publication
contains records and code, not those generated raw datasets; it cannot reproduce
field values from the Git repository alone.

For an exact executed-source reproduction in that isolated checkout, restore:

```sh
cp runs/wo03-bridge-gauss-stress-20261101-v1/executed-postprocessor.py scripts/wo03_bridge_gauss_stress.py
cp runs/wo03-bridge-gauss-stress-20261101-v1/source-wo03_elmer_bridge_input.py scripts/wo03_elmer_bridge_input.py
cp runs/wo03-bridge-gauss-stress-20261101-v1/source-wo03_elmer_bridge_diagnostic.py scripts/wo03_elmer_bridge_diagnostic.py
cp runs/wo03-bridge-gauss-stress-20261101-v1/source-wo03_elmer_stress_fixture_reader.py scripts/wo03_elmer_stress_fixture_reader.py
cp runs/wo03-bridge-gauss-stress-20261101-v1/source-wo03_elmer_stress_fixture.py scripts/wo03_elmer_stress_fixture.py
cp runs/wo03-bridge-gauss-stress-20261101-v1/executed-test_bridge_gauss_stress.py tests/test_bridge_gauss_stress.py
```

Invoke from the checkout root, in sequence:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -m scripts.wo03_bridge_gauss_stress --phase verify
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -m scripts.wo03_bridge_gauss_stress --phase equal
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 .venv/bin/python -m scripts.wo03_bridge_gauss_stress --phase single
```

The verification phase invokes the exact pytest source and reads the saved known
B field. Actual use fails closed unless verification matches the exact worker
hash. Each process is limited to 30 CPU/30 wall seconds and requests one CPU;
there is no native solver or mesh generation. Outputs go to ignored
`build/wo03-bridge-gauss-stress-v1/`. A reproduction of maintained, formatted
source uses the same phase commands after a fresh `verify`; its source hash will
differ from the historical executed record.

Equations and limitations are documented in the report and `record.json`, with
Elmer source pinned to commit `a19504ac53ec222e3355e182b08f2ff280c2203a` and
Timoshenko and Goodier, *Theory of Elasticity*, third edition, chapter 1. All
stresses remain raw 150 N service-case values; DF3 is not reapplied here. No
estimated G11/adhesive screen is promoted to a material or joint allowable.
