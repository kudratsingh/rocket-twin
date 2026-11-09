import manifest from '../../../docs/studies/rp1-inspection-geometry-20261107/manifest.json' with { type: 'json' };
import type { InspectionDocument, Part } from '../types';

export type InspectionGeometryDownload = {
  available: true;
  url: string;
  filename: string;
  assetSha256: string;
  label: string;
  maturity: string;
  provenance: Record<string, unknown>;
};
export type InspectionGeometryAccess =
  InspectionGeometryDownload | { available: false; reason: string };
const unavailable = (reason: string): InspectionGeometryAccess => ({ available: false, reason });
const identity = manifest.identity;
function object(value: unknown): Record<string, unknown> | null {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : null;
}
function registeredUrl(partId: string, hash: string) {
  return `/api/design/${manifest.id}/inspection-mesh/${partId}?spec=${identity.specification_sha256}&geometry=${identity.inspection_geometry_sha256}&mesh=${hash}`;
}
function matchesUrl(value: unknown, partId: string, hash: string) {
  if (typeof value !== 'string' || !value.startsWith('/api/') || value.includes('\\')) return false;
  try {
    const url = new URL(value, 'https://inspection.invalid');
    return (
      value.split('?')[0] === `/api/design/${manifest.id}/inspection-mesh/${partId}` &&
      url.origin === 'https://inspection.invalid' &&
      !url.hash &&
      url.pathname === `/api/design/${manifest.id}/inspection-mesh/${partId}` &&
      [...url.searchParams].length === 3 &&
      url.searchParams.getAll('spec').length === 1 &&
      url.searchParams.get('spec') === identity.specification_sha256 &&
      url.searchParams.getAll('geometry').length === 1 &&
      url.searchParams.get('geometry') === identity.inspection_geometry_sha256 &&
      url.searchParams.getAll('mesh').length === 1 &&
      url.searchParams.get('mesh') === hash
    );
  } catch {
    return false;
  }
}

