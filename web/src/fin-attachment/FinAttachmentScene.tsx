import { Component, Suspense, useEffect, useMemo, useRef, useState } from 'react';
import type { ComponentRef, ReactNode } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { Html, Line, OrbitControls, useGLTF } from '@react-three/drei';
import { Box3, DoubleSide, Mesh, MOUSE, Vector3 } from 'three';
import type { Material, MeshStandardMaterial, PerspectiveCamera } from 'three';
import type { FinAttachmentCameraSnapshot } from './finAttachmentState';
import {
  isFinPickClick,
  sectionPlaneOutline,
  unionBounds,
  verifiedFinAssetBytes,
} from './finAttachment';
import type { BoundsM, FinAsset, FinCatalog, FinSectionId } from './finAttachment';

type LoadedPart = { meshUrl: string; capUrl: string | null };
type AssetState =
  | { status: 'loading' }
  | { status: 'ready'; urls: Map<string, LoadedPart> }
  | { status: 'error'; message: string };
export type FitCommand = { serial: number; scope: 'joint' | 'selected' };

class GeometryBoundary extends Component<{ children: ReactNode }, { error: string | null }> {
  state = { error: null as string | null };
  static getDerivedStateFromError(error: unknown) {
    return { error: error instanceof Error ? error.message : 'Unknown 3D asset error.' };
  }
  render() {
    return this.state.error ? (
      <p className="fin-attachment-state fin-attachment-alert" role="alert">
        Registered fin CAD unavailable: {this.state.error}
      </p>
    ) : (
      this.props.children
    );
  }
}

const colors: Record<string, string> = {
  fin_set: '#8dc7e3',
  fin_tabs: '#f2bd76',
  root_gussets: '#d8a675',
  body: '#a2c1cd',
  motor_tube: '#9bd4b1',
  forward_ring: '#c4afdf',
  aft_ring: '#c4afdf',
  motor: '#abb7c4',
  motor_retainer: '#d0a2a1',
};

function RegisteredMesh({
  url,
  color,
  selected,
  ghost,
  cap,
  onSelect,
}: {
  url: string;
  color: string;
  selected: boolean;
  ghost: boolean;
  cap: boolean;
  onSelect?: () => void;
}) {
  const gltf = useGLTF(url);
  const epochs = useRef(new WeakMap<object, number>());
  const scene = useMemo(() => {
    const copy = gltf.scene.clone(true);
    copy.traverse((object) => {
      if (!(object instanceof Mesh)) return;
      const decorate = (material: Material): Material => {
        const clone = material.clone() as MeshStandardMaterial;
        clone.color?.set(cap ? '#e9aa66' : selected ? '#ffe2a2' : color);
        clone.emissive?.set(selected ? '#8c5b2d' : '#000000');
        clone.emissiveIntensity = selected ? 0.28 : 0;
        if (ghost || cap) {
          clone.transparent = true;
          clone.opacity = cap ? 0.88 : 0.16;
          clone.depthWrite = false;
        }
        if (cap) {
          clone.side = DoubleSide;
          clone.polygonOffset = true;
          clone.polygonOffsetFactor = -2;
          clone.polygonOffsetUnits = -2;
        }
        return clone;
      };
      object.material = Array.isArray(object.material)
        ? object.material.map(decorate)
        : decorate(object.material);
    });
    return copy;
  }, [cap, color, ghost, gltf.scene, selected]);
  useEffect(() => {
    const epochMap = epochs.current;
    const epoch = (epochMap.get(scene) ?? 0) + 1;
    epochMap.set(scene, epoch);
    return () => {
      queueMicrotask(() => {
        if (epochMap.get(scene) !== epoch) return;
        scene.traverse((object) => {
          if (!(object instanceof Mesh)) return;
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          materials.forEach((material) => material.dispose());
        });
        epochMap.delete(scene);
      });
    };
  }, [scene]);
  return (
    <primitive
      object={scene}
      dispose={null}
      onClick={
        onSelect
          ? (event: { stopPropagation: () => void; delta: number }) => {
              if (!isFinPickClick(event.delta)) return;
              event.stopPropagation();
              onSelect();
            }
          : undefined
      }
    />
  );
}

