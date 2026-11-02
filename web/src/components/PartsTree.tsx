import { useMemo, useState } from 'react';
import { grams, partName, title } from '../format';
import { useInspection } from '../store';
import type { Part } from '../types';
import { Icon } from './Icons';
import { matchesPartSearch } from './partSearch';

export function PartsTree({
  parts,
  candidateMessage,
}: {
  parts: Part[];
  candidateMessage?: string;
}) {
  const [query, setQuery] = useState('');
  const [collapsed, setCollapsed] = useState<string[]>([]);
  const selectedId = useInspection((s) => s.selectedId);
  const hiddenIds = useInspection((s) => s.hiddenIds);
  const select = useInspection((s) => s.select);
  const hover = useInspection((s) => s.hover);
  const togglePart = useInspection((s) => s.togglePart);
  const showAll = useInspection((s) => s.showAll);
  const ids = useMemo(() => new Set(parts.map((part) => part.id)), [parts]);
  const children = useMemo(() => {
    const map = new Map<string | null, Part[]>();
    for (const part of parts) {
      const parent = part.parent && ids.has(part.parent) ? part.parent : null;
      map.set(parent, [...(map.get(parent) || []), part]);
    }
    return map;
  }, [parts, ids]);
  const filtered = query.trim().toLowerCase();
  const matches = (part: Part) =>
    matchesPartSearch(filtered, {
      id: part.id,
      name: partName(part),
      type: part.type,
      material: part.material,
    });
  const hasMatch = (part: Part): boolean =>
    matches(part) || (children.get(part.id) || []).some(hasMatch);
  function renderPart(part: Part, level: number) {
    if (filtered && !hasMatch(part)) return null;
    const descendants = children.get(part.id) || [];
    const isClosed = !filtered && collapsed.includes(part.id);
    const hidden = hiddenIds.includes(part.id);
    return (
      <li key={part.id}>
        <div
          className={`tree-row ${selectedId === part.id ? 'selected' : ''} ${hidden ? 'is-hidden' : ''}`}
          style={{ paddingLeft: `${10 + level * 15}px` }}
          onMouseEnter={() => hover(part.id)}
          onMouseLeave={() => hover(null)}
        >
          {descendants.length > 0 ? (
            <button
              className={`tree-expand ${isClosed ? '' : 'open'}`}
              aria-label={`${isClosed ? 'Expand' : 'Collapse'} ${partName(part)}`}
              aria-expanded={!isClosed}
              onClick={() =>
                setCollapsed((list) =>
                  list.includes(part.id) ? list.filter((id) => id !== part.id) : [...list, part.id],
                )
              }
            >
              <Icon name="chevron" size={12} />
            </button>
          ) : (
            <span className="tree-leaf" />
          )}
          <button
            className="tree-select"
            aria-pressed={selectedId === part.id}
            onClick={() => select(part.id)}
            title={part.id}
          >
            <span
              className="part-dot"
              style={{ background: part.color || part.cad?.color || '#81959c' }}
            />
            <span className="tree-name">
              {partName(part)}
              <small>{title(part.type)}</small>
            </span>
            <span
              className="tree-mass"
              title={
                descendants.length
                  ? `Subtree: ${grams(part.subtree_mass_kg)}; this part: ${grams(part.mass_kg)}`
                  : undefined
              }
            >
              {grams(descendants.length ? part.subtree_mass_kg : part.mass_kg)}
              {descendants.length > 0 && <small>subtree</small>}
            </span>
          </button>
          <button
            className="icon-button visibility-button"
            title={`${hidden ? 'Show' : 'Hide'} ${partName(part)}`}
            aria-label={`${hidden ? 'Show' : 'Hide'} ${partName(part)}`}
            aria-pressed={!hidden}
            onClick={() => togglePart(part.id)}
          >
            <Icon name={hidden ? 'eyeOff' : 'eye'} size={14} />
          </button>
        </div>
        {!isClosed && descendants.length > 0 && (
          <ul>{descendants.map((child) => renderPart(child, level + 1))}</ul>
        )}
      </li>
    );
  }
  return (
    <aside className="parts-panel" aria-label="Parts tree">
      <div className="panel-heading">
        <span className="eyebrow">Assembly</span>
        <span className="count">{parts.length} parts</span>
      </div>
      <h2>Parts explorer</h2>
      <label className="search-field">
        <Icon name="search" size={15} />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Find name or part ID…"
          aria-label="Search parts"
        />
        <kbd>/</kbd>
      </label>
      <div className="tree-toolbar">
        <span>{parts.length - hiddenIds.length} visible</span>
        <button onClick={showAll} disabled={!hiddenIds.length}>
          Show all
        </button>
      </div>
      <div className="tree-scroll">
        <ul className="parts-tree">
          {(children.get(null) || []).map((part) => renderPart(part, 0))}
        </ul>
        {filtered && !parts.some(matches) && (
          <p className="empty-copy">No parts match “{query}”.</p>
        )}
      </div>
      <div className="candidate-section">
        <span className="eyebrow">Candidate designs</span>
        <p>{candidateMessage || 'No separate candidate snapshots are available.'}</p>
      </div>
      <div className="parts-footer">
        <Icon name="cube" size={15} />
        <span>
          Click any part to inspect.
          <br />
          Eye controls change visibility only.
        </span>
      </div>
    </aside>
  );
}
