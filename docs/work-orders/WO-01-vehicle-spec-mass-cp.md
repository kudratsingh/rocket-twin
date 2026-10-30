# WO-01 — Modular platform definition and preliminary model validation

Rebaselined 2026-10-29 by explicit owner direction; ADR-0006. Tier: local CPU.
Custom building, maximum practical no-HPR performance and serious PID-to-RL control
research are core goals. The original fixed F15/three-second/average-TWR-3/29 mm/
78 mm/PETG assumptions are historical design choices, not completion requirements.

## Deliverables

1. Typed YAML parts contract and explicit performance, finned TVC and finless TVC
   configuration identities. Shared upper assembly resolves into each complete spec;
   mode-specific fins, gimbal, motor, geometry and masses remain actual parts.
2. Part-by-part mass/CG/inertia including motor depletion, physical fin radial inertia,
   subsonic Barrowman CP and estimated drag. Every part has mass evidence or estimate,
   `learn` content and build/cost/generator metadata. CAD generators remain WO-03;
   full procurement BOM/build instructions remain WO-09.
3. Bounded materials/construction, dimensions/mount and motor trade. Recommend a
   coherent preliminary hardware configuration per mode, with source disagreements,
   mass allowance, cost estimate, fabrication approach and remaining checks explicit.
   Reconsider old threshold-only rejections without editing their historical records.
4. Traceable, hashed numerical motor inputs with dimensions/masses/thrust values
   consistent with the resolved mode. Distinguish web transcription, byte-verified
   archive, certification summary, sold variant and measured hardware. Document exact
   correspondence gaps instead of requiring an arbitrary count of three motors.
5. Reproducible CPU reporting for every mode, derived inventory previews, source/code
   hashes and real independent RocketPy static comparison. `make tiny` and
   `make benchmark` evaluate the modular platform. Legacy study commands remain.

## Stage-appropriate completion benchmark

- All three specs validate; common upper parts agree; each physical fin set affects
  mass, radial inertia and aero together; each mode has its own independent comparison.
- Loaded design including explicit growth allowance remains <1.5 kg; qualifying
  commercial single-G motor evidence is declared, <=160 N s and <=80 N certified
  average thrust, no hybrid/sparky. This does not certify a particular purchased lot.
- Input hashes and numerical summaries match each mode's source-curve hypothesis.
  Quarantined motor data cannot become accepted merely by loosening a threshold.
- Mass within 3%, CG and CP within 3% of vehicle length, stability margin within
  0.1 calibre of RocketPy at liftoff and burnout. Mass distributions/inertia are
  labelled unmeasured; agreement checks arithmetic and geometry, not actual hardware.
- Mode-specific preliminary design screens pass: performance rail exit >=15 m/s
  on 1.5 m usable guide; TVC >=10 m/s on 2.4 m usable guide, with mass allowance,
  lower-bound thrust, estimated drag/friction. Passive configurations have >=1 cal
  margin with all growth allowance aft at both endpoints. Finless records its
  negative static margin explicitly and has no passive-margin pass claim.
- TVC has >=2 s contiguous post-guide thrust/weight >=1.2 under the conservative
  screening mass/thrust case, target >=5 s. These values assume roughly 0.2 s
  actuator/control settling: >=10 settling intervals minimum, >=25 preferred.
  This proxy does not establish achievable closed-loop bandwidth or torque authority.
- Recovery canopy area/descent target is budgeted for the heaviest mode. Costs,
  fabrication route, open source/fit questions and later release gates are recorded.
- CPU tiny/benchmark <120 s; appropriate tests, formatting and type checks pass.

These are **preliminary numerical design** completion criteria. They do not require
purchases, fabricated hardware, flight readiness, a closed-loop controller or proof
of RL superiority. Source transcriptions are permitted as labelled hypotheses here;
exact source/variant reconciliation is mandatory before the relevant later validation
claim or hardware decision. A passing WO-01 record always has `flight_ready: false`.

## Later gates retained

WO-02: flight/rail transient, altitude/site limit, wind, drag sensitivity, recovery
and motor-ejection delay; reference comparisons use actual finned geometries.
WO-03/09: CAD, fits/tolerances, assembled motor envelope/CG, weighed parts, joint and
fin strength, load margins, case/airframe temperatures, wiring and recovery ground tests.
WO-06/07: actuator/sensor realism, PID then committed RL, domain randomisation,
fair multi-seed comparison and embedded size/output constraints.
WO-09/10: exact current motor certification/California classification and offered lot,
independent recovery, abort logic, HIL and release documentation.
WO-11: actual club/RSO acceptance, conventional performance flights, PID before RL,
separate finless validation including burnout-to-recovery behavior with no thrust
available for stabilization. No unconditional flight schedule from a sim pass.

Sequence WO-01 through WO-12, including WO-05b, is retained. No later implementation,
physical work, purchase or paid run is authorized by this work order. GitHub pushes
and PRs are separately authorized by the owner; follow `AGENTS.md` without a
routine owner-review pause.
