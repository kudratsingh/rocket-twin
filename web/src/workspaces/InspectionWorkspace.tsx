import { useEffect, useId, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import './workspaces.css';

/** Stable child positions keep the renderer mounted through panel and focus toggles. */
export function InspectionWorkspace({
  tree,
  visual,
  inspector,
}: {
  tree: ReactNode;
  visual: ReactNode;
  inspector: ReactNode;
}) {
  const id = useId();
  const [treeOpen, setTreeOpen] = useState(true);
  const [inspectorOpen, setInspectorOpen] = useState(true);
  const [focused, setFocused] = useState(false);
  const focusButton = useRef<HTMLButtonElement>(null);

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
        <div id={`${id}-tree`} className="research-tree" hidden={!treeOpen || focused}>
          {tree}
        </div>
        <div className="research-visual">{visual}</div>
        <div
          id={`${id}-inspector`}
          className="research-inspector"
          hidden={!inspectorOpen || focused}
        >
          {inspector}
        </div>
      </div>
    </main>
  );
}
