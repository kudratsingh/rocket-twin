import assert from 'node:assert/strict';
import test from 'node:test';
import {
  exportMetadata,
  recordedSettingsDraft,
  telemetryCsv,
} from '../src/experiments/runExport.ts';

const config = 'modular-performance-v1';
const makeRun = (id, times, values) => ({
  record: {
    run_id: id,
    configuration: config,
    vehicle_id: config,
    controller: 'locked, unguided',
    resolved_sha256: 'spec-hash',
    cad_revision_sha256: 'cad-hash',
    code_sha256: 'code-hash',
    input_sha256: { 'source.yaml': 'input-hash' },
    settings: {
      configuration: config,
      preset: 'sim',
      wind_mps: 0,
      wind_direction_deg: 20,
      gust_mps: 1,
    },
    case: { dt_s: 0.001 },
  },
  telemetry: {
    frame: 'NED',
    full_sample_count: 100,
    channel_metadata: { 'a,"quoted"': { unit: 'm', source: 'recorded-parquet', semantic_id: 'a' } },
    columns: { time_s: times, 'a,"quoted"': values, short: [0] },
  },
});

test('CSV preserves each playback timestamp, escapes names, and leaves missing values blank', () => {
  const run = makeRun('A', [0, 0.3, 1], [0, null, NaN]);
  assert.equal(telemetryCsv(run), 'time_s,"a,""quoted""",short\r\n0,0,0\r\n0.3,,\r\n1,,\r\n');
  assert.throws(() => telemetryCsv(makeRun('A', [0, 0], [1, 2])), /strictly increasing/);
  assert.throws(() => telemetryCsv(makeRun('A', [0], [1, 2])), /coverage/);
});

test('metadata retains full original identities and independent comparison coverage and differences', () => {
  const a = makeRun('A', [0, 1, 2], [1, 2, 3]);
  const b = makeRun('B', [0, 0.5], [7, 8]);
  b.record.settings.wind_mps = 3;
  b.record.code_sha256 = 'other-code';
  const metadata = JSON.parse(exportMetadata(a, b));
  assert.deepEqual(metadata.selected_run, a.record);
  assert.deepEqual(metadata.playback.channel_metadata, a.telemetry.channel_metadata);
  assert.equal(metadata.coverage.last_time_s, 2);
  assert.equal(metadata.comparison_run.coverage.last_time_s, 0.5);
  assert.deepEqual(metadata.comparison_run.record, b.record);
  assert.ok(metadata.comparison_differences.some((row) => row[0] === 'setting: wind_mps'));
  assert.ok(metadata.comparison_differences.some((row) => row[0] === 'Simulation code SHA-256'));
  assert.equal(telemetryCsv(b).split('\r\n').length, 4);
});

test('only complete supported matching settings can become a draft without modifying the record', () => {
  const run = makeRun('A', [0], [0]);
  const before = JSON.stringify(run.record);
  assert.deepEqual(recordedSettingsDraft(run.record, config), {
    ok: true,
    wind: 0,
    direction: 20,
    gust: 1,
  });
  assert.equal(JSON.stringify(run.record), before);
  assert.equal(recordedSettingsDraft(run.record, 'modular-tvc-finned-v1').ok, false);
  assert.equal(
    recordedSettingsDraft(
      { ...run.record, settings: { ...run.record.settings, preset: 'tiny' } },
      config,
    ).ok,
    false,
  );
  assert.equal(
    recordedSettingsDraft({ ...run.record, settings: { ...run.record.settings, seed: 42 } }, config)
      .ok,
    false,
  );
  assert.equal(
    recordedSettingsDraft(
      { ...run.record, settings: { ...run.record.settings, gust_mps: null } },
      config,
    ).ok,
    false,
  );
  assert.equal(recordedSettingsDraft({ ...run.record, controller: 'PID' }, config).ok, false);
});
