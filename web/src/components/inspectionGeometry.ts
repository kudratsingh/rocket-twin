export type InspectionView = 'overview' | 'front' | 'side' | 'aft';

export const CAMERA_VIEWS: ReadonlyArray<{
  id: InspectionView;
  label: string;
  description: string;
}> = [
  {
    id: 'overview',
    label: 'Overview',
    description: 'See the whole design from above and to one side.',
  },
  { id: 'front', label: 'Front', description: 'Front elevation, with the nose pointing up.' },
  { id: 'side', label: 'Side', description: 'See the rocket from the side.' },
  {
    id: 'aft',
    label: 'Motor end',
    description: 'Look into the motor end along the rocket’s length.',
  },
];

export type Bounds3 = { min: [number, number, number]; max: [number, number, number] };
export type CameraFrame = {
  target: [number, number, number];
  position: [number, number, number];
  up: [number, number, number];
  near: number;
  far: number;
};

type Vec3 = [number, number, number];

const VIEW_DIRECTION: Record<InspectionView, Vec3> = {
  overview: [1, 1, 1],
  front: [0, 0, 1],
  side: [1, 0, 0],
  aft: [0, -1, 0],
};

const WORLD_UP: Vec3 = [0, 1, 0];
const AFT_UP: Vec3 = [0, 0, 1];
const FRAME_MARGIN = 1.15;
const MIN_DISTANCE = 0.05;

function dot(a: Vec3, b: Vec3): number {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}

function cross(a: Vec3, b: Vec3): Vec3 {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}

function normalize(vector: Vec3): Vec3 {
  const length = Math.hypot(...vector);
  return [vector[0] / length, vector[1] / length, vector[2] / length];
}

function corners(bounds: Bounds3, target: Vec3): Vec3[] {
  const points: Vec3[] = [];
  for (const x of [bounds.min[0], bounds.max[0]]) {
    for (const y of [bounds.min[1], bounds.max[1]]) {
      for (const z of [bounds.min[2], bounds.max[2]])
        points.push([x - target[0], y - target[1], z - target[2]]);
    }
  }
  return points;
}

/** Fit the eight corners of real source bounds inside the camera's field of view. */
export function cameraFrame(
  bounds: Bounds3,
  aspect: number,
  verticalFovDegrees = 35,
  view: InspectionView = 'overview',
): CameraFrame {
  if (
    !bounds ||
    bounds.min.length !== 3 ||
    bounds.max.length !== 3 ||
    !bounds.min.every(Number.isFinite) ||
    !bounds.max.every(Number.isFinite) ||
    bounds.min.some((value, index) => value > bounds.max[index])
  ) {
    throw new RangeError('Bounds must contain finite, ordered three-dimensional limits.');
  }
  if (!Number.isFinite(aspect) || aspect <= 0)
    throw new RangeError('Aspect ratio must be finite and positive.');
  if (
    !Number.isFinite(verticalFovDegrees) ||
    verticalFovDegrees <= 0 ||
    verticalFovDegrees >= 180
  ) {
    throw new RangeError('Vertical field of view must be between 0 and 180 degrees.');
  }
  if (!(view in VIEW_DIRECTION)) throw new RangeError('Unknown inspection view.');

  const target: Vec3 = [
    (bounds.min[0] + bounds.max[0]) / 2,
    (bounds.min[1] + bounds.max[1]) / 2,
    (bounds.min[2] + bounds.max[2]) / 2,
  ];
  const direction = normalize(VIEW_DIRECTION[view]);
  const upHint = view === 'aft' ? AFT_UP : WORLD_UP;
  const right = normalize(cross(direction, upHint));
  const up = normalize(cross(right, direction));
  const tanVertical = Math.tan((verticalFovDegrees * Math.PI) / 360);
  const tanHorizontal = tanVertical * aspect;
  const points = corners(bounds, target);

  // Each corner's available half-angle shrinks with its depth along the view axis.
  let distance = MIN_DISTANCE;
  for (const point of points) {
    distance = Math.max(
      distance,
      dot(point, direction) + (FRAME_MARGIN * Math.abs(dot(point, right))) / tanHorizontal,
      dot(point, direction) + (FRAME_MARGIN * Math.abs(dot(point, up))) / tanVertical,
    );
  }
  // A flat/line-like model must still leave positive space in front of its nearest face.
  distance = Math.max(
    MIN_DISTANCE,
    distance,
    Math.max(...points.map((point) => dot(point, direction))) + 0.001,
  );
  const depths = points.map((point) => distance - dot(point, direction));
  const minDepth = Math.min(...depths);
  const maxDepth = Math.max(...depths);
  const near = Math.max(0.0001, minDepth / 2);
  const far = Math.max(
    near * 2,
    maxDepth + Math.hypot(...bounds.max.map((value, i) => value - bounds.min[i])),
  );

  return {
    target,
    position: [
      target[0] + direction[0] * distance,
      target[1] + direction[1] * distance,
      target[2] + direction[2] * distance,
    ],
    up: upHint,
    near,
    far,
  };
}
