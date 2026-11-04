# RP1 FR1 fin/root replacement — stopped before detailed analysis

**Decision: do not admit FR1 to detailed CAD, finite-element analysis or
construction.** Its proposed complete ledger is20.840g lighter, but the
finite-support movement cases fail, the one-sided body-fillet mean exceeds the
unchanged shear screen, and qualified finished hot-laminate/joint properties
are unavailable. This is a stopped preliminary proposal, not a demonstrated
physical failure or a replacement for frozen RP1 AD1 v2.

Open the [drawings/BOM](../output/rp1-fin-root-fr1/index.html),
[dimension definition](../configs/engineering/rp1-fr1-connection-definition.yaml),
[study](../configs/studies/rp1-fin-root-replacement.yaml),
[record](../runs/wo03-rp1-fin-root-20261104-v1/record.json) and
[joint supplement](../runs/wo03-rp1-fin-root-20261104-v1/joint-supplement.json).
Identity is`RP1-FR1-monolithic-carbon-v1`; all stations are mm aft from nose.
No active vehicle, G54 upgrade or G12 PID-to-RL hardware is changed.

## Inputs checked before choosing the correction

The [load/material source audit](wo03-rp1-fin-input-sources.md) found the
40kPa/5deg case is a historical engineering sensitivity, not current flight
evidence. **8.83N·m belongs to the older90mm C1 fin.** On the present60mm fin,
the same40kPa/5deg/DF3 formula gives2.905255N·m. AD1 retained8.83 by explicitly
rescaling the pressure distribution. Its earlier prose conflated those two
cases. FR1 still uses8.83N·m and331.125N, with DF3 already applied; no additional
factor is applied to stress or movement. A [separate proposed correction](wo03-rp1-fin-load-review-proposal.md)
is **not adopted**. Old flightq maxima and estimated hot plywood properties
are retained with their exact source/configuration limitations.

One selected replacement uses **Rock West204-11**,12×12×1/8in infused
quasi-isotropic carbon/epoxy sheet, nominal3.175mm, manufacturer tolerance
2.921–3.429mm, nominal density1520kg/m³ and listed$108.99. Immediate stock is
unconfirmed. Three130×77.451mm blank envelopes fit within the sheet before
tool/edge/coupon allowances; final nesting and cut quality are not released.

The advertised CLT table explicitly disclaims guaranteed properties. Reading
6.664million aspsi in its default imperial context gives45.947GPa; the web
unit selector did not expose an explicit unit label, so that interpretation
still needs confirmation. It is an **in-plane CLT reference**, not measured
flexural modulus or a hot/wet allowable. The supplied laminate layup does not
make an isotropic bending approximation a qualification. The table's modeled
compression value, raw-fiber properties and an E-glass result in the neat-resin
bulletin are not qualified carbon bending strengths. No finished hot strength
or modulus was found. Half the referenceE is explored only as a sensitivity;
it is not a sourced environmental lower bound. Neat-resin90°C DSC Tg does not
qualify this plate, cure, joint or45°C substrate screen.

Construction precedent: Madcow cardboard/plywood DX3 K-126 lists G80T-7 and
uses a conventional motor mount/body/through-wall fin connection; it does not
qualify current78010 or our loads. The fiberglass DX3 K-170 manual explicitly
shows G10 tangs epoxied to the tube and external fillets, but uses different
materials/geometry and supplies no measured joint stiffness. FR1 borrows this
**connection topology**, not a capacity, catalogue weight or G80 approval for
the fiberglass version. See the exact manual/version register in the audit.

## One dimensioned arrangement and actual force routes

Keep three130/65mm-chord,60mm-span,45mm-sweep fins at0/120/240deg. Their
3.175mm nominal integral tabs occupy1080.2–1189.6, with inner flat radius15.95
and radial depth17.451. No bolt, socket or removable aft interface is added.
The forward ring remains1060–1072.2, ahead of the tabs; the aft ring1190–1196
has a nominal0.4mm **filled adhesive gap**, not direct tab butt contact.

The proposed body cuts are3.8±.05mm wide and1079.9–1189.9 axial endpoints
at±.025mm. With maximum3.429mm stock and provisional0.05mm environmental
closure, per-flank minimum is0.1355mm, and each axial end minimum0.175mm,
against unchanged0.1mm. These depend on proposed inspection/conditioning bounds,
not supplier guarantees. No removed-paper mass credit is taken.

Continuous internal tab/tube and external fin/body fillets have6mm nominal,
5.8mm minimum legs. Retain14g internal and10g external adhesive budgets;2g
edge seal/finish replaces the old wedge-specific process allocation. The exact
adhesive, cure, surface preparation and allowed bond-gap range remain unqualified.
As a volume check, ideal quarter-circle6mm fillets consume about6.03mL over
the six130mm external sides and5.07mL over the six109.4mm internal sides,
before flat/end films and process losses. The budgets remain estimates, not
weighed assemblies or an epoxy density/coverage certification.

