import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

const digest = (bytes) => createHash('sha256').update(bytes).digest('hex');
const baseBytes = readFileSync(new URL('./fixtures/rp1-draft-library.json', import.meta.url));
assert.equal(digest(baseBytes), 'b2339838a42a6426d535a533df7c021211362e3dd4e643a933e5c4562d0cded0');
const overlayBytes = readFileSync(new URL('./fixtures/rp1-source-intents.json', import.meta.url));
assert.equal(
  digest(overlayBytes),
  'e0d2bd1797f5df6014713f6c7ad13a1e6ff77c00a21ca68fa69572b57b5f7ad1',
);
const fixture = JSON.parse(baseBytes);
const planning = JSON.parse(overlayBytes);
assert.equal(planning.base_fixture.sha256, digest(baseBytes));
assert.equal(
  planning.module_sha256,
  digest(readFileSync(new URL('../../src/vehicle/draft_composition.py', import.meta.url))),
);
assert.equal(planning.generator, 'src.vehicle.draft_composition.create_overlay/apply_command');
const saved = fixture.revisions[planning.base_fixture.revision];
const snapshot = {
  ...saved.metadata,
  revision_sha256: saved.revision_sha256,
  source: fixture.source,
};
const vehicle = {
  ...snapshot.source.inspection,
  identity: {
    ...snapshot.source.inspection.identity,
    inspection_geometry_sha256: '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608',
  },
};
const overlays = Object.fromEntries(
  Object.entries(planning.overlays).map(([key, row]) => [key, { ...row, base: snapshot }]),
);
const response = (body, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });
const clone = (value) => structuredClone(value);

