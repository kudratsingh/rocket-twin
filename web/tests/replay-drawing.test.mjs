import assert from 'node:assert/strict';
import test from 'node:test';
import {selectReplayDrawing,replayDrawingDiagnostics} from '../src/experiments/replayDrawing.ts';
import {telemetryCsv} from '../src/experiments/runExport.ts';

const indices=result=>result.segments.flat();

test('bounded native-index drawing preserves gaps, exact endpoints/extrema and recorded-event neighbours',()=>{
  const times=Object.freeze(Array.from({length:10000},(_,i)=>i*.001));
  const values=Array.from(times,(_,i)=>Math.sin(i*.01));values[1234]=100;values[5678]=-100;
  for(let i=3000;i<=3003;i++)values[i]=NaN;
  Object.freeze(values);
  const result=selectReplayDrawing(times,[values],{maxVertices:120,events:{burnout:times[1234],landing:times.at(-1),gap:times[3001],absent:null}});
  assert.equal(result.status,'ready');assert.ok(result.drawn_samples<=120);assert.equal(result.source_samples,10000);assert.equal(result.valid_samples,9996);assert.equal(result.segments.length,2);
  const chosen=new Set(indices(result));
  for(const index of [0,9999,1234,5678,2999,3004,1233,1235,9998])assert.ok(chosen.has(index),String(index));
  assert.ok(result.unavailable_events.includes('gap'));assert.ok(result.unavailable_events.includes('absent'));
  for(const segment of result.segments){assert.ok(segment.every((index,i)=>Number.isFinite(values[index])&&(i===0||index>segment[i-1])));assert.ok(segment.at(-1)<3000||segment[0]>3003,'no segment crosses the missing interval');}
  assert.ok(result.preparation_ms>=0);assert.match(replayDrawingDiagnostics(result).policy,/Display-only/);
});

test('extrema for all three trajectory coordinates survive a bounded native drawing',()=>{
  const times=Object.freeze(Array.from({length:132856},(_,i)=>(i+1)*.001));
  const x=Array.from(times,(_,i)=>Math.sin(i*.001)),y=Array.from(times,(_,i)=>i*.01),z=Array.from(times,(_,i)=>Math.cos(i*.001));
  x[45001]=500;y[50001]=-100;z[90001]=900;
  const result=selectReplayDrawing(times,[x,y,z],{maxVertices:3000,events:{apogee:times[45000]}});
  assert.equal(result.status,'ready');assert.ok(result.drawn_samples<=3000);
  const chosen=new Set(indices(result));for(const i of [0,132855,45001,50001,90001,44999,45000])assert.ok(chosen.has(i));
});

test('mandatory anchors or disconnected segments exceeding budget withhold instead of connecting gaps',()=>{
  const result=selectReplayDrawing([0,1,2,3,4],[[0,NaN,2,NaN,4]],{maxVertices:2});
  assert.equal(result.status,'withheld');assert.deepEqual(result.segments,[]);assert.match(result.reason,/gap boundaries/);
  const times=Array.from({length:400},(_,i)=>i),values=times.map(i=>i%2?NaN:i);
  const disconnected=selectReplayDrawing(times,[values]);assert.equal(disconnected.status,'withheld');assert.match(disconnected.reason,/128 disconnected/);
});

test('display range/alignment uses native indices and never extrapolates or modifies export samples',()=>{
  const times=Object.freeze([10,11,12,13,14,15]),values=Object.freeze([0,1,20,3,4,5]);
  const run={record:{run_id:'fixture'},telemetry:{columns:{time_s:times,value:values}}};const before=telemetryCsv(run);
  const result=selectReplayDrawing(times,[values],{maxVertices:10,window:{start:2,end:4},offset:10,events:{event:13}});
  assert.deepEqual(indices(result),[2,3,4]);assert.equal(telemetryCsv(run),before);
  assert.deepEqual(times,[10,11,12,13,14,15]);assert.deepEqual(values,[0,1,20,3,4,5]);
  assert.equal(selectReplayDrawing(times,[values],{window:{start:100,end:101}}).status,'withheld');
  assert.equal(selectReplayDrawing([0,0,1],[[1,2,3]]).status,'withheld');
  assert.equal(selectReplayDrawing(times,[[1]]).status,'withheld');
});


test('irregular backend sample spacing alone does not invent a gap or a missing event',()=>{
  const result=selectReplayDrawing([0,.001,.05,1.5,4],[[0,1,2,3,4]],{events:{event:1.4}});
  assert.equal(result.status,'ready');assert.deepEqual(result.segments,[[0,1,2,3,4]]);assert.deepEqual(result.unavailable_events,[]);
  assert.ok(result.event_indices.includes(2)&&result.event_indices.includes(3));
});
