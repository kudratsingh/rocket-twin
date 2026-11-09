import { lazy, Suspense, useState } from 'react';
import { displayValue, grams, label, number, partName, title } from '../format';
import { useInspection } from '../store';
import type { InspectionDocument, JsonValue, MassSample, Part } from '../types';
import { Icon } from './Icons';
import { representationLabel, recordedQuantity } from './presentationGroups';
import { FinAlternatives } from './FinAlternatives';
import { ThrustCurve } from './ThrustCurve';
import { InspectionGeometryAccess } from './InspectionGeometryAccess';
import { InspectionStepAccess } from './InspectionStepAccess';
import { RecoveryIdentityNotice } from './RecoveryIdentityNotice';

const HighGBoardDetail = lazy(() => import('./HighGBoardDetail'));
const ArchivedCadAccess = lazy(() => import('./ArchivedCadAccess'));
const Rp1PartEvidenceLinks = lazy(() => import('./Rp1PartEvidenceLinks'));
const ComponentDepthAccess = lazy(() => import('./ComponentDepthAccess'));

function numeric(value: JsonValue | undefined): number | undefined {
  return typeof value === 'number' ? value : undefined;
}
function record(value: JsonValue | undefined): Record<string, JsonValue> {
  return value && typeof value === 'object' && !Array.isArray(value) ? value : {};
}
function items(value: JsonValue | undefined): JsonValue[] {
  return Array.isArray(value) ? value : [];
}

function SavedFinEvidence({ evidence }: { evidence?: Record<string, JsonValue> }) {
  const fin = record(evidence?.fin);
  if (!Object.keys(fin).length) return null;
  const rows = items(fin.ideal_composite_strip_lower_deflection_only);
  const panel = record(rows.at(-1));
  return (
    <section className="detail-section">
      <h3>Recorded AD1 fin finding</h3>
      <p className="notice small">
        {fin.bonded_panel_stress_screen_pass_only === false
          ? 'Failed recorded panel strength screen.'
          : 'No installed fin pass established.'}{' '}
        The saved ideal-panel movement excludes the flexible installed attachment; it cannot
        establish total tip movement.
      </p>
      <DataList
        data={{
          factored_moment_Nm: fin.factored_moment_Nm,
          factored_force_N: fin.factored_force_N,
          optimistic_panel_movement_m: panel.deflection_m,
          panel_bending_stress_Pa: panel.maximum_bending_Pa,
        }}
      />
      <p className="small muted">
        The factor of three is already applied once. Installed movement, peel capacity,
        hot/conditioned properties and flutter remain unavailable or unqualified. Showing this
        frozen result does not rerun or adopt the failed construction.
      </p>
    </section>
  );
}

export function DataList({
  data,
  empty = 'Unavailable in the recorded specification.',
  labels = {},
}: {
  data: Record<string, JsonValue | undefined>;
  empty?: string;
  labels?: Record<string, string>;
}) {
  const values = Object.entries(data).filter(
    (entry): entry is [string, JsonValue] => entry[1] != null,
  );
  if (!values.length) return <p className="muted small">{empty}</p>;
  return (
    <dl className="data-list">
      {values.map(([key, value]) => (
        <div key={key}>
          <dt>{labels[key] || label(key)}</dt>
          <dd>{displayValue(key, value)}</dd>
        </div>
      ))}
    </dl>
  );
}

function EvidenceValue({ value }: { value?: JsonValue }) {
  if (value == null)
    return <p className="muted small">Evidence unavailable. No acceptance is implied.</p>;
  if (typeof value !== 'object') return <p className="body-copy">{String(value)}</p>;
  if (Array.isArray(value))
    return (
      <ul className="plain-list">
        {value.map((item, index) => (
          <li key={index}>
            <EvidenceValue value={item} />
          </li>
        ))}
      </ul>
    );
  return <DataList data={value} />;
}

