import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useMemo,
  useReducer,
} from 'react';
import type { ReactNode } from 'react';
import {
  compactEntryLayout,
  defaultLayout,
  layoutReducer,
  readLayout,
  writeLayout,
} from './layoutPreferences';
import type { LayoutPreferences, LayoutStorage } from './layoutPreferences';
import type { WorkspaceId } from './navigation';

interface WorkspaceLayout {
  preferences: LayoutPreferences;
  focused: boolean;
  source: ReactNode;
  id: string;
  updatePreferences: (patch: Partial<LayoutPreferences>) => void;
  openContext: (tab: 'parts' | 'details') => void;
  closeContext: () => void;
  toggleFocus: () => void;
  resetLayout: () => void;
  toggleRail: () => void;
  toggleTools: () => void;
}
const LayoutContext = createContext<WorkspaceLayout | null>(null);
export const useWorkspaceLayout = () => useContext(LayoutContext);
function localStorageOrNull(): LayoutStorage | null {
  try {
    return typeof window === 'undefined' ? null : window.localStorage;
  } catch {
    return null;
  }
}
function focusById(id: string) {
  if (typeof window !== 'undefined')
    window.requestAnimationFrame(() => document.getElementById(id)?.focus());
}
export function WorkspaceLayoutProvider({
  workspace,
  source,
  children,
}: {
  workspace: WorkspaceId;
  source: ReactNode;
  children: ReactNode;
}) {
  const id = useId();
  const [state, dispatch] = useReducer(layoutReducer, undefined, () => ({
    preferences: compactEntryLayout(
      readLayout(workspace, localStorageOrNull()),
      typeof window === 'undefined' ? Infinity : window.innerWidth,
    ),
    focusSnapshot: null,
  }));
  useEffect(() => {
    writeLayout(workspace, state.focusSnapshot ?? state.preferences, localStorageOrNull());
  }, [workspace, state.preferences, state.focusSnapshot]);
  const updatePreferences = useCallback(
    (patch: Partial<LayoutPreferences>) => dispatch({ type: 'update', patch }),
    [],
  );
  const openContext = useCallback(
    (tab: 'parts' | 'details') => {
      dispatch({ type: 'update', patch: { contextOpen: true, contextTab: tab } });
      if (typeof window !== 'undefined')
        window.requestAnimationFrame(() => {
          const panel = document.getElementById(`${id}-${tab}`);
          (tab === 'parts'
            ? (panel?.querySelector<HTMLInputElement>('input') ?? panel)
            : panel
          )?.focus();
        });
    },
    [id],
  );
  const closeContext = useCallback(() => {
    dispatch({ type: 'update', patch: { contextOpen: false } });
    focusById(`${id}-open-${state.preferences.contextTab}`);
  }, [id, state.preferences.contextTab]);
  const toggleFocus = useCallback(() => {
    dispatch({ type: 'focus' });
    focusById(`${id}-focus`);
  }, [id]);
  const resetLayout = useCallback(() => {
    dispatch({ type: 'reset' });
    focusById(`${id}-open-parts`);
  }, [id]);
  const toggleRail = useCallback(
    () => dispatch({ type: 'update', patch: { railOpen: !state.preferences.railOpen } }),
    [state.preferences.railOpen],
  );
  const toggleTools = useCallback(() => {
    dispatch({ type: 'update', patch: { toolsOpen: !state.preferences.toolsOpen } });
    if (state.preferences.toolsOpen) focusById(`${id}-tools-toggle`);
  }, [id, state.preferences.toolsOpen]);
  useEffect(() => {
    function keyboard(event: KeyboardEvent) {
      if (event.defaultPrevented || event.ctrlKey || event.altKey || event.metaKey) return;
      if (event.key === 'Escape' && state.focusSnapshot) {
        event.preventDefault();
        event.stopImmediatePropagation();
        dispatch({ type: 'exit-focus' });
        focusById(`${id}-focus`);
        return;
      }
      if (
        event.target instanceof HTMLElement &&
        (['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName) ||
          event.target.isContentEditable)
      )
        return;
      if (event.key === '/') {
        event.preventDefault();
        event.stopImmediatePropagation();
        openContext('parts');
      }
    }
    window.addEventListener('keydown', keyboard, true);
    return () => window.removeEventListener('keydown', keyboard, true);
  }, [id, openContext, state.focusSnapshot]);
  const value = useMemo(
    () => ({
      preferences: state.preferences,
      focused: !!state.focusSnapshot,
      source,
      id,
      updatePreferences,
      openContext,
      closeContext,
      toggleFocus,
      resetLayout,
      toggleRail,
      toggleTools,
    }),
    [
      state,
      source,
      id,
      updatePreferences,
      openContext,
      closeContext,
      toggleFocus,
      resetLayout,
      toggleRail,
      toggleTools,
    ],
  );
  return <LayoutContext.Provider value={value}>{children}</LayoutContext.Provider>;
}

/** Kept exported for pure consumers and SSR fixtures without storage access. */
export { defaultLayout };
