import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import test from 'node:test';
import {
  loadRp1Detail,
  validateRp1Detail,
  RP1_DETAIL_MANIFEST_URL,
} from '../src/components/rp1Detail.ts';

const raw = readFileSync(
  new URL('../../docs/studies/frontend-design-ux-20261108/detail-catalog.json', import.meta.url),
  'utf8',
);
const catalog = JSON.parse(raw);
const core = JSON.parse(
  readFileSync(
    new URL('../../docs/studies/rp1-inspection-geometry-20261107/manifest.json', import.meta.url),
  ),
);
function document() {
  return {
    id: core.id,
    identity: {
      specification_sha256: core.identity.specification_sha256,
      inspection_geometry_sha256: core.identity.inspection_geometry_sha256,
    },
    summary: {},
    parts: core.parts.map((p) => ({
      id: p.id,
      inspection_shape_sha256: p.inspection_shape_sha256,
      representation: { role: p.maturity },
      mesh_url: p.mesh
        ? `/api/design/${core.id}/inspection-mesh/${p.id}?spec=${core.identity.specification_sha256}&geometry=${core.identity.inspection_geometry_sha256}&mesh=${p.mesh.sha256}`
        : undefined,
    })),
  };
}
test('optionaldetail keeps55IDs/core URLs and admits only3source-supported replacements', () => {
  const doc = document(),
    before = JSON.stringify(doc);
  const result = validateRp1Detail(doc, catalog);
  assert.deepEqual(Object.keys(result.detailMeshes), ['forward_ring', 'motor_tube', 'aft_ring']);
  assert.equal(result.cases.length, 3);
  assert.equal(result.annotations.length, 10);
  assert.deepEqual(result.cases.find((c) => c.id === 'avionics-envelope').replacementPartIds, []);
  assert.ok(result.missingNotes.some((s) => s.includes('threads')));
  assert.ok(result.missingNotes.some((s) => s.includes('PCB')));
  assert.ok(result.annotations.every((a) => a.annotationOnly && a.units === 'mm'));
  assert.equal(JSON.stringify(doc), before);
});
test('foreigncore/shape/path and engineeringpromotion cannot attachoptionaldetail', () => {
  const wrong = document();
  wrong.identity.inspection_geometry_sha256 = '0'.repeat(64);
  assert.equal(validateRp1Detail(wrong, catalog), null);
  for (const mutate of [
    (p) => (p.parts[0].part_id = 'fin_set'),
    (p) => (p.parts[0].asset_path = '/outside/part.glb'),
    (p) => (p.parts[0].inspection_shape_sha256 = '0'.repeat(64)),
    (p) => (p.parts[0].display_only = false),
    (p) => (p.engineering_accepted = true),
  ]) {
    const bad = structuredClone(catalog);
    mutate(bad);
    assert.equal(validateRp1Detail(document(), bad), null);
  }
});
test('loader rejectsunrecordedmanifestbytes before anyassetload', async () => {
  const before = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => {
    calls++;
    return new Response(raw + '\n');
  };
  try {
    assert.equal(await loadRp1Detail(document()), null);
    assert.equal(calls, 1);
  } finally {
    globalThis.fetch = before;
  }
});
test('actualoptionalGLB bytes are verified before source-owned display URLs are returned', async (t) => {
  const assetPath = (url) =>
    new URL('../public' + new URL(url, 'http://local').pathname, import.meta.url);
  if (!catalog.parts.every((p) => existsSync(assetPath(p.asset_path))))
    return t.skip('Optional local display assets not exported');
  const before = globalThis.fetch;
  globalThis.fetch = async (url) =>
    new Response(url === RP1_DETAIL_MANIFEST_URL ? raw : readFileSync(assetPath(url)));
  try {
    const result = await loadRp1Detail(document());
    assert.equal(Object.keys(result.detailMeshes).length, 3);
  } finally {
    globalThis.fetch = before;
  }
});