function Traceability({
  records,
  kind,
}: {
  records: JsonValue[];
  kind: 'interface' | 'requirement' | 'failure';
}) {
  return (
    <div className="traceability-list">
      {records.map((value, index) => {
        const entry = record(value);
        return (
          <details key={String(entry.id || index)}>
            <summary>
              <span>{String(entry.id || title(kind))}</span>{' '}
              {String(
                entry.name || entry.title || entry.failure_mode || entry.purpose_source || '',
              )}
              <small>{String(entry.status || 'Open')}</small>
            </summary>
            <DataList
              data={
                kind === 'failure'
                  ? {
                      cause: entry.cause,
                      effect: entry.local_system_effect,
                      mitigation: entry.mitigation_design_change,
                      residual_risk: entry.residual_risk,
                      verification_test: entry.verification_test,
                      requirements: entry.requirements,
                      interfaces: entry.interfaces,
                    }
                  : kind === 'requirement'
                    ? {
                        criterion: entry.acceptance,
                        verification_method: entry.verification_method,
                        applicable_configurations: entry.applies_to,
                        responsible_work_order: entry.responsible_wo,
                        evidence: entry.evidence,
                      }
                    : entry
              }
            />
          </details>
        );
      })}
    </div>
  );
}

export function PartInspector({
  part,
  parts,
  evidence,
  design,
}: {
  part: Part;
  parts: Part[];
  evidence?: Record<string, JsonValue>;
  design?: InspectionDocument;
}) {
  const select = useInspection((s) => s.select);
  const isolate = useInspection((s) => s.isolate);
  const togglePart = useInspection((s) => s.togglePart);
  const focusPart = useInspection((s) => s.focusPart);
  const hidden = useInspection((s) => s.hiddenIds.includes(part.id));
  const parent = parts.find((entry) => entry.id === part.parent);
  const children = parts.filter((entry) => entry.parent === part.id);
  const position = part.location?.position_m ?? part.position_m;
  const raw = part.raw || {};
  const electrical = part.electrical || record(raw.electrical);
  const manufacturing = record(part.manufacturing);
  const source = part.source;
  return (
    <>
      <div className="panel-heading">
        <span className="eyebrow">Part inspector</span>
        <button
          className="icon-button"
          aria-label="Clear selection and show vehicle summary"
          title="Vehicle summary (Esc)"
          onClick={() => select(null)}
        >
          <Icon name="close" />
        </button>
      </div>
      <div className="part-title">
        <span
          className="large-part-dot"
          style={{ background: part.color || part.cad?.color || '#8ba4ae' }}
        />
        <div>
          <h2>{partName(part)}</h2>
          <span className="type-label">{title(part.type)}</span>
        </div>
      </div>
      <p className="part-id">{part.id}</p>
      {design && <RecoveryIdentityNotice vehicle={design} selectedPart={part} />}
      {design &&
        (design.id === 'G80-F2-RP1-AD1-definition-v2' ? (
          <Suspense fallback={<p>Loading matching Engineering connections…</p>}>
            <Rp1PartEvidenceLinks design={design} partId={part.id} />
          </Suspense>
        ) : (
          <p>RP1 connection evidence unavailable for this historical design.</p>
        ))}
      {design?.id === 'G80-F2-RP1-AD1-definition-v2' && (
        <Suspense fallback={<p>Loading detailed component availability…</p>}>
          <ComponentDepthAccess vehicle={design} part={part} />
        </Suspense>
      )}
      <div className="inspector-actions">
        <button onClick={() => focusPart(part.id)} disabled={!part.mesh_url}>
          <Icon name="fit" size={14} />
          Focus in 3D
        </button>
        <button
          onClick={() =>
            isolate(
              part.id,
              parts.map((item) => item.id),
            )
          }
          disabled={!part.mesh_url}
        >
          <Icon name="target" size={14} />
          Isolate part
        </button>
        <button disabled={!part.mesh_url} onClick={() => togglePart(part.id)}>
          <Icon name={hidden ? 'eye' : 'eyeOff'} size={14} />
          {hidden ? 'Show part' : 'Hide part'}
        </button>
      </div>
      {!part.mesh_url && (
        <div className="notice small">
          This source record has no display solid. Frame and Isolate are unavailable; selecting it
          keeps the other solids visible. Its details and matching drawings remain inspectable.
        </div>
      )}
      <p className="small muted">
        {representationLabel(part)}
        {recordedQuantity(part) ? ` · ${recordedQuantity(part)}` : ''}
      </p>
      {design?.id === 'G80-F2-RP1-AD1-definition-v2' && /fin/.test(part.id) && (
        <FinAlternatives design={design} />
      )}
      <section className="detail-section">
        <h3>What this part does</h3>
        <p className="body-copy">
          {part.function ||
            part.engineering?.function ||
            'Function is not available in the recorded specification.'}
        </p>
      </section>
      {part.id === 'high_g_accel' && design && (
        <Suspense fallback={<p>Loading manufacturer PCB reference…</p>}>
          <HighGBoardDetail
            partId={part.id}
            configurationId={design.id}
            specificationSha256={
              typeof design.identity?.specification_sha256 === 'string'
                ? design.identity.specification_sha256
                : null
            }
          />
        </Suspense>
      )}
      <section className="detail-section">
        <h3>Location & connections</h3>
        <DataList
          data={{
            position_m: position,
            cg_station_m: part.location?.cg_station_m,
            material: part.material,
          }}
        />
        <p className="small muted">
          Positions are measured aft from the nose along the vehicle axis.
        </p>
        <p className="small muted">
          Record parent/child links organize the source ledger. They do not establish physical
          attachment or a verified force path; use the linked connection evidence.
        </p>
        {parent && (
          <div className="connection-line">
            <span>Source-record parent</span>
            <button className="text-button" onClick={() => select(parent.id)}>
              {partName(parent)} <Icon name="chevron" size={12} />
            </button>
          </div>
        )}
        {children.length > 0 && (
          <div className="connection-line">
            <span>Source-record children</span>
            <div>
              {children.map((child) => (
                <button key={child.id} className="text-button" onClick={() => select(child.id)}>
                  {partName(child)}
                </button>
              ))}
            </div>
          </div>
        )}
        {part.connections?.length ? (
          <Traceability records={part.connections} kind="interface" />
        ) : null}
      </section>
      <section className="detail-section">
        <h3>Mass & dimensions</h3>
        <div className="mass-pair">
          <div>
            <span>Specification mass</span>
            <strong>{grams(part.mass_kg)}</strong>
          </div>
          <div>
            <span>
              {part.mass_basis === 'volume_density' ? 'CAD-derived mass' : 'Recorded model mass'}
            </span>
            <strong>{grams(part.cad_mass_kg ?? part.cad_mass?.mass_kg)}</strong>
          </div>
        </div>
        <p className="small muted">
          {part.mass_basis || part.cad?.mass_basis || 'Mass provenance unavailable.'} · CAD means
          computer-aided design. These are model values, not measured hardware.
        </p>
        {part.cad_bounding_size_mm && (
          <p className="small muted">
            Recorded CAD bounding size:{' '}
            {part.cad_bounding_size_mm.map((value) => number(value, 2)).join(' × ')} mm. Bounds
            describe the displayed geometry; they are not purchased hardware dimensions.
          </p>
        )}
        <DataList
          data={part.dimensions || part.geometry || {}}
          labels={
            part.type === 'fin_set'
              ? { count: 'Number of fins', thickness_m: 'Fin thickness' }
              : undefined
          }
        />
      </section>
      {(/fin/.test(part.type) || /fin.*bond|gusset/.test(part.id)) && (
        <div className="notice small">
          A gusset is a reinforcing block at the fin-to-body joint. The dimensions and mass above
          come from this resolved specification. Installed joint strength, root attachment and
          flutter acceptance remain open.
        </div>
      )}
      {/fin/.test(part.type) && <SavedFinEvidence evidence={evidence} />}
      <section className="detail-section">
        <h3>How it is made</h3>
        <DataList
          data={
            Object.keys(manufacturing).length
              ? manufacturing
              : part.build
                ? {
                    method: part.build.method,
                    generator: part.build.generator,
                    notes: part.build.notes,
                  }
                : {}
          }
        />
        <DataList
          data={{
            representation: record(part.representation).role,
            representation_scope: record(part.representation).description,
          }}
        />
        {raw.print && (
          <details className="print-details">
            <summary>Print settings</summary>
            <DataList data={record(raw.print)} />
          </details>
        )}
      </section>
      {Object.keys(electrical).length > 0 && (
        <section className="detail-section">
          <h3>Electrical ratings</h3>
          <DataList data={electrical} />
        </section>
      )}
      <section className="detail-section learn-section">
        <span className="eyebrow">Learn the design</span>
        <p className="body-copy">{part.learn}</p>
        {part.cite && <p className="small muted">Source: {part.cite}</p>}
      </section>
      <section className="detail-section">
        <h3>Failure modes & service</h3>
        {part.fmea_records?.length ? (
          <Traceability records={part.fmea_records} kind="failure" />
        ) : part.failure_modes?.length ? (
          <ul className="plain-list body-copy">
            {part.failure_modes.map((failure, index) => (
              <li key={index}>{failure}</li>
            ))}
          </ul>
        ) : (
          <p className="muted small">
            No separate failure-mode record is available for this part. Read the design explanation
            and open engineering findings.
          </p>
        )}
        {part.engineering?.service_notes && (
          <p className="body-copy">{part.engineering.service_notes}</p>
        )}
      </section>
      {!!part.requirements?.length && (
        <section className="detail-section">
          <h3>Requirements & verification</h3>
          <Traceability records={part.requirements} kind="requirement" />
        </section>
      )}
      <section className="detail-section">
        <h3>Engineering evidence</h3>
        <EvidenceValue value={part.evidence_status || part.evidence} />
        {part.engineering?.required_physical_verification?.length ? (
          <>
            <h4>Required physical verification</h4>
            <ul className="plain-list small">
              {part.engineering.required_physical_verification.map((test) => (
                <li key={test}>{test}</li>
              ))}
            </ul>
          </>
        ) : null}
      </section>
      {(part.engineering?.load_cases?.length || part.engineering?.thermal_cases?.length) && (
        <section className="detail-section">
          <h3>Linked analysis cases</h3>
          <DataList
            data={{
              load_cases: part.engineering?.load_cases,
              thermal_cases: part.engineering?.thermal_cases,
              property_basis: part.engineering?.property_basis,
            }}
          />
        </section>
      )}
      <section className="detail-section source-section">
        <h3>Source identity</h3>
        <DataList
          data={{
            specification: source?.spec_path || source?.spec,
            cad_generator: source?.cad_generator || source?.cad || part.cad?.generator,
          }}
        />
        {source?.spec_path && (
          <a
            className="source-link"
            href={`https://github.com/kudratsingh/rocket-twin/blob/main/${source.spec_path}`}
            target="_blank"
            rel="noreferrer"
          >
            Open specification in private repository <Icon name="external" size={11} />
          </a>
        )}
        {source?.shape_sha256 && (
          <div className="hash-block">
            <span>Part shape SHA-256</span>
            <code title={source.shape_sha256}>{source.shape_sha256}</code>
          </div>
        )}
      </section>
    </>
  );
}

