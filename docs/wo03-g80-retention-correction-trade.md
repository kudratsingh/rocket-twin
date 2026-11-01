# G80 retention correction trade — bounded source-based screen

**Scope:** compare three correction hypotheses for the prospective fixed-motor
G80 package. The current bond-only bridge path is **unaccepted under
the existing provisional screens**. Its adverse rigid-support tractions and
coarse Gauss stresses do not establish a physical capacity; they are enough to
stop blind refinement of that same load path. This note performs only source-
based area, section and mass arithmetic. It makes no geometry, active-spec,
solver, purchase or hardware-selection change and accepts no architecture.

## Evidence and load basis

The source-pinned coarse field uses a **1.5 mm nominal mesh target**. The
3.0 / 2.0 / 1.5 mm pilot settings change the calculation grid, not the part:
the source geometry's G11 plate remains **2 mm thick**, with six tabs to rail backs and nominal 0.1 mm proposed adhesive
films. The saved [rigid-backing traction diagnostic](wo03-g80-bridge-support-traction.md)
uses **150 N service** and applies existing DF3 = 3 once in its reported
screen values. Each of the six support faces has area 99.540830698 mm². In the
SINGLE case, the two highest tangential traction lower bounds are 1.3215 and
1.3356 MPa raw, or **3.9646 and 4.0068 MPa after DF3**. The estimated epoxy hot
shear screen is 1 MPa. The resulting area arithmetic is:

- To put the *same resultant* below a uniform 1 MPa screen, the two critical
  interface faces would each need at least about **394.6 and 398.8 mm²**, about
  4.0 times their current area, if the resultants did not change.
- A perfectly uniform total-share lower bound is **450 mm²** (`150 N × 3 /
  1 MPa`) across all interfaces. It does not describe the observed SINGLE
  concentration and must not be treated as a sufficient joint area.
- The EQUAL case has 1.044–1.065 MPa DF3 face-average tangential bounds on all
  six current faces. Normal/peel is not qualified: the saved [SINGLE Gauss
  stress field](wo03-bridge-gauss-stress.md) reaches positive normal values about
  8.2 MPa on two films, and no
  matching adhesive normal/peel allowable exists.

These are force-resultant/area screens from saved fields and an idealized rigid
rail support. Earlier actual-geometry CCX solves completed but failed
equilibrium checks, so those structural outputs do not validate this path.
Later coarse Elmer field diagnostics pass their stated force/reciprocity checks;
that does not remove the CCX failures or establish an installed-joint capacity.
Actual interface load sharing, adhesive wetting, normal/peel, local peaks and
convergence remain unverified. Neither the arithmetic nor any saved field is a
bond-capacity pass.

The 150 N value is the existing **service** reverse-retention load. Apply DF3
once for its demand arithmetic, giving 450 N. The separate **1,782.253 N
recovery backbone** demand is already factored in its existing off-nominal
screen; do not factor it again. It is not a retention-service substitute, and
the two cases are not combined as simultaneous loads here.

For rough section arithmetic only, current engineering profiles estimate G11
strength as 50 MPa cold / 25 MPa hot and weak-direction plywood strength as
10 MPa. Those are generic estimates, **not bearing, pull-through, net-section,
laminate-direction or joint allowables**. Thus the values below are minimum
ideal net areas under uniform axial stress, not approved dimensions:

| Load case | Estimated screen used | Ideal net area arithmetic |
|---|---:|---:|
| Retention, 450 N factored | G11 hot 25 MPa / cold 50 MPa | 18.0 / 9.0 mm² |
| Retention, 450 N factored | Plywood weak-direction 10 MPa | 45.0 mm² |
| Recovery, 1,782.253 N already factored | G11 hot 25 MPa / cold 50 MPa | 71.3 / 35.6 mm² |
| Recovery, 1,782.253 N already factored | Plywood weak-direction 10 MPa | 178.2 mm² |

No additional DF is applied to the recovery rows. Actual bearing and hole
breakout need mode-specific, hot, directional data and geometry. No equal
sharing across screws, rails, tabs or bonds is assumed.

## Three correction hypotheses

