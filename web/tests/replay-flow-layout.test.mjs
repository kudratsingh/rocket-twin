import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import ts from '../node_modules/typescript/lib/typescript.js';

const source = await readFile(new URL('../src/experiments/Experiment.tsx', import.meta.url), 'utf8');
const tree = ts.createSourceFile('Experiment.tsx', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
function nodes(root, predicate) {
  const found = [];
  function visit(node) { if (predicate(node)) found.push(node); ts.forEachChild(node, visit); }
  visit(root);
  return found;
}
function attribute(element, name) {
  const opening = ts.isJsxElement(element) ? element.openingElement : element;
  return opening.attributes.properties.find(p => p.name?.getText(tree) === name)?.initializer?.getText(tree);
}
function named(root, name) {
  return nodes(root, n => ts.isJsxSelfClosingElement(n) && n.tagName.getText(tree) === name);
}

test('visible replay controls and tracking status are ordered siblings outside the actual Canvas host', () => {
  const host = nodes(tree, n => ts.isJsxElement(n) && attribute(n, 'ref') === '{replayCanvasHost}')[0];
  assert.ok(host);
  assert.equal(attribute(host, 'className'), '"exp-replay"');
  const children = host.children.filter(n => !ts.isJsxText(n) || n.text.trim());
  assert.equal(children.length, 1);
  assert.equal(children[0].tagName.getText(tree), 'FlightScene');
  assert.equal(named(tree, 'FlightScene').length, 1);
  const siblings = host.parent.children;
  const controls = siblings.find(n => ts.isJsxElement(n) && attribute(n, 'className') === '"exp-scene-controls"');
  const tracking = siblings.find(n => ts.isJsxSelfClosingElement(n) && n.tagName.getText(tree) === 'CameraTrackingReadout');
  assert.ok(controls && controls.end <= host.pos);
  assert.ok(tracking && host.end <= tracking.pos);
  assert.equal(attribute(controls, 'role'), '"group"');
  assert.equal(attribute(controls, 'aria-label'), '"Visible replay controls"');
  const readout = nodes(tree, n => ts.isFunctionDeclaration(n) && n.name?.text === 'CameraTrackingReadout')[0];
  assert.ok(readout.getText(tree).includes('className="exp-camera-tracking"'));
  assert.ok(!readout.getText(tree).includes('style='), 'tracking has no inline absolute overlay');
  for (const binding of ['run={shown}', 'other={other}', 'time={time}', 'mode={mode}', 'offsets={alignment}']) {
    assert.ok(children[0].getText(tree).includes(binding));
    assert.ok(tracking.getText(tree).includes(binding));
  }
});
