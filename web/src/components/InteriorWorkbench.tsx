import { useEffect, useRef, useState } from 'react';
import type { InspectionDocument } from '../types';
import { useInspection } from '../store';
import { presentationGroups } from './presentationGroups';
import { interiorHiddenIds, interiorShellIds, type InteriorSnapshot } from './interiorWorkflow';
import {
  detailForDocument,
  loadRp1Detail,
  type Rp1DetailView,
  type Rp1DetailSnapshot,
  type Rp1DetailCase,
} from './rp1Detail';
import { useWorkspaceLayout } from '../workspaces/workspaceLayoutContext';
import { FinAlternatives } from './FinAlternatives';
import './interiorWorkbench.css';
export function InteriorWorkbench({
  vehicle,
  onDetailMeshesChange,
  onDetailViewChange,
}: {
  vehicle: InspectionDocument;
  onDetailMeshesChange?: (meshes: Record<string, string>) => void;
  onDetailViewChange?: (source: InspectionDocument, view: Rp1DetailView | null) => void;
}) {
  const [loadedDetail, setLoadedDetail] = useState<Rp1DetailSnapshot | null>(null);
  const catalog = detailForDocument(loadedDetail, vehicle);
  const layout = useWorkspaceLayout();
  const coverageRef = useRef<HTMLDetailsElement>(null);
  const [detailed, setDetailed] = useState(true);
  const [detailError, setDetailError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    void loadRp1Detail(vehicle, controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) {
          setLoadedDetail({ source: vehicle, detail: value });
          setDetailError(
            value
              ? ''
              : 'Optional source-detail assets unavailable; base inspection remains usable.',
          );
        }
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setDetailError(
            'Optional source-detail assets unavailable; base inspection remains usable.',
          );
      });
    return () => controller.abort();
  }, [vehicle]);
  useEffect(() => {
    onDetailMeshesChange?.(detailed && catalog ? catalog.detailMeshes : {});
    onDetailViewChange?.(vehicle, detailed ? catalog : null);
  }, [catalog, detailed, vehicle, onDetailMeshesChange, onDetailViewChange]);
  const [previous, setPrevious] = useState<InteriorSnapshot | null>(null);
  const hidden = useInspection((s) => s.hiddenIds);
  const groupId = useInspection((s) => s.selectedGroupId);
  const groups = presentationGroups(vehicle);
  const shells = interiorShellIds(vehicle);
  const interior =
    previous !== null && shells.length > 0 && shells.every((id) => hidden.includes(id));
  const capture = () => {
    const s = useInspection.getState();
    return {
      hiddenIds: [...s.hiddenIds],
      exploded: s.exploded,
      section: s.section,
      ghostShell: s.ghostShell,
    };
  };
  function inspect(id?: string) {
    const group = groups.find((g) => g.id === id);
    const base = interior && previous ? previous : capture();
    if (!interior || !previous) setPrevious(base);
    useInspection.setState({
      hiddenIds: interiorHiddenIds(vehicle, base, group?.part_ids),
      isolatedFrom: null,
      exploded: 0,
      section: false,
      ghostShell: false,
    });
    if (group) useInspection.getState().selectGroup(group.id, group.part_ids);
    else useInspection.setState({ selectedGroupId: null, selectedGroupPartIds: [] });
    useInspection.getState().fitVisible();
  }
  function inspectCase(item: Rp1DetailCase) {
    const ids = item.partIds.filter((id) => vehicle.parts.some((p) => p.id === id && p.mesh_url));
    const target = item.replacementPartIds.find((id) => ids.includes(id)) ?? ids[0];
    if (!target) return;
    const base = interior && previous ? previous : capture();
    setPrevious(base);
    useInspection.setState({
      hiddenIds: vehicle.parts.filter((p) => p.mesh_url && !ids.includes(p.id)).map((p) => p.id),
      isolatedFrom: null,
      exploded: 0,
      section: false,
      ghostShell: false,
      selectedGroupId: null,
      selectedGroupPartIds: [],
    });
    useInspection.getState().select(target);
    useInspection.getState().focusPart(target);
    if (coverageRef.current) coverageRef.current.open = false;
  }
  function restore() {
    if (previous)
      useInspection.setState({
        ...previous,
        hiddenIds: [...previous.hiddenIds],
        isolatedFrom: null,
        selectedGroupId: null,
        selectedGroupPartIds: [],
      });
    else useInspection.getState().showAll();
    setPrevious(null);
    useInspection.getState().fitVisible();
  }
  return (
    <div className="interior-workbench" aria-label="Interior inspection workflow">
      <div
        className="inspection-control-group interior-inspect-group"
        role="group"
        aria-label="Inspect assembly"
      >
        <span className="inspection-control-label">Inspect</span>
        <button
          className="interior-primary"
          aria-pressed={interior}
          disabled={!shells.length}
          onClick={() => (interior ? restore() : inspect())}
        >
          {interior ? 'Restore visibility' : 'Inspect interior'}
        </button>
        <label>
          <span className="sr-only">Inspect subsystem</span>
          <select
            aria-label="Inspect subsystem"
            value={interior ? (groupId ?? '') : ''}
            onChange={(e) => inspect(e.target.value)}
          >
            <option value="">Choose internal assembly…</option>
            {groups
              .filter((g) => g.id !== 'launch_finish' && g.id !== 'nose_airframe')
              .map((g) => (
                <option key={g.id} value={g.id}>
                  {g.label}
                </option>
              ))}
          </select>
        </label>
        <button
          type="button"
          onClick={() => {
            const state = useInspection.getState();
            if (!state.section) state.toggleSection();
            layout?.updatePreferences({ toolsOpen: true });
          }}
        >
          Adjust section cut
        </button>
      </div>
      <div
        className="inspection-control-group interior-source-group"
        role="group"
        aria-label="Source detail"
      >
        <span className="inspection-control-label">Source</span>
        <label className="detail-toggle">
          <input
            type="checkbox"
            aria-label="Source detail"
            checked={detailed && !!catalog}
            disabled={!catalog}
            onChange={(e) => setDetailed(e.target.checked)}
          />
          Detail
        </label>
        <details
          className="interior-coverage"
          ref={coverageRef}
          onKeyDown={(event) => {
            if (event.key !== 'Escape') return;
            event.currentTarget.open = false;
            event.currentTarget.querySelector('summary')?.focus();
            event.stopPropagation();
            event.preventDefault();
          }}
        >
          <summary>Detail coverage</summary>
          <div>
            {catalog ? (
              <>
                <p>
                  Higher-detail source features for3 records. Electronics/recovery boxes remain
                  envelopes where hardware details are unavailable.
                </p>
                <ul>
                  {catalog.cases.map((c) => (
                    <li key={c.id}>
                      <strong>{c.label}</strong>: {c.supportedFeatures.join('; ')}. Missing:{' '}
                      {c.missing.join('; ')}.
                      <button type="button" onClick={() => inspectCase(c)}>
                        Inspect modeled detail
                      </button>
                      <ul>
                        {catalog.annotations
                          .filter((a) => c.partIds.includes(a.partId))
                          .map((a) => (
                            <li key={a.id}>
                              {a.label}: {Number(a.value.toFixed(3))} {a.units} · source nominal
                              <small>
                                {' '}
                                · {a.source.path} · {a.source.locator}
                              </small>
                            </li>
                          ))}
                      </ul>
                    </li>
                  ))}
                </ul>
                <p>
                  Separate display detail revision: <code>{catalog.detailSha256}</code>. No
                  manufacturing or strength acceptance.
                </p>
              </>
            ) : (
              <p>{detailError || 'Loading optional source-detail catalog…'}</p>
            )}
          </div>
        </details>
      </div>
      {vehicle.id === 'G80-F2-RP1-AD1-definition-v2' && (
        <div
          className="inspection-control-group interior-alternatives-group"
          role="group"
          aria-label="Alternatives"
        >
          <span className="inspection-control-label">Alternatives</span>
          <FinAlternatives design={vehicle} compact />
        </div>
      )}
      <span className="interior-status">
        {interior
          ? 'Outer shell hidden · source positions retained'
          : 'Drag to rotate · scroll or pinch to zoom'}
      </span>
    </div>
  );
}
