import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { createServer } from '../node_modules/vite/dist/node/index.js';

const bytes = readFileSync(
  new URL(
    '../../docs/studies/frontend-component-depth-20261108/mechanical-detail-layout.json',
    import.meta.url,
  ),
);
assert.equal(
  createHash('sha256').update(bytes).digest('hex'),
  '1044bc7aeacad0802fe74add1fecbc77aeddcd0ed09f493c685bb639d271eda1',
  'tracked mechanical catalog must remain byte-identical to the verified child export',
);
const catalog = JSON.parse(bytes);
const exact = {
  configurationId: 'G80-F2-RP1-AD1-definition-v2',
  specificationSha256: '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660',
  inspectionGeometrySha256: '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608',
};

async function withSource(run) {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const source = await server.ssrLoadModule('/src/components/rp1MechanicalReference.ts');
    await run(source);
  } finally {
    await server.close();
  }
}

test('tracked source catalog admits exactly seven current parents and 18 actual child pieces', async () => {
  await withSource((source) => {
    const admitted = source.admitRp1MechanicalLayout(catalog, exact);
    assert.equal(admitted.ok, true, admitted.reason);
    assert.equal(admitted.layout.all55_part_ids.length, 55);
    assert.equal(admitted.layout.units, 'm');
    assert.equal(admitted.layout.viewer_frame, 'X=body+y, Y=length-station, Z=body-z');
    assert.deepEqual(
      Object.fromEntries(
        admitted.layout.parents.map((parent) => [
          parent.id,
          admitted.layout.children.filter((child) => child.parent_part_id === parent.id).length,
        ]),
      ),
      {
        fin_set: 3,
        fin_tabs: 3,
        root_gussets: 6,
        body: 1,
        motor_tube: 1,
        aft_ring: 1,
        forward_ring: 3,
      },
    );
    assert.equal(
      admitted.layout.children.find((child) => child.id === 'forward_ring:bond_reservation')
        .visual_bond_reservation_only,
      true,
    );
    assert.equal(
      admitted.layout.children.find((child) => child.id === 'forward_ring:bond_reservation')
        .material,
      'Unspecified bond reservation (display only)',
    );
    assert.ok(
      admitted.layout.children.every((child) =>
        child.url.startsWith('/engineering-workbench/rp1-component-detail/'),
      ),
    );
  });
});

test('source tuple, all 55 IDs, parent mesh source and child fingerprint reject foreign or stale layouts', async () => {
  await withSource((source) => {
    for (const changed of [
      { ...exact, configurationId: 'modular-performance-v1' },
      { ...exact, specificationSha256: 'b'.repeat(64) },
      { ...exact, inspectionGeometrySha256: 'b'.repeat(64) },
    ])
      assert.equal(source.admitRp1MechanicalLayout(catalog, changed).ok, false);
    const cases = [
      (copy) => {
        copy.all55_part_ids[0] = 'foreign';
      },
      (copy) => {
        copy.parents[0].core_mesh_sha256 = 'b'.repeat(64);
      },
      (copy) => {
        copy.parents[0].source_mesh_sha256 = 'b'.repeat(64);
      },
      (copy) => {
        copy.children[0].source_mesh_sha256 = 'b'.repeat(64);
      },
      (copy) => {
        copy.children[0].sha256 = 'not-a-hash';
      },
      (copy) => {
        copy.children[0].bounds_m[0][0] = -1;
      },
      (copy) => {
        copy.children[0].parent_part_id = 'foreign';
      },
      (copy) => {
        copy.children[0].id = 'fin_set:invented-panel';
        copy.children[0].sub_id = 'invented-panel';
      },
      (copy) => {
        copy.children[0].url = 'https://foreign.example/child.glb';
      },
      (copy) => {
        copy.children.push({ ...copy.children[0], id: 'foreign:piece', parent_part_id: 'foreign' });
      },
      (copy) => {
        copy.children.find((child) => child.id === 'forward_ring:bond_reservation').material =
          'plywood';
      },
    ];
    for (const change of cases) {
      const copy = structuredClone(catalog);
      change(copy);
      assert.equal(source.admitRp1MechanicalLayout(copy, exact).ok, false);
    }
  });
});

