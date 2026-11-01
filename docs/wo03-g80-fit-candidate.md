# G80 fixed-mount fit: one candidate, further checks required

The current G80 fixed plywood mount-to-shell gap fails the in-domain tolerance screen. One separate **32.2 mm outer-radius** candidate passes the cold and in-domain versions of that screen and is ready for the primary's decision about further engineering; it does **not** pass the separate out-of-domain hot sensitivity or qualify the joint. It is not adopted, flight-ready, or a complete G80 package. No active vehicle, CAD generator, simulation or thermal input was changed.

## Identity and correction

The existing analyzer was run on exact current G80 resolved identity `c18abfee2444307e46eaaca55197693a3d9353bd8d8d8ac42162ffd238ef1d5e`; [preflight](../build/wo03-g80-fit-candidate-v1/preflight-record.json) records source/part hashes before and after. Its existing `aft_shell` to `motor_mount` stack gives a **0.02093 mm** in-domain minimum and **0.05 mm** cold minimum against the unchanged **0.1 mm** radial criterion. This reproduces the historical numerical finding on the current identity rather than inheriting the old `c5eab65c…` result.

The proposed copy changes only fixed mount outer radius **32.3 → 32.2 mm**, with its existing cylindrical trim, plywood material, ring stations, rails, fin channels, mounting blocks and motor/liner geometry retained. It adds a separate 43rd explicit adhesive *budget*, described below. The [executed record](../build/wo03-g80-fit-candidate-v1/candidate-record-io-replan.json) and [resolved study copy](../build/wo03-g80-fit-candidate-v1/resolved-candidate-io-replan.yaml) have identities and the full source hashes. Candidate resolved SHA-256 is `0a1ad4c196e7bbd046704199e99bad1f6649bc237c3c07b0e4f26118d4572c4b`; the executed script SHA-256 is `89e9dc716026c873a39f53f0077460a56d2d42733e1353d72b023b46dd55f225`.

| Existing stack | Current G80 | Candidate | Requirement/status |
| --- | ---: | ---: | --- |
| Cold manufacturing radial minimum | 0.05000 mm | 0.15000 mm | ≥0.100 mm; candidate passes |
| In-domain independent-temperature minimum | 0.02093 mm | 0.12102 mm | ≥0.100 mm; candidate passes |
| Out-of-domain hot sensitivity minimum | −0.226165 mm | −0.125310 mm | ≥0.100 mm; candidate fails |

The source code labels the last row `out_of_range_hot_sensitivity`: its actual numeric input varies each component independently by 0–285 K from 15°C, beyond the 45°C declared domains for both shell and mount. The 300°C external case does not establish either component temperature; no paired history is measured. The study YAML prose also retains an older 0–235 K description, but the executed numeric bounds were 0–285 K and govern the reported result. Do not call all bounded fits passed. The in-domain result assumes the existing tolerances and expansion model; manufactured eccentricity and process capability remain unmeasured. Mount-to-radiant-shield cold minimum is 0.38 mm, but its hot result is **unavailable** because the shield CTE is missing. The nominal liner-to-motor gap is 0.2 mm, but motor-case fit is **unavailable** without actual purchased-case tolerances. A pass is not assigned to either unavailable result.

## Geometry, mass and conditional structural screens

The candidate mount is a valid positive-volume single solid. Its volume decreases **63,972.492 → 63,583.670 mm³**; Boolean subtraction finds **0 mm³** candidate material outside the saved original, confirming a subset to the declared 1e-4 mm³ threshold. Nominal Boolean common volumes with the saved G80 shell, fin set and thrust plate are each **0 mm³**. These are checked pairs only; actual bond area, tolerance-expanded interferences, fasteners, service, retention and load transfer remain open. The [candidate STEP](../build/wo03-g80-fit-candidate-v1/motor-mount-candidate-io-replan.step) and source STEP hashes are recorded; the original volume agrees with its cached source.

Mount mass falls **45.7403 → 45.4623 g** using the existing 715 kg/m³ plywood estimate. The potential incremental radial gap is charged separately as a full 0.1 mm annular shell from 32.2 to 32.3 mm over the 190 mm mount length at the project estimate **1200 kg/m³**, or **4.6200 g**. It is a named, centered tube budget with its own annulus inertia, not mass silently added to `fin_bonds`. This bounds *the nominal added annular occupancy under that density*, not fillets, extra adhesive, the baseline bond, wetting, strength or joint stiffness. Actual occupancy can range from zero to the full idealized increment; either endpoint is an estimate, not final hardware.

