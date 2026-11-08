import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

const server = await createServer({
  configFile: false,
  root: new URL('..', import.meta.url).pathname,
  cacheDir: new URL('../../.cache/frontend-tests/workspace-failure', import.meta.url).pathname,
  server: { middlewareMode: true, hmr: false, ws: false },
  appType: 'custom',
});
const { WorkspaceFailureBoundary, workspaceRecoveryHref, workspaceRenderFailureRequested } =
  await server.ssrLoadModule('/src/workspaces/WorkspaceFailureBoundary.tsx');
await server.close();

test('diagnostic rendering fault requires development mode and the exact selected workspace', () => {
  const href = '/?workspace=replay&__previewFault=replay-render';
  assert.equal(workspaceRenderFailureRequested(false, href, 'replay'), false);
  assert.equal(workspaceRenderFailureRequested(true, href, 'replay'), true);
  assert.equal(workspaceRenderFailureRequested(true, href, 'design'), false);
  assert.equal(workspaceRenderFailureRequested(true, '/?workspace=replay', 'replay'), false);
});

test('recovery URL removes only the diagnostic while preserving exact source, part and run context', () => {
  const href =
    '/?workspace=replay&design=RP1&spec=abc&part=fin_set&run=exp-123&compare=exp-456&__previewFault=replay-render#cursor';
  const result = new URL(workspaceRecoveryHref(href), 'http://rocket-twin.local');
  assert.equal(result.searchParams.has('__previewFault'), false);
  for (const [key, value] of [
    ['workspace', 'replay'],
    ['design', 'RP1'],
    ['spec', 'abc'],
    ['part', 'fin_set'],
    ['run', 'exp-123'],
    ['compare', 'exp-456'],
  ])
    assert.equal(result.searchParams.get(key), value);
  assert.equal(result.hash, '#cursor');
});

test('failure view explains the limitation and escapes errors; ordinary children remain untouched', () => {
  const child = React.createElement('p', null, 'Valid source view');
  const boundary = new WorkspaceFailureBoundary({ workspace: 'replay', children: child });
  assert.equal(boundary.render(), child);
  boundary.state = WorkspaceFailureBoundary.getDerivedStateFromError(
    new Error('<script>bad module</script>'),
  );
  const html = renderToStaticMarkup(boundary.render());
  assert.match(html, /role="alert"/);
  assert.match(html, /Saved designs and experiment records have not been changed/);
  assert.match(html, /Reload this workspace/);
  assert.ok(html.includes('&lt;script&gt;bad module&lt;/script&gt;'));
  assert.ok(!html.includes('<script>'));
  assert.match(
    WorkspaceFailureBoundary.getDerivedStateFromError(null).error,
    /Unexpected workspace/,
  );
});
