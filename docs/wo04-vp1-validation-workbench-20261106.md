# VP1 programme inside the engineering workbench

The early Engineering workspace now implements a separate **VP1 validation programme** view:
`http://127.0.0.1:5173/?workspace=engineering&view=rp1-validation`.
It displays the frozen, unperformed programme; it cannot authorize, send, purchase or execute it.
The repository is public by owner confirmation. Engineering/physical gates and outreach authorization remain separate.

From a normal host terminal:

```sh
cd /Users/kudratsingh/Machine-Learning-Projects/rocket-twin
make workbench-vp1-validation
make preview
```

`make preview` also prepares the VP1 snapshot. The page reads only the Python-prepared
`/engineering-workbench/rp1-validation.json`; it does not depend on historical C1 API data.
Missing, changed or incompatible sources produce an unavailable state, not an older accepted result.
The production build and ordinary API/experiment setup are retained. This session does not
claim a newly observed listening server or browser/WebGL/download interaction.

## What the view explains

- **A selectable stage-to-part graphic:** S0 documentation, S1 room pilot, S2a conditioned samples,
  and the separate S2b complete-root hold. Select a stage or conceptual part to see its scope,
  entry requirement and stop decision. Nine specimen/part records include fin, tabs, motor/body
  tubes, rings, test strips, joint witnesses and harness keep-out. These are source concepts,
  not a complete current CAD assembly or mappings onto archived rocket meshes.
- **Costs and missing costs:** $236.75 room-material and $269.49 full-stock subtotals are explicitly
  dated2026-11-04. Laboratory/fixture/calibration/delivery costs and the all-in total are unquoted.
  A planning reservation is never displayed as a quote or spending permission.
- **Five exact draft previews:** recipient/channel, source hash, plain-text download and copy,
  with a selectable-text fallback when clipboard access is unavailable. Copy/download does not
  send a message, start outreach timing, grant permission or change the saved package.
- **Plain-language limits:** force and turning moment units, the retained331.125 N/8.83 N·m,
  factor3 already applied once, and1 mm movement. A test specimen is distinguished from vehicle
  hardware. An unperformed plan is distinguished from measured evidence and acceptance.

Every stage remains **not authorized**, every part **unverified**, and every draft **UNSENT**.
S0's day5/day10 timing starts only after a future authorized send; its clock has not started.
There are no send/approval/run-test controls or frontend engineering calculations.
Existing inspector, experiments, flight replay and separate FP1/FR1 comparison are preserved.

## Source and configuration identity

Preview: `RP1-VP1-inspection-preview-v1`.
Package: `RP1-VP1-plywood-validation-package-v1` in
`configs/studies/rp1-validation-package.yaml`, SHA-256
`3bc7ef7a01d20599faec2fb7ad8ca6c225243f273fedf9dcc870aa1d2d98eff8`.
Frozen configuration: `G80-F2-RP1-AD1-definition-v2`, SHA-256
`811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`.
Protocol: `docs/validation/rp1-vp1/protocol.md`, SHA-256
`7941ee02b27255c760cbb9d59002452821596e3e30c86835e7b0ad805e31a2ac`.

The exporter pins the package, accounting and original producer, protocol, summary,
source registers and all five message files, then rechecks bytes before returning.
The separate presentation manifest `configs/engineering/rp1-vp1-preview.yaml` maps
stages to conceptual parts without changing engineering inputs. It distinguishes
S2a evidence gathering from S2b admission. The browser validator requires this exact
revision, retained limits and false authorization flags. A future approval or source
revision needs its own recorded data contract; it is not inferred from a click.

No physical specification, mass, inertia, material allowable, guide requirement,
load or analysis result changes. AD1, FP1/FR1 and D1 remain frozen/unadopted as applicable.
No stopped structural/thermal campaign or flight simulation was repeated for this view.
G80 custom construction/performance stays first; G54 and G12 PID-to-RL remain separate.

## Verification and remaining acceptance

Primary integrated checks pass:90 web tests, TypeScript, ESLint, formatting and packaged build;
`make check` and31 related Python/provenance/export tests. Tests include actual-source validation,
corrupt/missing data, authorization and identity changes, stage/part relationships,
verbatim draft data, unavailable costs and server-side rendering. Startup preparation and
shell syntax pass. The existing large-bundle warning remains.

Browser verification still belongs only to the original designated frontend owner/window after
its runtime-ownership prerequisite is restored. No supported restoration action is exposed;
no retry, alternative browser, headless path or bypass occurred. Pending: stage/part click and
keyboard behavior, scrolling/layout, clipboard fallback, actual file downloads, route Back/Forward,
and inspector/experiment/replay interaction regression. Source/SSR and native offline images
are distinct from those observations. Full WO-03/04/05 and all physical/flight gates remain open.

## Available offline drawings and explicit visual gap

Open the [offline gallery](../output/vp1-workbench-20261106/index.html),
[actual React SVG](../output/vp1-workbench-20261106/vp1-graph-1.svg),
[full static React view](../output/vp1-workbench-20261106/view.html) or
[ZIP](../output/vp1-workbench-20261106/vp1-offline.zip). The gallery embeds the SVG
so it can be inspected without a PNG. Static buttons are inert; this is not the
live application or proof of interactions. Exact sources and artifact hashes
are in [the compact manifest](studies/vp1-workbench-20261106/manifest.json).

The native renderer packet is stopped. The delegated attempt reported no PNG by
its90 s deadline; initial terminal output/session and exact elapsed time were not
retained, so its cause and timing are unconfirmed. A host process inspection was
denied by the sandbox. [The attempt record](studies/vp1-workbench-20261106/native-render-attempt.json)
preserves those limits rather than inferring a rendering diagnosis. There is no
new PNG, screenshot or visual-acceptance claim. The final exporter only creates
SSR HTML and portable SVG; it rejects native invocation and performs no retry,
installation or alternate-renderer/browser workaround. Source/XML, draft hashes,
script syntax and ZIP integrity pass. Visual legibility and actual browser
behavior remain open checks, not engineering design failures.
