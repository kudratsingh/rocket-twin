import type { InspectionDocument } from '../types';
import featureMap from '../../../docs/studies/frontend-component-depth-20261108/mechanical-feature-map.json';
import {
  admitPartsBank,
  RP1_BANK_CONFIGURATION,
  RP1_BANK_SPEC,
  RP1_BANK_DEFINITION,
  RP1_BANK_RECORD,
  RP1_BANK_GEOMETRY,
} from '../parts-bank/partsBank';
import type { PartsBankCatalog } from '../parts-bank/partsBank';

export const DRAFT_API = '/api/design-drafts';
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const sha = /^[0-9a-f]{64}$/;
// Exact snapshots produced by the frozen store from source-only inputs and the
// admitted 26-mesh cache respectively. These are admission pins, never fallback data.
const sourceSnapshots = new Map([
  [
    '7f04cbeb5d4c2aa96a61fac41a1f2b0f1f52ad54e68c9dd3856f7363f52ded44',
    'bd69971e461251b843e24b4f2ec93c8d56e693bcbfa2d121697399a4510761cc',
  ],
  [
    '754cc2ae24c3d3f20e53bc919457f5b09f3982d7fc4cf7610dea72d4c2368fd1',
    '7508b1f4361d3bada13ad23d11f6e997cda4aa3a476d33d847898425b2367e36',
  ],
]);
const sourceRefs = new Map([
  ['configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml', RP1_BANK_SPEC],
  ['configs/studies/rp1-attachment-definition-v2.yaml', RP1_BANK_DEFINITION],
  ['runs/wo03-rp1-attachment-definition-20261103-v2/record.json', RP1_BANK_RECORD],
]);
const readiness = {
  status: 'unresolved_source_fork',
  resolved_candidate: false,
  simulation_eligible: false,
  engineering_accepted: false,
  flight_ready: false,
  blockers: [
    'Source fork only; no candidate resolver or simulation admission is implemented',
    'Whole-body physical inertia and complete installed geometry are unavailable',
    'Source product conflicts, estimates and missing geometry remain unresolved',
    'Installed fin, recovery, thermal, physical, WO-10 and flight gates remain open',
  ],
} as const;

export interface DraftSummary {
  draft_id: string;
  revision_sha256: string;
  label: string;
  sequence: number;
  created_at: string;
  readiness: typeof readiness;
}
export interface DraftRevision extends DraftSummary {
  schema_version: 1;
  source_sha256: string;
  base_configuration_id: typeof RP1_BANK_CONFIGURATION;
  parent_revision_sha256: string | null;
  notes: string;
  operation: 'fork_rp1' | 'save_metadata';
  capabilities: { save_metadata: true; compose: false; resolve: false };
  source: {
    configuration_id: string;
    source_refs: { path: string; sha256: string }[];
    parts_bank_revision_sha256: string;
    parts_bank: PartsBankCatalog;
    specification: Record<string, unknown>;
    inspection: Record<string, unknown>;
    accounting_policy: string;
  };
}
export interface DraftPage {
  drafts: DraftSummary[];
  next_after: string | null;
}
export interface DraftEditor {
  snapshot: DraftRevision;
  label: string;
  notes: string;
  conflict: string | null;
}

