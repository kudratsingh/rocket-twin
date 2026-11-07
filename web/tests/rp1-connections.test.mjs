import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import {
  RP1_CONNECTIONS_ID,
  RP1_CONNECTIONS_CONFIGURATION,
  RP1_CONNECTIONS_SHA256,
  RP1_CONNECTION_PART_IDS,
  RP1_DRAWING_HASHES,
  validateRp1Connections,
  loadRp1Connections,
  rp1ConnectionDesignHref,
  rp1ConnectionDrawingHref,
  rp1ConnectionQuantity,
} from '../src/workbench/rp1Connections.ts';

// Synthetic relationship fixture: only IDs/pins are production constants; figures are test labels.
const fixture = () => ({
  schema_version: 1,
  id: RP1_CONNECTIONS_ID,
  configuration: {
    id: RP1_CONNECTIONS_CONFIGURATION,
    path: 'configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml',
    sha256: RP1_CONNECTIONS_SHA256,
  },
  status: 'Test definition only; installed response unverified',
  part_ids: [...RP1_CONNECTION_PART_IDS],
  sources: [{ id: 'fixture', path: 'fixture/source.md', sha256: 'a'.repeat(64) }],
  drawings: Object.entries(RP1_DRAWING_HASHES).map(([id, sha256]) => ({
    id,
    label: id,
    path: `output/rp1-attachment-definition/${id}.svg`,
    sha256,
    status: 'Concept only',
  })),
  connections: ['fin-root', 'recovery'].map((id) => {
    const part = id === 'fin-root' ? 'fin_tabs' : 'rp1_kevlar_wrap';
    return {
      id,
      label: id === 'fin-root' ? 'Fin root' : 'Recovery',
      summary: 'Finite source connection; no equal sharing.',
      part_ids: [part, 'body'],
      nodes: [
        {
          id: 'input',
          label: 'Conceptual input',
          part_ids: [],
          note: 'Input only; no corresponding physical part.',
        },
        {
          id: 'joint',
          label: 'Recorded joint',
          part_ids: [part],
          note: 'Contact and finite motion remain unverified.',
        },
        {
          id: 'body',
          label: 'Body route',
          part_ids: ['body'],
          note: 'Paper support is not rigid.',
        },
      ],
      edges: [
        {
          id: 'input-joint',
          from: 'input',
          to: 'joint',
          label: 'Applied input',
          note: 'Not an equal split.',
        },
        {
          id: 'joint-body',
          from: 'joint',
          to: 'body',
          label: 'Finite transfer',
          note: 'Mixed-mode capacity unavailable.',
        },
      ],
      dimensions: [
        {
          id: 'gap',
          label: 'Nominal filled gap',
          value: 0.4,
          unit: 'mm',
          source_id: 'fixture',
          note: 'No direct butt contact.',
        },
        {
          id: 'capacity',
          label: 'Finished capacity',
          value: null,
          unit: 'N',
          source_id: 'fixture',
          note: 'No allowable supplied.',
        },
      ],
      findings: [
        {
          id: 'failed',
          label: 'Optimistic screen',
          status: 'failed-screen',
          detail: 'Saved component screen fails; not an installed measurement.',
          source_id: 'fixture',
          measurement_needed: 'Later supported construction evidence.',
        },
        {
          id: 'unknown',
          label: 'Installed response',
          status: 'unknown',
          detail: 'Complete joint response unavailable.',
          source_id: 'fixture',
          measurement_needed: 'Later authorized measurement of finite support.',
        },
        {
          id: 'limit',
          label: 'Retained load',
          status: 'requirement',
          detail: '8.83 N·m / 331.125 N, factor 3 already applied once.',
          source_id: 'fixture',
          measurement_needed: 'No lower load decision inferred.',
        },
      ],
      drawing_ids: ['01-local-attachment', '02-load-paths'],
    };
  }),
});

