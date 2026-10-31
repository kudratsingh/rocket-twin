# Notched shield-end baffle: fitted geometry and sampled baffle-first assembly

The single R24.8 mm baffle family has **zero nominal intersections** against
applicable source hardware and passes the specified **24-panel baffle-first
rigid assembly sequence**. Its source/manufacturing/thermal scalar clearances
are 0.370–0.436 mm against a 0.300 mm requirement. This is a geometry candidate
for actual-CAD radiation analysis, not thermal acceptance or demonstrated
manufacturing capability.

The original straight radial paths still fail for all 24 panels. Passing the
new sequence does not erase those failures or establish replacement access after
permanent body bonding. Original structural, thermal and release gates remain.

## Exact evidence and geometry exports

Final executed record:
`runs/wo03-baffle-fit-20261031T035358211715Z/record.json`.
Its `geometry-manifest.json` identifies **170 actual placed STEP/STL assets**,
part IDs, masses, units/frame and individual asset hashes. All cuts, three-piece
seams and rotated circular support sectors are present in the exported solids.
The CAD-ray consumer must use those assets, not substitute annular baffles.

Input:
`runs/wo03-circular-pad-candidate-20261031T034153884353Z/record.json`, candidate
identity `e25026cdc3b63f53a01cb4b91f3fb4b7e15c1b3e70e53924e95a639f4c5166b6`.
The source regenerates every CAD cache and opts sector pads into actual circular
boundaries, correcting their old inscribed-chord intrusion into adjacent foil.
The historical pre-correction source remains
`runs/wo03-multilayer-shield-20261031T022026246942Z/record.json`; its old failures
and histories are preserved, not relabeled as compatible with the new CAD.

The runner snapshots all inputs and relevant generator files before computation,
and rejects changes during generation/check/export. The new baffle postprocessor
is separately hashed. Generic `local_shape()` alone does not reproduce the new
notches or sector rotations; the complete study runner is required. A future
active-spec adoption would need a normal shared generator implementation.

The earlier rejected R26 mm baffle's actual rail collisions remain in
`runs/wo03-finite-thermal-20261031T030801091027Z/record.json`. It is not this family.

## One coherent family

- The **structural ring bore stays R15.8 mm**. The separate foil baffle clearance
  opening is R16.2 mm; no structural ring material is removed.
- Eight 20 µm foil baffles have outer R24.8 mm. All foil surfaces retain
  emissivity 0.9 for the required contaminated case.
- Actual rail and integral retainer-block rectangles are enlarged 1.0 mm in XY
  to define explicit baffle notches. Block clearance openings are included in
  every baffle's common cutting pattern, and remain real radiation leakage paths.
- Through radial seams 1.2 mm wide at 90°, 210°, 330° divide each baffle into
  three rigid panels. A 0.3 mm seam would not retain the source ±0.25 mm edge
  allowance plus opposing thermal expansion and required clearance.
- Three 10° circular support sectors at 30°, 150°, 270°, radii 24.0–24.3 mm,
  avoid both rails and blocks. They are actual separate sectors, not full disks.
- Each ring-to-baffle stack is ring / 20 µm epoxy / 560 µm mica / 20 µm epoxy /
  foil, giving a 0.600 mm stand-off. Every volume, mass and contact is recorded.
- Segmented foil/ring windows increase from 0.5 to **1.8 mm clearance per face**.
  The runner shortens the real foil segments and moves their existing end
  spacers accordingly. Every original segment and spacer retains its identity.
  The larger openings are exported and must be included in radiation analysis.

The family adds **0.385382 g** of baffles, mica sectors and adhesive. Shortening
the existing foils reduces the total candidate mass, giving **−0.078409 g net**
against this source. No positive thermal performance is inferred from that small
mass difference. Densities remain existing estimated aluminum/mica/epoxy values,
not measured manufactured masses.

**This is only the fixed G54 eight-layer assembly. No mass saving, shield fit or
thermal credit transfers to G12.** The separate G12 0.753 g forefoil probe remains
a failed/unsupported thermal solution, and compatible G12 shielding/budget work
remains open.

The candidate's loaded mass is 846.009911 g versus the regenerated source's
846.088320 g. Its CG moves forward 0.023648 mm at liftoff and 0.030524 mm at
burnout. The run records full 3×3 inertia tensors, lateral CG and deltas at both
endpoints. Body x points noseward; station CG increases aft. The symmetric tensor
changes below are in kg m²:

| Component | Liftoff delta | Burnout delta |
| --- | ---: | ---: |
| Ixx | −3.73560e−8 | −3.73568e−8 |
| Iyy | −5.12700e−6 | −6.69225e−6 |
| Izz | −5.12700e−6 | −6.69224e−6 |
| Ixy = Iyx | −9.42580e−10 | −1.21663e−9 |
| Ixz = Izx | +3.73849e−9 | +4.82543e−9 |
| Iyz = Izy | −6.90233e−13 | −8.80105e−13 |

External aerodynamic geometry and CP 0.924622198 m are unchanged. Static margins
are 1.525622 cal at liftoff and 2.078784 at burnout; placing the entire 50 g
allowance aft gives 1.197510 / 1.676325 cal. The minimum over 101 depletion samples
is 1.197510 cal. RocketPy 1.13.0 independently agrees on static mass, CG, CP and
margin at both endpoints to floating-point precision. That comparison excludes
inertia and flight. No new trajectory or launch acceptance is claimed.

