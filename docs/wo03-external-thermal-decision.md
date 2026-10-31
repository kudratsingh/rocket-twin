# External thermal tools — bounded comparison and decision

2026-10-31. **Neither evaluated tool qualifies for an actual-baffle calculation
yet.** Elmer is unavailable to execute in the checked environment. CalculiX
completed two three-grid fixtures, with useful individual checks, but did not
verify the difficult spatial-wall cases or sufficiently precise energy accounting.
No production heat method or working vehicle changed. WO-03 remains open.

The later [isolated-distribution preflight](wo03-elmer-isolated-setup.md) found a
MacPorts source port with arm64 build records, but no verified accessible binary,
runtime closure or relocatable installation for this host. It adds distribution
evidence, not a successful setup or solver test. No further packet was executed.

## Declared allowance and what was executed

Two packets were declared before execution: Elmer and installed CalculiX 2.23.
Each gets one CPU, at most120 seconds per case across all three grids, and600
CPU seconds per packet:1200 CPU seconds total. Setup is separate, with a600-second
wall limit per tool; no system installation, dependency upgrade or paid compute.

Elmer inventory/release/network setup preflight stopped after8 seconds: no trusted
accessible Mac arm64 solver was identified in the checked release assets, and
shell GitHub downloads failed DNS. No Elmer calculation, binary download or
source build occurred; its calculation allowance was unused. This is a checked
availability limitation, not a claim that Elmer cannot run on a Mac.

CalculiX used0.305709 child CPU seconds including failed input attempts, with
maximum recorded cumulative child peak memory16,269,312 bytes. No solve approached
its cap. Inclusive setup wall time was not measured; compliance with that setup
limit is therefore **unverified**, rather than inferred from short solver times.
Both input-format errors and the explicit final formatting-only replan are
preserved. There were no numerical-method retries or resource increases.
The packet is now stopped; no additional solve is implicit in unused allowance.

## Capability shortlist: documentation versus execution

| Tool | Documented relevance | Setup, dependencies, license | Actually established here |
| --- | --- | --- | --- |
| Elmer | Transient conduction; prescribed temperature/flux and spatial/time-dependent finite-transfer walls; diffuse-gray mutual radiation with visibility and partially open enclosures | Serial CLI; Mac source-build instructions use GCC/CMake, with optional GUI/MPI. No working local solver found. Upstream license policy distinguishes LGPL libraries and GPL modules/tools. No project dependency changed. | Literature and bounded availability check only; all numerical results unavailable. Its special double-boundary Heat Gap model is not automatically a conductive gas or adhesive-contact model. |
| CalculiX2.23 | Steady/transient conduction, film boundaries, cavity radiation and contact conductance | Existing arm64 CLI `/opt/homebrew/bin/ccx`; existing runtime dependencies; no install. GPL2-or-later. Exact spatial film inputs require an appropriate linked user routine. | Straight finite-wall and curved-cylinder stationary calculations completed. No transient, radiation, contact or continuously varying-wall verification. |

See the [Elmer assessment](wo03-elmer-literature.md) and
[CalculiX inputs/results](wo03-ccx-thermal-comparison.md) for official sources,
version/hash evidence and setup limitations. The Elmer manual inspected is dated
January20,2026, corresponding to26.1; release26.2.1 availability was checked
separately. No binary's features are inferred from a different manual version.

## Known-answer comparison

“Curved temperature” and “curved geometry” are different tests. B/B_strong are
harmonic quadratic temperature fields in a straight box. The existing cylinder
is a physically curved5mm-wide annulus; it is not a935:1 narrow annulus with
finite wall resistance. The latter combined behavior remains unavailable.

| Problem / unchanged criterion | Existing implementation, historical | Elmer | CalculiX executed result |
| --- | --- | --- | --- |
| A:0.2mm ×1mm ×187mm, k=.04, fixed573.15K hot wall, finite cold resistance h=36030.6, bulk308.15K; grids2/4/8 | Exact field and heat checks pass, including1e-7K and balances | Unavailable | All three complete. Largest printed field error4.816e-5K; output quantization prevents proving1e-7K. Hot heat9.856289W at each level, consistent with independent9.856289341W. Full verification unavailable. |
| B: same935:1 geometry, spatially varying Robin input h=30, known harmonic field | Nodal errors4.296→1.056→.262K; finest below true boundary minimum by.259K; not qualified | Unavailable | Unavailable: no matching linked `film.f`; centroid replacement was not substituted for the specified continuous input. |
| B_strong: same, h=36030.6 | Nodal errors4.617→1.156→.288K, finest undershoot.288K; two subsequent wall-treatment trials rejected and stopped | Unavailable | Unavailable for the same boundary-input reason. No claim to have resolved the original failure. |
| Existing cylinder: Ri5/Ro10/length12mm, k=.026,310/290K, insulated ends; exact logarithmic field/heat | Earlier fixture retained separately | Unavailable |262/786/3297 nodes. Field errors1.566→.760→.235K. Finest heat error.369%, last-two heat change.657%; individual existing.5K/3%/5% checks pass. Complete/local energy verification remains unavailable. |
| Narrow physically curved gap with finite/spatial walls; transient heating/cooling; contact; obstructed surface exchange | Not qualified by A/B or the simple cylinder | Unavailable | Unavailable; stationary exit success does not establish these behaviors. |

