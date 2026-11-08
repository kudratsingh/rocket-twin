import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';

const source = await readFile(new URL('../src/experiments/Experiment.tsx', import.meta.url), 'utf8');
const tree = ts.createSourceFile('Experiment.tsx', source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
function nodes(root, predicate) {
  const found = [];
  function visit(node) { if (predicate(node)) found.push(node); ts.forEachChild(node, visit); }
  visit(root);
  return found;
}
const elements = (root, tag) => nodes(root, n => ts.isJsxElement(n) && n.openingElement.tagName.getText(tree) === tag);
function attr(element, name) {
  return element.openingElement.attributes.properties.find(p => p.name?.getText(tree) === name)?.initializer?.getText(tree);
}
const byClass = name => elements(tree, 'div').find(n => attr(n, 'className') === JSON.stringify(name));
test('one continuously mounted scene and its controls precede diagnostics beside the shared plots', () => {
  const dashboard = byClass('exp-replay-dashboard');
  assert.ok(dashboard);
  const scene = nodes(tree, n => ts.isJsxSelfClosingElement(n) && n.tagName.getText(tree) === 'FlightScene');
  assert.equal(scene.length, 1, 'no duplicate Canvas or breakpoint-specific scene');
  const plots = nodes(dashboard, n => ts.isJsxSelfClosingElement(n) && n.tagName.getText(tree) === 'Plot');
  assert.equal(plots.length, 1, 'one existing plotChannels map, no layout-dependent copy');
  for (let ancestor = scene[0].parent; ancestor && ancestor !== dashboard; ancestor = ancestor.parent) {
    assert.ok(!ts.isConditionalExpression(ancestor), 'layout must not conditionally remount the scene');
    if (ts.isJsxElement(ancestor)) assert.notEqual(ancestor.openingElement.tagName.getText(tree), 'details');
  }
  const scenePanel = elements(dashboard, 'section').find(n => attr(n, 'className') === '"exp-flight-panel"');
  for (const label of ['Replay camera', 'Replay speed', 'Replay time']) assert.ok(scenePanel.getText(tree).includes(`aria-label="${label}"`));
  assert.ok(scenePanel.getText(tree).includes('<ExactReplayTime'));
  assert.ok(plots[0].getText(tree).includes('setTime={scrubTo}'));
  assert.ok(plots[0].getText(tree).includes('offsets={alignment}'));
  assert.ok(plots[0].getText(tree).includes('window={plotWindow}'));
  const main = elements(tree, 'main')[0];
  for (const name of ['Comparison clock and plot/export range', 'Scene scale, sampling and channel interpretation', 'Playback instrumentation']) {
    const detail = elements(main, 'details').find(n => n.getText(tree).includes(name));
    assert.ok(detail && detail.pos > dashboard.end, name);
  }
  assert.ok(source.includes('aria-label="Current replay validity"'));
  assert.ok(source.includes('aria-label="Recorded events"'));
});

