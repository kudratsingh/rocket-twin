import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import {
  ASSEMBLY_EDGES,
  ASSEMBLY_NODES,
  ASSEMBLY_SOURCES,
  ASSEMBLY_STEPS,
  RP1_ASSEMBLY_CONFIGURATION,
  RP1_ASSEMBLY_SOURCE_COMMIT,
  RP1_ASSEMBLY_SPECIFICATION,
  assemblyDesignTarget,
  assemblyNode,
  assemblySourceHref,
  assemblyStep,
  matchesAssemblySource,
} from '../src/workbench/rp1AssemblyData.ts';

const core = JSON.parse(
  readFileSync(
    new URL('../../docs/studies/rp1-inspection-geometry-20261107/manifest.json', import.meta.url),
  ),
);
const definition = readFileSync(
  new URL('../../configs/studies/rp1-attachment-definition-v2.yaml', import.meta.url),
  'utf8',
);
const record = JSON.parse(
  readFileSync(
    new URL('../../runs/wo03-rp1-attachment-definition-20261103-v2/record.json', import.meta.url),
  ),
);
function vehicle() {
  return {
    id: core.id,
    identity: { ...core.identity },
    parts: core.parts.map((row) => ({
      id: row.id,
      type: 'source',
      material: 'source',
      parent: null,
      learn: '',
    })),
    summary: {},
  };
}

test('assembly source pins match actual unchanged local bytes and owner-specified source checkpoint', () => {
  assert.equal(RP1_ASSEMBLY_SOURCE_COMMIT, '2308648ecd2c4dbce857350316088524c10986ec');
  for (const [id, source] of Object.entries(ASSEMBLY_SOURCES)) {
    const bytes = readFileSync(new URL(`../../${source.path}`, import.meta.url));
    assert.equal(createHash('sha256').update(bytes).digest('hex'), source.sha256, id);
    assert.equal(
      assemblySourceHref(id),
      `https://github.com/kudratsingh/rocket-twin/blob/${RP1_ASSEMBLY_SOURCE_COMMIT}/${source.path}`,
    );
  }
  assert.equal(ASSEMBLY_SOURCES.specification.sha256, core.identity.specification_sha256);
  assert.equal(ASSEMBLY_SOURCES.definition.sha256, core.identity.definition_sha256);
  assert.equal(ASSEMBLY_SOURCES.record.sha256, core.identity.record_sha256);
  assert.equal(record.adopted, false);
  assert.equal(record.fin.bonded_panel_stress_screen_pass_only, false);
  assert.equal(record.fin.factored_moment_Nm, 8.83);
  assert.equal(record.fin.factored_force_N, 331.125);
  assert.match(definition, /finished_capacity_N: null/);
});

test('every reading step maps actual stable parts, diagram nodes and exact source locators', () => {
  const current = vehicle(),
    before = JSON.stringify(current);
  const ids = new Set(current.parts.map((part) => part.id));
  const nodes = new Set(ASSEMBLY_NODES.map((node) => node.id));
  assert.equal(nodes.size, ASSEMBLY_NODES.length);
  assert.equal(new Set(ASSEMBLY_STEPS.map((step) => step.id)).size, 7);
  for (const node of ASSEMBLY_NODES) {
    assert.equal(assemblyNode(node.id), node);
    assert.ok(node.parts.length > 0 && node.parts.every((id) => ids.has(id)));
    assert.equal(new Set(node.parts).size, node.parts.length);
  }
  for (const edge of ASSEMBLY_EDGES) assert.ok(nodes.has(edge.from) && nodes.has(edge.to));
  for (const step of ASSEMBLY_STEPS) {
    assert.equal(assemblyStep(step.id), step);
    assert.ok(step.nodes.length && step.nodes.every((id) => nodes.has(id)));
    assert.ok(step.checks.length && step.limit.length > 50);
    assert.ok(
      step.citations.length &&
        step.citations.every(
          (citation) =>
            Object.hasOwn(ASSEMBLY_SOURCES, citation.source) && citation.locator.length > 10,
        ),
    );
  }
  assert.equal(assemblyNode('foreign'), null);
  assert.equal(assemblyStep('foreign'), null);
  assert.equal(JSON.stringify(current), before);
});

