import { useId, useRef, useState } from 'react';
import type { KeyboardEvent, ReactNode } from 'react';
import type { EvidenceState, JointDetail, WorkbenchDocument } from './types';
import type {
  CandidateRecord,
  ExtendedDocument,
  ExtensionGraph,
  ExtensionMode,
  ExtensionStep,
  LinkedItem,
  RecordedQuantity,
} from './extendedTypes';
import { firstAvailablePart, quantityText } from './extendedTypes';
import { downloadWorkbenchSvg } from './exportSvg';
import './extensionViews.css';

type Props = {
  document: WorkbenchDocument;
  extended: ExtendedDocument;
  mode: ExtensionMode;
  selectedPartId: string | null;
  onSelectPart: (id: string) => void;
  onOpenJoint?: (id: string) => void;
};
const COLORS: Record<EvidenceState, string> = {
  calculated: '#80bff1',
  estimated: '#ddb877',
  measured: '#84d3d0',
  unavailable: '#e2bc80',
  failed: '#ed9895',
  historical: '#a6aec2',
  superseded: '#a6aec2',
};
const wrap = (value: string, limit = 27) => {
  const lines: string[] = [];
  for (const word of value.split(/\s+/)) {
    if (!lines.length || lines[lines.length - 1].length + word.length + 1 > limit) lines.push(word);
    else lines[lines.length - 1] += ` ${word}`;
  }
  return lines;
};
const n = (value: number | null | undefined) =>
  value == null || !Number.isFinite(value)
    ? 'Unavailable'
    : new Intl.NumberFormat('en', { maximumFractionDigits: 6 }).format(value);
function activate(event: KeyboardEvent<SVGGElement>, action: () => void) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    action();
  }
}
function State({ state }: { state: EvidenceState }) {
  return (
    <span className="wb-ext-state" style={{ color: COLORS[state] }}>
      {state}
    </span>
  );
}
function Quantities({ items }: { items: RecordedQuantity[] }) {
  return items.length ? (
    <dl className="wb-ext-quantities">
      {items.map((item, index) => (
        <div key={`${item.label}-${index}`}>
          <dt>{item.label}</dt>
          <dd>
            {quantityText(item)} <State state={item.state} />
          </dd>
        </div>
      ))}
    </dl>
  ) : (
    <p className="wb-ext-muted">
      No recorded quantities supplied. Missing results remain unavailable.
    </p>
  );
}
function Sources({ ids, extended }: { ids: string[]; extended: ExtendedDocument }) {
  return (
    <details className="wb-ext-sources">
      <summary>Source identity ({ids.length})</summary>
      {ids.map((id) => {
        const source = extended.generated_from.find((item) => item.id === id);
        return (
          <div key={id}>
            <strong>{id}</strong>
            <p>{source?.description ?? 'Source reference unavailable'}</p>
            <code>{source?.path ?? 'Unavailable'}</code>
            <code>{source?.sha256 ?? 'Unavailable'}</code>
          </div>
        );
      })}
    </details>
  );
}
function PartLinks({
  ids,
  ...props
}: { ids: string[] } & Pick<Props, 'document' | 'onSelectPart'>) {
  return (
    <div className="wb-ext-part-links">
      {ids.map((id) => {
        const part = props.document.parts.find((item) => item.id === id);
        return part ? (
          <button type="button" key={id} onClick={() => props.onSelectPart(id)}>
            {part.label}
          </button>
        ) : (
          <span key={id}>{id} · candidate-specific / no C1 geometry mapping</span>
        );
      })}
    </div>
  );
}
function Figure({
  title,
  note,
  document,
  children,
}: {
  title: string;
  note: string;
  document: WorkbenchDocument;
  children: (ref: React.RefObject<SVGSVGElement | null>) => ReactNode;
}) {
  const ref = useRef<SVGSVGElement>(null);
  return (
    <section className="wb-ext-figure">
      <div className="wb-ext-figure-heading">
        <h3>{title}</h3>
        <button type="button" onClick={() => downloadWorkbenchSvg(ref.current, document, title)}>
          Export SVG
        </button>
      </div>
      <p>{note}</p>
      <div className="wb-ext-scroll">{children(ref)}</div>
      <div className="wb-ext-stamp">
        Source-linked schematic · preliminary / engineering acceptance open
      </div>
    </section>
  );
}

