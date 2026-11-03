import { useRef } from 'react';
import type { RefObject } from 'react';
import type { A1Feature, A1Snapshot, A1Value } from './a1Types';
import { a1ValueText } from './a1Types';
import './a1ConnectionViews.css';

type Props = { snapshot: A1Snapshot; prepared?: boolean };

function Scalar({ label, value }: { label: string; value: A1Value }) {
  return (
    <div className="a1-scalar">
      <dt>{label}</dt>
      <dd>
        {a1ValueText(value)} <span className={`a1-state a1-${value.state}`}>{value.state}</span>
      </dd>
      <small>{value.note}</small>
    </div>
  );
}

function arrow(x: number, y: number, color: string) {
  return <path d={`M${x} ${y}h18m-7-6 7 6-7 6`} fill="none" stroke={color} strokeWidth="2" />;
}
const numberText = (value: number | null, unit: string) =>
  value === null || !Number.isFinite(value)
    ? 'Unavailable'
    : `${new Intl.NumberFormat('en', { maximumFractionDigits: 4 }).format(value)} ${unit}`;
function featureDimensions(feature: A1Feature) {
  const z =
    feature.start_mm === null || feature.end_mm === null
      ? 'z unavailable'
      : `z ${feature.start_mm}–${feature.end_mm} mm`;
  const r =
    feature.inner_radius_mm === null || feature.outer_radius_mm === null
      ? 'r unavailable'
      : `R ${feature.inner_radius_mm}–${feature.outer_radius_mm} mm`;
  return `${z} · ${r}`;
}
function wrapSvg(value: string, limit: number): string[] {
  const lines: string[] = [];
  for (const word of value.split(/\s+/)) {
    if (!lines.length || lines[lines.length - 1].length + word.length + 1 > limit) lines.push(word);
    else lines[lines.length - 1] += ` ${word}`;
  }
  return lines;
}

