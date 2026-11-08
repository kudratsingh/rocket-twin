import assert from 'node:assert/strict';
import test from 'node:test';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import {
  Group,
  PerspectiveCamera,
  OrthographicCamera,
} from '../node_modules/three/build/three.module.js';

const close = (actual, expected) =>
  assert.ok(Math.abs(actual - expected) < 1e-9, `${actual} != ${expected}`);
const server = await createServer({
  configFile: false,
  root: new URL('..', import.meta.url).pathname,
  server: { middlewareMode: true, hmr: false, ws: false },
  appType: 'custom',
});
const { sceneLabelProjection, mountSceneLabel } = await server.ssrLoadModule(
  '/src/components/SceneLabel.tsx',
);
await server.close();

test('scene labels retain complete parent transforms, camera projection, canvas offset and distance scale', () => {
  const camera = new PerspectiveCamera(60, 4 / 3, 0.1, 100);
  camera.position.z = 10;
  camera.lookAt(0, 0, 0);
  const parent = new Group(),
    anchor = new Group();
  parent.add(anchor);
  const centered = sceneLabelProjection(anchor, camera, { width: 800, height: 600 }, 1.8, [10, 0]);
  close(centered.x, 400);
  close(centered.y, 300);
  close(centered.scale, 1.8 / (20 * Math.tan(Math.PI / 6)));
  assert.equal(centered.visible, true);
  assert.equal(centered.zIndex, 9);
  parent.position.set(1, 2, 0);
  anchor.position.set(1, 0, 0);
  const shifted = sceneLabelProjection(anchor, camera, {
    width: 800,
    height: 600,
    left: 13,
    top: 7,
  });
  close(shifted.x, 400 + (2 / (10 * Math.tan(Math.PI / 6) * (4 / 3))) * 400 + 13);
  close(shifted.y, 300 - (2 / (10 * Math.tan(Math.PI / 6))) * 300 + 7);
  assert.equal(shifted.scale, 1);
  // Parent motion/explosion updates the exact world anchor without editing source values.
  parent.position.x = 0;
  assert.ok(sceneLabelProjection(anchor, camera, { width: 800, height: 600 }).x < shifted.x - 13);
});

test('orthographic zoom and camera changes retain labels; behind-camera/invalid anchors hide', () => {
  const camera = new OrthographicCamera(-2, 2, 1.5, -1.5, 0.1, 100);
  camera.position.z = 10;
  camera.zoom = 2;
  camera.updateProjectionMatrix();
  const anchor = new Group();
  anchor.position.x = 0.5;
  const result = sceneLabelProjection(anchor, camera, { width: 800, height: 600 }, 1.8);
  close(result.x, 600);
  close(result.y, 300);
  close(result.scale, 3.6);
  assert.equal(result.visible, true);
  anchor.position.z = 20;
  assert.equal(sceneLabelProjection(anchor, camera, { width: 800, height: 600 }).visible, false);
  anchor.position.z = 10;
  assert.equal(sceneLabelProjection(anchor, camera, { width: 800, height: 600 }).visible, false);
  anchor.position.set(0, 0, 0);
  assert.equal(sceneLabelProjection(anchor, camera, { width: 0, height: 600 }).visible, false);
  anchor.position.x = NaN;
  assert.equal(sceneLabelProjection(anchor, camera, { width: 800, height: 600 }).visible, false);
});

// Small ownership fixture, not a browser or a DOM-rendering acceptance claim.
class Node {
  constructor(document, tag = 'text') {
    this.ownerDocument = document;
    this.tag = tag;
    this.children = [];
    this.style = {};
    this.textContent = '';
  }
  appendChild(child) {
    child.parent = this;
    this.children.push(child);
    return child;
  }
  replaceChildren() {
    for (const child of this.children) child.parent = null;
    this.children = [];
    this.textContent = '';
  }
  remove() {
    if (this.parent) {
      this.parent.children = this.parent.children.filter((child) => child !== this);
      this.parent = null;
    }
  }
}
const document = {
  createElement(tag) {
    return new Node(this, tag);
  },
  createTextNode(text) {
    const node = new Node(this);
    node.textContent = text;
    return node;
  },
};

test('owned DOM lease preserves classes/text/title and survives setup-cleanup-setup without duplicates or sibling removal', () => {
  const host = new Node(document, 'host'),
    foreign = new Node(document, 'foreign');
  host.appendChild(foreign);
  const first = mountSceneLabel(host);
  first.update({
    text: 'CG',
    contentClassName: 'model-label cg-label',
    title: 'saved estimate',
    center: true,
    lines: [{ text: 'balance point · saved estimate' }],
  });
  const centered = first.element.children[0],
    content = centered.children[0];
  assert.equal(first.element.style.pointerEvents, 'none');
  assert.equal(centered.style.transform, 'translate3d(-50%,-50%,0)');
  assert.equal(content.className, 'model-label cg-label');
  assert.equal(content.title, 'saved estimate');
  assert.equal(content.children[0].textContent, 'CG');
  assert.equal(content.children[1].textContent, 'balance point · saved estimate');
  first.update({
    className: 'selected-part-anchor',
    contentClassName: 'selected-part-label',
    lines: [
      { text: 'Selected part', className: 'eyebrow' },
      { text: '<untrusted name>', tag: 'strong' },
      { text: 'Source material' },
      { text: 'Estimated envelope' },
    ],
  });
  assert.equal(host.children.length, 2);
  assert.equal(first.element.className, 'selected-part-anchor');
  assert.equal(content.children[1].tag, 'strong');
  assert.equal(content.children[1].textContent, '<untrusted name>');
  first.dispose();
  first.dispose();
  assert.deepEqual(host.children, [foreign]);
  const replayed = mountSceneLabel(host);
  replayed.update({
    text: 'CP',
    contentClassName: 'model-label',
    lines: [{ text: 'aerodynamic force point' }],
  });
  assert.equal(host.children.length, 2);
  replayed.dispose();
  assert.deepEqual(host.children, [foreign]);
});
