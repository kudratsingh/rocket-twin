import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import { connectionAxialStations, connectionNumber, connectionGraphLayout, connectionEdgeDisplay, loadF2ConnectionSnapshot, validateF2ConnectionSnapshot } from '../src/workbench/f2ConnectionStudyTypes.ts';

// Deliberately small synthetic contract; no ignored prepared export is required in CI.
const row = { label: 'Synthetic ring', function: 'Transfer fixture load', material: 'fixture plywood', mass_g: 1, z_mm: 1075, dimensions: { 'length mm': 12.2 }, state: 'estimated', notes: 'Synthetic source only.' };
const snapshot = {
  schema_version: '1.0.0', id: 'G80-F2-C1-fit-proposal-v2', status: 'Synthetic unadopted fixture; installed strength open',
  identity: { candidate_id: 'G80-F2-C1', source_identity: 'fixture-source', specification_sha256: 'fixture-spec', cad_revision: null },
  sources: [{ id: 'fixture', path: 'synthetic/fixture.json', sha256: 'fixture-hash' }],
  parts: [{ ...row, id: 'forward_ring', parameters: { front_web_m: 0.0048 } },
    { ...row, id: 'fin_tabs', label: 'Synthetic tab', z_mm: 1080.2, parameters: { front_station_m: 1.0802 } }],
  cases: [{ identity: 'G80-F2-C1-fit-proposal-v2', variant: 'C1_fit_proposal', case: 'synthetic',
    parts_mass_kg: 0.9, growth_kg: 0.05, extra_aft_kg: 0, total_mass_kg: 0.95, cg_m: null,
    margin_cal: null, guide_mps: {'1.5': null}, formal_mass_headroom_g: null, planning_mass_headroom_g: -1,
    required_whole_mean_proxy_N: null, common_acceleration_partition_N: { body: null } }],
  fits: [{ id: 'front_tab_end', minimum_mm: 0.25, nominal_mm: 0.4, maximum_mm: 0.55, criterion_mm: 0.1,
    conditional_screen_pass: true, basis: 'Unverified fixture bounds', measured: false, environmental_bounds_verified: false }],
  audit: { source_variant: 'frozen_F2', note: 'Separate old-ring audit' },
  numerical: { completed_grids: 2, required_grids: 3, status: 'stopped_node_budget', fine_nodes: 139953, node_limit: 100000, installed_strength_accepted: false },
  field_export: { active_compatible: false, three_grid_convergence: false },
  graph: { nodes: [{ id: 'ring', part_ids: ['forward_ring'], label: 'Fixture ring', note: 'Ring pulled noseward', state: 'open' },
    { id: 'tabs', part_ids: ['fin_tabs'], label: 'Fixture tab', note: 'Bonded route not capture', state: 'open' }],
    edges: [{ from: 'ring', to: 'tabs', label: 'Adhesive tension/shear', note: 'Load share unknown', state: 'open' }] },
  findings: [{ id: 'floor', label: 'Floor opens', state: 'open', note: 'No direct bearing under noseward ring pull.', part_ids: ['forward_ring','fin_tabs'] }],
};

test('proposal identity, source mapping and diagnostic incompatibility are enforced', () => {
  assert.equal(validateF2ConnectionSnapshot(snapshot), snapshot);
  assert.throws(() => validateF2ConnectionSnapshot({ ...snapshot, identity: { ...snapshot.identity, candidate_id: 'G80-F2' } }), /source identity/);
  assert.throws(() => validateF2ConnectionSnapshot({ ...snapshot, identity: { ...snapshot.identity, cad_revision: 'old32.3mm' } }), /CAD association/);
  assert.throws(() => validateF2ConnectionSnapshot({ ...snapshot, field_export: { active_compatible: true, three_grid_convergence: false } }), /field cannot attach/);
  assert.throws(() => validateF2ConnectionSnapshot({ ...snapshot, audit: { source_variant: 'C1_fit_proposal' } }), /audit source variant/);
  assert.throws(() => validateF2ConnectionSnapshot({ ...snapshot, graph: { ...snapshot.graph, edges: [{ ...snapshot.graph.edges[0], to: 'unrelated-archived-solid' }] } }), /graph edges/);
  assert.throws(() => validateF2ConnectionSnapshot({ ...snapshot, numerical: { ...snapshot.numerical, installed_strength_accepted: true } }), /numerical evidence/);
});