function CameraRig({
  section,
  dragMode,
  bounds,
  command,
  initial,
  onCameraChange,
}: {
  section: FinSectionId;
  dragMode: 'rotate' | 'pan';
  bounds: BoundsM;
  command: FitCommand;
  initial: FinAttachmentCameraSnapshot | null;
  onCameraChange: (camera: FinAttachmentCameraSnapshot) => void;
}) {
  const controls = useRef<ComponentRef<typeof OrbitControls>>(null);
  const { camera, invalidate, size } = useThree();
  const first = useRef(true);
  const initialRef = useRef(initial);
  const lastSetup = useRef('');
  useEffect(() => {
    const setup = `${section}:${bounds.flat().join(',')}:${command.serial}:${size.width}:${size.height}`;
    // Strict Mode replays this effect with the same refs. A replay is not a Fit command.
    if (lastSetup.current === setup) return;
    lastSetup.current = setup;
    const view = camera as PerspectiveCamera;
    const savePose = () =>
      onCameraChange({
        position: view.position.toArray(),
        target: controls.current?.target.toArray() ?? [0, 0, 0],
        up: view.up.toArray(),
        zoom: view.zoom,
      });
    if (first.current && initialRef.current) {
      first.current = false;
      view.position.set(...initialRef.current.position);
      view.up.set(...initialRef.current.up);
      view.zoom = initialRef.current.zoom;
      controls.current?.target.set(...initialRef.current.target);
      view.lookAt(...initialRef.current.target);
      view.updateProjectionMatrix();
      controls.current?.update();
      savePose();
      invalidate();
      return;
    }
    first.current = false;
    const box = new Box3(new Vector3(...bounds[0]), new Vector3(...bounds[1]));
    const center = box.getCenter(new Vector3());
    const span = box.getSize(new Vector3());
    const viewAngle = Math.max(0.01, (view.fov * Math.PI) / 180);
    const aspect = Math.max(0.5, size.width / Math.max(1, size.height));
    const distance = Math.max(
      span.length() * 1.22,
      (span.y / (2 * Math.tan(viewAngle / 2))) * (aspect < 1 ? 1 / aspect : 1) * 1.25,
      0.045,
    );
    controls.current?.target.copy(center);
    view.up.set(0, 1, 0);
    view.zoom = 1;
    // Look from removed material toward the actual cap, rather than the opaque outside.
    const direction =
      section === 'longitudinal'
        ? [0.35, 0.15, -1]
        : section === 'transverse'
          ? [0.35, 1, 0.25]
          : [0.7, 0.32, 1];
    view.position.copy(center).add(new Vector3(...direction).multiplyScalar(distance));
    view.near = Math.max(0.0001, distance / 1000);
    view.far = Math.max(5, distance * 20);
    view.lookAt(center);
    view.updateProjectionMatrix();
    controls.current?.update();
    savePose();
    invalidate();
  }, [
    bounds,
    camera,
    command.serial,
    invalidate,
    onCameraChange,
    section,
    size.height,
    size.width,
  ]);
  return (
    <OrbitControls
      ref={controls}
      makeDefault
      enablePan
      enableRotate
      enableZoom
      enableDamping={false}
      mouseButtons={{
        LEFT: dragMode === 'pan' ? MOUSE.PAN : MOUSE.ROTATE,
        MIDDLE: MOUSE.DOLLY,
        RIGHT: MOUSE.PAN,
      }}
      onEnd={() => {
        const view = camera as PerspectiveCamera;
        const target = controls.current?.target;
        if (!target) return;
        onCameraChange({
          position: [view.position.x, view.position.y, view.position.z],
          target: [target.x, target.y, target.z],
          up: [view.up.x, view.up.y, view.up.z],
          zoom: view.zoom,
        });
      }}
    />
  );
}

