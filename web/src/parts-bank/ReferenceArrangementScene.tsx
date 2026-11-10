import { Component, Suspense, useEffect, useRef, useState } from 'react';
import type { ComponentRef, ReactNode } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { Html, OrbitControls } from '@react-three/drei';
import { Box3, Mesh, MOUSE, PerspectiveCamera, Sphere, Vector3 } from 'three';
import type { Group } from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { verifiedTemplateAsset } from './templateGeometry';
import type { TemplateAsset } from './templateGeometry';
import {
  admitArrangementDisplay,
  ARRANGEMENT_DISPLAY_FRAME,
  arrangementDisplayBounds,
  arrangementFramingIdentity,
  arrangementInstanceBounds,
  arrangementTranslation,
  type ArrangementBounds,
  type DisplayInstance,
} from './referenceArrangementDisplay';
import './referenceArrangementScene.css';

export type { DisplayInstance } from './referenceArrangementDisplay';
export interface ReferenceArrangementSceneProps {
  instances: DisplayInstance[];
  selectedInstanceId: string | null;
  onSelect: (id: string | null) => void;
}
type ViewCommand = { kind: 'fit' | 'in' | 'out'; sequence: number };
type AssetRequest = { id: string; asset: TemplateAsset };
const initialCamera = { position: [0.2, 0.2, 0.2] as [number, number, number], fov: 40 };
class ArrangementBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <p role="alert">
        Reference arrangement renderer unavailable. No substitute geometry is displayed.
      </p>
    ) : (
      this.props.children
    );
  }
}
function releaseScene(scene: Group) {
  scene.traverse((object) => {
    if (!(object instanceof Mesh)) return;
    object.geometry.dispose();
    for (const material of Array.isArray(object.material) ? object.material : [object.material])
      material.dispose();
  });
}
function box(bounds: ArrangementBounds): Box3 {
  return new Box3(new Vector3(...bounds.min), new Vector3(...bounds.max));
}
function ArrangementObjects({
  instances,
  scenes,
  selectedInstanceId,
  onSelect,
  move,
  command,
}: ReferenceArrangementSceneProps & {
  scenes: Map<string, Group>;
  move: boolean;
  command: ViewCommand;
}) {
  const controls = useRef<ComponentRef<typeof OrbitControls>>(null);
  const lastFraming = useRef<string | null>(null);
  const lastCommand = useRef<number | null>(null);
  const { camera } = useThree();
  const bounds = arrangementDisplayBounds(instances)!;
  const framing = arrangementFramingIdentity(instances);
  useEffect(() => {
    if (!(camera instanceof PerspectiveCamera) || !controls.current) return;
    const fresh = lastFraming.current !== framing;
    if (!fresh && lastCommand.current === command.sequence) return;
    lastFraming.current = framing;
    lastCommand.current = command.sequence;
    const sphere = box(bounds).getBoundingSphere(new Sphere());
    if (!Number.isFinite(sphere.radius) || sphere.radius <= 0) return;
    if (fresh || command.kind === 'fit') {
      const vertical = (camera.fov * Math.PI) / 360;
      const horizontal = Math.atan(Math.tan(vertical) * camera.aspect);
      const distance = (1.35 * sphere.radius) / Math.sin(Math.min(vertical, horizontal));
      controls.current.target.copy(sphere.center);
      camera.position
        .copy(sphere.center)
        .add(new Vector3(1, 0.65, 1).normalize().multiplyScalar(distance));
      camera.near = Math.max(0.00001, sphere.radius / 100);
      camera.far = Math.max(10, distance * 50);
      controls.current.minDistance = sphere.radius * 0.1;
      controls.current.maxDistance = distance * 40;
    } else {
      const offset = camera.position.clone().sub(controls.current.target);
      const distance = Math.min(
        controls.current.maxDistance,
        Math.max(
          controls.current.minDistance,
          offset.length() * (command.kind === 'in' ? 0.8 : 1.25),
        ),
      );
      camera.position.copy(controls.current.target).add(offset.setLength(distance));
    }
    camera.updateProjectionMatrix();
    controls.current.update();
  }, [camera, bounds, framing, command]);
  const selected = instances.find((row) => row.id === selectedInstanceId);
  const selectionBounds = selected ? arrangementInstanceBounds(selected) : null;
  return (
    <>
      <ambientLight intensity={0.85} />
      <directionalLight position={[1, 2, 3]} intensity={1.8} />
      <directionalLight position={[-1, -1, -2]} intensity={0.6} />
      <group name={ARRANGEMENT_DISPLAY_FRAME}>
        {instances.map((instance) => (
          <group
            key={instance.id}
            name={`planning-reference:${instance.id}`}
            position={arrangementTranslation(instance)}
            rotation={[0, 0, 0]}
            scale={1}
            onClick={(event) => {
              event.stopPropagation();
              if (event.delta <= 2) onSelect(instance.id);
            }}
          >
            <primitive object={scenes.get(instance.id)!} dispose={null} />
          </group>
        ))}
        {selected && selectionBounds && (
          <>
            <box3Helper args={[box(selectionBounds), '#8fc8ff']} raycast={() => undefined} />
            <Html position={selectionBounds.max} style={{ pointerEvents: 'none' }}>
              <span className="reference-arrangement-scene__callout">
                Selected: {selected.definition.name} · planning only
              </span>
            </Html>
          </>
        )}
      </group>
      <OrbitControls
        ref={controls}
        makeDefault
        enableDamping
        screenSpacePanning
        mouseButtons={{
          LEFT: move ? MOUSE.PAN : MOUSE.ROTATE,
          MIDDLE: MOUSE.DOLLY,
          RIGHT: move ? MOUSE.ROTATE : MOUSE.PAN,
        }}
      />
    </>
  );
}
/** One separate display Canvas; no source/asset edits, command API or model generation. */
export default function ReferenceArrangementScene(props: ReferenceArrangementSceneProps) {
  let instances: DisplayInstance[];
  try {
    instances = admitArrangementDisplay(props.instances);
  } catch {
    return (
      <p role="alert" className="reference-arrangement-scene">
        Reference arrangement source, frame or placement is invalid. No geometry was loaded.
      </p>
    );
  }
  return (
    <ValidatedArrangementScene
      key={arrangementFramingIdentity(instances)}
      {...props}
      instances={instances}
    />
  );
}
function ValidatedArrangementScene({
  instances,
  selectedInstanceId,
  onSelect,
}: ReferenceArrangementSceneProps) {
  const assetKey = JSON.stringify(
    instances
      .map((row) => {
        const asset = row.definition.representation.assets.glb;
        return { id: row.id, asset: { url: asset.url, sha256: asset.sha256, bytes: asset.bytes } };
      })
      .sort((left, right) => left.id.localeCompare(right.id)),
  );
  const [loaded, setLoaded] = useState<{ key: string; scenes: Map<string, Group> } | null>(null);
  const [failure, setFailure] = useState<{ key: string; message: string } | null>(null);
  const [move, setMove] = useState(false);
  const [command, setCommand] = useState<ViewCommand>({ kind: 'fit', sequence: 0 });
  useEffect(() => {
    const requests = JSON.parse(assetKey) as AssetRequest[];
    if (!requests.length) return;
    const abort = new AbortController();
    const owned = new Set<Group>();
    function releaseAll() {
      for (const scene of owned) releaseScene(scene);
      owned.clear();
    }
    Promise.all(
      requests.map(async ({ id, asset }) => {
        const bytes = await verifiedTemplateAsset(asset, abort.signal);
        if (abort.signal.aborted) throw new Error('Cancelled');
        const value = await new GLTFLoader().parseAsync(bytes, '');
        if (abort.signal.aborted) {
          releaseScene(value.scene);
          throw new Error('Cancelled');
        }
        owned.add(value.scene);
        return [id, value.scene] as const;
      }),
    )
      .then((entries) => {
        if (!abort.signal.aborted) setLoaded({ key: assetKey, scenes: new Map(entries) });
      })
      .catch(() => {
        if (abort.signal.aborted) return;
        abort.abort();
        releaseAll();
        setFailure({
          key: assetKey,
          message:
            'Registered local reference geometry could not be verified or loaded. No substitute geometry is displayed.',
        });
      });
    return () => {
      abort.abort();
      releaseAll();
    };
  }, [assetKey]);
  const scenes = loaded?.key === assetKey ? loaded.scenes : null;
  const error = failure?.key === assetKey ? failure.message : null;
  const ready = instances.length > 0 && scenes !== null && error === null;
  return (
    <section
      className="reference-arrangement-scene"
      aria-label="Uninstalled local reference arrangement preview"
    >
      <h3>Local reference arrangement</h3>
      <p>
        Separate uninstalled planning frame · translation only · no physical mating or fit result.
      </p>
      <div
        className="reference-arrangement-scene__controls"
        role="group"
        aria-label="Arrangement view controls"
      >
        <button type="button" disabled={!ready} aria-pressed={!move} onClick={() => setMove(false)}>
          Rotate view
        </button>
        <button type="button" disabled={!ready} aria-pressed={move} onClick={() => setMove(true)}>
          Pan view
        </button>
        <button
          type="button"
          disabled={!ready}
          onClick={() => setCommand((value) => ({ kind: 'fit', sequence: value.sequence + 1 }))}
        >
          Fit arrangement
        </button>
        <button
          type="button"
          disabled={!ready}
          onClick={() => setCommand((value) => ({ kind: 'in', sequence: value.sequence + 1 }))}
        >
          Zoom in
        </button>
        <button
          type="button"
          disabled={!ready}
          onClick={() => setCommand((value) => ({ kind: 'out', sequence: value.sequence + 1 }))}
        >
          Zoom out
        </button>
      </div>
      {instances.length === 0 ? (
        <p role="status">
          Empty arrangement. Add a reference explicitly to display its verified local geometry.
        </p>
      ) : error ? (
        <p role="alert">{error}</p>
      ) : scenes ? (
        <div className="reference-arrangement-scene__canvas">
          <ArrangementBoundary key={assetKey}>
            <Canvas dpr={[1, 2]} camera={initialCamera}>
              <Suspense fallback={null}>
                <ArrangementObjects
                  instances={instances}
                  scenes={scenes}
                  selectedInstanceId={selectedInstanceId}
                  onSelect={onSelect}
                  move={move}
                  command={command}
                />
              </Suspense>
            </Canvas>
          </ArrangementBoundary>
        </div>
      ) : (
        <p role="status">Verifying and loading exact local reference GLB bytes…</p>
      )}
      <p className="reference-arrangement-scene__hint">
        Drag to {move ? 'pan' : 'rotate'}; wheel or pinch to zoom. Selection and translation
        preserve the view; use Fit after placement changes. New instances may frame automatically.
      </p>
    </section>
  );
}
