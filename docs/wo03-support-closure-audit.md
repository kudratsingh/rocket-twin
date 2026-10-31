# WO-03 complete support and independent-recovery audit

**The selected package is not structurally closed.** This bounded audit closes source/force-accounting and current-section subitems, but retains failed recovery screens and unavailable interface capacities. It does not substitute frame-only buckling for the ring/bond/shell/joint path, combine incompatible prototypes, or select another design family.

The completed calculation is `build/wo03-support-closure-audit-v1/completed/audit.json`, run `wo03-support-closure-audit-20261031T071937512739Z`: **2.010 s**, one CPU, $0, unchanged recorded inputs, no FEA or flight run. It uses two local BRep rail slices only. The first attempt stopped at a recovery-file identity guard; its failed `record.json` and `worker.log` remain at the output root. No failure was erased.

## What closes, and at which identity

| Subitem | Exact result | Closure limit |
|---|---|---|
| Current fitted G54 geometry | Candidate `69df790ec9bcba1465be4fa9861a7ad5fbc467091cbf58f44dee069e56e00bac`, from `runs/wo03-baffle-fit-20261031T035358211715Z/resolved-candidate.json`; normal schema/cache validation passes | No complete independent-recovery package is integrated into this thermal copy |
| Two brace rings and structural bore | Five 3 mm rings at local 0/55/110/148.5/187 mm; **Ri15.8 / Ro31.82 mm** | The 95.1% stiffness loss of the rejected **Ri24.8** six-layer trial does not apply here. Current simple unperforated-ring stiffness ratio is **0.9780** of the old R32 reference; this is not an assembled restraint or eigenvalue pass |
| Actual current rail section | Full section **79.565 mm²**, weak I **292.626 mm⁴**; fin-channel section **43.429 mm²**, weak I **158.005 mm⁴** | Nominal section integrals do not rate notches, laminate directions, ring joints or hot defects |
| Original frame-only buckling | Source YAML SHA `df3e9e9bc289f175666138b2c0b9bfa274550639a641dc495094549c347e5b89`; resolved spec `77a4a467…`; factor **3.743855**, required 3, last mesh change **1.463%** | Belongs to its original R32 frame and ideal aft-ring support. No bond/body path or current-geometry pass is inherited |
| Recovery force accounting | Embedded G80/G54 source ledgers reproduce every branch load and balance with DF3 once and full 50 g aft growth | Force balance proves no installed capacity |
| Recovery file compatibility | All four mutable mass-copy hashes differ from the frozen `020015` record; explicit part IDs/masses still match its embedded ledger within rounding | Current aliases fail current CAD-cache validation (50/50/60/59 errors). No historical geometry pass is transferred to them. Frozen G12 cap/hoop file still matches its own `81529f6a…` identity |

The changing recovery aliases are therefore used only for an explicit identity/mass comparison. The audit recomputes historical recovery force arithmetic from the immutable **embedded branch ledgers**, without clearing stale caches or pretending the changed files are the recorded geometry.

## Complete fixed support path

The intended thrust path is motor shoulder → mica pads/G11 plate → finger bonds and possible plate-OD transfer → three rails/five rings → ring bonds and aft shell → finite module joint → upper body. Reverse motor inertia instead needs the aft retainer/blocks and positive hardware. Contact, interface splitting and actual joints remain part of the path.

Every current G54 thrust-curve knot is scanned with the existing **1.15 thrust multiplier**, impulse-based motor depletion and full 50 g growth. At the governing 0.135 s knot: thrust **139.9688 N**, motor mass **189.707 g**, whole mass **887.517 g**, net motor-flank load **110.0505 N**, and forward-growth upper-joint load **58.2161 N**. The smaller joint force is not used to clear the mount.

