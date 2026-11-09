import { frameProfile } from './playbackProfile.ts';
import type { ReplaySessionObservationSnapshot } from './useReplaySessionCapture.ts';

type Source = {
  run_id: string;
  configuration: string;
  code_sha256?: string;
  resolved_sha256?: string;
  cad_revision_sha256?: string;
};
export type ReplayDiagnosticInput = {
  primary: Source;
  comparison?: Source | null;
  profileMode: string;
  frameDeltas: readonly number[];
  fullSessionObservation?: ReplaySessionObservationSnapshot | null;
  sourceRows: number | null;
  returnedRows: number;
  drawingA: unknown;
  drawingB?: unknown;
  loadProfile: unknown;
  scrubProfile: unknown;
  heap: unknown;
  viewport: {
    width: number;
    height: number;
    devicePixelRatio: number;
    canvasWidth?: number;
    canvasHeight?: number;
    canvasLeft?: number;
    canvasTop?: number;
  };
  userAgent: string;
};

/** A read-only app-owned observation export, not a simulation or automatic acceptance. */
export function replayDiagnosticReport(input: ReplayDiagnosticInput) {
  const deltas = [...input.frameDeltas].slice(-600);
  const valid = deltas.length > 0 && deltas.every((value) => Number.isFinite(value) && value > 0);
  const profile = valid ? frameProfile(deltas) : null;
  const viewport = input.viewport;
  const validViewport = [viewport.width, viewport.height, viewport.devicePixelRatio].every(
    (value) => Number.isFinite(value) && value > 0,
  );
  const canvas = viewport;
  const observedCanvas = [
    canvas.canvasWidth,
    canvas.canvasHeight,
    canvas.canvasLeft,
    canvas.canvasTop,
  ].every((value) => typeof value === 'number' && Number.isFinite(value));
  const visibleArea =
    observedCanvas && canvas.canvasWidth! > 0 && canvas.canvasHeight! > 0 && validViewport
      ? (Math.max(
          0,
          Math.min(viewport.width, canvas.canvasLeft! + canvas.canvasWidth!) -
            Math.max(0, canvas.canvasLeft!),
        ) *
          Math.max(
            0,
            Math.min(viewport.height, canvas.canvasTop! + canvas.canvasHeight!) -
              Math.max(0, canvas.canvasTop!),
          )) /
        (canvas.canvasWidth! * canvas.canvasHeight!)
      : null;
  return {
    schema_version: 'rocket-twin.replay-diagnostic.v1',
    source: { primary: input.primary, comparison: input.comparison ?? null },
    data_profile: input.profileMode,
    drawing_profile: 'native telemetry / separately bounded drawing; source arrays unchanged',
    source_rows: input.sourceRows,
    returned_rows: input.returnedRows,
    drawing: { a: input.drawingA, b: input.drawingB ?? null },
    frames: {
      status: valid ? 'app_observed' : 'unavailable_or_invalid',
      scope:
        'Rolling last at most600 requestAnimationFrame intervals in milliseconds; not all playback, GPU completion or endurance.',
      received_interval_count: input.frameDeltas.length,
      raw_intervals_ms: deltas.map((value) => (Number.isFinite(value) ? value : null)),
      recent_duration_ms: valid ? deltas.reduce((a, b) => a + b, 0) : null,
      profile,
      target_fps: 60,
      target_interval_ms: 1000 / 60,
      mean_interval_target_met: profile ? profile.mean_ms <= 1000 / 60 : null,
      acceptance:
        'No automatic full benchmark acceptance; use exact source, representative data, host, viewport, load/scrub/memory limits and separately observed native behavior.',
    },
    full_session_observation: input.fullSessionObservation ?? null,
    full_session_scope:
      'Bounded last Play epoch when supplied; observed RAF, cursor and cached visibility conditions, not automatic benchmark acceptance or GPU completion. Legacy rolling diagnostics remain separate.',
    environment: {
      viewport_css_pixels: validViewport ? viewport : null,
      viewport_basis:
        'Reported by the running application; no viewport resizing, DevTools, CDP or inferred raster dimensions.',
      canvas_visible_area_fraction_at_export: visibleArea,
      canvas_visibility_scope:
        'Export-time rectangle intersection only; does not establish visibility during the recorded playback interval.',
      user_agent: input.userAgent,
      cpu_time: null,
      cpu_affinity: null,
      gpu_process_memory: null,
    },
    load: input.loadProfile,
    scrub: input.scrubProfile,
    javascript_heap: input.heap,
    memory_scope:
      'performance.memory JavaScript heap when supported; not total process/GPU memory. Missing is unavailable, never zero.',
    simulation_started: false,
    engineering_or_flight_approval: false,
  };
}
