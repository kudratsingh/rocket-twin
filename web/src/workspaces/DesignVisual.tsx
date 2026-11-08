import { useId, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { OrthographicDesign } from '../design/OrthographicDesign';
import { useInspection } from '../store';
import type { InspectionDocument } from '../types';
import { InspectionTools, useOpenInspectionDetails } from './InspectionWorkspace';
import { useWorkspaceLayout } from './workspaceLayoutContext';
import {
  drawingShortcut,
  inspectionGeometryPresentation,
  inspectionPartRepresentation,
} from './inspectionWorkflow';
import { ComponentEvidence } from './ComponentEvidence';
import './revampDesignVisual.css';
import { InteriorWorkbench } from '../components/InteriorWorkbench';

/** Representation changes preserve shared selection and the mounted 3D camera. */
export function DesignVisual({
  vehicle,
  meshView,
  recordedCaseControls,
  onDetailMeshesChange,
}: {
  vehicle: InspectionDocument;
  meshView: ReactNode;
  recordedCaseControls?: ReactNode;
  onDetailMeshesChange?: (meshes: Record<string, string>) => void;
}) {
  const id = useId();
  const evidenceRef = useRef<HTMLDetailsElement>(null);
  const [localRepresentation, setLocalRepresentation] = useState<'3d' | '2d'>(() =>
    vehicle.parts.some((part) => part.mesh_url) ? '3d' : '2d',
  );
  const layout = useWorkspaceLayout();
  const preferred = layout?.preferences.representation;
  const hasMeshes = vehicle.parts.some((part) => part.mesh_url);
  const representation =
    preferred === '3d' && !hasMeshes
      ? '2d'
      : preferred && preferred !== 'auto'
        ? preferred
        : localRepresentation;
  const setRepresentation = (value: '3d' | '2d') => {
    setLocalRepresentation(value);
    layout?.updatePreferences({ representation: value });
  };
  const selected = useInspection((s) => s.selectedId);
  const hiddenIds = useInspection((s) => s.hiddenIds);
  const select = useInspection((s) => s.select);
  const openDetails = useOpenInspectionDetails();
  const selectedPart = vehicle.parts.find((part) => part.id === selected);
  const geometry = inspectionGeometryPresentation(vehicle);
  return (
    <section
      className="research-design-visual"
      data-representation={representation}
      aria-label="Design representations"
      onKeyDown={(event) => {
        // Drawing controls own these keys; do not command the retained, hidden 3D camera.
        if (representation !== '2d' || event.ctrlKey || event.metaKey || event.altKey) return;
        if (
          event.target instanceof HTMLElement &&
          (['INPUT', 'SELECT', 'TEXTAREA'].includes(event.target.tagName) ||
            event.target.isContentEditable ||
            event.target.closest('[data-inspection-evidence]'))
        )
          return;
        const action = drawingShortcut(event.key);
        if (!action) return;
        event.preventDefault();
        event.stopPropagation();
        if (action !== 'unsupported')
          event.currentTarget
            .querySelector<HTMLButtonElement>(`[data-inspection-action="${action}"]`)
            ?.click();
      }}
    >
      <div className="inspection-workflow-header">
        <div className="research-representation-controls" aria-label="Drawing representation">
          <button
            type="button"
            aria-controls={`${id}-3d`}
            aria-pressed={representation === '3d'}
            disabled={!hasMeshes}
            title={
              hasMeshes
                ? geometry.sourceDerived
                  ? 'Inspect this source-derived model; complete manufacturing CAD is unavailable'
                  : 'Inspect matching recorded CAD'
                : 'No matching 3D assembly exists for this source; use its source drawing'
            }
            onClick={() => setRepresentation('3d')}
          >
            {geometry.sourceDerived ? '3D model' : '3D recorded geometry'}
          </button>
          <button
            type="button"
            aria-controls={`${id}-2d`}
            aria-pressed={representation === '2d'}
            onClick={() => setRepresentation('2d')}
          >
            2D dimensions
          </button>
          <span>
            {vehicle.label || vehicle.name || vehicle.id} · {geometry.coverage}
          </span>
        </div>
        <InteriorWorkbench vehicle={vehicle} onDetailMeshesChange={onDetailMeshesChange} />
        {geometry.sourceDerived && (
          <details className="inspection-source-note">
            <summary>Preliminary</summary>
            <p className="revamp-source-state" role="status">
              Source-derived inspection model · source estimates and simplified envelopes · complete
              manufacturing CAD unavailable. Mass allowances and missing geometry have no solid;
              every source record remains selectable in the parts tree. Physical qualification open.
            </p>
          </details>
        )}
      </div>
      {recordedCaseControls && <InspectionTools>{recordedCaseControls}</InspectionTools>}
      {!hasMeshes && (
        <p className="revamp-source-state" role="status">
          Source drawing / concept · matching 3D assembly unavailable
        </p>
      )}
      {selectedPart && (
        <div className="research-selection-summary" aria-live="polite">
          <div>
            <strong>{selectedPart.name || selectedPart.id}</strong>
            <p>
              {selectedPart.function || selectedPart.engineering?.function || selectedPart.learn}
            </p>
            <span>
              {selectedPart.material} · {inspectionPartRepresentation(selectedPart).label}
              {hiddenIds.includes(selectedPart.id) ? ' · currently hidden' : ''}
            </span>
            {geometry.sourceDerived && inspectionPartRepresentation(selectedPart).description && (
              <p>{inspectionPartRepresentation(selectedPart).description}</p>
            )}
          </div>
          <button
            type="button"
            onClick={() => {
              layout?.updatePreferences({ toolsOpen: true });
              if (!evidenceRef.current) return;
              evidenceRef.current.open = true;
              window.requestAnimationFrame(() => {
                evidenceRef.current?.scrollIntoView({ block: 'nearest' });
                evidenceRef.current?.querySelector('summary')?.focus();
              });
            }}
          >
            Connections & evidence
          </button>
          {openDetails && (
            <button type="button" onClick={openDetails}>
              Open selected component details
            </button>
          )}
        </div>
      )}
      <div id={`${id}-3d`} className="research-representation" hidden={representation !== '3d'}>
        {meshView}
      </div>
      <div id={`${id}-2d`} className="research-representation" hidden={representation !== '2d'}>
        <OrthographicDesign
          active={representation === '2d'}
          vehicle={vehicle}
          selectedPartId={selected}
          onSelectPart={select}
          hiddenPartIds={hiddenIds}
          onRevealPart={(id) => {
            const state = useInspection.getState();
            if (state.hiddenIds.includes(id)) state.togglePart(id);
          }}
        />
      </div>
      <InspectionTools>
        <ComponentEvidence
          vehicle={vehicle}
          selectedId={selected}
          onSelect={select}
          hiddenIds={hiddenIds}
          disclosureRef={evidenceRef}
        />
      </InspectionTools>
    </section>
  );
}
