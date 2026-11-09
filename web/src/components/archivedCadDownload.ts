import registry from '../../../docs/studies/frontend-desktop-detail-20261108/archived-cad-access.json' with { type: 'json' };
import type { InspectionDocument, Part } from '../types';

export const ARCHIVED_CAD_REGISTRY_SHA256 =
  'cd3cc2557c61df5f051fbc5a48002ef62678831e1639379364a19ead6398f49f';
const IDS = [
  'modular-performance-v1',
  'modular-performance-g54-hypothesis',
  'modular-tvc-finned-v1',
  'modular-tvc-finless-v1',
];
const BASE = '/engineering-workbench/archived-cad/';
export type ArchivedCadFormat = 'glb' | 'step' | 'stl';
type Configuration = (typeof registry.configurations)[number];
export interface ArchivedCadDownload {
  configurationId: string;
  partId: string | null;
  format: ArchivedCadFormat;
  url: string;
  filename: string;
  assetSha256: string;
  bytes: number;
  units: 'm' | 'mm';
  frame: string;
}
export type ArchivedCadAccess =
  | {
      available: true;
      configurationId: string;
      partId: string | null;
      label: string;
      designStatus: string;
      description: string;
      sourceRole: string;
      files: ArchivedCadDownload[];
      provenanceUrl: string;
      provenanceFilename: string;
    }
  | { available: false; reason: string };

function object(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}
function configuration(id: string): Configuration | null {
  if (!IDS.includes(id)) return null;
  return registry.configurations.find((item) => item.id === id) ?? null;
}
function sameShapes(value: unknown, expected: Record<string, string | undefined>) {
  const actual = object(value);
  return (
    actual &&
    Object.keys(actual).length === Object.keys(expected).length &&
    Object.entries(expected).every(([id, hash]) => typeof hash === 'string' && actual[id] === hash)
  );
}

/** A fixed file registry; user strings never become paths unless matched to an existing row. */
function registeredFile(
  cid: string,
  partId: string | null,
  format: string,
): ArchivedCadDownload | null {
  const entry = configuration(cid);
  if (!entry || !['glb', 'step', 'stl'].includes(format)) return null;
  const fmt = format as ArchivedCadFormat;
  const row = partId === null ? null : entry.parts.find((item) => item.id === partId);
  if (partId !== null && !row) return null;
  const asset = row ? row.assets[fmt] : entry.assemblies[fmt];
  if (!asset) return null;
  const relative = row ? `parts/${row.id}.${fmt}` : `assembly.${fmt}`;
  if (asset.path !== `build/${cid}/${relative}` || asset.format !== fmt) return null;
  const units = fmt === 'glb' ? 'm' : 'mm';
  if (asset.units !== units) return null;
  return {
    configurationId: cid,
    partId,
    format: fmt,
    url: `${BASE}${cid}/${relative}`,
    filename: `${cid}--${partId ?? 'assembly'}--recorded-${asset.sha256.slice(0, 12)}.${fmt}`,
    assetSha256: asset.sha256,
    bytes: asset.bytes,
    units,
    frame: row
      ? fmt === 'glb'
        ? row.glb_frame
        : fmt === 'step'
          ? row.step_frame
          : `STL has no encoded units; recorded producer used CAD millimetres. ${row.stl_frame}`
      : fmt === 'glb'
        ? 'Assembled viewer metres: X=cadX/1000, Y=length_m-cadZ/1000, Z=cadY/1000'
        : 'Assembled CAD millimetres; origin at nose, +Z station aft',
  };
}

