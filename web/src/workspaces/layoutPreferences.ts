import type { WorkspaceId } from './navigation';

export interface LayoutPreferences {
  railOpen: boolean;
  contextOpen: boolean;
  contextTab: 'parts' | 'details';
  contextWidth: number;
  toolsOpen: boolean;
  toolsHeight: number;
  representation: 'auto' | '3d' | '2d';
}
export const LAYOUT_VERSION = 1;
export const CONTEXT_LIMITS = { min: 220, max: 440 };
export const TOOLS_LIMITS = { min: 140, max: 420 };
export const defaultLayout = (): LayoutPreferences => ({
  railOpen: true,
  contextOpen: true,
  contextTab: 'parts',
  contextWidth: 264,
  toolsOpen: false,
  toolsHeight: 240,
  representation: 'auto',
});
const record = (value: unknown): value is Record<string, unknown> =>
  !!value && typeof value === 'object' && !Array.isArray(value);
const clamp = (value: unknown, minimum: number, maximum: number, fallback: number) =>
  typeof value === 'number' && Number.isFinite(value)
    ? Math.min(maximum, Math.max(minimum, Math.round(value)))
    : fallback;

/** Allowlisted UI preferences only: source, run, selection and camera never enter storage. */
export function normalizeLayout(value: unknown): LayoutPreferences {
  const fallback = defaultLayout();
  if (!record(value)) return fallback;
  return {
    railOpen: typeof value.railOpen === 'boolean' ? value.railOpen : fallback.railOpen,
    contextOpen: typeof value.contextOpen === 'boolean' ? value.contextOpen : fallback.contextOpen,
    contextTab: value.contextTab === 'details' ? 'details' : 'parts',
    contextWidth: clamp(
      value.contextWidth,
      CONTEXT_LIMITS.min,
      CONTEXT_LIMITS.max,
      fallback.contextWidth,
    ),
    toolsOpen: typeof value.toolsOpen === 'boolean' ? value.toolsOpen : fallback.toolsOpen,
    toolsHeight: clamp(value.toolsHeight, TOOLS_LIMITS.min, TOOLS_LIMITS.max, fallback.toolsHeight),
    representation:
      value.representation === '2d' || value.representation === '3d'
        ? value.representation
        : 'auto',
  };
}
export const layoutStorageKey = (workspace: WorkspaceId) =>
  `rocket-twin.layout.v${LAYOUT_VERSION}.${workspace}`;
export function parseLayout(serialized: string | null, workspace: WorkspaceId): LayoutPreferences {
  try {
    const value: unknown = JSON.parse(serialized ?? 'null');
    if (!record(value) || value.version !== LAYOUT_VERSION || value.workspace !== workspace)
      return defaultLayout();
    return normalizeLayout(value.preferences);
  } catch {
    return defaultLayout();
  }
}
export interface LayoutStorage {
  getItem: (key: string) => string | null;
  setItem: (key: string, value: string) => void;
}
const memoryPreferences = new Map<WorkspaceId, string>();
export function readLayout(
  workspace: WorkspaceId,
  storage?: LayoutStorage | null,
): LayoutPreferences {
  // Keep the latest session choice even if a quota error left older browser storage behind.
  if (memoryPreferences.has(workspace))
    return parseLayout(memoryPreferences.get(workspace)!, workspace);
  try {
    return parseLayout(
      storage?.getItem(layoutStorageKey(workspace)) ?? memoryPreferences.get(workspace) ?? null,
      workspace,
    );
  } catch {
    return parseLayout(memoryPreferences.get(workspace) ?? null, workspace);
  }
}

/** Compact entry starts with an on-demand context drawer, without changing stored sizes. */
export function compactEntryLayout(
  preferences: LayoutPreferences,
  width: number,
): LayoutPreferences {
  return Number.isFinite(width) && width > 0 && width < 1100
    ? { ...preferences, contextOpen: false }
    : preferences;
}
export function writeLayout(
  workspace: WorkspaceId,
  preferences: LayoutPreferences,
  storage?: LayoutStorage | null,
): boolean {
  const serialized = JSON.stringify({
    version: LAYOUT_VERSION,
    workspace,
    preferences: normalizeLayout(preferences),
  });
  memoryPreferences.set(workspace, serialized);
  try {
    if (!storage) return false;
    storage.setItem(layoutStorageKey(workspace), serialized);
    return true;
  } catch {
    return false;
  }
}
export interface LayoutSession {
  preferences: LayoutPreferences;
  focusSnapshot: LayoutPreferences | null;
}
export type LayoutAction =
  | { type: 'update'; patch: Partial<LayoutPreferences> }
  | { type: 'focus' }
  | { type: 'exit-focus' }
  | { type: 'reset' };
export function layoutReducer(state: LayoutSession, action: LayoutAction): LayoutSession {
  if (action.type === 'reset') return { preferences: defaultLayout(), focusSnapshot: null };
  if (action.type === 'exit-focus')
    return state.focusSnapshot ? { preferences: state.focusSnapshot, focusSnapshot: null } : state;
  if (action.type === 'focus')
    return state.focusSnapshot
      ? { preferences: state.focusSnapshot, focusSnapshot: null }
      : {
          preferences: {
            ...state.preferences,
            railOpen: false,
            contextOpen: false,
            toolsOpen: false,
          },
          focusSnapshot: { ...state.preferences },
        };
  if (state.focusSnapshot && Object.keys(action.patch).every((key) => key === 'representation')) {
    return {
      preferences: normalizeLayout({ ...state.preferences, ...action.patch }),
      focusSnapshot: normalizeLayout({ ...state.focusSnapshot, ...action.patch }),
    };
  }
  // Explicit panel openers exit focus first; editing chrome never changes an inspection identity.
  return {
    preferences: normalizeLayout({
      ...(state.focusSnapshot ?? state.preferences),
      ...action.patch,
    }),
    focusSnapshot: null,
  };
}

export function resizeLayoutValue(
  kind: 'context' | 'tools',
  current: number,
  key: string,
): number | null {
  const limits = kind === 'context' ? CONTEXT_LIMITS : TOOLS_LIMITS;
  if (key === 'Home') return limits.min;
  if (key === 'End') return limits.max;
  const increase = kind === 'context' ? 'ArrowRight' : 'ArrowUp';
  const decrease = kind === 'context' ? 'ArrowLeft' : 'ArrowDown';
  if (key !== increase && key !== decrease) return null;
  return clamp(current + (key === increase ? 16 : -16), limits.min, limits.max, current);
}
