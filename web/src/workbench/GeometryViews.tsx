import { useId, useRef, useState } from 'react';
import type { CSSProperties, KeyboardEvent, ReactNode, RefObject } from 'react';
import type { JointDetail, WorkbenchDocument, WorkbenchPart } from './types';
import { downloadWorkbenchSvg } from './exportSvg';
import './geometryViews.css';

type Props = {
  document: WorkbenchDocument;
  selectedPartId: string | null;
  onSelectPart: (id: string) => void;
};

type Selection = Pick<Props, 'selectedPartId' | 'onSelectPart'>;
const PALETTE = ['#65c7df', '#b6a0ed', '#e9b86a', '#84c59a', '#e58f9c', '#91aee9'];
const number = (value: number) =>
  new Intl.NumberFormat('en', { maximumFractionDigits: 3 }).format(value);
const maturityLabel = (value: WorkbenchPart['geometry_maturity']) =>
  ({
    detailed_cad: 'Detailed CAD',
    envelope: 'Envelope',
    concept: 'Concept',
    undefined: 'Undefined geometry',
  })[value];
const finite = (value: number | null | undefined): value is number =>
  value != null && Number.isFinite(value);
const positioned = (part: WorkbenchPart) =>
  finite(part.start_mm) && finite(part.length_mm) && finite(part.radius_mm);
const colorFor = (doc: WorkbenchDocument, subsystem: string) => {
  const keys = [...new Set(doc.parts.map((part) => part.subsystem))];
  return PALETTE[Math.max(0, keys.indexOf(subsystem)) % PALETTE.length];
};
const selectable = (part: WorkbenchPart, selection: Selection) => ({
  role: 'button' as const,
  tabIndex: 0,
  'aria-label': `${part.label}: ${maturityLabel(part.geometry_maturity)}; ${part.state}. Select part`,
  'aria-pressed': part.id === selection.selectedPartId,
  className: `wb-geometry-part ${part.id === selection.selectedPartId ? 'is-selected' : ''} maturity-${part.geometry_maturity}`,
  onClick: () => selection.onSelectPart(part.id),
  onKeyDown: (event: KeyboardEvent<SVGGElement>) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      selection.onSelectPart(part.id);
    }
  },
});

function PartTitle({ part }: { part: WorkbenchPart }) {
  return (
    <title>{`${part.label} · ${maturityLabel(part.geometry_maturity)} · ${part.state}\n${part.function}\n${part.findings.join('\n')}`}</title>
  );
}

function Dimension({ x1, x2, y, label }: { x1: number; x2: number; y: number; label: string }) {
  return (
    <g className="wb-geometry-dimension" aria-label={label}>
      <path d={`M${x1},${y - 6}v12 M${x1},${y}H${x2} M${x2},${y - 6}v12`} />
      <text x={(x1 + x2) / 2} y={y - 9} textAnchor="middle">
        {label}
      </text>
    </g>
  );
}

function Figure({
  title,
  note,
  svgRef,
  document: doc,
  children,
  className = '',
}: {
  title: string;
  note: string;
  svgRef: RefObject<SVGSVGElement | null>;
  document: WorkbenchDocument;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`wb-geometry-figure ${className}`}>
      <div className="wb-geometry-figure-heading">
        <h3>{title}</h3>
        <button type="button" onClick={() => downloadWorkbenchSvg(svgRef.current, doc, title)}>
          Export SVG
        </button>
      </div>
      <p className="wb-geometry-figure-note">{note}</p>
      <div className="wb-geometry-canvas">{children}</div>
      <p className="wb-geometry-stamp">Preliminary illustration · engineering acceptance open</p>
    </section>
  );
}

