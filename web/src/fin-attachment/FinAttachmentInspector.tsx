import { useMemo, useState } from 'react';
import type { InspectionDocument } from '../types';
import catalogSource from '../../../docs/studies/frontend-fin-attachment-20261109/geometry.json';
import { admitFinAttachmentCatalog } from './finAttachment';
import type { FinCatalog, FinSectionId } from './finAttachment';
import { FinAttachmentScene } from './FinAttachmentScene';
import type { FitCommand } from './FinAttachmentScene';
import { validFinAttachmentState } from './finAttachmentState';
import type { FinAttachmentState } from './finAttachmentState';
import './finAttachment.css';

const sectionLabels: Record<FinSectionId, string> = {
  assembled: 'Assembled',
  longitudinal: 'Longitudinal through fin',
  transverse: 'Transverse at slot',
};

function DimensionValue({ value, tolerance }: { value: number; tolerance: number | null }) {
  return (
    <>
      {value.toFixed(2)} mm{tolerance === null ? '' : ` ± ${tolerance.toFixed(2)} mm`}
    </>
  );
}

function PartsSidebar({
  catalog,
  state,
  onChange,
  visibleIds,
}: {
  catalog: FinCatalog;
  state: FinAttachmentState;
  onChange: (state: FinAttachmentState) => void;
  visibleIds: Set<string>;
}) {
  if (!state.partsSidebarOpen)
    return (
      <aside className="fin-attachment-sidebar collapsed" aria-label="Parts sidebar collapsed">
        <button type="button" onClick={() => onChange({ ...state, partsSidebarOpen: true })}>
          Show parts
        </button>
      </aside>
    );
  const selected = catalog.parts.find((part) => part.id === state.selectedPieceId);
  return (
    <aside className="fin-attachment-sidebar" aria-label="Fin joint parts">
      <div className="fin-attachment-sidebar-head">
        <h3>Registered joint parts</h3>
        <button type="button" onClick={() => onChange({ ...state, partsSidebarOpen: false })}>
          Hide parts
        </button>
      </div>
      <div className="fin-attachment-sidebar-body">
        <p>
          Nine original STEP records in one coordinate frame. Select a part in this list or on the
          solid.
        </p>
        <div className="fin-attachment-part-list">
          {catalog.parts.map((part) => {
            const available = part.assets[state.section] !== null;
            return (
              <button
                key={part.id}
                type="button"
                aria-pressed={state.selectedPieceId === part.id}
                onClick={() =>
                  onChange({
                    ...state,
                    selectedPieceId: part.id as FinAttachmentState['selectedPieceId'],
                  })
                }
              >
                <strong>{part.label}</strong>
                <small>
                  <code>{part.id}</code> · {part.maturity.replaceAll('_', ' ')}
                  {!available && ' · no retained solid in this cut'}
                  {available && !visibleIds.has(part.id) && ' · hidden'}
                </small>
              </button>
            );
          })}
        </div>
        {selected && (
          <div className="fin-attachment-datum">
            <strong>{selected.label}</strong>
            <p>
              {selected.material} · {selected.section_status[state.section]}
            </p>
            <p className="fin-attachment-source">
              Registered source <code>{String(selected.source.path)}</code> · SHA{' '}
              {String(selected.source.sha256).slice(0, 16)}…
            </p>
          </div>
        )}
        <ul className="fin-attachment-legend">
          <li>Blue: fin panel; amber: integral tab and root gussets.</li>
          <li>Green: motor tube; violet: rings; pale shell: body.</li>
          <li>Gray motor/retainer are simplified inspection envelopes.</li>
        </ul>
      </div>
    </aside>
  );
}

