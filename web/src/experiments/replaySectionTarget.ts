/** Presentation destinations only; navigation never edits replay state or the URL. */
export const replaySections = [
  ['scene', 'Scene'],
  ['telemetry', 'Graphs'],
  ['events', 'Events'],
  ['validity', 'Validity'],
  ['details', 'Data & limits'],
] as const;

export type ReplaySection = (typeof replaySections)[number][0];
const workspaceSelector = '[data-replay-workspace]';

/** Never borrow a target from another mounted replay, even inside a nested workspace. */
export function jumpToReplaySection(origin: Element | null, section: ReplaySection): boolean {
  if (!origin?.isConnected || !replaySections.some(([key]) => key === section)) return false;
  const workspace = origin.closest(workspaceSelector);
  if (!workspace?.isConnected) return false;
  const target = Array.from(
    workspace.querySelectorAll<HTMLElement>(`[data-replay-section='${section}']`),
  ).find((candidate) => candidate.closest(workspaceSelector) === workspace);
  if (!target?.isConnected || typeof target.focus !== 'function') return false;
  if (target.tagName === 'DETAILS') (target as HTMLDetailsElement).open = true;
  target.focus({ preventScroll: true });
  if (!origin.isConnected || !workspace.isConnected || !target.isConnected) return false;
  target.scrollIntoView({ behavior: 'auto', block: 'start', inline: 'nearest' });
  return true;
}
