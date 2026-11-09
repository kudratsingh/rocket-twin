import assert from 'node:assert/strict';
import test from 'node:test';
import { existsSync, mkdtempSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import {
  archivedCadAccess,
  fetchArchivedCad,
  fetchArchivedCadProvenance,
  ARCHIVED_CAD_REGISTRY_SHA256,
} from '../src/components/archivedCadDownload.ts';

const root = new URL('../../', import.meta.url);
const raw = readFileSync(
  new URL('docs/studies/frontend-desktop-detail-20261108/archived-cad-access.json', root),
);
const registry = JSON.parse(raw);
function document(index = 0) {
  const cfg = registry.configurations[index];
  return {
    id: cfg.id,
    identity: structuredClone(cfg.identity),
    summary: {},
    parts: cfg.parts.map((row) => ({
      id: row.id,
      material: row.material,
      learn: '',
      representation: { role: row.role },
      mesh_url: `/api/vehicles/${cfg.id}/meshes/${row.id}.glb`,
      source: {
        spec_path: cfg.path,
        shape_sha256: row.shape_sha256,
        spec_inputs: Object.entries(cfg.input_sha256).map(([path, sha256]) => ({ path, sha256 })),
      },
    })),
  };
}
test('all four tracked registries admit current parts and assemblies with explicit format/frame differences', () => {
  assert.equal(createHash('sha256').update(raw).digest('hex'), ARCHIVED_CAD_REGISTRY_SHA256);
  assert.equal(registry.configurations.length, 4);
  for (let index = 0; index < 4; index++) {
    const vehicle = document(index),
      before = JSON.stringify(vehicle);
    const access = archivedCadAccess(vehicle, vehicle.parts[0]);
    assert.equal(access.available, true);
    assert.deepEqual(
      access.files.map((file) => file.format),
      ['glb', 'step', 'stl'],
    );
    const [glb, step, stl] = access.files;
    assert.equal(glb.units, 'm');
    assert.equal(step.units, 'mm');
    assert.equal(stl.units, 'mm');
    assert.match(step.frame, /Part-local/);
    assert.match(stl.frame, /Print-oriented\/bed-packed|Part-local/);
    assert.match(stl.frame, /no encoded units/);
    assert.equal(
      step.url,
      `/engineering-workbench/archived-cad/${vehicle.id}/parts/${vehicle.parts[0].id}.step`,
    );
    assert.equal(
      access.provenanceUrl,
      `/engineering-workbench/archived-cad/${vehicle.id}/provenance.json`,
    );
    const assembly = archivedCadAccess(vehicle);
    assert.deepEqual(
      assembly.files.map((file) => file.format),
      ['glb', 'step'],
    );
    assert.match(assembly.files[1].frame, /Assembled CAD millimetres/);
    assert.equal(
      assembly.files[1].url,
      `/engineering-workbench/archived-cad/${vehicle.id}/assembly.step`,
    );
    assert.equal(JSON.stringify(vehicle), before);
  }
  assert.match(archivedCadAccess(document(1)).designStatus, /Conditional/);
  assert.match(archivedCadAccess(document(3)).designStatus, /Concept/);
});
test('foreign/spec/CAD/shape/input/role/inventory/stale-part mismatches fail closed', () => {
  for (const mutate of [
    (v) => {
      v.id = 'G80-F2-RP1-AD1-definition-v2';
    },
    (v) => {
      v.identity.configuration_id = 'foreign';
    },
    (v) => {
      v.identity.resolved_spec_sha256 = '0'.repeat(64);
    },
    (v) => {
      v.identity.cad_revision_sha256 = '0'.repeat(64);
    },
    (v) => {
      v.identity.part_shape_sha256[v.parts[0].id] = '0'.repeat(64);
    },
    (v) => {
      v.parts[0].source.shape_sha256 = '0'.repeat(64);
    },
    (v) => {
      v.parts[0].source.spec_inputs[0].sha256 = '0'.repeat(64);
    },
    (v) => {
      v.parts[0].source.spec_path = '../foreign.yaml';
    },
    (v) => {
      v.parts[0].representation.role = 'qualified_hardware';
    },
    (v) => {
      v.parts[0].mesh_url = v.parts[0].mesh_url.replace('/nose_cone.glb', '/../nose_cone.glb');
    },
    (v) => {
      v.parts.push(v.parts[0]);
    },
    (v) => {
      v.parts.pop();
    },
  ]) {
    const vehicle = document();
    mutate(vehicle);
    assert.equal(archivedCadAccess(vehicle, vehicle.parts[0]).available, false);
  }
  const vehicle = document();
  assert.equal(archivedCadAccess(vehicle, { ...vehicle.parts[0] }).available, false);
  assert.equal(archivedCadAccess(vehicle, document(1).parts[0]).available, false);
});
test('unregistered URLs/formats/parts/hashes and altered/missing/redirected bytes cannot be saved', async () => {
  const vehicle = document(),
    access = archivedCadAccess(vehicle, vehicle.parts[0]);
  const file = access.files[0];
  let calls = 0;
  const bad = async (url, options) => {
    calls++;
    assert.equal(url, file.url);
    assert.equal(options.redirect, 'error');
    assert.equal(options.credentials, 'same-origin');
    return new Response('changed');
  };
  await assert.rejects(fetchArchivedCad(file, undefined, bad), /SHA-256/);
  for (const override of [
    { configurationId: 'foreign' },
    { partId: '../nose_cone' },
    { format: 'exe' },
    { url: 'https://foreign.example/file.glb' },
    { url: file.url + '?source=elsewhere' },
    { url: file.url.replace('/parts/', '/../parts/') },
    { assetSha256: '0'.repeat(64) },
    { filename: 'unregistered.glb' },
  ])
    await assert.rejects(
      fetchArchivedCad({ ...file, ...override }, undefined, bad),
      /Unregistered/,
    );
  assert.equal(calls, 1);
  await assert.rejects(
    fetchArchivedCad(file, undefined, async () => new Response('', { status: 404 })),
    /unavailable/,
  );
  await assert.rejects(
    fetchArchivedCad(file, undefined, async () => ({ ok: true, redirected: true })),
    /redirected/,
  );
  const assembly = archivedCadAccess(vehicle);
  await assert.rejects(
    fetchArchivedCad({ ...assembly.files[1], format: 'stl' }, undefined, bad),
    /Unregistered/,
  );
  await assert.rejects(
    fetchArchivedCadProvenance({ ...access, provenanceUrl: '/arbitrary.json' }, undefined, bad),
    /Unregistered/,
  );
  const provenance = await fetchArchivedCadProvenance(
    access,
    undefined,
    async () => new Response(raw),
  );
  assert.equal(JSON.parse(new TextDecoder().decode(provenance)).total_assets, 572);
});
test('actual existing source bytes verify without requiring public assets or regenerating CAD', async (t) => {
  const source = registry.configurations[0].parts[0].assets.glb;
  if (!existsSync(new URL(source.path, root)))
    return t.skip('Original recorded local CAD bytes are not present');
  const vehicle = document();
  const file = archivedCadAccess(vehicle, vehicle.parts[0]).files[0];
  const bytes = await fetchArchivedCad(
    file,
    undefined,
    async () => new Response(readFileSync(new URL(source.path, root))),
  );
  assert.equal(bytes.byteLength, source.bytes);
});
test('preparer validates/copies only fixed files to a temporary folder, never public during hold', (t) => {
  const python = new URL('.venv/bin/python', root);
  if (
    !existsSync(python) ||
    registry.configurations.some((cfg) => !existsSync(new URL(cfg.assemblies.step.path, root)))
  )
    return t.skip('Original local archive/interpreter is not present');
  const destination = mkdtempSync(join(tmpdir(), 'archived-cad-test-'));
  try {
    const script = new URL('scripts/wo04_prepare_archived_cad_preview.py', root).pathname;
    const result = spawnSync(python.pathname, [script, '--prepare', '--destination', destination], {
      encoding: 'utf8',
      timeout: 30000,
    });
    assert.equal(result.status, 0, result.stderr);
    assert.equal(JSON.parse(result.stdout).files, 576);
    assert.deepEqual(
      readdirSync(destination).sort(),
      registry.configurations.map((cfg) => cfg.id).sort(),
    );
    for (const cfg of registry.configurations) {
      assert.equal(readdirSync(join(destination, cfg.id, 'parts')).length, cfg.part_count * 3);
      assert.deepEqual(readdirSync(join(destination, cfg.id)).sort(), [
        'assembly.glb',
        'assembly.step',
        'parts',
        'provenance.json',
      ]);
      assert.equal(
        createHash('sha256')
          .update(readFileSync(join(destination, cfg.id, 'provenance.json')))
          .digest('hex'),
        ARCHIVED_CAD_REGISTRY_SHA256,
      );
    }
  } finally {
    rmSync(destination, { recursive: true, force: true });
  }
});
test('SSR distinguishes local part STEP/print STL and assembly formats while retaining design limits', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { ArchivedCadAccess } = await server.ssrLoadModule(
      '/src/components/ArchivedCadAccess.tsx',
    );
    const render = (props) => renderToStaticMarkup(React.createElement(ArchivedCadAccess, props));
    const vehicle = document(),
      part = render({ vehicle, selectedPart: vehicle.parts[0] });
    assert.match(part, /Download recorded GLB/);
    assert.match(part, /Download recorded STEP/);
    assert.match(part, /Download recorded STL/);
    assert.match(part, /Part STEP is local CAD/);
    assert.match(part, /print-oriented or bed-packed/);
    assert.match(part, /STL does not encode units/);
    assert.match(part, /Metres/);
    assert.match(part, /Millimetres/);
    assert.match(part, /geometry has not received a new CAD readback/);
    assert.match(part, /do not authorize manufacturing/);
    const assembly = render({ vehicle });
    assert.doesNotMatch(assembly, /Download recorded STL/);
    assert.match(assembly, /Assembly STL is unavailable/);
    assert.match(render({ vehicle: document(1) }), /Conditional/);
    assert.match(render({ vehicle: document(3) }), /control gates remain open/);
    assert.match(
      render({ vehicle, selectedPart: { ...vehicle.parts[0] } }),
      /Unavailable: Selected part is stale/,
    );
  } finally {
    await server.close();
  }
});
