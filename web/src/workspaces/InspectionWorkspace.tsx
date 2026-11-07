import { createContext, useCallback, useContext, useEffect, useId, useRef, useState } from 'react';
import type { CSSProperties, ReactNode } from 'react';
import { createPortal } from 'react-dom';
import { useWorkspaceLayout } from './workspaceLayoutContext';
import { CONTEXT_LIMITS, TOOLS_LIMITS, resizeLayoutValue } from './layoutPreferences';
import './workspaces.css';

const InspectionDetailsContext = createContext<(() => void) | null>(null);
export const useOpenInspectionDetails = () => useContext(InspectionDetailsContext);

/** Stable child positions keep the renderer mounted through panel and focus toggles. */
interface InspectionWorkspaceProps {
  tree: ReactNode;
  visual: ReactNode;
  inspector: ReactNode;
  source?: ReactNode;
}

export function InspectionWorkspace(props: InspectionWorkspaceProps) {
  const layout = useWorkspaceLayout();
  return layout ? (
    <RevampedInspectionWorkspace {...props} />
  ) : (
    <LegacyInspectionWorkspace {...props} />
  );
}

function LegacyInspectionWorkspace({ tree, visual, inspector }: InspectionWorkspaceProps) {
  const id = useId();
  const [treeOpen, setTreeOpen] = useState(true);
  const [inspectorOpen, setInspectorOpen] = useState(true);
  const [focused, setFocused] = useState(false);
  const focusButton = useRef<HTMLButtonElement>(null);
  const inspectorPanel = useRef<HTMLDivElement>(null);
  const treePanel = useRef<HTMLDivElement>(null);

  function openDetails() {
    setInspectorOpen(true);
    setFocused(false);
    window.requestAnimationFrame(() => {
      inspectorPanel.current?.scrollIntoView({ block: 'nearest', behavior: 'auto' });
      inspectorPanel.current?.focus({ preventScroll: true });
    });
  }
  const openParts = useCallback(() => {
    setTreeOpen(true);
    setFocused(false);
    window.requestAnimationFrame(() => {
      treePanel.current?.scrollIntoView({ block: 'nearest', behavior: 'auto' });
      treePanel.current?.querySelector<HTMLInputElement>('input')?.focus({ preventScroll: true });
    });
  }, []);

  useEffect(() => {
    function find(event: KeyboardEvent) {
      if (
        event.key !== '/' ||
        event.defaultPrevented ||
        event.ctrlKey ||
        event.metaKey ||
        event.altKey
      )
        return;
      if (
        event.target instanceof HTMLElement &&
        (['INPUT', 'SELECT', 'TEXTAREA'].includes(event.target.tagName) ||
          event.target.isContentEditable)
      )
        return;
      event.preventDefault();
      event.stopImmediatePropagation();
      openParts();
    }
    window.addEventListener('keydown', find, true);
    return () => window.removeEventListener('keydown', find, true);
  }, [openParts]);

  useEffect(() => {
    if (!focused) return;
    function escape(event: KeyboardEvent) {
      if (event.key !== 'Escape' || event.defaultPrevented) return;
      event.preventDefault();
      event.stopImmediatePropagation();
      setFocused(false);
      focusButton.current?.focus();
    }
    // Capture before the legacy window shortcut can clear the selected part.
    window.addEventListener('keydown', escape, true);
    return () => window.removeEventListener('keydown', escape, true);
  }, [focused]);

  return (
    <InspectionDetailsContext.Provider value={openDetails}>
      <main
        className={`research-inspection${focused ? ' is-focused' : ''}`}
        aria-label="Design inspection"
      >
        <div className="research-panel-controls" aria-label="Inspection layout">
          <button
            type="button"
            aria-expanded={treeOpen && !focused}
            aria-controls={`${id}-tree`}
            disabled={focused}
            onClick={() => setTreeOpen((open) => !open)}
          >
            {treeOpen ? 'Hide' : 'Show'} parts
          </button>
          <button type="button" onClick={openParts}>
            Find a component
          </button>
          <button type="button" onClick={openDetails}>
            Open component details
          </button>
          <button
            type="button"
            aria-expanded={inspectorOpen && !focused}
            aria-controls={`${id}-inspector`}
            disabled={focused}
            onClick={() => setInspectorOpen((open) => !open)}
          >
            {inspectorOpen ? 'Hide' : 'Show'} details
          </button>
          <button
            ref={focusButton}
            type="button"
            aria-pressed={focused}
            onClick={() => setFocused((value) => !value)}
          >
            {focused ? 'Exit focus view' : 'Focus view'}
          </button>
          <span>
            {focused
              ? 'Escape restores panels and keeps selection.'
              : 'Panels can be hidden to enlarge the view.'}
          </span>
        </div>
        <div
          className="research-inspection-grid"
          data-tree={treeOpen && !focused}
          data-inspector={inspectorOpen && !focused}
        >
          <div
            ref={treePanel}
            id={`${id}-tree`}
            className="research-tree"
            hidden={!treeOpen || focused}
          >
            {tree}
          </div>
          <div className="research-visual">{visual}</div>
          <div
            ref={inspectorPanel}
            id={`${id}-inspector`}
            className="research-inspector"
            role="region"
            tabIndex={-1}
            aria-label="Component details panel"
            hidden={!inspectorOpen || focused}
          >
            {inspector}
          </div>
        </div>
      </main>
    </InspectionDetailsContext.Provider>
  );
}

