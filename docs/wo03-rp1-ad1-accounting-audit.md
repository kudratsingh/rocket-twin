# RP1 AD1 bookkeeping and admission audit

2026-11-03 local. Read-only audit of the completed AD1 record; the producer was
**not executed by this audit**. Only this new note is written. No source research,
solver, physical work, supplier contact or Git operation was performed. Audit
started 2026-11-04 05:22:31 UTC, within the declared 12-minute read/arithmetic
ceiling. Arithmetic below is ledger addition, moments, unit conversion and
reservation reconciliation; no trajectory or strip integration was rerun.

**Outcome:** the saved exact-once mass, cost and case arithmetic reconcile. No
remaining bookkeeping error was found in those fields. The definition remains
unadopted: the ideal panel screen already misses stress and movement limits,
planning departure still misses, and finished cord/joint/environmental evidence
is unavailable. Positive formal-guide headroom does not admit the package.

## Audited identity and evidence

Inputs are [the definition study](../configs/studies/rp1-attachment-definition.yaml),
[the producer](../scripts/wo03_rp1_attachment_definition.py), frozen
[balanced RP1](../configs/vehicle/candidates/g80-f2-rp1-balanced.yaml), and
[the completed record](../runs/wo03-rp1-attachment-definition-20261103-v1/record.json),
identity `G80-F2-RP1-AD1-definition-v1`, `adopted: false`.

Record SHA256:
`dbdd6183de505af4979f0088d41ed4ae89d1058afdf41c6d5ad4beadc8c93126`.
All four direct input/output hashes in its `sources` map matched the files read;
the archived `executed-producer.py` matched the current producer byte for byte.
The register does not independently freeze every imported helper, material
source, motor curve or the guide-ceiling record; those remain inherited evidence
dependencies rather than newly qualified inputs. No claim of complete dependency
capture follows from the four matching hashes.

One placement ambiguity was reported promptly before completion: the initial
slot-fill proposal used station 1140 mm plus a 65 mm CG offset. The primary
corrected it before the completed run. The saved ledger now places that 0.15 g
increment at **1140 mm CG**, matching the intended root-bond station. This audit
did not edit the producer or rerun it. The primary reports the initial schema
validation failure separately; it is not another completed engineering result.

## Exact-once mass and price reconciliation

Comparison against the frozen balanced-v2 ledger finds 53 old rows and 55 new
rows, with no duplicate part IDs and no removed rows. Only these mass/cost fields
change:

| Item | Balanced v2 | AD1 | Delta / accounting meaning |
|---|---:|---:|---|
| Kevlar installed budget | 15.00 g | 16.25 g | +1.25 g for the 6.5 ft cut estimate |
| New cord sleeve | absent | 2.00 g | +2.00 g once, additional to the retained 4 g mouth guard |
| Additional slot epoxy | absent | 0.15 g | +0.15 g once; no removed-paper credit |
| LOC main mass | 55.00 g | 55.00 g | No additional main or second sewn-end mass inserted |
| LOC main price | $20.00 estimate | $12.39 source snapshot | −$7.61; exact NW-12 variant, not the default elastic product |
| Sleeve / slot price | absent | $2.00 / $0.25 | +$2.25 estimates |

Thus **+3.400 g** is added to the physical model, from 881.149218 g to
**884.549218 g**. Ledger moments reproduce each saved case CG; the largest
mass/CG reconciliation residual is approximately 3.4e−13 in the displayed g/mm
units. Estimated total cost moves from $482.048 to **$476.688**, a −$5.36 delta.
That total is a source-and-budget estimate, not a complete procurement quote with
tax/shipping.

The entire minimum 10 ft Kevlar purchase remains costed at $17.10. Only 6.5 ft is
allocated to flight mass, leaving 3.5 ft outside the flight ledger. Neither the
purchase length nor the leftover stock is counted as installed mass. The 16.25 g
budget still depends on the unconfirmed 2 g/ft interpretation plus 25%; it is not
a measured finished weight.

Balanced RP1's prior removals are inherited once. AD1 neither removes the former
18 g eyes / old leader again nor repeats the ballast/sole-carrier removal. The
retained 3 g nose service hardware, existing 4 g ring-installation bond, 1 g notch
sealer, old bond reserves, protector and 4 g lip guard remain counted. No new
void, cut-width or old front-end bond removal credit is taken.

