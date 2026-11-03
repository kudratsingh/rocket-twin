import type { InspectionDocument, Part } from '../types';

export type DesignLayer = 'body' | 'fins' | 'rings' | 'motor' | 'envelopes';
export const designLayers: DesignLayer[] = ['body', 'fins', 'rings', 'motor', 'envelopes'];
export type Point = [number, number];
export interface DrawingPart {
  part: Part;
  layer: DesignLayer;
  polygons: Point[][];
  bounds: [number, number, number, number];
  representation: string;
  note: string;
}
const finite = (value: unknown): value is number =>
  typeof value === 'number' && Number.isFinite(value);
const positive = (value: unknown): value is number => finite(value) && value > 0;
function rectangle(x: number, y: number, width: number, height: number): Point[] {
  return [
    [x, y],
    [x + width, y],
    [x + width, y + height],
    [x, y + height],
  ];
}

/** Display conversion only: supplied metres become millimetres, with no solved properties. */
export function drawingPart(part: Part): DrawingPart | string {
  const g = part.dimensions ?? part.geometry;
  const station = part.location?.position_m ?? part.position_m;
  if (!g || !finite(station)) return 'Axial station or source dimensions unavailable.';
  const x = station * 1000;
  const lateral = part.location?.lateral_offset_m?.[0];
  if (lateral !== undefined && !finite(lateral)) return 'Invalid recorded transverse position.';
  const y = (lateral ?? 0) * 1000;
  const representation =
    typeof part.representation === 'object' &&
    part.representation &&
    !Array.isArray(part.representation)
      ? String(part.representation.role ?? 'unspecified')
      : 'unspecified';
  let note =
    lateral === undefined ? 'Transverse offset unavailable; shown as a centreline envelope. ' : '';
  let layer: DesignLayer = 'envelopes';
  let polygons: Point[][];
  if (part.type === 'fin_set') {
    if (
      ![g.radius_m, g.span_m, g.root_chord_m, g.tip_chord_m].every(positive) ||
      !finite(g.sweep_m) ||
      g.sweep_m < 0
    )
      return 'Fin radius, span, root/tip chord or sweep unavailable.';
    const radius = (g.radius_m as number) * 1000;
    const span = (g.span_m as number) * 1000;
    const root = (g.root_chord_m as number) * 1000;
    const tip = (g.tip_chord_m as number) * 1000;
    const sweep = g.sweep_m * 1000;
    polygons = [
      [
        [x, y + radius],
        [x + root, y + radius],
        [x + sweep + tip, y + radius + span],
        [x + sweep, y + radius + span],
      ],
    ];
    layer = 'fins';
    note += 'One radial fin planform; not a projection of fin count, clocking, tabs or attachment.';
  } else if (Array.isArray(g.bbox_m)) {
    if (g.bbox_m.length !== 3 || !g.bbox_m.every(positive))
      return 'Complete positive source box dimensions unavailable.';
    const [length, width] = g.bbox_m as number[];
    polygons = [rectangle(x, y - width * 500, length * 1000, width * 1000)];
    note +=
      'Source box envelope: axial length and first transverse width. Internal geometry unavailable.';
  } else {
    const radius = finite(g.radius_m)
      ? g.radius_m
      : finite(g.diameter_m)
        ? g.diameter_m / 2
        : finite(g.od_m)
          ? g.od_m / 2
          : undefined;
    if (!positive(g.length_m) || !positive(radius))
      return 'Positive source length and outer radius unavailable.';
    const length = g.length_m * 1000;
    const r = radius * 1000;
    if (part.type === 'motor') layer = 'motor';
    else if (part.type.includes('ring')) layer = 'rings';
    else if (
      part.outer_body ||
      part.nose ||
      ['nose_cone', 'body_tube', 'tube', 'transition'].includes(part.type)
    )
      layer = 'body';
    const inner = g.inner_radius_m;
    if (inner !== undefined && (!finite(inner) || inner < 0 || inner >= radius))
      return 'Recorded inner radius is invalid.';
    if (finite(inner) && inner > 0 && part.type !== 'nose_cone') {
      const ri = inner * 1000;
      polygons = [rectangle(x, y + ri, length, r - ri), rectangle(x, y - r, length, r - ri)];
      note += 'Source radial wall bands; holes, joints and detailed profiles are not projected.';
    } else {
      polygons = [rectangle(x, y - r, length, 2 * r)];
      note +=
        part.type === 'nose_cone'
          ? `Nose bounding envelope (${typeof g.shape === 'string' ? g.shape : 'profile unavailable'}); not the curved CAD surface.`
          : 'Source cylindrical envelope; detailed features are not projected.';
    }
  }
  const points = polygons.flat();
  return {
    part,
    layer,
    polygons,
    representation,
    note,
    bounds: [
      Math.min(...points.map(([a]) => a)),
      Math.min(...points.map(([, b]) => b)),
      Math.max(...points.map(([a]) => a)),
      Math.max(...points.map(([, b]) => b)),
    ],
  };
}

export function orthographicModel(vehicle: InspectionDocument) {
  const available: DrawingPart[] = [];
  const unavailable: { part: Part; reason: string }[] = [];
  for (const part of vehicle.parts) {
    const result = drawingPart(part);
    if (typeof result === 'string') unavailable.push({ part, reason: result });
    else available.push(result);
  }
  return { available, unavailable };
}

export function orthographicMetadata(vehicle: InspectionDocument) {
  return {
    configuration_id: vehicle.id,
    label: vehicle.label ?? vehicle.name ?? vehicle.id,
    identity: vehicle.identity ?? null,
    source_units: 'm',
    drawing_units: 'mm',
    axis: 'Axial station from source nose datum, increasing aft; vertical body-y / first lateral offset.',
    representation:
      'Source-dimensioned simplified envelopes and one radial fin planform; not a CAD projection.',
    status: vehicle.status ?? 'Engineering acceptance open',
    qualification: 'No physical qualification or flight release.',
    parts: vehicle.parts.map((part) => ({
      id: part.id,
      source: part.source ?? null,
      representation: part.representation ?? null,
    })),
    unavailable: orthographicModel(vehicle).unavailable.map(({ part, reason }) => ({
      id: part.id,
      reason,
    })),
  };
}
