import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { requestOrder } from './requestOrder';
import {
  acceptedAttemptIds,
  attemptSummary,
  readAttemptStatuses,
  savedAttemptExport,
  savedAttemptIds,
  experimentJson as json,
} from './attemptMonitor';
import type { AttemptStatus } from './attemptMonitor';
import { playbackStep } from './playbackStep';
import { ExactReplayTime } from './ExactReplayTime.tsx';
import { replayValidity } from './replayValidity';
import { firstRecordedTime, replayWindow, replayWindowStatus } from './replayWindow';
import { replayPose } from './replayPose';
import type { ReplayPose } from './replayPose';
import { comparisonDifferences, comparisonValue } from './comparison';
import { plotScale, scaleLabels } from './plotScale';
import { exportMetadata, telemetryCsv } from './runExport';
import { adjustPlotWindow, plotSegments, recordedAlignment } from './plotWindow';
import type { PlotWindow } from './plotWindow';
import { batchDeclaration, requestDraft, terminalStatuses } from './runLifecycle';
import type { ExperimentRequest } from './runLifecycle';
import { filterRuns, frameProfile } from './playbackProfile';
import { browserHeap, telemetryUrl, validatePlaybackProfile } from './playbackMode';
import type { PlaybackMode } from './playbackMode';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Line, OrbitControls, useGLTF } from '@react-three/drei';
import { Vector3 } from 'three';
import type { OrbitControls as OrbitControlsType } from 'three-stdlib';
import type { InspectionDocument, Part } from '../types';
import {
  channelOptions,
  comparisonReason,
  defaultChannels,
  displayedMetadata,
  label,
  nearestSample,
  prepareSamples,
} from './channels';
import type { ChannelMeta } from './channels';
import './experiment.css';

