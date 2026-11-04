import { Component, Suspense, useEffect, useMemo, useRef, useState } from 'react';
import type { ComponentRef, ErrorInfo, ReactNode, RefObject } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { GizmoHelper, GizmoViewport, Grid, Html, OrbitControls, useGLTF } from '@react-three/drei';
import {
  Box3,
  Color,
  Group,
  Mesh,
  MeshStandardMaterial,
  PerspectiveCamera,
  Plane,
  Vector3,
} from 'three';
import { useInspection } from '../store';
import { millimetres, partName } from '../format';
import type { InspectionDocument, JsonValue, MassSample, Part, Vector3Tuple } from '../types';
import { Icon } from './Icons';
import { CAMERA_VIEWS, cameraFrame } from './inspectionGeometry';
import { fitOrbitFrame, isPointClipped } from './inspectionCamera';
import './inspectionViews.css';

export interface ViewOverlay {
  partColors: Record<string, string | null>;
  surface?: ReactNode;
  baseOpacity?: number;
  caption: string;
  legend?: { minimum: number; maximum: number; unit: string };
}

const CUT_PLANE = new Plane(new Vector3(-1, 0, 0), 0);
function scalar(value: JsonValue | undefined): number | undefined {
  return typeof value === 'number' ? value : undefined;
}
function outerBody(part: Part): boolean {
  if (
    typeof part.representation === 'object' &&
    part.representation &&
    !Array.isArray(part.representation) &&
    part.representation.outer_body === true
  )
    return true;
  return part.outer_body === true || /^(body_tube|airframe|body)$/.test(part.type);
}
function nose(part: Part): boolean {
  return part.nose === true || /nose/.test(part.type);
}

class MeshBoundary extends Component<
  { children: ReactNode; name: string; onError: (name: string) => void },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(_error: Error, _info: ErrorInfo) {
    this.props.onError(this.props.name);
  }
  render() {
    return this.state.failed ? null : this.props.children;
  }
}