At printed precision the A fields stay within308.15–573.15K and the cylinder
within290–310K. A strict no-violation assertion below rounding resolution is
unavailable. The cylinder's hot/cold printed heats are ±.05818231,
±.05714763 and ±.05677237W; cancellation of rounded values cannot prove1e-10W
balance. No local element balance was established.

A read-only audit of all A cold-face nodes finds the same printed309.6129K.
Using the specified h and area gives9.856613806W outward, with ±.000336886W
rounding uncertainty, compared with hot9.856289W (±.0000005W). Their central
difference−.000324806W is compatible with rounding, but cannot establish the
required energy tolerance. This is output-resolution uncertainty, not evidence
of a real heat source or a verified energy balance. No solver field was clipped.

## Evidence-based decision and next prerequisite

**Do not select a production solver or launch an actual-baffle attempt from this
packet.** Retain CalculiX as an independent conduction cross-check. Elmer remains
a suitable documented candidate to qualify once a trusted isolated CLI is
available. The unresolved question is accurate local fields and heat with the
specified spatial finite-wall inputs, not merely whether a large program exits.

Before any more execution, declare a new bounded packet and establish either:

1. A versioned isolated Elmer CLI plus precise field/flux output, then the same
   difficult A/B/B_strong cases and physical curved-gap, transient, contact and
   blocked-radiation checks; or
2. A documented CalculiX path to matching spatial inputs and sufficiently precise
   field/reaction/flux output, without upgrading the working installation. This
   is an input/output capability prerequisite, not permission to invent a new
   heat discretization or rebuild indefinitely.

The literature does not make either route automatically physical. Li and Huang's
[maximum-principle analysis](https://arxiv.org/abs/1209.5657) gives conditional
mesh/time-step requirements for a particular finite-element setting; it is not a
guarantee for either tool or this Robin/radiation geometry. NASA's
[Building Thermal Models](https://ntrs.nasa.gov/citations/20170010293) separates
building, checking, executing and verifying. These support retaining independent
local-field, geometry/connectivity, heat and refinement checks. Neither justifies
the stopped wall tweaks or treating solver reputation as verification.

An independently discretized, boundary-fitted analysis grid remains the preferred
detailed contingency to assess **after** tool qualification. A simplified network
is permissible only with justified enclosures of end/junction, wall-input and
numerical errors. A radial-only annulus cannot represent the baffle's seams,
notches and end leaks. A trivial ambient-to-case bound cannot decide a45°C screen.

## Conditional resources and checks for one actual-baffle attempt

There is **no actual attempt selected or started**. After the prerequisites pass,
the proposal must identify candidate69df790ec9bcba1465be4fa9861a7ad5fbc467091cbf58f44dee069e56e00bac
and generator1193713d0f4a7ad8393a00a0a03e7aaa04e9aa9393d2034691ef7126ae3cdd3b,
or explicitly record a different isolated revision. Export material/face/contact
ownership from its CAD, partition glued/open areas, retain slots/notches/seams,
finite shield thickness, shield ends and all support paths. Radiation must use
the same visible surfaces and opaque barriers, with physical opening gas
temperature separate from external radiative brightness.

Preflight first: one CPU; ≤300s mesh, ≤900s complete factor/solve pilot; existing
150k-node/750k-tet/100k-free-node and1536MiB factor/128MiB map guards. Record
**observed total process memory as well as allocation estimates**: the old
3.156GiB observed factor demonstrates that estimated-map guards alone are not a
memory proof. Do not authorize another attempt on an unproved resource estimate.
These are ceilings, not predicted successful resources for an unavailable tool.
Set a separately justified total transient/matrix allowance before running it.

One diagnostic pilot would not close acceptance. Require valid geometry and
material ownership; admissible local fields; precise surface/element/global heat
and stored-energy accounting; three spatial levels and independent time-step
refinement; controlled wall and radiation quadrature; local peak versus part-mean
coverage; exact compatible exports. Any invalid mesh, unexplained field violation
or cap stops that attempt and returns to this decision, without automatic retry.
Apply the unchanged full thermal matrix through burn and post-burn soak, including
300°C/contaminated foil/35°C and the45°C provisional substrate screen. If credible
uncertainty bounds straddle45°C, temperature acceptance stays open.

## Decision-driving physical uncertainty and unchanged gates

Case/end temperatures and cooling history; foil emissivity/contamination and actual
openings; adhesive coverage, bond thickness/contact and hot material properties
remain decision-driving. Source ranges have already changed support/substrate
outcomes across45°C; no measured narrowing is credited. Supplier case-temperature
histories and later owner thermocouple/heat-soak, bond-section and hot-load tests
would resolve them. Numerical convergence cannot supply those measurements.

Recovery/support and installed-fin audits remain as in the
[complete-package closure table](wo03-package-closure-progress.md). No strength,
flutter, recovery mass or G12 departure item closes from this tool comparison.
The shared flight simulator, active vehicle and physical/paid/WO-10/flight gates
are unchanged. The owner's later instruction independently resumes preview
**code only** through a bounded frontend agent; computer use remains paused.