const InspectionToolsContext = createContext<HTMLDivElement | null | undefined>(undefined);
/** In revamp mode children mount once the stable drawer target exists, then stay mounted. */
export function InspectionTools({ children }: { children: ReactNode }) {
  const target = useContext(InspectionToolsContext);
  if (target === undefined) return <>{children}</>;
  return target ? createPortal(children, target) : null;
}

function LayoutSplitter({
  kind,
  value,
  controls,
  onChange,
  onCollapse,
}: {
  kind: 'context' | 'tools';
  value: number;
  controls: string;
  onChange: (value: number) => void;
  onCollapse: () => void;
}) {
  const drag = useRef<{ coordinate: number; value: number } | null>(null);
  const limits = kind === 'context' ? CONTEXT_LIMITS : TOOLS_LIMITS;
  return (
    <div
      className={`revamp-splitter revamp-splitter-${kind}`}
      role="separator"
      tabIndex={0}
      aria-label={kind === 'context' ? 'Resize context sidebar' : 'Resize scene tools'}
      aria-orientation={kind === 'context' ? 'vertical' : 'horizontal'}
      aria-controls={controls}
      aria-valuemin={limits.min}
      aria-valuemax={limits.max}
      aria-valuenow={value}
      aria-valuetext={`${value} pixels; arrow keys resize, Enter collapses`}
      onKeyDown={(event) => {
        if (event.key === 'Enter') {
          event.preventDefault();
          onCollapse();
          return;
        }
        const next = resizeLayoutValue(kind, value, event.key);
        if (next !== null) {
          event.preventDefault();
          onChange(next);
        }
      }}
      onPointerDown={(event) => {
        if (event.button !== 0) return;
        event.preventDefault();
        event.currentTarget.focus();
        event.currentTarget.setPointerCapture(event.pointerId);
        drag.current = { coordinate: kind === 'context' ? event.clientX : event.clientY, value };
      }}
      onPointerMove={(event) => {
        if (!drag.current || !event.currentTarget.hasPointerCapture(event.pointerId)) return;
        const coordinate = kind === 'context' ? event.clientX : event.clientY;
        const delta = (coordinate - drag.current.coordinate) * (kind === 'context' ? 1 : -1);
        onChange(Math.min(limits.max, Math.max(limits.min, drag.current.value + delta)));
      }}
      onPointerUp={(event) => {
        drag.current = null;
        if (event.currentTarget.hasPointerCapture(event.pointerId))
          event.currentTarget.releasePointerCapture(event.pointerId);
      }}
      onPointerCancel={() => {
        drag.current = null;
      }}
    >
      <span aria-hidden="true" />
    </div>
  );
}

