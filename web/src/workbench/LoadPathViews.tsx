import { useId, useRef, useState } from 'react';
import type { KeyboardEvent } from 'react';
import type { EvidenceState, LoadPath, WorkbenchDocument } from './types';
import { downloadWorkbenchSvg } from './exportSvg';
import {
  evidenceColors,
  evidenceLabels,
  layoutLoadPath,
  recordedValue,
  wrapLabel,
} from './loadPathDisplay';
import './loadPathViews.css';

interface Props {
  document: WorkbenchDocument;
  selectedPartId: string | null;
  onSelectPart: (id: string) => void;
}
type Selection = { kind: 'node' | 'edge' | 'arrow'; id: string } | null;

function activate(event: KeyboardEvent<SVGGElement>, action: () => void) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    action();
  }
}

function State({ state }: { state: EvidenceState }) {
  return <span className={`wb-forces-state wb-forces-${state}`}>{evidenceLabels[state]}</span>;
}

function Sources({ ids, document }: { ids: string[]; document: WorkbenchDocument }) {
  return (
    <details className="wb-forces-sources">
      <summary>Source IDs ({ids.length})</summary>
      {ids.length ? (
        <ul>
          {ids.map((id) => {
            const source = document.generated_from.find((item) => item.id === id);
            return (
              <li key={id}>
                <code>{id}</code>
                {source && (
                  <>
                    <span>{source.description}</span>
                    <code>{source.path}</code>
                    <code>SHA-256 {source.sha256}</code>
                  </>
                )}
              </li>
            );
          })}
        </ul>
      ) : (
        <p>No source IDs recorded for this item.</p>
      )}
    </details>
  );
}

function PartLinks({
  ids,
  document,
  onSelectPart,
}: { ids: string[] } & Pick<Props, 'document' | 'onSelectPart'>) {
  return (
    <div className="wb-forces-parts">
      {ids.map((id) => (
        <button type="button" key={id} onClick={() => onSelectPart(id)}>
          {document.parts.find((part) => part.id === id)?.label ?? id}
        </button>
      ))}
    </div>
  );
}

function Markers({ prefix }: { prefix: string }) {
  return (
    <defs>
      {(Object.keys(evidenceColors) as EvidenceState[]).map((state) => (
        <marker
          key={state}
          id={`${prefix}-${state}`}
          markerWidth="10"
          markerHeight="10"
          refX="8"
          refY="5"
          orient="auto"
          markerUnits="userSpaceOnUse"
        >
          <path d="M 0 0 L 9 5 L 0 10 Z" fill={evidenceColors[state]} />
        </marker>
      ))}
    </defs>
  );
}

function DiagramText({
  text,
  x,
  y,
  width = 30,
}: {
  text: string;
  x: number;
  y: number;
  width?: number;
}) {
  return (
    <text x={x} y={y} textAnchor="middle">
      {wrapLabel(text, width).map((line, index) => (
        <tspan key={index} x={x} dy={index ? 18 : 0}>
          {line}
        </tspan>
      ))}
    </text>
  );
}