/** Orthographic placement only: no fit, motion, stress or other engineering calculation. */
function AxialDrawing({
  document: doc,
  section = false,
  region,
  ...selection
}: Props & {
  section?: boolean;
  region?: { start: number; end: number; parts: WorkbenchPart[] };
}) {
  const left = 64;
  const right = 1036;
  const start = region?.start ?? 0;
  const end = region?.end ?? doc.arrangement.overall_length_mm;
  const scale = (right - left) / Math.max(end - start, 1);
  const x = (station: number) => left + (station - start) * scale;
  const parts = (region?.parts ?? doc.parts).filter(positioned);
  const bodyRadius = doc.arrangement.body_diameter_mm / 2;
  const extent = Math.max(
    bodyRadius,
    ...parts.map(
      (part) => (part.radius_mm ?? 0) + (part.shape === 'fin' ? (part.span_mm ?? 0) : 0),
    ),
  );
  // Full arrangement uses the same radial and axial scale. Detail panels explicitly separate their scales.
  const radialScale = region
    ? Math.min(scale, 105 / Math.max(extent, 1))
    : Math.min(scale, 110 / Math.max(extent, 1));
  const axis = 178;
  const y = (radius: number) => axis - radius * radialScale;
  const visible =
    section || region
      ? parts
      : parts.filter(
          (part) =>
            part.shape === 'shell' || part.shape === 'fin' || part.geometry_maturity === 'envelope',
        );
  const ticks = [
    ...new Set([
      start,
      end,
      ...(region
        ? parts.map((part) => part.start_mm!)
        : [
            doc.arrangement.nose_length_mm,
            ...doc.arrangement.subsystem_ranges.map((range) => range.start_mm),
          ]),
    ]),
  ]
    .filter((station) => station >= start && station <= end)
    .sort((a, b) => a - b);
  const sorted = [...visible].sort((a, b) => (b.radius_mm ?? 0) - (a.radius_mm ?? 0));
  const selected = parts.find((part) => part.id === selection.selectedPartId);
  return (
    <>
      <text x={left} y={24} className="wb-geometry-svg-kicker">
        NOSE / FORWARD
      </text>
      <text x={right} y={24} textAnchor="end" className="wb-geometry-svg-kicker">
        AFT / MOTOR END →
      </text>
      <Dimension
        x1={left}
        x2={right}
        y={52}
        label={`${number(end - start)} mm ${region ? 'displayed axial span' : 'overall reference'}`}
      />
      <path className="wb-geometry-reference" d={`M${left},${axis}H${right}`} />
      {!region && (
        <>
          <path
            className="wb-geometry-envelope"
            d={`M${x(0)},${axis}L${x(doc.arrangement.nose_length_mm)},${y(bodyRadius)}H${right}V${y(-bodyRadius)}H${x(doc.arrangement.nose_length_mm)}Z`}
          />
          <text
            x={x(doc.arrangement.nose_length_mm / 2)}
            y={axis - 13}
            textAnchor="middle"
            className="wb-geometry-small"
          >
            nose envelope
          </text>
        </>
      )}
      {sorted.map((part) => {
        const px = x(part.start_mm!);
        const width = part.length_mm! * scale;
        const radius = part.radius_mm!;
        const inner = finite(part.inner_radius_mm)
          ? part.inner_radius_mm
          : finite(part.thickness_mm)
            ? Math.max(0, radius - part.thickness_mm)
            : null;
        const color = colorFor(doc, part.subsystem);
        const style = { '--part-color': color } as CSSProperties;
        const finKnown =
          part.shape === 'fin' &&
          finite(part.span_mm) &&
          finite(part.root_chord_mm) &&
          finite(part.tip_chord_mm) &&
          finite(part.sweep_mm);
        const finAzimuths = part.azimuth_deg?.filter(finite) ?? [];
        return (
          <g key={part.id} {...selectable(part, selection)} style={style}>
            <PartTitle part={part} />
            {finKnown ? (
              <>
                {finAzimuths.map((angle, index) => {
                  const projection = Math.cos((angle * Math.PI) / 180);
                  return (
                    <path
                      key={`${angle}-${index}`}
                      data-fin-azimuth-deg={angle}
                      data-radial-projection={projection}
                      d={`M${px},${y(projection * radius)}l${part.sweep_mm! * scale},${-projection * part.span_mm! * radialScale}h${part.tip_chord_mm! * scale}L${px + part.root_chord_mm! * scale},${y(projection * radius)}Z`}
                    />
                  );
                })}
                {!finAzimuths.length && (
                  <text x={px} y={axis - 20} className="wb-geometry-small">
                    Fin azimuth unavailable: projection omitted
                  </text>
                )}
              </>
            ) : section && (part.shape === 'shell' || part.shape === 'ring') && inner != null ? (
              <>
                <rect x={px} y={y(radius)} width={width} height={(radius - inner) * radialScale} />
                <rect x={px} y={y(-inner)} width={width} height={(radius - inner) * radialScale} />
                <path
                  className="wb-geometry-open-face"
                  d={`M${px},${y(radius)}V${y(-radius)}M${px + width},${y(radius)}V${y(-radius)}`}
                />
              </>
            ) : (
              <rect x={px} y={y(radius)} width={width} height={radius * 2 * radialScale} />
            )}
          </g>
        );
      })}
      {ticks.map((station, index) => (
        <g key={station} className="wb-geometry-station">
          <path d={`M${x(station)},${axis + 116}v8`} />
          <text x={x(station)} y={axis + 139 + (index % 2) * 15} textAnchor="middle">
            {number(station)}
          </text>
        </g>
      ))}
      {visible.some((part) => part.shape === 'fin') && (
        <text x={left} y={347} className="wb-geometry-small">
          Fin centerplanes projected onto the axial / 0° radial plane; coincident projections
          overlap.
        </text>
      )}
      <text x={left} y={362} className="wb-geometry-small">
        Axial station (mm), increasing aft ·{' '}
        {region
          ? 'radial scale fitted separately for readability'
          : 'source dimensions; no contact or fit inferred'}
      </text>
      {selected && (
        <g className="wb-geometry-selected-label">
          <path d={`M${x(selected.start_mm! + selected.length_mm! / 2)},${axis}V82`} />
          <text
            x={Math.min(
              right - 100,
              Math.max(left + 100, x(selected.start_mm! + selected.length_mm! / 2)),
            )}
            y={76}
            textAnchor="middle"
          >
            {selected.label}
          </text>
        </g>
      )}
      {section && (
        <text x={right} y={280} textAnchor="end" className="wb-geometry-small">
          Shell edges are strokes; stroke width is not wall thickness.
        </text>
      )}
    </>
  );
}