## Allowance, adverse case and metadata sensitivity

The physical ledger excludes growth. Each case adds the **full separate 50 g at
1250 mm** exactly once. The adverse case additionally adds **20 g at 1250 mm**.
Its **12.8 mm motor-CG probe** changes the first moment, not the mass. The launch
helper receives `total − 50 g` and itself adds the configured 50 g; reading the
helper confirms the allowance is not doubled. The record's four total masses,
CGs, burnout arithmetic and whole/body mean proxies reconcile independently to
the ledger and these declared operations.

| Main mass interpretation | Case | Total g | CG mm | 1.5 m guide m/s | Formal headroom g | Planning headroom g |
|---|---|---:|---:|---:|---:|---:|
| 55 g budget | nominal | 934.549218 | 763.805128 | 15.212909 | +23.794335 | −30.749923 |
| 55 g budget | adverse | 954.549218 | 775.711122 | 15.033479 | +3.794335 | −50.749923 |
| 68 g non-binding probe | nominal | 947.549218 | 757.990689 | 15.095650 | +10.794335 | −43.749923 |
| 68 g non-binding probe | adverse | 967.549218 | 769.856903 | 14.919669 | −9.205665 | −63.749923 |

The 68 g entry is a **+13 g hypothetical increment at the main's 340 mm CG**.
Every row says `probe_is_bound: false`; neither mass nor availability is inferred
from that commerce field. It is not an upper bound, actual finished mass or a new
selected hardware variant. The adverse formal failure of that sensitivity does
not prove the real harness weighs 68 g. Conversely, the passing 55 g estimate
does not establish an actual weight. Under the other fixed budgets, adverse
formal headroom corresponds to only 58.794335 g total main budget; no selection
or relaxation follows from this arithmetic.

The body proxy excludes the main, Kevlar and listed recovery soft group, so the
13 g hypothetical main increment changes the whole-vehicle proxy but not the
body proxy. The new sleeve is retained in the body-side mass group. This is
explicit conservative grouping, not omission. The required severe whole-vehicle
mean proxy is unchanged in method: 20.4 m/s, 0.3 m and design factor 3 including
gravity. At the 55 g adverse case it is **2014.309 N**; body demand is
**1400.931 N**. These remain required proxy demands, not measured peaks or
finished hardware ratings.

## Length and geometry reservations

The length arithmetic is reproducible:

`1981.2 − 2×300 − 110.486672 − 932.2 = 338.513328 mm`.

These terms are the 6.5 ft raw cut, two termination reservations, one cord-centerline
wrap circumference using proposed 3.8 mm cord diameter, and the 1072.2-to-160 mm
route plus 20 mm detour. The external reach exceeds the proposed 300 mm target
by **38.513328 mm**. The wrap is not silently omitted or added twice.

This closes reservation bookkeeping only. A 300 mm termination allocation is not
measured consumption by the proposed figure-eight eye, 100 mm tail, choker or
40 mm distal bearing eye. Actual knot dimensions, seating/slip and bend rules are
unavailable. The uncut 12 ft NW-12 nominal length is not established as bearing-point
length and is not used to invent extra available leader reach.

Recorded 0.300 mm notch flank clearance, 0.414492 mm **cold** knot-box/body clearance
and 0.250 mm slot flank clearance are conditional envelope numbers. The proposed
knot box is not a demonstrated knot, and textile folds, exact stock tolerances,
thermal/moisture closure, packing and sleeve edges remain unmeasured. Passing a
reserved-box clearance cannot close those gates.

## Admission limits of the scalar and quadrature results

The recorded refinement and closed-form comparison check integration arithmetic
for the declared ideal strip model. They do not establish its installed support,
gusset composite action, grain properties, adhesive transfer or hot/wet stiffness.
No numerical solver was executed by this audit.

Even that ideal model reports **7.301 MPa** maximum bending against the study's
5 MPa screen and **1.805416 mm** tip displacement against 1 mm. Both miss. Root
flexibility adds movement; no positive finite root stiffness can bring an already
over-limit ideal panel below 1 mm. The null required-root-stiffness field is
appropriate, rather than an accepted stiffness. The frozen former front-ring
tab support is not credited in this moved-ring attachment. The supplied study
allowables remain provisional engineering inputs, not conditioned stock evidence.

