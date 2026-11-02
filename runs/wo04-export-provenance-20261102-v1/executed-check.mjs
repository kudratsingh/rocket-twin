import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import { createServer } from '../web/node_modules/vite/dist/node/index.js';
import React from '../web/node_modules/react/index.js';
import { renderToStaticMarkup } from '../web/node_modules/react-dom/server.node.js';
const ROOT=resolve(import.meta.dirname,'..');
const baseline='runs/wo04-extended-drawings-20261102-v4/source-archive/ExtensionViews-rendered.tsx';
const target=resolve(ROOT,'web/src/workbench/ExtensionViews.tsx');
const document=JSON.parse(readFileSync(resolve(ROOT,'web/public/engineering-workbench/g80-c1.json')));
const extended=JSON.parse(readFileSync(resolve(ROOT,'web/public/engineering-workbench/g80-extended.json')));
const hash=(value)=>createHash('sha256').update(value).digest('hex');
const modes=['comparison','recovery','thermal','electrical','assembly','requirements'];
async function capture(historical){
  const server=await createServer({configFile:false,root:resolve(ROOT,'web'),server:{middlewareMode:true,hmr:false},appType:'custom',plugins:historical?[{name:'archived-rendered-source',enforce:'pre',load(id){if(id.split('?')[0]===target)return readFileSync(resolve(ROOT,baseline),'utf8');}}]:[]});
  try{
    const {ExtensionViews}=await server.ssrLoadModule('/src/workbench/ExtensionViews.tsx');
    const svg=[];
    for(const mode of modes){
      const markup=renderToStaticMarkup(React.createElement(ExtensionViews,{document,extended,mode,selectedPartId:null,onSelectPart:()=>{}}));
      for(const item of markup.matchAll(/<svg\b[\s\S]*?<\/svg>/g)){assert.ok(!item[0].includes('wb-ext-electrical-glossary'));svg.push({mode,sha256:hash(item[0])});}
      if(!historical&&mode==='electrical'){const g=markup.match(/<section class="wb-ext-electrical-glossary"[\s\S]*?<\/section>/);assert.ok(g&&!g[0].includes('<svg'));}
    }
    const {extensionExportDocument}=await server.ssrLoadModule('/src/workbench/extendedTypes.ts');
    const {exportMetadata}=await server.ssrLoadModule('/src/workbench/exportSvg.ts');
    const metadata=exportMetadata(extensionExportDocument(document,extended),'Engineering extension');
    assert.equal(metadata.sources.length,extended.generated_from.length);
    assert.equal(metadata.sources.length,33);
    assert.equal(document.generated_from.length,15);
    assert.equal(metadata.configuration,extended.identity.configuration_id);
    return {svg,export_source_count:metadata.sources.length};
  }finally{await server.close();}
}
const old=await capture(true),current=await capture(false);
assert.equal(current.svg.length,11);
assert.deepEqual(current.svg,old.svg);
const oldCSS=readFileSync(resolve(ROOT,'runs/wo04-extended-drawings-20261102-v4/source-archive/extensionViews-rendered.css'),'utf8');
const newCSS=readFileSync(resolve(ROOT,'web/src/workbench/extensionViews.css'),'utf8');
assert.ok(newCSS.startsWith(oldCSS));
const extraCSS=newCSS.slice(oldCSS.length);
const selectors=[...extraCSS.matchAll(/([^{}]+)\{/g)].map(m=>m[1].trim());
assert.ok(selectors.length>0 && selectors.every(s=>s.startsWith('.wb-ext-electrical-glossary')));

const record={status:'metadata_adapter_verified_all_11_SVGs_byte_identical_to_actual_V4_render_source',browser_download_clicked:false,new_native_render:false,old,current,baseline,HTML_only_CSS_additions:selectors,source_sha256:Object.fromEntries(['web/src/workbench/ExtensionViews.tsx','web/src/workbench/extendedTypes.ts','web/src/workbench/extensionViews.css',baseline].map(p=>[p,hash(readFileSync(resolve(ROOT,p)))]))};
const out=resolve(ROOT,'runs/wo04-export-provenance-20261102-v1');mkdirSync(out,{recursive:true});writeFileSync(resolve(out,'record.json'),JSON.stringify(record,null,2)+'\n');writeFileSync(resolve(out,'executed-check.mjs'),readFileSync(import.meta.filename));
console.log(JSON.stringify({status:record.status,SVGs:current.svg.length,export_sources:current.export_source_count,browser:false}));
