# RP1 named template and feature-source contract

This packet adds a **read-only source registry** for FW2-009/010. It lets the workbench name and inspect nominal local geometry recipes and their feature evidence. The prepared file does not install a part, create a draft, run CadQuery, assign mass, resolve an interface, or qualify the existing vehicle. Frozen RP1/AD1 v2 remains unchanged.

## Pinned inputs and output

`src.vehicle.part_templates.build(root)` checks the exact bytes of the frozen RP1 specification (`811b3bed…631660`), AD1 definition (`e9db49f2…2012555`), saved record (`bc349a24…8bd95b`), and registered STEP catalog (`a7af1fad…bf731`), as well as the generic CAD generator source (`911ae4a9…442b98`) and the admitted AD1 inspection projection (`d79db74c…f90d3`). It uses the existing AD1 inspection builder to require the same 55 stable part IDs. The STEP catalog identifies the 26 represented installed records; an installed STEP file is never a reusable local template.

Run `.venv/bin/python scripts/prepare_part_templates.py` to write the ignored `web/public/engineering-workbench/rp1-part-templates.json`. The CLI accepts only that fixed project output, refuses foreign files and symlinks, and checks the source again before atomic replacement. `--check` compares existing bytes to a fresh build without writing. The output is deterministic JSON with no timestamp. A host serving only a prepared snapshot must identify it as such and pin its whole-file digest before parsing; there is no new live API route in this slice.

The top record has `schema_version: 1`, `id: rp1-part-templates-v1`, `revision_sha256`, `configuration_id`, nested `identity` objects `{path, sha256}` for specification, definition, record, registered STEP and CAD generator source, `all55_part_ids`, `templates`, `feature_sources`, `dispositions`, and explicit disabled draft/CAD execution capabilities. Each of the 55 dispositions retains its original source accounting line. A definition is not an installed occurrence, and a template is not an additional mass entry.

## Named source templates

| Template ID suffix | Local geometry | Source basis and limit |
| --- | --- | --- |
| `motor-tube-cut` | Supported nominal annular tube recipe | Source 31.369 mm outside diameter, 29.169 mm bore, 165 mm length. Exact purchased tube/motor fit, liner and retention remain unresolved. |
| `aft-annular-ring` | Supported **plain** nominal annulus recipe | Source 64.4 mm outside diameter, 31.9 mm bore, 6 mm thickness; proposed ±0.05 mm cuts. Complete installed ring, fit and bond are not admitted. |
| `slotted-body-tube` | Blocked for local reuse | The AD1 inspection projection replaces the historical generic CAD's 6.5 mm slot with 6.8 ±0.05 mm, and the registered installed STEP reflects that projection. A standalone local slot recipe and interface contract remain unadmitted. |
| `forward-notched-ring` | Blocked for local reuse | The AD1 projection builds an ideal notch from `route.passage_width_mm` (4.5), `passage_depth_mm` (5) and `passage_angle_deg` (60), with proposed ±0.05 mm cut tolerance. Its registered STEP is an installed reference; proposed edge roundovers and cord contact are unverified. |
| `continuous-fin-tab` | Blocked for local reuse | The AD1 inspection projection uses the corrected 109.4 mm integral tab, superseding the generic fin generator's historical 109.8 mm field. The fin panel and tab are integral in construction, but root gussets are **separate supports**. These three source part IDs retain separate existing accounting lines; the template adds none. |

The two supported recipes declare only source-nominal, exact-parameter geometry **requests** using `src.cad.parts.tube`. They generate no asset here and cannot be varied or added to a draft through this API. Every recipe has `mass_kg: null`, `cad_execution: false`, and `draft_admission: false`. Product-specific conflicts for the motor retainer and independent recovery system have no template; the high-g board reference likewise supplies no reusable installed hardware geometry.

## Frames, features and interfaces

Each template lists explicit parameters with values, units, source path/hash/locator and any recorded proposed tolerance. Its local recipe frame is millimetres with a front-center origin and `X=body+y, Y=body-z, Z=aft along part`. Installed STEP references remain in the registered CAD frame, `X=body+y, Y=body-z, Z=station aft from nose tip; origin at nose`. A global installed mesh cannot be moved into a new draft by assuming the local frame. No source records a measured joint contact or qualified tolerance stack.

The 14 feature-source rows identify actual source part IDs, nominal feature kind, parameter keys, mates and source locators. The interface rows are navigation/evidence links: `geometry_status: nominal`, `installed_contact_status: unknown`. They are not mate constraints or finite assembly checks. Selection of the fin template preserves `fin_set` as the panel, `fin_tabs` as its integral tab account, and `root_gussets` as associated support.

Example abbreviated template record:

```json
{
  "id": "rp1-template:motor-tube-cut",
  "source_part_ids": ["motor_tube"],
  "parameters": [
    {"key": "outer_diameter_mm", "value": 31.369, "unit": "mm", "value_basis": "source_nominal", "source": {"path": "configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml", "sha256": "811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660", "locator": "parts[id=motor_tube].geometry.radius_m"}, "tolerance": null}
  ],
  "geometry": {"local_generator": "src.cad.parts.tube", "local_recipe_supported": true, "generated_asset": null, "installed_step_is_local_template": false},
  "reuse": {"geometry": "supported_nominal", "draft_admission": false},
  "mass_accounting": {"source_part_ids": ["motor_tube"], "template_mass_kg": null, "incremental_charge": false},
  "engineering_status": "open",
  "physical_verification": "open"
}
```

The example is a field excerpt; the prepared record carries the full source and revision fields. Do not treat its omitted fields as optional.

## Callable boundary and proof

- `build(root)` returns the deterministic registry and fails if any pinned source changes.
- `validate_catalog(root, payload)` compares every field to the current source projection, including nested revisions, frames, interface state and mass flags.
- `select_template(root, payload, template_id, revision_sha256, action="inspect")` admits only read-only selection of an exact template revision.
- `prepare_local_geometry_request(root, payload, template_id, revision_sha256, parameters)` returns a nonexecuting tube/annulus recipe only for the two supported cases with exact nominal parameter maps. It rejects unsupported recipes, changed values and stale source.

`tests/test_part_templates.py` exercises source coverage, the separate fin/gusset roles, actual AD1 projection versus stale generic CAD fields, the AD1 passage parameters, exact nominal parameters, installed-only STEP references, no added mass, blocked local reuse, stale revisions, altered IDs/frames/source hashes/reuse flags, source drift and deterministic prepared bytes. This is code and source-contract evidence. No new CAD output, browser interaction, interface fit, structural property, physical test or flight acceptance is claimed. Five inquiries remain UNSENT.
