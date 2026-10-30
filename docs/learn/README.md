# Learn (owner's study index)

The agent links here; the owner writes here. Each `learn:` block in the vehicle spec and each
physics module's derivation summary points at one of these topics.

| Topic | Where it shows up | Starting reference |
|---|---|---|
| Static stability, CG vs CP, calibres | WO-01, vehicle summary panel | Barrowman, TIR-33 (Centuri 1966); Stine, *Handbook of Model Rocketry* |
| Thrust curves, total impulse, motor codes | WO-01, motor panel | NAR motor certification pages; thrustcurve.org |
| Rigid-body dynamics, quaternions, variable mass | WO-02, `src/sim/dynamics.py` | Zipfel, *Modeling and Simulation of Aerospace Vehicle Dynamics* |
| Drag, Mach effects, base drag | WO-02, `src/sim/aero.py` | Mandell, Caporaso & Bengen, *Topics in Advanced Model Rocketry* |
| Thrust vectoring moment arm and gimbal kinematics | WO-02, `src/sim/tvc.py` | any TVC note; BPS.space build logs for hobby scale |
| Servos: torque, speed, deadband, PWM | WO-03/06, servo part | servo datasheets; `src/sim/actuators.py` summary |
| IMU and barometer: noise, bias, drift, sampling | WO-06, `src/avionics/` | sensor datasheets; Madgwick 2010 filter report |
| PID tuning for attitude | WO-06, `src/control/pid.py` | Åström & Murray, *Feedback Systems* ch. 10–11 |
| PPO and domain randomisation | WO-07, `src/rl/` | Schulman et al. 2017; Peng et al. 2018 (DR) |
| Lossless convexification / G-FOLD | WO-08, `src/gnc/gfold.py` | Açıkmeşe & Ploen 2007; Blackmore, Açıkmeşe & Scharf 2010 |
| Liquid rocket engines: Isp, chamber pressure, expansion ratio, cycles | WO-05b, engine parts | Sutton & Biblarz, *Rocket Propulsion Elements* ch. 2–3, 6, 10 |
| Tanks, pressurisation, propellant mass fraction | WO-05b, tank parts | Sutton & Biblarz ch. 6; Huzel & Huang, *Design of Liquid-Propellant Rocket Engines* |
| Rocket equation, staging, Δv budgets | WO-05b, vehicle summary | Curtis, *Orbital Mechanics for Engineering Students* ch. 11; Sutton ch. 4 |
| Standard atmosphere, max-Q, gravity turn, orbital insertion | WO-05b, mission | US Standard Atmosphere 1976; Curtis ch. 11; Zipfel |
| Entry, grid fins, landing legs, boostback geometry | WO-05b, stage-1 return | NASA entry-vehicle reports; Fleeman, *Missile Design and System Engineering* (grid fins) |
| Reference frames: ECI, rotating Earth, launch-site velocity | WO-05b, ADR-0005 | Curtis ch. 1, 4; Vallado, *Fundamentals of Astrodynamics* |
| 3D printing for airframes: orientation, infill, PETG vs PLA | WO-03/09 | print-settings notes in the build pack |
| LiPo safety, voltage regulation, brownout | WO-09, power parts | battery and regulator datasheets |
| NAR Model Rocket Safety Code, FAA Part 101 Class 1 | WO-09 RSO document | nar.org safety codes; 14 CFR 101.22 |
| System identification from flight logs | WO-12 | Ljung, *System Identification*, intro chapters |
| Where the model stops and the full treatment begins | every `learn:` block | `docs/EXTENSIONS.md` |

Additional study links from the modular rebaseline:

| Topic | Where it shows up | Starting reference |
|---|---|---|
| Custom tubes, bonded/keyed joints, grain and print direction | WO-01 trade; WO-03/09 custom parts | [Construction trade](../wo01-rebaseline.md); material and adhesive supplier data |
| Fin bending, buckling, thermal isolation and recovery opening loads | WO-03/09 validation plans | Mandell et al.; measured coupons and supplier data |
| Guide departure versus mean TWR; useful control time | WO-01 screen; WO-02/06 validation | [ADR-0006](../adr/0006-modular-platform-rebaseline.md); Newton force balance |
| Honest PID/RL comparison, embedded constraints and negative transfer | WO-06/07/10/12 | [WO-07](../work-orders/WO-07-rl-ascent.md); Schulman et al.; Peng et al. |