type RecordRun = {
  run_id: string;
  status: string;
  progress: string;
  error?: string;
  configuration: string;
  controller?: string;
  vehicle_id?: string;
  resolved_sha256?: string;
  cad_revision_sha256?: string;
  code_sha256?: string;
  input_sha256?: Record<string, string>;
  case?: Record<string, number | boolean>;
  settings: ExperimentRequest;
  created_at?: string;
  random_seed?: number;
  effective_settings?: Record<string, unknown>;
  resources?: Record<string, unknown>;
  batch_id?: string | null;
  batch_members?: string[];
  metrics?: Record<string, number | boolean | null>;
  events?: Record<string, number | null>;
  trajectory_complete?: boolean;
  validity?: string[];
  limitations: string[];
};
type Telemetry = {
  run_id: string;
  frame: string;
  columns: Record<string, number[]>;
  channel_metadata?: Record<string, ChannelMeta>;
  full_sample_count?: number;
  returned_sample_count?: number;
  sampling?: { mode?: string; policy?: string; benchmark_bounds?: Record<string, unknown> };
};
type Loaded = {
  record: RecordRun;
  telemetry: Telemetry;
  vehicle: InspectionDocument;
  playbackMode: PlaybackMode;
};
const choices = [
  ['modular-performance-v1', 'Performance · G80 reference'],
  ['modular-performance-g54-hypothesis', 'Performance · G54 conditional'],
  ['modular-tvc-finned-v1', 'Finned trainer · G12, locked gimbal'],
  ['modular-tvc-finless-v1', 'Finless trainer · static inspection only'],
];
function MeshPart({ part }: { part: Part }) {
  const model = useGLTF(part.mesh_url!);
  const scene = useMemo(() => model.scene.clone(true), [model]);
  return <primitive object={scene} />;
}
function FlightGeometry({
  run,
  pose,
}: {
  run: Loaded;
  pose: Extract<ReplayPose, { kind: 'pose' }>;
}) {
  return (
    <group position={pose.position} quaternion={pose.quaternion}>
      <group position={pose.pivot}>
        {run.vehicle.parts
          .filter((p) => p.mesh_url)
          .map((p) => (
            <Suspense key={p.id} fallback={null}>
              <MeshPart part={p} />
            </Suspense>
          ))}
      </group>
    </group>
  );
}
function ReplayCamera({
  loc,
  mode,
  fitToken,
  run,
}: {
  loc: Vector3 | null;
  mode: 'follow' | 'pad' | 'free';
  fitToken: number;
  run: Loaded;
}) {
  const controls = useRef<OrbitControlsType>(null);
  const previous = useRef<Vector3 | null>(null);
  const { camera } = useThree();
  useEffect(() => {
    if (mode === 'pad') {
      camera.position.set(12, 3, 12);
      controls.current?.target.set(0, 3, 0);
      controls.current?.update();
    }
    previous.current = null;
  }, [mode, camera]);
  useEffect(() => {
    previous.current = null;
  }, [camera, run]);
  useEffect(() => {
    if (!fitToken || !replayWindow(run.telemetry.columns.time_s)) return;
    const c = run.telemetry.columns;
    if (
      !['east_m', 'down_m', 'north_m'].every(
        (key) =>
          Array.isArray(c[key]) &&
          c[key].length === c.time_s.length &&
          c[key].every(Number.isFinite),
      )
    )
      return;
    const points = c.time_s.map((_, i) => new Vector3(c.east_m[i], -c.down_m[i], -c.north_m[i]));
    const min = points[0].clone(),
      max = points[0].clone();
    for (const point of points) {
      min.min(point);
      max.max(point);
    }
    const center = min.clone().add(max).multiplyScalar(0.5);
    const radius = Math.max(2, max.distanceTo(min) * 0.5);
    camera.position
      .copy(center)
      .add(new Vector3(1, 0.8, 1.4).normalize().multiplyScalar(radius * 2.8));
    controls.current?.target.copy(center);
    controls.current?.update();
    previous.current = null;
  }, [fitToken, camera, run]);
  useFrame(() => {
    if (mode === 'follow' && loc && controls.current) {
      if (previous.current) {
        const delta = loc.clone().sub(previous.current);
        camera.position.add(delta);
        controls.current.target.add(delta);
      } else {
        camera.position.copy(loc).add(new Vector3(2, 1.5, 3));
        controls.current.target.copy(loc);
      }
      previous.current = loc.clone();
      controls.current.update();
    } else previous.current = null;
  });
  return <OrbitControls ref={controls} makeDefault enableDamping />;
}
function FlightScene({
  run,
  other,
  time,
  mode,
  fitToken,
  offsets,
}: {
  run: Loaded;
  other: Loaded | null;
  time: number;
  offsets: { a: number; b: number };
  mode: 'follow' | 'pad' | 'free';
  fitToken: number;
}) {
  const path = (r: Loaded) => {
    const c = r.telemetry.columns;
    if (
      !replayWindow(c.time_s) ||
      !['east_m', 'down_m', 'north_m'].every(
        (key) =>
          Array.isArray(c[key]) &&
          c[key].length === c.time_s.length &&
          c[key].every(Number.isFinite),
      )
    )
      return null;
    return c.time_s.map(
      (_, i) =>
        [
          r.telemetry.columns.east_m[i],
          -r.telemetry.columns.down_m[i],
          -r.telemetry.columns.north_m[i],
        ] as [number, number, number],
    );
  };
  const primaryPath = useMemo(() => path(run), [run]);
  const comparisonPath = useMemo(() => (other ? path(other) : null), [other]);
  const c = run.telemetry.columns;
  const primaryPose = replayPose(c, Number(run.vehicle.summary.length_m), time + offsets.a);
  const comparisonPose = other
    ? replayPose(other.telemetry.columns, Number(other.vehicle.summary.length_m), time + offsets.b)
    : null;
  const loc = primaryPose.kind === 'unavailable' ? null : new Vector3(...primaryPose.position);
  const theta = (run.record.settings.wind_direction_deg * Math.PI) / 180;
  const wind = run.record.settings.wind_mps;
  return (
    <Canvas camera={{ position: [2, 1.5, 3], fov: 45, near: 0.01, far: 5000 }}>
      <ambientLight intensity={1.4} />
      <directionalLight position={[20, 50, 30]} intensity={2} />
      <ReplayCamera loc={loc} mode={mode} fitToken={fitToken} run={run} />
      <gridHelper args={[100, 20, '#38505b', '#24343c']} />
      {primaryPath && <Line points={primaryPath} color="#54d8d2" lineWidth={2} />}
      {comparisonPath && <Line points={comparisonPath} color="#f5b960" lineWidth={2} />}
      {primaryPose.kind === 'pose' && (
        <>
          <FlightGeometry run={run} pose={primaryPose} />
          <mesh position={primaryPose.position}>
            <sphereGeometry args={[0.03, 10, 8]} />
            <meshBasicMaterial color="#ffffff" depthTest={false} />
          </mesh>
        </>
      )}
      {primaryPose.kind === 'marker' && (
        <mesh position={primaryPose.position}>
          <sphereGeometry args={[0.08, 12, 8]} />
          <meshBasicMaterial color="#54d8d2" />
        </mesh>
      )}
      {other && comparisonPose?.kind === 'pose' && (
        <FlightGeometry run={other} pose={comparisonPose} />
      )}
      {comparisonPose?.kind === 'marker' && (
        <mesh position={comparisonPose.position}>
          <sphereGeometry args={[0.08, 12, 8]} />
          <meshBasicMaterial color="#f5b960" />
        </mesh>
      )}
      {wind > 0 && (
        <arrowHelper
          args={[
            new Vector3(Math.sin(theta), 0, -Math.cos(theta)),
            new Vector3(0, 0.1, 0),
            Math.max(3, wind),
            '#f5b960',
          ]}
        />
      )}
    </Canvas>
  );
}
function StaticPreview({ vehicle, reset }: { vehicle: InspectionDocument; reset: number }) {
  const length = typeof vehicle.summary.length_m === 'number' ? vehicle.summary.length_m : null;
  if (!length || !vehicle.parts.some((p) => p.mesh_url))
    return (
      <div className="exp-empty">Actual CAD geometry is unavailable for this configuration.</div>
    );
  return (
    <Canvas
      key={`${vehicle.id}-${reset}`}
      camera={{ position: [2, length / 2 + 1, 2], fov: 35, near: 0.001, far: 100 }}
    >
      <ambientLight intensity={1.4} />
      <directionalLight position={[2, 3, 3]} intensity={2} />
      <OrbitControls makeDefault target={[0, length / 2, 0]} />
      <gridHelper args={[4, 20, '#38505b', '#24343c']} />
      {vehicle.parts
        .filter((p) => p.mesh_url)
        .map((p) => (
          <Suspense key={p.id} fallback={null}>
            <MeshPart part={p} />
          </Suspense>
        ))}
    </Canvas>
  );
}
function headline(n: number | boolean | null | undefined, unit: string) {
  return typeof n === 'number' && Number.isFinite(n) && n >= 0
    ? `${n.toFixed(1)} ${unit}`
    : 'unavailable';
}
function RunDetails({ run, label }: { run: Loaded; label: string }) {
  const record = run.record;
  const settings = record.settings;
  return (
    <section>
      <h3>
        {label}: {record.run_id}
      </h3>
      <p>
        Configuration and motor:{' '}
        {choices.find(([id]) => id === record.configuration)?.[1] ?? record.configuration}
      </p>
      <p>
        Steady wind: {settings.wind_mps} m/s · Direction toward: {settings.wind_direction_deg}°
        clockwise from north · Gust amplitude: {settings.gust_mps} m/s
      </p>
      <details>
        <summary>Run identity and simulation settings</summary>
        <p>Resolved specification SHA-256: {record.resolved_sha256 ?? 'unavailable'}</p>
        <p>CAD generator SHA-256: {record.cad_revision_sha256 ?? 'unavailable'}</p>
        <p>Simulation code SHA-256: {record.code_sha256 ?? 'unavailable'}</p>
        <p>
          Recorded seed:{' '}
          {record.random_seed ?? record.settings.seed ?? 'unavailable (historical record)'}
        </p>
        <p>Preset: {settings.preset ?? 'unavailable'}</p>
        <p>
          Effective settings:{' '}
          {record.effective_settings
            ? JSON.stringify(record.effective_settings)
            : 'unavailable (historical record)'}
        </p>
        <p>
          Resource declaration:{' '}
          {record.resources ? JSON.stringify(record.resources) : 'unavailable (historical record)'}
        </p>
        <p>Simulation case: {record.case ? JSON.stringify(record.case) : 'unavailable'}</p>
        <p>
          Input file hashes:{' '}
          {record.input_sha256 ? JSON.stringify(record.input_sha256) : 'unavailable'}
        </p>
      </details>
      <p>
        Peak height: {headline(record.metrics?.apogee_agl_m, 'm')} · Peak speed:{' '}
        {headline(record.metrics?.max_speed_mps, 'm/s')} · Guide exit speed:{' '}
        {record.events?.guide_exit == null
          ? 'unavailable'
          : headline(record.metrics?.guide_exit_mps, 'm/s')}{' '}
        · Landing displacement:{' '}
        {record.metrics?.landing_downrange_m == null
          ? 'not recorded'
          : headline(record.metrics.landing_downrange_m, 'm')}
      </p>
    </section>
  );
}
function ReplayValidity({ run, time, label }: { run: Loaded; time: number; label: string }) {
  const window = useMemo(
    () => replayWindow(run.telemetry.columns.time_s),
    [run.telemetry.columns.time_s],
  );
  const coverage = replayWindowStatus(window, time);
  const pose = replayPose(run.telemetry.columns, Number(run.vehicle.summary.length_m), time);
  const validity = replayValidity(run.record, time);
  return (
    <section aria-label={`${label} replay validity`}>
      <h3>{label} · replay validity</h3>
      <p>
        {validity.identity} · Controller: {validity.controller}
      </p>
      <p role="status">
        {coverage === 'inside'
          ? 'Inside recorded window'
          : coverage === 'outside'
            ? 'Outside recorded window'
            : 'Recorded window unavailable'}
      </p>
      {window && (
        <p>
          Recorded support: {window.start.toFixed(3)}–{window.end.toFixed(3)} s · requested{' '}
          {Number.isFinite(time) ? `${time.toFixed(3)} s` : 'time unavailable'}.
        </p>
      )}
      {pose.kind === 'marker' && <p>Position marker only: {pose.reason}.</p>}
      {pose.kind === 'unavailable' && coverage === 'inside' && (
        <p>Current position unavailable: {pose.reason}.</p>
      )}
      <p>
        {coverage === 'inside'
          ? `${validity.phase} (inferred from event times, not a recorded phase channel). `
          : 'Phase unavailable at the requested time. '}
        {validity.completion}
      </p>
      <p>
        The assembly follows the recorded body-to-world quaternion, normalized and interpolated for
        display; its orientation is not inferred from velocity. Current simulator recovery uses
        point drag with modeled inflation and angular-rate damping. Recovery attitude is approximate
        and does not establish a suspended-body orientation; canopy, lines and separation are not
        replayed.
      </p>
      <p>
        Missing event times:{' '}
        {validity.missingEvents.length
          ? validity.missingEvents.join(', ')
          : 'none among the listed events'}
        . Deployment is a modeled time derived from the apogee trigger and lag, not a recorded
        opening state.
      </p>
      <details>
        <summary>Source identity</summary>
        <p>Simulation code SHA-256: {validity.sourceIdentity.simulationCode}</p>
        <p>Resolved specification SHA-256: {validity.sourceIdentity.resolvedSpecification}</p>
        <p>
          Model description reflects current source; the saved code hash identifies the run and must
          be checked for historical correspondence.
        </p>
      </details>
    </section>
  );
}
function ComparisonDifferences({ a, b }: { a: RecordRun; b: RecordRun }) {
  const differences = comparisonDifferences(a, b);
  return (
    <details open>
      <summary>Differences and unavailable settings ({differences.length})</summary>
      {differences.length ? (
        differences.map(([label, left, right]) => (
          <p key={label}>
            <strong>{label}</strong>
            <br />
            A: {comparisonValue(left)}
            <br />
            B: {comparisonValue(right)}
          </p>
        ))
      ) : (
        <p>
          Available recorded settings and identities match; unrecorded fields cannot be compared.
        </p>
      )}
    </details>
  );
}
function Plot({
  run,
  other,
  name,
  time,
  setTime,
  setName,
  window,
  offsets,
}: {
  run: Loaded;
  other: Loaded | null;
  name: string;
  time: number;
  setTime: (v: number) => void;
  setName: (v: string) => void;
  window: PlotWindow;
  offsets: { a: number; b: number };
}) {
  const aSamples = useMemo(() => prepareSamples(run.telemetry.columns, name), [run, name]);
  const bSamples = useMemo(
    () => (other ? prepareSamples(other.telemetry.columns, name) : null),
    [other, name],
  );
  const mismatch =
    other && aSamples && bSamples
      ? comparisonReason(
          run.telemetry.channel_metadata?.[name],
          other.telemetry.channel_metadata?.[name],
          run.record.code_sha256,
          other.record.code_sha256,
        )
      : null;
  const chart = useMemo(() => {
    const a = plotSegments(run.telemetry.columns.time_s, run.telemetry.columns[name], offsets.a, {
      start: window.start,
      end: window.end,
    });
    const b =
      other && !mismatch
        ? plotSegments(other.telemetry.columns.time_s, other.telemetry.columns[name], offsets.b, {
            start: window.start,
            end: window.end,
          })
        : [];
    const available = [...a.flat(), ...b.flat()].map(([, value]) => value);
    const bounds = available.length ? plotScale(available) : { min: 0, max: 1 };
    const x = (t: number) => ((t - window.start) / (window.end - window.start || 1)) * 100;
    const y = (v: number) => 95 - ((v - bounds.min) / (bounds.max - bounds.min || 1)) * 90;
    const curves = [
      { segments: a, color: '#54d8d2' },
      { segments: b, color: '#f5b960' },
    ].flatMap(({ segments, color }, runIndex) =>
      segments.map((segment, i) =>
        segment.length === 1 ? (
          <circle
            key={`${runIndex}-${i}`}
            cx={x(segment[0][0])}
            cy={y(segment[0][1])}
            r="1"
            fill={color}
          />
        ) : (
          <polyline
            key={`${runIndex}-${i}`}
            points={segment.map(([t, v]) => `${x(t)},${y(v)}`).join(' ')}
            fill="none"
            stroke={color}
            vectorEffect="non-scaling-stroke"
          />
        ),
      ),
    );
    return { ...bounds, available, curves };
  }, [run, other, name, mismatch, offsets.a, offsets.b, window.start, window.end]);
  const { min, max, available } = chart;
  const [minLabel, maxLabel] = scaleLabels(min, max);
  const displayed = displayedMetadata(
    !!aSamples,
    !!bSamples && !mismatch,
    run.telemetry.channel_metadata?.[name],
    other?.telemetry.channel_metadata?.[name],
  );
  const x = (t: number) => ((t - window.start) / (window.end - window.start || 1)) * 100;
  const readout = (samples: ReturnType<typeof prepareSamples>, offset: number) => {
    const sample = nearestSample(samples, time + offset);
    return !sample
      ? 'unavailable at this time'
      : sample.value === null
        ? 'missing sample'
        : `${sample.value} at recorded T+${sample.time.toFixed(3)} s`;
  };
  return (
    <div className="exp-plot">
      <select aria-label="Telemetry channel" value={name} onChange={(e) => setName(e.target.value)}>
        {!channelOptions(run.telemetry.columns, other?.telemetry.columns).includes(name) && (
          <option value={name}>{label(name)} (unavailable)</option>
        )}
        {channelOptions(run.telemetry.columns, other?.telemetry.columns).map((option) => (
          <option key={option} value={option}>
            {label(option)}
          </option>
        ))}
      </select>
      <p>
        Nearest playback sample · A: {readout(aSamples, offsets.a)}
        {other && <> · B: {mismatch ? 'comparison withheld' : readout(bSamples, offsets.b)}</>}
      </p>
      <span>
        Scale: {available.length ? `${minLabel} – ${maxLabel}` : 'unavailable'}{' '}
        {displayed?.meta?.unit ?? '(units unknown)'}
      </span>
      <svg
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        tabIndex={0}
        role="img"
        aria-label={`${label(name)} plot; left and right arrows move the shared cursor`}
        onKeyDown={(e) => {
          if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') {
            e.preventDefault();
            setTime(
              Math.max(
                window.start,
                Math.min(
                  window.end,
                  time + ((e.key === 'ArrowLeft' ? -1 : 1) * (window.end - window.start)) / 100,
                ),
              ),
            );
          }
        }}
        onClick={(e) =>
          setTime(
            window.start +
              Math.max(
                0,
                Math.min(
                  1,
                  (e.clientX - e.currentTarget.getBoundingClientRect().left) /
                    e.currentTarget.clientWidth,
                ),
              ) *
                (window.end - window.start),
          )
        }
      >
        {chart.curves}
        {time >= window.start && time <= window.end && (
          <line
            x1={x(time)}
            x2={x(time)}
            y1="0"
            y2="100"
            stroke="#fff"
            vectorEffect="non-scaling-stroke"
          />
        )}
      </svg>
      {!available.length && <p>No samples in this range. Missing data is not zero.</p>}
      {!aSamples && <p>Run A channel unavailable; missing data is not zero.</p>}
      {other && !bSamples && <p>Run B channel unavailable; missing data is not zero.</p>}
      {mismatch && <p>{mismatch}</p>}
      <p>
        {displayed?.meta
          ? `Run ${displayed.run}: ${displayed.meta.description} · ${displayed.meta.source} · ${displayed.meta.unit ?? 'units unknown'}`
          : 'Channel meaning, units and source unavailable.'}
      </p>
    </div>
  );
}
export default function Experiment({
  configurationId,
  vehicle,
  onConfigurationChange,
  workspace,
  onOpenReplay,
  initialRunId,
  initialComparisonId,
  onRunSelect,
}: {
  configurationId: string;
  vehicle: InspectionDocument | null;
  onConfigurationChange: (id: string) => void;
  workspace?: 'experiments' | 'replay';
  onOpenReplay?: () => void;
  initialRunId?: string;
  initialComparisonId?: string;
  onRunSelect?: (id: string | null, comparison: boolean) => void;
}) {
  const [wind, setWind] = useState(0),
    [direction, setDirection] = useState(0),
    [gust, setGust] = useState(0),
    [seed, setSeed] = useState(0),
    [preset, setPreset] = useState<'tiny' | 'sim'>('sim'),
    [batchCount, setBatchCount] = useState(2),
    [batchEnabled, setBatchEnabled] = useState(false),
    [submitting, setSubmitting] = useState(false),
    [librarySelection, setLibrarySelection] = useState<RecordRun | null>(null),
    [libraryQuery, setLibraryQuery] = useState(''),
    [libraryStatus, setLibraryStatus] = useState('all'),
    [profile, setProfile] = useState<ReturnType<typeof frameProfile>>(null),
    [fullRateBenchmark, setFullRateBenchmark] = useState(false),
    [loadingIds, setLoadingIds] = useState<string[]>([]),
    [loadStatus, setLoadStatus] = useState(''),
    [heap, setHeap] = useState<ReturnType<typeof browserHeap>>(null),
    [scrubProfile, setScrubProfile] = useState<{
      count: number;
      last_ms: number;
      max_ms: number;
    } | null>(null),
    [loadProfile, setLoadProfile] = useState<{
      id: string;
      ms: number;
      bytes: number | null;
      samples: number;
    } | null>(null),
    [alignmentEvent, setAlignmentEvent] = useState('absolute'),
    [chartRange, setChartRange] = useState<(PlotWindow & { key: string }) | null>(null),
    [reducedMotion, setReducedMotion] = useState(false),
    [runs, setRuns] = useState<RecordRun[]>([]),
    [current, setCurrent] = useState<Loaded | null>(null),
    [other, setOther] = useState<Loaded | null>(null),
    [pending, setPending] = useState(''),
    [monitorIds, setMonitorIds] = useState<string[]>([]),
    [monitorRecords, setMonitorRecords] = useState<Record<string, AttemptStatus>>({}),
    [monitorError, setMonitorError] = useState(''),
    [cancellationNotice, setCancellationNotice] = useState(''),
    [monitorEpoch, setMonitorEpoch] = useState(0),
    [libraryError, setLibraryError] = useState(''),
    [status, setStatus] = useState(''),
    [error, setError] = useState(''),
    [draftStatus, setDraftStatus] = useState(''),
    [time, setTime] = useState(0),
    [playing, setPlaying] = useState(false),
    [speed, setSpeed] = useState(1),
    [mode, setMode] = useState<'follow' | 'pad' | 'free'>('follow'),
    [fitToken, setFitToken] = useState(0),
    [resetPreview, setResetPreview] = useState(0),
    [plotChannels, setPlotChannels] = useState(defaultChannels);
  const frameDeltas = useRef<number[]>([]);
  const playbackModeRef = useRef<PlaybackMode>('bounded');
  const activeLoads = useRef<{
    primary: AbortController | null;
    comparison: AbortController | null;
  }>({ primary: null, comparison: null });
  const activeLoadIds = useRef<{ primary: string | null; comparison: string | null }>({
    primary: null,
    comparison: null,
  });
  const scrubGeneration = useRef(0);
  const submission = useRef(false);
  const submissionIdentity = useRef<{ payload: string; key: string } | null>(null);
  const lastObservedMembers = useRef<Record<string, AttemptStatus>>({});
  const supportedChoice = choices.some(([id]) => id === configurationId);
  const request: ExperimentRequest = {
    configuration: configurationId,
    wind_mps: wind,
    wind_direction_deg: direction,
    gust_mps: gust,
    preset,
    seed,
  };
  const declaredCases = Array.from({ length: batchCount }, (_, i) => ({
    ...request,
    seed: seed + i,
  }));
  const declaration = batchDeclaration(declaredCases);
  useEffect(() => {
    const preference = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => {
      setReducedMotion(preference.matches);
      if (preference.matches) setPlaying(false);
    };
    update();
    preference.addEventListener('change', update);
    return () => preference.removeEventListener('change', update);
  }, []);
  const loadOrder = useRef({ primary: requestOrder(), comparison: requestOrder() });
  const libraryOrder = useRef(requestOrder());
  useEffect(() => {
    const order = loadOrder.current;
    return () => {
      order.primary.cancel();
      order.comparison.cancel();
      activeLoads.current.primary?.abort();
      activeLoads.current.comparison?.abort();
    };
  }, [configurationId]);
  const shown =
    current?.record.vehicle_id === configurationId &&
    current.playbackMode === playbackModeRef.current
      ? current
      : null;
  const primaryTimes = shown?.telemetry.columns.time_s;
  const comparisonTimes = other?.telemetry.columns.time_s;
  const primaryWindow = useMemo(() => replayWindow(primaryTimes), [primaryTimes]);
  const comparisonWindow = useMemo(() => replayWindow(comparisonTimes), [comparisonTimes]);
  const alignment = recordedAlignment(
    other ? alignmentEvent : 'absolute',
    shown?.record.events,
    other?.record.events,
  );
  const replayStart = shown
    ? firstRecordedTime(
        primaryWindow && {
          start: primaryWindow.start - alignment.a,
          end: primaryWindow.end - alignment.a,
        },
        other && comparisonWindow
          ? { start: comparisonWindow.start - alignment.b, end: comparisonWindow.end - alignment.b }
          : null,
      )
    : 0;
  const replayEnd = shown
    ? Math.max(
        primaryWindow ? primaryWindow.end - alignment.a : replayStart,
        other && comparisonWindow ? comparisonWindow.end - alignment.b : replayStart,
      )
    : 0;
  const rangeKey = `${shown?.record.run_id}-${other?.record.run_id}-${alignment.event}`;
  const fullRange = { start: replayStart, end: Math.max(replayStart + 0.001, replayEnd) };
  const plotWindow = chartRange?.key === rangeKey ? chartRange : fullRange;
  const refresh = useCallback(async () => {
    const isCurrent = libraryOrder.current.begin();
    try {
      const saved = await json<RecordRun[]>('/api/runs');
      if (
        !Array.isArray(saved) ||
        saved.some(
          (item) => !item || typeof item.run_id !== 'string' || typeof item.status !== 'string',
        )
      )
        throw new Error('Saved-run library response lacks inspectable run IDs/statuses.');
      if (isCurrent()) {
        setRuns(saved);
        setLibraryError('');
      }
    } catch (e) {
      if (isCurrent())
        setLibraryError(`Saved-run library refresh failed; prior list retained: ${String(e)}`);
    }
  }, []);
  useEffect(() => {
    void refresh();
    const interval = window.setInterval(() => void refresh(), 2500);
    const order = libraryOrder.current;
    return () => {
      window.clearInterval(interval);
      order.cancel();
    };
  }, [refresh]);
  const load = useCallback(
    async (id: string, compare = false, requestedMode: PlaybackMode = playbackModeRef.current) => {
      const lane = compare ? 'comparison' : 'primary';
      activeLoads.current[lane]?.abort();
      const controller = new AbortController();
      activeLoads.current[lane] = controller;
      activeLoadIds.current[lane] = id;
      setLoadStatus(`Loading saved run ${id} in ${requestedMode}; no simulation is started.`);
      setLoadingIds([
        ...new Set(
          Object.values(activeLoadIds.current).filter((value): value is string => value !== null),
        ),
      ]);
      const isCurrent = (
        compare ? loadOrder.current.comparison : loadOrder.current.primary
      ).begin();
      try {
        const loadStarted = performance.now();
        let responseBytes: number | null = null;
        const record = await json<RecordRun>(`/api/runs/${id}`, { signal: controller.signal });
        const [telemetry, vehicle] = await Promise.all([
          json<Telemetry>(
            telemetryUrl(id, requestedMode),
            { signal: controller.signal },
            (response) => {
              const header = response.headers.get('Content-Length');
              const bytes = header === null ? NaN : Number(header);
              responseBytes = Number.isFinite(bytes) && bytes >= 0 ? bytes : null;
            },
          ),
          json<InspectionDocument>(`/api/vehicles/${record.vehicle_id}`, {
            signal: controller.signal,
          }),
        ]);
        validatePlaybackProfile(telemetry, requestedMode);
        if (
          record.run_id !== id ||
          telemetry.run_id !== id ||
          telemetry.frame !== 'NED; body x forward; quaternion scalar first' ||
          !record.vehicle_id ||
          record.configuration !== record.vehicle_id ||
          vehicle.id !== record.vehicle_id ||
          !/^[a-f0-9]{64}$/.test(record.resolved_sha256 ?? '') ||
          !/^[a-f0-9]{64}$/.test(record.cad_revision_sha256 ?? '') ||
          vehicle.identity?.resolved_spec_sha256 !== record.resolved_sha256 ||
          vehicle.identity?.cad_revision_sha256 !== record.cad_revision_sha256
        )
          throw new Error(
            'Saved run configuration does not match current CAD identity. Replay is unavailable.',
          );
        if (typeof vehicle.summary.length_m !== 'number')
          throw new Error('Matching geometry length is unavailable.');
        if (!vehicle.parts.some((p) => p.mesh_url))
          throw new Error(
            'Matching CAD meshes unavailable; replay cannot be attached to different geometry.',
          );
        if (!isCurrent() || requestedMode !== playbackModeRef.current || controller.signal.aborted)
          return;
        if (Array.isArray(telemetry.columns.time_s)) Object.freeze(telemetry.columns.time_s);
        const item = { record, telemetry, vehicle, playbackMode: requestedMode };
        setLoadProfile({
          id,
          ms: performance.now() - loadStarted,
          bytes: responseBytes,
          samples: telemetry.columns.time_s?.length ?? 0,
        });
        setProfile(null);
        setHeap(browserHeap(performance));
        setScrubProfile(null);
        frameDeltas.current = [];
        if (compare) setOther(item);
        else {
          onConfigurationChange(record.vehicle_id!);
          setCurrent(item);
          setTime(firstRecordedTime(replayWindow(telemetry.columns.time_s)));
          setPlaying(false);
        }
        onRunSelect?.(id, compare);
        setLoadStatus(`Loaded ${id} with matching source and ${requestedMode} samples.`);
        setError('');
      } catch (e) {
        if (
          isCurrent() &&
          !controller.signal.aborted &&
          requestedMode === playbackModeRef.current
        ) {
          setError(String(e));
          setLoadStatus(`Saved-run load failed: ${String(e)}`);
        }
      } finally {
        if (activeLoads.current[lane] === controller) {
          activeLoads.current[lane] = null;
          activeLoadIds.current[lane] = null;
          setLoadingIds([
            ...new Set(
              Object.values(activeLoadIds.current).filter(
                (value): value is string => value !== null,
              ),
            ),
          ]);
        }
      }
    },
    [onConfigurationChange, onRunSelect],
  );
  useEffect(() => {
    if (!onRunSelect && initialRunId === undefined && initialComparisonId === undefined) return;
    const routeLoad = (id: string | undefined, compare: boolean) => {
      const lane = compare ? 'comparison' : 'primary';
      const selected = compare ? other : current;
      if (id && selected?.record.run_id === id) return;
      const active = activeLoads.current[lane];
      if (id && active && !active.signal.aborted && activeLoadIds.current[lane] === id) return;
      loadOrder.current[lane].cancel();
      active?.abort();
      if (compare) setOther(null);
      else {
        setCurrent(null);
        setPlaying(false);
      }
      if (id) void load(id, compare);
    };
    routeLoad(initialRunId, false);
    routeLoad(initialRunId ? initialComparisonId : undefined, true);
  }, [initialRunId, initialComparisonId, current, other, configurationId, load, onRunSelect]);
  useEffect(() => {
    if (!pending || !monitorIds.length) return;
    let timer: number;
    let alive = true;
    const controller = new AbortController();
    const observed: Record<string, AttemptStatus> = { ...lastObservedMembers.current };
    const poll = async () => {
      const result = await readAttemptStatuses(
        monitorIds,
        (id, signal) => json(`/api/experiments/${encodeURIComponent(id)}`, { signal }),
        controller.signal,
      );
      if (!alive || controller.signal.aborted) return;
      for (const record of result.records) observed[record.run_id] = record;
      lastObservedMembers.current = { ...observed };
      setMonitorRecords({ ...observed });
      const summary = attemptSummary(monitorIds, observed);
      setStatus(summary.text);
      if (result.errors.length) {
        setMonitorError(
          `Status observation paused. Accepted work may still be running; this is not worker failure or termination. ${result.errors.join(' · ')}`,
        );
        return;
      }
      setMonitorError('');
      if (summary.terminal) {
        setPending('');
        void refresh();
        // Preserve the original primary auto-load only for a successful primary.
        if (observed[pending]?.status === 'complete') void load(pending);
      } else {
        timer = window.setTimeout(poll, 1200);
      }
    };
    void poll();
    return () => {
      alive = false;
      controller.abort();
      clearTimeout(timer);
    };
  }, [pending, monitorIds, monitorEpoch, refresh, load]);
  useEffect(() => {
    if (!playing || !shown) return;
    let last = performance.now(),
      lastProfile = last,
      frame = 0;
    frameDeltas.current = [];
    const tick = (now: number) => {
      const elapsedMs = now - last;
      const advance = playbackStep(elapsedMs, speed, replayEnd);
      frameDeltas.current.push(elapsedMs);
      if (frameDeltas.current.length > 600) frameDeltas.current.shift();
      if (now - lastProfile >= 1000) {
        setProfile(frameProfile(frameDeltas.current));
        setHeap(browserHeap(performance));
        lastProfile = now;
      }
      setTime((t) => {
        const next = advance(t);
        if (next >= replayEnd) {
          setPlaying(false);
          return replayEnd;
        }
        return next;
      });
      last = now;
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [playing, shown, speed, replayEnd]);
  function scrubTo(next: number) {
    setPlaying(false);
    const started = performance.now();
    const generation = ++scrubGeneration.current;
    setTime(next);
    requestAnimationFrame(() =>
      requestAnimationFrame(() => {
        if (generation !== scrubGeneration.current) return;
        const elapsed = performance.now() - started;
        setScrubProfile((previous) => ({
          count: (previous?.count ?? 0) + 1,
          last_ms: elapsed,
          max_ms: Math.max(previous?.max_ms ?? 0, elapsed),
        }));
        setHeap(browserHeap(performance));
      }),
    );
  }
  function changePlaybackProfile(enabled: boolean) {
    const primaryId = shown?.record.run_id;
    const comparisonId = other?.record.run_id;
    loadOrder.current.primary.cancel();
    loadOrder.current.comparison.cancel();
    activeLoads.current.primary?.abort();
    activeLoads.current.comparison?.abort();
    activeLoads.current = { primary: null, comparison: null };
    activeLoadIds.current = { primary: null, comparison: null };
    setLoadingIds([]);
    setPlaying(false);
    setCurrent(null);
    setOther(null);
    setProfile(null);
    setLoadProfile(null);
    setScrubProfile(null);
    setHeap(null);
    frameDeltas.current = [];
    scrubGeneration.current++;
    playbackModeRef.current = enabled ? 'full-rate-benchmark' : 'bounded';
    setFullRateBenchmark(enabled);
    setError('');
    if (primaryId) void load(primaryId, false, playbackModeRef.current);
    if (primaryId && comparisonId) void load(comparisonId, true, playbackModeRef.current);
  }
  function cancelSavedLoad() {
    loadOrder.current.primary.cancel();
    loadOrder.current.comparison.cancel();
    activeLoads.current.primary?.abort();
    activeLoads.current.comparison?.abort();
    activeLoads.current = { primary: null, comparison: null };
    activeLoadIds.current = { primary: null, comparison: null };
    setLoadingIds([]);
    setLoadStatus('Saved-run load cancelled; no simulation was started.');
  }
  function downloadRun(run: Loaded, peer: Loaded | null, kind: 'csv' | 'json') {
    try {
      const isA = run.record.run_id === shown?.record.run_id;
      const selection = {
        start_s: plotWindow.start,
        end_s: plotWindow.end,
        offset_s: isA ? alignment.a : alignment.b,
        peer_offset_s: isA ? alignment.b : alignment.a,
        alignment_event: alignment.event,
      };
      const content =
        kind === 'csv' ? telemetryCsv(run, selection) : exportMetadata(run, peer, selection);
      const url = URL.createObjectURL(
        new Blob([content], {
          type: kind === 'csv' ? 'text/csv;charset=utf-8' : 'application/json',
        }),
      );
      const link = document.createElement('a');
      link.href = url;
      link.download = `${run.record.run_id.replace(/[^a-zA-Z0-9_-]/g, '_')}-playback.${kind}`;
      link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      setError('');
    } catch (e) {
      setError(`Export unavailable: ${String(e)}`);
    }
  }
  function reuseRequest(record: RecordRun) {
    try {
      const draft = requestDraft(record, configurationId);
      setWind(draft.wind_mps);
      setDirection(draft.wind_direction_deg);
      setGust(draft.gust_mps);
      setSeed(draft.seed);
      setPreset(draft.preset);
      setDraftStatus(
        `Draft copied from ${record.run_id}; review before starting a new attempt. Saved record unchanged. Historical source revisions are not copied.`,
      );
    } catch (e) {
      setDraftStatus(String(e));
    }
  }
  function reuseDraft(run: Loaded) {
    reuseRequest(run.record);
  }
  function observeSavedAttempt(record: RecordRun) {
    try {
      const ids = savedAttemptIds(record);
      lastObservedMembers.current = {};
      setMonitorIds(ids);
      setMonitorRecords({});
      setMonitorError('');
      setCancellationNotice('');
      setPending(ids[0]);
    } catch (reason) {
      setError(String(reason));
    }
  }
  function downloadAttempt(record: RecordRun) {
    try {
      const url = URL.createObjectURL(
        new Blob([savedAttemptExport(record, runs)], { type: 'application/json' }),
      );
      const link = document.createElement('a');
      link.href = url;
      link.download = `${record.run_id.replace(/[^a-zA-Z0-9_-]/g, '_')}-attempt.json`;
      link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (reason) {
      setError(`Attempt metadata export unavailable: ${String(reason)}`);
    }
  }
  async function cancelRun(id: string) {
    try {
      const result = await json<{ acknowledgement: string }>(`/api/experiments/${id}/cancel`, {
        method: 'POST',
      });
      if (typeof result.acknowledgement !== 'string')
        throw new Error(
          'Cancellation acknowledgement unavailable; terminal status is not confirmed.',
        );
      setCancellationNotice(
        `${result.acknowledgement}. Cancellation request is not confirmed termination.`,
      );
      setMonitorEpoch((value) => value + 1);
      await refresh();
    } catch (e) {
      setError(String(e));
    }
  }
  async function start() {
    if (submission.current) return;
    submission.current = true;
    setSubmitting(true);
    let submissionSent = false;
    try {
      setError('');
      if (!supportedChoice || configurationId === 'modular-tvc-finless-v1')
        throw new Error(
          'Select a supported complete flight configuration; inspection candidates and finless unguided flight cannot run.',
        );
      const payload = JSON.stringify(
        batchEnabled ? { cases: declaredCases, concurrency: 1, resource: 'local-cpu' } : request,
      );
      // Retain the same key after an uncertain network response, including a tab reload.
      if (!submissionIdentity.current) {
        try {
          submissionIdentity.current = JSON.parse(
            sessionStorage.getItem('rocket-twin-experiment-submission') ?? 'null',
          );
        } catch {
          /* Storage may be unavailable. */
        }
      }
      if (submissionIdentity.current?.payload !== payload)
        submissionIdentity.current = { payload, key: crypto.randomUUID() };
      const identity = submissionIdentity.current!;
      try {
        sessionStorage.setItem('rocket-twin-experiment-submission', JSON.stringify(identity));
      } catch {
        /* In-memory duplicate protection remains active. */
      }
      submissionSent = true;
      const r = await json<unknown>(batchEnabled ? '/api/experiment-batches' : '/api/experiments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Idempotency-Key': identity.key },
        body: payload,
      });
      const ids = acceptedAttemptIds(r, batchEnabled ? declaredCases.length : 1);
      lastObservedMembers.current = {};
      submissionIdentity.current = null;
      try {
        sessionStorage.removeItem('rocket-twin-experiment-submission');
      } catch {
        /* No durable state to clear. */
      }
      setMonitorIds(ids);
      setMonitorRecords({});
      setMonitorError('');
      setCancellationNotice('');
      setPending(ids[0]);
      setStatus(`Accepted ${ids.length} case(s); observing saved statuses.`);
      await refresh();
    } catch (e) {
      setError(
        submissionSent
          ? `Submission acceptance not confirmed: ${String(e)}. No accepted member IDs were established by this response. Check saved attempts before retrying; the unchanged request retains its idempotency key.`
          : `Experiment setup unavailable: ${String(e)}`,
      );
    } finally {
      submission.current = false;
      setSubmitting(false);
    }
  }
  return (
    <div className={`experiment${workspace ? ` experiment--${workspace}` : ''}`}>
      <aside>
        <h2>{workspace === 'replay' ? 'Flight replay' : 'Run an experiment'}</h2>
        <details className="exp-setup" open={workspace !== 'replay'}>
          <summary>Experiment setup</summary>
          <p>
            Simulated, preliminary, unguided flights using complete configurations. Finless unguided
            flight is unsupported. Proportional–integral–derivative (PID) and reinforcement learning
            (RL) controllers are later work.
          </p>
          <label>
            Vehicle and motor
            <select
              value={configurationId}
              onChange={(e) => {
                loadOrder.current.primary.cancel();
                loadOrder.current.comparison.cancel();
                setPlaying(false);
                onConfigurationChange(e.target.value);
              }}
            >
              {!supportedChoice && (
                <option value={configurationId} disabled>
                  Unsupported inspection design — choose a flight configuration
                </option>
              )}
              {choices.map(([id, label]) => (
                <option value={id} key={id}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Steady wind (m/s)
            <input
              type="number"
              min="0"
              max="10"
              step="0.1"
              value={wind}
              onChange={(e) => setWind(Number(e.target.value))}
            />
          </label>
          <label>
            Wind direction toward (° clockwise from north)
            <input
              type="number"
              min="0"
              max="359"
              value={direction}
              onChange={(e) => setDirection(Number(e.target.value))}
            />
          </label>
          <label>
            Gust amplitude (m/s)
            <input
              type="number"
              min="0"
              max="5"
              step="0.1"
              value={gust}
              onChange={(e) => setGust(Number(e.target.value))}
            />
          </label>
          <label>
            Preset
            <select value={preset} onChange={(e) => setPreset(e.target.value as 'tiny' | 'sim')}>
              <option value="tiny">tiny · 45 s / 9,000 steps</option>
              <option value="sim">sim · 360 s / 360,000 steps</option>
            </select>
          </label>
          <label>
            Random seed (integer 0–4,294,967,295)
            <input
              type="number"
              min="0"
              max="4294967295"
              step="1"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
            />
          </label>
          <label>
            <input
              type="checkbox"
              checked={batchEnabled}
              onChange={(e) => setBatchEnabled(e.target.checked)}
            />{' '}
            Bounded seed sweep
          </label>
          {batchEnabled && (
            <>
              <label>
                Declared cases{' '}
                <select value={batchCount} onChange={(e) => setBatchCount(Number(e.target.value))}>
                  {[2, 3, 4].map((n) => (
                    <option key={n}>{n}</option>
                  ))}
                </select>
              </label>
              <p>
                {declaration.count} explicit cases · local CPU · concurrency 1 · at most{' '}
                {declaration.max_steps.toLocaleString()} model steps total. Each case uses the shown
                configuration, wind, gust and preset; seeds increment by one. No remote compute.
              </p>
              <ol>
                {declaredCases.map((c, i) => (
                  <li key={i}>
                    Case {i + 1}: seed {c.seed} · wind {c.wind_mps} m/s toward{' '}
                    {c.wind_direction_deg}° · gust {c.gust_mps} m/s · {c.preset}
                  </li>
                ))}
              </ol>
            </>
          )}
          <p>
            Cancellation is cooperative before/after rollout. A compiled JAX rollout can finish
            before cancellation is acknowledged; queued members remain saved. Local records,
            resolved snapshots and Parquet are retained without automatic deletion; each member has
            at most its declared model-step count in rows. Compressed disk bytes and JAX compilation
            memory vary by host.
          </p>
          <button
            disabled={
              submitting ||
              !!pending ||
              !supportedChoice ||
              configurationId === 'modular-tvc-finless-v1'
            }
            onClick={() => void start()}
          >
            {submitting ? 'Submitting…' : batchEnabled ? 'Run declared batch on CPU' : 'Run on CPU'}
          </button>
          {!supportedChoice && (
            <p role="status">
              This inspection candidate has no supported complete flight configuration. Choose one
              of the recorded G80/G54/G12 reference configurations above; no candidate is silently
              substituted.
            </p>
          )}
          {configurationId === 'modular-tvc-finless-v1' && (
            <p>
              Finless unguided simulation is unsupported. The actual design is shown for inspection.
            </p>
          )}
        </details>
        {pending && (
          <>
            <p role="status">
              {status} · {pending}
            </p>
            <button onClick={() => void cancelRun(pending)}>Request cancellation</button>
            {monitorError && (
              <>
                <p role="alert">{monitorError}</p>
                <button
                  type="button"
                  onClick={() => {
                    setMonitorError('');
                    setMonitorEpoch((value) => value + 1);
                  }}
                >
                  Resume status observation
                </button>
              </>
            )}
          </>
        )}
        {cancellationNotice && <p role="status">{cancellationNotice}</p>}
        {error && (
          <p role="alert" className="exp-error">
            {error}
          </p>
        )}
        <h3>Saved runs</h3>
        {libraryError && <p role="alert">{libraryError}</p>}
        {monitorIds.length > 0 && (
          <section className="exp-info" aria-label="Accepted attempt members">
            <h4>Accepted attempt members · last observed statuses</h4>
            <ul>
              {monitorIds.map((id) => (
                <li key={id}>
                  {id}: {monitorRecords[id]?.status ?? 'status unavailable'}
                  {monitorRecords[id]?.error ? ` · ${monitorRecords[id].error}` : ''}
                  {!monitorRecords[id]?.error && monitorRecords[id]?.progress
                    ? ` · ${monitorRecords[id].progress}`
                    : ''}
                </li>
              ))}
            </ul>
            <p>
              Each member is retained independently. Resume observes existing work; reuse as draft
              requires a separate explicit submission.
            </p>
          </section>
        )}
        <label>
          <input
            type="checkbox"
            checked={fullRateBenchmark}
            onChange={(e) => changePlaybackProfile(e.target.checked)}
          />{' '}
          Opt in: full-rate benchmark load
        </label>
        <p>
          {fullRateBenchmark
            ? 'FULL-RATE BENCHMARK: every native sample is loaded, up to 150,000 rows and 64 raw / 73 returned numeric channels per run. At the cap, numeric float64 storage alone is 87.6 MB and the conservative numeric JSON envelope is 350.4 MB per run; parsing, CAD, arrays and metadata add memory. Two runs double these bounds. No new simulation is started.'
            : 'Normal bounded playback: approximately 3,000 samples plus recorded event neighbours per run. Arrow download remains bounded.'}
        </p>
        <p>
          Qualification requires an actual ≥120 s, 1 kHz recorded recovery trajectory, identified
          host/viewport and observed frame/scrub/load/memory measurements. Enabling this option does
          not establish 60 fps or acceptance. Switching profiles clears actors and reloads the same
          source-checked saved run.
        </p>
        {loadStatus && <p role="status">{loadStatus}</p>}
        {loadingIds.length > 0 && (
          <>
            <p role="status">
              Loading {playbackModeRef.current}: {loadingIds.join(', ')}
            </p>
            <button onClick={cancelSavedLoad}>Cancel saved-run load</button>
          </>
        )}
        {workspace === 'experiments' && onOpenReplay && (
          <button type="button" onClick={onOpenReplay}>
            Open flight replay
          </button>
        )}
        <label>
          Filter runs by ID, configuration or batch
          <input
            type="search"
            value={libraryQuery}
            onChange={(e) => setLibraryQuery(e.target.value)}
          />
        </label>
        <label>
          Run status
          <select value={libraryStatus} onChange={(e) => setLibraryStatus(e.target.value)}>
            {['all', 'queued', 'running', 'cancel_requested', ...terminalStatuses].map((value) => (
              <option key={value} value={value}>
                {value.replaceAll('_', ' ')}
              </option>
            ))}
          </select>
        </label>
        <p>
          {filterRuns(runs, libraryQuery, libraryStatus).length} of {runs.length} saved attempts
          shown. Batch members retain independent status; no failure is excluded from batch
          statistics.
        </p>
        {runs.length === 0 && <p>No saved runs are available.</p>}
        {filterRuns(runs, libraryQuery, libraryStatus).map((r) => (
          <div key={r.run_id} className="exp-run">
            <button
              onClick={() => {
                setLibrarySelection(r);
                if (r.status === 'complete') void load(r.run_id);
              }}
            >
              {r.configuration}
              <br />
              <small>
                {r.run_id} · {r.status} · seed {r.random_seed ?? r.settings?.seed ?? 'unavailable'}
                <br />
                {r.created_at ?? 'date unavailable'} · {r.controller ?? 'controller unavailable'}
                <br />
                Peak height {headline(r.metrics?.apogee_agl_m, 'm')} ·{' '}
                {r.trajectory_complete === false
                  ? 'partial trajectory'
                  : r.trajectory_complete === true
                    ? 'landing recorded'
                    : 'trajectory completeness unavailable'}
                {r.batch_id && (
                  <>
                    <br />
                    {r.batch_id}
                  </>
                )}
              </small>
            </button>
            <button disabled={r.status !== 'complete'} onClick={() => void load(r.run_id, true)}>
              Compare
            </button>
          </div>
        ))}
        {librarySelection && (
          <section className="exp-info" aria-label="Saved attempt details">
            <h3>{librarySelection.run_id}</h3>
            <p>
              Status:{' '}
              {runs.find((r) => r.run_id === librarySelection.run_id)?.status ??
                librarySelection.status}
            </p>
            <p>
              {runs.find((r) => r.run_id === librarySelection.run_id)?.error ??
                librarySelection.error ??
                librarySelection.progress}
            </p>
            {librarySelection.batch_id && (
              <p>
                Batch {librarySelection.batch_id}:{' '}
                {librarySelection.batch_members
                  ?.map(
                    (id) =>
                      `${id}: ${runs.find((r) => r.run_id === id)?.status ?? 'member unavailable'}`,
                  )
                  .join(' · ')}
              </p>
            )}
            <button onClick={() => reuseRequest(librarySelection)}>Reuse request as draft</button>
            <button
              type="button"
              disabled={!!pending}
              onClick={() => observeSavedAttempt(librarySelection)}
            >
              Observe saved attempt / batch status
            </button>
            <button
              type="button"
              onClick={() =>
                downloadAttempt(
                  runs.find((item) => item.run_id === librarySelection.run_id) ?? librarySelection,
                )
              }
            >
              Export saved attempt metadata
            </button>
            {!terminalStatuses.includes(
              runs.find((r) => r.run_id === librarySelection.run_id)?.status ??
                librarySelection.status,
            ) && (
              <button onClick={() => void cancelRun(librarySelection.run_id)}>
                Request cancellation of run / batch
              </button>
            )}
            <details>
              <summary>Saved request, resources and provenance</summary>
              <pre>
                {JSON.stringify(
                  runs.find((r) => r.run_id === librarySelection.run_id) ?? librarySelection,
                  null,
                  2,
                )}
              </pre>
            </details>
          </section>
        )}
        {draftStatus && <p role="status">{draftStatus}</p>}
      </aside>
      <main>
        {shown ? (
          <>
            <div className="exp-replay">
              <FlightScene
                run={shown}
                other={other}
                time={time}
                mode={mode}
                fitToken={fitToken}
                offsets={alignment}
              />
            </div>
            <div className="exp-controls">
              <select
                aria-label="Replay camera"
                value={mode}
                onChange={(e) => setMode(e.target.value as 'follow' | 'pad' | 'free')}
              >
                <option value="follow">Camera: follow</option>
                <option value="pad">Camera: fixed pad</option>
                <option value="free">Camera: free</option>
              </select>
              <button
                onClick={() => {
                  setMode('free');
                  setFitToken((n) => n + 1);
                }}
              >
                Fit trajectory
              </button>
              <button
                onClick={() => {
                  if (!playing && time >= replayEnd) setTime(replayStart);
                  setPlaying(!playing);
                }}
              >
                {playing ? 'Pause' : 'Play'}
              </button>
              <select
                aria-label="Replay speed"
                value={speed}
                onChange={(e) => setSpeed(Number(e.target.value))}
              >
                {[0.25, 0.5, 1, 2, 4].map((n) => (
                  <option key={n} value={n}>
                    {n}×
                  </option>
                ))}
              </select>
              <input
                type="range"
                aria-label="Replay time"
                min={replayStart}
                max={replayEnd}
                step="0.01"
                value={time}
                onChange={(e) => scrubTo(Number(e.target.value))}
              />
              <span>
                {alignment.event ? 'Aligned' : 'T+'}
                {time.toFixed(2)} s
              </span>
              <ExactReplayTime
                key={`${rangeKey}-${fullRateBenchmark}`}
                time={time}
                start={replayStart}
                end={replayEnd}
                aligned={!!alignment.event}
                onApply={scrubTo}
              />
            </div>
            <p>
              Orbit and zoom with mouse. Teal: {shown.record.run_id}
              {other && ` · Gold: ${other.record.run_id}`}
              {other && ' · Each actor is visible only within its recorded window.'}
            </p>
            <p>
              Spatial scale: 1 scene unit = 1 m; ground grid is 100 m wide with 5 m squares. White
              dot: recorded centre of mass. Paths and body poses use recorded telemetry; the wind
              arrow represents request settings and is illustrative, not a measured local vector. No
              canopy or line-load geometry is inferred.
            </p>
            <p>
              {reducedMotion
                ? 'Reduced-motion preference detected; playback starts paused and remains user controlled.'
                : 'Playback is paused until Play is selected.'}{' '}
              Gimbal angles remain recorded channels; locked-gimbal runs add no animated control
              action.
            </p>
            <p>
              Playback profile: {shown.playbackMode} · A returned{' '}
              {shown.telemetry.returned_sample_count ?? shown.telemetry.columns.time_s.length} /{' '}
              {shown.telemetry.full_sample_count ?? 'unavailable'} raw samples
              {other &&
                ` · B returned ${other.telemetry.returned_sample_count ?? other.telemetry.columns.time_s.length} / ${other.telemetry.full_sample_count ?? 'unavailable'} raw samples`}
              . {shown.telemetry.sampling?.policy}
            </p>
            <ReplayValidity run={shown} time={time + alignment.a} label="A · teal" />
            {other && <ReplayValidity run={other} time={time + alignment.b} label="B · gold" />}
            <div className="exp-events">
              {Object.entries(shown.record.events ?? {}).map(([k, v]) => (
                <button
                  key={k}
                  disabled={v === null}
                  onClick={() => {
                    setPlaying(false);
                    scrubTo(v! - alignment.a);
                  }}
                >
                  {k.replace('_', ' ')}: {v === null ? 'not recorded' : `T+${v.toFixed(2)} s`}
                </button>
              ))}
            </div>
            <p>
              Choose recorded or backend-derived channels. Unrecognized names are shown exactly as
              recorded; their units and meaning are not inferred. Plots use returned playback
              samples in the selected profile. Readouts use the nearest returned sample within each
              run’s recorded time range, without interpolation; they do not establish full-rate
              extremes.
            </p>
            <div className="exp-controls" aria-label="Comparison clock and plot range">
              <label>
                Clock alignment
                <select
                  value={alignmentEvent}
                  onChange={(e) => {
                    setPlaying(false);
                    setAlignmentEvent(e.target.value);
                    setTime(0);
                  }}
                  disabled={!other}
                >
                  <option value="absolute">Absolute elapsed time</option>
                  {['guide_exit', 'burnout', 'apogee', 'deployment', 'landing'].map((event) => (
                    <option key={event} value={event}>
                      {event.replace('_', ' ')} recorded event
                    </option>
                  ))}
                </select>
              </label>
              <span>
                Display time = recorded time − offset. A offset {alignment.a.toFixed(3)} s; B offset{' '}
                {alignment.b.toFixed(3)} s. {alignment.reason}
              </span>
              <span>
                Plot/export range: {plotWindow.start.toFixed(3)}–{plotWindow.end.toFixed(3)} s
              </span>
              {(['in', 'out', 'left', 'right'] as const).map((action) => (
                <button
                  key={action}
                  onClick={() =>
                    setChartRange({
                      ...adjustPlotWindow(plotWindow, fullRange, action),
                      key: rangeKey,
                    })
                  }
                >
                  {action === 'in' ? 'Zoom in' : action === 'out' ? 'Zoom out' : `Pan ${action}`}
                </button>
              ))}
              <button onClick={() => setChartRange(null)}>Reset plot range</button>
            </div>
            <details className="exp-info">
              <summary>
                Playback instrumentation (browser observation required for acceptance)
              </summary>
              <p>
                Scenario: one or two identified recorded runs,{' '}
                {fullRateBenchmark
                  ? 'full native-rate benchmark samples'
                  : 'bounded playback samples'}
                , four linked plots and matching CAD. Frame intervals include UI scheduling; they
                are not GPU render-only timings. The rolling window retains at most 600 frames.
              </p>
              {loadProfile && (
                <p>
                  Last load {loadProfile.id}: {loadProfile.ms.toFixed(1)} ms including API/identity
                  checks · {loadProfile.samples} returned samples ·{' '}
                  {loadProfile.bytes === null
                    ? 'Content-Length unavailable'
                    : `${loadProfile.bytes.toLocaleString()} response Content-Length bytes`}{' '}
                  (not total network transfer or heap usage).
                </p>
              )}
              <p>
                {profile
                  ? `${profile.samples} recent frame intervals · median ${profile.p50_ms.toFixed(2)} ms · p95 ${profile.p95_ms.toFixed(2)} ms · max ${profile.max_ms.toFixed(2)} ms · mean ${profile.mean_ms.toFixed(2)} ms`
                  : 'No measured playback frame interval profile yet. Start playback to collect browser data.'}
              </p>
              <p>
                {scrubProfile
                  ? `${scrubProfile.count} completed scrub presentations · last ${scrubProfile.last_ms.toFixed(2)} ms · max ${scrubProfile.max_ms.toFixed(2)} ms to the second animation-frame callback (includes scheduling; not GPU-only completion)`
                  : 'No measured scrub presentation yet.'}
              </p>
              <p>
                {heap
                  ? `Host-reported JavaScript heap: used ${heap.used.toLocaleString()} bytes / allocated ${heap.total.toLocaleString()} / limit ${heap.limit.toLocaleString()}. Nonstandard host estimate, not total process or GPU memory.`
                  : 'Memory unmeasured: this host does not expose performance.memory, or no playback/scrub/load measurement has occurred. No zero is substituted.'}
              </p>
              <p>
                The ≥120 s / 1 kHz / 60 fps benchmark still requires the designated runtime,
                identified host, viewport, raw dataset and memory measurements. These counters alone
                do not pass it.
              </p>
            </details>
            <div className="exp-plots">
              {plotChannels.map((name, index) => (
                <Plot
                  key={index}
                  run={shown}
                  other={other}
                  name={name}
                  time={time}
                  window={plotWindow}
                  offsets={alignment}
                  setTime={scrubTo}
                  setName={(next) =>
                    setPlotChannels((previous) =>
                      previous.map((value, i) => (i === index ? next : value)),
                    )
                  }
                />
              ))}
            </div>
          </>
        ) : (
          <>
            <div className="exp-replay">
              {vehicle && vehicle.id === configurationId ? (
                <StaticPreview vehicle={vehicle} reset={resetPreview} />
              ) : (
                <div className="exp-empty">Loading the selected actual configuration…</div>
              )}
            </div>
            <div className="exp-controls">
              <button onClick={() => setResetPreview((n) => n + 1)}>Reset view</button>
            </div>
            <p>
              Selected design preview. Run a supported configuration or load a saved run to see its
              prediction.
            </p>
          </>
        )}
      </main>
      <aside className="exp-results">
        <h2>Selected design</h2>
        <p>{choices.find(([id]) => id === configurationId)?.[1] ?? configurationId}</p>
        <p>
          The selected design uses its resolved configuration and available CAD; engineering
          acceptance remains open.
        </p>
        {shown ? (
          <>
            {' '}
            <div className="exp-info">
              <h3>Simulated preliminary results · unguided</h3>
              <RunDetails run={shown} label="A · teal" />
              <div>
                <p>
                  Export the selected plot range of returned playback samples in the selected
                  profile, including backend-derived channels. CSV preserves recorded timestamps;
                  metadata stores alignment offsets and inclusive range. Each run keeps its own
                  timestamps and coverage; missing values are blank.{' '}
                  {fullRateBenchmark
                    ? 'Native-rate output preserves the returned native samples in this selected range; this is not scientific or flight validation.'
                    : 'These files are not full-resolution telemetry.'}
                </p>
                <button onClick={() => downloadRun(shown, other, 'csv')}>
                  Download A range CSV
                </button>
                <a
                  href={`/api/runs/${encodeURIComponent(shown.record.run_id)}/telemetry.arrow`}
                  download
                >
                  Download A bounded Arrow stream (normal ~3k profile)
                </a>
                <button onClick={() => downloadRun(shown, other, 'json')}>
                  Download A metadata JSON
                </button>
                <button onClick={() => reuseDraft(shown)}>
                  Reuse A recorded settings as draft
                </button>
                {other && (
                  <>
                    <button onClick={() => downloadRun(other, shown, 'csv')}>
                      Download B range CSV
                    </button>
                    <a
                      href={`/api/runs/${encodeURIComponent(other.record.run_id)}/telemetry.arrow`}
                      download
                    >
                      Download B bounded Arrow stream (normal ~3k profile)
                    </a>
                    <button onClick={() => downloadRun(other, shown, 'json')}>
                      Download B metadata JSON
                    </button>
                    <button onClick={() => reuseDraft(other)}>
                      Reuse B recorded settings as draft
                    </button>
                  </>
                )}
                {draftStatus && <p role="status">{draftStatus}</p>}
              </div>
              {other && (
                <>
                  <RunDetails run={other} label="B · gold" />
                  <button
                    onClick={() => {
                      loadOrder.current.comparison.cancel();
                      setOther(null);
                      onRunSelect?.(null, true);
                      setAlignmentEvent('absolute');
                      setPlaying(false);
                      setTime(firstRecordedTime(primaryWindow));
                    }}
                  >
                    Clear comparison
                  </button>
                  <p>
                    The comparison clock and offsets are shown above the plots. Alignment uses
                    recorded event times only. Differences or missing assumptions prevent
                    attributing a result to one change. Compare complete configurations, not motors
                    alone: mounting, mass, geometry and recovery may also differ. Match wind, gust
                    and other case settings to investigate a motor change; model and input
                    identities still matter.
                  </p>
                  <ComparisonDifferences a={shown.record} b={other.record} />
                  {other.record.validity?.map((l) => (
                    <p key={l}>B: {l}</p>
                  ))}
                  {other.record.limitations.map((l) => (
                    <p key={l}>B: {l}</p>
                  ))}
                </>
              )}
              <p>
                Guide exit speed is the speed when the rocket leaves its launch guide. Landing
                displacement is the straight-line distance from launch to landing, not the length of
                the flight path.
              </p>
              <p>
                Net acceleration includes gravity and is the magnitude of the change in velocity,
                not necessarily the rate of change of speed. Specific force is the modeled
                accelerometer-like force per unit mass and excludes gravity. The idealized landing
                clamp does not model the impact or contact force.
              </p>
              {shown.record.validity?.map((l) => (
                <p key={l}>{l}</p>
              ))}
              {shown.record.limitations.map((l) => (
                <p key={l}>{l}</p>
              ))}
            </div>
          </>
        ) : (
          <p>No run prediction selected for this design.</p>
        )}
      </aside>
    </div>
  );
}