function GraphView({
  graph,
  electrical = false,
  ...props
}: { graph: ExtensionGraph; electrical?: boolean } & Omit<Props, 'mode'>) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const prefix = `ext-${useId().replace(/[^a-zA-Z0-9_-]/g, '')}`;
  const available = new Set(props.document.parts.map((part) => part.id));
  const nodeHeight = Math.max(112, ...graph.nodes.map((node) => wrap(node.label).length * 17 + 62));
  const rowHeight = nodeHeight + 100;
  const nodeWidth = electrical ? 200 : 244;
  const columns = Math.min(3, Math.max(graph.nodes.length, 1));
  const electricalPositions: Record<string, { x: number; y: number }> = {
    battery: { x: 260, y: 125 },
    regulator_5v: { x: 260, y: 325 },
    flight_computer: { x: 260, y: 525 },
    arming_switch: { x: 30, y: 325 },
    imu: { x: 80, y: 775 },
    baro: { x: 400, y: 775 },
    high_g_accel: { x: 80, y: 975 },
    pyro_mosfet: { x: 400, y: 975 },
    recovery_battery: { x: 740, y: 125 },
    recovery_power_switch: { x: 740, y: 325 },
    independent_recovery: { x: 740, y: 525 },
    recovery_output_harness: { x: 740, y: 775 },
  };
  const knownElectricalNets = new Set([
    'battery/regulator_5v',
    'regulator_5v/flight_computer',
    'flight_computer/imu',
    'flight_computer/baro',
    'flight_computer/pyro_mosfet',
    'arming_switch/flight_computer',
    'flight_computer/high_g_accel',
    'recovery_battery/recovery_power_switch',
    'recovery_power_switch/independent_recovery',
    'recovery_battery/independent_recovery',
    'independent_recovery/recovery_output_harness',
  ]);
  if (
    electrical &&
    (graph.nodes.some((node) => !electricalPositions[node.id]) ||
      graph.edges.some((edge) => !knownElectricalNets.has(`${edge.from}/${edge.to}`)))
  )
    return (
      <p className="wb-ext-help">
        Electrical drawing unavailable because source node/net identities changed. The recorded
        netlist remains available below; no substitute circuit is inferred.
      </p>
    );
  const positions = new Map(
    graph.nodes.map((node, index) => [
      node.id,
      electrical
        ? electricalPositions[node.id]
        : { x: 45 + (index % columns) * 315, y: 85 + Math.floor(index / columns) * rowHeight },
    ]),
  );
  const diagramBottom = electrical
    ? 1180
    : 95 + Math.ceil(graph.nodes.length / columns) * rowHeight;
  const edgeLines = graph.edges.map((edge, index) =>
    wrap(
      `${index + 1}. ${edge.label} · ${edge.state}${edge.quantities?.length ? ' · ' + edge.quantities.map((q) => `${q.label}: ${quantityText(q)}`).join('; ') : ''}`,
      115,
    ),
  );
  const legendHeight = edgeLines.reduce((total, lines) => total + lines.length * 17 + 10, 0);
  const selected =
    graph.nodes.find((node) => node.id === selectedId) ??
    graph.edges.find((edge) => edge.id === selectedId);
  const select = (item: LinkedItem) => {
    setSelectedId(item.id);
    const part = firstAvailablePart(item.part_ids, available);
    if (part) props.onSelectPart(part);
  };
  let legendY = diagramBottom;
  return (
    <div className="wb-ext-graph-area">
      <Figure
        title={graph.label}
        note={`${graph.note} Configuration: ${graph.configuration_id}. C1 attachment scope: ${graph.compatible_with_c1 ? 'source-linked current interface map only; no qualification' : 'historical / different candidate; cannot attach as current C1 results'}.`}
        document={props.document}
      >
        {(ref) => (
          <svg
            ref={ref}
            viewBox={`0 0 1000 ${diagramBottom + legendHeight + 48}`}
            role="img"
            aria-label={`${graph.label}: selectable source topology; arrows schematic`}
            data-electrical-layout={electrical ? 'separate-source-power-groups' : undefined}
          >
            <title>{`${graph.label} · ${graph.state} · preliminary schematic`}</title>
            <desc>
              Node positions and arrow lengths do not encode physical distance, force, temperature
              or capacity. Select a node or numbered connection to inspect its sources.
            </desc>
            <defs>
              {Object.entries(COLORS).map(([state, color]) => (
                <marker
                  key={state}
                  id={`${prefix}-${state}`}
                  viewBox="0 0 10 10"
                  refX="9"
                  refY="5"
                  markerWidth="7"
                  markerHeight="7"
                  orient="auto"
                >
                  <path d="M0,0L10,5L0,10Z" fill={color} />
                </marker>
              ))}
            </defs>
            <text x={28} y={27} className="wb-ext-svg-kicker">
              DIRECTED SOURCE TOPOLOGY · SCHEMATIC, NOT TO SCALE
            </text>
            <text x={28} y={49} className="wb-ext-svg-small">
              Red: failed · amber/dashed: estimated or unavailable · blue: calculated, not qualified
            </text>
            {electrical && (
              <g aria-label="Separate recorded electrical groups">
                <rect
                  x={10}
                  y={110}
                  width={665}
                  height={1010}
                  rx={9}
                  fill="#142634"
                  stroke="#45667b"
                />
                <rect
                  x={695}
                  y={110}
                  width={290}
                  height={1010}
                  rx={9}
                  fill="#182a36"
                  stroke="#678898"
                />
                <text x={28} y={84} className="wb-ext-svg-kicker">
                  MAIN AVIONICS · RECORDED POWER / SIGNAL NETS
                </text>
                <text x={28} y={102} className="wb-ext-svg-small">
                  ARM follows its recorded logic-input net.
                </text>
                <text x={710} y={84} className="wb-ext-svg-kicker">
                  INDEPENDENT RECOVERY
                </text>
                <text x={710} y={102} className="wb-ext-svg-small">
                  Separate source battery / nets
                </text>
              </g>
            )}
            {graph.edges.map((edge, index) => {
              const a = positions.get(edge.from),
                b = positions.get(edge.to);
              if (!a || !b) return null;
              const x1 = a.x + nodeWidth / 2,
                y1 = a.y + nodeHeight,
                x2 = b.x + nodeWidth / 2,
                y2 = b.y;
              const mid = (y1 + y2) / 2;
              let route = { start: [x1, y1], c1: [x1, mid], c2: [x2, mid], end: [x2, y2 - 6] };
              if (electrical) {
                const key = `${edge.from}/${edge.to}`;
                if (key === 'arming_switch/flight_computer')
                  route = {
                    start: [a.x + nodeWidth / 2, a.y + nodeHeight],
                    c1: [a.x + nodeWidth / 2, 510],
                    c2: [210, b.y + nodeHeight / 2],
                    end: [b.x - 6, b.y + nodeHeight / 2],
                  };
                else if (key === 'flight_computer/high_g_accel')
                  route = {
                    start: [a.x, a.y + nodeHeight / 2],
                    c1: [0, a.y + nodeHeight / 2],
                    c2: [0, b.y + nodeHeight / 2],
                    end: [b.x - 6, b.y + nodeHeight / 2],
                  };
                else if (key === 'flight_computer/pyro_mosfet')
                  route = {
                    start: [a.x + nodeWidth, a.y + nodeHeight / 2],
                    c1: [660, a.y + nodeHeight / 2],
                    c2: [660, b.y + nodeHeight / 2],
                    end: [b.x + nodeWidth + 6, b.y + nodeHeight / 2],
                  };
                else if (key === 'recovery_battery/independent_recovery')
                  route = {
                    start: [a.x, a.y + nodeHeight / 2],
                    c1: [695, a.y + nodeHeight / 2],
                    c2: [695, b.y + nodeHeight / 2],
                    end: [b.x - 6, b.y + nodeHeight / 2],
                  };
              }
              const badge = electrical
                ? [0, 1].map(
                    (axis) =>
                      (route.start[axis] +
                        3 * route.c1[axis] +
                        3 * route.c2[axis] +
                        route.end[axis]) /
                      8,
                  )
                : [(x1 + x2) / 2, mid];
              return (
                <g
                  key={edge.id}
                  role="button"
                  tabIndex={0}
                  aria-label={`${edge.label}; ${edge.state}`}
                  aria-pressed={selectedId === edge.id}
                  onClick={() => select(edge)}
                  onKeyDown={(event) => activate(event, () => select(edge))}
                  className={`wb-ext-svg-action ${selectedId === edge.id ? 'is-selected' : ''}`}
                >
                  <title>{`${edge.label}. ${edge.note}`}</title>
                  <path
                    d={`M${route.start[0]},${route.start[1]}C${route.c1[0]},${route.c1[1]} ${route.c2[0]},${route.c2[1]} ${route.end[0]},${route.end[1]}`}
                    data-source-edge-id={electrical ? edge.id : undefined}
                    data-net-from={electrical ? edge.from : undefined}
                    data-net-to={electrical ? edge.to : undefined}
                    fill="none"
                    stroke={COLORS[edge.state]}
                    strokeWidth={selectedId === edge.id ? 4 : 2}
                    strokeDasharray={
                      edge.state === 'unavailable' || edge.state === 'estimated' ? '7 5' : undefined
                    }
                    markerEnd={`url(#${prefix}-${edge.state})`}
                  />
                  <circle
                    cx={badge[0]}
                    cy={badge[1]}
                    r={13}
                    fill="#172c3a"
                    stroke={COLORS[edge.state]}
                  />
                  <text
                    x={badge[0]}
                    y={badge[1] + 4}
                    textAnchor="middle"
                    className="wb-ext-svg-small"
                  >
                    {index + 1}
                  </text>
                </g>
              );
            })}
            {graph.nodes.map((node) => {
              const position = positions.get(node.id)!;
              const selected =
                selectedId === node.id ||
                Boolean(props.selectedPartId && node.part_ids.includes(props.selectedPartId));
              return (
                <g
                  key={node.id}
                  role="button"
                  tabIndex={0}
                  aria-label={`${node.label}; ${node.state}`}
                  aria-pressed={selected}
                  onClick={() => select(node)}
                  onKeyDown={(event) => activate(event, () => select(node))}
                  className={`wb-ext-svg-action ${selected ? 'is-selected' : ''}`}
                >
                  <title>{`${node.label}. ${node.note}`}</title>
                  <rect
                    x={position.x}
                    y={position.y}
                    data-electrical-node-id={electrical ? node.id : undefined}
                    width={nodeWidth}
                    height={nodeHeight}
                    rx={7}
                    fill="#192e3d"
                    stroke={selected ? '#f0fbff' : COLORS[node.state]}
                    strokeWidth={selected ? 3 : 1.5}
                    strokeDasharray={
                      node.state === 'unavailable' || node.state === 'estimated' ? '7 5' : undefined
                    }
                  />
                  {wrap(node.label).map((line, index) => (
                    <text key={index} x={position.x + 15} y={position.y + 28 + index * 17}>
                      {line}
                    </text>
                  ))}
                  <text
                    x={position.x + 15}
                    y={position.y + nodeHeight - 17}
                    fill={COLORS[node.state]}
                    className="wb-ext-svg-small"
                  >
                    {node.state}
                    {!electrical && ` · ${node.kind ?? 'source component / interface'}`}
                  </text>
                </g>
              );
            })}
            {edgeLines.map((lines, index) => {
              const py = legendY;
              legendY += lines.length * 17 + 10;
              return (
                <g
                  key={graph.edges[index].id}
                  role="button"
                  tabIndex={0}
                  onClick={() => select(graph.edges[index])}
                  onKeyDown={(event) => activate(event, () => select(graph.edges[index]))}
                  aria-label={`Select connection ${index + 1}`}
                  className="wb-ext-svg-action"
                >
                  {lines.map((line, lineIndex) => (
                    <text
                      key={lineIndex}
                      x={28}
                      y={py + lineIndex * 17}
                      className="wb-ext-svg-small"
                    >
                      {line}
                    </text>
                  ))}
                </g>
              );
            })}
          </svg>
        )}
      </Figure>
      {selected ? (
        <div className="wb-ext-selection">
          <h4>{selected.label}</h4>
          <State state={selected.state} />
          <p>{selected.note}</p>
          <Quantities
            items={
              'quantities' in selected ? ((selected.quantities as RecordedQuantity[]) ?? []) : []
            }
          />
          <PartLinks ids={selected.part_ids} {...props} />
          <Sources ids={selected.source_ids} extended={props.extended} />
        </div>
      ) : (
        <p className="wb-ext-help">
          Select a node or numbered connection. Source parts stay linked across tabs; a candidate
          association does not supply its revised geometry.
        </p>
      )}
    </div>
  );
}

