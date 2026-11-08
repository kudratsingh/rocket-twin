/** Offline export of the actual source-gated PCB SVG; no browser or hardware execution. */
import {createServer} from '../web/node_modules/vite/dist/node/index.js';
import React from '../web/node_modules/react/index.js';
import {renderToStaticMarkup} from '../web/node_modules/react-dom/server.node.js';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..');
const out=resolve(root,'output/frontend-interiors-20261108/high-g-board');mkdirSync(out,{recursive:true});
const hash=v=>createHash('sha256').update(v).digest('hex');
const data=JSON.parse(readFileSync(resolve(root,'web/src/data/highGBoardLayout.json'),'utf8'));
if(hash(readFileSync(resolve(root,'configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml')))!==data.specification_sha256)throw Error('Mismatched frozen source');
const server=await createServer({configFile:false,root:resolve(root,'web'),server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
let html;
try{const {default:Board}=await server.ssrLoadModule('/src/components/HighGBoardDetail.tsx');html=renderToStaticMarkup(React.createElement(Board,{partId:data.part_id,configurationId:data.configuration_id,specificationSha256:data.specification_sha256}));}finally{await server.close();}
const originalSvg=html.match(/<svg[\s\S]*?<\/svg>/)?.[0];
const svg=originalSvg?.replace(/^(<svg[^>]*?) style="[^"]*"/, '$1');if(!svg||!svg.includes('CC BY-SA 3.0'))throw Error('Missing source SVG/license');
const file=resolve(out,'high-g-board-reference.svg');writeFileSync(file,svg);
const record={kind:'offline_actual_React_SVG',browser_verified:false,hardware_verified:false,source_sha256:data.source.sha256,data_sha256:hash(readFileSync(resolve(root,'web/src/data/highGBoardLayout.json'))),svg_sha256:hash(readFileSync(file)),native:{status:'not_requested'}};
if(process.argv.includes('--png')){
 const helper=resolve(root,'runs/wo04-offline-render-feasibility-20261102-v4/native_image_document.swift');
 if(existsSync(helper)){
  const cache=resolve(out,'swift-module-cache');mkdirSync(cache,{recursive:true});const start=performance.now();
  try{const log=execFileSync('/usr/bin/swift',['-module-cache-path',cache,helper,file,resolve(out,'high-g-board-reference.png')],{timeout:Number(process.argv.find(v=>v.startsWith('--native-budget-ms='))?.split('=')[1]??90000),encoding:'utf8'});record.native={status:'render_complete_visual_inspection_pending',seconds:(performance.now()-start)/1000,log,png_sha256:hash(readFileSync(resolve(out,'high-g-board-reference.png'))),helper_sha256:hash(readFileSync(helper))};}
  catch(error){record.native={status:'failed_or_time_limited',seconds:(performance.now()-start)/1000,error:String(error)};}
 }else record.native={status:'unavailable_existing_helper_missing'};
}
writeFileSync(resolve(out,'record.json'),JSON.stringify(record,null,2)+'\n');
writeFileSync(resolve(out,'index.html'),'<!doctype html><meta charset="utf-8"><title>High-g PCB source reference</title><h1>Adafruit5374 source PCB reference</h1><p>Offline React SVG; not browser interaction or hardware acceptance. Drawing25.4×17.78mm differs from nominal envelope25.6×17.7mm; no silent rescale. Package heights and incoming revision undefined. U1 source value ADXL343 retained. Adafruit Industries / Limor Fried, CC BY-SA3.0; full notice in SVG metadata.</p><p><a href="high-g-board-reference.svg">Open/export source SVG</a></p><img style="max-width:100%" src="high-g-board-reference.svg" alt="Source PCB outline, mounting holes and footprints">');
console.log(JSON.stringify(record));
