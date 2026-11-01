# Structural solver decision — limited known-case qualification

The selected next route is the existing isolated **Elmer StressSolve with
direct UMFPACK**, for one bounded diagnostic of the saved G80 bridge model.
This decision qualifies a specific input/output path on the small layered-bar
problem. It does not qualify bridge stress, hot bonds, installed fins or the
vehicle. Thermal-tool qualification is a separate, still-negative decision.

| Route and evidence | Process execution | Displacement and force evidence | Decision |
| --- | --- | --- | --- |
| CalculiX SPOOLES, documented binary vector output (B1) | Completed | Known displacement passes. Step 1 residual plus float32 encoding uncertainty cannot certify the unchanged 1e-5 N force limit; step 2 individually passes. | Packet stopped; do not advance this route. |
| CalculiX iterative Cholesky (B2) | Completed | Known displacement fails: transverse motion reaches 0.08850 mm where the zero-component limit is 1e-8 mm. Later force checks were not reached. | Stop; no tuning or actual-bridge retry. |
| Elmer direct UMFPACK, EQUAL | Completed; original checker stopped on an unused keyword containing “not converged” | Separate read-only assessment of saved Float64 output passes all-node displacement and strict force checks. Maximum axial error 2.0751e-15 m; force residual components are below 1.8e-11 N. | Individual known-case evidence recovered; original stop remains preserved. |
| Elmer direct UMFPACK, SINGLE | Separately admitted remaining case completed; EQUAL not rerun | Maximum axial error 6.2241e-15 m; force residual components below 9.6e-11 N, including output precision well within 1e-5 N. | Specific two-load known-case path supported. No actual-geometry pass. |

A third, separately admitted [matching-B nodal-RHS case](wo03-elmer-nodal-fixture.md)
also passes: its 13 exact original load tokens use the same input path required
by the bridge. Maximum axial error is6.2246e-15 m, axial force residual9.533e-11 N
and encoding bound1.066e-14 N, with the unchanged analytic/force criteria.
This closes that source-path prerequisite on B; no actual bridge solve ran.

The comparison uses the same saved 593-node / 254-quadratic-tetrahedron
physical problem, original material regions, supports and reconstructed loads.
The 1% axial displacement criterion, 1e-8 mm zero-component criterion and
1e-5 N force criterion are unchanged. Native reaction signs were used without
flipping. Moment residuals are reported; a new moment threshold was not
invented. The deliberately simple linear-elastic material values are method
verification inputs, not properties measured on the proposed adhesives.

The Elmer artifact is pinned in the [fixture report](wo03-elmer-structural-fixture.md).
Its direct-library build and symbol probe are recorded separately from the
actual solver loading. Float64 fields remove the observed B1 output-precision
obstacle for these two tests. They do not explain or cure the saved real
bridge's 104.697/22.093 N reaction imbalance or reciprocal-work discrepancy.

The log-classification correction is limited to the exact unused iterative
setting row in an observed **direct** solve. The stopped original packet,
read-only EQUAL assessment and SINGLE continuation remain separate records.
No numerical threshold, sign, load, material or boundary condition was changed.

## Bounded next deliverable and stop condition

The [bridge input conversion](wo03-elmer-bridge-input.md) now preserves the existing
mesh, physical connections, support and two load cases. Its first attempt
compared mesh volume with CAD volume too strictly and stopped. A read-only
diagnosis identified that category error; the separately admitted v2 compares
serialization against the saved mesh integral and checks the original CAD
approximation criterion separately. Both pass without changing geometry. Verify node/element
mapping, material volumes, loaded areas, force/moment and exact load distribution;
prove any excluded nodes are unused. The bridge uses equilibrated affine-pressure
quadrature loads, unlike the uniform boundary tractions in the small tests.
The separate nodal-RHS mapping has now passed that matching known-answer
gate; its actual-geometry force/moment and reciprocity checks remain required. Stop before execution if these cannot be
mapped. The proposed packet reserves two serial cases at 120 CPU / 120 wall
seconds each, 60 CPU seconds setup and 120 CPU seconds parent: 420 planned CPU
seconds under 600. One CPU is requested; 2 GiB applies to each supervised root
process, not the process tree. Input preparation alone authorizes no native run.

After publication and primary admission, the first actual-case attempt must
stop on missing fields, source change, nonfinite values, equilibrium failure,
solver error or resource cap. No automatic alternative backend or repeat is
permitted. A completed coarse solve would remain diagnostic until reciprocity,
boundary/load interpretation and the existing three-grid convergence criteria
support its intended engineering use. An inconclusive or failed attempt requires
a recorded cause and replan, not another blind run.

No thermal actual-baffle attempt, production heat solver, CAD adoption or
physical qualification follows. The [closed thermal decision](wo03-elmer-campaign-decision.md),
required thermal matrix and unchanged 45 °C substrate screen remain in force.
The active working vehicle, G54 and G12 configurations are unchanged. WO-03
remains open.

Evidence: [B1](wo03-ccx-backend-diagnostic-plan.md),
[B2](wo03-ccx-b2-diagnostic-plan.md),
[Elmer fixture and compact records](wo03-elmer-structural-fixture.md),
[current G80 closure table](wo03-g80-current-closure.md).
