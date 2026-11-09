import sourceLayout from '../../../docs/studies/frontend-component-depth-20261108/high-g-pcb-layout.json';

export interface HighGPcbReferenceSource {
  partId: string;
  configurationId: string;
  specificationSha256: string | null;
  boardLayoutId?: string | null;
  boardSourceSha256?: string | null;
}

export type XY = [number, number];
export type SourcePlacement = (typeof sourceLayout.placements)[number];
export type SourcePad = (typeof sourceLayout.pads)[number];
export type SourceTrace = (typeof sourceLayout.traces)[number];
export type SourceVia = (typeof sourceLayout.vias)[number];
export type SourceSilk = typeof sourceLayout.silkscreen;

const LAYOUT_ID = 'adafruit-5374-source-xy-layers-4a768fc9-v1';
const SOURCE_SHA256 = '7c089eb8cc0756b7dc5e30abd240978dc272113d93f602b497f8f442d532d68c';

export function matchesHighGPcbReferenceSource(source: HighGPcbReferenceSource): boolean {
  return (
    sourceLayout.id === LAYOUT_ID &&
    sourceLayout.source.sha256 === SOURCE_SHA256 &&
    sourceLayout.license.spdx === 'CC-BY-SA-3.0' &&
    sourceLayout.units === 'mm' &&
    sourceLayout.pcb_thickness_mm === null &&
    sourceLayout.component_heights_available === false &&
    sourceLayout.placements.length === 26 &&
    sourceLayout.pads.length === 82 &&
    sourceLayout.traces.length === 208 &&
    sourceLayout.vias.length === 26 &&
    sourceLayout.nets.length === 14 &&
    source.partId === sourceLayout.part_id &&
    source.configurationId === sourceLayout.configuration_id &&
    source.specificationSha256 === sourceLayout.specification_sha256 &&
    (source.boardLayoutId == null || source.boardLayoutId === LAYOUT_ID) &&
    (source.boardSourceSha256 == null || source.boardSourceSha256 === SOURCE_SHA256)
  );
}

/** A manufacturer board-layer reference. It does not register vehicle CAD or hardware Z. */
export function highGPcbReference(source: HighGPcbReferenceSource) {
  return matchesHighGPcbReferenceSource(source) ? sourceLayout : null;
}

/** Join the recorded eight perimeter segments without changing their XY coordinates. */
export function outlinePoints(segments: number[][][]): XY[] {
  const result: XY[] = [];
  for (const segment of segments) {
    for (const point of segment) {
      const xy: XY = [point[0], point[1]];
      if (
        !Number.isFinite(xy[0]) ||
        !Number.isFinite(xy[1]) ||
        (result.length &&
          result[result.length - 1][0] === xy[0] &&
          result[result.length - 1][1] === xy[1])
      )
        continue;
      result.push(xy);
    }
  }
  return result;
}

/** Exact source-width rectangular strip triangles for straight Eagle traces and silk wires. */
export function lineTriangles(points: number[][], widthMm: number): number[] {
  if (!Number.isFinite(widthMm) || widthMm <= 0 || points.length < 2) return [];
  const out: number[] = [];
  for (let i = 0; i < points.length - 1; i += 1) {
    const [ax, ay] = points[i];
    const [bx, by] = points[i + 1];
    const dx = bx - ax;
    const dy = by - ay;
    const length = Math.hypot(dx, dy);
    if (!Number.isFinite(length) || length === 0) continue;
    const ox = (-dy / length) * widthMm * 0.5;
    const oy = (dx / length) * widthMm * 0.5;
    out.push(
      ax + ox,
      ay + oy,
      bx + ox,
      by + oy,
      bx - ox,
      by - oy,
      ax + ox,
      ay + oy,
      bx - ox,
      by - oy,
      ax - ox,
      ay - oy,
    );
  }
  return out;
}

/** Sample a recorded Eagle arc in the same XY plane; zero-curve wires stay exact segments. */
export function sourceLinePoints(points: number[][], curveDeg = 0): number[][] {
  if (points.length !== 2 || !Number.isFinite(curveDeg) || Math.abs(curveDeg) < 1e-9) return points;
  const [a, b] = points;
  const theta = (curveDeg * Math.PI) / 180;
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const chord = Math.hypot(dx, dy);
  if (chord === 0 || !Number.isFinite(chord) || Math.abs(Math.sin(theta / 2)) < 1e-9) return points;
  const h = chord / (2 * Math.tan(theta / 2));
  const cx = (a[0] + b[0]) / 2 - (dy / chord) * h;
  const cy = (a[1] + b[1]) / 2 + (dx / chord) * h;
  const radius = Math.hypot(a[0] - cx, a[1] - cy);
  const start = Math.atan2(a[1] - cy, a[0] - cx);
  const count = Math.max(6, Math.ceil(Math.abs(curveDeg) / 8));
  return Array.from({ length: count + 1 }, (_, index) => {
    const angle = start + (theta * index) / count;
    return [cx + radius * Math.cos(angle), cy + radius * Math.sin(angle)];
  });
}

export function quadTriangles(corners: number[]): number[] {
  if (corners.length !== 8 || corners.some((v) => !Number.isFinite(v))) return [];
  const [x1, y1, x2, y2, x3, y3, x4, y4] = corners;
  return [x1, y1, x2, y2, x3, y3, x1, y1, x3, y3, x4, y4];
}

/** Labels for a source-XY ruler; the final source boundary is retained even off the 5 mm grid. */
export function pcbAxisTicks(extentMm: number, intervalMm = 5): number[] {
  if (
    !Number.isFinite(extentMm) ||
    extentMm <= 0 ||
    !Number.isFinite(intervalMm) ||
    intervalMm <= 0
  )
    return [];
  const ticks = [0];
  for (let step = 1; step * intervalMm < extentMm; step += 1) ticks.push(step * intervalMm);
  ticks.push(extentMm);
  return ticks;
}

/** Ruler label layout only: retain exact endpoints without crowding a nearby regular label. */
export function pcbAxisLabelTicks(extentMm: number, intervalMm = 5): number[] {
  const ticks = pcbAxisTicks(extentMm, intervalMm);
  return ticks.filter(
    (tick, index) => index === 0 || index === ticks.length - 1 || extentMm - tick >= intervalMm / 2,
  );
}

/** Recorded pad relationships only; an unconnected source pad is not assigned a net. */
export function footprintConnectionSummary(
  ref: string,
): { padCount: number; unassignedPadCount: number; nets: string[] } | null {
  if (!sourceLayout.placements.some((placement) => placement.ref === ref)) return null;
  const pads = sourceLayout.pads.filter((pad) => pad.ref === ref);
  return {
    padCount: pads.length,
    unassignedPadCount: pads.filter((pad) => pad.net === null).length,
    nets: [
      ...new Set(pads.map((pad) => pad.net).filter((net): net is string => net !== null)),
    ].sort(),
  };
}

export function netContactSummary(
  netName: string,
): { padCount: number; traceCount: number; viaCount: number; refs: string[] } | null {
  const net = sourceLayout.nets.find((item) => item.name === netName);
  if (!net) return null;
  return {
    padCount: sourceLayout.pads.filter((pad) => pad.net === netName).length,
    traceCount: sourceLayout.traces.filter((trace) => trace.net === netName).length,
    viaCount: sourceLayout.vias.filter((via) => via.net === netName).length,
    refs: [...new Set(net.contacts.map((contact) => contact.ref))].sort(),
  };
}