function Projection({ document: doc, aft = false, ...selection }: Props & { aft?: boolean }) {
  const aftIds = new Set(
    doc.joints
      .filter((joint) => ['receiver_end', 'motor', 'fin_root'].includes(joint.kind))
      .flatMap((joint) => joint.part_ids),
  );
  const parts = doc.parts.filter(
    (part) =>
      finite(part.radius_mm) &&
      (!aft || aftIds.has(part.id) || part.shape === 'motor' || part.shape === 'fin'),
  );
  const extent = Math.max(
    doc.arrangement.body_diameter_mm / 2,
    ...parts.map((part) => part.radius_mm! + (part.shape === 'fin' ? (part.span_mm ?? 0) : 0)),
  );
  const scale = 110 / Math.max(extent, 1);
  const cx = 220;
  const cy = 162;
  const radials = parts
    .filter((part) => part.shape !== 'fin')
    .sort((a, b) => b.radius_mm! - a.radius_mm!);
  const direction = aft ? -1 : 1;
  return (
    <>
      <path className="wb-geometry-reference" d={`M${cx - 145},${cy}h290M${cx},${cy - 135}v270`} />
      <circle
        className="wb-geometry-envelope"
        cx={cx}
        cy={cy}
        r={(doc.arrangement.body_diameter_mm / 2) * scale}
      />
      {radials.map((part) => {
        const radius = part.radius_mm! * scale;
        const inner = finite(part.inner_radius_mm) ? part.inner_radius_mm * scale : null;
        return (
          <g
            key={part.id}
            {...selectable(part, selection)}
            style={{ '--part-color': colorFor(doc, part.subsystem) } as CSSProperties}
          >
            <PartTitle part={part} />
            {inner != null ? (
              <path
                fillRule="evenodd"
                d={`M${cx + radius},${cy}a${radius},${radius} 0 1 0 ${-2 * radius},0a${radius},${radius} 0 1 0 ${2 * radius},0 M${cx + inner},${cy}a${inner},${inner} 0 1 0 ${-2 * inner},0a${inner},${inner} 0 1 0 ${2 * inner},0`}
              />
            ) : (
              <circle cx={cx} cy={cy} r={radius} />
            )}
          </g>
        );
      })}
      {parts
        .filter((part) => part.shape === 'fin')
        .map((part) => (
          <g
            key={part.id}
            {...selectable(part, selection)}
            style={{ '--part-color': colorFor(doc, part.subsystem) } as CSSProperties}
          >
            <PartTitle part={part} />
            {part.azimuth_deg?.map((angle) => (
              <g key={angle} transform={`rotate(${direction * angle} ${cx} ${cy})`}>
                <rect
                  x={cx + part.radius_mm! * scale}
                  y={cy - ((part.thickness_mm ?? 0) * scale) / 2}
                  width={(part.span_mm ?? 0) * scale}
                  height={(part.thickness_mm ?? 0) * scale}
                />
              </g>
            ))}
          </g>
        ))}
      <Dimension
        x1={cx - (doc.arrangement.body_diameter_mm / 2) * scale}
        x2={cx + (doc.arrangement.body_diameter_mm / 2) * scale}
        y={303}
        label={`Body Ø ${number(doc.arrangement.body_diameter_mm)} mm`}
      />
      <text x={cx} y={339} textAnchor="middle" className="wb-geometry-small">
        {aft
          ? 'Looking forward · aft assembly projected'
          : 'Looking aft · all axial stations projected'}
      </text>
      <text x={cx} y={358} textAnchor="middle" className="wb-geometry-small">
        Depth collapsed; overlaps do not establish contact.
      </text>
      {parts.some((part) => part.shape === 'fin' && !part.azimuth_deg?.length) && (
        <text x={cx} y={380} textAnchor="middle" className="wb-geometry-warning-text">
          Fin azimuth unavailable; radial fin placement omitted.
        </text>
      )}
    </>
  );
}

