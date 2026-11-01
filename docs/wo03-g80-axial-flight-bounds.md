# G80 forward shell: saved-flight axial bounds

At the **1009 mm shell-only cut**, the sampled, near-vertical one-dimensional free-body bounds give maximum uniform DF3 axial stresses of **1.479 MPa nominal**, **1.158 MPa low thrust/high drag**, and **1.643 MPa high thrust**. Each is below the existing **2 MPa estimated paper screen**. These results cover only the three saved modeled powered trajectories and the assumptions below; they do not establish local shell stress, bond or joint strength, hot properties, other winds, or flight qualification.

This closes the earlier [drag-free conditional screen](wo03-g80-axial-cuts.md) for the specified **sampled modeled cases**, by incorporating time-aligned modeled axial drag with an intentionally unknown spatial partition. It is not a continuum-time guarantee or a measured aerodynamic load. The 1178 mm internal-motor cut is not used as a shell-force bound.

## Source, force accounting and assumptions

The [postprocessing record](../build/wo03-g80-axial-flight-bounds-v1/record.json) reads the saved [candidate flights](wo03-g80-candidate-flight.md), their 5 ms telemetry and the matching axial-cut record. Their candidate identity is `0a1ad4c196e7bbd046704199e99bad1f6649bc237c3c07b0e4f26118d4572c4b`. All loaded mass includes the 43rd upper-annulus adhesive budget. The axial record bounded forward mass by **0.325138–0.389467 kg** while allowing 50 g of growth on either side. For these actual flight cases the added growth is either zero or at **1.212 m**, aft of the 1.009 m cut, so the applicable source-derived forward-mass bound is **0.325138–0.339467 kg**. The full 50 g remains in each growth trajectory's recorded total mass `M(t)`, which decreases as the modeled propellant burns.

The recorded cut crosses only the aft shell among modeled components; the force insertion interval is aft of it. With compression positive, in the axial approximation

```text
N = (m_forward / M) × (T − D) + D_forward,
0 ≤ D_forward ≤ D.
```

`T`, `M`, and `D` are time-aligned sampled thrust, total mass and modeled body-axis drag magnitude. For `T−D ≥ 0`, the minimum uses the lower forward mass and zero forward drag; the maximum uses the upper forward mass and all drag forward. When `T−D < 0`, the mass extrema reverse: the minimum uses the upper mass and the maximum the lower mass, still adding 0 or D respectively. The calculation actually encounters such negative-drive samples and does not discard them. Uniform gravity cancels between whole-vehicle acceleration and the forward free body under this approximation.

`D` is reconstructed from the saved dynamic pressure, Mach and the **existing simulator's** powered `q × area × Cd × drag_scale` expression. Reconstructed drag at each saved thrust/drag peak matches the flight report. It is an unmeasured total force; no source justifies a particular forward drag distribution. The numerical results bound every assumed partition in `[0,D]`, not the actual surface forces. Powered peak modeled tilt is at most **0.514°** and powered peak angle of attack at most **0.259°** in these cases. The scalar calculation is therefore a near-vertical approximation to the 6-DOF simulation, not a rigorous vector bound for arbitrary attitude or wind. At the guide, the low-thrust case also includes a separate sensitivity allowing its **0.5 N** friction anywhere along the vehicle; it does not change the worst sampled result.

## Sampled results

The relevant unbroken annular shell section is **102.8872 mm²**, and the factor of three is applied once to the maximum absolute signed force bound. The worst sample and both endpoints are shown; other sampled intervals, including those with negative `T−D`, were checked.

| Saved case | Worst sample time | Sampled mass / thrust / drag | Force interval | Maximum uniform DF3 stress | 2 MPa comparison |
| --- | ---: | --- | ---: | ---: | --- |
| Nominal calm | 0.995 s | 0.698926 kg / 91.628 N / 12.090 N | 37.001–50.721 N | **1.479 MPa** | Conditional pass |
| Full growth, low thrust / high drag | 0.650 s | 0.762845 kg / 84.424 N / 3.869 N | 34.334–39.716 N | **1.158 MPa** | Conditional pass |
| Full growth, high thrust | 1.170 s | 0.743914 kg / 100.660 N / 19.139 N | 35.630–56.339 N | **1.643 MPa** | Conditional pass |

The separate unallocated guide-friction check returns the same worst sample and value for all three. The shell comparison is against an estimated uniform axial-strength screen, not a measured kraft allowable; compressive buckling, stress concentrations, joint transfer, radial/peel loading, material direction, temperatures and actual loads remain open. The upper bound's all-drag-forward end is deliberately conservative for the assumed scalar resultant, but cannot substitute for a real drag distribution or demonstrate flight safety.

## Validation and execution

A known free-body check with forward mass 0.2–0.3 kg, total 1 kg, thrust 10 N and drag 2 N gives **1.6–4.4 N**; a negative-drive check with thrust 2 N and drag 10 N gives **−2.4–8.4 N**. Focused tests also cover the zero-drive case and invalid mass partitions. The record hashes both flight/cut reports, the candidate specification, the executed postprocessor and all three telemetry files before and after reading; they were unchanged. It verifies finite monotonic time and the recorded loaded/burnout mass range, explicit aft growth, source-identity consistency and reconstructed drag peaks.

The single read-only child took **0.458 s wall / 0.378 CPU s**, peak RSS **95,567,872 bytes**. One worker and one Arrow compute/I/O thread were requested; OS affinity was not established. Black, Ruff and two focused tests pass. Script SHA-256 `ba7b24e9eece1f625a116d1ef16d45e9c946220cbefc7fc70cf9e6de7aaedbbd`; record SHA-256 `7fef496b5802173ad36efb05fc90fcab661e8cbdf22ddf6af8c419ff3b4ce34c`. No flight, thermal, CAD or structural solver was rerun. Real load sharing and every other G80 acceptance and physical-release gate remain open.

## Published evidence

The [candidate-check packet](../runs/wo03-g80-candidate-checks-20261101T053200Z/record.json) retains the exact compact records and their source hashes, including the stopped fit input attempt. Generated CAD, resolved copies and full telemetry remain local; their hashes and reproduction sources are recorded. This is evidence for the separate candidate, not adoption or complete WO-03 acceptance.
