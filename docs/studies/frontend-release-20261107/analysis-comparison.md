# Recorded Analysis comparison — code packet

Date: 2026-11-07. This packet adds a reusable, source-checked recorded-scalar
comparison and CSV export. It does not add solver results, a geometry overlay,
new physics, a simulator or engineering acceptance. No eligible pair of RP1
spatial field records is supplied by this packet. The integrated workspace
should show the explicit unavailable state until a real compatible pair exists.

## Integration contract

`web/src/analysis/RecordedCaseComparison.tsx` exports the named and default
`RecordedCaseComparison` component. The primary owns integration into existing
Analysis workspaces; this packet does not edit them.

```tsx
import { RecordedCaseComparison } from './RecordedCaseComparison';

// Truthful current state when no eligible pair is supplied.
<RecordedCaseComparison left={null} right={null} />

// Future admitted recorded pair; each side supplies its own manifest,
// registered field object and already loaded payload.
<RecordedCaseComparison
  left={{ manifest: leftManifest, field: leftField, payload: leftPayload }}
  right={{ manifest: rightManifest, field: rightField, payload: rightPayload }}
  legend={[0, 25_000_000]} // optional fixed shared limits in source Pa
/>
```

The `RecordedComparisonSource` interface and pure functions
`compareRecordedCases(left, right, options)` and `recordedComparisonCsv(model)`
are exported from `web/src/analysis/recordedComparison.ts`.
Options accept independent integer `leftSample` and `rightSample` indices and
an optional two-number fixed source-unit legend. Missing sides are explicit
`null`; they are not populated from another configuration or synthetic data.

Callers demonstrating synthetic software fixtures must pass `fixtureNotice`.
The component prominently labels this as synthetic and not engineering evidence.
The regression tests use synthetic values and fingerprints only; they do not
establish that a real pair is available.

## Admission and missingness

Before producing any comparison rows, both supplied manifests must be marked
compatible and carry nonempty configuration, resolved specification, CAD and
part-shape identities. The full identity maps must match across both sources.
Each selected field must be the exact registered field in its own manifest and
have a registered case and declared artifact identity. Source quantity and units
must agree (`temperature/K`, `stress/Pa`, `displacement/m`, `design_margin/1`).
Quantity, component, units, association, margin definition, coordinate frame,
declared coverage notes, part-ID coverage and sample count must match.

Part-level fields may list the same covered parts in a different order; values
are joined by the exact source part ID, not by array position. Coverage must be
nonempty, unique and refer to the manifest's shape identities. Spatial sample
tables additionally require matching recorded mesh identity, registration,
topology, coordinates and declared mesh coverage. Existing payload validation
checks the supported associations and registration. No spatial field or
deformation surface is constructed by this component, even for compatible input.
Its `geometryAttachment` result is always `false`.

Failed numerical validation, unavailable provenance, malformed/nonfinite sample
values, invalid payload shape, non-increasing times and incompatible identities
block the comparison. A requested exact sample outside the recorded array is
unavailable; no nearest sample, interpolation or extrapolation is substituted.
Null stays a visible gap, zero stays numeric zero, and a difference is unavailable
if either selected value is null. No missing entry becomes a calculated pass.

The supplied artifact fingerprint is a declared manifest identity. This
component does not fetch files or independently rehash the original artifact
bytes. The existing caller/loader must retain its allowlisted artifact route,
source identity and byte-digest verification responsibilities. A compatible
comparison is a software/data association result, not qualified material or
installed-assembly evidence.

## Clocks, legend and export

Each side exposes its own exact recorded sample selector and time. Static cases
show no fabricated time axis. The two clocks do not change the replay cursor or
each other; selected unequal times remain visible. Changing source identity
resets that side's selection to sample zero, instead of silently carrying another
record's selected sample index. The displayed subtraction is explicitly **right
minus left at those two selected samples**; it is not a new physical model.

One fixed source-unit legend applies to both columns and all selected times.
Default ranges are 273.15–573.15 K, 0–25,000,000 Pa, 0–0.005 m and −1–3 for
dimensionless margin. The caller may explicitly supply another finite increasing
range. No data-driven auto-stretch occurs. Out-of-range colors saturate while
raw table/export numbers remain unchanged; missing samples receive no color.
Colors are not pass/fail criteria. Source-unit display avoids mixing display
conversions with the raw selected-record values.

CSV export is bounded to the selected sample on each side, rather than exporting
all recorded history. It contains status/reason, both full source identity maps,
run/API/field/case identifiers, quantity/component/units/association, mesh and
artifact digests, selected sample indices and exact times, provenance/validation,
shared legend, coverage IDs, raw left/right values and right-minus-left.
Unavailable results export the reason and identities with empty value cells.
Null values export as empty cells with `unavailable gap`; zero exports as `0`.
CSV quoting preserves embedded commas, quotes and line breaks. Source labels
beginning with spreadsheet-formula characters receive a leading apostrophe;
numeric negative values remain numeric.

## Verification and remaining evidence

The new `web/tests/analysis-comparison-release.test.mjs` passed four regression
groups covering reordered exact coverage, zero/null semantics, independent
unequal sample times, unchanged source objects, fixed legends, invalid sample
indices, identity/coverage/field/units rejection, failed and unavailable data,
static times, exact spatial topology, CSV metadata and formula-safe labels,
and SSR unavailable/explicitly synthetic presentation.

Full frontend TypeScript checking and ESLint for this packet's files passed.
These are software and SSR checks. They do not establish browser selection,
scrolling, download behavior, layout acceptance or a real eligible Analysis pair.
Browser verification remains blocked separately by the unavailable browser access
host recorded in [the access report](browser-access.md). No CUA call, solver,
simulation, engineering-source mutation or hardware action occurred for this packet.
