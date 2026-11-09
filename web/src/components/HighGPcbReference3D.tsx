import { useEffect, useMemo, useRef, useState } from 'react';
import type { ComponentRef } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { Html, OrbitControls } from '@react-three/drei';
import { BufferGeometry, DoubleSide, Float32BufferAttribute, Path, Shape } from 'three';
import type { OrthographicCamera } from 'three';
import {
  highGPcbReference,
  footprintConnectionSummary,
  lineTriangles,
  netContactSummary,
  outlinePoints,
  pcbAxisLabelTicks,
  pcbAxisTicks,
  quadTriangles,
  sourceLinePoints,
} from './highGPcbReference';
import type { HighGPcbReferenceSource, SourcePlacement } from './highGPcbReference';
import './highGPcbReference.css';

type Layout = NonNullable<ReturnType<typeof highGPcbReference>>;
type CameraAction = 'fit' | 'top' | 'bottom' | 'selected' | 'in' | 'out';
type ViewCommand = { action: CameraAction; serial: number };

function xyShape(points: number[][]): Shape {
  const shape = new Shape();
  points.forEach(([x, y], index) => (index === 0 ? shape.moveTo(x, y) : shape.lineTo(x, y)));
  shape.closePath();
  return shape;
}

function flatGeometry(triangles: number[]): BufferGeometry {
  const geometry = new BufferGeometry();
  const xyz = new Float32Array((triangles.length / 2) * 3);
  for (let i = 0; i < triangles.length / 2; i += 1) {
    xyz[i * 3] = triangles[i * 2];
    xyz[i * 3 + 1] = triangles[i * 2 + 1];
  }
  geometry.setAttribute('position', new Float32BufferAttribute(xyz, 3));
  geometry.computeVertexNormals();
  return geometry;
}

function lineBatch(
  lines: { points_mm: number[][]; width_mm: number; source_curve_deg?: number }[],
): BufferGeometry {
  return flatGeometry(
    lines.flatMap((line) =>
      lineTriangles(sourceLinePoints(line.points_mm, line.source_curve_deg ?? 0), line.width_mm),
    ),
  );
}

function rectangleBatch(groups: { corners_mm: number[][] }[]): BufferGeometry {
  return flatGeometry(groups.flatMap((group) => group.corners_mm.flatMap(quadTriangles)));
}

