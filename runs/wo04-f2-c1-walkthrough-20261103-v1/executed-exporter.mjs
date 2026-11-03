/** Recorded connection-study React/SVG exports; offline only, no physics. */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve, relative } from 'node:path';
import { performance } from 'node:perf_hooks';
import React from '../web/node_modules/react/index.js';
import { renderToStaticMarkup } from '../web/node_modules/react-dom/server.node.js';
import { createServer } from '../web/node_modules/vite/dist/node/index.js';
const root=resolve(import.meta.dirname,'..');
const out=resolve(root,'output/engineering-f2-c1');
const rec=resolve(root,'build/wo04-f2-c1-drawings');
const input=resolve(root,'web/public/engineering-workbench/f2-c1.json');
const sha=x=>createHash('sha256').update(x).digest('hex');
const raw=readFileSync(input),snapshot=JSON.parse(raw);
assert.equal(snapshot.identity.candidate_id,'G80-F2-C1');
for(const source of snapshot.sources)assert.equal(sha(readFileSync(resolve(root,source.path))),source.sha256,`Changed ${source.path}`);
mkdirSync(out,{recursive:true});mkdirSync(rec,{recursive:true});
const server=await createServer({configFile:false,root:resolve(root,'web'),server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
let drawings;
try{
 const module=await server.ssrLoadModule('/src/workbench/F2ConnectionStudy.tsx');
 drawings=[['connection-route',module.F2ConnectionGraph,{snapshot,selectedNodeId:'tabs',onSelectNode(){}}],['blind-notch-section',module.F2ConnectionAxialCut,{snapshot}]].map(([name,component,props])=>({name,svg:renderToStaticMarkup(React.createElement(component,props))}));
}finally{await server.close();}
const started=performance.now(),artifacts=[];
for(const drawing of drawings){
 assert.match(drawing.svg,/^<svg\b/);assert.doesNotMatch(drawing.svg,/(?:="(?:NaN|undefined|Infinity)"|<script\b|<foreignObject\b)/);
 const size=drawing.svg.match(/viewBox="0 0 ([0-9.]+) ([0-9.]+)"/);assert.ok(size);
 const svg=drawing.svg.replace('<svg ',`<svg xmlns="http://www.w3.org/2000/svg" width="${size[1]}" height="${size[2]}" `);
 const svgFile=resolve(out,drawing.name+'.svg'),pngFile=resolve(out,drawing.name+'.png');writeFileSync(svgFile,svg+'\n');
 const remaining=120000-(performance.now()-started);assert.ok(remaining>1000);
 const stdout=execFileSync('/usr/bin/swift',['-module-cache-path',resolve(root,'build/wo04-focused-2d-v2/swift-module-cache'),resolve(root,'runs/wo04-offline-render-feasibility-20261102-v4/native_image_document.swift'),svgFile,pngFile],{encoding:'utf8',timeout:Math.floor(remaining)});
 artifacts.push({name:drawing.name,svg:relative(root,svgFile),svg_sha256:sha(readFileSync(svgFile)),png:relative(root,pngFile),png_sha256:sha(readFileSync(pngFile)),renderer_output:stdout});
}
const code=['web/src/workbench/F2ConnectionStudy.tsx','web/src/workbench/f2ConnectionStudyTypes.ts','web/src/workbench/f2ConnectionStudy.css','scripts/wo04_export_f2_c1_drawings.mjs'];
const record={status:'offline_render_complete_pending_visual_inspection',identity:snapshot.identity,prepared_sha256:sha(raw),sources:snapshot.sources,rendered_sources:code.map(path=>({path,sha256:sha(readFileSync(resolve(root,path)))})),artifacts,wall_s:(performance.now()-started)/1000,wall_budget_s:120,browser_verified:false,engineering_accepted:false};
writeFileSync(resolve(rec,'record.json'),JSON.stringify(record,null,2)+'\n');
console.log(JSON.stringify({wall_s:record.wall_s,artifacts:artifacts.map(a=>a.name)}));
