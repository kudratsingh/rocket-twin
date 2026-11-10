import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

// Frozen actual-store output, shared source once. Runtime is Node-only;
// the separate store test checks generation against current pinned inputs.
const fixtureBytes = readFileSync(new URL('./fixtures/rp1-draft-library.json', import.meta.url));
assert.equal(
  createHash('sha256').update(fixtureBytes).digest('hex'),
  'b2339838a42a6426d535a533df7c021211362e3dd4e643a933e5c4562d0cded0',
);
const fixture = JSON.parse(fixtureBytes);
assert.equal(fixture.schema_version, 1);
const actual = {
  ...Object.fromEntries(
    Object.entries(fixture.revisions).map(([name, row]) => [
      name,
      { ...row.metadata, revision_sha256: row.revision_sha256, source: fixture.source },
    ]),
  ),
  page: fixture.page,
};
const vehicle = {
  ...actual.initial.source.inspection,
  identity: {
    ...actual.initial.source.inspection.identity,
    inspection_geometry_sha256: '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608',
  },
};
const response = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
const clone = (value) => structuredClone(value);

function signRevision(row) {
  const { source: _source, revision_sha256: _revision, ...unsigned } = row;
  void _source;
  void _revision;
  function canonical(value) {
    if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
    if (value !== null && typeof value === 'object')
      return `{${Object.keys(value)
        .sort()
        .map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`)
        .join(',')}}`;
    return JSON.stringify(value);
  }
  row.revision_sha256 = createHash('sha256').update(canonical(unsigned)).digest('hex');
  return row;
}

test('standalone draft client and embedded SSR use actual store contracts', async (t) => {
  const vite = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
    logLevel: 'silent',
  });
  try {
    const source = await vite.ssrLoadModule('/src/design-builder/draftLibraryClient.ts');
    const { default: DraftLibrary } = await vite.ssrLoadModule(
      '/src/design-builder/DraftLibrary.tsx',
    );

    await t.test(
      'real source fork and metadata revision pass exact source and content-hash admission',
      async () => {
        for (const row of [actual.initial, actual.saved, actual.other]) {
          const admitted = await source.admitDraftRevision(
            row,
            vehicle,
            row.draft_id,
            row.revision_sha256,
          );
          assert.equal(admitted, row);
          assert.equal(admitted.source.parts_bank.instances.length, 55);
          assert.equal(admitted.readiness.flight_ready, false);
        }
        assert.deepEqual(source.admitDraftPage(actual.page), actual.page);
      },
    );

    await t.test(
      'source, UUID, SHA, lineage, 55 accounting occurrences and readiness fail closed',
      async () => {
        const mutations = [
          (row) => {
            row.draft_id = '../configs';
          },
          (row) => {
            row.revision_sha256 = 'b'.repeat(64);
          },
          (row) => {
            row.source_sha256 = 'b'.repeat(64);
          },
          (row) => {
            row.base_configuration_id = 'other';
          },
          (row) => {
            row.source.source_refs[0].sha256 = 'b'.repeat(64);
          },
          (row) => {
            row.source.source_refs.push(row.source.source_refs[0]);
          },
          (row) => {
            row.source.parts_bank.instances.pop();
          },
          (row) => {
            row.source.parts_bank.instances[0].quantity = 3;
          },
          (row) => {
            row.source.parts_bank.definitions[0].mass_kg = 0;
          },
          (row) => {
            row.source.parts_bank.definitions.find(
              (d) => d.source_part_id === 'motor_retainer',
            ).issues = [];
          },
          (row) => {
            row.source.specification.parts[1].id = row.source.specification.parts[0].id;
          },
          (row) => {
            row.source.inspection.summary.inertia_status = 'complete';
          },
          (row) => {
            row.readiness.simulation_eligible = true;
          },
          (row) => {
            row.readiness.flight_ready = true;
          },
          (row) => {
            row.capabilities.compose = true;
          },
          (row) => {
            row.parent_revision_sha256 = 'x';
          },
          (row) => {
            row.label = 'Modified without rehash';
          },
          (row) => {
            row.additional_result = { passed: true };
          },
        ];
        for (const mutate of mutations) {
          const row = clone(actual.initial);
          mutate(row);
          await assert.rejects(source.admitDraftRevision(row, vehicle));
        }
        await assert.rejects(
          source.admitDraftRevision(actual.initial, vehicle, actual.other.draft_id),
        );
        await assert.rejects(
          source.admitDraftRevision(
            actual.initial,
            vehicle,
            actual.initial.draft_id,
            actual.saved.revision_sha256,
          ),
        );
        assert.equal(source.matchesDraftSource({ ...vehicle, id: 'other' }), false);
        assert.equal(
          source.matchesDraftSource({ ...vehicle, parts: vehicle.parts.slice(1) }),
          false,
        );
        assert.throws(() =>
          source.createDraftClient({
            ...vehicle,
            identity: { specification_sha256: 'b'.repeat(64) },
          }),
        );
      },
    );

    await t.test(
      'list cannot invent a page from malformed readiness, duplicated entries or cursor',
      () => {
        for (const mutate of [
          (page) => {
            page.drafts[0].readiness.engineering_accepted = true;
          },
          (page) => {
            page.drafts.push(page.drafts[0]);
          },
          (page) => {
            page.next_after = actual.other.draft_id;
            page.drafts = [];
          },
          (page) => {
            page.next_after = '../configs';
          },
          (page) => {
            page.drafts[0].draft_id = 'not-an-id';
          },
          (page) => {
            page.drafts[0].extra = 'unknown';
          },
        ]) {
          const page = clone(actual.page);
          mutate(page);
          assert.throws(() => source.admitDraftPage(page));
        }
      },
    );

    await t.test('client construction and SSR cause no automatic POST or fetch', () => {
      const original = globalThis.fetch;
      let requests = 0;
      globalThis.fetch = async () => {
        requests++;
        throw new Error('Unexpected request');
      };
      try {
        source.createDraftClient(vehicle);
        const html = renderToStaticMarkup(
          React.createElement(DraftLibrary, { vehicle, onInspectSource: () => {} }),
        );
        assert.equal(requests, 0);
        assert.match(html, /Fork RP1 as separate draft/);
        assert.match(html, /No draft list has been admitted yet/);
        assert.match(html, /55 source accounting occurrences/);
        assert.match(html, /Simulation eligibility: false/);
        assert.match(html, /Inspect frozen parent rocket/);
        assert.match(html, /aria-label="Fork frozen RP1 source"/);
        assert.match(html, /<label for=/);
        assert.doesNotMatch(html, /<dialog|role="dialog"|role="alertdialog"/);
        assert.doesNotMatch(html, /Add part|Replace part|Connect parts/);
        const foreign = renderToStaticMarkup(
          React.createElement(DraftLibrary, {
            vehicle: { ...vehicle, id: 'other' },
            onInspectSource: () => {},
          }),
        );
        assert.match(foreign, /Draft library unavailable for this source/);
        assert.doesNotMatch(foreign, /<form/);
        assert.equal(requests, 0);
      } finally {
        globalThis.fetch = original;
      }
    });

    await t.test(
      'explicit list, fork, read/history and save use only the intended service calls',
      async () => {
        const calls = [];
        const replies = [actual.page, actual.initial, actual.saved, actual.initial, actual.saved];
        const client = source.createDraftClient(vehicle, async (path, options) => {
          calls.push({ path, options });
          return response(replies.shift());
        });
        assert.equal(calls.length, 0);
        await client.list();
        await client.fork(actual.initial.label, actual.initial.notes);
        await client.read(actual.saved.draft_id);
        await client.read(actual.initial.draft_id, actual.initial.revision_sha256);
        const editor = {
          ...source.editDraft(actual.initial),
          label: actual.saved.label,
          notes: actual.saved.notes,
        };
        assert.equal(source.hasDraftChanges(editor), true);
        await client.save(editor);
        assert.deepEqual(
          calls.map((call) => call.options.method),
          ['GET', 'POST', 'GET', 'GET', 'PATCH'],
        );
        assert.equal(calls[0].path, '/api/design-drafts?limit=25');
        assert.match(calls[3].path, new RegExp(`\\?revision=${actual.initial.revision_sha256}$`));
        assert.deepEqual(JSON.parse(calls[1].options.body), {
          source_configuration_id: vehicle.id,
          source_specification_sha256: vehicle.identity.specification_sha256,
          label: actual.initial.label,
          notes: actual.initial.notes,
        });
        assert.deepEqual(JSON.parse(calls[4].options.body), {
          base_revision: actual.initial.revision_sha256,
          label: actual.saved.label,
          notes: actual.saved.notes,
        });
        assert.ok(calls.every((call) => call.options.cache === 'no-store'));
        assert.ok(calls.every((call) => !call.path.includes('engineering-workbench')));
      },
    );

    await t.test(
      'stale 409 preserves exact unsaved text and performs no automatic reload/retry',
      async () => {
        const calls = [];
        const client = source.createDraftClient(vehicle, async (path, options) => {
          calls.push({ path, options });
          return response(
            { detail: { code: 'stale_revision', current_revision: actual.saved.revision_sha256 } },
            409,
          );
        });
        const editor = {
          ...source.editDraft(actual.initial),
          label: 'Unsaved label',
          notes: 'Unsaved notes\nkept exactly',
        };
        let failure;
        try {
          await client.save(editor);
        } catch (error) {
          failure = error;
        }
        assert.ok(failure instanceof source.DraftServiceError);
        const preserved = source.retainDraftConflict(editor, failure);
        assert.equal(preserved.label, editor.label);
        assert.equal(preserved.notes, editor.notes);
        assert.equal(preserved.snapshot, editor.snapshot);
        assert.equal(preserved.conflict, actual.saved.revision_sha256);
        assert.equal(calls.length, 1);
        assert.equal(calls[0].options.method, 'PATCH');
        assert.match(failure.message, /unsaved text is preserved/i);
      },
    );

    await t.test(
      '404 route errors require normal-host restart without mutable prepared fallback',
      async () => {
        for (const body of [{ detail: 'Not Found' }, null]) {
          const paths = [];
          const client = source.createDraftClient(vehicle, async (path) => {
            paths.push(path);
            return body
              ? response(body, 404)
              : new Response('<html>Not Found</html>', { status: 404 });
          });
          await assert.rejects(client.list(), /normal-host preview needs a restart/);
          assert.deepEqual(paths, ['/api/design-drafts?limit=25']);
        }
      },
    );

    await t.test(
      'transport, unsafe requests, bad JSON and mismatching operation responses fail visibly',
      async () => {
        let calls = 0;
        const network = source.createDraftClient(vehicle, async () => {
          calls++;
          throw new Error('/Users/private secret');
        });
        await assert.rejects(network.list(), /could not be reached/);
        assert.equal(calls, 1);
        assert.equal(source.hasDraftChanges(source.editDraft(actual.initial)), false);
        for (const call of [
          () => network.read('../source'),
          () => network.read(actual.initial.draft_id, '../revision'),
          () => network.list('../cursor'),
          () => network.fork('', ''),
        ])
          await assert.rejects(call());
        assert.equal(calls, 1);
        const invalidJson = source.createDraftClient(vehicle, async () => new Response('not JSON'));
        await assert.rejects(invalidJson.list(), /unreadable data/);
        const wrongFork = source.createDraftClient(vehicle, async () => response(actual.other));
        await assert.rejects(
          wrongFork.fork(actual.initial.label, actual.initial.notes),
          /differs from the explicit metadata request/,
        );
        const modified = signRevision({ ...clone(actual.saved), label: 'Unexpected response' });
        const wrongSave = source.createDraftClient(vehicle, async () => response(modified));
        await assert.rejects(
          wrongSave.save({
            ...source.editDraft(actual.initial),
            label: actual.saved.label,
            notes: actual.saved.notes,
          }),
          /differs from the source or requested metadata/,
        );
        const unknown = source.createDraftClient(vehicle, async () =>
          response({ detail: { code: 'draft_not_found', message: '/Users/private/secret' } }, 404),
        );
        await assert.rejects(
          unknown.read(actual.initial.draft_id),
          (error) => error.code === 'draft_not_found' && !error.message.includes('/Users/'),
        );
      },
    );
  } finally {
    await vite.close();
  }
});
