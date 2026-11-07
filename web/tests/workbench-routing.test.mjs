import { URL } from 'node:url';
const { Response, AbortController } = globalThis;
import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import {
  engineeringRoute,
  engineeringHref,
  engineeringTopics,
  isConstructionTopic,
  loadRecordedSource,
} from '../src/workbench/workbenchRouting.ts';

test('current construction defaults independently; explicit historical topics remain addressable', () => {
  assert.deepEqual(engineeringRoute(''), { view: 'rp1-connections', notice: null });
  for (const [view] of engineeringTopics) {
    assert.deepEqual(engineeringRoute(`?workspace=engineering&view=${view}`), {
      view,
      notice: null,
    });
  }
  assert.equal(engineeringRoute('?view=obsolete').view, 'rp1-connections');
  assert.match(engineeringRoute('?view=obsolete').notice, /Unknown engineering topic/);
  for (const view of ['a1', 'g80-fixed', 'g80-f2', 'rp1-validation']) assert.equal(isConstructionTopic(view), true);
  assert.equal(isConstructionTopic('geometry'), false);
  const url = new URL(
    engineeringHref(
      '/?workspace=engineering&design=archive&run=r1&view=geometry#joint',
      'g80-fixed',
    ),
    'http://test',
  );
  assert.equal(url.searchParams.get('design'), 'archive');
  assert.equal(url.searchParams.get('run'), 'r1');
  assert.equal(url.searchParams.get('view'), 'g80-fixed');
  assert.equal(url.hash, '#joint');
});

test('independent requested source succeeds even when the C1 endpoint is unavailable', async () => {
  const calls = [];
  const request = async (path) => {
    calls.push(path);
    return path === '/api/engineering/workbench'
      ? Response.json({ detail: 'C1 source missing' }, { status: 503 })
      : Response.json({ id: path });
  };
  for (const path of [
    '/api/engineering/workbench-g80-fixed',
    '/api/engineering/workbench-g80-f2',
    '/api/engineering/workbench-a1',
  ]) {
    const result = await loadRecordedSource(
      path,
      '/prepared',
      new AbortController().signal,
      request,
    );
    assert.equal(result.value.id, path);
    assert.equal(result.prepared, false);
  }
  assert.equal(calls.length, 3);
  assert.ok(!calls.includes('/api/engineering/workbench'));
});

test('prepared fallback requires exact missing-route response; source and corrupt data stay unavailable', async () => {
  for (const [status, detail] of [
    [404, 'Source file missing'],
    [500, 'Not Found'],
  ]) {
    const calls = [];
    const request = async (path) => {
      calls.push(path);
      return Response.json({ detail }, { status });
    };
    await assert.rejects(
      loadRecordedSource('/api/source', '/prepared', new AbortController().signal, request),
      new RegExp(String(status)),
    );
    assert.deepEqual(calls, ['/api/source']);
  }
  const calls = [];
  const fallback = await loadRecordedSource(
    '/api/source',
    '/prepared',
    new AbortController().signal,
    async (path) => {
      calls.push(path);
      return path === '/api/source'
        ? Response.json({ detail: 'Not Found' }, { status: 404 })
        : Response.json({ id: 'prepared-source' });
    },
  );
  assert.equal(fallback.prepared, true);
  assert.deepEqual(calls, ['/api/source', '/prepared']);
  await assert.rejects(
    loadRecordedSource(
      '/api/source',
      '/prepared',
      new AbortController().signal,
      async () => new Response('not JSON'),
    ),
    /JSON/,
  );
});

test('default construction shell renders before the absent C1 document guard and retains topic navigation', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { default: EngineeringWorkbench } = await server.ssrLoadModule(
      '/src/workbench/EngineeringWorkbench.tsx',
    );
    const markup = renderToStaticMarkup(React.createElement(EngineeringWorkbench));
    assert.match(markup, /Current RP1 connections/);
    assert.match(markup, /Loading source-pinned AD1 connections/);
    assert.match(markup, /aria-label="Engineering views"/);
    assert.doesNotMatch(markup, /Loading the recorded engineering walkthrough/);
    assert.equal((markup.match(/aria-current="page"/g) || []).length, 1);
  } finally {
    await server.close();
  }
});