function PathDiagram({
  path,
  document,
  selectedPartId,
  selection,
  select,
}: Omit<Props, 'onSelectPart'> & {
  path: LoadPath;
  selection: Selection;
  select: (selection: Selection, partIds: string[]) => void;
}) {
  const prefix = `wb-path-${useId().replace(/:/g, '')}`;
  const svgRef = useRef<SVGSVGElement>(null);
  const layout = layoutLoadPath(path);
  return (
    <section className="wb-forces-diagram-panel">
      <div className="wb-forces-section-heading">
        <div>
          <h3>Load-transfer topology</h3>
          <p>Click any joint or numbered arrow. Positions and arrow lengths are schematic.</p>
        </div>
        <button
          type="button"
          onClick={() => {
            if (svgRef.current)
              downloadWorkbenchSvg(svgRef.current, document, `${path.label} — load path`);
          }}
        >
          Export path SVG
        </button>
      </div>
      {layout.hasCycle && (
        <p className="wb-forces-warning">
          This record contains a cycle. Its connections are shown; the layout does not establish
          transfer order.
        </p>
      )}
      <div className="wb-forces-svg-scroll">
        <svg
          ref={svgRef}
          className="wb-forces-topology"
          style={{ minWidth: layout.width }}
          viewBox={`0 0 ${layout.width} ${layout.height}`}
          role="group"
          aria-label={`${path.label}: selectable load-transfer diagram`}
        >
          <title>{`${path.label} — recorded load path`}</title>
          <desc>
            {path.description} Schematic only; arrows are not scaled. Dashed amber connections
            remain unresolved. Blue calculations do not qualify hardware.
          </desc>
          <Markers prefix={prefix} />
          <rect className="wb-forces-svg-background" width={layout.width} height={layout.height} />
          <text x="24" y="28" className="wb-forces-svg-title">
            {path.label}
          </text>
          <text x="24" y="49" className="wb-forces-svg-caption">
            Recorded case: {path.case_id} · schematic, not to scale · engineering acceptance open
          </text>
          {path.edges.map((edge, index) => {
            const start = layout.positions.get(edge.from);
            const end = layout.positions.get(edge.to);
            if (!start || !end) return null;
            const y1 = start.y + layout.nodeHeight;
            const y2 = end.y;
            const midY = (y1 + y2) / 2;
            const midX = (start.x + end.x) / 2;
            const edgeLines = wrapLabel(`${index + 1}. ${edge.label}`);
            const labelHeight = edgeLines.length * 15 + 29;
            const d = `M ${start.x} ${y1} C ${start.x} ${midY}, ${end.x} ${midY}, ${end.x} ${y2 - 5}`;
            const selected = selection?.kind === 'edge' && selection.id === edge.id;
            const action = () => select({ kind: 'edge', id: edge.id }, edge.part_ids);
            return (
              <g
                key={edge.id}
                role="button"
                tabIndex={0}
                aria-label={`${index + 1}. ${edge.label}; ${recordedValue(edge.value, edge.unit)}; ${evidenceLabels[edge.state]}`}
                aria-pressed={selected}
                onClick={action}
                onKeyDown={(event) => activate(event, action)}
                className={`wb-forces-svg-action wb-forces-${edge.state}${selected ? ' is-selected' : ''}`}
              >
                <title>{`${edge.label}: ${recordedValue(edge.value, edge.unit)}. ${edge.note}`}</title>
                <path d={d} className="wb-forces-hit" />
                <path
                  d={d}
                  className="wb-forces-edge"
                  markerEnd={`url(#${prefix}-${edge.state})`}
                />
                <rect
                  x={midX - 116}
                  y={midY - labelHeight / 2}
                  width="232"
                  height={labelHeight}
                  rx="5"
                  className="wb-forces-edge-label"
                />
                <text
                  x={midX}
                  y={midY - labelHeight / 2 + 16}
                  textAnchor="middle"
                  className="wb-forces-edge-name"
                >
                  {edgeLines.map((line, lineIndex) => (
                    <tspan key={lineIndex} x={midX} dy={lineIndex ? 15 : 0}>
                      {line}
                    </tspan>
                  ))}
                </text>
                <text
                  x={midX}
                  y={midY + labelHeight / 2 - 9}
                  textAnchor="middle"
                  className="wb-forces-edge-value"
                >
                  {recordedValue(edge.value, edge.unit)}
                </text>
              </g>
            );
          })}
          {path.nodes.map((node) => {
            const position = layout.positions.get(node.id)!;
            const selected =
              (selection?.kind === 'node' && selection.id === node.id) ||
              (!!node.part_id && node.part_id === selectedPartId);
            const action = () =>
              select({ kind: 'node', id: node.id }, node.part_id ? [node.part_id] : []);
            return (
              <g
                key={node.id}
                role="button"
                tabIndex={0}
                aria-label={`${node.label}; ${evidenceLabels[node.state]}`}
                aria-pressed={selected}
                onClick={action}
                onKeyDown={(event) => activate(event, action)}
                className={`wb-forces-svg-action wb-forces-${node.state}${selected ? ' is-selected' : ''}`}
              >
                <title>{`${node.label}. ${node.note}`}</title>
                <rect
                  x={position.x - layout.nodeWidth / 2}
                  y={position.y}
                  width={layout.nodeWidth}
                  height={layout.nodeHeight}
                  rx="7"
                  className="wb-forces-node"
                />
                <DiagramText text={node.label} x={position.x} y={position.y + 25} />
                <text
                  x={position.x}
                  y={position.y + layout.nodeHeight - 14}
                  textAnchor="middle"
                  className="wb-forces-node-state"
                >
                  {evidenceLabels[node.state].split(' · ')[0]}
                </text>
              </g>
            );
          })}
          <text x="24" y={layout.height - 41} className="wb-forces-svg-caption">
            Red: failed screen · dashed amber: unresolved / estimated · blue: calculated, not
            qualified
          </text>
          <text x="24" y={layout.height - 20} className="wb-forces-svg-caption">
            Document: {document.id} · no fixed ground or equal sharing implied
          </text>
        </svg>
      </div>
      <ol className="wb-forces-edge-index">
        {path.edges.map((edge, index) => (
          <li key={edge.id}>
            <button
              type="button"
              aria-pressed={selection?.kind === 'edge' && selection.id === edge.id}
              className={`wb-forces-${edge.state}`}
              onClick={() => select({ kind: 'edge', id: edge.id }, edge.part_ids)}
            >
              <span className="wb-forces-index">{index + 1}</span>
              <span>
                {edge.label}
                <small>
                  {recordedValue(edge.value, edge.unit)} · {evidenceLabels[edge.state]}
                </small>
              </span>
            </button>
          </li>
        ))}
      </ol>
    </section>
  );
}

