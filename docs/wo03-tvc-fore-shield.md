# G12 fixed fore-bay shield probe

The explicit lightweight foil is **not adopted**. It clears the checked nominal
motion poses, but the existing reduced thermal model still predicts **45.9129°C**
for the aft shell against the unchanged **45°C** screen. Finite-end radiation is
not resolved here; the [finite-radiation diagnostic](wo03-finite-radiation.md)
also prevents treating the axial-band model as a conservative thermal bound.

This probe starts from the complete hoop-cap, original flat-horn, layered-fin and
independent-recovery candidate in the [clearance study](wo03-recovery-clearance.md).
It imports that candidate's actual frame STEP and explicit fin-layer STEP. It does
not substitute generic frame geometry for the rounded recovery saddles.

The new fixed foil spans stations **1.025–1.075 m**, has outer radius **29 mm** and
wall **0.020 mm**, and is held by three curved-inner/flat-outer mica stand-offs at
each end. The stand-offs meet the actual G11 rail wings outside the fin channels.
An additional **0.250 g** adhesive/application allowance is counted once. The total
addition is **0.753216 g**, including actual foil and stand-off CAD volume.

The combined candidate is **782.395 g loaded**, or **832.395 g** including the full
50 g growth allowance. Its calculated axial balance point is **783.793 mm aft of
the nose**. The resolved full inertia tensor and part-by-part mass ledger are in
the record. These are candidate properties, not replacements for the active
G12 vehicle or a new flight prediction. The structural recovery failures remain.

All **25 nominal ±5° combined-axis poses** have no new rigid intersection above
**0.05 mm³**. The minimum foil-to-link distance is **0.931 mm**, and foil-to-frame
distance is **0.500 mm**; intended mica contacts are zero-distance contacts.
Fixed-to-fixed pairs are checked once. Soft stowage and distributed mass proxies
are excluded from rigid contact, with IDs recorded. The declared 0.10 mm radial
manufacturing estimate is metadata, not an executed tolerance envelope. The
sampled sweep does not establish continuous clearance, foil roundness, thermal
expansion, wire/harness clearance, retention under vibration or service access.

The thermal case retains **300°C exterior case temperature, 35°C ambient and
all foil emissivities 0.9**, the high-conductivity/low-heat-capacity corner, burn
and 300 s soak. The shell peaks at **85 s**, failing by **0.912899 K**. The energy
residual is **3.39×10⁻¹¹ J**. Energy conservation verifies numerical bookkeeping;
it does not verify external case histories, air flow, contact conductance or
finite-end/angular radiation. No temperature limit or operating envelope changed.

Reproduce from the preceding candidate exports:

```sh
XDG_CACHE_HOME="$PWD/.cache" .venv/bin/python scripts/wo03_tvc_fore_shield.py
```

Executed record: `runs/wo03-tvc-fore-shield-20261031T025947335730Z/record.json`.
It binds the source candidate, actual frame/fin exports and code/configuration
hashes, confirms unchanged inputs, and retains `engineering_acceptance_passed:
false` and `flight_ready: false`. Full histories, new-part STEP files and resolved
candidate remain local. The isolated foil geometry is useful for a future coupled
thermal correction; this failed screen does not justify adoption. Hot-material,
bond/foil retention, mechanism, instrumented soak and deployment tests remain in
the existing owner-performed stages.
