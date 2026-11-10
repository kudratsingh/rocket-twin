import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { createServer } from '../node_modules/vite/dist/node/index.js';

const digest = (bytes) => createHash('sha256').update(bytes).digest('hex');
const fixtureBytes = readFileSync(
  new URL('./fixtures/reference-arrangement.json', import.meta.url),
);
assert.equal(
  digest(fixtureBytes),
  'b7aaa1ea524010a5c59da6a3189302bbc69904a8c3207f6e0f301b9f73092db0',
);
const fixture = JSON.parse(fixtureBytes);
const admissionBytes = readFileSync(
  new URL(
    '../../docs/studies/frontend-reference-arrangement-20261109/admission.json',
    import.meta.url,
  ),
);
assert.equal(
  digest(admissionBytes),
  '379c8072af75534d741ed3e216bca1e48abb91c30f0b1fc3d48098622d17d321',
);
const admission = JSON.parse(admissionBytes);
assert.equal(fixture.admission_sha256, digest(admissionBytes));
for (const [field, path] of [
  ['generator_sha256', '../../src/vehicle/reference_arrangement.py'],
  ['catalog_generator_sha256', '../../src/vehicle/reference_parts.py'],
]) {
  assert.equal(fixture[field], digest(readFileSync(new URL(path, import.meta.url))));
  assert.equal(admission[field], fixture[field]);
}
assert.equal(fixture.generator, 'src.vehicle.reference_arrangement.create_plan/apply_command');
assert.equal(fixture.catalog_generator, 'src.vehicle.reference_parts.build');
assert.equal(fixture.schema_version, 1);
const clone = (value) => structuredClone(value);
const envelope = (name) =>
  clone({
    catalog: fixture.catalog,
    plan: fixture.plans[name],
    action: 'preview_uninstalled_reference_arrangement',
    persisted: false,
    source_vehicle_changed: false,
  });
const response = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
const [tube, ring] = admission.definition_mappings;
const add = (base, mapping = tube) => ({
  type: 'add-reference',
  reference_id: mapping.reference_id,
  definition_revision_sha256: mapping.definition_revision_sha256,
  base_plan_revision: base.plan.revision_sha256,
});
const move = (base, coordinates) => ({
  type: 'translate-reference',
  instance_id: tube.instance_id,
  translation_mm: coordinates,
  base_plan_revision: base.plan.revision_sha256,
});
const invalid = (error) => error.code === 'invalid_response' && !error.message.includes('/Users/');

