# WO-03 G80 recovery axial cut screen

**Status:** preliminary structural demand screen from a read-only force-path
audit. It does not establish qualified capacity, a proof test or predicted
physical failure. The machine-readable record contains the prior load-path
intake, hashes, the 73-row full part/freebody ledger, and unrounded calculation
outputs: [recovery path record](../runs/wo03-g80-recovery-path-20261101-v1/record.json).

## Candidate and cut

This screen uses the Stage 3 corrected `6b0577…d1dc4` +5 g sensitivity for the staged72 source identity `90b2a9…bdfc`. The input spec is `runs/wo03-g80-canopy-stage3-20261101-v1/sensitivity.yaml`; Stage 3 equivalence says the 6b correction changed only allowance learn/build metadata and kept the input arrays unchanged. The resolved sensitivity parts sum to 0.7945817123 kg before the full 50 g growth allowance, matching the corrected flight record's 0.8445817123 kg loaded mass. At burnout, 62.5 g is removed from the motor part, leaving 0.7820817123 kg full-vehicle mass.

The diagnostic cut is at station **0.500 m** (nose-to-aft), in a plain body-tube interval. `body_upper` runs from 0.140 to 0.918 m and is modeled as a 66 mm OD / 65 mm ID cardboard tube. The recovery switch doubler ends at 0.485 m; `avionics_bay` and rail-guide envelopes end at 0.450 m; the coupler begins at 0.868 m. A modeled side hole is at local body station 330 mm (global 0.470 m), 30 mm forward of this cut. The saved parts inventory shows **one solid crossing the cut: the `body_upper` tube annulus**. No modeled continuous recovery backbone crosses it. Component parent fields do not establish that the components are attached or can transmit force.

The cut area is the requested gross annulus:

`A = π(33² − 32.5²) = 102.887159 mm²`.

This is a gross-section area calculation, not a local stress solution. The cut is upstream of the aft module joint, so under a serial path all material aft of the cut must be accelerated through this section. The calculation below excludes the whole `body_upper` part because it straddles the cut, even though some tube mass is physically aft of the plane. It also excludes three aft `distributed_budget` entries (`fin_bonds`, `incremental_mount_gap_epoxy_upper_budget`, and `retention_locking_materials_reserve`) because they have no itemized physical solid. This makes the included mass a lower bound, not a mass closure.

## Aft-side mass freebody

The complete 73-part ledger is in the JSON record. It includes each ID, parent reference, start station, geometry-derived extent, end station, material, mass, mass basis, CAD role, and cut classification. A part is included only when its saved start station is at/after 0.500 m and its CAD role is not `distributed_budget`; its entire configured mass is then counted. All straddling parts are excluded wholesale. The 50 g growth allowance is added separately at the configured 1.212 m station.

The included wholly aft part mass is **457.845578 g**. It includes the coupler and joint stop, aft shell and interface hardware, motor/retention/fin set, and staged G80 motor-mount/service parts. It includes the 128.2 g loaded motor envelope; the burnout freebody subtracts the source's 62.5 g propellant depletion. The two lower-bound masses are therefore:

| State | Wholly aft listed parts | Full-growth allowance | Aft freebody mass used |
|---|---:|---:|---:|
| Corrected 6b full-loaded | 457.846 g | 50 g | **507.846 g** |
| Corrected 6b burnout | 395.346 g after 62.5 g depletion | 50 g | **445.346 g** |

For an idealized serial load path, the axial freebody demand is `F_DF3 = 3 m_aft (v²/(2s) + 9.80665)`, using the existing DF3, velocities, and stopping distances. No new load criterion was introduced. The 20.4 m/s speed is still the archived off-nominal delay probe, not an approved deployment delay. Opening shock remains absent.

The calculation's un-factored freebody balance is `F_net = m_aft a_stop + m_aft g` in the configured axial screening direction; DF3 multiplies that resultant once. The JSON ledger records the inertia term, gravity term, un-factored resultant, DF3 resultant and area stress for every mass/velocity/travel combination. This balance assumes the serial tube interface transmits the full force; it does not infer a real joint from part-parent links.

| Mass state | Speed | Travel | Lower-bound DF3 cut force | Gross annular stress `F/A` |
|---|---:|---:|---:|---:|
| Full-loaded | 5 m/s | 0.3 m | 78.421 N | 0.762 MPa |
| Full-loaded | 5 m/s | 0.6 m | 46.681 N | 0.454 MPa |
| Full-loaded | 20.4 m/s | 0.3 m | 1071.666 N | 10.416 MPa |
| Full-loaded | 20.4 m/s | 0.6 m | 543.303 N | 5.281 MPa |
| Burnout | 5 m/s | 0.3 m | 68.770 N | 0.668 MPa |
| Burnout | 5 m/s | 0.6 m | 40.936 N | 0.398 MPa |
| Burnout | 20.4 m/s | 0.3 m | 939.777 N | 9.134 MPa |
| Burnout | 20.4 m/s | 0.6 m | 476.440 N | 4.631 MPa |

The active `configs/engineering/wo03.yaml` assigns cardboard/kraft `strength_pa: 2,000,000` (2 MPa), with an estimated-property basis, humidity/local-bearing/adhesive caveats, and a provisional 45 °C substrate screen. If the serial tube wall alone carries the cut demand, the 20.4 m/s cases exceed that estimated gross screen; the 5 m/s cases are below it. This comparison is **not** a supplier allowable, measured tube property, safety margin, bond capacity, or predicted failure. The configured 2 MPa estimate is not hot-qualified and does not cover local buckling, tear-out, ovalization, defects, moisture, joints, eccentricity, or dynamic snatch.

## Engineering implication

A local bulkhead or annular spreader at station 0.225 m can distribute anchor load into nearby wall, but it cannot bypass the 0.500 m tube cut. If the recovery load continues serially through the current body wall, the existing lower-bound axial screen already exceeds the configured 2 MPa estimate in the high-speed cases, before counting the aft portion of the tube itself. The next candidate correction should therefore examine a **continuous lightweight recovery tether/backbone from the forward bulkhead area to an aft structural attachment**, crossing the cut explicitly. This is a direction for analysis only: no material, geometry, bonding, attachment, capacity, or adoption is approved here. An off-CAD physical backbone could change the real force path; if so, the current cut stress estimate would not represent its load share.

The original local bulkhead-to-tube bond, canopy/cord/eye endpoints, module-joint axial transfer, and opening-shock basis remain unresolved. The aft motor bridge/keeper is not credited as a recovery attachment, and no G12 evidence is borrowed. No CAD, solver, test, browser, or physical work was performed.