/** Display-only, deliberately schematic. Spacing and drawn radii are not measurements. */
export function A1ConnectionDrawing({
  snapshot,
  svgRef,
}: {
  snapshot: A1Snapshot;
  svgRef?: RefObject<SVGSVGElement | null>;
}) {
  const paths = snapshot.paths;
  const index = snapshot.geometry.features.find((feature) => feature.role === 'index');
  const retention = snapshot.geometry.features.find((feature) => feature.role === 'retention');
  const motor = snapshot.geometry.features.find((feature) => /motor/.test(feature.role));
  const harness = snapshot.geometry.features.find((feature) => /harness/.test(feature.role));
  const sleeve = snapshot.geometry.features.find((feature) => feature.role === 'sleeve');
  const stop = snapshot.geometry.features.find((feature) => feature.role === 'stop');
  const collar = snapshot.geometry.features.find((feature) => feature.role === 'collar');
  const span =
    sleeve?.start_mm !== null &&
    sleeve?.end_mm !== null &&
    sleeve?.start_mm !== undefined &&
    sleeve?.end_mm !== undefined &&
    sleeve.end_mm > sleeve.start_mm;
  const stationX = (station: number | null | undefined, fallback: number) =>
    span && station !== null && station !== undefined
      ? 78 + ((station - sleeve.start_mm!) / (sleeve.end_mm! - sleeve.start_mm!)) * 442
      : fallback;
  const stopX = stationX(stop?.start_mm, 355);
  const collarX = stationX(collar?.start_mm, 430);
  const collarEndX = stationX(collar?.end_mm, 550);
  return (
    <svg
      ref={svgRef}
      className="a1-drawing"
      viewBox="0 0 1080 1180"
      width="1080"
      height="1180"
      fontFamily="Helvetica,Arial,sans-serif"
      role="img"
      aria-labelledby="a1-title a1-desc"
      xmlns="http://www.w3.org/2000/svg"
    >
      <title id="a1-title">A1 upper sleeve, stop, index and retention connection concept</title>
      <desc id="a1-desc">
        Schematic axial and end sections plus recorded fin, recovery and motor force-path sequences.
        Positions and sizes are not to scale; no capacity or installed fit is inferred.
      </desc>
      <rect x="0" y="0" width="1080" height="1180" rx="12" fill="#12202a" />
      <text x="28" y="40" fill="#eff8fb" fontSize="23" fontWeight="700">
        A1 · upper connection concept
      </text>
      <text x="28" y="65" fill="#f0bf83" fontSize="13">
        SEPARATE VERSION · CONCEPT / NOT ADMITTED · schematic, not to scale
      </text>
      <text x="28" y="99" fill="#b6d3df" fontSize="14">
        Axial relationship
      </text>
      <rect
        x="40"
        y="128"
        width="650"
        height="150"
        rx="12"
        fill="#213c4b"
        stroke="#83b9d2"
        strokeWidth="2"
      />
      <rect
        x="78"
        y="151"
        width={Math.max(20, stopX - 78)}
        height="104"
        fill="#365c69"
        stroke="#a6d2df"
        strokeWidth="2"
      />
      <text x="99" y="181" fill="#f5fbff" fontSize="15">
        Retained upper body
      </text>
      <text x="99" y="201" fill="#cfe4ed" fontSize="12">
        bonded to proposed A1 sleeve
      </text>
      <rect
        x={stopX + 7}
        y="151"
        width={Math.max(20, 690 - stopX - 7)}
        height="104"
        fill="#274451"
        stroke="#8fb4c3"
        strokeWidth="2"
      />
      <rect x="78" y="166" width="442" height="74" fill="none" stroke="#e2bc82" strokeWidth="5" />
      <text x="400" y="193" fill="#f8e0b4" fontSize="16">
        A1 sleeve · {a1ValueText(snapshot.geometry.sleeve_length)}
      </text>
      <text x="400" y="213" fill="#e9c993" fontSize="12">
        OD {a1ValueText(snapshot.geometry.sleeve_outer_diameter)} · ID{' '}
        {a1ValueText(snapshot.geometry.sleeve_inner_diameter)}
      </text>
      <rect
        x={collarX}
        y="130"
        width={Math.max(8, collarEndX - collarX)}
        height="9"
        fill="#ad8fc5"
        stroke="#ddc5ed"
      />
      <path d={`M${stopX} 138v128`} stroke="#eac480" strokeWidth="7" />
      <text x="78" y="305" fill="#f2d39d" fontSize="13">
        Stop at {a1ValueText(snapshot.geometry.upper_stop_station)} · capacity unproven
      </text>
      <path d={`M${stopX + 16} 137v-18h38v18`} fill="#9ac7ca" stroke="#e4f2f2" strokeWidth="2" />
      <text x="390" y="118" fill="#d3e8e8" fontSize="13">
        {a1ValueText(snapshot.geometry.index_feature_count)} index features · fit unverified
      </text>
      <path
        d={`M${stationX(retention?.start_mm, 488)} 137v-20m-9 10h18`}
        stroke="#eea9a5"
        strokeWidth="4"
      />
      <text x="528" y="229" fill="#f2c3bb" fontSize="13">
        Retention provision
      </text>
      <text x="528" y="247" fill="#e8b4ad" fontSize="12">
        {a1ValueText(snapshot.geometry.retention_feature_count)} stations · bearing unproven
      </text>
      <rect x="712" y="104" width="340" height="239" rx="7" fill="#183340" stroke="#63899b" />
      <text x="728" y="128" fill="#e8f4f7" fontSize="14">
        Source-defined feature stations / radii
      </text>
      {snapshot.geometry.features.slice(0, 7).map((feature, i) => (
        <g key={feature.id}>
          <text x="728" y={152 + i * 25} fill="#f0d5a5" fontSize="11" fontWeight="700">
            {feature.label.length > 31 ? `${feature.label.slice(0, 29)}…` : feature.label}
          </text>
          <text x="728" y={164 + i * 25} fill="#c9e0e9" fontSize="10">
            {featureDimensions(feature)}
          </text>
        </g>
      ))}
      <text x="28" y="360" fill="#b6d3df" fontSize="14">
        End relationship and protected service routes
      </text>
      <circle cx="180" cy="475" r="106" fill="#213c4b" stroke="#8fb9ca" strokeWidth="3" />
      <circle cx="180" cy="475" r="80" fill="#142a34" stroke="#e2bc82" strokeWidth="7" />
      <circle
        cx="180"
        cy="475"
        r="42"
        fill="#1c4051"
        stroke="#6bb3d1"
        strokeWidth="2"
        strokeDasharray="7 5"
      />
      {index?.axes_deg.map((angle, i) => (
        <rect
          key={`index-${i}`}
          x="174"
          y="381"
          width="12"
          height="22"
          fill="#a8d6d2"
          stroke="#e1f3f2"
          strokeWidth="1"
          transform={`rotate(${angle} 180 475)`}
        />
      ))}
      {retention?.axes_deg.map((angle, i) => (
        <circle
          key={`retention-${i}`}
          cx="180"
          cy="373"
          r="5"
          fill="#f0aba3"
          stroke="#ffe1d8"
          transform={`rotate(${angle} 180 475)`}
        />
      ))}
      <path d="M89 475h30m122 0h30" stroke="#e9b77b" strokeWidth="7" />
      <text x="310" y="416" fill="#f2d39d" fontSize="14">
        Sleeve, stop and collar: proposed
      </text>
      <text x="310" y="444" fill="#d1e6ec" fontSize="14">
        Index axes: {index?.axes_deg.length ? index.axes_deg.join(' / ') + '°' : 'unavailable'}
      </text>
      <text x="310" y="472" fill="#87c6df" fontSize="14">
        Motor corridor: {motor ? featureDimensions(motor) : 'bounds unavailable'}
      </text>
      <text x="310" y="500" fill="#c5dce6" fontSize="14">
        Harness centre:{' '}
        {harness?.outer_radius_mm === null || harness?.outer_radius_mm === undefined
          ? 'radius unavailable'
          : `R ${harness.outer_radius_mm} mm`}{' '}
        · z {harness?.start_mm ?? 'unknown'}–{harness?.end_mm ?? 'unknown'} mm
      </text>
      <text x="310" y="531" fill="#e9b77b" fontSize="12">
        Symbolic separation; angular and radial clearance unverified
      </text>
      <rect x="740" y="384" width="300" height="156" rx="7" fill="#183340" stroke="#63899b" />
      <text x="759" y="411" fill="#e8f4f7" fontSize="15">
        Fit and access hold points
      </text>
      <text x="759" y="439" fill="#f0aaa5" fontSize="13">
        Historical A/B cold radial gap: 0 mm
      </text>
      <text x="759" y="459" fill="#f0aaa5" fontSize="13">
        Required minimum: 0.1 mm
      </text>
      <text x="759" y="485" fill="#d2e7ee" fontSize="13">
        A1 fit: see recorded table below
      </text>
      <text x="759" y="506" fill="#d2e7ee" fontSize="13">
        Removal / harness sweeps: unverified
      </text>
      <text x="28" y="587" fill="#b6d3df" fontSize="14">
        Recorded force paths · arrows show intended transfer, not shared load or capacity
      </text>
      {paths.map((path, row) => {
        const y = 620 + row * 90;
        const sequence = path.sequence.slice(0, 4);
        return (
          <g key={path.id}>
            {wrapSvg(path.label, 26).map((line, lineIndex) => (
              <text
                key={`${path.id}-label-${lineIndex}`}
                x="28"
                y={y + 17 + lineIndex * 16}
                fill="#e7f3f7"
                fontSize="13"
                fontWeight="700"
              >
                {line}
              </text>
            ))}
            {sequence.map((label, i) => {
              const x = 240 + i * 200;
              return (
                <g key={`${path.id}-${i}`}>
                  <rect
                    x={x}
                    y={y - 5}
                    width="160"
                    height="72"
                    rx="5"
                    fill="#254251"
                    stroke="#7899a9"
                  />
                  {wrapSvg(label, 21).map((line, lineIndex) => (
                    <text
                      key={`${path.id}-${i}-line-${lineIndex}`}
                      x={x + 8}
                      y={y + 12 + lineIndex * 15}
                      fill="#e3f1f5"
                      fontSize="11"
                    >
                      {line}
                    </text>
                  ))}
                  {i < sequence.length - 1 && arrow(x + 165, y + 31, '#e8bd80')}
                </g>
              );
            })}
            {path.sequence.length > 4 && (
              <text x="1026" y={y + 18} fill="#e8bd80" fontSize="15">
                …
              </text>
            )}
          </g>
        );
      })}
      <text x="28" y="1152" fill="#96b7c4" fontSize="12">
        {snapshot.identity.candidate_id} · {snapshot.identity.source_identity} ·{' '}
        {snapshot.identity.units} · CAD unavailable · acceptance open
      </text>
    </svg>
  );
}

