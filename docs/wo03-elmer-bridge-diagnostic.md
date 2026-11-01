# Elmer G80 bridge coarse diagnostic — prepared, execution disabled

The existing 48/24 coarse bridge input is prepared for a possible two-case Elmer diagnostic, but **no native bridge solve has run or is authorized by this preparation**. The frozen config requires both explicit native admission and confirmation of the required solver-evidence CI checks before its execution phase can start. A successful coarse run would remain diagnostic: it would not establish stress accuracy, convergence, installed strength or acceptance.

The prepared input retains the exact original serialized G80 CLOAD tokens through the direct-nodal-RHS path tested by the separately completed B SINGLE known-answer case. It uses the saved 22,495 quadratic tetrahedra and seven materials, with 42,715 used nodes in an explicit old-to-new ID map; the 135 excluded declared nodes were shown to have no element, load or support use. The 1,574 support nodes, original source force/moment resultants and the complete EQUAL (3,184) and SINGLE (1,072) nodal tokens are checked again against the prepared SIFs. The prior conversion independently checked curved-geometry volume against saved mesh integrals, the distinct 1% mesh/CAD criterion, washer areas, shared 10-node topology and connectedness. Source material, load and support assumptions remain those of the unqualified original bridge model; no mesh generation or physical change occurred.

The output reader requires one complete, uniquely coordinate-mapped 42,715-node Float64 displacement field and `Displacement Loads` field; it uses the frozen map to relate original load/support IDs and does not infer values for the 135 unused original nodes. It sums the native support loads without a sign flip and requires the residual norm plus conservative Float64 reaction and serialized-input load encoding bounds to be ≤ **1e-5 N**. Missing/ambiguous/nonfinite fields, unknown mapping or unavailable/failed force precision stop the packet; SINGLE will not run if EQUAL fails. Moment balance and its encoding bound are reported without adding a moment pass threshold.

If both independently solved cases pass their field and force gates, the diagnostic computes `F_equal · U_single` and `F_single · U_equal`, as well as each `½ F · U`, from the exact original nodal load tokens and both displacement fields. As in the [prior reciprocal-work audit](wo03-g80-bridge-reciprocity-audit.md), the difference is compared with propagated Float64 output encoding and the original audit’s conservative half-last-decimal-place load-token bounds (plus binary conversion); no new engineering tolerance is added. A result outside those bounds is explicitly stopped, not a strength result. A single coarse mesh cannot establish the existing three-mesh convergence requirements, regional stress, hot allowables or keeper/installed load sharing.

The [reviewed preflight](../build/wo03-elmer-bridge-diagnostic-v1/preflight-reviewed.json) pins the generated SIF/mesh/map inputs, source deck and metadata, B nodal-RHS result, converter source, installed prefix, StressSolve module, solver, observed hashable runtime dependencies and VTK reader libraries. It verifies source-to-SIF load tokens, all input hashes, support/load mapping, input force/moment, coordinate uniqueness and runtime pins before execution; the same checks repeat after each case and at completion. Any source, field, force, solver or resource failure stops without retry. One CPU is requested; no OS-affinity claim is made. The 2 GiB RSS cap applies to each supervised **root process**, not the process tree.

The future packet is two cases at 120 CPU / 120 wall seconds each plus 60 CPU seconds setup and 120 CPU seconds parent reservation, totaling 420 CPU seconds under 600. Each case runs in a fresh directory with the prepared physical mesh and direct UMFPACK; EQUAL precedes SINGLE. The exact unused iterative-option keyword row is tracked separately from native error/nonconvergence text. Four focused synthetic tests cover force failure, missing/nonfinite field/coverage, reciprocal-work reporting, and the original decimal-token rounding convention; they are not a bridge solver run. Ruff and Black passed. Input preflight measured 0.853 s wall / 0.858 CPU s / 345,948,160 bytes process RSS; the subsequent source review used 0.850 s wall / 0.907 CPU s. Test/setup work beyond those samples was unmetered and is not zero. No native, CAD, thermal, installation, vehicle or physical work was performed.

