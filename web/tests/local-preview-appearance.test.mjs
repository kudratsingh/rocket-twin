import assert from 'node:assert/strict';
import test from 'node:test';
import {
  Group,
  Mesh,
  BoxGeometry,
  MeshStandardMaterial,
} from '../node_modules/three/build/three.module.js';
import { applyLocalPreviewGhost } from '../src/parts-bank/localPreviewAppearance.ts';

test('ghosting deduplicates shared materials and restores exact display properties', () => {
  const scene = new Group();
  const shared = new MeshStandardMaterial({ opacity: 0.9, transparent: false, depthWrite: true });
  const translucent = new MeshStandardMaterial({
    opacity: 0.12,
    transparent: true,
    depthWrite: false,
  });
  const geometry = new BoxGeometry(); // Synthetic display-helper test, not rocket/CAD evidence.
  scene.add(new Mesh(geometry, shared), new Mesh(geometry, [shared, translucent]));
  const beforeVertices = [...geometry.attributes.position.array];
  const color = shared.color.getHex();
  const restore = applyLocalPreviewGhost(scene);
  assert.equal(shared.opacity, 0.2);
  assert.equal(shared.transparent, true);
  assert.equal(shared.depthWrite, false);
  assert.equal(translucent.opacity, 0.12);
  restore();
  assert.deepEqual([shared.opacity, shared.transparent, shared.depthWrite], [0.9, false, true]);
  assert.deepEqual(
    [translucent.opacity, translucent.transparent, translucent.depthWrite],
    [0.12, true, false],
  );
  const version = shared.version;
  restore();
  assert.equal(shared.version, version);
  assert.equal(shared.color.getHex(), color);
  assert.deepEqual([...geometry.attributes.position.array], beforeVertices);
  geometry.dispose();
  shared.dispose();
  translucent.dispose();
});

test('empty scenes have safe repeatable appearance cleanup', () => {
  const restore = applyLocalPreviewGhost(new Group());
  restore();
  restore();
});
