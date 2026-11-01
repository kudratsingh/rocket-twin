# One S1 short-subframe admission packet

Status: not admitted; no native CAD/FEA/thermal or free-flight invocation.
The exact executed maintained script and study YAML are copied here. The record
pins original73-part as-run canopy YAML (distinct from its metadata-corrected
identity), source72-part geometry YAML, engineering properties and the archived
schema/guide function. Archived native geometry is not included or regenerated.

Run in a separate prepared checkout/output location; the command refuses to
overwrite this packet:

```
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python scripts/wo03_g80_short_subframe.py
```

The execution used the existing source-identical staged schema so stale root
CAD caches were not overridden. The external supervisor applied10CPU/20wall
seconds and observed exit0; requested thread counts were1, OS affinity is not
claimed. Actual hand-worker CPU0.385s. Production physics remain in the shared
backend. No new numerical solver, package upgrade, paid compute or physical
work is included.

`decision-audit.json` regroups already saved masses and the guide ceiling; it
is not another solver run. Mandatory-solid floor is conditional on this one
specified geometry and retained estimated source ledger. The preliminary
budget includes unqualified hardware/coverage assumptions; it is not a CAD-
reconciled installed mass. The heel screw stack also fails, so this cannot be
promoted to a physical candidate or accepted frontend analysis snapshot.

See `docs/wo03-g80-short-subframe-decision.md` for force paths, joint details,
limits, the unchanged thermal/strength/guide criteria and required interface
revision. Existing physical/purchase/paid/firmware/flight gates remain intact.
