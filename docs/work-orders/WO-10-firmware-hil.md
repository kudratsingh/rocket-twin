# WO-10 — Flight-computer firmware and hardware-in-the-loop test (owner reviews this PR)

Branch: `wo-10-firmware`. Tier: Mac + Teensy over USB.

## Deliverables

1. `firmware/src/`: sensor drivers (IMU, baro) at the spec rates; estimator (same algorithm as
   `src/avionics/estimator.py`, codegen or hand-port with a bit-exact test on recorded data);
   PID controller (codegen from `src/control/pid.py`); MLP policy from `policy.h`; controller
   selector (PID / RL / passive) set before arming; abort state machine (codegen from
   `src/control/abort.py`); servo output with the spec's limits and rate cap; recovery pyro
   trigger; microSD logging of every loop at full rate; arming sequence (switch + continuity +
   self-test); buzzer and LED states.
2. `scripts/wo10_hil.py`: hardware-in-the-loop — the Mac runs the WO-02 sim, streams sensor
   values over USB serial to the Teensy at the loop rate, receives gimbal commands back, and
   feeds them into the sim. Logs timing. Fault injection from `src/avionics/faults.py`.
3. Bench tests documented in `firmware/TESTS.md`: loop timing, abort on each condition,
   servo range vs spec, logging integrity across a power cycle, brownout behaviour.

## Benchmark

HIL flight at the spec loop rate with ≤ 2 ms jitter; HIL tilt trace matches the pure-sim trace
for the same seed within estimator noise; every abort condition verified on the bench with
the servo visibly centring; SD log replays in the frontend as a run.

## Notes

- Owner reviews this PR line by line; it is the one place a bug costs hardware or safety.
- No dynamic allocation in the loop; no floating-point formatting in the loop; log binary,
  decode on the Mac.
- The controller cannot command the gimbal until the abort state machine reports `ARMED_OK`.

Test the actual performance, finned TVC and finless configuration identities;
reject a mismatched geometry/motor/policy hash before arming. Include servo-load,
loss-of-thrust, sensor faults, loop overrun and power-loss cases through coast and
recovery. Demonstrate recovery independence from policy/control-task failure and
qualify power isolation. G12ST-P is plugged; no motor-ejection fallback is assumed.
WO-10 owner review remains the explicit exception to routine autonomous PR handling.

## Fidelity, instrumentation and HIL additions

Log both low-g IMU and high-g accelerometer, voltage, actuator command/response and
qualified temperature channels with timing/alignment. Exercise load, voltage sag,
friction/backlash, delay, moving-inertia coupling and aerodynamic validity bounds
from WO-06; test saturation, overtemperature, out-of-envelope and sensor-clip
responses. HIL uses the shared improved core and exact configuration hashes.
Verify independent recovery across failure and burnout transitions. Owner line-by-
line firmware/abort review and physical bench acceptance remain mandatory.
