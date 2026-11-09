import assert from 'node:assert/strict';
import test from 'node:test';
import { Vector3 } from 'three';
import { DEFAULT_SECTION, inspectionSectionPlane, sectionDimensions } from '../src/components/inspectionSection.ts';
import { isPointClipped } from '../src/components/inspectionCamera.ts';
const dims={lengthM:1.25,radiusM:0.033401};
const eps=(a,b)=>assert.ok(Math.abs(a-b)<1e-12,`${a} != ${b}`);
test('default preserves X=0 cut, offset uses millimetres and clip hit-test uses the same side',()=>{
 const p=inspectionSectionPlane(DEFAULT_SECTION,dims);
 eps(p.distanceToPoint(new Vector3(.01,.6,0)),-.01);
 assert.equal(isPointClipped(new Vector3(.01,.6,0),p,true),true);
 assert.equal(isPointClipped(new Vector3(-.01,.6,0),p,true),false);
 assert.equal(isPointClipped(new Vector3(.01,.6,0),p,false),false);
 const shifted=inspectionSectionPlane({...DEFAULT_SECTION,offsetMm:10},dims);
 eps(shifted.distanceToPoint(new Vector3(.01,0,0)),0);
 eps(shifted.distanceToPoint(new Vector3(.005,0,0)),.005);
});
test('rotating the normal, and a 60 degree radial passage, have independently known dot products',()=>{
 const p=inspectionSectionPlane({...DEFAULT_SECTION,angleDeg:90},dims);
 eps(p.distanceToPoint(new Vector3(.01,.6,.02)),-.02);
 const throughPassage=inspectionSectionPlane({...DEFAULT_SECTION,angleDeg:150},dims);
 const r=.02,angle=Math.PI/3;
 eps(throughPassage.distanceToPoint(new Vector3(r*Math.cos(angle),.6,r*Math.sin(angle))),0);
 eps(inspectionSectionPlane({...DEFAULT_SECTION,angleDeg:450},dims).normal.z,-1);
});
test('transverse cut uses recorded nose station and opposite side negates every signed distance',()=>{
 const s={...DEFAULT_SECTION,mode:'transverse',stationMm:1100};
 const p=inspectionSectionPlane(s,dims),reverse=inspectionSectionPlane({...s,flipped:true},dims);
 eps(p.distanceToPoint(new Vector3(0,.15,0)),0);
 eps(p.distanceToPoint(new Vector3(0,.2,0)),-.05);
 eps(reverse.distanceToPoint(new Vector3(0,.2,0)),.05);
});
test('unknown dimensions and invalid bounds cannot create fabricated cuts',()=>{
 assert.deepEqual(sectionDimensions({geometry:{},summary:{},id:'missing'}),{lengthM:null,radiusM:null});
 const unknown={lengthM:null,radiusM:null};
 assert.equal(inspectionSectionPlane(DEFAULT_SECTION,unknown).constant,0);
 assert.throws(()=>inspectionSectionPlane({...DEFAULT_SECTION,offsetMm:1},unknown),RangeError);
 assert.throws(()=>inspectionSectionPlane({...DEFAULT_SECTION,mode:'transverse'},unknown),RangeError);
 for(const settings of [{...DEFAULT_SECTION,angleDeg:NaN},{...DEFAULT_SECTION,offsetMm:34},{...DEFAULT_SECTION,mode:'transverse',stationMm:1250.1},{...DEFAULT_SECTION,mode:'transverse',stationMm:-1}])assert.throws(()=>inspectionSectionPlane(settings,dims),RangeError);
 assert.deepEqual(sectionDimensions({geometry:{length_m:1.25,diameter_m:.066802},summary:{}}),dims);
});