test('strict frozen source, complete part membership and relational provenance reject mismatches', () => {
  const good = fixture();
  assert.equal(validateRp1Connections(good), good);
  for (const mutate of [
    (x) => (x.id = 'other'),
    (x) => (x.schema_version = 2),
    (x) => (x.configuration.id = 'modular-performance-v1'),
    (x) => (x.configuration.sha256 = 'b'.repeat(64)),
    (x) => (x.configuration.path = 'old.yaml'),
    (x) => x.part_ids.pop(),
    (x) => (x.part_ids[0] = 'foreign'),
    (x) => (x.part_ids[0] = x.part_ids[1]),
    (x) => (x.connections[0] = null),
    (x) => x.connections.pop(),
    (x) => (x.connections[0].id = 'other'),
    (x) => x.connections[0].part_ids.push('unknown-part'),
    (x) => (x.connections[0].nodes[1].part_ids = ['motor']),
    (x) => x.connections[0].nodes.pop(),
    (x) => (x.connections[0].edges[0].to = 'missing-node'),
    (x) => (x.connections[0].edges[0].from = 'joint'),
    (x) => (x.connections[0].dimensions[0].value = NaN),
    (x) => delete x.connections[0].dimensions[0].value,
    (x) => (x.connections[0].dimensions[0].source_id = 'missing'),
    (x) => (x.connections[0].findings[0].status = 'passed'),
    (x) => delete x.connections[0].findings[0].measurement_needed,
    (x) => (x.sources[0].sha256 = 'unknown'),
    (x) => (x.drawings[0].sha256 = 'b'.repeat(64)),
    (x) => (x.drawings[0].path = 'historical.svg'),
    (x) => (x.connections[0].drawing_ids = ['foreign']),
  ]) {
    const invalid = fixture();
    mutate(invalid);
    assert.throws(() => validateRp1Connections(invalid), /unavailable: invalid or incompatible/);
  }
  good.drawings = [];
  assert.equal(
    validateRp1Connections(good).drawings.length,
    0,
    'absent drawing metadata remains displayable as unavailable',
  );
});

test('one API fetch, exact Design and drawing links, and no quantity arithmetic', async () => {
  const signal = new AbortController().signal;
  const calls = [];
  const value = await loadRp1Connections(signal, async (path, options) => {
    calls.push(path);
    assert.equal(options.signal, signal);
    return new Response(JSON.stringify(fixture()));
  });
  assert.equal(value.id, RP1_CONNECTIONS_ID);
  assert.deepEqual(calls, ['/api/engineering/rp1-connections']);
  const fallbackCalls = [];
  await loadRp1Connections(signal, async (path) => {
    fallbackCalls.push(path);
    return path.startsWith('/api/') ? new Response(JSON.stringify({ detail: 'Not Found' }), { status: 404 }) : new Response(JSON.stringify(fixture()));
  });
  assert.deepEqual(fallbackCalls, ['/api/engineering/rp1-connections', '/engineering-workbench/rp1-connections.json']);
  for (const status of [409, 500]) await assert.rejects(loadRp1Connections(signal, async () => new Response(JSON.stringify({ detail: 'Source mismatch' }), { status })), /Source mismatch/);
  await assert.rejects(
    loadRp1Connections(signal, async () => new Response('', { status: 404 })),
    /404/,
  );
  await assert.rejects(
    loadRp1Connections(signal, async () => new Response('{}')),
    /invalid or incompatible/,
  );
  const design = new URL(rp1ConnectionDesignHref('fin_tabs'), 'http://local');
  assert.equal(design.searchParams.get('workspace'), 'design');
  assert.equal(design.searchParams.get('design'), RP1_CONNECTIONS_CONFIGURATION);
  assert.equal(design.searchParams.get('part'), 'fin_tabs');
  assert.equal(design.searchParams.get('spec'), RP1_CONNECTIONS_SHA256);
  assert.throws(() => rp1ConnectionDesignHref('foreign'), /unavailable/);
  const drawing = fixture().drawings[0];
  const asset = new URL(rp1ConnectionDrawingHref(drawing), 'http://local');
  assert.equal(asset.pathname, '/api/engineering/rp1-connections/drawings/01-local-attachment');
  assert.equal(asset.searchParams.get('spec'), RP1_CONNECTIONS_SHA256);
  assert.equal(asset.searchParams.get('sha256'), drawing.sha256);
  assert.throws(() => rp1ConnectionDrawingHref({ ...drawing, sha256: 'b'.repeat(64) }), /mismatch/);
  assert.equal(rp1ConnectionQuantity(null, 'N'), 'Unavailable');
  assert.equal(rp1ConnectionQuantity(0, 'mm'), '0 mm');
  assert.equal(rp1ConnectionQuantity([50, 20, 14], 'mm'), '[50, 20, 14] mm (source order)');
});

