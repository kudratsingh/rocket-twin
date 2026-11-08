import { Box3, MeshStandardMaterial, PerspectiveCamera, Vector3 } from 'three';
import type { BufferGeometry } from 'three';

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
  const nearest = depths.length ? Math.min(...depths) : 0;
  const near =
    nearest > 0
      ? Math.max(1e-8, nearest / 4)
      : Math.max(
          1e-8,
          Math.min(scale * 1e-5, distance * 1e-4, ...positive.map((value) => value / 4)),
        );
  const far = Math.max(near * 2, distance + scale, ...depths.map((value) => value + scale));
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

/** Normalize wheel line/page units and the ctrl-wheel stream emitted by trackpad pinches. */
export function orbitWheelFactor(
  event: { deltaY: number; deltaMode: number; ctrlKey: boolean },
  height: number,
) {
  const pixels =
    event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? Math.max(height, 1) : 1);
  const sensitivity = event.ctrlKey ? 0.012 : 0.002;
  return Math.exp(Math.max(-0.35, Math.min(0.35, pixels * sensitivity)));
}

/** One canvas gesture owner; real drags cannot fall through to R3F surface picking. */
export function bindInspectionOrbit(
  canvas: HTMLElement,
  handlers: {
    begin: () => void;
    move: (dx: number, dy: number, kind: string) => void;
    zoom: (factor: number) => void;
  },
  height: () => number,
) {
  type Pointer = { x: number; y: number; startX: number; startY: number; kind: string };
  const pointers = new Map<number, Pointer>();
  let dragging = false,
    suppressClick = false;
  const originalTouch = canvas.style.touchAction;
  canvas.style.touchAction = 'none';
  const start = () => {
    if (!dragging) {
      dragging = true;
      suppressClick = true;
      canvas.dataset.orbitDragging = 'true';
      handlers.begin();
    }
  };
  const down = (event: PointerEvent) => {
    if (event.button > 2 || pointers.size >= 2) return;
    if (!pointers.size) {
      dragging = false;
      suppressClick = false;
    }
    pointers.set(event.pointerId, {
      x: event.clientX,
      y: event.clientY,
      startX: event.clientX,
      startY: event.clientY,
      kind: event.altKey
        ? 'roll'
        : event.button === 2 || event.shiftKey || event.ctrlKey
          ? 'pan'
          : 'orbit',
    });
    canvas.setPointerCapture(event.pointerId);
    if (pointers.size === 2) start();
  };
  const move = (event: PointerEvent) => {
    const previous = pointers.get(event.pointerId);
    if (!previous) return;
    const old = [...pointers.values()];
    const oldDistance = old.length === 2 ? Math.hypot(old[0].x - old[1].x, old[0].y - old[1].y) : 0;
    let dx = event.clientX - previous.x,
      dy = event.clientY - previous.y;
    previous.x = event.clientX;
    previous.y = event.clientY;
    if (!dragging) {
      if (Math.hypot(event.clientX - previous.startX, event.clientY - previous.startY) < 3) return;
      dx = event.clientX - previous.startX;
      dy = event.clientY - previous.startY;
      start();
    }
    if (dx === 0 && dy === 0) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (pointers.size === 2) {
      const next = [...pointers.values()];
      const distance = Math.hypot(next[0].x - next[1].x, next[0].y - next[1].y);
      handlers.move(dx / 2, dy / 2, 'pan');
      if (oldDistance > 0 && distance > 0) handlers.zoom(oldDistance / distance);
    } else handlers.move(dx, dy, previous.kind);
  };
  const up = (event: PointerEvent) => {
    pointers.delete(event.pointerId);
    if (canvas.hasPointerCapture(event.pointerId)) canvas.releasePointerCapture(event.pointerId);
    if (!pointers.size) {
      dragging = false;
      delete canvas.dataset.orbitDragging;
    }
  };
  const wheel = (event: WheelEvent) => {
    event.preventDefault();
    event.stopImmediatePropagation();
    handlers.begin();
    handlers.zoom(orbitWheelFactor(event, height()));
  };
  const click = (event: MouseEvent) => {
    if (suppressClick) {
      event.preventDefault();
      event.stopImmediatePropagation();
      suppressClick = false;
    }
  };
  const context = (event: Event) => event.preventDefault();
  canvas.addEventListener('pointerdown', down, true);
  canvas.addEventListener('pointermove', move, true);
  canvas.addEventListener('pointerup', up, true);
  canvas.addEventListener('pointercancel', up, true);
  canvas.addEventListener('lostpointercapture', up, true);
  canvas.addEventListener('wheel', wheel, { capture: true, passive: false });
  canvas.addEventListener('click', click, true);
  canvas.addEventListener('contextmenu', context, true);
  return () => {
    for (const id of pointers.keys())
      if (canvas.hasPointerCapture(id)) canvas.releasePointerCapture(id);
    pointers.clear();
    delete canvas.dataset.orbitDragging;
    canvas.style.touchAction = originalTouch;
    canvas.removeEventListener('pointerdown', down, true);
    canvas.removeEventListener('pointermove', move, true);
    canvas.removeEventListener('pointerup', up, true);
    canvas.removeEventListener('pointercancel', up, true);
    canvas.removeEventListener('lostpointercapture', up, true);
    canvas.removeEventListener('wheel', wheel, true);
    canvas.removeEventListener('click', click, true);
    canvas.removeEventListener('contextmenu', context, true);
  };
}

/** Appearance follows declared material families; colours remain source/maturity display colours. */
export function inspectionSurface(material: string) {
  const value = material.toLowerCase();
  if (/alumin|steel|brass|copper|metal/.test(value)) return { roughness: 0.48, metalness: 0.65 };
  if (/cardboard|paper|kraft|wood|ply|birch/.test(value)) return { roughness: 0.92, metalness: 0 };
  if (/carbon|fibreglass|fiberglass|composite/.test(value))
    return { roughness: 0.72, metalness: 0 };
  return { roughness: 0.8, metalness: 0 };
}

/** Repair absent display normals without mutating the cached source geometry. */
export function inspectionNormals(source: BufferGeometry): {
  geometry: BufferGeometry;
  owned: boolean;
} {
  if (source.getAttribute('normal')) return { geometry: source, owned: false };
  const geometry = source.clone();
  geometry.computeVertexNormals();
  return { geometry, owned: true };
}

/** Clone a display material; admitted detail layers retain their own colours. */
export function inspectionMaterial(
  source: unknown,
  material: string,
  color: string,
  preserveSource = false,
) {
  const result =
    preserveSource && source instanceof MeshStandardMaterial
      ? source.clone()
      : new MeshStandardMaterial({ color, ...inspectionSurface(material), side: 2 });
  result.userData.inspectionBaseColor = `#${result.color.getHexString()}`;
  return result;
}
