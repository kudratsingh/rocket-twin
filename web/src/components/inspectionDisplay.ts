import type { InspectionDocument } from '../types';

export interface InspectionDisplayState {
  selectedId: string | null;
  hiddenIds: string[];
  exploded: number;
  section: boolean;
  ghostShell: boolean;
  wireframe: boolean;
}

/** Display state only. Mesh URLs establish references, not successful WebGL loading. */
export function inspectionDisplayModel(vehicle: InspectionDocument, state: InspectionDisplayState) {
  const ids = new Set(vehicle.parts.map((part) => part.id));
  const meshCount = vehicle.parts.filter((part) => !!part.mesh_url).length;
  const hiddenCount = state.hiddenIds.filter((id) => ids.has(id)).length;
  const selected = vehicle.parts.find((part) => part.id === state.selectedId) ?? null;
  return {
    meshCount,
    hiddenCount,
    selected,
    selectedHidden: !!selected && state.hiddenIds.includes(selected.id),
    altered:
      hiddenCount > 0 ||
      state.exploded !== 0 ||
      state.section ||
      state.ghostShell ||
      state.wireframe,
  };
}

interface DisplayActions extends InspectionDisplayState {
  showAll: () => void;
  setExploded: (amount: number) => void;
  toggleSection: () => void;
  toggleGhostShell: () => void;
  toggleWireframe: () => void;
  fitVisible: () => void;
}

/** Restore only display modes; preserve source, selection, burn state and viewing angle. */
export function restoreAssembledInspection(state: DisplayActions) {
  state.showAll();
  state.setExploded(0);
  if (state.section) state.toggleSection();
  if (state.ghostShell) state.toggleGhostShell();
  if (state.wireframe) state.toggleWireframe();
  state.fitVisible();
}
