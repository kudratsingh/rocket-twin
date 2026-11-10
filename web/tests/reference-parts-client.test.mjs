import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { createServer } from '../node_modules/vite/dist/node/index.js';

const bytes = readFileSync(new URL('./fixtures/reference-parts.json', import.meta.url));
assert.equal(
  createHash('sha256').update(bytes).digest('hex'),
  '5db095fc80474ce25b1c0bb70087ca9c49abe4d696227a5b4810e4e6abfcd838',
);
const fixture = JSON.parse(bytes);
const manifest = JSON.parse(
  readFileSync(
    new URL('../../docs/studies/frontend-template-bank-20261109/geometry.json', import.meta.url),
  ),
);
// Exact detail projection of the actual Python build fixture, matching the new
// router's select_reference result plus catalog identity. No runtime Python.
const actual = fixture.catalog.definitions.map((definition) => ({
  definition,
  availability: fixture.availability[definition.id],
  action: 'inspect_geometry_reference',
  instance_created: false,
  engineering_accepted: false,
  simulation_eligible: false,
  flight_ready: false,
  catalog_id: fixture.catalog.id,
  catalog_revision_sha256: fixture.catalog.revision_sha256,
  scope: fixture.catalog.scope,
}));
const clone = (value) => structuredClone(value);
const response = (value, status = 200) =>
  new Response(JSON.stringify(value), { status, headers: { 'content-type': 'application/json' } });
const representationFor = (row) =>
  manifest.representations.find((item) => item.template_id === row.definition.source_template_id);

