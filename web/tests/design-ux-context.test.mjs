import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

// Frozen actual IDs/maturity/dimensions from tracked audit. Group slots and parent
// are explicitly synthetic display fixtures; backend tests verify real membership.
const geometry = JSON.parse(readFileSync(new URL('../../docs/studies/rp1-inspection-geometry-20261107/manifest.json', import.meta.url)));
const groupIds=['nose_airframe','fins_roots','motor_retention','recovery','avionics_power','launch_finish'];
const groupLabels=['Nose and airframe','Fins and roots','Motor and retention','Recovery','Avionics and power','Launch guides and finishing'];
const prepared={id:geometry.id,identity:geometry.identity,parts:geometry.parts.map(row=>({id:row.id,parent:row.id==='rp1_kevlar_wrap'?'motor_tube':null,type:'fixture',material:'source fixture',learn:'Source audit display test',representation:{maturity:row.maturity},dimensions:row.source_dimensions,mesh_url:row.mesh?`/fixture/${row.id}.glb`:null})),summary:{presentation:{id:'rp1-ad1-v2-functional-presentation-v1',schema_version:1,presentation_sha256:'4ed997e371f8b2473d9da47aee7396562cb9b4d7e031d87f9876025b136c005b',source_tuple:{configuration_id:geometry.id,specification_sha256:geometry.identity.specification_sha256,inspection_geometry_sha256:geometry.identity.inspection_geometry_sha256},geometry_compatible:true,breakdown:{kind:'staged-display-illustration',assembly_stage_end:.5,units:'m',manufacturing_clearance:false}}}};
prepared.summary.presentation.groups=groupIds.map((id,i)=>({id,label:groupLabels[i],description:'Synthetic grouping for UI test only',part_ids:prepared.parts.filter((_,j)=>j%6===i).map(p=>p.id),record_count:prepared.parts.filter((_,j)=>j%6===i).length,mesh_count:prepared.parts.filter((p,j)=>j%6===i&&p.mesh_url).length}));
test('RP1 tree exposes six complete functional groups with distinct record/mesh counts and contextual comparison', async()=>{
 const server=await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
 try {
  const {PartsTree}=await server.ssrLoadModule('/src/components/PartsTree.tsx');
  const html=renderToStaticMarkup(React.createElement(PartsTree,{parts:prepared.parts,vehicle:prepared}));
  for(const group of prepared.summary.presentation.groups) assert.ok(html.includes(group.label));
  assert.match(html,/55 records/);assert.match(html,/26 meshes/);
  assert.match(html,/Compare fin alternatives/);assert.match(html,/Frame group/);assert.match(html,/Isolate group/);
  assert.match(html,/Mass\/process allowance/);assert.match(html,/Geometry unavailable/);
 } finally {await server.close();}
});
test('meshless Details disable unsafe actions and source parentage never asserts a physical support',async()=>{
 const server=await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
 try {
  const {PartInspector}=await server.ssrLoadModule('/src/components/InspectionPanel.tsx');
  const part=prepared.parts.find(p=>/kevlar/i.test(p.id)&&!p.mesh_url);assert.ok(part);
  const html=renderToStaticMarkup(React.createElement(PartInspector,{part,parts:prepared.parts,design:prepared}));
  assert.match(html,/Frame and Isolate are unavailable/);
  assert.match(html,/<button disabled=""><svg[^]*?Focus in 3D/);
  assert.match(html,/Source-record parent/);assert.doesNotMatch(html,/>Attached to</);assert.doesNotMatch(html,/>Supports</);
 } finally {await server.close();}
});
test('fin comparisons are contextual and refuse same-name foreign source revision',async()=>{
 const server=await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
 try {
  const {FinAlternatives}=await server.ssrLoadModule('/src/components/FinAlternatives.tsx');
  const valid=renderToStaticMarkup(React.createElement(FinAlternatives,{design:prepared}));assert.match(valid,/Compare fin alternatives/);
  const invalid=renderToStaticMarkup(React.createElement(FinAlternatives,{design:{...prepared,identity:{...prepared.identity,specification_sha256:'foreign'}}}));
  assert.doesNotMatch(invalid,/Compare fin alternatives/);assert.match(invalid,/unavailable/);
 } finally {await server.close();}
});
