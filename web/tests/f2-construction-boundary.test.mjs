import assert from 'node:assert/strict';
import test from 'node:test';
import { URL } from 'node:url';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import { f2Number, isMissingF2Route, validateF2Snapshot } from '../src/workbench/f2Types.ts';

const source = {
  id: 'fixture',
  description: 'Synthetic fixture',
  path: 'fixture.json',
  sha256: 'a'.repeat(64),
};
const component = (id, label, z0, z1, r0, r1) => ({
  id,
  label,
  category: 'airframe',
  function: `Source function for ${label}`,
  construction: 'source stock',
  material: 'source material',
  mass_g: null,
  z_start_mm: z0,
  z_end_mm: z1,
  inner_radius_mm: r0,
  outer_radius_mm: r1,
  maturity: 'concept',
  state: 'unavailable',
  source_ids: ['fixture'],
  note: 'No installed qualification',
});
const layer = (component_id, label, z_start_mm, z_end_mm, inner_radius_mm, outer_radius_mm) => ({
  component_id,
  label,
  z_start_mm,
  z_end_mm,
  inner_radius_mm,
  outer_radius_mm,
  state: 'unavailable',
  note: 'Relief unverified',
  source_ids: ['fixture'],
});
const snapshot = {
  schema_version: '1.0.0',
  id: 'synthetic-g80-f2',
  label: 'Synthetic F2 fixture',
  status: 'open',
  identity: {
    candidate_id: 'G80-F2',
    source_identity: 'sha256:test-f2',
    specification_sha256: null,
    cad_revision: null,
    frame: 'nose-tip z',
    units: 'mm, g, N',
  },
  generated_from: [source],
  components: [
    component('parachute', 'Canopy', 200, 270, null, null),
    component('body_a', 'Source stock A', 160, 700, 32.385, 33.3375),
    component('body_b', 'Source stock B', 690, 1220, 32.385, 33.3375),
    component('splice', 'Permanent bond splice', 685, 715, 30, 32.385),
    component('fin_tab', 'Notched fin tab', 1080, 1190, 15.367, 33.3375),
  ],
  sections: [
    {
      id: 'splice_station',
      label: 'Splice station',
      station_mm: 700,
      component_ids: ['body_a', 'body_b', 'splice'],
      note: 'Source section',
      source_ids: ['fixture'],
    },
  ],
  joints: [
    {
      id: 'stock_splice',
      label: 'Permanent stock splice',
      kind: 'splice bond',
      station_mm: 700,
      clearance_mm: null,
      state: 'unavailable',
      note: 'Bond and fit unverified',
      source_ids: ['fixture'],
      layers: [
        layer('body_a', 'Stock A wall', 685, 700, 32.385, 33.3375),
        layer('splice', 'Sleeve stock', 685, 715, 30, 32.385),
      ],
    },
    {
      id: 'notched_fin_ring',
      label: 'Notched fin/ring',
      kind: 'fin joint',
      station_mm: 1080,
      clearance_mm: null,
      state: 'failed',
      note: 'Notch relief missing',
      source_ids: ['fixture'],
      layers: [
        layer('fin_tab', 'Fin tab band', 1080, 1190, 15.367, 33.3375),
        layer('forward_ring', 'Forward ring band', 1075, 1088, 15.567, 32.18),
      ],
    },
  ],
  connections: [
    {
      id: 'recovery_anchor',
      label: 'Canopy to body anchor',
      from_id: 'parachute',
      to_id: 'body_anchor',
      kind: 'recovery force path',
      state: 'unavailable',
      note: 'No installed snatch test',
      source_ids: ['fixture'],
    },
    {
      id: 'body-transfer',
      label: 'Ring outer bond into body',
      from_id: 'body_anchor',
      to_id: 'body_a',
      kind: 'recorded proposed connection',
      state: 'unavailable',
      note: 'Capacity unverified',
      source_ids: ['fixture'],
    },
  ],
  sequences: { assembly: [], recovery: [] },
  cases: [
    {
      id: 'nominal',
      label: 'Nominal case',
      total_mass_g: null,
      loaded_cg_mm: null,
      reference_cp_mm: null,
      margin_cal: null,
      guide_speed_mps: null,
      usable_guide_m: 1.5,
      formal_headroom_g: null,
      planning_headroom_g: null,
      note: 'No computed result',
      source_ids: ['fixture'],
    },
  ],
  ledger: [
    {
      id: 'splice_stock',
      label: 'Splice stock',
      mass_g: null,
      station_mm: 700,
      role: 'additional stock',
      replaces_id: null,
      state: 'unavailable',
      note: 'Finished mass unknown',
      source_ids: ['fixture'],
    },
  ],
  uncertainties: [
    {
      id: 'nose_capture',
      label: 'Nose ballast capture',
      state: 'unavailable',
      note: 'No positive retention proof',
      source_ids: ['fixture'],
    },
    {
      id: 'ring-mesh',
      label: 'Ring diagnostic stopped',
      state: 'failed',
      note: 'One inverted element; no convergence or strength acceptance.',
      source_ids: ['fixture'],
    },
  ],
  cad_manifest: null,
};