## Axial, radial and thermal-clearance bounds

The declared source foil-edge error is ±0.25 mm; source hardware linear error
±0.10 mm; stand-off stack error ±0.05 mm; eccentricity/runout allowance 0.10 mm.
Foil CTE 23e−6/K is an estimate. Plywood CTE 30e−6/K is the existing source
estimate. Foil is geometrically probed at 300°C from 35°C; hardware at 65°C.
The latter is an adverse expansion probe and **does not raise the 45°C substrate
screen**. New baffle/pad cutting tolerances remain proposed, unmeasured processes.
The clearance budget uses the wider source foil-edge allowance conservatively.

The longest shortened segment is 48.4 mm. Full-span, rather than half-span, foil
growth is 0.2950 mm; relative frame-station growth is bounded by another
0.0495 mm. Nominal segment-end-to-baffle clearance is 1.180 mm.

| Declared scalar clearance | Minimum remaining | Requirement |
| --- | ---: | ---: |
| Axial foil end → baffle | 0.435502 mm | 0.300 mm |
| Inflated rail/block notches | 0.370206 mm | 0.300 mm |
| Baffle opening → original foil | 0.387844 mm | 0.300 mm |
| Panel seams | 0.397688 mm | 0.300 mm |

These are explicit scalar worst-case calculations for the stated dimensions,
CTEs and temperature probes. They are not a continuous CAD deformation analysis,
foil-warping/vibration result, measured tolerance capability or a thermal pass.

## Actual hardware and assembly/service sequence

Exact BRep intersections use a 1e−5 mm³ reporting threshold, rather than the
larger legacy threshold that could hide thin-foil penetrations. Every new part
is checked against all applicable source hardware and other new parts. Budget
envelopes are explicitly excluded in the record; purchased motor geometry is
the source envelope and not a verified supplier closure/nozzle model.

Every direct radial panel insertion/withdrawal still intersects the monolithic
mount at 15 mm translation. The parent-approved baffle-first sequence uses the
following **different, explicitly sampled rigid path**:

1. Work before permanent shell bonding. Remove body, motor/liner, foil wraps and
   the removable aft retainer/hardware/pads. Retain the actual monolithic mount,
   including all rings, rails and integral retainer blocks, the fixed forward
   thrust plate and fore thrust pads. All new support compounds are present.
2. For an interior panel, yaw 30° to an open rail window, tilt 45° about that
   local radial axis and enter radially at mid-bay into an 8 mm inward central
   workspace. Flatten there, recenter, restore final yaw, then move axially to
   the final 0.6 mm stand-off. No plastic bending or elastic deflection is used.
3. The first forward bay accounts for the actual forward-plate web ending at
   1.010 m. Its effective open bay is 35.0 mm; other interior bays are 35.5 or
   52.0 mm. The actual tilted panel's axial span is **29.955 mm**. Integral plate
   fingers remain in the collision geometry.
4. Rearmost aft panels approach axially from aft. Integral retention blocks stay
   in place and are cleared by the actual notches. Already-installed panels and
   all support sets remain obstacles for each subsequent panel.

All 24 staged panel paths pass their sampled poses. This establishes the stated
nominal baffle-first sequence, not continuous clearance between poses or service
replacement after the body has been bonded. The contact/adhesive installation
process, access for tooling, cure control and manufactured foil integrity remain
unverified.

The final record contains 588 evaluated staged poses. The original straight-path
failures remain separate fields. A targeted synthetic CAD test independently
checks three real panels, through-notches/seams and retained support-bearing
material; Ruff and Black also pass for the fit runner/test.

Nominal motor extraction also clears ten sampled aft positions from 0 to 240 mm,
with the removable aft retainer, retention hardware and aft thrust pads removed.
That uses the source motor cylinder. Actual supplier shoulders/nozzle envelope,
thermal dimensional changes, insertion friction and a continuous removal sweep
remain open. No physical work was performed.

## Thermal handoff and unchanged gates

The new contact ledger does not hide heat paths. Each baffle has about
**0.002510 W/K bulk bonded-sector conductance** and an estimated **0.053487 W/K
parallel axial air-gap conductance**, using actual notched footprint minus actual
support area, 0.6 mm gap and assumed air k=0.04 W/(m K). The latter is over twenty
times the bulk support path and must not be discarded when radiation improves.
Both paths belong at the same solved physical surfaces. New baffle/support
temperature histories remain unavailable.

The CAD-ray/occupancy pipeline must consume the actual notches, seams, shorter
wraps, exact sector supports, glue, fin/tab and end openings. Then the coupled
common-surface model must be rerun through required cases, property corners,
end-boundary uncertainty and numerical/geometry convergence. The 300°C case,
emissivity 0.9, 35°C ambient and 45°C substrate screen are unchanged. The source
finite transient failure and all other engineering findings stay open.

Reproduce with `.venv/bin/python scripts/wo03_baffle_fit.py` using the regenerated
source record. The run uses one CPU worker, no rays and $0 paid compute.
`thermal_acceptance_available`, `active_adoption` and `flight_ready` are false.
