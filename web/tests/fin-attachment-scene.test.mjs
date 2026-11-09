import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { createServer } from '../node_modules/vite/dist/node/index.js';

const bytes = readFileSync(
  new URL('../../docs/studies/frontend-fin-attachment-20261109/geometry.json', import.meta.url),
);
const catalog = JSON.parse(bytes);
const featureMap = JSON.parse(
  readFileSync(
    new URL(
      '../../docs/studies/frontend-component-depth-20261108/mechanical-feature-map.json',
      import.meta.url,
    ),
  ),
);
const step = JSON.parse(
  readFileSync(
    new URL('../../docs/studies/frontend-desktop-detail-20261108/cad-export.json', import.meta.url),
  ),
);

function vehicle() {
  const sourceParts = new Map(step.parts.map((part) => [part.id, part]));
  return {
    id: catalog.configuration_id,
    identity: {
      specification_sha256: catalog.specification_sha256,
      inspection_geometry_sha256: catalog.inspection_geometry_sha256,
    },
    parts: featureMap.stable_part_ids.map((id) => ({
      id,
      material: sourceParts.get(id)?.material ?? 'not used by joint inspector',
    })),
  };
}

async function withSource(run) {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const source = await server.ssrLoadModule('/src/fin-attachment/finAttachment.ts');
    await run(source);
  } finally {
    await server.close();
  }
}

test('admitted registered STEP sections retain exact source, parts, caps and dimensions', async () => {
  assert.equal(
    createHash('sha256').update(bytes).digest('hex'),
    '046cf7aac77cdd53882a6577f7585c44532068e23cef467126434adbd38e442c',
  );
  assert.equal(catalog.parts.length, 9);
  assert.equal(
    catalog.parts.flatMap((part) => Object.values(part.assets)).filter(Boolean).length,
    26,
  );
  assert.equal(
    catalog.parts.flatMap((part) => Object.values(part.assets)).filter((asset) => asset?.cap_url)
      .length,
    14,
  );
  assert.equal(catalog.parts.find((part) => part.id === 'forward_ring').assets.transverse, null);
  assert.deepEqual(
    catalog.dimensions.map((dimension) => [
      dimension.id,
      dimension.value_mm,
      dimension.tolerance_mm,
    ]),
    [
      ['tab-thickness', 6, null],
      ['slot-width', 6.8, 0.05],
      ['aft-gap', 0.4, null],
    ],
  );
  await withSource((source) => {
    const admitted = source.admitFinAttachmentCatalog(catalog, vehicle());
    assert.equal(admitted.ok, true, admitted.reason);
    assert.equal(admitted.catalog.download.included_part_ids.length, 9);
    assert.deepEqual(admitted.catalog.all55_part_ids, featureMap.stable_part_ids);
  });
});

test('foreign vehicle, altered STEP/source, fake cut, missing section and changed dimension are rejected', async () => {
  await withSource((source) => {
    const current = vehicle();
    const cases = [
      (copy) => {
        copy.specification_sha256 = 'a'.repeat(64);
      },
      (copy) => {
        copy.revision_sha256 = 'a'.repeat(64);
      },
      (copy) => {
        copy.parts[0].source.sha256 = 'a'.repeat(64);
      },
      (copy) => {
        copy.parts[0].assets.longitudinal.closed = false;
      },
      (copy) => {
        copy.parts[0].assets.longitudinal.cap_url = null;
      },
      (copy) => {
        copy.parts[1].assets.transverse = copy.parts[1].assets.assembled;
      },
      (copy) => {
        copy.parts[2].assets.longitudinal = null;
      },
      (copy) => {
        copy.sections[0].plane_cad_mm.offset = 1;
      },
      (copy) => {
        copy.dimensions[1].value_mm = 6.5;
      },
      (copy) => {
        copy.dimensions[1].points_m[1][2] += 0.001;
      },
      (copy) => {
        copy.all55_part_ids[0] = 'foreign';
      },
      (copy) => {
        copy.engineering_accepted = true;
      },
    ];
    for (const change of cases) {
      const copy = structuredClone(catalog);
      change(copy);
      assert.equal(source.admitFinAttachmentCatalog(copy, current).ok, false);
    }
    assert.equal(
      source.admitFinAttachmentCatalog(catalog, { ...current, id: 'modular-performance-v1' }).ok,
      false,
    );
    assert.equal(
      source.admitFinAttachmentCatalog(catalog, { ...current, parts: current.parts.slice(1) }).ok,
      false,
    );
  });
});

test('camera scope and plane guide use the local joint frame and actual source planes', async () => {
  await withSource((source) => {
    const body = catalog.parts.find((part) => part.id === 'body').assets.assembled.bounds_m;
    const focus = catalog.focus_bounds_m;
    assert.ok(body[1][1] - body[0][1] > focus[1][1] - focus[0][1]);
    assert.equal(source.sectionPlaneOutline(catalog, 'assembled'), null);
    const longitudinal = source.sectionPlaneOutline(catalog, 'longitudinal');
    assert.equal(longitudinal.length, 5);
    assert.ok(longitudinal.every((point) => point[2] === 0));
    const transverse = source.sectionPlaneOutline(catalog, 'transverse');
    assert.ok(transverse.every((point) => Math.abs(point[1] - 0.1151) < 1e-12));
    const tab = catalog.parts.find((part) => part.id === 'fin_tabs').assets.assembled.bounds_m;
    const aft = catalog.parts.find((part) => part.id === 'aft_ring').assets.assembled.bounds_m;
    const union = source.unionBounds([tab, aft]);
    assert.ok(union[0].every((value, axis) => value <= tab[0][axis] && value <= aft[0][axis]));
    assert.ok(union[1].every((value, axis) => value >= tab[1][axis] && value >= aft[1][axis]));
  });
});

test('camera drags do not select a rendered part on release', async () => {
  await withSource(source => {
    for (const value of [0, 1, 3]) assert.equal(source.isFinPickClick(value), true);
    for (const value of [4, 25, -1, NaN, Infinity]) assert.equal(source.isFinPickClick(value), false);
  });
});

test('asset bytes require source scope, exact length and SHA before a GLB URL can be created', async () => {
  await withSource(async (source) => {
    const body = Uint8Array.from([1, 4, 9, 16, 25]);
    const hash = createHash('sha256').update(body).digest('hex');
    const fetcher = async () => new Response(body);
    const url = '/engineering-workbench/rp1-fin-attachment/test.glb';
    assert.deepEqual(
      new Uint8Array(await source.verifiedFinAssetBytes(url, hash, 5, fetcher)),
      body,
    );
    await assert.rejects(source.verifiedFinAssetBytes(url, hash, 6, fetcher), /byte count/);
    await assert.rejects(source.verifiedFinAssetBytes(url, 'a'.repeat(64), 5, fetcher), /hash/);
    await assert.rejects(
      source.verifiedFinAssetBytes('/foreign/test.glb', hash, 5, fetcher),
      /scope/,
    );
  });
});
