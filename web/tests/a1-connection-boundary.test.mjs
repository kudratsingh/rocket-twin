import assert from 'node:assert/strict';
import test from 'node:test';
import { a1ValueText, isMissingA1Route, validateA1Snapshot } from '../src/workbench/a1Types.ts';

const snapshot = {
  schema_version: '1.0.0',
  id: 'a1-source-snapshot',
  identity: { candidate_id: 'A1', source_identity: 'sha256:source', cad_revision: null, frame: 'nose tip', units: 'mm, g, N' },
  generated_from: [],
  geometry: {
    sleeve_length: { value: 120, unit: 'mm', state: 'estimated', note: 'source concept' },
    sleeve_outer_diameter: { value: 63.4, unit: 'mm', state: 'estimated', note: 'source concept' },
    sleeve_inner_diameter: { value: 61.4, unit: 'mm', state: 'estimated', note: 'source concept' },
    upper_stop_station: { value: 918, unit: 'mm', state: 'estimated', note: 'source concept' },
    axial_overlap: { value: 40, unit: 'mm', state: 'estimated', note: 'source concept' },
    index_feature_count: { value: 3, unit: '', state: 'estimated', note: 'source concept' },
    retention_feature_count: { value: 3, unit: '', state: 'estimated', note: 'source concept' },
    features: [],
  },
  fit_rows: [],
  paths: [],
  protected_volumes: [],
  mass: { net_delta: { value: null, unit: 'g', state: 'unavailable', note: 'not solved' }, ledger_rows: [] },
  cases: [],
  findings: [],
};

test('A1 is an independent versioned snapshot and rejects an invented CAD association', () => {
  assert.equal(validateA1Snapshot(snapshot).identity.candidate_id, 'A1');
  assert.throws(() => validateA1Snapshot({ ...snapshot, schema_version: '2.0.0' }), /incompatible/);
  assert.throws(() => validateA1Snapshot({ ...snapshot, identity: { ...snapshot.identity, candidate_id: 'C1' } }), /incompatible/);
  assert.throws(() => validateA1Snapshot({ ...snapshot, identity: { ...snapshot.identity, cad_revision: 'archived-72-part' } }), /incompatible/);
});

test('unknown fit and mass evidence is explicit, while measured zero remains zero', () => {
  assert.equal(a1ValueText({ value: null, unit: 'g' }), 'Unavailable');
  assert.equal(a1ValueText({ value: NaN, unit: 'mm' }), 'Unavailable');
  assert.equal(a1ValueText({ value: 0, unit: 'mm' }), '0 mm');
});

test('prepared A1 export is used only for an unmatched API route', () => {
  assert.equal(isMissingA1Route(404, 'Not Found'), true);
  assert.equal(isMissingA1Route(404, 'A1 source record missing'), false);
  assert.equal(isMissingA1Route(500, 'Not Found'), false);
});
