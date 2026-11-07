import { Matrix4, Quaternion } from 'three';
import { replayWindow, replayWindowStatus } from './replayWindow.ts';

export type ReplayPose =
  | { kind: 'unavailable'; reason: string }
  | { kind: 'marker'; reason: string; position: [number, number, number] }
  | {
      kind: 'pose';
      position: [number, number, number];
      quaternion: Quaternion;
      pivot: [number, number, number];
      bracket: [number, number];
      fraction: number;
    };

type Columns = Record<string, number[]>;

/** Resolve recorded samples without extrapolation; no velocity-derived attitude. */
export function replayPose(
  columns: Columns,
  length: number,
  time: number,
  maxGap?: number,
): ReplayPose {
  const times = columns.time_s;
  const window = replayWindow(times);
  const status = replayWindowStatus(window, time);
  if (status !== 'inside')
    return {
      kind: 'unavailable',
      reason: status === 'outside' ? 'Outside recorded window' : 'Recorded window unavailable',
    };
  let lo = 0;
  let hi = times.length - 1;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (times[mid] < time) lo = mid + 1;
    else hi = mid;
  }
  const right = lo;
  const left = times[right] === time || right === 0 ? right : right - 1;
  const gap = times[right] - times[left];
  if (maxGap !== undefined && (!Number.isFinite(maxGap) || maxGap <= 0 || gap > maxGap))
    return { kind: 'unavailable', reason: 'Interpolation gap unsupported' };
  const fraction = left === right ? 0 : (time - times[left]) / gap;
  const sample = (name: string, index: number) => {
    const values = columns[name];
    return Array.isArray(values) && values.length === times.length && Number.isFinite(values[index])
      ? values[index]
      : null;
  };
  const interpolate = (name: string) => {
    const a = sample(name, left);
    const b = sample(name, right);
    return a === null || b === null ? null : a * (1 - fraction) + b * fraction;
  };
  const north = interpolate('north_m');
  const east = interpolate('east_m');
  const down = interpolate('down_m');
  if (north === null || east === null || down === null)
    return { kind: 'unavailable', reason: 'Recorded position unavailable' };
  const position: [number, number, number] = [east, -down, -north];
  const marker = (reason: string): ReplayPose => ({ kind: 'marker', reason, position });
  const quaternionAt = (index: number) => {
    const w = sample('qw', index),
      x = sample('qx', index),
      y = sample('qy', index),
      z = sample('qz', index);
    if (w === null || x === null || y === null || z === null) return null;
    const q = new Quaternion(x, y, z, w);
    return Number.isFinite(q.lengthSq()) && q.lengthSq() > 0 ? q.normalize() : null;
  };
  const a = quaternionAt(left);
  const b = quaternionAt(right);
  if (!a || !b) return marker('Recorded attitude unavailable');
  const cg = interpolate('cg_station_m');
  if (!Number.isFinite(length) || length <= 0 || cg === null)
    return marker('Recorded centre of mass or geometry length unavailable');
  const q = a.slerp(b, fraction);
  const bodyFromCad = new Matrix4().set(0, 1, 0, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1);
  const sceneFromNed = new Matrix4().set(0, 1, 0, 0, 0, 0, -1, 0, -1, 0, 0, 0, 0, 0, 0, 1);
  const quaternion = new Quaternion().setFromRotationMatrix(
    sceneFromNed.multiply(new Matrix4().makeRotationFromQuaternion(q)).multiply(bodyFromCad),
  );
  return {
    kind: 'pose',
    position,
    quaternion,
    pivot: [0, -(length - cg), 0],
    bracket: [times[left], times[right]],
    fraction,
  };
}
