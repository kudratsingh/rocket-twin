import manifest from '../../../docs/studies/frontend-template-bank-20261109/geometry.json';
import { admitReferenceDefinition, type ReferenceDefinition } from './referenceDatumGeometry';
import type { TemplateRepresentation } from './templateGeometry';

export const REFERENCE_PARTS_API = '/api/reference-parts';
export const REFERENCE_CATALOG_ID = 'reference-local-v1';
export const REFERENCE_CATALOG_REVISION =
  '8f6b7bf2f0dcc8dfb2714ba7a28688c820869dc3045060aba6ea5901983b7748';
export interface ReferencePartIdentity {
  referenceId: string;
  revision: string;
  templateId: string;
  templateRevision: string;
}
// Exact source DTO revisions; the original template identity is independently
// matched against the existing frozen geometry manifest before choosing a URL.
const identities: readonly ReferencePartIdentity[] = [
  {
    referenceId: 'reference-local-v1:motor-tube-nominal',
    revision: 'fd6c666dfed5d79ed44ed126b85d1de7dca87c1210165808b44f270e2ce2a42c',
    templateId: 'rp1-template:motor-tube-cut',
    templateRevision: '7f3d7dd2ce09293d787aac7343138c1f8a9a44f40f07ff63f4c58d0eae5690e3',
  },
  {
    referenceId: 'reference-local-v1:aft-annulus-nominal',
    revision: '158150615a9c291ce12b3320d535c11151a564d7ad176dda9ca9693025a5d710',
    templateId: 'rp1-template:aft-annular-ring',
    templateRevision: 'f720488a173d91f936666c160e0bc9c912eb4bb0e2a5b18e188857d40637db8e',
  },
];
export type ReferenceAvailability = {
  status: 'verified_registered_local_cache' | 'unavailable';
  missing_formats: ('step' | 'glb')[];
  geometry_available: boolean;
  public_url_cache_verified: false;
  generation_attempted: false;
  reason: string;
};
export interface ReferencePartDetail {
  definition: ReferenceDefinition;
  availability: ReferenceAvailability;
  action: 'inspect_geometry_reference';
  instance_created: false;
  engineering_accepted: false;
  simulation_eligible: false;
  flight_ready: false;
  catalog_id: typeof REFERENCE_CATALOG_ID;
  catalog_revision_sha256: typeof REFERENCE_CATALOG_REVISION;
  scope: 'geometry_only_planning';
}
export class ReferencePartsServiceError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly currentRevision: string | null = null,
  ) {
    super(message);
    this.name = 'ReferencePartsServiceError';
  }
}
function object(raw: unknown): raw is Record<string, unknown> {
  return raw !== null && typeof raw === 'object' && !Array.isArray(raw);
}
function same(left: unknown, right: unknown): boolean {
  if (left === right) return true;
  if (Array.isArray(left) || Array.isArray(right))
    return (
      Array.isArray(left) &&
      Array.isArray(right) &&
      left.length === right.length &&
      left.every((value, index) => same(value, right[index]))
    );
  return (
    object(left) &&
    object(right) &&
    Object.keys(left).length === Object.keys(right).length &&
    Object.keys(left).every((key) => Object.hasOwn(right, key) && same(left[key], right[key]))
  );
}
export function referencePartForTemplate(templateId: string): ReferencePartIdentity | null {
  const identity = identities.find((row) => row.templateId === templateId);
  const representation = manifest.representations.find((row) => row.template_id === templateId);
  if (
    !identity ||
    !representation ||
    manifest.schema_version !== 1 ||
    manifest.id !== 'rp1-template-geometry-v1' ||
    manifest.configuration_id !== 'G80-F2-RP1-AD1-definition-v2' ||
    manifest.specification_sha256 !==
      '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660' ||
    manifest.registry.revision_sha256 !==
      'cb43e923df940ba0a1f9ec80216a194bd1cbc85e92b1eac5c77f3e18b55fd9be' ||
    representation.template_revision_sha256 !== identity.templateRevision ||
    representation.representation_status !== 'source_nominal_local_only'
  )
    return null;
  return { ...identity };
}
function matchesRepresentation(
  representation: TemplateRepresentation,
  identity: ReferencePartIdentity,
  definition?: ReferenceDefinition,
): boolean {
  if (!object(representation)) return false;
  const expected = manifest.representations.find((row) => row.template_id === identity.templateId)!;
  return (
    representation.template_id === identity.templateId &&
    representation.template_revision_sha256 === identity.templateRevision &&
    representation.representation_status === 'source_nominal_local_only' &&
    same(representation.bounds_m, expected.bounds_m) &&
    (['step', 'glb'] as const).every((format) => {
      const asset = representation[format];
      const registered = definition?.representation.assets[format] ?? expected[format];
      return (
        object(asset) &&
        asset.url === registered.url &&
        asset.sha256 === registered.sha256 &&
        asset.bytes === registered.bytes
      );
    })
  );
}
function validAvailability(raw: unknown): raw is ReferenceAvailability {
  if (!object(raw) || !Array.isArray(raw.missing_formats)) return false;
  const missing = raw.missing_formats;
  if (
    missing.length > 2 ||
    !same(
      missing,
      ['step', 'glb'].filter((format) => missing.includes(format)),
    )
  )
    return false;
  return same(raw, {
    status: missing.length ? 'unavailable' : 'verified_registered_local_cache',
    missing_formats: missing,
    geometry_available: missing.length === 0,
    public_url_cache_verified: false,
    generation_attempted: false,
    reason: missing.length
      ? 'Required local cache absent; no regeneration'
      : 'Exact existing STEP/GLB bytes verified; no new CAD readback or physical acceptance',
  });
}
/** Admit a live response; availability never proves public URL or asset-byte access. */
export function admitReferencePartDetail(
  raw: unknown,
  templateId: string,
  representation?: TemplateRepresentation,
): ReferencePartDetail {
  const identity = referencePartForTemplate(templateId);
  const definition = object(raw) ? admitReferenceDefinition(raw.definition) : null;
  if (
    !identity ||
    !object(raw) ||
    !definition ||
    definition.id !== identity.referenceId ||
    definition.revision_sha256 !== identity.revision ||
    definition.source_template_id !== identity.templateId ||
    definition.source_template_revision_sha256 !== identity.templateRevision ||
    !validAvailability(raw.availability) ||
    (representation !== undefined &&
      !matchesRepresentation(representation, identity, definition)) ||
    !same(raw, {
      definition,
      availability: raw.availability,
      action: 'inspect_geometry_reference',
      instance_created: false,
      engineering_accepted: false,
      simulation_eligible: false,
      flight_ready: false,
      catalog_id: REFERENCE_CATALOG_ID,
      catalog_revision_sha256: REFERENCE_CATALOG_REVISION,
      scope: 'geometry_only_planning',
    })
  )
    throw new ReferencePartsServiceError(
      200,
      'invalid_response',
      'Reference detail source, identity, frame, availability or gates differ; no reference was admitted.',
    );
  return raw as unknown as ReferencePartDetail;
}
const messages: Record<string, string> = {
  reference_not_found:
    'That registered reference is unavailable. Reload source reference details explicitly.',
  reference_revision_mismatch:
    'The reference revision differs. Reload source reference details explicitly; no alternate revision was loaded.',
  reference_source_unavailable:
    'Pinned reference source, frame or registered cache could not be verified. No regeneration or substitute was attempted.',
  origin_forbidden: 'The local preview origin is not permitted to inspect reference details.',
  invalid_request: 'The reference detail request was rejected. No reference was admitted.',
};
function checkAbort(signal?: AbortSignal): void {
  if (signal?.aborted) throw new DOMException('Reference inspection was cancelled.', 'AbortError');
}
/** Constructing this client does no I/O. Only readForTemplate performs one GET. */
export function createReferencePartsClient(fetcher: typeof fetch = fetch) {
  return {
    async readForTemplate(
      templateId: string,
      representation?: TemplateRepresentation,
      signal?: AbortSignal,
    ): Promise<ReferencePartDetail> {
      checkAbort(signal);
      const identity = referencePartForTemplate(templateId);
      if (
        !identity ||
        (representation !== undefined && !matchesRepresentation(representation, identity))
      )
        throw new ReferencePartsServiceError(
          0,
          'invalid_request',
          'Choose one exact registered local template and its matching representation.',
        );
      let response: Response;
      try {
        response = await fetcher(
          `${REFERENCE_PARTS_API}/${identity.referenceId}/${identity.revision}`,
          {
            method: 'GET',
            signal,
            cache: 'no-store',
            headers: { Accept: 'application/json' },
          },
        );
      } catch {
        checkAbort(signal);
        throw new ReferencePartsServiceError(
          0,
          'transport_unavailable',
          'Reference detail service could not be reached. No reference was admitted.',
        );
      }
      checkAbort(signal);
      let raw: unknown;
      try {
        raw = await response.json();
      } catch {
        checkAbort(signal);
        if (response.status !== 404)
          throw new ReferencePartsServiceError(
            response.status,
            'invalid_response',
            'Reference detail service returned unreadable data. No reference was admitted.',
          );
      }
      checkAbort(signal);
      if (!response.ok) {
        const detail = object(raw) && object(raw.detail) ? raw.detail : null;
        if (response.status === 404 && detail?.code !== 'reference_not_found')
          throw new ReferencePartsServiceError(
            404,
            'route_unavailable',
            'Reference detail API is unavailable (404). Restart the normal-host backend with the reference router enabled. No prepared fallback is available.',
          );
        const code =
          typeof detail?.code === 'string' && Object.hasOwn(messages, detail.code)
            ? detail.code
            : 'reference_error';
        const revision =
          typeof detail?.current_revision === 'string' &&
          /^[a-f0-9]{64}$/.test(detail.current_revision)
            ? detail.current_revision
            : null;
        if (
          code === 'reference_revision_mismatch' &&
          (response.status !== 409 || revision === null)
        )
          throw new ReferencePartsServiceError(
            response.status,
            'invalid_response',
            'Reference revision error was malformed. Reload source details explicitly.',
          );
        throw new ReferencePartsServiceError(
          response.status,
          code,
          messages[code] ?? 'Reference detail request failed. No reference was admitted.',
          revision,
        );
      }
      return admitReferencePartDetail(raw, templateId, representation);
    },
  };
}
