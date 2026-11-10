import type { InspectionDocument } from '../types';
import type { BankDefinition, BankInstance } from '../parts-bank/partsBank';
import {
  admitDraftRevision,
  DRAFT_API,
  matchesDraftSource,
  type DraftRevision,
} from './draftLibraryClient';

export type SourceIntentType = 'exclude-source-occurrence' | 'restore-source-occurrence';
export interface RemovedSourceFunction {
  occurrence_id: string;
  definition_id: string;
  function: string;
  status: 'excluded_intent_function_unresolved';
  source_occurrence: BankInstance;
  source_evidence: Pick<
    BankDefinition,
    'provenance' | 'issues' | 'physical_verification' | 'interfaces_status' | 'geometry'
  >;
  blocker: string;
}
export interface SourceIntentOverlay {
  schema_version: 1;
  kind: 'rp1-source-fork-planning-overlay';
  status: 'planning_intent_only';
  base: DraftRevision;
  source_revision_sha256: string;
  source_sha256: string;
  revision_sha256: string;
  excluded_occurrence_ids: string[];
  preview: {
    source_occurrences: 55;
    source_ledger_preserved: true;
    exclusion_intents: number;
    removed_functions: RemovedSourceFunction[];
    effective_inventory: null;
    reason: string;
  };
  checks: {
    status: 'unavailable';
    total_mass_kg: null;
    mass_removal_credit_kg: null;
    cg_m: null;
    inertia_kg_m2: null;
    reason: string;
  };
  readiness: {
    resolve_available: false;
    resolved_candidate: false;
    simulation_eligible: false;
    engineering_accepted: false;
    flight_ready: false;
    blockers: string[];
  };
  capabilities: {
    exclude_source_occurrence: true;
    restore_source_occurrence: true;
    add: false;
    replace: false;
    connect: false;
    'set-position': false;
    'set-parameter': false;
    resolve: false;
  };
}
const sha = /^[a-f0-9]{64}$/;
const removedBlocker =
  'Source function would be removed by this planning intent; no replacement, mass credit or effective candidate has been resolved';