/** Current exact source/document admission; byte pinning does not establish geometry readback. */
export function archivedCadAccess(
  vehicle: InspectionDocument,
  selectedPart: Part | null = null,
): ArchivedCadAccess {
  const entry = configuration(vehicle.id);
  if (!entry)
    return {
      available: false,
      reason: 'This is not one of the four registered archived CAD configurations.',
    };
  const identity = vehicle.identity;
  if (
    identity?.configuration_id !== entry.id ||
    identity.resolved_spec_sha256 !== entry.identity.resolved_spec_sha256 ||
    identity.cad_revision_sha256 !== entry.identity.cad_revision_sha256 ||
    !sameShapes(identity.part_shape_sha256, entry.identity.part_shape_sha256)
  )
    return {
      available: false,
      reason:
        'Current resolved specification/CAD/part-shape identity differs from the archived registry.',
    };
  if (
    vehicle.parts.length !== entry.parts.length ||
    new Set(vehicle.parts.map((part) => part.id)).size !== entry.parts.length ||
    vehicle.parts.some((part) => !entry.parts.some((row) => row.id === part.id))
  )
    return {
      available: false,
      reason: 'Complete part inventory differs from the registered source.',
    };
  if (selectedPart && !vehicle.parts.includes(selectedPart))
    return {
      available: false,
      reason: 'Selected part is stale or belongs to another source; select it again.',
    };
  for (const part of vehicle.parts) {
    const row = entry.parts.find((item) => item.id === part.id)!;
    const source = object(part.source),
      inputs = source?.spec_inputs;
    if (
      source?.shape_sha256 !== row.shape_sha256 ||
      source.spec_path !== entry.path ||
      object(part.representation)?.role !== row.role ||
      part.mesh_url !== `/api/vehicles/${entry.id}/meshes/${row.id}.glb` ||
      !Array.isArray(inputs) ||
      inputs.length !== Object.keys(entry.input_sha256).length ||
      new Set(inputs.map((input) => object(input)?.path)).size !== inputs.length ||
      Object.entries(entry.input_sha256).some(
        ([path, hash]) =>
          !inputs.some((input) => object(input)?.path === path && object(input)?.sha256 === hash),
      )
    )
      return {
        available: false,
        reason:
          'Part source, representation, input hashes or mesh reference differs from the registered configuration.',
      };
  }
  const partId = selectedPart?.id ?? null;
  const files = (['glb', 'step', 'stl'] as const)
    .map((format) => registeredFile(entry.id, partId, format))
    .filter((file): file is ArchivedCadDownload => file !== null);
  if (!files.length)
    return {
      available: false,
      reason: 'No registered recorded asset exists for this source part.',
    };
  return {
    available: true,
    configurationId: entry.id,
    partId,
    label: selectedPart ? (selectedPart.name ?? selectedPart.id) : 'Whole recorded assembly',
    designStatus: entry.design_status,
    description: entry.description,
    sourceRole: partId
      ? entry.parts.find((row) => row.id === partId)!.role
      : 'mixed recorded roles',
    files,
    provenanceUrl: `${BASE}${entry.id}/provenance.json`,
    provenanceFilename: `${entry.id}--${partId ?? 'assembly'}--cad-provenance.json`,
  };
}

async function checkedResponse(
  url: string,
  hash: string,
  signal: AbortSignal | undefined,
  fetcher: typeof fetch,
) {
  const response = await fetcher(url, { signal, redirect: 'error', credentials: 'same-origin' });
  if (!response.ok || response.redirected)
    throw new Error('Recorded CAD/provenance unavailable or redirected.');
  const bytes = await response.arrayBuffer();
  const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), (v) =>
    v.toString(16).padStart(2, '0'),
  ).join('');
  if (signal?.aborted) throw new DOMException('Download cancelled', 'AbortError');
  if (digest !== hash)
    throw new Error('Recorded CAD/provenance bytes differ from the registered SHA-256.');
  return bytes;
}

export async function fetchArchivedCad(
  file: ArchivedCadDownload,
  signal?: AbortSignal,
  fetcher: typeof fetch = fetch,
) {
  const registered = registeredFile(file.configurationId, file.partId, file.format);
  if (
    !registered ||
    file.url !== registered.url ||
    file.assetSha256 !== registered.assetSha256 ||
    file.filename !== registered.filename
  )
    throw new Error('Unregistered archived CAD request.');
  const bytes = await checkedResponse(registered.url, registered.assetSha256, signal, fetcher);
  if (bytes.byteLength !== registered.bytes) throw new Error('Recorded CAD byte length differs.');
  return bytes;
}
export async function fetchArchivedCadProvenance(
  access: Extract<ArchivedCadAccess, { available: true }>,
  signal?: AbortSignal,
  fetcher: typeof fetch = fetch,
) {
  if (
    !configuration(access.configurationId) ||
    access.provenanceUrl !== `${BASE}${access.configurationId}/provenance.json` ||
    !registeredFile(access.configurationId, access.partId, 'glb')
  )
    throw new Error('Unregistered archived CAD provenance request.');
  return checkedResponse(access.provenanceUrl, ARCHIVED_CAD_REGISTRY_SHA256, signal, fetcher);
}