test('source axial parameters are converted only for display; missing stays unavailable and zero survives', () => {
  assert.deepEqual(connectionAxialStations(snapshot), { ringFront: 1075, floor: 1079.8, tabFront: 1080.2 });
  assert.equal(connectionAxialStations({ ...snapshot, parts: snapshot.parts.map((part) => ({...part, parameters: {}})) }), null);
  assert.equal(connectionNumber(null, 'N'), 'Unavailable');
  assert.equal(connectionNumber(0, 'N'), '0 N');
});

test('semantic diagram routes downward recovery and upward motor/fin arrows through outside ports', () => {
  const nodes = ['harness','eyes','ring','outer','inner','tabs','nose','motor','fins'].map((id) => ({ id }));
  const layout = connectionGraphLayout(nodes);
  const p = (id) => layout.positions.get(id);
  assert.equal(p('harness').x, p('eyes').x);
  assert.ok(p('harness').y < p('eyes').y && p('eyes').y < p('ring').y);
  assert.ok(p('nose').x < p('eyes').x);
  for (const [from,to] of [['motor','inner'],['fins','tabs']]) {
    const display = connectionEdgeDisplay(p(from),p(to));
    const arrow = display.arrow.split(' ').map((point) => point.split(',').map(Number));
    assert.ok(arrow[0][1] < arrow[1][1]);
    assert.equal(arrow[0][1], p(to).y + 94 + 4);
  }
  const down = connectionEdgeDisplay(p('harness'),p('eyes')).arrow.split(' ').map((point) => point.split(',').map(Number));
  assert.ok(down[0][1] > down[1][1]);
  const fallback = connectionGraphLayout([{id:'fixture-a'},{id:'fixture-b'}]);
  assert.equal(fallback.positions.get('fixture-a').y, fallback.positions.get('fixture-b').y);
});

test('exact missing API route alone admits prepared fallback, with validation and no C1 dependency', async () => {
  const signal = new AbortController().signal;
  const calls = [];
  const result = await loadF2ConnectionSnapshot(signal, async (path) => { calls.push(path); return path.startsWith('/api/') ? Response.json({detail:'Not Found'}, {status:404}) : Response.json(snapshot); });
  assert.equal(result.prepared, true);
  assert.deepEqual(calls, ['/api/engineering/workbench-g80-f2-c1','/engineering-workbench/f2-c1.json']);
  for (const response of [Response.json({detail:'Source missing'}, {status:404}), new Response('missing', {status:404,statusText:'Not Found'}), Response.json({detail:'Not Found'}, {status:500})]) {
    let count = 0;
    await assert.rejects(loadF2ConnectionSnapshot(signal, async () => { count++; return response; }));
    assert.equal(count, 1);
  }
  await assert.rejects(loadF2ConnectionSnapshot(signal, async () => Response.json({...snapshot,id:'old-frozen-F2'})), /identity/);
});

test('standalone SVG and linked view disclose source, pull direction, conditional fits and stopped evidence', async () => {
  const server = await createServer({ configFile: false, root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false }, appType: 'custom' });
  try {
    const { F2ConnectionStudyView, F2ConnectionGraph, F2ConnectionAxialCut } = await server.ssrLoadModule('/src/workbench/F2ConnectionStudy.tsx');
    const markup = renderToStaticMarkup(React.createElement(F2ConnectionStudyView, { snapshot }));
    const graph = renderToStaticMarkup(React.createElement(F2ConnectionGraph, { snapshot, selectedNodeId: 'ring', onSelectNode() {} }));
    const cut = renderToStaticMarkup(React.createElement(F2ConnectionAxialCut, { snapshot }));
    assert.match(graph, /fixture-source/);
    assert.match(graph, /role="button"/);
    assert.match(graph, /<polygon points=/);
    assert.doesNotMatch(graph, /marker-end|paint-order|<marker/);
    assert.match(graph, /not force magnitude or equal load allocation/);
    assert.match(cut, /1,079.8 mm/);
    assert.match(cut, /1,080.2 mm/);
    assert.match(cut, /Adhesive tension\/shear carries recovery/);
    assert.match(markup, /2 allocation rows, not qualified parts/);
    assert.match(markup, /Conditional only/);
    assert.match(markup, /frozen_F2/);
    assert.match(markup, /0.05/);
    assert.match(markup, /2 of 3 grids completed/);
    assert.match(markup, /No stress or temperature colors are attached/);
    assert.match(markup, /Unavailable/);
  } finally { await server.close(); }
});
