import assert from 'node:assert/strict';
import test from 'node:test';
import { plotScale, scaleLabels } from '../src/experiments/plotScale.ts';

test('plot scale fits nonzero and very small recorded variations', () => {
  assert.deepEqual(plotScale([0.999, 1, 1.001]), { min: 0.999, max: 1.001 });
  assert.deepEqual(scaleLabels(0.000001, 0.000002), ['0.000001', '0.000002']);
  const labels = scaleLabels(1.000000001, 1.000000002);
  assert.notEqual(labels[0], labels[1]);
});

test('constant and all-zero samples get a nonzero display range', () => {
  const constant = plotScale([5, 5]);
  assert.ok(constant.min < 5 && constant.max > 5);
  assert.deepEqual(plotScale([0, 0]), { min: -0.001, max: 0.001 });
});