function PartMesh({
  part,
  length,
  onLoaded,
  overlayColor,
  analysisMode = false,
  baseOpacity = 1,
}: {
  part: Part;
  length: number;
  onLoaded: (id: string) => void;
  overlayColor?: string | null;
  analysisMode?: boolean;
  baseOpacity?: number;
}) {
  const gltf = useGLTF(part.mesh_url!);
  const selected = useInspection((s) => s.selectedId === part.id);
  const hovered = useInspection((s) => s.hoveredId === part.id);
  const exploded = useInspection((s) => s.exploded);
  const section = useInspection((s) => s.section);
  const ghostShell = useInspection((s) => s.ghostShell);
  const wireframe = useInspection((s) => s.wireframe);
  const partLabels = useInspection((s) => s.partLabels);
  const select = useInspection((s) => s.select);
  const hover = useInspection((s) => s.hover);
  const scene = useMemo(() => {
    const copy = gltf.scene.clone(true);
    copy.traverse((object) => {
      if (object instanceof Mesh) {
        const color = part.color || part.cad?.color || '#899da5';
        object.material = new MeshStandardMaterial({
          color,
          roughness: 0.64,
          metalness: 0.12,
          side: 2,
        });
        object.castShadow = true;
        object.receiveShadow = true;
      }
    });
    return copy;
  }, [gltf.scene, part.color, part.cad?.color]);
  const bounds = useMemo(() => new Box3().setFromObject(scene), [scene]);
  const center = useMemo(() => bounds.getCenter(new Vector3()), [bounds]);
  const size = useMemo(() => bounds.getSize(new Vector3()), [bounds]);
  const ghost = !analysisMode && ghostShell && outerBody(part);
  const translation = useMemo<Vector3Tuple>(() => {
    const offset = part.location?.explode_offset ?? part.explode_offset ?? 0;
    // Display-only explosion: GLB coordinates already contain the physical placement.
    // Spread relative to the assembly center; do not reapply the part's spec station.
    const radial = Math.hypot(center.x, center.z);
    return [
      radial > 0.003 ? center.x * 2.8 : 0,
      offset || (center.y - length / 2) * 0.65,
      radial > 0.003 ? center.z * 2.8 : 0,
    ];
  }, [center, part.location?.explode_offset, part.explode_offset, length]);
  useEffect(() => {
    scene.traverse((object) => {
      if (!(object instanceof Mesh) || !(object.material instanceof MeshStandardMaterial)) return;
      object.material.color.set(
        analysisMode ? overlayColor || '#4d5b63' : part.color || part.cad?.color || '#899da5',
      );
      const opacity = ghost ? 0.14 : baseOpacity;
      object.material.opacity = opacity;
      object.material.transparent = opacity < 1;
      object.material.depthWrite = opacity >= 1;
      object.material.wireframe = !analysisMode && wireframe;
      object.material.emissive = new Color(
        analysisMode ? '#000000' : selected ? '#26b5ba' : hovered ? '#3b858b' : '#000000',
      );
      object.material.emissiveIntensity = selected ? 0.55 : 0.35;
      object.material.clippingPlanes = section ? [CUT_PLANE] : [];
      object.material.needsUpdate = true;
    });
  }, [
    scene,
    selected,
    hovered,
    section,
    analysisMode,
    overlayColor,
    baseOpacity,
    ghost,
    wireframe,
    part.color,
    part.cad?.color,
  ]);
  useEffect(() => {
    onLoaded(part.id);
    return () => {
      scene.traverse((object) => {
        if (object instanceof Mesh && object.material instanceof MeshStandardMaterial)
          object.material.dispose();
      });
    };
  }, [scene, part.id, onLoaded]);
  return (
    <group
      name={`inspection-part:${part.id}`}
      position={translation.map((coordinate) => coordinate * exploded) as Vector3Tuple}
      onClick={(event) => {
        if (ghost || isPointClipped(event.point, CUT_PLANE, section)) return;
        event.stopPropagation();
        select(part.id);
      }}
      onPointerOver={(event) => {
        if (ghost || isPointClipped(event.point, CUT_PLANE, section)) return;
        event.stopPropagation();
        hover(part.id);
        document.body.style.cursor = 'pointer';
      }}
      onPointerOut={() => {
        if (ghost) return;
        hover(null);
        document.body.style.cursor = '';
      }}
    >
      <primitive object={scene} />
      {!analysisMode && selected && partLabels && (
        <Html
          position={[center.x + size.x / 2 + 0.014, center.y, center.z]}
          zIndexRange={[12, 0]}
          className="selected-part-anchor"
        >
          <div className="selected-part-label">
            <span className="eyebrow">Selected part</span>
            <strong>{partName(part)}</strong>
            <span>{part.material}</span>
          </div>
        </Html>
      )}
    </group>
  );
}

type CameraCommand = { id: number; kind: 'fit' | 'zoom-in' | 'zoom-out' };

