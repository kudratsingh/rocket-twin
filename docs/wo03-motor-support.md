# WO-03 motor-support load path

**Status:** preliminary analytical screen; acceptance open; flight readiness false. Run `wo03-motor-support-20261030T203638821720Z`; source hashes unchanged: **true**. Results below are calculated from the reconciled active specs and cached geometry inputs, not measured hardware data. The run hashes all CAD generator modules, vehicle geometry loaders, analysis code, configs and resolved source inputs. No physical test, supplier fit confirmation, or detailed joint analysis is represented.

## Load path

Forward thrust is traced as case shoulder → three mica compression sectors → fixed G11 thrust plate or integral TVC cassette stop → support rails → fixed shell attachment or three radial cassette screws → inner gimbal and pivot pins → frame. The mica is compression-only and carries no retention tension. Reverse loading is screened as case aft closure → removable retainer/cap → three fasteners and attachment blocks → frame or cassette.

The exact purchased motor case front shoulder, closure and the required 24 mm nozzle opening remain unresolved supplier dependencies. The present design screens cannot establish capture, clearance, contact location, or a complete load path at those interfaces.

## Material/property screens

The engineering inputs are estimates for sensitivity analysis, not design allowables. A design factor of 3 is applied to the tabulated strength screens. “Hot” means the requested half-strength sensitivity, not a measured temperature-dependent curve.

| Component/property | Cold screen | Hot sensitivity | Basis and limitation |
|---|---:|---:|---|
| G11 modulus | 10 GPa | 5 GPa for Euler sensitivity | Low-end estimated modulus; laminate direction and purchased grade unverified. |
| G11 strength | 50 MPa | 25 MPa | Cautious study estimates, not allowables; bearing, thread, hole and edge strengths may be lower. |
| Plywood modulus | 2 GPa | 1 GPa for Euler sensitivity | Estimated weak direction; grade, veneers, moisture, grain orientation and bond quality unknown. |
| Plywood strength | 10 MPa | 5 MPa | Estimated screen, not an allowable or coupon result. |
| Adhesive joint shear | 2 MPa | 1 MPa | Estimated wood/paper bond screen. The cited glass-to-glass adhesive bulletin is not evidence for plywood or paper substrates. Bond geometry, peel, cure, voids and temperature history remain unknown. |
| Mica sector compression | 20 MPa | no measured hot reduction available | Provisional compression-only screen. Product grade, edge damage, thickness tolerance and case contact pressure are unverified. |

The source configuration and solver-derived scaled thrust are stored in the run record once generated. Structural demands use the configured thrust multiplier and design factor from `configs/engineering/wo03.yaml`; the multiplier is not applied a second time in this report.

## Calculated screens

Margins are (capacity/(3\times demand)-1) against the stated estimated strength screen. The Euler screen uses ideal pinned rails and the hot column sensitivity halves E. All figures below are calculations; no loads, dimensions, or stresses are measured.

| Configuration | Scaled thrust (N) | Forward rails / net area per rail (mm²) | Rail stress (MPa) | Rail hot strength margin | Longest span (mm) | Euler margin, hot E/2 | Pad pressure (MPa) | Pad margin, provisional | Stop strip bending (MPa) | G11 plate margin cold / hot | Last-ring bond hot margin |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| G80 performance | 117.53 | 3 / 46.04 after fin-channel cut | 0.851 | 0.959 | 90 | 1.088 | 2.473 | 1.696 | 5.542 | 2.007 / 0.504 | 0.727 |
| G54 performance | 139.97 | 3 / 46.04 after fin-channel cut | 1.013 | 0.645 | 110 | 0.173 | 2.945 | 1.264 | 6.601 | 1.525 / 0.263 | 0.450 |
| G12 finned TVC | 35.95 | 2 / 24.00 | 0.749 | 10.126 | 81 | 3.463 | 1.004 | 5.641 | 1.316 | 11.666 / 5.333* | n/a |
| G12 finless TVC | 35.95 | 2 / 24.00 | 0.749 | 10.126 | 81 | 3.463 | 1.004 | 5.641 | 1.316 | 11.666 / 5.333* | n/a |

The fixed mount rails are 7 × 12 mm. The configured 6.4 × 7.3 mm radial/tangential fin-channel cut leaves a 46.04 mm² estimated net section and 201.36 mm⁴ minimum centroidal inertia per rail. Notch-root concentration and local buckling are not represented. The TVC screen uses only the two configured forward load-bearing rails because the third rail starts aft for pushrod clearance. Its fore stop is a 5 mm partial ring (outer/inner radii 18/8 mm) with an 80° relief. All three TVC pad sectors are within the relief's kept radius: pad outer radius is 13.8 mm and keep radius is 13.9 mm, so the pressure estimate includes all three 40° sectors. **The positive TVC strip margins marked * are not a full-ring pass:** the strip model does not solve load redistribution around the rod-relief edge or a discontinuous ring.

Fixed plate geometry has a 9 mm forward web and six integral 18 mm slot-flank bond fingers (the CAD envelope length is 18 mm; it is not the bending thickness). The fixed plate strip screens are positive against estimated G11 strength, with hot half-strength margins 0.504 (G80) and 0.263 (G54). This simple strip estimate omits circumferential action, finger-root interaction and local stress concentrations; it is not a detailed plate proof. The fixed mount's last-ring bond proxy hot margins are 0.727 and 0.450. Six slot-flank bond faces use a conservative 6.2 mm radial contact width × 18 mm length, giving 669.6 mm² assumed area. Estimated hot uniform-shear margins are 0.899 (G80) and 0.595 (G54); full-OD bond proxy margins are 4.132 and 3.309. Actual 0.2 mm flank gaps, bond preparation/cure, peel, finger load sharing and shell contact are unresolved, so these calculated margins do not validate either bond.

