import assert from 'node:assert/strict';
import test from 'node:test';
import { presentationGroups, recordedQuantity, representationLabel } from '../src/components/presentationGroups.ts';
const ids = Array.from({length:55}, (_,i) => `part_${i}`);
const groups = Array.from({length:6}, (_,i) => ({ id:["nose_airframe","fins_roots","motor_retention","recovery","avionics_power","launch_finish"][i],label:`Group ${i}`,description:'Display grouping only', record_count:ids.filter((_,n)=>n%6===i).length,mesh_count:0,part_ids:ids.filter((_,n)=>n%6===i) }));
const source = {configuration_id:'G80-F2-RP1-AD1-definition-v2', specification_sha256:'811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660',inspection_geometry_sha256:'238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608'};
const fixture = () => ({id:source.configuration_id,identity:{specification_sha256:source.specification_sha256,inspection_geometry_sha256:source.inspection_geometry_sha256},parts:ids.map(id=>({id})),summary:{presentation:{id:'rp1-ad1-v2-functional-presentation-v1',schema_version:1,presentation_sha256:'4ed997e371f8b2473d9da47aee7396562cb9b4d7e031d87f9876025b136c005b',breakdown:{kind:'staged-display-illustration',assembly_stage_end:.5,manufacturing_clearance:false,units:'m'},source_tuple:{...source},geometry_compatible:true,groups:structuredClone(groups)}}});
test('exact membership has one functional home for every source record',()=>{
 assert.equal(presentationGroups(fixture()).flatMap(g=>g.part_ids).length,55);
 const duplicate=fixture();duplicate.summary.presentation.groups[0].part_ids.push('part_1');assert.deepEqual(presentationGroups(duplicate),[]);
 const missing=fixture();missing.summary.presentation.groups[0].part_ids.pop();assert.deepEqual(presentationGroups(missing),[]);
 const foreign=fixture();foreign.summary.presentation.groups[0].part_ids[0]='foreign';assert.deepEqual(presentationGroups(foreign),[]);
});
test('group maps fail closed on wrong geometry, design or specification and missing backend projection',()=>{
 for(const key of Object.keys(source)){const d=fixture();d.summary.presentation.source_tuple[key]='foreign';assert.deepEqual(presentationGroups(d),[]);}
 const d=fixture();d.id='historical-G80';assert.deepEqual(presentationGroups(d),[]);
 assert.deepEqual(presentationGroups({...fixture(),summary:{}}),[]);
});
test('record quantity and maturity do not infer pieces from rows or mesh existence',()=>{
 assert.equal(recordedQuantity({representation:{presentation:{quantity:null}}}),null);
 assert.equal(recordedQuantity({representation:{presentation:{quantity:{value:3,unit:'fins',basis:'source'}}}}),'3 fins (source recorded)');
 assert.equal(representationLabel({representation:{presentation:{maturity:'mass_allowance'}}}),'Mass/process allowance — no separate solid');
 assert.equal(representationLabel({mesh_url:null}),'No display solid');
});