### Read-only known-B reciprocity check

The unchanged comparator was applied once to the saved, valid B EQUAL and
SINGLE Float64 fields and the original serialized B nodal load tokens. It gave
`F_equal · U_single = 0.047343749999970056 N m` and
`F_single · U_equal = 0.04734374999997012 N m`: their absolute difference is
`6.245004513516506e-17 N m`, within the unchanged combined encoding bound of
`4.734375000022028e-5 N m`. Both saved fields also satisfy the existing strict
force check. This is evidence for the comparator on this one known case; an
encoding-only interval is not a general bound on numerical solver error. It
does not establish actual-bridge accuracy or authorize a native run. EQUAL was
recovered by read-only evaluation after the original packet stopped; SINGLE
was a separately admitted continuation, not a retroactive pass of that packet.

The [read-only record](../build/wo03-elmer-bridge-diagnostic-v1/known-B-reciprocity-readonly.json)
contains input hashes before and after, mapping and force results. All inputs
were unchanged. The single read-only process used 1.150 CPU seconds and
1.356 wall seconds, with 197,181,440 bytes process peak RSS; no solver ran.


## Source interpretation of the load field

The [pinned-source audit](wo03-elmer-load-field-semantics.md) identifies the
saved field as `K_bulk u - f_bulk`, rather than a support-only reaction vector.
For this diagnostic there are no body forces or mixed boundary terms; target
nodal loads and fixed support nodes are disjoint. Summing only the explicitly
mapped support entries is therefore the intended reaction interpretation, with
its known-case sign evidence kept separate from actual-bridge validation.
The free-node field minus the prescribed nodal vector could support a later
read-only algebraic-residual diagnosis; that calculation is not implemented or
used to relax the unchanged force or reciprocal-work comparisons here.

### Actual coarse packet and stopped SINGLE continuation

The actual EQUAL native process completed, but the original packet stopped
before field assessment because the generated VTU was outside the frozen
reader's searched paths. A separately admitted read-only recovery located the
single file at the path stated by the solver log and applied the unchanged
reader. Its strict force check passed: axial residual `-7.8839e-10 N`, with
`4.1779e-14 N` encoding bound; maximum displacement magnitude was
`0.380781777 mm`. The original packet remains stopped. This one coarse result
is not a strength or convergence qualification.

The separately admitted SINGLE continuation stopped before preflight and before
any native invocation: its launcher could not import the `scripts` package when
invoked from the build directory. The failure, launcher, and admission are
preserved in the compact continuation record. SINGLE and reciprocity remain
unavailable; the disabled configuration and original EQUAL evidence are
unchanged. No retry was made.

The primary then authorized one environment-only startup correction, keeping
the launcher and disabled configuration unchanged. SINGLE launched once. Its
log reports Elmer completed and its process returned zero, but the supervisor
reported an RSS-reader ESRCH while the root process appeared live, so the
supervised case stopped. Cleanup reaped the root without a recorded cleanup
error. SINGLE's saved field and reciprocity were not evaluated, and no retry
was made. Source, runtime and prefix postchecks were unchanged. The compact
path-replan packet records the failure and hashes; no actual bridge
qualification follows.

A separately authorized read-only evaluation recovered numerical evidence from
the saved SINGLE VTU. Its strict force check passed: axial residual
`-1.114529e-9 N`, encoding bound `5.02545e-14 N`; maximum displacement was
`1.1570073 mm`. The unchanged reciprocity comparator gave cross-work values
`0.04008097325330081` and `0.04008097325330107 N m`, a difference of
`2.63678e-16 N m` against the `4.84028e-16 N m` encoding bound. Sources,
runtime and prefix were unchanged. These results do not resolve the
supervisor's RSS-reader ESRCH or establish resource compliance, strength,
convergence, or installed acceptance. The original failed supervisory status
is not revised; no solver was run for the recovery.
