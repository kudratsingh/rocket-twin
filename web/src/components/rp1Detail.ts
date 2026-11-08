import type { InspectionDocument, Vector3Tuple } from '../types';

export const RP1_DETAIL_MANIFEST_URL = '/engineering-workbench/rp1-detail/manifest.json';
export const RP1_DETAIL_MANIFEST_SHA256 =
  'b3ac3cc62294676d5614eab048bab7111320f61eecaa002a85a7d1469b6e8ac6';
export const RP1_DETAIL_REVISION =
  'e4ff19fec90e36d2a97987387572749cf3e11449312d09b3cf7e1c8d15016238';
const ID = 'rp1-ad1-optional-source-detail-v1';
const CONFIGURATION = 'G80-F2-RP1-AD1-definition-v2';
const SPEC = '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
const GEOMETRY = '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608';
const PARTS = ['forward_ring', 'motor_tube', 'aft_ring'];
const CASES = ['forward-ring-recovery', 'motor-support-retention', 'avionics-envelope'];
type ObjectValue = Record<string, unknown>;
export interface Rp1DetailCase {
  id: string;
  label: string;
  partIds: string[];
  replacementPartIds: string[];
  supportedFeatures: string[];
  missing: string[];
}
export interface Rp1DetailAnnotation {
  id: string;
  partId: string;
  label: string;
  value: number;
  units: 'mm';
  from: Vector3Tuple;
  to: Vector3Tuple;
  source: { path: string; sha256: string; locator: string };
  annotationOnly: true;
}
export interface Rp1DetailView {
  id: string;
  detailSha256: string;
  detailMeshes: Record<string, string>;
  cases: Rp1DetailCase[];
  annotations: Rp1DetailAnnotation[];
  missingNotes: string[];
}
function object(value: unknown): ObjectValue | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as ObjectValue)
    : null;
}
function hash(value: unknown): value is string {
  return typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
}
function strings(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((v) => typeof v === 'string');
}
function vector(value: unknown): value is Vector3Tuple {
  return (
    Array.isArray(value) &&
    value.length === 3 &&
    value.every((v) => typeof v === 'number' && Number.isFinite(v) && Math.abs(v) < 5)
  );
}
function active(document: InspectionDocument) {
  return (
    document.id === CONFIGURATION &&
    document.identity?.specification_sha256 === SPEC &&
    document.identity.inspection_geometry_sha256 === GEOMETRY &&
    document.parts.length === 55 &&
    new Set(document.parts.map((p) => p.id)).size === 55
  );
}

