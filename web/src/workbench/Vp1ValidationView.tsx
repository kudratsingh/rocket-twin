import { useEffect, useRef, useState } from 'react';
import {
  loadVp1Validation,
  validateVp1Validation,
  vp1DraftDownload,
  vp1Money,
} from './vp1Validation';
import type { Vp1Message, Vp1Snapshot, Vp1Source } from './vp1Validation';
import './vp1Validation.css';

function graphLines(label: string, width = 25) {
  const lines = [''];
  for (const word of label.split(/\s+/)) {
    const last = lines.length - 1;
    if (lines[last] && lines[last].length + word.length + 1 > width) lines.push(word);
    else lines[last] += `${lines[last] ? ' ' : ''}${word}`;
  }
  return lines;
}

/** Exportable relationship drawing. Coordinates encode layout only, never physical dimensions. */
export function Vp1StageGraph({
  snapshot,
  stageId = 'S0',
  partId = null,
  onStage = () => {},
  onPart = () => {},
}: {
  snapshot: Vp1Snapshot;
  stageId?: string;
  partId?: string | null;
  onStage?: (id: string) => void;
  onPart?: (id: string) => void;
}) {
  const stage = snapshot.stages.find((item) => item.id === stageId) ?? snapshot.stages[0];
  const parts = snapshot.parts;
  const rows = Math.ceil(parts.length / 4);
  const height = 330 + rows * 128;
  const selectedStageX = 131 + snapshot.stages.findIndex((item) => item.id === stage.id) * 246;
  return (
    <svg
      className="vp1-stage-graph"
      xmlns="http://www.w3.org/2000/svg"
      viewBox={`0 0 1000 ${height}`}
      role="group"
      aria-label="VP1 conceptual stage and specimen map"
    >
      <title>VP1 unperformed stage and specimen relationships</title>
      <desc>
        Selectable conceptual records. No CAD association or physical geometry; all stages require
        separate authorization.
      </desc>
      <metadata>
        {JSON.stringify({
          package: snapshot.package,
          configuration: snapshot.configuration,
          protocol: snapshot.protocol,
          stage: stage.id,
          performed: false,
          accepted: false,
        })}
      </metadata>
      <rect width="1000" height={height} fill="#111e2a" rx="8" />
      <text x="22" y="30" fill="#e5f4ff" fontSize="18" fontFamily="sans-serif">
        VP1 · proposed evidence sequence · no execution authorized
      </text>
      <text x="22" y="55" fill="#b6c9d6" fontSize="13" fontFamily="sans-serif">
        Concept relationships only · no CAD association · arrows do not authorize progression
      </text>
      {snapshot.stages.map((item, index) => (
        <g key={item.id}>
          {index < 3 && (
            <g>
              <path d={`M ${246 + index * 246} 140 h 12`} stroke="#9ab6c9" strokeWidth="2" />
              <polygon
                points={`${264 + index * 246},140 ${256 + index * 246},135 ${256 + index * 246},145`}
                fill="#9ab6c9"
              />
            </g>
          )}
          <g
            role="button"
            tabIndex={0}
            aria-label={`${item.id}: ${item.label}, not authorized`}
            aria-pressed={stage.id === item.id}
            onClick={() => onStage(item.id)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                onStage(item.id);
              }
            }}
          >
            <rect
              x={18 + index * 246}
              y="82"
              width="226"
              height="132"
              rx="6"
              fill={stage.id === item.id ? '#244357' : '#182b3a'}
              stroke={stage.id === item.id ? '#9edcff' : '#60788b'}
              strokeWidth="2"
            />
            <text x={32 + index * 246} y="110" fill="#9edcff" fontSize="21" fontFamily="sans-serif">
              {item.id}
            </text>
            {graphLines(item.label).map((line, row) => (
              <text
                key={row}
                x={32 + index * 246}
                y={136 + row * 19}
                fill="#e5f4ff"
                fontSize="14"
                fontFamily="sans-serif"
              >
                {line}
              </text>
            ))}
            <text x={32 + index * 246} y="198" fill="#e8bc70" fontSize="11" fontFamily="sans-serif">
              {item.id === 'S2b' ? 'SEPARATE ROOT HOLD' : 'NOT AUTHORIZED'}
            </text>
          </g>
        </g>
      ))}
      <text x="22" y={height - 38} fill="#e5f4ff" fontSize="14" fontFamily="sans-serif">
        {stage.id} links only · brighter borders mark linked parts · all parts selectable
      </text>
      {snapshot.links
        .filter((link) => link.stage_id === stage.id)
        .map((link) => {
          const index = parts.findIndex((item) => item.id === link.part_id);
          const x = 18 + (index % 4) * 246,
            y = 274 + Math.floor(index / 4) * 128 + 48;
          return (
            <g key={link.part_id}>
              <title>{link.label}</title>
              <path
                d={`M ${selectedStageX} 214 V 242 H ${x - 8} V ${y} H ${x - 4}`}
                fill="none"
                stroke="#8bb5ce"
                strokeWidth="1.5"
              />
              <polygon points={`${x},${y} ${x - 6},${y - 4} ${x - 6},${y + 4}`} fill="#9edcff" />
            </g>
          );
        })}
      {parts.map((item, index) => {
        const x = 18 + (index % 4) * 246,
          y = 274 + Math.floor(index / 4) * 128;
        return (
          <g
            key={item.id}
            role="button"
            tabIndex={0}
            aria-label={`${item.label}: unverified`}
            aria-pressed={partId === item.id}
            onClick={() => onPart(item.id)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                onPart(item.id);
              }
            }}
          >
            <rect
              x={x}
              y={y}
              width="226"
              height="96"
              rx="6"
              fill={partId === item.id ? '#244357' : '#182b3a'}
              stroke={
                partId === item.id
                  ? '#ffffff'
                  : stage.part_ids.includes(item.id)
                    ? '#9edcff'
                    : '#60788b'
              }
              strokeWidth="2"
            />
            {graphLines(item.label).map((line, row) => (
              <text
                key={row}
                x={x + 14}
                y={y + 28 + row * 19}
                fill="#e5f4ff"
                fontSize="14"
                fontFamily="sans-serif"
              >
                {line}
              </text>
            ))}
            <text x={x + 14} y={y + 79} fill="#e8bc70" fontSize="11" fontFamily="sans-serif">
              UNVERIFIED · CONCEPT RECORD
            </text>
          </g>
        );
      })}
      <text x="22" y={height - 12} fill="#b6c9d6" fontSize="11" fontFamily="sans-serif">
        {snapshot.package.id} · source hashes embedded · no installed or flight pass
      </text>
    </svg>
  );
}

