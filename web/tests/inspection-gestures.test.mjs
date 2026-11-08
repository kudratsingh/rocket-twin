import assert from 'node:assert/strict';
import test from 'node:test';
import {bindInspectionOrbit,orbitWheelFactor,inspectionSurface,orbitClips,applyOrbit} from '../src/components/inspectionOrbit.ts';
import {Box3,PerspectiveCamera,Vector3} from 'three';

class Canvas {
  style={touchAction:'pan-y'};dataset={};captured=new Set();listeners=new Map();clientHeight=800;
  addEventListener(name,handler,options){const list=this.listeners.get(name)??[];list.push({handler,capture:options===true||!!options?.capture});this.listeners.set(name,list);}
  removeEventListener(name,handler){this.listeners.set(name,(this.listeners.get(name)??[]).filter(item=>item.handler!==handler));}
  setPointerCapture(id){this.captured.add(id);} hasPointerCapture(id){return this.captured.has(id);} releasePointerCapture(id){this.captured.delete(id);}
  fire(name,values={}){const event={pointerId:1,clientX:0,clientY:0,button:0,deltaY:0,deltaMode:0,preventDefault(){this.prevented=true;},stopImmediatePropagation(){this.stopped=true;},...values};for(const item of [...(this.listeners.get(name)??[])].sort((a,b)=>Number(b.capture)-Number(a.capture))){item.handler(event);if(event.stopped)break;}return event;}
}
function fixture(){const canvas=new Canvas(),calls=[];const dispose=bindInspectionOrbit(canvas,{begin:()=>calls.push(['begin']),move:(...args)=>calls.push(['move',...args]),zoom:(factor)=>calls.push(['zoom',factor])},()=>canvas.clientHeight);return {canvas,calls,dispose};}

test('click jitter is pickable; a drag returning to its start never falls through to scene picking',()=>{
  const {canvas,calls,dispose}=fixture();let picks=0,hover=0;canvas.addEventListener('click',()=>picks++);canvas.addEventListener('pointermove',()=>hover++);
  canvas.fire('pointerdown');canvas.fire('pointermove',{clientX:2});canvas.fire('pointerup',{clientX:2});canvas.fire('click');
  assert.equal(picks,1);assert.equal(calls.length,0);assert.equal(hover,1);
  canvas.fire('pointerdown');canvas.fire('pointermove',{clientX:20});canvas.fire('pointermove',{clientX:0});canvas.fire('pointerup');const click=canvas.fire('click');
  assert.equal(picks,1);assert.equal(click.prevented,true);assert.equal(hover,1,'R3F hover/raycast listeners do not intercept active drags');
  assert.deepEqual(calls,[['begin'],['move',20,0,'orbit'],['move',-20,0,'orbit']]);
  assert.equal(canvas.captured.size,0);assert.equal(canvas.dataset.orbitDragging,undefined);dispose();
});

test('pan, roll, normalized wheel/pinch and cancellation keep one gesture owner and clean up',()=>{
  const {canvas,calls,dispose}=fixture();let raycastWheels=0;canvas.addEventListener('wheel',()=>raycastWheels++);
  canvas.fire('pointerdown',{button:2});canvas.fire('pointermove',{clientX:10});canvas.fire('pointercancel');
  assert.deepEqual(calls.at(-1),['move',10,0,'pan']);
  canvas.fire('pointerdown',{altKey:true});canvas.fire('pointermove',{clientX:10});canvas.fire('pointerup');
  assert.deepEqual(calls.at(-1),['move',10,0,'roll']);
  const wheel=canvas.fire('wheel',{deltaY:100,deltaMode:0,ctrlKey:false});assert.equal(wheel.prevented,true);assert.equal(raycastWheels,0);
  assert.ok(Math.abs(orbitWheelFactor({deltaY:100,deltaMode:0,ctrlKey:false},800)-orbitWheelFactor({deltaY:6.25,deltaMode:1,ctrlKey:false},800))<1e-12);
  assert.ok(orbitWheelFactor({deltaY:-10,deltaMode:0,ctrlKey:true},800)<orbitWheelFactor({deltaY:-10,deltaMode:0,ctrlKey:false},800));
  canvas.fire('pointerdown',{pointerId:1,clientX:0});canvas.fire('pointerdown',{pointerId:2,clientX:100});canvas.fire('pointermove',{pointerId:2,clientX:200});
  assert.equal(calls.at(-1)[0],'zoom');assert.equal(calls.at(-1)[1],.5);
  dispose();assert.equal(canvas.captured.size,0);assert.equal(canvas.style.touchAction,'pan-y');assert.equal(canvas.dataset.orbitDragging,undefined);
  const count=calls.length;canvas.fire('pointermove',{pointerId:2,clientX:300});assert.equal(calls.length,count);
});

