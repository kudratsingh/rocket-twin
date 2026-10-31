# Actual-CAD radiation reconciliation remains a screening calculation

The raw first-hit ray counts remain unchanged. The new preparation step fits a
reciprocal, closed operator to those counts and checks compatibility with their
sampling intervals before the operator can enter a transient calculation.
It does not add a visibility path where both directed hit counts are zero.

This matters for the fitting-baffle source because tiny epoxy-edge patches have
much smaller area than the large ring or shell surfaces they see. An unweighted
average of reciprocal exchange-area observations gives a rare reverse hit from
a large surface excessive influence. In this executed case the old symmetric
balancing changes **26 directed entries beyond conservative simultaneous
sampling intervals**, with a largest exceedance of 0.271943 in view factor.
That candidate operator is rejected for transient use and retained in the new
record. The raw geometry/ray evidence itself is not overwritten.

The replacement maximizes the ray-destination count likelihood subject to fixed
surface areas, reciprocal exchange and closure. This uses the same mathematical
constraints as a reversible transition matrix with known stationary populations,
with populations proportional to physical area. This is our application of the
fixed-population likelihood equations in [the estimator paper, section II.C](https://pmc.ncbi.nlm.nih.gov/articles/PMC7047717/)
and [Trendelkamp-Schroer et al.](https://arxiv.org/abs/1507.05990), rather than a
new physical heat-transfer law. An independent two-surface scalar optimization
checks the fitted result, count-scale invariance and preserved zero support.

Executed record:
`runs/wo03-cad-radiosity-20261031T051129909396Z/record.json`.
Candidate is `69df790…`, generator `1193713…`, using the original 1,127 groups
and 1,150,000 fine-level rays. Raw count/operator/group/spec hashes are pinned.
The fitted operator has **zero entries outside** the declared intervals. Those
are Bonferroni-adjusted Clopper–Pearson marginal intervals over 1,270,129 ordered
pairs, with family alpha0.05. They can be very broad (maximum width0.858), so
passing is a consistency condition, **not local optical convergence** or a
confidence bound on temperature. The earlier three-level local sampling
limitations remain open.

Separate diffuse-gray operators are prepared for foil emissivity0.1/0.3/0.9;
black external openings stay emissivity1. These operators have zero isothermal
heat transfer to floating-point precision. No temperature history, new material
limit, active adoption or thermal acceptance is produced. Physical gas opening
temperatures remain separate from radiative brightness when coupled later.

```sh
.venv/bin/python scripts/wo03_cad_radiosity.py --preset tiny
.venv/bin/python -m pytest tests/test_radiation_sampling.py -q
```

The exact source snapshot and hash-pinned local assets are required to reproduce
this record. Generated operator arrays remain local; compact numerical evidence
can be published. Raw sampling and material/contact/boundary uncertainties must
remain visible in every downstream result.