function record(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
// Structural equality only. Python's overlay hash is an opaque server identity;
// JS must not rehash or serialize the complete source back to the service.
function same(left: unknown, right: unknown): boolean {
  if (left === right) return true;
  if (Array.isArray(left) || Array.isArray(right))
    return (
      Array.isArray(left) &&
      Array.isArray(right) &&
      left.length === right.length &&
      left.every((item, index) => same(item, right[index]))
    );
  if (!record(left) || !record(right)) return false;
  return (
    Object.keys(left).length === Object.keys(right).length &&
    Object.keys(left).every((key) => Object.hasOwn(right, key) && same(left[key], right[key]))
  );
}
function orderedIds(snapshot: DraftRevision, ids: string[]): string[] {
  const sourceIds = snapshot.source.parts_bank.instances.map((row) => row.id);
  if (
    ids.length > 55 ||
    new Set(ids).size !== ids.length ||
    ids.some((id) => !sourceIds.includes(id))
  )
    throw new Error('Intent IDs must be unique original source occurrences.');
  return sourceIds.filter((id) => ids.includes(id));
}
export class SourceIntentError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly currentDraftRevision: string | null = null,
    readonly currentOverlayRevision: string | null = null,
  ) {
    super(message);
    this.name = 'SourceIntentError';
  }
}
export async function admitSourceIntentOverlay(
  raw: unknown,
  vehicle: InspectionDocument,
  snapshot: DraftRevision,
  expectedExcludedIds: string[],
): Promise<SourceIntentOverlay> {
  if (!record(raw) || !record(raw.base))
    throw new Error('Planning preview is malformed; current intents are preserved.');
  if (
    raw.base.draft_id === snapshot.draft_id &&
    raw.base.revision_sha256 !== snapshot.revision_sha256
  )
    throw new SourceIntentError(
      409,
      'stale_draft_revision',
      'The saved parent metadata changed. Current intents are preserved; reload metadata before preparing a new preview.',
      typeof raw.base.revision_sha256 === 'string' && sha.test(raw.base.revision_sha256)
        ? raw.base.revision_sha256
        : null,
    );
  const base = await admitDraftRevision(
    raw.base,
    vehicle,
    snapshot.draft_id,
    snapshot.revision_sha256,
  );
  if (!same(base, snapshot))
    throw new Error('Planning preview parent/source differs from the loaded saved metadata.');
  const excluded = orderedIds(snapshot, expectedExcludedIds);
  const bank = base.source.parts_bank;
  const removed: RemovedSourceFunction[] = excluded.map((id) => {
    const occurrence = bank.instances.find((row) => row.id === id)!;
    const definition = bank.definitions.find((row) => row.source_part_id === id)!;
    return {
      occurrence_id: id,
      definition_id: definition.id,
      function: definition.function,
      status: 'excluded_intent_function_unresolved',
      source_occurrence: occurrence,
      source_evidence: {
        provenance: definition.provenance,
        issues: definition.issues,
        physical_verification: definition.physical_verification,
        interfaces_status: definition.interfaces_status,
        geometry: definition.geometry,
      },
      blocker: removedBlocker,
    };
  });
  const expected = {
    schema_version: 1,
    kind: 'rp1-source-fork-planning-overlay',
    status: 'planning_intent_only',
    base,
    source_revision_sha256: base.revision_sha256,
    source_sha256: base.source_sha256,
    excluded_occurrence_ids: excluded,
    preview: {
      source_occurrences: 55,
      source_ledger_preserved: true,
      exclusion_intents: excluded.length,
      removed_functions: removed,
      effective_inventory: null,
      reason: 'Intent only; every original occurrence remains in the immutable source ledger',
    },
    checks: {
      status: 'unavailable',
      total_mass_kg: null,
      mass_removal_credit_kg: null,
      cg_m: null,
      inertia_kg_m2: null,
      reason:
        'No effective candidate, replacement-function accounting, CAD or engineering calculation is admitted',
    },
    readiness: {
      resolve_available: false,
      resolved_candidate: false,
      simulation_eligible: false,
      engineering_accepted: false,
      flight_ready: false,
      blockers: [
        'Planning overlay is not an effective vehicle; exclusion never credits source mass',
        'Source estimates/conflicts, failed fin findings, unavailable installed geometry/inertia and all physical gates remain unchanged',
        ...removed.map((row) => `${row.blocker}: ${row.occurrence_id}`),
      ],
    },
    capabilities: {
      exclude_source_occurrence: true,
      restore_source_occurrence: true,
      add: false,
      replace: false,
      connect: false,
      'set-position': false,
      'set-parameter': false,
      resolve: false,
    },
    revision_sha256: raw.revision_sha256,
  };
  if (
    typeof raw.revision_sha256 !== 'string' ||
    !sha.test(raw.revision_sha256) ||
    !same(raw, expected)
  )
    throw new Error(
      'Planning preview source, function evidence, intent set or gates differ; current intents are preserved.',
    );
  return raw as unknown as SourceIntentOverlay;
}
const messages: Record<string, string> = {
  origin_forbidden: 'The local preview origin is not permitted to access intent previews.',
  stale_draft_revision:
    'The saved parent metadata changed. Current intents are preserved; reload metadata before preparing a new preview.',
  stale_overlay_revision:
    'The preview identity changed. Current intents are preserved; explicitly prepare a fresh preview before continuing.',
  draft_not_found:
    'This saved draft is unavailable. Reload metadata through the saved drafts library.',
  duplicate_exclusion: 'That source occurrence already has an exclusion intent.',
  unknown_occurrence: 'Choose an exact original source occurrence.',
};
export function createSourceIntentClient(
  vehicle: InspectionDocument,
  snapshot: DraftRevision,
  fetcher: typeof fetch = fetch,
) {
  if (!matchesDraftSource(vehicle))
    throw new Error('Intent preview requires the exact frozen current RP1 source.');
  async function request(method: 'GET' | 'POST', body?: unknown): Promise<unknown> {
    await admitDraftRevision(snapshot, vehicle, snapshot.draft_id, snapshot.revision_sha256);
    let response: Response;
    try {
      response = await fetcher(`${DRAFT_API}/${snapshot.draft_id}/intent-preview`, {
        method,
        cache: 'no-store',
        headers: {
          Accept: 'application/json',
          ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
    } catch {
      throw new SourceIntentError(
        0,
        'transport_unavailable',
        'Intent preview service could not be reached. Current intents are preserved; no command was confirmed.',
      );
    }
    let raw: unknown;
    try {
      raw = await response.json();
    } catch {
      if (response.status !== 404)
        throw new SourceIntentError(
          response.status,
          'invalid_response',
          'Intent preview returned unreadable data. Current intents are preserved.',
        );
    }
    if (
      response.status === 404 &&
      !(record(raw) && record(raw.detail) && raw.detail.code === 'draft_not_found')
    )
      throw new SourceIntentError(
        404,
        'route_unavailable',
        'Intent preview API is unavailable (404). Restart the normal-host backend with the intent router enabled. No prepared fallback is available.',
      );
    if (!response.ok) {
      const detail = record(raw) && record(raw.detail) ? raw.detail : null;
      const code =
        typeof detail?.code === 'string' && Object.hasOwn(messages, detail.code)
          ? detail.code
          : 'intent_unavailable';
      const currentDraft =
        typeof detail?.current_draft_revision === 'string' &&
        sha.test(detail.current_draft_revision)
          ? detail.current_draft_revision
          : null;
      const currentOverlay =
        typeof detail?.current_overlay_revision === 'string' &&
        sha.test(detail.current_overlay_revision)
          ? detail.current_overlay_revision
          : null;
      if (
        (code === 'stale_draft_revision' || code === 'stale_overlay_revision') &&
        (response.status !== 409 ||
          (code === 'stale_draft_revision' ? currentDraft : currentOverlay) === null)
      )
        throw new SourceIntentError(
          response.status,
          'invalid_response',
          'Intent conflict response was malformed. Current intents are preserved; reload metadata explicitly.',
        );
      throw new SourceIntentError(
        response.status,
        code,
        messages[code] ??
          'Intent preview was rejected. Current intents are preserved; no command was confirmed.',
        currentDraft,
        currentOverlay,
      );
    }
    return raw;
  }
  return {
    async prepare(): Promise<SourceIntentOverlay> {
      return admitSourceIntentOverlay(await request('GET'), vehicle, snapshot, []);
    },
    async apply(
      overlay: SourceIntentOverlay,
      type: SourceIntentType,
      occurrenceId: string,
    ): Promise<SourceIntentOverlay> {
      await admitSourceIntentOverlay(overlay, vehicle, snapshot, overlay.excluded_occurrence_ids);
      const ids = orderedIds(snapshot, overlay.excluded_occurrence_ids);
      if (
        !snapshot.source.parts_bank.instances.some((row) => row.id === occurrenceId) ||
        (type !== 'exclude-source-occurrence' && type !== 'restore-source-occurrence')
      )
        throw new Error('Choose an original source occurrence and a supported intent command.');
      if (type === 'exclude-source-occurrence' && ids.includes(occurrenceId))
        throw new Error('That source occurrence already has an exclusion intent.');
      const expected =
        type === 'exclude-source-occurrence'
          ? [...ids, occurrenceId]
          : ids.filter((id) => id !== occurrenceId);
      const raw = await request('POST', {
        base_draft_revision: snapshot.revision_sha256,
        base_overlay_revision: overlay.revision_sha256,
        excluded_occurrence_ids: ids,
        type,
        occurrence_id: occurrenceId,
      });
      return admitSourceIntentOverlay(raw, vehicle, snapshot, expected);
    },
  };
}
