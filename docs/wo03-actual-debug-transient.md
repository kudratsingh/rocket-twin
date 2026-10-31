# Actual replacement-baffle transient — failed numerical model

**The first actual-candidate burn/soak calculation completed, but its temperature
prediction is not credible.** The source gas operator fails field checks. The
values below are diagnostic outputs for investigating that model, not physical
predictions, a thermal pass, or grounds for adopting the baffle. WO-03 remains
open and the provisional 45°C paper/wood substrate screen is unchanged.

## Exact candidate and calculation

- Candidate: `69df790ec9bcba1465be4fa9861a7ad5fbc467091cbf58f44dee069e56e00bac`.
- CAD generator: `1193713d0f4a7ad8393a00a0a03e7aaa04e9aa9393d2034691ef7126ae3cdd3b`.
- Actual placed geometry: `wo03-baffle-fit-20261031T035358211715Z`, including
  rail/hardware notches, seams, eight three-panel baffles and their finite
  adhesive/mica supports. [Fit and assembly scope](wo03-baffle-fit.md).
- Transient: `wo03-actual-transient-20261031T061319026057Z`;
  [full record](../runs/wo03-actual-transient-20261031T061319026057Z/record.json),
  SHA256 `5112ab1e5571fbdc048b50a693041e98b3b45e7ec06d2f5663270d9c90c9f4a0`.
- Completed 0–303.026 s: source-curve burn of 3.026 s plus 300 s heat soak.
  Wall time 492.070 s; 1,062 integrator evaluations; maximum step 1 s;
  306 recorded times and 140 part-average histories. Inputs were unchanged.
- Required combined source case: exterior case-temperature hypothesis 300°C,
  contaminated foil emissivity 0.9, ambient 35°C. This run uses **nominal material
  properties only**, including gas conductivity 0.04 W/(m·K); it does not replace
  required material/contact/gap corners or the other configurations.
- The case boundary steps to the bound through burn and then decays with the
  existing 120 s time constant. All three motor surfaces share that declared
  hypothesis. Actual motor-case measurements are unavailable. Opening gas and
  radiative brightness are separately specified at ambient.
- Existing finite part capacities and lumped solid contacts are retained once;
  actual gas/radiation replaces the corresponding opaque-gap approximation.
  New baffle stacks have explicit serial connections. Other solids share part
  means; the liner has 16 radial cells and only one axial cell. Local solid hot
  spots and real contact spreading are not qualified.

The debug runner requires `--investigate-failed-operator`. Ordinary execution
rejects the failed source record; an incomplete operator is never usable. The
original 300 s gas-factor attempt remains incomplete. The separate observed
repeat completed in 892.496 s, returning a complete operator with failed field
checks. Its successful process exit and map algebra do not override those checks.
[Observed factor](wo03-actual-gas-observed.md).

## Computed debug values against the unchanged screen

**These are outputs of a failed numerical model. The arithmetic differences are
shown for transparency; neither side of 45°C establishes thermal acceptance.**

| Quantity | Debug peak | Time | Arithmetic 45°C minus peak | Acceptance |
| --- | ---: | ---: | ---: | --- |
| Wooden motor-support part mean | 50.672°C | 114 s | −5.672 K | Unavailable |
| Aft body-substrate part mean | 42.585°C | 128 s | +2.415 K | Unavailable |
| Foil-baffle means, range of eight peaks | 67.497–77.031°C | Worst at 34 s | Not a paper/wood part | Unavailable |
| Foil-side adhesive means, range of eight peaks | 66.914–76.076°C | Worst at 35 s | Separate provisional adhesive screen applies | Unavailable |
| Liner mean / maximum calculated radial cell | 269.225 / 270.091°C | Mean at 13 s | Separate liner screen applies | Unavailable |

The largest foil-side adhesive mean also exceeds the existing provisional 65°C
adhesive screen. The transient contains an unphysical minimum part mean of
34.586°C despite a 35°C initial/ambient boundary. No error bar supporting a
physical interpretation is established.

![Failed-model diagnostic temperature histories](../runs/wo03-actual-transient-20261031T061319026057Z/debug-temperature-history.png)

The earlier pre-baffle coaxial proxy gave 46.059/43.525°C support/shell with
ambient ends and 51.975/50.084°C with hot ends in its high-conductivity corner.
Those different geometry/property/boundary cases remain historical diagnostic
evidence. Subtracting their temperatures from this nominal-property failed-model
run cannot establish cooling attributable to the baffle. The old 44.749°C band
pass remains superseded for acceptance. [Model history](wo03-thermal-model-corrections.md).

