import type { WorkbenchDocument } from './types';

export function exportMetadata(document: WorkbenchDocument, title: string) {
  return {
    title,
    configuration: document.identity.configuration_id,
    specification_sha256: document.identity.specification_sha256,
    cad_revision: document.identity.cad_revision,
    frame: document.identity.frame,
    units: document.identity.units,
    status: document.status,
    representation: 'Presentation drawing; concept/envelope maturity is labeled in the graphic.',
    sources: document.generated_from,
  };
}

/** Save the visible drawing with its identity and styles; no analysis is performed. */
export function downloadWorkbenchSvg(
  svg: SVGSVGElement | null,
  document: WorkbenchDocument,
  title: string,
) {
  if (!svg) return;
  const clone = svg.cloneNode(true) as SVGSVGElement;
  const originals = [svg, ...svg.querySelectorAll('*')];
  const copies = [clone, ...clone.querySelectorAll('*')];
  originals.forEach((element, i) => {
    const computed = window.getComputedStyle(element);
    const copy = copies[i] as SVGElement;
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
      'vector-effect',
      'paint-order',
    ])
      copy.style.setProperty(name, computed.getPropertyValue(name));
  });
  const ns = 'http://www.w3.org/2000/svg';
  const width = svg.viewBox.baseVal.width || 1000;
  const height = svg.viewBox.baseVal.height || 500;
  const output = window.document.createElementNS(ns, 'svg');
  output.setAttribute('xmlns', ns);
  output.setAttribute('viewBox', `0 0 ${width} ${height + 75}`);
  output.setAttribute('width', String(width));
  output.setAttribute('height', String(height + 75));
  const background = window.document.createElementNS(ns, 'rect');
  background.setAttribute('width', '100%');
  background.setAttribute('height', '100%');
  background.setAttribute('fill', '#10161b');
  output.append(background);
  const metadata = window.document.createElementNS(ns, 'metadata');
  metadata.textContent = JSON.stringify(exportMetadata(document, title));
  output.append(metadata);
  for (const [i, text] of [
    title,
    `${document.label} · ${document.identity.units} · Preliminary / acceptance open`,
    `Source ${document.identity.specification_sha256.slice(0, 16)} · CAD ${document.identity.cad_revision ?? 'undefined; concept drawing'}`,
  ].entries()) {
    const label = window.document.createElementNS(ns, 'text');
    label.setAttribute('x', '16');
    label.setAttribute('y', String(20 + i * 20));
    label.setAttribute('fill', i ? '#b9c7d1' : '#ecf4f8');
    label.setAttribute('font-size', i ? '11' : '14');
    label.setAttribute('font-family', 'system-ui, sans-serif');
    label.textContent = text;
    output.append(label);
  }
  clone.setAttribute('x', '0');
  clone.setAttribute('y', '75');
  clone.setAttribute('width', String(width));
  clone.setAttribute('height', String(height));
  output.append(clone);
  const blob = new Blob([new XMLSerializer().serializeToString(output)], {
    type: 'image/svg+xml;charset=utf-8',
  });
  const url = URL.createObjectURL(blob);
  const link = window.document.createElement('a');
  link.href = url;
  link.download = `${document.id}-${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}.svg`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
