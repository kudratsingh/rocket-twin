# Extension points

The twin is a foundation. These are the interfaces where deeper models plug in later. The agent
must keep each one as a swappable function/class behind the name given here; never hard-wire the
v1 simplification where an interface is named. Each has a v1 implementation, the subject it
opens up, and the full treatment the owner may build later.

| Interface | v1 implementation | Opens up | Later |
|---|---|---|---|
| `sim.aero.AeroModel` | Barrowman CP + empirical Cd/CP vs Mach tables, grid-fin lookup | Aerodynamics | Panel-method or CFD-derived tables; Missile DATCOM-style buildup; unsteady effects |
| `sim.propulsion.EngineModel` | Ideal rocket equation, Isp vs ambient pressure, first-order transients | Propulsion | Engine cycle model (gas generator / staged combustion), chamber pressure dynamics, turbopump start, mixture-ratio control |
| `sim.propulsion.TankModel` | Fill fraction, fixed ullage pressure, CG from fill | Fluids, pressurisation | Pressurisation thermodynamics, slosh (pendulum/spring-mass), boil-off |
| `sim.structures.LoadsModel` | None (loads reported, not limited) | Structures | Bending moments from q·α, axial loads, margins; FEA via exported STEP |
| `sim.thermal.ThermalModel` | None | Aerothermal | Entry heating (Sutton-Graves), TPS sizing, cryogenic heat leak |
| `sim.environment.Atmosphere` | US Standard Atmosphere 1976 | Atmospheric science | NRLMSISE-00, winds-aloft profiles, day/season variation |
| `sim.environment.Gravity` | Inverse square (+J2 flag) | Orbital mechanics | Full geopotential, third-body, perturbation analysis |
| `sim.environment.Wind` | Steady + gust + power-law profile | Meteorology | Dryden/von Kármán turbulence, measured sounding profiles |
| `avionics.Estimator` | Complementary / Madgwick | Estimation | EKF/UKF with GNSS, radar altimeter, multi-sensor fusion |
| `control.Controller` | PID/LQR, PPO MLP | Control | MPC, gain scheduling, adaptive control, residual RL |
| `gnc.Guidance` | Scripted mission + G-FOLD landing | Guidance | Closed-loop ascent guidance (PEG), successive convexification, trajectory optimisation |
| `sim.staging.SeparationModel` | Instant mass drop + impulse | Multi-body dynamics | Contact/collision between bodies, pusher dynamics, fairing aerodynamics after jettison |
| `sim.faults.FaultModel` | Engine-out, sensor dropout, servo stall, brownout | Reliability engineering | Fault trees, Monte-Carlo mission dispersion, abort-trigger analysis |
| `vehicle.cad.PartGenerator` | Parametric CadQuery per part type | Mechanical design | Imported STEP from external CAD, mass properties from CAD, tolerance stacks |
| `export.*` | BOM, wiring, build pack | Systems engineering | Requirements traceability, interface control documents, test matrices |

Adding a vehicle class (a sounding rocket, a third stage, a different launcher) is a new spec
file and, where needed, a new engine/motor definition — not a code change — as long as the part
types exist.

## Modular physical configuration invariant

ADR-0006 uses the same extension interfaces for three physical configurations.
Resolve common and aft YAML into a complete immutable experiment input; each aero,
propulsion, structure, CAD and control model receives that same identity and hashes.
Shared hardware is reuse, not shared validation evidence. New materials or motor
bores require actual parts/mass/aero changes, not a hidden frontend or sim override.
