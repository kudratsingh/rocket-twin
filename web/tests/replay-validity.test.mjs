import assert from 'node:assert/strict';
import test from 'node:test';
import { replayValidity } from '../src/experiments/replayValidity.ts';

const run = {
  run_id: 'exp-example', configuration: 'modular-performance-v1', controller: 'locked, unguided',
  code_sha256: 'code', resolved_sha256: 'spec', trajectory_complete: true,
  events: { ignition: 0, guide_exit: 0.17, burnout: 1.8, apogee: 10.4, deployment: 10.7, landing: 116 },
};

test('identifies the recorded run and event-derived phases, including descent and landing', () => {
  assert.equal(replayValidity(run, 10.3).phase, 'Before recorded apogee trigger');
  assert.match(replayValidity(run, 10.4).phase, /After apogee/);
  const descent = replayValidity(run, 11.15);
  assert.equal(descent.phase, 'After modeled deployment start');
  assert.equal(descent.controller, 'locked, unguided');
  assert.equal(descent.sourceIdentity.simulationCode, 'code');
  assert.deepEqual(descent.missingEvents, []);
  assert.match(replayValidity(run, 116).phase, /recorded landing/);
});

test('missing, malformed, and inconsistent evidence remains unavailable', () => {
  const incomplete = { run_id: 'old', configuration: 'unknown', trajectory_complete: false,
    events: { ignition: 0, apogee: null, deployment: 3, landing: Number.NaN } };
  const result = replayValidity(incomplete, 4);
  assert.match(result.phase, /unavailable/);
  assert.match(result.completion, /Incomplete/);
  assert.equal(result.controller, 'unavailable in record');
  assert.equal(result.sourceIdentity.simulationCode, 'unavailable');
  assert.deepEqual(result.missingEvents, ['guide_exit', 'burnout', 'apogee', 'landing']);
  assert.match(replayValidity({ ...run, events: { apogee: 10, deployment: 5 } }, 6).phase, /unavailable/);
  assert.match(replayValidity({ ...run, trajectory_complete: undefined }, 1).completion, /unavailable/);
});
