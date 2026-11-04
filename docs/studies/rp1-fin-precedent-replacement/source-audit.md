# RP1 AD1 v2 current fin model and replacement ledger audit

Read-only arithmetic audit; no design adoption, supplier qualification, installed-joint pass, flutter result, or flight/WO-03 acceptance. The v2 saved producer reuses the v1 strip results; it does not rerun them. Source identities are in the companion JSON.

## Load provenance and consistency

The 40 kPa / 5° case is the `bounded-40kpa-5deg` upper sensitivity at 5° only in `configs/studies/wo03-fin-design.yaml`, not a validated load envelope. The 8.830347836 N m and 220.7586959 N per fin are already DF3 once in `configs/studies/wo03-c1-attachment-source-lock.json`: they belong to the earlier 90 mm span, 120/60 mm chord planform, area 0.0081 m², centroid arm 40 mm. Keep this inherited demand as an explicit conservative design case, not as a recalculation of the current geometry.

Current RP1 geometry is three fins, span 60 mm, root/tip 130/65 mm, sweep 45 mm. For uniform normal pressure over the trapezoid, A = 0.00585 m², AR = 2s²/A = 1.230769, slope = 1.778407/rad, and q × slope × alpha × 3 = 18,623.43 Pa; integration yields 108.9471 N, centroid arm 26.6667 mm and 2.905255 N m. The strip code instead rescales its entire moment distribution by 8.83/2.905255 = 3.039320, to preserve the separately inherited rounded moment. Its claimed 'tiny rounding difference' is false. The resulting implied distributed resultant is 331.125 N, 1.5 times the earlier 220.759 N force. Do not describe either 331.125 N or the scaled 8.83 N m as the direct current-planform 40 kPa case. A replacement must explicitly screen both at least 8.83 N m and 331.125 N with consistent load path; no second factor of three. No relaxation of either demand is implied.

For x radial from root, s = 0.06 m, c(x) = r + bx, b=(t-r)/s, and w(x)=p c(x), M(x)=p[r(s-x)²/2 + b(s³/3 - xs²/2 + x³/6)] = p[c(x)(s-x)²/2 + b(s-x)³/3]. This is the correct integral of w(u)(u-x) over x..s; V(0)=p A and M(0)=V(0)s(r+2t)/[3(r+t)]. The virtual-work deflection integral ∫ M(x)(s-x)/(E c(x) h(x)³/12) dx is correct for the *assumed* strip model, not a validated plate or joint.

## Bending and root

At 5.8 mm minimum thickness (nominal 6 mm, 5.8–6.2 is a proposed inspection range, not confirmed tolerance), E=1 GPa and strength 5 MPa are estimated hot screening inputs. Code sets h=5.8+12 max(0,1-x/15) mm: it treats two 6 mm-base gussets as a perfectly bonded full-width rectangular section, tapered to zero at 15 mm, with the fin modulus throughout. The real six wedges are triangular, 15 mm radial × 6 mm base × 130 mm axial. Composite rectangular-section behavior, load sharing, grain and bond shear are unverified; clamp alone does not make the full model a proved physical lower bound.

At 1600 divisions, idealized gusset case deflection 1.805416 mm and peak strip stress 7.301269 MPa both fail the 1 mm and 5 MPa screens; bare panel 3.988119 mm and 12.114699 MPa also fail. These are screen outputs, not installed predictions. Finite rotational root stiffness adds 8.83 × 0.06/K meters to the strip tip displacement if the ideal elastic spring is independent. A positive finite K cannot rescue a panel that already exceeds 1 mm; required K expression is undefined in this case. For K=200/500/1000/3000 N m/rad, totals are 4.4544/2.8650/2.3352/1.9820 mm. Translational joint compliance, nonlinear gaps, paper/tube distortion and adhesive peel are additional unmodeled terms; no K is established by the strip calculation. No front-ring tab support is present; aft tab ends at 1189.6 mm, ring begins 1190 mm (0.4 mm gap), and aft connection is adhesive, not direct butt contact. Root bending stress, joint loads/peel, assembly and flutter remain independently open.

## Replacement accounting

All entries below refer to the existing three-fin assembly, in grams; stations are axial CGs aft of the nose. Sum is 159.026489 g, an accounting envelope only, not a guaranteed removable credit:

| Record | g | station m | Scope |
|---|---:|---:|---|
| fin_set | 78.831677 | 1.145556 | Three external panels; excludes tabs |
| fin_tabs | 25.917587 | 1.135100 | Three integral blank tabs, counted separately |
| root_gussets | 26.277226 | 1.140000 | Six wedges |
| fin_internal_bonds | 14.000000 | 1.135000 | Tab/tube/body and tab end; retained installation reserve |
| outer_fin_fillets | 10.000000 | 1.140000 | Fin/body fillets and slot seal |
| root_extra_bond_finish | 4.000000 | 1.140000 | Gusset adhesive/sealer increment |

Remove a ledger row only where the proposed replacement actually eliminates its complete physical function and define/count all replacement panels, integral tabs, gussets, bondlines, closeouts and process excess once, at their own CG stations. `ring_bonds` 10 g supports ring/body, ring/mount and recovery-related functions, and must not be credited as fin-only. Retain `c1_forward_root_bond_fill` 0.763109 g, `c1_aft_bond_fill` 0.145896 g, and `ad1_slot_fill` 0.15 g unless exact replacement geometry and functions substantiate a change; some are installation reserves. Global `finish` 12 g is not fin-only and is excluded. Changes to slots, body, ring or mount need their own complete replacement accounting; existing frozen assumptions do not grant removal or installed load credit.

## Exact reuse path

`src.vehicle.schema.load_vehicle`, `src.vehicle.mass.mass_properties`, `src.vehicle.aero.center_of_pressure`, and `src.vehicle.benchmark.screen_launch` are the source helpers; `src.analysis.fin_attachment.normal_force_coefficient_per_radian` and `src.analysis.fin_design.planform_geometry` support geometry-specific scalar checks. Use a deep copied vehicle and a complete candidate part ledger; do not invoke the artifact-writing RP1 `main`. Recompute CP when shape, geometry or station changes. Replicate v1 script case accounting: nominal total = resolved mass + 0.050 kg; adverse adds 0.020 kg at station 1.25 m and shifts the actual motor CG 0.0128 m aft; all 0.050 kg allowance also at 1.25 m. Motor probe is a first-moment shift, not a second added motor mass. Compute loaded and propellant-subtracted burnout CG and margins with 0.066802 m diameter, plus the saved separate aft soft-stowage sensitivity. Call `screen_launch(copy, study_nominal_mass_kg=total-0.05)` because it adds `design.mass_allowance_kg` itself; preserve 1.5 m, formal 15 m/s and separate 15.5 m/s planning thresholds. The 1.8 m option is conditional, not adopted. Any alternative nylon mass probe is separate and not a bound. Results remain estimated; hardware and installed properties unverified.