The load routes are **parallel**, with no assumed equal sharing:

- Panel → integral tab → mount flat/fillets → paper motor tube → ring bore
  bonds → rings/perimeter bonds → body.
- Panel/root → external fillets → paper body → connected rings/body structure.
- Tab aft face →0.4mm end film → aft annulus → body/mount bonds. This route
  exists physically but has no qualified stiffness or capacity; no fixed
  aft-ring support is invented to complete the calculation.

Narrower tabs and6mm fillets leave a projected1.375mm gap to the unverified
50×20×14mm knot box at60deg after a0.2mm geometric allowance. Wrap-to-tab
axial separation is3.05mm under the declared stack. The sleeve still ends
ahead of the ring. These are corner/station projections, not actual dressed
knot geometry, a full motion sweep, packing, assembly or hot-clearance proof.
The bore, liner and independent motor-removal/retainer layout stay unchanged;
missing exact motor/retainer dimensions are not resolved by this study.

Install/inspect the loop and forward ring before the integral fins. Keep the
aft ring off while internal films/fillets, cord and cure witnesses are visible;
install it only after inspection. Rounded/sealed carbon cut edges and wiring
clearance need verification: conductive carbon/finish receives no electrical,
abrasion or heat credit. Removing wood wedges and changing conduction/contact
paths requires later thermal revalidation, not transfer of old temperatures.

## Complete proposed ledger and coupled checks

| Construction item | AD1 mass | FR1 nominal mass | Accounting |
| --- | ---: | ---: | --- |
| External panels |78.832g |84.696g | Finished laminate nominal density/thickness |
| Integral tabs |25.918g |27.641g | Separate mass region of same three blanks |
| Six wooden wedges |26.277g |0 | Intended replacement by carbon/root construction; **not admitted saving** |
| Wedge bond/finish + slot increment |4.150g |2.000g edge finish | Wedge-only function removed;14/10g main bond budgets retained |
| All remaining parts | unchanged | unchanged | Motor, shields, harness, avionics, recovery, guides and service items retained |

Net proposal change is **−20.839669g**, physical nominal ledger863.709549g,
53unique rows. Because installed support fails, the removed wedges' complete
function has **not** been demonstrated transferred; do not adopt the saving.
The wood sheet69.75dollars is still required for rings/nose and is reallocated
from fin_set to forward_ring. Add the full carbon sheet once. Total estimate
is **$585.43**, before shipping/tax/tests and still budgeted purchases, not owner
stock. Full50g is added at1250mm separately; adverse adds20g there and the
12.8mm motor-CG probe. Nothing consumes the growth allowance.

| Stock thickness / main | Case | Total incl50g | CG | Static margin |1.5m speed | Formal / planning headroom |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
|3.175mm /55g estimate |Nominal |913.710g |755.137mm |1.561cal |15.405955m/s |+44.634 /−9.910g |
|3.175mm /55g |Adverse |933.710g |767.495mm |1.376cal |15.220563m/s |+24.634 /−29.910g |
|3.175mm /68g probe |Nominal |926.710g |749.314mm |1.649cal |15.284786m/s |+31.634 /−22.910g |
|3.175mm /68g |Adverse |946.710g |761.624mm |1.464cal |15.103170m/s |+11.634 /−42.910g |
|3.429mm /55g |Nominal |922.696g |758.915mm |1.505cal |15.321933m/s |+35.647 /−18.897g |
|3.429mm /55g |Adverse |942.696g |771.074mm |1.323cal |15.139134m/s |+15.647 /−38.897g |
|3.429mm /68g |Nominal |935.696g |753.095mm |1.592cal |15.202473m/s |+22.647 /−31.897g |
|3.429mm /68g |Adverse |955.696g |765.210mm |1.411cal |15.023333m/s |+2.647 /−51.897g |

Formal threshold15m/s and separate planning15.5m/s are unchanged. All eight
declared cases pass formal under assumptions; all miss planning.55g is an
unverified finished-main estimate,68g is a nonbinding metadata probe, and neither
is a measured bound. At maximum stock, the adverse68g case has only2.647g left;
roughly2.2percent additional plate density would consume that. Nominal density
has no verified manufacturing range. A complete weight pass remains conditional.
Conditional1.8m speeds and each recalculated recovery demand are in the record;
equipment is unconfirmed. Nominal-thickness55g whole mean proxies are
1928.128/1970.333N; body proxies1314.750/1356.955N, with20.4m/s/.3m/DF3once
unchanged. Nothing infers peak opening load or actual stretch.

