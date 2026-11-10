# RP1 system map source audit — November 9, 2026

## Scope and gate

`Rp1SystemMap` is a read-only Engineering graphic for configuration `G80-F2-RP1-AD1-definition-v2` and specification SHA-256 `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`. The exported component accepts `{ configurationId, specificationSha256 }` and shows an unavailable state for any mismatch. Primary integration supplies those props from the actual selected source. This packet adds no simulator, controller, route, vehicle or acceptance change.

The current G80 tab separates shared simulation code from incomplete RP1 flight input and source-only instrumentation/recovery. The future G12 tab presents a proposed feedback loop; arrows are interface directions, not installed wiring. SVG blocks are mouse- and keyboard-selectable, with status, units/frame, limitation and repository source path in a detail panel. Links point at the fixed merged source checkpoint `07552bd1425dce4cf0b47af56c70b44a9500625e`; later source changes require a new audit.

The input block has three distinct dependencies: scenario input to environment, motor curve to thrust/force formation, and mass/CG/inertia to the 6DOF plant. The latter two branches route above the graph so they cannot be read as passing through environment. Their unavailable styling refers to incomplete RP1 flight inputs; it does not erase the implemented shared simulator interfaces.

## Block evidence

| Map area | Recorded source | What the map may state | Limit |
|---|---|---|---|
| Complete vehicle input | `src/sim/inputs.py`; `configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml` | Simulator requires vehicle, motor curve, mass, CG and inertia | RP1 lacks complete flight/inertia input; no current RP1 flight run inferred |
| Environment, forces, 6DOF | `src/sim/environment.py`, `aero.py`, `tvc.py`, `dynamics.py`, `protocol.py` | ISA/wind, quasi-steady aero, thrust mapping and RK4 NED/body dynamics implemented as models | Current protocol says `none; gimbal locked`; model domains, physical evidence and installed fit remain open |
| Instrumentation and telemetry | `src/sim/sensors.py`, `telemetry.py`; RP1 source YAML | Sampled IMU/baro/high-g models, SI/NED/body export, source flight-computer and logging roles | Calibration, pin assignment, write reliability and RP1 physical telemetry unavailable |
| Independent recovery | RP1 source YAML; `src/sim/dynamics.py` | Separate source controller/battery and simplified apogee/recovery simulation | Installed deployment, power isolation, canopy/harness behavior unqualified |
| Future control | `docs/work-orders/WO-06-avionics-pid-baseline.md`, `WO-07-rl-ascent.md`; `configs/control/pid.yaml` | Planned estimator, guidance, PID then distinct RL, limits and abort | PID gains are null; no tuned controller, policy or validated abort |
| Actuator model | `src/sim/actuators.py`, `tvc.py` | Preliminary servo dynamics and two-axis thrust mapping | Current G80 has no active gimbal; no qualified linkage, torque/current or moving inertia |
| Firmware and HIL | `firmware/README.md`; `docs/work-orders/WO-10-firmware-hil.md` | Future verification scope | No firmware or physical installation claim |

The owner reference [REF25](../../frontend-design-workbench-v2/reference-set-20261109.md) supplies a visual organization goal. Its 3DOF/fixed-mass abstraction, numerical gains and example target are not adopted. Existing engineering/physical/flight gates and five UNSENT inquiries remain unchanged.

## Verification and native limit

Focused source/render tests check exact-source refusal, all edge endpoints, current G80 missingness, future G12 planned statuses, and selectable SVG output. Typecheck, lint, format and build are source checks. Native Engineering integration, keyboard focus/selection, responsive legibility and source-link navigation require a separate designated-window check after primary mounts the component. This document does not mark FW2-020/A15 accepted.

## P72 legibility correction

The designated P72 capture found that long flow labels crowd the 22 px gaps between blocks, while the selected detail card sits below the large SVG. Selection and source attributes were observed; their readability remained partial. The display correction substitutes compact E1… markers at the existing edge positions and prints every existing `from → to`, signal label and status in a flow key below the bounded graph. The selected block's existing detail, signal/frame and source links move to an adjacent 340 px desktop panel. The SVG is bounded to 1200 px width and 400 px height, with a stacked fallback in narrower layouts. No node, edge, status, physical source or keyboard selection contract changed. P72 remains historical partial; a fresh designated-window check is required for the corrected view.
