import { Component, Suspense, useEffect, useMemo, useRef, useState } from 'react';
import type { ComponentRef, ErrorInfo, ReactNode, RefObject } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { Grid, Html, OrbitControls, useGLTF } from '@react-three/drei';
import {
  Box3,
  Color,
  Group,
  Mesh,
  MeshStandardMaterial,
  PerspectiveCamera,
  Plane,
  Sphere,
  Vector3,
} from 'three';
import { useInspection } from '../store';
import { millimetres, partName } from '../format';
import type { InspectionDocument, JsonValue, MassSample, Part, Vector3Tuple } from '../types';
import { Icon } from './Icons';

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
  const translation = useMemo<Vector3Tuple>(() => {
    const center = new Box3().setFromObject(scene).getCenter(new Vector3());
    const offset = part.location?.explode_offset ?? part.explode_offset ?? 0;
    // Display-only explosion: GLB coordinates already contain the physical placement.
    // Spread relative to the assembly center; do not reapply the part's spec station.
    const radial = Math.hypot(center.x, center.z);
    return [
      radial > 0.003 ? center.x * 2.8 : 0,
      offset || (center.y - length / 2) * 0.65,
      radial > 0.003 ? center.z * 2.8 : 0,
    ];
  }, [scene, part.location?.explode_offset, part.explode_offset, length]);
  useEffect(() => {
    scene.traverse((object) => {
      if (!(object instanceof Mesh) || !(object.material instanceof MeshStandardMaterial)) return;
      object.material.color.set(
        analysisMode ? overlayColor || '#4d5b63' : part.color || part.cad?.color || '#899da5',
      );
      object.material.opacity = baseOpacity;
      object.material.transparent = baseOpacity < 1;
      object.material.depthWrite = baseOpacity >= 1;
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
      position={translation.map((coordinate) => coordinate * exploded) as Vector3Tuple}
      onClick={(event) => {
        event.stopPropagation();
        select(part.id);
      }}
      onPointerOver={(event) => {
        event.stopPropagation();
        hover(part.id);
        document.body.style.cursor = 'pointer';
      }}
      onPointerOut={() => {
        hover(null);
        document.body.style.cursor = '';
      }}
    >
      <primitive object={scene} />
    </group>
  );
}

function CameraFit({
  group,
  length,
  loadedToken,
}: {
  group: RefObject<Group | null>;
  length: number;
  loadedToken: number;
}) {
  const { camera, invalidate } = useThree();
  const controls = useRef<ComponentRef<typeof OrbitControls>>(null);
  const resetToken = useInspection((s) => s.resetToken);
  useEffect(() => {
    const bounds = group.current ? new Box3().setFromObject(group.current) : new Box3();
    const sphere = bounds.isEmpty()
      ? new Sphere(new Vector3(0, length / 2, 0), length / 2)
      : bounds.getBoundingSphere(new Sphere());
    const perspective = camera as PerspectiveCamera;
    const distance = (sphere.radius / Math.sin((perspective.fov * Math.PI) / 360)) * 1.18;
    camera.position
      .copy(sphere.center)
      .add(new Vector3(0.8, 0.24, 1.6).normalize().multiplyScalar(distance));
    camera.near = Math.max(0.001, sphere.radius / 100);
    camera.far = Math.max(100, distance * 20);
    camera.updateProjectionMatrix();
    controls.current?.target.copy(sphere.center);
    controls.current?.update();
    invalidate();
  }, [camera, group, length, loadedToken, resetToken, invalidate]);
  return (
    <OrbitControls
      ref={controls}
      makeDefault
      enableDamping
      dampingFactor={0.1}
      minDistance={0.03}
      maxDistance={20}
      screenSpacePanning
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
          <button onClick={resetCamera}>
            <Icon name="fit" />
            Fit rocket
          </button>
        </div>
        <div className="button-group">
          <button onClick={toggleSection} aria-pressed={section} title="Section cut (S)">
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
          <CameraFit group={group} length={overallLength} loadedToken={loadedIds.length} />
        </Canvas>
        <div className="viewport-scale">
          <span className="scale-line" />
          <span>{millimetres(overallLength)} overall · metre grid</span>
        </div>
        <div className="viewport-orientation">
          <b>Y</b>
          <span>↑ nose</span>
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
          <kbd>R</kbd> reset <kbd>S</kbd> section <kbd>esc</kbd> clear
        </span>
      </div>
    </section>
  );
}