function BoardScene({
  layout,
  selected,
  net,
  top,
  bottom,
  silk,
  artwork,
  documentation,
  separation,
  command,
  onSelectRef,
  onSelectNet,
}: {
  layout: Layout;
  selected: SourcePlacement;
  net: string;
  top: boolean;
  bottom: boolean;
  silk: boolean;
  artwork: boolean;
  documentation: boolean;
  separation: number;
  command: ViewCommand;
  onSelectRef: (ref: string) => void;
  onSelectNet: (net: string) => void;
}) {
  const controls = useRef<ComponentRef<typeof OrbitControls>>(null);
  const { camera, size, invalidate } = useThree();
  const midX = layout.pcb_size_mm[0] / 2;
  const midY = layout.pcb_size_mm[1] / 2;
  const topZ = 0.015 + separation * 2;
  const bottomZ = -0.015 - separation * 2;
  const silkTopZ = topZ + 0.006;
  const silkBottomZ = bottomZ - 0.006;
  const xTicks = useMemo(() => pcbAxisTicks(layout.pcb_size_mm[0]), [layout]);
  const yTicks = useMemo(() => pcbAxisTicks(layout.pcb_size_mm[1]), [layout]);
  const boardShape = useMemo(() => {
    const outline = xyShape(outlinePoints(layout.outline_segments_mm));
    for (const hole of layout.mounting_holes) {
      const path = new Path();
      path.absarc(hole.center_mm[0], hole.center_mm[1], hole.radius_mm, 0, Math.PI * 2, true);
      outline.holes.push(path);
    }
    return outline;
  }, [layout]);
  const traceGroups = useMemo(() => {
    const groups = new Map<string, typeof layout.traces>();
    for (const trace of layout.traces) {
      const key = `${trace.layer}:${trace.net}`;
      groups.set(key, [...(groups.get(key) ?? []), trace]);
    }
    return [...groups].map(([key, lines]) => ({
      key,
      layer: lines[0].layer,
      net: lines[0].net,
      geometry: lineBatch(lines),
    }));
  }, [layout]);
  const silkBatches = useMemo(
    () =>
      [21, 22].map((layer) => ({
        layer,
        lines: lineBatch(layout.silkscreen.lines.filter((line) => line.layer === layer)),
        rectangles: rectangleBatch(
          layout.silkscreen.rectangle_groups.filter((group) => group.layer === layer),
        ),
      })),
    [layout],
  );
  const documentationBatches = useMemo(
    () =>
      [51, 52].map((layer) => ({
        layer,
        lines: lineBatch(layout.documentation.lines.filter((line) => line.layer === layer)),
        rectangles: rectangleBatch(
          layout.documentation.rectangle_groups.filter((group) => group.layer === layer),
        ),
      })),
    [layout],
  );
  const axisLines = useMemo(
    () =>
      lineBatch([
        {
          points_mm: [
            [-0.8, -0.8],
            [layout.pcb_size_mm[0], -0.8],
          ],
          width_mm: 0.045,
        },
        {
          points_mm: [
            [-0.8, -0.8],
            [-0.8, layout.pcb_size_mm[1]],
          ],
          width_mm: 0.045,
        },
        ...xTicks.map((x) => ({
          points_mm: [
            [x, -0.58],
            [x, -1.02],
          ],
          width_mm: 0.045,
        })),
        ...yTicks.map((y) => ({
          points_mm: [
            [-0.58, y],
            [-1.02, y],
          ],
          width_mm: 0.045,
        })),
      ]),
    [layout, xTicks, yTicks],
  );

  const pendingDisposal = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    if (pendingDisposal.current !== null) {
      clearTimeout(pendingDisposal.current);
      pendingDisposal.current = null;
    }
    return () => {
      // Strict Mode replays effects without recreating these memoized buffers.
      // Defer disposal so the replay can cancel it; a real unmount releases them.
      pendingDisposal.current = setTimeout(() => {
        traceGroups.forEach((group) => group.geometry.dispose());
        silkBatches.forEach((batch) => {
          batch.lines.dispose();
          batch.rectangles.dispose();
        });
        documentationBatches.forEach((batch) => {
          batch.lines.dispose();
          batch.rectangles.dispose();
        });
        axisLines.dispose();
        pendingDisposal.current = null;
      }, 0);
    };
  }, [traceGroups, silkBatches, documentationBatches, axisLines]);

  useEffect(() => {
    const view = camera as OrthographicCamera;
    const target = controls.current?.target;
    const fitZoom = Math.min(size.width / 32, size.height / 24);
    if (command.action === 'in' || command.action === 'out') {
      view.zoom *= command.action === 'in' ? 1.4 : 1 / 1.4;
    } else if (command.action === 'selected') {
      const [x, y] = selected.position_mm;
      target?.set(x, y, 0);
      view.position.set(x + 5, y - 5, 14);
      view.up.set(0, 1, 0);
      view.zoom = Math.min(size.width / 9, size.height / 8);
    } else {
      target?.set(midX, midY, 0);
      view.position.set(
        midX + (command.action === 'fit' ? 13 : 0),
        midY + (command.action === 'fit' ? -10 : 0),
        command.action === 'bottom' ? -50 : command.action === 'fit' ? 35 : 50,
      );
      view.up.set(0, 1, 0);
      view.zoom = fitZoom;
    }
    view.zoom = Math.max(4, Math.min(180, view.zoom));
    view.lookAt(target?.x ?? midX, target?.y ?? midY, target?.z ?? 0);
    view.updateProjectionMatrix();
    controls.current?.update();
    invalidate();
  }, [camera, command, invalidate, midX, midY, selected, size.height, size.width]);

  return (
    <>
      <color attach="background" args={['#101a27']} />
      <ambientLight intensity={1} />
      <mesh>
        <shapeGeometry args={[boardShape]} />
        <meshBasicMaterial color="#254c5b" side={DoubleSide} transparent opacity={0.84} />
      </mesh>
      <mesh geometry={axisLines} dispose={null} position-z={0.09}>
        <meshBasicMaterial color="#8edcf5" side={DoubleSide} />
      </mesh>
      {pcbAxisLabelTicks(layout.pcb_size_mm[0]).map((x) => (
        <Html key={`x:${x}`} position={[x, -1.45, 0.09]} center style={{ pointerEvents: 'none' }}>
          <span className="highg-pcb-axis-label">{x} mm</span>
        </Html>
      ))}
      {pcbAxisLabelTicks(layout.pcb_size_mm[1])
        .slice(1)
        .map((y) => (
          <Html key={`y:${y}`} position={[-1.85, y, 0.09]} center style={{ pointerEvents: 'none' }}>
            <span className="highg-pcb-axis-label">{y} mm</span>
          </Html>
        ))}
      {layout.mounting_holes.map((hole) => (
        <mesh key={hole.ref} position={[hole.center_mm[0], hole.center_mm[1], 0.03]}>
          <ringGeometry args={[hole.radius_mm, hole.radius_mm + 0.055, 40]} />
          <meshBasicMaterial color="#d4e6ec" side={DoubleSide} />
        </mesh>
      ))}
      {traceGroups
        .filter((group) => (group.layer === 1 ? top : bottom))
        .map((group) => (
          <mesh
            key={group.key}
            geometry={group.geometry}
            dispose={null}
            position-z={group.layer === 1 ? topZ : bottomZ}
            onClick={(event) => {
              event.stopPropagation();
              onSelectNet(group.net);
            }}
          >
            <meshBasicMaterial
              color={net === group.net ? '#f7fb91' : group.layer === 1 ? '#d89a54' : '#9c78ce'}
              side={DoubleSide}
              transparent={Boolean(net && net !== group.net)}
              opacity={net && net !== group.net ? 0.24 : 1}
            />
          </mesh>
        ))}
      {layout.pads
        .filter((pad) => (pad.layer === 1 ? top : pad.layer === 16 ? bottom : top || bottom))
        .map((pad) => {
          const key = `${pad.ref}:${pad.name}:${pad.layer}`;
          const active = pad.ref === selected.ref || (net && pad.net === net);
          const z = pad.layer === 16 ? bottomZ + 0.002 : topZ + 0.002;
          const material = () => (
            <meshBasicMaterial
              color={active ? '#72f5f0' : pad.layer === 16 ? '#b393db' : '#f0c673'}
              side={DoubleSide}
              transparent={Boolean(net && pad.net !== net && pad.ref !== selected.ref)}
              opacity={net && pad.net !== net && pad.ref !== selected.ref ? 0.28 : 1}
            />
          );
          if ('points_mm' in pad && Array.isArray(pad.points_mm))
            return (
              <mesh
                key={key}
                position-z={z}
                onClick={(event) => {
                  event.stopPropagation();
                  onSelectRef(pad.ref);
                }}
              >
                <shapeGeometry args={[xyShape(pad.points_mm)]} />
                {material()}
              </mesh>
            );
          const outer =
            'diameter_mm' in pad && typeof pad.diameter_mm === 'number' ? pad.diameter_mm / 2 : 0;
          const inner =
            'drill_mm' in pad && typeof pad.drill_mm === 'number' ? pad.drill_mm / 2 : 0;
          if (outer <= inner) return null;
          const faces = [top ? topZ + 0.002 : null, bottom ? bottomZ - 0.002 : null].filter(
            (face): face is number => face !== null,
          );
          return faces.map((face, index) => (
            <mesh
              key={`${key}:${index}`}
              position={[pad.center_mm[0], pad.center_mm[1], face]}
              onClick={(event) => {
                event.stopPropagation();
                onSelectRef(pad.ref);
              }}
            >
              <ringGeometry args={[inner, outer, 28]} />
              {material()}
            </mesh>
          ));
        })}
      {(top || bottom) &&
        layout.vias.flatMap((via, index) =>
          [top ? topZ + 0.004 : null, bottom ? bottomZ - 0.004 : null]
            .filter((face): face is number => face !== null)
            .map((face, side) => (
              <mesh
                key={`${via.net}:${index}:${side}`}
                position={[via.center_mm[0], via.center_mm[1], face]}
                onClick={(event) => {
                  event.stopPropagation();
                  onSelectNet(via.net);
                }}
              >
                <circleGeometry args={[via.drill_mm / 2, 20]} />
                <meshBasicMaterial
                  color={net === via.net ? '#fbf3a8' : '#0b1722'}
                  side={DoubleSide}
                />
              </mesh>
            )),
        )}
      {silk &&
        silkBatches
          .filter((batch) => (batch.layer === 21 ? top : bottom))
          .map((batch) => (
            <group key={batch.layer} position-z={batch.layer === 21 ? silkTopZ : silkBottomZ}>
              <mesh geometry={batch.lines} dispose={null}>
                <meshBasicMaterial color="#eff3df" side={DoubleSide} />
              </mesh>
              {artwork && (
                <mesh geometry={batch.rectangles} dispose={null}>
                  <meshBasicMaterial color="#eff3df" side={DoubleSide} />
                </mesh>
              )}
            </group>
          ))}
      {silk &&
        layout.silkscreen.circles
          .filter((circle) => (circle.layer === 21 ? top : bottom))
          .map((circle, index) => (
            <mesh
              key={index}
              position={[
                circle.center_mm[0],
                circle.center_mm[1],
                circle.layer === 21 ? silkTopZ : silkBottomZ,
              ]}
            >
              <ringGeometry
                args={[
                  Math.max(0, circle.radius_mm - circle.width_mm / 2),
                  circle.radius_mm + circle.width_mm / 2,
                  40,
                ]}
              />
              <meshBasicMaterial color="#eff3df" side={DoubleSide} />
            </mesh>
          ))}
      {silk &&
        layout.silkscreen.polygons
          .filter((polygon) => (polygon.layer === 21 ? top : bottom))
          .map((polygon, index) => (
            <mesh key={index} position-z={polygon.layer === 21 ? silkTopZ : silkBottomZ}>
              <shapeGeometry args={[xyShape(polygon.vertices.map((vertex) => vertex.xy_mm))]} />
              <meshBasicMaterial color="#eff3df" side={DoubleSide} />
            </mesh>
          ))}
      {silk &&
        layout.silkscreen.texts
          .filter((label) => (label.layer === 21 ? top : bottom))
          .map((label, index) => (
            <Html
              key={index}
              position={[
                label.position_mm[0],
                label.position_mm[1],
                label.layer === 21 ? silkTopZ : silkBottomZ,
              ]}
              center
              // Keep source XY anchored, but render the glyph at its fixed CSS size.
              // Drei multiplies distanceFactor by orthographic zoom and obscures the board.
              style={{ pointerEvents: 'none' }}
            >
              <span
                className="highg-pcb-silk-label"
                style={{ transform: `rotate(${-label.rotation_deg}deg)` }}
              >
                {label.text}
              </span>
            </Html>
          ))}
      {documentation &&
        documentationBatches
          .filter((batch) => (batch.layer === 51 ? top : bottom))
          .map((batch) => (
            <group
              key={batch.layer}
              position-z={batch.layer === 51 ? silkTopZ + 0.005 : silkBottomZ - 0.005}
            >
              <mesh geometry={batch.lines} dispose={null}>
                <meshBasicMaterial color="#7eaed6" side={DoubleSide} transparent opacity={0.68} />
              </mesh>
              <mesh geometry={batch.rectangles} dispose={null}>
                <meshBasicMaterial color="#7eaed6" side={DoubleSide} transparent opacity={0.68} />
              </mesh>
            </group>
          ))}
      {documentation &&
        layout.documentation.circles
          .filter((circle) => (circle.layer === 51 ? top : bottom))
          .map((circle, index) => (
            <mesh
              key={index}
              position={[
                circle.center_mm[0],
                circle.center_mm[1],
                circle.layer === 51 ? silkTopZ + 0.005 : silkBottomZ - 0.005,
              ]}
            >
              <ringGeometry
                args={[
                  Math.max(0, circle.radius_mm - circle.width_mm / 2),
                  circle.radius_mm + circle.width_mm / 2,
                  30,
                ]}
              />
              <meshBasicMaterial color="#7eaed6" side={DoubleSide} />
            </mesh>
          ))}
      {documentation &&
        layout.documentation.texts
          .filter((label) => ([25, 26].includes(label.layer) ? top : bottom))
          .map((label, index) => (
            <Html
              key={index}
              position={[
                label.position_mm[0],
                label.position_mm[1],
                [25, 26].includes(label.layer) ? silkTopZ + 0.006 : silkBottomZ - 0.006,
              ]}
              center
              // Refdes uses the same fixed screen size as the silk text above.
              style={{ pointerEvents: 'none' }}
            >
              <span
                className="highg-pcb-ref-label"
                style={{ transform: `rotate(${-label.rotation_deg}deg)` }}
              >
                {label.text}
              </span>
            </Html>
          ))}
      {documentation &&
        layout.placements
          .filter((placement) => (placement.side === 'top' ? top : bottom))
          .map((placement) => (
            <mesh
              key={`pick:${placement.ref}`}
              position={[
                placement.position_mm[0],
                placement.position_mm[1],
                placement.side === 'top' ? silkTopZ + 0.015 : silkBottomZ - 0.015,
              ]}
              onClick={(event) => {
                event.stopPropagation();
                onSelectRef(placement.ref);
              }}
            >
              <circleGeometry args={[0.42, 20]} />
              <meshBasicMaterial
                color={placement.ref === selected.ref ? '#68f5f2' : '#8edcf5'}
                side={DoubleSide}
                transparent
                opacity={placement.ref === selected.ref ? 0.75 : 0.28}
                depthTest={false}
              />
            </mesh>
          ))}
      {(selected.side === 'top' ? top : bottom) && (
        <mesh
          position={[
            selected.position_mm[0],
            selected.position_mm[1],
            selected.side === 'top' ? silkTopZ + 0.02 : silkBottomZ - 0.02,
          ]}
        >
          <ringGeometry args={[0.68, 0.76, 32]} />
          <meshBasicMaterial color="#68f5f2" side={DoubleSide} depthTest={false} />
        </mesh>
      )}
      <OrbitControls
        ref={controls}
        makeDefault
        enableDamping={false}
        enablePan
        screenSpacePanning
        minZoom={4}
        maxZoom={180}
      />
    </>
  );
}

