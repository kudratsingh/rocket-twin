import { Component, Suspense, useEffect, useMemo, useRef, useState } from 'react';
import type { ComponentRef, ReactNode } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls, useGLTF } from '@react-three/drei';
import { Box3, DoubleSide, Mesh, Plane, Vector3 } from 'three';
import type { Material, MeshStandardMaterial, PerspectiveCamera } from 'three';
import catalog from '../../../docs/studies/frontend-component-depth-20261108/mechanical-detail-layout.json';
import {
  admitRp1MechanicalLayout,
  displayOffset,
  displayedChildBounds,
  displayedChildrenBounds,
  verifiedMechanicalBlobUrl,
} from './rp1MechanicalReference';
import type {
  BoundsM,
  MechanicalChild,
  MechanicalIdentity,
  MechanicalLayout,
} from './rp1MechanicalReference';
import './rp1MechanicalReference.css';

type BodyMode = 'solid' | 'ghost' | 'off' | 'section';
type FitCommand = { scope: 'root' | 'selected'; serial: number };
type AssetState =
  | { status: 'loading' }
  | { status: 'ready'; urls: Map<string, string> }
  | { status: 'error'; message: string };

class MechanicalLoadBoundary extends Component<{ children: ReactNode }, { error: string | null }> {
  state = { error: null as string | null };

  static getDerivedStateFromError(error: unknown) {
    return { error: error instanceof Error ? error.message : 'Unknown geometry load error.' };
  }

  render() {
    if (this.state.error)
      return (
        <p className="rp1-mechanical-loading" role="alert">
          Mechanical 3D closeup unavailable: {this.state.error}
        </p>
      );
    return this.props.children;
  }
}

const assemblyParents = [
  'fin_set',
  'fin_tabs',
  'root_gussets',
  'body',
  'motor_tube',
  'forward_ring',
  'aft_ring',
];
const parentNames: Record<string, string> = {
  fin_set: 'Fin panels',
  fin_tabs: 'Integral fin tabs',
  root_gussets: 'Root gussets',
  body: 'Slotted body shell',
  motor_tube: 'Motor tube',
  forward_ring: 'Forward ring stack',
  aft_ring: 'Aft centering ring',
};

function ChildMesh({
  child,
  url,
  selected,
  ghost,
  clipBody,
  exploded,
  onSelect,
}: {
  child: MechanicalChild;
  url: string;
  selected: boolean;
  ghost: boolean;
  clipBody: boolean;
  exploded: number;
  onSelect: (id: string) => void;
}) {
  const gltf = useGLTF(url);
  const materialEpochs = useRef(new WeakMap<object, number>());
  const scene = useMemo(() => {
    const copy = gltf.scene.clone(true);
    copy.traverse((object) => {
      if (!(object instanceof Mesh)) return;
      const original = object.material;
      const decorate = (material: Material): Material => {
        const clone = material.clone() as MeshStandardMaterial;
        if (selected) {
          clone.color?.set('#f7c56b');
          clone.emissive?.set('#9b6325');
          clone.emissiveIntensity = 0.28;
        }
        if (ghost) {
          clone.transparent = true;
          clone.opacity = 0.2;
          clone.depthWrite = false;
        }
        if (clipBody) {
          clone.clippingPlanes = [new Plane(new Vector3(1, 0, 0), 0)];
          clone.side = DoubleSide;
          clone.needsUpdate = true;
        }
        return clone;
      };
      object.material = Array.isArray(original) ? original.map(decorate) : decorate(original);
    });
    return copy;
  }, [clipBody, gltf.scene, ghost, selected]);
  useEffect(() => {
    const epochs = materialEpochs.current;
    const epoch = (epochs.get(scene) ?? 0) + 1;
    epochs.set(scene, epoch);
    return () => {
      queueMicrotask(() => {
        // Strict Mode replays setup/cleanup for the same scene; dispose only after final release.
        if (epochs.get(scene) !== epoch) return;
        scene.traverse((object) => {
          if (!(object instanceof Mesh)) return;
          const materials = Array.isArray(object.material) ? object.material : [object.material];
          materials.forEach((material) => material.dispose());
        });
        epochs.delete(scene);
      });
    };
  }, [scene]);
  return (
    <group
      position={displayOffset(child, exploded)}
      onClick={(event) => {
        event.stopPropagation();
        onSelect(child.id);
      }}
    >
      <primitive object={scene} dispose={null} />
    </group>
  );
}

