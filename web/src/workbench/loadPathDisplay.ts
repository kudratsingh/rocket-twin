import type { EvidenceState, LoadPath } from './types';

export const evidenceLabels: Record<EvidenceState, string> = {
  calculated: 'Calculated · not qualified',
  estimated: 'Estimated · unresolved',
  measured: 'Measured · scope limited to source',
  unavailable: 'Unresolved · unavailable',
  failed: 'Failed screen',
  historical: 'Historical · not current',
  superseded: 'Superseded · not current',
};

export const evidenceColors: Record<EvidenceState, string> = {
  calculated: '#7db6f5',
  estimated: '#dfb66c',
  measured: '#75cecf',
  unavailable: '#dfb66c',
  failed: '#ee9691',
  historical: '#a6a6ba',
  superseded: '#a6a6ba',
};

export function recordedValue(value: number | null, unit: string): string {
  return value === null || !Number.isFinite(value)
    ? `Unavailable${unit ? ` (${unit})` : ''}`
    : `${value}${unit ? ` ${unit}` : ''}`;
}

export function wrapLabel(label: string, width = 30): string[] {
  const lines: string[] = [];
  for (const word of label.split(/\s+/).filter(Boolean)) {
    const last = lines.length - 1;
    if (last < 0 || lines[last].length + word.length + 1 > width) lines.push(word);
    else lines[last] += ` ${word}`;
  }
  return lines.length ? lines : ['Unnamed'];
}

/** Display-only graph layout. Positions do not encode distances or force magnitude. */
export function layoutLoadPath(path: Pick<LoadPath, 'nodes' | 'edges'>) {
  const ids = new Set(path.nodes.map((node) => node.id));
  const incoming = new Map(path.nodes.map((node) => [node.id, 0]));
  const rank = new Map(path.nodes.map((node) => [node.id, 0]));
  const validEdges = path.edges.filter((edge) => ids.has(edge.from) && ids.has(edge.to));
  for (const edge of validEdges) incoming.set(edge.to, (incoming.get(edge.to) ?? 0) + 1);
  const queue = path.nodes.filter((node) => incoming.get(node.id) === 0).map((node) => node.id);
  const visited = new Set<string>();
  for (let index = 0; index < queue.length; index++) {
    const id = queue[index];
    visited.add(id);
    for (const edge of validEdges.filter((item) => item.from === id)) {
      rank.set(edge.to, Math.max(rank.get(edge.to) ?? 0, (rank.get(id) ?? 0) + 1));
      incoming.set(edge.to, (incoming.get(edge.to) ?? 0) - 1);
      if (incoming.get(edge.to) === 0) queue.push(edge.to);
    }
  }
  // A cyclic or disconnected record remains visible, without an unbounded layout loop.
  let fallbackRank = Math.max(0, ...rank.values()) + 1;
  for (const node of path.nodes) {
    if (!visited.has(node.id)) rank.set(node.id, fallbackRank++);
  }
  const levels = new Map<number, string[]>();
  for (const node of path.nodes) {
    const level = rank.get(node.id) ?? 0;
    levels.set(level, [...(levels.get(level) ?? []), node.id]);
  }
  const nodeWidth = 258;
  const nodeHeight = Math.max(
    94,
    ...path.nodes.map((node) => wrapLabel(node.label).length * 18 + 44),
  );
  const width = Math.max(760, ...[...levels.values()].map((level) => level.length * 310 + 70));
  const edgeGap = Math.max(
    106,
    ...path.edges.map(
      (edge, index) => wrapLabel(`${index + 1}. ${edge.label ?? ''}`).length * 15 + 50,
    ),
  );
  const rowHeight = nodeHeight + edgeGap;
  const positions = new Map<string, { x: number; y: number }>();
  for (const [level, nodes] of levels) {
    nodes.forEach((id, index) => {
      positions.set(id, {
        x: (width / (nodes.length + 1)) * (index + 1),
        y: 100 + level * rowHeight,
      });
    });
  }
  const height = 190 + (Math.max(0, ...levels.keys()) + 1) * rowHeight;
  return { positions, width, height, nodeWidth, nodeHeight, hasCycle: visited.size !== ids.size };
}
