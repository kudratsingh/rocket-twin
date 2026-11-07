import { useState } from 'react';
import { fieldColor, quantityName } from './display';
import { compareRecordedCases, recordedComparisonCsv } from './recordedComparison';
import type { RecordedComparisonSource } from './recordedComparison';

export interface RecordedCaseComparisonProps {
  left: RecordedComparisonSource | null;
  right: RecordedComparisonSource | null;
  /** Shared fixed source-unit limits. Changes are explicit, never data-driven auto range. */
  legend?: readonly [number, number];
  /** Required by callers presenting synthetic software fixtures instead of recorded evidence. */
  fixtureNotice?: string;
}

function sourceKey(source: RecordedComparisonSource | null) {
  return source
    ? JSON.stringify([
        source.manifest.run_id,
        source.manifest.api_id,
        source.field.id,
        source.field.case_id,
        source.field.artifact_sha256,
        source.field.times_s,
      ])
    : '';
}

/** A recorded-scalar comparison table. It never supplies an overlay to the 3D viewer. */
export function RecordedCaseComparison({
  left,
  right,
  legend,
  fixtureNotice,
}: RecordedCaseComparisonProps) {
  const [leftChoice, setLeftChoice] = useState({ source: sourceKey(left), sample: 0 });
  const [rightChoice, setRightChoice] = useState({ source: sourceKey(right), sample: 0 });
  const leftSample = leftChoice.source === sourceKey(left) ? leftChoice.sample : 0;
  const rightSample = rightChoice.source === sourceKey(right) ? rightChoice.sample : 0;
  const model = compareRecordedCases(left, right, { leftSample, rightSample, legend });
  const compatible = model.status === 'compatible';
  const units = left?.field.units;
  const value = (sample: number | null) => (sample === null ? 'Unavailable — gap' : String(sample));
  const shade = (sample: number | null) =>
    sample === null || !model.legend
      ? undefined
      : { borderLeft: `4px solid ${fieldColor(sample, model.legend[0], model.legend[1])}` };
  function download() {
    const blob = new Blob([recordedComparisonCsv(model)], { type: 'text/csv;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'recorded-analysis-comparison.csv';
    link.click();
    URL.revokeObjectURL(url);
  }
  return (
    <section className="recorded-case-comparison" aria-label="Recorded case comparison">
      <h2>Compare recorded cases</h2>
      {fixtureNotice && (
        <p role="note">Synthetic software fixture: {fixtureNotice}. Not engineering evidence.</p>
      )}
      <p>
        Separate analysis clocks · exact recorded samples only · original source units. No
        interpolation, replay-clock coupling, inferred spatial field or geometry attachment.
      </p>
      <div role="status" aria-live="polite">
        {compatible
          ? `Compatible recorded coverage: ${left!.field.association}. ${quantityName[left!.field.quantity]} · ${units}. Difference is right minus left at the two explicitly selected samples.`
          : model.status === 'incompatible'
            ? 'Incompatible recorded cases — comparison and differences unavailable.'
            : 'Recorded comparison unavailable.'}
        {model.reasons.length > 0 && (
          <ul>
            {model.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        )}
      </div>
      {(
        [
          ['Left', left, leftSample],
          ['Right', right, rightSample],
        ] as const
      ).map(([label, source, sample]) => (
        <fieldset key={label}>
          <legend>{label} recorded case</legend>
          {!source ? (
            <p>No eligible recorded field supplied.</p>
          ) : (
            <>
              <p>
                <code>{source.manifest.run_id}</code> · case <code>{source.field.case_id}</code> ·
                field <code>{source.field.id}</code>
              </p>
              <p>
                {source.field.evidence.provenance} · {source.field.evidence.validation} ·{' '}
                {source.field.coverage_notes}
              </p>
              <label>
                {label} exact analysis sample
                <select
                  aria-label={`${label} exact analysis sample`}
                  value={sample}
                  disabled={!compatible}
                  onChange={(event) => {
                    const choice = {
                      source: sourceKey(source),
                      sample: Number(event.target.value),
                    };
                    if (label === 'Left') setLeftChoice(choice);
                    else setRightChoice(choice);
                  }}
                >
                  {source.payload.values.map((_frame, index) => (
                    <option key={index} value={index}>
                      {source.field.times_s
                        ? `${source.field.times_s[index]} s · sample ${index}`
                        : 'Static recorded case · no time axis'}
                    </option>
                  ))}
                </select>
              </label>
              <details>
                <summary>{label} exact source identity</summary>
                <dl>
                  <dt>Configuration</dt>
                  <dd>
                    <code>{source.manifest.identity.configuration_id}</code>
                  </dd>
                  <dt>Resolved specification</dt>
                  <dd>
                    <code>{source.manifest.identity.resolved_spec_sha256}</code>
                  </dd>
                  <dt>CAD revision</dt>
                  <dd>
                    <code>{source.manifest.identity.cad_revision_sha256}</code>
                  </dd>
                  <dt>Part shape identities</dt>
                  <dd>
                    <code>{JSON.stringify(source.manifest.identity.part_shape_sha256)}</code>
                  </dd>
                  <dt>Recorded artifact digest</dt>
                  <dd>
                    <code>{source.field.artifact_sha256 || 'Unavailable'}</code>
                  </dd>
                </dl>
              </details>
            </>
          )}
        </fieldset>
      ))}
      {compatible && model.legend && (
        <>
          <p>
            Shared fixed legend: {model.legend[0]} to {model.legend[1]} {units}. Values beyond the
            legend saturate the display color; the table and export retain the raw values. Missing
            values have no color. Colors are not pass/fail criteria.
          </p>
          <p>
            Left: {model.leftTime === null ? 'static case' : `${model.leftTime} s`}; right:{' '}
            {model.rightTime === null ? 'static case' : `${model.rightTime} s`}.
            {left!.field.association === 'part'
              ? ' Part-level scalars only; no spatial gradient is inferred.'
              : ' Recorded mesh sample scalars only; no surface or deformation is fabricated.'}
          </p>
          <div style={{ overflowX: 'auto' }} tabIndex={0} aria-label="Recorded comparison values">
            <table>
              <caption>Selected exact recorded samples · {units}</caption>
              <thead>
                <tr>
                  <th scope="col">Recorded coverage</th>
                  <th scope="col">Left</th>
                  <th scope="col">Right</th>
                  <th scope="col">Right − left</th>
                </tr>
              </thead>
              <tbody>
                {model.rows.map((row) => (
                  <tr key={row.sampleId}>
                    <th scope="row">{row.sampleId}</th>
                    <td style={shade(row.left)}>{value(row.left)}</td>
                    <td style={shade(row.right)}>{value(row.right)}</td>
                    <td>{value(row.difference)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
      <button type="button" onClick={download}>
        Export selected comparison CSV
      </button>
      <p>
        Export includes identities, selected exact times, original units and status. Unavailable
        comparisons export reasons without fabricated values. Engineering qualification remains
        open.
      </p>
    </section>
  );
}

export default RecordedCaseComparison;
