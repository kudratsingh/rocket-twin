import { useEffect, useMemo, useRef, useState } from 'react';
import { grams, partName } from '../format';
import { useInspection } from '../store';
import type { InspectionDocument, Part } from '../types';
import { Icon } from './Icons';
import { matchesPartSearch } from './partSearch';
import { presentationGroups, recordedQuantity, representationLabel } from './presentationGroups';
import { FinAlternatives } from './FinAlternatives';
import { functionalGroupOpen } from './groupExpansion.ts';

export function PartsTree({
  parts,
  vehicle,
  candidateMessage,
}: {
  parts: Part[];
  vehicle?: InspectionDocument;
  candidateMessage?: string;
}) {
  const [query, setQuery] = useState('');
  const [collapsedAt, setCollapsedAt] = useState<Record<string, number | undefined>>({});
  const tree = useRef<HTMLDivElement>(null);
  const selectedId = useInspection((s) => s.selectedId);
  const selectionToken = useInspection((s) => s.selectionToken);
  const selectedGroupId = useInspection((s) => s.selectedGroupId);
  const hiddenIds = useInspection((s) => s.hiddenIds);
  const isolatedFrom = useInspection((s) => s.isolatedFrom);
  const groups = useMemo(() => presentationGroups(vehicle), [vehicle]);
  const selectedGroup = groups.find((g) => g.part_ids.includes(selectedId ?? ''));
  useEffect(() => {
    if (selectedGroup)
      useInspection.setState({
        selectedGroupId: selectedGroup.id,
        selectedGroupPartIds: selectedGroup.part_ids,
      });
    tree.current?.querySelector('[data-selected="true"]')?.scrollIntoView?.({ block: 'nearest' });
  }, [selectedId, selectedGroup]);
  const meshes = parts.filter((p) => p.mesh_url);
  const filtered = query.trim().toLowerCase();
  const matches = (part: Part) =>
    matchesPartSearch(filtered, {
      id: part.id,
      name: partName(part),
      type: part.type,
      material: part.material,
    });
  function row(part: Part) {
    const hidden = hiddenIds.includes(part.id);
    return (
      <li key={part.id}>
        <div
          className={`tree-row ${selectedId === part.id ? 'selected' : ''} ${hidden ? 'is-hidden' : ''}`}
          data-selected={selectedId === part.id}
          onMouseEnter={() => useInspection.getState().hover(part.id)}
          onMouseLeave={() => useInspection.getState().hover(null)}
        >
          <button
            className="tree-select"
            aria-pressed={selectedId === part.id}
            title={part.id}
            onClick={() => useInspection.getState().select(part.id)}
          >
            <span
              className="part-dot"
              style={{ background: part.color || part.cad?.color || '#81959c' }}
            />
            <span className="tree-name">
              {partName(part)}
              <small>{representationLabel(part)}</small>
              {recordedQuantity(part) && <small>{recordedQuantity(part)}</small>}
            </span>
            <span className="tree-mass">{grams(part.mass_kg)}</span>
          </button>
          <button
            className="icon-button visibility-button"
            disabled={!part.mesh_url}
            title={
              part.mesh_url
                ? `${hidden ? 'Show' : 'Hide'} ${partName(part)}`
                : 'No separate display solid'
            }
            aria-label={`${hidden ? 'Show' : 'Hide'} ${partName(part)}`}
            aria-pressed={!hidden && !!part.mesh_url}
            onClick={() => useInspection.getState().togglePart(part.id)}
          >
            <Icon name={hidden ? 'eyeOff' : 'eye'} size={14} />
          </button>
        </div>
      </li>
    );
  }
  return (
    <aside className="parts-panel" aria-label="Parts tree">
      <div className="panel-heading">
        <span className="eyebrow">Functional assemblies</span>
        <span className="count">
          {parts.length} records · {meshes.length} meshes
        </span>
      </div>
      <h2>Parts explorer</h2>
      <label className="search-field">
        <Icon name="search" size={15} />
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Find name or part ID…"
          aria-label="Search parts"
        />
      </label>
      <PartsVisibilityControls
        meshCount={meshes.length}
        visibleCount={meshes.filter((p) => !hiddenIds.includes(p.id)).length}
        hasHidden={hiddenIds.length > 0}
        isolated={isolatedFrom !== null}
        onExit={() => useInspection.getState().exitIsolate()}
        onShowAll={() => useInspection.getState().showAll()}
      />
      <div className="tree-scroll" ref={tree}>
        {groups.length ? (
          groups.map((group) => {
            const entries = parts.filter(
              (p) => group.part_ids.includes(p.id) && (!filtered || matches(p)),
            );
            if (filtered && !entries.length) return null;
            const open = functionalGroupOpen(
              group.id,
              !!filtered,
              selectedGroup?.id ?? selectedGroupId,
              selectionToken,
              collapsedAt,
            );
            const meshIds = entries.filter((p) => p.mesh_url).map((p) => p.id);
            return (
              <section className="functional-group" key={group.id}>
                <div className="functional-group-heading">
                  <button
                    aria-label={`${open ? 'Collapse' : 'Expand'} ${group.label}`}
                    aria-expanded={open}
                    onClick={() =>
                      setCollapsedAt((state) => ({
                        ...state,
                        [group.id]: open ? selectionToken : undefined,
                      }))
                    }
                  >
                    <Icon name="chevron" size={12} />
                  </button>
                  <button
                    aria-pressed={selectedGroupId === group.id}
                    onClick={() => useInspection.getState().selectGroup(group.id, group.part_ids)}
                  >
                    {group.label}
                    <small>
                      {group.part_ids.length} records ·{' '}
                      {parts.filter((p) => group.part_ids.includes(p.id) && p.mesh_url).length}{' '}
                      meshes
                    </small>
                  </button>
                </div>
                {open && (
                  <>
                    <p className="small muted">{group.description}</p>
                    <div className="group-actions">
                      <button
                        disabled={!meshIds.length}
                        onClick={() => {
                          useInspection.getState().selectGroup(group.id, group.part_ids);
                          useInspection.getState().fitVisible();
                        }}
                      >
                        Frame group
                      </button>
                      <button
                        disabled={!meshIds.length}
                        onClick={() => {
                          useInspection.getState().selectGroup(group.id, group.part_ids);
                          useInspection.getState().isolateGroup(group.part_ids);
                        }}
                      >
                        Isolate group
                      </button>
                    </div>
                    {group.id === 'fins_roots' && vehicle && <FinAlternatives design={vehicle} />}
                    <ul className="parts-tree">{entries.map(row)}</ul>
                  </>
                )}
              </section>
            );
          })
        ) : (
          <>
            <p className="small muted">
              Functional grouping unavailable for this source. Flat source records below do not
              imply physical attachments.
            </p>
            <ul className="parts-tree">{parts.filter((p) => !filtered || matches(p)).map(row)}</ul>
          </>
        )}
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
          Records can describe several pieces or a mass allowance. Grouping describes function, not
          a verified joint.
        </span>
      </div>
    </aside>
  );
}

/** Exit is independent of single-part selection, including functional-group isolation. */
export function PartsVisibilityControls({
  meshCount,
  visibleCount,
  hasHidden,
  isolated,
  onExit,
  onShowAll,
}: {
  meshCount: number;
  visibleCount: number;
  hasHidden: boolean;
  isolated: boolean;
  onExit: () => void;
  onShowAll: () => void;
}) {
  return (
    <div className="tree-toolbar">
      <span>
        {visibleCount} / {meshCount} meshes visible
      </span>
      {isolated && <button onClick={onExit}>Exit isolation</button>}
      <button onClick={onShowAll} disabled={!hasHidden}>
        Show all
      </button>
    </div>
  );
}