/** Planar manufacturer copper/footprint reference in an orbitable 3D scene; no package bodies. */
export default function HighGPcbReference3D(props: HighGPcbReferenceSource) {
  const layout = highGPcbReference(props);
  const [selectedRef, setSelectedRef] = useState('U1');
  const [selectedNet, setSelectedNet] = useState('');
  const [top, setTop] = useState(true);
  const [bottom, setBottom] = useState(true);
  const [silk, setSilk] = useState(true);
  const [artwork, setArtwork] = useState(true);
  const [documentation, setDocumentation] = useState(false);
  const [separation, setSeparation] = useState(0);
  const [command, setCommand] = useState<ViewCommand>({ action: 'fit', serial: 0 });
  if (!layout)
    return (
      <p role="status">
        Manufacturer PCB layers unavailable: exact board or vehicle source does not match.
      </p>
    );
  const selected =
    layout.placements.find((placement) => placement.ref === selectedRef) ?? layout.placements[0];
  const footprintSummary = footprintConnectionSummary(selected.ref);
  const netSummary = selectedNet ? netContactSummary(selectedNet) : null;
  const view = (action: CameraAction) =>
    setCommand((current) => ({ action, serial: current.serial + 1 }));
  const selectFootprint = (ref: string) => {
    setSelectedRef(ref);
    setSelectedNet('');
  };
  const resetReference = () => {
    setSelectedRef('U1');
    setSelectedNet('');
    setTop(true);
    setBottom(true);
    setSilk(true);
    setArtwork(true);
    setDocumentation(false);
    setSeparation(0);
    view('fit');
  };
  return (
    <section
      className="highg-pcb-reference"
      aria-label="Manufacturer PCB planar layers in an interactive 3D view"
    >
      <h3>High-g board · source layer explorer</h3>
      <p>
        Orbit and zoom the actual Adafruit PID 5374 board XY artwork. Copper pads/traces, drilled
        locations, silk and footprints are source planar features.{' '}
        <strong>Board thickness and component/package heights are unknown.</strong> This is a
        separate manufacturer reference, not the vehicle installation or a populated 3D CAD
        assembly.
      </p>
      <div className="highg-pcb-controls">
        <button type="button" onClick={() => view('fit')}>
          Fit board
        </button>
        <button type="button" onClick={() => view('top')}>
          View top (camera)
        </button>
        <button type="button" onClick={() => view('bottom')}>
          View bottom (camera)
        </button>
        <button type="button" onClick={() => view('selected')}>
          Zoom to selected
        </button>
        <button type="button" onClick={() => view('in')}>
          Zoom in
        </button>
        <button type="button" onClick={() => view('out')}>
          Zoom out
        </button>
      </div>
      <div className="highg-pcb-controls" aria-label="Source layer visibility shortcuts">
        <button
          type="button"
          onClick={() => {
            setTop(true);
            setBottom(false);
          }}
        >
          Show top layers only
        </button>
        <button
          type="button"
          onClick={() => {
            setTop(false);
            setBottom(true);
          }}
        >
          Show bottom layers only
        </button>
        <button
          type="button"
          onClick={() => {
            setTop(true);
            setBottom(true);
          }}
        >
          Restore both layers
        </button>
        <button type="button" onClick={resetReference}>
          Reset reference view
        </button>
      </div>
      <p className="highg-pcb-hint">
        Camera buttons turn the view; layer buttons control which source faces are visible. Source
        XY rulers use millimetres with 5 mm ticks and exact 25.4 × 17.78 mm end marks; they do not
        establish vehicle alignment or board thickness.
      </p>
      <div className="highg-pcb-controls">
        <label>
          <input type="checkbox" checked={top} onChange={(event) => setTop(event.target.checked)} />{' '}
          Top source layers
        </label>
        <label>
          <input
            type="checkbox"
            checked={bottom}
            onChange={(event) => setBottom(event.target.checked)}
          />{' '}
          Bottom source layers
        </label>
        <label>
          <input
            type="checkbox"
            checked={silk}
            onChange={(event) => setSilk(event.target.checked)}
          />{' '}
          Silk
        </label>
        <label>
          <input
            type="checkbox"
            checked={artwork}
            disabled={!silk}
            onChange={(event) => setArtwork(event.target.checked)}
          />{' '}
          Fine silk artwork
        </label>
        <label>
          <input
            type="checkbox"
            checked={documentation}
            onChange={(event) => setDocumentation(event.target.checked)}
          />{' '}
          Footprint outlines and pick points
        </label>
      </div>
      <label className="highg-pcb-spacing">
        Spread layers for visibility ·{' '}
        <strong>display spacing only, not actual Z or PCB thickness</strong>
        <input
          type="range"
          min="0"
          max="100"
          value={Math.round(separation * 100)}
          onChange={(event) => setSeparation(Number(event.target.value) / 100)}
        />
        <span>{Math.round(separation * 100)}%</span>
      </label>
      <div
        className="highg-pcb-canvas"
        role="group"
        aria-label="Orbitable manufacturer PCB source layer reference"
      >
        <Canvas
          orthographic
          frameloop="demand"
          dpr={[1, 2]}
          camera={{ position: [12.7, 8.89, 50], zoom: 18, near: 0.01, far: 200 }}
          gl={{ antialias: true }}
        >
          <BoardScene
            layout={layout}
            selected={selected}
            net={selectedNet}
            top={top}
            bottom={bottom}
            silk={silk}
            artwork={artwork}
            documentation={documentation}
            separation={separation}
            command={command}
            onSelectRef={selectFootprint}
            onSelectNet={setSelectedNet}
          />
        </Canvas>
      </div>
      <p className="highg-pcb-hint">
        Left drag: orbit · right drag: pan · wheel/pinch: zoom. Thin selection ring is a locator
        only. Bottom view is through the planar board source; no physical stack height is supplied.
      </p>
      <div className="highg-pcb-controls">
        <label>
          Source footprint{' '}
          <select value={selected.ref} onChange={(event) => selectFootprint(event.target.value)}>
            {layout.placements.map((placement) => (
              <option key={placement.ref} value={placement.ref}>
                {placement.ref} · {placement.package}
              </option>
            ))}
          </select>
        </label>
        <label>
          Highlight source net{' '}
          <select value={selectedNet} onChange={(event) => setSelectedNet(event.target.value)}>
            <option value="">All nets</option>
            {layout.nets.map((item) => (
              <option key={item.name} value={item.name}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <p>
        <strong>{selected.ref}</strong> · {selected.value || 'No source value'} · {selected.package}{' '}
        · {selected.side} · manufacturer XY {selected.position_mm.join(', ')} mm · rotation{' '}
        {selected.rotation_deg}°. Height unavailable.{' '}
        {selected.ref === 'U1'
          ? 'Official Eagle U1 value is ADXL343 in this ADXL375/PID5374 board file; incoming silicon identity is unverified.'
          : ''}
      </p>
      {!(selected.side === 'top' ? top : bottom) && (
        <p role="status">
          Selected {selected.side} placement is hidden by the current layer filter.
        </p>
      )}
      {footprintSummary && (
        <div className="highg-pcb-footprint-nets">
          <span>
            {selected.ref} source pads: {footprintSummary.padCount}; unassigned source pads:{' '}
            {footprintSummary.unassignedPadCount}. Connected nets:
          </span>{' '}
          {footprintSummary.nets.length ? (
            footprintSummary.nets.map((name) => (
              <button
                key={name}
                type="button"
                aria-pressed={selectedNet === name}
                onClick={() => setSelectedNet(name)}
              >
                {name}
              </button>
            ))
          ) : (
            <span>none recorded</span>
          )}
        </div>
      )}
      {netSummary && (
        <p>
          <strong>{selectedNet}</strong> source net: {netSummary.padCount} pads,{' '}
          {netSummary.traceCount} routed segments, {netSummary.viaCount} via drill locations.
          Contact refs: {netSummary.refs.join(', ') || 'none'}. This does not infer a poured copper
          plane or electrical test result.
        </p>
      )}
      <p>
        Source coverage: {layout.placements.length} placements · {layout.pads.length} pads ·{' '}
        {layout.traces.length} width-preserved routed traces · {layout.vias.length} via drills ·{' '}
        {layout.nets.length} nets. Via copper outer diameters and ground pour fill are unavailable;
        source boundary polygons are intentionally not rendered as filled copper. Silk/refdes text
        sits at recorded XY positions; browser glyphs are an approximation because Eagle glyph
        outlines are not supplied.
      </p>
      <p>
        Manufacturer board 25.4 × 17.78 mm, XY origin retained, +Y up. Product envelope 25.6 × 17.7
        × 4.6 mm is separately recorded and is not used as a board or component height. No vehicle
        datum, mating tolerance, mass/inertia or installed fit is derived here.
      </p>
      <p>
        Adafruit Industries / Limor Fried (Ladyada) ·{' '}
        <a href={layout.source.url} target="_blank" rel="noreferrer">
          official Eagle source
        </a>{' '}
        ·{' '}
        <a href={layout.license.url} target="_blank" rel="noreferrer">
          CC BY-SA 3.0 upstream notice
        </a>{' '}
        · source SHA-256 <code>{layout.source.sha256}</code>.
      </p>
    </section>
  );
}
