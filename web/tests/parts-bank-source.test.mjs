import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { createServer } from '../node_modules/vite/dist/node/index.js';

const fixtureBytes = readFileSync(new URL('./fixtures/rp1-parts-bank.json', import.meta.url));
assert.equal(
  createHash('sha256').update(fixtureBytes).digest('hex'),
  '93e0743bd8f1c7460132b13415b77425ac0a8f1ea62d98e1e871cfaa23fd85b3',
);
const fixture = JSON.parse(fixtureBytes);

function vehicle() {
  const defs = new Map(
    fixture.definitions.map((definition) => [definition.source_part_id, definition]),
  );
  return {
    id: fixture.configuration_id,
    identity: {
      specification_sha256: fixture.identity.specification_sha256,
      inspection_geometry_sha256:
        '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608',
    },
    parts: fixture.instances.map((instance) => {
      const def = defs.get(instance.id);
      return {
        id: instance.id,
        name: def.name,
        type: def.kind,
        parent: instance.source_parent_id,
        position_m: instance.position_m,
        location: { position_m: instance.position_m, lateral_offset_m: instance.lateral_offset_m },
        material: def.material,
        function: def.function,
        geometry: def.dimensions.values,
        mass_kg: def.mass_kg ?? undefined,
        cad: { role: def.source_cad_role },
        estimate: def.source_estimate,
        build: {
          method: def.manufacturing.method,
          generator: def.manufacturing.generator,
          notes: def.manufacturing.notes,
          cost_usd: def.price.amount_usd,
        },
      };
    }),
    summary: {},
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
    const source = await server.ssrLoadModule('/src/parts-bank/partsBank.ts');
    await run(source);
  } finally {
    await server.close();
  }
}

test('fixture is the source-only backend projection of the exact tracked RP1 inputs', async () => {
  assert.equal(fixture.definitions.length, 55);
  assert.equal(fixture.instances.length, 55);
  assert.equal(fixture.summary.mesh_available, 0);
  assert.equal(fixture.identity.inspection_geometry_sha256, null);
  for (const [path, expected] of [
    [fixture.identity.specification_path, fixture.identity.specification_sha256],
    [fixture.identity.definition_path, fixture.identity.definition_sha256],
    [fixture.identity.record_path, fixture.identity.record_sha256],
  ]) {
    const bytes = readFileSync(new URL(`../../${path}`, import.meta.url));
    assert.equal(createHash('sha256').update(bytes).digest('hex'), expected, path);
  }
  await withSource((source) => {
    const admitted = source.admitPartsBank(fixture, vehicle());
    assert.equal(admitted.ok, true, admitted.reason);
    assert.deepEqual(admitted.catalog.summary.by_maturity, {
      source_dimensioned: 10,
      simplified_envelope: 16,
      mass_allowance: 25,
      missing_geometry: 4,
    });
    const zero = admitted.catalog.definitions.filter(
      (definition) => definition.price.amount_usd === 0,
    );
    assert.ok(zero.length > 0);
    assert.ok(
      zero.every(
        (definition) =>
          definition.price.owner_stock_credit === false &&
          definition.issues.some((issue) => issue.id === 'zero_source_budget'),
      ),
    );
  });
});