/** Pure admission of an optional presentation packet; original source mesh URLs stay untouched. */
export function validateRp1Detail(
  document: InspectionDocument,
  value: unknown,
): Rp1DetailView | null {
  if (!active(document)) return null;
  const packet = object(value),
    tuple = object(packet?.source_tuple);
  if (
    !packet ||
    packet.id !== ID ||
    packet.schema_version !== 1 ||
    packet.detail_sha256 !== RP1_DETAIL_REVISION ||
    tuple?.configuration_id !== CONFIGURATION ||
    tuple.specification_sha256 !== SPEC ||
    tuple.inspection_geometry_sha256 !== GEOMETRY ||
    packet.core_source_records !== 55 ||
    packet.core_mesh_records !== 26 ||
    packet.mass_or_inertia_generated !== false ||
    packet.engineering_accepted !== false ||
    packet.manufacturing_clearance !== false ||
    !Array.isArray(packet.parts) ||
    packet.parts.length !== 3 ||
    !Array.isArray(packet.cases) ||
    packet.cases.length !== 3 ||
    !Array.isArray(packet.annotations)
  )
    return null;
  const detailMeshes: Record<string, string> = {};
  for (const raw of packet.parts) {
    const row = object(raw),
      pid = row?.part_id;
    if (
      !row ||
      typeof pid !== 'string' ||
      !PARTS.includes(pid) ||
      pid in detailMeshes ||
      !hash(row.asset_sha256) ||
      !hash(row.core_mesh_sha256) ||
      !hash(row.inspection_shape_sha256) ||
      row.display_only !== true ||
      row.asset_path !== `/engineering-workbench/rp1-detail/parts/${pid}.glb`
    )
      return null;
    const part = document.parts.find((p) => p.id === pid);
    if (
      !part?.mesh_url ||
      (part as unknown as ObjectValue).inspection_shape_sha256 !== row.inspection_shape_sha256 ||
      object(part.representation)?.role !== row.maturity
    )
      return null;
    try {
      const url = new URL(part.mesh_url, 'http://inspection.invalid');
      if (
        url.pathname !== `/api/design/${CONFIGURATION}/inspection-mesh/${pid}` ||
        url.searchParams.get('spec') !== SPEC ||
        url.searchParams.get('geometry') !== GEOMETRY ||
        url.searchParams.get('mesh') !== row.core_mesh_sha256
      )
        return null;
    } catch {
      return null;
    }
    detailMeshes[pid] = `${row.asset_path}?sha=${row.asset_sha256}`;
  }
  const cases: Rp1DetailCase[] = [];
  for (const [index, raw] of packet.cases.entries()) {
    const row = object(raw);
    if (
      !row ||
      row.id !== CASES[index] ||
      typeof row.label !== 'string' ||
      !strings(row.part_ids) ||
      !strings(row.replacement_part_ids) ||
      !strings(row.supported_features) ||
      !strings(row.missing) ||
      !row.part_ids.every((id) => document.parts.some((p) => p.id === id)) ||
      !row.replacement_part_ids.every((id) => id in detailMeshes)
    )
      return null;
    cases.push({
      id: row.id,
      label: row.label,
      partIds: row.part_ids,
      replacementPartIds: row.replacement_part_ids,
      supportedFeatures: row.supported_features,
      missing: row.missing,
    });
  }
  const annotations: Rp1DetailAnnotation[] = [];
  const sources = object(packet.sources);
  if (!sources) return null;
  for (const raw of packet.annotations) {
    const row = object(raw),
      source = object(row?.source);
    if (
      !row ||
      typeof row.id !== 'string' ||
      typeof row.part_id !== 'string' ||
      !document.parts.some((p) => p.id === row.part_id) ||
      typeof row.label !== 'string' ||
      typeof row.value !== 'number' ||
      !Number.isFinite(row.value) ||
      row.value <= 0 ||
      row.units !== 'mm' ||
      row.annotation_only !== true ||
      row.contributes_geometry_bounds !== false ||
      !vector(row.from_m) ||
      !vector(row.to_m) ||
      !source ||
      typeof source.path !== 'string' ||
      !hash(source.sha256) ||
      sources[source.path] !== source.sha256 ||
      typeof source.locator !== 'string'
    )
      return null;
    annotations.push({
      id: row.id,
      partId: row.part_id,
      label: row.label,
      value: row.value,
      units: 'mm',
      from: row.from_m,
      to: row.to_m,
      source: { path: source.path, sha256: source.sha256, locator: source.locator },
      annotationOnly: true,
    });
  }
  return {
    id: ID,
    detailSha256: RP1_DETAIL_REVISION,
    detailMeshes,
    cases,
    annotations,
    missingNotes: cases.flatMap((c) => c.missing),
  };
}

/** Optional same-origin load; verify all three GLB bytes before admitting replacement URLs. */
export async function loadRp1Detail(
  document: InspectionDocument,
  signal?: AbortSignal,
): Promise<Rp1DetailView | null> {
  if (!active(document) || signal?.aborted) return null;
  try {
    const response = await fetch(RP1_DETAIL_MANIFEST_URL, { signal });
    if (!response.ok) return null;
    const manifestText = await response.text();
    const manifestHash = Array.from(
      new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(manifestText))),
      (v) => v.toString(16).padStart(2, '0'),
    ).join('');
    if (manifestHash !== RP1_DETAIL_MANIFEST_SHA256) return null;
    const admitted = validateRp1Detail(document, JSON.parse(manifestText));
    if (!admitted || signal?.aborted) return null;
    for (const url of Object.values(admitted.detailMeshes)) {
      const expected = new URL(url, 'http://inspection.invalid').searchParams.get('sha');
      const asset = await fetch(url, { signal });
      if (!asset.ok) return null;
      const actual = Array.from(
        new Uint8Array(await crypto.subtle.digest('SHA-256', await asset.arrayBuffer())),
        (v) => v.toString(16).padStart(2, '0'),
      ).join('');
      if (actual !== expected || signal?.aborted) return null;
    }
    return admitted;
  } catch {
    return null;
  }
}