function JointLayers({
  joint,
  document: doc,
  ...selection
}: { joint: JointDetail; document: WorkbenchDocument } & Selection) {
  const layers = joint.layers;
  const known = layers.map((layer) => layer.thickness_mm).filter(finite);
  const maxThickness = Math.max(...known, 1);
  return (
    <svg
      viewBox={`0 0 900 ${Math.max(240, layers.length * 64 + 114)}`}
      role="img"
      aria-label={`${joint.label}: separated layer illustration, not a contact model`}
    >
      <text x={26} y={26} className="wb-geometry-svg-kicker">
        SEPARATED LAYERS · SCHEMATIC, NOT TO SCALE
      </text>
      <text x={26} y={49} className="wb-geometry-small">
        Layer order follows the source record; adjacency, engagement and clearance require geometry.
      </text>
      {layers.length === 0 && (
        <>
          <rect x={30} y={85} width={330} height={70} className="wb-geometry-undefined" />
          <text x={48} y={119} className="wb-geometry-warning-text">
            Layer geometry undefined
          </text>
        </>
      )}
      {layers.map((layer, index) => {
        const part = doc.parts.find((entry) => entry.id === layer.part_id);
        const top = 75 + index * 64;
        const width = finite(layer.thickness_mm)
          ? 30 + (layer.thickness_mm / maxThickness) * 190
          : 180;
        return (
          <g key={`${layer.part_id}-${index}`}>
            {part ? (
              <g
                {...selectable(part, selection)}
                style={{ '--part-color': colorFor(doc, part.subsystem) } as CSSProperties}
              >
                <PartTitle part={part} />
                <path
                  d={`M42,${top + 10}l22,-10h${width}v28l-22,10H42Z M42,${top + 10}h${width}l22,-10 M${42 + width},${top + 10}v28`}
                />
              </g>
            ) : (
              <rect x={42} y={top} width={width} height={38} className="wb-geometry-undefined" />
            )}
            <text x={330} y={top + 12} className="wb-geometry-layer-label">
              {layer.label}
            </text>
            <text x={330} y={top + 32} className="wb-geometry-small">
              {layer.material} ·{' '}
              {finite(layer.thickness_mm)
                ? `${number(layer.thickness_mm)} mm`
                : 'thickness undefined'}{' '}
              · {layer.state}
            </text>
            {index < layers.length - 1 && (
              <>
                <path className="wb-geometry-undefined" d={`M80,${top + 43}v16h200`} />
                <text x={330} y={top + 52} className="wb-geometry-gap-label">
                  Interface geometry / contact not established by this illustration
                </text>
              </>
            )}
          </g>
        );
      })}
      <text x={26} y={Math.max(220, layers.length * 64 + 94)} className="wb-geometry-small">
        Separation is illustrative only. No shim, adhesive, engagement or manufacturing allowance is
        inferred.
      </text>
    </svg>
  );
}