test('catalog rejects foreign source, altered roles, duplicate IDs and broken definition-instance links', async () => {
  await withSource((source) => {
    const current = vehicle();
    const cases = [
      (copy) => {
        copy.identity.specification_sha256 = 'b'.repeat(64);
      },
      (copy) => {
        copy.identity.record_sha256 = 'b'.repeat(64);
      },
      (copy) => {
        copy.revision_sha256 = 'b'.repeat(64);
      },
      (copy) => {
        copy.definitions[0].source_part_id = 'foreign';
      },
      (copy) => {
        copy.definitions[0].source_cad_role =
          'manufactured' === copy.definitions[0].source_cad_role ? 'budget' : 'manufactured';
      },
      (copy) => {
        copy.instances[0].definition_revision_sha256 = 'b'.repeat(64);
      },
      (copy) => {
        copy.instances[1].id = copy.instances[0].id;
      },
      (copy) => {
        copy.definitions[0].price.owner_stock_credit = true;
      },
      (copy) => {
        copy.definitions.find(
          (definition) => definition.source_part_id === 'motor_retainer',
        ).issues = [];
      },
      (copy) => {
        copy.definitions[0].reuse_status = 'ready_to_drop';
      },
      (copy) => {
        copy.definitions[0].physical_verification = 'accepted';
      },
      (copy) => {
        copy.definitions[0].geometry.mesh_scope = 'installed_reference';
      },
      (copy) => {
        copy.definitions[0].geometry.reusable_local_geometry = true;
      },
      (copy) => {
        copy.definitions[0].geometry.registered_instance_id = 'foreign';
      },
      (copy) => {
        copy.capabilities.draft_builder = true;
      },
    ];
    for (const change of cases) {
      const copy = structuredClone(fixture);
      change(copy);
      assert.equal(source.admitPartsBank(copy, current).ok, false);
    }
    assert.equal(
      source.admitPartsBank(fixture, { ...current, id: 'modular-performance-v1' }).ok,
      false,
    );
    assert.equal(
      source.admitPartsBank(fixture, { ...current, parts: current.parts.slice(1) }).ok,
      false,
    );
  });
});

test('search and filters use actual current definition attributes and preserve source order', async () => {
  await withSource((source) => {
    const admitted = source.admitPartsBank(fixture, vehicle()).catalog;
    const all = source.filteredBankDefinitions(admitted, {
      query: '',
      kind: '',
      material: '',
      maturity: '',
    });
    assert.equal(all.length, 55);
    const fin = source.filteredBankDefinitions(admitted, {
      query: 'fin_tabs',
      kind: '',
      material: '',
      maturity: '',
    });
    assert.equal(fin.length, 1);
    assert.equal(fin[0].id, 'rp1:fin_tabs');
    const plywood = source.filteredBankDefinitions(admitted, {
      query: '',
      kind: '',
      material: 'plywood',
      maturity: 'source_dimensioned',
    });
    assert.ok(plywood.some((definition) => definition.source_part_id === 'fin_set'));
    assert.ok(
      plywood.every(
        (definition) =>
          definition.material === 'plywood' &&
          definition.geometry.maturity === 'source_dimensioned',
      ),
    );
    assert.equal(
      source.filteredBankDefinitions(admitted, {
        query: 'not-a-real-part',
        kind: '',
        material: '',
        maturity: '',
      }).length,
      0,
    );
  });
});

test('only an API 404 uses prepared snapshot; 500, foreign payload and network failures stay unavailable', async () => {
  await withSource(async (source) => {
    const called = [];
    const fallback = async (url) => {
      called.push(url);
      return url === source.RP1_BANK_API_URL
        ? new Response('', { status: 404 })
        : new Response(JSON.stringify(fixture), { status: 200 });
    };
    const result = await source.loadPartsBank(vehicle(), fallback);
    assert.equal(result.transport, 'prepared source snapshot');
    assert.deepEqual(called, [source.RP1_BANK_API_URL, source.RP1_BANK_PREPARED_URL]);
    const noFallback = [];
    await assert.rejects(
      source.loadPartsBank(vehicle(), async (url) => {
        noFallback.push(url);
        return new Response('', { status: 500 });
      }),
      /API unavailable \(500\)/,
    );
    assert.deepEqual(noFallback, [source.RP1_BANK_API_URL]);
    await assert.rejects(
      source.loadPartsBank(
        vehicle(),
        async () =>
          new Response(JSON.stringify({ ...fixture, configuration_id: 'foreign' }), {
            status: 200,
          }),
      ),
      /source identity/,
    );
    await assert.rejects(
      source.loadPartsBank(vehicle(), async () => {
        throw new Error('network down');
      }),
      /network down/,
    );
  });
});