async function withView(run) {
  const server = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
  });
  try {
    await run(await server.ssrLoadModule('/src/workbench/Rp1ConnectionsView.tsx'));
  } finally {
    await server.close();
  }
}

test('both accessible source graphs and selected exact part expose distinct failure, unknown and requirement evidence', async () => {
  await withView(({ Rp1ConnectionsView, Rp1ConnectionGraph }) => {
    const document = fixture();
    const html = renderToStaticMarkup(
      React.createElement(Rp1ConnectionsView, {
        document,
        connectionId: 'fin-root',
        requestedPartId: 'fin_tabs',
      }),
    );
    assert.equal((html.match(/<svg/g) ?? []).length, 2);
    for (const text of [
      'CONCEPT',
      'NOT CAD',
      'FAILED SCREEN',
      'UNKNOWN / UNVERIFIED',
      'RETAINED REQUIREMENT',
      '0.4 mm',
      'Unavailable',
      'No direct butt contact',
      '8.83 N·m / 331.125 N',
      'factor 3 already applied once',
      '1 mm',
      'UNSENT',
      'fixture/source.md',
      'fin_tabs',
    ])
      assert.ok(html.includes(text), text);
    assert.match(html, /aria-pressed="true"/);
    assert.match(html, /role="button" tabindex="0"/);
    assert.match(html, /aria-live="polite"/);
    assert.ok(html.includes(rp1ConnectionDesignHref('fin_tabs').replaceAll('&', '&amp;')));
    assert.ok(
      html.includes(rp1ConnectionDrawingHref(document.drawings[0]).replaceAll('&', '&amp;')),
    );
    const graph = renderToStaticMarkup(
      React.createElement(Rp1ConnectionGraph, {
        connection: document.connections[0],
        selectedNodeId: 'input',
        onSelectNode() {},
      }),
    );
    assert.match(graph, /no source part assigned/);
    assert.match(graph, /<polygon/);
  });
});

test('missing requested records or saved drawings stay unavailable without foreign source fallback', async () => {
  await withView(({ Rp1ConnectionsView }) => {
    const render = (props) =>
      renderToStaticMarkup(
        React.createElement(Rp1ConnectionsView, { document: fixture(), ...props }),
      );
    assert.match(
      render({ requestedPartId: 'archived-body' }),
      /Requested part archived-body is unavailable/,
    );
    assert.match(render({ connectionId: 'old-c1' }), /Requested connection old-c1 is unavailable/);
    const missingDrawings = fixture();
    missingDrawings.drawings = [];
    const html = render({
      document: missingDrawings,
      requestedPartId: 'battery',
      connectionId: 'recovery',
    });
    assert.match(html, /Connection evidence unavailable for this part/);
    assert.match(html, /Saved drawing 01-local-attachment unavailable/);
    assert.doesNotMatch(html, /<img/);
    assert.equal(
      (html.match(/<svg/g) ?? []).length,
      2,
      'missing saved images do not erase available source relationships',
    );
    const bad = fixture();
    bad.configuration.sha256 = 'b'.repeat(64);
    assert.match(render({ document: bad }), /role="alert"/);
    assert.doesNotMatch(render({ document: bad }), /<svg/);
  });
});

const actualPath = new URL('../public/engineering-workbench/rp1-connections.json', import.meta.url);
test(
  'optional prepared actual connections preserve exact AD1 membership and both graph/source relationships',
  { skip: !existsSync(actualPath) ? 'Prepared connections export absent' : false },
  async () => {
    const document = validateRp1Connections(JSON.parse(readFileSync(actualPath, 'utf8')));
    assert.equal(document.part_ids.length, 55);
    assert.equal(document.drawings.length, 4);
    await withView(({ Rp1ConnectionsView }) => {
      for (const connection of document.connections) {
        const html = renderToStaticMarkup(
          React.createElement(Rp1ConnectionsView, {
            document,
            connectionId: connection.id,
            requestedPartId: connection.part_ids[0],
          }),
        );
        assert.equal((html.match(/<svg/g) ?? []).length, 2);
        assert.ok(html.includes(document.configuration.sha256));
        for (const finding of connection.findings)
          assert.ok(html.includes(finding.label.replaceAll('&', '&amp;')));
      }
    });
  },
);
