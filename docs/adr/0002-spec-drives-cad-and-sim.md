# ADR-0002: The vehicle spec drives CAD, mass properties, sim and frontend

Status: accepted
Date: 2026-10-26
Work order: WO-01

## Decision

`configs/vehicle/<id>.yaml` is the only hand-edited description of a vehicle. A pydantic
schema (`src/vehicle/schema.py`) validates it, including NAR/Class-1 mass and propellant
limits as hard errors. From the spec: `src/vehicle/mass.py` computes mass, CG and inertia as
functions of burn fraction; `src/vehicle/aero.py` computes CP (Barrowman) and the drag model;
`src/cad/` generates every part's geometry; `src/sim/` reads params from the spec; `src/api/`
serves it; `src/export/` writes the BOM and wiring diagram from the parts and the netlist.

Each part has `learn:` text and, where relevant, `electrical:` ratings and `print:` settings.

## Why

- The owner's stated goal is to look into every part and see how it connects to the physics;
  that only works if there is exactly one description of each part.
- Spec-first makes the twin and the physical build the same object: printing `build/` is
  building the spec.

## Alternatives considered

- OpenRocket `.ork` as the source — rich design format, but Java-only tooling and no room for
  electrical, print or learn metadata.
- CAD-first (CadQuery as source, spec derived) — mass and electrical data do not belong in CAD
  code; and the sim would depend on CadQuery at import time.

## What would reopen this

A part type whose geometry cannot be reasonably parameterised in YAML (then the spec points at
a checked-in STEP file and records its mass/CG by hand, flagged `measured`).
