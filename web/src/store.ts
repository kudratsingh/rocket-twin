import { create } from 'zustand';

interface InspectionState {
  selectedId: string | null;
  hoveredId: string | null;
  hiddenIds: string[];
  exploded: number;
  section: boolean;
  markers: boolean;
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
  resetCamera: () => set((s) => ({ resetToken: s.resetToken + 1 })),
  resetVehicle: () =>
    set((s) => ({
      selectedId: null,
      hoveredId: null,
      hiddenIds: [],
      exploded: 0,
      section: false,
      resetToken: s.resetToken + 1,
    })),
}));