| Mass-property case | Loaded mass | With separate full 50 g | Loaded CG from nose |
| --- | ---: | ---: | ---: |
| Baseline | 739.4622 g | 789.4622 g | 792.8144 mm |
| Candidate, zero extra annular fill | 739.1842 g | 789.1842 g | 792.6988 mm |
| Candidate, full incremental-annulus budget | 743.8042 g | 793.8042 g | 794.6386 mm |

The unchanged mass core calculated each complete tensor; all three are in the record. The candidate upper-budget tensor in body axes, kg m², is:

```text
[[ 0.000893596260,  0.000190079256, -0.000030361033],
 [ 0.000190079256,  0.125611874255, -0.000000106371],
 [-0.000030361033, -0.000000106371,  0.125616872568]]
```

Existing motor-support hand screens use the same 117.53 N source thrust and DF3. Channel-cut single-rail section is **45.6408 → 45.2365 mm²**, its weak-axis inertia **194.404 → 187.441 mm⁴**, hot axial margin **0.9417 → 0.9245**, and hot half-modulus Euler margin **1.0154 → 0.9433**. The assumed full last-ring bond hot margin changes **0.7268 → 0.7214**. The unchanged thrust plate hot bending and six-finger hot shear sensitivities are **0.5036** and **0.8991** respectively. These are margins defined as **capacity / (3 × demand) − 1**, so **zero or greater passes the individual screen**; both candidate rail margins remain positive. In the candidate, the axial calculation uses a 5 MPa assumed hot strength against 0.86604 MPa per-rail stress. The Euler calculation uses 456.783 N single-rail cold Euler capacity, half the modulus for hot, three equally loaded rails, and 117.53 N total demand. Neither ratio is an acceptance boolean for the assembled load path. These are conditional estimates using idealized sharing, restraint and bond coverage; they do not resolve edge stresses, local ring/rail/plate contacts, peel, bond gap or hot allowables. The 150 N reverse-retainer screen still lacks verified nut, washer, bearing, fastener and capture details. Fin tabs, shell connection, root loads and actual retention remain unqualified.

## Execution and evidence limits

The first child produced a valid solid but stopped at an incorrect top-level YAML lookup for epoxy density; it saved no STEP. The primary agent recorded **one input-only replan** within the original packet and the owner-authorized local work. The failed source and [failure record](../build/wo03-g80-fit-candidate-v1/candidate-failure.json) remain preserved. The nested `material_estimates.epoxy_density_kg_m3` key, input types, exact identity, saved STEP inputs, candidate stack, budget schema and existing support calculations were validated before the one reconstruction. No numerical method, criterion or candidate size changed. An isolated Boolean fixture returned 500 mm³ as expected; the fixture and candidate selected the OCCT pool at one thread and requested one-thread numerical libraries, without an OS-affinity claim.

The successful child used **4.276 CPU seconds**, **5.601 s full child wall**, and peak RSS **552,550,400 bytes**; its own recorded measured section was 1.844 s. The original failed child did not reach its resource write, so its CPU and peak RSS are **unavailable**, as are complete cumulative CPU figures; do not imply a measured aggregate total. No child reached the 120 s wall cap. All recorded candidate source hashes match before/after; the resolved 43-part copy reloads successfully. The focused annular mass/inertia test, Ruff and Black checks pass.

A candidate decision must account for the failed out-of-domain sensitivity, unspecified actual joint and fill, motor/shield fit, tab/channel clearances, local and assembled loads, recovery, flutter and the still-unqualified thermal method. No FEA, thermal or flight run was performed. G54 upgrade and G12 PID/RL remain independent; no G54/G12 result is transferred to this fixed G80 copy.

## Published evidence

The [candidate-check packet](../runs/wo03-g80-candidate-checks-20261101T053200Z/record.json) retains the exact compact records and their source hashes, including the stopped fit input attempt. Generated CAD, resolved copies and full telemetry remain local; their hashes and reproduction sources are recorded. This is evidence for the separate candidate, not adoption or complete WO-03 acceptance.
