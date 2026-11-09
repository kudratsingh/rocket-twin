import { URL } from 'node:url';
import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

test('joint Engineering keeps the same Design frame/provider structure and exposes drawing scroll', async () => {
  const server = await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
  try {
    const {WorkspaceFrame} = await server.ssrLoadModule('/src/workspaces/WorkspaceChrome.tsx');
    const props={header:'header',navigation:'navigation',identity:'source',children:React.createElement('span',null,'retained scene')};
    const design=renderToStaticMarkup(React.createElement(WorkspaceFrame,{...props,workspace:'design'}));
    const jointDrawing=renderToStaticMarkup(React.createElement(WorkspaceFrame,{...props,workspace:'engineering',retainDesign:true}));
    const ordinary=renderToStaticMarkup(React.createElement(WorkspaceFrame,{...props,workspace:'engineering'}));
    assert.match(design,/revamp-design-shell/);assert.match(jointDrawing,/revamp-design-shell/);
    assert.match(jointDrawing,/overflow:auto;display:block/);
    assert.match(jointDrawing,/aria-label="Design panels" hidden/);
    assert.doesNotMatch(ordinary,/revamp-design-shell/);
  } finally {await server.close();}
});

test('workspace chrome keeps navigation addressable and unavailable source explicit', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { WorkspaceNavigation, WorkspaceIdentityStrip, WorkspaceFrame } =
      await server.ssrLoadModule('/src/workspaces/WorkspaceChrome.tsx');
    const { InspectionWorkspace } = await server.ssrLoadModule(
      '/src/workspaces/InspectionWorkspace.tsx',
    );
    const navigation = React.createElement(WorkspaceNavigation, {
      active: 'engineering',
      href: '/?workspace=engineering&view=g80-fixed',
      onNavigate() {},
    });
    const identity = React.createElement(WorkspaceIdentityStrip, {
      name: 'Requested synthetic source',
      maturity: 'Geometry unavailable',
      state: 'unavailable',
      details: React.createElement(
        'p',
        null,
        'Source fingerprint unavailable; retry the requested record.',
      ),
    });
    const markup = renderToStaticMarkup(
      React.createElement(WorkspaceFrame, {
        header: React.createElement('header', null, 'Test application'),
        navigation,
        identity,
        children: React.createElement(InspectionWorkspace, {
          tree: 'Parts fixture',
          visual: 'Visual fixture',
          inspector: 'Details fixture',
        }),
      }),
    );
    assert.equal((markup.match(/aria-current="page"/g) || []).length, 1);
    for (const label of ['Design', 'Engineering', 'Experiments', 'Flight Replay', 'Analysis']) {
      assert.ok(markup.includes(`>${label}</a>`));
    }
    assert.match(markup, /workspace=replay&amp;view=g80-fixed/);
    assert.match(markup, /Source unavailable/);
    assert.match(markup, /Engineering acceptance open/);
    assert.match(markup, /Source &amp; limitations/);
    assert.match(markup, /id="workspace-content"/);
    assert.match(markup, /aria-expanded="true"/);
    assert.doesNotMatch(markup, /C1|G80-F1|G80-F2/);
  } finally {
    await server.close();
  }
});
