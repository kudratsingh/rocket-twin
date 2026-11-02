import assert from 'node:assert/strict';
import test from 'node:test';
import {
  compatibleExtension,
  extensionExportDocument,
  firstAvailablePart,
  quantityText,
} from '../src/workbench/extendedTypes.ts';

test('extension records attach only to the same frozen configuration, spec and CAD identity', () => {
  const identity = { configuration_id: 'C1', specification_sha256: 'frozen', cad_revision: null };
  assert.equal(compatibleExtension(identity, { ...identity }), true);
  for (const changed of [
    { configuration_id: 'R1' },
    { specification_sha256: 'changed' },
    { cad_revision: 'historical-cad' },
  ])
    assert.equal(compatibleExtension(identity, { ...identity, ...changed }), false);
});
test('unavailable scalar evidence never renders as zero and actual zero remains visible', () => {
  assert.equal(quantityText({ value: null, unit: '°C' }), 'Unavailable (°C)');
  assert.equal(quantityText({ value: NaN, unit: 'N' }), 'Unavailable (N)');
  assert.equal(quantityText({ value: Infinity, unit: 'mm' }), 'Unavailable (mm)');
  assert.equal(quantityText({ value: 0, unit: 'g' }), '0 g');
});
test('candidate source links never select a missing current-C1 part', () => {
  const available = new Set(['source-fin', 'source-cap']);
  assert.equal(firstAvailablePart(['candidate-only', 'source-fin'], available), 'source-fin');
  assert.equal(firstAvailablePart(['candidate-only'], available), null);
  assert.equal(firstAvailablePart([], available), null);
});

test('SVG downloads retain all extension sources without mutating frozen C1 provenance', () => {
  const identity = { configuration_id: 'C1', specification_sha256: 'frozen', cad_revision: null };
  const base = { id: 'frozen-c1', identity, generated_from: [{ id: 'base' }] };
  const extension = {
    id: 'extended',
    label: 'Candidate and connection history',
    status: 'Preliminary',
    identity: { ...identity },
    generated_from: [{ id: 'base' }, { id: 'new-evidence' }],
  };
  const result = extensionExportDocument(base, extension);
  assert.equal(result.id, 'extended');
  assert.deepEqual(
    result.generated_from.map((s) => s.id),
    ['base', 'new-evidence'],
  );
  assert.deepEqual(base.generated_from, [{ id: 'base' }]);
  assert.throws(
    () =>
      extensionExportDocument(base, {
        ...extension,
        identity: { ...identity, specification_sha256: 'wrong' },
      }),
    /incompatible/,
  );
});
