import type { HighGMountingSource } from './highGMountingData';
import { highGBoardSourceJson, highGMountingReference } from './highGMountingData';

export interface HighGMountingReferenceProps extends HighGMountingSource {
  selectedRef?: string | null;
}

function downloadJson(name: string, content: string): void {
  const url = URL.createObjectURL(new Blob([content], { type: 'application/json' }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = name;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Source-only mounting reference; no vehicle datum or qualified drill template. */
export default function HighGMountingReference(props: HighGMountingReferenceProps) {
  const selected = props.selectedRef ?? 'U1';
  const reference = highGMountingReference(props, selected);
  if (!reference)
    return (
      <p role="status">
        Manufacturer mounting reference unavailable for this source or selected placement. No
        historical board revision is substituted.
      </p>
    );
  const sourceJson = highGBoardSourceJson(props);
  return (
    <section aria-label="High-g manufacturer mounting reference">
      <h4>Adafruit 5374 · manufacturer mounting reference</h4>
      <p>
        Manufacturer PCB XY, origin retained, +Y up; units {reference.units}. Four source drill
        circles are nominal Ø2.5 mm. This is a reference for later inspection, not a qualified drill
        template or build permission. Vehicle mounting datums and mating tolerances are unavailable.
      </p>
      <table>
        <caption>Source mounting-hole centres in manufacturer XY (mm)</caption>
        <thead>
          <tr>
            <th scope="col">Source ref</th>
            <th scope="col">X (mm)</th>
            <th scope="col">Y (mm)</th>
            <th scope="col">Drill Ø (mm)</th>
          </tr>
        </thead>
        <tbody>
          {reference.holes.map((hole) => (
            <tr key={hole.ref}>
              <th scope="row">{hole.ref}</th>
              <td>{hole.center_mm[0]}</td>
              <td>{hole.center_mm[1]}</td>
              <td>{hole.diameter_mm}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p>
        Source PCB {reference.pcb_size_mm.join(' × ')} mm; nominal product envelope{' '}
        {reference.nominal_product_envelope_mm.join(' × ')} mm. These differ; no fit or tolerance is
        inferred.
      </p>
      <p>
        Selected source placement <strong>{reference.selected_placement.ref}</strong> ·{' '}
        {reference.selected_placement.package} · XY{' '}
        {reference.selected_placement.position_mm.join(', ')} mm · rotation{' '}
        {reference.selected_placement.rotation_deg}° · {reference.selected_placement.side} side ·
        height unavailable. Source value {reference.selected_placement.value || 'unavailable'} is
        retained, not actual silicon verification.
      </p>
      <p>
        Source {reference.source.manufacturer}, PID {reference.source.product_id}; blob{' '}
        <code>{reference.source.git_blob_sha}</code>.{' '}
        <a href={reference.source.url} target="_blank" rel="noreferrer">
          Official Eagle source
        </a>{' '}
        · {reference.license.credit} ·{' '}
        <a href={reference.license.url} target="_blank" rel="noreferrer">
          {reference.license.spdx}
        </a>
        . Component/package heights, incoming board revision and installed 3D fit remain
        unavailable.
      </p>
      <details>
        <summary>Full upstream attribution / license notice</summary>
        <pre style={{ whiteSpace: 'pre-wrap' }}>{reference.license.upstream_notice}</pre>
      </details>
      <div>
        <button
          type="button"
          onClick={() =>
            downloadJson(
              `${reference.layout_id}-${reference.selected_placement.ref.replace(/[^a-zA-Z0-9_-]/g, '_')}-mounting.json`,
              JSON.stringify(reference, null, 2),
            )
          }
        >
          Download selected placement and mounting JSON
        </button>{' '}
        <button
          type="button"
          disabled={!sourceJson}
          onClick={() => {
            if (sourceJson) downloadJson(`${reference.layout_id}-source.json`, sourceJson);
          }}
        >
          Download exact tracked board source JSON
        </button>
      </div>
      <p>
        {reference.maturity}. No measured mating tolerance, component height, actual board revision,
        vehicle registration or engineering acceptance.
      </p>
    </section>
  );
}
