# WO-03 integrated corrections and closure

Updated 2026-10-30. The selected corrections are adopted in the **active shared and
mode specifications** under ADR-0008. This is a combined vehicle calculation, not
a collection of proposal-only passes. **Expanded WO-03 acceptance remains open;
WO-04 has not started.** No physical qualification or flight release is claimed.

## Adopted configuration

All modes share the 66 mm upper assembly, now with 400 mm extra tube length while
equipment stays forward, a 5 mm G11 recovery bulkhead, EasyMini controller and
separate 1S recovery battery/switch/carrier/harness. Mode-level wiring overrides
have been corrected: all six resolved modes/alternatives contain the dedicated
recovery positive, switched positive, return and output bundle. The former direct
main-battery recovery connection is preserved as a recorded integration defect.

Finned modes use three 70 x 120 x 6.35 mm unswept rectangular aircraft-plywood fins,
100 mm root tabs, two 12 mm-span x 3 mm-base gussets per fin and an additional 2 g
bond allowance. The nominal plywood density is 715 kg/m3. Fixed-motor afts use
12 x 7 mm plywood rails, additional support rings, a machined G11 thrust plate
with a 9 mm web and six integral 18 mm bond fingers, a bolted removable aft plate,
and separate 3 mm mica compression pads at both motor ends. Neither sleeve nor
foil provides tensile motor retention.

G12 TVC modes use G11 rings/frame and a machined cassette with an integral fore
stop, three rails and bolted rear capture. Pushrod relief interrupts one forward
rail; the other two carry forward-stop force. Three radial M2.5 screw envelopes
transfer cassette load to the inner ring. The sleeve is mica with a separate
20 micrometre foil shield; the thermal guard is spaced around the moving assembly.
The shortened aft tube and lobed cap provide nominal motion clearance. The finless
mode actually omits fin and fin-bond parts. The outer tube/case ends at 1,200 mm;
overall retained-hardware envelope is 1,212 mm. The G12 guide screen now requires
5 m usable travel, retaining its 10 m/s threshold. Actual launch equipment remains
unconfirmed. G80 remains reference, G54 conditional, G12 controls; no motor purchase
or exact flight hardware is selected. G25W remains quarantined.

## Mass, stability and flight

The [generated property report](wo03-integrated-vehicle.md) contains full tensors,
part budgets, launch/half-depletion/burnout states and all growth at either axial
extreme. Current record: `wo03-integrated-20261030T211523356909Z`.

| Mode | Loaded mass | With 50 g growth | Loaded CG from nose | Minimum growth/depletion margin |
|---|---:|---:|---:|---:|
| G80 performance | 739.462 g | 789.462 g | 792.814 mm | 1.314793 cal |
| G54 conditional | 817.991 g | 867.991 g | 814.216 mm | 1.045596 cal |
| G12 finned TVC | 780.147 g | 830.147 g | 800.988 mm | 1.218129 cal |
| G12 finless TVC | 645.944 g | 695.944 g | 730.917 mm | -10.626087 cal; positive passive gate inapplicable |

The G54 package-only prototype's 0.991 and first combined revision's 0.961 failed.
The current 1.045596 clears 1.0 without rounding or reducing the allowance. This
assumes the source motor's uniform midpoint CG. An **additional exploratory** aft
CG shift of 10% motor length gives 0.980899 cal with aft growth and fails; that is
an unsourced sensitivity, not a certification tolerance. Exact motor CG/source
correspondence or further design margin remains necessary before accepting G54.

Current full flight campaign `wo02-20261030T204849990760Z` has unchanged source/input
hashes, 27 cases, five nominal RocketPy comparisons and a 4,096-environment CPU
step. Nominal modeled apogees are G80 635.19 m, G54 755.53 m and locked finned G12
531.16 m. G54's nominal gain is about 18.9%. Maximum nominal reference errors are
2.064% altitude and 0.917% time, both from finned G12, within the 5% benchmark.
This does not inherit the historical WO-02 0.004% agreement or establish flight
accuracy. Guide/wind, recovery timing and source hypotheses remain in that record;
large post-burn angles remain outside validated aerodynamics. Finless is not flight
validated. The pre-CAD WO-02 acceptance record remains unchanged.

## Issue closure table

All margins below are calculated using estimated properties. A positive hand
screen is narrower evidence than complete installed acceptance.

