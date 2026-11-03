import { useId, useMemo, useRef, useState } from 'react';
import type { PointerEvent } from 'react';
import type { InspectionDocument } from '../types';
import { designLayers, orthographicMetadata, orthographicModel } from './orthographicGeometry';
import type { DesignLayer, DrawingPart } from './orthographicGeometry';
import './orthographicDesign.css';

export type OrthographicDesignProps = {
  vehicle: InspectionDocument;
  selectedPartId: string | null;
  onSelectPart: (id: string | null) => void;
};
type View = { cx: number; cy: number; scale: number };
const colors: Record<DesignLayer, string> = {
  body: '#8dbacc',
  fins: '#dab477',
  rings: '#a6c89b',
  motor: '#df9b83',
  envelopes: '#b7a5d2',
};

function fit(parts: DrawingPart[]): View {
  if (!parts.length) return { cx: 0, cy: 0, scale: 1 };
  const left = Math.min(...parts.map((item) => item.bounds[0]));
  const right = Math.max(...parts.map((item) => item.bounds[2]));
  const bottom = Math.min(...parts.map((item) => item.bounds[1]));
  const top = Math.max(...parts.map((item) => item.bounds[3]));
  return {
    cx: (left + right) / 2,
    cy: (bottom + top) / 2,
    scale: Math.min(1080 / Math.max(right - left, 1), 300 / Math.max(top - bottom, 1)),
  };
}

/** Source identity changes reset only this drawing's display transform. */
export function OrthographicDesign(props: OrthographicDesignProps) {
  return (
    <DesignDrawing
      key={`${props.vehicle.id}:${JSON.stringify(props.vehicle.identity ?? null)}`}
      {...props}
    />
  );
}

