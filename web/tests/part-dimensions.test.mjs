import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';

// Small source-shaped excerpts from the archived modular inspection, not F2 CAD.
// Tests do not load ignored build/public output or require generated meshes.
const base={id:'body_upper',type:'tube',parent:null,material:'cardboard',learn:'Fixture excerpt',
 dimensions:{length_m:0.778,radius_m:0.033,inner_radius_m:0.0325,wall_m:0.0005},
 location:{position_m:0.14,lateral_offset_m:[0,0]},mass_kg:0.05603234701199932,mass_basis:'volume_density',
 mesh_url:'/fixture/body.glb',representation:{role:'manufactured',description:'Nominal CAD design; density/tolerances unmeasured.'},
 engineering:{function:'Thin tube',property_basis:'estimated',tolerances_mm:{linear:0.1}}};
const source={id:'archived-reference-fixture',summary:{},parts:[base]};

test('source-derived dimension display: tube, motor envelope, board box and tab edge cases',async()=>{
 const server=await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
 try{
  const {PartDimensions,dimensionValue,partDimensionModel}=await server.ssrLoadModule('/src/workspaces/PartDimensions.tsx');
  const render=(part,extra={})=>renderToStaticMarkup(React.createElement(PartDimensions,{vehicle:{...source,...extra,parts:[part]},partId:part.id}));
  const tube=render(base);
  for(const value of ['0.778 m (778 mm)','0.0005 m (0.5 mm)','0.14 m (140 mm)','56.032347 g','volume_density','estimated','Recorded CAD mesh available','0.1 mm (0.0001 m)','not as-built verification']) assert.ok(tube.includes(value),value);
  assert.equal(partDimensionModel(base).wallAvailable,true);
  assert.ok(!tube.includes('Wall thickness unavailable'));
  const motor=render({...base,id:'motor',dimensions:{length_m:0.128,radius_m:0.0145,diameter_m:0.029},representation:{role:'purchased_envelope'}});
  assert.ok(motor.includes('0.029 m (29 mm)'));
  assert.ok(motor.includes('Simplified or conceptual envelope'));
  assert.ok(motor.includes('Wall thickness unavailable'));
  const board=render({...base,id:'flight_computer',dimensions:{bbox_m:[0.061,0.018,0.006]},representation:{role:'purchased_envelope'}});
  assert.ok(board.includes('0.061 m (61 mm) × 0.018 m (18 mm) × 0.006 m (6 mm)'));
  assert.ok(board.includes('Box envelope (source order)'));
  const tab=render({...base,id:'tab',mesh_url:null,dimensions:{tab_length_m:0.012,tab_width_m:0.008,tab_thickness_m:0.002,sweep_m:0},representation:{role:'concept'}});
  assert.ok(tab.includes('Tab thickness'));
  assert.ok(tab.includes('0.002 m (2 mm)'));
  assert.equal(dimensionValue('sweep_m',0),'0 m (0 mm)');
  assert.equal(dimensionValue('position_m',-0.01),'-0.01 m (-10 mm)');
  assert.equal(dimensionValue('wall_m',NaN),'Unavailable — invalid source number');
  assert.equal(dimensionValue('length_m',Infinity),'Unavailable — invalid source number');
  assert.equal(dimensionValue('mass_kg',undefined),'Unavailable — not supplied');
 }finally{await server.close();}
});

test('missing geometry, mismatched identities and separate source fields do not borrow values',async()=>{
 const server=await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
 try{
  const {PartDimensions,partDimensionModel}=await server.ssrLoadModule('/src/workspaces/PartDimensions.tsx');
  const render=(part,partId=part.id)=>renderToStaticMarkup(React.createElement(PartDimensions,{vehicle:{...source,parts:[part]},partId}));
  const missing={id:'unknown',type:'unknown',parent:'absent',material:'',learn:''};
  const html=render(missing);
  for(const value of ['Dimensions unavailable','Axial length unavailable','Wall thickness unavailable','Recorded CAD mesh unavailable','Tolerances unavailable','not assumed to be zero','Mesh frame: Unavailable','mass_basis']) assert.ok(html.includes(value),value);
  assert.ok(render(missing,'other-source').includes('not mapped in source archived-reference-fixture'));
  const both={...base,dimensions:{length_m:0.2},geometry:{wall_m:0.001,length_m:0.9}};
  assert.equal(partDimensionModel(both).wallAvailable,false);
  assert.deepEqual(partDimensionModel(both).fields,{length_m:0.2});
  assert.ok(render(both).includes('Separate geometry record (not merged with dimensions)'));
  assert.ok(render({...missing,geometry:{width_m:0.02}}).includes('0.02 m (20 mm)'));
  assert.ok(render({...base,mass_kg:0,subtree_mass_kg:0.1}).includes('0 kg (0 g)'));
  assert.ok(render({...base,mass_kg:0,subtree_mass_kg:0.1}).includes('not values to add together'));
 }finally{await server.close();}
});
