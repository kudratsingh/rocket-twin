import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { Box3, PerspectiveCamera, Vector3 } from 'three';
import { fitOrbitFrame, inspectionFrameInsets } from '../src/components/inspectionCamera.ts';
const model = JSON.parse(
  readFileSync(
    new URL('../../docs/studies/rp1-inspection-geometry-20261107/manifest.json', import.meta.url),
    'utf8',
  ),
);
const corners = (bounds) => {
  const out = [];
  for (const x of [bounds.min.x, bounds.max.x])
    for (const y of [bounds.min.y, bounds.max.y])
      for (const z of [bounds.min.z, bounds.max.z]) out.push(new Vector3(x, y, z));
  return out;
};
test('actual RP1 full-scene and every represented small-part box fit the declared safe rectangle', () => {
  const targets = [
    ['assembly', model.bounds_m],
    ...model.parts.filter((p) => p.mesh).map((p) => [p.id, p.bounds_m]),
  ];
  const fill = 0.85;
  let checks = 0;
  for (const [label, extent] of targets)
    for (const [width, height] of [
      [1127, 782],
      [967, 602],
      [390, 780],
    ])
      for (const direction of [
        [2, 1, 3],
        [0, -3, 0],
        [3, 0, 0],
      ]) {
        const insets = inspectionFrameInsets(width, height);
        const bounds = new Box3(new Vector3(...extent[0]), new Vector3(...extent[1]));
        const target = bounds.getCenter(new Vector3());
        const position = target.clone().add(new Vector3(...direction));
        const frame = fitOrbitFrame(
          bounds,
          width / height,
          35,
          position,
          target,
          new Vector3(0, 1, 0),
          { insets, fill },
        );
        const camera = new PerspectiveCamera(35, width / height, frame.near, frame.far);
        camera.position.set(...frame.position);
        camera.up.set(...frame.up);
        camera.lookAt(new Vector3(...frame.target));
        camera.updateMatrixWorld();
        camera.updateProjectionMatrix();
        for (const point of corners(bounds)) {
          const p = point.project(camera);
          assert.ok(
            p.x >= -1 + 2 * insets.left - 1e-8 && p.x <= 1 - 2 * insets.right + 1e-8,
            `${label} x ${p.x}`,
          );
          assert.ok(
            p.y >= -1 + 2 * insets.bottom - 1e-8 && p.y <= 1 - 2 * insets.top + 1e-8,
            `${label} y ${p.y}`,
          );
          assert.ok(p.z >= -1 && p.z <= 1, `${label} depth`);
          checks++;
        }
        const finalDirection = new Vector3(...frame.position)
          .sub(new Vector3(...frame.target))
          .normalize();
        assert.ok(finalDirection.distanceTo(new Vector3(...direction).normalize()) < 1e-10);
      }
  assert.equal(checks, 27 * 3 * 3 * 8);
  // Bounding boxes conservatively contain actual exported mesh vertices (backend GLB tests).
  // This proves projection mathematics only, not observed canvas pixels/layout/controls.
});
