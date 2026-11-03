/** URL presentation only. Identity compatibility remains the data owner's responsibility. */
export const workspaceItems = [
  { id: 'design', label: 'Design' },
  { id: 'engineering', label: 'Engineering' },
  { id: 'experiments', label: 'Experiments' },
  { id: 'replay', label: 'Flight Replay' },
  { id: 'analysis', label: 'Analysis' },
] as const;

export type WorkspaceId = (typeof workspaceItems)[number]['id'];

export function readWorkspace(search: string): { workspace: WorkspaceId; notice: string | null } {
  const value = new URLSearchParams(search).get('workspace');
  const aliases: Record<string, WorkspaceId> = {
    inspect: 'design',
    workbench: 'engineering',
    experiment: 'experiments',
    'flight-replay': 'replay',
  };
  if (!value) return { workspace: 'design', notice: null };
  if (Object.hasOwn(aliases, value)) return { workspace: aliases[value], notice: null };
  const match = workspaceItems.find((item) => item.id === value);
  return match
    ? { workspace: match.id, notice: null }
    : { workspace: 'design', notice: `Unknown workspace “${value}”. Showing Design.` };
}

/** Preserve topic, source, run and unrelated URL parameters when changing workspaces. */
export function workspaceHref(href: string, workspace: WorkspaceId): string {
  const url = new URL(href, 'http://local.invalid');
  url.searchParams.set('workspace', workspace);
  return `${url.pathname}${url.search}${url.hash}`;
}

/** A different design must not inherit unvalidated run/part/result associations. */
export function designHref(href: string, design: string): string {
  const url = new URL(href, 'http://local.invalid');
  if (url.searchParams.get('design') !== design) {
    for (const key of ['part', 'run', 'result', 'compare']) url.searchParams.delete(key);
  }
  url.searchParams.set('design', design);
  return `${url.pathname}${url.search}${url.hash}`;
}