function Checks({ checks }: { checks?: JsonValue }) {
  const values = items(checks);
  if (!values.length) return null;
  return (
    <section className="detail-section">
      <h3>Recorded design checks</h3>
      <div className="checks-list">
        {values.map((value, index) => {
          const check = record(value);
          const status = String(
            check.status ||
              (check.passed === true ? 'pass' : check.passed === false ? 'fail' : 'open'),
          );
          return (
            <div
              className={`check-row ${/fail|open|unresolved/i.test(status) ? 'check-open' : ''}`}
              key={String(check.id || index)}
            >
              <span className="status-dot" />
              <div>
                <strong>{String(check.label || check.name || check.id || 'Design check')}</strong>
                <p>{String(check.detail || check.criterion || check.reason || status)}</p>
              </div>
              <span className="check-status">{title(status)}</span>
            </div>
          );
        })}
      </div>
      <p className="small muted">
        Numerical and limit checks remain separate from physical qualification and flight approval.
      </p>
    </section>
  );
}

function VehicleSummary({
  vehicle,
  mass,
}: {
  vehicle: InspectionDocument;
  mass: MassSample | null;
}) {
  const summary = vehicle.summary;
  const motor = record(summary.motor || vehicle.motor);
  const motorQualification = record(motor.qualification);
  const margin = mass?.stability_margin_cal ?? numeric(summary.stability_margin_cal);
  const findings = items(vehicle.findings);
  const select = useInspection((s) => s.select);
  const budget = items(summary.mass_budget);
  return (
    <>
      <div className="panel-heading">
        <span className="eyebrow">Vehicle summary</span>
        <span className="status-badge">Preliminary</span>
      </div>
      <h2>{vehicle.label || vehicle.name || vehicle.id}</h2>
      <p className="summary-description">
        {vehicle.description ||
          (vehicle.role
            ? title(vehicle.role)
            : 'Resolved configuration with source-linked parts and engineering evidence.')}
      </p>
      <div className="summary-metrics">
        <div>
          <span>Vehicle mass</span>
          <strong>
            {grams(mass?.mass_kg ?? mass?.total_mass_kg ?? numeric(summary.nominal_mass_kg))}
          </strong>
          <small>
            {Array.isArray(summary.mass_cases)
              ? 'Saved cases below; no compatible burn-state model'
              : `${Math.round((mass?.burn_fraction || 0) * 100)}% propellant consumed · model estimate`}
          </small>
        </div>
        <div>
          <span>Static margin</span>
          <strong className={margin != null && margin < 0 ? 'negative-value' : ''}>
            {number(margin)} <em>cal</em>
          </strong>
          <small>One calibre = one body diameter</small>
        </div>
      </div>
      {Array.isArray(summary.mass_cases) && (
        <section className="detail-section">
          <h3>Recorded AD1 mass and launch cases</h3>
          <p className="small muted">
            Source estimates, not measurements. Each total already includes its separate full 50 g
            growth allowance. The 55 g and 68 g harness values are unverified probes, not
            uncertainty bounds. The adverse case also includes 20 g aft and its saved motor-balance
            probe.
          </p>
          <div className="recorded-cases-table" style={{ overflowX: 'auto' }}>
            <table>
              <thead>
                <tr>
                  <th>Case / harness</th>
                  <th>Total incl. growth (g)</th>
                  <th>Balance from nose (mm)</th>
                  <th>Margin (cal)</th>
                  <th>1.5 m departure (m/s)</th>
                  <th>15 formal margin (m/s)</th>
                  <th>15.5 planning margin (m/s)</th>
                </tr>
              </thead>
              <tbody>
                {summary.mass_cases.map((raw, index) => {
                  const row = record(raw);
                  const speeds = record(row.guide_mps);
                  return (
                    <tr key={index}>
                      <th>
                        {String(row.case)} / {String(row.nylon_mass_probe_g)} g
                      </th>
                      <td>{number(numeric(row.total_mass_g), 3)}</td>
                      <td>{number(numeric(row.cg_mm), 3)}</td>
                      <td>{number(numeric(row.margin_cal), 3)}</td>
                      <td>{number(numeric(speeds['1.5']), 6)}</td>
                      <td>{number(numeric(row.formal_speed_margin_mps), 6)}</td>
                      <td>{number(numeric(row.planning_speed_margin_mps), 6)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p className="small muted">
            Negative margin remains a failed screen; rounding does not establish a pass. Longer
            guides are conditional on unconfirmed equipment. Full rotational inertia and matching
            complete 3D CAD remain unavailable. These records do not authorize a build or flight.
          </p>
        </section>
      )}
      <SavedFinEvidence evidence={vehicle.evidence} />
      {margin != null && margin < 0 && (
        <div className="notice negative small">
          <Icon name="warning" />
          Negative static margin. This configuration requires active stabilization; control and
          flight acceptance remain open.
        </div>
      )}
      <section className="detail-section">
        <h3>Geometry & mass allowance</h3>
        <DataList
          data={{
            overall_length_m: summary.overall_length_m,
            length_m: summary.length_m,
            diameter_m: summary.diameter_m,
            nominal_mass_kg: summary.nominal_mass_kg,
            growth_allowance_kg: summary.growth_allowance_kg,
            loaded_mass_with_allowance_kg: summary.loaded_mass_with_allowance_kg,
          }}
        />
      </section>
      <section className="detail-section">
        <h3>Balance & aerodynamic force</h3>
        <DataList
          data={{
            cg_m: typeof mass?.cg_m === 'number' ? mass.cg_m : summary.cg_m,
            cp_m: mass?.cp_m ?? summary.cp_m,
            burnout_cg_m: summary.burnout_cg_m,
            burnout_stability_margin_cal: summary.burnout_stability_margin_cal,
          }}
        />
        <p className="small muted">
          The balance point (centre of gravity, CG) and aerodynamic force point (centre of pressure,
          CP) are measured aft from the nose.{' '}
          {Array.isArray(summary.mass_cases)
            ? 'These are saved estimated cases from the recorded backend evidence. No compatible burn-state model is available for this design.'
            : 'The browser requests burn-state values from the backend.'}
        </p>
      </section>
      <section className="detail-section">
        <h3>Propulsion</h3>
        <strong className="motor-name">{title(String(motor.id || 'Motor unavailable'))}</strong>
        <DataList
          data={{
            burn_time_s: motor.burn_time_s,
            total_impulse_ns: motor.total_impulse_ns,
            average_thrust_n: motor.average_thrust_n,
            propellant_mass_kg: motor.propellant_mass_kg,
            casing_mass_kg: motor.casing_mass_kg,
          }}
        />
        {typeof motor.id === 'string' && <ThrustCurve key={motor.id} motorId={motor.id} />}
        <details className="print-details">
          <summary>Certification & exact-hardware evidence</summary>
          <DataList data={motorQualification} />
        </details>
        <p className="small muted">
          TVC means thrust vector control: tilting the motor to steer. Certified commercial motor
          identity and operating release remain separate gates.
        </p>
      </section>
      <Checks checks={vehicle.checks} />
      <section className="detail-section">
        <h3>Engineering acceptance</h3>
        <div className="notice small">
          <Icon name="warning" />
          <span>
            Engineering acceptance remains open. Displayed CAD and calculated results do not
            establish a qualified physical vehicle.
          </span>
        </div>
        {findings.length > 0 ? (
          <ul className="findings-list">
            {findings.map((value, index) => {
              const finding = record(value);
              return (
                <li key={String(finding.id || index)}>
                  <span className="finding-status">{String(finding.status || 'Open')}</span>
                  <strong>{String(finding.title || finding.id || 'Engineering finding')}</strong>
                  <p>{String(finding.detail || '')}</p>
                  {finding.source && <small>{String(finding.source)}</small>}
                </li>
              );
            })}
          </ul>
        ) : vehicle.engineering_open?.length ? (
          <ul className="plain-list small">
            {vehicle.engineering_open.map((finding) => (
              <li key={finding}>{finding}</li>
            ))}
          </ul>
        ) : (
          <p className="small muted">
            Select a part to read its assumptions and required physical tests.
          </p>
        )}
      </section>
      <section className="detail-section">
        <h3>Mass budget</h3>
        <p className="small muted">
          Specification mass per physical part. Select a row for its source and CAD comparison.
        </p>
        <div className="mass-budget">
          <div className="budget-head">
            <span>Part</span>
            <span>Mass</span>
          </div>
          {budget.length > 0
            ? budget.map((value, index) => {
                const row = record(value);
                const id = String(row.part_id || row.id || '');
                return (
                  <button key={id || index} onClick={() => select(id)}>
                    <span>{String(row.name || title(id))}</span>
                    <span>
                      {grams(numeric(row.mass_kg))}
                      {typeof row.percent_total === 'number' && (
                        <small>{number(row.percent_total, 1)}%</small>
                      )}
                    </span>
                  </button>
                );
              })
            : vehicle.parts.map((part) => (
                <button key={part.id} onClick={() => select(part.id)}>
                  <span>{partName(part)}</span>
                  <span>{grams(part.mass_kg)}</span>
                </button>
              ))}
        </div>
      </section>
      <section className="detail-section source-section">
        <h3>Configuration identity</h3>
        <p className="small muted">
          Recorded identity binds this view to its resolved specification and CAD. SHA-256 is the
          content fingerprint.
        </p>
        {Object.entries(vehicle.identity || {}).map(([key, value]) => (
          <div className="hash-block" key={key}>
            <span>{label(key)}</span>
            <code title={displayValue(key, value)}>{displayValue(key, value)}</code>
          </div>
        ))}
      </section>
    </>
  );
}

export function InspectionPanel({
  vehicle,
  mass,
}: {
  vehicle: InspectionDocument;
  mass: MassSample | null;
}) {
  const selectedId = useInspection((s) => s.selectedId);
  const part = vehicle.parts.find((item) => item.id === selectedId);
  const [wholeFiles, setWholeFiles] = useState(false);
  const downloadPart = wholeFiles ? null : (part ?? null);
  return (
    <aside
      className="inspection-panel"
      aria-label={part ? `${partName(part)} inspector` : 'Vehicle summary'}
    >
      <div className="inspector-scroll" key={part?.id || vehicle.id}>
        <details className="detail-section" aria-label="Source 3D geometry files">
          <summary>
            3D geometry files · {downloadPart ? partName(downloadPart) : 'whole assembly'}
          </summary>
          <div className="inspector-actions" role="group" aria-label="Geometry download scope">
            <button
              type="button"
              disabled={!part}
              aria-pressed={!wholeFiles && !!part}
              onClick={() => setWholeFiles(false)}
            >
              Selected component files
            </button>
            <button
              type="button"
              aria-pressed={wholeFiles || !part}
              onClick={() => setWholeFiles(true)}
            >
              Whole rocket assembly files
            </button>
          </div>
          <p className="small muted">
            File scope does not change the selected component or the camera view.
          </p>
          {vehicle.id === 'G80-F2-RP1-AD1-definition-v2' ? (
            <>
              <InspectionGeometryAccess vehicle={vehicle} selectedPart={downloadPart} />
              <InspectionStepAccess vehicle={vehicle} selectedPart={downloadPart} />
            </>
          ) : (
            <Suspense fallback={<p>Loading recorded CAD source registry…</p>}>
              <ArchivedCadAccess vehicle={vehicle} selectedPart={downloadPart} />
            </Suspense>
          )}
        </details>
        {part ? (
          <PartInspector
            part={part}
            parts={vehicle.parts}
            evidence={vehicle.evidence}
            design={vehicle}
          />
        ) : (
          <VehicleSummary vehicle={vehicle} mass={mass} />
        )}
      </div>
      <div className="inspector-footer">YAML specification → CAD → recorded evidence → viewer</div>
    </aside>
  );
}
