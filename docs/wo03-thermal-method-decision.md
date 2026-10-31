# Thermal method decision — stop blind full-size retries

**Latest checkpoint:** [external Elmer/CalculiX evaluation](wo03-external-thermal-decision.md)
is complete as a bounded partial comparison. Neither tool is selected for an
actual-baffle run: availability, precise energy output and spatial-wall evidence
are unresolved. Historical stopped approaches below remain stopped.

2026-10-31. **The original optical-parent-preserving mesh route is stopped under
its present caps.** A completed debug transient exists, but its source field is
numerically failed. The next task is the small error-isolation packet in
[the closure plan](wo03-closure-plan.md), followed by a feasible representation
of the actual gas domain. There is no new physical design or temperature pass.

## Executed stopping evidence

The middle mesh has five exact zero-volume cells. One volume optimization and
the duplicate-only quotient still fail unchanged topology guards. Native
isotropic remeshing and midpoint boundary refinement hit their declared caps.
They are retained as invalid/incomplete attempts, not thermal design failures.

The subsequent read-only [strip-count preflight](wo03-strip-refinement-preflight.md)
establishes a necessary lower bound of **122,166 boundary nodes /245,188
triangles from original-edge subdivisions alone**. This already exceeds the
120,000/240,000 caps while retaining the old vertices/parent edges and requested
resolution. Adding the cap-area requirement raises the lower bound to
123,510/247,876. It is not sensible to repeat that construction under those caps.
The wider150k-node/750k-tet envelope is unproved, and the existing100k-free-node
factor guard must also be respected. Old density ratios are not a meshing proof.

## Alternatives assessed

The completed [known-case isolation](wo03-thermal-error-isolation.md) strengthens
this stop decision. The exact affine935:1 case passes. The curved strong-wall
case has local errors4.617→1.156→0.288 K across three refinements while its
energy balance and coarse5% map-convergence indicator pass. This isolates a
coarse spatial/Robin representation mechanism; it does not uniquely explain the
actual geometry's much larger errors. Its finest local-envelope and strict
reference-heat checks remain failed. No new full-size factor is justified yet.

| Route | What it retains | Evidence needed before actual use | Present decision |
| --- | --- | --- | --- |
| Independent analysis surface discretization, same conduction equations | Actual BRep/material boundaries, seams/notches/openings, solid barriers, contact ownership and prescribed gas/brightness identities | Preserve the exact planar union where possible; otherwise bound geometric error against thin-wall/gap dimensions under existing guards. Register gas and optical quadrature by physical face and conservative area integration. Recompute wall terms; never copy old M/B/D. Demonstrate geometry validity, known-case accuracy, admissible actual local fields, heat balances and refinements. | Preferred detailed-method contingency to assess after small cases. Retaining every old optical vertex is a discretization restriction, not a physical requirement. Removing it must not remove materials or openings. The rejected native pilot is not a validated implementation. No actual retry yet. |
| Hybrid analytical narrow-gap sections plus explicit opening/junction subdomains | Geometry-derived channels and every real opening/material/contact route, with declared junction ports and finite thermal masses | Verify analytical sections and junction response against independent cases; bound end/3D effects, spatial variability and domain-interface error. Radiation must retain actual visibility. For conservative use, prove the resulting uncertain network encloses relevant temperatures over time, including mixed hot and cooling paths. | Candidate bounded alternative only. No current result has these guarantees. It may be cheaper than a monolithic mesh, but a coaxial model alone omits decisive paths and is rejected as a substitute. |
| Equilibrated-flux/goal-oriented error bounds on a detailed solution | The existing physical PDE/domain, with explicitly admissible potential/flux fields | Boundary/source data, local flux equilibrium, reconstruction and any constants must be controlled. Bound the actual output of interest, not just an unrelated norm. Extend/verify treatment of Robin walls, nonlinear radiation and transient coupling as necessary. | Possible numerical tool, not a ready implementation or claimed temperature bound. Development effort may exceed remeshing; do not add a solver package or begin a broad framework without a bounded demonstration. |

The last route has a research basis: potential/flux reconstructions can bound
specified linear outputs of the Poisson problem. An energy-norm guarantee does
**not** by itself bound a local peak temperature. This is a limitation of applying
that result here, not a claim that our current solver implements it.
[Parés, Nguyen, Díez and Peraire, goal-oriented potential/flux reconstruction](https://arxiv.org/abs/2106.10945).

## Executed correction-trial stop

Two separately sourced, fixture-only wall treatments have now been executed;
**this family is stopped after its authorized maximum of two trials**. No failed
actual operator was patched and no production thermal source changed.

| Trial | What improves | Decisive failed check | Decision |
| --- | --- | --- | --- |
| Vertex quadrature for wall and source | Removes local envelope violations on the regular fixtures | Strong-wall continuum source heat defect remains4.211W at the finest grid; exact heat/volume comparisons fail | Rejected standalone. [Trial1](wo03-robin-lumped-trial.md) |
| Lumped wall with original accurate source B/D | Local envelope and continuum net-source heat are preserved | Strong-wall maximum nodal error9.020K, facet-mean error8.297K; nested-field change8.430% exceeds5%; reference heat fails | Rejected standalone. [Trial2](wo03-robin-hybrid-trial.md) |

The simple regular-grid volume operator has no positive offdiagonals above its
declared tolerance. The actual old volume operator does, including at the
interior overshoot, so a boundary-only improvement would not qualify it anyway.
The next route must address actual geometry/resolution and controlled local
accuracy or justified bounds. There is no third wall-formula adjustment, cap
increase, weaker numerical criterion or new full-size factor in this branch.

## What a conservative thermal result would have to establish

Conservative means an explicit enclosure covering numerical and relevant input
uncertainty. It cannot mean “one hot-looking case,” the old band-model result,
or setting every parameter to its maximum. A contact can cool one part while
heating another; removing mount-to-shell contact previously raised the modeled
shell temperature. Mixed parameter effects require proved monotonicity or an
enclosure covering their combinations.

Any replacement must include the required300°C case / contaminated foil /35°C
ambient through burn and soak, plus the rest of the active matrix. It must cover
case/end histories, material properties, adhesive coverage/thickness/contact,
gaps, emissivity and numerical error. Missing local-hot-spot coverage stays
unavailable. A temperature interval straddling45°C leaves acceptance open; an
ambient-to-case interval alone is too broad to choose this design. No screen,
required case, mass allowance or release gate is relaxed.

Before another full actual factor: pass the known-case isolation packet, state
the changed numerical treatment, show a feasible resource estimate, verify its
geometry/mapping and declare one bounded trial. A repeated unexplained invalid
cell/connectivity result or time/resource cap stops that treatment and returns
the decision here. Budget increases require an explicit resource rationale;
they cannot substitute for resolving a numerical defect.
