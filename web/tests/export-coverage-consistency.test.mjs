import assert from 'node:assert/strict';
import test from 'node:test';
import { exportMetadata, telemetryCsv } from '../src/experiments/runExport.ts';

const run = (id, times, channels = {}) => ({
  record: { run_id: id, configuration: 'fixture', metrics: { raw_peak: 123 } },
  telemetry: {
    frame: 'fixture',
    channel_metadata: { height: { unit: 'm', source: 'fixture', semantic_id: 'height' } },
    columns: { time_s: times, ...channels },
  },
});

test('metadata cannot describe coverage that its companion CSV must withhold', () => {
  for (const times of [[], [0, 0], [1, 0], [0, NaN], [0, Infinity], [0, null]]) {
    const invalid = run('bad-axis', times);
    for (const exportRun of [telemetryCsv, exportMetadata])
      assert.throws(() => exportRun(invalid), /time samples.*strictly increasing/);
  }
  for (const values of [null, [1, 2, 3]]) {
    const invalid = run('bad-channel', [0, 1], { height: values });
    for (const exportRun of [telemetryCsv, exportMetadata])
      assert.throws(() => exportRun(invalid), /Channel height has invalid coverage/);
  }
});

test('comparison metadata also rejects an invalid peer instead of claiming its support', () => {
  const a = run('A', [0, 1], { height: [0, 1] });
  assert.throws(() => exportMetadata(a, run('B', [2, 2])), /time samples/);
  assert.throws(
    () => exportMetadata(a, run('B', [0, 2], { height: [0, 1, 2] })),
    /Channel height has invalid coverage/,
  );
  for (const selection of [
    { start_s: 0, end_s: 1, offset_s: NaN },
    { start_s: 2, end_s: 1, offset_s: 0 },
    { start_s: 0, end_s: 1, offset_s: 0, peer_offset_s: Infinity },
  ])
    assert.throws(
      () => exportMetadata(a, run('B', [0, 2]), { alignment_event: null, ...selection }),
      /invalid range or clock offset/,
    );
});

test('aligned unequal coverage keeps raw timestamps, genuine zero and explicit short/null gaps', () => {
  const a = run('A', [1, 2, 3, 4], { height: [0, null, 4, 8], short: [0] });
  const b = run('B', [10, 11, 12], { height: [0, null, 9] });
  const before = JSON.stringify([a, b]);
  const selection = {
    start_s: -1,
    end_s: 1,
    offset_s: 2,
    peer_offset_s: 10,
    alignment_event: 'burnout',
  };
  const csv = telemetryCsv(a, selection);
  const metadata = JSON.parse(exportMetadata(a, b, selection));
  assert.equal(csv, 'time_s,height,short\r\n1,0,0\r\n2,,\r\n3,4,\r\n');
  assert.equal(metadata.selection.selected_sample_count, 3);
  assert.equal(metadata.comparison_run.coverage.selected_sample_count, 2);
  assert.equal(metadata.coverage.first_time_s, 1);
  assert.equal(metadata.coverage.last_time_s, 4);
  assert.equal(metadata.coverage.channel_sample_counts.short, 1);
  assert.deepEqual(metadata.selected_run.metrics, { raw_peak: 123 });
  assert.deepEqual(metadata.playback.channel_metadata, a.telemetry.channel_metadata);
  assert.equal(JSON.stringify([a, b]), before);
});
