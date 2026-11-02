import { createServer } from '../web/node_modules/vite/dist/node/index.js';
import React from '../web/node_modules/react/index.js';
import { renderToStaticMarkup } from '../web/node_modules/react-dom/server.node.js';
import { readFileSync, writeFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
const root = resolve(import.meta.dirname, '..');
const dataPath = 'web/public/engineering-workbench/g80-c1.json';
const doc = JSON.parse(readFileSync(resolve(root, dataPath), 'utf8'));
const originalError = console.error;
const originalWarn = console.warn;
const warnings = [];
console.error = (...args) => warnings.push(args.map(String).join(' '));
console.warn = (...args) => warnings.push(args.map(String).join(' '));
const results = [];
let server;
try {
  server = await createServer({ configFile: false, root: resolve(root, 'web'), server: { middlewareMode: true, hmr: false }, appType: 'custom' });
  for (const name of ['GeometryViews', 'MassLaunchViews', 'LoadPathViews']) {
    const mod = await server.ssrLoadModule(`/src/workbench/${name}.tsx`);
    const markup = renderToStaticMarkup(React.createElement(mod[name], { document: doc, selectedPartId: 'c1_fin_panels', onSelectPart: () => {} }));
    assert.ok(!/(?:NaN|Infinity)/.test(markup), `${name}: finite coordinates and display values`);
    assert.ok(!markup.includes('<title></title>'), `${name}: populated source tooltips`);
    assert.ok(markup.includes('engineering') && markup.includes('aria-pressed="true"'), `${name}: preliminary state and supplied part selection visible`);
    assert.ok(markup.includes('is-selected'), `${name}: selected source part highlighted`);
    const svgCount = (markup.match(/<svg\b/g) || []).length;
    assert.equal(svgCount, {GeometryViews: 7, MassLaunchViews: 6, LoadPathViews: 2}[name], `${name}: expected SVG diagrams`);
    const source = readFileSync(resolve(root, `web/src/workbench/${name}.tsx`), 'utf8');
    assert.ok(source.includes('onSelectPart') && source.includes('onKeyDown'), `${name}: mouse/keyboard selection wiring present`);
    if (name === 'GeometryViews') {
      assert.ok(markup.includes('Full longitudinal internal section') && markup.includes('Actual controlled bond/shim stack'), 'Geometry: section and undefined stack retained');
      assert.ok(markup.includes('Complete detailed CAD not supplied') || markup.includes('complete detailed CAD not supplied'), 'Geometry: complete CAD unavailable');
      assert.ok(markup.includes('Corrected calculated R1 aggregate scalar proxy') && markup.includes('1.054'), 'Geometry: corrected failed R1 motion visible');
      assert.ok(markup.includes('R1 recorded 1.039 mm aggregate: superseded receiver-lever proxy'), 'Geometry: old R1 proxy retained as superseded');
    }
    if (name === 'MassLaunchViews') {
      assert.ok(markup.includes('1,129.807') && markup.includes('0.991984'), 'Mass: recorded C1 total and adverse failed R1 stability retained');
      assert.ok(markup.includes('0.00025187'), 'Mass: tiny adverse R1 positive formal speed margin retained');
      assert.ok(markup.includes('baseline stays 1.5 m'), 'Mass: unchanged launch baseline');
      assert.ok(markup.includes('scalar energy-equivalent mean demand') && markup.includes('not a measured peak or a spatial stress field'), 'Mass: scalar-demand scope explicit');
      assert.ok(markup.includes('R1 mass-addition ledger') && markup.includes('C1 distribution is unchanged'), 'Mass: separate R1 per-item ledger exposed');
      assert.equal(doc.revision_mass_changes?.length, 14, 'Mass: all14 saved R1 additions supplied');
      assert.ok(doc.revision_mass_changes.every((row) => row.revision === 'R1' && row.state === 'estimated' && row.mass_g > 0 && Number.isFinite(row.station_mm)), 'Mass: saved positive estimated R1 rows and finite stations retained');
      assert.ok(doc.revision_mass_changes.every((row) => !row.part_ids[0] || doc.parts.some((part) => part.id === row.part_ids[0])), 'Mass: first-part selection targets valid source parts');
    }
    if (name === 'LoadPathViews') {
      assert.ok(markup.includes('SHA-256') && markup.includes(doc.generated_from.find((item) => item.id === 'source_lock').sha256), 'Load paths: frozen source hash displayed');
      assert.ok(markup.includes('R1') && markup.includes('Stopped before CAD/native analysis'), 'Load paths: R1 historical failure scope retained');
    }
    results.push({ component: name, result: 'passed', svg_count: svgCount, markup_bytes: Buffer.byteLength(markup), finite_values: true, nonempty_tooltips: true, selected_part_id: 'c1_fin_panels', selected_class_count: (markup.match(/is-selected/g) || []).length, pressed_count: (markup.match(/aria-pressed="true"/g) || []).length, selection_verification: 'Supplied selectedPartId reflected in SVG and controls; mouse/keyboard callback wiring present in source; events not executed.' });
  }
  for (const source of doc.generated_from) {
    const actual = createHash('sha256').update(readFileSync(resolve(root, source.path))).digest('hex');
    assert.equal(actual, source.sha256, `Source hash: ${source.path}`);
  }
  const exports = await server.ssrLoadModule('/src/workbench/exportSvg.ts');
  const metadata = exports.exportMetadata(doc, 'SSR source check');
  assert.equal(metadata.specification_sha256, doc.identity.specification_sha256);
  assert.equal(metadata.cad_revision, null);
  assert.deepEqual(metadata.sources, doc.generated_from);
  assert.equal(doc.launch.equipment_confirmed, false);
  assert.equal(doc.cases.filter((item) => item.id.startsWith('R1') && item.state === 'failed').length, 2);
  assert.ok(doc.historical_candidates.find((item) => item.id === 'R1')?.reason.includes('before CAD/native analysis'));
  const finJoint = doc.joints.find((joint) => joint.id === 'fin_root');
  const correctedR1 = finJoint.dimensions.find((item) => item.label.startsWith('Corrected calculated R1 aggregate'));
  const correctedC1 = finJoint.dimensions.find((item) => item.label.startsWith('Corrected calculated C1 aggregate'));
  const supersededR1 = finJoint.dimensions.find((item) => item.label.startsWith('R1 recorded 1.039'));
  assert.equal(correctedR1.state, 'failed'); assert.equal(correctedR1.value.toFixed(4), '1.0543');
  assert.equal(correctedC1.state, 'failed'); assert.equal(correctedC1.value.toFixed(4), '3.1982');
  assert.equal(supersededR1.state, 'superseded');
  assert.equal(results.reduce((total, item) => total + item.svg_count, 0), 15);
  const inventory = [...readdirSync(resolve(root, 'web/src/workbench')).map((name) => `web/src/workbench/${name}`), 'web/src/App.tsx', ...readdirSync(resolve(root, 'web/tests')).filter((name) => name.endsWith('.test.mjs')).map((name) => `web/tests/${name}`), 'tests/test_workbench_api.py', 'tests/test_workbench_export.py'].sort();
  const record = {
    schema_version: '1.0.0', recorded_at_utc: new Date().toISOString(), result: 'passed_source_and_ssr_only',
    commands: [ { command: 'make workbench', result: 'passed; actual source-checked export and source manifest written' }, { command: 'node .cache/wo04-workbench-ssr-check.mjs', result: 'passed; actual exported document rendered through existing Vite SSR' } ],
    input: { path: dataPath, id: doc.id, configuration_id: doc.identity.configuration_id, specification_sha256: doc.identity.specification_sha256, cad_revision: doc.identity.cad_revision, part_count: doc.parts.length, source_count: doc.generated_from.length, sources_hash_verified: true },
    components: results,
    source_and_r1_scope: { export_metadata_matches_document: true, all_sources_match_sha256: true, r1_cases_failed_and_historical: true, scalar_mean_demand_scope_explicit: true, absent_cad_revision_remains_null: true, launch_equipment_unconfirmed: true, no_solver_or_cad_run: true },
    revision_mass_additions: { revision: 'R1', row_count: doc.revision_mass_changes.length, recorded_added_mass_g: doc.cases.find((item) => item.id === 'R1_nominal').added_mass_g, per_item_stations_and_valid_selection_targets: true, c1_distribution_unchanged: true, browser_does_not_sum_total: true },
    scalar_motion_proxies: { corrected_c1: correctedC1, corrected_r1: correctedR1, superseded_r1: supersededR1 },
    warnings,
    source_inventory: inventory.map((path) => ({path, sha256: createHash('sha256').update(readFileSync(resolve(root, path))).digest('hex')})),
    integration_fix: { path: 'web/src/workbench/LoadPathViews.tsx', description: 'Primary-authorized React19 SVG title fix: five dynamic titles changed to one template-string child. Physical data unchanged.', reproduction: { command: 'React19 renderToStaticMarkup(svg(title(label, separator, note)))', before: '<svg><title></title></svg>', before_warning_count: 1, after: 'Actual SSR tooltips populated, no empty title elements' } },
    limitations: [ 'Non-browser source and server-render smoke only; no browser, headless browser, screenshots, computer use or visual acceptance.', 'SVG counts, finite output, source identity and selection-prop rendering verified. Actual click, keyboard event dispatch, responsive layout, SVG download and browser rendering were not exercised.', 'Vite SSR may emit a sandbox WebSocket EPERM on port24678; no port workaround was attempted. Rendering completion is recorded separately from that environment warning.', 'R1 values remain scalar recorded screens and historical failure evidence. No spatial stress, displacement, temperature or CFD field is established.', 'Complete detailed C1 CAD, installed geometry/contact/fit, real guide equipment and all engineering/physical/flight gates remain unresolved.' ],
  };
  writeFileSync(resolve(root, '.cache/wo04-workbench-source-check.json'), JSON.stringify(record, null, 2) + '\n');
  console.error = originalError; console.warn = originalWarn;
  console.log(JSON.stringify({ result: record.result, components: results.map(({component, svg_count}) => ({component, svg_count})), warnings: warnings.length, source_count: doc.generated_from.length, record: '.cache/wo04-workbench-source-check.json' }));
} finally {
  console.error = originalError; console.warn = originalWarn;
  if (server) await server.close();
}
