# Engines (liquid, `scale: full` vehicles only)

One YAML per engine. Created in WO-05b. Fields: cycle, propellants, mixture ratio, chamber
pressure, expansion ratio, thrust SL/vac, Isp SL/vac, throttle range, gimbal range, mass, start
and shutdown transient times, `cite:` for every number or `estimate: true`.

Thrust and Isp vs ambient pressure are computed in `src/sim/propulsion.py` from chamber
pressure and expansion ratio (ideal rocket equation, Sutton & Biblarz ch. 3) and checked
against the cited SL/vac values.

Planned: `gg-lox-rp1-sl.yaml` (sea-level, nine on stage 1), `gg-lox-rp1-vac.yaml`
(vacuum-optimised, one on stage 2). Class-representative, no vendor names.
