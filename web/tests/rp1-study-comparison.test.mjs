import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import {renderToStaticMarkup} from '../node_modules/react-dom/server.node.js';
import {createServer} from '../node_modules/vite/dist/node/index.js';
import {RP1_COMPARISON_ID,RP1_SOURCE_ID,RP1_SOURCE_SHA256,RP1_STUDY_IDS,validateRp1Studies,loadRp1Studies,rp1Quantity} from '../src/workbench/rp1Studies.ts';
import {engineeringRoute,engineeringHref,isConstructionTopic} from '../src/workbench/workbenchRouting.ts';

const fixture=()=>({schema_version:1,id:RP1_COMPARISON_ID,status:'unaccepted comparison',
 source_configuration:{id:RP1_SOURCE_ID,path:'configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml',sha256:RP1_SOURCE_SHA256},
 load_definition:{required_moment_Nm:8.83,proposed_moment_Nm:2.905255,proposal_adopted:false,note:'Retained older-planform envelope; proposed correction not adopted.'},
 studies:RP1_STUDY_IDS.map((id,index)=>({id,label:index?'FR1':'FP1',status:index?'failed finite-support sensitivity':'nominal component screen only',adopted:false,installed_accepted:false,source:{path:`fixture/study-${index}.json`,sha256:'a'.repeat(64)},maturity:'Preliminary model; no installed qualification.',displacement:{reported_mm:index?1.185:0.961,attachment_budget_mm:index?null:0.1,limit_mm:1,note:index?'Finite support sensitivity failed; complete installed prediction unavailable.':'Includes assumed attachment budget; not a pass.'},mass:{conditional_credit_g:index?20.840:4.670,note:'Conditional saving, replacement function not demonstrated.'},nodes:[{id:'panel',label:'Panel',status:'estimated',note:'Material bound unavailable.'},{id:'joint',label:'Attachment',status:'unverified',note:'Installed joint unknown.'}],edges:[{from:'panel',to:'joint',label:'Recorded relationship'}],unknowns:['Conditioned material properties','Installed contact and adhesive stiffness'],sources:[{path:'fixture/source.md'}]}))});

test('exact source identities, unknown values and unaccepted states are retained',()=>{
 const value=fixture();assert.equal(validateRp1Studies(value),value);
 assert.equal(rp1Quantity(null,'mm'),'Unavailable');assert.equal(rp1Quantity(0,'mm'),'0.000 mm');
 for(const mutate of [x=>x.load_definition.required_moment_Nm=2.905,x=>delete x.load_definition.required_moment_Nm,x=>x.studies[0].displacement.limit_mm=2,x=>delete x.studies[0].displacement.limit_mm,x=>x.studies[0].displacement.attachment_budget_mm=0,x=>x.id='other',x=>x.source_configuration.sha256='b'.repeat(64),x=>x.studies[0].id='borrowed-CAD',x=>x.studies[0].installed_accepted=true,x=>x.studies[0].adopted=true,x=>x.load_definition.proposal_adopted=true,x=>delete x.studies[0].displacement.reported_mm,x=>x.studies[0].displacement.reported_mm=NaN,x=>x.studies[0].edges[0].to='missing',x=>x.studies.push(x.studies[0])]){
  const invalid=fixture();mutate(invalid);assert.throws(()=>validateRp1Studies(invalid),/invalid or incompatible/);
 }
 assert.deepEqual(validateRp1Studies({...value,studies:[]}).studies,[]);
});

test('prepared loader has one explicit source, exposes errors, and never substitutes an API or CAD source',async()=>{
 const calls=[];const signal=new AbortController().signal;
 const loaded=await loadRp1Studies(signal,async(path,options)=>{calls.push(path);assert.equal(options.signal,signal);return new Response(JSON.stringify(fixture()));});
 assert.equal(loaded.id,RP1_COMPARISON_ID);assert.deepEqual(calls,['/engineering-workbench/rp1-studies.json']);
 for(const status of [404,500])await assert.rejects(loadRp1Studies(signal,async()=>new Response('missing',{status})),new RegExp(String(status)));
 await assert.rejects(loadRp1Studies(signal,async()=>new Response('{}')),/invalid or incompatible/);
});

test('RP1 route retains workspace context and avoids unrelated construction endpoint loads',()=>{
 assert.equal(engineeringRoute('?workspace=engineering&view=rp1-studies').view,'rp1-studies');
 assert.equal(isConstructionTopic('rp1-studies'),true);
 assert.equal(engineeringHref('http://local/?design=archived&run=recorded','rp1-studies'),'/?design=archived&run=recorded&workspace=engineering&view=rp1-studies');
 assert.equal(engineeringRoute('?view=g80-f2').view,'g80-f2');
});

test('SSR comparison preserves nominal budget vs failed finite case, source provenance and local accessible graphic',async()=>{
 const server=await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
 try{
  const {Rp1StudyComparisonView,Rp1StudyGraph}=await server.ssrLoadModule('/src/workbench/Rp1StudyComparison.tsx');
  const html=renderToStaticMarkup(React.createElement(Rp1StudyComparisonView,{snapshot:fixture()}));
  for(const text of ['UNACCEPTED','0.961 mm','0.100 mm','1.185 mm','Unavailable','8.830 N·m','2.905 N·m','not adopted','not a pass','complete installed prediction unavailable','4.670 g','20.840 g','no CAD association','fixture/study-0.json','fixture/study-1.json'])assert.ok(html.includes(text),text);
  assert.match(html,/tabindex="0"/);assert.match(html,/aria-pressed="true"/);assert.match(html,/aria-live="polite"/);
  const empty=renderToStaticMarkup(React.createElement(Rp1StudyComparisonView,{snapshot:{...fixture(),studies:[]}}));assert.match(empty,/No study records supplied/);
  const graph=renderToStaticMarkup(React.createElement(Rp1StudyGraph,{study:fixture().studies[0],selected:'joint',onSelect:()=>{}}));assert.match(graph,/<polygon/);assert.ok(graph.includes(RP1_STUDY_IDS[0]));assert.ok(graph.includes('aria-label="Attachment: unverified"'));
 }finally{await server.close();}
});
