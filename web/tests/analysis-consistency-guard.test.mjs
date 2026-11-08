import assert from 'node:assert/strict';
import test from 'node:test';
import {parseAnalysisManifest} from '../src/analysis/responseGuard.ts';
function source(){return {schema_version:'rocket-twin.analysis.v1',flight_ready:false,api_id:'fixture',run_id:'run',coordinate_frame:'CAD_mm_registered_to_viewer_m',compatible:true,identity:{configuration_id:'software-only',resolved_spec_sha256:'a'.repeat(64),cad_revision_sha256:'b'.repeat(64),part_shape_sha256:{part:'c'.repeat(64)}},cases:{case:{}},tools:{},input_sha256:{},artifacts:{},fields:[{id:'field',case_id:'case',quantity:'stress',component:'normal',units:'Pa',part_ids:['part'],sample_count:1,association:'part',coverage_notes:'Software-only',reported_extrema:{},evidence:{provenance:'calculated',validation:'unvalidated',assumptions:[],limits:[],sources:[],required_physical_tests:[],uncertainty:'unknown'},times_s:null,artifact:'field.json',artifact_sha256:'d'.repeat(64)}]};}
test('recorded field response preserves the backend evidence/association/criterion consistency rules',()=>{
  const good=source();assert.equal(parseAnalysisManifest(good,'fixture','run'),good);
  for(const mutate of [x=>x.flight_ready=true,x=>delete x.flight_ready,x=>x.fields[0].sample_count=2,x=>x.fields[0].evidence.provenance='measured',x=>x.fields[0].association='node',x=>Object.assign(x.fields[0],{quantity:'design_margin',units:'1',margin_definition:null}),x=>{const f=x.fields[0];Object.assign(f,{sample_count:0,artifact:null,unavailable_reason:'No result'});f.evidence.provenance='unavailable';f.evidence.validation='numerically_verified';}]){
    const bad=source();mutate(bad);assert.throws(()=>parseAnalysisManifest(bad,'fixture','run'),/malformed|inconsistent/);
  }
  const unavailable=source(),f=unavailable.fields[0];Object.assign(f,{sample_count:0,artifact:null,unavailable_reason:'No result'});f.evidence.provenance='unavailable';f.evidence.validation='unavailable';assert.equal(parseAnalysisManifest(unavailable,'fixture','run'),unavailable);
});