function Storyboard({
  title,
  steps,
  ...props
}: { title: string; steps: ExtensionStep[] } & Omit<Props, 'mode'>) {
  const [stepId, setStepId] = useState<string | null>(null);
  const selected = steps.find((step) => step.id === stepId) ?? steps[0];
  const available = new Set(props.document.parts.map((part) => part.id));
  const choose = (step: ExtensionStep) => {
    setStepId(step.id);
    const part = firstAvailablePart(step.part_ids, available);
    if (part) props.onSelectPart(part);
  };
  return (
    <section className="wb-ext-story">
      <Figure
        title={title}
        note="Recorded sequence illustration. Spacing is not travel; tool access, packed volume, extraction and clearance require actual geometry and owner verification."
        document={props.document}
      >
        {(ref) => (
          <svg
            ref={ref}
            viewBox={`0 0 1000 ${110 + Math.ceil(steps.length / 3) * 160}`}
            role="img"
            aria-label={`${title}: recorded sequence, not simulated motion`}
          >
            <title>{`${title} · service and extraction unverified`}</title>
            <text x={28} y={30} className="wb-ext-svg-kicker">
              SOURCE SEQUENCE · NO SWEPT MOTION / ACCESS VERIFICATION
            </text>
            {steps.map((step, index) => {
              const x = 25 + (index % 3) * 325,
                y = 65 + Math.floor(index / 3) * 160;
              return (
                <g
                  key={step.id}
                  role="button"
                  tabIndex={0}
                  aria-label={`Step ${index + 1}: ${step.label}`}
                  aria-pressed={selected?.id === step.id}
                  onClick={() => choose(step)}
                  onKeyDown={(event) => activate(event, () => choose(step))}
                  className={`wb-ext-svg-action ${selected?.id === step.id ? 'is-selected' : ''}`}
                >
                  <title>{step.description}</title>
                  <rect
                    x={x}
                    y={y}
                    width={290}
                    height={125}
                    rx={7}
                    fill="#182d3c"
                    stroke={selected?.id === step.id ? '#e8f7ff' : COLORS[step.state]}
                    strokeWidth={selected?.id === step.id ? 2.5 : 1.2}
                  />
                  <circle cx={x + 27} cy={y + 28} r={14} fill="#2b4b60" />
                  <text x={x + 27} y={y + 33} textAnchor="middle">
                    {index + 1}
                  </text>
                  {wrap(step.label, 31).map((line, i) => (
                    <text key={i} x={x + 15} y={y + 65 + i * 17}>
                      {line}
                    </text>
                  ))}
                  <text x={x + 15} y={y + 110} className="wb-ext-svg-small">
                    {step.state}
                  </text>
                  {index < steps.length - 1 && index % 3 !== 2 && (
                    <path
                      d={`M${x + 297},${y + 62}h18m-6,-5l6,5l-6,5`}
                      stroke="#8eb6ce"
                      fill="none"
                    />
                  )}
                </g>
              );
            })}
          </svg>
        )}
      </Figure>
      {selected && (
        <div className="wb-ext-selection">
          <h4>{selected.label}</h4>
          <p>{selected.description}</p>
          <PartLinks ids={selected.part_ids} {...props} />
          <Sources ids={selected.source_ids} extended={props.extended} />
        </div>
      )}
    </section>
  );
}

