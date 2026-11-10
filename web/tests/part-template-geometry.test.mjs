import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { createServer } from '../node_modules/vite/dist/node/index.js';

const registry = JSON.parse(
  readFileSync(new URL('./fixtures/rp1-part-templates.json', import.meta.url)),
);
const manifest = JSON.parse(
  readFileSync(
    new URL('../../docs/studies/frontend-template-bank-20261109/geometry.json', import.meta.url),
  ),
);

async function withSource(run) {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    await run(await server.ssrLoadModule('/src/parts-bank/templateGeometry.ts'));
  } finally {
    await server.close();
  }
}

test('local geometry links only its exact recipe revision and keeps assembled source assets separate', async () => {
  await withSource(({ localTemplateRepresentation }) => {
    assert.equal(manifest.step_units, 'mm');
    assert.equal(manifest.viewer_units, 'm');
    assert.equal(manifest.vehicle_adoption, false);
    for (const recipe of registry.templates) {
      const result = localTemplateRepresentation(recipe, registry);
      assert.equal(Boolean(result), recipe.geometry.local_recipe_supported);
      if (!result) continue;
      assert.equal(result.template_revision_sha256, recipe.revision_sha256);
      assert.ok(result.step.url.endsWith('.step'));
      assert.ok(result.glb.url.endsWith('.glb'));
      assert.equal(result.bounds_m.min.length, 3);
      assert.equal(
        localTemplateRepresentation({ ...recipe, revision_sha256: '0'.repeat(64) }, registry),
        null,
      );
      assert.equal(
        localTemplateRepresentation(recipe, { ...registry, revision_sha256: '0'.repeat(64) }),
        null,
      );
    }
  });
});

test('asset transport rejects foreign paths, missing bytes and corruption before parse or download', async () => {
  await withSource(async ({ verifiedTemplateAsset }) => {
    const asset = manifest.representations[0].step;
    const calls = [];
    const corrupt = async (url) => {
      calls.push(url);
      return new Response('x');
    };
    await assert.rejects(
      verifiedTemplateAsset({ ...asset, url: '/foreign.step' }, undefined, corrupt),
      /registration/,
    );
    assert.equal(calls.length, 0);
    await assert.rejects(verifiedTemplateAsset(asset, undefined, corrupt), /bytes differ/);
    assert.deepEqual(calls, [asset.url]);
    await assert.rejects(
      verifiedTemplateAsset(asset, undefined, async () => new Response('', { status: 404 })),
      /404/,
    );
  });
});
