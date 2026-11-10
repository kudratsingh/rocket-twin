import {
  matchesRp1SystemMapSource,
  SYSTEM_MAPS,
  systemMapNode,
  type SystemMapMode,
} from './rp1SystemMapData.ts';

export const RP1_SYSTEM_MAP_SOURCE_COMMIT = '07552bd1425dce4cf0b47af56c70b44a9500625e';

export type SystemMapExportRequest = {
  configurationId: string;
  specificationSha256: string | null;
  mode: SystemMapMode;
  selectedId: string;
  graphSvgMarkup: string;
};

function xml(value: string): string {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;');
}

function line(value: string, x: number, y: number, size = 14, fill = '#e7f0f2', weight = 400) {
  return `<text x="${x}" y="${y}" fill="${fill}" font-family="Arial, sans-serif" font-size="${size}" font-weight="${weight}">${xml(value)}</text>`;
}

function wrap(value: string, max = 47): string[] {
  const words = value.split(/\s+/).filter(Boolean);
  const lines: string[] = [];
  let current = '';
  for (const word of words) {
    if (current && `${current} ${word}`.length > max) {
      lines.push(current);
      current = '';
    }
    if (word.length > max) {
      if (current) lines.push(current);
      for (let start = 0; start < word.length; start += max)
        lines.push(word.slice(start, start + max));
      current = '';
    } else {
      current = current ? `${current} ${word}` : word;
    }
  }
  if (current) lines.push(current);
  return lines;
}

function textBlock(value: string, x: number, y: number, max = 47, size = 14, step = 19) {
  const rows = wrap(value, max);
  return {
    markup: rows.map((row, index) => line(row, x, y + index * step, size)).join(''),
    nextY: y + rows.length * step,
  };
}

