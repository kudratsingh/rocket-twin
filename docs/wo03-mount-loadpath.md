# WO-03 motor-mount load-path proposal

This is an isolated geometry and hand-screen proposal. It changes resolved vehicle copies only. No active vehicle or CAD source is modified; no hardware adoption, physical-fit, strength qualification, or flight-readiness claim is made.

Run: `wo03-mount-loadpath-20261030T183924533321Z`; inputs unchanged: `True`; acceptance: **open / false**; active adoption: **false**; flight ready: **false**; cost: $0.

## Proposal

Fixed configurations extend the existing phenolic liner from the actual motor-mount front to 800 mm, retaining the two 3 mm centering-ring annuli. TVC configurations extend it from 4 mm ahead of the existing retention stop to 800 mm, into the 18 mm-long cradle annulus. The existing retention radius is 18 mm (36 mm OD); in the copy, its outer radius is set to the liner inner radius (14.7 mm, 29.4 mm OD in current resolved specs). A nominal 0.2 mm radial annular gap is treated as a bondline assumption, not a measured or detailed adhesive layer.

Before, the 36 mm OD (18 mm radius) forward stop at the fixed-mode station is spatially disconnected from the three-rail mount, while the liner starts at the motor front. In TVC modes, no verified stop-to-liner-to-cradle-to-gimbal-to-pin load path is established. Proposed paths are shown per mode below; mount-to-shell retention, pin/frame transfer and actual motor case capture remain open.

## Quantitative pilot

The axial tube screen uses `A = π(ro²−ri²)`, `I = π(ro⁴−ri⁴)/4`, `σ = F/A`, and pinned Euler `Pcr = π²EI/(KL)²`. Peak thrust comes from the linked executed WO-03 structural report, whose `peak_scaled_thrust_n` already applies its configured 1.15 multiplier. Strength/bond screens use design factor 3. Phenolic E=3 GPa and strength=20 MPa, epoxy shear=2 MPa are provisional engineering-input bounds. Euler uses full clear liner length with K=1 and a stated 0.1 imperfection reduction before DF as a deliberately conservative load-path sensitivity only: segments ahead of/behind the internal stop have different axial loads and support spans, and the fixed centering rings may share load. Thus a failed G54 full-length bound does not establish that the actual tube buckles. No calibrated imperfection or support restraint is available. Cylindrical bond area is `2πrL` under uniform average shear. Local bending, peel, crushing, thermal property degradation, tolerance, adhesive process and joint failure are not represented.

| Mode | Peak scaled thrust (N) | Proposed liner (mm) | Compression screen margin | Buckling screen margin | Stop bond margin | Liner/mount bond margin | TVC cradle/inner bond margin | Δmass (g) | ΔCG (mm) | Acceptance |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| G80 | 117.53 | 620.0–800.0 | 1.124 | 0.078 | 1.096 | 2.250 | n/a | 1.79 | 0.58 | open |
| G54 | 139.97 | 600.0–800.0 | 0.784 | -0.267 | 0.760 | 1.729 | n/a | -0.11 | -0.03 | open |
| G12-F | 35.95 | 636.0–800.0 | 5.944 | 3.244 | 5.851 | 30.877 | 11.653 | -0.23 | -0.06 | open |
| G12-L | 35.95 | 636.0–800.0 | 5.944 | 3.244 | 5.851 | 30.877 | 11.653 | -0.23 | -0.07 | open |

All computed margins are preliminary average-stress/buckling screens, not acceptance evidence. A screen-pass does not establish real load transfer. TVC final bond margin represents only cradle-to-inner-gimbal annular shear; pin and outer-frame capacity are unavailable.

## Per-mode load paths and limitations

### G80

Before: The axial retention disk has 18 mm radius (36 mm OD) at the fixed-mode forward station and is spatially separated from the 28.5 mm-radius three-rail mount; the liner starts at the motor front. No continuous load-transfer interface is established from the disk into the mount.

Proposal: Motor front stop -> 4 mm cylindrical bond at liner ID -> extended phenolic liner -> two fixed centering-ring annular bonds (3 mm each) -> motor-mount rails/rings -> aft-shell joints. The mount-to-shell joints remain unqualified.

Neutral BRep overlap pairs in proposed copy: 0; touching surfaces and bond layers are not resolved by this diagnostic. Full mass/CG/inertia change is in `build/wo03-mount-loadpath/G80.json`.

### G54

Before: The axial retention disk has 18 mm radius (36 mm OD) at the fixed-mode forward station and is spatially separated from the 28.5 mm-radius three-rail mount; the liner starts at the motor front. No continuous load-transfer interface is established from the disk into the mount.

Proposal: Motor front stop -> 4 mm cylindrical bond at liner ID -> extended phenolic liner -> two fixed centering-ring annular bonds (3 mm each) -> motor-mount rails/rings -> aft-shell joints. The mount-to-shell joints remain unqualified.

Neutral BRep overlap pairs in proposed copy: 0; touching surfaces and bond layers are not resolved by this diagnostic. Full mass/CG/inertia change is in `build/wo03-mount-loadpath/G54.json`.

### G12-F

Before: The retention stop is separated from the liner start, and no verified load-transfer path is established from stop into the motor cradle, inner gimbal, pivots and frame.

Proposal: Motor front stop -> 4 mm cylindrical bond at liner ID -> extended phenolic liner -> 18 mm cradle annular bond -> 6 mm motor-cradle/inner-gimbal bond -> pivot pins -> outer frame. Retention, all bonds, pin bearing/shear and frame closure remain unqualified.

Neutral BRep overlap pairs in proposed copy: 0; touching surfaces and bond layers are not resolved by this diagnostic. Full mass/CG/inertia change is in `build/wo03-mount-loadpath/G12-F.json`.

### G12-L

Before: The retention stop is separated from the liner start, and no verified load-transfer path is established from stop into the motor cradle, inner gimbal, pivots and frame.

Proposal: Motor front stop -> 4 mm cylindrical bond at liner ID -> extended phenolic liner -> 18 mm cradle annular bond -> 6 mm motor-cradle/inner-gimbal bond -> pivot pins -> outer frame. Retention, all bonds, pin bearing/shear and frame closure remain unqualified.

Neutral BRep overlap pairs in proposed copy: 0; touching surfaces and bond layers are not resolved by this diagnostic. Full mass/CG/inertia change is in `build/wo03-mount-loadpath/G12-L.json`.

## Open closure work

- The stop-ring capture geometry must match the exact purchased motor case and closure and sustain bidirectional axial load.
- Resolve annular bond preparation, adhesive, thickness, cure, thermal cycle, voiding and load sharing; test representative coupons and assembled proof articles.
- Verify local retainer and centering-ring bending, liner-end bearing/crush, shell attachment, gimbal pins/bearings, outer frame and combined TVC loads with targeted FEA and physical tests.
- The report checks neither continuous motion nor wiring access, hot fit, vibration, or stability/flight effects. All WO-03 acceptance remains open.

Source hashes and resolved/proposal identities are stored in the run record and per-configuration JSON. No original spec/CAD inputs are edited.
