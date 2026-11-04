import type { CatalogEntry, InspectionDocument, JsonValue } from '../types';

export function drawingShortcut(key: string): 'focus' | 'reset' | 'unsupported' | null {
  if (key.toLowerCase() === 'f') return 'focus';
  if (key.toLowerCase() === 'r') return 'reset';
  if (['s', 'e'].includes(key.toLowerCase())) return 'unsupported';
  return null;
}

function fingerprint(identity: Record<string, JsonValue> | undefined, keys: string[]) {
  for (const key of keys) {
    const value = identity?.[key];
    if (typeof value === 'string' && value) return value;
  }
  return null;
}

/** Never borrow a loaded source's name or CAD maturity for a different requested ID. */
export function inspectionSourceContext(
  requestedId: string,
  document: InspectionDocument | null,
  entry?: CatalogEntry,
) {
  const current = document?.id === requestedId ? document : null;
  const meshCount = current?.parts.filter((part) => !!part.mesh_url).length ?? 0;
  return {
    name:
      current?.label ||
      current?.name ||
      (entry?.id === requestedId ? entry.label : null) ||
      requestedId ||
      'Selected design source',
    maturity: !current
      ? 'Requested source not loaded; geometry identity unavailable'
      : current.snapshot_only
        ? 'Historical snapshot; geometry availability is stated per component'
        : meshCount
          ? `Recorded meshes: ${meshCount}/${current.parts.length} source components; physical qualification open`
          : 'Source dimensions available; recorded 3D geometry unavailable',
    specification: fingerprint(current?.identity, ['resolved_spec_sha256', 'specification_sha256']),
    cadRevision: fingerprint(current?.identity, ['cad_revision_sha256', 'cad_revision']),
    meshCount,
    current,
  };
}

/** Fail explicitly before an out-of-order or wrong-identity document enters inspection state. */
export function requireInspectionSource(value: InspectionDocument, requestedId: string) {
  if (!value || value.id !== requestedId || !Array.isArray(value.parts))
    throw new Error(`Inspection source identity does not match requested design ${requestedId}.`);
  if (
    value.parts.some((part) => !part || typeof part.id !== 'string') ||
    new Set(value.parts.map((part) => part.id)).size !== value.parts.length
  )
    throw new Error(`Inspection component identities are invalid for ${requestedId}.`);
  return value;
}
