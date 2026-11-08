import { Box3, PerspectiveCamera, Vector3 } from 'three';

/** CAD inspection axes: +Y nose; azimuth 0 at +Z, positive toward +X. */
export type OrbitAngles = { azimuth: number; tilt: number; roll: number };
export type OrbitReadout = OrbitAngles & {
  mode: string;
  target: 'assembly' | 'selection';
  targetLabel?: string;
};
const radians = Math.PI / 180;
export function orbitBasis({ azimuth, tilt, roll }: OrbitAngles) {
  if (![azimuth, tilt, roll].every(Number.isFinite) || tilt < 0 || tilt > 180)
    throw new RangeError('Use finite angles; tilt must be between 0° nose end and 180° motor end.');
  const a = azimuth * radians,
    t = tilt * radians,
    r = roll * radians;
  const direction = new Vector3(Math.sin(t) * Math.sin(a), Math.cos(t), Math.sin(t) * Math.cos(a));
  const unrolledUp = new Vector3(
    -Math.cos(t) * Math.sin(a),
    Math.sin(t),
    -Math.cos(t) * Math.cos(a),
  );
  const right = new Vector3().crossVectors(unrolledUp, direction).normalize();
  const up = unrolledUp
    .multiplyScalar(Math.cos(r))
    .addScaledVector(right, -Math.sin(r))
    .normalize();
  return { direction, up };
}

/** At either pole keep the previous azimuth as a stable coordinate convention. */
export function orbitAngles(
  camera: PerspectiveCamera,
  target: Vector3,
  previousAzimuth = 0,
): OrbitAngles {
  const d = camera.position.clone().sub(target).normalize();
  if (!d.lengthSq()) throw new RangeError('Camera and orbit target must differ.');
  const tilt = Math.acos(Math.max(-1, Math.min(1, d.y))) / radians;
  const raw = Math.hypot(d.x, d.z) < 1e-8 ? previousAzimuth : Math.atan2(d.x, d.z) / radians;
  const azimuth = raw + 360 * Math.round((previousAzimuth - raw) / 360);
  const basis = orbitBasis({ azimuth, tilt, roll: 0 });
  const actualUp = new Vector3(0, 1, 0).applyQuaternion(camera.quaternion).normalize();
  const right = new Vector3().crossVectors(basis.up, basis.direction).normalize();
  const roll = Math.atan2(-actualUp.dot(right), actualUp.dot(basis.up)) / radians;
  return { azimuth, tilt, roll };
}

export function applyOrbit(
  camera: PerspectiveCamera,
  target: Vector3,
  distance: number,
  angles: OrbitAngles,
) {
  if (!Number.isFinite(distance) || distance <= 0)
    throw new RangeError('Orbit distance must be positive.');
  const { direction, up } = orbitBasis(angles);
  camera.position.copy(target).addScaledVector(direction, distance);
  camera.up.copy(up);
  camera.lookAt(target);
  camera.updateMatrixWorld();
}

/** View-depth clipping is refreshed after every manual move, including close zoom. */
export function orbitClips(bounds: Box3, camera: PerspectiveCamera, target: Vector3) {
  const distance = camera.position.distanceTo(target);
  const scale = bounds.isEmpty()
    ? Math.max(distance, 0.001)
    : Math.max(bounds.getSize(new Vector3()).length(), 1e-7);
  const forward = target.clone().sub(camera.position).normalize();
  const depths: number[] = [];
  if (!bounds.isEmpty())
    for (const x of [bounds.min.x, bounds.max.x])
      for (const y of [bounds.min.y, bounds.max.y])
        for (const z of [bounds.min.z, bounds.max.z])
          depths.push(new Vector3(x, y, z).sub(camera.position).dot(forward));
  const positive = depths.filter((value) => value > 0);
  const near = Math.max(
    1e-8,
    Math.min(scale * 1e-5, distance * 1e-4, ...positive.map((value) => value / 4)),
  );
  const far = Math.max(near * 1000, distance + scale, ...depths.map((value) => value + scale));
  return { near, far };
}

/** Pan in the actual rolled camera plane, using CSS-pixel motion. */
export function panOrbit(
  target: Vector3,
  camera: PerspectiveCamera,
  dx: number,
  dy: number,
  height: number,
) {
  const metresPerPixel =
    (2 * Math.tan((camera.fov * radians) / 2) * camera.position.distanceTo(target)) /
    Math.max(height, 1);
  const right = new Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
  const up = new Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
  const translation = right
    .multiplyScalar(-dx * metresPerPixel)
    .addScaledVector(up, dy * metresPerPixel);
  target.add(translation);
  camera.position.add(translation);
}