function SceneContent({
  catalog,
  section,
  urls,
  visibleIds,
  selectedPieceId,
  selectedDimensionId,
  bodyMode,
  dragMode,
  fit,
  camera,
  onSelect,
  onSelectDimension,
  onCameraChange,
}: {
  catalog: FinCatalog;
  section: FinSectionId;
  urls: Map<string, LoadedPart>;
  visibleIds: Set<string>;
  selectedPieceId: string | null;
  selectedDimensionId: string | null;
  bodyMode: 'ghost' | 'solid' | 'hidden';
  dragMode: 'rotate' | 'pan';
  fit: FitCommand;
  camera: FinAttachmentCameraSnapshot | null;
  onSelect: (partId: string) => void;
  onSelectDimension: (dimensionId: FinCatalog['dimensions'][number]['id']) => void;
  onCameraChange: (camera: FinAttachmentCameraSnapshot) => void;
}) {
  const displayed = useMemo(
    () =>
      catalog.parts.filter(
        (part) =>
          visibleIds.has(part.id) &&
          part.assets[section] !== null &&
          !(part.id === 'body' && bodyMode === 'hidden'),
      ),
    [catalog, section, visibleIds, bodyMode],
  );
  const selected = displayed.find((part) => part.id === selectedPieceId);
  const selectedDimension = catalog.dimensions.find(
    (dimension) => dimension.id === selectedDimensionId,
  );
  const planeOutline = useMemo(() => sectionPlaneOutline(catalog, section), [catalog, section]);
  const selectedAsset = fit.scope === 'selected' ? selected?.assets[section] : null;
  const bounds = useMemo(() => {
    if (selectedAsset) return selectedAsset.bounds_m;
    if (catalog.focus_bounds_m && visibleIds.size === catalog.parts.length)
      return catalog.focus_bounds_m;
    return unionBounds(displayed.map((part) => part.assets[section]!.bounds_m));
  }, [catalog, displayed, selectedAsset, section, visibleIds]);
  if (!bounds) return null;
  return (
    <>
      <color attach="background" args={['#101c29']} />
      <ambientLight intensity={1.4} />
      <hemisphereLight args={['#e4efff', '#34495c', 1.4]} />
      <directionalLight position={[0.45, 0.8, 0.6]} intensity={2.5} />
      <directionalLight position={[-0.6, -0.3, -0.4]} intensity={0.8} />
      {planeOutline && (
        <Line points={planeOutline} color="#84cfe7" lineWidth={1.2} depthTest={false} />
      )}
      {displayed.map((part) => {
        const asset = part.assets[section]!;
        const loaded = urls.get(part.id);
        if (!loaded) return null;
        const highlighted =
          selectedPieceId === part.id || Boolean(selectedDimension?.feature_ids.includes(part.id));
        return (
          <group key={part.id}>
            <RegisteredMesh
              url={loaded.meshUrl}
              color={colors[part.id] ?? '#b9c6d3'}
              selected={highlighted}
              ghost={part.id === 'body' && bodyMode === 'ghost'}
              cap={false}
              onSelect={() => onSelect(part.id)}
            />
            {loaded.capUrl && (
              <RegisteredMesh
                url={loaded.capUrl}
                color="#e9aa66"
                selected={highlighted}
                ghost={false}
                cap
                onSelect={() => onSelect(part.id)}
              />
            )}
            {asset.cut_edges_m.map((edge, index) => (
              <Line
                key={`${part.id}:edge:${index}`}
                points={edge}
                color={highlighted ? '#ffe0a5' : '#ef9f5c'}
                lineWidth={highlighted ? 2.2 : 1.2}
                depthTest={false}
              />
            ))}
          </group>
        );
      })}
      {catalog.dimensions
        .filter((dimension) =>
          dimension.feature_ids.some((partId) => displayed.some((part) => part.id === partId)),
        )
        .map((dimension) => {
          const labelOffset =
            dimension.id === 'tab-thickness'
              ? [-76, -30]
              : dimension.id === 'slot-width'
                ? [46, -6]
                : [54, 40];
          const middle: [number, number, number] = [
            (dimension.points_m[0][0] + dimension.points_m[1][0]) / 2,
            (dimension.points_m[0][1] + dimension.points_m[1][1]) / 2,
            (dimension.points_m[0][2] + dimension.points_m[1][2]) / 2,
          ];
          return (
            <Html key={dimension.id} position={middle} zIndexRange={[20, 0]}>
              <svg
                width="1"
                height="1"
                aria-hidden="true"
                style={{ position: 'absolute', overflow: 'visible', pointerEvents: 'none' }}
              >
                <line
                  x1="0"
                  y1="0"
                  x2={labelOffset[0]}
                  y2={labelOffset[1]}
                  stroke="#f2d993"
                  strokeWidth="1"
                />
              </svg>
              <button
                type="button"
                className="fin-attachment-dim-marker"
                aria-label={`Select ${dimension.label} dimension`}
                aria-pressed={selectedDimensionId === dimension.id}
                style={{
                  transform: `translate(${labelOffset[0]}px, ${labelOffset[1]}px) translate(-50%, -50%)`,
                }}
                onClick={(event) => {
                  event.stopPropagation();
                  onSelectDimension(dimension.id);
                }}
              >
                {dimension.value_mm.toFixed(2)} mm
              </button>
            </Html>
          );
        })}
      {selectedDimension && (
        <>
          <Line
            points={selectedDimension.points_m}
            color="#ffdf86"
            lineWidth={3}
            depthTest={false}
          />
          {selectedDimension.points_m.map((point, index) => (
            <mesh key={index} position={point}>
              <sphereGeometry args={[0.0018, 10, 10]} />
              <meshBasicMaterial color="#ffdf86" depthTest={false} />
            </mesh>
          ))}
        </>
      )}
      <CameraRig
        section={section}
        dragMode={dragMode}
        bounds={bounds}
        command={fit}
        initial={camera}
        onCameraChange={onCameraChange}
      />
    </>
  );
}

