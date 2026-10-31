import assert from 'node:assert/strict';
import test from 'node:test';
import { fieldBlockReason, identityMismatch, validatePayload } from '../src/analysis/display.ts';

const identity = {
  configuration_id: 'test-vehicle',
  resolved_spec_sha256: 'a'.repeat(64),
  cad_revision_sha256: 'b'.repeat(64),
  part_shape_sha256: { hot_part: 'c'.repeat(64), cold_part: 'd'.repeat(64) },
};

test('only the exact recorded vehicle, source and part geometry identity can attach', () => {
  const manifest = { compatible: true, identity };
  assert.equal(identityMismatch(manifest, 'test-vehicle', identity), null);
  assert.match(identityMismatch(manifest, 'different-vehicle', identity), /Configuration/);
  assert.match(
    identityMismatch(manifest, 'test-vehicle', {
      ...identity,
      cad_revision_sha256: 'e'.repeat(64),
    }),
    /CAD generator/,
  );
  assert.match(
    identityMismatch(manifest, 'test-vehicle', {
      ...identity,
      resolved_spec_sha256: 'f'.repeat(64),
    }),
    /specification/,
  );
  assert.match(
    identityMismatch(manifest, 'test-vehicle', {
      ...identity,
      part_shape_sha256: { hot_part: identity.part_shape_sha256.hot_part },
    }),
    /part geometry/i,
  );
  assert.match(
    identityMismatch(
      { ...manifest, compatible: false, incompatible_reason: 'historical mesh' },
      'test-vehicle',
      identity,
    ),
    /historical mesh/,
  );
});

test('missing coverage stays null and malformed or nonfinite field samples are rejected', () => {
  const field = {
    association: 'part',
    sample_count: 2,
    part_ids: ['hot_part', 'cold_part'],
    times_s: [0, 1],
  };
  const data = {
    part_ids: field.part_ids,
    values: [
      [300, null],
      [310, null],
    ],
  };
  assert.doesNotThrow(() => validatePayload(field, data));
  assert.equal(data.values[1][1], null);
  assert.throws(() => validatePayload(field, { ...data, values: [[300], [310]] }), /shape/);
  assert.throws(
    () => validatePayload(field, { ...data, part_ids: ['cold_part', 'hot_part'] }),
    /part order/,
  );
  assert.throws(
    () =>
      validatePayload(field, {
        ...data,
        values: [
          [Infinity, null],
          [310, null],
        ],
      }),
    /values/,
  );
});

test('spatial fields require an explicit supported registration and cannot infer surfaces from measured points', () => {
  const field = {
    association: 'measured_point',
    sample_count: 1,
    part_ids: ['hot_part'],
    times_s: null,
    registration: null,
  };
  assert.throws(() => validatePayload(field, { values: [[300]] }), /registration/);
});


test('failed numerical fields cannot color active geometry', () => {
  assert.match(fieldBlockReason({ evidence: { provenance: 'calculated', validation: 'failed' } }), /FAILED/);
  assert.equal(fieldBlockReason({ evidence: { provenance: 'calculated', validation: 'unvalidated' } }), '');
});
