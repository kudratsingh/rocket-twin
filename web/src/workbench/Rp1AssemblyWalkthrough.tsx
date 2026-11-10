import { useId, useState } from 'react';
import type { InspectionDocument } from '../types';
import {
  ASSEMBLY_EDGES,
  ASSEMBLY_NODES,
  ASSEMBLY_SOURCES,
  ASSEMBLY_STEPS,
  RP1_ASSEMBLY_CONFIGURATION,
  RP1_ASSEMBLY_SOURCE_COMMIT,
  RP1_ASSEMBLY_SPECIFICATION,
  assemblyDesignTarget,
  assemblyNode,
  assemblySourceHref,
  assemblyStep,
  matchesAssemblySource,
} from './rp1AssemblyData';
import type { AssemblyStep, Rp1AssemblyDesignTarget } from './rp1AssemblyData';
import './rp1AssemblyWalkthrough.css';

export interface Rp1AssemblyWalkthroughProps {
  vehicle: InspectionDocument;
  /** Initial reading position only; unsupported IDs fail unavailable. */
  initialStepId?: string;
  /** Optional SPA return; without it the exact source-pinned Design anchor works. */
  onInspectPart?: (target: Rp1AssemblyDesignTarget) => void;
}

function AssemblySchematic({
  step,
  selectedNodeId,
  onSelectNode,
}: {
  step: AssemblyStep;
  selectedNodeId: string;
  onSelectNode: (id: string) => void;
}) {
  const title = useId();
  const active = new Set(step.nodes);
  return (
    <figure className="rp1-assembly-schematic">
      <svg viewBox="0 0 1100 540" role="group" aria-labelledby={title}>
        <title id={title}>{`RP1 source part and service-route schematic · ${step.title}`}</title>
        <desc>
          Logical source groups, not CAD or scaled assembly positions. Highlighted groups relate to
          the current reading step. Select a group for its notes and exact source parts.
        </desc>
        <rect width="1100" height="540" rx="10" fill="#102633" />
        <text x="18" y="26" fill="#d8e9ef" fontSize="16">
          CORD / SERVICE ROUTE · conceptual order, not force vectors
        </text>
        <text x="18" y="222" fill="#d8e9ef" fontSize="16">
          FINITE STRUCTURE / ACCESS · no rigid clamps or accepted load split
        </text>
        {ASSEMBLY_EDGES.map((edge) => (
          <g key={edge.id}>
            <title>{edge.label}</title>
            <path
              d={edge.d}
              className={active.has(edge.from) && active.has(edge.to) ? 'is-active' : ''}
              fill="none"
              stroke="#69889b"
              strokeWidth="3"
              strokeDasharray="5 4"
            />
          </g>
        ))}
        <text x="18" y="410" fill="#a7c2d0" fontSize="15">
          Highlighted: source groups discussed in this step
        </text>
        <text x="18" y="438" fill="#a7c2d0" fontSize="15">
          Selected: group whose notes and part links appear below
        </text>
        <text x="18" y="477" fill="#f2c884" fontSize="15">
          No knot, textile, adhesive volume or installed contact geometry is reconstructed.
        </text>
        {ASSEMBLY_NODES.map((node) => (
          <g
            key={node.id}
            role="button"
            tabIndex={0}
            aria-label={`Read source group: ${node.label.join(' ')}`}
            aria-pressed={selectedNodeId === node.id}
            className={`rp1-assembly-node${active.has(node.id) ? ' is-active' : ''}${selectedNodeId === node.id ? ' is-selected' : ''}`}
            onClick={() => onSelectNode(node.id)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                onSelectNode(node.id);
              }
            }}
          >
            <rect
              x={node.x}
              y={node.y}
              width="195"
              height="94"
              rx="7"
              fill="#183543"
              stroke="#658799"
              strokeWidth="1.5"
            />
            {node.label.map((line, index) => (
              <text
                key={line}
                x={node.x + 12}
                y={node.y + 27 + index * 22}
                fill="#e4eff5"
                fontSize="16"
              >
                {line}
              </text>
            ))}
            <text x={node.x + 12} y={node.y + 79} fill="#b6d7e4" fontSize="12">
              {node.parts.length} source record{node.parts.length === 1 ? '' : 's'}
            </text>
          </g>
        ))}
      </svg>
      <figcaption>
        Reading layout only. Dashed connections identify cord/service relationships; they carry no
        dimensions, equal-sharing assumption or capacity. All parts retain their existing source
        accounting.
      </figcaption>
    </figure>
  );
}

