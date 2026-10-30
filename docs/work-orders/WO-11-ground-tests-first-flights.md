# WO-11 — Ground tests and first flights

Branch: `wo-11-flights`. Tier: Mac + hardware; owner does all physical work.

## Deliverables

1. `scripts/wo11_ground.py`: bench tilt test (hand-tilt the armed vehicle on a stand; gimbal
   should counter; plot command vs tilt), servo range/latency measurement (step response
   recorded through the Teensy log → feeds WO-12 system ID), mass and CG measurement entry.
2. Flight plan in `docs/flights/plan.md`: qualify conventional performance flights
   first, then the actual finned trainer with PID before qualified RL. Progress to
   finless PID/RL only after separate control, abort and burnout-to-recovery evidence.
   No automatic fin-removal schedule. Per-mode go/no-go includes verified wind,
   motor/curve/lot/delay, measured mass/CG, battery, continuity, logging and club/RSO approval.
3. `scripts/wo11_import_log.py`: Teensy log → run with `source: flight`, wind estimate entry,
   and the sim's prediction for the same motor/wind as a paired run; frontend compare shows
   flight vs prediction.
4. `docs/results.md` flights table filled for every flight, including failures.

## Benchmark

Bench tilt test shows correct-sign gimbal response; at least one PID flight with a complete
log imported and overlaid on its sim prediction; a separately qualified RL flight
attempted and reported either way. If a release gate or launch opportunity prevents
flight, record the blocked flight milestone honestly rather than waive the gate.

## Notes

- Expect the first flights to differ from sim. Report them; WO-12 is for closing the gap.
- Weather and launch dates are outside the agent's control; the sim-only milestone is already
  shipped.

Each flight and paired prediction uses the actual complete configuration and
motor/source hashes. Finless TVC cannot stabilize after thrust ends: demonstrate
a qualified recovery transition before flight. No simulated benchmark or PR merge
is a physical flight authorization.

## Engineering qualification and comparison

Owner ground acceptance must close WO-03 material/joint/fin/gimbal strength, hot-soak,
clearance/assembly and retention tests with measured evidence. Validate actuator
response under load and supply/temperature variation. Compare logged acceleration,
attitude, temperatures, voltage, actuator response and flight-derived aero against
preflight uncertainty bands. Report model-domain violations, failures and unexplained
residuals; do not infer physical accuracy from the WO-02 integrator agreement.
