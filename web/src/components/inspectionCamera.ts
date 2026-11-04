import { Box3, Plane, Vector3 } from 'three';
import type { CameraFrame } from './inspectionGeometry';

/** Frame the actual bounds along the camera's current viewing direction. */
export function fitOrbitFrame(
  bounds: Box3,
  aspect: number,
  fov: number,
  cameraPosition: Vector3,
  orbitTarget: Vector3,
  cameraUp: Vector3,
): CameraFrame {
  const target = bounds.getCenter(new Vector3());
  const direction = cameraPosition.clone().sub(orbitTarget);
  if (direction.lengthSq() < 1e-12) direction.set(1, 1, 1);
  direction.normalize();
  const upHint = cameraUp.clone().normalize();
  let right = new Vector3().crossVectors(direction, upHint);
  if (right.lengthSq() < 1e-12) {
    upHint.set(0, 0, 1);
    if (Math.abs(direction.dot(upHint)) > 0.99) upHint.set(0, 1, 0);
    right = new Vector3().crossVectors(direction, upHint);
  }
  right.normalize();
  const up = new Vector3().crossVectors(right, direction).normalize();
  const tanV = Math.tan((fov * Math.PI) / 360);
  const tanH = tanV * aspect;
  let distance = 0.05;
  const points: Vector3[] = [];
  for (const x of [bounds.min.x, bounds.max.x]) {
    for (const y of [bounds.min.y, bounds.max.y]) {
      for (const z of [bounds.min.z, bounds.max.z]) {
        const point = new Vector3(x, y, z).sub(target);
        points.push(point);
        distance = Math.max(
          distance,
          point.dot(direction) + (1.15 * Math.abs(point.dot(right))) / tanH,
          point.dot(direction) + (1.15 * Math.abs(point.dot(up))) / tanV,
          point.dot(direction) + 0.001,
        );
      }
    }
  }
  const depths = points.map((point) => distance - point.dot(direction));
  const near = Math.max(0.0001, Math.min(...depths) / 2);
  const far = Math.max(near * 2, Math.max(...depths) + bounds.getSize(new Vector3()).length());
  return {
    target: target.toArray(),
    position: target.addScaledVector(direction, distance).toArray(),
    up: upHint.toArray(),
    near,
    far,
  };
}

/** Clipped geometry must not intercept a pick intended for a visible interior part. */
export function isPointClipped(point: Vector3, plane: Plane, sectionEnabled: boolean): boolean {
  return sectionEnabled && plane.distanceToPoint(point) < 0;
}