function ViewRig({ bounds, command }: { bounds: BoundsM; command: FitCommand }) {
  const controls = useRef<ComponentRef<typeof OrbitControls>>(null);
  const { camera, invalidate, size } = useThree();
  useEffect(() => {
    const box = new Box3(new Vector3(...bounds[0]), new Vector3(...bounds[1]));
    const center = box.getCenter(new Vector3());
    const span = box.getSize(new Vector3());
    const view = camera as PerspectiveCamera;
    const diagonal = Math.max(span.length(), 0.045);
    const vertical = Math.max(0.01, (view.fov * Math.PI) / 180);
    const aspect = Math.max(0.5, size.width / Math.max(1, size.height));
    const distance = Math.max(
      diagonal * 1.15,
      (span.y / (2 * Math.tan(vertical / 2))) * (aspect < 1 ? 1 / aspect : 1) * 1.18,
    );
    controls.current?.target.copy(center);
    view.position.copy(center).add(new Vector3(distance * 0.82, distance * 0.42, distance * 0.9));
    view.near = Math.max(0.0001, distance / 1000);
    view.far = Math.max(5, distance * 20);
    view.lookAt(center);
    view.updateProjectionMatrix();
    controls.current?.update();
    invalidate();
  }, [bounds, camera, command, invalidate, size.height, size.width]);
  return (
    <OrbitControls
      ref={controls}
      makeDefault
      enablePan
      enableZoom
      enableRotate
      enableDamping={false}
    />
  );
}

function MechanicalScene({
  layout,
  urls,
  selectedId,
  bodyMode,
  exploded,
  fit,
  onSelect,
}: {
  layout: MechanicalLayout;
  urls: Map<string, string>;
  selectedId: string;
  bodyMode: BodyMode;
  exploded: number;
  fit: FitCommand;
  onSelect: (id: string) => void;
}) {
  const selected = layout.children.find((child) => child.id === selectedId);
  const rootBounds = useMemo(
    () =>
      displayedChildrenBounds(
        layout.children.filter((child) => child.parent_part_id !== 'body'),
        exploded,
      ),
    [layout, exploded],
  );
  const scope =
    fit.scope === 'selected' && selected ? displayedChildBounds(selected, exploded) : rootBounds;
  if (!scope) return null;
  return (
    <>
      <color attach="background" args={['#101c28']} />
      <ambientLight intensity={1.45} />
      <hemisphereLight args={['#d9efff', '#425367', 1.35]} />
      <directionalLight position={[0.4, 0.5, 0.6]} intensity={2.3} />
      <directionalLight position={[-0.4, -0.2, -0.3]} intensity={0.75} />
      {layout.children.map((child) => {
        if (child.parent_part_id === 'body' && bodyMode === 'off') return null;
        const url = urls.get(child.id);
        if (!url) return null;
        return (
          <ChildMesh
            key={child.id}
            child={child}
            url={url}
            selected={selectedId === child.id}
            ghost={child.parent_part_id === 'body' && bodyMode === 'ghost'}
            clipBody={child.parent_part_id === 'body' && bodyMode === 'section'}
            exploded={exploded}
            onSelect={onSelect}
          />
        );
      })}
      <ViewRig bounds={scope} command={fit} />
    </>
  );
}

