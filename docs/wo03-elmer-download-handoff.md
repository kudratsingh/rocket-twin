# Isolated Elmer prerequisites — download-only handoff

The agent's shell cannot resolve GitHub and CMake is absent. Run the following
in a normal macOS terminal with working internet access:

```sh
cd /Users/kudratsingh/Machine-Learning-Projects/rocket-twin
.venv/bin/python scripts/wo03_fetch_elmer_eval.py
```

This only downloads two public archives into
`.cache/elmer-evaluation/downloads/` (approximately 150 MB total). It does not
extract, install, compile or execute either archive, change project dependency
pins, or start an engineering calculation. The working vehicle is unchanged.

The helper enforces one acquisition attempt, a 120-second per-file alarm and
300-second total allowance, with a 100 MiB per-file limit. It preserves partial
files and a failed manifest rather than overwriting or retrying automatically.
An offline corrupted-checksum fixture verifies that an unverified archive cannot
be renamed to the final name. No network access is used by that test.

## Official identities

- **CMake 3.31.8 macOS universal archive**, 78,373,419 bytes; SHA-256
  `d1449f969c54d5c00886d5b643340d493dfb3c81cb39ee29b35453395c11ebf7`.
  The official [GitHub release metadata](https://api.github.com/repos/Kitware/CMake/releases/tags/v3.31.8)
  supplies both the archive URL and digest. The helper requires this checksum.
- **Elmer 26.2.1**, annotated tag object
  `38fbce9fa264cb4b6f740cc045f1e8fbb876e06e`, peeled commit
  `a19504ac53ec222e3355e182b08f2ff280c2203a`. The official
  [tag object](https://api.github.com/repos/ElmerCSC/elmerfem/git/tags/38fbce9fa264cb4b6f740cc045f1e8fbb876e06e)
  supplies that binding. The archive URL uses the full commit. Its downloaded
  SHA-256 is recorded for subsequent checks; an independently supplied archive
  SHA-256 has not been established. A recorded digest is not a tool-qualification
  result or independent authenticity proof.

The final `acquisition.json` records URLs, checksums, sizes, elapsed time and
status. Stop and retain that manifest on failure; do not increase time limits
or switch installers automatically.

## Next gate

Successful download only removes a retrieval prerequisite. Inspect the archives
and validate their source/contents before extraction into a task-specific prefix.
The [headless build preflight](wo03-elmer-headless-build-preflight.md) still leaves
compiler/BLAS/runtime closure, a feasible module set, and a build within the
600-second setup limit unproved. No compilation is selected by this handoff.

Elmer must still demonstrate the unchanged physical known-answer packet,
temperature/heat output precision, local/global energy accounting and spatial/time
refinement before any actual-baffle attempt. Preserve the required thermal
matrix and 45°C substrate screen; neither solver is qualified yet.
