import { useEffect, useMemo, useRef } from 'react';
import { Line } from '@react-three/drei';
import { replayDrawingDiagnostics, selectReplayDrawing } from '../experiments/replayDrawing';

export type ReplayTrajectoryDiagnostics = ReturnType<typeof replayDrawingDiagnostics>;
/** Drawing only; callers must continue passing the original columns to replayPose. */
export function ReplayTrajectory({
  columns,
  events,
  color,
  maxVertices = 3000,
  onDiagnostics,
}: {
  columns: Record<string, number[]>;
  events?: Record<string, number | null>;
  color: string;
  maxVertices?: number;
  onDiagnostics?: (value: ReplayTrajectoryDiagnostics) => void;
}) {
  const drawing = useMemo(
    () =>
      selectReplayDrawing(columns.time_s, [columns.east_m, columns.down_m, columns.north_m], {
        maxVertices,
        events,
      }),
    [columns, events, maxVertices],
  );
  const paths = useMemo(
    () =>
      drawing.segments.map((segment) =>
        segment.map(
          (index) =>
            [columns.east_m[index], -columns.down_m[index], -columns.north_m[index]] as [
              number,
              number,
              number,
            ],
        ),
      ),
    [drawing, columns],
  );
  const diagnosticCallback = useRef(onDiagnostics);
  useEffect(() => {
    diagnosticCallback.current = onDiagnostics;
  }, [onDiagnostics]);
  useEffect(() => {
    diagnosticCallback.current?.(replayDrawingDiagnostics(drawing));
  }, [drawing]);
  return (
    <>
      {paths.map((points, index) =>
        points.length > 1 ? (
          <Line key={index} points={points} color={color} lineWidth={2} />
        ) : (
          <mesh key={index} position={points[0]}>
            <sphereGeometry args={[0.02, 6, 4]} />
            <meshBasicMaterial color={color} />
          </mesh>
        ),
      )}
    </>
  );
}

/** Render outside Canvas to inspect changed drawing work without opening developer tools. */
export function ReplayDrawingReadout({
  label,
  diagnostics,
}: {
  label: string;
  diagnostics: ReplayTrajectoryDiagnostics | null;
}) {
  return (
    <details>
      <summary>{label} · replay drawing work</summary>
      {diagnostics ? (
        <>
          <p>
            {diagnostics.status}: {diagnostics.reason ?? 'Drawing prepared'} ·{' '}
            {diagnostics.drawn_samples} / {diagnostics.valid_samples} valid samples drawn from{' '}
            {diagnostics.source_samples} returned samples · cap {diagnostics.max_vertices} vertices
            / 128 disconnected segments.
          </p>
          <p>
            {diagnostics.segments} segments · {diagnostics.mandatory_samples} mandatory anchors ·{' '}
            {diagnostics.event_neighbours} drawable event neighbours · preparation{' '}
            {diagnostics.preparation_ms.toFixed(3)} ms.
          </p>
          <p>
            {diagnostics.policy}. Trail lines connect retained native positions and may omit small
            spatial features; body pose still uses the full native samples. Isolated valid
            trajectory samples use a point marker. Undrawable events:{' '}
            {diagnostics.unavailable_events.join(', ') || 'none'}.
          </p>
          <p>
            App-owned synchronous JavaScript index-selection timing only; not browser paint, GPU
            work, FPS or a performance pass. Raw telemetry remains the source for body pose, sample
            readouts, events, metrics and exports.
          </p>
        </>
      ) : (
        <p>No drawing preparation observed for this run/profile yet.</p>
      )}
    </details>
  );
}