function FreeBody({
  path,
  document,
  selection,
  select,
}: Pick<Props, 'document'> & {
  path: LoadPath;
  selection: Selection;
  select: (selection: Selection, partIds: string[]) => void;
}) {
  const prefix = `wb-body-${useId().replace(/:/g, '')}`;
  const svgRef = useRef<SVGSVGElement>(null);
  const { free_body: body } = path;
  const arrowRows = body.arrows.map((arrow) => ({
    lines: wrapLabel(arrow.label, 61),
    height: Math.max(94, wrapLabel(arrow.label, 61).length * 17 + 72),
  }));
  const loadHeight = Math.max(
    80,
    arrowRows.reduce((sum, row) => sum + row.height, 0),
  );
  const supportLines = (
    body.supports.length
      ? body.supports
      : [
          'Unavailable: no support conditions recorded. No fixed clamp or equal sharing is inferred.',
        ]
  ).flatMap((support) => wrapLabel(`• ${support}`, 98));
  const supportY = loadHeight + 108;
  const height = supportY + supportLines.length * 18 + 94;
  return (
    <section className="wb-forces-diagram-panel">
      <div className="wb-forces-section-heading">
        <div>
          <h3>Free-body diagram</h3>
          <p>{body.label}</p>
        </div>
        <button
          type="button"
          onClick={() => {
            if (svgRef.current)
              downloadWorkbenchSvg(svgRef.current, document, `${path.label} — free body`);
          }}
        >
          Export free-body SVG
        </button>
      </div>
      <p className="wb-forces-help">
        Each row shows one recorded load on the isolated part. Arrows show recorded directions;
        lengths do not encode magnitude. The curved symbol identifies a moment; its rotation sign is
        not supplied by this record. No artificial ground is attached.
      </p>
      <div className="wb-forces-svg-scroll">
        <svg
          ref={svgRef}
          className="wb-forces-free-body"
          style={{ minWidth: 760 }}
          viewBox={`0 0 760 ${height}`}
          role="group"
          aria-label={`${body.label}: separate recorded force and moment arrows`}
        >
          <title>{`${body.label} — free body`}</title>
          <desc>
            One schematic arrow per recorded load. Support conditions are listed separately and must
            be resolved as recorded.
          </desc>
          <Markers prefix={prefix} />
          <rect className="wb-forces-svg-background" width="760" height={height} />
          <text x="24" y="28" className="wb-forces-svg-title">
            {body.label}
          </text>
          <text x="24" y="49" className="wb-forces-svg-caption">
            Case: {path.case_id} · separate arrows, not a combined load solution
          </text>
          {body.arrows.map((arrow, index) => {
            const row = arrowRows[index];
            const y = 109 + arrowRows.slice(0, index).reduce((sum, item) => sum + item.height, 0);
            const selected = selection?.kind === 'arrow' && selection.id === String(index);
            const action = () => select({ kind: 'arrow', id: String(index) }, [body.part_id]);
            const paths = {
              right: `M 57 ${y} L 165 ${y}`,
              left: `M 165 ${y} L 57 ${y}`,
              up: `M 110 ${y + 28} L 110 ${y - 28}`,
              down: `M 110 ${y - 28} L 110 ${y + 28}`,
              moment: `M 90 ${y + 23} A 28 28 0 1 1 137 ${y + 1}`,
            };
            return (
              <g
                key={index}
                role="button"
                tabIndex={0}
                aria-label={`${arrow.label}; ${recordedValue(arrow.value, arrow.unit)}; direction ${arrow.direction}; ${evidenceLabels[arrow.state]}`}
                aria-pressed={selected}
                onClick={action}
                onKeyDown={(event) => activate(event, action)}
                className={`wb-forces-svg-action wb-forces-${arrow.state}${selected ? ' is-selected' : ''}`}
              >
                <title>{`${arrow.label}; ${evidenceLabels[arrow.state]}. Direction: ${arrow.direction}.`}</title>
                <rect
                  x="28"
                  y={y - 37}
                  width="704"
                  height={row.height - 12}
                  rx="6"
                  className="wb-forces-arrow-row"
                />
                <path
                  d={paths[arrow.direction]}
                  className="wb-forces-edge"
                  markerEnd={`url(#${prefix}-${arrow.state})`}
                />
                <text x="200" y={y - 12}>
                  {row.lines.map((line, lineIndex) => (
                    <tspan key={lineIndex} x="200" dy={lineIndex ? 17 : 0}>
                      {line}
                    </tspan>
                  ))}
                </text>
                <text x="200" y={y + row.lines.length * 17 + 9} className="wb-forces-edge-value">
                  {recordedValue(arrow.value, arrow.unit)} ·{' '}
                  {evidenceLabels[arrow.state].split(' · ')[0]}
                </text>
              </g>
            );
          })}
          {!body.arrows.length && (
            <text x="24" y="110" className="wb-forces-svg-caption">
              No free-body loads recorded. Missing loads are not zero loads.
            </text>
          )}
          <text x="24" y={supportY} className="wb-forces-svg-title">
            Recorded supports — finite / unresolved as stated
          </text>
          {supportLines.map((line, index) => (
            <text
              key={index}
              x="24"
              y={supportY + 26 + index * 18}
              className="wb-forces-svg-caption"
            >
              {line}
            </text>
          ))}
          <text x="24" y={height - 44} className="wb-forces-svg-caption">
            Support stiffness / equal sharing is not implied. Curved symbol: moment; sign
            unspecified.
          </text>
          <text x="24" y={height - 24} className="wb-forces-svg-caption">
            Part: {body.part_id} · arrows inherit this path’s recorded case and sources
          </text>
        </svg>
      </div>
      <div className="wb-forces-supports">
        <h4>Recorded support conditions — finite / unresolved as stated</h4>
        {body.supports.length ? (
          <ul>
            {body.supports.map((support, index) => (
              <li key={index}>{support}</li>
            ))}
          </ul>
        ) : (
          <p className="wb-forces-warning">
            Support conditions unavailable. A fixed clamp, stiffness or equal reaction split cannot
            be inferred.
          </p>
        )}
        <p>Support text does not establish measured stiffness or installed qualification.</p>
      </div>
      <PartLinks
        ids={[body.part_id]}
        document={document}
        onSelectPart={(id) => select(null, [id])}
      />
    </section>
  );
}

