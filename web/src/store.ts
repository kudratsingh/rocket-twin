import { create } from 'zustand';
import type { InspectionView } from './components/inspectionGeometry';

interface InspectionState {
  selectedId: string | null;
  hoveredId: string | null;
  hiddenIds: string[];
  isolatedFrom: string[] | null;
  exploded: number;
  section: boolean;
  markers: boolean;
  ghostShell: boolean;
  wireframe: boolean;
  partLabels: boolean;
  cameraView: InspectionView;
  cameraAction: 'reset' | 'fit' | 'focus' | 'preset';
  focusId: string | null;
  resetToken: number;
  select: (id: string | null) => void;
  hover: (id: string | null) => void;
  togglePart: (id: string) => void;
  isolate: (id: string, allIds: string[]) => void;
  exitIsolate: () => void;
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
  isolatedFrom: null,
  exploded: 0,
  section: false,
  markers: true,
  ghostShell: false,
  wireframe: false,
  partLabels: true,
  cameraView: 'overview',
  cameraAction: 'reset',
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
  isolate: (id, allIds) =>
    set((s) => ({
      isolatedFrom: s.isolatedFrom ?? [...s.hiddenIds],
      hiddenIds: allIds.filter((item) => item !== id),
    })),
  exitIsolate: () => set((s) => ({ hiddenIds: s.isolatedFrom ?? s.hiddenIds, isolatedFrom: null })),
  hideParts: (ids) => set((s) => ({ hiddenIds: [...new Set([...s.hiddenIds, ...ids])] })),
  showAll: () => set({ hiddenIds: [], isolatedFrom: null }),
  setExploded: (exploded) => set({ exploded }),
  toggleSection: () => set((s) => ({ section: !s.section })),
  toggleMarkers: () => set((s) => ({ markers: !s.markers })),
  toggleGhostShell: () => set((s) => ({ ghostShell: !s.ghostShell })),
  toggleWireframe: () => set((s) => ({ wireframe: !s.wireframe })),
  togglePartLabels: () => set((s) => ({ partLabels: !s.partLabels })),
  setCameraView: (cameraView) =>
    set((s) => ({
      cameraView,
      cameraAction: 'preset',
      focusId: null,
      resetToken: s.resetToken + 1,
    })),
  focusPart: (focusId) =>
    set((s) => ({
      focusId,
      cameraAction: 'focus',
      selectedId: focusId,
      hiddenIds: s.hiddenIds.filter((id) => id !== focusId),
      resetToken: s.resetToken + 1,
    })),
  fitVisible: () =>
    set((s) => ({ focusId: null, cameraAction: 'fit', resetToken: s.resetToken + 1 })),
  resetCamera: () =>
    set((s) => ({
      focusId: null,
      cameraView: 'overview',
      cameraAction: 'reset',
      resetToken: s.resetToken + 1,
    })),
  resetVehicle: () =>
    set((s) => ({
      selectedId: null,
      hoveredId: null,
      hiddenIds: [],
      isolatedFrom: null,
      exploded: 0,
      section: false,
      ghostShell: false,
      wireframe: false,
      partLabels: true,
      markers: true,
      cameraView: 'overview',
      cameraAction: 'reset',
      focusId: null,
      resetToken: s.resetToken + 1,
    })),
}));