function CandidateView(props: Omit<Props, 'mode'>) {
  const candidates = props.extended.candidate_comparison;
  const [id, setId] = useState<string | null>(null);
  const selected = candidates.find((candidate) => candidate.id === id) ?? candidates[0];
  const cases = candidates.flatMap((candidate) =>
    candidate.cases.map((item) => ({ candidate, item })),
  );
  const maxMass = Math.max(...cases.map(({ item }) => item.total_g), 1);
  const maxMargin = Math.max(
    ...cases.flatMap(({ item }) => [item.loaded_margin_cal, item.burnout_margin_cal]),
    props.document.criteria?.minimum_static_margin_cal ?? 0,
    1,
  );
  const choose = (candidate: CandidateRecord) => {
    setId(candidate.id);
    const part = firstAvailablePart(
      candidate.part_ids,
      new Set(props.document.parts.map((item) => item.id)),
    );
    if (part) props.onSelectPart(part);
  };
  return (
    <>
      <h2>Compare C1 with recorded construction candidates</h2>
      <p className="wb-ext-lead">
        C1 remains frozen and preliminary. Other supplied candidates are separate stopped
        comparisons. Architecture concepts are not admitted and do not replace C1 parts or recovery
        geometry. Full intrinsic inertia remains unavailable; no candidate inherits old CAD or
        clears another candidate’s findings.
      </p>
      <div className="wb-ext-tabs">
        {candidates.map((candidate) => (
          <button
            type="button"
            key={candidate.id}
            aria-pressed={selected?.id === candidate.id}
            onClick={() => choose(candidate)}
          >
            {candidate.id} · {candidate.label}
            <State state={candidate.state} />
          </button>
        ))}
      </div>
      <Figure
        title="Recorded complete-case comparison"
        note="Bar length shows supplied complete loaded mass. Dots show supplied loaded (filled) / burnout (hollow) static margins. No mass, CG, speed, force or margin is recomputed in the browser."
        document={props.document}
      >
        {(ref) => (
          <svg
            ref={ref}
            viewBox={`0 0 1100 ${135 + cases.length * 78}`}
            role="img"
            aria-label={`Recorded mass and static margins for ${candidates.map((candidate) => candidate.id).join(', ')}`}
          >
            <title>Recorded candidates · no adoption or qualification</title>
            <text x={24} y={32} className="wb-ext-svg-kicker">
              COMPLETE LOADED MASS (g) / RECORDED STATIC MARGIN (cal)
            </text>
            <text x={325} y={60} className="wb-ext-svg-small">
              Loaded mass
            </text>
            <text x={800} y={60} className="wb-ext-svg-small">
              Loaded ● / burnout ○ margin
            </text>
            {props.document.criteria && (
              <path
                d={`M${800 + (props.document.criteria.minimum_static_margin_cal / maxMargin) * 240},68v${cases.length * 78}`}
                stroke="#d8b276"
                strokeDasharray="5 5"
              />
            )}
            {cases.map(({ candidate, item }, index) => {
              const y = 87 + index * 78;
              return (
                <g
                  key={`${candidate.id}-${item.id}`}
                  role="button"
                  tabIndex={0}
                  aria-label={`${candidate.id} ${item.label}: ${n(item.total_g)} g; loaded margin ${n(item.loaded_margin_cal)} cal`}
                  aria-pressed={selected?.id === candidate.id}
                  onClick={() => choose(candidate)}
                  onKeyDown={(event) => activate(event, () => choose(candidate))}
                  className={`wb-ext-svg-action ${selected?.id === candidate.id ? 'is-selected' : ''}`}
                >
                  <title>{`${candidate.label} · ${item.label} · ${candidate.state}`}</title>
                  <text x={24} y={y + 8}>
                    {candidate.id}
                  </text>
                  <text x={24} y={y + 28} className="wb-ext-svg-small">
                    {item.extra_aft_g ? 'additional aft / motor probe' : 'nominal complete case'}
                  </text>
                  <text x={24} y={y + 49} className="wb-ext-svg-small">
                    {candidate.geometry_maturity === 'concept'
                      ? 'CONCEPT · NOT ADMITTED'
                      : candidate.id === 'C1'
                        ? 'selected preliminary direction'
                        : 'stopped comparison'}
                  </text>
                  <rect
                    x={325}
                    y={y - 6}
                    width={(item.total_g / maxMass) * 350}
                    height={23}
                    rx={3}
                    fill={COLORS[candidate.state]}
                    fillOpacity={selected?.id === candidate.id ? 0.8 : 0.45}
                  />
                  <text x={690} y={y + 11}>
                    {n(item.total_g)} g
                  </text>
                  <path d={`M800,${y + 5}h240`} stroke="#3c596c" />
                  <circle
                    cx={800 + (item.loaded_margin_cal / maxMargin) * 240}
                    cy={y + 5}
                    r={5}
                    fill={COLORS[candidate.state]}
                  />
                  <circle
                    cx={800 + (item.burnout_margin_cal / maxMargin) * 240}
                    cy={y + 5}
                    r={7}
                    fill="none"
                    stroke={COLORS[candidate.state]}
                  />
                  <text x={800} y={y + 34} className="wb-ext-svg-small">
                    {n(item.loaded_margin_cal)} / {n(item.burnout_margin_cal)} cal
                  </text>
                  <text x={325} y={y + 36} className="wb-ext-svg-small">
                    nominal {n(item.nominal_g)} g · separate {n(item.growth_g)} g · extra aft probe{' '}
                    {n(item.extra_aft_g)} g
                  </text>
                </g>
              );
            })}
            <text x={24} y={119 + cases.length * 78} className="wb-ext-svg-small">
              Static criterion line uses supplied minimum{' '}
              {n(props.document.criteria?.minimum_static_margin_cal)} cal. Small numerical headroom
              is not useful margin.
            </text>
          </svg>
        )}
      </Figure>
      {selected && (
        <div className="wb-ext-selection">
          <h3>{selected.label}</h3>
          <State state={selected.state} />
          {selected.geometry_maturity === 'concept' && (
            <p>
              <strong>Concept architecture · NOT ADMITTED.</strong> Existing C1 parts and recovery
              geometry are unchanged; no architecture solids are supplied.
            </p>
          )}
          {selected.preferred_for_next_joint_study && (
            <p>
              Preferred only for the next bounded connection-demand study. This is not adoption,
              detailed CAD permission or construction release.
            </p>
          )}
          <p>{selected.stop_reason}</p>
          <p>
            Recorded net added mass: {n(selected.net_added_mass_g)} g · Full intrinsic inertia:
            unavailable.
          </p>
          <Quantities items={selected.quantities} />
          <PartLinks ids={selected.part_ids} {...props} />
          <div className="wb-ext-tabs">
            {selected.stop_joint_ids?.map((jointId) => (
              <button type="button" key={jointId} onClick={() => props.onOpenJoint?.(jointId)}>
                Open stop joint:{' '}
                {props.document.joints.find((joint) => joint.id === jointId)?.label ?? jointId}
              </button>
            ))}
          </div>
          <Sources ids={selected.source_ids} extended={props.extended} />
        </div>
      )}
    </>
  );
}

