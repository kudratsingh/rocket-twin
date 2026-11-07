import type { CatalogEntry, InspectionDocument, JsonValue, Part } from '../types';

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

function record(value: JsonValue | undefined) {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : null;
}

type InspectionGeometryKind =
  'source_dimensioned' | 'simplified_envelope' | 'mass_allowance' | 'missing_geometry';

/** Presentation maturity is separate from canonical CAD and physical qualification. */
export function inspectionPartRepresentation(part: Part) {
  const representation = record(part.representation);
  const role = representation?.role ?? representation?.maturity;
  const kind: InspectionGeometryKind | null =
    role === 'source_dimensioned' ||
    role === 'simplified_envelope' ||
    role === 'mass_allowance' ||
    role === 'missing_geometry'
      ? role
      : null;
  const labels = {
    source_dimensioned: 'Source-dimensioned inspection geometry · source estimates',
    simplified_envelope: 'Simplified inspection envelope · detailed geometry unavailable',
    mass_allowance: 'Mass allowance · no separate solid',
    missing_geometry: 'Geometry unavailable · no solid modeled',
  };
  return {
    kind,
    label: kind
      ? labels[kind]
      : part.mesh_url
        ? 'Recorded component mesh'
        : 'No recorded 3D mesh for this component',
    description:
      typeof representation?.description === 'string' ? representation.description : null,
  };
}

export function inspectionGeometryPresentation(document: InspectionDocument) {
  const digest = fingerprint(document.identity, ['inspection_geometry_sha256']);
  const metadata = record(document.summary.inspection_geometry);
  const sourceDerived = !!digest && !!metadata;
  const counts = {
    source_dimensioned: 0,
    simplified_envelope: 0,
    mass_allowance: 0,
    missing_geometry: 0,
  };
  for (const part of document.parts) {
    const { kind } = inspectionPartRepresentation(part);
    if (kind) counts[kind] += 1;
  }
  const meshCount = document.parts.filter((part) => !!part.mesh_url).length;
  return {
    sourceDerived,
    digest: sourceDerived ? digest : null,
    counts,
    meshCount,
    coverage: sourceDerived
      ? `${meshCount}/${document.parts.length} source records have inspection meshes; ${counts.source_dimensioned} source-dimensioned, ${counts.simplified_envelope} simplified envelopes, ${counts.mass_allowance} mass allowances without solids, ${counts.missing_geometry} missing geometry`
      : meshCount
        ? `${meshCount} recorded component meshes`
        : 'No recorded component meshes',
  };
}

/** Never borrow a loaded source's name or CAD maturity for a different requested ID. */
export function inspectionSourceContext(
  requestedId: string,
  document: InspectionDocument | null,
  entry?: CatalogEntry,
) {
  const current = document?.id === requestedId ? document : null;
  const meshCount = current?.parts.filter((part) => !!part.mesh_url).length ?? 0;
  const presentation = current ? inspectionGeometryPresentation(current) : null;
  return {
    name:
      current?.label ||
      current?.name ||
      (entry?.id === requestedId ? entry.label : null) ||
      requestedId ||
      'Selected design source',
    maturity: !current
      ? 'Requested source not loaded; geometry identity unavailable'
      : presentation?.sourceDerived
        ? `Source-derived inspection model; ${presentation.coverage}. Complete manufacturing CAD and physical qualification unavailable`
        : current.snapshot_only && !meshCount
          ? 'Source definition / concept; matching 3D geometry unavailable; estimates unverified'
          : current.snapshot_only
            ? 'Historical snapshot; geometry availability is stated per component'
            : meshCount
              ? `Recorded meshes: ${meshCount}/${current.parts.length} source components; physical qualification open`
              : 'Source dimensions available; recorded 3D geometry unavailable',
    specification: fingerprint(current?.identity, ['resolved_spec_sha256', 'specification_sha256']),
    cadRevision: fingerprint(current?.identity, ['cad_revision_sha256', 'cad_revision']),
    inspectionGeometry: presentation?.digest ?? null,
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
  if (
    inspectionGeometryPresentation(value).sourceDerived &&
    value.parts.some((part) => {
      const { kind } = inspectionPartRepresentation(part);
      return part.mesh_url && (kind === 'mass_allowance' || kind === 'missing_geometry');
    })
  )
    throw new Error(
      `Inspection allowance or missing component has an unsupported solid for ${requestedId}.`,
    );
  return value;
}
