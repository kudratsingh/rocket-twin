/** Static scene labels without a nested React DOM root; no measurements are inferred. */
import { useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { Vector3 } from 'three';
import type { Camera, Group, Object3D, OrthographicCamera, PerspectiveCamera } from 'three';
type TextLine = { text: string; tag?: 'span' | 'strong'; className?: string };
export type SceneLabelContent = {
  text?: string;
  lines?: readonly TextLine[];
  className?: string;
  contentClassName?: string;
  title?: string;
  center?: boolean;
  pointerEvents?: 'none' | 'auto';
};
export type SceneLabelProps = SceneLabelContent & {
  position: [number, number, number];
  distanceFactor?: number;
  zIndexRange?: [number, number];
};
/** Project the complete world transform, preserving perspective/orthographic scale. */
export function sceneLabelProjection(
  anchor: Object3D,
  camera: Camera,
  viewport: { width: number; height: number; left?: number; top?: number },
  distanceFactor?: number,
  zIndexRange: readonly [number, number] = [10, 0],
) {
  camera.updateMatrixWorld();
  anchor.updateWorldMatrix(true, false);
  const world = new Vector3().setFromMatrixPosition(anchor.matrixWorld);
  const cameraWorld = new Vector3().setFromMatrixPosition(camera.matrixWorld);
  const distance = world.distanceTo(cameraWorld);
  const depth = world.clone().sub(cameraWorld).dot(camera.getWorldDirection(new Vector3()));
  const point = world.project(camera);
  const perspective = camera as PerspectiveCamera;
  const orthographic = camera as OrthographicCamera;
  const scale =
    distanceFactor === undefined
      ? 1
      : orthographic.isOrthographicCamera
        ? orthographic.zoom * distanceFactor
        : perspective.isPerspectiveCamera
          ? distanceFactor / (2 * Math.tan((perspective.fov * Math.PI) / 360) * distance)
          : 1;
  const x = ((point.x + 1) * viewport.width) / 2 + (viewport.left ?? 0);
  const y = ((1 - point.y) * viewport.height) / 2 + (viewport.top ?? 0);
  const zIndex = Math.round(
    zIndexRange[0] +
      ((zIndexRange[1] - zIndexRange[0]) * (distance - perspective.near)) /
        (perspective.far - perspective.near),
  );
  return {
    x,
    y,
    scale,
    zIndex,
    visible:
      depth > 0 &&
      viewport.width > 0 &&
      viewport.height > 0 &&
      [x, y, scale, zIndex].every(Number.isFinite) &&
      scale > 0,
  };
}
/** Each lease owns exactly one node; cleanup never queries or removes sibling labels. */
export function mountSceneLabel(target: HTMLElement) {
  const document = target.ownerDocument;
  const element = document.createElement('div');
  const centered = document.createElement('div');
  const content = document.createElement('div');
  Object.assign(element.style, {
    position: 'absolute',
    left: '0',
    top: '0',
    transformOrigin: '0 0',
    display: 'none',
  });
  centered.appendChild(content);
  element.appendChild(centered);
  target.appendChild(element);
  return {
    element,
    update(spec: SceneLabelContent) {
      element.className = spec.className ?? '';
      element.style.pointerEvents = spec.pointerEvents ?? 'none';
      centered.style.transform = spec.center ? 'translate3d(-50%,-50%,0)' : '';
      content.className = spec.contentClassName ?? '';
      content.title = spec.title ?? '';
      content.replaceChildren();
      if (spec.text) content.appendChild(document.createTextNode(spec.text));
      for (const line of spec.lines ?? []) {
        const node = document.createElement(line.tag ?? 'span');
        node.className = line.className ?? '';
        node.textContent = line.text;
        content.appendChild(node);
      }
    },
    dispose() {
      element.remove();
    },
  };
}
export function SceneLabel({
  position,
  distanceFactor,
  zIndexRange = [10, 0],
  ...content
}: SceneLabelProps) {
  const anchor = useRef<Group>(null);
  const lease = useRef<ReturnType<typeof mountSceneLabel> | null>(null);
  const { gl, invalidate } = useThree();
  const target = (gl.domElement.offsetParent as HTMLElement | null) ?? gl.domElement.parentElement;
  const signature = JSON.stringify(content);
  const stableContent = useMemo(() => JSON.parse(signature) as SceneLabelContent, [signature]);
  useEffect(() => {
    if (!target) return;
    const owned = mountSceneLabel(target);
    lease.current = owned;
    invalidate();
    return () => {
      owned.dispose();
      if (lease.current === owned) lease.current = null;
    };
  }, [target, invalidate]);
  useEffect(() => {
    lease.current?.update(stableContent);
    invalidate();
  }, [stableContent, target, invalidate]);
  useFrame(({ camera }) => {
    if (!anchor.current || !lease.current || !target) return;
    const canvas = gl.domElement.getBoundingClientRect();
    const container = target.getBoundingClientRect();
    const projection = sceneLabelProjection(
      anchor.current,
      camera,
      {
        width: canvas.width,
        height: canvas.height,
        left: canvas.left - container.left - target.clientLeft + target.scrollLeft,
        top: canvas.top - container.top - target.clientTop + target.scrollTop,
      },
      distanceFactor,
      zIndexRange,
    );
    const style = lease.current.element.style;
    style.display = projection.visible ? 'block' : 'none';
    style.transform = `translate3d(${projection.x}px,${projection.y}px,0) scale(${projection.scale})`;
    style.zIndex = String(projection.zIndex);
  });
  return <group ref={anchor} position={position} />;
}
