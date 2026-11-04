import { useId, useMemo, useRef, useState } from 'react';
import type { PointerEvent } from 'react';
import type { InspectionDocument } from '../types';
import { designLayers, orthographicMetadata, orthographicModel } from './orthographicGeometry';
import type { DesignLayer } from './orthographicGeometry';
import {
  fitDrawing as fit,
  selectionVisibility,
  visibleDrawingParts,
  sourceMaturity,
} from './designPresentation';
import type { DrawingView as View } from './designPresentation';
import './orthographicDesign.css';

export type OrthographicDesignProps = {
  vehicle: InspectionDocument;
  selectedPartId: string | null;
  onSelectPart: (id: string | null) => void;
  hiddenPartIds?: readonly string[];
  onRevealPart?: (id: string) => void;
};
const colors: Record<DesignLayer, string> = {
  body: '#8dbacc',
  fins: '#dab477',
  rings: '#a6c89b',
  motor: '#df9b83',
  envelopes: '#b7a5d2',
};

/** Source identity changes reset only this drawing's display transform. */
export function OrthographicDesign(props: OrthographicDesignProps) {
  return (
    <DesignDrawing
      key={`${props.vehicle.id}:${JSON.stringify(props.vehicle.identity ?? null)}`}
      {...props}
    />
  );
}