test('recorded child unions stay inside source parent bounds; separation is limited display translation', async () => {
  await withSource((source) => {
    const layout = source.admitRp1MechanicalLayout(catalog, exact).layout;
    for (const parent of layout.parents) {
      const pieces = layout.children.filter((child) => child.parent_part_id === parent.id);
      const union = source.boundsUnion(pieces.map((child) => child.bounds_m));
      assert.deepEqual(union, parent.bounds_m);
      for (const child of pieces) {
        assert.deepEqual(source.displayOffset(child, 0), [0, 0, 0]);
        const offset = source.displayOffset(child, 1);
        assert.equal(offset[1], 0);
        assert.ok(Math.hypot(...offset) <= 0.018000001);
        assert.deepEqual(source.displayOffset(child, Number.NaN), [0, 0, 0]);
        if (!['fin_set', 'fin_tabs', 'root_gussets'].includes(child.parent_part_id))
          assert.deepEqual(offset, [0, 0, 0]);
      }
    }
  });
});

test('camera scopes follow positive and negative display offsets while source bounds stay fixed', async () => {
  await withSource((source) => {
    const layout = source.admitRp1MechanicalLayout(catalog, exact).layout;
    const panels = layout.children.filter((child) => child.parent_part_id === 'fin_set');
    const sourceBounds = panels.map((panel) => structuredClone(panel.bounds_m));
    const positive = panels.find((panel) => panel.id === 'fin_set:panel-01');
    const negative = panels.find((panel) => panel.id === 'fin_set:panel-02');
    const positiveOffset = source.displayOffset(positive, 1);
    const negativeOffset = source.displayOffset(negative, 1);
    assert.ok(positiveOffset[0] > 0);
    assert.ok(negativeOffset[0] < 0 && negativeOffset[2] > 0);
    assert.deepEqual(source.displayedChildBounds(positive, 0), positive.bounds_m);
    assert.equal(
      source.displayedChildBounds(positive, 1)[1][0],
      positive.bounds_m[1][0] + positiveOffset[0],
    );
    assert.equal(
      source.displayedChildBounds(negative, 1)[0][0],
      negative.bounds_m[0][0] + negativeOffset[0],
    );
    assert.equal(
      source.displayedChildBounds(negative, 0.5)[1][2],
      negative.bounds_m[1][2] + negativeOffset[2] / 2,
    );
    const originalUnion = source.boundsUnion(panels.map((panel) => panel.bounds_m));
    const displayUnion = source.displayedChildrenBounds(panels, 1);
    assert.deepEqual(source.displayedChildrenBounds(panels, 0), originalUnion);
    assert.ok(displayUnion[0][0] < originalUnion[0][0]);
    assert.ok(displayUnion[1][0] > originalUnion[1][0]);
    assert.ok(displayUnion[1][2] > originalUnion[1][2]);
    assert.deepEqual(
      panels.map((panel) => panel.bounds_m),
      sourceBounds,
    );
  });
});

test('asset verifier compares exact SHA-256 before returning a loadable blob URL', async () => {
  await withSource(async (source) => {
    const child = catalog.children[0];
    const content = new Uint8Array([1, 2, 3, 4]);
    const hash = createHash('sha256').update(content).digest('hex');
    const fetcher = async () => ({ ok: true, arrayBuffer: async () => content.buffer });
    await assert.rejects(source.verifiedMechanicalBlobUrl(child, fetcher), /fingerprint differs/);
    const url = await source.verifiedMechanicalBlobUrl({ ...child, sha256: hash }, fetcher);
    assert.match(url, /^blob:/);
    URL.revokeObjectURL(url);
    await assert.rejects(
      source.verifiedMechanicalBlobUrl(child, async () => ({ ok: false, status: 404 })),
      /unavailable \(404\)/,
    );
  });
});
