import assert from 'node:assert/strict';
import test from 'node:test';
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import {
  inspectionStepAccess,
  inspectionJointStepAccess,
  fetchInspectionStep,
  fetchInspectionStepProvenance,
  INSPECTION_STEP_PROVENANCE_SHA256,
} from '../src/components/inspectionStepDownload.ts';

const root = new URL('../../', import.meta.url);
const core = JSON.parse(
  readFileSync(new URL('docs/studies/rp1-inspection-geometry-20261107/manifest.json', root)),
);
const raw = readFileSync(
  new URL('docs/studies/frontend-desktop-detail-20261108/cad-export.json', root),
);
const packet = JSON.parse(raw);
function document() {
  return {
    id: core.id,
    identity: { ...core.identity },
    summary: {},
    parts: core.parts.map((row) => ({
      id: row.id,
      material: 'source',
      inspection_shape_sha256: row.inspection_shape_sha256,
      representation: { role: row.maturity },
      mesh_url: row.mesh
        ? `/api/design/${core.id}/inspection-mesh/${row.id}?spec=${core.identity.specification_sha256}&geometry=${core.identity.inspection_geometry_sha256}&mesh=${row.mesh.sha256}`
        : null,
    })),
  };
}
test('joint download is the exact registered nine-record assembled mm STEP, never camera or section output', async (t) => {
  const access = inspectionJointStepAccess(document());
  assert.equal(access.available, true);
  assert.equal(access.joint, true);
  const row = packet.assemblies.find((item) => item.id === 'critical_motor_fin_ring_joint');
  assert.equal(row.part_ids.length, 9);
  assert.equal(access.assetSha256, row.sha256);
  assert.equal(access.url, '/engineering-workbench/rp1-step/critical_motor_fin_ring_joint.step');
  if (!existsSync(new URL(row.path, root))) return t.skip('Registered generated STEP bytes are local only; metadata admission checked above.');
  const saved = readFileSync(new URL(row.path, root));
  const actual = await fetchInspectionStep(access, undefined, async url => {
    assert.equal(url, access.url);
    return new Response(saved);
  });
  assert.equal(createHash('sha256').update(Buffer.from(actual)).digest('hex'), row.sha256);
  assert.match(new TextDecoder().decode(actual), /SI_UNIT\(\.MILLI\.,\.METRE\.\)/);
  await assert.rejects(fetchInspectionStep({...access, url: access.url + '?section=transverse'}), /Unregistered/);
  const foreign = document(); foreign.identity.specification_sha256 = '0'.repeat(64);
  assert.equal(inspectionJointStepAccess(foreign).available, false);
});
test('registered source parts and whole assembly use fixed static STEP paths and CAD mm provenance', () => {
  assert.equal(createHash('sha256').update(raw).digest('hex'), INSPECTION_STEP_PROVENANCE_SHA256);
  const vehicle = document(),
    before = JSON.stringify(vehicle);
  const part = vehicle.parts.find((item) => item.id === 'motor_tube');
  const access = inspectionStepAccess(vehicle, part);
  assert.equal(access.available, true);
  assert.equal(access.url, '/engineering-workbench/rp1-step/parts/motor_tube.step');
  assert.equal(access.assetSha256, packet.parts.find((item) => item.id === part.id).sha256);
  assert.equal(access.units, 'mm');
  assert.match(access.cadFrame, /Z=station aft from nose tip/);
  assert.match(access.viewerMapping, /length_m-cadZ\/1000/);
  assert.ok(access.limitations.some((text) => /not manufacturing-ready/.test(text)));
  assert.equal(access.provenanceUrl, '/engineering-workbench/rp1-step/provenance.json');
  const assembly = inspectionStepAccess(vehicle);
  assert.equal(
    assembly.url,
    '/engineering-workbench/rp1-step/rp1_ad1_v2_inspection_26_records.step',
  );
  assert.equal(assembly.partId, null);
  assert.equal(JSON.stringify(vehicle), before);
});
test('foreign source, stale part, missing geometry, wrong maturity and mesh URL fail closed', () => {
  for (const mutate of [
    (v) => {
      v.id = 'historical';
    },
    (v) => {
      v.identity.specification_sha256 = '0'.repeat(64);
    },
    (v) => {
      v.identity.inspection_geometry_sha256 = '0'.repeat(64);
    },
    (v) => {
      v.parts[0].inspection_shape_sha256 = '0'.repeat(64);
    },
    (v) => {
      v.parts[0].representation.role = 'qualified_manufactured';
    },
    (v) => {
      v.parts[0].mesh_url = 'https://foreign.example/model.step';
    },
    (v) => {
      v.parts.pop();
    },
  ]) {
    const vehicle = document();
    mutate(vehicle);
    assert.equal(inspectionStepAccess(vehicle).available, false);
  }
  const vehicle = document();
  assert.equal(inspectionStepAccess(vehicle, { ...vehicle.parts[0] }).available, false);
  assert.equal(
    inspectionStepAccess(
      vehicle,
      vehicle.parts.find((part) => !part.mesh_url),
    ).available,
    false,
  );
});
test('missing, altered, redirected and forged STEP/provenance assets refuse download', async () => {
  const access = inspectionStepAccess(document());
  let calls = 0;
  const bad = async (url, options) => {
    calls++;
    assert.equal(url, access.url);
    assert.equal(options.redirect, 'error');
    assert.equal(options.credentials, 'same-origin');
    return new Response('wrong bytes');
  };
  await assert.rejects(fetchInspectionStep(access, undefined, bad), /SHA-256/);
  await assert.rejects(
    fetchInspectionStep(access, undefined, async () => new Response('', { status: 404 })),
    /unavailable/,
  );
  await assert.rejects(
    fetchInspectionStep(access, undefined, async () => ({ ok: true, redirected: true })),
    /redirected/,
  );
  for (const override of [
    { url: 'https://foreign.example/test.step' },
    { url: access.url + '?source=arbitrary' },
    { assetSha256: '0'.repeat(64) },
    { partId: '../other' },
    { provenanceUrl: '/arbitrary.json' },
  ])
    await assert.rejects(
      fetchInspectionStep({ ...access, ...override }, undefined, bad),
      /Unregistered/,
    );
  assert.equal(calls, 1);
  await assert.rejects(
    fetchInspectionStepProvenance(
      access,
      undefined,
      async () => new Response(raw.toString() + '\n'),
    ),
    /SHA-256/,
  );
  const provenance = await fetchInspectionStepProvenance(
    access,
    undefined,
    async () => new Response(raw),
  );
  assert.equal(JSON.parse(new TextDecoder().decode(provenance)).units.step, 'mm');
});
test('actual fixed-source STEP bytes verify without regeneration', async (t) => {
  const vehicle = document(),
    part = vehicle.parts.find((item) => item.id === 'motor_tube');
  const row = packet.parts.find((item) => item.id === 'motor_tube');
  const path = new URL(row.path, root);
  if (!existsSync(path)) return t.skip('Original bounded STEP packet is not locally present');
  const bytes = await fetchInspectionStep(
    inspectionStepAccess(vehicle, part),
    undefined,
    async () => new Response(readFileSync(path)),
  );
  const text = new TextDecoder().decode(bytes);
  assert.match(text, /^ISO-10303-21;/);
  assert.match(text, /SI_UNIT\(\.MILLI\.,\.METRE\.\)/);
});
test('preparation copies only registered verified assets into a temporary folder, never public during hold', (t) => {
  const python = new URL('.venv/bin/python', root);
  if (!existsSync(python) || !existsSync(new URL(packet.parts[0].path, root)))
    return t.skip('Original local packet/interpreter unavailable');
  const destination = mkdtempSync(join(tmpdir(), 'rp1-step-preview-test-'));
  try {
    const result = spawnSync(
      python.pathname,
      [
        new URL('scripts/wo04_prepare_inspection_step_preview.py', root).pathname,
        '--prepare',
        '--destination',
        destination,
      ],
      { encoding: 'utf8' },
    );
    assert.equal(result.status, 0, result.stderr);
    assert.equal(JSON.parse(result.stdout).files, 29);
    assert.equal(readdirSync(join(destination, 'parts')).length, 26);
    assert.deepEqual(readdirSync(destination).sort(), [
      'critical_motor_fin_ring_joint.step',
      'parts',
      'provenance.json',
      'rp1_ad1_v2_inspection_26_records.step',
    ]);
    assert.equal(
      createHash('sha256')
        .update(readFileSync(join(destination, 'provenance.json')))
        .digest('hex'),
      INSPECTION_STEP_PROVENANCE_SHA256,
    );
    const repeat = spawnSync(
      python.pathname,
      [
        new URL('scripts/wo04_prepare_inspection_step_preview.py', root).pathname,
        '--prepare',
        '--destination',
        destination,
      ],
      { encoding: 'utf8' },
    );
    assert.equal(repeat.status, 0, repeat.stderr);
    writeFileSync(join(destination, 'critical_motor_fin_ring_joint.step'), 'changed bytes');
    const changed = spawnSync(python.pathname, [new URL('scripts/wo04_prepare_inspection_step_preview.py', root).pathname, '--prepare', '--destination', destination], {encoding:'utf8'});
    assert.notEqual(changed.status, 0);
    assert.match(changed.stderr, /unregistered or changed bytes/);
  } finally {
    rmSync(destination, { recursive: true, force: true });
  }
});
test('component identifies inspection reconstruction, source mm and remaining installed/manufacturing limits', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { InspectionStepAccess } = await server.ssrLoadModule(
      '/src/components/InspectionStepAccess.tsx',
    );
    const html = renderToStaticMarkup(
      React.createElement(InspectionStepAccess, { vehicle: document() }),
    );
    assert.match(html, /Download inspection STEP/);
    assert.match(html, /Download STEP provenance JSON/);
    assert.match(html, /CAD millimetres/);
    assert.match(html, /Origin at nose tip; Z increases aft/);
    assert.match(html, /not manufacturing-ready or installed-qualified/);
    assert.match(html, /source-dimensioned|source dimensioned|source_dimensioned/);
  } finally {
    await server.close();
  }
});
