import assert from 'node:assert/strict';
import test from 'node:test';
import { channelOptions, label, series, comparisonReason, displayedMetadata } from '../src/experiments/channels.ts';

test('picker discovers new recorded columns across both runs without inventing units', () => {
  const a = { time_s: [0, 1], height_m: [0, 2], new_sensor_xyz: [3, 4] };
  const b = { time_s: [0, 1], other_channel: [5, 6] };
  assert.deepEqual(new Set(channelOptions(a, b)), new Set(['height_m', 'new_sensor_xyz', 'other_channel']));
  assert.equal(label('new_sensor_xyz'), 'new_sensor_xyz');
  assert.equal(label('height_m'), 'Height above launch (m)');
  assert.equal(series(a, 'other_channel'), null);
  assert.deepEqual(series(b, 'other_channel'), [5, 6]);
});

test('missing, nonfinite, and mismatched samples remain unavailable', () => {
  const columns = { time_s: [0, 1], missing: [], short: [1], invalid: [1, NaN], zero: [0, 0] };
  assert.equal(series(columns, 'missing'), null);
  assert.equal(series(columns, 'short'), null);
  assert.equal(series(columns, 'invalid'), null);
  assert.deepEqual(series(columns, 'zero'), [0, 0]);
});


test('comparison requires known matching units, semantics, source and simulation identity', () => {
  const meta = { unit: 'm', semantic_id: 'wo05-v1:height_m', source: 'backend-derived' };
  assert.equal(comparisonReason(meta, meta, 'abc', 'abc'), null);
  assert.match(comparisonReason(meta, { ...meta, unit: 'ft' }, 'abc', 'abc'), /withheld/);
  assert.match(comparisonReason(meta, { ...meta, semantic_id: null }, 'abc', 'abc'), /withheld/);
  assert.match(comparisonReason(meta, meta, 'abc', 'def'), /withheld/);
  assert.match(comparisonReason(undefined, meta, 'abc', 'abc'), /withheld/);
});

test('only the displayed run supplies graph metadata, even when the other advertises a channel', () => {
  const a = { unit: 'm', semantic_id: 'a', source: 'recorded-parquet', description: 'A' };
  const b = { unit: 's', semantic_id: 'b', source: 'backend-derived', description: 'B' };
  assert.deepEqual(displayedMetadata(false, true, a, b), { run: 'B', meta: b });
  assert.deepEqual(displayedMetadata(true, false, undefined, b), { run: 'A', meta: undefined });
  assert.deepEqual(displayedMetadata(true, true, a, b), { run: 'A', meta: a });
  assert.equal(displayedMetadata(false, false, a, b), null);
});
