# WO-12 — System identification, retrain, fly again, final writeup

Branch: `wo-12-sysid`. Tier: Mac CPU + dev GPU for retrain.

## Deliverables

1. `src/sysid/fit.py`: fit servo (lag, rate limit, deadband), thrust-curve scale and timing,
   drag coefficient and TVC moment arm from flight logs and bench step responses (least
   squares / simple optimisation over the sim); writes a `fitted:` block into the spec with
   confidence and the logs it came from.
2. Retrain PID gains and the RL policy on the fitted spec; export; fly again (owner).
3. Before/after table: tracking error vs reference and vs sim prediction, per flight.
4. Final writeup: README with sim tables, flight table, cost table, hardware list, reproduce
   commands per number, what did not transfer and why; model card for the released policy;
   `docs/adr/README.md` index; all ADRs accepted or superseded; `docs/blog.md` final with
   flight video embedded (owner records; agent provides the overlay script stamping time,
   tilt, gimbal command).

## Benchmark

Fitted parameters reduce sim-vs-flight tilt error on held-out flights; at least one post-retrain
flight reported; README numbers match results.md; STATUS.md shows final compute and hardware
spend.

## Notes

- One change per retrain so the delta is attributable.
- If RL still does not transfer after one retrain cycle, residual RL on top of PID (ADR-0004)
  is the fallback; record it, do not keep iterating silently.

Fit and evaluate by actual configuration identity, measured mass properties and
motor lot; use held-out logs and report uncertainty. Preserve negative PID/RL and
sim-to-real results. A failed transfer does not remove committed RL or the original
finless research objective; it constrains the next experiment and flight release.

## Updated model calibration scope

Fit measured actuator torque/speed/voltage, friction/backlash/delay, moving-mass
properties and aerodynamic force/moment/damping parameters where identifiable.
Update thermal/contact and material/connection bounds using instrumented ground
tests; do not fit unidentifiable parameters to a single trajectory. Preserve data
identity, confidence intervals and held-out tests/flights. Re-run applicable
structural, thermal, clearance and RocketPy comparisons after changes, then compare
PID/RL fairly before/after. Publish negative findings and remaining limitations.

## Traceability and vibration-risk carry-through

Correlate mode/attachment/thermal/actuator/aero models with measured and flight evidence. Update uncertainty and repeat affected comparisons using separate calibration and evaluation data; preserve original evidence and honest negative results.
