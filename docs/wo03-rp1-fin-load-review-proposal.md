# Proposed RP1 fin-load definition correction — not adopted

The current requirements retain **8.83N·m per fin**. This review corrects its
description; it does not replace the gate used by FR1 or retroactively pass AD1.

The [source audit](wo03-rp1-fin-input-sources.md) traces the original engineering
profile to25kPa/5deg/DF3 and the fin-design study to a40kPa sensitivity at5deg.
Neither was established by current RP1 flight evidence. Dynamic pressure
`q=ρV²/2` is not itself the normal pressure on a fin: the normal-force coefficient
and reference area must be applied. The repository uses a finite-aspect-ratio
small-angle slope, one-fin area and a tapered-area centroid. Its Mach, Reynolds,
body-interference and incidence validity remain model assumptions.

For the current60mm span,130/65mm root/tip and5deg, that exact formula gives
**108.947063N and2.905255N·m after DF3 once** at40kPa. Historical C1's90mm span,
120/60mm chords produced220.758696N/8.830348N·m. AD1 explicitly rescaled its
60mm distribution to8.83N·m, yielding331.125N. That extra3.0393moment ratio is
a **retained older-planform envelope**, not a second legitimate application of
DF3 and not the direct current40kPa/5deg result. The earlier AD1 prose calling
8.83N·m the direct current-planform40kPa result was incorrect.

Saved52-part historical flights have maxq6.973/12.199/15.315kPa, with near-zero
incidence at maximumq. These are neither a time-aligned current RP1 bound nor
permission to multiply independent maxima or remove the required case. Fixed
RP1's physical inertia/current complete flight envelope remains unavailable.
The standalone300m/s vibration ceiling is also an exploratory assumption.

**Proposal:** define the current-planform40kPa/5deg/DF3 case explicitly as
2.905255N·m, and name8.83N·m separately as the retained legacy-envelope case.
Adoption of a different governing envelope requires a recorded engineering
decision supported by the exact intended G80/mass/geometry, time-alignedq and
incidence/wind/rate cases, source uncertainty and applicable coefficient domain.
Keep exceptional handling/fault cases distinct. Do not lower a load merely
because a proposed attachment fails. Until that work is recorded, **8.83 remains
the required FR1 screen**, and both original records remain unchanged.

Plywood E1GPa/5MPa similarly traces to a50percent hot/weak sensitivity on the
engineering estimates2GPa/10MPa. It is not a measured temperature curve or
allowable for Aircraft Spruce02-20850. Any replacement property requires exact
finished-stock/direction/temperature/conditioning and test-method evidence;
neither catalogue kit success nor raw fiber modulus supplies that evidence.
