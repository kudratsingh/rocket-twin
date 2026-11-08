import assert from 'node:assert/strict';
import test from 'node:test';
import {
  acceptedAttemptIds,
  attemptSummary,
  readAttemptStatuses,
  savedAttemptExport,
  savedAttemptIds,
  experimentJson,
} from '../src/experiments/attemptMonitor.ts';

test('request errors retain HTTP/malformed/transport distinctions without inventing accepted IDs', async () => {
  const fetchResponse = (response) => async () => response;
  await assert.rejects(
    experimentJson(
      '/api/experiments',
      { method: 'POST' },
      undefined,
      fetchResponse(
        new Response('<h1>Proxy failed</h1>', { status: 500, statusText: 'Internal Server Error' }),
      ),
    ),
    /HTTP 500.*POST/,
  );
  await assert.rejects(
    experimentJson(
      '/api/runs',
      undefined,
      undefined,
      fetchResponse(new Response('{broken', { status: 200 })),
    ),
    /Malformed JSON.*GET/,
  );
  await assert.rejects(
    experimentJson('/api/runs', undefined, undefined, async () => {
      throw new TypeError('Offline fixture');
    }),
    /Offline fixture/,
  );
  assert.deepEqual(
    await experimentJson(
      '/api/experiments',
      { method: 'POST' },
      undefined,
      fetchResponse(Response.json({ run_id: 'A', run_ids: ['A'] })),
    ),
    { run_id: 'A', run_ids: ['A'] },
  );
});

test('accepted membership must match the declared batch before monitoring can begin', () => {
  assert.deepEqual(acceptedAttemptIds({ run_id: 'A', run_ids: ['A', 'B'] }, 2), ['A', 'B']);
  for (const value of [
    null,
    {},
    { run_id: 'A', run_ids: ['B', 'A'] },
    { run_id: 'A', run_ids: ['A', 'A'] },
    { run_id: 'A', run_ids: ['A'] },
  ])
    assert.throws(() => acceptedAttemptIds(value, 2), /did not confirm/);
  assert.deepEqual(savedAttemptIds({ run_id: 'B', batch_members: ['A', 'B'] }), ['A', 'B']);
  assert.deepEqual(savedAttemptIds({ run_id: 'legacy-single' }), ['legacy-single']);
  assert.throws(() => savedAttemptIds({ run_id: 'B', batch_members: ['A'] }), /membership/);
});

test('one completed member cannot finish a batch and cancellation acknowledgement is not termination', () => {
  const members = { A: { run_id: 'A', status: 'complete' }, B: { run_id: 'B', status: 'running' } };
  assert.equal(attemptSummary(['A', 'B'], members).terminal, false);
  assert.deepEqual(attemptSummary(['A', 'B'], members).outstanding, ['B']);
  members.B.status = 'cancel_requested';
  assert.equal(attemptSummary(['A', 'B'], members).terminal, false);
  members.B.status = 'cancelled';
  assert.equal(attemptSummary(['A', 'B'], members).terminal, true);
  for (const status of ['failed', 'interrupted']) {
    members.B.status = status;
    assert.equal(attemptSummary(['A', 'B'], members).terminal, true);
    assert.match(attemptSummary(['A', 'B'], members).text, new RegExp(status));
  }
  assert.equal(attemptSummary(['A', 'missing'], members).terminal, false);
  assert.equal(attemptSummary([], {}).terminal, false);
});

test('transport failure retains successful member status; explicit resume only reads the same IDs', async () => {
  const ids = ['A', 'B'],
    calls = [];
  const controller = new AbortController();
  const first = await readAttemptStatuses(
    ids,
    async (id) => {
      calls.push(id);
      if (id === 'B') throw new Error('HTTP 500 fixture, no worker failure');
      return { run_id: id, status: 'complete' };
    },
    controller.signal,
  );
  assert.deepEqual(first.records, [{ run_id: 'A', status: 'complete' }]);
  assert.match(first.errors[0], /B.*HTTP 500/);
  assert.deepEqual(ids, ['A', 'B']);
  const resumed = await readAttemptStatuses(
    ids,
    async (id) => {
      calls.push(id);
      return {
        run_id: id,
        status: id === 'A' ? 'complete' : 'failed',
        error: id === 'B' ? 'Saved worker error' : null,
      };
    },
    controller.signal,
  );
  assert.deepEqual(calls, ['A', 'B', 'A', 'B']);
  assert.deepEqual(resumed.errors, []);
  assert.equal(
    attemptSummary(ids, Object.fromEntries(resumed.records.map((r) => [r.run_id, r]))).terminal,
    true,
  );
  assert.equal(resumed.records[1].error, 'Saved worker error');
});

test('late aborted and foreign status responses cannot become observed member records', async () => {
  const controller = new AbortController();
  let release;
  const read = readAttemptStatuses(
    ['A'],
    () =>
      new Promise((resolve) => {
        release = resolve;
      }),
    controller.signal,
  );
  controller.abort();
  release({ run_id: 'A', status: 'complete' });
  assert.deepEqual(await read, { records: [], errors: [] });
  const wrong = await readAttemptStatuses(
    ['A'],
    async () => ({ run_id: 'foreign', status: 'complete' }),
    new AbortController().signal,
  );
  assert.deepEqual(wrong.records, []);
  assert.match(wrong.errors[0], /foreign identity/);
});

test('failed and missing batch members export with exact saved metadata and no invented telemetry', () => {
  const first = {
    run_id: 'A',
    status: 'failed',
    error: 'exact saved failure',
    settings: { seed: 0 },
    batch_members: ['A', 'B'],
  };
  const snapshot = JSON.stringify(first);
  const result = JSON.parse(savedAttemptExport(first, [first]));
  assert.deepEqual(result.members[0].record, first);
  assert.deepEqual(result.members[1], { run_id: 'B', record: null });
  assert.deepEqual(result.missing_members, ['B']);
  assert.equal(result.telemetry_included, false);
  assert.equal(JSON.stringify(first), snapshot);
});
