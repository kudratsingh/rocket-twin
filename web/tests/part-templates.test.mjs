import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

const bytes = readFileSync(new URL('./fixtures/rp1-part-templates.json', import.meta.url));
const fixture = JSON.parse(bytes);
const admission = JSON.parse(
  readFileSync(
    new URL(
      '../../docs/studies/frontend-template-bank-20261109/registry-admission.json',
      import.meta.url,
    ),
  ),
);
const vehicle = () => ({
  id: fixture.configuration_id,
  identity: {
    specification_sha256: fixture.identity.specification.sha256,
    inspection_geometry_sha256: '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608',
  },
  parts: fixture.all55_part_ids.map((id) => ({ id })),
});

async function withSource(run) {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const source = await server.ssrLoadModule('/src/parts-bank/templateBank.ts');
    const component = await server.ssrLoadModule('/src/parts-bank/TemplateBankPanel.tsx');
    await run(source, component);
  } finally {
    await server.close();
  }
}

test('template fixture is pinned to actual frozen source bytes and never adds mass charges', () => {
  assert.equal(createHash('sha256').update(bytes).digest('hex'), admission.prepared_sha256);
  assert.equal(fixture.revision_sha256, admission.revision_sha256);
  for (const source of Object.values(fixture.identity)) {
    assert.equal(
      createHash('sha256')
        .update(readFileSync(new URL(`../../${source.path}`, import.meta.url)))
        .digest('hex'),
      source.sha256,
      source.path,
    );
  }
  assert.equal(fixture.dispositions.length, 55);
  assert.equal(new Set(fixture.dispositions.map((row) => row.source_part_id)).size, 55);
  assert.equal(fixture.feature_sources.length, 14);
  assert.ok(
    fixture.templates.every(
      (row) =>
        row.mass_accounting.template_mass_kg === null &&
        row.mass_accounting.incremental_charge === false,
    ),
  );
  assert.equal(
    fixture.dispositions.find((row) => row.source_part_id === 'root_gussets').template_role,
    'associated_support',
  );
  assert.ok(
    fixture.dispositions
      .find((row) => row.source_part_id === 'motor_retainer')
      .reason.includes('19002/009750'),
  );
});

test('prepared nominal recipes load only with matching current design, exact bytes and 55 unique source parts', async () => {
  await withSource(async (source) => {
    const calls = [];
    const result = await source.loadTemplateRegistry(vehicle(), async (path) => {
      calls.push(path);
      return new Response(bytes);
    });
    assert.deepEqual(calls, [admission.prepared_path]);
    assert.equal(result.templates.length, 5);
    assert.deepEqual(
      result.templates
        .filter((row) => row.geometry.local_recipe_supported)
        .map((row) => row.family),
      ['tube_cut', 'annular_ring'],
    );
    for (const change of [
      (v) => {
        v.id = 'modular-performance-v1';
      },
      (v) => {
        v.identity.specification_sha256 = '0'.repeat(64);
      },
      (v) => {
        v.identity.inspection_geometry_sha256 = null;
      },
      (v) => {
        v.parts[1].id = v.parts[0].id;
      },
    ]) {
      const v = vehicle();
      change(v);
      await assert.rejects(
        source.loadTemplateRegistry(v, async () => new Response(bytes)),
        /exact current|coverage/,
      );
    }
  });
});

test('altered dimensions, stale content and transport errors stay unavailable without fallback', async () => {
  await withSource(async (source) => {
    const changed = structuredClone(fixture);
    changed.templates[0].parameters[0].value += 1;
    await assert.rejects(
      source.loadTemplateRegistry(vehicle(), async () => Response.json(changed)),
      /bytes differ/,
    );
    await assert.rejects(
      source.loadTemplateRegistry(vehicle(), async () => new Response('{}')),
      /bytes differ/,
    );
    for (const status of [404, 409, 500]) {
      const calls = [];
      await assert.rejects(
        source.loadTemplateRegistry(vehicle(), async (path) => {
          calls.push(path);
          return new Response('', { status });
        }),
        new RegExp(String(status)),
      );
      assert.equal(calls.length, 1);
    }
  });
});

test('template details distinguish exact source geometry from unavailable stock/joint/asset evidence', async () => {
  await withSource((source, { TemplateRecipeDetail }) => {
    const render = (id) =>
      renderToStaticMarkup(
        React.createElement(TemplateRecipeDetail, {
          recipe: fixture.templates.find((row) => row.id === `rp1-template:${id}`),
          registry: fixture,
          onInspect() {},
        }),
      );
    const tube = render('motor-tube-cut');
    assert.match(tube, /Nominal local geometry recipe supported/);
    assert.match(tube, /Inspect installed motor_tube/);
    assert.match(tube, /31\.369 mm/);
    assert.match(tube, /tolerance unavailable/);
    assert.match(tube, /installed contact: unknown/);
    assert.match(tube, /None charged; source mass is counted once/);
    const fin = render('continuous-fin-tab');
    assert.match(fin, /Local geometry recipe blocked/);
    assert.match(fin, /6 mm/);
    assert.match(fin, /109\.4 mm/);
    assert.match(render('slotted-body-tube'), /6\.8 mm/);
    assert.match(fin, /Inspect installed fin_set/);
    assert.match(fin, /Separate local asset/);
    assert.doesNotMatch(fin, /Download.*STEP|Add part|Replace part|Engineering pass/);
    assert.match(
      source.sourceLink(fixture.templates[0].parameters[0].source),
      /07552bd1425dce4cf0b47af56c70b44a9500625e/,
    );
  });
});