/** Dimension labels are supplied by the A1 record. Blocks show ordered interfaces, not thickness scale. */
export function A1JointDetailDrawing({
  snapshot,
  svgRef,
}: {
  snapshot: A1Snapshot;
  svgRef?: RefObject<SVGSVGElement | null>;
}) {
  const detail = snapshot.joint_detail;
  if (!detail) return null;
  const swatches = [
    '#7db3cb',
    '#a895ca',
    '#cfac7b',
    '#87a6b7',
    '#adbf8e',
    '#d4ad7a',
    '#8fb5c9',
    '#d0ad82',
    '#a995c7',
  ];
  return (
    <svg
      ref={svgRef}
      className="a1-drawing"
      viewBox="0 0 1080 880"
      width="1080"
      height="880"
      fontFamily="Helvetica,Arial,sans-serif"
      role="img"
      aria-labelledby="a1-joint-title a1-joint-desc"
      xmlns="http://www.w3.org/2000/svg"
    >
      <title id="a1-joint-title">A1 radial M5 joint, upper bond lap and fin-root detail</title>
      <desc id="a1-joint-desc">
        Source dimension labels for the ordered bolt stack, upper body bond and fin-root interfaces.
        The drawing is schematic, not to scale; hot installed joint capacities and actual CAD remain
        unqualified.
      </desc>
      <rect width="1080" height="880" rx="12" fill="#12202a" />
      <text x="28" y="42" fill="#eff8fb" fontSize="23" fontWeight="700">
        A1 · finite joint detail
      </text>
      <text x="28" y="67" fill="#f0bf83" fontSize="13">
        SOURCE-DIMENSIONED CONCEPT · SCHEMATIC, NOT TO SCALE · NOT ADMITTED
      </text>
      <text x="28" y="104" fill="#b6d3df" fontSize="15">
        M5 radial retention stack · outside → inside
      </text>
      {detail.radial_stack.map((layer, i) => {
        const x = 32 + i * 113;
        const label = layer.label.length > 17 ? `${layer.label.slice(0, 15)}…` : layer.label;
        return (
          <g key={`${layer.label}-${i}`}>
            <rect
              x={x}
              y="128"
              width="107"
              height="111"
              fill={swatches[i % swatches.length]}
              stroke="#dcecf1"
              strokeWidth="1"
            />
            <text x={x + 6} y="154" fill="#142532" fontSize="11" fontWeight="700">
              {label}
            </text>
            <text x={x + 6} y="179" fill="#142532" fontSize="16" fontWeight="700">
              {numberText(layer.thickness_mm, 'mm')}
            </text>
            <text x={x + 6} y="213" fill="#253743" fontSize="10">
              layer {i + 1}
            </text>
          </g>
        );
      })}
      <path d="M32 258h1000m-12-7 12 7-12 7" fill="none" stroke="#91c7db" strokeWidth="2" />
      <text x="32" y="289" fill="#d6e9ef" fontSize="13">
        Recorded stack to nut end {numberText(detail.total_to_nut_end_mm, 'mm')} · maximum{' '}
        {numberText(detail.maximum_to_nut_end_mm, 'mm')}
      </text>
      <text x="32" y="313" fill="#d6e9ef" fontSize="13">
        Specified bolt {numberText(detail.bolt_length_mm, 'mm')} · minimum protrusion{' '}
        {numberText(detail.minimum_protrusion_mm, 'mm')} · hole Ø{' '}
        {numberText(detail.hole_diameter_mm, 'mm')}
      </text>
      <text x="32" y="344" fill="#f2aaa6" fontSize="13">
        Combined single-lap bolt screen failed; installed bearing, capture and preload remain open.
      </text>
      <rect x="27" y="370" width="496" height="356" rx="8" fill="#183340" stroke="#63899b" />
      <text x="46" y="402" fill="#e8f4f7" fontSize="16" fontWeight="700">
        Upper body lap / sleeve
      </text>
      <text x="46" y="427" fill="#e0bb82" fontSize="12">
        Axial bond length {numberText(detail.upper_bond.length_mm, 'mm')}
      </text>
      <rect x="60" y="462" width="430" height="47" fill="#537383" stroke="#aed2df" />
      <rect x="60" y="515" width="430" height="58" fill="#d2a971" stroke="#eed9ba" />
      <rect x="60" y="579" width="430" height="48" fill="#a688c1" stroke="#d6c2e5" />
      <text x="74" y="491" fill="#f2fbfd" fontSize="14">
        Retained paper wall · {numberText(detail.upper_bond.paper_wall_mm, 'mm')}
      </text>
      <text x="74" y="549" fill="#1d2d39" fontSize="14" fontWeight="700">
        Radial bond gap · {numberText(detail.upper_bond.radial_gap_mm, 'mm')}
      </text>
      <text x="74" y="608" fill="#f5eef9" fontSize="14">
        New G11 sleeve
      </text>
      <text x="46" y="667" fill="#f1b2ad" fontSize="12">
        Paper-wall / bond peel capacity unavailable
      </text>
      <text x="46" y="689" fill="#bcd3dd" fontSize="12">
        Mean bond shear does not establish installed peel.
      </text>
      <rect x="541" y="370" width="512" height="356" rx="8" fill="#183340" stroke="#63899b" />
      <text x="560" y="402" fill="#e8f4f7" fontSize="16" fontWeight="700">
        Proposed fin-root connection
      </text>
      <rect
        x="575"
        y="437"
        width="235"
        height="116"
        fill="#816f59"
        stroke="#d2b99c"
        strokeWidth="2"
      />
      <path d="M810 437l36-25v141l-36-25" fill="#d4ad79" stroke="#f0d7b6" strokeWidth="2" />
      <rect
        x="846"
        y="425"
        width="157"
        height="128"
        fill="#405f6c"
        stroke="#9ec2d0"
        strokeWidth="2"
      />
      <text x="589" y="471" fill="#f6eadc" fontSize="13">
        Dense root edge
      </text>
      <text x="589" y="493" fill="#f6eadc" fontSize="13">
        {numberText(detail.root.edge_patch_mm[0], 'mm')} ×{' '}
        {numberText(detail.root.edge_patch_mm[1], 'mm')}
      </text>
      <text x="856" y="461" fill="#e5f1f5" fontSize="13">
        Outer can /
      </text>
      <text x="856" y="482" fill="#e5f1f5" fontSize="13">
        root transfer
      </text>
      <text x="560" y="586" fill="#dcecf1" fontSize="12">
        Fillet leg {numberText(detail.root.fillet_leg_mm, 'mm')} · toe z{' '}
        {detail.root.toe_z_mm.join('–')} mm · heel z {detail.root.heel_z_mm.join('–')} mm
      </text>
      <text x="560" y="610" fill="#dcecf1" fontSize="12">
        Axial stops {detail.root.stop_radial_tangential_mm.join(' × ')} mm; radial capture unproven
      </text>
      <text x="560" y="640" fill="#f2aaa6" fontSize="13">
        Normal outer {numberText(detail.root.normal_outer_n, 'N')} / inner{' '}
        {numberText(detail.root.normal_inner_n, 'N')}
      </text>
      <text x="560" y="662" fill="#f2aaa6" fontSize="13">
        Mean normal demand {numberText(detail.root.normal_peel_mpa, 'MPa')} · local peel unavailable
      </text>
      <text x="560" y="691" fill="#bcd3dd" fontSize="12">
        A mean-shear pass cannot clear root normal/peel demand.
      </text>
      <rect x="27" y="747" width="1026" height="87" rx="7" fill="#352a2a" stroke="#ad7470" />
      <text x="44" y="777" fill="#f0b4ad" fontSize="14">
        Joint stop: {detail.note.length > 145 ? `${detail.note.slice(0, 143)}…` : detail.note}
      </text>
      <text x="44" y="814" fill="#cfdae2" fontSize="12">
        {snapshot.identity.candidate_id} · {snapshot.identity.source_identity} · source IDs{' '}
        {detail.source_ids.join(', ')} · CAD/physical acceptance open
      </text>
      <text x="28" y="860" fill="#9ebbc8" fontSize="12">
        Diagram spacing is illustrative; all dimensions, demands and absences come from the separate
        A1 record.
      </text>
    </svg>
  );
}

