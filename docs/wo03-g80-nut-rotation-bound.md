# G80 keeper: bounded nominal rotation, not a torque rating

The stopped keeper trial's **5° / 0.05 mm³ overlap probe is a diagnostic**, not
a project requirement that a captive nut have zero play at 5°. Its measured
0.008278 mm³ remains below that discrimination threshold and inconclusive.
Do not relabel that result as a pass or treat it as evidence of free spinning.

For ordinary cap service the geometric question is whether the nut can turn
continuously with the screw. The ideal source geometry supplies a separate,
closed-form bound: a nut in the declared across-flats range cannot rotate
through either **+15° or −15°** about its fixed axis without meeting the keeper.
This allows finite angular play; it establishes no allowable tightening torque,
manufacturing fit, vibration retention or physical qualification.

## Source-specific argument

The source recipe uses concentric regular hexagons: nut across flats 5.32–5.50
mm from the supplier range, pocket across flats 5.70 mm, and six 0.50 mm radius
tool-relief holes centered on the pocket vertices. The straight nut pocket
occupies z=166.5–168.9 mm; even the declared minimum nut/washer stack has
1.65 mm axial engagement. The larger washer counterbore is above that region.
The actual manufactured corner shapes and pocket tolerances are unverified.

At a 15° relative rotation a nut vertex has projection toward a pocket-flat
normal of `r_n cos(15°)`, where `r_n = AF_n / sqrt(3)`. The pocket apothem is
`5.70/2 = 2.85 mm`. Even the smallest declared ideal nut gives

```text
r_n(min)                 = 3.071503 mm
r_n(min) cos(15°)         = 2.966844 mm
projection beyond flat   = 0.116844 mm
```

The nearest tool-relief hole cannot remove this blocking vertex: for a point
on that 15° ray, its distance to the nearest pocket-vertex center is at least
`(5.70/sqrt(3)) sin(15°) = 0.851747 mm`, greater than the 0.50 mm relief radius.
Symmetry gives the same bound for negative rotation. The nut vertex is also
outside the 1.8 mm screw-tip bore. Its radial position lies within the keeper
annulus: the source axis at R25.5 plus/minus the largest nut corner radius is
22.3246–28.6754 mm, inside R15.8–32.2. Rail notches and M2 holes must retain
their separately checked source positions; this argument does not transfer to
a different pocket or a new overlapping cut.

Thus there is solid keeper material in the nut's path at the stated angle in
the ideal undeformed source geometry. A continuous centered rotation from its
installed position must encounter material before reaching that angle. This
is an upper bound on free turning, not a calculation of first contact. Corner
reliefs can delay first contact, so an unrelieved-hex formula alone must not be
reported as the actual free-play angle.

## Consequence and stop boundary

Retain the original stopped packet and its 5° diagnostic. One explicitly
declared service/export continuation may reconstruct the **unchanged** keeper
geometry, retain the diagnostic, check the predicted 15° barrier as an additional
observation, and investigate pre-shell assembly and aft cap/motor service.
This is not a smaller volume threshold or a changed thermal/structural limit.
Stop on a contradiction of the geometric bound, a new collision, invalid shape
or resource cap. No automatic retry follows.

The washer OD tolerance, pocket machining, nut translation/tilt, preload,
hex-wall bearing/crushing, closure-fastener forces, G11 direction/hot properties
and bridge/tab loads remain open. Passing a geometric restraint check cannot
close those strength and assembly requirements. The active vehicle and full
WO-03/physical/flight gates remain unchanged.

[Published compact keeper evidence](../runs/wo03-g80-keeper-20261101T063807744500Z/record.json) retains the stop, source-identical continuation, source snapshots, fixture values and resource accounting; native geometry stays local. No full engineering or physical acceptance follows.
