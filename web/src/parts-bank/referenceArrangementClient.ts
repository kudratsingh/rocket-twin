import admission from '../../../docs/studies/frontend-reference-arrangement-20261109/admission.json';
import { admitReferencePartDetail, type ReferenceAvailability } from './referencePartsClient';
import type { ReferenceDefinition } from './referenceDatumGeometry';

export const REFERENCE_ARRANGEMENT_API = '/api/reference-arrangement';
export type ArrangementTranslation = [number, number, number];
export interface ArrangementInstance {
  reference_id: string;
  definition_revision_sha256: string;
  translation_mm: ArrangementTranslation;
  id: string;
  quantity: 1;
  rotation_quaternion_xyzw: [0, 0, 0, 1];
  scale: [1, 1, 1];
  installed_transform: null;
  scope: 'arrangement_display_occurrence_only';
  added_to_source: false;
  added_to_vehicle: false;
}
export type ArrangementPlan = Omit<typeof admission.empty_plan, 'instances' | 'revision_sha256'> & {
  instances: ArrangementInstance[];
  revision_sha256: string;
};
export type ArrangementCatalog = typeof admission.catalog_header & {
  definitions: ReferenceDefinition[];
  availability: Record<string, ReferenceAvailability>;
};
export interface ArrangementEnvelope {
  catalog: ArrangementCatalog;
  plan: ArrangementPlan;
  action: 'preview_uninstalled_reference_arrangement';
  persisted: false;
  source_vehicle_changed: false;
}
export type ArrangementCoreCommand =
  | {
      type: 'add-reference';
      reference_id: string;
      definition_revision_sha256: string;
      base_plan_revision: string;
    }
  | {
      type: 'translate-reference';
      instance_id: string;
      translation_mm: ArrangementTranslation;
      base_plan_revision: string;
    };
