# WO-03 current checkpoint — 2026-10-30

WO-03 remains active under ADR-0007. The engineering/structural, thermal,
tolerance-motion, service/packaging, vibration/flutter and analysis-export gates are
not complete. `expanded_wo03_benchmark_passed: false` and `flight_ready: false` in
the latest CAD record. No transition to WO-04 or physical release is claimed.
The earlier pre-resume snapshot is retained in [wo03-checkpoint.md](wo03-checkpoint.md).

## Publication state

- Scope/planning PR #4 and analysis-record transport PR #5 are merged; latest merged
  commit is `959432802888611ff2989a3638dd250195458b08`.
- The next CAD/analysis PR is pending. No PR number, push or merge is claimed here.
- No purchase, fabrication, flight, paid compute or physical qualification occurred.

## Latest evidence

| Evidence | Result | Scope boundary |
|---|---|---|
| Fresh full WO-02 run [`wo02-20261030T173859843386Z`](../runs/wo02-20261030T173859843386Z/record.json) | 27-case source-hypothesis campaign; unchanged code/input hashes; RocketPy actual-mode comparisons; 4,096-env CPU step; CPU tiny under 120 s. `wo02_benchmark_passed: true`, cost $0. | Preserves the separate historical pre-CAD baseline `wo02-20261030T044930127544Z`. Both remain model evidence only; every case has `flight_ready: false`. Wind, attitude, recovery opening loads, real hardware identity and finless burnout transition remain unvalidated. |
| Engineering / analysis exports [`wo03-engineering-20261030T175947969565Z`](../runs/wo03-engineering-20261030T175947969565Z/record.json) | `inputs_unchanged: true`; quantity exports and consumer checks pass for all four configurations. Stress, margin, part displacement and thermal histories are exported at their stated resolution; unsupported gimbal displacements are explicitly unavailable. `engineering_benchmark_passed: false`. | Calculations use estimated properties, loads, hot limits and external case boundary. Lumped thermal network has approximate gap conduction/contact/radiation, no internal propellant/combustion model or spatial thermal gradients. The exploratory 120/250 °C boundary through source burnout then exponential cooling is not an exact-motor measured history. |
| FEA/vibration/flutter [`wo03-vibration-20261030T175839356500Z`](../runs/wo03-vibration-20261030T175839356500Z/record.json) | `inputs_unchanged: true`; known analytical cases pass. G80, finned-TVC and G54 spatial field exports and consumer checks pass; finless has no applicable fin field. `vibration_flutter_acceptance_passed: false`. | Convergence validates idealized numerical models, not estimated material, ideal clamps/roots, actual fin strength or flutter clearance. No physical vibration/flight qualification. |
| CAD exports + nominal motion [`wo03-20261030T180113490389Z`](../runs/wo03-20261030T180113490389Z/record.json) | `cad_export_benchmark_passed: true`, unchanged input hashes, 67.41 s, $0. Six nominal interfaces and both inclusive 5×5 / 25-pose TVC sweeps pass at ±4.9847°. The continuous cylindrical liner-to-shell radial bound is 5.135 mm. All six generated configurations pass mass-reconciliation/print-volume checks and report zero rigid intersections. | Radial bound is not a full mechanism, tolerance, wiring, retention or service proof. Reconciliation uses CAD/spec and unmeasured estimates. `expanded_wo03_benchmark_passed: false`; measured mass, fabricated fit, strength and hardware gates remain open. The earlier 34.71 s export remains archived without the formal motion proof. |

## Open numerical and integration conclusions

- **Nominal motion:** The latest CAD record now contains passing 25-pose sweeps for
  both TVC modes through ±4.9847°, six passing nominal interface checks and a 5.135 mm
  continuous cylindrical liner-to-shell radial bound. This is not a full-mechanism
  or tolerance-expanded continuous swept-volume proof. Wiring slack/bend,
  nozzle and retention envelopes, purchased joint details, fastener/bond access,
  service withdrawal and combined thermal expansion are still open.
- **Structural:** Executed fin-shell FEA converges for the idealized case, but the
  independent load screen remains adverse: fin-set margins are **−0.749** for
  performance/G54 and **−0.845** for finned TVC under estimated weak-direction
  properties and prescribed loads. TVC gimbal neck-only screen margin is only
  **+0.024** and excludes eccentricity, holes, transverse rod force and print
  anisotropy. A passing thrust-mount screen does not close the joint/load path.
  Detailed local buckling, bond/fastener bearing, recovery opening, material range,
  physical coupons and proof tests remain required.
  The G80 fin spatial calculation in [`wo03-vibration-20261030T175839356500Z`](../runs/wo03-vibration-20261030T175839356500Z/record.json) uses an identified 2,028-node/969-element mesh;
  it reports calculated maximum displacement **12.053 mm**, maximum absolute
  normal stress **|Sxx| = 12.926 MPa**, and regional shell von Mises **10.890 MPa**.
  These are separate calculated quantities, not measurements or allowables. Raw
  deck, mesh and part-shape identity guards passed. Hand-screen fin tip displacement
  and spatial FE displacement are not interchangeable.
- **Thermal:** The upper-hot-soak scenario gives the finned TVC motor liner peak
  **230.9 °C against a provisional 120 °C screen**, mount **130.2/45 °C**, gimbal
  **81.9/60 °C**, and fin bonds **59.1/45 °C**. Performance/G54 cases also exceed
  liner and mount screens; for example G54 liner is **227.4/120 °C**. Even the
  nominal lower finned-TVC scenario exceeds the mount screen (**54.3/45 °C**).
  These model failures need design/input resolution; no exact motor temperature
  history or physical hot-soak has been measured.
- **Vibration/flutter:** Numerical modes are exploratory 1D/body-beam and clamped
  shell reductions with estimated stiffness and joints. The flutter screen spans
  42–225 m/s in the performance estimate and does not meet its provisional speed
  ratio criterion; taper/thickness and installed root stiffness validity failures
  are recorded. TVC/gimbal/sensor/servo excitation, damping, filters and sample
  timing have not been measured. No modal or flutter clearance is established.
- **G54 growth/stability:** G54 aft-growth static margin remains below **1 cal**
  (the retained prior report gives 1.023 cal before the latest reconciled geometry).
  Exact current CAD mass/CG and all-growth-aft condition must be reconciled before
  this tight clearance can be accepted. G54 remains a conditional hypothesis.
- **Recovery/service/power:** No chute packing/attachment qualification, opening
  load proof, connector/strain-relief fit, complete wire route, isolated recovery
  power or safe arming hardware procedure is established. Preliminary assembly and
  service diagrams do not assert actual fit.
- **Analysis export:** Identity-bound artifacts and consumer checks exist, but the
  current run remains unaccepted because critical FEA/load, thermal, motion/access,
  recovery and interface conclusions are open. Estimated/model outputs cannot
  become measured evidence or a green pass in WO-04.

## Environment and next work

Python 3.11.16, uv 0.12.17, JAX/jaxlib 0.4.38, RocketPy 1.13.0, SciPy 1.17.1,
CadQuery 2.8.0, Gmsh 4.15.2 and CalculiX 2.23 were verified locally; exact pins
and caveats are in [ENVIRONMENT.md](ENVIRONMENT.md). Keep original WO-02 baseline
records immutable. The next implementation work is to correct adverse/open design
conclusions, finish tolerance and combined-motion/access checks, validate exact
suppliers/materials, complete structural/thermal/recovery/power packaging evidence,
then reconcile and rerun affected reference and flight benchmarks. Advance only
when expanded WO-03 acceptance is actually passed and recorded in STATUS.
