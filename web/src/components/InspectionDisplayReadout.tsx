import { useInspection } from '../store';
import type { InspectionDocument } from '../types';
import { PartDimensions } from '../workspaces/PartDimensions';
import { inspectionDisplayModel, restoreAssembledInspection } from './inspectionDisplay';
import type { InspectionDisplayState } from './inspectionDisplay';
import './inspectionDisplayReadout.css';

/** The same source document and selection as the surrounding viewer; no alternate geometry. */
export function InspectionDisplayReadout({ vehicle }: { vehicle: InspectionDocument }) {
  const state = useInspection();
  return (
    <InspectionDisplayReadoutView
      vehicle={vehicle}
      state={state}
      onRestore={() => restoreAssembledInspection(useInspection.getState())}
    />
  );
}

export function InspectionDisplayReadoutView({
  vehicle,
  state,
  onRestore,
}: {
  vehicle: InspectionDocument;
  state: InspectionDisplayState;
  onRestore: () => void;
}) {
  const model = inspectionDisplayModel(vehicle, state);
  return (
    <section
      className="inspection-display-readout"
      aria-label="Section, explode and source dimensions"
    >
      <div className="inspection-display-readout-heading">
        <h3>Inspection display</h3>
        <button type="button" disabled={!model.meshCount || !model.altered} onClick={onRestore}>
          Restore assembled inspection
        </button>
      </div>
      <p className="inspection-display-state" aria-live="polite">
        {model.meshCount ? (
          <>
            <strong>{state.section ? 'Section clipping on' : 'Section clipping off'}</strong>
            {' · '}
            {state.exploded > 0
              ? `Exploded display ${Math.round(state.exploded * 100)}%`
              : 'Assembled display'}
            {' · '}
            {model.hiddenCount} of {vehicle.parts.length} source parts hidden
            {state.ghostShell ? ' · Transparent shell on' : ''}
            {state.wireframe ? ' · Wireframe on' : ''}
          </>
        ) : (
          <strong>
            3D section and explode unavailable — no recorded component mesh references.
          </strong>
        )}
      </p>
      <details className="inspection-display-explanation">
        <summary>How this display works</summary>
        <p>
          Restore shows all parts, removes section clipping and display separation, and returns the
          shell to opaque solid shading. It keeps the selected component and viewing angle, then
          fits the assembly.
        </p>
        {model.meshCount > 0 && (
          <>
            <p>
              Section is a fixed display cut through the vehicle axis at viewer X = 0; the
              positive-X half is hidden. It exposes existing mesh surfaces without adding a physical
              cut face or verifying internal construction.
            </p>
            <p>
              Explode separates parts for visibility only. Its percentage and apparent gaps are not
              dimensions, assembly clearances or motion results. Source dimensions below do not
              change with this display. CG / CP markers are hidden while exploded.
            </p>
          </>
        )}
        <p>
          Source: <code>{vehicle.id}</code>. Mesh references do not confirm successful loading or
          as-built geometry; unavailable meshes remain listed in the parts tree.
        </p>
      </details>
      {state.selectedId ? (
        <details className="inspection-source-dimensions" key={`${vehicle.id}:${state.selectedId}`}>
          <summary>
            Selected component dimensions · {model.selected?.name || state.selectedId}
            {model.selectedHidden ? ' · currently hidden' : ''}
          </summary>
          <p>
            Selected component record: <code>{state.selectedId}</code>
          </p>
          <PartDimensions vehicle={vehicle} partId={state.selectedId} />
        </details>
      ) : (
        <p>
          Select a component in this source to inspect its recorded dimensions. Missing dimensions
          are unavailable, never inferred from an exploded view.
        </p>
      )}
    </section>
  );
}