test('reference detail client uses exact live GET and actual frozen source DTOs', async (t) => {
  const vite = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
    logLevel: 'silent',
  });
  try {
    const source = await vite.ssrLoadModule('/src/parts-bank/referencePartsClient.ts');
    await t.test(
      'exact two source mappings, actual detail admission and explicit GET with signal',
      async () => {
        for (const row of actual) {
          const templateId = row.definition.source_template_id;
          const representation = representationFor(row);
          const identity = source.referencePartForTemplate(templateId);
          assert.deepEqual(identity, {
            referenceId: row.definition.id,
            revision: row.definition.revision_sha256,
            templateId,
            templateRevision: row.definition.source_template_revision_sha256,
          });
          assert.equal(source.admitReferencePartDetail(row, templateId, representation), row);
          const calls = [];
          const controller = new AbortController();
          const client = source.createReferencePartsClient(async (path, options) => {
            calls.push({ path, options });
            return response(row);
          });
          assert.equal(calls.length, 0);
          assert.deepEqual(
            await client.readForTemplate(templateId, representation, controller.signal),
            row,
          );
          assert.equal(calls.length, 1);
          assert.equal(
            calls[0].path,
            `/api/reference-parts/${row.definition.id}/${row.definition.revision_sha256}`,
          );
          assert.deepEqual(calls[0].options, {
            method: 'GET',
            signal: controller.signal,
            cache: 'no-store',
            headers: { Accept: 'application/json' },
          });
          identity.revision = 'a'.repeat(64);
          assert.equal(
            source.referencePartForTemplate(templateId).revision,
            row.definition.revision_sha256,
          );
        }
      },
    );
    await t.test(
      'unavailable cache remains an explicit admitted state, never a substituted model',
      async () => {
        for (const missing of [['step'], ['glb'], ['step', 'glb']]) {
          const row = clone(actual[0]);
          row.availability = {
            status: 'unavailable',
            missing_formats: missing,
            geometry_available: false,
            public_url_cache_verified: false,
            generation_attempted: false,
            reason: 'Required local cache absent; no regeneration',
          };
          const client = source.createReferencePartsClient(async () => response(row));
          const detail = await client.readForTemplate(row.definition.source_template_id);
          assert.equal(detail.availability.status, 'unavailable');
          assert.equal(detail.availability.geometry_available, false);
          assert.deepEqual(detail.definition, actual[0].definition);
          assert.equal(detail.instance_created, false);
          assert.equal(detail.flight_ready, false);
        }
      },
    );
    await t.test(
      'foreign source/catalog/revision/frame/assets and nonliteral gates fail closed',
      () => {
        const mutations = [
          (row) => {
            row.catalog_id = 'foreign';
          },
          (row) => {
            row.catalog_revision_sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.scope = 'installed';
          },
          (row) => {
            row.action = 'add_instance';
          },
          (row) => {
            row.instance_created = 0;
          },
          (row) => {
            row.engineering_accepted = true;
          },
          (row) => {
            row.simulation_eligible = 0;
          },
          (row) => {
            row.flight_ready = true;
          },
          (row) => {
            row.definition = clone(actual[1].definition);
          },
          (row) => {
            row.definition.revision_sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.definition.frames.viewer.mapping = 'viewer=cad';
          },
          (row) => {
            row.definition.parameters_mm.length_mm = 200;
          },
          (row) => {
            row.definition.provenance.specification_sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.definition.representation.assets.glb.sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.definition.unknown_properties.mass_kg = 0;
          },
          (row) => {
            row.definition.readiness.connect_api = true;
          },
          (row) => {
            row.definition.analytic_features[0].cad_face_ids = [1];
          },
          (row) => {
            row.availability.public_url_cache_verified = true;
          },
          (row) => {
            row.availability.generation_attempted = 0;
          },
          (row) => {
            row.availability.geometry_available = false;
          },
          (row) => {
            row.availability.status = 'unavailable';
          },
          (row) => {
            row.availability.missing_formats = ['glb', 'step'];
          },
          (row) => {
            row.availability.missing_formats = ['unknown'];
          },
          (row) => {
            row.availability.missing_formats = ['glb', 'glb'];
          },
          (row) => {
            row.availability.reason = 'Generated new substitute';
          },
          (row) => {
            row.extra = true;
          },
        ];
        for (const mutate of mutations) {
          const row = clone(actual[0]);
          mutate(row);
          assert.throws(
            () => source.admitReferencePartDetail(row, actual[0].definition.source_template_id),
            (error) => error.code === 'invalid_response',
          );
        }
        assert.throws(() =>
          source.admitReferencePartDetail(null, actual[0].definition.source_template_id),
        );
      },
    );
    await t.test(
      'optional representation requires exact registered template and both asset identities before fetch',
      async () => {
        const row = actual[0];
        const templateId = row.definition.source_template_id;
        let calls = 0;
        const client = source.createReferencePartsClient(async () => {
          calls++;
          return response(row);
        });
        for (const mutate of [
          (rep) => {
            rep.template_id = actual[1].definition.source_template_id;
          },
          (rep) => {
            rep.template_revision_sha256 = 'a'.repeat(64);
          },
          (rep) => {
            rep.representation_status = 'installed';
          },
          (rep) => {
            rep.bounds_m.min[1] = -0.2;
          },
          (rep) => {
            rep.glb.url = 'https://foreign/model.glb';
          },
          (rep) => {
            rep.step.url += '?foreign=true';
          },
          (rep) => {
            rep.glb.sha256 = 'a'.repeat(64);
          },
          (rep) => {
            rep.step.bytes++;
          },
        ]) {
          const representation = clone(representationFor(row));
          mutate(representation);
          await assert.rejects(
            client.readForTemplate(templateId, representation),
            (error) => error.code === 'invalid_request',
          );
          assert.throws(() => source.admitReferencePartDetail(row, templateId, representation));
        }
        for (const invalid of [null, [], {}])
          await assert.rejects(
            client.readForTemplate(templateId, invalid),
            (error) => error.code === 'invalid_request',
          );
        for (const template of [
          '../source',
          'https://foreign',
          'rp1-template:unknown',
          row.definition.id,
        ]) {
          assert.equal(source.referencePartForTemplate(template), null);
          await assert.rejects(
            client.readForTemplate(template),
            (error) => error.code === 'invalid_request',
          );
        }
        assert.equal(calls, 0);
      },
    );
    await t.test(
      'safe route, source, revision, transport and JSON errors cause no retry/fallback',
      async () => {
        const template = actual[0].definition.source_template_id;
        for (const reply of [
          response({ detail: 'Not Found' }, 404),
          new Response('<html>404</html>', { status: 404 }),
        ]) {
          let calls = 0;
          const client = source.createReferencePartsClient(async () => {
            calls++;
            return reply;
          });
          await assert.rejects(
            client.readForTemplate(template),
            (error) =>
              error.code === 'route_unavailable' &&
              /Restart the normal-host backend/.test(error.message),
          );
          assert.equal(calls, 1);
        }
        for (const [code, status] of [
          ['reference_source_unavailable', 409],
          ['reference_not_found', 404],
          ['reference_revision_mismatch', 409],
        ]) {
          let calls = 0;
          const client = source.createReferencePartsClient(async () => {
            calls++;
            return response(
              { detail: { code, message: '/Users/private', current_revision: 'a'.repeat(64) } },
              status,
            );
          });
          await assert.rejects(
            client.readForTemplate(template),
            (error) =>
              error instanceof source.ReferencePartsServiceError &&
              error.code === code &&
              !error.message.includes('/Users/') &&
              error.currentRevision === 'a'.repeat(64),
          );
          assert.equal(calls, 1);
        }
        const malformed = source.createReferencePartsClient(async () =>
          response(
            { detail: { code: 'reference_revision_mismatch', current_revision: '../secret' } },
            409,
          ),
        );
        await assert.rejects(
          malformed.readForTemplate(template),
          (error) => error.code === 'invalid_response',
        );
        const transport = source.createReferencePartsClient(async () => {
          throw new Error('/Users/private');
        });
        await assert.rejects(
          transport.readForTemplate(template),
          (error) => error.code === 'transport_unavailable' && !error.message.includes('/Users/'),
        );
        const badJson = source.createReferencePartsClient(async () => new Response('not JSON'));
        await assert.rejects(
          badJson.readForTemplate(template),
          (error) => error.code === 'invalid_response',
        );
        const wrong = source.createReferencePartsClient(async () => response(actual[1]));
        await assert.rejects(
          wrong.readForTemplate(template),
          (error) => error.code === 'invalid_response',
        );
      },
    );
    await t.test(
      'abort signal cancels before fetch, during transport and after body without exposing abort reason',
      async () => {
        const template = actual[0].definition.source_template_id;
        let calls = 0;
        const before = new AbortController();
        before.abort('/Users/private');
        const never = source.createReferencePartsClient(async () => {
          calls++;
          return response(actual[0]);
        });
        await assert.rejects(
          never.readForTemplate(template, undefined, before.signal),
          (error) => error.name === 'AbortError' && !error.message.includes('/Users/'),
        );
        assert.equal(calls, 0);
        const during = new AbortController();
        const transport = source.createReferencePartsClient(async (_path, options) => {
          calls++;
          assert.equal(options.signal, during.signal);
          during.abort('/Users/private');
          throw new Error('/Users/private');
        });
        await assert.rejects(
          transport.readForTemplate(template, undefined, during.signal),
          (error) => error.name === 'AbortError' && !error.message.includes('/Users/'),
        );
        assert.equal(calls, 1);
        const body = new AbortController();
        const after = source.createReferencePartsClient(async () => ({
          ok: true,
          status: 200,
          async json() {
            body.abort('/Users/private');
            return actual[0];
          },
        }));
        await assert.rejects(
          after.readForTemplate(template, undefined, body.signal),
          (error) => error.name === 'AbortError' && !error.message.includes('/Users/'),
        );
      },
    );
  } finally {
    await vite.close();
  }
});
