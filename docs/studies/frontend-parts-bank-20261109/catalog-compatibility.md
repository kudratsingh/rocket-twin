# Preserving the archived CAD download audit

The first combined web run had332 passes and one failure. The Parts bank API
added two GET handlers to `src/api/app.py`; an existing CAD preview preparer pins
that whole file as its catalog source. The archived source geometry, four vehicle
catalog declarations and asset identities had not changed, but the original
whole-file check correctly rejected the changed source. The failure log is retained
locally in `.cache/fw2-bank-web-full.log`.

The original audit `docs/studies/frontend-desktop-detail-20261108/archived-cad-access.json`
and its SHA `cd3cc2557c61df5f051fbc5a48002ef62678831e1639379364a19ead6398f49f`
remain unchanged. No exporter, CAD generation, public overwrite or shape change
was performed. The new companion [equivalence record](archived-catalog-equivalence.json)
is separately pinned by the production preparer.

## Narrow comparison

1. Fetch the original API source from the exact public main commit38e70be….
   Require its exact registered byte SHA `04d83d808491629eef5906a2274b073b10d494f257cc9a2ced07b553cf51591c`.
2. Compare the original and current `CatalogEntry`/`CATALOG` syntax trees.
3. Remove only the new named `source_parts_bank` and `source_part_definition`
   handler definitions from the current `create_app` syntax tree. Require the
   entire remaining module tree to match the original. This confirms that no
   existing API behavior was edited in this packet, not merely that four paths
   happen to match.
4. Pin the exact current API byte hash and the companion record. The preparer
   accepts either its original exact API bytes or this exact route-only extension;
   it does not accept arbitrary future edits with similar-looking catalog data.
5. Continue every original CAD source, resolved configuration, part-shape,
   manifest, inventory, path and asset hash check. Original provenance files
   are copied unchanged and still describe their historical export source.

The first diagnostic proof used host Python3.13.7, whose syntax-tree serialization
includes fields absent from pinned Python3.11.16. Its2/4 unit failures are retained
in `.cache/fw2-catalog-equivalence-tests.log`; the initial record is in
`.cache/fw2-catalog-proof-system-python.json`. Recomputing through the project's
pinned Python3.11 interpreter corrected that method mismatch. The helper now
requires Python3.11 explicitly instead of misreporting another interpreter as a
catalog change. No source-equivalence or asset criterion was relaxed.

Four corrected unit cases pass: the exact extension; rejection of an unrecorded
byte edit; rejection of a changed catalog; and rejection of unrelated existing API
behavior/foreign registry. All six archived-CAD focused web tests pass, including
verification/copy to a temporary test destination. Full repository Ruff/Black/mypy
checks pass. The first failed full web result is not relabeled as a passing run;
subsequent combined/hosted checks are recorded against their exact code head.

This record supports source-compatible supply of the same archived CAD artifacts.
It supplies no current RP1 geometry, inertia, fit, structural, thermal or flight
validation.