| Hypothesis | Potential benefit | Quantified screen / current evidence | Main unresolved consequences |
|---|---|---|---|
| **A. Increase bond overlap and/or web thickness; adhesive remains the primary reverse path** | More bonded area could reduce average shear if the same force spreads over the larger faces; a thicker web could reduce local plate bending. It retains the current fabrication concept. | Current SINGLE critical faces need roughly **395–399 mm² each** under the same-resultant / 1 MPa estimated hot-shear arithmetic, versus 99.541 mm² current. That is only an area lower bound; the actual reactions would change with geometry. Increasing thickness alone does not increase bond area. The 150 N service and DF3 are already represented in the 3.965/4.007 MPa values. | Still relies on unverified glue as primary; actual wet coverage, peel, G11 tab/root stresses, plywood/ring/shell load transfer, hot bond properties and rail compliance remain unresolved. More web/overlap may consume fin-channel, motor/liner, ring, fastener and service clearances; adds aft mass with CG/guide cost. Thermal case can reduce adhesive/substrate margin. No added mass is quantifiable without a source-matched geometry and bond allocation; the 4.620 g upper annulus is not proven coverage or a free allowance. **Not accepted; no same-path mesh refinement proposed.** |
| **B. Align retainer axes with structural rails; use positive G11 bearing/capture and preserve the light plywood frame where its role is verified** | Gives the reverse-retention load a direct, inspectable mechanical route into the rails/G11 seats instead of relying on the adhesive film as its sole primary tensile/peel path. Could keep the broad custom plywood frame and its mass where analysis supports it. | For 450 N factored retention, scalar screens imply at least 18 mm² G11 net area at the estimated hot 25 MPa screen (9 mm² cold) or 45 mm² plywood at its estimated 10 MPa weak-direction screen. These figures are **not bearing or pull-through allowables**. The SINGLE rigid-support field shows unequal reactions, so no per-fastener or per-rail equal split is credited. Existing nominal G11 keeper/bridge geometry uses a 54.538 mm² washer-to-bridge probe per site, but keeper anti-rotation and load capacity are unqualified. | Requires exact retainer/rail axis alignment, positive washer/shoulder capture, net ligament and hole-bearing checks, bridge/tab-to-rail load transfer, rail/ring/shell buckling and fastener engagement. The existing geometry's 5° nut-rotation gate was inconclusive; later nominal service samples do not prove tolerance, torque or structural retention. Recovery still needs its separate continuous load path, protection, attachments and full 1,782.253 N screening; do not presume this retention bridge captures recovery. Added/changed parts are aft and can reduce CG/stability or guide margin; hot G11, plywood and glue interfaces remain open. |
| **C. Continuous mechanically captured G11 load frame/cage** | Could provide a continuous positive reverse-capture frame across local rings/rails and allow selected recovery attachment/load introduction to be studied without asking the plywood bond alone to close the path. | At the estimated 25 MPa hot G11 screen, carrying the full **already-factored 1,782.253 N recovery** as ideal axial net section requires at least **71.3 mm²**; at 50 MPa cold it is 35.6 mm². An ideal uniform 71.3 mm² G11 section at density 1,850 kg/m³ is **131.9 g per metre**, before holes, geometry, joints, capture, bending or buckling. Retention-only 450 N would require 18.0 mm² / 33.3 g per ideal metre at 25 MPa. These mass-per-length values are arithmetic lower bounds, not a proposed rod, cage or fabrication. | The required usable length and section shape are not defined; real cage load includes eccentricity, apertures, discrete capture and bending, so net section alone is insufficient. Greater aft mass can shift CG and degrade guide/stability performance. Cage may obstruct fin channels, motor/nozzle/retainer, module joint and motor removal. Thermal conduction/exposure and hot G11 directional strength remain open. It must not become unverified metal body load rods; a G11 positive capture still needs detailed joints and source-matched load introduction. No full replacement architecture is accepted. |

## Available source mass evidence and limits

