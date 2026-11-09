import featureMap from '../../../docs/studies/frontend-component-depth-20261108/mechanical-feature-map.json';
import stepSource from '../../../docs/studies/frontend-desktop-detail-20261108/cad-export.json';
import type { InspectionDocument } from '../types';
import { FIN_ATTACHMENT_DIMENSION_IDS } from './finAttachmentState';
import type { FinAttachmentDimensionId } from './finAttachmentState';

export type FinSectionId = 'assembled' | 'longitudinal' | 'transverse';
export type BoundsM = [[number, number, number], [number, number, number]];
export type FinAsset = {
  url: string;
  sha256: string;
  bytes: number;
  bounds_m: BoundsM;
  solid_count: number;
  closed: true;
  cut_faces: { bounds_m: BoundsM; area_mm2: number }[];
  cut_edges_m: [number, number, number][][];
  cap_url: string | null;
  cap_sha256: string | null;
};
export type FinPart = {
  id: string;
  label: string;
  maturity: string;
  material: string;
  source: Record<string, unknown>;
  assets: Record<FinSectionId, FinAsset | null>;
  section_status: Record<FinSectionId, string>;
};
export type FinSection = {
  id: FinSectionId;
  label: string;
  plane_cad_mm: { normal: [number, number, number]; offset: number };
  kept_side: string;
  viewerplane: { normal: [number, number, number]; constant: number };
};
export type FinDimension = {
  id: FinAttachmentDimensionId;
  label: string;
  value_mm: number;
  tolerance_mm: number | null;
  basis: string;
  source: { path: string; sha256: string; locator: string };
  feature_ids: string[];
  points_m: [[number, number, number], [number, number, number]];
};
export type FinCatalog = {
  schema_version: 1;
  id: 'rp1-fin-attachment-inspection-v1';
  configuration_id: string;
  specification_sha256: string;
  definition_sha256: string;
  inspection_geometry_sha256: string;
  revision_sha256: string;
  frame: { units: 'm'; cad_units: 'mm'; viewer_mapping: string };
  focus_bounds_m: BoundsM;
  parts: FinPart[];
  sections: FinSection[];
  dimensions: FinDimension[];
  download: {
    url: string;
    sha256: string;
    bytes: number;
    provenance_url: string;
    provenance_sha256: string;
    units: 'mm';
    included_part_ids: string[];
  };
};

export const FIN_PART_IDS = [
  'motor_tube',
  'forward_ring',
  'aft_ring',
  'fin_set',
  'fin_tabs',
  'root_gussets',
  'body',
  'motor',
  'motor_retainer',
] as const;
const sections: FinSectionId[] = ['assembled', 'longitudinal', 'transverse'];
const cutSections: FinSectionId[] = ['longitudinal', 'transverse'];
const sha = /^[a-f0-9]{64}$/;
const assetPrefix = '/engineering-workbench/rp1-fin-attachment/';
const specSha = '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660';
const definitionSha = 'e9db49f2cafc89b1f77bf9d7396434297bc8bb8754085fdcf74d3b0242012555';
const coreSha = '238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608';
export const FIN_CATALOG_REVISION =
  '1b81037624a4a6bd59c5d2b89b053b598d1dffae56e94140d6f899d7d6506c42';
const sourceHashes = new Map([
  ['configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml', specSha],
  ['configs/studies/rp1-attachment-definition-v2.yaml', definitionSha],
  [
    'runs/wo03-rp1-attachment-definition-20261103-v2/record.json',
    'bc349a24fe1cfaa4d883b9e00dc5b75387638a7be5cd4b05d9f32112ee8bd95b',
  ],
  [
    'src/inspection/rp1_geometry.py',
    'd79db74c6285f9c45d7ffade4bb4e8e95279cf64cc7a3c4f0253c09baedf90d3',
  ],
  ['src/cad/parts.py', '911ae4a960556ebfd4aa468a99deba5fd8d755310669e30c040b155107442b98'],
  ['src/cad/assembly.py', '0288b5455cf449e9c26e7c057ac8597e3bef860f2a3c8f2cbe2be9ebf9b3a03a'],
  ['src/vehicle/geometry.py', 'dee5aec39ec6d0f5140fd449aff99bed9d887ffb30a80846fceae1c234f240e8'],
  [
    'docs/studies/frontend-desktop-detail-20261108/cad-export.json',
    'a7af1fadc431dea8958a212e2a552cf2ee833b068dbeaf51dc151d6d7fbbf731',
  ],
  [
    'scripts/wo04_fin_attachment_export.py',
    '24bfbb672b02ff88c191499c144535d6099a37c52e198f152ba54c0139d94dcd',
  ],
]);