function Layers({ joint, ...props }: { joint: JointDetail } & Omit<Props, 'mode'>) {
  return (
    <Figure
      title={`${joint.label} · assembly layers`}
      note="Source layer order only. Illustrative separation is not actual mating, engagement or clearance. Removed items and tool paths must be demonstrated in actual geometry."
      document={props.document}
    >
      {(ref) => (
        <svg
          ref={ref}
          viewBox={`0 0 1000 ${110 + joint.layers.length * 76}`}
          role="img"
          aria-label={`${joint.label}: source assembly layer diagram`}
        >
          <title>{`${joint.label} · schematic separated layers`}</title>
          <text x={28} y={30} className="wb-ext-svg-kicker">
            SOURCE LAYERS · ADJACENCY / SERVICE CLEARANCE UNVERIFIED
          </text>
          {joint.layers.map((layer, index) => {
            const y = 65 + index * 76;
            const part = props.document.parts.find((part) => part.id === layer.part_id);
            const select = () => {
              if (part) props.onSelectPart(part.id);
            };
            return (
              <g
                key={`${layer.part_id}-${index}`}
                role={part ? 'button' : undefined}
                tabIndex={part ? 0 : undefined}
                aria-label={layer.label}
                aria-pressed={Boolean(part && props.selectedPartId === part.id)}
                onClick={select}
                onKeyDown={(event) => activate(event, select)}
                className="wb-ext-svg-action"
              >
                <title>{`${layer.label} · ${layer.material} · ${layer.state}`}</title>
                <path
                  d={`M45,${y + 12}l25,-12h200v30l-25,12H45Z M45,${y + 12}h200l25,-12 M245,${y + 12}v30`}
                  fill="#355267"
                  fillOpacity=".35"
                  stroke={props.selectedPartId === part?.id ? '#eefaff' : COLORS[layer.state]}
                  strokeDasharray={layer.thickness_mm === null ? '5 5' : undefined}
                />
                <text x={320} y={y + 16}>
                  {layer.label}
                </text>
                <text x={320} y={y + 39} className="wb-ext-svg-small">
                  {layer.material} · thickness {n(layer.thickness_mm)} mm · {layer.state}
                </text>
                {index < joint.layers.length - 1 && (
                  <path
                    d={`M80,${y + 50}v18h180`}
                    stroke="#d8b176"
                    fill="none"
                    strokeDasharray="5 4"
                  />
                )}
              </g>
            );
          })}
        </svg>
      )}
    </Figure>
  );
}