function WalkthroughContent({
  vehicle,
  initialStepId,
  onInspectPart,
}: Rp1AssemblyWalkthroughProps) {
  const [stepId, setStepId] = useState(initialStepId ?? ASSEMBLY_STEPS[0].id);
  const [nodeId, setNodeId] = useState(
    assemblyStep(initialStepId ?? ASSEMBLY_STEPS[0].id)?.nodes[0] ?? 'notch',
  );
  const step = assemblyStep(stepId);
  const heading = useId();
  if (!step)
    return (
      <p role="status">
        Assembly concept step unavailable. No other source or step is substituted.
      </p>
    );
  const index = ASSEMBLY_STEPS.indexOf(step);
  const node = assemblyNode(nodeId);
  function selectStep(next: AssemblyStep) {
    setStepId(next.id);
    setNodeId(next.nodes[0]);
  }
  return (
    <section className="rp1-assembly" aria-label="RP1 assembly and service concept walkthrough">
      <header>
        <p className="rp1-assembly-eyebrow">
          READ-ONLY · FROZEN AD1 v2 · CONSTRUCTION / SERVICE CONCEPT
        </p>
        <h2>How the recorded attachment would be assembled and serviced</h2>
        <p>
          This walks through a sacrificial article/construction definition. It is not approved build
          instructions or authority for manufacture, bonding, loading or flight. Advancing a step
          records no completion or inspection pass.
        </p>
      </header>
      <div className="rp1-assembly-limits">
        <p>
          <strong>Failed fin screen:</strong> the saved optimistic wood-panel result is 7.301 MPa
          and 1.805 mm before complete installed-root flexibility. D1 retains 8.83 N·m / 331.125 N
          per fin, factor three already applied once.
        </p>
        <p>
          <strong>Unknown installed capacity:</strong> fin/root movement, peel, thermal/flutter and
          finished cord/loop/knot strength remain unverified. The permanently buried choker is not
          fully replaceable. All physical gates remain open; five inquiries are UNSENT.
        </p>
      </div>
      <nav aria-label="Assembly concept steps">
        <ol className="rp1-assembly-steps">
          {ASSEMBLY_STEPS.map((item, itemIndex) => (
            <li key={item.id}>
              <button
                type="button"
                aria-current={item.id === step.id ? 'step' : undefined}
                onClick={() => selectStep(item)}
              >
                <span>{itemIndex + 1}</span>
                {item.title}
              </button>
            </li>
          ))}
        </ol>
      </nav>
      <div className="rp1-assembly-controls">
        <button
          type="button"
          disabled={index === 0}
          onClick={() => selectStep(ASSEMBLY_STEPS[index - 1])}
        >
          Previous concept step
        </button>
        <p role="status" aria-live="polite">
          Step {index + 1} of {ASSEMBLY_STEPS.length} · {step.stage}
        </p>
        <button
          type="button"
          disabled={index === ASSEMBLY_STEPS.length - 1}
          onClick={() => selectStep(ASSEMBLY_STEPS[index + 1])}
        >
          Next concept step
        </button>
      </div>
      <AssemblySchematic step={step} selectedNodeId={nodeId} onSelectNode={setNodeId} />
      <div className="rp1-assembly-detail-layout">
        <article aria-labelledby={heading}>
          <h3 id={heading}>{step.title}</h3>
          <p>{step.summary}</p>
          <ul>
            {step.checks.map((text) => (
              <li key={text}>{text}</li>
            ))}
          </ul>
          <p className="rp1-assembly-open">
            <strong>Scope / open evidence:</strong> {step.limit}
          </p>
          <details>
            <summary>Exact source records for this step</summary>
            <ul className="rp1-assembly-citations">
              {step.citations.map((citation) => (
                <li key={`${citation.source}-${citation.locator}`}>
                  <a href={assemblySourceHref(citation.source)} target="_blank" rel="noreferrer">
                    {ASSEMBLY_SOURCES[citation.source].path}
                  </a>
                  <p>{citation.locator}</p>
                  <code>SHA-256 {ASSEMBLY_SOURCES[citation.source].sha256}</code>
                </li>
              ))}
            </ul>
          </details>
        </article>
        <aside aria-label="Selected source group and Design return">
          {node && (
            <>
              <h3>{node.label.join(' ')}</h3>
              <p>{node.note}</p>
              {!step.nodes.includes(node.id) && (
                <p>
                  This selected group is outside the highlighted step; its source notes remain
                  available.
                </p>
              )}
              <p>
                Open an exact frozen source record in Design. A display child or process allowance
                is not added hardware or a second mass charge.
              </p>
              <ul className="rp1-assembly-part-links">
                {node.parts.map((partId) => {
                  const target = assemblyDesignTarget(vehicle, partId);
                  if (!target) return <li key={partId}>Source return unavailable: {partId}</li>;
                  const part = vehicle.parts.find((row) => row.id === partId);
                  return (
                    <li key={partId}>
                      <a
                        href={target.href}
                        onClick={(event) => {
                          if (
                            onInspectPart &&
                            !event.metaKey &&
                            !event.ctrlKey &&
                            !event.shiftKey &&
                            !event.altKey
                          ) {
                            event.preventDefault();
                            onInspectPart(target);
                          }
                        }}
                      >
                        Inspect in Design: {part?.name ?? partId.replaceAll('_', ' ')}
                        <code>{partId}</code>
                      </a>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </aside>
      </div>
      <footer>
        <p>
          <code>{RP1_ASSEMBLY_CONFIGURATION}</code> · specification SHA-256{' '}
          <code>{RP1_ASSEMBLY_SPECIFICATION}</code>
        </p>
        <p>
          Source checkpoint <code>{RP1_ASSEMBLY_SOURCE_COMMIT}</code>. This schematic changes no
          source, CAD, material, mass, inertia, product identity or engineering result.
        </p>
      </footer>
    </section>
  );
}

/** Standalone integration seam; parent owns workspace entry, return state and acceptance. */
export default function Rp1AssemblyWalkthrough(props: Rp1AssemblyWalkthroughProps) {
  if (!matchesAssemblySource(props.vehicle))
    return (
      <section className="rp1-assembly" aria-label="Assembly walkthrough unavailable">
        <h2>Assembly walkthrough unavailable for this source</h2>
        <p>
          The exact current RP1 specification, AD1 evidence, inspection revision and all 55 source
          identities are required. No historical assembly or guessed build sequence is substituted.
        </p>
      </section>
    );
  return (
    <WalkthroughContent
      {...props}
      key={`${props.vehicle.id}:${String(props.vehicle.identity?.specification_sha256)}`}
    />
  );
}