function SelectionDetails({
  path,
  document,
  selection,
  onSelectPart,
}: Pick<Props, 'document' | 'onSelectPart'> & { path: LoadPath; selection: Selection }) {
  const edge =
    selection?.kind === 'edge' ? path.edges.find((item) => item.id === selection.id) : undefined;
  const node =
    selection?.kind === 'node' ? path.nodes.find((item) => item.id === selection.id) : undefined;
  const arrow =
    selection?.kind === 'arrow' ? path.free_body.arrows[Number(selection.id)] : undefined;
  const item = edge ?? node ?? arrow;
  const sourceIds = edge?.source_ids ?? path.source_ids;
  const partIds =
    edge?.part_ids ?? (node?.part_id ? [node.part_id] : arrow ? [path.free_body.part_id] : []);
  return (
    <aside className="wb-forces-selection" aria-live="polite">
      <span className="wb-forces-eyebrow">
        {edge
          ? 'Selected transfer / joint load'
          : node
            ? 'Selected connection'
            : arrow
              ? 'Selected free-body load'
              : 'Recorded path details'}
      </span>
      <h3>{item?.label ?? path.label}</h3>
      <State state={item?.state ?? path.state} />
      <dl>
        <div>
          <dt>Recorded case</dt>
          <dd>
            <code>{path.case_id}</code>
          </dd>
        </div>
        {(edge || arrow) && (
          <div>
            <dt>Recorded value / units</dt>
            <dd>{recordedValue((edge ?? arrow)!.value, (edge ?? arrow)!.unit)}</dd>
          </div>
        )}
        <div>
          <dt>Failure / evidence status</dt>
          <dd>
            {evidenceLabels[item?.state ?? path.state]}. Calculated demand is not joint capacity or
            physical qualification.
          </dd>
        </div>
      </dl>
      <p>{edge?.note ?? node?.note ?? path.description}</p>
      {arrow && (
        <p>
          Direction: {arrow.direction}. Case, assumptions and source IDs below belong to the
          containing path; no independent arrow-source record is supplied.
        </p>
      )}
      {node && <p>Connection sources below belong to the containing path.</p>}
      <PartLinks ids={partIds} document={document} onSelectPart={onSelectPart} />
      <h4>Recorded assumptions</h4>
      {path.assumptions.length ? (
        <ul>
          {path.assumptions.map((assumption, index) => (
            <li key={index}>{assumption}</li>
          ))}
        </ul>
      ) : (
        <p>No assumptions supplied; this does not establish an ideal support.</p>
      )}
      <Sources ids={sourceIds} document={document} />
    </aside>
  );
}