The aft retention screens assume a 150 N reverse load shared across three M3 fasteners (50 N each). CAD screw envelopes are 20 mm fixed and 16 mm TVC; the estimated screw/nut/washer/locking hardware mass is 7 g per assembly. Nominal M3 tensile demand is 9.94 MPa and screw grade remains unselected. Fixed captive-nut blocks have a 0.347 MPa average cross-section demand and estimated hot DF3 margin 3.80; nut pullout/pocket breakout remain unmodeled. TVC tapped G11 blocks have a simple thread-cylinder shear estimate of 0.531 MPa and hot DF3 margin 14.71, assuming 10 mm engagement. This is not a thread-strip allowable. TVC block cross-section stress is 1.042 MPa with estimated hot DF3 margin 7.00. Forward mica pads are compression-only and do not enter this reverse retention load path.

For each TVC pivot pair, the calculation assigns half of axial thrust to each of two 3 mm pins. Single-shear demand is 2.543 MPa; double-shear demand is half that. Pin bending demands are 4.408 MPa outer and 3.391 MPa inner at nominal clearances 1.3 and 1.0 mm. Radial-wall G11 bearing demands are 1.498 MPa outer and 1.619 MPa inner. The CAD bore is radial through each concentric ring wall, centered axially at z=3 mm in 6 mm-thick rings. Axial edge ligament is therefore (6−3.4)/2 = 1.3 mm for both pairs; two-plane shear-out demands are 1.728 MPa outer and 1.869 MPa inner. These are geometric load demands, not pin/lug capacities. Pin material, positive axial retention, actual fit, hot bearing behavior and proof load remain unverified.

Fixed plate slot footprint averages are 0.427 MPa (G80) and 0.509 MPa (G54), based on three 12.4 × 7.4 mm slot rectangles. These are footprint averages, not verified bearing contact pressures. For TVC, each of three radial screws sees 11.98 N axial load; gross-shank single-shear demand is 2.093 MPa and projected G11 bearing demand is 0.555 MPa. Screw material strength and exact shear planes are not rated.

## Calculation bounds

- Rail axial stress assumes equal sharing over the configured forward load-bearing rails. The fixed mount uses three rails; CAD fin-channel cuts are subtracted from each rail's rectangular section to estimate a net area and centroidal second moments. The idealized subtraction does not capture cut-root concentration or local web buckling. TVC forward rail count is read from the cassette parameter because pushrod clearance leaves one rail starting aft of the fore stop. Euler buckling uses the weaker net rectangular-section axis and largest span between configured support locations. For the fixed mount these are configured rings and endpoints; for the TVC cassette they are the integral fore stop, grip collar and aft blocks. This ideal-column result omits initial curvature, rail twist, load eccentricity, and imperfect end restraint. Real contact stiffness and load transfer need detailed analysis.
- The fixed thrust plate screen uses the configured 9 mm web thickness, not the 18 mm envelope length. It treats each mica sector as an independent radial cantilever strip from the pad edge to the plate outer radius, omitting circumferential ring action. Rail-slot footprint pressure uses the slot rectangle only; the CAD does not establish actual contact pressure or adhesive load distribution.
- Pad pressure uses radial and angular overlap between the configured annular sectors and rod-relief cut. With current TVC pad outer radius 13.8 mm and relief keep radius 13.9 mm, all three pads remain within supported material. This area calculation does not establish uniform contact, eliminate edge stress, or validate the relief-adjacent web.
- Fixed bond estimates use six specified slot-flank fingers and a full circumferential plate OD bond, plus a separate last-ring bond proxy. Actual bond thickness, substrate preparation, cure, peel, voiding, thermal properties and load split are not resolved. Cold/hot bond strengths are screening assumptions, not allowables.
- TVC radial-screw transfer reports equal per-screw demand, gross-shank single-shear stress, and a G11 projected-bearing screen using configured radial hole depth as an upper-bound engagement proxy. It does not rate screw strength, real thread engagement, countersink pull-through, gimbal ligament, preload, fatigue or combined TVC motion loads.
- Reverse retention shares the specified 150 N total load equally across configured blocks and fasteners. Nominal M3 tensile area is a bolt-demand indicator. Fixed-mode nut pockets are treated as a captive-nut hypothesis; TVC G11 thread-cylinder area is an explicit approximation, not a validated stripping model. Nut pullout, washer bearing, block splitting, edge distance and eccentricity remain open.

## Acceptance dependencies

The analysis remains preliminary until the following are resolved:

- Supplier drawings confirm case shoulder, closure and nozzle dimensions, including the 24 mm opening and the exact contact/capture geometry.
- The final reconciled CAD defines actual slot lands, bond surfaces, support contacts, fastener engagement, gimbal ligaments and pin spans. Bondline and clearances need explicit geometry or a justified contact model.
- Material grade, orientation and temperature-dependent properties are documented. Representative hot adherend-specific coupons and assembled proof tests establish joint performance.
- Fastener grade, thread form, nut/washer geometry, engagement and installation torque are selected and sourced.
- Detailed local stress analysis and physical axial proof testing validate both forward thrust and reverse retention load paths, including thermal and motion conditions.

No calculation in this study qualifies a component, closes WO-03 acceptance, or authorizes physical fabrication or flight.
