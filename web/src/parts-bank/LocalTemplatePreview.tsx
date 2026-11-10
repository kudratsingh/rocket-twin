import { Component, Suspense, useEffect, useRef, useState } from 'react';
import type { ComponentRef, ReactNode } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { Box3, Mesh, MOUSE, PerspectiveCamera, Sphere, Vector3 } from 'three';
import type { Group } from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { verifiedTemplateAsset } from './templateGeometry';
import type { TemplateRepresentation } from './templateGeometry';

type Command = { kind: 'fit' | 'in' | 'out'; sequence: number };

class LocalCadBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? (
      <p role="alert">
        Local 3D preview unavailable. Source details, STEP download and installed inspection remain
        available.
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

function RecipeScene({ scene, command, move }: { scene: Group; command: Command; move: boolean }) {
  const controls = useRef<ComponentRef<typeof OrbitControls>>(null);
  const { camera } = useThree();
  useEffect(() => {
    if (!(camera instanceof PerspectiveCamera) || !controls.current) return;
    const bounds = new Box3().setFromObject(scene);
    const sphere = bounds.getBoundingSphere(new Sphere());
    if (bounds.isEmpty() || !Number.isFinite(sphere.radius) || sphere.radius <= 0) return;
    const target = controls.current.target;
    if (command.kind === 'fit') {
      const distance = (1.35 * sphere.radius) / Math.sin((camera.fov * Math.PI) / 360);
      target.copy(sphere.center);
      camera.position
        .copy(sphere.center)
        .add(new Vector3(1, 0.65, 1).normalize().multiplyScalar(distance));
      camera.near = Math.max(0.00001, sphere.radius / 100);
      camera.far = Math.max(10, distance * 50);
      controls.current.minDistance = sphere.radius * 0.1;
      controls.current.maxDistance = distance * 40;
    } else {
      camera.position
        .sub(target)
        .multiplyScalar(command.kind === 'in' ? 0.8 : 1.25)
        .add(target);
    }
    camera.updateProjectionMatrix();
    controls.current.update();
  }, [camera, scene, command]);
  return (
    <>
      <ambientLight intensity={0.85} />
      <directionalLight position={[1, 2, 3]} intensity={1.8} />
      <directionalLight position={[-1, -1, -2]} intensity={0.6} />
      <primitive object={scene} />
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

export default function LocalTemplatePreview({
  representation,
}: {
  representation: TemplateRepresentation;
}) {
  const [scene, setScene] = useState<Group | null>(null);
  const [error, setError] = useState('');
  const [downloadState, setDownloadState] = useState('');
  const [move, setMove] = useState(false);
  const [command, setCommand] = useState<Command>({ kind: 'fit', sequence: 0 });
  useEffect(() => {
    const abort = new AbortController();
    let loaded: Group | null = null;
    setScene(null);
    setError('');
    verifiedTemplateAsset(representation.glb, abort.signal)
      .then((bytes) => new GLTFLoader().parseAsync(bytes, ''))
      .then((value) => {
        if (abort.signal.aborted) releaseScene(value.scene);
        else {
          loaded = value.scene;
          setScene(value.scene);
        }
      })
      .catch((reason: unknown) => {
        if (!abort.signal.aborted)
          setError(reason instanceof Error ? reason.message : 'Local model unavailable.');
      });
    return () => {
      abort.abort();
      if (loaded) releaseScene(loaded);
    };
  }, [representation]);
  async function download() {
    setDownloadState('Verifying local STEP bytes…');
    try {
      const bytes = await verifiedTemplateAsset(representation.step);
      const url = URL.createObjectURL(new Blob([bytes], { type: 'application/step' }));
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `RP1-template-${representation.template_id.split(':').at(-1)}.step`;
      document.body.append(anchor);
      anchor.click();
      anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setDownloadState(
        'Verified STEP download requested · millimetres, local front-center coordinates.',
      );
    } catch (reason: unknown) {
      setDownloadState(reason instanceof Error ? reason.message : 'STEP download unavailable.');
    }
  }
  return (
    <section className="template-local-preview" aria-label="Nominal local CAD inspection">
      <h3>Local CAD preview</h3>
      <p>
        Actual nominal recipe solid · metre display, millimetre STEP · separate from the installed
        rocket.
      </p>
      <div className="template-preview-controls" role="group" aria-label="Local model controls">
        <button type="button" aria-pressed={move} onClick={() => setMove(true)}>
          Move
        </button>
        <button type="button" aria-pressed={!move} onClick={() => setMove(false)}>
          Rotate
        </button>
        <button
          type="button"
          onClick={() => setCommand((value) => ({ kind: 'fit', sequence: value.sequence + 1 }))}
        >
          Fit local part
        </button>
        <button
          type="button"
          onClick={() => setCommand((value) => ({ kind: 'in', sequence: value.sequence + 1 }))}
        >
          Zoom in
        </button>
        <button
          type="button"
          onClick={() => setCommand((value) => ({ kind: 'out', sequence: value.sequence + 1 }))}
        >
          Zoom out
        </button>
      </div>
      {error ? (
        <p role="alert">
          Local preview unavailable: {error} Installed inspection remains available above.
        </p>
      ) : (
        <div className="template-preview-canvas">
          {scene ? (
            <LocalCadBoundary>
              <Canvas dpr={[1, 2]} camera={{ position: [0.2, 0.2, 0.2], fov: 40 }}>
                <Suspense fallback={null}>
                  <RecipeScene scene={scene} command={command} move={move} />
                </Suspense>
              </Canvas>
            </LocalCadBoundary>
          ) : (
            <p role="status">Verifying and loading matching local CAD…</p>
          )}
        </div>
      )}
      <div className="template-actions">
        <button type="button" onClick={() => void download()}>
          Download local part STEP
        </button>
      </div>
      {downloadState && (
        <p role="status" className="parts-bank-note">
          {downloadState}
        </p>
      )}
      <p className="parts-bank-note">
        Drag to {move ? 'pan' : 'rotate'}; wheel or pinch to zoom. Fit restores the local overview.
        No camera or view setting changes the exported geometry.
      </p>
    </section>
  );
}
