import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import {
  VP1_ID,
  VP1_PACKAGE_ID,
  VP1_PACKAGE_SHA256,
  VP1_CONFIG_ID,
  VP1_CONFIG_SHA256,
  VP1_PROTOCOL_SHA256,
  VP1_STAGE_IDS,
  validateVp1Validation,
  loadVp1Validation,
  vp1Money,
  vp1DraftDownload,
} from '../src/workbench/vp1Validation.ts';

const source = (path) => ({ path, sha256: 'a'.repeat(64) });
const fixture = () => ({
  schema_version: 1,
  id: VP1_ID,
  package: {
    id: VP1_PACKAGE_ID,
    path: 'configs/studies/rp1-validation-package.yaml',
    sha256: VP1_PACKAGE_SHA256,
  },
  configuration: { id: VP1_CONFIG_ID, sha256: VP1_CONFIG_SHA256 },
  protocol: { path: 'docs/validation/rp1-vp1/protocol.md', sha256: VP1_PROTOCOL_SHA256 },
  status: 'Inquiry ready; execution not authorized',
  approvals: {
    supplier_contact: false,
    purchases: false,
    physical_work: false,
    paid_service: false,
  },
  currency: 'USD',
  price_snapshot_date: '2026-11-04',
  costs: {
    room_materials_usd: '236.75',
    full_materials_usd: '269.49',
    all_in_usd: null,
    note: 'Services and delivery unquoted.',
  },
  limits: {
    fin_force_N: 331.125,
    fin_moment_Nm: 8.83,
    design_factor_already_applied: 3,
    tip_limit_mm: 1,
  },
  stages: VP1_STAGE_IDS.map((id) => ({
    id,
    label: { S0: 'Inquiries', S1: 'Room pilot', S2a: 'Conditioned samples', S2b: 'Root hold' }[id],
    status: 'not-authorized',
    scope: `${id} source scope`,
    entry: 'Written method and owner authorization required.',
    decision: 'Clock has not started. Stop at unsupported method.',
    part_ids: ['wood'],
  })),
  parts: [
    {
      id: 'wood',
      label: 'Birch strip',
      note: 'Coupon evidence is not installed acceptance.',
      status: 'unverified',
    },
  ],
  links: VP1_STAGE_IDS.map((stage_id) => ({
    stage_id,
    part_id: 'wood',
    label: 'Proposed evidence',
  })),
  messages: ['aircraft-spruce', 'loc', 'aerotech', 'west-system', 'laboratory'].map((id) => ({
    id,
    label: id,
    recipient: 'Recorded recipient',
    channel: 'Recorded inquiry channel',
    text: `UNSENT ${id}\nLiteral source <text> & 105/206\n`,
    source: source(`messages/${id}.txt`),
  })),
  materials: [
    {
      id: 'wood',
      sku: '02-20850',
      quantity: 1,
      unit: 'half sheet',
      unit_usd: 69.75,
      basis: 'Recorded listing',
      availability: 'Not reserved',
      source: 'https://example.com/material',
    },
  ],
  limitations: ['No installed fin pass; distributed-panel response unavailable.'],
  sources: [source('docs/source.md')],
});

test('frozen identities and all unapproved flags fail closed; missing prices remain unavailable', () => {
  const good = fixture();
  assert.equal(validateVp1Validation(good), good);
  for (const mutate of [
    (x) => (x.id = 'other'),
    (x) => (x.schema_version = 2),
    (x) => (x.package.sha256 = 'b'.repeat(64)),
    (x) => (x.package.path = 'other.yaml'),
    (x) => (x.package.id = 'other'),
    (x) => (x.configuration.id = 'C1'),
    (x) => (x.configuration.sha256 = 'b'.repeat(64)),
    (x) => (x.protocol.sha256 = 'b'.repeat(64)),
    ...Object.keys(good.approvals).flatMap((key) => [
      (x) => (x.approvals[key] = true),
      (x) => delete x.approvals[key],
    ]),
    (x) => (x.costs.all_in_usd = '0.00'),
    (x) => delete x.costs.all_in_usd,
    (x) => delete x.costs.full_materials_usd,
    (x) => (x.costs.room_materials_usd = -1),
    (x) => (x.price_snapshot_date = '2026-11-06'),
    (x) => (x.currency = 'GBP'),
    (x) => (x.limits.fin_force_N *= 3),
    (x) => (x.limits.fin_moment_Nm = 2.905),
    (x) => (x.limits.tip_limit_mm = 2),
    (x) => (x.limits.design_factor_already_applied = 1),
    (x) => x.stages.pop(),
    (x) => (x.stages[0].status = 'complete'),
    (x) => (x.stages[0] = x.stages[1]),
    (x) => (x.parts[0].status = 'measured'),
    (x) => (x.links[0].part_id = 'archived-cad'),
    (x) => x.links.pop(),
    (x) => x.links.push(x.links[0]),
    (x) => x.messages.pop(),
    (x) => (x.messages[0].id = '../escape'),
    (x) => (x.messages[0].source.sha256 = 'unknown'),
    (x) => (x.messages[0] = x.messages[1]),
    (x) => (x.materials[0].source = 'javascript:bad()'),
    (x) => (x.materials[0].unit_usd = NaN),
  ]) {
    const value = fixture();
    mutate(value);
    assert.throws(() => validateVp1Validation(value), /invalid or incompatible/);
  }
  good.costs.room_materials_usd = null;
  good.costs.full_materials_usd = null;
  assert.equal(validateVp1Validation(good).costs.room_materials_usd, null);
  assert.equal(vp1Money(null), 'Unavailable');
  assert.equal(vp1Money('0.00'), '$0.00 USD');
});

