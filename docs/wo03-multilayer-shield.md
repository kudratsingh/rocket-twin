# WO-03 multilayer thermal correction

## Decision

Continue the **segmented shield with preserved brace rings** as the fixed-motor
thermal candidate. Do not adopt it yet. The G54 eight-layer version calculates
44.749°C in one required combined 300°C / contaminated-foil ε=0.9 / 35°C ambient
corner, leaving only 0.251 K against the unchanged 45°C screen. This is a narrow
calculated part-mean reserve, not completed thermal acceptance. The full candidate
matrix, tolerance/contact/foil-shape sensitivities and integrated structural and
flight comparisons remain open. No equivalent TVC shield is established.

## Implemented geometry and comparison

`scripts/wo03_multilayer_shield.py` constructs isolated normal-generator CAD parts,
rebuilds their mass/CG/inertia and records exact source identities. Every added foil
uses the original aluminum profile, including ε=0.9 in this required combined case.
All histories include source burn and 300 seconds of post-burn soak. The material
corner is high conductivity / low heat capacity; the fixed-mount radial bond gap
is 0.68 mm, adhesive conductivity 0.15 W/(m·K), and interface contact 2 W/K.

| Actual fixed G54 candidate | Maximum limited-part temperature | Mass change from source package | New-part nominal intersections | Interpretation |
|---|---:|---:|---|---|
| Four total foils, full mica collars, enlarged bores | 45.604°C | −1.976 g | None | Fails |
| Six total foils, full collars, enlarged bores | 45.099°C | +0.206 g | None | Fails; no rounding |
| Six foils to R22 mm, three small mica pads at each end | 44.951°C | −2.836 g | None | One thermal point passes narrowly; changed brace-ring stiffness is unacceptable to carry forward |
| Six foils to R24.5 mm, small end pads, enlarged bores | 44.656°C | −6.321 g | None | One thermal point passes; enlarged bores lose substantial ring bracing |
| Six segmented foils to R24.5 mm, original bores preserved | 45.013°C | +6.831 g | None | Still fails; 0.013 K exceedance is retained |
| Eight segmented foils to R24.5 mm, original bores preserved | **44.749°C** | **+8.899 g** | None | One calculated point passes; further acceptance remains open |

The eight-layer candidate has the original R15.12 mm foil plus seven added radii:
17, 18.25, 19.5, 20.75, 22, 23.25 and 24.5 mm. Each added foil is 20 µm thick.
Three 10° mica sectors, 1 mm long axially, separate adjacent foils at each segment
end. Each sector is a real CAD solid with its own thermal capacity and serial
contact/conduction links. No full-radius overlapping spacer disk or massless,
perfectly insulating support is credited.

The initial continuous-shield design enlarged mount bores to foil radius +0.3 mm.
Although that removed mass, the structural study found that the aft fin channels
leave only a 2 mm continuous inner ring band at the largest bore. The prior
3.7439 buckling factor does not apply. The selected direction instead leaves the
original bores and removes shield material around every actual ring station and
width, with 0.5 mm nominal axial clearance on each side. These windows are also
removed from thermal opacity. Outer foils stop 2 mm ahead of actual aft-retention
blocks where their radii would intersect those blocks. The segmented correction
therefore does not preserve heat shielding by silently removing a structural ring.

`rigid_intersections` checks actual placed solids with the existing 0.05 mm³ reporting
threshold. Its zero new-part intersections establish only nominal rigid geometry;
foil roundness, seams, wrinkles, fastening, thermal expansion, insertion and
manufacturing tolerances remain unresolved. No moving-gimbal sweep is claimed.

## Numerical evidence and heat paths

Frozen-source fixed G54 record:
`runs/wo03-multilayer-shield-20261031T020146392505Z/record.json`.
It retains the resolved candidate, raw thermal histories and immutable source-byte
snapshots alongside the compact record. The refined run uses 16 liner cells, a 0.5 s maximum integration step and
0.25 s heat-flow sampling. The preceding 16-cell/default-time-step calculation
gave 44.748952438°C; refined time controls give 44.748952765°C. That agreement
checks this numerical calculation; it does not measure temperature accuracy or
demonstrate a full spatial hot-spot model.

The baseline worst-case heat accounting explains why removing mount contact was
counterproductive. At the G54 shell maximum near 52 s, the opaque radial foil-to-
shell paths deliver about 15.48 W. External shell convection/radiation removes
9.05 W, bonded-ring paths remove about 4.08 W and fin/avionics paths remove roughly
2.12 W. The mount/bond network is a heat sink at that time. Weakening it can warm
the shell even while reducing direct case conduction. The geometry and contact
assumptions must therefore remain coupled to structural analysis.

The equivalent G80 preserved-ring/eight-layer corner is separately executed:
`runs/wo03-multilayer-shield-20261031T020146392490Z/record.json`.
Its limiting part is the plywood mount at 43.250°C, margin 1.750 K; mass increases
5.880 g and no new nominal rigid intersections are reported. This is the exact
G80 source configuration, not a relabeled G54 result. The reproduced unshielded
reference is `runs/wo03-multilayer-shield-20261031T020144942512Z/record.json`.
All three frozen records report unchanged inputs and matching source snapshots;
their CAD revision is `671116b6a3e90d111b37d7e6dcab7cb17a20821eb6ff6b52475dcb5a27bbf80f`.

The fixed G54 source is the isolated Package A copy with **75 mm fin span**,
not the active 70 mm-span vehicle. The shield copy is 846.088 g nominal loaded
(896.088 g with allowance). Its calculated full-growth liftoff/burnout margins are
1.1972/1.6759 calibre. Those numbers precede the remaining recovery/joint
corrections and do not establish a final integrated configuration or flight result.

## Reproduce and remaining verification

```zsh
.venv/bin/python scripts/wo03_multilayer_shield.py --mode G54 \
  --candidate eight_total_foils_wide --spacers three_10deg_pads \
  --rings preserved --preset sim
```

The hash-identified predecessor copies under
`build/wo03-correction-package/latest/` must exist (`make correction-package`).
Historical runs preserve their original source identities. The script does not
edit active specs, CAD sources, the 45°C screen, ambient limits or source histories.

Before any adoption: execute the full required matrix on the same mechanically
selected package; check numerical and geometric uncertainty; design foil retention,
seams and assembly access; validate the actual support/bond stiffness; reconcile
the full vehicle mass/CG/inertia; and rerun affected static and flight/reference
checks. The current TVC cassette, gimbals, links and full two-axis motion have not
been shown to accommodate this fixed-motor geometry. G12 acceptance remains open.

Instrumented case/liner/support/shell/fin-root/gimbal temperatures, foil aging and
contact measurements, hot joints and assembled proof tests stay in owner-performed
stages. This model still omits finite-end angular radiation, gas circulation, plume
heating, seams and local plate/bond hot spots. `flight_ready` remains false.
