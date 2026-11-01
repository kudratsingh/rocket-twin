import assert from 'node:assert/strict';
import test from 'node:test';
import { requestOrder } from '../src/experiments/requestOrder.ts';

test('newer selections and cancellation suppress stale completions independently', () => {
  const primary = requestOrder();
  const comparison = requestOrder();
  const first = primary.begin();
  const other = comparison.begin();
  const second = primary.begin();
  assert.equal(first(), false);
  assert.equal(second(), true);
  assert.equal(other(), true);
  comparison.cancel();
  assert.equal(other(), false);
  assert.equal(second(), true);
});