test('source intent preview admits actual pure Python output and ID-only requests', async (t) => {
  const vite = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
    logLevel: 'silent',
  });
  try {
    const source = await vite.ssrLoadModule('/src/design-builder/sourceIntentClient.ts');
    const { default: Preview } = await vite.ssrLoadModule(
      '/src/design-builder/SourceIntentPreview.tsx',
    );
    await t.test(
      'base, actual fin exclusion, two exclusions and restore retain all source records',
      async () => {
        for (const overlay of Object.values(overlays)) {
          const before = clone(overlay);
          assert.equal(
            await source.admitSourceIntentOverlay(
              overlay,
              vehicle,
              snapshot,
              overlay.excluded_occurrence_ids,
            ),
            overlay,
          );
          assert.deepEqual(overlay, before);
          assert.equal(overlay.base.source.parts_bank.instances.length, 55);
          assert.equal(overlay.checks.mass_removal_credit_kg, null);
          assert.equal(overlay.checks.total_mass_kg, null);
          assert.equal(overlay.checks.cg_m, null);
          assert.equal(overlay.checks.inertia_kg_m2, null);
          assert.equal(overlay.readiness.simulation_eligible, false);
        }
        assert.equal(overlays.fin.preview.removed_functions[0].source_occurrence.group_count, 3);
        assert.equal(overlays.fin.preview.exclusion_intents, 1);
        assert.deepEqual(overlays.initial, overlays.restored);
        assert.ok(
          overlays.both.preview.removed_functions
            .find((row) => row.occurrence_id === 'motor_retainer')
            .source_evidence.issues.some((issue) => issue.id === 'retainer_product_conflict'),
        );
      },
    );
    await t.test(
      'explicit GET and exclude/restore POST transmit tiny IDs and opaque Python identities',
      async () => {
        const calls = [];
        const replies = [overlays.initial, overlays.fin, overlays.restored];
        const client = source.createSourceIntentClient(vehicle, snapshot, async (path, options) => {
          calls.push({ path, options });
          return response(replies.shift());
        });
        assert.equal(calls.length, 0);
        const initial = await client.prepare();
        const fin = await client.apply(initial, 'exclude-source-occurrence', 'fin_set');
        const restored = await client.apply(fin, 'restore-source-occurrence', 'fin_set');
        assert.deepEqual(restored, initial);
        assert.deepEqual(
          calls.map((call) => call.options.method),
          ['GET', 'POST', 'POST'],
        );
        assert.ok(
          calls.every(
            (call) =>
              call.path === `/api/design-drafts/${snapshot.draft_id}/intent-preview` &&
              call.options.cache === 'no-store',
          ),
        );
        assert.equal(calls[0].options.body, undefined);
        assert.deepEqual(JSON.parse(calls[1].options.body), {
          base_draft_revision: snapshot.revision_sha256,
          base_overlay_revision: overlays.initial.revision_sha256,
          excluded_occurrence_ids: [],
          type: 'exclude-source-occurrence',
          occurrence_id: 'fin_set',
        });
        assert.deepEqual(JSON.parse(calls[2].options.body), {
          base_draft_revision: snapshot.revision_sha256,
          base_overlay_revision: overlays.fin.revision_sha256,
          excluded_occurrence_ids: ['fin_set'],
          type: 'restore-source-occurrence',
          occurrence_id: 'fin_set',
        });
        assert.ok(
          calls
            .slice(1)
            .every(
              (call) =>
                call.options.body.length < 400 && !call.options.body.includes('source_sha256'),
            ),
        );
        assert.deepEqual(overlays.initial.excluded_occurrence_ids, []);
      },
    );
    await t.test(
      'tampered source, function, evidence, order, counts, unknown keys and false/null flags are rejected',
      async () => {
        const mutations = [
          (row) => {
            row.schema_version = 2;
          },
          (row) => {
            row.kind = 'candidate';
          },
          (row) => {
            row.status = 'resolved';
          },
          (row) => {
            row.source_sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.source_revision_sha256 = 'a'.repeat(64);
          },
          (row) => {
            row.revision_sha256 = '../hash';
          },
          (row) => {
            row.base.draft_id = fixture.revisions.other.metadata.draft_id;
          },
          (row) => {
            row.base.source.parts_bank.instances.pop();
          },
          (row) => {
            row.excluded_occurrence_ids.reverse();
          },
          (row) => {
            row.excluded_occurrence_ids.push('fin_set');
          },
          (row) => {
            row.preview.source_occurrences = 54;
          },
          (row) => {
            row.preview.source_ledger_preserved = 1;
          },
          (row) => {
            row.preview.exclusion_intents = 3;
          },
          (row) => {
            row.preview.effective_inventory = [];
          },
          (row) => {
            row.preview.removed_functions[0].function = 'Replacement installed';
          },
          (row) => {
            row.preview.removed_functions[0].source_occurrence.group_count = 1;
          },
          (row) => {
            row.preview.removed_functions[1].source_evidence.issues = [];
          },
          (row) => {
            row.preview.removed_functions[0].source_evidence.provenance = [];
          },
          (row) => {
            row.preview.removed_functions[0].source_evidence.geometry.reusable_local_geometry = true;
          },
          (row) => {
            row.checks.total_mass_kg = 0;
          },
          (row) => {
            row.checks.mass_removal_credit_kg = 0;
          },
          (row) => {
            row.checks.cg_m = 0;
          },
          (row) => {
            row.checks.inertia_kg_m2 = [0, 0, 0];
          },
          (row) => {
            row.readiness.resolve_available = 0;
          },
          (row) => {
            row.readiness.resolved_candidate = true;
          },
          (row) => {
            row.readiness.simulation_eligible = true;
          },
          (row) => {
            row.readiness.engineering_accepted = true;
          },
          (row) => {
            row.readiness.flight_ready = true;
          },
          (row) => {
            row.readiness.blockers = [];
          },
          (row) => {
            row.capabilities.add = 0;
          },
          (row) => {
            row.capabilities.replace = true;
          },
          (row) => {
            row.capabilities.resolve = true;
          },
          (row) => {
            row.result = 'pass';
          },
        ];
        for (const mutate of mutations) {
          const overlay = clone(overlays.both);
          mutate(overlay);
          await assert.rejects(
            source.admitSourceIntentOverlay(overlay, vehicle, snapshot, [
              'fin_set',
              'motor_retainer',
            ]),
          );
        }
        await assert.rejects(source.admitSourceIntentOverlay(overlays.fin, vehicle, snapshot, []));
        await assert.rejects(
          source.admitSourceIntentOverlay(overlays.both, vehicle, snapshot, ['not_a_part']),
        );
        assert.throws(() => source.createSourceIntentClient({ ...vehicle, id: 'other' }, snapshot));
      },
    );
    await t.test(
      'stale metadata/overlay errors expose safe exact hashes without retry or state mutation',
      async () => {
        for (const [code, field, property] of [
          ['stale_draft_revision', 'current_draft_revision', 'currentDraftRevision'],
          ['stale_overlay_revision', 'current_overlay_revision', 'currentOverlayRevision'],
        ]) {
          const before = clone(overlays.fin);
          let calls = 0;
          const client = source.createSourceIntentClient(vehicle, snapshot, async () => {
            calls++;
            return response(
              { detail: { code, [field]: 'a'.repeat(64), message: '/Users/private' } },
              409,
            );
          });
          await assert.rejects(
            client.apply(overlays.fin, 'restore-source-occurrence', 'fin_set'),
            (error) =>
              error instanceof source.SourceIntentError &&
              error[property] === 'a'.repeat(64) &&
              error.code === code &&
              !error.message.includes('/Users/'),
          );
          assert.equal(calls, 1);
          assert.deepEqual(overlays.fin, before);
          const malformed = source.createSourceIntentClient(vehicle, snapshot, async () =>
            response({ detail: { code, [field]: 'not-a-hash' } }, 409),
          );
          await assert.rejects(malformed.prepare(), (error) => error.code === 'invalid_response');
        }
        const moved = clone(overlays.initial);
        const initial = fixture.revisions.initial;
        moved.base = {
          ...initial.metadata,
          revision_sha256: initial.revision_sha256,
          source: fixture.source,
        };
        await assert.rejects(
          source.admitSourceIntentOverlay(moved, vehicle, snapshot, []),
          (error) =>
            error.code === 'stale_draft_revision' &&
            error.currentDraftRevision === initial.revision_sha256,
        );
      },
    );
    await t.test(
      '404 demands backend restart; transport and bad responses preserve current intentions',
      async () => {
        for (const reply of [
          response({ detail: 'Not Found' }, 404),
          new Response('<html>404</html>', { status: 404 }),
        ]) {
          let calls = 0;
          const client = source.createSourceIntentClient(vehicle, snapshot, async () => {
            calls++;
            return reply;
          });
          await assert.rejects(client.prepare(), /Restart the normal-host backend/);
          assert.equal(calls, 1);
        }
        const transport = source.createSourceIntentClient(vehicle, snapshot, async () => {
          throw new Error('/Users/private');
        });
        await assert.rejects(
          transport.apply(overlays.fin, 'restore-source-occurrence', 'fin_set'),
          (error) =>
            error.code === 'transport_unavailable' &&
            /preserved/.test(error.message) &&
            !error.message.includes('/Users/'),
        );
        const invalidJson = source.createSourceIntentClient(
          vehicle,
          snapshot,
          async () => new Response('not JSON'),
        );
        await assert.rejects(invalidJson.prepare(), /unreadable/);
        const wrong = source.createSourceIntentClient(vehicle, snapshot, async () =>
          response(overlays.initial),
        );
        await assert.rejects(
          wrong.apply(overlays.initial, 'exclude-source-occurrence', 'fin_set'),
          /gates differ/,
        );
        const before = clone(overlays.fin);
        let calls = 0;
        const never = source.createSourceIntentClient(vehicle, snapshot, async () => {
          calls++;
          return response(overlays.fin);
        });
        await assert.rejects(never.apply(overlays.fin, 'exclude-source-occurrence', 'fin_set'));
        await assert.rejects(never.apply(overlays.fin, 'restore-source-occurrence', '../owner'));
        await assert.rejects(never.apply(overlays.fin, 'add', 'fin_set'));
        assert.equal(calls, 0);
        assert.deepEqual(overlays.fin, before);
      },
    );
    await t.test(
      'standalone SSR makes no request and provides explicit normal-flow preparation',
      () => {
        const original = globalThis.fetch;
        let calls = 0;
        globalThis.fetch = async () => {
          calls++;
          throw new Error('Unexpected request');
        };
        try {
          const html = renderToStaticMarkup(React.createElement(Preview, { vehicle, snapshot }));
          assert.equal(calls, 0);
          assert.match(html, /<details class="source-intent-preview"/);
          assert.match(html, /Prepare intent preview/);
          assert.match(html, /No intent preview has been admitted/);
          assert.match(html, /55 source accounting occurrences/);
          assert.match(
            html,
            /Unsaved intents reset when the parent metadata revision or page changes/,
          );
          assert.match(html, /Simulation eligibility: false/);
          assert.doesNotMatch(
            html,
            /<dialog|role="dialog"|Save intent|Add part|Replace part|Connect parts/,
          );
          const wrong = renderToStaticMarkup(
            React.createElement(Preview, { vehicle: { ...vehicle, id: 'other' }, snapshot }),
          );
          assert.match(wrong, /unavailable for this source/);
          assert.doesNotMatch(wrong, /<button/);
          assert.equal(calls, 0);
        } finally {
          globalThis.fetch = original;
        }
      },
    );
  } finally {
    await vite.close();
  }
});