function AssemblyStoryboard({
  joint,
  document: doc,
  ...selection
}: { joint: JointDetail; document: WorkbenchDocument } & Selection) {
  const parts = joint.part_ids
    .map((id) => doc.parts.find((part) => part.id === id))
    .filter((part): part is WorkbenchPart => Boolean(part));
  const [stepIndex, setStepIndex] = useState(0);
  const step = Math.min(stepIndex, Math.max(0, joint.assembly_steps.length - 1));
  return (
    <section className="wb-geometry-storyboard">
      <div className="wb-geometry-figure-heading">
        <h4>Assembly / removal sequence</h4>
        <span>Illustration · clearance and service unverified</span>
      </div>
      {joint.assembly_steps.length ? (
        <>
          <ol className="wb-geometry-step-list">
            {joint.assembly_steps.map((text, index) => (
              <li key={`${index}-${text}`}>
                <button
                  type="button"
                  aria-current={step === index ? 'step' : undefined}
                  onClick={() => setStepIndex(index)}
                >
                  <span>{index + 1}</span>
                  {text}
                </button>
              </li>
            ))}
          </ol>
          <svg
            viewBox="0 0 900 150"
            role="img"
            aria-label={`Assembly step ${step + 1}; associated parts shown as schematic tiles, no simulated motion`}
          >
            <text x={24} y={24} className="wb-geometry-svg-kicker">
              STEP {step + 1} · ASSOCIATED PARTS, NO SIMULATED INSERTION
            </text>
            {parts.slice(0, 6).map((part, index) => {
              const px = 25 + index * 144;
              return (
                <g
                  key={part.id}
                  {...selectable(part, selection)}
                  style={{ '--part-color': colorFor(doc, part.subsystem) } as CSSProperties}
                >
                  <PartTitle part={part} />
                  <rect x={px} y={49} width={128} height={45} rx={4} />
                  <text x={px + 64} y={76} textAnchor="middle" className="wb-geometry-story-number">
                    {index + 1}
                  </text>
                  <text x={px + 64} y={116} textAnchor="middle" className="wb-geometry-small">
                    {part.label.length > 21 ? `${part.label.slice(0, 20)}…` : part.label}
                  </text>
                </g>
              );
            })}
            <text x={24} y={143} className="wb-geometry-small">
              Read the recorded instruction above. Tile order is a parts key, not a validated
              assembly order or travel.
            </text>
          </svg>
        </>
      ) : (
        <p>
          No assembly or removal steps are recorded. Access and service sequence remain undefined.
        </p>
      )}
    </section>
  );
}

