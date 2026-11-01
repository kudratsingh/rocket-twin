# Rejected G80 capture envelopes: supplementary hand checks

This packet records six independent known-formula checks, conditional rail/pin
screens and isolated kA/L conductances. It is not a native finite-element,
transient heat, geometry or flight run. The original defined stock packet is
`../wo03-g80-capture-comparison-20261101-v1`; its full tensors are copied into
the record, with the exact source-record hash.

The record pins the executed script, input YAML, existing material profiles and
stock record. The two copied source files are byte-identical to their executed
maintained versions. Run from the repository root in its pinned environment:

```
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python scripts/wo03_g80_capture_bounds.py
```

The command refuses to overwrite the existing packet. Reproduction requires a
separate checkout/output path, never deletion of a failed or successful record.
10 CPU/15 wall seconds were declared before the one execution; actual CPU was
0.059 s. No native solver, CAD, flight, browser or paid resource was invoked.
The 50 g growth reserve stays separate. Both envelopes were screened out before
detailed analysis, and temperatures remain unavailable. See
`docs/wo03-g80-capture-decision.md` for the decision and evidence boundary.
