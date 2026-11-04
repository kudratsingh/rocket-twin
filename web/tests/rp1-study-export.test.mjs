import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import {renderToStaticMarkup} from '../node_modules/react-dom/server.node.js';
import {createServer} from '../node_modules/vite/dist/node/index.js';
import {RP1_COMPARISON_ID,RP1_SOURCE_ID,RP1_SOURCE_SHA256,RP1_STUDY_IDS} from '../src/workbench/rp1Studies.ts';
const snapshot={schema_version:1,id:RP1_COMPARISON_ID,status:'unaccepted',source_configuration:{id:RP1_SOURCE_ID,path:'configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml',sha256:RP1_SOURCE_SHA256},load_definition:{required_moment_Nm:8.83,proposed_moment_Nm:2.905255,proposal_adopted:false,note:'Unchanged'},studies:RP1_STUDY_IDS.map((id,i)=>({id,label:i?'FR1':'FP1',status:'UNACCEPTED',adopted:false,installed_accepted:false,source:{path:'fixture/source.json',sha256:'a'.repeat(64)},maturity:'Concept only',displacement:{reported_mm:i?1.185:0.961,attachment_budget_mm:i?null:0.1,limit_mm:1,note:'Unverified'},mass:{conditional_credit_g:null,note:'No credit accepted'},nodes:[{id:'panel',label:'Panel & root',status:'unqualified',note:'Bond < bound; no qualification.'},{id:'joint',label:'Joint',status:'unknown',note:'Installed contact unavailable'}],edges:[{from:'panel',to:'joint',label:'Adhesive relationship'}],unknowns:['Hot material & joint unknown'],sources:[{path:'fixture/material.md'}]}))};

test('standalone export retains actual graph, numbered key, identity, units and distinct scope without external styles',async()=>{
 const server=await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
 try{
  const {buildRp1StudySvg}=await server.ssrLoadModule('/src/workbench/rp1StudyExport.ts');
  const {Rp1StudyGraph,Rp1StudyComparisonView}=await server.ssrLoadModule('/src/workbench/Rp1StudyComparison.tsx');
  for(const [i,study] of snapshot.studies.entries()){
   const graph=renderToStaticMarkup(React.createElement(Rp1StudyGraph,{study,selected:'joint',onSelect:()=>{}}));
   const contents=graph.slice(graph.indexOf('>')+1,graph.lastIndexOf('</svg>'));
   const svg=buildRp1StudySvg(snapshot,study.id,contents);
   const flattened=svg.replace(/<[^>]*>/g,' ').replace(/\s+/g,' ');
   for(const token of ['xmlns="http://www.w3.org/2000/svg"','UNACCEPTED',RP1_SOURCE_SHA256,RP1_COMPARISON_ID,study.id,'a'.repeat(64),'Numbered relationship key','1. Panel &amp; root → Joint: Adhesive relationship','movement mm; mass g; moment N·m','Conditional mass credit: Unavailable','Bond &lt; bound','fixture/material.md','SHA256: unavailable','No CAD association','<polygon','font-family="Arial, sans-serif"'])assert.ok(svg.includes(token)||flattened.includes(token),token);
   assert.ok(flattened.includes(i?'FR1 1.185 mm is a failed finite-support sensitivity':'FP1 0.961 mm already includes the unverified 0.100 mm attachment budget'));
   assert.ok(flattened.includes(i?'Complete installed displacement remains unavailable':'not an installed pass'));
   assert.ok(!svg.includes('<script'));assert.ok(!svg.includes('blob:'));assert.ok(!svg.includes('<foreignObject'));
  }
  assert.throws(()=>buildRp1StudySvg(snapshot,'other-source','<g/>'),/unavailable/);
  assert.throws(()=>buildRp1StudySvg(snapshot,snapshot.studies[0].id,''),/unavailable/);
  assert.throws(()=>buildRp1StudySvg({...snapshot,id:'other-revision'},snapshot.studies[0].id,'<g/>'),/invalid/);
  const html=renderToStaticMarkup(React.createElement(Rp1StudyComparisonView,{snapshot}));
  for(const text of ['Export study SVG','Zoom in','Zoom out','Fit width / reset graph','zoomable relationship graph','aria-pressed="true"'])assert.ok(html.includes(text),text);
 }finally{await server.close();}
});
