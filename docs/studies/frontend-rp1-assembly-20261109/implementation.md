# RP1 assembly/service concept — standalone implementation

This bounded FW2-023 increment supplies a read-only, source-linked walkthrough
of the existing AD1 v2 construction/service concept. It is **not approved build
instructions**, a manufacturing release or a new engineering variant. It changes
no frozen part, CAD, mass/inertia, material, motor, product identity or result.
All physical gates remain open; the five inquiries remain UNSENT.

## Integration seam

`web/src/workbench/Rp1AssemblyWalkthrough.tsx` exports the default component and
`Rp1AssemblyWalkthroughProps`:

```tsx
<Rp1AssemblyWalkthrough
  vehicle={inspectionDocument}
  initialStepId="source-stock"
  onInspectPart={(target) => {
    // Primary wires the existing Design return/navigation path.
    // target = { partId, href, configurationId, specificationSha256 }
  }}
/>
```

Only `vehicle: InspectionDocument` is required. `initialStepId` is an optional
initial reading position; an unknown step shows unavailable. `onInspectPart` is
optional: without it, each source-part anchor already has the exact existing
`/?workspace=design&design=…&part=…&spec=…` route. With a callback, ordinary
activation passes that complete target to the parent; modified link activation
keeps normal browser behavior. The primary owns workspace entry, any return
state/camera handling, actual routing integration and acceptance. No shared
import, router or existing UI file is changed by this slice.

`rp1AssemblyData.ts` has a distinct basename from the TSX component, preventing
case-insensitive module collisions. It exports the seven steps, eleven logical
source groups, their relationship paths, source citations, guard and target
builder. There are no network calls, storage writes or geometry/physics jobs.

## Reading path and source boundaries

| Step ID | What the source explains |
| --- | --- |
| `source-stock` | Labelled stock/ply/process, rounded/sealed notch and witness preparation; no incoming acceptance inferred |
| `dry-route` | Proposed figure-eight-on-a-bight eyes, tube choker, intact factory-sewn nylon loops, raw reservations and tails; no approved termination or knot-efficiency credit |
| `protection` | Corrected sleeve ahead of the ring/notch, lip guard, textile access and working fibers free of adhesive; no thermal/chafe or capacity pass |
| `forward-root` | Forward-ring/mount/body order, integral tab and finite fillet/gusset/body/aft routes; no front-tab ring support, direct aft butt stop or rigid clamp |
| `open-inspection` | Aft ring remains off until tab fillets, route and cure witnesses are inspected; later aft/mouth/borescope access without an invented cure schedule |
| `aft-motor` | Aft bonds and unobstructed bore/independent retainer intent; exact motor/tube/retainer/liner and removal/fit acceptance remain separate holds |
| `service-retire` | Outside-mouth junction and nylon service; permanently buried choker requires destructive access for replacement, and suspected hidden damage retires the assembly in the source concept |

The selected step highlights its actual source groups in a schematic. Selecting a
group exposes its source notes and exact-part Design links. Boxes, dashed paths
and their XY coordinates are **reading layout**, not a knot reconstruction,
scaled assembly, spatial bond definition, force vector or accepted load split.
Group references can repeat a source part without charging mass again.

Step buttons and previous/next controls are ordinary keyboard-accessible buttons;
SVG group controls support Tab, Enter and Space, with visible focus/selection.
The source citations are accessible links/details, and the current reading step
has an explicit status. Advancing a step records no completion, inspection or
physical action. Native keyboard/focus/visual behavior remains unobserved.

The failed saved optimistic wood-panel screen (7.301 MPa / 1.805 mm) and unknown
installed root/finished cord capacity remain conspicuous above every step.
D1's retained 8.83 N·m / 331.125 N per fin is already factored once. No lower case,
equal force division, perfect restraint, supplier rope rating, process allowance
or generic product envelope becomes a passing construction. No fin alternative
or product is adopted, and no owner measurement/contact/purchase is requested.

## Exact source and revision admission

Admission requires current `G80-F2-RP1-AD1-definition-v2`, exact specification,
AD1 definition/record and inspection-geometry revisions, and every stable source
ID exactly once across all 55 records. A foreign, historical, incomplete or
changed source shows unavailable; it cannot produce an apparently compatible
walkthrough or Design target.

Source links use the primary-designated published checkpoint
`2308648ecd2c4dbce857350316088524c10986ec`. This slice read and hashed the actual
local source bodies; it performed no Git/network/remote blob verification.
The three frozen input pins match their existing identity contract, and the two
unchanged narrative bodies are pinned independently:

| Source | Actual local SHA-256 |
| --- | --- |
| `configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml` | `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660` |
| `configs/studies/rp1-attachment-definition-v2.yaml` | `e9db49f2cafc89b1f77bf9d7396434297bc8bb8754085fdcf74d3b0242012555` |
| `runs/wo03-rp1-attachment-definition-20261103-v2/record.json` | `bc349a24fe1cfaa4d883b9e00dc5b75387638a7be5cd4b05d9f32112ee8bd95b` |
| `docs/wo03-rp1-attachment-definition.md` | `012cd168e03807460debd5bb9dbc543f058d02597f87bd83945a769794a1aa4a` |
| `docs/wo03-rp1-load-attachment-decision.md` | `af6eabd641063d262d0190ee46f5bbc847e54af5c7a3a1f1c442f0a57740bb47` |

Each step carries exact document sections or YAML/record locators. Generic stock,
connector, knot and retainer references remain at their recorded scope. Source
images, diagrams and inherited measurements are not reinterpreted as qualified
installed assemblies.

## Verification and remaining work

The scoped pure-Node/Vite SSR suite reports **7 passing tests**. It checks actual
source bytes/pins, all node/step/source membership, the retained failed/unknown
record, revision/inventory rejection, every exact-part target, all seven rendered
steps, keyboard semantics, critical limits and unavailable cases. No Python
runtime or web dependency is introduced. Scoped ESLint/Prettier and web
TypeScript checking pass. One focused correction changed the SVG title to a
single string, removing React's multi-child title warning.

These establish source/routing payloads and rendered markup, not actual native
step selection, keyboard/focus, screenshot readability, navigation return or a
physical service path. No server, browser, CAD, solver, physical work or Git/network
action was performed. The standalone component is not imported into the existing
app by this slice. Primary integration, required publication checks and a bounded
designated-window acceptance packet remain separate. FW2-023 remains partial.

## Primary integration follow-up

The primary now supplies the already verified inspection through App into a new,
separate **Engineering → RP1 assembly & service** topic. The historical C1 assembly
route stays separate. Integrated route tests admit actual current source and
refuse missing/foreign/repeated source identity. [Current integrated scope](integration.md)
supersedes the standalone-only wiring statements above.

P78 was unexecuted due to an incorrectly positioned URL assertion. Its one
verifier-only correction used named source fields and negative probes before
P79's first actual view. P79 reached step7 and showed the controls, critical
warning and upper diagram within its bounds; lower diagram/step details were
AX-only and remain partial. Source-part returns, keyboard/scroll and complete
pixel coverage remain unverified. No engineering/build/service release follows.
