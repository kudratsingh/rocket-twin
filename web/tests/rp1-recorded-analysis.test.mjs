import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import { rp1RecordedFindings } from '../src/analysis/rp1Recorded.ts';
const fixture = () => ({ id: 'G80-F2-RP1-AD1-definition-v2', parts: [], summary: {}, identity: { specification_sha256: '811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660', record_path: 'runs/wo03-rp1-attachment-definition-20261103-v2/record.json', record_sha256: 'bc349a24fe1cfaa4d883b9e00dc5b75387638a7be5cd4b05d9f32112ee8bd95b' }, evidence: { fin: { ideal_composite_strip_lower_deflection_only: [{ divisions: 1600, maximum_bending_Pa: 7301269.256902433, deflection_m: .0018054161114599912 }], bonded_panel_stress_screen_pass_only: false, installed_displacement: null, normal_peel_capacity: null }, connections: { finished_attachment_capacity_N: null, outer_ring_mean_shear_Pa: 567572.3292268821 }, cord_geometry: { available_external_reach_mm: 338.51332796590054, notch_min_per_flank_mm: .30000000000000016 } } });
test('saved scalar extraction preserves scope, failed result, missingness and valid zero', () => {
 const source=fixture();const result=rp1RecordedFindings(source);
 assert.equal(result.finStatus,'failed-screen');assert.equal(result.finMovementM,.0018054161114599912);assert.equal(result.installedMovementM,null);assert.equal(result.recoveryCapacityN,null);
 source.evidence.fin.installed_displacement=0;assert.equal(rp1RecordedFindings(source).installedMovementM,0);
 for (const mutate of [(v)=>v.id='modular-performance-v1',(v)=>v.identity.specification_sha256='a'.repeat(64),(v)=>v.identity.record_sha256='b'.repeat(64)]) {const bad=fixture();mutate(bad);assert.throws(()=>rp1RecordedFindings(bad),/source identity mismatch/);}
 assert.equal(rp1RecordedFindings({...fixture(),evidence:{}}).finStressPa,null);
});
test('actual RP1 source carries failed component evidence, not an installed field', { skip: !existsSync('public/engineering-workbench/rp1-ad1-inspection.json') }, () => {
 const vehicle=JSON.parse(readFileSync('public/engineering-workbench/rp1-ad1-inspection.json','utf8'));const result=rp1RecordedFindings(vehicle);assert.equal(result.finStatus,'failed-screen');assert.equal(result.installedMovementM,null);assert.equal(result.installedPeelCapacityPa,null);assert.equal(result.recoveryCapacityN,null);
});
test('actual Analysis React panel labels scalar-only evidence, units and unknowns without invented maps', async () => {
 const server=await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
 try {const {Rp1FindingsPanel}=await server.ssrLoadModule('/src/analysis/Rp1RecordedAnalysis.tsx');const html=renderToStaticMarkup(React.createElement(Rp1FindingsPanel,{vehicle:fixture()}));for(const label of ['Recorded findings','not a 3D field','FAILED SCREEN','1.805 mm','7.301 MPa','Unavailable','finished-joint capacity','spatial stress map','no failed historical baffle result'])assert.ok(html.includes(label),label);assert.doesNotMatch(html,/<canvas|<img/);}finally{await server.close();}
});