Other recorded demands also prevent a simple mean-stress pass claim:

- Outer-ring mean shear is 0.568 MPa; the separate inner-ring full-force envelope
  is 1.200 MPa against the 1 MPa provisional shear input.
- Full-route body axial demand is 7.610 MPa against the 2 MPa provisional hot-paper
  input. The existence of another load path would require established transfer
  and partition; it cannot be assumed from a lower average at another interface.
- Gusset/body normal mean is 0.755 MPa, but no normal/peel allowable exists. Shear
  capacity cannot substitute for that missing mode.

These are separate demand envelopes, not equal-sharing assumptions or loads to
sum again. Averaging force over an area cannot resolve local rope pressure,
annular-ring bending, paper crush/peel, plywood tension perpendicular to grain,
rolling shear, end gaps or installed movement. Converged quadrature and static
RocketPy agreement cannot close finished knots/sewn loops, heat/chafe, inflation/
snatch dynamics, installed flutter or flight release. The RocketPy static rows
also use the **884.549218 g physical model**, not the 50 g/adverse cases; agreement
there is not independent validation of those scenario assumptions.

The completed record is therefore useful as a reproducible failed-screen/test
definition packet. It supplies no recovery attachment qualification or permission
to adopt AD1. Supplier documentation and later separately authorized representative
tests may resolve missing properties; the known panel and planning misses still
remain independent admission findings. No reinforcement or solver retry is
proposed by this audit.

## Final v2 sleeve correction audit

Appended 2026-11-03 local after a separate read-only check, started
2026-11-04 05:26:30 UTC within a five-minute ceiling. The preceding sections audit
the preserved **v1** record; the following values identify final **v2**, not a
silent rewrite of v1.

Final inputs are [study v2](../configs/studies/rp1-attachment-definition-v2.yaml),
[candidate v2](../configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml),
[correction producer](../scripts/wo03_rp1_sleeve_correction.py) and
[record v2](../runs/wo03-rp1-attachment-definition-20261103-v2/record.json), identity
`G80-F2-RP1-AD1-definition-v2`, still `adopted: false`. All six hashes in the final
source map matched. Archived final specification and producer matched their
referenced files byte for byte. Final record SHA256:
`bc349a24fe1cfaa4d883b9e00dc5b75387638a7be5cd4b05d9f32112ee8bd95b`.
The original v1 record hash above remains unchanged.

The only ledger change is the **2 g sleeve CG from 1072.2 to 1020 mm**. The final
specification places its 80 mm envelope at 980–1060 mm, ending at the nominal
forward-ring front face, rather than occupying the 4.5 mm passage. This removes
the invalid assumption that an 8 mm folded sleeve fits that passage; it does not
prove manufactured end clearance or packing. The matching study explicitly
records no notch occupancy.

Independent moment arithmetic gives `0.002 × (1.020 − 1.0722) = −0.0001044 kg·m`.
Dividing by each saved loaded/dry case mass reproduces every final loaded/burnout
CG shift; the corresponding stability-margin shifts agree:

| Main probe | Case | Final loaded CG mm | Final loaded margin cal |
|---|---|---:|---:|
| 55 g | nominal | 763.693416 | 1.433324 |
| 55 g | adverse | 775.601751 | 1.255060 |
| 68 g, non-binding | nominal | 757.880510 | 1.520340 |
| 68 g, non-binding | adverse | 769.749002 | 1.342674 |

All part masses and prices are unchanged. Total masses, +3.4 g increment, growth/
adverse allowances, motor-CG probe, whole/body force demands and formal/planning
mass headrooms are identical to v1. Guide outputs, fin results, method check,
recovery means, slot clearance and cord reservations are unchanged saved values.
Reading the correction code confirms zero repeated guide or strip cases; only
the CG update and a new static RocketPy comparison are performed. This audit
executed neither producer nor solver. Reuse is consistent with the unchanged
mass-only guide inputs and unchanged structural inputs; it does not add new
validation evidence.

The corrected sleeve leaves **bare cord in the rounded/sealed passage**. The new
sleeve end, bare passage, exact textile and cord, heat exposure, chafe and packing
remain unqualified. No thermal or abrasion capacity is credited. The previously
reported panel, body/inner-ring envelope, planning and finished-joint findings
remain open or failed as stated; the geometry correction closes no admission or
flight gate.