export function ExtensionViews(props: Props) {
  const [jointId, setJointId] = useState<string | null>(null);
  const [thermalView, setThermalView] = useState<'current' | 'historical'>('current');
  const extended = props.extended;
  const joint =
    extended.assembly.joints.find((item) => item.id === jointId) ?? extended.assembly.joints[0];
  return (
    <section className="wb-extension">
      <div className="wb-ext-banner">
        Preliminary source-linked engineering · no build or flight acceptance · complete C1 CAD
        unavailable
      </div>
      {props.mode === 'comparison' ? (
        <CandidateView {...props} />
      ) : props.mode === 'recovery' ? (
        <>
          <h2>Recovery topology, packing & extraction</h2>
          <p className="wb-ext-lead">
            Finished sewn loops, caps, upper restraints and actual packed extraction remain open.
            Raw webbing ratings do not qualify the installed recovery system.
          </p>
          <GraphView graph={extended.recovery.topology} {...props} />
          <Quantities items={extended.recovery.opening_assumptions} />
          <Storyboard
            title="Packing illustration"
            steps={extended.recovery.packing_steps}
            {...props}
          />
          <Storyboard
            title="Extraction illustration"
            steps={extended.recovery.extraction_steps}
            {...props}
          />
          <ul>
            {extended.recovery.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </>
      ) : props.mode === 'thermal' ? (
        <>
          <h2>Thermal connections & historical evidence</h2>
          <p className="wb-ext-lead">
            Current C1 temperatures and compatible spatial fields are unavailable. Historical
            campaigns retain their own geometry, failure and solver identities. No temperature curve
            is fabricated from scalar summaries.
          </p>
          <div className="wb-ext-tabs">
            <button
              type="button"
              aria-pressed={thermalView === 'current'}
              onClick={() => setThermalView('current')}
            >
              Current unqualified interfaces
            </button>
            <button
              type="button"
              aria-pressed={thermalView === 'historical'}
              onClick={() => setThermalView('historical')}
            >
              Historical connection model
            </button>
          </div>
          <GraphView
            key={thermalView}
            graph={
              thermalView === 'current'
                ? extended.thermal.current_interfaces
                : extended.thermal.topology
            }
            {...props}
          />
          <h3>Recorded campaign / peak summaries</h3>
          <p className="wb-ext-help">
            No time-series samples are exported here. These are recorded scalar metrics, not
            histories drawn as curves or results attached to C1.
          </p>
          <Figure
            title="Thermal evidence matrix · recorded scalars"
            note="Each row retains its run/configuration identity. All listed historical runs are incompatible with current C1. Missing values remain unavailable; no interpolated curve or field is drawn."
            document={props.document}
          >
            {(ref) => (
              <svg
                ref={ref}
                viewBox={`0 0 1100 ${100 + extended.thermal.history.reduce((total, item) => total + 82 + item.metrics.length * 22, 0)}`}
                role="img"
                aria-label="Historical thermal campaign scalar evidence, incompatible with C1"
              >
                <title>Historical thermal evidence · not current C1 results</title>
                {(() => {
                  let y = 35;
                  return extended.thermal.history.map((item) => {
                    const top = y;
                    y += 82 + item.metrics.length * 22;
                    return (
                      <g key={item.id}>
                        <rect
                          x={20}
                          y={top - 19}
                          width={1060}
                          height={66 + item.metrics.length * 22}
                          fill="#182c3a"
                          stroke={COLORS[item.state]}
                        />
                        <text x={35} y={top}>
                          {item.label} · {item.state}
                        </text>
                        <text x={35} y={top + 22} className="wb-ext-svg-small">
                          {item.configuration_id} · candidate{' '}
                          {item.candidate_identity ?? 'unavailable'} · C1 compatible: no
                        </text>
                        {item.metrics.map((metric, index) => (
                          <text
                            key={`${metric.label}-${index}`}
                            x={35}
                            y={top + 49 + index * 22}
                            className="wb-ext-svg-small"
                          >
                            {metric.label}: {quantityText(metric)} · {metric.state}
                          </text>
                        ))}
                      </g>
                    );
                  });
                })()}
              </svg>
            )}
          </Figure>
          {extended.thermal.history.map((item) => (
            <details className="wb-ext-record" key={item.id}>
              <summary>
                {item.label} · {item.state}
              </summary>
              <p>{item.note}</p>
              <p>
                Configuration: {item.configuration_id}; CAD: {item.cad_revision ?? 'unavailable'};
                candidate: {item.candidate_identity ?? 'unavailable'}; C1 compatible: no.
              </p>
              <Quantities items={item.metrics} />
              <Sources ids={item.source_ids} extended={extended} />
            </details>
          ))}
          <h3>Material and opening assumptions</h3>
          <div className="wb-ext-record-grid">
            {extended.thermal.materials.map((item) => (
              <details className="wb-ext-record" key={item.id}>
                <summary>
                  {item.label} · {item.state}
                </summary>
                <p>{item.note}</p>
                <Quantities items={item.properties} />
                <PartLinks ids={item.part_ids} {...props} />
                <Sources ids={item.source_ids} extended={extended} />
              </details>
            ))}
            {extended.thermal.openings.map((item) => (
              <details className="wb-ext-record" key={item.id}>
                <summary>
                  {item.label} · {item.state}
                </summary>
                <p>{item.note}</p>
                <Quantities items={item.dimensions} />
                <Sources ids={item.source_ids} extended={extended} />
              </details>
            ))}
          </div>
          <ul>
            {extended.thermal.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </>
      ) : props.mode === 'electrical' ? (
        <>
          <h2>Electrical nets & independent recovery power</h2>
          <p className="wb-ext-lead">
            Source connections explain the intended circuit. Missing exact pins, connector details
            and qualification stay unavailable. Planned controller blocks are separate from
            installed hardware and executed control evidence.
          </p>
          <GraphView graph={extended.electrical.topology} {...props} electrical />
          <div className="wb-ext-table">
            <table>
              <caption>Actual recorded netlist · unavailable pins are not inferred</caption>
              <thead>
                <tr>
                  <th>Net</th>
                  <th>From → to</th>
                  <th>Wire</th>
                  <th>Pin</th>
                  <th>State / scope</th>
                </tr>
              </thead>
              <tbody>
                {extended.electrical.nets.map((net) => (
                  <tr key={net.id}>
                    <th>{net.net}</th>
                    <td>
                      {net.from} → {net.to.join(', ')}
                    </td>
                    <td>{net.gauge_awg === null ? 'Unavailable' : `${net.gauge_awg} AWG`}</td>
                    <td>{net.pin ?? 'Unavailable'}</td>
                    <td>
                      <State state={net.state} />
                      <p>{net.note}</p>
                      <PartLinks ids={net.part_ids} {...props} />
                      <Sources ids={net.source_ids} extended={extended} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <ul>
            {extended.electrical.power_independence.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
          <GraphView graph={extended.electrical.control_blocks} {...props} />
        </>
      ) : props.mode === 'assembly' ? (
        <>
          <h2>Assembly, removal & service illustration</h2>
          <p className="wb-ext-lead">
            The recorded construction sequence is illustrative. No insertion/removal sweep, packing,
            nozzle passage, connector reach or tool access is accepted by these graphics.
          </p>
          <div className="wb-ext-tabs">
            {extended.assembly.joints.map((item) => (
              <button
                type="button"
                key={item.id}
                aria-pressed={joint?.id === item.id}
                onClick={() => setJointId(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
          {joint && (
            <>
              <Layers joint={joint} {...props} />
              <Quantities items={joint.dimensions.map((dimension) => ({ ...dimension }))} />
              <PartLinks ids={joint.part_ids} {...props} />
              <Sources ids={joint.source_ids} extended={extended} />
            </>
          )}
          <Storyboard
            title="Recorded assembly / service sequence"
            steps={extended.assembly.steps}
            {...props}
          />
          <ul>
            {extended.assembly.notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </>
      ) : (
        <>
          <h2>Physical requirements & verification map</h2>
          <p className="wb-ext-lead">
            Follow each requirement to its source components and required evidence. Owner-performed
            measurements, hot loads, proof tests, modal checks and flight gates remain explicit.
            This read-only map records no new verification.
          </p>
          <GraphView graph={extended.requirements} {...props} />
        </>
      )}
    </section>
  );
}
