import assert from 'node:assert/strict';
import test from 'node:test';
import { replayDiagnosticReport } from '../src/experiments/replayDiagnosticReport.ts';
import { createPlaybackSessionCapture } from '../src/experiments/playbackSessionCapture.ts';

const base = {
  primary: { run_id: 'software-fixture', configuration: 'test-only' },
  profileMode: 'full-rate-benchmark', frameDeltas: Array(600).fill(17.5),
  sourceRows: 132856, returnedRows: 132856,
  drawingA: null, loadProfile: null, scrubProfile: null, heap: null,
  viewport: { width: 1440, height: 900, devicePixelRatio: 2 }, userAgent: 'unit fixture',
};

test('full-session export is additive and cannot masquerade as the recent rolling window', () => {
  const session = createPlaybackSessionCapture({
    primary: { run_id: 'software-fixture' }, profileMode: 'full-rate-benchmark',
    speed: 1, firstObservedCursorS: 0.001, startedWallMs: 0,
  });
  for (let i = 0; i < 1200; i++) session.appendFrame({
    deltaMs: 16, observedCursorS: i * 0.016,
    documentVisibility: 'visible', windowFocused: true, canvasIntersectionFraction: 1,
  });
  const full = { ...session.snapshot({ lastObservedCursorS: 19.2, endedWallMs: 19200 }), host_javascript_heap: { initial: null, final: null, scope: 'software fixture; unavailable, not zero' } };
  const report = replayDiagnosticReport({ ...base, fullSessionObservation: full });
  assert.equal(report.frames.raw_intervals_ms.length, 600);
  assert.equal(report.frames.mean_interval_target_met, false);
  assert.equal(report.full_session_observation.raf.raw_frames.length, 1200);
  assert.equal(report.full_session_observation.raf.mean_interval_target_met, true);
  assert.equal(report.full_session_observation.context.last_observed_cursor_s, 19.2);
  assert.match(report.full_session_observation.acceptance, /No automatic/);
  assert.equal(report.engineering_or_flight_approval, false);
  assert.equal(report.full_session_observation.host_javascript_heap.initial, null);
  assert.equal(report.full_session_observation.host_javascript_heap.final, null);
  assert.deepEqual(report.source.primary, base.primary);
  assert.deepEqual(base.frameDeltas, Array(600).fill(17.5));
});

test('missing full-session or memory observations stay null rather than a fake zero', () => {
  const report = replayDiagnosticReport(base);
  assert.equal(report.full_session_observation, null);
  assert.equal(report.javascript_heap, null);
  assert.equal(report.environment.canvas_visible_area_fraction_at_export, null);
  assert.equal(JSON.parse(JSON.stringify(report)).full_session_observation, null);
});
