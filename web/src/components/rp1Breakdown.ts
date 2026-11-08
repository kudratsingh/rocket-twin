import type { InspectionDocument, Vector3Tuple } from '../types';

export const RP1_PRESENTATION_ID = 'rp1-ad1-v2-functional-presentation-v1';
export const RP1_PRESENTATION_SHA256 =
  '4ed997e371f8b2473d9da47aee7396562cb9b4d7e031d87f9876025b136c005b';
const RP1_ID = 'G80-F2-RP1-AD1-definition-v2';
const SPEC = '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
const GEOMETRY = '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608';
const GROUPS = [
  'nose_airframe',
  'fins_roots',
  'motor_retention',
  'recovery',
  'avionics_power',
  'launch_finish',
];
type ObjectValue = Record<string, unknown>;
export interface Rp1PresentationGroup {
  id: string;
  label: string;
  part_ids: string[];
  record_count: number;
  mesh_count: number;
}
export interface Rp1Presentation {
  id: string;
  presentation_sha256: string;
  groups: Rp1PresentationGroup[];
  source_tuple: ObjectValue;
}
function object(value: unknown): ObjectValue | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as ObjectValue)
    : null;
}
function tuple(value: unknown) {
  const v = object(value);
  return (
    v?.configuration_id === RP1_ID &&
    v.specification_sha256 === SPEC &&
    v.inspection_geometry_sha256 === GEOMETRY
  );
}
function vector(value: unknown): value is Vector3Tuple {
  return (
    Array.isArray(value) &&
    value.length === 3 &&
    value.every((v) => typeof v === 'number' && Number.isFinite(v) && Math.abs(v) <= 1)
  );
}
function hash(value: unknown): value is string {
  return typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
}

/** Display metadata is admitted only against the active exact RP1 source/geometry tuple. */
export function getRp1Presentation(document: InspectionDocument): Rp1Presentation | null {
  if (
    document.id !== RP1_ID ||
    document.identity?.specification_sha256 !== SPEC ||
    document.identity.inspection_geometry_sha256 !== GEOMETRY
  )
    return null;
  const p = object(document.summary.presentation);
  if (
    !p ||
    p.id !== RP1_PRESENTATION_ID ||
    p.schema_version !== 1 ||
    p.geometry_compatible !== true ||
    p.presentation_sha256 !== RP1_PRESENTATION_SHA256 ||
    !tuple(p.source_tuple)
  )
    return null;
  const breakdown = object(p.breakdown);
  if (
    breakdown?.kind !== 'staged-display-illustration' ||
    breakdown.assembly_stage_end !== 0.5 ||
    breakdown.manufacturing_clearance !== false ||
    breakdown.units !== 'm'
  )
    return null;
  if (!Array.isArray(p.groups) || p.groups.length !== 6 || document.parts.length !== 55)
    return null;
  const sourceIds = new Set(document.parts.map((part) => part.id));
  if (sourceIds.size !== 55) return null;
  const assigned = new Set<string>();
  for (const [index, raw] of p.groups.entries()) {
    const group = object(raw);
    if (
      !group ||
      group.id !== GROUPS[index] ||
      typeof group.label !== 'string' ||
      !Array.isArray(group.part_ids) ||
      group.record_count !== group.part_ids.length ||
      !Number.isInteger(group.mesh_count) ||
      Number(group.mesh_count) < 0 ||
      Number(group.mesh_count) > group.part_ids.length
    )
      return null;
    for (const id of group.part_ids) {
      if (typeof id !== 'string' || !sourceIds.has(id) || assigned.has(id)) return null;
      assigned.add(id);
    }
  }
  return assigned.size === 55 ? (p as unknown as Rp1Presentation) : null;
}

/** Final viewer-metre translation, shared by drawing, picking and actual-mesh framing.
 * null means another design uses its own existing display convention. Invalid RP1
 * metadata, meshless evidence and foreign IDs stay at zero; no inferred fallback.
 * The first half separates groups; the second half opens only the chosen group.
 * This is a display illustration, never a collision-free manufacturing sequence.
 */
export function rp1BreakdownOffset(
  document: InspectionDocument,
  partId: string,
  separation01: number,
  openedGroupId: string | null,
): Vector3Tuple | null {
  if (document.id !== RP1_ID) return null;
  const zero: Vector3Tuple = [0, 0, 0];
  if (!Number.isFinite(separation01) || separation01 <= 0) return zero;
  const presentation = getRp1Presentation(document);
  if (
    !presentation ||
    (openedGroupId !== null && !presentation.groups.some((g) => g.id === openedGroupId))
  )
    return zero;
  const part = document.parts.find((p) => p.id === partId);
  if (!part || !part.mesh_url) return zero;
  const metadata = object(object(part.representation)?.presentation);
  const rawPart = part as unknown as ObjectValue;
  if (
    !metadata ||
    metadata.id !== partId ||
    !tuple(metadata.source_tuple) ||
    metadata.presentation_sha256 !== presentation.presentation_sha256 ||
    metadata.source_parent !== part.parent ||
    metadata.has_mesh !== true ||
    !hash(metadata.inspection_shape_sha256) ||
    metadata.inspection_shape_sha256 !== rawPart.inspection_shape_sha256 ||
    !hash(metadata.mesh_sha256) ||
    !vector(metadata.assembly_offset_m) ||
    !vector(metadata.detail_offset_m)
  )
    return zero;
  const group = presentation.groups.find(
    (g) => g.id === metadata.group_id && g.part_ids.includes(partId),
  );
  if (!group) return zero;
  try {
    const url = new URL(part.mesh_url, 'http://inspection.invalid');
    if (
      url.pathname !== `/api/design/${RP1_ID}/inspection-mesh/${partId}` ||
      url.searchParams.get('spec') !== SPEC ||
      url.searchParams.get('geometry') !== GEOMETRY ||
      url.searchParams.get('mesh') !== metadata.mesh_sha256
    )
      return zero;
  } catch {
    return zero;
  }
  const amount = Math.min(separation01, 1);
  const assembly = Math.min(amount / 0.5, 1);
  const detail = openedGroupId === group.id ? Math.max((amount - 0.5) / 0.5, 0) : 0;
  return metadata.assembly_offset_m.map(
    (value, index) => value * assembly + (metadata.detail_offset_m as Vector3Tuple)[index] * detail,
  ) as Vector3Tuple;
}
