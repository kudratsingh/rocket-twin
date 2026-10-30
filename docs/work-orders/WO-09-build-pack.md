# WO-09 — Build pack: prints, BOM, wiring, RSO document, firmware stub

Branch: `wo-09-build-pack`. Tier: Mac.

## Deliverables

1. `src/export/bom.py`: BOM from the spec — every part, source (printed / cut / bonded / assembled / purchased), vendor
   link placeholder, unit price (agent researches current prices; owner confirms), quantity,
   spares column. Output `build/<vehicle>/BOM.md` and `.csv`.
2. `src/export/wiring.py`: wiring diagram SVG generated from the spec's `netlist` (power,
   signal, pyro, with wire gauge and connector notes) → `build/<vehicle>/wiring.svg`.
3. `build/<vehicle>/PRINT.md`: print list with orientation, settings, estimated time and
   filament per part; assembly order with the mass-check step after each subassembly
   (weigh it, enter the number into the spec as `measured_mass`).
4. `build/<vehicle>/RSO.md`: one-page document for the Range Safety Officer — vehicle class
   numbers, motor, stability approach for that actual fixed/finned-TVC/finless-TVC configuration, abort logic summary,
   recovery, first-flight plan, references to the NAR Model Rocket Safety Code sections met.
5. `firmware/`: PlatformIO project stub for Teensy 4.1 with `policy.h` from WO-07, pin map
   generated from the spec's netlist, and a `README` of what WO-10 fills in.
6. Frontend build panel: BOM table, wiring SVG, print checklist.

## Benchmark

`make build-pack` regenerates everything; BOM total within the PLAN.md hardware budget or a
written reason why not; wiring SVG matches the netlist (test: every net appears once);
owner can print and order from the pack alone.

## Notes

- Owner buys, prints and builds. The agent's job ends at the pack and the firmware stub.
- Any part whose `measured_mass` differs from spec by > 10 % after printing triggers a spec
  update and a re-run of WO-01/02 numbers (one command: `make revalidate`).

## Configuration freeze before procurement

Deduplicate the shared upper, count each actual aft cartridge and every consumable.
Verify the exact offered motor lot, source curve/certificate, full installed
hardware, California classification and club requirements before recommending an
order. Refresh stock and prices; unresolved G25W remains quarantined.

Provide custom tube/joint, plywood, print and integration instructions with jigs,
tolerances, load paths and learning links. Record measured mass/CG and structural,
thermal, recovery deployment and power-isolation evidence per actual configuration.
Plugged G12ST-P has no motor-ejection backup. Independent recovery must not depend
on the learned policy or a failing flight-control task. Owner buys and performs all
physical work; generating the pack is not permission to purchase or fabricate.

## Engineering verification carried from WO-03/06

Include load paths, analysis margins and temperature/tolerance limits, print/grain
orientation, bond preparation/cure and fastener locking, inspection/access checks
and analysis-to-test traceability. Define owner-performed material coupons, fin-root,
modular-joint/recovery and gimbal proof loads, plus instrumented motor-case/liner/
adhesive/gimbal/electronics burn and heat-soak tests. Measure as-built tolerances,
mass/CG and loaded actuator torque/speed/backlash versus voltage/temperature.
Record failures, update property bounds and re-run affected CAD, analyses and flight
checks before release. Do not order or perform physical work without the owner.

## Traceability and vibration-risk carry-through

Generate manufacturing, inspection and unit-acceptance instructions tied to requirement/interface/FMEA IDs. Owner performs coupon, joint, mechanism, thermal and recovery tests and records measured as-built properties and component revisions, including modal/torsional/clearance measurements.