| Existing DF3 screen on current geometry | Calculated demand | Existing estimate / finding |
|---|---:|---|
| Equal-share rail axial stress | **2.5340 MPa** | 5 MPa plywood estimate: conditional gross-section pass |
| Full net-flank transfer through one gross aft-shell section | **3.20887 MPa** | 2 MPa paper estimate: retained conservative transfer screen fails |
| Upper-joint gross axial stress | **1.69747 MPa** | 2 MPa: small gross reserve only; local contact/peel/retention unqualified |
| Uniform mean shear over all five ring bonds | **0.11652 MPa** | 1 MPa estimate: conditional average pass |
| Uniform mean shear in only the smallest ring bond | **0.61098 MPa** | 1 MPa estimate: conditional average pass; normal/peel capacity unavailable |
| Pinned-column modulus needed, no effective braces / ideal braces | **2.389 GPa / 0.191 GPa** | Actual restraint is unavailable; 1 GPa hot estimate cannot be used with imaginary grounding |

The aft-shell row is an **existing conservative all-transfer envelope**, not an area-integrated physical cut traction or proof of actual fracture. Distributed inertia and real parallel load paths must determine the installed section forces. The audit retains both 110.0505 N mount and 58.2161 N upstream loads explicitly. Choosing the smaller one everywhere would hide transfer demand; declaring the larger one a resolved cut load would also overstate the evidence.

The full-transfer paper screen would require DF no greater than **1.8698** at 2 MPa; the required factor remains **3**. Original frame-only buckling would need at least **0.8013 GPa** under its own original geometry/support assumptions. These sensitivities identify decisions; they do not reduce the factor or qualify a modulus. Actual bond gap is **0.68 mm**, and material mean-gap contact areas are **606.202/606.202/540.360/540.360/540.360 mm²**. Uniform shear cannot establish hot paper tear, bond peel, local crush, shell ovalization or joint retention. No new small FEA patch could close those absent construction/property inputs, so none was run.

## Complete recovery path and retained failures

