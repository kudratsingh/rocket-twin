import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { requestOrder } from './requestOrder';
import { replayValidity } from './replayValidity';
import { firstRecordedTime, replayWindow, replayWindowStatus } from './replayWindow';
import { comparisonDifferences, comparisonValue } from './comparison';
import { plotScale, scaleLabels } from './plotScale';
import { exportMetadata, recordedSettingsDraft, telemetryCsv } from './runExport';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Line, OrbitControls, useGLTF } from '@react-three/drei';
import { Matrix4, Quaternion, Vector3 } from 'three';
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
  series,
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
  settings: { wind_mps: number; wind_direction_deg: number; gust_mps: number };
  metrics?: Record<string, number | boolean | null>;
  events?: Record<string, number | null>;
  trajectory_complete?: boolean;
  validity?: string[];
  limitations: string[];
};
type Telemetry = {
  columns: Record<string, number[]>;
  channel_metadata?: Record<string, ChannelMeta>;
};
type Loaded = { record: RecordRun; telemetry: Telemetry; vehicle: InspectionDocument };
const choices = [
  ['modular-performance-v1', 'Performance · G80 reference'],
  ['modular-performance-g54-hypothesis', 'Performance · G54 conditional'],
  ['modular-tvc-finned-v1', 'Finned trainer · G12, locked gimbal'],
  ['modular-tvc-finless-v1', 'Finless trainer · static inspection only'],
];
async function json<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok)
    throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
  return data as T;
}
function nearest(t: number, times: number[]) {
  let lo = 0,
    hi = times.length - 1;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (times[mid] < t) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}
