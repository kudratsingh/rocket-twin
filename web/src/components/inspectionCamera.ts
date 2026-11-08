import { Box3, Plane, Vector3 } from 'three';
import type { CameraFrame } from './inspectionGeometry';

/** Insets are fractions of canvas width/height. Fill is the fraction of the safe rectangle. */
export type OrbitFitOptions = {
  insets?: { left?: number; right?: number; top?: number; bottom?: number };
  fill?: number;
};

/** Fractions of the actual canvas; shared by the fitter and its visible display guide. */
export function inspectionFrameInsets(width: number, height: number) {
  return {
    left: 16 / Math.max(width, 80),
    right: Math.min(130, width * 0.18) / Math.max(width, 1),
    top: Math.min(84, height * 0.18) / Math.max(height, 1),
    bottom: Math.min(92, height * 0.18) / Math.max(height, 1),
  };
}

function boxCorners(bounds: Box3): Vector3[] {
  const points: Vector3[] = [];
  for (const x of [bounds.min.x, bounds.max.x]) {
    for (const y of [bounds.min.y, bounds.max.y]) {
      for (const z of [bounds.min.z, bounds.max.z]) points.push(new Vector3(x, y, z));
    }
  }
  return points;
}

/** Frame all supplied box corners along the current viewing direction (not clipped mesh bounds). */
export function fitOrbitFrame(
  bounds: Box3,
  aspect: number,
  fov: number,
  cameraPosition: Vector3,
  orbitTarget: Vector3,
  cameraUp: Vector3,
  options: OrbitFitOptions = {},
): CameraFrame {
  const coordinates = [...bounds.min.toArray(), ...bounds.max.toArray()];
  if (
    bounds.isEmpty() ||
    !coordinates.every(Number.isFinite) ||
    !Number.isFinite(aspect) ||
    aspect <= 0 ||
    !Number.isFinite(fov) ||
    fov <= 0 ||
    fov >= 180 ||
    ![...cameraPosition.toArray(), ...orbitTarget.toArray(), ...cameraUp.toArray()].every(
      Number.isFinite,
    )
  ) {
    throw new RangeError('Invalid bounds or perspective camera');
  }
  const { left = 0, right: insetRight = 0, top = 0, bottom = 0 } = options.insets ?? {};
  const fill = options.fill ?? 1 / 1.15;
  if (
    ![left, insetRight, top, bottom, fill].every(Number.isFinite) ||
    Math.min(left, insetRight, top, bottom) < 0 ||
    left + insetRight >= 1 ||
    top + bottom >= 1 ||
    fill <= 0 ||
    fill > 1
  ) {
    throw new RangeError('Invalid safe rectangle or fill');
  }
  const center = bounds.getCenter(new Vector3());
  const direction = cameraPosition.clone().sub(orbitTarget);
  if (direction.lengthSq() === 0) direction.set(1, 1, 1);
  direction.normalize();
  const upHint = cameraUp.clone().normalize();
  let right = new Vector3().crossVectors(upHint, direction);
  if (right.lengthSq() < 1e-12) {
    upHint.set(0, 0, 1);
    if (Math.abs(direction.dot(upHint)) > 0.99) upHint.set(0, 1, 0);
    right = new Vector3().crossVectors(upHint, direction);
  }
  right.normalize();
  const up = new Vector3().crossVectors(direction, right).normalize();
  const tanV = Math.tan((fov * Math.PI) / 360);
  const tanH = tanV * aspect;
  const centerX = left - insetRight;
  const centerY = bottom - top;
  const halfX = (1 - left - insetRight) * fill;
  const halfY = (1 - top - bottom) * fill;
  const xLimits = [centerX - halfX, centerX + halfX];
  const yLimits = [centerY - halfY, centerY + halfY];
  const points = boxCorners(bounds).map((p) => {
    p.sub(center);
    return { x: p.dot(right), y: p.dot(up), z: p.dot(direction) };
  });
  // Every pair gives a lower distance bound for a non-empty range of lateral offsets.
  let distance = Math.max(...points.map((p) => p.z));
  for (const a of points) {
    for (const b of points) {
      distance = Math.max(
        distance,
        (a.x - b.x + tanH * (xLimits[1] * a.z - xLimits[0] * b.z)) /
          (tanH * (xLimits[1] - xLimits[0])),
        (a.y - b.y + tanV * (yLimits[1] * a.z - yLimits[0] * b.z)) /
          (tanV * (yLimits[1] - yLimits[0])),
      );
    }
  }
  const scale = bounds.getSize(new Vector3()).length();
  distance += Math.max(scale * 1e-10, Number.EPSILON * Math.max(scale, 1), 1e-12);
  function offset(axis: 'x' | 'y', limits: number[], tangent: number): number {
    const lower = Math.max(...points.map((p) => p[axis] - limits[1] * tangent * (distance - p.z)));
    const upper = Math.min(...points.map((p) => p[axis] - limits[0] * tangent * (distance - p.z)));
    // Perspective depth makes the projected center differ from the box center.
    // Find the offset that centers the projected extrema inside this safe axis.
    let lo = lower;
    let hi = upper;
    const desiredCenter = (limits[0] + limits[1]) / 2;
    for (let i = 0; i < 48; i += 1) {
      const mid = (lo + hi) / 2;
      const projected = points.map((p) => (p[axis] - mid) / (tangent * (distance - p.z)));
      const projectedCenter = (Math.min(...projected) + Math.max(...projected)) / 2;
      if (projectedCenter > desiredCenter) lo = mid;
      else hi = mid;
    }
    return (lo + hi) / 2;
  }
  const target = center
    .clone()
    .addScaledVector(right, offset('x', xLimits, tanH))
    .addScaledVector(up, offset('y', yLimits, tanV));
  const depths = points.map((point) => distance - point.z);
  const near = Math.min(...depths) / 2;
  const far = Math.max(...depths) * 2 + scale;
  return {
    target: target.toArray(),
    position: target.clone().addScaledVector(direction, distance).toArray(),
    up: upHint.toArray(),
    near,
    far,
  };
}

/** Bound the plane's nonnegative half-space of a box, not of its contained mesh. */
export function clippedBoxBounds(bounds: Box3, plane: Plane): Box3 | null {
  if (bounds.isEmpty()) return null;
  const corners = boxCorners(bounds);
  const distances = corners.map((corner) => plane.distanceToPoint(corner));
  const result = new Box3();
  corners.forEach((corner, index) => {
    if (distances[index] >= 0) result.expandByPoint(corner);
  });
  // Corner index differs by one bit along exactly one box edge.
  for (let i = 0; i < corners.length; i += 1) {
    for (const bit of [1, 2, 4]) {
      const j = i ^ bit;
      if (j <= i || distances[i] * distances[j] >= 0) continue;
      const t = distances[i] / (distances[i] - distances[j]);
      result.expandByPoint(corners[i].clone().lerp(corners[j], t));
    }
  }
  return result.isEmpty() ? null : result;
}

/** Clipped geometry must not intercept a pick intended for a visible interior part. */
export function isPointClipped(point: Vector3, plane: Plane, sectionEnabled: boolean): boolean {
  return sectionEnabled && plane.distanceToPoint(point) < 0;
}