function MechanicalReferenceAdmitted({
  layout,
  initialPartId,
}: {
  layout: MechanicalLayout;
  initialPartId?: string;
}) {
  const [assets, setAssets] = useState<AssetState>({ status: 'loading' });
  const initial =
    layout.children.find((child) => child.parent_part_id === initialPartId)?.id ??
    layout.children[0].id;
  const [selectedId, setSelectedId] = useState(initial);
  const [bodyMode, setBodyMode] = useState<BodyMode>('ghost');
  const [exploded, setExploded] = useState(0);
  const [fit, setFit] = useState<FitCommand>({ scope: 'root', serial: 0 });
  useEffect(() => {
    let cancelled = false;
    const abort = new AbortController();
    const created: string[] = [];
    setAssets({ status: 'loading' });
    Promise.all(
      layout.children.map(async (child) => {
        const url = await verifiedMechanicalBlobUrl(child, (input, init) =>
          fetch(input, { ...init, signal: abort.signal }),
        );
        // A close during fetch/hash must not leave a late object URL alive.
        if (cancelled) URL.revokeObjectURL(url);
        else created.push(url);
        return [child.id, url] as const;
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
      created.forEach((url) => {
        // These blob URLs belong only to this close-up, never to the vehicle's GLTF cache.
        useGLTF.clear(url);
        URL.revokeObjectURL(url);
      });
    };
  }, [layout]);
  const selected = layout.children.find((child) => child.id === selectedId) ?? layout.children[0];
  const parent = layout.parents.find((item) => item.id === selected.parent_part_id);
  const fitView = (scope: FitCommand['scope']) =>
    setFit((current) => ({ scope, serial: current.serial + 1 }));
  const reset = () => {
    setSelectedId(initial);
    setBodyMode('ghost');
    setExploded(0);
    fitView('root');
  };
  return (
    <div className="rp1-mechanical-reference">
      <div className="rp1-mechanical-header">
        <div>
          <h3>RP1 mechanical source closeup</h3>
          <p>
            Exact source child solids · metre frame · X body lateral, Y length station, Z body depth
          </p>
        </div>
        <div className="rp1-mechanical-actions">
          <button type="button" onClick={() => fitView('root')}>
            Fit root
          </button>
          <button type="button" onClick={() => fitView('selected')}>
            Fit piece
          </button>
          <button type="button" onClick={reset}>
            Reset view
          </button>
        </div>
      </div>
      <div className="rp1-mechanical-controls">
        <label>
          Body shell
          <select
            value={bodyMode}
            onChange={(event) => setBodyMode(event.target.value as BodyMode)}
          >
            <option value="ghost">Transparent</option>
            <option value="solid">Solid</option>
            <option value="off">Off</option>
            <option value="section">Half-shell display cutaway (uncapped)</option>
          </select>
        </label>
        <label>
          Illustrative panel/tab/gusset separation
          <input
            type="range"
            min="0"
            max="1"
            step="0.25"
            value={exploded}
            onChange={(event) => setExploded(Number(event.target.value))}
          />
        </label>
        <span>Orbit · pan · zoom; select a solid or a piece below.</span>
        <p className="rp1-mechanical-limit">
          Panels and tabs represent continuous plywood cuts. Their display separation explains the
          source records; it is not a proposed glue joint or checked assembly motion.
        </p>
      </div>
      <div className="rp1-mechanical-layout">
        <div
          className="rp1-mechanical-canvas"
          role="img"
          aria-label="Interactive source-linked fin root, body slot, motor tube and ring closeup"
        >
          {assets.status === 'loading' ? (
            <p className="rp1-mechanical-loading">Verifying exact source GLB bytes…</p>
          ) : assets.status === 'error' ? (
            <p className="rp1-mechanical-loading" role="alert">
              Mechanical 3D closeup unavailable: {assets.message}
            </p>
          ) : (
            <MechanicalLoadBoundary>
              <Canvas
                frameloop="demand"
                dpr={[1, 2]}
                camera={{ position: [0.3, 0.25, 0.3], fov: 40, near: 0.0001, far: 10 }}
                gl={{ antialias: true }}
                onCreated={({ gl }) => {
                  gl.localClippingEnabled = true;
                }}
              >
                <Suspense fallback={null}>
                  <MechanicalScene
                    layout={layout}
                    urls={assets.urls}
                    selectedId={selectedId}
                    bodyMode={bodyMode}
                    exploded={exploded}
                    fit={fit}
                    onSelect={setSelectedId}
                  />
                </Suspense>
              </Canvas>
            </MechanicalLoadBoundary>
          )}
        </div>
        <div className="rp1-mechanical-sidebar">
          <div className="rp1-mechanical-selected">
            <span>Selected source piece</span>
            <strong>{selected.label}</strong>
            <code>{selected.id}</code>
            <p>
              Parent: {parentNames[selected.parent_part_id]} <code>{selected.parent_part_id}</code>
            </p>
            <p>{parent?.function ?? 'Function unavailable in source catalog.'}</p>
            <dl>
              <div>
                <dt>Material</dt>
                <dd>{selected.material}</dd>
              </div>
              <div>
                <dt>Representation</dt>
                <dd>{selected.maturity.replaceAll('_', ' ')}</dd>
              </div>
              <div>
                <dt>Bounds (mm)</dt>
                <dd>
                  {[0, 1, 2]
                    .map((axis) =>
                      ((selected.bounds_m[1][axis] - selected.bounds_m[0][axis]) * 1000).toFixed(2),
                    )
                    .join(' × ')}
                </dd>
              </div>
              <div>
                <dt>Source</dt>
                <dd>{parent?.source_kind ?? selected.source_kind}</dd>
              </div>
            </dl>
          </div>
          <div className="rp1-mechanical-piece-list">
            {assemblyParents.map((id) => (
              <details key={id} open={id === selected.parent_part_id}>
                <summary>
                  {parentNames[id]}{' '}
                  <span>
                    {layout.children.filter((child) => child.parent_part_id === id).length}
                  </span>
                </summary>
                {layout.children
                  .filter((child) => child.parent_part_id === id)
                  .map((child) => (
                    <button
                      key={child.id}
                      type="button"
                      aria-pressed={child.id === selectedId}
                      onClick={() => setSelectedId(child.id)}
                    >
                      {child.label}
                    </button>
                  ))}
              </details>
            ))}
          </div>
        </div>
      </div>
      <p className="rp1-mechanical-limit">
        Source inspection solids only. Transparent shell, uncapped half-shell cutaway and offsets
        are display controls; they do not change source geometry or establish contact, clearance,
        joint strength or manufacturing acceptance. Bond and slot-fill records are mass allowances
        without bead geometry.
      </p>
    </div>
  );
}

export function Rp1MechanicalReference3D({
  configurationId,
  specificationSha256,
  inspectionGeometrySha256,
  initialPartId,
}: MechanicalIdentity & { initialPartId?: string }) {
  const admitted = admitRp1MechanicalLayout(catalog, {
    configurationId,
    specificationSha256,
    inspectionGeometrySha256,
  });
  if (!admitted.ok)
    return <p role="status">RP1 mechanical source closeup unavailable: {admitted.reason}</p>;
  return <MechanicalReferenceAdmitted layout={admitted.layout} initialPartId={initialPartId} />;
}