function DesignDrawing({
  vehicle,
  selectedPartId,
  onSelectPart,
  hiddenPartIds = [],
  onRevealPart,
}: OrthographicDesignProps) {
  const clipId = `drawing-${useId()}`;
  const model = useMemo(() => orthographicModel(vehicle), [vehicle]);
  const [view, setView] = useState(() => fit(model.available));
  const [layers, setLayers] = useState<DesignLayer[]>([...designLayers]);
  const [onlySelected, setOnlySelected] = useState(false);
  const [exportError, setExportError] = useState('');
  const svg = useRef<SVGSVGElement>(null);
  const drag = useRef<{ x: number; y: number; view: View } | null>(null);
  const moved = useRef(false);
  const visible = visibleDrawingParts(
    model.available,
    layers,
    hiddenPartIds,
    onlySelected,
    selectedPartId,
  );
  const selected = model.available.find((item) => item.part.id === selectedPartId);
  const visibility = selectionVisibility(selected, layers, hiddenPartIds);
  const selectedVisible = visibility === 'visible' ? selected : undefined;
  const selectedMissing = model.unavailable.find((item) => item.part.id === selectedPartId);
  const selectedPart = selected?.part ?? selectedMissing?.part;
  const metadata = orthographicMetadata(vehicle);
  const sx = (x: number) => 600 + (x - view.cx) * view.scale;
  const sy = (y: number) => 270 - (y - view.cy) * view.scale;
  const zoom = (factor: number) =>
    setView((current) => ({
      ...current,
      scale: Math.max(0.02, Math.min(10000, current.scale * factor)),
    }));
  const pan = (x: number, y: number) =>
    setView((current) => ({
      ...current,
      cx: current.cx + x / current.scale,
      cy: current.cy + y / current.scale,
    }));
  function revealAndFocus() {
    if (!selected || (hiddenPartIds.includes(selected.part.id) && !onRevealPart)) return;
    if (hiddenPartIds.includes(selected.part.id)) onRevealPart?.(selected.part.id);
    setLayers((current) =>
      current.includes(selected.layer) ? current : [...current, selected.layer],
    );
    setView(fit([selected]));
  }
  function showContext() {
    setOnlySelected(false);
    setView(fit(visibleDrawingParts(model.available, layers, hiddenPartIds, false, null)));
  }
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
      clone.setAttribute('height', '560');
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
          onClick={revealAndFocus}
          data-inspection-action="focus"
          disabled={!selected || (visibility === 'hidden-part' && !onRevealPart)}
        >
          {visibility === 'hidden-part' || visibility === 'hidden-layer'
            ? 'Reveal & focus selection'
            : 'Focus selection'}
        </button>
        <button onClick={showContext} data-inspection-action="reset">
          Show context / reset view
        </button>
        <button
          aria-pressed={onlySelected}
          disabled={!selected || visibility !== 'visible'}
          onClick={() => {
            setOnlySelected((value) => !value);
            setView(
              fit(
                onlySelected
                  ? visibleDrawingParts(model.available, layers, hiddenPartIds, false, null)
                  : [selected!],
              ),
            );
          }}
        >
          {onlySelected ? 'Show other visible parts' : 'Inspect selection only'}
        </button>
        <button onClick={download}>Export SVG</button>
        <details>
          <summary>Pan controls</summary>
          <div className="ortho-pan-controls">
            <button aria-label="Pan view left" onClick={() => pan(-100, 0)}>
              Left
            </button>
            <button aria-label="Pan view right" onClick={() => pan(100, 0)}>
              Right
            </button>
            <button aria-label="Pan view up" onClick={() => pan(0, 100)}>
              Up
            </button>
            <button aria-label="Pan view down" onClick={() => pan(0, -100)}>
              Down
            </button>
          </div>
        </details>
      </div>
      <label className="ortho-component-picker">
        Component
        <select
          aria-label="Select source component"
          value={selectedPartId ?? ''}
          onChange={(event) => onSelectPart(event.target.value || null)}
        >
          <option value="">No selected component</option>
          {vehicle.parts.map((part) => (
            <option key={part.id} value={part.id}>
              {part.name ?? part.id}
              {hiddenPartIds.includes(part.id) ? ' — hidden' : ''}
              {model.unavailable.some((item) => item.part.id === part.id)
                ? ' — geometry unavailable'
                : ''}
            </option>
          ))}
        </select>
      </label>
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
        tree. Focus the drawing to use arrow keys to pan, +/− to zoom, F to focus and R to reset.
        These are simplified source envelopes, not CAD projections.
      </p>
      <div className="ortho-stage">
        <svg
          ref={svg}
          viewBox="0 0 1200 560"
          tabIndex={0}
          onKeyDown={(event) => {
            if (event.ctrlKey || event.metaKey || event.altKey) return;
            const key = event.key.toLowerCase();
            if (
              ![
                'arrowleft',
                'arrowright',
                'arrowup',
                'arrowdown',
                '+',
                '=',
                '-',
                'f',
                'r',
              ].includes(key)
            )
              return;
            event.preventDefault();
            event.stopPropagation();
            if (key === 'arrowleft') pan(-80, 0);
            if (key === 'arrowright') pan(80, 0);
            if (key === 'arrowup') pan(0, 80);
            if (key === 'arrowdown') pan(0, -80);
            if (key === '+' || key === '=') zoom(1.4);
            if (key === '-') zoom(1 / 1.4);
            if (key === 'f') revealAndFocus();
            if (key === 'r') showContext();
          }}
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
              selected_visibility: visibility,
              hidden_part_ids: hiddenPartIds,
              selected_only: onlySelected,
              drawing_transform: view,
            })}
          </metadata>
          <defs>
            <clipPath id={clipId}>
              <rect x="0" y="130" width="1200" height="270" />
            </clipPath>
          </defs>
          <rect width="1200" height="560" fill="#111d26" />
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
            {designLayers.map((layer, index) => (
              <g key={layer} opacity={layers.includes(layer) ? 1 : 0.5}>
                <rect
                  x={22 + index * 180}
                  y="83"
                  width="18"
                  height="10"
                  fill={colors[layer]}
                  fillOpacity="0.35"
                  stroke={colors[layer]}
                />
                <text x={48 + index * 180} y="93" fontSize="12">
                  {layer} ({visible.filter((item) => item.layer === layer).length})
                  {layers.includes(layer) ? '' : ' off'}
                </text>
              </g>
            ))}
            <text x="22" y="116" fontSize="11">
              Dashed: bounding envelope · gold: selected source component ·{' '}
              {onlySelected ? 'Selection only' : 'Visible component context'} · hidden components:{' '}
              {hiddenPartIds.filter((id) => vehicle.parts.some((part) => part.id === id)).length}
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
                  tabIndex={
                    item.part.id === selectedPartId ||
                    (!selectedVisible && item.part.id === visible[0]?.part.id)
                      ? 0
                      : -1
                  }
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
              {selectedVisible && (
                <g pointerEvents="none">
                  <rect
                    x={sx(selectedVisible.bounds[0]) - 5}
                    y={sy(selectedVisible.bounds[3]) - 5}
                    width={
                      (selectedVisible.bounds[2] - selectedVisible.bounds[0]) * view.scale + 10
                    }
                    height={
                      (selectedVisible.bounds[3] - selectedVisible.bounds[1]) * view.scale + 10
                    }
                    fill="none"
                    stroke="#fff2a5"
                    strokeWidth="1"
                    strokeDasharray="3 3"
                  />
                </g>
              )}
            </g>
            {selectedVisible && (
              <g pointerEvents="none">
                <rect
                  x="600"
                  y="20"
                  width="575"
                  height="44"
                  rx="4"
                  fill="#27313a"
                  stroke="#fff2a5"
                />
                <text x="612" y="38" fontSize="12" fill="#fff2a5">
                  Selected: {(selectedVisible.part.name ?? selectedVisible.part.id).slice(0, 62)}
                </text>
                <text x="612" y="55" fontSize="11">
                  Axial {selectedVisible.bounds[0].toFixed(2)}–
                  {selectedVisible.bounds[2].toFixed(2)} mm · highlight is an annotation
                </text>
              </g>
            )}
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
              0 mm · source nose datum{sx(0) < 0 || sx(0) > 1200 ? ' (outside current view)' : ''}
            </text>
            {selected && (
              <text x="22" y="481" fontSize="12">
                Selected: {selected.part.id} · axial bounds {selected.bounds[0].toFixed(2)}–
                {selected.bounds[2].toFixed(2)} mm · source role: {selected.representation} ·{' '}
                {visibility.replace('-', ' ')}
              </text>
            )}
            <text x="22" y="507" fontSize="11">
              {selected
                ? sourceMaturity(selected)
                : selectedMissing
                  ? `${selectedMissing.part.id}: ${selectedMissing.reason}`
                  : 'Select a source component for its dimensions and representation scope.'}
            </text>
            <text x="22" y="544" fontSize="12">
              Station increases toward aft → · vertical: first source transverse coordinate · no
              manufacturing/flight qualification
            </text>
          </g>
        </svg>
      </div>
      {onlySelected && (
        <p className="ortho-help" role="status">
          Showing only the selected source component.{' '}
          <button onClick={showContext}>Return to visible component context</button>
        </p>
      )}
      {!visible.length && (
        <p role="status">
          No drawable geometry in the visible layers. Enable a source layer or inspect unavailable
          dimensions below.
        </p>
      )}
      {exportError && <p role="alert">Export unavailable: {exportError}</p>}
      {selectedPartId && !selectedPart && (
        <p className="ortho-help" role="status">
          Selected component {selectedPartId} is not recorded in this source. No geometry is mapped
          from another design. <button onClick={() => onSelectPart(null)}>Clear selection</button>
        </p>
      )}
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
            <p>
              {selected
                ? sourceMaturity(selected)
                : 'Drawing geometry unavailable; no replacement shape is inferred.'}
            </p>
            <p>{selected?.note ?? selectedMissing?.reason}</p>
            {visibility === 'hidden-part' && (
              <p role="status">
                Selected component is hidden by the shared parts visibility control.{' '}
                {onRevealPart ? (
                  <button onClick={revealAndFocus}>Reveal & focus this part</button>
                ) : (
                  'Reveal it in the parts tree to inspect its drawing.'
                )}
              </p>
            )}
            {selected && (
              <p>
                Source axial interval: {selected.bounds[0].toFixed(2)}–
                {selected.bounds[2].toFixed(2)} mm. Displaying an envelope does not establish
                manufactured geometry.
              </p>
            )}
            {selected && !layers.includes(selected.layer) && (
              <p role="status">
                Selected component is in a hidden {selected.layer} layer.{' '}
                <button onClick={revealAndFocus}>Reveal layer & focus</button>
              </p>
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
