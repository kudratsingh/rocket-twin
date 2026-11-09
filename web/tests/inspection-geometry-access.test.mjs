import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync, existsSync } from 'node:fs';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import {
  inspectionGeometryAccess,
  fetchInspectionGeometry,
} from '../src/components/inspectionGeometryDownload.ts';
const manifest = JSON.parse(
  readFileSync(
    new URL('../../docs/studies/rp1-inspection-geometry-20261107/manifest.json', import.meta.url),
    'utf8',
  ),
);
function document() {
  return {
    id: manifest.id,
    identity: { ...manifest.identity },
    summary: {},
    parts: manifest.parts.map((row) => ({
      id: row.id,
      type: 'inspection',
      parent: null,
      material: 'source',
      learn: '',
      inspection_shape_sha256: row.inspection_shape_sha256,
      representation: { role: row.maturity },
      mesh_url: row.mesh
        ? `/api/design/${manifest.id}/inspection-mesh/${row.id}?spec=${manifest.identity.specification_sha256}&geometry=${manifest.identity.inspection_geometry_sha256}&mesh=${row.mesh.sha256}`
        : null,
    })),
  };
}
test('registered part and whole assembly expose exact geometry provenance without mutating source', () => {
  const vehicle = document(),
    before = JSON.stringify(vehicle),
    part = vehicle.parts.find((p) => p.mesh_url);
  const access = inspectionGeometryAccess(vehicle, part);
  assert.equal(access.available, true);
  assert.equal(access.url, part.mesh_url);
  assert.equal(access.provenance.inspection_shape_sha256, part.inspection_shape_sha256);
  assert.equal(access.provenance.units.glb, 'm');
  assert.equal(access.provenance.engineering_accepted, false);
  assert.match(access.filename, /--inspection-[a-f0-9]{12}\.glb$/);
  assert.match(access.provenance.limitations, /not manufacturing CAD/);
  const assembly = inspectionGeometryAccess(vehicle);
  assert.equal(assembly.available, true);
  assert.equal(assembly.assetSha256, manifest.assembly.sha256);
  assert.match(assembly.url, /inspection-mesh\/assembly\?/);
  assert.equal(Object.keys(assembly.provenance.assembly_part_shape_sha256).length, 55);
  assert.equal(JSON.stringify(vehicle), before);
});
test('source mismatch, foreign/traversing paths, query substitution, stale selection and meshless parts fail closed', () => {
  for (const mutate of [
    (v) => (v.identity.specification_sha256 = '0'.repeat(64)),
    (v) => (v.identity.inspection_geometry_sha256 = '0'.repeat(64)),
    (v) => (v.id = 'historical'),
    (v) => v.parts.push(v.parts[0]),
  ]) {
    const v = document();
    mutate(v);
    assert.equal(inspectionGeometryAccess(v, v.parts[0]).available, false);
  }
  for (const mutate of [
    (p) => (p.mesh_url = 'https://foreign.example' + p.mesh_url),
    (p) => (p.mesh_url = '//foreign.example' + p.mesh_url),
    (p) => (p.mesh_url = p.mesh_url.replace('/nose?', '/motor_tube?')),
    (p) => (p.mesh_url = p.mesh_url.replace('/nose?', '/../inspection-mesh/nose?')),
    (p) => (p.mesh_url += '&spec=wrong'),
    (p) => (p.mesh_url += '&extra=x'),
    (p) => (p.mesh_url += '#fragment'),
    (p) => (p.mesh_url = p.mesh_url.replace('spec=', 'spec=wrong')),
    (p) => (p.mesh_url = p.mesh_url.replace('mesh=', 'mesh=wrong')),
    (p) => (p.inspection_shape_sha256 = '0'.repeat(64)),
    (p) => (p.representation.role = 'manufacturing_CAD'),
  ]) {
    const v = document();
    mutate(v.parts[0]);
    assert.equal(inspectionGeometryAccess(v, v.parts[0]).available, false);
  }
  const v = document();
  assert.equal(inspectionGeometryAccess(v, { ...v.parts[0] }).available, false);
  assert.equal(
    inspectionGeometryAccess(
      v,
      v.parts.find((p) => !p.mesh_url),
    ).available,
    false,
  );
});
test('download refuses altered bytes, redirects and forged hashes before browser saving', async () => {
  const v = document(),
    access = inspectionGeometryAccess(v, v.parts[0]);
  let calls = 0;
  const fetcher = async (url, options) => {
    calls++;
    assert.equal(url, access.url);
    assert.equal(options.redirect, 'error');
    return new Response(new Uint8Array([1, 2, 3]));
  };
  await assert.rejects(fetchInspectionGeometry(access, undefined, fetcher), /SHA-256/);
  await assert.rejects(
    fetchInspectionGeometry({ ...access, assetSha256: '0'.repeat(64) }, undefined, fetcher),
    /Unregistered/,
  );
  assert.equal(calls, 1);
  await assert.rejects(
    fetchInspectionGeometry(access, undefined, async () => ({ ok: true, redirected: true })),
    /redirected/,
  );
});
test('component exposes available downloads and honest unavailable state', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { InspectionGeometryAccess } = await server.ssrLoadModule(
      '/src/components/InspectionGeometryAccess.tsx',
    );
    const v = document();
    const html = renderToStaticMarkup(
      React.createElement(InspectionGeometryAccess, { vehicle: v, selectedPart: v.parts[0] }),
    );
    assert.match(html, /Download inspection GLB/);
    assert.match(html, /Download geometry provenance JSON/);
    assert.match(html, /Manufacturing STL is unavailable/);
    assert.match(html, /inspection STEP files are listed below/);
    const unavailable = renderToStaticMarkup(
      React.createElement(InspectionGeometryAccess, {
        vehicle: v,
        selectedPart: v.parts.find((p) => !p.mesh_url),
      }),
    );
    assert.match(unavailable, /Unavailable/);
    assert.doesNotMatch(unavailable, /Download inspection GLB/);
  } finally {
    await server.close();
  }
});
const local = new URL('../../output/rp1-inspection-geometry/parts/nose.glb', import.meta.url);
test(
  'available local registered GLB bytes pass the production verifier',
  { skip: !existsSync(local) },
  async () => {
    const v = document(),
      access = inspectionGeometryAccess(v, v.parts[0]),
      bytes = readFileSync(local);
    const result = await fetchInspectionGeometry(
      access,
      undefined,
      async () => new Response(bytes),
    );
    assert.equal(result.byteLength, bytes.byteLength);
  },
);