/** Build a standalone vector sheet from the actual visible graph SVG and current source data. */
export function buildRp1SystemMapSvg(request: SystemMapExportRequest) {
  if (!matchesRp1SystemMapSource(request.configurationId, request.specificationSha256)) {
    throw new Error('System-map export requires the exact current RP1 source');
  }
  if (request.mode !== 'g80' && request.mode !== 'g12') throw new Error('Unknown system-map mode');
  const graph = SYSTEM_MAPS[request.mode];
  const selected = systemMapNode(request.mode, request.selectedId);
  if (!selected) throw new Error('Selected system-map block is unavailable');
  if (
    !/^<svg[\s>]/i.test(request.graphSvgMarkup.trim()) ||
    !/<\/svg>\s*$/i.test(request.graphSvgMarkup) ||
    /<(?:script|image|foreignObject|iframe|use)\b|@import|url\((?!#)/i.test(request.graphSvgMarkup)
  ) {
    throw new Error('Graph markup is not a self-contained SVG');
  }
  const metadata = {
    schema_version: 1,
    id: 'rp1-system-map-source-svg',
    configuration_id: request.configurationId,
    specification_sha256: request.specificationSha256,
    source_commit: RP1_SYSTEM_MAP_SOURCE_COMMIT,
    mode: request.mode,
    mode_status:
      request.mode === 'g80'
        ? 'current G80 fixed unguided; RP1 flight inputs unavailable'
        : 'future G12 PID to RL; planned and unqualified',
    selected_block_id: selected.id,
    selected_block: selected,
    nodes: graph.nodes,
    edges: graph.edges,
    units_and_frames:
      'SI; NED world and body axes where defined; local block details carry signal units',
    status: 'source-bound presentation diagram; engineering and physical acceptance open',
    representation:
      'Actual current graph plus full flow key and selected block; no simulated result',
  };

  const flow = graph.edges
    .map((edge, index) => {
      const col = index < Math.ceil(graph.edges.length / 2) ? 0 : 1;
      const row = col ? index - Math.ceil(graph.edges.length / 2) : index;
      const x = col ? 590 : 24;
      const y = 604 + row * 55;
      const from = systemMapNode(request.mode, edge.from)!;
      const to = systemMapNode(request.mode, edge.to)!;
      return (
        `<rect x="${x}" y="${y - 17}" width="32" height="25" rx="4" fill="#d8e8ed"/>` +
        line(`E${index + 1}`, x + 6, y, 12, '#102835', 800) +
        line(`${from.title} → ${to.title}`, x + 42, y - 4, 13, '#eef5f6', 700) +
        line(`${edge.label} · ${edge.status}`, x + 42, y + 15, 12, '#c8d9df')
      );
    })
    .join('');

  const detailX = 1210;
  let detailY = 177;
  const detail: string[] = [
    `<rect x="1190" y="130" width="390" height="730" rx="9" fill="#1a2d38" stroke="#466674"/>`,
    line('Selected block', detailX, detailY, 17, '#f7d279', 700),
  ];
  detailY += 32;
  const title = textBlock(selected.title, detailX, detailY, 38, 20, 25);
  detail.push(title.markup);
  detailY = title.nextY + 12;
  detail.push(line(`Status: ${selected.status}`, detailX, detailY, 14, '#e7f0f2', 700));
  detailY += 29;
  const description = textBlock(selected.detail, detailX, detailY, 45, 14, 19);
  detail.push(description.markup);
  detailY = description.nextY + 15;
  detail.push(line('Signal / frame', detailX, detailY, 14, '#f7d279', 700));
  detailY += 22;
  const signal = textBlock(selected.signal, detailX, detailY, 45, 14, 19);
  detail.push(signal.markup);
  detailY = signal.nextY + 12;
  detail.push(line('Source paths', detailX, detailY, 14, '#f7d279', 700));
  detailY += 23;
  for (const source of selected.source) {
    const sourceText = textBlock(source, detailX, detailY, 45, 12, 17);
    detail.push(sourceText.markup);
    detailY = sourceText.nextY + 6;
  }
  if (detailY > 835) throw new Error('Selected block exceeds source sheet detail panel');

  const modeTitle = request.mode === 'g80' ? 'Current G80 · unguided' : 'Future G12 · PID → RL';
  const modeCaption =
    request.mode === 'g80'
      ? 'Shared 6DOF model exists; complete RP1 flight/inertia inputs unavailable. Fixed G80 has no active gimbal/controller.'
      : 'Future control work only; gains, policy, installed actuator and safe abort remain unqualified.';
  const content = [
    '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="980" viewBox="0 0 1600 980">',
    '<rect width="1600" height="980" fill="#101d27"/>',
    `<metadata>${xml(JSON.stringify(metadata))}</metadata>`,
    line('RP1 system and control paths', 24, 38, 26, '#f4f7f6', 700),
    line(modeTitle, 24, 67, 18, '#9bd4e2', 700),
    line(modeCaption, 24, 91, 14, '#f7d279'),
    line(
      'Legend: implemented model  ·  source definition  ·  planned  ·  unavailable',
      24,
      113,
      13,
      '#d9e8ec',
    ),
    `<rect x="18" y="130" width="1154" height="402" rx="8" fill="#142734" stroke="#355362"/>`,
    request.graphSvgMarkup,
    line('Flow key', 24, 575, 17, '#f4f7f6', 700),
    flow,
    ...detail,
    line(
      'Independent recovery is outside the ascent-control loop. Source topology is not verified wiring.',
      24,
      895,
      14,
      '#c8d9df',
    ),
    line(
      'Source-bound diagram only; installed performance, engineering, physical and flight acceptance remain open.',
      24,
      921,
      14,
      '#f7d279',
    ),
    line(
      `Configuration ${request.configurationId} · specification SHA-256 ${request.specificationSha256}`,
      24,
      947,
      12,
      '#a9c8d0',
    ),
    line(`Pinned repository source ${RP1_SYSTEM_MAP_SOURCE_COMMIT}`, 24, 966, 12, '#a9c8d0'),
    '</svg>',
  ].join('');
  return {
    filename: `rp1-system-map-${request.mode}-${request.specificationSha256!.slice(0, 12)}.svg`,
    content,
    metadata,
  };
}

/** Reuse the workbench's computed-style cloning pattern so the graphic travels without CSS. */
export function downloadRp1SystemMapSvg(
  svg: SVGSVGElement | null,
  request: Omit<SystemMapExportRequest, 'graphSvgMarkup'>,
): string {
  if (!svg) throw new Error('Visible system-map graph is unavailable');
  const clone = svg.cloneNode(true) as SVGSVGElement;
  const originals = [svg, ...svg.querySelectorAll('*')];
  const copies = [clone, ...clone.querySelectorAll('*')];
  originals.forEach((element, index) => {
    const computed = window.getComputedStyle(element);
    const copy = copies[index] as SVGElement;
    for (const name of [
      'fill',
      'fill-opacity',
      'stroke',
      'stroke-opacity',
      'stroke-width',
      'stroke-dasharray',
      'font-size',
      'font-family',
      'font-weight',
      'opacity',
      'text-anchor',
      'paint-order',
    ])
      copy.style.setProperty(name, computed.getPropertyValue(name));
  });
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
  clone.setAttribute('x', '20');
  clone.setAttribute('y', '131');
  clone.setAttribute('width', '1150');
  clone.setAttribute('height', '400');
  const result = buildRp1SystemMapSvg({
    ...request,
    graphSvgMarkup: new XMLSerializer().serializeToString(clone),
  });
  const url = URL.createObjectURL(
    new Blob([result.content], { type: 'image/svg+xml;charset=utf-8' }),
  );
  const link = window.document.createElement('a');
  link.href = url;
  link.download = result.filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  return result.filename;
}