function Source({ source }: { source: Vp1Source }) {
  return (
    <span className="vp1-source">
      <code>{source.path}</code>
      <small>SHA-256: {source.sha256}</small>
    </span>
  );
}

function Draft({ message }: { message: Vp1Message }) {
  const field = useRef<HTMLTextAreaElement>(null);
  const [status, setStatus] = useState('');
  const download = vp1DraftDownload(message);
  async function copy() {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(message.text);
      setStatus('Draft copied locally. Still UNSENT.');
    } catch {
      field.current?.focus();
      field.current?.select();
      setStatus(
        'Automatic copy unavailable. Draft selected: use Command+C or Control+C to copy. Still UNSENT.',
      );
    }
  }
  return (
    <details className="vp1-draft">
      <summary>
        {message.label} <span className="vp1-badge">UNSENT</span>
      </summary>
      <p>
        <strong>Recipient:</strong> {message.recipient}
        <br />
        <strong>Recorded channel:</strong> {message.channel}
      </p>
      <label className="vp1-draft-label">
        {message.label} — full plain-text draft
        <textarea ref={field} readOnly value={message.text} rows={14} spellCheck={false} />
      </label>
      <div className="vp1-actions">
        <a href={download.href} download={download.filename}>
          Download plain text
        </a>
        <button type="button" onClick={() => void copy()}>
          Copy draft
        </button>
        <button
          type="button"
          onClick={() => {
            field.current?.focus();
            field.current?.select();
            setStatus('Draft selected. Use Command+C or Control+C to copy. Still UNSENT.');
          }}
        >
          Select text for manual copy
        </button>
      </div>
      <p role="status">{status}</p>
      <Source source={message.source} />
    </details>
  );
}