## Four separate gates

| Gate | Executed result | Remaining restriction |
| --- | --- | --- |
| Mesh validity | Coarse mesh passes its recorded positive-cell/closed-boundary guards; all 783,535 internal adjacent faces have opposite-side vertices | This does not prove adequate resolution, global embedding, or temperature accuracy. Middle replay contains five exact flattened cells. The one optimized trial still fails topology. |
| Calculation completion | Complete coarse response operator and completed burn/soak histories | The earlier coarse and fine time caps remain incomplete attempts, not physical failures. |
| Numerical accuracy | Two analytic/central-difference Jacobian comparisons pass; global ODE energy residual is small | Actual field bounds fail; spatial, time-step, wall quadrature and local optical convergence are unestablished. Local heat-route integration is not verified. |
| Temperature acceptance | Unavailable | Failed source numerics and incomplete required matrix block acceptance, regardless of individual debug peaks. |

The hot-case gas probe spans **181.615–602.731 K** when the available fixed/bulk
temperatures span 308.15–573.15 K. There are 13,562 nodes and 194 surface-group
means below ambient. No clipping, coefficient repair or weaker limit was used.
The local equations reproduce both extreme temperatures with very small row
residuals; this is more than a solver-completion problem. The cylindrical trace
contains 187 mm axial facets across a 0.2 mm gap. A local refinement pilot targets
those traces and mixed-boundary motor-end corners while preserving the original
piecewise-planar material boundary, openings and optical-parent identities.
[Field diagnosis](wo03-gas-field-diagnostic.md). The bounded refinement pilot
preserved the original planar boundary union but stopped before achieving its
resolution targets: 101,741 boundary nodes / 204,338 triangles, with the next
conforming batch exceeding the declared 120,000 / 240,000 caps. It produced no
volume mesh or new temperature solution. This is incomplete refinement, not a
failed physical baffle. [Pilot](wo03-refined-gas-boundary.md).

## Energy accounting and numerical checks

The integrated global ODE energy residual is **0.001700 J** against net external
energy 2,790.395 J (relative 6.09×10⁻⁷). That checks the recorded integration of
the approximate network; it cannot validate spatial temperatures.

**The separate connection-by-connection energy audit is not verified:** its
largest local storage/heat mismatch is **470.811 J**. Actual postprocessing
sampling is 1 s, including burnout; the raw output's generic “≤0.5 s” description
does not describe this run. Fast initial heat transfer is under-resolved by this
audit. Dominant integrated heat routes cannot be accepted from these totals.
A finer/adaptive connection-flux integration and time-step refinement remain
required. The original output is retained unchanged, including that metadata
limitation and inherited legacy approximation descriptions; the actual exchange
hook and source snapshot identify this run's implemented geometry.

A separate read-only gas-ledger audit demonstrates cancellation in the original
bulk heat subtraction: equivalent local temperature-difference accounting reduces
the captured field ledger residual below the unchanged 1 µW threshold. That audit
does **not** repair the unphysical fields or retroactively pass the source record.
[Energy diagnosis](wo03-gas-energy-diagnostic.md).

## Export, next verification and unchanged gates

`analysis-debug/manifest.json` and `debug-part-temperatures.json` export only the
recorded part means, in kelvin, with exact candidate/CAD identity and
`validation: failed`. Compatible consumer loading passes. Missing coverage remains
unavailable; there is no invented local temperature field, design-margin pass or
registration on an active configuration. The geometry-only candidate preview is
separate. [Export record](../runs/wo03-actual-transient-20261031T061319026057Z/debug-export-record.json).

Next: obtain a valid, sufficiently resolved geometry-preserving gas mesh;
recompute its wall quadrature; repeat complete source-field checks; establish
relevant spatial and time refinements and both global/local heat balances; then
execute the required configuration/property/contact matrix. None of those steps
may infer convergence from the unrelated known-case fixtures alone.

No new physical design, mass saving, G12 departure credit, build approval or
flight approval follows. Installed fin/root/flutter, structural recovery/support
paths and all other expanded WO-03 items remain open. After numerical and design
acceptance, motor-case, substrate, bond and post-burn measurements plus owner
proof tests remain in WO-09–11. Physical-work, paid-run and WO-10 owner-review
gates are unchanged.
