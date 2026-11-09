import { replayWindow } from './replayWindow.ts';

export type TrajectoryColumns = Record<string, readonly number[]>;
export type ReplayTrajectoryBounds = {
  min: [number, number, number];
  max: [number, number, number];
  points: number;
};

/** View-only bounds in Three.js east/up/south axes, from recorded positions.
 * Missing position samples remain missing; no interpolation or origin is invented.
 * All loaded recorded windows are included, independently of replay alignment.
 */
export function replayTrajectoryBounds(
  ...runs: (TrajectoryColumns | null | undefined)[]
): ReplayTrajectoryBounds | null {
  let bounds: ReplayTrajectoryBounds | null = null;
  for (const columns of runs) {
    if (!columns || !replayWindow(columns.time_s)) continue;
    const count = columns.time_s.length;
    if (
      !['east_m', 'down_m', 'north_m'].every(
        (name) => Array.isArray(columns[name]) && columns[name].length === count,
      )
    )
      continue;
    for (let index = 0; index < count; index++) {
      const east = columns.east_m[index];
      const down = columns.down_m[index];
      const north = columns.north_m[index];
      if (![east, down, north].every(Number.isFinite)) continue;
      const point: [number, number, number] = [east, -down, -north];
      if (!bounds) bounds = { min: [...point], max: [...point], points: 0 };
      for (let axis = 0; axis < 3; axis++) {
        bounds.min[axis] = Math.min(bounds.min[axis], point[axis]);
        bounds.max[axis] = Math.max(bounds.max[axis], point[axis]);
      }
      bounds.points++;
    }
  }
  return bounds;
}

/** Distance to contain a bounding sphere through the narrower perspective angle. */
export function replayFitDistance(radius: number, verticalFovDegrees: number, aspect: number) {
  if (
    ![radius, verticalFovDegrees, aspect].every(Number.isFinite) ||
    radius <= 0 ||
    aspect <= 0 ||
    verticalFovDegrees <= 0 ||
    verticalFovDegrees >= 180
  )
    return null;
  const halfVertical = (verticalFovDegrees * Math.PI) / 360;
  const halfHorizontal = Math.atan(Math.tan(halfVertical) * aspect);
  return (radius / Math.sin(Math.min(halfVertical, halfHorizontal))) * 1.1;
}
