# G54 support axial free-body cuts

**Result: equilibrium narrows the combined axial force but does not determine
the shell's share or close the support.** At the source's 0.135 s G54 peak,
assuming the entire motor-to-structure resultant enters at the nominal motor
front, the bounded net force across the complete non-motor section changes sign
across that contact. For example, at 1.006 m the force on the forward piece is
**+51.682 to +73.091 N**; at 1.020 m it is **−51.846 to −34.907 N**. Positive
means noseward force on the forward piece; negative means aftward. These are
intervals for **all non-motor material paths together** in both the nominal
extent and placed STEP BRep extent models. They are not shell stresses,
measured contact, or an installed capacity result. They use the source's rigid,
vertical, no-drag axial force idealization; wind, drag, bending and local forces
are not resolved. Gravity is included in the supported inertial-plus-weight
demand, as described below.

## Exact source and what it retains

This is candidate `69df790ec9bcba1465be4fa9861a7ad5fbc467091cbf58f44dee069e56e00bac`,
file SHA-256 `c80a6d4f563c6c99c92ba7acbbc9ad4b6a0fa0655166f71bbf5a618959e32535`,
and the published [support audit](wo03-support-closure-audit.md), not a new
vehicle or a compatible completed recovery package. Frame rings remain 3 mm
thick at local 0, 55, 110, 148.5 and 187 mm, Ri 15.8 mm and Ro 31.82 mm;
mean radial bond gap remains 0.68 mm. The five ring bond areas and thermal
contacts are unchanged. Force and property screens retain design factor 3,
2 MPa estimated paper strength and 5 MPa hot plywood estimate. All earlier
thermal, structural, recovery and guide failures remain open.

The frozen audit scans the source motor curve with a 1.15 thrust multiplier,
impulse-based motor depletion and the full 50 g growth allowance. At 0.135 s:
thrust 139.9688 N; remaining motor 189.707 g; total 887.517 g; effective axial
specific force T/M **157.7084 m/s²**. This is the inertial-plus-weight demand
per unit mass, not kinematic acceleration. For vertical motion with no drag,
kinematic acceleration is T/M − g = **147.9017 m/s²**, using standard gravity
9.80665 m/s² (`src/sim/frames.py`); each part's support demand is
`m(a_kin + g) = mT/M`. It computes the motor resultant as 139.9688 minus motor
inertial-plus-weight demand,
**110.0505 N**. The equal and opposite interaction is counted once as an
external load on the non-motor free body. The motor and non-motor global force
residuals are less than 4e−15 N. Its 58.2161 N forward-growth joint result is
the published *whole-part start-station grouping*, not a measured shell traction:
the coupler and joint-stop span the 0.922 m joint plane.

## Placed geometry screen

A hash-checked screen of all 170 placed STL meshes found two vertices beyond
their nominal part intervals by more than 0.001 mm. That tolerance is for float32
coordinate comparison; it is not a bound on tessellation error. Hash-verified,
valid STEP BReps for the two flagged parts confirm nose cone **0–170 mm** versus
nominal 0–140 mm, and recovery anchor **215–231 mm** versus nominal 215–230 mm.
Both lie wholly forward of every support cut (first cut 922 mm), and remain fully
forward mass contributions, so these two discrepancies do not change the
reported forces. The other 168 meshes show no larger extension, but a vertex
screen cannot establish continuous BRep containment.

A separate bounded run checked **all 170 placed STEP hashes and BRep validity**
and calculated each CAD axial bounding box; every source centroid lay inside its
box, with no clamping. Applying the same mass/centroid ledger and contact/growth
assumptions to those BRep intervals produces the same nine cut bounds to within
1.5e−14 N. These are bounds for the **represented CAD shapes and source mass
model**, not as-built hardware; purchased and soft-stowage shapes, masses and
centroids remain unmeasured estimates. The nose shoulder does not change the
specified aerodynamic geometry length. The one-CPU STEP run took 6.58 s wall,
3.42 s user and 1.71 s system under a 60 s cap. Per-part STEP hashes and bounds:
`build/wo03-support-cutloads-v1/all-step/step-progress.jsonl` (SHA-256
`7c9a0e196c4224589f9f3d6e7ec65efec582ff29b25ad2656c69bfde0c8d6fa7`).
The separate STEP result is `build/wo03-support-cutloads-v1/all-step/step-cutloads.json`;
the exact executed script is retained as `executed-source.py` beside it. The
earlier STL screen and nominal result remain preserved.

