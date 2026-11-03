import assert from 'node:assert/strict';
import test from 'node:test';
import { URL } from 'node:url';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import { conventionalNumber, isMissingConventionalRoute, validateConventionalSnapshot } from '../src/workbench/conventionalG80Types.ts';

const snapshot = {
  schema_version: '1.0.0', id: 'synthetic-g80-f1', label: 'Synthetic G80-F1 fixture', status: 'open',
  identity: { candidate_id: 'G80-F1', source_identity: 'sha256:test', specification_sha256: null,
    cad_revision: null, frame: 'nose-tip z', units: 'mm, g, N' },
  generated_from: [],
  components: [{ id: 'one_body', label: 'Continuous body', category: 'airframe',
    function: 'Carry the fixed-motor arrangement.', construction: 'kraft tube', material: 'kraft',
    mass_g: null, z_start_mm: 160, z_end_mm: 920, inner_radius_mm: 32.385,
    outer_radius_mm: 33.3375, maturity: 'concept', state: 'estimated', source_ids: [], note: 'Synthetic fixture' }],
  sections: [{ id: 'aft', label: 'Fixed aft section', station_mm: 800,
    component_ids: ['one_body'], note: 'Synthetic section', source_ids: [] }],
  connections: [{ id: 'joint', label: 'Body to mount', from_id: 'one_body', to_id: 'mount',
    kind: 'proposed bond', state: 'unavailable', note: 'Capacity open', source_ids: [] }],
  sequences: { assembly: [{ id: 's1', label: 'Install mount', acts_on_ids: ['one_body'],
    state: 'estimated', note: 'Illustration', source_ids: [] }],
    recovery: [{ id: 'r1', label: 'Deploy canopy', acts_on_ids: ['one_body'],
      state: 'unavailable', note: 'Deployment unverified', source_ids: [] }] },
  cases: [{ id: 'nominal', label: 'Nominal', total_mass_g: null, loaded_cg_mm: null,
    reference_cp_mm: null, margin_cal: null, guide_speed_mps: null, usable_guide_m: 1.5,
    formal_headroom_g: null, planning_headroom_g: null, source_ids: [], note: 'No case computed' }],
  uncertainties: [{ id: 'motor_fit', label: 'Exact motor fit', state: 'unavailable',
    note: 'No supplier dimension', source_ids: [] }],
  cad_manifest: null,
};

test('G80-F1 source identity is independent and cannot claim archived CAD', () => {
  assert.equal(validateConventionalSnapshot(snapshot).identity.candidate_id, 'G80-F1');
  assert.throws(() => validateConventionalSnapshot({ ...snapshot, identity: { ...snapshot.identity, candidate_id: 'C1' } }), /incompatible/);
  assert.throws(() => validateConventionalSnapshot({ ...snapshot, identity: { ...snapshot.identity, cad_revision: 'old-cad' } }), /CAD identity/);
  assert.throws(() => validateConventionalSnapshot({ ...snapshot, schema_version: '2.0.0' }), /incompatible/);
});

test('unknown values remain unavailable; zero is retained; fallback only covers missing route', () => {
  assert.equal(conventionalNumber(null, 'g'), 'Unavailable');
  assert.equal(conventionalNumber(0, 'mm'), '0 mm');
  assert.equal(isMissingConventionalRoute(404, 'Not Found'), true);
  assert.equal(isMissingConventionalRoute(404, 'Source file missing'), false);
  assert.equal(isMissingConventionalRoute(500, 'Not Found'), false);
});

test('React drawings preserve source station, function and recovery uncertainty', async () => {
  const server = await createServer({ configFile: false, root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false }, appType: 'custom' });
  try {
    const { ConventionalArrangementDrawing, ConventionalConstructionDrawing,
      ConventionalMassDrawing, ConventionalRocketDrawing, ConventionalConnectionDrawing } =
      await server.ssrLoadModule('/src/workbench/ConventionalG80Views.tsx');
    const arrangement = renderToStaticMarkup(React.createElement(ConventionalArrangementDrawing, { snapshot }));
    const construction = renderToStaticMarkup(React.createElement(ConventionalConstructionDrawing, { snapshot }));
    const mass = renderToStaticMarkup(React.createElement(ConventionalMassDrawing, { snapshot }));
    assert.match(arrangement, /Continuous body/);
    assert.match(arrangement, /160 mm/);
    assert.match(arrangement, /920 mm/);
    assert.match(construction, /Deploy canopy/);
    assert.match(construction, /Deployment unverified/);
    assert.match(mass, /Unavailable/);
    assert.doesNotMatch(arrangement, /archived-72-part/);
    // Self-contained display fixture: generated preview exports are intentionally absent in CI.
    const component = (id, z_start_mm, z_end_mm, inner_radius_mm, outer_radius_mm, dimensions = {}) => ({
      ...snapshot.components[0], id, z_start_mm, z_end_mm, inner_radius_mm, outer_radius_mm, dimensions,
    });
    const prepared = validateConventionalSnapshot({ ...snapshot,
      components: [
        component('body', 160, 1220, 32.385, 33.3375),
        component('nose', 0, 160, 0, 33.3375),
        component('fin_set', 1075, 1205, 0, 33.3375,
          { span_mm: 60, root_chord_mm: 130, tip_chord_mm: 65, sweep_mm: 45, thickness_mm: 6.5 }),
        component('forward_ring', 1075, 1088, 15.567, 32.18),
        component('fin_tabs', 1080, 1190, 15.367, 33.3375),
      ],
      connections: [{ ...snapshot.connections[0], id: 'anchor-ring',
        from_id: 'body_recovery_eye', to_id: 'forward_ring',
        label: 'Eye → reinforced forward ring', state: 'failed' }],
    });
    const rocket = renderToStaticMarkup(React.createElement(ConventionalRocketDrawing, { snapshot: prepared }));
    const graph = renderToStaticMarkup(React.createElement(ConventionalConnectionDrawing, { snapshot: prepared }));
    assert.match(rocket, /Source envelope overlap: z 8 mm/);
    assert.match(rocket, /Fin span 60 mm/);
    assert.match(graph, /Eye → reinforced forward ring/);
    assert.match(graph, /failed/);
  } finally {
    await server.close();
  }
});