function JointPanel({
  joint,
  document: doc,
  ...selection
}: { joint: JointDetail; document: WorkbenchDocument } & Selection) {
  const svgRef = useRef<SVGSVGElement>(null);
  const parts = doc.parts.filter((part) => joint.part_ids.includes(part.id));
  const placed = parts.filter(positioned);
  const start = Math.min(...placed.map((part) => part.start_mm!));
  const end = Math.max(...placed.map((part) => part.start_mm! + part.length_mm!));
  const region = placed.length && end > start ? { start, end, parts } : undefined;
  return (
    <div className="wb-geometry-joint">
      <Figure
        title={joint.label}
        note={`${joint.description} Recorded evidence: ${joint.state}.`}
        document={doc}
        svgRef={svgRef}
      >
        <svg
          ref={svgRef}
          viewBox="0 0 1100 390"
          role="img"
          aria-label={`${joint.label} preliminary longitudinal section`}
        >
          <title>{`${joint.label} · preliminary concept section · engineering acceptance open`}</title>
          {region ? (
            <AxialDrawing document={doc} {...selection} section region={region} />
          ) : (
            <>
              <rect x={60} y={90} width={980} height={140} className="wb-geometry-undefined" />
              <text x={550} y={154} textAnchor="middle" className="wb-geometry-warning-text">
                Axial / radial geometry undefined
              </text>
              <text x={550} y={185} textAnchor="middle" className="wb-geometry-small">
                Recorded dimensions below do not establish a complete joint solid.
              </text>
            </>
          )}
          <text x={64} y={385} className="wb-geometry-small">
            Concept / envelope section · mating surfaces, contact and hardware engagement unresolved
          </text>
        </svg>
      </Figure>
      <div className="wb-geometry-detail-grid">
        <div className="wb-geometry-layer-drawing">
          <JointLayers joint={joint} document={doc} {...selection} />
        </div>
        <div className="wb-geometry-dimensions">
          <h4>Recorded joint dimensions</h4>
          {joint.dimensions.length ? (
            <dl>
              {joint.dimensions.map((dimension, index) => (
                <div key={`${dimension.label}-${index}`}>
                  <dt>{dimension.label}</dt>
                  <dd>
                    {finite(dimension.value)
                      ? `${number(dimension.value)} ${dimension.unit}`
                      : 'Unavailable'}{' '}
                    <span>{dimension.state}</span>
                  </dd>
                </div>
              ))}
            </dl>
          ) : (
            <p>No dimensioned joint geometry recorded.</p>
          )}
        </div>
      </div>
      <div className="wb-geometry-part-links">
        {parts.map((part) => (
          <button
            type="button"
            key={part.id}
            aria-pressed={selection.selectedPartId === part.id}
            onClick={() => selection.onSelectPart(part.id)}
            style={{ '--part-color': colorFor(doc, part.subsystem) } as CSSProperties}
          >
            {part.label}
            <span>{maturityLabel(part.geometry_maturity)}</span>
          </button>
        ))}
      </div>
      {joint.findings.length > 0 && (
        <ul className="wb-geometry-findings">
          {joint.findings.map((finding) => (
            <li key={finding}>{finding}</li>
          ))}
        </ul>
      )}
      <AssemblyStoryboard key={joint.id} joint={joint} document={doc} {...selection} />
    </div>
  );
}

