# Thermal-tool campaign decision — closed, actual geometry unqualified

2026-11-01 UTC / 2026-10-31 Pacific. **Decision: Elmer is available and useful
for the tested offline comparisons, but is not qualified for an actual-baffle
temperature or G80 thermal-acceptance calculation.** CalculiX remains an
independent cross-check and is also unqualified for that use. The declared
nine-result Elmer campaign is complete. No further solve follows automatically
from its unused CPU allowance.

## Four separate conclusions

| Question | Evidence and conclusion |
| --- | --- |
| Can the tool run here? | Yes. The isolated source build, selected modules, local installation and version/runtime check completed in 489.423 s including the owner's 107.013 s acquisition, below the declared 600 s ceiling. No project dependency was upgraded. The executable reports 26.2-unknown and is tied to the recorded 26.2.1 source archive/commit and binary hashes. |
| Are its fields and heat accurate on the known problems? | Partly. A's maximum nodal errors are 1.93e-5 / 1.12e-4 / 3.74e-5 K, all above the unchanged 1e-7 K criterion. B_strong is below 1e-7 K on every level; B exceeds that additional diagnostic at its finest level. B/B_strong have bounded continuous fixture temperatures inside their effective-wall envelopes. Native conductive-flux errors are reported separately; Robin wall exchange and local/algebraic/form balances are unavailable. |
| Do results improve with finer grids? | Not monotonically. A rises then falls, and the tiny B errors rise. Medium/fine nested field changes are very small but do not replace the existing raw-C criterion, which is unavailable. These results establish neither a passed general refinement gate nor a cause for the A discrepancy. |
| Is actual-geometry accuracy/resource feasibility established? | No. These straight affine P2 fixtures have at most 4,913 nodes. They do not validate physically curved narrow gaps, transient heat/soak, opaque/open radiation, real material/contact partitions, local hot spots, or the actual baffle mesh/factor/memory cost. No actual-geometry attempt is selected. |

The complete comparison used 4.1685 tracked CPU seconds including charged
original A-2 and resumed work. The original output-discovery stop is retained;
A-2 was read from its saved output, not rerun. See
[comparison](wo03-elmer-thermal-comparison.md),
[tagged source audit](wo03-elmer-tagged-io.md) and
[mixed-wall diagnosis](wo03-elmer-mixed-wall-diagnostic.md).

## Software verification versus a temperature design decision

The 1e-7 K exact-field and 1e-10 W balance checks test intended mathematical
reproduction and implementation accounting. They remain in force and their
failed/unavailable states remain visible. A small error is still a failure of
that specific check; successful exit or Float64 output is not a substitute.

The largest observed toy-field error, about 0.000112 K, is much smaller than
the 10 K between the required 35°C ambient and 45°C provisional substrate
screen. That comparison explains the different purposes, **not** an accepted
error budget for the rocket. The actual numerical uncertainty must be bounded
relative to the smallest design margin, using the actual materials, openings,
contacts and required cases. No such actual-geometry bound or accepted margin
exists here. It cannot be inferred from the toy error, and the uncertain
motor-case history, contamination, bond coverage and properties remain separate.

No threshold, temperature limit, required case or evidence classification is
relaxed by this decision. A future engineering numerical-error budget must
have a documented physical-margin rationale and independent verification; it
cannot be chosen merely to turn this campaign green.

## Best justified alternative and stop boundary

Keep an **existing-solver route**, rather than starting another custom heat
solver. The source-supported classic `HeatSolve` implementation is the best
bounded alternative for discriminating the mixed-wall A discrepancy: one
otherwise identical A comparison against `HeatSolveVec`, with the same mesh,
material, boundary conditions, direct solver and output precision. It is an
unexecuted diagnostic proposal, not a qualified replacement. If later selected,
declare its case count and one-CPU/120 s per-case/600 CPU s packet limit first;
stop on invalid inputs, parser/solver failure or cap, and do not tune multiple
settings blindly. Preserve failed results. This campaign itself is closed.

Meanwhile, use the already verified closed-form solid-wall/radial results only
for the G80 component screens they actually cover. A conservative network or
enclosure is eligible only if its bounds retain real openings, end paths and
material contacts and are narrow enough to decide the required limits. A trivial
ambient-to-case bound is not useful acceptance evidence. Bounds straddling
45°C leave the design open. No new numerical heat-method implementation is
authorized by this decision.

Actual-baffle work still requires a qualified applicable method, exact compatible
CAD/material/opening/contact/radiation identity, feasible valid analysis mesh,
explicit time/spatial and local/global heat checks, observed memory/resource
preflight, and a separately declared attempt budget. The required 300°C case
source + contaminated foil + 35°C ambient remains required; source temperature
is not silently assigned to every component. Preserve the 45°C substrate screen,
all previous failed/stopped records and all physical/paid/WO-10/flight gates.

## Delivery consequence

Proceed with the dependency-ordered **G80 mechanical/recovery package** under
ADR-0011 while thermal acceptance is open. G54 and G12 keep their own evidence
and requirements. The saved frontend inspector/experiment/replay is delivered
under ADR-0009; missing compatible temperature overlays remain unavailable.

## Published compact evidence

[Campaign record](../runs/wo03-elmer-campaign-20261101T054800Z/record.json) is an explicitly labeled compact projection of the hashed raw record. It preserves all nine extrema/error/heat results and unavailable states; generated nodal arrays are omitted. The same packet retains the original stopped record, read-only A-2 recovery, original and completed harnesses, and corrected source-quadrature audit.