Planform/positions/body are unchanged and the backend Barrowman calculation
returns the same859.442mm CP. At nominal stock55g, burnout margins2.002/1.794
and stated aft-stowage sensitivities1.441/1.258cal pass their calculated screen.
Thickness, removed protruding wedges and fillets change real aerodynamics;
the model ignores those local details. Reusing the0.8upper drag assumption and
small-angle coefficient is a screening hypothesis, not validated drag/CP.
Static RocketPy endpoints agree under common assumptions. Full physical inertia,
flight/altitude, installed vibration and flutter remain unavailable; no old
isolated-fin or old-support result is transferred.

## Executed structural checks, limits and stop

Minimum thickness2.921mm, retained8.83N·m and the interpreted45.947GPa reference
give an **ideal outboard panel** movement0.679522mm. This omits root movement.
At halfE the panel alone gives1.359044mm. Neither reference nor halfE is a
qualified hot-property bound, so no required strength/movement pass follows.

The short17.451mm tab uses standard Euler–Bernoulli compliance with finite
mount translation/rotation and body translation springs. The actual tube's
polarJ is2.3991e−8m⁴. Estimated paperE500MPa/ν.3 givesG192.308MPa; torsion to
the two ring centres gives146.468N·m/rad **only with ideal end rotations**.
Actual ring/bond/body flexibility is not zero and may soften it. Body springs
0.1–100MN/m and mount springs1–10MN/m are sensitivities, not measured bounds.
They produce **1.185–8.176mm total** at the referenceE, and2.159–9.894mm at
halfE. All fail1mm. The fully rigid boundary diagnostic gives0.901mm at the
referenceE; it is not installed evidence. Peak required tab bending stress in
the finite sweep is76.111MPa, already factored, against **no qualified hot
laminate allowable**. No raw-fiber or E-glass strength is substituted.

Body peak reaction847.748N over the actual minimum one-face129.9×5.8mm
contact gives **1.1252MPa**, exceeding unchanged1MPa shear screen. The original
record's1.337MPa uses only109.4mm overlap; the supplement clearly corrects its
scope.70/30 and equal sharing are diagnostics, not demonstrated splits; normal
peel and paper interlaminar capacity remain unknown. Increasing a leg alone
does not solve total movement or unknown finished capacity, so no such revision
is executed.

The aft end has50.682mm² minimum area: a mean1MPa shear screen corresponds to
50.682N. A rectangular elastic pure-rotation film gives0.1466N·m and a
same-direction full-traction inner-edge moment bound0.4397N·m. An illustrative
G100MPa/0.4mm film would give317.88N·m/rad **against an ideal rigid ring**;
thatG, the actual annulus/support and mixed-mode strength are unqualified.
The short-tab sensitivity therefore does not credit that extra rotational
route. It is not a complete installed displacement prediction or a proof the
physical design is impossible. A passing complete-path result remains absent.

Independent force/moment cantilever and fixed/pinned beam answers, reciprocal
work/positive compliance and force/moment balance checks pass. Outboard
quadrature is refined100/400/1600divisions. These verify elementary calculations,
not materials, installed joints, constitutive laws, modes or flutter. No CAD,
mesh, FEA, custom thermal campaign or stopped calculation was repeated.

Two pre-execution adapter failures are retained: tuple bbox assignment, then
the schema's missing nonmetallic `carbon_epoxy` tag. They occurred before
arithmetic. The tag now names solid nonmetallic carbon/epoxy; it grants no
capacity and does not permit metal fins. The one completed packet used
1.191CPU/1.951wall seconds,8vehicle cases/16guide calls; thread settings1,
affinity unverified. The joint supplement reused saved outputs without new
guide/beam cases. Source records and executed producers are preserved.

The raw mass-model snapshot retains legacy CAD placeholders/material-profile
labels; they are not accepted carbon properties or build dimensions. The
linked connection definition/study controls this stopped proposal. Normalize
the complete specification and CAD only after a credible design is admitted.

## Required evidence and next decision

No installed requirement closes. The completed items are load-provenance
correction, one dimensioned/fully counted proposal, conditional fit/static/guide
screens and numerical-method checks. The next decision is **which explicitly
justified fin-load envelope governs this60mm G80**, followed by exact finished
laminate and installed-joint properties. Do not start another local reinforcement
without settling those inputs. The original8.83case stays in force meanwhile.

Supplier documents could establish units, bendingD/E, tested strength, hot/wet
retention, tolerance/density and cure. Later owner-authorized coupons and an
installed fin/mount/body/aft-ring specimen must measure load–displacement,
root rotation, asymmetric reactions, peel/paper failure and temperature effects;
then installed modal/flutter and operating-envelope validation. The RP1 cord
coupon plan stays separate. No hardware exists to measure now, no supplier
question is sent and no purchase/build/test/flight authorization follows.
