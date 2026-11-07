import RecordedCaseComparison from './RecordedCaseComparison';
import { useEffect, useState } from 'react';
import { Viewer } from '../components/Viewer';
import { PartsTree } from '../components/PartsTree';
import { PartInspector } from '../components/InspectionPanel';
import { useInspection } from '../store';
import type { InspectionDocument } from '../types';
import { loadRp1Connections } from '../workbench/rp1Connections';
import type { Rp1Connection, Rp1ConnectionsDocument } from '../workbench/rp1Connections';
import { partHref } from '../workspaces/partLinks';
import { rp1RecordedFindings } from './rp1Recorded';
import './analysis.css';

const numberText = (value: number | null, factor: number, unit: string) =>
  value === null
    ? 'Unavailable'
    : `${(value * factor).toLocaleString(undefined, { maximumFractionDigits: 3 })} ${unit}`;

export function Rp1FindingsPanel({
  vehicle,
  connection,
}: {
  vehicle: InspectionDocument;
  connection?: Rp1Connection;
}) {
  let saved;
  try {
    saved = rp1RecordedFindings(vehicle);
  } catch (error) {
    return (
      <p role="alert">{error instanceof Error ? error.message : 'Saved findings unavailable.'}</p>
    );
  }
  return (
    <section className="rp1-recorded-findings" aria-label="RP1 recorded scalar findings">
      <h2>Recorded findings — not a 3D field</h2>
      <p>
        Calculated screening results and estimated inputs from frozen AD1 v2. Neutral geometry is
        not colored by these scalar calculations. Stress means internal force per area; movement
        means a change in shape.
      </p>
      <dl className="rp1-recorded-values">
        <div>
          <dt>Optimistic fin component stress</dt>
          <dd>
            {numberText(saved.finStressPa, 1e-6, 'MPa')} ·{' '}
            {saved.finStatus === 'failed-screen' ? 'FAILED SCREEN' : 'Unavailable'}
          </dd>
        </div>
        <div>
          <dt>Optimistic component tip movement</dt>
          <dd>{numberText(saved.finMovementM, 1000, 'mm')} · retained total limit 1 mm</dd>
        </div>
        <div>
          <dt>Installed fin/root movement</dt>
          <dd>
            {numberText(saved.installedMovementM, 1000, 'mm')} — joint flexibility still needs
            evidence
          </dd>
        </div>
        <div>
          <dt>Installed adhesive peel capacity</dt>
          <dd>
            {numberText(saved.installedPeelCapacityPa, 1e-6, 'MPa')} — not inferred from glue
            strength
          </dd>
        </div>
        <div>
          <dt>Finished recovery attachment capacity</dt>
          <dd>
            {numberText(saved.recoveryCapacityN, 1, 'N')} — raw cord rating is not finished-joint
            capacity
          </dd>
        </div>
        <div>
          <dt>Outer-ring mean bond demand</dt>
          <dd>
            {numberText(saved.recoveryMeanOuterRingShearPa, 1e-6, 'MPa')} · calculated full-route
            envelope, not a spatial stress map or capacity
          </dd>
        </div>
        <div>
          <dt>Estimated available cord reach</dt>
          <dd>{numberText(saved.cordReachMm, 1, 'mm')} · dressed knot/route unmeasured</dd>
        </div>
        <div>
          <dt>Nominal minimum notch clearance</dt>
          <dd>
            {numberText(saved.notchPerFlankMm, 1, 'mm')} per flank · not a measured conditioned fit
          </dd>
        </div>
      </dl>
      <p>
        The component calculation omits a validated installed root. A smaller calculation-grid
        change does not make a failed design pass. No perfectly rigid joint or equal load sharing is
        credited.
      </p>
      <details>
        <summary>Exact saved source</summary>
        <code>{saved.source}</code>
        <p>SHA-256 {saved.sourceHash}</p>
      </details>
      {connection && (
        <section aria-label="Applicable recorded findings">
          <h3>{connection.label}</h3>
          {connection.findings.map((finding) => (
            <article key={finding.id} className={`rp1-finding-${finding.status}`}>
              <h4>{finding.label}</h4>
              <strong>
                {finding.status === 'failed-screen'
                  ? 'FAILED SCREEN'
                  : finding.status === 'unknown'
                    ? 'UNKNOWN / UNVERIFIED'
                    : 'RETAINED REQUIREMENT'}
              </strong>
              <p>{finding.detail}</p>
              <p>Later evidence: {finding.measurement_needed}</p>
              <small>Source: {finding.source_id}</small>
            </article>
          ))}
        </section>
      )}
      <p>
        Spatial stress, deformation and temperature maps: <strong>Unavailable</strong>. No
        compatible recorded field is registered to this inspection geometry. Temperature history and
        thermal clock are unavailable; no failed historical baffle result is attached.
      </p>
    </section>
  );
}

export default function Rp1RecordedAnalysis({
  vehicle,
  candidateMessage,
}: {
  vehicle: InspectionDocument;
  candidateMessage?: string;
}) {
  const selectedId = useInspection((s) => s.selectedId);
  const part = vehicle.parts.find((p) => p.id === selectedId);
  const [document, setDocument] = useState<Rp1ConnectionsDocument | null>(null);
  const [error, setError] = useState('');
  const [connectionId, setConnectionId] = useState('fin-root');
  useEffect(() => {
    const controller = new AbortController();
    void loadRp1Connections(controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setDocument(data);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted)
          setError(reason instanceof Error ? reason.message : 'Connection sources unavailable.');
      });
    return () => controller.abort();
  }, []);
  const connection = document?.connections.find((c) => c.id === connectionId);
  return (
    <main className="inspection-workspace analysis-workspace rp1-recorded-analysis">
      <PartsTree parts={vehicle.parts} candidateMessage={candidateMessage} />
      <section className="analysis-center">
        <header className="rp1-analysis-heading">
          <h1>RP1 recorded engineering evidence</h1>
          <p>
            Preliminary, unadopted design. Select a part to inspect its recorded evidence.
            Calculated findings, physical tests and flight approval are separate.
          </p>
          <label>
            Connection evidence{' '}
            <select value={connectionId} onChange={(event) => setConnectionId(event.target.value)}>
              <option value="fin-root">Fin root</option>
              <option value="recovery">Recovery attachment</option>
            </select>
          </label>
          {part && (
            <p>
              <a href={partHref('/', vehicle, part.id, 'engineering')}>
                Open this part's Engineering connections
              </a>
            </p>
          )}
          {part && connection && !connection.part_ids.includes(part.id) && (
            <p role="status">
              No specific finding for this part in {connection.label}. Connection-level context
              below is not a part qualification.
            </p>
          )}
          {error && <p role="alert">{error}</p>}
        </header>
        <Viewer
          vehicle={vehicle}
          mass={null}
          burn={0}
          onBurnChange={() => undefined}
          overlay={{
            partColors: {},
            caption: 'Neutral inspection geometry — spatial analysis unavailable',
          }}
        />
        <Rp1FindingsPanel vehicle={vehicle} connection={connection} />
        <RecordedCaseComparison left={null} right={null} />
      </section>
      <aside className="inspector">
        {part ? (
          <PartInspector
            part={part}
            parts={vehicle.parts}
            evidence={vehicle.evidence}
            design={vehicle}
          />
        ) : (
          <p>
            Select a component in the list or 3D view. The drawing dimensions and saved scalar
            findings remain estimates until their specified verification.
          </p>
        )}
      </aside>
    </main>
  );
}