export function FinAttachmentScene({
  catalog,
  section,
  visibleIds,
  selectedPieceId,
  selectedDimensionId,
  bodyMode,
  dragMode,
  fit,
  camera,
  onSelect,
  onSelectDimension,
  onCameraChange,
}: {
  catalog: FinCatalog;
  section: FinSectionId;
  visibleIds: Set<string>;
  selectedPieceId: string | null;
  selectedDimensionId: string | null;
  bodyMode: 'ghost' | 'solid' | 'hidden';
  dragMode: 'rotate' | 'pan';
  fit: FitCommand;
  camera: FinAttachmentCameraSnapshot | null;
  onSelect: (partId: string) => void;
  onSelectDimension: (dimensionId: FinCatalog['dimensions'][number]['id']) => void;
  onCameraChange: (camera: FinAttachmentCameraSnapshot) => void;
}) {
  const [assets, setAssets] = useState<AssetState>({ status: 'loading' });
  useEffect(() => {
    let cancelled = false;
    const created: string[] = [];
    const abort = new AbortController();
    setAssets({ status: 'loading' });
    Promise.all(
      catalog.parts
        .filter((part) => part.assets[section])
        .map(async (part) => {
          const asset = part.assets[section] as FinAsset;
          const fetcher: typeof fetch = (url, init) =>
            fetch(url, { ...init, signal: abort.signal });
          const bytes = await verifiedFinAssetBytes(asset.url, asset.sha256, asset.bytes, fetcher);
          const meshUrl = URL.createObjectURL(new Blob([bytes], { type: 'model/gltf-binary' }));
          if (cancelled) URL.revokeObjectURL(meshUrl);
          else created.push(meshUrl);
          let capUrl: string | null = null;
          if (asset.cap_url && asset.cap_sha256) {
            const capBytes = await verifiedFinAssetBytes(
              asset.cap_url,
              asset.cap_sha256,
              null,
              fetcher,
            );
            capUrl = URL.createObjectURL(new Blob([capBytes], { type: 'model/gltf-binary' }));
            if (cancelled) URL.revokeObjectURL(capUrl);
            else created.push(capUrl);
          }
          return [part.id, { meshUrl, capUrl }] as const;
        }),
    )
      .then((entries) => {
        if (!cancelled) setAssets({ status: 'ready', urls: new Map(entries) });
      })
      .catch((error: unknown) => {
        if (!cancelled)
          setAssets({
            status: 'error',
            message: error instanceof Error ? error.message : 'Unknown asset error.',
          });
      });
    return () => {
      cancelled = true;
      abort.abort();
      created.forEach((url) => URL.revokeObjectURL(url));
    };
  }, [catalog, section]);
  if (assets.status === 'loading')
    return (
      <p className="fin-attachment-state" role="status">
        Verifying registered section CAD…
      </p>
    );
  if (assets.status === 'error')
    return (
      <p className="fin-attachment-state fin-attachment-alert" role="alert">
        Fin CAD unavailable: {assets.message}
      </p>
    );
  if (
    !catalog.parts.some(
      (part) =>
        visibleIds.has(part.id) &&
        part.assets[section] &&
        !(part.id === 'body' && bodyMode === 'hidden'),
    )
  )
    return (
      <p className="fin-attachment-state" role="status">
        No retained solid is visible in this section. Select another part, show all, or change
        section; assembled geometry has not been substituted.
      </p>
    );
  return (
    <GeometryBoundary key={section}>
      <Suspense
        fallback={
          <p className="fin-attachment-state" role="status">
            Opening verified section solids…
          </p>
        }
      >
        <Canvas camera={{ fov: 42, near: 0.0001, far: 20 }} dpr={[1, 2]}>
          <SceneContent
            catalog={catalog}
            section={section}
            urls={assets.urls}
            visibleIds={visibleIds}
            selectedPieceId={selectedPieceId}
            selectedDimensionId={selectedDimensionId}
            bodyMode={bodyMode}
            dragMode={dragMode}
            fit={fit}
            camera={camera}
            onSelect={onSelect}
            onSelectDimension={onSelectDimension}
            onCameraChange={onCameraChange}
          />
        </Canvas>
      </Suspense>
    </GeometryBoundary>
  );
}