test('source guard and exact-part Design targets reject revision/inventory drift and traversal', () => {
  const current = vehicle();
  assert.equal(matchesAssemblySource(current), true);
  for (const mutate of [
    (v) => {
      v.id = 'historical';
    },
    (v) => {
      v.identity.configuration_id = 'foreign';
    },
    (v) => {
      v.identity.specification_sha256 = '0'.repeat(64);
    },
    (v) => {
      v.identity.definition_sha256 = '0'.repeat(64);
    },
    (v) => {
      v.identity.record_sha256 = '0'.repeat(64);
    },
    (v) => {
      v.identity.inspection_geometry_sha256 = '0'.repeat(64);
    },
    (v) => {
      v.parts.pop();
    },
    (v) => {
      v.parts[1] = { ...v.parts[0] };
    },
    (v) => {
      v.parts[1].id = 'foreign';
    },
  ]) {
    const copy = structuredClone(current);
    mutate(copy);
    assert.equal(matchesAssemblySource(copy), false);
    assert.equal(assemblyDesignTarget(copy, 'motor_tube'), null);
  }
  for (const partId of new Set(ASSEMBLY_NODES.flatMap((node) => node.parts))) {
    const target = assemblyDesignTarget(current, partId);
    const route = new URL(target.href, 'http://localhost');
    assert.equal(target.partId, partId);
    assert.equal(target.configurationId, RP1_ASSEMBLY_CONFIGURATION);
    assert.equal(target.specificationSha256, RP1_ASSEMBLY_SPECIFICATION);
    assert.equal(route.searchParams.get('part'), partId);
    assert.equal(route.searchParams.get('design'), current.id);
    assert.equal(route.searchParams.get('spec'), current.identity.specification_sha256);
    assert.equal(route.searchParams.get('workspace'), 'design');
  }
  assert.equal(assemblyDesignTarget(current, '../../motor'), null);
});

test('critical source conditions are represented without turning concepts into accepted actions', () => {
  const combined = JSON.stringify(ASSEMBLY_STEPS);
  for (const phrase of [
    'figure-eight-on-a-bight',
    'both original sewn loops',
    'must not occupy the 4.5 mm notch',
    'no epoxy or CA',
    'before direct sight is lost',
    'cure witnesses',
    'no direct butt contact',
    'without destructive access',
    'retires that assembly',
    'no half-force',
    'thermal/chafe',
  ])
    assert.ok(combined.includes(phrase), phrase);
  assert.ok(assemblyStep('open-inspection').summary.includes('aft ring remains off'));
  assert.ok(assemblyStep('aft-motor').limit.includes('No motor installation/removal'));
  assert.ok(assemblyStep('service-retire').summary.includes('outside the mouth'));
  assert.ok(assemblyStep('forward-root').limit.includes('optimistic wood-panel screen fails'));
});

test('standalone SSR presents every step, highlighted schematic and guarded source return', async (t) => {
  const vite = await createServer({
    configFile: false,
    root: new URL('..', import.meta.url).pathname,
    server: { middlewareMode: true, hmr: false, ws: false },
    appType: 'custom',
    logLevel: 'silent',
  });
  try {
    const { default: Walkthrough } = await vite.ssrLoadModule(
      '/src/workbench/Rp1AssemblyWalkthrough.tsx',
    );
    const render = (props) => renderToStaticMarkup(React.createElement(Walkthrough, props));
    await t.test(
      'all seven actual source steps expose keyboard semantics, citations and open gates',
      () => {
        const current = vehicle();
        for (const step of ASSEMBLY_STEPS) {
          const html = render({ vehicle: current, initialStepId: step.id });
          assert.ok(html.includes(step.title));
          assert.ok(html.includes(step.summary));
          assert.match(html, /CONSTRUCTION \/ SERVICE CONCEPT/);
          assert.match(html, /not approved build instructions/);
          assert.match(html, /Failed fin screen/);
          assert.match(html, /7.301 MPa and 1.805 mm/);
          assert.match(html, /finished cord\/loop\/knot strength remain unverified/);
          assert.match(html, /five inquiries are UNSENT/);
          assert.match(html, /aria-current="step"/);
          assert.match(html, /role="button" tabindex="0"/);
          assert.match(html, /aria-pressed="true"/);
          assert.match(html, /<svg/);
          assert.match(html, /rp1-assembly-node is-active/);
          assert.match(html, /Previous concept step/);
          assert.match(html, /Next concept step/);
          assert.ok(html.includes(`blob/${RP1_ASSEMBLY_SOURCE_COMMIT}/`));
          assert.ok(html.includes('workspace=design&amp;design=G80-F2-RP1-AD1-definition-v2'));
          assert.ok(html.includes(`spec=${RP1_ASSEMBLY_SPECIFICATION}`));
          assert.doesNotMatch(html, /<dialog|<canvas|<form|Mark complete|mailto:|Buy now/);
        }
      },
    );
    await t.test(
      'foreign source and unknown initial step show unavailable rather than replacement content',
      () => {
        const foreign = render({ vehicle: { ...vehicle(), id: 'historical' } });
        assert.match(foreign, /Assembly walkthrough unavailable for this source/);
        assert.doesNotMatch(foreign, /<svg|<button|href=/);
        const step = render({ vehicle: vehicle(), initialStepId: 'foreign' });
        assert.match(step, /Assembly concept step unavailable/);
        assert.doesNotMatch(step, /<svg|<button|href=/);
      },
    );
  } finally {
    await vite.close();
  }
});