export class ReferenceArrangementServiceError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly currentPlanRevision: string | null = null,
  ) {
    super(message);
    this.name = 'ReferenceArrangementServiceError';
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
function hash(raw: unknown): raw is string {
  return typeof raw === 'string' && /^[a-f0-9]{64}$/.test(raw);
}
function invalid(status = 200): never {
  throw new ReferenceArrangementServiceError(
    status,
    'invalid_response',
    'Arrangement source, state, fixed transforms or false gates differ. Keep the previous view; no response was admitted.',
  );
}
function invalidCommand(): never {
  throw new ReferenceArrangementServiceError(
    0,
    'invalid_command',
    'Choose one exact reference addition or bounded translation against the current plan revision. No request was sent.',
  );
}
/** Exact decimal input granularity, never rounding, physical tolerance or fit. */
export function parseTranslationText(raw: string): number {
  const reject = (): never => {
    throw new ReferenceArrangementServiceError(
      0,
      'invalid_translation',
      'Enter a finite coordinate from −500 to 500 mm with at most three meaningful decimal places. This is input granularity, not a tolerance.',
    );
  };
  if (typeof raw !== 'string' || raw.length > 128) return reject();
  const text = raw.trim();
  if (!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(text)) return reject();
  const [mantissa, power] = text.toLowerCase().split('e');
  const exponent = power === undefined ? 0 : Number(power);
  if (!Number.isSafeInteger(exponent) || Math.abs(exponent) > 1000) return reject();
  const unsigned = mantissa.replace(/^[+-]/, '');
  const [whole, fraction = ''] = unsigned.split('.');
  const digits = whole + fraction;
  if (!/[1-9]/.test(digits)) return 0;
  const trailing = digits.match(/0*$/)![0].length;
  if (exponent - fraction.length + trailing < -3) return reject();
  const number = Number(text);
  if (!Number.isFinite(number) || Math.abs(number) > 500) return reject();
  return number === 0 ? 0 : number;
}
function translation(raw: unknown): ArrangementTranslation | null {
  if (!Array.isArray(raw) || raw.length !== 3) return null;
  const result: number[] = [];
  for (const value of raw) {
    if (typeof value !== 'number' || !Number.isFinite(value)) return null;
    try {
      result.push(parseTranslationText(String(value)));
    } catch {
      return null;
    }
  }
  return result as ArrangementTranslation;
}
function instance(
  mapping: (typeof admission.definition_mappings)[number],
  coordinates: ArrangementTranslation,
): ArrangementInstance {
  return {
    reference_id: mapping.reference_id,
    definition_revision_sha256: mapping.definition_revision_sha256,
    translation_mm: coordinates,
    id: mapping.instance_id,
    quantity: 1,
    rotation_quaternion_xyzw: [0, 0, 0, 1],
    scale: [1, 1, 1],
    installed_transform: null,
    scope: 'arrangement_display_occurrence_only',
    added_to_source: false,
    added_to_vehicle: false,
  };
}
/** Admit source/semantic state; nonempty Python hashes remain opaque identities. */
export function admitArrangementEnvelope(raw: unknown): ArrangementEnvelope {
  if (!object(raw) || !object(raw.catalog) || !object(raw.plan)) return invalid();
  const { definitions, availability, ...header } = raw.catalog;
  if (
    !same(header, admission.catalog_header) ||
    !Array.isArray(definitions) ||
    definitions.length !== 2 ||
    !object(availability) ||
    !same(
      Object.keys(availability).sort(),
      admission.definition_mappings.map((row) => row.reference_id).sort(),
    )
  )
    return invalid();
  try {
    admission.definition_mappings.forEach((mapping, index) => {
      const detail = admitReferencePartDetail(
        {
          definition: definitions[index],
          availability: availability[mapping.reference_id],
          action: 'inspect_geometry_reference',
          instance_created: false,
          engineering_accepted: false,
          simulation_eligible: false,
          flight_ready: false,
          catalog_id: header.id,
          catalog_revision_sha256: header.revision_sha256,
          scope: header.scope,
        },
        mapping.source_template_id,
      );
      if (
        detail.definition.id !== mapping.reference_id ||
        detail.definition.revision_sha256 !== mapping.definition_revision_sha256
      )
        invalid();
    });
  } catch {
    return invalid();
  }
  const { instances, revision_sha256: revision, ...planHeader } = raw.plan;
  const expectedHeader = Object.fromEntries(
    Object.entries(admission.empty_plan).filter(
      ([key]) => key !== 'instances' && key !== 'revision_sha256',
    ),
  );
  if (
    !same(planHeader, expectedHeader) ||
    !Array.isArray(instances) ||
    instances.length > 2 ||
    !hash(revision)
  )
    return invalid();
  let previousIndex = -1;
  for (const row of instances) {
    if (!object(row)) return invalid();
    const index = admission.definition_mappings.findIndex(
      (mapping) => mapping.reference_id === row.reference_id,
    );
    const coordinates = translation(row.translation_mm);
    if (
      index <= previousIndex ||
      !coordinates ||
      !same(row, instance(admission.definition_mappings[index], coordinates))
    )
      return invalid();
    previousIndex = index;
  }
  if (!instances.length && revision !== admission.empty_plan.revision_sha256) return invalid();
  if (
    !same(raw, {
      catalog: raw.catalog,
      plan: raw.plan,
      action: 'preview_uninstalled_reference_arrangement',
      persisted: false,
      source_vehicle_changed: false,
    })
  )
    return invalid();
  return raw as unknown as ArrangementEnvelope;
}
function transition(
  base: ArrangementEnvelope,
  raw: ArrangementCoreCommand,
): {
  command: ArrangementCoreCommand;
  rows: ArrangementInstance[];
} {
  if (
    !object(raw) ||
    raw.base_plan_revision !== base.plan.revision_sha256 ||
    !hash(raw.base_plan_revision)
  )
    return invalidCommand();
  const rows = structuredClone(base.plan.instances);
  let command: ArrangementCoreCommand;
  if (raw.type === 'add-reference') {
    if (
      !same(
        Object.keys(raw).sort(),
        ['type', 'reference_id', 'definition_revision_sha256', 'base_plan_revision'].sort(),
      )
    )
      return invalidCommand();
    const mapping = admission.definition_mappings.find(
      (row) =>
        row.reference_id === raw.reference_id &&
        row.definition_revision_sha256 === raw.definition_revision_sha256,
    );
    if (
      !mapping ||
      rows.some((row) => row.reference_id === mapping.reference_id) ||
      rows.length >= 2
    )
      return invalidCommand();
    command = { ...raw };
    rows.push(instance(mapping, [0, 0, 0]));
    rows.sort(
      (left, right) =>
        admission.definition_mappings.findIndex((row) => row.reference_id === left.reference_id) -
        admission.definition_mappings.findIndex((row) => row.reference_id === right.reference_id),
    );
  } else if (raw.type === 'translate-reference') {
    if (
      !same(
        Object.keys(raw).sort(),
        ['type', 'instance_id', 'translation_mm', 'base_plan_revision'].sort(),
      )
    )
      return invalidCommand();
    const row = rows.find((row) => row.id === raw.instance_id);
    const coordinates = translation(raw.translation_mm);
    if (!row || !coordinates) return invalidCommand();
    row.translation_mm = coordinates;
    command = { ...raw, translation_mm: coordinates };
  } else return invalidCommand();
  return { command, rows };
}
const messages: Record<string, string> = {
  stale_plan_revision:
    'The submitted arrangement content guard differs. Keep the previous view and explicitly prepare a new unsaved plan if needed; no retry was sent.',
  invalid_catalog:
    'The pinned reference catalog could not be admitted. Keep the previous view; no substitute was prepared.',
  reference_source_unavailable:
    'Pinned reference sources or existing cache could not be verified. No regeneration or substitute was attempted.',
  origin_forbidden: 'This local preview origin is not permitted to prepare reference arrangements.',
  invalid_request: 'The arrangement request was rejected. The previous view is unchanged.',
  invalid_plan: 'The arrangement state was rejected. The previous view is unchanged.',
  invalid_command: 'The arrangement command was rejected. The previous view is unchanged.',
  invalid_translation:
    'The translation was rejected. Enter finite coordinates within ±500 mm at up to three decimal places.',
  duplicate_reference:
    'That reference already has its one display occurrence. The previous view is unchanged.',
  unknown_instance:
    'That arrangement display occurrence is unavailable. The previous view is unchanged.',
  unknown_reference: 'That nominal reference is not registered. The previous view is unchanged.',
  definition_revision_mismatch:
    'That reference definition revision differs. No alternate reference was admitted.',
  instance_limit: 'Only the two distinct registered display occurrences are supported.',
  unsupported_command:
    'Only explicit reference addition and translation are supported; no physical composition was performed.',
  request_too_large:
    'The arrangement request exceeded its bounded size. The previous view is unchanged.',
};
function checkAbort(signal?: AbortSignal): void {
  if (signal?.aborted) throw new DOMException('Reference arrangement was cancelled.', 'AbortError');
}
/** No constructor I/O, persistence, automatic prepare, retry, download or fallback. */
export function createReferenceArrangementClient(fetcher: typeof fetch = fetch) {
  async function request(
    method: 'GET' | 'POST',
    signal?: AbortSignal,
    body?: unknown,
  ): Promise<ArrangementEnvelope> {
    checkAbort(signal);
    let response: Response;
    try {
      response = await fetcher(REFERENCE_ARRANGEMENT_API, {
        method,
        signal,
        cache: 'no-store',
        headers: {
          Accept: 'application/json',
          ...(method === 'POST' ? { 'Content-Type': 'application/json' } : {}),
        },
        ...(body === undefined ? {} : { body: JSON.stringify(body) }),
      });
    } catch {
      checkAbort(signal);
      throw new ReferenceArrangementServiceError(
        0,
        'transport_unavailable',
        'The arrangement service could not be reached. Keep the previous view; no retry or fallback was attempted.',
      );
    }
    checkAbort(signal);
    let raw: unknown;
    try {
      raw = await response.json();
    } catch {
      checkAbort(signal);
      if (response.status !== 404) return invalid(response.status);
    }
    checkAbort(signal);
    if (!response.ok) {
      if (response.status === 404)
        throw new ReferenceArrangementServiceError(
          404,
          'route_unavailable',
          'The arrangement API is unavailable (404). Enable the mounted router in the normal-host preview. No prepared fallback is available.',
        );
      const detail = object(raw) && object(raw.detail) ? raw.detail : null;
      const code =
        typeof detail?.code === 'string' && Object.hasOwn(messages, detail.code)
          ? detail.code
          : 'arrangement_error';
      const current = hash(detail?.current_plan_revision) ? detail.current_plan_revision : null;
      if (code === 'stale_plan_revision' && (response.status !== 409 || current === null))
        return invalid(response.status);
      throw new ReferenceArrangementServiceError(
        response.status,
        code,
        messages[code] ??
          'The arrangement request failed. Keep the previous view; no response was admitted.',
        current,
      );
    }
    return admitArrangementEnvelope(raw);
  }
  return {
    async prepare(signal?: AbortSignal): Promise<ArrangementEnvelope> {
      const result = await request('GET', signal);
      if (!same(result.plan, admission.empty_plan)) return invalid();
      return result;
    },
    async command(
      baseEnvelope: ArrangementEnvelope,
      corecommand: ArrangementCoreCommand,
      signal?: AbortSignal,
    ): Promise<ArrangementEnvelope> {
      checkAbort(signal);
      const base = structuredClone(admitArrangementEnvelope(baseEnvelope));
      const expected = transition(base, corecommand);
      const result = await request('POST', signal, {
        instances: base.plan.instances.map(
          ({ reference_id, definition_revision_sha256, translation_mm }) => ({
            reference_id,
            definition_revision_sha256,
            translation_mm: [...translation_mm],
          }),
        ),
        command: expected.command,
      });
      const unchanged = same(expected.rows, base.plan.instances);
      if (
        !same(result.plan.instances, expected.rows) ||
        (unchanged
          ? result.plan.revision_sha256 !== base.plan.revision_sha256
          : result.plan.revision_sha256 === base.plan.revision_sha256)
      )
        return invalid();
      return result;
    },
  };
}