test('reference arrangement client admits actual Python source and guarded transitions', async (t) => {
  const vite = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
    logLevel: 'silent',
  });
  try {
    const source = await vite.ssrLoadModule('/src/parts-bank/referenceArrangementClient.ts');
    await t.test(
      'actual producer record is compact, source-bound and independent of a runtime Python process',
      () => {
        const { definitions, availability, ...header } = fixture.catalog;
        assert.deepEqual(header, admission.catalog_header);
        assert.deepEqual(fixture.plans.empty, admission.empty_plan);
        assert.equal(definitions.length, 2);
        assert.equal(Object.keys(fixture.plans).length, 4);
        assert.ok(
          Object.values(availability).every(
            (row) => row.status === 'unavailable' && row.generation_attempted === false,
          ),
        );
        const code = readFileSync(
          new URL('../src/parts-bank/referenceArrangementClient.ts', import.meta.url),
          'utf8',
        );
        assert.ok(!code.includes('tests/fixtures'));
        assert.ok(!code.includes('crypto.subtle') && !code.includes('createHash'));
        for (const name of Object.keys(fixture.plans)) {
          const value = envelope(name);
          const before = clone(value);
          assert.equal(source.admitArrangementEnvelope(value), value);
          assert.deepEqual(value, before);
          assert.equal(value.plan.checks.mass_credit_kg, null);
          assert.equal(value.plan.physical_inventory, null);
          assert.ok(Object.values(value.plan.readiness).every((gate) => gate === false));
        }
      },
    );
    await t.test(
      'constructor does no I/O; explicit GET, add twice and translate use tiny POST rows',
      async () => {
        const calls = [];
        const replies = ['empty', 'tube', 'both', 'translated'];
        const client = source.createReferenceArrangementClient(async (path, options) => {
          calls.push({ path, options });
          return response(envelope(replies.shift()));
        });
        assert.equal(calls.length, 0);
        const controller = new AbortController();
        const empty = await client.prepare(controller.signal);
        const tubeState = await client.command(empty, add(empty), controller.signal);
        const both = await client.command(tubeState, add(tubeState, ring), controller.signal);
        const moved = await client.command(
          both,
          move(both, [12.125, -8, 165.001]),
          controller.signal,
        );
        assert.deepEqual(moved, envelope('translated'));
        assert.deepEqual(
          calls.map(({ options }) => options.method),
          ['GET', 'POST', 'POST', 'POST'],
        );
        assert.ok(
          calls.every(
            ({ path, options }) =>
              path === '/api/reference-arrangement' &&
              options.signal === controller.signal &&
              options.cache === 'no-store',
          ),
        );
        assert.equal(calls[0].options.body, undefined);
        assert.deepEqual(calls[0].options.headers, { Accept: 'application/json' });
        assert.deepEqual(calls[1].options.headers, {
          Accept: 'application/json',
          'Content-Type': 'application/json',
        });
        assert.deepEqual(JSON.parse(calls[1].options.body), { instances: [], command: add(empty) });
        assert.deepEqual(JSON.parse(calls[3].options.body), {
          instances: both.plan.instances.map(
            ({ reference_id, definition_revision_sha256, translation_mm }) => ({
              reference_id,
              definition_revision_sha256,
              translation_mm,
            }),
          ),
          command: move(both, [12.125, -8, 165.001]),
        });
        assert.deepEqual(empty, envelope('empty'));
        assert.deepEqual(both, envelope('both'));
      },
    );
    await t.test('text parsing never rounds finer lexical input or creates zero from blank', () => {
      for (const [raw, expected] of [
        ['0', 0],
        ['-0.000', 0],
        [' 1.0000 ', 1],
        ['.125', 0.125],
        ['+500', 500],
        ['-500.000', -500],
        ['1e-3', 0.001],
        ['1000e-6', 0.001],
        ['12.125', 12.125],
      ]) {
        assert.equal(source.parseTranslationText(raw), expected);
        assert.ok(!Object.is(source.parseTranslationText(raw), -0));
      }
      for (const raw of [
        '',
        ' ',
        '.',
        'Infinity',
        'NaN',
        'true',
        '0x10',
        '1,2',
        '500.001',
        '-500.001',
        '0.0001',
        '1e-4',
        '0.00100000000000000000001',
        '500.00000000000000001',
        '1e100000',
        '--1',
        null,
        1,
      ])
        assert.throws(
          () => source.parseTranslationText(raw),
          (error) => error.code === 'invalid_translation',
        );
    });
    await t.test(
      'source headers, definitions, assets, availability and false gates fail closed',
      () => {
        const mutations = [
          (row) => {
            row.catalog.source_pins = {};
          },
          (row) => {
            row.catalog.revision_sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.catalog.extra = true;
          },
          (row) => {
            row.catalog.definitions.reverse();
          },
          (row) => {
            row.catalog.definitions[0].frames.viewer.mapping = 'identity';
          },
          (row) => {
            row.catalog.definitions[0].representation.assets.glb.sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.catalog.definitions[0].parameters_mm.length_mm = 166;
          },
          (row) => {
            row.catalog.definitions[0].unknown_properties.mass_kg = 0;
          },
          (row) => {
            row.catalog.definitions[0].readiness.add_instance_api = true;
          },
          (row) => {
            row.catalog.availability[tube.reference_id].geometry_available = true;
          },
          (row) => {
            row.catalog.availability[tube.reference_id].public_url_cache_verified = true;
          },
          (row) => {
            row.catalog.availability[tube.reference_id].missing_formats = ['glb', 'step'];
          },
          (row) => {
            row.catalog.availability.foreign = row.catalog.availability[tube.reference_id];
          },
          (row) => {
            row.persisted = 0;
          },
          (row) => {
            row.source_vehicle_changed = true;
          },
          (row) => {
            row.action = 'adopt';
          },
          (row) => {
            row.extra = {};
          },
        ];
        for (const mutate of mutations) {
          const value = envelope('both');
          mutate(value);
          assert.throws(() => source.admitArrangementEnvelope(value), invalid);
        }
      },
    );
    await t.test(
      'plan frame, nulls, fixed transforms, identity, order and translation tampering rejects',
      () => {
        const mutations = [
          (row) => {
            row.plan.frame.units = 'm';
          },
          (row) => {
            row.plan.source_pins = {};
          },
          (row) => {
            row.plan.checks.mass_credit_kg = 0;
          },
          (row) => {
            row.plan.checks.total_mass_kg = 1;
          },
          (row) => {
            row.plan.checks.results = {};
          },
          (row) => {
            row.plan.readiness.resolved_candidate = true;
          },
          (row) => {
            row.plan.readiness.flight_ready = 0;
          },
          (row) => {
            row.plan.installed_transform = [];
          },
          (row) => {
            row.plan.instances.reverse();
          },
          (row) => {
            row.plan.instances.push(clone(row.plan.instances[0]));
          },
          (row) => {
            row.plan.instances[1] = clone(row.plan.instances[0]);
          },
          (row) => {
            row.plan.instances[0].id = '../../foreign';
          },
          (row) => {
            row.plan.instances[0].quantity = true;
          },
          (row) => {
            row.plan.instances[0].rotation_quaternion_xyzw = [0, 0, 1, 0];
          },
          (row) => {
            row.plan.instances[0].scale = [1, 2, 1];
          },
          (row) => {
            row.plan.instances[0].added_to_vehicle = true;
          },
          (row) => {
            row.plan.instances[0].translation_mm = [500.001, 0, 0];
          },
          (row) => {
            row.plan.instances[0].translation_mm = [0.0001, 0, 0];
          },
          (row) => {
            row.plan.instances[0].translation_mm = [true, 0, 0];
          },
          (row) => {
            row.plan.instances[0].translation_mm = [NaN, 0, 0];
          },
          (row) => {
            row.plan.instances[0].translation_mm = [0, 0];
          },
          (row) => {
            row.plan.revision_sha256 = 'BAD';
          },
          (row) => {
            row.plan.extra = null;
          },
        ];
        for (const mutate of mutations) {
          const value = envelope('both');
          mutate(value);
          assert.throws(() => source.admitArrangementEnvelope(value), invalid);
        }
        const empty = envelope('empty');
        empty.plan.revision_sha256 = 'a'.repeat(64);
        assert.throws(() => source.admitArrangementEnvelope(empty), invalid);
      },
    );
    await t.test(
      'prepare requires the exact empty plan, while a genuine cold catalog remains admitted',
      async () => {
        await assert.rejects(
          source.createReferenceArrangementClient(async () => response(envelope('both'))).prepare(),
          invalid,
        );
        const prepared = await source
          .createReferenceArrangementClient(async () => response(envelope('empty')))
          .prepare();
        assert.equal(prepared.catalog.availability[tube.reference_id].geometry_available, false);
        assert.deepEqual(prepared.plan, admission.empty_plan);
      },
    );
    await t.test(
      'echoed base, wrong transition and stale identity cannot replace the previous view',
      async () => {
        const empty = envelope('empty');
        const tubeState = envelope('tube');
        const both = envelope('both');
        for (const reply of [empty, both]) {
          await assert.rejects(
            source
              .createReferenceArrangementClient(async () => response(reply))
              .command(empty, add(empty)),
            invalid,
          );
          assert.deepEqual(empty, envelope('empty'));
        }
        const wrongHash = envelope('both');
        wrongHash.plan.revision_sha256 = tubeState.plan.revision_sha256;
        await assert.rejects(
          source
            .createReferenceArrangementClient(async () => response(wrongHash))
            .command(tubeState, add(tubeState, ring)),
          invalid,
        );
        const wrongMove = envelope('translated');
        wrongMove.plan.instances[0].translation_mm[0] = 12;
        await assert.rejects(
          source
            .createReferenceArrangementClient(async () => response(wrongMove))
            .command(both, move(both, [12.125, -8, 165.001])),
          invalid,
        );
      },
    );
    await t.test('invalid local commands and bases send no request', async () => {
      let calls = 0;
      const client = source.createReferenceArrangementClient(async () => {
        calls++;
        return response(envelope('both'));
      });
      const base = envelope('tube');
      for (const command of [
        add(base),
        { ...add(base, ring), base_plan_revision: 'a'.repeat(64) },
        { ...add(base, ring), extra: 1 },
        { ...add(base, ring), reference_id: 'foreign' },
        { ...add(base, ring), definition_revision_sha256: 'a'.repeat(64) },
        move(base, [0.0001, 0, 0]),
        { ...move(base, [0, 0, 0]), instance_id: 'foreign' },
        { type: 'Connect', base_plan_revision: base.plan.revision_sha256 },
      ])
        await assert.rejects(
          client.command(base, command),
          (error) => error.code === 'invalid_command',
        );
      const badBase = clone(base);
      badBase.plan.readiness.flight_ready = true;
      await assert.rejects(client.command(badBase, add(badBase, ring)), invalid);
      assert.equal(calls, 0);
      assert.deepEqual(base, envelope('tube'));
    });
    await t.test(
      'no-op translation preserves opaque hash and snapshots caller state during flight',
      async () => {
        const base = envelope('tube');
        const client = source.createReferenceArrangementClient(async () => {
          base.plan.instances[0].translation_mm = [20, 0, 0];
          return response(envelope('tube'));
        });
        assert.deepEqual(await client.command(base, move(base, [0, -0, 0])), envelope('tube'));
      },
    );
    await t.test('service and transport failures are sanitized and never retried', async () => {
      for (const [status, body, code] of [
        [
          409,
          {
            detail: {
              code: 'stale_plan_revision',
              current_plan_revision: 'a'.repeat(64),
              message: '/Users/private',
            },
          },
          'stale_plan_revision',
        ],
        [
          409,
          { detail: { code: 'reference_source_unavailable', message: '/Users/private' } },
          'reference_source_unavailable',
        ],
        [
          403,
          { detail: { code: 'origin_forbidden', message: '/Users/private' } },
          'origin_forbidden',
        ],
        [
          422,
          { detail: { code: 'invalid_command', message: '/Users/private' } },
          'invalid_command',
        ],
        [
          503,
          { detail: { code: '/Users/private', message: '/Users/private' } },
          'arrangement_error',
        ],
        [404, {}, 'route_unavailable'],
        [
          409,
          { detail: { code: 'stale_plan_revision', current_plan_revision: 'BAD' } },
          'invalid_response',
        ],
      ]) {
        let calls = 0;
        const base = envelope('empty');
        const client = source.createReferenceArrangementClient(async () => {
          calls++;
          return response(body, status);
        });
        await assert.rejects(
          client.command(base, add(base)),
          (error) =>
            error.status === status &&
            error.code === code &&
            !error.message.includes('/Users/private') &&
            (code !== 'stale_plan_revision' || error.currentPlanRevision === 'a'.repeat(64)),
        );
        assert.equal(calls, 1);
        assert.deepEqual(base, envelope('empty'));
      }
      await assert.rejects(
        source
          .createReferenceArrangementClient(async () => {
            throw new Error('/Users/private');
          })
          .prepare(),
        (error) =>
          error.code === 'transport_unavailable' && !error.message.includes('/Users/private'),
      );
      await assert.rejects(
        source.createReferenceArrangementClient(async () => new Response('invalid json')).prepare(),
        invalid,
      );
      await assert.rejects(
        source
          .createReferenceArrangementClient(
            async () => new Response('<html>not found</html>', { status: 404 }),
          )
          .prepare(),
        (error) => error.code === 'route_unavailable',
      );
    });
    await t.test(
      'abort guards before I/O, after transport and after JSON prevent applying responses',
      async () => {
        let calls = 0;
        const pre = new AbortController();
        pre.abort();
        const client = source.createReferenceArrangementClient(async () => {
          calls++;
          return response(envelope('empty'));
        });
        await assert.rejects(client.prepare(pre.signal), { name: 'AbortError' });
        await assert.rejects(
          client.command(envelope('empty'), add(envelope('empty')), pre.signal),
          { name: 'AbortError' },
        );
        assert.equal(calls, 0);
        const during = new AbortController();
        await assert.rejects(
          source
            .createReferenceArrangementClient(async () => {
              during.abort();
              return response(envelope('empty'));
            })
            .prepare(during.signal),
          { name: 'AbortError' },
        );
        const parsing = new AbortController();
        await assert.rejects(
          source
            .createReferenceArrangementClient(async () => ({
              ok: true,
              status: 200,
              json: async () => {
                parsing.abort();
                return envelope('empty');
              },
            }))
            .prepare(parsing.signal),
          { name: 'AbortError' },
        );
      },
    );
  } finally {
    await vite.close();
  }
});
