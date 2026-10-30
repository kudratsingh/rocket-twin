# WO-05b — Orbital vehicle pack: `orbital-launcher-v1`

Branch: `wo-05b-orbital`. Tier: Mac CPU. Likely to need splitting (05b-i spec + sim, 05b-ii
CAD + frontend); say so in STATUS.md when it does.

## Deliverables

1. `configs/vehicle/orbital-launcher-v1.yaml`: `scale: full`, two stages as top-level nodes,
   40–60 parts — stage 1: octaweb thrust structure, nine engines (centre + ring), LOX tank,
   RP-1 tank, common bulkhead, helium COPVs, pressurisation lines, grid fins ×4, landing legs
   ×4, cold-gas RCS, interstage with pushers; stage 2: engine with vacuum nozzle, LOX and RP-1
   tanks, RCS, avionics; fairing halves, payload adapter, payload. Every part: geometry, mass
   with citation or `estimate`, propulsion/tank ratings where relevant, `learn:` block that
   names the physics, the simplification made, and the full treatment. Vehicle-level cited
   figures: liftoff mass, thrust, Isp SL/vac, propellant mass fractions, payload to LEO.
2. `configs/vehicle/engines/`: engine definitions (thrust vs pressure from the ideal rocket
   equation with cited chamber pressure and expansion ratio; Isp SL/vac; throttle range;
   gimbal range; mass; start/shutdown transients) with a sidecar citing sources.
3. Schema additions (`src/vehicle/schema.py`): `stages[]`, `tank` (volume, propellant,
   density, fill, ullage, pressure), `engine` (ref to engines/), `event` list for the mission,
   `scale`. `src/vehicle/mass.py` handles per-stage wet/dry and fill-dependent CG; rocket
   equation Δv per stage.
4. Sim extensions (`src/sim/`): `atmosphere.py` (US Standard Atmosphere 1976 to 150 km),
   `gravity.py` (inverse-square, J2 optional), spherical-Earth ECI frame with rotating Earth
   (ADR-0005), `propulsion.py` liquid engine model (Isp vs ambient pressure, throttle, mass
   flow, transients), `staging.py` (mass drop, separation impulse, body split into two
   simulated objects), aero tables subsonic → hypersonic with cited Cd and CP vs Mach, grid-fin
   force model, `events.py` extended, engine-out fault.
5. Scripted mission (`src/gnc/mission.py`): open-loop pitch program + gravity turn with a
   simple closed-loop pitch hold, max-Q throttle bucket, MECO on propellant or velocity target,
   separation, SES, fairing jettison on dynamic-pressure threshold, SECO on orbital energy;
   stage 1: flip, boostback burn to a target downrange point, entry burn, grid-fin attitude
   hold, landing burn with a simple polynomial guidance (G-FOLD replaces it in WO-08).
6. CAD (`src/cad/`): generators for cylindrical tanks with domes, common bulkhead, octaweb,
   engine bell (parametric expansion ratio), interstage, fairing halves, grid fin, landing leg,
   COPV. Illustrative fidelity; no `print:` blocks.
7. Frontend per `docs/UI.md`: scale switch, stage nodes, tank fill in section cut, mission
   timeline, stage selector, ground-track inset, per-stage summary with Δv.
8. `docs/results.md` orbital table: sim vs cited class figures.

## Benchmark

Nominal mission: stage 2 reaches a 200 km circular orbit (±10 km) with the spec'd payload;
MECO velocity, altitude and time, max-Q, and stage-1 landing propellant each within 10 % of
the cited class figures; stage 1 touches down at < 2 m/s nominal; engine-out at T+60 s still
reaches orbit with reduced margin (or the shortfall is reported); every part inspectable with
its `learn:` text and citations in the frontend; the model rocket still passes all WO-01–05
benchmarks unchanged (regression).

## Notes

- No vendor names, logos, liveries or proprietary figures anywhere — spec, CAD, UI or docs.
  Class-representative numbers from NASA technical reports, launch-vehicle user guides,
  Sutton & Biblarz *Rocket Propulsion Elements*, and Curtis *Orbital Mechanics for
  Engineering Students*.
- The flat-Earth model rocket path must not get slower or more complex: `scale: model` keeps
  the NED frame and skips atmosphere/gravity variation above its ceiling.
- Where the model simplifies — no slosh, no structural loads, no entry heating, no plume
  interaction, no turbopump start dynamics — say so in the `learn:` block and point at the
  interface in `docs/EXTENSIONS.md`.