function record(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function sameSourceValue(left: unknown, right: unknown): boolean {
  if (left === right) return true;
  if (Array.isArray(left) || Array.isArray(right))
    return (
      Array.isArray(left) &&
      Array.isArray(right) &&
      left.length === right.length &&
      left.every((value, index) => sameSourceValue(value, right[index]))
    );
  if (!record(left) || !record(right)) return false;
  const keys = Object.keys(left);
  return (
    keys.length === Object.keys(right).length &&
    keys.every((key) => Object.hasOwn(right, key) && sameSourceValue(left[key], right[key]))
  );
}

function finite(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function point(value: unknown): value is [number, number, number] {
  return Array.isArray(value) && value.length === 3 && value.every(finite);
}

function pointSpanMm(value: unknown): number | null {
  if (!Array.isArray(value) || value.length !== 2 || !point(value[0]) || !point(value[1]))
    return null;
  const first = value[0];
  const last = value[1];
  return Math.hypot(last[0] - first[0], last[1] - first[1], last[2] - first[2]) * 1000;
}

export function validBounds(value: unknown): value is BoundsM {
  return (
    Array.isArray(value) &&
    value.length === 2 &&
    point(value[0]) &&
    point(value[1]) &&
    [0, 1, 2].every((axis) => value[0][axis] <= value[1][axis])
  );
}

function sameIds(actual: unknown, expected: readonly string[]): boolean {
  return (
    Array.isArray(actual) &&
    actual.length === expected.length &&
    new Set(actual).size === expected.length &&
    actual.every((id) => expected.includes(id))
  );
}

function validAsset(value: unknown): value is FinAsset {
  if (!record(value)) return false;
  return (
    typeof value.url === 'string' &&
    value.url.startsWith(assetPrefix) &&
    /^\/engineering-workbench\/rp1-fin-attachment\/[a-z0-9_/-]+\.glb$/.test(value.url) &&
    typeof value.sha256 === 'string' &&
    sha.test(value.sha256) &&
    Number.isSafeInteger(value.bytes) &&
    Number(value.bytes) > 0 &&
    validBounds(value.bounds_m) &&
    Number.isInteger(value.solid_count) &&
    Number(value.solid_count) > 0 &&
    value.closed === true &&
    Array.isArray(value.cut_faces) &&
    value.cut_faces.every(
      (face: unknown) =>
        record(face) && validBounds(face.bounds_m) && finite(face.area_mm2) && face.area_mm2 >= 0,
    ) &&
    Array.isArray(value.cut_edges_m) &&
    value.cut_edges_m.every(
      (edge: unknown) => Array.isArray(edge) && edge.length >= 2 && edge.every(point),
    ) &&
    ((value.cut_faces as unknown[]).length === 0) === (value.cap_url === null) &&
    ((value.cap_url === null && value.cap_sha256 === null) ||
      (typeof value.cap_url === 'string' &&
        value.cap_url.startsWith(assetPrefix) &&
        /^\/engineering-workbench\/rp1-fin-attachment\/[a-z0-9_/-]+\.glb$/.test(value.cap_url) &&
        typeof value.cap_sha256 === 'string' &&
        sha.test(value.cap_sha256)))
  );
}

/** The source catalog must match the active frozen RP1 and its registered STEP records. */
export function admitFinAttachmentCatalog(
  raw: unknown,
  vehicle: InspectionDocument,
): { ok: true; catalog: FinCatalog } | { ok: false; reason: string } {
  if (
    vehicle.id !== featureMap.frozen_identity.configuration_id ||
    vehicle.identity?.specification_sha256 !== specSha ||
    vehicle.identity?.inspection_geometry_sha256 !== coreSha ||
    !sameIds(
      vehicle.parts.map((part) => part.id),
      featureMap.stable_part_ids,
    )
  )
    return { ok: false, reason: 'Current vehicle is not the frozen RP1 source.' };
  if (
    !record(raw) ||
    !record(raw.frame) ||
    !record(raw.download) ||
    !record(raw.sources) ||
    !Array.isArray(raw.parts) ||
    !Array.isArray(raw.sections) ||
    !Array.isArray(raw.dimensions)
  )
    return { ok: false, reason: 'Fin attachment catalog is malformed.' };
  const sources = raw.sources;
  if (
    raw.schema_version !== 1 ||
    raw.id !== 'rp1-fin-attachment-inspection-v1' ||
    raw.configuration_id !== vehicle.id ||
    raw.specification_sha256 !== specSha ||
    raw.definition_sha256 !== definitionSha ||
    raw.inspection_geometry_sha256 !== coreSha ||
    raw.revision_sha256 !== FIN_CATALOG_REVISION ||
    raw.frame.units !== 'm' ||
    raw.frame.cad_units !== 'mm' ||
    raw.frame.viewer_mapping !== '[cadX/1000,1.25-cadZ/1000,cadY/1000]' ||
    !validBounds(raw.focus_bounds_m) ||
    !sameIds(raw.all55_part_ids, featureMap.stable_part_ids) ||
    raw.engineering_accepted !== false ||
    raw.mass_or_inertia_generated !== false ||
    raw.canonical_vehicle_geometry_changed !== false ||
    Object.keys(sources).length !== sourceHashes.size ||
    [...sourceHashes].some(([path, hash]) => sources[path] !== hash) ||
    !sameIds(
      raw.parts.map((part: unknown) => (record(part) ? part.id : null)),
      FIN_PART_IDS,
    ) ||
    !sameIds(
      raw.sections.map((section: unknown) => (record(section) ? section.id : null)),
      cutSections,
    ) ||
    !sameIds(
      raw.dimensions.map((dimension: unknown) => (record(dimension) ? dimension.id : null)),
      FIN_ATTACHMENT_DIMENSION_IDS,
    ) ||
    !sameIds(raw.download.included_part_ids, FIN_PART_IDS)
  )
    return { ok: false, reason: 'Fin attachment source identity, revision or coverage differs.' };
  const stepParts = new Map(stepSource.parts.map((part) => [part.id, part]));
  for (const value of raw.parts) {
    if (
      !record(value) ||
      typeof value.id !== 'string' ||
      !record(value.assets) ||
      !record(value.section_status) ||
      !record(value.source)
    )
      return { ok: false, reason: 'Fin attachment part record is malformed.' };
    const assets = value.assets;
    const statuses = value.section_status;
    const step = stepParts.get(value.id);
    const current = vehicle.parts.find((part) => part.id === value.id);
    if (
      !step ||
      !current ||
      value.material !== step.material ||
      value.material !== current.material ||
      value.maturity !== step.maturity ||
      value.source.path !== step.path ||
      value.source.sha256 !== step.sha256 ||
      !sameSourceValue(value.source.specification, step.source) ||
      !sameSourceValue(value.source.definition, step.definition_source) ||
      value.source.inspection_shape_sha256 !== step.inspection_shape_sha256 ||
      typeof value.label !== 'string' ||
      !value.label ||
      sections.some(
        (section) =>
          (assets[section] !== null && !validAsset(assets[section])) ||
          typeof statuses[section] !== 'string' ||
          (assets[section] === null) !== (value.id === 'forward_ring' && section === 'transverse'),
      ) ||
      assets.assembled === null
    )
      return { ok: false, reason: `Fin attachment part differs from source: ${value.id}.` };
  }
  for (const value of raw.sections) {
    if (
      !record(value) ||
      !cutSections.includes(value.id as FinSectionId) ||
      typeof value.label !== 'string' ||
      !value.label ||
      !record(value.plane_cad_mm) ||
      !record(value.viewerplane) ||
      value.kept_side !== 'positive' ||
      (value.id === 'longitudinal' &&
        (!sameSourceValue(value.plane_cad_mm.normal, [0, 1, 0]) ||
          value.plane_cad_mm.offset !== 0 ||
          !sameSourceValue(value.viewerplane.normal, [0, 0, 1]) ||
          value.viewerplane.constant !== 0)) ||
      (value.id === 'transverse' &&
        (!sameSourceValue(value.plane_cad_mm.normal, [0, 0, 1]) ||
          value.plane_cad_mm.offset !== 1134.9 ||
          !sameSourceValue(value.viewerplane.normal, [0, -1, 0]) ||
          Math.abs(Number(value.viewerplane.constant) - 0.1151) > 1e-9))
    )
      return { ok: false, reason: 'Fin attachment section record is invalid.' };
  }
  const expectedDimensions = new Map([
    [
      'tab-thickness',
      {
        value: 6,
        tolerance: null,
        path: 'configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml',
        sha: specSha,
      },
    ],
    [
      'slot-width',
      {
        value: 6.8,
        tolerance: 0.05,
        path: 'configs/studies/rp1-attachment-definition-v2.yaml',
        sha: definitionSha,
      },
    ],
    [
      'aft-gap',
      {
        value: 0.4,
        tolerance: null,
        path: 'configs/studies/rp1-attachment-definition-v2.yaml',
        sha: definitionSha,
      },
    ],
  ]);
  for (const value of raw.dimensions) {
    const expected = record(value) ? expectedDimensions.get(String(value.id)) : undefined;
    if (
      !record(value) ||
      typeof value.id !== 'string' ||
      !value.id ||
      typeof value.label !== 'string' ||
      !finite(value.value_mm) ||
      !(value.tolerance_mm === null || finite(value.tolerance_mm)) ||
      !expected ||
      value.value_mm !== expected.value ||
      value.tolerance_mm !== expected.tolerance ||
      typeof value.basis !== 'string' ||
      !record(value.source) ||
      value.source.path !== expected.path ||
      value.source.sha256 !== expected.sha ||
      typeof value.source.locator !== 'string' ||
      !value.source.locator ||
      !Array.isArray(value.feature_ids) ||
      value.feature_ids.length === 0 ||
      !value.feature_ids.every((id: unknown) =>
        FIN_PART_IDS.includes(id as (typeof FIN_PART_IDS)[number]),
      ) ||
      pointSpanMm(value.points_m) === null ||
      Math.abs((pointSpanMm(value.points_m) ?? Infinity) - expected.value) > 1e-8
    )
      return { ok: false, reason: 'Fin attachment dimensions are not source linked.' };
  }
  const download = raw.download;
  const jointStep = stepSource.assemblies.find(
    (entry) => entry.id === 'critical_motor_fin_ring_joint',
  );
  if (
    download.url !== '/engineering-workbench/rp1-step/critical_motor_fin_ring_joint.step' ||
    download.sha256 !== jointStep?.sha256 ||
    download.bytes !== jointStep?.bytes ||
    download.provenance_url !== '/engineering-workbench/rp1-step/provenance.json' ||
    download.provenance_sha256 !==
      sources['docs/studies/frontend-desktop-detail-20261108/cad-export.json'] ||
    download.units !== 'mm'
  )
    return { ok: false, reason: 'Fin attachment CAD download is not registered.' };
  return { ok: true, catalog: raw as FinCatalog };
}

export function unionBounds(bounds: BoundsM[]): BoundsM | null {
  if (!bounds.length) return null;
  return [
    [0, 1, 2].map((axis) => Math.min(...bounds.map((bound) => bound[0][axis]))) as BoundsM[0],
    [0, 1, 2].map((axis) => Math.max(...bounds.map((bound) => bound[1][axis]))) as BoundsM[1],
  ];
}

/** Display-only outline of the source CAD cutting plane within the local joint frame. */
export function sectionPlaneOutline(
  catalog: FinCatalog,
  section: FinSectionId,
): [number, number, number][] | null {
  const plane = catalog.sections.find((item) => item.id === section)?.viewerplane;
  if (!plane) return null;
  const [low, high] = catalog.focus_bounds_m;
  if (section === 'longitudinal') {
    const z = -plane.constant / plane.normal[2];
    return [
      [low[0], low[1], z],
      [high[0], low[1], z],
      [high[0], high[1], z],
      [low[0], high[1], z],
      [low[0], low[1], z],
    ];
  }
  const y = -plane.constant / plane.normal[1];
  return [
    [low[0], y, low[2]],
    [high[0], y, low[2]],
    [high[0], y, high[2]],
    [low[0], y, high[2]],
    [low[0], y, low[2]],
  ];
}

export async function verifiedFinAssetBytes(
  url: string,
  expectedSha256: string,
  expectedBytes: number | null,
  fetcher: typeof fetch = fetch,
): Promise<ArrayBuffer> {
  if (!url.startsWith(assetPrefix))
    throw new Error('Fin CAD asset path is outside its source scope.');
  const response = await fetcher(url, { cache: 'no-store' });
  if (!response.ok) throw new Error(`Fin CAD asset unavailable (${response.status}).`);
  const bytes = await response.arrayBuffer();
  if (expectedBytes !== null && bytes.byteLength !== expectedBytes)
    throw new Error('Fin CAD asset byte count differs from its source catalog.');
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  const actual = [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('');
  if (actual !== expectedSha256)
    throw new Error('Fin CAD asset hash differs from its source catalog.');
  return bytes;
}