| Issue | Previous finding | Adopted correction | Acceptance criterion | New result and evidence | Design status / later physical verification |
|---|---|---|---|---|---|
| G54 static margin | 0.991 package prototype; 0.961 first complete package failed | Shared extension, forward structural recovery bulkhead, complete revised fins/supports/power/mass | At least 1.0 cal with full growth and depletion | 1.045596 minimum; integrated property record above | Growth/depletion screen passes under midpoint motor CG. Exploratory +18.7 mm motor CG sensitivity gives 0.980899; G54 remains conditional. Measure as-built mass/CG and exact motor before release. |
| Fin panel | Thin panel excessive deflection and strength demand | 6.35 mm ply, rectangular planform, root gussets/tabs | Directional DF3 strength, 1 mm displacement, applicable convergence | Minimum 6.05 mm G80/G12 panels: cold displacement 0.3307 mm; half-stiffness/hot 0.6612 mm. Estimated directional strength screens pass. Five mesh levels retained. | Dominant Sxx/displacement/modes converge; small Syy/tau relative changes still fail the formal per-component gate. Strip fixture verifies method, not installed joint. Coupons/grain/thickness checks remain later. |
| Installed fin/root | Ideal clamp and bare-shell load path unqualified | Actual gusset/tab/frame parameters included in root demand screen; coincident flight loads separated from broadside sensitivity | Root/bond/frame strength, deflection and stiffness; credible load/operating domain | G80 coincident estimate 1.253 N/fin; G54 1.183 N/fin. Max-q x CN2 gives 308.2/272.8 N and fails bare-shell/single-rail bounds. | Peel allowable and installed rotational/torsional stiffness unavailable; distributed attachment/root model remains open. Full Cartesian sensitivity is not the coincident operating maximum. Root/joint proof and modal tests later. |
| Flutter/vibration | Tapered source premise mismatch, old geometry/mass | Actual rectangle, min thickness, orthotropic modes and fresh flight speed; body model ends at real tube with outboard mass levers | Applicable method, stiffness uncertainty, known cases and mesh checks | G80 panel NACA sensitivity 352.9–1218.7 m/s vs 218.0 m/s speed plus 20%; G54 vs 206.4 m/s. Body first modes roughly 16–26 Hz; numerical known/nullspace/mesh checks pass (`wo03-vibration-20261030T205443545391Z`). | NACA result remains an empirical panel screen; installed root, damping, body/fin/gimbal/control and large-angle coupling remain open. WO-06 must address identified risks; later modal/vibration measurements calibrate them. |
| Forward thrust transfer | Disconnected stop and insufficient plate/bond capacity | 9 mm G11 web, integral 18 mm bond fingers, 7 mm rails and actual net slot section | DF3 hot plate/bond/strength/Euler screens and complete connection model | G80/G54 hot plate margins +0.504/+0.263; finger-bond +0.899/+0.595; G54 hot Euler +0.173 (`wo03-motor-support-20261030T204829437762Z`) | Hand screens pass under estimated sharing; notch/local plate/finger/contact/buckling and peel details still open. Exact grade, hot coupons and assembled proof later. |
| Reverse capture and pivots | No complete reverse support or pin/fastener rating | Three-bolt G11 cap/blocks, aft mica compression pads, radial cassette screws, explicit pins | Case capture, bearing/thread/retention and combined motion margins | 150 N reverse-demand screens and corrected 1.3 mm axial pin ligaments recorded; nominal motion clear | Exact shoulder/nozzle/closure, thread/preload/washer details, pin strength and positive pin retention remain design dependencies. Supplier fit and proof tests later. |
| Standard heat/soak | Liner/polymer/bond overheating; axial bypass | Mica/foil, G11 hot structure and serial front/aft mica pad conduction | Configured material limits through burn/soak; energy, space/time checks | All four standard upper cases pass. Fixed mounts 39.54/39.81 C vs 45; TVC aft caps about 51 C vs 150 (`wo03-thermal-20261030T204848956297Z`) | Standard bounded screen passes. Exact case history/grade/emissivity/contact and local hot spots remain unmeasured. Instrumented burn/soak and hot-joint tests later. |
| Thermal sensitivity | High case bound and degraded foil unresolved | Explicit 300 C and contaminated foil cases retained | Same unchanged 45 C substrate screen | G54 shell 46.33 C at 300 C case; 47.10 C with contaminated foil | **Open modeled failure.** Do not raise the substrate limit to force closure. Resolve protection/input evidence; physical tests remain separate. |
| Coupler/key fits | Minimum clearance failed | Smaller coupler and wider differentiated key gaps | Minimum 0.1 mm; per-flank and total distinct | In-domain coupler min 0.2732 mm; key centered per-flank min 0.26447 mm (`wo03-tolerances-20261030T205656390867Z`) | Centered/in-domain screen passes; unilateral float, actual process and fitted retention unqualified. Measure assembly later. |
| Other manufacturing/thermal fits | Bore proxy and new complete hardware not checked | Use smallest rail/grip installation radius and carrier-plane corners, include outer foil | Minimum radial clearance 0.1 mm; bounded expansion | Fixed frame/shell min 0.02093 mm in domain fails. TVC rail/foil cold min 0.030 mm fails. Carrier-plane cold min 0.4206 mm passes; unavailable CTE is not a thermal pass. | **Open design failures/inputs.** Geometry/thermal fits require further correction and revalidation; purchased motor OD, pivots and rod ends remain explicit dependencies. |
| Gimbal motion | Frame/lug, horn and new cassette/retainer conflicts | Revised frame, fore relief/rail start, lobed aft plate and open aft region | Combined-axis commanded motion; tolerances, wiring, nozzle and access coverage | Both 25-pose sweeps pass at ±4.9847 degrees; no neutral rigid intersections; liner/shell continuous cylindrical bound 5.135 mm (`wo03-20261030T205235088123Z`) | Nominal sampled geometry passes. Full tolerance-expanded mechanism, wires, purchased nozzle/joints and continuous sweep remain open. Loaded mechanism/wire-flex tests later. |
| Recovery power | Mode overrides silently used main battery | Four dedicated recovery nets adopted in every resolved mode; regression added | Spec network separated from main power/control | All four integration modes and all six regression variants pass topology (`wo03-recovery-integration-20261030T204618137637Z`) | Functional net definition passes. Exact cell electrical profile, pulse/ESR, connectors, continuity and common-cause verification remain later design/electrical tests; graph separation alone is not qualification. |
| Recovery packing/service/anchor | Generic controller, unverified mounting/packing and load ratings | Credible component envelopes/carrier, separate power, 5 mm G11 bulkhead and explicit service report | Credible passage/access and rated load paths | Soft circumscribed diameter 58.728 mm vs shoulder 61.6 mm; 1.436 mm radial gap. Off-nominal factored anchor demand up to 1831.7 N; no capacity inferred. | Switch bushing/arming opening, positive board retention, wire routing and anchor/bulkhead load capacity remain **open design items**. Packing, extraction, deployment and unit proof remain later owner work. |
| Flight/reference and mass | Individual prototypes omitted combined mass | Reconciled CAD/CG/full inertia from one active spec; current static/flight campaigns | Static reference and 5% actual-mode flight benchmarks, preserved baseline | Current nominal/reference and CPU batch benchmarks pass; all exports match current spec; estimated parts plus 50 g remain below 1.5 kg | Model comparison passes, not hardware release. Motor sources/CG/lot/stock, site/guide, aerodynamics, sensors/control and measured performance remain bounded/unverified. |

