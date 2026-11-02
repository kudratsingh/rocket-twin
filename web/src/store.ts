import { create } from 'zustand';
import type { InspectionView } from './components/inspectionGeometry';

interface InspectionState {
  selectedId: string | null;
  hoveredId: string | null;
  hiddenIds: string[];
  exploded: number;
  section: boolean;
  markers: boolean;
  ghostShell: boolean;
  wireframe: boolean;
  partLabels: boolean;
  cameraView: InspectionView;
  focusId: string | null;
  resetToken: number;
  select: (id: string | null) => void;
  hover: (id: string | null) => void;
  togglePart: (id: string) => void;
  isolate: (id: string, allIds: string[]) => void;
  hideParts: (ids: string[]) => void;
  showAll: () => void;
  setExploded: (value: number) => void;
  toggleSection: () => void;
  toggleMarkers: () => void;
  toggleGhostShell: () => void;
  toggleWireframe: () => void;
  togglePartLabels: () => void;
  setCameraView: (view: InspectionView) => void;
  focusPart: (id: string) => void;
  fitVisible: () => void;
  resetCamera: () => void;
  resetVehicle: () => void;
}

export const useInspection = create<InspectionState>((set) => ({
  selectedId: null,
  hoveredId: null,
  hiddenIds: [],
  exploded: 0,
  section: false,
  markers: true,
  ghostShell: false,
  wireframe: false,
  partLabels: true,
  cameraView: 'overview',
  focusId: null,
  resetToken: 0,
  select: (selectedId) => set({ selectedId }),
  hover: (hoveredId) => set({ hoveredId }),
  togglePart: (id) =>
    set((s) => ({
      hiddenIds: s.hiddenIds.includes(id)
        ? s.hiddenIds.filter((item) => item !== id)
        : [...s.hiddenIds, id],
    })),
  isolate: (id, allIds) => set({ hiddenIds: allIds.filter((item) => item !== id) }),
  hideParts: (ids) => set((s) => ({ hiddenIds: [...new Set([...s.hiddenIds, ...ids])] })),
  showAll: () => set({ hiddenIds: [] }),
  setExploded: (exploded) => set({ exploded }),
  toggleSection: () => set((s) => ({ section: !s.section })),
  toggleMarkers: () => set((s) => ({ markers: !s.markers })),
  toggleGhostShell: () => set((s) => ({ ghostShell: !s.ghostShell })),
  toggleWireframe: () => set((s) => ({ wireframe: !s.wireframe })),
  togglePartLabels: () => set((s) => ({ partLabels: !s.partLabels })),
  setCameraView: (cameraView) => set((s) => ({ cameraView, resetToken: s.resetToken + 1 })),
  focusPart: (focusId) =>
    set((s) => ({
      focusId,
      selectedId: focusId,
      hiddenIds: s.hiddenIds.filter((id) => id !== focusId),
      resetToken: s.resetToken + 1,
    })),
  fitVisible: () => set((s) => ({ focusId: null, resetToken: s.resetToken + 1 })),
  resetCamera: () =>
    set((s) => ({ focusId: null, cameraView: 'overview', resetToken: s.resetToken + 1 })),
  resetVehicle: () =>
    set((s) => ({
      selectedId: null,
      hoveredId: null,
      hiddenIds: [],
      exploded: 0,
      section: false,
      ghostShell: false,
      wireframe: false,
      partLabels: true,
      markers: true,
      cameraView: 'overview',
      focusId: null,
      resetToken: s.resetToken + 1,
    })),
}));