export class DraftServiceError extends Error {
  readonly status: number;
  readonly code: string;
  readonly currentRevision: string | null;
  constructor(
    status: number,
    code: string,
    message: string,
    currentRevision: string | null = null,
  ) {
    super(message);
    this.name = 'DraftServiceError';
    this.status = status;
    this.code = code;
    this.currentRevision = currentRevision;
  }
}
function object(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
function canonical(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(canonical).join(',')}]`;
  if (object(value))
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`)
      .join(',')}}`;
  return JSON.stringify(value);
}
function same(left: unknown, right: unknown): boolean {
  return canonical(left) === canonical(right);
}
function exactKeys(value: Record<string, unknown>, keys: string[]): boolean {
  return same(Object.keys(value).sort(), keys.sort());
}
function validText(value: unknown, max: number, required = false): value is string {
  return (
    typeof value === 'string' &&
    value.length <= max &&
    (!required || value.trim().length > 0) &&
    Array.from(value).every(
      (letter) => letter.charCodeAt(0) >= 32 || letter === '\n' || letter === '\t',
    )
  );
}
function validSummary(value: unknown): value is DraftSummary {
  return (
    object(value) &&
    typeof value.draft_id === 'string' &&
    uuid.test(value.draft_id) &&
    typeof value.revision_sha256 === 'string' &&
    sha.test(value.revision_sha256) &&
    validText(value.label, 160, true) &&
    Number.isInteger(value.sequence) &&
    Number(value.sequence) >= 1 &&
    Number(value.sequence) <= 1000 &&
    typeof value.created_at === 'string' &&
    Number.isFinite(Date.parse(value.created_at)) &&
    same(value.readiness, readiness)
  );
}
export function matchesDraftSource(vehicle: InspectionDocument): boolean {
  const ids = vehicle.parts.map((p) => p.id);
  return (
    vehicle.id === RP1_BANK_CONFIGURATION &&
    vehicle.identity?.specification_sha256 === RP1_BANK_SPEC &&
    vehicle.identity?.inspection_geometry_sha256 === RP1_BANK_GEOMETRY &&
    ids.length === 55 &&
    new Set(ids).size === 55 &&
    same([...ids].sort(), [...featureMap.stable_part_ids].sort())
  );
}
export function admitDraftPage(raw: unknown): DraftPage {
  if (
    !object(raw) ||
    !exactKeys(raw, ['drafts', 'next_after']) ||
    !Array.isArray(raw.drafts) ||
    raw.drafts.length > 100 ||
    !raw.drafts.every(
      (row) =>
        validSummary(row) &&
        exactKeys(row as unknown as Record<string, unknown>, [
          'draft_id',
          'revision_sha256',
          'label',
          'sequence',
          'created_at',
          'readiness',
        ]),
    ) ||
    !(raw.next_after === null || (typeof raw.next_after === 'string' && uuid.test(raw.next_after)))
  )
    throw new Error('Draft list identity or readiness differs; no entries admitted.');
  const rows = raw.drafts as DraftSummary[];
  const ids = rows.map((row) => row.draft_id);
  if (
    new Set(ids).size !== rows.length ||
    !same(ids, [...ids].sort()) ||
    (raw.next_after !== null && (rows.length === 0 || raw.next_after !== ids.at(-1)))
  )
    throw new Error('Draft list cursor or ordering differs; no entries admitted.');
  return raw as unknown as DraftPage;
}
export async function admitDraftRevision(
  raw: unknown,
  vehicle: InspectionDocument,
  expectedId?: string,
  expectedRevision?: string,
): Promise<DraftRevision> {
  if (
    !matchesDraftSource(vehicle) ||
    !object(raw) ||
    !validSummary(raw) ||
    !exactKeys(raw as unknown as Record<string, unknown>, [
      'schema_version',
      'draft_id',
      'source_sha256',
      'base_configuration_id',
      'parent_revision_sha256',
      'sequence',
      'created_at',
      'label',
      'notes',
      'operation',
      'readiness',
      'capabilities',
      'revision_sha256',
      'source',
    ])
  )
    throw new Error('Draft source, identity or readiness differs; snapshot unavailable.');
  const row = raw as unknown as DraftRevision;
  if (
    row.schema_version !== 1 ||
    row.base_configuration_id !== RP1_BANK_CONFIGURATION ||
    !validText(row.notes, 8000) ||
    !sourceSnapshots.has(row.source_sha256) ||
    (expectedId !== undefined && row.draft_id !== expectedId) ||
    (expectedRevision !== undefined && row.revision_sha256 !== expectedRevision) ||
    !same(row.capabilities, { save_metadata: true, compose: false, resolve: false }) ||
    (row.sequence === 1
      ? row.parent_revision_sha256 !== null || row.operation !== 'fork_rp1'
      : typeof row.parent_revision_sha256 !== 'string' ||
        !sha.test(row.parent_revision_sha256) ||
        row.operation !== 'save_metadata')
  )
    throw new Error('Draft revision lineage or supported capabilities differ.');
  const source = row.source;
  if (
    !object(source) ||
    source.configuration_id !== RP1_BANK_CONFIGURATION ||
    !Array.isArray(source.source_refs) ||
    source.source_refs.length !== 3 ||
    new Set(source.source_refs.map((r) => (object(r) ? r.path : null))).size !== 3 ||
    source.source_refs.some((ref) => !object(ref) || sourceRefs.get(ref.path) !== ref.sha256) ||
    source.parts_bank_revision_sha256 !== sourceSnapshots.get(row.source_sha256) ||
    !object(source.specification) ||
    source.specification.id !== RP1_BANK_CONFIGURATION ||
    !Array.isArray(source.specification.parts) ||
    source.specification.parts.length !== 55 ||
    !object(source.inspection) ||
    source.inspection.id !== RP1_BANK_CONFIGURATION ||
    !Array.isArray(source.inspection.parts) ||
    source.inspection.parts.length !== 55 ||
    !object(source.inspection.summary) ||
    source.inspection.summary.flight_ready !== false ||
    source.inspection.summary.engineering_acceptance !== 'open' ||
    source.inspection.summary.inertia_status !== 'unavailable'
  )
    throw new Error('Draft frozen source references, inventory or missingness differ.');
  const bank = admitPartsBank(source.parts_bank, vehicle);
  if (!bank.ok || bank.catalog.revision_sha256 !== source.parts_bank_revision_sha256)
    throw new Error('Draft does not preserve the exact 55 source accounting occurrences.');
  const expectedIds = bank.catalog.instances.map((instance) => instance.id).sort();
  for (const parts of [source.specification.parts, source.inspection.parts]) {
    if (
      !parts.every((p) => object(p) && typeof p.id === 'string') ||
      !same(parts.map((p) => p.id).sort(), expectedIds)
    )
      throw new Error('Draft source inventory coverage differs.');
  }
  const unsigned = Object.fromEntries(
    Object.entries(row).filter(([key]) => key !== 'source' && key !== 'revision_sha256'),
  );
  const bytes = new TextEncoder().encode(canonical(unsigned));
  const hashed = await crypto.subtle.digest('SHA-256', bytes);
  const actual = Array.from(new Uint8Array(hashed), (n) => n.toString(16).padStart(2, '0')).join(
    '',
  );
  if (actual !== row.revision_sha256) throw new Error('Draft revision content hash differs.');
  return row;
}

export function editDraft(snapshot: DraftRevision): DraftEditor {
  return { snapshot, label: snapshot.label, notes: snapshot.notes, conflict: null };
}
export function hasDraftChanges(editor: DraftEditor): boolean {
  return editor.label !== editor.snapshot.label || editor.notes !== editor.snapshot.notes;
}
export function retainDraftConflict(editor: DraftEditor, error: DraftServiceError): DraftEditor {
  return error.code === 'stale_revision' ? { ...editor, conflict: error.currentRevision } : editor;
}

const errorMessages: Record<string, string> = {
  origin_forbidden: 'The local preview origin is not permitted to access drafts.',
  invalid_request: 'The draft request was rejected. Check its label, notes and current source.',
  draft_not_found:
    'That draft or saved revision is unavailable. Refresh the library to check its current entries.',
  stale_revision:
    'This draft changed since it was loaded. Your unsaved text is preserved. Reload latest explicitly to discard it.',
  draft_unavailable:
    'Saved draft data is unsafe, damaged or exceeds its limits. It was not admitted.',
  source_unavailable: 'The exact frozen RP1 source could not be verified. Forking is unavailable.',
  storage_unavailable:
    'Local draft storage is unavailable. No save is confirmed; refresh the library before retrying a fork.',
  draft_error:
    'The draft operation failed. No save is confirmed; reload the library before retrying.',
};
export function createDraftClient(vehicle: InspectionDocument, fetcher: typeof fetch = fetch) {
  if (!matchesDraftSource(vehicle))
    throw new Error('Draft library requires the exact frozen current RP1 source.');
  async function request(
    path: string,
    method: 'GET' | 'POST' | 'PATCH',
    body?: unknown,
    signal?: AbortSignal,
  ): Promise<unknown> {
    let response: Response;
    try {
      response = await fetcher(path, {
        method,
        signal,
        cache: 'no-store',
        headers: {
          Accept: 'application/json',
          ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
    } catch (error) {
      if (signal?.aborted) throw error;
      throw new DraftServiceError(
        0,
        'transport_unavailable',
        'Draft service could not be reached. No save is confirmed; refresh the library before retrying a fork.',
      );
    }
    let raw: unknown;
    try {
      raw = await response.json();
    } catch {
      if (response.status === 404)
        throw new DraftServiceError(
          404,
          'route_unavailable',
          'Draft API is unavailable (404). The normal-host preview needs a restart with the draft router enabled. No prepared snapshot can substitute for mutable drafts.',
        );
      throw new DraftServiceError(
        response.status,
        'invalid_response',
        'Draft service returned unreadable data. No snapshot or save was admitted.',
      );
    }
    if (!response.ok) {
      const detail = object(raw) && object(raw.detail) ? raw.detail : null;
      if (response.status === 404 && detail?.code !== 'draft_not_found')
        throw new DraftServiceError(
          404,
          'route_unavailable',
          'Draft API is unavailable (404). The normal-host preview needs a restart with the draft router enabled. No prepared snapshot can substitute for mutable drafts.',
        );
      const code =
        typeof detail?.code === 'string' && Object.hasOwn(errorMessages, detail.code)
          ? detail.code
          : 'draft_error';
      const revision =
        typeof detail?.current_revision === 'string' && sha.test(detail.current_revision)
          ? detail.current_revision
          : null;
      if (code === 'stale_revision' && (response.status !== 409 || revision === null))
        throw new DraftServiceError(
          response.status,
          'invalid_response',
          'Draft conflict response was malformed. Unsaved text is preserved; reload latest explicitly.',
        );
      throw new DraftServiceError(response.status, code, errorMessages[code], revision);
    }
    return raw;
  }
  return {
    async list(after?: string, signal?: AbortSignal): Promise<DraftPage> {
      if (after !== undefined && !uuid.test(after)) throw new Error('Invalid draft cursor.');
      return admitDraftPage(
        await request(
          `${DRAFT_API}?limit=25${after ? `&after=${after}` : ''}`,
          'GET',
          undefined,
          signal,
        ),
      );
    },
    async read(id: string, revision?: string, signal?: AbortSignal): Promise<DraftRevision> {
      if (!uuid.test(id) || (revision !== undefined && !sha.test(revision)))
        throw new Error('Invalid draft identity or revision.');
      return admitDraftRevision(
        await request(
          `${DRAFT_API}/${id}${revision ? `?revision=${revision}` : ''}`,
          'GET',
          undefined,
          signal,
        ),
        vehicle,
        id,
        revision,
      );
    },
    async fork(label: string, notes: string, signal?: AbortSignal): Promise<DraftRevision> {
      if (!validText(label, 160, true) || !validText(notes, 8000))
        throw new Error('Use a label of 1–160 characters and notes of at most 8,000 characters.');
      const raw = await request(
        DRAFT_API,
        'POST',
        {
          source_configuration_id: RP1_BANK_CONFIGURATION,
          source_specification_sha256: RP1_BANK_SPEC,
          label,
          notes,
        },
        signal,
      );
      const row = await admitDraftRevision(raw, vehicle);
      if (row.sequence !== 1 || row.label !== label || row.notes !== notes)
        throw new Error(
          'Fork response differs from the explicit metadata request; refresh the library before retrying.',
        );
      return row;
    },
    async save(editor: DraftEditor, signal?: AbortSignal): Promise<DraftRevision> {
      const previous = editor.snapshot;
      if (
        !uuid.test(previous.draft_id) ||
        !sha.test(previous.revision_sha256) ||
        !validText(editor.label, 160, true) ||
        !validText(editor.notes, 8000)
      )
        throw new Error('Draft metadata or identity is invalid.');
      const raw = await request(
        `${DRAFT_API}/${previous.draft_id}`,
        'PATCH',
        { base_revision: previous.revision_sha256, label: editor.label, notes: editor.notes },
        signal,
      );
      const row = await admitDraftRevision(raw, vehicle, previous.draft_id);
      if (
        row.source_sha256 !== previous.source_sha256 ||
        row.label !== editor.label ||
        row.notes !== editor.notes ||
        (hasDraftChanges(editor)
          ? row.parent_revision_sha256 !== previous.revision_sha256 ||
            row.sequence !== previous.sequence + 1
          : row.revision_sha256 !== previous.revision_sha256)
      )
        throw new Error(
          'Save response differs from the source or requested metadata; no new editor state admitted.',
        );
      return row;
    },
  };
}
export type DraftClient = ReturnType<typeof createDraftClient>;
