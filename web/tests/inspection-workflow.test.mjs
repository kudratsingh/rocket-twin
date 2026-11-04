import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import { drawingShortcut, inspectionSourceContext, requireInspectionSource } from '../src/workspaces/inspectionWorkflow.ts';

const component = { id: 'source-ring', type: 'ring', parent: null, material: 'fixture plywood',
  learn: 'Transfer the source load.', location: { position_m: 0.2, lateral_offset_m: [0,0] },
  dimensions: { length_m: 0.01, radius_m: 0.03 }, mesh_url: '/source/ring.glb' };
const vehicle = { id: 'recorded-reference', label: 'Exact recorded reference', summary: {},
  identity: { resolved_spec_sha256: 'exact-spec', cad_revision_sha256: 'recorded-cad' },
  parts: [component] };

test('requested identity never borrows a previous document label, CAD hash or mesh availability', () => {
  const requested = inspectionSourceContext('other-source', vehicle, { id:'other-source', label:'Requested candidate' });
  assert.equal(requested.name, 'Requested candidate');
  assert.equal(requested.current, null);
  assert.equal(requested.cadRevision, null);
  assert.equal(requested.specification, null);
  assert.equal(requested.meshCount, 0);
  assert.match(requested.maturity, /not loaded/);
  const current = inspectionSourceContext(vehicle.id, vehicle, { id:vehicle.id,label:'Older catalog label' });
  assert.equal(current.name, vehicle.label);
  assert.equal(current.cadRevision, 'recorded-cad');
  assert.equal(current.specification, 'exact-spec');
  assert.equal(current.meshCount, 1);
  assert.match(current.maturity, /1\/1/);
});

test('wrong or ambiguous source documents fail explicitly before entering inspection state', () => {
  assert.equal(requireInspectionSource(vehicle, vehicle.id), vehicle);
  assert.throws(() => requireInspectionSource(vehicle, 'candidate-F2'), /does not match/);
  assert.throws(() => requireInspectionSource(null, vehicle.id), /does not match/);
  assert.throws(() => requireInspectionSource({...vehicle,parts:[component,component]}, vehicle.id), /identities are invalid/);
  const dimensionsOnly = inspectionSourceContext(vehicle.id, { ...vehicle, identity: {}, parts:[{...component,mesh_url:null}] });
  assert.equal(dimensionsOnly.cadRevision, null);
  assert.match(dimensionsOnly.maturity, /3D geometry unavailable/);
});

test('active drawing shortcuts use drawing actions without invoking hidden section/explode state', () => {
  assert.equal(drawingShortcut('F'), 'focus');
  assert.equal(drawingShortcut('r'), 'reset');
  assert.equal(drawingShortcut('s'), 'unsupported');
  assert.equal(drawingShortcut('e'), 'unsupported');
  assert.equal(drawingShortcut('/'), null);
  assert.equal(drawingShortcut('Escape'), null);
});

test('inspection provides reachable parts/details targets and dimensions-first entry without a mesh', async () => {
  const server = await createServer({ configFile:false, root:new URL('..',import.meta.url).pathname,
    server:{middlewareMode:true,hmr:false,ws:false},appType:'custom' });
  try {
    const { InspectionWorkspace } = await server.ssrLoadModule('/src/workspaces/InspectionWorkspace.tsx');
    const { DesignVisual } = await server.ssrLoadModule('/src/workspaces/DesignVisual.tsx');
    const render = (source) => renderToStaticMarkup(React.createElement(InspectionWorkspace, {
      tree: React.createElement('input', {'aria-label':'Search parts'}),
      inspector: React.createElement('p', null, 'Long source component details remain here'),
      visual: React.createElement(DesignVisual, {vehicle:source,meshView:React.createElement('div',null,'Retained 3D fixture')}),
    }));
    const mesh = render(vehicle);
    assert.match(mesh, /data-representation="3d"/);
    assert.match(mesh, /Find a component/);
    assert.match(mesh, /Open component details/);
    assert.match(mesh, /role="region" tabindex="-1" aria-label="Component details panel"/);
    assert.match(mesh, /1 recorded component meshes/);
    const source = {...vehicle, id:'concept-source',label:'Separate concept source',snapshot_only:true,identity:{},parts:[{...component,mesh_url:null}]};
    const concept = render(source);
    assert.match(concept, /data-representation="2d"/);
    assert.match(concept, /No recorded component meshes/);
    assert.match(concept, /data-inspection-action="focus"/);
    assert.match(concept, /data-inspection-action="reset"/);
    assert.match(concept, /Separate concept source/);
    assert.doesNotMatch(concept, /recorded-cad|Exact recorded reference/);
    assert.match(concept, /Retained 3D fixture/); // Representation switching does not discard the child.
  } finally { await server.close(); }
});