## Method, station results and limitations

Take x from the nose towards the tail. Treat the entire motor as a separate
free body. For a cut of **every non-motor part** at station x, the noseward
force applied to the forward free body is `Fcut = (T/M) Mforward − Cforward`,
where `Cforward` is 110.0505 N if the assumed point contact at 1.013 m is
forward of the cut, otherwise zero. This cut includes parts that cross the
plane, including the frame, shell, coupler, shields and any other material;
it does not assume those crossing parts all load the shell. The nominal motor
front position is a bookkeeping assumption: exact shoulder/closure, axial
contact location, friction and multiple contact reactions remain unverified.
Moving or distributing that load can change the station results. No force at
the contact is reported as a unique cut value.

For each of 169 non-motor parts, use its source mass and axial centroid. The
first case uses source position and nominal length (or bounding-box length);
the second uses verified placed STEP BRep axial extents. If a cut is
inside `[l, r]` and the centroid is `c`, nonnegative mass and its first moment
bound the fraction forward by `max(0,(x−c)/(x−l))` and
`min(1,(r−c)/(r−x))`. Fully forward or aft parts contribute their full mass or
zero. This is an interval enclosure, not a reconstructed distribution; it
depends on the chosen extent and mass/centroid in the source and can be broad.
The unlocated 50 g growth is included exactly once, between zero and all forward
of each cut. Rows are separate bounds; they are not simultaneously independent
load cases. The JSON includes the full per-part ledger and input hashes.

| Station x (m) | Location | Combined cut force (N), noseward positive |
| --- | --- | ---: |
| 0.922 | joint plane | +46.940 to +58.204 |
| 0.990 | first ring front | +51.277 to +61.218 |
| 1.006 | ahead of motor front | +51.682 to +73.091 |
| 1.020 | aft of assumed contact | −51.846 to −34.907 |
| 1.0465 | ring 1 midplane | −51.588 to −33.138 |
| 1.1015 | ring 2 midplane | −49.844 to −14.161 |
| 1.1400 | ring 3 midplane | −45.575 to −4.802 |
| 1.1785 | ring 4 midplane | −33.839 to −4.406 |
| 1.195 | near aft mount | −31.186 to −3.682 |

These are bounded inertial partitions for the resolved mass copy, including the
fin set and all shields; they are not exact traction integration or a detailed
finite-element result. The extents and centroids need confirmation against the
actual geometry and purchased hardware, and a modeled connection must account
for the inertial-plus-weight demand of each separate crossing part. A rigid-body
idealization neglects elastic wave effects. The motor thrust history is a source hypothesis, not measured
as-built forcing.

The gross shell-only screen in the published audit applies the **entire
110.0505 N** motor resultant at one shell section and gives DF3 **3.20887 MPa**
versus 2 MPa. It remains a failed conservative *all-transfer scenario*, not a
resolved local force or a universal upper bound on a shell force: counteracting
internal paths could make an individual path larger than the net cut. Likewise,
substituting the 58.2161 N joint grouping at every section is invalid. For
illustration only, assigning the entire 1.006 m combined cut to the gross shell
would give DF3 **1.507–2.131 MPa**, straddling the 2 MPa estimate; this is an
enclosing scenario, not proof either endpoint is physically attainable. Actual
shell force, three-rail force, individual bond loads, local load introduction,
peel, ovalization and upper-joint load paths require finite, source-supported
rail/ring/bond/shell/joint stiffness and interface assumptions. These values are
`null` in the output: no ideal ground or unsubstantiated stiffness is supplied.

## Reproduction and checks

Run `.venv/bin/python scripts/wo03_support_cutloads.py --output <new-directory>`;
it refuses an existing output directory and checks candidate, motor-curve and
published-audit identities. The completed output is
`build/wo03-support-cutloads-v1/all-step/cutloads.json`; the earlier
records are preserved, including the superseded `acceleration_m_s2` label. To
repeat the bounded geometry screen, add `--geometry-screen` and use one CPU and
a 60 s wall cap; it only opens STEP files flagged by the STL comparison. The
separate `--all-step-screen` option reads every STEP and appends a partial
per-part record before each next read; run only with a declared budget. Two tests use
a self-contained synthetic ledger and independent simple first-moment bounds,
mass and motor equilibrium, the change across the assumed contact, and null
shell shares. The actual-candidate result is manual recorded evidence, not a CI
test requiring ignored data. No FEA, flight run, design
adoption, property increase or physical qualification is claimed.