Canopy attachment → hot leader/main line → rounded junction → separate nose/body/coupler/sled branches and three aft legs → actual cap/plate → rails/rings/bonds/body and motor/fin retention. Each missing attachment capacity remains **null**, not zero or pass. The nine-piece/**18-end** plan and independent controller/cell/switch/carrier/wiring/mounts remain charged. The 200 mm end preparation is still an unqualified cutting envelope.

For the embedded G54 late 23.139 m/s, 0.3 m stopping-distance case, whole DF3 demand is **2,490.414 N**. Its branch forces are approximately **177.757 main, 100.082 nose, 297.348 body, 88.130 coupler, 309.190 sled and 1,517.908 aft N**. Removing foreplate inertia once leaves **1,388.822 N** in the retained all-through-rails screen, versus **660 N** at three 44 mm² plywood ends and the existing 5 MPa estimate. Required collective stress is **10.521 MPa**. No qualified alternate plate/bond/shell bypass exists to waive this screen.

An explicitly limited original-Package-A axial-support fixture balances the same aft load and foreplate inertia at the three recorded rail centroids. A single centered port gives **1,269.621 / 59.600 / 59.600 N** rail reactions. Moving contact to one hole side gives **1,269.621 / 218.374 / −99.174 N**; the negative reaction is compression/prying. Maximum force/moment residual is 7.28e-12 in its N/N mm equations. Clearing that fixture's largest axial reaction with 44 mm² needs **28.855 MPa**, beyond both existing 5 MPa hot and 10 MPa cold plywood estimates. This fixture is not an integrated baffle layout or a verified finite-plate model: radial rope force, bending/torsion, stiffness and actual interfaces remain unresolved. It shows why equal thirds are not automatically safe.

The collective 660 N bound alone would need **0.639 m** stopping distance in that late proxy. This is a sensitivity, **not** a measured stroke or approved replacement of the retained 0.3 m screen. Smooth inflation does not bound slack-line snatch. Junction/termination ratings, body-band load introduction, bulkhead retention, positive coupler pins, nose attachment and sled/cell/board retention remain unqualified. The body branch's retained whole-branch/one-section proxy is **2.868 MPa vs 2 MPa**; actual front/aft sharing and local load entry must be established before calling it a physical section result.

The separate G12 cap/hoop copy retains a 25-pose clearance result with original flat horns, but its rail proxy is **395.888 N** versus retained matched/single-leg screen values **784.951/1,031.959 N**. These are screening assignments, not a substitute for equilibrium. The separate geometry-aware curved-flange study exposes the between-rail ports' tensile/compressive reactions: up to **802.89 N tension** and **329.62 N compression**, with minimum area **27.419 mm²** against **32.115 mm²** needed for its largest axial case. Its pinned Rayleigh upper capacity **172.50 N** is below that compression. Actual bilateral body restraint/peel and cap one-route strength are still unavailable. This heavier failed family is not selected or substituted for the current copy.

## Mass boundary and decision-driving evidence

| Copy / ledger | Mass boundary | Result |
|---|---|---|
| Current fitted G54 thermal copy | **846.010 g loaded**, plus separate 50 g growth | Does not include the later complete direct-harness correction; not a combined accepted package |
| Embedded G54 recovery copy | Recovery baseline **111.034 g** + increment **52.144 g** = **163.178 g allocation** | Structure shared with the vehicle is counted once; its geometry is a different revision |
| Current G12 cap/hoop copy | **781.642 g vehicle**, plus 50 g growth; recovery increment **67.506 g**, total allocation **178.539 g** | Assumed 5 m guide: **10.14219 m/s** with no thermal addition; adding 8 g gives **9.98513 m/s**, fails 10 m/s |
| Unadopted G12 flange family | **15.403 g** added; recovery increment **82.909 g** | **9.84114 m/s** with no thermal addition; fails even before accepting thermal hardware |

The 2.111 g prospective rail saving is unadopted; with it, the cap/hoop 8 g thermal **mass probe** gives only 10.02642 m/s and 1.350 g margin. It is not compatible thermal hardware. Accepted pressure-seal credit remains **zero**. No G54 shield saving transfers to G12, no growth is consumed, and real 5 m usable guide equipment is still unconfirmed.

Decision priorities are:

1. **Select one coherent load-entry/joint/package identity.** Current G54 plate is 9 mm with 18 mm fingers; recovery correction changes that interface. Actual rail/ring/bond/shell and upper-branch geometry must be composed and checked before capacities can be combined.
2. **Paper and interface evidence controls the support decision.** Need chosen tube layup/lot and hot/wet axial, end-crush, hoop and interlaminar data, plus an actual transfer/contact model. The 3.209 MPa envelope is above the existing 2 MPa screen; supplier strength alone does not establish redistribution or peel.
3. **Recovery sharing and terminations control rail demand.** Need a specified, source-compliant end method/cut plan; measured prepared-line EA/length spread, hot/aged end capacity, abrasion protection, and a bounded opening/snatch force–stroke envelope. They cannot be replaced with bare-line strength or smooth drag.
4. **Hot plywood/G11 and adhesive bounds remain material-specific.** The retained fixed single-port fixture exceeds existing cold and hot plywood screens. G11 flexural data do not rate axial/bearing/interlaminar paths. Adhesive aluminum-lap typical values cannot rate hot wood/paper peel; actual preparation/cure/gap and mixed-mode evidence are needed.
5. **Exact motor and guide inputs remain gates.** Confirm G54 variant/case/closure/nozzle/CG and external temperature history, retainer/pin/hardware identity and positive retention, and the physical usable guide. Do not use a hypothetical longer guide or a weaker load criterion to remove the current failure.

These identify the next correction and evidence needed under [the fixed closure plan](wo03-closure-plan.md). They authorize no purchases, hardware work, paid runs or flight. Owner coupon/hot-assembly/recovery tests remain later qualification gates; unresolved design interfaces and numerical compatibility must be corrected before those tests can stand in for acceptance.

Reproduce the audit with `.venv/bin/python scripts/wo03_support_closure_audit.py --output <fresh-local-folder>`. Scoped Ruff/Black pass. Raw selected CAD, parameter comparisons, source hashes, failed aliases, exact branch inventories and unchanged-capacity findings are retained in the completed audit; no root status/specification or frozen thermal method was edited.