test('F2 identity and CAD boundary remain separate from F1', () => {
  assert.equal(validateF2Snapshot(snapshot).identity.candidate_id, 'G80-F2');
  assert.throws(
    () =>
      validateF2Snapshot({
        ...snapshot,
        identity: { ...snapshot.identity, candidate_id: 'G80-F1' },
      }),
    /incompatible/,
  );
  assert.throws(() => validateF2Snapshot({ ...snapshot, cad_manifest: {} }), /incompatible/);
  assert.throws(
    () =>
      validateF2Snapshot({
        ...snapshot,
        joints: [
          {
            ...snapshot.joints[0],
            layers: [{ ...snapshot.joints[0].layers[0], inner_radius_mm: 'guessed' }],
          },
        ],
      }),
    /incompatible/,
  );
});

test('missing physical values and fallback boundary remain explicit', () => {
  assert.equal(f2Number(null, 'g'), 'Unavailable');
  assert.equal(f2Number(0, 'mm'), '0 mm');
  assert.equal(isMissingF2Route(404, 'Not Found'), true);
  assert.equal(isMissingF2Route(404, 'Stale source'), false);
  assert.equal(isMissingF2Route(500, 'Not Found'), false);
});

test('source-driven F2 drawings show stock, joint layers, recovery and ledger gaps', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false },
    appType: 'custom',
  });
  try {
    const { F2ArrangementDrawing, F2JointDrawing, F2RecoveryLedgerDrawing } =
      await server.ssrLoadModule('/src/workbench/F2ConstructionViews.tsx');
    const valid = validateF2Snapshot(snapshot);
    const arrangement = renderToStaticMarkup(
      React.createElement(F2ArrangementDrawing, { snapshot: valid }),
    );
    const joints = renderToStaticMarkup(React.createElement(F2JointDrawing, { snapshot: valid }));
    const recovery = renderToStaticMarkup(
      React.createElement(F2RecoveryLedgerDrawing, { snapshot: valid }),
    );
    assert.match(arrangement, /Source stock A/);
    assert.match(arrangement, /Permanent bond splice/);
    assert.match(joints, /Notched fin\/ring/);
    assert.match(joints, /Relief unverified/);
    assert.match(recovery, /Canopy to body anchor/);
    assert.match(recovery, /Ring outer bond into body/);
    assert.match(recovery, /Ring diagnostic stopped/);
    assert.match(recovery, /One inverted element/);
    assert.match(recovery, /Finished mass unknown/);
    assert.match(recovery, /Unavailable/);
    assert.doesNotMatch(arrangement, /archived-72-part/);
  } finally {
    await server.close();
  }
});
