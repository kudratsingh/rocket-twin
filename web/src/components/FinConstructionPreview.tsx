import { useEffect, useMemo, useRef, useState, type ComponentRef } from 'react';
import { Canvas, useThree } from '@react-three/fiber';
import { Edges, OrbitControls } from '@react-three/drei';
import { ExtrudeGeometry, Shape } from 'three';
import visuals from '../data/rp1FinVisuals.json';
import type { Rp1Studies } from '../workbench/rp1Studies';

type Study = (typeof visuals.studies)[number];
function profile(span: number) {
  const p = visuals.profile;
  const ratio = span / p.span_m;
  const s = new Shape();
  s.moveTo(0, 0);
  s.lineTo(span, -p.sweep_m * ratio);
  s.lineTo(span, -p.root_m + (-p.sweep_m - p.tip_m + p.root_m) * ratio);
  s.lineTo(0, -p.root_m);
  s.lineTo(0, -p.tab_offset_m - p.tab_chord_m);
  s.lineTo(-p.tab_depth_m, -p.tab_offset_m - p.tab_chord_m);
  s.lineTo(-p.tab_depth_m, -p.tab_offset_m);
  s.lineTo(0, -p.tab_offset_m);
  s.closePath();
  return s;
}
function Layer({
  span,
  thickness,
  z,
  color,
}: {
  span: number;
  thickness: number;
  z: number;
  color: string;
}) {
  const geometry = useMemo(
    () =>
      new ExtrudeGeometry(profile(span), {
        depth: thickness,
        bevelEnabled: false,
        curveSegments: 12,
      }),
    [span, thickness],
  );
  useEffect(() => () => geometry.dispose(), [geometry]);
  return (
    <mesh geometry={geometry} position={[0, 0, z - thickness / 2]}>
      <meshStandardMaterial color={color} roughness={0.7} metalness={0.03} />
      <Edges threshold={25} color="#4a5961" />
    </mesh>
  );
}
function Blank({ study, separate }: { study: Study; separate: boolean }) {
  const spacing = separate ? 0.005 : 0;
  return (
    <group>
      <Layer
        span={visuals.profile.span_m}
        thickness={study.core_m}
        z={0}
        color={study.id === 'FR1' ? '#3c454b' : '#b99262'}
      />
      {study.skin_each_m > 0 &&
        [-1, 1].map((sign) => (
          <group key={sign}>
            <Layer
              span={study.skin_span_m}
              thickness={study.bond_each_m}
              z={sign * (study.core_m / 2 + study.bond_each_m / 2 + spacing)}
              color="#e5bd58"
            />
            <Layer
              span={study.skin_span_m}
              thickness={study.skin_each_m}
              z={
                sign * (study.core_m / 2 + study.bond_each_m + study.skin_each_m / 2 + spacing * 2)
              }
              color="#424b55"
            />
          </group>
        ))}
    </group>
  );
}
function PreviewScene({
  study,
  separate,
  onZoom,
}: {
  study: Study;
  separate: boolean;
  onZoom: (fn: (factor: number) => void) => void;
}) {
  const controls = useRef<ComponentRef<typeof OrbitControls>>(null);
  const { camera, invalidate } = useThree();
  // Callback ref registers explicit controls without global keyboard interception.
  const bind = (value: ComponentRef<typeof OrbitControls> | null) => {
    controls.current = value;
    if (value)
      onZoom((factor) => {
        camera.position.sub(value.target).multiplyScalar(factor).add(value.target);
        value.update();
        invalidate();
      });
  };
  return (
    <>
      <ambientLight intensity={0.75} />
      <directionalLight position={[0.2, 0.2, 0.3]} intensity={2} />
      <directionalLight position={[-0.2, 0, -0.2]} intensity={0.5} />
      <Blank study={study} separate={separate} />
      <OrbitControls
        ref={bind}
        makeDefault
        target={[0.015, -0.065, 0]}
        minDistance={0.025}
        maxDistance={1.5}
        zoomSpeed={0.6}
        enableDamping={false}
      />
    </>
  );
}
export default function FinConstructionPreview({ snapshot }: { snapshot: Rp1Studies }) {
  const [choice, setChoice] = useState('AD1');
  const [separate, setSeparate] = useState(false);
  const [reset, setReset] = useState(0);
  const zoom = useRef<((factor: number) => void) | null>(null);
  const compatible = Object.entries(visuals.source_pins).every(([path, sha]) =>
    snapshot.studies.some((s) =>
      s.sources.some((source) => source.path === path && source.sha256 === sha),
    ),
  );
  if (!compatible || snapshot.source_configuration.sha256 !== visuals.specification_sha256)
    return (
      <p role="status">
        3D fin schematic unavailable: study/source revision does not match the recorded preview.
      </p>
    );
  const study = visuals.studies.find((s) => s.id === choice) ?? visuals.studies[0];
  return (
    <section className="fin-construction-preview">
      <h3>Try a recorded fin construction — separate visual preview</h3>
      <p>
        This changes the fin shown below. Your rocket design, complete mass and flight configuration
        are unchanged. This is a dimensioned schematic of one blank, not finished CAD or a validated
        replacement attachment.
      </p>
      <div className="fin-preview-actions">
        <label>
          Preview construction
          <select
            value={choice}
            onChange={(e) => {
              setChoice(e.target.value);
              setSeparate(false);
            }}
          >
            {visuals.studies.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
        <button onClick={() => zoom.current?.(0.8)}>Zoom in</button>
        <button onClick={() => zoom.current?.(1.25)}>Zoom out</button>
        <button onClick={() => setReset((v) => v + 1)}>Fit / reset preview</button>
        <label>
          <input
            type="checkbox"
            disabled={!study.skin_each_m}
            checked={separate}
            onChange={(e) => setSeparate(e.target.checked)}
          />{' '}
          Separate bonded layers
        </label>
      </div>
      <div
        className="fin-preview-canvas"
        role="group"
        aria-label={`${study.label} three-dimensional schematic`}
      >
        <Canvas
          key={reset}
          frameloop="demand"
          dpr={[1, 2]}
          camera={{ position: [0.16, 0.035, 0.22], fov: 40, near: 0.0001, far: 10 }}
          gl={{ antialias: true }}
        >
          <color attach="background" args={['#182730']} />
          <PreviewScene
            study={study}
            separate={separate}
            onZoom={(fn) => {
              zoom.current = fn;
            }}
          />
        </Canvas>
      </div>
      <p className="small">
        Illustrative colours:{' '}
        {study.id === 'FR1' ? 'dark grey = carbon core' : 'tan = plywood core'}
        {study.skin_each_m > 0 ? ' · gold = adhesive film · dark grey = carbon faces' : ''}.
      </p>
      <p className="small">
        Drag to rotate · scroll/pinch to zoom · right-drag to pan.{' '}
        {separate
          ? 'Layers are separated by illustrative5mm gaps; these gaps are not construction dimensions.'
          : 'Bonded dimensions shown at nominal recorded thickness.'}
      </p>
      <p>
        <strong>Unadopted:</strong> {study.status}
      </p>
      <details>
        <summary>Dimensions, sources and model limits</summary>
        <dl className="data-list">
          <div>
            <dt>Panel root / tip / span</dt>
            <dd>
              {[visuals.profile.root_m, visuals.profile.tip_m, visuals.profile.span_m]
                .map((v) => (v * 1000).toFixed(0))
                .join(' / ')}{' '}
              mm
            </dd>
          </div>
          <div>
            <dt>Core thickness</dt>
            <dd>{(study.core_m * 1000).toFixed(3)} mm</dd>
          </div>
          <div>
            <dt>Carbon / adhesive each face</dt>
            <dd>
              {(study.skin_each_m * 1000).toFixed(3)} /{(study.bond_each_m * 1000).toFixed(3)} mm
            </dd>
          </div>
        </dl>
        <p>{visuals.nominal_basis}</p>
        <p>Missing: {visuals.missing.join('; ')}.</p>
        <code>{study.record_id}</code>
      </details>
    </section>
  );
}