test('view-depth near plane retains precision outside geometry and remains safe for close interior bounds',()=>{
  const bounds=new Box3(new Vector3(-.05,0,-.05),new Vector3(.05,1,.05));
  const camera=new PerspectiveCamera(35,1.5,.001,100),target=new Vector3(0,.5,0);
  applyOrbit(camera,target,3,{azimuth:35,tilt:25,roll:15});
  const clips=orbitClips(bounds,camera,target);assert.ok(clips.near>.1,'manual orbit does not collapse a tight exterior near plane to micrometres');assert.ok(clips.far/clips.near<100);
  applyOrbit(camera,target,.001,{azimuth:35,tilt:25,roll:15});
  const interior=orbitClips(bounds,camera,target);assert.ok(interior.near>0&&interior.near<.001&&interior.far>1);
  assert.equal(inspectionSurface('cardboard').metalness,0);assert.ok(inspectionSurface('aluminium').metalness>0);assert.equal(inspectionSurface('unknown estimate').metalness,0);
});

test('missing source normals are generated privately without changing source vertices, indices or bounds',async()=>{
  const {BoxGeometry}=await import('three');const {inspectionNormals}=await import('../src/components/inspectionOrbit.ts');
  const source=new BoxGeometry(.1,.2,.3);source.deleteAttribute('normal');source.computeBoundingBox();
  const position=Array.from(source.getAttribute('position').array),indices=Array.from(source.index.array),bounds=source.boundingBox.clone();
  const result=inspectionNormals(source);
  assert.equal(result.owned,true);assert.notEqual(result.geometry,source);assert.equal(source.getAttribute('normal'),undefined);
  assert.deepEqual(Array.from(result.geometry.getAttribute('position').array),position);assert.deepEqual(Array.from(result.geometry.index.array),indices);
  result.geometry.computeBoundingBox();assert.deepEqual(result.geometry.boundingBox,bounds);
  assert.ok(Array.from(result.geometry.getAttribute('normal').array).every(Number.isFinite));
  assert.deepEqual(inspectionNormals(result.geometry),{geometry:result.geometry,owned:false});
  result.geometry.dispose();source.dispose();
});

test('detail layers retain separate cloned colours while core surfaces use declared display families',async()=>{
  const {MeshStandardMaterial}=await import('three');const {inspectionMaterial}=await import('../src/components/inspectionOrbit.ts');
  const ply=new MeshStandardMaterial({color:'#c49460',roughness:.9}),bond=new MeshStandardMaterial({color:'#455b80',roughness:.7});
  const a=inspectionMaterial(ply,'plywood','#89bdcf',true),b=inspectionMaterial(bond,'plywood','#89bdcf',true);
  assert.notEqual(a,ply);assert.notEqual(b,bond);assert.equal(a.color.getHexString(),'c49460');assert.equal(b.color.getHexString(),'455b80');
  assert.equal(a.userData.inspectionBaseColor,'#c49460');assert.equal(b.userData.inspectionBaseColor,'#455b80');
  const core=inspectionMaterial(ply,'cardboard','#89bdcf');assert.equal(core.color.getHexString(),'89bdcf');assert.equal(core.metalness,0);
  for(const material of [ply,bond,a,b,core])material.dispose();
});

 test('clearing the selected subsystem fits restored visible assembly rather than empty selection',async()=>{
 const {inspectionFitScope}=await import('../src/components/inspectionOrbit.ts');
 assert.equal(inspectionFitScope(false,'selection',[]),null);
 assert.deepEqual(inspectionFitScope(true,'assembly',['ring']),['ring']);
 assert.deepEqual(inspectionFitScope(false,'selection',['motor']),['motor']);
 assert.equal(inspectionFitScope(false,'assembly',['motor']),null);
 });