function CameraFit({
  group,
  length,
  complete,
  command,
}: {
  group: RefObject<Group | null>;
  length: number;
  complete: boolean;
  command: CameraCommand | null;
}) {
  const { camera, invalidate, size } = useThree();
  const controls = useRef<ComponentRef<typeof OrbitControls>>(null);
  const interacted = useRef(false);
  const initialComplete = useRef(false);
  const lastStoreCommand = useRef<number | null>(null);
  const pendingFocus = useRef<string | null>(null);
  const pendingFit = useRef(false);
  const resetToken = useInspection((s) => s.resetToken);
  const cameraAction = useInspection((s) => s.cameraAction);
  const view = useInspection((s) => s.cameraView);
  const focusId = useInspection((s) => s.focusId);

  function frame(mode: 'preset' | 'orbit', selectedId: string | null) {
    group.current?.updateWorldMatrix(true, true);
    const focused = selectedId
      ? group.current?.getObjectByName(`inspection-part:${selectedId}`)
      : null;
    // A hidden or unavailable selected mesh cannot be focused yet.
    if (selectedId && !focused) return false;
    const object = focused || group.current;
    const bounds = object ? new Box3().setFromObject(object) : new Box3();
    if (bounds.isEmpty()) bounds.set(new Vector3(0, 0, 0), new Vector3(0, length, 0));
    const perspective = camera as PerspectiveCamera;
    const aspect = size.width / Math.max(size.height, 1);
    const result =
      mode === 'preset'
        ? cameraFrame(
            { min: bounds.min.toArray(), max: bounds.max.toArray() },
            aspect,
            perspective.fov,
            view,
          )
        : fitOrbitFrame(
            bounds,
            aspect,
            perspective.fov,
            camera.position,
            controls.current?.target ?? new Vector3(),
            camera.up,
          );
    camera.up.fromArray(result.up);
    camera.position.fromArray(result.position);
    camera.near = Math.min(0.001, result.near);
    camera.far = Math.max(100, result.far);
    controls.current?.target.fromArray(result.target);
    camera.lookAt(new Vector3(...result.target));
    camera.updateProjectionMatrix();
    controls.current?.update();
    invalidate();
    return true;
  }

  useFrame(() => {
    if (pendingFocus.current && frame('orbit', pendingFocus.current)) pendingFocus.current = null;
  });

  // Store commands cover presets, keyboard reset and focus from the inspector.
  // Do not reframe on resize, selection changes, or each individual mesh load.
  useEffect(() => {
    // StrictMode repeats mount effects with the same token. Only a genuinely
    // new command suppresses the one initial fit after delayed meshes settle.
    if (lastStoreCommand.current !== null && lastStoreCommand.current !== resetToken)
      interacted.current = true;
    lastStoreCommand.current = resetToken;
    pendingFit.current = false;
    pendingFocus.current = cameraAction === 'focus' ? focusId : null;
    const mode = cameraAction === 'focus' || cameraAction === 'fit' ? 'orbit' : 'preset';
    if (frame(mode, pendingFocus.current)) pendingFocus.current = null;
    // This token intentionally identifies explicit store commands.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resetToken]);

  useEffect(() => {
    if (complete && !initialComplete.current) {
      initialComplete.current = true;
      if (!interacted.current) frame('preset', null);
    }
    if (complete && pendingFit.current) {
      pendingFit.current = false;
      frame('orbit', null);
    }
    // A single initial fit is allowed once all available meshes settle.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [complete]);

  useEffect(() => {
    if (!command) return;
    interacted.current = true;
    pendingFocus.current = null;
    pendingFit.current = false;
    if (command.kind === 'fit') {
      if (complete) frame('orbit', null);
      else pendingFit.current = true;
    } else {
      const target = controls.current?.target ?? new Vector3();
      const offset = camera.position.clone().sub(target);
      const distance = Math.min(
        20,
        Math.max(0.03, offset.length() * (command.kind === 'zoom-in' ? 0.8 : 1.25)),
      );
      camera.position.copy(target).add(offset.setLength(distance));
      controls.current?.update();
      invalidate();
    }
    // A command ID changes only for explicit toolbar actions.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [command]);

  return (
    <OrbitControls
      ref={controls}
      makeDefault
      enableDamping
      dampingFactor={0.1}
      minDistance={0.03}
      maxDistance={20}
      screenSpacePanning
      onStart={() => {
        interacted.current = true;
        pendingFocus.current = null;
        pendingFit.current = false;
      }}
    />
  );
}

function Markers({ length, mass }: { length: number; mass: MassSample | null }) {
  const markers = useInspection((s) => s.markers);
  const exploded = useInspection((s) => s.exploded);
  if (!markers || !mass || exploded > 0) return null;
  const cg = typeof mass.cg_m === 'number' ? mass.cg_m : undefined;
  const cp = mass.cp_m;
  return (
    <group>
      {cg != null && (
        <group position={[0.075, length - cg, 0]}>
          <mesh>
            <sphereGeometry args={[0.008, 20, 20]} />
            <meshBasicMaterial color="#55d5d3" depthTest={false} />
          </mesh>
          <Html position={[0.012, 0, 0]} center distanceFactor={1.8} zIndexRange={[10, 0]}>
            <div className="model-label cg-label">
              CG <span>balance point</span>
            </div>
          </Html>
        </group>
      )}
      {cp != null && (
        <group position={[0.075, length - cp, 0]}>
          <mesh>
            <sphereGeometry args={[0.009, 16, 12]} />
            <meshBasicMaterial color="#dce8ec" wireframe depthTest={false} />
          </mesh>
          <Html position={[0.012, 0, 0]} center distanceFactor={1.8} zIndexRange={[10, 0]}>
            <div className="model-label">
              CP <span>aerodynamic force point</span>
            </div>
          </Html>
        </group>
      )}
      {cg != null && cp != null && (
        <mesh position={[0.075, length - (cg + cp) / 2, 0]}>
          <cylinderGeometry args={[0.0007, 0.0007, Math.abs(cp - cg), 8]} />
          <meshBasicMaterial color="#718b94" depthTest={false} />
        </mesh>
      )}
    </group>
  );
}

export function Viewer({
  vehicle,
  mass,
  burn,
  onBurnChange,
  overlay,
}: {
  vehicle: InspectionDocument;
  mass: MassSample | null;
  burn: number;
  onBurnChange: (burn: number) => void;
  overlay?: ViewOverlay;
}) {
  const group = useRef<Group>(null);
  const [loadedIds, setLoadedIds] = useState<string[]>([]);
  const [meshErrors, setMeshErrors] = useState<string[]>([]);
  const [cameraCommand, setCameraCommand] = useState<CameraCommand | null>(null);
  const commandCamera = (kind: CameraCommand['kind']) =>
    setCameraCommand((previous) => ({ id: (previous?.id ?? 0) + 1, kind }));
  const exploded = useInspection((s) => s.exploded);
  const setExploded = useInspection((s) => s.setExploded);
  const section = useInspection((s) => s.section);
  const toggleSection = useInspection((s) => s.toggleSection);
  const markers = useInspection((s) => s.markers);
  const toggleMarkers = useInspection((s) => s.toggleMarkers);
  const hiddenIds = useInspection((s) => s.hiddenIds);
  const hideParts = useInspection((s) => s.hideParts);
  const showAll = useInspection((s) => s.showAll);
  const resetCamera = useInspection((s) => s.resetCamera);
  const focusPart = useInspection((s) => s.focusPart);
  const cameraView = useInspection((s) => s.cameraView);
  const setCameraView = useInspection((s) => s.setCameraView);
  const ghostShell = useInspection((s) => s.ghostShell);
  const toggleGhostShell = useInspection((s) => s.toggleGhostShell);
  const wireframe = useInspection((s) => s.wireframe);
  const toggleWireframe = useInspection((s) => s.toggleWireframe);
  const partLabels = useInspection((s) => s.partLabels);
  const togglePartLabels = useInspection((s) => s.togglePartLabels);
  const select = useInspection((s) => s.select);
  const selectedId = useInspection((s) => s.selectedId);
  const isolate = useInspection((s) => s.isolate);
  const length = scalar(vehicle.summary.length_m) || vehicle.geometry?.length_m || 1;
  const overallLength = scalar(vehicle.summary.overall_length_m) || length;
  const visible = vehicle.parts.filter((part) => !hiddenIds.includes(part.id));
  const unavailable = vehicle.parts.filter((part) => !part.mesh_url).length;
  const onLoaded = useMemo(
    () => (id: string) => setLoadedIds((ids) => (ids.includes(id) ? ids : [...ids, id])),
    [],
  );
  const onMeshError = useMemo(
    () => (name: string) => setMeshErrors((list) => (list.includes(name) ? list : [...list, name])),
    [],
  );
  const hasNose = vehicle.parts.some(nose);
  const hasShell = vehicle.parts.some(outerBody);
  const selectedPart = vehicle.parts.find((part) => part.id === selectedId);
  return (
    <section className="viewport-panel" aria-label="Three-dimensional vehicle inspection">
      <div className="viewport-heading">
        <div>
          <span className="eyebrow">
            {overlay ? 'Recorded result display' : 'Digital assembly'}
          </span>
          <h2>{overlay ? 'Engineering analysis' : 'Vehicle inspection'}</h2>
        </div>
        <span className="readonly-label">
          <span />
          Read only
        </span>
      </div>
      <div className="viewport-actions">
        <div className="button-group">
          <button onClick={resetCamera} title="Reset camera (R)">
            <Icon name="reset" />
            Reset view
          </button>
          <button onClick={() => commandCamera('zoom-in')} title="Zoom in">
            + Zoom in
          </button>
          <button onClick={() => commandCamera('zoom-out')} title="Zoom out">
            − Zoom out
          </button>
          <button
            onClick={() => commandCamera('fit')}
            title="Fit the currently visible parts, keeping this viewing angle"
          >
            <Icon name="fit" />
            Fit visible
          </button>
          <button
            onClick={() => {
              showAll();
              commandCamera('fit');
            }}
            title="Show all parts and fit the entire assembly, keeping this viewing angle"
          >
            Fit entire rocket
          </button>
          <button
            onClick={() => selectedId && focusPart(selectedId)}
            disabled={!selectedPart?.mesh_url}
            title="Move the camera close to the selected part (F)"
          >
            <Icon name="target" />
            Focus part
          </button>
        </div>
        <div className="button-group">
          <button
            onClick={toggleSection}
            aria-pressed={section}
            title="Section cut through the vehicle axis (S); select visible surfaces"
          >
            <Icon name="layers" />
            Section
          </button>
          {!overlay && (
            <button onClick={toggleMarkers} aria-pressed={markers}>
              <Icon name="target" />
              CG / CP
            </button>
          )}
        </div>
      </div>
      <div className="inspection-view-bar" aria-label="Inspection camera views">
        <span>View</span>
        {CAMERA_VIEWS.map((view) => (
          <button
            key={view.id}
            title={view.description}
            aria-pressed={cameraView === view.id}
            onClick={() => setCameraView(view.id)}
          >
            {view.label}
          </button>
        ))}
      </div>
      {!overlay && (
        <div className="inspection-display-bar" aria-label="Assembly display options">
          <button onClick={toggleGhostShell} aria-pressed={ghostShell} disabled={!hasShell}>
            <Icon name="layers" size={14} />
            Transparent shell
          </button>
          <button onClick={toggleWireframe} aria-pressed={wireframe}>
            <Icon name="cube" size={14} />
            Wireframe
          </button>
          <button onClick={togglePartLabels} aria-pressed={partLabels}>
            Selected-part label
          </button>
        </div>
      )}
      <div className="canvas-wrap">
        <Canvas
          fallback={
            <div className="canvas-loading">
              WebGL is unavailable. Use the parts tree to inspect the recorded specification.
            </div>
          }
          shadows
          dpr={[1, 2]}
          camera={{ position: [1.4, 0.9, 2.4], fov: 35, near: 0.001, far: 100 }}
          gl={{ antialias: true, localClippingEnabled: true }}
          onPointerMissed={() => select(null)}
        >
          <color attach="background" args={['#141c22']} />
          <ambientLight intensity={1.25} />
          <hemisphereLight args={['#dbeaf0', '#23313d', 0.65]} />
          <directionalLight position={[2, 3, 3]} intensity={2.5} />
          <directionalLight position={[-2, 1, -1]} intensity={1.2} color="#66a3b8" />
          <Grid
            position={[0, -0.015, 0]}
            args={[4, 4]}
            cellSize={0.1}
            sectionSize={1}
            cellColor="#23343e"
            sectionColor="#3a505c"
            cellThickness={0.5}
            sectionThickness={0.8}
            fadeDistance={5}
            fadeStrength={2}
            infiniteGrid
          />
          <group ref={group}>
            {visible
              .filter((part) => part.mesh_url)
              .map((part) => (
                <MeshBoundary key={part.id} name={partName(part)} onError={onMeshError}>
                  <Suspense fallback={null}>
                    <PartMesh
                      part={part}
                      length={length}
                      onLoaded={onLoaded}
                      analysisMode={!!overlay}
                      overlayColor={overlay?.partColors[part.id]}
                      baseOpacity={overlay?.baseOpacity}
                    />
                  </Suspense>
                </MeshBoundary>
              ))}
            {overlay?.surface}
          </group>
          {!overlay && <Markers length={length} mass={mass} />}
          <CameraFit
            group={group}
            length={overallLength}
            complete={visible.every(
              (part) =>
                !part.mesh_url ||
                loadedIds.includes(part.id) ||
                meshErrors.includes(partName(part)),
            )}
            command={cameraCommand}
          />
          <GizmoHelper alignment="bottom-right" margin={[65, 65]}>
            <GizmoViewport
              disabled
              axisColors={['#bc6c68', '#69b7aa', '#719dbd']}
              labelColor="#15212a"
            />
          </GizmoHelper>
        </Canvas>
        <div className="viewport-scale">
          <span className="scale-line" />
          <span>{millimetres(overallLength)} overall · metre grid</span>
        </div>
        <div className="viewport-orientation">
          <b>Y</b>
          <span>axis toward nose</span>
          <small>Metres · placed CAD geometry</small>
        </div>
        {overlay && (
          <div className="field-legend">
            <strong>{overlay.caption}</strong>
            {overlay.legend && (
              <>
                <div className="color-gradient" />
                <div className="legend-values">
                  <span>
                    {overlay.legend.minimum} {overlay.legend.unit}
                  </span>
                  <span>
                    {overlay.legend.maximum} {overlay.legend.unit}
                  </span>
                </div>
              </>
            )}
            <span className="unavailable-key">
              <i />
              Neutral grey = unavailable / outside field coverage
            </span>
          </div>
        )}
        {!overlay && (ghostShell || wireframe) && (
          <div className="inspection-display-note" role="status">
            {ghostShell && <span>Transparent shell: select internal parts through the body.</span>}
            {wireframe && (
              <span>Wireframe shows display triangles, not a stress-analysis mesh.</span>
            )}
          </div>
        )}
        {visible.some(
          (part) =>
            part.mesh_url && !loadedIds.includes(part.id) && !meshErrors.includes(partName(part)),
        ) && (
          <div className={`canvas-loading ${loadedIds.length ? 'mesh-progress' : ''}`}>
            <span className="spinner" />
            Loading CAD-derived part meshes… {loadedIds.length}/
            {vehicle.parts.filter((part) => part.mesh_url).length}
          </div>
        )}
        {visible.length === 0 && (
          <div className="canvas-loading" role="status">
            All parts are hidden. Use Show all to restore the assembly.
          </div>
        )}
        {visible.length > 0 && visible.every((part) => !part.mesh_url) && (
          <div className="canvas-loading" role="status">
            No 3D meshes are available for the visible parts. Use the parts tree to inspect their
            recorded specifications.
          </div>
        )}
        {(meshErrors.length > 0 || unavailable > 0) && (
          <div className="mesh-warning" role="status">
            <Icon name="warning" />
            {meshErrors.length > 0
              ? `${meshErrors.length} mesh load failure${meshErrors.length > 1 ? 's' : ''}: ${meshErrors.join(', ')}`
              : `${unavailable} part meshes unavailable`}
            . Parts remain inspectable in the tree.
          </div>
        )}
      </div>
      <div className="visibility-toolbar">
        <button
          onClick={() =>
            hideParts(
              vehicle.parts.filter((part) => outerBody(part) && !nose(part)).map((part) => part.id),
            )
          }
        >
          <Icon name="eyeOff" size={14} />
          Hide outer body
        </button>
        {hasNose && (
          <button onClick={() => hideParts(vehicle.parts.filter(nose).map((part) => part.id))}>
            Hide nose
          </button>
        )}
        <button onClick={showAll} disabled={!hiddenIds.length}>
          Show all
        </button>
        {selectedId && (
          <button
            onClick={() =>
              isolate(
                selectedId,
                vehicle.parts.map((part) => part.id),
              )
            }
          >
            Isolate selected
          </button>
        )}
      </div>
      {!overlay && (
        <div className="viewport-controls">
          <label className="slider-control">
            <span>
              Exploded view <small>{Math.round(exploded * 100)}%</small>
            </span>
            <input
              aria-label="Exploded view"
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={exploded}
              onChange={(event) => setExploded(Number(event.target.value))}
            />
            <span className="slider-labels">
              <small>Assembled</small>
              <small>Exploded</small>
            </span>
          </label>
          <label className="slider-control burn-control">
            <span>
              Propellant consumed <small>{Math.round(burn * 100)}%</small>
            </span>
            <input
              aria-label="Propellant consumed"
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={burn}
              onChange={(event) => onBurnChange(Number(event.target.value))}
            />
            <span className="slider-labels">
              <small>Ignition</small>
              <small>Burnout</small>
            </span>
          </label>
        </div>
      )}
      <div className="viewport-help">
        <span>Drag to orbit · scroll to zoom · right-drag to pan</span>
        <span>
          {!overlay && (
            <>
              <kbd>E</kbd> explode
            </>
          )}
          <kbd>F</kbd> focus <kbd>R</kbd> reset <kbd>S</kbd> section <kbd>esc</kbd> clear
        </span>
      </div>
    </section>
  );
}
