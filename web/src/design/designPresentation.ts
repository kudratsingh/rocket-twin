import type { DesignLayer, DrawingPart } from './orthographicGeometry';

export type DrawingView = { cx: number; cy: number; scale: number };

/** Fit only source bounds; the minimum is a display guard, never a part dimension. */
export function fitDrawing(parts: DrawingPart[]): DrawingView {
  if (!parts.length) return { cx: 0, cy: 0, scale: 1 };
  const left = Math.min(...parts.map((item) => item.bounds[0]));
  const right = Math.max(...parts.map((item) => item.bounds[2]));
  const bottom = Math.min(...parts.map((item) => item.bounds[1]));
  const top = Math.max(...parts.map((item) => item.bounds[3]));
  return {
    cx: (left + right) / 2,
    cy: (bottom + top) / 2,
    scale: Math.min(1080 / Math.max(right - left, 0.001), 240 / Math.max(top - bottom, 0.001)),
  };
}

export function selectionVisibility(
  part: DrawingPart | undefined,
  layers: readonly DesignLayer[],
  hiddenIds: readonly string[],
): 'unavailable' | 'hidden-part' | 'hidden-layer' | 'visible' {
  if (!part) return 'unavailable';
  if (hiddenIds.includes(part.part.id)) return 'hidden-part';
  if (!layers.includes(part.layer)) return 'hidden-layer';
  return 'visible';
}

export function visibleDrawingParts(
  parts: DrawingPart[],
  layers: readonly DesignLayer[],
  hiddenIds: readonly string[],
  onlySelected: boolean,
  selectedId: string | null,
): DrawingPart[] {
  return parts.filter(
    (part) =>
      selectionVisibility(part, layers, hiddenIds) === 'visible' &&
      (!onlySelected || part.part.id === selectedId),
  );
}

export function sourceMaturity(part: DrawingPart): string {
  return `Drawing: simplified ${part.layer === 'fins' ? 'radial planform' : 'envelope'}; source role: ${part.representation}. Physical qualification remains open.`;
}