export function GeometryViews({ document: doc, selectedPartId, onSelectPart }: Props) {
  const sideRef = useRef<SVGSVGElement>(null);
  const frontRef = useRef<SVGSVGElement>(null);
  const aftRef = useRef<SVGSVGElement>(null);
  const sectionRef = useRef<SVGSVGElement>(null);
  const headingId = useId();
  const [jointId, setJointId] = useState<string | null>(null);
  const selectedJoint =
    doc.joints.find((joint) => joint.id === jointId) ??
    doc.joints.find((joint) => joint.part_ids.includes(selectedPartId ?? '')) ??
    doc.joints[0];
  const selection = { selectedPartId, onSelectPart };
  const subsystems = [...new Set(doc.parts.map((part) => part.subsystem))];
  const missing = doc.parts.filter((part) => !positioned(part));
  const selected = doc.parts.find((part) => part.id === selectedPartId);
  return (
    <section className="wb-geometry" aria-labelledby={headingId}>
      <div className="wb-geometry-intro">
        <div>
          <p className="wb-geometry-eyebrow">Geometry & construction</p>
          <h2 id={headingId}>See the arrangement. Inspect the unfinished joints.</h2>
        </div>
        <span className="wb-geometry-status">Preliminary design · engineering acceptance open</span>
      </div>
      <p className="wb-geometry-explanation">
        These drawings place the recorded parts and dimensions in their source reference frame.
        Concept outlines and component envelopes are not a reconciled CAD assembly. Click a part in
        any drawing to inspect it across the views.
      </p>
      <div className="wb-geometry-identity">
        <span>{doc.identity.configuration_id}</span>
        <span>
          CAD revision:{' '}
          {doc.identity.cad_revision ?? 'Unavailable — complete detailed CAD not supplied'}
        </span>
        <span>{doc.identity.frame}</span>
      </div>
      <div className="wb-geometry-legend" aria-label="Subsystem colors">
        {subsystems.map((subsystem) => (
          <span key={subsystem}>
            <i style={{ background: colorFor(doc, subsystem) }} />
            {subsystem.replaceAll('_', ' ')}
          </span>
        ))}
      </div>
      <div className="wb-geometry-maturity-key">
        <span>
          <i className="concept-line" />
          Concept
        </span>
        <span>
          <i className="envelope-line" />
          Envelope
        </span>
        <span>
          <i className="cad-line" />
          Detailed CAD when explicitly recorded
        </span>
        <span>
          <i className="undefined-line" />
          Undefined / unresolved
        </span>
        <span className="wb-geometry-selection-key">White outline: selected part</span>
      </div>
      <Figure
        title="General arrangement · side"
        note={`${doc.arrangement.reference} The nose outline is an envelope, not a manufactured profile. Fin centerplanes use recorded azimuths projected onto the axial plane containing the 0° radial direction; near/far fins may overlap. Panel thickness is not resolved in this projection.`}
        document={doc}
        svgRef={sideRef}
      >
        <svg
          ref={sideRef}
          viewBox="0 0 1100 390"
          role="img"
          aria-label="Preliminary side general arrangement with source axial stations"
        >
          <title>{`${doc.label} · preliminary side arrangement · engineering acceptance open`}</title>
          <AxialDrawing document={doc} {...selection} />
        </svg>
      </Figure>
      <div className="wb-geometry-projections">
        <Figure
          title="Front view · station projection"
          note="A view along the axis. Recorded radii and fin azimuths are projected together; this is not a nose surface rendering."
          document={doc}
          svgRef={frontRef}
        >
          <svg
            ref={frontRef}
            viewBox="0 0 440 395"
            role="img"
            aria-label="Preliminary front projection of recorded radial envelopes"
          >
            <title>Front projection · preliminary · engineering acceptance open</title>
            <Projection document={doc} {...selection} />
          </svg>
        </Figure>
        <Figure
          title="Motor-end view · aft projection"
          note="Aft-joint, fin and motor envelopes viewed looking forward. Axial depth is collapsed; unrecorded openings are not drawn."
          document={doc}
          svgRef={aftRef}
        >
          <svg
            ref={aftRef}
            viewBox="0 0 440 395"
            role="img"
            aria-label="Preliminary motor-end projection; no contact or service clearance verified"
          >
            <title>Motor-end projection · preliminary · engineering acceptance open</title>
            <Projection document={doc} aft {...selection} />
          </svg>
        </Figure>
      </div>
      <Figure
        title="Full longitudinal internal section"
        note="The section exposes recorded shells, rings and internal envelopes, with fin centerplanes projected from their recorded azimuths onto the axial / 0° radial plane. Solid rectangles with no inner radius are component envelopes; they do not imply solid material or resolved internals."
        document={doc}
        svgRef={sectionRef}
      >
        <svg
          ref={sectionRef}
          viewBox="0 0 1100 390"
          role="img"
          aria-label="Preliminary full longitudinal section of recorded parts"
        >
          <title>Longitudinal concept section · preliminary · engineering acceptance open</title>
          <AxialDrawing document={doc} section {...selection} />
        </svg>
      </Figure>
      <div className="wb-geometry-ranges">
        {doc.arrangement.subsystem_ranges.map((range) => (
          <span key={range.id}>
            <strong>{range.label}</strong>
            {number(range.start_mm)}–{number(range.end_mm)} mm
          </span>
        ))}
      </div>
      <div className="wb-geometry-current" aria-live="polite">
        {selected ? (
          <>
            <strong>{selected.label}</strong>
            <span>
              {maturityLabel(selected.geometry_maturity)} · {selected.state}
            </span>
            <p>{selected.function}</p>
          </>
        ) : (
          <p>Select a colored part. Keyboard: Tab to a drawing part, then Enter or Space.</p>
        )}
      </div>
      <details className="wb-geometry-parts-key">
        <summary>Drawing parts key · {doc.parts.length} recorded components</summary>
        <div className="wb-geometry-part-links">
          {doc.parts.map((part) => (
            <button
              type="button"
              key={part.id}
              aria-pressed={selectedPartId === part.id}
              onClick={() => onSelectPart(part.id)}
              style={{ '--part-color': colorFor(doc, part.subsystem) } as CSSProperties}
            >
              {part.label}
              <span>{maturityLabel(part.geometry_maturity)}</span>
            </button>
          ))}
        </div>
      </details>
      {missing.length > 0 && (
        <details className="wb-geometry-missing">
          <summary>{missing.length} parts have incomplete placement or envelope dimensions</summary>
          <p>
            These parts remain selectable; no dimensions or locations are invented to draw them.
          </p>
          <ul>
            {missing.map((part) => (
              <li key={part.id}>
                <button type="button" onClick={() => onSelectPart(part.id)}>
                  {part.label}
                </button>
                <span>
                  {[
                    !finite(part.start_mm) && 'station',
                    !finite(part.length_mm) && 'length',
                    !finite(part.radius_mm) && 'radius',
                  ]
                    .filter(Boolean)
                    .join(', ')}{' '}
                  unavailable
                </span>
              </li>
            ))}
          </ul>
        </details>
      )}
      <div className="wb-geometry-joint-heading">
        <h3>Focused construction sections</h3>
        <p>
          Read the actual dimensions beside the illustration. Undefined engagement, fit, contact,
          packing and tool access stay open.
        </p>
      </div>
      <div className="wb-geometry-joint-tabs" role="group" aria-label="Choose construction detail">
        {doc.joints.map((joint) => (
          <button
            type="button"
            key={joint.id}
            aria-pressed={selectedJoint?.id === joint.id}
            onClick={() => setJointId(joint.id)}
          >
            {joint.label}
            <span>{joint.state}</span>
          </button>
        ))}
      </div>
      {selectedJoint ? (
        <JointPanel joint={selectedJoint} document={doc} {...selection} />
      ) : (
        <p>No detailed joint records are available for this document.</p>
      )}
    </section>
  );
}