function EvidenceSidebar({
  catalog,
  state,
  onChange,
  onOpenDrawing,
}: {
  catalog: FinCatalog;
  state: FinAttachmentState;
  onChange: (state: FinAttachmentState) => void;
  onOpenDrawing?: (drawing: 'root' | 'loadpath') => void;
}) {
  if (!state.evidenceSidebarOpen)
    return (
      <aside
        className="fin-attachment-sidebar evidence collapsed"
        aria-label="Evidence sidebar collapsed"
      >
        <button type="button" onClick={() => onChange({ ...state, evidenceSidebarOpen: true })}>
          Show evidence
        </button>
      </aside>
    );
  const selected = catalog.dimensions.find(
    (dimension) => dimension.id === state.selectedDimensionId,
  );
  return (
    <aside
      className="fin-attachment-sidebar evidence"
      aria-label="Fin joint dimensions and evidence"
    >
      <div className="fin-attachment-sidebar-head">
        <h3>Dimensions and evidence</h3>
        <button type="button" onClick={() => onChange({ ...state, evidenceSidebarOpen: false })}>
          Hide evidence
        </button>
      </div>
      <div className="fin-attachment-sidebar-body">
        <p>Select a source dimension to mark its endpoints and linked features in 3D.</p>
        <div className="fin-attachment-dimension-list">
          {catalog.dimensions.map((dimension) => (
            <button
              key={dimension.id}
              type="button"
              aria-pressed={state.selectedDimensionId === dimension.id}
              onClick={() =>
                onChange({
                  ...state,
                  selectedDimensionId:
                    state.selectedDimensionId === dimension.id ? null : dimension.id,
                })
              }
            >
              <strong>{dimension.label}</strong>
              <small>
                <DimensionValue value={dimension.value_mm} tolerance={dimension.tolerance_mm} />
              </small>
            </button>
          ))}
        </div>
        {selected && (
          <div className="fin-attachment-datum">
            <strong>
              <DimensionValue value={selected.value_mm} tolerance={selected.tolerance_mm} />
            </strong>
            <p>{selected.basis}</p>
            <p>Linked parts: {selected.feature_ids.join(', ')}</p>
            <p className="fin-attachment-source">
              <code>{selected.source.path}</code> · <code>{selected.source.locator}</code> · SHA{' '}
              {selected.source.sha256.slice(0, 16)}…
            </p>
          </div>
        )}
        <div className="fin-attachment-finding">
          <strong>Fin result remains failed or unqualified</strong>
          <p>
            The recorded FP1/FR1 evaluations do not establish an installed fin pass. The present RP1
            joint's complete movement, strength, thermal and material response remains unresolved.
          </p>
        </div>
        <div className="fin-attachment-finding">
          <strong>Adhesive is a source relationship</strong>
          <p>
            Internal and outer fillets, saddle bonds and aft tab-end adhesive are documented routes.
            This section shows registered solids and CAD cut faces; it does not define bond bead
            shape, stiffness or capacity.
          </p>
        </div>
        <p className="fin-attachment-source">
          Source: AD1 v2 and D1 load/attachment decision. The 0.40 mm aft tab-end gap is a
          calculated nominal relationship, not a measured installed clearance.
        </p>
        {onOpenDrawing && (
          <div className="fin-attachment-toggle-group">
            <button type="button" onClick={() => onOpenDrawing('root')}>
              Root drawing
            </button>
            <button type="button" onClick={() => onOpenDrawing('loadpath')}>
              Load path drawing
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}

export function FinAttachmentInspector({
  vehicle,
  state,
  onChange,
  onOpenDrawing,
  onDownloadStep,
  onDownloadProvenance,
}: {
  vehicle: InspectionDocument;
  state: FinAttachmentState;
  onChange: (state: FinAttachmentState) => void;
  onOpenDrawing?: (drawing: 'root' | 'loadpath') => void;
  onDownloadStep?: () => void;
  onDownloadProvenance?: () => void;
}) {
  const admission = useMemo(() => admitFinAttachmentCatalog(catalogSource, vehicle), [vehicle]);
  const [bodyMode, setBodyMode] = useState<'ghost' | 'solid' | 'hidden'>('ghost');
  const [dragMode, setDragMode] = useState<'rotate' | 'pan'>('rotate');
  const [fit, setFit] = useState<FitCommand>({ serial: 0, scope: 'joint' });
  const isolatedPieceIds = state.isolatedPieceIds;
  const hiddenPieceIds = state.hiddenPieceIds;
  const visibleIds = useMemo(
    () =>
      new Set(
        admission.ok
          ? admission.catalog.parts
              .filter(
                (part) =>
                  (isolatedPieceIds.length === 0 ||
                    isolatedPieceIds.includes(part.id as (typeof isolatedPieceIds)[number])) &&
                  !hiddenPieceIds.includes(part.id as (typeof hiddenPieceIds)[number]),
              )
              .map((part) => part.id)
          : [],
      ),
    [admission, isolatedPieceIds, hiddenPieceIds],
  );
  if (!admission.ok || !validFinAttachmentState(state))
    return (
      <section className="fin-attachment" aria-label="Fin attachment CAD unavailable">
        <p className="fin-attachment-state fin-attachment-alert" role="alert">
          Fin attachment inspection unavailable:{' '}
          {admission.ok ? 'View state is invalid.' : admission.reason}
        </p>
      </section>
    );
  const catalog = admission.catalog;
  const selectedPart = catalog.parts.find((part) => part.id === state.selectedPieceId);
  const selectedAvailable =
    selectedPart?.assets[state.section] !== null &&
    selectedPart !== undefined &&
    visibleIds.has(selectedPart.id) &&
    !(selectedPart.id === 'body' && bodyMode === 'hidden');
  const section = catalog.sections.find((entry) => entry.id === state.section);
  const planeText =
    state.section === 'assembled'
      ? 'Uncut registered assembly'
      : `${section?.label ?? 'Section unavailable'} · CAD plane ${section?.plane_cad_mm.normal.join(', ') ?? 'unavailable'} / ${section?.plane_cad_mm.offset ?? 'unavailable'} mm · retained positive side`;
  return (
    <section className="fin-attachment" aria-label="Registered fin attachment CAD inspector">
      <div className="fin-attachment-toolbar">
        <strong>RP1 fin attachment · registered STEP detail</strong>
        <div className="fin-attachment-toggle-group" aria-label="CAD section">
          {(['assembled', 'longitudinal', 'transverse'] as const).map((sectionId) => (
            <button
              key={sectionId}
              type="button"
              aria-pressed={state.section === sectionId}
              onClick={() => {
                onChange({ ...state, section: sectionId, camera: null });
                setFit((current) => ({ serial: current.serial + 1, scope: 'joint' }));
              }}
            >
              {sectionLabels[sectionId]}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={() => setFit((current) => ({ serial: current.serial + 1, scope: 'joint' }))}
        >
          Fit joint
        </button>
        <button
          type="button"
          disabled={!selectedAvailable}
          onClick={() => setFit((current) => ({ serial: current.serial + 1, scope: 'selected' }))}
        >
          Fit selected
        </button>
        <button
          type="button"
          onClick={() => {
            onChange({ ...state, camera: null });
            setFit((current) => ({ serial: current.serial + 1, scope: 'joint' }));
          }}
        >
          Reset view
        </button>
        <button
          type="button"
          disabled={!selectedAvailable}
          onClick={() =>
            onChange({ ...state, isolatedPieceIds: [state.selectedPieceId!], hiddenPieceIds: [] })
          }
        >
          Isolate selected
        </button>
        <button
          type="button"
          disabled={!selectedAvailable}
          onClick={() =>
            onChange({
              ...state,
              isolatedPieceIds: [],
              hiddenPieceIds: [...state.hiddenPieceIds, state.selectedPieceId!],
            })
          }
        >
          Hide selected
        </button>
        <button
          type="button"
          onClick={() => onChange({ ...state, isolatedPieceIds: [], hiddenPieceIds: [] })}
        >
          Show all
        </button>
        <button
          type="button"
          aria-pressed={dragMode === 'rotate'}
          onClick={() => setDragMode('rotate')}
        >
          Rotate drag
        </button>
        <button type="button" aria-pressed={dragMode === 'pan'} onClick={() => setDragMode('pan')}>
          Move view
        </button>
        <label>
          Body
          <select
            value={bodyMode}
            onChange={(event) => setBodyMode(event.target.value as typeof bodyMode)}
          >
            <option value="ghost">Transparent</option>
            <option value="solid">Solid</option>
            <option value="hidden">Hidden</option>
          </select>
        </label>
        {onDownloadStep && (
          <button type="button" onClick={onDownloadStep}>
            Download joint STEP
          </button>
        )}
        {onDownloadProvenance && (
          <button type="button" onClick={onDownloadProvenance}>
            Download provenance
          </button>
        )}
      </div>
      <div className="fin-attachment-layout">
        <PartsSidebar catalog={catalog} state={state} onChange={onChange} visibleIds={visibleIds} />
        <div className="fin-attachment-scene-wrap">
          <FinAttachmentScene
            catalog={catalog}
            section={state.section}
            visibleIds={visibleIds}
            selectedPieceId={state.selectedPieceId}
            selectedDimensionId={state.selectedDimensionId}
            bodyMode={bodyMode}
            dragMode={dragMode}
            fit={fit}
            camera={state.camera}
            onSelect={(partId) =>
              onChange({
                ...state,
                selectedPieceId: partId as FinAttachmentState['selectedPieceId'],
              })
            }
            onSelectDimension={(dimensionId) =>
              onChange({ ...state, selectedDimensionId: dimensionId })
            }
            onCameraChange={(camera) => onChange({ ...state, camera })}
          />
          <div className="fin-attachment-scene-note">
            {planeText} · cyan outline is the plane guide, orange edges/caps are from the CAD cut ·
            Drag to rotate; Move view changes drag to pan. Wheel or pinch to zoom.
          </div>
        </div>
        <EvidenceSidebar
          catalog={catalog}
          state={state}
          onChange={onChange}
          onOpenDrawing={onOpenDrawing}
        />
      </div>
    </section>
  );
}

export default FinAttachmentInspector;