/** Admit only the tracked RP1 registry and the selected object in this exact document. */
export function inspectionGeometryAccess(
  vehicle: InspectionDocument,
  selectedPart: Part | null = null,
): InspectionGeometryAccess {
  if (
    vehicle.id !== manifest.id ||
    vehicle.identity?.configuration_id !== manifest.id ||
    vehicle.identity.specification_sha256 !== identity.specification_sha256 ||
    vehicle.identity.inspection_geometry_sha256 !== identity.inspection_geometry_sha256
  )
    return unavailable(
      'Exact registered inspection configuration/specification/geometry identity is unavailable or mismatched.',
    );
  if (
    vehicle.parts.length !== manifest.parts.length ||
    new Set(vehicle.parts.map((part) => part.id)).size !== manifest.parts.length ||
    vehicle.parts.some((part) => !manifest.parts.some((row) => row.id === part.id))
  )
    return unavailable('Inspection part inventory does not match the registered source.');
  if (selectedPart && !vehicle.parts.includes(selectedPart))
    return unavailable(
      'The selected part is stale or does not belong to the displayed source. Select it again.',
    );
  const selectedRow = selectedPart
    ? manifest.parts.find((row) => row.id === selectedPart.id)
    : null;
  if (selectedPart && !selectedRow?.mesh)
    return unavailable(
      'No inspection mesh is recorded for this part; mass allowances and missing geometry have no downloadable solid.',
    );
  const checkedParts = selectedPart ? [selectedPart] : vehicle.parts;
  for (const part of checkedParts) {
    const row = manifest.parts.find((item) => item.id === part.id)!;
    if (
      object(part)?.inspection_shape_sha256 !== row.inspection_shape_sha256 ||
      object(part.representation)?.role !== row.maturity
    )
      return unavailable(
        'Part shape or representation maturity differs from the registered inspection source.',
      );
    if (row.mesh ? !matchesUrl(part.mesh_url, part.id, row.mesh.sha256) : !!part.mesh_url)
      return unavailable(
        'Inspection mesh URL or query identity is not registered for this exact part.',
      );
  }
  const partId = selectedPart?.id ?? 'assembly';
  const hash = selectedRow?.mesh?.sha256 ?? manifest.assembly.sha256;
  const url = selectedPart?.mesh_url;
  const assetUrl = selectedPart ? url! : registeredUrl('assembly', hash);
  const maturity =
    selectedRow?.maturity ??
    'mixed source_dimensioned / simplified_envelope with explicit omissions';
  const filename = `${manifest.id}--${partId}--inspection-${hash.slice(0, 12)}.glb`;
  return {
    available: true,
    url: assetUrl,
    filename,
    assetSha256: hash,
    label: selectedPart
      ? (selectedPart.name ?? selectedPart.id)
      : 'Whole recorded inspection assembly',
    maturity,
    provenance: {
      schema_version: 'rocket-twin.inspection-geometry-download.v1',
      configuration_id: manifest.id,
      part_id: selectedPart?.id ?? null,
      scope: selectedPart ? 'selected_part' : 'recorded_assembly',
      specification_sha256: identity.specification_sha256,
      inspection_geometry_sha256: identity.inspection_geometry_sha256,
      inspection_shape_sha256: selectedRow?.inspection_shape_sha256 ?? null,
      assembly_part_shape_sha256: selectedPart
        ? null
        : Object.fromEntries(manifest.parts.map((row) => [row.id, row.inspection_shape_sha256])),
      mesh_asset_sha256: hash,
      mesh_url: assetUrl,
      filename,
      units: manifest.units,
      coordinates: manifest.viewer_frame,
      origin: manifest.origin,
      source_datum: manifest.source_datum,
      maturity,
      description: selectedRow?.description ?? manifest.status,
      source_records: selectedRow
        ? { source: selectedRow.source, definition: selectedRow.definition_source }
        : manifest.sources,
      source_urls: {
        geometry_manifest: `/api/design/${manifest.id}/inspection-geometry`,
        mesh: assetUrl,
      },
      asset_verification:
        'Expected registered SHA-256; the mesh download verifies response bytes before saving. This JSON alone is not proof of a downloaded file.',
      limitations:
        'Frozen inspection GLB only. Ideal solids and simplified envelopes are not manufacturing CAD, STEP, installed fit, canonical mass/inertia or engineering/flight approval. Optional detail replacements and display transforms are not included.',
      engineering_accepted: false,
      flight_ready: false,
    },
  };
}

/** Fetch only admitted same-origin bytes; reject redirects and a changed or non-GLB response. */
export async function fetchInspectionGeometry(
  access: InspectionGeometryDownload,
  signal?: AbortSignal,
  fetcher: typeof fetch = fetch,
): Promise<ArrayBuffer> {
  const partId =
    access.provenance.part_id === null ? 'assembly' : String(access.provenance.part_id);
  const registeredHash =
    partId === 'assembly'
      ? manifest.assembly.sha256
      : manifest.parts.find((row) => row.id === partId)?.mesh?.sha256;
  if (access.assetSha256 !== registeredHash || !matchesUrl(access.url, partId, access.assetSha256))
    throw new Error('Unregistered inspection asset request.');
  const response = await fetcher(access.url, {
    signal,
    redirect: 'error',
    credentials: 'same-origin',
  });
  if (!response.ok || response.redirected)
    throw new Error('Inspection mesh response unavailable or redirected.');
  const bytes = await response.arrayBuffer();
  const digest = Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), (value) =>
    value.toString(16).padStart(2, '0'),
  ).join('');
  if (signal?.aborted) throw new DOMException('Download cancelled', 'AbortError');
  if (digest !== access.assetSha256)
    throw new Error('Inspection mesh bytes do not match the registered SHA-256.');
  if (bytes.byteLength < 12 || new DataView(bytes).getUint32(0, true) !== 0x46546c67)
    throw new Error('Registered response is not a GLB asset.');
  return bytes;
}
