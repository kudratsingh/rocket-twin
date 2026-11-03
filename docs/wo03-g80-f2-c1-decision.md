# G80-F2-C1 — connection decision and integrated fit proposal

**Decision: retain the fixed conventional F2 architecture; hold adoption.**
The recovery pull moves the blind-notch front web away from the aft fin tab.
Its axial force must pass through adhesive tension and side shear. Nominal
zero-intersection CAD never established a compression stop or positive recovery
capture. Finished eyes/washers, installed joint capacity and the current motor
contact remain unresolved. Do not thicken the ring, add brackets or claim that
numerical consistency resolves these connections.

The separately identified `G80-F2-C1-fit-proposal-v2` defines controlled cut/stock
windows, preserves the original conservative wood/tab mass allocations and adds
**1.190022g of epoxy**. It is not adopted, registered as a flight configuration,
or admitted to whole-vehicle CAD/FEA. F2/F1 and all earlier failures remain frozen.

## Complete coupled results

All rows include the full separate50g; adverse additionally20g aft and the saved
12.8mm motor-CG probe. Same historicalG80 thrust source, same external geometry/
aerodynamic hypothesis, unchanged1.5m usable reference. No longer equipment is
confirmed or adopted. Positive headroom is conditional on that launch model.

| Case | Total,g | CG from nose,mm | Static margin,cal |1.5m,m/s | Formal15 headroom,g |15.5 planning headroom,g | Required whole mean proxy,N |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FrozenF2 nominal |917.560 |773.559 |1.286 |15.370 |40.784 |−13.761 |1936.253 |
| FrozenF2 adverse |937.560 |785.473 |1.107 |15.186 |20.784 |−33.761 |1978.458 |
| C1 fit proposal nominal |918.750 |773.707 |1.283 |15.359 |39.594 |−14.951 |1938.765 |
| C1 fit proposal adverse |938.750 |785.603 |1.105 |15.175 |19.594 |−34.951 |1980.969 |

The separately executed [burnout check](../runs/wo03-g80-f2-c1-burnout-20261103-v1/record.json)
adds the previously omitted sensitivity at burnout: proposal856.250/876.250g,
CG745.803/759.183mm and margins1.701/1.501cal. It retains the saved loaded-motor
mass moment probe at burnout, conservative versus translating only the dry motor;
actual motorCG remains unknown. This static arithmetic took0.162s, with no full
flight or changed requirement. The source hashes match the final proposal.

The conditional1.8m proposal predicts16.827/16.627m/s. Static RocketPy endpoints
pass the existing comparison; no new full flight ran. Full physical rotational
inertia remains unavailable. No ballast, hardware, recovery or growth mass was
removed. The53-row proposal ledger comprises50 previous allocations plus three
positive adhesive increments; it is not53 qualified CAD parts. The complete
proposal cost remains an estimate, with all purchases/physical work gated.

The [v2 arithmetic record](../runs/wo03-g80-f2-c1-load-path-20261103-v2/record.json)
completed in1.483s after schema/setup and font-cache failures were preserved in
v1. The [final definition](../runs/wo03-g80-f2-c1-definition-20261103-v1/record.json)
reuses these valid cases after checking exact mass/CG/diagnostic inertia/CP
identity: explicit CAD parameters, unavailable-generator labels and source
narrative corrections introduce no new solved physics. Both source versions
and producers are retained. Current proposal is
`configs/vehicle/candidates/g80-f2-c1-fit-proposal.yaml`; its full SHA is in the
record. Do not use the frozenF2 localSTEP or diagnostic fields for this proposal.

## Dimensioned interfaces and clearances

The old generic0.1mm linear tolerance is ambiguous about radius versus diameter.
For an old64.6mm ring in proposed bodyID>=64.9mm, the original worst cold gap is
0.05–0.10mm depending on that interpretation; another0.05mm differential closure
leaves0–0.05mm, below0.1. It was not a qualified fit.

The following are **proposed incoming/cut acceptance windows**, not supplier
manufacturing tolerances or measured environmental properties. The extra±0.05mm
conditioning/thermal allowance is still an unverified bound. Actual stock/coupon
measurements outside it require correction and revalidation.

