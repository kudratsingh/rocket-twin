import assert from 'node:assert/strict';
import test from 'node:test';
import {readFile} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import postcss from 'postcss';
import React from '../node_modules/react/index.js';
import {renderToStaticMarkup} from '../node_modules/react-dom/server.node.js';
import {createServer} from '../node_modules/vite/dist/node/index.js';

const css=postcss.parse(await readFile(new URL('../src/analysis/analysis.css',import.meta.url),'utf8'));
function declarations(selector){const result={};css.walkRules(rule=>{if(rule.selector.split(',').map(s=>s.trim()).includes(selector))rule.walkDecls(decl=>result[decl.prop]=decl.value);});return result;}

test('RP1 Analysis gives the renderer a definite grid row independent of flowing controls/evidence',()=>{
  const center=declarations('.rp1-recorded-analysis .analysis-center');assert.equal(center.display,'block');assert.equal(center['overflow-y'],'auto');
  const panel=declarations('.rp1-recorded-analysis .analysis-center > .viewport-panel');assert.equal(panel.display,'block');assert.equal(panel.height,'auto');assert.equal(panel.flex,'none');assert.equal(panel.overflow,'visible');
  const canvas=declarations('.rp1-recorded-analysis .viewport-panel > .canvas-wrap');assert.equal(canvas.display,'grid');assert.match(canvas['grid-template-rows'],/^clamp\(380px, 56vh, 620px\) auto auto$/);assert.equal(canvas['min-height'],'0');
  const renderer=declarations('.rp1-recorded-analysis .canvas-wrap > .inspection-camera-surface');assert.equal(renderer['grid-area'],'1 / 1');
  const controls=declarations('.rp1-recorded-analysis .canvas-wrap > .inspection-orbit-controls');assert.equal(controls['grid-area'],'2 / 1');assert.equal(controls.position,'relative');assert.equal(controls.inset,'auto');
  const form=declarations('.rp1-recorded-analysis .inspection-orbit-controls form');assert.equal(form.position,'static');assert.equal(form['max-height'],'none');
  const units=declarations('.rp1-recorded-analysis .canvas-wrap > .viewport-scale');assert.equal(units['grid-area'],'3 / 1');assert.equal(units.position,'static');
});

async function assertLayout(vehicle){
  const source=JSON.stringify(vehicle);
  const server=await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
  try{
    const {default:Analysis}=await server.ssrLoadModule('/src/analysis/Rp1RecordedAnalysis.tsx');
    const {useInspection}=await server.ssrLoadModule('/src/store.ts');const before=JSON.stringify(useInspection.getState());
    const html=renderToStaticMarkup(React.createElement(Analysis,{vehicle}));
    for(const marker of ['rp1-recorded-analysis','canvas-wrap','inspection-camera-surface','inspection-orbit-controls','inspection-analysis-status','Recorded findings','not a 3D field','Neutral inspection geometry','metre grid'])assert.ok(html.includes(marker),marker);
    assert.ok(html.indexOf('inspection-camera-surface')<html.indexOf('inspection-orbit-controls'));
    assert.ok(html.indexOf('inspection-orbit-controls')<html.indexOf('inspection-analysis-status'));
    assert.equal(JSON.stringify(useInspection.getState()),before);assert.equal(JSON.stringify(vehicle),source);
  }finally{await server.close();}
}


// Always runs in clean checkouts. These are source dimensions/identities from the
// tracked manifest, not prepared meshes, measured properties or a browser render.
test('tracked RP1 layout fixture preserves renderer/control/evidence structure and source/global state',async()=>{
 const manifest=JSON.parse(await readFile(new URL('../../docs/studies/rp1-inspection-geometry-20261107/manifest.json',import.meta.url),'utf8'));
 const vehicle={id:manifest.id,label:'Source-layout fixture; no prepared geometry',snapshot_only:true,identity:manifest.identity,summary:{length_m:manifest.length_m},evidence:{},parts:manifest.parts.map(part=>({id:part.id,type:'source-layout-record',parent:null,material:'unavailable in layout fixture',learn:'',mesh_url:null,dimensions:part.source_dimensions??{},representation:{role:part.maturity,description:part.description}}))};
 await assertLayout(vehicle);
});
const prepared=new URL('../public/engineering-workbench/rp1-ad1-inspection.json',import.meta.url);
test('optional generated RP1 inspection also satisfies the layout contract', {skip:!existsSync(prepared)},async()=>{await assertLayout(JSON.parse(await readFile(prepared,'utf8')));});
