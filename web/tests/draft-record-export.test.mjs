import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { createServer } from '../node_modules/vite/dist/node/index.js';

const fixtureBytes = readFileSync(new URL('./fixtures/rp1-draft-library.json', import.meta.url));
assert.equal(
  createHash('sha256').update(fixtureBytes).digest('hex'),
  'b2339838a42a6426d535a533df7c021211362e3dd4e643a933e5c4562d0cded0',
);
const fixture = JSON.parse(fixtureBytes);
function saved(name = 'saved') {
  const entry = fixture.revisions[name];
  return structuredClone({
    ...entry.metadata,
    revision_sha256: entry.revision_sha256,
    source: fixture.source,
  });
}
function vehicle() {
  return {
    ...structuredClone(fixture.source.inspection),
    identity: {
      ...fixture.source.inspection.identity,
      inspection_geometry_sha256:
        '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608',
    },
  };
}
function canonical(value) {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (value !== null && typeof value === 'object')
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`)
      .join(',')}}`;
  return JSON.stringify(value);
}
function signMetadata(row) {
  const unsigned = Object.fromEntries(
    Object.entries(row).filter(([key]) => key !== 'source' && key !== 'revision_sha256'),
  );
  row.revision_sha256 = createHash('sha256').update(canonical(unsigned)).digest('hex');
  return row;
}
function freeze(value) {
  if (value !== null && typeof value === 'object') {
    for (const child of Object.values(value)) freeze(child);
    Object.freeze(value);
  }
  return value;
}

