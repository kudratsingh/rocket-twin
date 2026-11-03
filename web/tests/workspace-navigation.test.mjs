import { URL } from 'node:url';
import assert from 'node:assert/strict';
import test from 'node:test';
import { designHref, readWorkspace, workspaceHref } from '../src/workspaces/navigation.ts';

test('focused routes and legacy entry links have a recoverable default', () => {
  for (const workspace of ['design', 'engineering', 'experiments', 'replay', 'analysis']) {
    assert.deepEqual(readWorkspace(`?workspace=${workspace}`), { workspace, notice: null });
  }
  assert.equal(readWorkspace('?workspace=inspect').workspace, 'design');
  assert.equal(readWorkspace('?workspace=experiment').workspace, 'experiments');
  assert.equal(readWorkspace('?workspace=workbench').workspace, 'engineering');
  assert.equal(readWorkspace('').workspace, 'design');
  assert.match(readWorkspace('?workspace=obsolete').notice, /Unknown workspace/);
  assert.equal(readWorkspace('?workspace=__proto__').workspace, 'design');
});

test('workspace navigation retains legacy engineering topic, identity, run and fragment', () => {
  const next = workspaceHref(
    '/?workspace=engineering&view=g80-fixed&design=F1&run=old#section',
    'design',
  );
  const url = new URL(next, 'http://test.local');
  assert.equal(url.searchParams.get('workspace'), 'design');
  assert.equal(url.searchParams.get('view'), 'g80-fixed');
  assert.equal(url.searchParams.get('design'), 'F1');
  assert.equal(url.searchParams.get('run'), 'old');
  assert.equal(url.hash, '#section');
});

test('changing design clears incompatible associations without mutating the original link', () => {
  const before =
    '/?workspace=analysis&design=old&part=fin&run=r1&result=s1&compare=r2&view=thermal';
  const url = new URL(designHref(before, 'new'), 'http://test.local');
  assert.equal(url.searchParams.get('design'), 'new');
  for (const key of ['part', 'run', 'result', 'compare'])
    assert.equal(url.searchParams.has(key), false);
  assert.equal(url.searchParams.get('view'), 'thermal');
  assert.equal(
    new URL(designHref(before, 'old'), 'http://test.local').searchParams.get('part'),
    'fin',
  );
});