function RevampedInspectionWorkspace({
  tree,
  visual,
  inspector,
  source,
}: InspectionWorkspaceProps) {
  const layout = useWorkspaceLayout()!;
  const { preferences, id } = layout;
  const [toolsTarget, setToolsTarget] = useState<HTMLDivElement | null>(null);
  const targetRef = useCallback((node: HTMLDivElement | null) => setToolsTarget(node), []);
  const openDetails = useCallback(() => layout.openContext('details'), [layout]);
  const style = {
    '--revamp-context-width': `${preferences.contextWidth}px`,
    '--revamp-tools-height': `${preferences.toolsHeight}px`,
  } as CSSProperties;
  return (
    <InspectionDetailsContext.Provider value={openDetails}>
      <InspectionToolsContext.Provider value={toolsTarget}>
        <main
          className="revamp-inspection"
          aria-label="Design inspection"
          data-context={preferences.contextOpen}
          data-tools={preferences.toolsOpen}
          style={style}
        >
          <aside
            className="revamp-context"
            id={`${id}-context`}
            aria-label="Design context sidebar"
            hidden={!preferences.contextOpen}
            onKeyDown={(event) => {
              if (event.key === 'Escape' && !event.defaultPrevented) {
                event.preventDefault();
                event.stopPropagation();
                layout.closeContext();
              }
            }}
          >
            <div className="revamp-context-tabs" role="tablist" aria-label="Design context">
              {(['parts', 'details'] as const).map((tab) => (
                <button
                  key={tab}
                  type="button"
                  role="tab"
                  id={`${id}-tab-${tab}`}
                  aria-controls={`${id}-${tab}`}
                  aria-selected={preferences.contextTab === tab}
                  tabIndex={preferences.contextTab === tab ? 0 : -1}
                  onClick={() => layout.updatePreferences({ contextTab: tab })}
                  onKeyDown={(event) => {
                    if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) {
                      event.preventDefault();
                      const next =
                        event.key === 'Home'
                          ? 'parts'
                          : event.key === 'End'
                            ? 'details'
                            : tab === 'parts'
                              ? 'details'
                              : 'parts';
                      layout.updatePreferences({ contextTab: next });
                      document.getElementById(`${id}-tab-${next}`)?.focus();
                    }
                  }}
                >
                  {tab === 'parts' ? 'Parts' : 'Details'}
                </button>
              ))}
              <button
                type="button"
                className="revamp-context-close"
                aria-label="Close context sidebar"
                onClick={layout.closeContext}
              >
                ×
              </button>
            </div>
            <div
              id={`${id}-parts`}
              className="revamp-context-panel revamp-parts-panel"
              role="tabpanel"
              aria-labelledby={`${id}-tab-parts`}
              tabIndex={-1}
              hidden={preferences.contextTab !== 'parts'}
            >
              {tree}
            </div>
            <div
              id={`${id}-details`}
              className="revamp-context-panel revamp-details-panel"
              role="tabpanel"
              aria-labelledby={`${id}-tab-details`}
              tabIndex={-1}
              hidden={preferences.contextTab !== 'details'}
            >
              {inspector}
              <details className="revamp-context-source">
                <summary>Source, status & limitations</summary>
                {layout.source}
                {source}
              </details>
            </div>
          </aside>
          <div className="revamp-context-resizer" hidden={!preferences.contextOpen}>
            <LayoutSplitter
              kind="context"
              value={preferences.contextWidth}
              controls={`${id}-context`}
              onChange={(contextWidth) => layout.updatePreferences({ contextWidth })}
              onCollapse={layout.closeContext}
            />
          </div>
          <div className="revamp-inspection-visual">{visual}</div>
          <section className="revamp-tools-drawer" aria-label="Scene tools drawer">
            <div className="revamp-tools-resizer" hidden={!preferences.toolsOpen}>
              <LayoutSplitter
                kind="tools"
                value={preferences.toolsHeight}
                controls={`${id}-tools-content`}
                onChange={(toolsHeight) => layout.updatePreferences({ toolsHeight })}
                onCollapse={layout.toggleTools}
              />
            </div>
            <div className="revamp-tools-strip">
              <button
                type="button"
                id={`${id}-tools-toggle`}
                aria-expanded={preferences.toolsOpen}
                aria-controls={`${id}-tools-content`}
                onClick={layout.toggleTools}
              >
                {preferences.toolsOpen ? 'Close scene tools' : 'Scene tools'}
              </button>
              <span>View options · source evidence</span>
              <button type="button" onClick={() => layout.openContext('details')}>
                Component details
              </button>
            </div>
            <div
              ref={targetRef}
              id={`${id}-tools-content`}
              className="revamp-tools-content"
              hidden={!preferences.toolsOpen}
              onKeyDown={(event) => {
                if (event.key === 'Escape' && !event.defaultPrevented) {
                  event.preventDefault();
                  event.stopPropagation();
                  layout.toggleTools();
                }
              }}
            />
          </section>
        </main>
      </InspectionToolsContext.Provider>
    </InspectionDetailsContext.Provider>
  );
}