## Acceptance boundary

Remaining **WO-03 design/model acceptance items** include failed minimum fits,
G54 thermal/CG sensitivities, root peel/stiffness/flutter and convergence evidence,
local support/retention details, actual recovery arming/mounting/routing and rated
anchor load transfer. These are not automatically deferred as physical tests.

Owner-performed **WO-09–11 qualification** separately covers material and joint
coupons, as-built mass/CG/inertia, dimensional/unit inspection, mechanism/pin/wiring
proof, temperature instrumentation, recovery packing/deployment and staged flights.
WO-06/07 retain realistic actuator/aerodynamic models, PID and committed RL; WO-10
retains owner firmware/abort/HIL review. Solid thrust cannot be stopped by centering
the gimbal, and finless burnout loses thrust authority; recovery/abort limitations
remain explicit. Purchases, physical work, paid runs and flight release remain gated.

Exact per-part engineering tables and recorded Analysis fields are regenerated
from the active specifications. Minimum-thickness solver results remain distinct
from nominal-CAD field exports; an incompatible field cannot be displayed as zero
or relabeled onto a different shape. Current STEP/GLB assemblies and visibility
previews are local under `build/` and are not committed generated bulk data.

## Installed fin and Analysis evidence

The current installed records are `wo03-fin-installed-20261030T205715365284Z`
(G80), `wo03-fin-installed-20261030T205816596002Z` (G54), and
`wo03-fin-installed-20261030T210211507451Z` (G12 finned). All report unchanged
inputs and use the current flight campaign. The G12 coincident panel-force estimate
is 0.3896 N; its separate max-q x CN2 sensitivity is 57.63 N and fails bare-shell/
single-rail bounds. Peel and installed root stiffness remain unavailable in each.

The minimum-thickness 6.05 mm fields failed nominal-CAD identity checks as intended.
A separate exact 6.35 mm nominal case now exports displacement and absolute spanwise
stress for all three finned modes: `wo03-fin-nominal-fields-20261030T210337367164Z`.
Each manifest carries its own resolved configuration/CAD identity. G54 reuses the
G80 solve only after matching actual fin shape, geometry, parameters, material,
density and load; G12 has its own solve. The nominal case has one 5 mm mesh and is
**calculated/unvalidated**, with no borrowed convergence flag. It covers the 2D
panel midsurface, not bond, root or connection stresses. Nominal maximum displacement
is about 0.28967 mm at 40 kPa / 5 degrees. Solver matrices, meshes and field arrays
remain local under `build/`; compact `runs/.../record.json` files retain global
quantities, failed flags, provenance and hashes of complete original reports.
