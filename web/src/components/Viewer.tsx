import { Component, Suspense, useEffect, useMemo, useRef, useState } from 'react';
import type { ErrorInfo, ReactNode, RefObject } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { GizmoHelper, GizmoViewport, Grid, useGLTF } from '@react-three/drei';
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
import {
  consumeMainCamera,
  mainCameraKey,
  registerMainCamera,
} from '../fin-attachment/mainCameraCheckpoint';
import { millimetres, partName } from '../format';
import type { InspectionDocument, JsonValue, MassSample, Part, Vector3Tuple } from '../types';
import { Icon } from './Icons';
import { SceneLabel } from './SceneLabel';
import {
  applyOrbit,
  bindInspectionOrbit,
  inspectionMaterial,
  inspectionFitScope,
  inspectionNormals,
  orbitAngles,
  orbitClips,
  panOrbit,
} from './inspectionOrbit';
import type { OrbitAngles, OrbitReadout } from './inspectionOrbit';
import { OrbitCameraControls } from './OrbitCameraControls';
import { getRp1Presentation, rp1BreakdownOffset } from './rp1Breakdown';
import { CAMERA_VIEWS, cameraFrame } from './inspectionGeometry';
import { fitOrbitFrame, inspectionFrameInsets, isPointClipped } from './inspectionCamera';
import { inspectionSceneBounds } from './inspectionSceneBounds';
import type { RecordedMeshBounds } from './inspectionSceneBounds';
import { InspectionTools } from '../workspaces/InspectionWorkspace';
import { useWorkspaceLayout } from '../workspaces/workspaceLayoutContext';
import './inspectionViews.css';
import { InspectionDisplayReadout } from './InspectionDisplayReadout';
import { restoreAssembledInspection } from './inspectionDisplay';
import {
  inspectionGeometryPresentation,
  inspectionPartRepresentation,
} from '../workspaces/inspectionWorkflow';
import './revampViewer.css';
import { SectionPlaneControls } from './SectionPlaneControls';
import { SourceDimensionOverlay } from './SourceDimensionOverlay';
import type { Rp1DetailAnnotation } from './rp1Detail';
import { DEFAULT_SECTION, inspectionSectionPlane, sectionDimensions } from './inspectionSection';
import type { SectionSettings } from './inspectionSection';

export interface ViewOverlay {
  partColors: Record<string, string | null>;
  surface?: ReactNode;
  baseOpacity?: number;
  caption: string;
  legend?: { minimum: number; maximum: number; unit: string };
}

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
  groupHighlighted = false,
  displayOffset,
  displayMeshUrl,
  cutPlane,
}: {
  part: Part;
  length: number;
  onLoaded: (
    id: string,
    bounds: Box3,
    explodeOffset: Vector3Tuple,
    displayOffset?: Vector3Tuple,
  ) => void;
  overlayColor?: string | null;
  analysisMode?: boolean;
  baseOpacity?: number;
  groupHighlighted?: boolean;
  displayOffset?: Vector3Tuple;
  displayMeshUrl?: string;
  cutPlane: Plane;
}) {
  const gltf = useGLTF(displayMeshUrl ?? part.mesh_url!);
  const invalidate = useThree((state) => state.invalidate);
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
        const makeMaterial = (source: unknown) =>
          inspectionMaterial(source, part.material, color, !!displayMeshUrl);
        object.material = Array.isArray(object.material)
          ? object.material.map(makeMaterial)
          : makeMaterial(object.material);
        const normals = inspectionNormals(object.geometry);
        object.geometry = normals.geometry;
        object.userData.inspectionOwnedGeometry = normals.owned;
        object.castShadow = true;
        object.receiveShadow = true;
      }
    });
    return copy;
  }, [gltf.scene, part.color, part.cad?.color, part.material, displayMeshUrl]);
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
      if (!(object instanceof Mesh)) return;
      for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
        if (!(material instanceof MeshStandardMaterial)) continue;
        material.color.set(
          analysisMode
            ? overlayColor || '#4d5b63'
            : (material.userData.inspectionBaseColor ?? part.color ?? part.cad?.color ?? '#899da5'),
        );
        const opacity = ghost ? 0.14 : baseOpacity;
        material.opacity = opacity;
        material.transparent = opacity < 1;
        material.depthWrite = opacity >= 1;
        material.wireframe = !analysisMode && wireframe;
        material.emissive = new Color(
          analysisMode
            ? '#000000'
            : selected || groupHighlighted
              ? '#26b5ba'
              : hovered
                ? '#3b858b'
                : '#000000',
        );
        material.emissiveIntensity = selected ? 0.16 : groupHighlighted ? 0.1 : hovered ? 0.08 : 0;
        material.clippingPlanes = section ? [cutPlane] : [];
        material.needsUpdate = true;
      }
    });
    invalidate();
  }, [
    scene,
    invalidate,
    selected,
    groupHighlighted,
    hovered,
    section,
    cutPlane,
    analysisMode,
    overlayColor,
    baseOpacity,
    ghost,
    wireframe,
    part.color,
    part.cad?.color,
  ]);
  useEffect(() => {
    onLoaded(part.id, bounds, translation, displayOffset);
  }, [part.id, onLoaded, bounds, translation, displayOffset]);
  useEffect(() => {
    return () => {
      scene.traverse((object) => {
        if (object instanceof Mesh) {
          for (const material of Array.isArray(object.material)
            ? object.material
            : [object.material])
            material.dispose();
          if (object.userData.inspectionOwnedGeometry) object.geometry.dispose();
        }
      });
    };
  }, [scene]);
  return (
    <group
      name={`inspection-part:${part.id}`}
      position={
        displayOffset ?? (translation.map((coordinate) => coordinate * exploded) as Vector3Tuple)
      }
      onClick={(event) => {
        if (event.delta > 2 || ghost || isPointClipped(event.point, cutPlane, section)) return;
        event.stopPropagation();
        select(part.id);
      }}
      onPointerOver={(event) => {
        if (ghost || isPointClipped(event.point, cutPlane, section)) return;
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
        <SceneLabel
          position={[center.x + size.x / 2 + 0.014, center.y, center.z]}
          zIndexRange={[12, 0]}
          className="selected-part-anchor"
          contentClassName="selected-part-label"
          lines={[
            { text: 'Selected part', className: 'eyebrow' },
            { text: partName(part), tag: 'strong' },
            { text: part.material },
            { text: inspectionPartRepresentation(part).label },
          ]}
        />
      )}
    </group>
  );
}