export function LoadPathViews({ document, selectedPartId, onSelectPart }: Props) {
  const [pathId, setPathId] = useState(document.load_paths[0]?.id ?? '');
  const [selection, setSelection] = useState<Selection>(null);
  const path = document.load_paths.find((item) => item.id === pathId) ?? document.load_paths[0];
  const select = (next: Selection, partIds: string[]) => {
    setSelection(next);
    if (partIds[0]) onSelectPart(partIds[0]);
  };
  return (
    <div className="wb-forces">
      <header className="wb-forces-heading">
        <div>
          <span className="wb-forces-eyebrow">Recorded engineering workbench</span>
          <h2>Loads, joints & evidence</h2>
          <p>
            Preliminary design — engineering acceptance remains open. Follow how forces pass through
            real connections; select an arrow to inspect its evidence.
          </p>
        </div>
      </header>
      <div className="wb-forces-legend" aria-label="Evidence legend">
        <State state="failed" />
        <State state="unavailable" />
        <State state="calculated" />
        <span>
          Force: N (newtons). Moment: N·m, a turning or bending effect. Stress: force per area,
          recorded in Pa or MPa.
        </span>
      </div>
      <nav className="wb-forces-path-picker" aria-label="Recorded load path">
        {document.load_paths.map((item) => (
          <button
            type="button"
            key={item.id}
            aria-pressed={path?.id === item.id}
            onClick={() => {
              setPathId(item.id);
              setSelection(null);
            }}
          >
            <span>{item.label}</span>
            <State state={item.state} />
          </button>
        ))}
      </nav>
      {path ? (
        <>
          <div className="wb-forces-path-intro">
            <h3>{path.label}</h3>
            <p>{path.description}</p>
            <code>Case: {path.case_id}</code>
          </div>
          <div className="wb-forces-workspace">
            <div className="wb-forces-drawings">
              <PathDiagram
                path={path}
                document={document}
                selectedPartId={selectedPartId}
                selection={selection}
                select={select}
              />
              <FreeBody path={path} document={document} selection={selection} select={select} />
            </div>
            <SelectionDetails
              path={path}
              document={document}
              selection={selection}
              onSelectPart={onSelectPart}
            />
          </div>
        </>
      ) : (
        <p className="wb-forces-warning">
          No recorded load paths are available for this document. Missing transfer evidence is not a
          pass.
        </p>
      )}
      <section className="wb-forces-evidence-map">
        <div className="wb-forces-section-heading">
          <div>
            <h3>Unresolved evidence & verification map</h3>
            <p>
              Select a linked part to connect the missing evidence to the assembly. These are
              required next checks, not completed tests.
            </p>
          </div>
        </div>
        <div className="wb-forces-gap-grid">
          {document.gaps.map((gap) => (
            <article key={gap.id} className={`wb-forces-gap wb-forces-${gap.state}`}>
              <div className="wb-forces-gap-stage">
                <span className="wb-forces-eyebrow">{gap.id}</span>
                <h4>{gap.label}</h4>
                <State state={gap.state} />
                <PartLinks ids={gap.part_ids} document={document} onSelectPart={onSelectPart} />
              </div>
              <div className="wb-forces-next-test">
                <span aria-hidden="true">→</span>
                <div>
                  <span className="wb-forces-eyebrow">Required verification</span>
                  <p>{gap.next_verification}</p>
                </div>
              </div>
              <Sources ids={gap.source_ids} document={document} />
            </article>
          ))}
        </div>
        {!document.gaps.length && (
          <p>No gap entries recorded. This does not establish complete engineering coverage.</p>
        )}
      </section>
      <section className="wb-forces-history">
        <h3>Historical & rejected candidate comparisons</h3>
        <p>
          These records preserve why earlier directions stopped. Their calculations do not qualify
          the selected package.
        </p>
        <div className="wb-forces-history-grid">
          {document.historical_candidates.map((candidate) => (
            <article key={candidate.id}>
              <span className="wb-forces-eyebrow">{candidate.id}</span>
              <h4>{candidate.label}</h4>
              <State state={candidate.state} />
              <p>{candidate.reason}</p>
              <Sources ids={candidate.source_ids} document={document} />
            </article>
          ))}
        </div>
        {!document.historical_candidates.length && <p>No historical candidate records supplied.</p>}
      </section>
    </div>
  );
}
