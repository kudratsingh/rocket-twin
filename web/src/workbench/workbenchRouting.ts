export const engineeringTopics = [
  ['g80-f2', 'G80-F2 stock construction'],
  ['rp1-studies', 'RP1 FP1 / FR1 studies'],
  ['rp1-validation', 'VP1 validation programme'],
  ['g80-f2-c1', 'F2-C1 connection proposal'],
  ['g80-fixed', 'G80-F1 fixed candidate'],
  ['a1', 'A1 upper connection'],
  ['geometry', 'Arrangement & sections'],
  ['forces', 'Forces & connections'],
  ['mass', 'Mass, balance & launch'],
  ['comparison', 'Candidate comparisons'],
  ['recovery', 'Recovery & extraction'],
  ['thermal', 'Thermal connections'],
  ['electrical', 'Electrical nets'],
  ['assembly', 'Assembly & service'],
  ['requirements', 'Physical verification'],
  ['evidence', 'Evidence & next views'],
] as const;
export type EngineeringTopic = (typeof engineeringTopics)[number][0];
export function engineeringRoute(search: string): {
  view: EngineeringTopic;
  notice: string | null;
} {
  const value = new URLSearchParams(search).get('view');
  const match = engineeringTopics.find(([id]) => id === value);
  return {
    view: match?.[0] ?? 'g80-f2',
    notice: value && !match ? `Unknown engineering topic “${value}”. Showing G80-F2.` : null,
  };
}
export function engineeringHref(href: string, view: EngineeringTopic): string {
  const url = new URL(href, 'http://local.invalid');
  url.searchParams.set('workspace', 'engineering');
  url.searchParams.set('view', view);
  return `${url.pathname}${url.search}${url.hash}`;
}
export function isConstructionTopic(view: EngineeringTopic): boolean {
  return (
    view === 'rp1-studies' ||
    view === 'rp1-validation' ||
    view === 'a1' ||
    view === 'g80-fixed' ||
    view === 'g80-f2' ||
    view === 'g80-f2-c1'
  );
}

/** Only a recognized missing API route permits a prepared export, never missing source. */
export async function loadRecordedSource(
  path: string,
  preparedPath: string,
  signal: AbortSignal,
  request: typeof fetch = fetch,
): Promise<{ value: unknown; prepared: boolean }> {
  const response = await request(path, { signal, headers: { Accept: 'application/json' } });
  if (response.ok) return { value: await response.json(), prepared: false };
  let detail = response.statusText;
  let apiDetail = '';
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === 'string') detail = apiDetail = body.detail;
  } catch {
    // A non-JSON or source-missing 404 does not establish an absent API route.
  }
  if (response.status !== 404 || apiDetail !== 'Not Found')
    throw new Error(`${response.status} ${detail}`);
  signal.throwIfAborted();
  const saved = await request(preparedPath, { signal, headers: { Accept: 'application/json' } });
  if (!saved.ok)
    throw new Error(`Prepared source unavailable: ${saved.status} ${saved.statusText}`);
  return { value: await saved.json(), prepared: true };
}