test('loader fetches only prepared VP1 source and preserves signal; errors never substitute another source', async () => {
  const paths = [];
  const signal = new AbortController().signal;
  const result = await loadVp1Validation(signal, async (path, options) => {
    paths.push(path);
    assert.equal(options.signal, signal);
    return new Response(JSON.stringify(fixture()));
  });
  assert.equal(result.id, VP1_ID);
  assert.deepEqual(paths, ['/engineering-workbench/rp1-validation.json']);
  for (const status of [404, 500])
    await assert.rejects(
      loadVp1Validation(signal, async () => new Response('', { status })),
      new RegExp(String(status)),
    );
  await assert.rejects(
    loadVp1Validation(signal, async () => new Response('{}')),
    /invalid or incompatible/,
  );
  await assert.rejects(
    loadVp1Validation(signal, async () => {
      throw new Error('offline');
    }),
    /offline/,
  );
});

test('individual downloads retain exact draft bytes and use local plain-text resources', () => {
  for (const message of fixture().messages) {
    const download = vp1DraftDownload(message);
    assert.equal(download.filename, `${message.id}-UNSENT.txt`);
    assert.equal(decodeURIComponent(download.href.split(',')[1]), message.text);
    assert.match(download.href, /^data:text\/plain;charset=utf-8,/);
  }
});

test('SSR review exposes stages, all five exact drafts, unavailable total and immutable acceptance boundary', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { Vp1ValidationView } = await server.ssrLoadModule(
      '/src/workbench/Vp1ValidationView.tsx',
    );
    const html = renderToStaticMarkup(
      React.createElement(Vp1ValidationView, { snapshot: fixture() }),
    );
    for (const text of [
      'UNPERFORMED',
      'NOT AUTHORIZED',
      'NOT ADOPTED',
      'Room pilot',
      'Conditioned samples',
      'Root hold',
      'SEPARATE ROOT HOLD',
      'Clock has not started',
      '$236.75 USD',
      '$269.49 USD',
      'All-in programme cost',
      'Unavailable',
      '331.125',
      '8.83',
      '1 mm',
      'already applied once',
      'no CAD association',
      'WO-03 remains open',
      'G12 PID-to-RL',
      VP1_PACKAGE_SHA256,
      VP1_CONFIG_SHA256,
    ])
      assert.ok(html.includes(text), text);
    assert.equal((html.match(/<textarea/g) ?? []).length, 5);
    assert.equal((html.match(/download="/g) ?? []).length, 5);
    assert.match(html, /aria-pressed="true"/);
    assert.match(html, /aria-live="polite"/);
    assert.match(html, /Select text for manual copy/);
    assert.match(html, /&lt;text&gt; &amp; 105\/206/);
    assert.doesNotMatch(html, /href="mailto:|<form|>Send<|>Approve<|>Execute</);
    const bad = fixture();
    bad.approvals.physical_work = true;
    const error = renderToStaticMarkup(React.createElement(Vp1ValidationView, { snapshot: bad }));
    assert.match(error, /role="alert"/);
    assert.match(error, /review unavailable/);
    assert.doesNotMatch(error, /<textarea/);
  } finally {
    await server.close();
  }
});