function DesignDrawing({ vehicle, selectedPartId, onSelectPart }: OrthographicDesignProps) {
  const clipId = `drawing-${useId()}`;
  const model = useMemo(() => orthographicModel(vehicle), [vehicle]);
  const [view, setView] = useState(() => fit(model.available));
  const [layers, setLayers] = useState<DesignLayer[]>([...designLayers]);
  const [exportError, setExportError] = useState('');
  const svg = useRef<SVGSVGElement>(null);
  const drag = useRef<{ x: number; y: number; view: View } | null>(null);
  const moved = useRef(false);
  const visible = model.available.filter((item) => layers.includes(item.layer));
  const selected = model.available.find((item) => item.part.id === selectedPartId);
  const selectedMissing = model.unavailable.find((item) => item.part.id === selectedPartId);
  const selectedPart = selected?.part ?? selectedMissing?.part;
  const metadata = orthographicMetadata(vehicle);
  const sx = (x: number) => 600 + (x - view.cx) * view.scale;
  const sy = (y: number) => 250 - (y - view.cy) * view.scale;
  const zoom = (factor: number) =>
    setView((current) => ({
      ...current,
      scale: Math.max(0.02, Math.min(100, current.scale * factor)),
    }));
  const pan = (x: number, y: number) =>
    setView((current) => ({
      ...current,
      cx: current.cx + x / current.scale,
      cy: current.cy + y / current.scale,
    }));
  function localPoint(event: PointerEvent<SVGSVGElement>) {
    const matrix = svg.current?.getScreenCTM();
    return matrix
      ? new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse())
      : null;
  }
  function pointerDown(event: PointerEvent<SVGSVGElement>) {
    if (event.button !== 0 || event.ctrlKey || event.metaKey || event.altKey) return;
    const point = localPoint(event);
    if (!point) return;
    moved.current = false;
    drag.current = { x: point.x, y: point.y, view };
    // Capture only after a drag threshold so an ordinary part click keeps its target.
  }
  function pointerMove(event: PointerEvent<SVGSVGElement>) {
    const start = drag.current;
    const point = localPoint(event);
    if (!start || !point) return;
    const dx = point.x - start.x;
    const dy = point.y - start.y;
    if (Math.hypot(dx, dy) < 4 && !moved.current) return;
    moved.current = true;
    event.currentTarget.setPointerCapture(event.pointerId);
    setView({
      ...start.view,
      cx: start.view.cx - dx / start.view.scale,
      cy: start.view.cy + dy / start.view.scale,
    });
  }
  function pointerUp(event: PointerEvent<SVGSVGElement>) {
    drag.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId))
      event.currentTarget.releasePointerCapture(event.pointerId);
  }
  function download() {
    if (!svg.current) return;
    try {
      const clone = svg.current.cloneNode(true) as SVGSVGElement;
      clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
      clone.setAttribute('width', '1200');
      clone.setAttribute('height', '520');
      const blob = new Blob([new XMLSerializer().serializeToString(clone)], {
        type: 'image/svg+xml;charset=utf-8',
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${vehicle.id.replace(/[^a-z0-9_-]/gi, '_')}-source-arrangement.svg`;
      link.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setExportError('');
    } catch (error) {
      setExportError(error instanceof Error ? error.message : 'SVG export unavailable.');
    }
  }
  return (
    <section className="orthographic-design" aria-label="Source-dimensioned horizontal design">
      <div className="ortho-toolbar" aria-label="Drawing navigation">
        <button onClick={() => zoom(1.4)} disabled={!visible.length}>
          Zoom in
        </button>
        <button onClick={() => zoom(1 / 1.4)} disabled={!visible.length}>
          Zoom out
        </button>
        <button onClick={() => setView(fit(visible))} disabled={!visible.length}>
          Fit visible
        </button>
        <button
          onClick={() => selected && setView(fit([selected]))}
          disabled={!selected || !layers.includes(selected.layer)}
        >
          Focus selection
        </button>
        <button onClick={() => setView(fit(model.available))}>Reset view</button>
        <button onClick={download}>Export SVG</button>
        <details>
          <summary>Pan controls</summary>
          <div className="ortho-pan-controls">
            <button aria-label="Pan drawing left" onClick={() => pan(-100, 0)}>
              Left
            </button>
            <button aria-label="Pan drawing right" onClick={() => pan(100, 0)}>
              Right
            </button>
            <button aria-label="Pan drawing up" onClick={() => pan(0, 100)}>
              Up
            </button>
            <button aria-label="Pan drawing down" onClick={() => pan(0, -100)}>
              Down
            </button>
          </div>
        </details>
      </div>
      <fieldset className="ortho-layers">
        <legend>Source layers</legend>
        {designLayers.map((layer) => (
          <label key={layer}>
            <input
              type="checkbox"
              checked={layers.includes(layer)}
              onChange={() =>
                setLayers((current) =>
                  current.includes(layer)
                    ? current.filter((item) => item !== layer)
                    : [...current, layer],
                )
              }
            />
            {layer}
          </label>
        ))}
      </fieldset>
      <p className="ortho-help">
        Drag to pan; use zoom buttons. Wheel scrolls the page. Select an outline or use the parts
        tree. These are simplified source envelopes, not CAD projections.
      </p>
      <div className="ortho-stage">
        <svg
          ref={svg}
          viewBox="0 0 1200 520"
          role="group"
          aria-label={`${metadata.label}: horizontal source arrangement in millimetres`}
          onPointerDown={pointerDown}
          onPointerMove={pointerMove}
          onPointerUp={pointerUp}
          onPointerCancel={pointerUp}
          onPointerLeave={() => {
            if (!moved.current) drag.current = null;
          }}
        >
          <title>{`${metadata.label} — source-dimensioned arrangement`}</title>
          <desc>
            {metadata.representation} {metadata.axis} Engineering acceptance remains open.
          </desc>
          <metadata>
            {JSON.stringify({
              ...metadata,
              visible_layers: layers,
              selected_part_id: selectedPartId,
            })}
          </metadata>
          <defs>
            <clipPath id={clipId}>
              <rect x="0" y="70" width="1200" height="335" />
            </clipPath>
          </defs>
          <rect width="1200" height="520" fill="#111d26" />
          <g fontFamily="system-ui, sans-serif" fill="#d8e8ef">
            <text x="22" y="28" fontSize="17">
              {metadata.label}
            </text>
            <text x="22" y="50" fontSize="12">
              Source envelopes · mm · acceptance open · {model.unavailable.length} parts have
              unavailable drawing geometry
            </text>
            <text x="22" y="65" fontSize="10">
              {vehicle.id} · specification{' '}
              {typeof vehicle.identity?.resolved_spec_sha256 === 'string'
                ? vehicle.identity.resolved_spec_sha256.slice(0, 16)
                : 'unavailable'}{' '}
              · CAD{' '}
              {typeof vehicle.identity?.cad_revision_sha256 === 'string'
                ? vehicle.identity.cad_revision_sha256.slice(0, 16)
                : 'unavailable'}
            </text>
            <g clipPath={`url(#${clipId})`}>
              <line
                x1="25"
                y1={sy(0)}
                x2="1175"
                y2={sy(0)}
                stroke="#718791"
                strokeDasharray="8 6"
              />
              {visible.map((item) => (
                <g
                  key={item.part.id}
                  role="button"
                  tabIndex={0}
                  aria-label={`Select ${item.part.name ?? item.part.id}: ${item.note}`}
                  aria-pressed={item.part.id === selectedPartId}
                  onClick={() => {
                    if (!moved.current) onSelectPart(item.part.id);
                  }}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      onSelectPart(item.part.id);
                    }
                  }}
                >
                  <title>{`${item.part.name ?? item.part.id}: ${item.note}`}</title>
                  {item.polygons.map((points, index) => (
                    <polygon
                      key={index}
                      points={points.map(([x, y]) => `${sx(x)},${sy(y)}`).join(' ')}
                      fill={colors[item.layer]}
                      fillOpacity={item.part.id === selectedPartId ? 0.5 : 0.13}
                      stroke={item.part.id === selectedPartId ? '#fff2a5' : colors[item.layer]}
                      strokeWidth={item.part.id === selectedPartId ? 3 : 1.4}
                      strokeDasharray={
                        item.layer === 'envelopes' || item.part.type === 'nose_cone'
                          ? '6 4'
                          : undefined
                      }
                      vectorEffect="non-scaling-stroke"
                    />
                  ))}
                </g>
              ))}
            </g>
            {[100, 350, 600, 850, 1100].map((pixel) => (
              <g key={pixel}>
                <line x1={pixel} y1="410" x2={pixel} y2="420" stroke="#718791" />
                <text x={pixel} y="437" textAnchor="middle" fontSize="11">
                  {(view.cx + (pixel - 600) / view.scale).toFixed(1)} mm
                </text>
              </g>
            ))}
            <line x1={sx(0)} y1="410" x2={sx(0)} y2="430" stroke="#b8d2df" />
            <text x={Math.max(22, Math.min(1000, sx(0)))} y="457" textAnchor="start" fontSize="12">
              0 mm · source nose datum
            </text>
            {selected && (
              <text x="22" y="481" fontSize="12">
                Selected: {selected.part.id} · axial bounds {selected.bounds[0].toFixed(2)}–
                {selected.bounds[2].toFixed(2)} mm · source role: {selected.representation}
              </text>
            )}
            <text x="22" y="507" fontSize="12">
              Station increases toward aft → · vertical: first source transverse coordinate · no
              manufacturing/flight qualification
            </text>
          </g>
        </svg>
      </div>
      {!visible.length && (
        <p role="status">
          No drawable geometry in the visible layers. Enable a source layer or inspect unavailable
          dimensions below.
        </p>
      )}
      {exportError && <p role="alert">Export unavailable: {exportError}</p>}
      <div className="ortho-selection" aria-live="polite">
        <strong>
          {selectedPart?.name ??
            selectedPart?.id ??
            'Select a component to inspect its source dimensions'}
        </strong>
        {selectedPart && (
          <>
            <p>{selectedPart.function ?? selectedPart.learn}</p>
            <p>
              Material: {selectedPart.material} · Source role:{' '}
              {selected?.representation ?? 'unavailable'}
            </p>
            <p>{selected?.note ?? selectedMissing?.reason}</p>
            {selected && !layers.includes(selected.layer) && (
              <p>Selected component is in a hidden layer; enable {selected.layer} to see it.</p>
            )}
            <details>
              <summary>Recorded dimensions & source</summary>
              <pre>
                {JSON.stringify(
                  {
                    dimensions: selectedPart.dimensions ?? selectedPart.geometry ?? null,
                    location: selectedPart.location ?? {
                      position_m: selectedPart.position_m ?? null,
                    },
                    source: selectedPart.source ?? null,
                  },
                  null,
                  2,
                )}
              </pre>
            </details>
          </>
        )}
      </div>
      <details className="ortho-unavailable">
        <summary>Unavailable geometry ({model.unavailable.length}) & representation scope</summary>
        <p>
          No dimension is inferred from mass, CAD display bounds or another design. Nose profiles,
          holes, joints and fin clocking are not reconstructed.
        </p>
        {model.unavailable.map(({ part, reason }) => (
          <p key={part.id}>
            <button onClick={() => onSelectPart(part.id)}>{part.name ?? part.id}</button> {reason}
          </p>
        ))}
        <pre>
          {JSON.stringify(
            {
              configuration: vehicle.id,
              identity: vehicle.identity ?? null,
              representation: metadata.representation,
            },
            null,
            2,
          )}
        </pre>
      </details>
    </section>
  );
}