// Vite runs only as an in-process source loader, with no listening server/browser.
test('saved draft review export uses actual admitted snapshots and returns deterministic bytes', async (t) => {
  const vite = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
    logLevel: 'silent',
  });
  try {
    const { exportDraftReviewRecord } = await vite.ssrLoadModule(
      '/src/design-builder/draftRecordExport.ts',
    );

    await t.test(
      'current and historical records preserve every semantic field and lineage without mutating inputs',
      async () => {
        for (const name of ['initial', 'saved', 'other']) {
          const row = freeze(saved(name)),
            current = freeze(vehicle());
          const before = JSON.stringify({ row, current });
          const output = await exportDraftReviewRecord(row, current);
          const again = await exportDraftReviewRecord(row, current);
          assert.equal(output.text, again.text);
          assert.equal(output.filename, again.filename);
          assert.deepEqual(output.bytes, again.bytes);
          assert.equal(output.sha256, again.sha256);
          assert.equal(
            output.filename,
            `rp1-draft-review-${row.draft_id}-r${row.sequence}-${row.revision_sha256.slice(0, 12)}.json`,
          );
          assert.ok(output.bytes instanceof Uint8Array);
          assert.equal(Buffer.from(output.bytes).toString('utf8'), output.text);
          assert.equal(output.text.at(-1), '\n');
          assert.equal(createHash('sha256').update(output.bytes).digest('hex'), output.sha256);
          const parsed = JSON.parse(output.text);
          assert.equal(parsed.format, 'rp1-saved-source-fork-review-v1');
          assert.deepEqual(parsed.draft, row);
          assert.equal(parsed.draft.parent_revision_sha256, row.parent_revision_sha256);
          const unsigned = Object.fromEntries(
            Object.entries(parsed.draft).filter(
              ([key]) => key !== 'source' && key !== 'revision_sha256',
            ),
          );
          assert.equal(
            createHash('sha256').update(canonical(unsigned)).digest('hex'),
            row.revision_sha256,
          );
          assert.equal(JSON.stringify({ row, current }), before);
          assert.equal(Object.hasOwn(parsed, 'sha256'), false);
          assert.equal(parsed.scope.included_revision_count, 1);
          assert.equal(parsed.scope.complete_history_embedded, false);
          assert.equal(parsed.scope.geometry_assets_embedded, false);
          assert.equal(parsed.scope.source_fork_only, true);
          assert.equal(parsed.scope.import_or_restore_supported, false);
          assert.equal(parsed.scope.byte_exact_store_backup, false);
          for (const key of [
            'resolved_candidate',
            'simulation_configuration',
            'simulation_eligible',
            'engineering_accepted',
            'flight_ready',
          ])
            assert.equal(parsed.scope[key], false, key);
          assert.match(parsed.serialization.numeric_scope, /Python 1.0 becoming JavaScript 1/);
          assert.match(
            parsed.serialization.source_sha256_scope,
            /not a digest of the reconstructed export/,
          );
          assert.match(parsed.serialization.restoration_scope, /not a byte-exact store backup/);
        }
      },
    );

    await t.test(
      'all 55 accounting records, original source pins and null/estimated evidence remain intact',
      async () => {
        const row = saved();
        const parsed = JSON.parse((await exportDraftReviewRecord(row, vehicle())).text);
        const source = parsed.draft.source;
        assert.equal(source.parts_bank.definitions.length, 55);
        assert.equal(source.parts_bank.instances.length, 55);
        assert.equal(new Set(source.parts_bank.instances.map((instance) => instance.id)).size, 55);
        assert.deepEqual(source.source_refs, fixture.source.source_refs);
        assert.equal(parsed.draft.source_sha256, fixture.revisions.saved.metadata.source_sha256);
        assert.equal(source.inspection.summary.physical_inertia, null);
        assert.equal(source.inspection.summary.inertia_status, 'unavailable');
        assert.equal(source.inspection.summary.flight_ready, false);
        assert.equal(source.parts_bank.summary.by_maturity.mass_allowance, 25);
        assert.equal(source.parts_bank.summary.by_maturity.missing_geometry, 4);
        assert.match(source.inspection.summary.mass_basis, /estimates/);
        const fin = source.parts_bank.instances.find((part) => part.id === 'fin_set');
        assert.equal(fin.group_count, 3);
        assert.equal(fin.quantity, 1);
        assert.equal(source.inspection.evidence.fin.bonded_panel_stress_screen_pass_only, false);
        assert.deepEqual(
          source.inspection.summary.mass_cases,
          fixture.source.inspection.summary.mass_cases,
        );
        assert.ok(
          source.parts_bank.definitions.every(
            (definition) => definition.physical_verification === 'open',
          ),
        );
        assert.ok(
          source.parts_bank.definitions.every((definition) => definition.geometry.mesh === null),
        );
        // Server snapshot identity is retained; review serialization is a different encoding.
        assert.notEqual(
          createHash('sha256').update(JSON.stringify(source)).digest('hex'),
          parsed.draft.source_sha256,
        );
      },
    );

    await t.test(
      'object key ordering is deterministic and labels/notes cannot enter filenames',
      async () => {
        const row = signMetadata({
          ...saved(),
          label: 'Review ../雪/notes.json',
          notes: 'A structured review — not a restore file.\nSecond line.',
        });
        const reordered = Object.fromEntries(Object.entries(row).reverse());
        const first = await exportDraftReviewRecord(row, vehicle());
        const second = await exportDraftReviewRecord(reordered, vehicle());
        assert.equal(first.text, second.text);
        assert.equal(first.sha256, second.sha256);
        assert.match(first.filename, /^rp1-draft-review-[0-9a-f-]{36}-r\d+-[0-9a-f]{12}\.json$/);
        assert.doesNotMatch(first.filename, /\.\.|雪|notes|\/|\\/);
        assert.equal(JSON.parse(first.text).draft.label, row.label);
        assert.equal(JSON.parse(first.text).draft.notes, row.notes);
      },
    );

    await t.test(
      'foreign, tampered or unavailable guarded source/metadata is rejected before output',
      async () => {
        for (const mutate of [
          (row) => {
            row.draft_id = '../source';
          },
          (row) => {
            row.label = 'Unsaved text mixed into snapshot';
          },
          (row) => {
            row.notes = 'Not the saved revision';
          },
          (row) => {
            row.source_sha256 = '0'.repeat(64);
          },
          (row) => {
            row.revision_sha256 = '0'.repeat(64);
          },
          (row) => {
            row.readiness.flight_ready = true;
          },
          (row) => {
            row.source.source_refs[0].sha256 = '0'.repeat(64);
          },
          (row) => {
            row.source.parts_bank.instances.pop();
          },
          (row) => {
            row.source.parts_bank.instances[0].quantity = 2;
          },
          (row) => {
            row.source.parts_bank.definitions[0].mass_kg = 0;
          },
          (row) => {
            row.source.inspection.summary.inertia_status = 'available';
          },
          (row) => {
            row.source = null;
          },
        ]) {
          const row = saved();
          mutate(row);
          await assert.rejects(exportDraftReviewRecord(row, vehicle()));
        }
        const foreign = vehicle();
        foreign.id = 'modular-performance-v1';
        await assert.rejects(exportDraftReviewRecord(saved(), foreign));
        const incomplete = vehicle();
        incomplete.parts.pop();
        await assert.rejects(exportDraftReviewRecord(saved(), incomplete));
        // The input contract is a saved revision, not an editor holding unsaved text.
        await assert.rejects(
          exportDraftReviewRecord(
            { snapshot: saved(), label: 'unsaved', notes: 'unsaved', conflict: null },
            vehicle(),
          ),
        );
      },
    );

    await t.test(
      'non-JSON coercion is rejected and building has no fetch or download side effect',
      async () => {
        const originalFetch = globalThis.fetch;
        let requests = 0;
        globalThis.fetch = async () => {
          requests++;
          throw new Error('No network allowed');
        };
        try {
          for (const value of [undefined, Infinity, NaN, 1n, new Date(), () => {}]) {
            const row = saved();
            row.source.test_non_json = value;
            await assert.rejects(exportDraftReviewRecord(row, vehicle()));
          }
          const cycle = saved();
          cycle.source.test_cycle = cycle;
          await assert.rejects(exportDraftReviewRecord(cycle, vehicle()), /cycle/);
          let getterRead = false;
          const accessor = saved();
          Object.defineProperty(accessor, 'label', {
            enumerable: true,
            get() {
              getterRead = true;
              return 'bad';
            },
          });
          await assert.rejects(exportDraftReviewRecord(accessor, vehicle()), /accessor/);
          assert.equal(getterRead, false);
          await exportDraftReviewRecord(saved(), vehicle());
          assert.equal(requests, 0);
          const implementation = readFileSync(
            new URL('../src/design-builder/draftRecordExport.ts', import.meta.url),
            'utf8',
          );
          assert.doesNotMatch(
            implementation,
            /createObjectURL|document\.createElement|\.click\(|window\.|fetch\(/,
          );
        } finally {
          globalThis.fetch = originalFetch;
        }
      },
    );
  } finally {
    await vite.close();
  }
});
