# Exact circular pad candidate and cache reconciliation

The previous 10° mica-pad primitive used eight chord segments. Its inner chords
intruded approximately 1 µm into adjacent cylindrical foil. The actual Boolean
radiation boundary therefore had genuinely ambiguous material ownership, even
though each overlap was below the earlier 0.05 mm³ rigid-intersection reporting
threshold. The historical candidate and failed ownership checks remain preserved.

`cad.parameters.circular_boundaries: true` now opts into true circular inner and
outer radii. The annulus is intersected with an oversized angular wedge; it is not
approximated by inner polygon chords. Default geometry remains unchanged for
historical replay and for the active vehicle. A known-volume/contact test checks
the exact sector area, three components and zero intrusion into the mating foil;
it also preserves the old positive-overlap finding.

The explicit new candidate is
`runs/wo03-circular-pad-candidate-20261031T034153884353Z/record.json`, identity
`e25026cdc3b63f53a01cb4b91f3fb4b7e15c1b3e70e53924e95a639f4c5166b6`.
It derives from the frozen `7aec…` G54 eight-foil study. All 138 CAD caches were
recomputed; 62 pad parts opt into the new boundary. Every non-pad volume remains
unchanged within 1e-5 mm³, and every checked adjacent foil overlap is at most
1e-7 mm³. Supplied component masses remain supplied; volume-owned masses and full
inertia were recalculated. Net mass change is **+0.000385 g**, with **+0.000128 mm**
aft CG change. These small changes do not transfer old thermal acceptance.

The CAD generator revision is
`1193713d0f4a7ad8393a00a0a03e7aaa04e9aa9393d2034691ef7126ae3cdd3b`.
The source spec, actual pads, solver and mesh each retain separate identities.
The new fitting-baffle candidate has a further distinct identity and cannot
inherit this candidate's analysis without a checked geometry mapping.

The global generator hash invalidates old active caches even when their default
geometry is unchanged. Active caches were therefore **regenerated**, using the
normal reconciliation command. A separate comparison of all six active variants
confirms exactly unchanged geometry, CAD parameters, materials, mass, centroid
and full physical inertia entries; only the cache identity changed. Fresh CAD
`wo03-20261031T034832494277Z` passes all six variants and both 25-pose sweeps with
unchanged inputs. Static/flight regressions `wo01-platform-20261031T034519135584Z`
and `wo02-20261031T034519948032Z` pass. This is not adoption of candidate pads or
expanded engineering acceptance. Current active CAD previews were regenerated.

Reproduce the candidate with
`.venv/bin/python scripts/wo03_circular_pad_candidate.py`, using the preceding
archived source candidate named in that script. No active YAML geometry is edited
by the candidate builder. Physical fit, adhesive contact, hot properties, assembled
proof and thermal measurements retain their existing later gates.
