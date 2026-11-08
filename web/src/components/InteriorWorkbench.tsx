import { useEffect, useState } from 'react';
import type { InspectionDocument } from '../types';
import { useInspection } from '../store';
import { presentationGroups } from './presentationGroups';
import { interiorHiddenIds, interiorShellIds, type InteriorSnapshot } from './interiorWorkflow';
import { loadRp1Detail, type Rp1DetailView } from './rp1Detail';
import { FinAlternatives } from './FinAlternatives';
import './interiorWorkbench.css';
export function InteriorWorkbench({
  vehicle,
  onDetailMeshesChange,
}: {
  vehicle: InspectionDocument;
  onDetailMeshesChange?: (meshes: Record<string, string>) => void;
}) {
  const [catalog, setCatalog] = useState<Rp1DetailView | null>(null);
  const [detailed, setDetailed] = useState(true);
  const [detailError, setDetailError] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    void loadRp1Detail(vehicle, controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) {
          setCatalog(value);
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
  }, [catalog, detailed, onDetailMeshesChange]);
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
      {vehicle.id === 'G80-F2-RP1-AD1-definition-v2' && (
        <FinAlternatives design={vehicle} compact />
      )}
      <label className="detail-toggle">
        <input
          type="checkbox"
          checked={detailed && !!catalog}
          disabled={!catalog}
          onChange={(e) => setDetailed(e.target.checked)}
        />
        Source detail
      </label>
      <details className="interior-coverage">
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
      <span className="interior-status">
        {interior
          ? 'Outer shell hidden · source positions retained'
          : 'Drag to rotate · scroll or pinch to zoom'}
      </span>
    </div>
  );
}
