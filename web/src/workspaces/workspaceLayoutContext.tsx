import { ownedByOpenDialog } from './modalOwnership';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useId,
  useMemo,
  useReducer,
  useRef,
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
  dismissContext: () => void;
  toggleContext: () => void;
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
/** Wait for hidden state to commit, then return to a usable opener or the stable panel control. */
export function restorePanelFocus(id: string, opener: HTMLElement | null = null) {
  if (typeof window !== 'undefined')
    window.requestAnimationFrame(() => {
      const usable = (target: HTMLElement | null): target is HTMLElement =>
        !!target &&
        target.isConnected &&
        target.tabIndex >= 0 &&
        !target.closest('[hidden], [inert]') &&
        !target.matches(':disabled') &&
        target.getClientRects().length > 0 &&
        window.getComputedStyle(target).visibility !== 'hidden' &&
        window.getComputedStyle(target).visibility !== 'collapse';
      const target = usable(opener) ? opener : document.getElementById(id);
      if (usable(target)) target.focus();
    });
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
  const contextOpener = useRef<HTMLElement | null>(null);
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
      if (
        typeof document !== 'undefined' &&
        document.activeElement instanceof HTMLElement &&
        document.activeElement.tabIndex >= 0 &&
        !document.getElementById(`${id}-context`)?.contains(document.activeElement)
      )
        contextOpener.current = document.activeElement;
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
    restorePanelFocus(`${id}-context-toggle`);
  }, [id]);
  const dismissContext = useCallback(() => {
    dispatch({ type: 'update', patch: { contextOpen: false } });
    restorePanelFocus(`${id}-context-toggle`, contextOpener.current);
  }, [id]);
  const toggleContext = useCallback(() => {
    if (state.preferences.contextOpen) closeContext();
    else openContext(state.preferences.contextTab);
  }, [state.preferences.contextOpen, state.preferences.contextTab, closeContext, openContext]);
  const toggleFocus = useCallback(() => {
    dispatch({ type: 'focus' });
    restorePanelFocus(`${id}-focus`);
  }, [id]);
  const resetLayout = useCallback(() => {
    dispatch({ type: 'reset' });
    restorePanelFocus(`${id}-context-toggle`);
  }, [id]);
  const toggleRail = useCallback(() => {
    dispatch({ type: 'update', patch: { railOpen: !state.preferences.railOpen } });
    if (state.preferences.railOpen) restorePanelFocus(`${id}-rail-toggle`);
  }, [id, state.preferences.railOpen]);
  const toggleTools = useCallback(() => {
    dispatch({ type: 'update', patch: { toolsOpen: !state.preferences.toolsOpen } });
    if (state.preferences.toolsOpen) restorePanelFocus(`${id}-tools-toggle`);
  }, [id, state.preferences.toolsOpen]);
  useEffect(() => {
    function keyboard(event: KeyboardEvent) {
      if (event.defaultPrevented || event.ctrlKey || event.altKey || event.metaKey) return;
      if (ownedByOpenDialog(event.target)) return;
      if (event.key === 'Escape' && state.focusSnapshot) {
        event.preventDefault();
        event.stopImmediatePropagation();
        dispatch({ type: 'exit-focus' });
        restorePanelFocus(`${id}-focus`);
        return;
      }
      // Capture before the global selection shortcut, including Escape in the search input.
      if (
        event.key === 'Escape' &&
        state.preferences.contextOpen &&
        event.target instanceof Node &&
        document.getElementById(`${id}-context`)?.contains(event.target)
      ) {
        event.preventDefault();
        event.stopImmediatePropagation();
        dismissContext();
        return;
      }
      if (
        event.key === 'Escape' &&
        window.innerWidth <= 680 &&
        state.preferences.railOpen &&
        event.target instanceof Node &&
        document.getElementById(`${id}-rail`)?.contains(event.target)
      ) {
        event.preventDefault();
        event.stopImmediatePropagation();
        toggleRail();
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
  }, [
    id,
    openContext,
    dismissContext,
    toggleRail,
    state.focusSnapshot,
    state.preferences.contextOpen,
    state.preferences.railOpen,
  ]);
  const value = useMemo(
    () => ({
      preferences: state.preferences,
      focused: !!state.focusSnapshot,
      source,
      id,
      updatePreferences,
      openContext,
      closeContext,
      dismissContext,
      toggleContext,
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
      dismissContext,
      toggleContext,
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
