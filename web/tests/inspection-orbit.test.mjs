import assert from 'node:assert/strict';
import test from 'node:test';
import {Box3,PerspectiveCamera,Vector3} from 'three';
import {applyOrbit,orbitAngles,orbitBasis,orbitClips,panOrbit} from '../src/components/inspectionOrbit.ts';
import {fitOrbitFrame} from '../src/components/inspectionCamera.ts';
const close=(a,b)=>assert.ok(Math.abs(a-b)<1e-8,`${a} != ${b}`);

test('precise azimuth/tilt/roll round trips including both poles and multiple horizontal turns',()=>{
  const camera=new PerspectiveCamera(35,1.8,.001,100),target=new Vector3(.1,.4,-.2);
  for(const a of [0,35,90,180,359,395,1080+35])for(const t of [0,.01,25,90,179.99,180])for(const r of [-170,0,15,90,179]){
    const angles={azimuth:a,tilt:t,roll:r};const basis=orbitBasis(angles);
    close(basis.direction.length(),1);close(basis.up.length(),1);close(basis.direction.dot(basis.up),0);
    applyOrbit(camera,target,3,angles);
    const actual=orbitAngles(camera,target,a);
    close(actual.azimuth,a);assert.ok(Math.abs(actual.tilt-t)<1e-6);close(actual.roll,r);
    const up=new Vector3(0,1,0).applyQuaternion(camera.quaternion);
    assert.ok(up.distanceTo(basis.up)<1e-9);
    const projected=target.clone().project(camera);close(projected.x,0);close(projected.y,0);
  }
  assert.throws(()=>orbitBasis({azimuth:NaN,tilt:0,roll:0}),RangeError);
  assert.throws(()=>orbitBasis({azimuth:0,tilt:181,roll:0}),RangeError);
});

test('Fit and Frame preserve actual rolled camera basis and project complete corners safely',()=>{
  for(const bounds of [new Box3(new Vector3(-.04,0,-.04),new Vector3(.04,1.2,.04)),new Box3(new Vector3(-.0001,-.0002,-.0003),new Vector3(.0001,.0002,.0003))])for(const tilt of [0,25,90,180]){
    const camera=new PerspectiveCamera(35,1.3,.001,100),target=new Vector3();
    applyOrbit(camera,target,3,{azimuth:35,tilt,roll:15});
    const before=orbitAngles(camera,target,35);
    const result=fitOrbitFrame(bounds,1.3,35,camera.position,target,camera.up,{fill:.8});
    camera.position.fromArray(result.position);camera.up.fromArray(result.up);target.fromArray(result.target);camera.lookAt(target);camera.near=result.near;camera.far=result.far;camera.updateProjectionMatrix();camera.updateMatrixWorld();
    const after=orbitAngles(camera,target,35);
    close(before.azimuth,after.azimuth);assert.ok(Math.abs(before.tilt-after.tilt)<1e-6);close(before.roll,after.roll);
    for(const x of [bounds.min.x,bounds.max.x])for(const y of [bounds.min.y,bounds.max.y])for(const z of [bounds.min.z,bounds.max.z]){
      const p=new Vector3(x,y,z).project(camera);assert.ok(Math.abs(p.x)<=.8000001&&Math.abs(p.y)<=.8000001);assert.ok(p.z>-1&&p.z<1);
    }
  }
});

test('manual close zoom, pullback and rolled pan update view-depth planes without moving the chosen angle',()=>{
  const camera=new PerspectiveCamera(35,1.4,.001,100),target=new Vector3();
  for(const scale of [1,.001])for(const distance of [scale*3,scale*30,100]){
    const bounds=new Box3(new Vector3(-scale,-scale,-scale),new Vector3(scale,scale,scale));
    applyOrbit(camera,target,distance,{azimuth:35,tilt:25,roll:15});
    const clips=orbitClips(bounds,camera,target);camera.near=clips.near;camera.far=clips.far;camera.updateProjectionMatrix();
    assert.ok(clips.near>0&&clips.far>clips.near);
    for(const x of [-scale,scale])for(const y of [-scale,scale])for(const z of [-scale,scale]){const p=new Vector3(x,y,z).project(camera);assert.ok(p.z>-1&&p.z<1);}
  }
  const before=orbitAngles(camera,target,35),distance=camera.position.distanceTo(target);
  panOrbit(target,camera,100,-50,800);camera.lookAt(target);camera.updateMatrixWorld();
  const after=orbitAngles(camera,target,35);
  close(before.azimuth,after.azimuth);close(before.tilt,after.tilt);close(before.roll,after.roll);close(camera.position.distanceTo(target),distance);
});

test('RP1 final display translation is used once by fitting; archived explosion remains scaled',async()=>{
  const {inspectionSceneBounds}=await import('../src/components/inspectionSceneBounds.ts');
  const source=new Box3(new Vector3(-.01,0,-.01),new Vector3(.01,.2,.01));
  const records=new Map([['motor',{bounds:source,explodeOffset:[0,3,0],displayOffset:[.14,.01,0]}],['archive',{bounds:source,explodeOffset:[0,3,0]}]]);
  const rp1=inspectionSceneBounds(records,['motor'],.7).bounds;
  close(rp1.min.x,.13);close(rp1.min.y,.01);
  const legacy=inspectionSceneBounds(records,['archive'],.7).bounds;
  close(legacy.min.y,2.1);
  records.set('motor',{bounds:source,explodeOffset:[0,3,0],displayOffset:[0,0,0]});
  assert.deepEqual(inspectionSceneBounds(records,['motor'],0).bounds,source);
  assert.deepEqual(source.min.toArray(),[-.01,0,-.01]);
});

test('camera UI is reachable without Scene tools and exposes actual custom angles, target and keyboard pan',async()=>{
  const {createServer}=await import('vite');
  const {default:React}=await import('react');
  const {renderToStaticMarkup}=await import('react-dom/server');
  const server=await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
  try{
    const {OrbitCameraControls}=await server.ssrLoadModule('/src/components/OrbitCameraControls.tsx');
    const html=renderToStaticMarkup(React.createElement(OrbitCameraControls,{readout:{azimuth:35,tilt:25,roll:15,mode:'Custom',target:'selection'},canTargetSelection:true,onAngles:()=>{},onTarget:()=>{},onPan:()=>{}}));
    for(const text of ['Orbit / camera','Custom','Horizontal angle','Nose-to-aft tilt','View roll','Apply camera angles','Actual camera angles','35.0','25.0','15.0','Orbit target','Selected group / part','Pan left','Pan right','Pan up','Pan down','trackpad','Alt-drag'])assert.ok(html.includes(text),text);
  }finally{await server.close();}
});