type CameraCommand = {
  id: number;
  kind:
    | 'fit'
    | 'fit-assembly'
    | 'frame-selection'
    | 'zoom-in'
    | 'zoom-out'
    | 'angles'
    | 'target-assembly'
    | 'target-selection'
    | 'pan-left'
    | 'pan-right'
    | 'pan-up'
    | 'pan-down';
  angles?: OrbitAngles;
};
function CameraFit({
  checkpointKey,
  group,
  length,
  complete,
  command,
  meshBounds,
  allIds,
  visibleIds,
  selectionIds,
  selectionLabel,
  groupSelected,
  presentationGroupId,
  dragMode,
  exploded,
  onStatus,
  onReadout,
}: {
  checkpointKey: string;
  group: RefObject<Group | null>;
  length: number;
  complete: boolean;
  command: CameraCommand | null;
  meshBounds: RefObject<Map<string, RecordedMeshBounds>>;
  allIds: string[];
  visibleIds: string[];
  selectionIds: string[];
  selectionLabel: string;
  groupSelected: boolean;
  presentationGroupId: string | null;
  dragMode: 'orbit' | 'pan';
  exploded: number;
  onStatus: (value: string) => void;
  onReadout: (value: OrbitReadout) => void;
}) {
  const { camera: rawCamera, gl, invalidate, size } = useThree();
  const camera = rawCamera as PerspectiveCamera;
  const target = useRef(new Vector3());
  const [restoredPose] = useState(() => consumeMainCamera(checkpointKey));
  const angles = useRef<OrbitAngles>({ azimuth: 45, tilt: 54.7356, roll: 0 });
  const mode = useRef('Overview');
  const targetScope = useRef<'assembly' | 'selection'>('assembly');
  const targetLabel = useRef('Assembly');
  const scopeCenter = useRef<Vector3 | null>(null);
  const interacted = useRef(false),
    initialComplete = useRef(false),
    pendingFit = useRef(false),
    assemblyFit = useRef(false);
  const lastStoreCommand = useRef<number | null>(null);
  const pendingFocus = useRef<string[] | null>(null),
    framedPart = useRef<string[] | null>(null);
  const intent = useRef<'preset' | 'fit' | 'part' | 'manual'>('preset');
  const resetToken = useInspection((s) => s.resetToken),
    cameraAction = useInspection((s) => s.cameraAction);
  const view = useInspection((s) => s.cameraView),
    focusId = useInspection((s) => s.focusId);
  function publish() {
    angles.current = orbitAngles(camera, target.current, angles.current.azimuth);
    onReadout({
      ...angles.current,
      mode: mode.current,
      target: targetScope.current,
      targetLabel: targetLabel.current,
    });
  }
  function safeClips() {
    const scope = inspectionSceneBounds(meshBounds.current, visibleIds, exploded);
    const clips = orbitClips(scope.bounds, camera, target.current);
    camera.near = clips.near;
    camera.far = clips.far;
    camera.updateProjectionMatrix();
  }
  function moved() {
    safeClips();
    publish();
    invalidate();
  }
  function manual() {
    interacted.current = true;
    intent.current = 'manual';
    mode.current = 'Custom';
    pendingFocus.current = null;
    pendingFit.current = false;
  }
  function frame(strategy: 'preset' | 'orbit', selected: string[] | null) {
    if (size.width <= 0 || size.height <= 0) {
      onStatus('Waiting for a visible canvas before framing loaded geometry.');
      return false;
    }
    group.current?.updateWorldMatrix(true, true);
    const ids = selected ?? (assemblyFit.current ? allIds : visibleIds);
    const scope = inspectionSceneBounds(meshBounds.current, ids, exploded);
    if (scope.bounds.isEmpty()) {
      onStatus('No loaded mesh bounds for this view; source properties and 2D remain available.');
      return false;
    }
    const aspect = size.width / Math.max(size.height, 1);
    const preset =
      strategy === 'preset'
        ? cameraFrame(
            { min: scope.bounds.min.toArray(), max: scope.bounds.max.toArray() },
            aspect,
            camera.fov,
            view,
          )
        : null;
    const result = fitOrbitFrame(
      scope.bounds,
      aspect,
      camera.fov,
      preset ? new Vector3(...preset.position) : camera.position,
      preset ? new Vector3(...preset.target) : target.current,
      preset ? new Vector3(...preset.up) : camera.up,
      {
        fill: selected || view === 'aft' ? 0.78 : 0.85,
        insets: inspectionFrameInsets(size.width, size.height),
      },
    );
    camera.up.fromArray(result.up);
    camera.position.fromArray(result.position);
    target.current.fromArray(result.target);
    camera.near = result.near;
    camera.far = result.far;
    camera.lookAt(target.current);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld();
    if (strategy === 'preset')
      mode.current = CAMERA_VIEWS.find((item) => item.id === view)?.label ?? view;
    targetScope.current = selected ? 'selection' : 'assembly';
    targetLabel.current = selected ? selectionLabel : 'Assembly';
    scopeCenter.current = scope.bounds.getCenter(new Vector3());
    publish();
    invalidate();
    initialComplete.current = true;
    onStatus(
      `${scope.available}/${scope.requested} loaded part bounds fitted${useInspection.getState().section ? ' · conservative full-part boxes; section cut does not tighten the fit' : ''}${scope.available < scope.requested ? ' · incomplete geometry' : ''}.`,
    );
    return true;
  }
  useFrame(() => {
    if (pendingFocus.current && frame('orbit', pendingFocus.current)) pendingFocus.current = null;
  });
  useEffect(() => {
    const saved = restoredPose;
    if (saved) {
      camera.position.fromArray(saved.position);
      camera.up.fromArray(saved.up);
      target.current.fromArray(saved.target);
      camera.lookAt(target.current);
      camera.updateMatrixWorld();
      initialComplete.current = true;
      interacted.current = true;
      intent.current = 'manual';
      targetScope.current = saved.targetScope ?? 'assembly';
      targetLabel.current = saved.targetLabel ?? 'Assembly';
      mode.current = 'Restored rocket view';
      safeClips();
      invalidate();
    }
    return registerMainCamera(checkpointKey, () => ({
      position: camera.position.toArray(),
      up: camera.up.toArray(),
      target: target.current.toArray(),
      targetScope: targetScope.current,
      targetLabel: targetLabel.current,
    }));
    // Capture the actual camera and orbit target, not a reconstructed readout.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [checkpointKey, camera]);
  useEffect(() => {
    publish();
    // Initialize readout from the actual configured camera even while meshes are delayed.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [camera]);
  useEffect(() => {
    if (lastStoreCommand.current === null && restoredPose) {
      lastStoreCommand.current = resetToken;
      publish();
      return;
    }
    if (lastStoreCommand.current !== null && lastStoreCommand.current !== resetToken)
      interacted.current = true;
    lastStoreCommand.current = resetToken;
    pendingFit.current = false;
    pendingFocus.current =
      cameraAction === 'focus' && focusId
        ? [focusId]
        : cameraAction === 'fit'
          ? inspectionFitScope(groupSelected, targetScope.current, selectionIds)
          : null;
    assemblyFit.current = cameraAction === 'reset';
    intent.current = cameraAction === 'focus' ? 'part' : cameraAction === 'fit' ? 'fit' : 'preset';
    framedPart.current = pendingFocus.current;
    if (
      frame(
        cameraAction === 'focus' || cameraAction === 'fit' ? 'orbit' : 'preset',
        pendingFocus.current,
      )
    )
      pendingFocus.current = null;
    // Explicit store token only; selection/panel changes never reset the camera.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resetToken]);
  useEffect(() => {
    if (complete && !initialComplete.current && !interacted.current) frame('preset', null);
    if (complete && pendingFit.current) {
      pendingFit.current = false;
      frame('orbit', framedPart.current);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [complete]);
  useEffect(() => {
    if (!command) return;
    interacted.current = true;
    pendingFocus.current = null;
    pendingFit.current = false;
    if (
      command.kind === 'fit' ||
      command.kind === 'fit-assembly' ||
      command.kind === 'frame-selection'
    ) {
      assemblyFit.current = command.kind === 'fit-assembly';
      framedPart.current = command.kind === 'frame-selection' ? selectionIds : null;
      intent.current = 'fit';
      if (complete) frame('orbit', framedPart.current);
      else pendingFit.current = true;
    } else if (command.kind === 'target-assembly' || command.kind === 'target-selection') {
      const ids = command.kind === 'target-selection' ? selectionIds : allIds;
      const scope = inspectionSceneBounds(meshBounds.current, ids, exploded);
      if (scope.bounds.isEmpty()) {
        onStatus('Orbit target has no loaded geometry; the current camera is retained.');
        return;
      }
      const distance = camera.position.distanceTo(target.current);
      target.current.copy(scope.bounds.getCenter(new Vector3()));
      scopeCenter.current = target.current.clone();
      targetScope.current = command.kind === 'target-selection' ? 'selection' : 'assembly';
      targetLabel.current = command.kind === 'target-selection' ? selectionLabel : 'Assembly';
      applyOrbit(camera, target.current, distance, angles.current);
      manual();
      moved();
    } else if (command.kind.startsWith('pan-')) {
      manual();
      panOrbit(
        target.current,
        camera,
        command.kind === 'pan-left' ? -40 : command.kind === 'pan-right' ? 40 : 0,
        command.kind === 'pan-up' ? -40 : command.kind === 'pan-down' ? 40 : 0,
        size.height,
      );
      moved();
    } else {
      manual();
      const distance = Math.max(
        0.000001,
        Math.min(
          Math.max(20, length * 20),
          camera.position.distanceTo(target.current) *
            (command.kind === 'zoom-in' ? 0.8 : command.kind === 'zoom-out' ? 1.25 : 1),
        ),
      );
      if (command.angles) angles.current = command.angles;
      applyOrbit(camera, target.current, distance, angles.current);
      moved();
    }
    // A command changes only through explicit viewport controls.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [command]);
  useEffect(() => {
    if (!initialComplete.current || intent.current === 'manual') return;
    frame(intent.current === 'preset' ? 'preset' : 'orbit', framedPart.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [size.width, size.height]);
  const selectionKey = selectionIds.join('|');
  useEffect(() => {
    if (!initialComplete.current) return;
    if (targetScope.current === 'selection' && selectionIds.length) {
      const scope = inspectionSceneBounds(meshBounds.current, selectionIds, exploded);
      if (!scope.bounds.isEmpty()) {
        const next = scope.bounds.getCenter(new Vector3());
        const shift = next.clone().sub(scopeCenter.current ?? next);
        camera.position.add(shift);
        target.current.add(shift);
        scopeCenter.current = next;
        targetLabel.current = selectionLabel;
        framedPart.current = selectionIds;
      }
    }
    moved();
    // Display transforms and a changed selection update the pivot without resetting its angle.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [exploded, presentationGroupId, selectionKey]);
  const handlers = useRef({
    begin: () => {},
    move: (_dx: number, _dy: number, _kind: string) => {},
    zoom: (_factor: number) => {},
  });
  useEffect(() => {
    handlers.current = {
      begin() {
        interacted.current = true;
        intent.current = 'manual';
        pendingFocus.current = null;
        pendingFit.current = false;
      },
      move(dx, dy, kind) {
        manual();
        if (kind === 'pan') panOrbit(target.current, camera, dx, dy, size.height);
        else {
          angles.current = {
            ...angles.current,
            ...(kind === 'roll'
              ? { roll: angles.current.roll + dx * 0.4 }
              : {
                  azimuth: angles.current.azimuth - dx * 0.4,
                  tilt: Math.max(0, Math.min(180, angles.current.tilt - dy * 0.4)),
                }),
          };
          applyOrbit(
            camera,
            target.current,
            camera.position.distanceTo(target.current),
            angles.current,
          );
        }
        moved();
      },
      zoom(factor) {
        manual();
        const distance = Math.max(
          0.000001,
          Math.min(Math.max(20, length * 20), camera.position.distanceTo(target.current) * factor),
        );
        applyOrbit(camera, target.current, distance, angles.current);
        moved();
      },
    };
  });
  useEffect(
    () =>
      bindInspectionOrbit(
        gl.domElement,
        {
          dragMode: () => dragMode,
          begin: () => handlers.current.begin(),
          move: (dx, dy, kind) => handlers.current.move(dx, dy, kind),
          zoom: (factor) => handlers.current.zoom(factor),
        },
        () => gl.domElement.clientHeight,
      ),
    [gl, dragMode],
  );
  return null;
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
          <SceneLabel
            position={[0.012, 0, 0]}
            center
            distanceFactor={1.8}
            zIndexRange={[10, 0]}
            contentClassName="model-label cg-label"
            title={mass.recorded_case_label}
            text="CG"
            lines={[
              { text: `balance point${mass.recorded_case_label ? ' · saved estimate' : ''}` },
            ]}
          />
        </group>
      )}
      {cp != null && (
        <group position={[0.075, length - cp, 0]}>
          <mesh>
            <sphereGeometry args={[0.009, 16, 12]} />
            <meshBasicMaterial color="#dce8ec" wireframe depthTest={false} />
          </mesh>
          <SceneLabel
            position={[0.012, 0, 0]}
            center
            distanceFactor={1.8}
            zIndexRange={[10, 0]}
            contentClassName="model-label"
            text="CP"
            lines={[
              {
                text: `aerodynamic force point${mass.recorded_case_label ? ' · saved estimate' : ''}`,
              },
            ]}
          />
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
  presentationVisual,
  detailMeshes,
  detailAnnotations,
  selectionIds: suppliedSelectionIds,
  presentationGroupId = null,
}: {
  vehicle: InspectionDocument;
  mass: MassSample | null;
  burn: number;
  onBurnChange: (burn: number) => void;
  overlay?: ViewOverlay;
  presentationVisual?: ReactNode;
  detailMeshes?: Record<string, string>;
  detailAnnotations?: readonly Rp1DetailAnnotation[];
  selectionIds?: string[];
  presentationGroupId?: string | null;
}) {
  const group = useRef<Group>(null);
  const meshBounds = useRef(new Map<string, RecordedMeshBounds>());
  const [fitStatus, setFitStatus] = useState('Waiting for actual component mesh bounds.');
  const layout = useWorkspaceLayout();
  const [loadedIds, setLoadedIds] = useState<string[]>([]);
  const [meshErrors, setMeshErrors] = useState<string[]>([]);
  const [dragMode, setDragMode] = useState<'orbit' | 'pan'>('pan');
  const [cameraCommand, setCameraCommand] = useState<CameraCommand | null>(null);
  const [cameraReadout, setCameraReadout] = useState<OrbitReadout>({
    azimuth: 45,
    tilt: 54.7356,
    roll: 0,
    mode: 'Overview',
    target: 'assembly',
  });
  const [framingGuide, setFramingGuide] = useState(false);
  const [canvasElement, setCanvasElement] = useState<HTMLDivElement | null>(null);
  const [canvasSize, setCanvasSize] = useState({ width: 0, height: 0 });
  useEffect(() => {
    if (!canvasElement) return;
    const observer = new ResizeObserver(([entry]) => {
      const { width, height } = entry.contentRect;
      setCanvasSize((previous) =>
        previous.width === width && previous.height === height ? previous : { width, height },
      );
    });
    observer.observe(canvasElement);
    return () => observer.disconnect();
  }, [canvasElement]);
  const guideInsets = inspectionFrameInsets(canvasSize.width, canvasSize.height);
  const commandCamera = (kind: CameraCommand['kind']) =>
    setCameraCommand((previous) => ({ id: (previous?.id ?? 0) + 1, kind }));
  const exploded = useInspection((s) => s.exploded);
  const setExploded = useInspection((s) => s.setExploded);
  const section = useInspection((s) => s.section);
  const toggleSection = useInspection((s) => s.toggleSection);
  const sectionDims = useMemo(() => sectionDimensions(vehicle), [vehicle]);
  const sectionSource = JSON.stringify([vehicle.id, vehicle.identity, sectionDims]);
  const [sectionState, setSectionState] = useState<{
    source: string;
    value: SectionSettings;
  } | null>(null);
  const sectionSettings =
    sectionState?.source === sectionSource ? sectionState.value : DEFAULT_SECTION;
  const cutPlane = useMemo(
    () => inspectionSectionPlane(sectionSettings, sectionDims),
    [sectionSettings, sectionDims],
  );

  const markers = useInspection((s) => s.markers);
  const toggleMarkers = useInspection((s) => s.toggleMarkers);
  const hiddenIds = useInspection((s) => s.hiddenIds);
  const hideParts = useInspection((s) => s.hideParts);
  const showAll = useInspection((s) => s.showAll);
  const resetCamera = useInspection((s) => s.resetCamera);
  const setCameraView = useInspection((s) => s.setCameraView);
  const ghostShell = useInspection((s) => s.ghostShell);
  const toggleGhostShell = useInspection((s) => s.toggleGhostShell);
  const wireframe = useInspection((s) => s.wireframe);
  const toggleWireframe = useInspection((s) => s.toggleWireframe);
  const partLabels = useInspection((s) => s.partLabels);
  const togglePartLabels = useInspection((s) => s.togglePartLabels);
  const selectedId = useInspection((s) => s.selectedId);
  const isolate = useInspection((s) => s.isolate);
  const exitIsolate = useInspection((s) => s.exitIsolate);
  const isolatedFrom = useInspection((s) => s.isolatedFrom);
  const length = scalar(vehicle.summary.length_m) || vehicle.geometry?.length_m || 1;
  const geometry = inspectionGeometryPresentation(vehicle);
  const presentation = useMemo(() => getRp1Presentation(vehicle), [vehicle]);
  const openedGroupLabel = presentation?.groups.find(
    (item) => item.id === presentationGroupId,
  )?.label;
  const overallLength = scalar(vehicle.summary.overall_length_m) || length;
  const displayOffsets = useMemo(
    () =>
      new Map(
        vehicle.parts.map((part) => [
          part.id,
          rp1BreakdownOffset(vehicle, part.id, exploded, presentationGroupId),
        ]),
      ),
    [vehicle, exploded, presentationGroupId],
  );
  const visible = vehicle.parts.filter((part) => !hiddenIds.includes(part.id));
  const unavailable = vehicle.parts.filter((part) => !part.mesh_url).length;
  const onLoaded = useMemo(
    () => (id: string, bounds: Box3, explodeOffset: Vector3Tuple, displayOffset?: Vector3Tuple) => {
      meshBounds.current.set(id, { bounds: bounds.clone(), explodeOffset, displayOffset });
      setLoadedIds((ids) => (ids.includes(id) ? ids : [...ids, id]));
    },
    [],
  );
  const onMeshError = useMemo(
    () => (name: string) => setMeshErrors((list) => (list.includes(name) ? list : [...list, name])),
    [],
  );
  const hasNose = vehicle.parts.some(nose);
  const hasShell = vehicle.parts.some(outerBody);
  const selectedPart = vehicle.parts.find((part) => part.id === selectedId);
  const cameraSelectionIds = (suppliedSelectionIds ?? (selectedId ? [selectedId] : [])).filter(
    (id) => vehicle.parts.some((part) => part.id === id && part.mesh_url),
  );
  const [dimensionId, setDimensionId] = useState('off');
  const selectedDimensions = (detailAnnotations ?? []).filter(
    (a) => cameraSelectionIds.includes(a.partId) && !hiddenIds.includes(a.partId),
  );
  const activeDimension = selectedDimensions.find((a) => a.id === dimensionId);
  const statusInTools = !!layout && !overlay;
  const fitReadout = (
    <p className="revamp-fit-status" role="status">
      {fitStatus}
    </p>
  );
  const meshWarning = (meshErrors.length > 0 || unavailable > 0) && (
    <div className="mesh-warning" role="status">
      <Icon name="warning" />
      {meshErrors.length > 0
        ? `${meshErrors.length} mesh load failure${meshErrors.length > 1 ? 's' : ''}: ${meshErrors.join(', ')}`
        : geometry.sourceDerived
          ? `${unavailable} source records have no solid: ${geometry.counts.mass_allowance} mass allowances, ${geometry.counts.missing_geometry} missing geometry`
          : `${unavailable} part meshes unavailable`}
      . Parts remain inspectable in the tree.
    </div>
  );
  return (
    <section className="viewport-panel" aria-label="Three-dimensional vehicle inspection">
      <div className="viewport-heading">
        <div>
          <span className="eyebrow">
            {overlay
              ? 'Recorded result display'
              : geometry.sourceDerived
                ? 'Source-derived inspection model'
                : 'Digital assembly'}
          </span>
          <h2>{overlay ? 'Engineering analysis' : 'Vehicle inspection'}</h2>
        </div>
        <span className="readonly-label">
          <span />
          Read only
        </span>
      </div>
      <div
        className="viewport-actions revamp-primary-actions"
        aria-label="Primary inspection actions"
      >
        <div className="inspection-drag-mode" role="group" aria-label="Mouse drag action">
          <button
            type="button"
            aria-pressed={dragMode === 'pan'}
            onClick={() => setDragMode('pan')}
            title="Grab and move the rocket across the screen without rotating it"
          >
            Move view
          </button>
          <button
            type="button"
            aria-pressed={dragMode === 'orbit'}
            onClick={() => setDragMode('orbit')}
            title="Drag to turn around the rocket"
          >
            Rotate view
          </button>
        </div>
        <button
          type="button"
          onClick={resetCamera}
          title="Return to the overview angle and frame the entire rocket, keeping visibility settings"
        >
          Whole rocket
        </button>
        <button
          onClick={() => commandCamera('fit-assembly')}
          title="Fit all loaded assembly bounds without changing visibility or display settings"
        >
          <Icon name="fit" /> Fit assembly
        </button>
        <button
          onClick={() => {
            if (!cameraSelectionIds.length) return;
            if (section) toggleSection();
            hideParts(hiddenIds.filter((id) => !cameraSelectionIds.includes(id)));
            commandCamera('frame-selection');
          }}
          disabled={!cameraSelectionIds.length}
          title="Frame the selected group or part; reveal its geometry and clear section clipping if necessary"
        >
          <Icon name="target" />{' '}
          {selectedId && (hiddenIds.includes(selectedId) || section)
            ? 'Show and frame'
            : 'Frame selection'}
        </button>
        <button onClick={() => commandCamera('zoom-in')} aria-label="Zoom in">
          + Zoom in
        </button>
        <button onClick={() => commandCamera('zoom-out')} aria-label="Zoom out">
          − Zoom out
        </button>
        <button onClick={resetCamera}>Reset view</button>
        {!overlay && (
          <button onClick={() => restoreAssembledInspection(useInspection.getState())}>
            Restore assembly
          </button>
        )}
        <details
          className="revamp-camera-menu"
          onKeyDown={(event) => {
            if (event.key !== 'Escape') return;
            event.preventDefault();
            event.stopPropagation();
            event.currentTarget.open = false;
            event.currentTarget.querySelector('summary')?.focus();
          }}
        >
          <summary>Camera</summary>
          <div>
            <button onClick={resetCamera}>Reset camera · overview</button>
            <button onClick={() => commandCamera('fit')}>Fit visible · full-part bounds</button>
            <button aria-pressed={framingGuide} onClick={() => setFramingGuide((value) => !value)}>
              Framing area guide
            </button>
            {CAMERA_VIEWS.map((view) => (
              <button
                key={view.id}
                title={view.description}
                aria-pressed={cameraReadout.mode === view.label}
                onClick={() => setCameraView(view.id)}
              >
                {view.label}
              </button>
            ))}
          </div>
        </details>
        {overlay && (
          <button onClick={toggleSection} aria-pressed={section}>
            Section
          </button>
        )}
      </div>
      <InspectionTools>
        {!overlay && (
          <div className="inspection-display-bar" aria-label="Assembly display options">
            <button onClick={toggleSection} aria-pressed={section}>
              Section
            </button>
            <button onClick={toggleMarkers} aria-pressed={markers}>
              CG / CP
            </button>
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
        {!overlay && section && (
          <SectionPlaneControls
            settings={sectionSettings}
            dimensions={sectionDims}
            onChange={(value) => setSectionState({ source: sectionSource, value })}
          />
        )}
        {!overlay && (
          <fieldset className="inspection-section-controls">
            <legend>Recorded 3D dimensions</legend>
            <label>
              Source guide for selected part or group
              <select
                aria-label="Recorded 3D dimension"
                value={activeDimension?.id ?? 'off'}
                onChange={(e) => setDimensionId(e.target.value)}
                disabled={!selectedDimensions.length}
              >
                <option value="off">Off</option>
                {selectedDimensions.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.label} · {Number(a.value.toFixed(3))} {a.units}
                  </option>
                ))}
              </select>
            </label>
            <p>
              {selectedDimensions.length
                ? 'One source guide at a time keeps small joints readable. Nominal dimensions remain visible across section cuts; they do not measure an exposed solid.'
                : 'No compatible recorded 3D dimension for this selection. Select the forward ring, motor tube, aft ring or barometer when source detail is available.'}
            </p>
          </fieldset>
        )}
      </InspectionTools>
      <div className="canvas-wrap" ref={setCanvasElement}>
        <Canvas
          className="inspection-camera-surface"
          fallback={
            <div className="canvas-loading">
              WebGL is unavailable. Use the parts tree to inspect the recorded specification.
            </div>
          }
          shadows
          frameloop="demand"
          dpr={[1, 2]}
          camera={{ position: [1.4, 0.9, 2.4], fov: 35, near: 0.001, far: 100 }}
          gl={{ antialias: true, localClippingEnabled: true }}
        >
          <color attach="background" args={['#141c22']} />
          <ambientLight intensity={0.35} />
          <hemisphereLight args={['#dbeaf0', '#23313d', 0.55]} />
          <directionalLight position={[2, 3, 3]} intensity={2} />
          <directionalLight position={[-2, 1, -1]} intensity={0.6} color="#a5bdc8" />
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
                      cutPlane={cutPlane}
                      onLoaded={onLoaded}
                      analysisMode={!!overlay}
                      overlayColor={overlay?.partColors[part.id]}
                      baseOpacity={overlay?.baseOpacity}
                      displayOffset={displayOffsets.get(part.id) ?? undefined}
                      displayMeshUrl={detailMeshes?.[part.id]}
                      groupHighlighted={
                        !!presentationGroupId && !selectedId && cameraSelectionIds.includes(part.id)
                      }
                    />
                  </Suspense>
                </MeshBoundary>
              ))}
            {overlay?.surface}
            {presentationVisual}
          </group>
          {!overlay && activeDimension && (
            <SourceDimensionOverlay
              annotations={[activeDimension]}
              selectedIds={cameraSelectionIds}
              visibleIds={visible.filter((p) => p.mesh_url).map((p) => p.id)}
              displayOffsets={displayOffsets}
            />
          )}
          {!overlay && <Markers length={length} mass={mass} />}
          <CameraFit
            checkpointKey={mainCameraKey(vehicle.id, vehicle.identity?.specification_sha256)}
            group={group}
            length={overallLength}
            complete={visible.every(
              (part) =>
                !part.mesh_url ||
                loadedIds.includes(part.id) ||
                meshErrors.includes(partName(part)),
            )}
            command={cameraCommand}
            dragMode={dragMode}
            meshBounds={meshBounds}
            allIds={vehicle.parts.filter((part) => part.mesh_url).map((part) => part.id)}
            visibleIds={visible.filter((part) => part.mesh_url).map((part) => part.id)}
            exploded={exploded}
            onStatus={setFitStatus}
            onReadout={setCameraReadout}
            selectionIds={cameraSelectionIds}
            selectionLabel={
              selectedPart ? partName(selectedPart) : (openedGroupLabel ?? 'Selected geometry')
            }
            groupSelected={!!presentationGroupId && !selectedId}
            presentationGroupId={presentationGroupId}
          />
          <GizmoHelper alignment="bottom-right" margin={[65, 65]}>
            <GizmoViewport
              disabled
              axisColors={['#bc6c68', '#69b7aa', '#719dbd']}
              labelColor="#15212a"
            />
          </GizmoHelper>
        </Canvas>
        <InspectionTools>
          {!overlay && geometry.sourceDerived && (
            <div className="inspection-display-shortcuts">
              <div role="group" aria-label="Assembly display mode">
                <button
                  aria-pressed={exploded === 0 && !section}
                  onClick={() => restoreAssembledInspection(useInspection.getState())}
                >
                  Assembled
                </button>
                <button
                  aria-pressed={exploded > 0}
                  disabled={!presentation}
                  onClick={() => {
                    if (section) toggleSection();
                    setExploded(1);
                    commandCamera(cameraSelectionIds.length ? 'frame-selection' : 'fit-assembly');
                  }}
                >
                  Breakdown
                </button>
                <button
                  aria-pressed={section}
                  onClick={() => {
                    setExploded(0);
                    if (!section) toggleSection();
                  }}
                >
                  Section
                </button>
              </div>
              <details>
                <summary>How breakdown works</summary>
                <p>
                  {!presentation
                    ? 'Breakdown unavailable: exact source-pinned presentation metadata is missing.'
                    : `Display separation: first half separates six functional groups; second half opens ${openedGroupLabel ?? 'no detailed group — select a functional group in Parts to open it'}. Display illustration only; no manufactured clearance or physical assembly sequence is implied.`}
                </p>
              </details>
            </div>
          )}
        </InspectionTools>
        <OrbitCameraControls
          readout={cameraReadout}
          dragMode={dragMode}
          canTargetSelection={cameraSelectionIds.length > 0}
          selectionLabel={
            selectedPart ? partName(selectedPart) : (openedGroupLabel ?? 'Selected group / part')
          }
          onAngles={(angles) =>
            setCameraCommand((previous) => ({
              id: (previous?.id ?? 0) + 1,
              kind: 'angles',
              angles,
            }))
          }
          onTarget={(target) =>
            commandCamera(target === 'selection' ? 'target-selection' : 'target-assembly')
          }
          onPan={(direction) => commandCamera(`pan-${direction}`)}
        />
        {framingGuide && canvasSize.width > 0 && canvasSize.height > 0 && (
          <div
            className="inspection-framing-guide"
            aria-label="Framing area: display guide excluding controls, not rocket geometry"
            style={{
              left: guideInsets.left * canvasSize.width,
              right: guideInsets.right * canvasSize.width,
              top: guideInsets.top * canvasSize.height,
              bottom: guideInsets.bottom * canvasSize.height,
            }}
          >
            <span>Framing area · display guide, not a rocket part</span>
          </div>
        )}
        {!statusInTools && !overlay && fitReadout}
        <div className="viewport-scale">
          <span className="scale-line" />
          <span>{millimetres(overallLength)} overall · metre grid</span>
        </div>
        <div className="viewport-orientation">
          <b>Y</b>
          <span>axis toward nose</span>
          <small>
            {geometry.sourceDerived
              ? 'Metres · placed inspection geometry'
              : 'Metres · placed CAD geometry'}
          </small>
        </div>
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
            {geometry.sourceDerived
              ? 'Loading inspection meshes… '
              : 'Loading CAD-derived part meshes… '}
            {loadedIds.length}/{vehicle.parts.filter((part) => part.mesh_url).length}
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
        {!statusInTools && !overlay && meshWarning}
      </div>
      {overlay && (
        <div className="inspection-analysis-status" aria-label="Recorded analysis display status">
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
          {fitReadout}
          {meshWarning}
        </div>
      )}
      <InspectionTools>
        {statusInTools && (
          <div className="revamp-scene-status" aria-label="Inspection geometry and framing status">
            {fitReadout}
            {meshWarning}
          </div>
        )}
        <div
          hidden={!!layout && layout.preferences.representation === '2d'}
          className="revamp-scene-settings"
        >
          <div className="visibility-toolbar">
            <button
              onClick={() =>
                hideParts(
                  vehicle.parts
                    .filter((part) => outerBody(part) && !nose(part))
                    .map((part) => part.id),
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
            {isolatedFrom && (
              <button onClick={exitIsolate}>Exit isolation · restore prior visibility</button>
            )}
            {selectedId && !isolatedFrom && (
              <button
                disabled={!isolatedFrom && !selectedPart?.mesh_url}
                title={
                  !selectedPart?.mesh_url
                    ? 'Isolate unavailable: this source record has no mesh.'
                    : undefined
                }
                onClick={() =>
                  isolatedFrom
                    ? exitIsolate()
                    : isolate(
                        selectedId,
                        vehicle.parts.map((part) => part.id),
                      )
                }
              >
                {isolatedFrom ? 'Exit isolate' : 'Isolate selected'}
              </button>
            )}
          </div>
          {!overlay && (
            <div className="viewport-controls">
              <label className="slider-control">
                <span>
                  {geometry.sourceDerived ? 'Staged breakdown' : 'Exploded view'}{' '}
                  <small>{Math.round(exploded * 100)}%</small>
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
                  <small>
                    {geometry.sourceDerived ? 'Groups → selected group detail' : 'Exploded'}
                  </small>
                </span>
              </label>
              {!geometry.sourceDerived && (
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
              )}
              {geometry.sourceDerived && (
                <p role="status">
                  Burn-state control unavailable: this inspection model has no admitted complete
                  flight configuration or canonical inertia.
                </p>
              )}
            </div>
          )}
          {!overlay && <InspectionDisplayReadout vehicle={vehicle} />}
          <div className="viewport-help">
            <span>
              {dragMode === 'pan' ? 'Drag to move the view' : 'Drag to rotate'} · scroll to zoom ·
              Whole rocket to return
            </span>
            <span>
              {!overlay && (
                <>
                  <kbd>E</kbd> explode
                </>
              )}
              <kbd>F</kbd> focus <kbd>R</kbd> reset <kbd>S</kbd> section <kbd>esc</kbd> clear
            </span>
          </div>
        </div>
      </InspectionTools>
    </section>
  );
}
