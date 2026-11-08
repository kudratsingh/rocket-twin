/** Status reads only. Resuming observation never submits or retries a simulation. */
export interface AttemptStatus {
  run_id: string;
  status: string;
  progress?: string;
  error?: string | null;
}

const terminal = new Set(['complete', 'failed', 'cancelled', 'interrupted']);
const statuses = new Set(['queued', 'running', 'cancel_requested', ...terminal]);
const nonempty = (value: unknown): value is string => typeof value === 'string' && value.length > 0;

/** Preserve transport/HTTP/JSON errors; none is a simulation terminal status. */
export async function experimentJson<T>(
  url: string,
  options?: RequestInit,
  observe?: (response: Response) => void,
  request: typeof fetch = fetch,
): Promise<T> {
  const response = await request(url, options);
  observe?.(response);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (body.detail !== undefined)
        detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* Preserve HTTP status when a proxy returns HTML or an empty body. */
    }
    throw new Error(`HTTP ${response.status} ${detail} (${options?.method ?? 'GET'} ${url})`);
  }
  try {
    return (await response.json()) as T;
  } catch {
    throw new Error(`Malformed JSON from ${options?.method ?? 'GET'} ${url}.`);
  }
}

export function acceptedAttemptIds(value: unknown, expectedCount: number): string[] {
  const response = value as { run_id?: unknown; run_ids?: unknown } | null;
  if (
    !response ||
    !nonempty(response.run_id) ||
    !Array.isArray(response.run_ids) ||
    response.run_ids.length !== expectedCount ||
    !response.run_ids.every(nonempty) ||
    new Set(response.run_ids).size !== response.run_ids.length ||
    response.run_ids[0] !== response.run_id
  )
    throw new Error(
      'Submission response did not confirm the exact declared member IDs. Retain the request key and check saved attempts before retrying.',
    );
  return [...response.run_ids];
}

/** Existing record membership is authoritative; no seeds or requests are reconstructed. */
export function savedAttemptIds(record: { run_id: string; batch_members?: unknown }): string[] {
  const ids = record.batch_members ?? [record.run_id];
  if (
    !Array.isArray(ids) ||
    !ids.length ||
    ids.length > 4 ||
    !ids.every(nonempty) ||
    new Set(ids).size !== ids.length ||
    !ids.includes(record.run_id)
  )
    throw new Error(
      'Saved batch membership is missing or malformed; inspect its saved provenance before observing members.',
    );
  return [...ids];
}

/** Missing library members stay explicit. This export contains no trajectory samples. */
export function savedAttemptExport<T extends { run_id: string; batch_members?: unknown }>(
  record: T,
  library: readonly T[],
): string {
  const ids = savedAttemptIds(record);
  const members = ids.map((id) => ({
    run_id: id,
    record: library.find((item) => item.run_id === id) ?? (id === record.run_id ? record : null),
  }));
  return (
    JSON.stringify(
      {
        schema_version: 'rocket-twin.saved-attempt-export.v1',
        selected_run_id: record.run_id,
        members,
        missing_members: members.filter((item) => item.record === null).map((item) => item.run_id),
        telemetry_included: false,
        notice:
          'Saved request/status/provenance only. Missing members are unavailable, never inferred. No new run or retry is started.',
      },
      null,
      2,
    ) + '\n'
  );
}

export function attemptSummary(
  ids: readonly string[],
  records: Readonly<Record<string, AttemptStatus>>,
) {
  const completed = ids.filter((id) => records[id]?.status === 'complete');
  const outstanding = ids.filter((id) => !terminal.has(records[id]?.status));
  return {
    terminal: ids.length > 0 && outstanding.length === 0,
    completed,
    outstanding,
    text: ids.map((id) => `${id}: ${records[id]?.status ?? 'status unavailable'}`).join(' · '),
  };
}

/** Retain successful member reads even when another member temporarily fails. */
export async function readAttemptStatuses(
  ids: readonly string[],
  read: (id: string, signal: AbortSignal) => Promise<unknown>,
  signal: AbortSignal,
): Promise<{ records: AttemptStatus[]; errors: string[] }> {
  const values = await Promise.allSettled(
    ids.map(async (id) => {
      const value = (await read(id, signal)) as AttemptStatus | null;
      if (
        !value ||
        value.run_id !== id ||
        !statuses.has(value.status) ||
        (value.progress !== undefined && typeof value.progress !== 'string') ||
        (value.error !== undefined && value.error !== null && typeof value.error !== 'string')
      )
        throw new Error('Status response has a foreign identity or unsupported status.');
      return value;
    }),
  );
  if (signal.aborted) return { records: [], errors: [] };
  const records: AttemptStatus[] = [],
    errors: string[] = [];
  values.forEach((result, index) => {
    if (result.status === 'fulfilled') records.push(result.value);
    else errors.push(`${ids[index]}: ${String(result.reason)}`);
  });
  return { records, errors };
}
