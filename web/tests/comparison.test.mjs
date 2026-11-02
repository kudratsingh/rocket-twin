import assert from 'node:assert/strict';
import test from 'node:test';
import { comparisonDifferences, comparisonValue } from '../src/experiments/comparison.ts';

const complete = {
  configuration: 'vehicle',
  settings: { wind_mps: 0, wind_direction_deg: 0, gust_mps: 0 },
  case: { seed: 0, sensor_noise: false },
  code_sha256: 'code', resolved_sha256: 'spec', cad_revision_sha256: 'cad',
  input_sha256: { motor: 'motor-hash' },
};

test('reports matching complete records and real differences without treating zero as missing', () => {
  assert.deepEqual(comparisonDifferences(complete, complete), []);
  const changed = { ...complete, settings: { ...complete.settings, wind_mps: 1 } };
  assert.deepEqual(comparisonDifferences(complete, changed), [['setting: wind_mps', 0, 1]]);
});

test('evidence missing from both records remains unavailable', () => {
  const incomplete = { ...complete, settings: { wind_mps: 0 }, case: {}, input_sha256: {} };
  const rows = comparisonDifferences(incomplete, incomplete);
  assert.deepEqual(rows.map(([name]) => name), [
    'setting: gust_mps', 'setting: wind_direction_deg', 'case', 'input',
  ]);
  assert.ok(rows.every(([, a, b]) => a === undefined && b === undefined));
  assert.ok(comparisonDifferences({ ...complete, case: undefined }, complete)
    .some(([name, a, b]) => name === 'case: seed' && a === undefined && b === 0));
  assert.ok(comparisonDifferences({ ...complete, code_sha256: '' }, { ...complete, code_sha256: '' })
    .some(([name]) => name === 'Simulation code SHA-256'));
  assert.equal(comparisonValue(''), 'unavailable');
  assert.equal(comparisonValue(false), 'false');
  assert.equal(comparisonValue(0), '0');
});
