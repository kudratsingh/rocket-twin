import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import { componentEvidence, evidenceEndpoints, selectEvidenceEndpoint } from '../src/workspaces/inspectionEvidenceModel.ts';

const part = {id:'ring',name:'Source ring',type:'ring',parent:'body',material:'fixture',learn:'Fixture only',
  connections:[{id:'IF-1',name:'Recorded attachment',status:'unavailable',spec_parts:['ring','body','absent'],unresolved:['Contact strength unknown'],evidence:['fixture/record.json']}],
  fmea_records:[{id:'FM-1',failure_mode:'Attachment opens',status:'failed',severity:'S4',residual_risk:'Qualification unavailable'}],
  requirements:[{id:'REQ-1',status:'superseded',acceptance:'Historical bound'}],
  evidence_status:{provenance:'estimated',validation:'unvalidated',physical_verification:'required',required_physical_tests:['Proof test required']}};
const body = {id:'body',name:'Source body',parent:null,type:'tube',material:'fixture',learn:'Fixture only'};
const source = {id:'synthetic-source',summary:{},parts:[part,body]};

test('connections use declared IDs, preserve unavailable endpoints and never match display names', () => {
  assert.deepEqual(evidenceEndpoints(source,['ring','absent','Source body','ring']).map(p=>[p.id,p.mapped]), [['ring',true],['absent',false],['Source body',false]]);
  assert.equal(componentEvidence(source,'ring').parent[0].id,'body');
  assert.equal(componentEvidence(source,'body').children[0].id,'ring');
  assert.equal(componentEvidence(source,'other-source-ring'),null);
});

test('endpoint activation checks this document and preserves selection on incompatible endpoints', () => {
  const calls=[];
  assert.equal(selectEvidenceEndpoint(source,'absent',id=>calls.push(id)),false);
  assert.equal(selectEvidenceEndpoint({...source,parts:[part]},'body',id=>calls.push(id)),false);
  assert.equal(selectEvidenceEndpoint(source,'body',id=>calls.push(id)),true);
  assert.deepEqual(calls,['body']);
});

test('source evidence renders failures, unmapped endpoints, statuses and reachable local sections', async () => {
  const server=await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
  try {
    const {ComponentEvidence}=await server.ssrLoadModule('/src/workspaces/ComponentEvidence.tsx');
    const render=(selectedId,vehicle=source)=>renderToStaticMarkup(React.createElement(ComponentEvidence,{vehicle,selectedId,onSelect:()=>{},hiddenIds:['body']}));
    const html=render('ring');
    for (const text of ['synthetic-source','endpoint not mapped in this source','hidden in drawing','failed · S4','superseded','estimated','unvalidated','Proof test required','fixture/record.json','Contact strength unknown','no wiring route is inferred']) assert.ok(html.includes(text),text);
    assert.match(html,/aria-label="Component evidence sections"/);
    assert.match(html,/aria-current="true"/);
    assert.match(render('missing'),/not mapped in source synthetic-source/);
    assert.match(render(null),/Select a component/);
    const empty=render('body');
    assert.match(empty,/No failure records supplied/);
    assert.match(empty,/Evidence status not supplied/);
    assert.match(empty,/qualification remains unavailable/);
    const explicit=render('ring',{...source,parts:[{...part,evidence_status:{calculation:'calculated',measurement:'measured',availability:'unavailable'}},body]});
    for(const value of ['calculated','measured','unavailable']) assert.ok(explicit.includes(value));
  } finally { await server.close(); }
});