function value(c: Record<string, number[]>, name: string, t: number) {
  const i = nearest(t, c.time_s);
  if (i === 0) return c[name][0];
  const a = i - 1,
    f = Math.max(0, Math.min(1, (t - c.time_s[a]) / (c.time_s[i] - c.time_s[a])));
  return c[name][a] * (1 - f) + c[name][i] * f;
}
function MeshPart({ part }: { part: Part }) {
  const model = useGLTF(part.mesh_url!);
  const scene = useMemo(() => model.scene.clone(true), [model]);
  return <primitive object={scene} />;
}
function attitude(c: Record<string, number[]>, t: number) {
  const i = nearest(t, c.time_s);
  const q = (j: number) => new Quaternion(c.qx[j], c.qy[j], c.qz[j], c.qw[j]).normalize();
  if (i === 0) return q(0);
  const a = i - 1,
    f = Math.max(0, Math.min(1, (t - c.time_s[a]) / (c.time_s[i] - c.time_s[a])));
  return q(a).slerp(q(i), f);
}
function FlightGeometry({ run, time }: { run: Loaded; time: number }) {
  const c = run.telemetry.columns,
    q = attitude(c, time);
  // GLB [body y, forward, -body z]; display [east, up, -north].
  const bodyFromCad = new Matrix4().set(0, 1, 0, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1);
  const sceneFromNed = new Matrix4().set(0, 1, 0, 0, 0, 0, -1, 0, -1, 0, 0, 0, 0, 0, 0, 1);
  const rot = new Quaternion().setFromRotationMatrix(
    sceneFromNed.multiply(new Matrix4().makeRotationFromQuaternion(q)).multiply(bodyFromCad),
  );
  const length = Number(run.vehicle.summary.length_m);
  const cg = value(c, 'cg_station_m', time);
  return (
    <group
      position={[value(c, 'east_m', time), -value(c, 'down_m', time), -value(c, 'north_m', time)]}
      quaternion={rot}
    >
      <group position={[0, -(length - cg), 0]}>
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
  mode: 'follow' | 'free';
  fitToken: number;
  run: Loaded;
}) {
  const controls = useRef<OrbitControlsType>(null);
  const previous = useRef<Vector3 | null>(null);
  const { camera } = useThree();
  useEffect(() => {
    previous.current = null;
  }, [camera, run]);
  useEffect(() => {
    if (!fitToken || !replayWindow(run.telemetry.columns.time_s)) return;
    const c = run.telemetry.columns;
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
}: {
  run: Loaded;
  other: Loaded | null;
  time: number;
  mode: 'follow' | 'free';
  fitToken: number;
}) {
  const path = (r: Loaded) =>
    r.telemetry.columns.time_s.map(
      (_, i) =>
        [
          r.telemetry.columns.east_m[i],
          -r.telemetry.columns.down_m[i],
          -r.telemetry.columns.north_m[i],
        ] as [number, number, number],
    );
  const c = run.telemetry.columns;
  const primaryWindow = useMemo(() => replayWindow(c.time_s), [c.time_s]);
  const otherTimes = other?.telemetry.columns.time_s;
  const comparisonWindow = useMemo(() => replayWindow(otherTimes), [otherTimes]);
  const primaryInside = replayWindowStatus(primaryWindow, time) === 'inside';
  const comparisonInside = replayWindowStatus(comparisonWindow, time) === 'inside';
  const loc = primaryInside
    ? new Vector3(value(c, 'east_m', time), -value(c, 'down_m', time), -value(c, 'north_m', time))
    : null;
  const theta = (run.record.settings.wind_direction_deg * Math.PI) / 180;
  const wind = run.record.settings.wind_mps;
  return (
    <Canvas camera={{ position: [2, 1.5, 3], fov: 45, near: 0.01, far: 5000 }}>
      <ambientLight intensity={1.4} />
      <directionalLight position={[20, 50, 30]} intensity={2} />
      <ReplayCamera loc={loc} mode={mode} fitToken={fitToken} run={run} />
      <gridHelper args={[100, 20, '#38505b', '#24343c']} />
      {primaryWindow && <Line points={path(run)} color="#54d8d2" lineWidth={2} />}
      {other && comparisonWindow && <Line points={path(other)} color="#f5b960" lineWidth={2} />}
      {primaryInside && <FlightGeometry run={run} time={time} />}
      {other && comparisonInside && <FlightGeometry run={other} time={time} />}
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
}: {
  run: Loaded;
  other: Loaded | null;
  name: string;
  time: number;
  setTime: (v: number) => void;
  setName: (v: string) => void;
}) {
  const aSamples = useMemo(() => prepareSamples(run.telemetry.columns, name), [run, name]);
  const bSamples = useMemo(
    () => (other ? prepareSamples(other.telemetry.columns, name) : null),
    [other, name],
  );
  const a = series(run.telemetry.columns, name),
    candidate = other ? series(other.telemetry.columns, name) : null;
  const mismatch =
    other && a && candidate
      ? comparisonReason(
          run.telemetry.channel_metadata?.[name],
          other.telemetry.channel_metadata?.[name],
          run.record.code_sha256,
          other.record.code_sha256,
        )
      : null;
  const comparison = mismatch ? null : candidate;
  const displayed = displayedMetadata(
    !!a,
    !!comparison,
    run.telemetry.channel_metadata?.[name],
    other?.telemetry.channel_metadata?.[name],
  );
  const available = [...(a ?? []), ...(comparison ?? [])];
  const sampleText = (samples: ReturnType<typeof prepareSamples>, loaded: Loaded) => {
    const sample = nearestSample(samples, time);
    if (!sample) return 'unavailable at this time';
    if (sample.value === null) return `unavailable at sampled T+${sample.time} s`;
    const unit = loaded.telemetry.channel_metadata?.[name]?.unit ?? 'units unknown';
    return `${sample.value} ${unit} at sampled T+${sample.time} s`;
  };
  const readout = (
    <p>
      Nearest decimated playback sample · A: {sampleText(aSamples, run)}
      {other && <> · B: {sampleText(bSamples, other)}</>}
    </p>
  );
  const selector = (
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
  );
  if (!available.length)
    return (
      <div className="exp-plot">
        {selector}
        {readout}
        <p>Channel unavailable for plotting. Missing data is not zero.</p>
      </div>
    );
  const { min, max } = plotScale(available);
  const [minLabel, maxLabel] = scaleLabels(min, max);
  const end = Math.max(
    run.telemetry.columns.time_s.at(-1)!,
    other?.telemetry.columns.time_s.at(-1) ?? 0,
  );
  const points = (r: Loaded, v: number[]) =>
    v
      .map(
        (n, i) =>
          `${(r.telemetry.columns.time_s[i] / end) * 100},${95 - ((n - min) / (max - min || 1)) * 90}`,
      )
      .join(' ');
  return (
    <div className="exp-plot">
      {selector}
      {readout}
      <span>
        Scale: {minLabel} – {maxLabel}
      </span>
      <svg
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        onClick={(e) =>
          setTime(
            ((e.clientX - e.currentTarget.getBoundingClientRect().left) /
              e.currentTarget.clientWidth) *
              end,
          )
        }
      >
        {a && (
          <polyline
            points={points(run, a)}
            fill="none"
            stroke="#54d8d2"
            vectorEffect="non-scaling-stroke"
          />
        )}
        {other && comparison && (
          <polyline
            points={points(other, comparison)}
            fill="none"
            stroke="#f5b960"
            vectorEffect="non-scaling-stroke"
          />
        )}
        <line
          x1={(time / end) * 100}
          x2={(time / end) * 100}
          y1="0"
          y2="100"
          stroke="#fff"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
      {!a && <p>Run A channel unavailable; missing data is not zero.</p>}
      {mismatch && <p>{mismatch}</p>}
      {other && !candidate && <p>Run B channel unavailable; missing data is not zero.</p>}
      <p>
        {displayed?.meta
          ? `Run ${displayed.run}: ${displayed.meta.description} · ${displayed.meta.source} · ${displayed.meta.unit ?? 'units unknown'}`
          : `Run ${displayed?.run}: channel metadata unavailable; units and source unknown.`}
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
}: {
  configurationId: string;
  vehicle: InspectionDocument | null;
  onConfigurationChange: (id: string) => void;
  workspace?: 'experiments' | 'replay';
  onOpenReplay?: () => void;
}) {
  const [wind, setWind] = useState(0),
    [direction, setDirection] = useState(0),
    [gust, setGust] = useState(0),
    [runs, setRuns] = useState<RecordRun[]>([]),
    [current, setCurrent] = useState<Loaded | null>(null),
    [other, setOther] = useState<Loaded | null>(null),
    [pending, setPending] = useState(''),
    [status, setStatus] = useState(''),
    [error, setError] = useState(''),
    [draftStatus, setDraftStatus] = useState(''),
    [time, setTime] = useState(0),
    [playing, setPlaying] = useState(false),
    [speed, setSpeed] = useState(1),
    [mode, setMode] = useState<'follow' | 'free'>('follow'),
    [fitToken, setFitToken] = useState(0),
    [resetPreview, setResetPreview] = useState(0),
    [plotChannels, setPlotChannels] = useState(defaultChannels);
  const supportedChoice = choices.some(([id]) => id === configurationId);
  const loadOrder = useRef({ primary: requestOrder(), comparison: requestOrder() });
  useEffect(() => {
    const order = loadOrder.current;
    return () => {
      order.primary.cancel();
      order.comparison.cancel();
    };
  }, [configurationId]);
  const shown = current?.record.vehicle_id === configurationId ? current : null;
  const primaryTimes = shown?.telemetry.columns.time_s;
  const comparisonTimes = other?.telemetry.columns.time_s;
  const primaryWindow = useMemo(() => replayWindow(primaryTimes), [primaryTimes]);
  const comparisonWindow = useMemo(() => replayWindow(comparisonTimes), [comparisonTimes]);
  const replayEnd = shown ? Math.max(primaryWindow?.end ?? 0, comparisonWindow?.end ?? 0, 0) : 0;
  const refresh = useCallback(
    () =>
      json<RecordRun[]>('/api/runs')
        .then(setRuns)
        .catch((e) => setError(String(e))),
    [],
  );
  useEffect(() => {
    void refresh();
  }, [refresh]);
  const load = useCallback(
    async (id: string, compare = false) => {
      const isCurrent = (
        compare ? loadOrder.current.comparison : loadOrder.current.primary
      ).begin();
      try {
        const record = await json<RecordRun>(`/api/runs/${id}`);
        const [telemetry, vehicle] = await Promise.all([
          json<Telemetry>(`/api/runs/${id}/telemetry`),
          json<InspectionDocument>(`/api/vehicles/${record.vehicle_id}`),
        ]);
        if (
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
        if (!isCurrent()) return;
        const item = { record, telemetry, vehicle };
        if (compare) setOther(item);
        else {
          onConfigurationChange(record.vehicle_id!);
          setCurrent(item);
          setTime(firstRecordedTime(replayWindow(telemetry.columns.time_s)));
          setPlaying(false);
        }
        setError('');
      } catch (e) {
        if (isCurrent()) setError(String(e));
      }
    },
    [onConfigurationChange],
  );
  useEffect(() => {
    if (!pending) return;
    let timer: number;
    let alive = true;
    const poll = async () => {
      try {
        const r = await json<RecordRun>(`/api/experiments/${pending}`);
        if (!alive) return;
        setStatus(r.progress);
        if (r.status === 'complete') {
          setPending('');
          void refresh();
          void load(pending);
        } else if (r.status === 'failed') {
          setError(r.error ?? 'Run failed');
          setPending('');
          void refresh();
        } else timer = window.setTimeout(poll, 1200);
      } catch (e) {
        setError(String(e));
        setPending('');
      }
    };
    void poll();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [pending, refresh, load]);
  useEffect(() => {
    if (!playing || !shown) return;
    let last = performance.now(),
      frame = 0;
    const tick = (now: number) => {
      setTime((t) => {
        const next = t + ((now - last) / 1000) * speed;
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
  function downloadRun(run: Loaded, peer: Loaded | null, kind: 'csv' | 'json') {
    try {
      const content = kind === 'csv' ? telemetryCsv(run) : exportMetadata(run, peer);
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
  function reuseDraft(run: Loaded) {
    const draft = recordedSettingsDraft(run.record, configurationId);
    if (!draft.ok) {
      setDraftStatus(draft.reason);
      return;
    }
    setWind(draft.wind);
    setDirection(draft.direction);
    setGust(draft.gust);
    setDraftStatus(
      `Draft copied from ${run.record.run_id}. Review Experiment setup; no run was started. Case/model details and source revisions are not copied.`,
    );
  }
  async function start() {
    try {
      setError('');
      if (!supportedChoice || configurationId === 'modular-tvc-finless-v1')
        throw new Error(
          'Select a supported complete flight configuration; inspection candidates and finless unguided flight cannot run.',
        );
      const r = await json<{ run_id: string }>('/api/experiments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          configuration: configurationId,
          wind_mps: wind,
          wind_direction_deg: direction,
          gust_mps: gust,
          preset: 'sim',
        }),
      });
      setPending(r.run_id);
      setStatus('Queued');
    } catch (e) {
      setError(String(e));
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
          <button
            disabled={!!pending || !supportedChoice || configurationId === 'modular-tvc-finless-v1'}
            onClick={() => void start()}
          >
            Run on CPU
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
          <p role="status">
            {status} · {pending}
          </p>
        )}
        {error && (
          <p role="alert" className="exp-error">
            {error}
          </p>
        )}
        <h3>Saved runs</h3>
        {workspace === 'experiments' && onOpenReplay && (
          <button type="button" onClick={onOpenReplay}>
            Open flight replay
          </button>
        )}
        {runs.length === 0 && <p>No saved runs are available.</p>}
        {runs.map((r) => (
          <div key={r.run_id} className="exp-run">
            <button disabled={r.status !== 'complete'} onClick={() => void load(r.run_id)}>
              {r.configuration}
              <br />
              <small>
                {r.run_id} · {r.status}
              </small>
            </button>
            <button disabled={r.status !== 'complete'} onClick={() => void load(r.run_id, true)}>
              Compare
            </button>
          </div>
        ))}
      </aside>
      <main>
        {shown ? (
          <>
            <div className="exp-replay">
              <FlightScene run={shown} other={other} time={time} mode={mode} fitToken={fitToken} />
            </div>
            <div className="exp-controls">
              <button onClick={() => setMode(mode === 'follow' ? 'free' : 'follow')}>
                Camera: {mode}
              </button>
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
                  if (!playing && time >= replayEnd)
                    setTime(firstRecordedTime(primaryWindow, comparisonWindow));
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
                min="0"
                max={replayEnd}
                step="0.01"
                value={time}
                onChange={(e) => setTime(Number(e.target.value))}
              />
              <span>T+{time.toFixed(2)} s</span>
            </div>
            <p>
              Orbit and zoom with mouse. Teal: {shown.record.run_id}
              {other && ` · Gold: ${other.record.run_id}`}
              {other && ' · Each actor is visible only within its recorded window.'}
            </p>
            <ReplayValidity run={shown} time={time} label="A · teal" />
            {other && <ReplayValidity run={other} time={time} label="B · gold" />}
            <div className="exp-events">
              {Object.entries(shown.record.events ?? {}).map(([k, v]) => (
                <button key={k} disabled={v === null} onClick={() => setTime(v!)}>
                  {k.replace('_', ' ')}: {v === null ? 'not recorded' : `T+${v.toFixed(2)} s`}
                </button>
              ))}
            </div>
            <p>
              Choose recorded or backend-derived channels. Unrecognized names are shown exactly as
              recorded; their units and meaning are not inferred. Plots use decimated playback
              samples. Readouts use the nearest decimated playback sample within each run’s recorded
              time range, without interpolation; they do not establish full-rate extremes.
            </p>
            <div className="exp-plots">
              {plotChannels.map((name, index) => (
                <Plot
                  key={index}
                  run={shown}
                  other={other}
                  name={name}
                  time={time}
                  setTime={setTime}
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
                  Export returned decimated playback samples, including backend-derived channels.
                  Each run keeps its own timestamps and coverage; missing values are blank. These
                  files are not full-resolution telemetry.
                </p>
                <button onClick={() => downloadRun(shown, other, 'csv')}>Download A CSV</button>
                <button onClick={() => downloadRun(shown, other, 'json')}>
                  Download A metadata JSON
                </button>
                <button onClick={() => reuseDraft(shown)}>
                  Reuse A recorded settings as draft
                </button>
                {other && (
                  <>
                    <button onClick={() => downloadRun(other, shown, 'csv')}>Download B CSV</button>
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
                      setTime((t) => Math.min(t, shown.telemetry.columns.time_s.at(-1) ?? 0));
                    }}
                  >
                    Clear comparison
                  </button>
                  <p>
                    The runs share elapsed time from ignition; this is not event alignment.
                    Differences or missing assumptions prevent attributing a result to one change.
                    Compare complete configurations, not motors alone: mounting, mass, geometry and
                    recovery may also differ. Match wind, gust and other case settings to
                    investigate a motor change; model and input identities still matter.
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