| Interface | Proposed dimensions,mm | Min/nom/max gap,mm | Calculated role/status |
| --- | --- | --- | --- |
| Forward/aft ring to body | RingOD64.40±0.05; bodyID64.90–65.15 |0.175/0.312/0.450 | Conditional radial fit≥0.1; actual wood/paper conditioning unknown |
| Ring to motor tube | Bore31.90±0.05; mountOD31.25–31.45 |0.150/0.266/0.400 | Incoming mount window unverified; not a manufacturer tolerance |
| Nose plate to shoulder | PlateOD61.00±0.05; bore61.50–61.70 |0.175/0.300/0.425 | No accepted printed/conditioned bore yet |
| Tab inner flat to mount | Flat radius15.950±0.025; same mount bounds |0.150/0.266/0.400 | Curved edge gap larger; adhesive volume/peak stress still need local definition |
| Notch sides | Slot6.60±0.05; ply5.8–6.2 |0.125/0.300/0.475 **per flank** | Total clearance is twice these values; not an interference-fit capture |
| Tab front end |1080.20±0.05; notchfloor1079.80±0.05 |0.250/0.400/0.550 | Filled bond, not a direct compression stop under recovery pull |
| Tab aft end |1189.60±0.05; aft-ringfront1190.00±0.05 |0.250/0.400/0.550 | Filled bond; no bearing credit across an adhesive gap |

Notchdepth7.4mm/frontweb4.8mm, angles0/120/240°, and eye-hole4.5mm atR23mm,
30/210°, now live explicitly in the proposal's CAD parameters. The notch/tab
CAD generators are labeled unadmitted; no cylindrical envelope masquerades as a
completed slotted joint. The old forward-ring13mm learning text is corrected to
**two6mm plies+0.2mm glue=12.2mm**. Pair-eye coordinates are explicit while the
inherited single hardware box remains an envelope with no actual pair geometry.

## Actual force routes and remaining connections

```text
Canopy → cord / junction → body bridle → two finished eyes (unknown capacity)
                                      ↓ nuts / washers on ring's aft face
                                 forward ring bends / shears
                        ┌────────────────┼─────────────────┐
                 outer ring bond    inner ring bond    notch side/floor bonds
                        ↓                ↓                 ↓
                 fore paper body   motor tube/long     integral fin tabs
                  + fixed splice   tab bonds/retainer   + aft ring/body bonds
                        ↓                ↓                 ↓
                    retained masses and distributed inertia

Separate nose branch → nose eye → plywood annulus → perimeter bond
                     → printed shoulder/carrier → retained nose/electronics

Motor thrust / reverse retention → exact shoulder/cap contacts (unresolved)
                                 → tube/retainer bonds → rings/tabs/body
Fin bending/twist → panel/gussets/root → tab and body bonds → rings/body
```

A recovery force applied to the ring noseward opens the front notch-floor gap.
That surface can carry adhesive tension, not contact compression. Side bonds
carry sliding shear. Their actual stiffness, mixed-mode peel and temperature-
conditioned capacity are missing. Fin/root moment8.83Nm remains already factored;
no second factor is applied or old isolated-panel result transferred. The ring
support springs in the local diagnostic omit these installed joint compliances.

For the explicitly defined **fore-paper branch**, known attached mass148.267g
plus0–38g uncertain finish/service/bond/shield allocation requires312.877–393.065N
under the frozen required common-acceleration proxy. Mean paper axial stress is
**1.700–2.135MPa** against the estimated2MPa scalar screen: the adverse bound
fails. This does not assert that all aft mass passes through the paper, or that
the scalar axial result covers eccentric bending/buckling/local peel. The nose,
soft goods, eyes and front motor-tube stub are excluded from this branch. Actual
spatial allocation and rotational dynamics remain open.

The provisional14OD/4.5ID washer area is138.034mm². FrozenF2 body demand1408.793N
gives mean contact pressure7.144MPa at70% loading or10.206MPa single-eye. Maximum
contact pressure cannot be smaller than its mean. A5MPa scalar comparison needs
at least281.759mm², but5MPa is **not** a product-specific transverse wood-bearing
allowable. No uniform spreading, rigid washer or finished strength is proved.
The new proposal's slightly higher body force must be used for any actual design.

Independent motor removal and harness passage stay protected. The10g shield is
a sector reserve; its inherited annular display envelope intersects the tube.
It must not become a physically occupied thermal region. Exact motor/retainer
contact and shield termination are still unknown, so no thermal rerun is admitted.

## Numerical outcome — four distinct checks

