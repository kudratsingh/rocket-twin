import { rp1Quantity, validateRp1Studies } from './rp1Studies';
import type { Rp1Studies } from './rp1Studies';

const escapeXml = (value: string) =>
  value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;');
function lines(value: string, width: number): string[] {
  const words = value
    .split(/\s+/)
    .flatMap((word) => word.match(new RegExp(`.{1,${width}}`, 'g')) || []);
  const result = [''];
  for (const word of words) {
    const index = result.length - 1;
    if (result[index] && result[index].length + word.length + 1 > width) result.push(word);
    else result[index] += `${result[index] ? ' ' : ''}${word}`;
  }
  return result;
}

/** graphContents is trusted inner markup from the rendered Rp1StudyGraph, never fetched SVG. */
export function buildRp1StudySvg(
  snapshot: Rp1Studies,
  studyId: string,
  graphContents: string,
): string {
  validateRp1Studies(snapshot);
  const study = snapshot.studies.find((item) => item.id === studyId);
  if (!study || !study.nodes.length || !graphContents.trim())
    throw new Error('Study graph unavailable for this exact source.');
  const header = [
    study.label,
    'UNACCEPTED — not adopted; installed acceptance false',
    `Comparison revision: ${snapshot.id}`,
    `Study revision: ${study.id}`,
    `Configuration: ${snapshot.source_configuration.id}`,
    `Configuration source: ${snapshot.source_configuration.path}`,
    `Configuration SHA256: ${snapshot.source_configuration.sha256}`,
    `Study record: ${study.source.path}`,
    `Study SHA256: ${study.source.sha256}`,
    `Status: ${study.status}`,
    'Units: movement mm; mass g; moment N·m. Schematic relationship coordinates are not physical dimensions.',
    `Required moment ${rp1Quantity(snapshot.load_definition.required_moment_Nm, 'N·m')}; proposed ${rp1Quantity(snapshot.load_definition.proposed_moment_Nm, 'N·m')} — not adopted.`,
  ].flatMap((text) => lines(text, 110));
  const key = [
    'Numbered relationship key',
    ...study.edges.map(
      (edge, index) =>
        `${index + 1}. ${study.nodes.find((node) => node.id === edge.from)?.label} → ${study.nodes.find((node) => node.id === edge.to)?.label}: ${edge.label}`,
    ),
  ].flatMap((text) => lines(text, 43));
  const scope =
    study.id === 'G80-F2-RP1-FP1-carbon-faced-plywood-screen-v1'
      ? `FP1 ${rp1Quantity(study.displacement.reported_mm, 'mm')} already includes the unverified ${rp1Quantity(study.displacement.attachment_budget_mm, 'mm')} attachment budget. Do not add it again. Nominal component point only, not an installed pass; material sensitivities fail.`
      : `FR1 ${rp1Quantity(study.displacement.reported_mm, 'mm')} is a failed finite-support sensitivity, not a complete installed prediction. Complete installed displacement remains unavailable.`;
  const footer = [
    'Scope and limitations',
    scope,
    `Movement limit: ${rp1Quantity(study.displacement.limit_mm, 'mm')}. ${study.displacement.note}`,
    `Conditional mass credit: ${rp1Quantity(study.mass.conditional_credit_g, 'g')}. ${study.mass.note}`,
    study.maturity,
    'No CAD association, physical geometry, equal force sharing, stress field or qualification is established by this graphic.',
    'Node notes:',
    ...study.nodes.map((node) => `${node.label} [${node.status}]: ${node.note}`),
    'Recorded unknowns:',
    ...study.unknowns,
    'Additional sources:',
    ...study.sources.map((source) => `${source.path} — SHA256: ${source.sha256 || 'unavailable'}`),
  ].flatMap((text) => lines(text, 110));
  const graphHeight = study.nodes.length * 140 + 20;
  const top = 28 + header.length * 20;
  const footerTop = top + Math.max(graphHeight, key.length * 20 + 30) + 24;
  const height = footerTop + footer.length * 20 + 24;
  const text = (items: string[], x: number, y: number) =>
    items
      .map(
        (line, index) =>
          `<text x="${x}" y="${y + index * 20}" fill="#e5edf4" font-size="13">${escapeXml(line)}</text>`,
      )
      .join('');
  const metadata = {
    comparison_id: snapshot.id,
    source_configuration: snapshot.source_configuration,
    study_id: study.id,
    study_source: study.source,
    sources: study.sources,
    status: study.status,
    adopted: false,
    installed_accepted: false,
    representation: 'Source relationship schematic; no CAD association',
    units: { movement: 'mm', mass: 'g', moment: 'N·m' },
    displacement: study.displacement,
    mass: study.mass,
    scope,
  };
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="${height}" viewBox="0 0 1000 ${height}" font-family="Arial, sans-serif"><title>${escapeXml(study.label)} — UNACCEPTED</title><metadata>${escapeXml(JSON.stringify(metadata))}</metadata><rect width="100%" height="100%" fill="#14212e"/>${text(header, 20, 28)}<svg x="0" y="${top}" width="600" height="${graphHeight}" viewBox="0 0 600 ${graphHeight}">${graphContents}</svg>${text(key, 620, top + 28)}${text(footer, 20, footerTop)}</svg>`;
}

export function downloadRp1StudySvg(
  svg: SVGSVGElement | null,
  snapshot: Rp1Studies,
  studyId: string,
) {
  if (!svg) throw new Error('Study graph unavailable for export.');
  const output = buildRp1StudySvg(snapshot, studyId, svg.innerHTML);
  const url = URL.createObjectURL(new Blob([output], { type: 'image/svg+xml;charset=utf-8' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = `${studyId}-unaccepted-relationships.svg`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
