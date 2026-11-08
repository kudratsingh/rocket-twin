import assert from 'node:assert/strict';
import test from 'node:test';
import {replayDiagnosticReport} from '../src/experiments/replayDiagnosticReport.ts';
const context={primary:{run_id:'saved',configuration:'archived',code_sha256:'a'.repeat(64)},profileMode:'full-rate-benchmark',frameDeltas:[16,17],sourceRows:132856,returnedRows:132856,drawingA:{drawn_samples:2999},loadProfile:null,scrubProfile:null,heap:null,viewport:{width:1440,height:900,devicePixelRatio:2},userAgent:'software-only fixture'};
test('diagnostic export retains unrounded recent intervals/source and reports the unchanged target separately from acceptance',()=>{
  const values=[16.6666668,16.6666668];const result=replayDiagnosticReport({...context,frameDeltas:values});
  assert.deepEqual(result.frames.raw_intervals_ms,values);assert.equal(result.frames.mean_interval_target_met,false);
  assert.equal(result.frames.target_interval_ms,1000/60);assert.equal(result.engineering_or_flight_approval,false);assert.equal(result.simulation_started,false);
  assert.equal(result.source.primary.run_id,'saved');assert.equal(result.returned_rows,132856);assert.equal(result.environment.viewport_css_pixels.width,1440);assert.equal(result.javascript_heap,null);
  assert.equal(result.frames.acceptance.startsWith('No automatic'),true);assert.deepEqual(values,[16.6666668,16.6666668]);
  const many=replayDiagnosticReport({...context,frameDeltas:Array.from({length:800},(_,i)=>i+1)});assert.equal(many.frames.raw_intervals_ms.length,600);assert.equal(many.frames.raw_intervals_ms[0],201);
});
test('invalid interval or viewport observations cannot be silently filtered into a passing measurement',()=>{
  for(const frameDeltas of [[],[NaN,16],[0,16],[-1,16]]){const result=replayDiagnosticReport({...context,frameDeltas});assert.equal(result.frames.profile,null);assert.equal(result.frames.mean_interval_target_met,null);}
  assert.equal(replayDiagnosticReport({...context,viewport:{width:0,height:900,devicePixelRatio:1}}).environment.viewport_css_pixels,null);
});


test('export-time canvas visibility is explicit and cannot be confused with playback visibility',()=>{
 const visible=replayDiagnosticReport({...context,viewport:{width:1440,height:900,devicePixelRatio:2,canvasWidth:1000,canvasHeight:600,canvasLeft:200,canvasTop:100}});
 assert.equal(visible.environment.canvas_visible_area_fraction_at_export,1);
 const offscreen=replayDiagnosticReport({...context,viewport:{width:1440,height:900,devicePixelRatio:2,canvasWidth:1000,canvasHeight:600,canvasLeft:200,canvasTop:-700}});
 assert.equal(offscreen.environment.canvas_visible_area_fraction_at_export,0);assert.match(offscreen.environment.canvas_visibility_scope,/does not establish visibility during/);
 assert.equal(replayDiagnosticReport(context).environment.canvas_visible_area_fraction_at_export,null);
});