The exact nominal [keeper-service source](wo03-g80-keeper-service.md) reports
**40.448195 g** for remaining plywood mount and guides at the study's 715
kg/m³ plywood density, **15.409675 g** for a G11 keeper including integral
pads, and **10.176847 g** for the G11 bridge at 1,850 kg/m³ G11 density. Their
named gross subtotal is **66.034717 g**. The [retention-integration config](../configs/studies/wo03-g80-retention-integration.yaml)
sets these study densities. These remain useful source component masses, but
the then-current [keeper-service mass audit](wo03-g80-retention-mass-audit.md)
was historical: it correctly said that 52-part study had not yet regenerated
the complete vehicle or net mass change.

That gap was subsequently closed for the **current isolated 72-part G80
candidate**, identity `90b2a9ad780fc81d11171363432c46088531817ddb6570fe9f800429bde2bdfc`.
The [staged report](wo03-g80-staged-retention-results.md) records regenerated
CAD, a complete 72-part component mass ledger, full mass/CG/inertia, static
comparison and four flight cases. Loaded mass is **772.982 g**, plus the full
separate 50 g allowance gives **822.982 g**. In that 72-part ledger, the prior
7 g retention lump was already removed once and replaced with itemized
hardware plus a distinct 1 g estimated locking/materials reserve. Do not
subtract the old 7 g again, and do not imply it remains unitemized in the
current 72-part mass. The 66.034717 g source subtotal is not an extra addition
on top of that integrated total.

The separate corrected **73-part canopy +5 g sensitivity**, identity
`6b0577cef1256065f27dc79bb494a89e6c1f0c90703c9815f47c7ae7910d1dc4`, is a
different recovery study. Its 5 g connector/line allocation is not part of a
new retention frame and is not added to the current 72-part package here.
Future B/C alternatives still need a complete exact-once replacement ledger
against the 72-part source before their net mass, CG or inertia can be known.
No new hardware mass, source availability or purchase status is assigned.

For A, extra bond/web mass is unavailable without a defined shape, bondline
and allocation. For B, use the 66.035 g subtotal only as source evidence for
named study components; compare any correction against the complete 72-part
candidate once its affected replacement boundaries are exact. For C,
131.9 g/m is the ideal recovery-section lower bound at the estimated hot G11
screen; actual cage mass and even feasible stock form are unavailable. In all
cases, mass added aft can move CG, alter static/guide margins and reduce
maximum-practical-performance headroom. Recompute those values on a single
resolved candidate before considering adoption.

## Cross-cutting gates and next bounded comparison

- **Recovery:** the 1,782.253 N primary recovery demand remains an independent,
  already-factored case. A retention seat or bridge is not a recovery anchor.
  Any shared G11 frame needs explicit nose/body/aft branch paths, positive
  retention, opening-load basis and uninterrupted load transfer; recovery
  branches, cord/endpoints and physical proof remain open.
- **Buckling and support:** neither a bonded overlap nor a positive retainer
  proves the plywood rails, G11 bridge/tabs, rings or body shell resist local
  buckling, prying, peel or asymmetric bearing. Do not turn the ideal net-area
  figures into a design criterion.
- **Thermal:** preserve existing 45 °C plywood/paper substrate and conditional
  65 °C adhesive/process screens. Neither the actual thermal method nor
  installed heat history is qualified; no threshold is raised here.
- **Assembly/service:** preserve the actual motor/nozzle/retainer, fin channels,
  rail envelope, fastener tool access, captive-nut pre-shell assembly and
  aft motor-removal path. Existing nominal service samples do not close
  tolerances or loaded access.
- **Performance and scope:** evaluate the fixed-motor G80 only. Keep the
  substantial custom frame and maximum practical performance goals visible;
  G54 and G12 remain separate committed tracks with their own evidence and
  acceptance.

**Recommendation to the primary:** make one source-pinned physical-geometry
comparison of **B versus C**, retaining A as the unaccepted bond-only baseline.
Check retainer-axis alignment, bearing/capture ligaments, rails/rings, finite
support faces, hole/washer envelopes, service access and exact component
replacement boundaries. Carry nominal source masses and unknowns separately;
stop if the positive path cannot fit without losing motor, fin, module or
service clearance. Do not repeat the unchanged bond-only design refinement. Only after a
reviewable geometry and load path exist should the primary decide whether to
authorize a newly bounded structural analysis. This note makes no request of
the owner and leaves all physical, procurement, flight and release gates open.
