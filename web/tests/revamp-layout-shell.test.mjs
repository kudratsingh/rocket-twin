import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

test('Design shell keeps one visual, mounted hidden panels, keyboard controls and identity inside Details', async () => {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    const { WorkspaceFrame, WorkspaceNavigation } = await server.ssrLoadModule(
      '/src/workspaces/WorkspaceChrome.tsx',
    );
    const { InspectionWorkspace, InspectionTools } = await server.ssrLoadModule(
      '/src/workspaces/InspectionWorkspace.tsx',
    );
    const { writeLayout, defaultLayout } = await server.ssrLoadModule(
      '/src/workspaces/layoutPreferences.ts',
    );
    const render = (workspace) =>
      renderToStaticMarkup(
        React.createElement(WorkspaceFrame, {
          workspace,
          header: React.createElement('header', { className: 'topbar' }, 'Current source picker'),
          navigation: React.createElement(WorkspaceNavigation, {
            active: workspace,
            href: '/?workspace=design&design=source-ad1',
            onNavigate() {},
          }),
          identity: React.createElement(
            'div',
            { 'data-source-hash': 'exact-source-hash' },
            'Exact source status',
          ),
          children: React.createElement(InspectionWorkspace, {
            tree: React.createElement('input', { 'aria-label': 'Find source component' }),
            visual: React.createElement(
              'div',
              { 'data-canvas-identity': 'same-source' },
              'Stable visual',
              React.createElement(InspectionTools, null, 'Advanced controls'),
            ),
            inspector: React.createElement(
              'div',
              { 'data-selected-part': 'source-part' },
              'Selected source details',
            ),
            source: React.createElement('p', null, 'Additional source notice'),
          }),
        }),
      );
    writeLayout('design', defaultLayout());
    const html = render('design');
    assert.match(html, /revamp-design-shell/);
    assert.match(html, /data-context="true" data-tools="false"/);
    assert.equal((html.match(/data-canvas-identity/g) ?? []).length, 1);
    assert.match(html, /role="separator" tabindex="0" aria-label="Resize context sidebar"/);
    assert.match(html, /aria-orientation="vertical"/);
    assert.match(html, /aria-orientation="horizontal"/);
    assert.match(html, /aria-valuenow="264"/);
    assert.match(html, /aria-valuenow="240"/);
    for (const label of [
      'Show workspace rail',
      'Parts',
      'Details',
      'Focus',
      'Reset layout',
      'Scene tools',
    ])
      assert.ok(
        html.includes(label) ||
          (label === 'Show workspace rail' && html.includes('Hide workspace rail')),
        label,
      );
    assert.match(html, /aria-label="Flight Replay"/);
    assert.match(html, /workspace=replay&amp;design=source-ad1/);
    assert.match(html, /class="revamp-context-panel revamp-details-panel"[^>]*hidden=""/);
    assert.match(html, /class="revamp-tools-content" hidden=""/);
    assert.ok(
      html.indexOf('Exact source status') > html.indexOf('class="revamp-details-panel"') ||
        html.indexOf('Exact source status') >
          html.indexOf('revamp-context-panel revamp-details-panel'),
    );
    assert.ok(
      html.indexOf('Additional source notice') > html.indexOf('Source, status &amp; limitations'),
    );
    assert.ok(
      !html.includes('Advanced controls'),
      'portal content waits for mounted target during SSR, never duplicates in canvas',
    );
    writeLayout('design', {
      ...defaultLayout(),
      railOpen: false,
      contextOpen: false,
      contextTab: 'details',
      contextWidth: 340,
      toolsOpen: true,
    });
    const collapsed = render('design');
    assert.match(collapsed, /data-rail="false"/);
    assert.match(collapsed, /data-context="false" data-tools="true"/);
    for (const marker of [
      'Stable visual',
      'Selected source details',
      'Find source component',
      'Exact source status',
      'Additional source notice',
    ])
      assert.ok(collapsed.includes(marker), marker);
    assert.equal((collapsed.match(/data-canvas-identity/g) ?? []).length, 1);
    assert.match(collapsed, /aria-valuenow="340"/);
    assert.match(collapsed, /Show workspace rail/);
    const legacy = render('engineering');
    assert.doesNotMatch(legacy, /revamp-design-shell/);
    assert.match(legacy, />Flight Replay<\/a>/);
    assert.match(legacy, /Advanced controls/);
    assert.match(legacy, /research-inspection-grid/);
    const fallback = renderToStaticMarkup(
      React.createElement(InspectionTools, null, 'Inline fallback'),
    );
    assert.equal(fallback, 'Inline fallback');
  } finally {
    await server.close();
  }
});