export function A1ConnectionViews({ snapshot, prepared = false }: Props) {
  const svg = useRef<SVGSVGElement>(null);
  const detailSvg = useRef<SVGSVGElement>(null);
  const download = (target: SVGSVGElement | null, slug: string) => {
    if (!target) return;
    const clone = target.cloneNode(true) as SVGSVGElement;
    const metadata = document.createElementNS('http://www.w3.org/2000/svg', 'metadata');
    metadata.textContent = JSON.stringify({
      schema_version: snapshot.schema_version,
      document_id: snapshot.id,
      identity: snapshot.identity,
      status: snapshot.status,
      generated_from: snapshot.generated_from,
      representation:
        'Separate A1 concept, schematic and not to scale; no CAD or capacity qualification',
    });
    clone.prepend(metadata);
    const blob = new Blob([new XMLSerializer().serializeToString(clone)], {
      type: 'image/svg+xml;charset=utf-8',
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${snapshot.id}-${slug}.svg`;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  return (
    <div className="a1-view">
      <header className="a1-header">
        <div>
          <span className="a1-kicker">
            Independent engineering snapshot · {snapshot.identity.candidate_id}
          </span>
          <h2>{snapshot.label}</h2>
          <p>{snapshot.status}</p>
        </div>
        <button type="button" onClick={() => download(svg.current, 'upper-connection')}>
          Export A1 overview SVG
        </button>
      </header>
      {prepared && (
        <p className="a1-banner">
          Prepared offline A1 source export. The current API returned 404; source identity is shown
          below.
        </p>
      )}
      <p className="a1-banner">
        This is an A1 connection concept. It does not replace frozen C1 or A/B, establish detailed
        CAD, joint capacity, motion/fit, guide departure or flight acceptance.
      </p>
      <div className="a1-figure">
        <A1ConnectionDrawing snapshot={snapshot} svgRef={svg} />
      </div>
      {snapshot.joint_detail && (
        <>
          <div className="a1-detail-heading">
            <h3>Radial retention, upper lap and fin-root detail</h3>
            <button type="button" onClick={() => download(detailSvg.current, 'joint-detail')}>
              Export joint-detail SVG
            </button>
          </div>
          <div className="a1-figure">
            <A1JointDetailDrawing snapshot={snapshot} svgRef={detailSvg} />
          </div>
          <section>
            <h3>Ordered M5 radial stack</h3>
            <p>
              Source-defined layer thicknesses are listed outside to inside. The drawing uses equal
              visual widths; they are not a tolerance stack calculation in the browser.
            </p>
            <p>{snapshot.joint_detail.note}</p>
            <div className="a1-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Layer</th>
                    <th>Thickness</th>
                    <th>Sources</th>
                  </tr>
                </thead>
                <tbody>
                  {snapshot.joint_detail.radial_stack.map((layer, i) => (
                    <tr key={`${layer.label}-${i}`}>
                      <th scope="row">
                        {i + 1}. {layer.label}
                      </th>
                      <td>{numberText(layer.thickness_mm, 'mm')}</td>
                      <td>{layer.source_ids.join(', ') || 'unavailable'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
      <section>
        <h3>Recorded connection dimensions</h3>
        <p>{snapshot.geometry.note}</p>
        <dl className="a1-scalars">
          <Scalar label="Sleeve length" value={snapshot.geometry.sleeve_length} />
          <Scalar label="Sleeve outside diameter" value={snapshot.geometry.sleeve_outer_diameter} />
          <Scalar label="Sleeve inside diameter" value={snapshot.geometry.sleeve_inner_diameter} />
          <Scalar label="Upper stop station" value={snapshot.geometry.upper_stop_station} />
          <Scalar label="Axial overlap" value={snapshot.geometry.axial_overlap} />
          <Scalar label="Index features" value={snapshot.geometry.index_feature_count} />
          <Scalar label="Retention features" value={snapshot.geometry.retention_feature_count} />
        </dl>
        <div className="a1-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Source feature</th>
                <th>Station / radial bounds</th>
                <th>Angular / width detail</th>
                <th>Limit</th>
                <th>Sources</th>
              </tr>
            </thead>
            <tbody>
              {snapshot.geometry.features.map((feature) => (
                <tr key={feature.id}>
                  <th scope="row">{feature.label}</th>
                  <td>{featureDimensions(feature)}</td>
                  <td>
                    {feature.axes_deg.length
                      ? `axes ${feature.axes_deg.join(' / ')}°`
                      : 'axes unavailable'}
                    ;{' '}
                    {feature.widths_mm.length
                      ? `widths ${feature.widths_mm.join(' / ')} mm`
                      : 'widths unavailable'}
                  </td>
                  <td>{feature.note}</td>
                  <td>{feature.source_ids.join(', ') || 'unavailable'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section>
        <h3>Fit and access ledger</h3>
        <div className="a1-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Interface</th>
                <th>Recorded result</th>
                <th>Criterion</th>
                <th>Interpretation</th>
                <th>Sources</th>
              </tr>
            </thead>
            <tbody>
              {snapshot.fit_rows.map((row) => (
                <tr key={row.id}>
                  <th scope="row">{row.label}</th>
                  <td>
                    {a1ValueText(row.result)}{' '}
                    <span className={`a1-state a1-${row.result.state}`}>{row.result.state}</span>
                  </td>
                  <td>{row.criterion}</td>
                  <td>{row.result.note}</td>
                  <td>{row.source_ids.join(', ')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section>
        <h3>Fin, recovery, motor and upper transfer</h3>
        <div className="a1-card-grid">
          {snapshot.paths.map((path) => (
            <article key={path.id}>
              <h4>
                {path.label} <span className={`a1-state a1-${path.state}`}>{path.state}</span>
              </h4>
              <ol>
                {path.sequence.map((node, i) => (
                  <li key={i}>{node}</li>
                ))}
              </ol>
              <p>{path.note}</p>
              <small>Sources: {path.source_ids.join(', ') || 'unavailable'}</small>
            </article>
          ))}
        </div>
      </section>
      <section>
        <h3>Protected service volumes</h3>
        <div className="a1-card-grid">
          {snapshot.protected_volumes.map((item) => (
            <article key={item.id}>
              <h4>
                {item.label} <span className={`a1-state a1-${item.state}`}>{item.state}</span>
              </h4>
              <p>{item.note}</p>
              <small>Sources: {item.source_ids.join(', ') || 'unavailable'}</small>
            </article>
          ))}
        </div>
      </section>
      <section>
        <h3>Complete mass change</h3>
        <p>
          <strong>Net delta: {a1ValueText(snapshot.mass.net_delta)}</strong> ·{' '}
          {snapshot.mass.net_delta.state}
        </p>
        <p>{snapshot.mass.note}</p>
        <div className="a1-card-grid">
          {snapshot.mass.ledger_rows.map((item) => (
            <article key={item.id}>
              <h4>{item.label}</h4>
              <p>{item.note}</p>
              <small>Sources: {item.source_ids.join(', ') || 'unavailable'}</small>
            </article>
          ))}
        </div>
      </section>
      <section>
        <h3>Recorded complete-case screen</h3>
        <p>
          Reference CP and margins reuse the earlier aerodynamic assumption. The external collar
          changes the shape, so a validated A1 CP and drag result is unavailable. The unchanged 1.5
          m usable guide remains the baseline; longer travel is conditional.
        </p>
        <div className="a1-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Case</th>
                <th>Mass / CG</th>
                <th>Reference CP / margin</th>
                <th>Guide speed by usable travel</th>
                <th>1.5 m mass headroom</th>
                <th>Recovery demand</th>
                <th>Status / sources</th>
              </tr>
            </thead>
            <tbody>
              {snapshot.cases.map((item) => (
                <tr key={item.id}>
                  <th scope="row">{item.label}</th>
                  <td>
                    {numberText(item.total_mass_g, 'g')}
                    <br />
                    loaded {numberText(item.loaded_cg_mm, 'mm')}
                    <br />
                    burnout {numberText(item.burnout_cg_mm, 'mm')}
                  </td>
                  <td>
                    CP hypothesis {numberText(item.reference_cp_mm, 'mm')}
                    <br />
                    loaded {numberText(item.loaded_margin_cal, 'cal')}
                    <br />
                    burnout {numberText(item.burnout_margin_cal, 'cal')}
                  </td>
                  <td>
                    {item.guide_results.map((guide, i) => (
                      <div key={i}>
                        {guide.usable_m} m: {numberText(guide.speed_mps, 'm/s')}
                      </div>
                    ))}
                  </td>
                  <td>
                    formal {numberText(item.baseline_formal_headroom_g ?? null, 'g')}
                    <br />
                    planning {numberText(item.baseline_planning_headroom_g ?? null, 'g')}
                    <br />
                    <small>Negative headroom is a deficit; 15.5 planning stays separate.</small>
                  </td>
                  <td>{numberText(item.recovery_force_n, 'N')}</td>
                  <td>
                    <span className={`a1-state a1-${item.state}`}>{item.state}</span>
                    <p>{item.note}</p>
                    <small>{item.source_ids.join(', ') || 'unavailable'}</small>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <section>
        <h3>Open findings</h3>
        <div className="a1-card-grid">
          {snapshot.findings.map((item) => (
            <article key={item.id}>
              <h4>
                {item.label} <span className={`a1-state a1-${item.state}`}>{item.state}</span>
              </h4>
              <p>{item.note}</p>
              <small>Sources: {item.source_ids.join(', ') || 'unavailable'}</small>
            </article>
          ))}
        </div>
      </section>
      <details className="a1-sources">
        <summary>Source identities ({snapshot.generated_from.length})</summary>
        {snapshot.generated_from.map((source) => (
          <div key={source.id}>
            <strong>{source.id}</strong>
            <p>{source.description}</p>
            <code>{source.path}</code>
            <br />
            <code>SHA-256 {source.sha256}</code>
          </div>
        ))}
      </details>
    </div>
  );
}