| Check | Result | What it establishes |
| --- | --- | --- |
| Known answers | NewTRI6 force/first moment error<1e−12; saved axial2.23/Spring1 evidence reused | Load integration and existing element/units path, not strength |
| Valid3/2mm meshes |30,144/80,858nodes; affine quadratic mapping, positive Jacobians; volume errors0.042/0.024% | Valid polygonal approximations for those grids |
| Completed calculations | Force/moment/work/reciprocity errors<2e−8 | Discrete calculation consistency, not realistic installed supports |
| Fine volume-partition attempt | Node limit reached before solver; exact count unavailable | Resource stop, no fine temperature/stress answer |
| Boundary-only replan |139,953nodes>100000; solver not run | One defined correction also exceeded the unchanged cap; no retry |
| Three-grid accuracy | **Unavailable** | Two valid grids differ little, but the required third result is absent |
| Installed strength | **Unresolved/adverse diagnostic** | Generic isotropic5MPa comparison does not establish actual wood/bonds/eye capacity |

At100N component load, the2mm fixture gives maximum displacement0.11346/0.16643mm
and volume-weighted95th principal stress0.5822/0.7841MPa for70/30/single-eye.
The fixture's springs are hypothetical grounds; no reaction percentage is
accepted as actual global mass sharing. Scaling beyond the estimated strength
screen is a diagnostic, not a physical deformation prediction.

The [export metadata](../runs/wo03-g80-f2-c1-field-export-20261103-v1/metadata.json)
indexes existing two-phase nodal displacement and four-Gauss stresses in an
ignoredNPZ. It refers to the frozen32.3mm-radius F2 ring, **not** the32.2mm proposal.
Active compatibility and installed acceptance are false. No analysis field is
registered with the active viewer. The numerical route is stopped for this packet;
no new fine grid, larger cap or solver project follows automatically.

## Recovery mechanisms: preserve the required case

[The source note](wo03-f2-c1-recovery-mechanisms.md) distinguishes canopy inflation,
line-snatch between free sections, and prescribed whole-vehicle arrest. For the
proposal, the unchanged required whole-case proxy is1938.765/1980.969N. A separate
ideal two-free-body comparison at the **same assumed20.4m/s relative speed** and
0.3m relative stroke gives311.015/313.174N (DF3 once, soft-goods engagement absent).
The existing point-drag canopy hypothesis at20.4m/s/rho1.225 gives84.458N drag,
or253.374N withDF3. These are different mechanisms, not lower replacement loads
or validated peaks. Actual relative separation velocity, force/stretch curve,
canopy inflation and transient peak remain unmeasured. Current evidence justifies
separating the cases; it does not silently revise the required severe screen.

## Closure and next bounded decision

| Issue | Implemented / proposed correction | Criterion/result | Remaining verification |
| --- | --- | --- | --- |
| Conflicting ring description | Explicit12.2mm/source CAD parameters | Source-definition conflict corrected in new proposal | Local jointCAD and physical stock still required |
| Unspecified tolerance stack | One connected OD/bore/notch/end proposal | Seven conditional minima≥0.1mm; not adopted | Actual measured stock, conditioning and installed strength |
| Uncounted fit adhesive | Three positive increments, zero wood credit |+1.190g; coupled formal guide/static pass, planning miss | Process excess and measured completed mass |
| Blind-notch load route | Identify tension/shear rather than contact stop | Actual force direction is explicit | Mixed-mode joint/retention definition and finite support evidence |
| Invalid old ring mesh | Affine quadratic meshes; pressure footprints | Two valid solves; fine attempts capped | Required3-grid criterion still open; no strength closure |
| Motor/retainer and finished eyes | New bounded supplier matrix | Exact contact/capacity still missing | Identified component drawings or owner measurements, later proof |
| Thermal/fin/flutter | Preserved open findings | No accepted new result | Existing expandedWO03 and later owner test gates |

**No installed engineering strength or thermal requirement closes.** What became
more buildable is an explicit cut/fit definition with counted glue and corrected
joint/learning descriptions. The controlling physical issue is the complete
recovery anchor → ring → bonded tab/body route. Before another reinforcement,
select actual finished attachment/harness data and substantiate its load cases
and joint transfer. If the bonded tensile route cannot meet the unchanged cases,
a positive through-ring retention detail needs its own complete limited preflight;
do not start another bracket sequence or assume a blind notch is captured.

Only owner involvement currently sought is whether exact hardware already exists.
If so, the supplier note lists external dimensions to record; no motor opening,
purchase, fabrication, proof/deployment or firing is authorized here. Normal-
terminal preview startup and designated browser ownership remain separate needs.
G54/G12 PID-to-RL, fullWO03/04/05, purchase/physical/paid/firmware/flight gates remain.
