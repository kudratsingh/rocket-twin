# RP1 functional presentation and staged breakdown

Frozen `G80-F2-RP1-AD1-definition-v2` now has a versioned functional grouping
for all 55 stable source records. Each record has exactly one primary group.
The source `parent`, coordinates, dimensions, estimated mass, CAD and engineering
records remain unchanged. Original parentage is explicitly described as source
assembly membership, **not** physical attachment, support or strength evidence.

The source-owned definition is
`configs/presentation/rp1-ad1-v2.yaml`, ID
`rp1-ad1-v2-functional-presentation-v1`, SHA-256
`4ed997e371f8b2473d9da47aee7396562cb9b4d7e031d87f9876025b136c005b`.
It pins the frozen specification, attachment definition and saved record.
The active source/geometry tuple is:

```text
configuration: G80-F2-RP1-AD1-definition-v2
specification: 811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660
inspection geometry: 238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608
```

No canonical resolved vehicle, physical inertia, adopted CAD, installed joint
acceptance or compatible RP1 flight run is created by this presentation.

## Functional membership and source quantities

| Group ID | User label | Source records | Supported mesh records |
| --- | --- | ---: | ---: |
| `nose_airframe` | Nose and airframe | 6 | 4 |
| `fins_roots` | Fins and roots | 9 | 3 |
| `motor_retention` | Motor and retention | 8 | 5 |
| `recovery` | Recovery | 12 | 6 |
| `avionics_power` | Avionics and power | 16 | 8 |
| `launch_finish` | Launch guides and finishing | 4 | 0 |
| Total | | 55 | 26 |

The groups retain all four representation maturities: source-dimensioned,
simplified envelope, mass allowance and missing geometry. Group record counts
are not physical quantities or visible-solid counts. Meshless evidence remains
a source record without a fabricated solid or display-bound contribution.

Only three source-recorded quantities are exposed: three fin panels from
`geometry.count`, three integral tabs from their explicit source notes, and six
root wedges from their explicit source notes. Each remains one bundled source
record. All other `quantity` values are null; no default physical quantity of
one, guessed guide count or connector count is assigned. Panels and integral
tabs share the `integral_fin_blanks` display bundle, while retaining both exact
source IDs and separate accounting records.

Cross-links identify the existing `fin-root` and `recovery` connection evidence
and the functional independent-recovery electronics reference. Each records
exact source path, hash and locator. None is generated from `parent` or promoted
to a qualified installed interface. The ring/tube/body records can therefore
be reached from related functional groups without duplicate primary membership.

## Staged display illustration

Authored translation vectors use the existing viewer frame and metres:
X=body+y, Y=length−station, Z=body−z. GLBs already contain their source placement.
The new vectors are added only as display translations; source positions are
never applied again or rewritten.

For separation `s` clamped to `[0,1]`:

1. `0 ≤ s ≤ 0.5`: separate the six functional assemblies together.
2. `0.5 < s ≤ 1`: retain the separated assemblies and spread supported parts
   only within the explicitly opened group.

At zero every source ID returns exactly `[0,0,0]`. With no opened group,
members remain together within each separated assembly; a motor deliberately
remains nested in its tube until Motor and retention is opened. The integral
fin panels and tabs receive exactly the same transform at every stage. Other
recorded physical joints may be bonded or destructive to disassemble; the
display does not claim a feasible extraction sequence.

`web/src/components/rp1Breakdown.ts` exports the pure shared helper:

```ts
rp1BreakdownOffset(document, partId, separation01, openedGroupId)
```

The result is the **final** viewer-metre offset. Drawing, picking and camera
bounds must consume it once; multiplying it by separation a second time would
be incorrect. A non-RP1 source returns null so its existing convention remains
separate. Invalid RP1 source/geometry/presentation/shape/asset tuples, unknown
IDs, an unknown opened group and meshless records return exact zero. There is
no RP1 center-derived fallback explosion. Nonfinite values fail closed.

Both the API and frontend pin the exact presentation version/hash and the
specification/inspection-geometry tuple. The helper additionally checks each
part's shape hash and mesh URL's spec/geometry/mesh tuple. Group membership must
cover the current 55 IDs exactly once. Absent or incompatible presentation data
is explicitly unavailable; the existing source inspector remains usable.

## Bounded recorded-bounds checks

Tests use the existing saved mesh bounds, without regenerating CAD or solving
physics. At full detail separation with the corresponding group opened:

| Comparison | Separating X interval gap in the authored illustration |
| --- | ---: |
| Motor versus motor tube | 109.816 mm |
| Parachute versus upper body | 181.599 mm |
| Shock cord envelope versus upper body | 186.599 mm |
| Connector envelope versus upper body | 199.099 mm |
| Recovery-protection envelope versus upper body | 186.599 mm |

These positive AABB gaps establish that these recorded nested representations
are pulled apart for inspection. They are **display spacing**, not physical
manufacturing clearances, assembly tolerances or qualification of a contact.
No all-pair collision or path-clearance claim is made. Tests explicitly retain
overlapping integral fin-panel/tab boxes and a still-nested motor/tube when its
group is not opened. Fin, material, thermal, recovery and flight findings stay
as recorded.

## Projection and integration contract

`src/api/rp1_presentation.py` validates the YAML definition and produces
`summary.presentation`, with group IDs, labels, part lists, record/mesh counts,
maturity counts, source references and staged-breakdown semantics.
`src/api/rp1_inspection_view.py` attaches per-part metadata at
`representation.presentation`: primary group, source-parent provenance,
source-only quantity, cross-link IDs, assembly/detail vectors, rigid bundle,
source tuple, shape/mesh hashes and presentation hash. It preserves every
existing raw source field.

Static inspection JSON was regenerated using the existing
`scripts/wo04_rp1_inspection_export.py`. This did not regenerate or modify any
GLB, engineering source, mass model, AD1/D1 record or canonical identity.
The primary owns tree/store/inspector/alternatives and overall integration;
the camera agent owns the shared final-offset consumption in rendering,
picking and framing. No independent publication is performed by this lane.

Focused local evidence: **7 Python tests and 4 TypeScript tests pass**. Python
checks exact 55-record coverage, source quantities, provenance, real authored
bound separation, unqualified-overlap cases, source/configuration drift,
foreign geometry and metadata attachment without source mutation. TypeScript
checks zero placement for all 55 actual frozen IDs, meshless/unknown handling,
the staged helper and integral bundle, actual recorded motor/recovery bounds,
and wrong source/shape/asset/group guards. Its display-vector fixture is
synthetic; source-owned group semantics and vectors are independently checked
by the Python tests. Ruff, Black, ESLint, Prettier and TypeScript typecheck pass.

This is source/code/offline evidence. The new walkthrough, loaded geometry
separation, picking/framing consistency, meshless actions, panel/camera
restoration and contextual alternatives still require the designated Chrome
observations after integration. No browser, CAD generation, FEA, simulation,
supplier contact, purchase or physical work occurred in this lane. All five
inquiry drafts remain UNSENT, and engineering/build/flight gates remain open.
