import { useRef, useState } from 'react';
import layout from '../data/highGBoardLayout.json';

export interface HighGBoardDetailProps {
  partId: string;
  configurationId: string;
  specificationSha256: string | null;
}

export function matchesHighGBoardSource(props: HighGBoardDetailProps): boolean {
  return (
    props.partId === layout.part_id &&
    props.configurationId === layout.configuration_id &&
    props.specificationSha256 === layout.specification_sha256
  );
}

type Shape = {
  kind: string;
  ref: string;
  role: string;
  points_mm?: number[][];
  center_mm?: number[];
  radius_mm?: number;
  width_mm?: number;
};

const points = (values: number[][]) => values.map(([x, y]) => `${x},${-y}`).join(' ');

export default function HighGBoardDetail(props: HighGBoardDetailProps) {
  const dialog = useRef<HTMLDialogElement>(null);
  const svg = useRef<SVGSVGElement>(null);
  const [selected, setSelected] = useState('U1');
  if (!matchesHighGBoardSource(props)) return null;
  const placement = layout.placements.find((item) => item.ref === selected)!;
  const exportSvg = () => {
    if (!svg.current) return;
    const standalone = svg.current.cloneNode(true) as SVGSVGElement;
    standalone.removeAttribute('style');
    standalone.setAttribute('width', '900');
    standalone.setAttribute('height', '810');
    const url = URL.createObjectURL(new Blob([standalone.outerHTML], { type: 'image/svg+xml' }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${layout.id}.svg`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };
  const drawing = (
    <svg
      ref={svg}
      xmlns="http://www.w3.org/2000/svg"
      width="900"
      height="810"
      viewBox="-2 -21 30 27"
      role="img"
      aria-label="Adafruit 5374 manufacturer PCB footprint drawing in millimetres"
      style={{ width: '100%', maxHeight: '65vh', background: '#101521' }}
    >
      <title>Adafruit PID5374: manufacturer PCB footprints, not a 3D assembly</title>
      <desc>
        Millimetres. Manufacturer XY origin retained; +Y up. PCB 25.4 by 17.78 mm. Product envelope
        25.6 by 17.7 by 4.6 mm. Component heights undefined. U1 source value ADXL343 retained;
        actual incoming board revision unverified.
      </desc>
      <metadata>
        {JSON.stringify({
          configuration_id: layout.configuration_id,
          specification_sha256: layout.specification_sha256,
          part_id: layout.part_id,
          drawing_id: layout.id,
          source: layout.source,
          license: layout.license,
          frame: layout.frame,
          maturity: layout.maturity,
          missing: layout.missing,
        })}
      </metadata>
      <polygon
        points={points(layout.outline_segments_mm.flat())}
        fill="#432560"
        stroke="#b69acb"
        strokeWidth="0.08"
      />
      {layout.placements.map((item) => (
        <g
          key={item.ref}
          role="button"
          tabIndex={0}
          aria-label={`${item.ref}: ${item.package}, ${item.value || 'no source value'}`}
          onClick={() => setSelected(item.ref)}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault();
              setSelected(item.ref);
            }
          }}
          style={{ cursor: 'pointer' }}
        >
          <title>{`${item.ref}: ${item.package}; ${item.value || 'no source value'}; height undefined`}</title>
          {(layout.shapes as Shape[])
            .filter((shape) => shape.ref === item.ref)
            .map((shape, index) => {
              const stroke =
                selected === item.ref ? '#8bf6ff' : shape.role === 'pad' ? '#e4c465' : '#e1d5e8';
              if (shape.kind === 'circle' && shape.center_mm)
                return (
                  <circle
                    key={index}
                    cx={shape.center_mm[0]}
                    cy={-shape.center_mm[1]}
                    r={shape.radius_mm}
                    fill={shape.role === 'drill' ? '#101521' : 'none'}
                    stroke={stroke}
                    strokeWidth="0.07"
                  />
                );
              if (shape.kind === 'polygon')
                return (
                  <polygon
                    key={index}
                    points={points(shape.points_mm ?? [])}
                    fill={shape.role === 'pad' ? stroke : 'none'}
                    stroke={stroke}
                    strokeWidth="0.04"
                  />
                );
              return (
                <polyline
                  key={index}
                  points={points(shape.points_mm ?? [])}
                  fill="none"
                  stroke={stroke}
                  strokeWidth={Math.max(0.04, shape.width_mm ?? 0.04)}
                  strokeDasharray={shape.role === 'documentation' ? '0.2 0.15' : undefined}
                />
              );
            })}
        </g>
      ))}
      <g fill="#e4e9f2" fontFamily="sans-serif" fontSize="0.65">
        <text x="0" y="-19.3">
          PCB 25.4 × 17.78 mm · XY, +Y ↑ · footprints only
        </text>
        <text x="0" y="2">
          0 → +X (mm); origin at board lower left
        </text>
        <text x="0" y="3.1">
          Adafruit Industries / Limor Fried (Ladyada) · CC BY-SA 3.0
        </text>
        <text x="0" y="4.2">
          Source blob 4a768fc9 · heights / installed fit undefined
        </text>
      </g>
    </svg>
  );
  return (
    <section aria-label="Manufacturer PCB detail">
      <h4>Manufacturer PCB detail · 2D</h4>
      <p>
        Adafruit PID5374 official Eagle layout: 26 source placements, four Ø2.5 mm mounting holes.
        Footprints and pads show source detail; component heights and incoming hardware revision
        remain unverified.
      </p>
      <p>
        PCB outline <strong>25.4 × 17.78 mm</strong>; current product envelope{' '}
        <strong>25.6 × 17.7 × 4.6 mm</strong>. Difference −0.20 / +0.08 mm in XY; mating tolerances
        and datums are undefined.
      </p>
      <button type="button" onClick={() => dialog.current?.showModal()}>
        Open PCB layout
      </button>
      <p>
        <a href={layout.source.url} target="_blank" rel="noreferrer">
          Official Eagle source
        </a>{' '}
        ·{' '}
        <a href="https://creativecommons.org/licenses/by-sa/3.0/" target="_blank" rel="noreferrer">
          CC BY-SA 3.0
        </a>{' '}
        · Adafruit Industries / Limor Fried (Ladyada)
      </p>
      <dialog
        ref={dialog}
        aria-label="Manufacturer PCB reference: Adafruit PID5374"
        style={{
          width: 'min(1000px, 94vw)',
          maxHeight: '94vh',
          overflow: 'auto',
          background: '#17202f',
          color: '#edf2fa',
        }}
      >
        <h3>High-g accelerometer: source PCB drawing</h3>
        <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
          <button type="button" onClick={() => dialog.current?.close()}>
            Close drawing
          </button>
          <button type="button" onClick={exportSvg}>
            Export SVG with provenance
          </button>
        </div>
        {drawing}
        <label>
          Source footprint{' '}
          <select value={selected} onChange={(event) => setSelected(event.target.value)}>
            {layout.placements.map((item) => (
              <option key={item.ref} value={item.ref}>
                {item.ref} · {item.package}
              </option>
            ))}
          </select>
        </label>
        <p>
          <strong>{placement.ref}</strong>: {placement.value || 'No source value'};{' '}
          {placement.package}; {placement.side}; XY {placement.position_mm.join(', ')} mm; rotation{' '}
          {placement.rotation_deg}°; height undefined.
          {'drawing_note' in placement ? ` ${placement.drawing_note}` : ''}
        </p>
        <ul>
          {layout.missing.map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
        <p>
          Source SHA-256 <code style={{ overflowWrap: 'anywhere' }}>{layout.source.sha256}</code>.
          SVG uses the manufacturer XY frame; it has no vehicle placement or engineering acceptance.
        </p>
        <details>
          <summary>Full upstream attribution / license notice</summary>
          <pre style={{ whiteSpace: 'pre-wrap' }}>{layout.license.upstream_notice}</pre>
        </details>
      </dialog>
    </section>
  );
}