function Vp1Content({ snapshot }: { snapshot: Vp1Snapshot }) {
  const [stageId, setStageId] = useState('S0');
  const [partId, setPartId] = useState<string | null>(null);
  const stage = snapshot.stages.find((item) => item.id === stageId) ?? snapshot.stages[0];
  const part = snapshot.parts.find((item) => item.id === partId);
  const related = snapshot.links.filter((link) => link.stage_id === stage.id);
  return (
    <section className="vp1-validation" aria-label="VP1 validation package review">
      <header>
        <p className="vp1-eyebrow">G80 · evidence planning · VP1</p>
        <h1>One material. Four evidence stages.</h1>
        <p className="vp1-warning">
          <strong>UNPERFORMED · NOT AUTHORIZED · NOT ADOPTED</strong>
          <br />
          Preliminary design — engineering acceptance remains open.
        </p>
        <p>
          Review the proposed ordinary 6 mm Finnish birch (02-20850) and WEST 105/206/406 process.
          Test specimens are samples for learning about material and joints; they are not an
          accepted vehicle, complete CAD or a full-root pass.
        </p>
        <p>
          Supplier contact, purchases, physical work and paid services are all unapproved. All five
          drafts remain UNSENT. The proposed first decision is inquiries only with a $0 spending
          limit.
        </p>
        <p className="vp1-muted">Source status: {snapshot.status}</p>
      </header>

      <section aria-labelledby="vp1-stages-title">
        <h2 id="vp1-stages-title">Explore the test plan</h2>
        <p>
          Select a stage, then a linked specimen or part. Connecting lines show planned evidence
          relationships only: no CAD association, geometry, stress field or automatic progression.
        </p>
        <div className="vp1-stage-map" role="group" aria-label="Conceptual stage map">
          {snapshot.stages.map((item) => (
            <button
              key={item.id}
              type="button"
              aria-pressed={stage.id === item.id}
              onClick={() => {
                setStageId(item.id);
                setPartId(null);
              }}
            >
              <span className="vp1-stage-id">{item.id}</span>
              <strong>{item.label}</strong>
              <small>{item.id === 'S2b' ? 'SEPARATE ROOT HOLD' : 'NOT AUTHORIZED'}</small>
            </button>
          ))}
        </div>
        <Vp1StageGraph
          snapshot={snapshot}
          stageId={stage.id}
          partId={partId}
          onStage={(id) => {
            setStageId(id);
            setPartId(null);
          }}
          onPart={setPartId}
        />
        <div className="vp1-stage-detail" aria-live="polite">
          <h3>
            {stage.id} · {stage.label}
          </h3>
          <p>{stage.scope}</p>
          <dl>
            <dt>Before this stage</dt>
            <dd>{stage.entry}</dd>
            <dt>Decision / stop condition</dt>
            <dd>{stage.decision}</dd>
          </dl>
          <div
            className="vp1-part-map"
            role="group"
            aria-label={`${stage.id} linked specimens and parts`}
          >
            {related.length ? (
              related.map((link) => (
                <button
                  key={link.part_id}
                  type="button"
                  aria-pressed={partId === link.part_id}
                  onClick={() => setPartId(link.part_id)}
                >
                  <span className="vp1-link-label">{link.label}</span>
                  <strong>{snapshot.parts.find((item) => item.id === link.part_id)?.label}</strong>
                  <small>UNVERIFIED · select for explanation</small>
                </button>
              ))
            ) : (
              <p>No specimen relationships are recorded for this stage.</p>
            )}
          </div>
          <aside className="vp1-part-detail">
            {part ? (
              <>
                <h4>{part.label}</h4>
                <p>{part.note}</p>
                <p>
                  Evidence status: {part.status}. Local concept ID: <code>{part.id}</code>.
                </p>
              </>
            ) : (
              <p>Select a linked specimen or part to read what its test can establish.</p>
            )}
          </aside>
        </div>
      </section>

      <section aria-labelledby="vp1-cost-title">
        <h2 id="vp1-cost-title">Known materials, unquoted programme</h2>
        <p>
          Recorded prices as of {snapshot.price_snapshot_date}; no live inventory or quote is
          implied.
        </p>
        <dl className="vp1-costs">
          <div>
            <dt>Room-pilot materials</dt>
            <dd>{vp1Money(snapshot.costs.room_materials_usd)}</dd>
          </div>
          <div>
            <dt>Conditional full stock reserve</dt>
            <dd>{vp1Money(snapshot.costs.full_materials_usd)}</dd>
          </div>
          <div className="vp1-unknown">
            <dt>All-in programme cost</dt>
            <dd>Unavailable</dd>
          </div>
        </dl>
        <p>{snapshot.costs.note}</p>
        <p>
          Services, fixtures, calibrated measurement channels, delivery and tax are unquoted. The
          $5,000 planning reservation is an affordability screen, not a price or spending
          permission.
        </p>
        <details>
          <summary>Recorded full-reserve material list</summary>
          <div
            className="vp1-table-scroll"
            tabIndex={0}
            role="region"
            aria-label="Full reserve stock table"
          >
            <table>
              <caption>
                Full-container purchase stock; not installed flight mass or an order
              </caption>
              <thead>
                <tr>
                  <th>Stock / SKU</th>
                  <th>Reserve quantity</th>
                  <th>Unit price</th>
                  <th>Source basis / availability</th>
                </tr>
              </thead>
              <tbody>
                {snapshot.materials.map((item) => (
                  <tr key={item.id}>
                    <th scope="row">
                      <a href={item.source} target="_blank" rel="noreferrer">
                        {item.sku}
                      </a>
                    </th>
                    <td>
                      {item.quantity} × {item.unit}
                    </td>
                    <td>{vp1Money(item.unit_usd)}</td>
                    <td>
                      {item.basis}
                      <br />
                      {item.availability}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      </section>

      <section aria-labelledby="vp1-drafts-title">
        <h2 id="vp1-drafts-title">Five inquiry drafts · UNSENT</h2>
        <p>
          Expand each draft to read, download or copy its exact source text. These local actions do
          not send a message or authorize work. RFQ means request for quotation: a request for a
          written method and price.
        </p>
        {snapshot.messages.map((message) => (
          <Draft key={message.id} message={message} />
        ))}
      </section>

      <section className="vp1-limits" aria-labelledby="vp1-limits-title">
        <h2 id="vp1-limits-title">What this package cannot clear</h2>
        <p>
          <strong>
            {snapshot.limits.fin_force_N} N force · {snapshot.limits.fin_moment_Nm} N·m turning load
            · {snapshot.limits.tip_limit_mm} mm total movement limit.
          </strong>{' '}
          The design factor of {snapshot.limits.design_factor_already_applied} is already applied
          once. N means newton, N·m means newton-metre, and mm means millimetre.
        </p>
        <p>
          A root is the fin attachment and supporting structure. A coupon is a small material
          specimen; a process witness is a sample joint. Surviving these tests does not qualify the
          full fin. Total movement plus justified measurement uncertainty must remain at or below 1
          mm under the retained equivalent load; the two-point root input alone cannot prove
          distributed-panel motion.
        </p>
        <ul>
          {snapshot.limitations.map((item, index) => (
            <li key={index}>{item}</li>
          ))}
        </ul>
        <p>
          WO-03 remains open. G80 custom construction and practical performance stay first; G54 and
          G12 PID-to-RL remain separate. Browser interaction is unverified under the existing
          designated-agent ownership prerequisite.
        </p>
      </section>

      <details className="vp1-provenance">
        <summary>Exact package, protocol and configuration sources</summary>
        <p>
          Preview: <code>{snapshot.id}</code>
        </p>
        <p>
          Package: <code>{snapshot.package.id}</code>
        </p>
        <Source source={snapshot.package} />
        <p>
          Frozen configuration: <code>{snapshot.configuration.id}</code>
          <br />
          <code>{snapshot.configuration.sha256}</code>
        </p>
        <Source source={snapshot.protocol} />
        <ul>
          {snapshot.sources.map((item) => (
            <li key={item.path}>
              <Source source={item} />
            </li>
          ))}
        </ul>
        <p>
          Source identity supports traceability; it does not establish laboratory, installed or
          flight acceptance.
        </p>
      </details>
    </section>
  );
}

export function Vp1ValidationView({ snapshot }: { snapshot: Vp1Snapshot }) {
  try {
    validateVp1Validation(snapshot);
  } catch (reason) {
    return (
      <section className="vp1-validation" role="alert">
        <h1>VP1 review unavailable</h1>
        <p>{reason instanceof Error ? reason.message : 'Invalid source.'}</p>
      </section>
    );
  }
  return <Vp1Content snapshot={snapshot} />;
}

export default function Vp1Validation() {
  const [snapshot, setSnapshot] = useState<Vp1Snapshot | null>(null);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    void loadVp1Validation(controller.signal)
      .then((value) => {
        if (!controller.signal.aborted) setSnapshot(value);
      })
      .catch((reason: unknown) => {
        if (!controller.signal.aborted)
          setError(reason instanceof Error ? reason.message : 'Prepared package unavailable.');
      });
    return () => controller.abort();
  }, [retry]);
  if (error)
    return (
      <section className="vp1-validation" role="alert">
        <h1>VP1 review unavailable</h1>
        <p>{error}</p>
        <p>
          The prepared source could not be verified. No previous design or zero cost is substituted.
        </p>
        <button
          type="button"
          onClick={() => {
            setError('');
            setSnapshot(null);
            setRetry((value) => value + 1);
          }}
        >
          Retry prepared source
        </button>
      </section>
    );
  return snapshot ? (
    <Vp1ValidationView snapshot={snapshot} />
  ) : (
    <section className="vp1-validation" role="status">
      Loading the separately identified, unperformed VP1 review package…
    </section>
  );
}
