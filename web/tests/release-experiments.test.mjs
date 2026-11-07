import assert from 'node:assert/strict';
import test from 'node:test';
import React from '../node_modules/react/index.js';
import { renderToStaticMarkup } from '../node_modules/react-dom/server.node.js';
import { createServer } from '../node_modules/vite/dist/node/index.js';
import { batchDeclaration, requestDraft, terminalStatuses } from '../src/experiments/runLifecycle.ts';
import { adjustPlotWindow, plotSegments, recordedAlignment } from '../src/experiments/plotWindow.ts';
import { telemetryCsv, exportMetadata } from '../src/experiments/runExport.ts';

const request = {configuration:'modular-performance-v1',wind_mps:1,wind_direction_deg:90,gust_mps:0,preset:'tiny',seed:42};
const record = {run_id:'fixture-A',configuration:request.configuration,settings:request,controller:'locked, unguided'};

test('request drafts preserve supported effective request fields and reject candidate borrowing', () => {
  assert.deepEqual(requestDraft(record, request.configuration), request);
  assert.throws(() => requestDraft(record,'G80-F2-RP1-AD1-definition-v2'), /eligible/);
  assert.throws(() => requestDraft({...record,settings:{...request,seed:-1}},request.configuration), /ranges/);
  assert.throws(() => requestDraft({...record,settings:{...request,unknown:1}},request.configuration), /unsupported overrides/);
  assert.deepEqual(terminalStatuses,['complete','failed','cancelled','interrupted']);
  const declaration=batchDeclaration([request,{...request,seed:43}]);
  assert.equal(declaration.count,2); assert.equal(declaration.concurrency,1); assert.equal(declaration.max_steps,18000);
  assert.deepEqual(declaration.cases.map(c=>c.seed),[42,43]);
  assert.throws(()=>batchDeclaration([request]),/two and four/);
});

test('recorded alignment, unequal support and missing samples remain explicit gaps', () => {
  assert.deepEqual(recordedAlignment('burnout',{burnout:2},{burnout:3}), {event:'burnout',a:2,b:3,reason:null});
  const absent=recordedAlignment('landing',{landing:5},{landing:null});
  assert.equal(absent.a,0);assert.equal(absent.b,0);assert.match(absent.reason,/unavailable/);
  const segments=plotSegments([0,1,2,3,4],[3,4,NaN,7,8],1,{start:-1,end:3});
  assert.deepEqual(segments,[[[-1,3],[0,4]],[[2,7],[3,8]]]);
  assert.deepEqual(plotSegments([0,1],[9,10],0,{start:2,end:4}),[]);
  assert.deepEqual(plotSegments([0,0],[9,10],0,{start:0,end:1}),[]);
  assert.deepEqual(adjustPlotWindow({start:0,end:10},{start:0,end:10},'in'),{start:2.5,end:7.5});
  assert.deepEqual(adjustPlotWindow({start:0,end:10},{start:0,end:10},'left'),{start:0,end:10});
});

test('selected exports retain native timestamps, alignment metadata and blank values', () => {
  const run={record,telemetry:{frame:'fixture',columns:{time_s:[0,1,2,3],height_m:[0,null,9,4]}}};
  const selection={start_s:-1,end_s:0,offset_s:2,peer_offset_s:3,alignment_event:'burnout'};
  assert.equal(telemetryCsv(run,selection),'time_s,height_m\r\n1,\r\n2,9\r\n');
  const meta=JSON.parse(exportMetadata(run,null,selection));
  assert.equal(meta.selection.selected_sample_count,2);
  assert.equal(meta.selection.offset_s,2);assert.equal(meta.selection.alignment_event,'burnout');
  assert.match(meta.selection.clock,/CSV keeps original/);
  assert.throws(()=>telemetryCsv(run,{...selection,end_s:-2}),/invalid range/);
});

test('experiment SSR exposes the bounded workflow and preserves unsupported RP1 state', async () => {
  const server=await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
  try {
    const {default:Experiment}=await server.ssrLoadModule('/src/experiments/Experiment.tsx');
    const html=renderToStaticMarkup(React.createElement(Experiment,{configurationId:'G80-F2-RP1-AD1-definition-v2',vehicle:null,onConfigurationChange:()=>{},workspace:'experiments'}));
    for(const text of ['Bounded seed sweep','Random seed','9,000 steps','Cancellation is cooperative','Saved runs','no supported complete flight configuration','no candidate is silently','Run on CPU']) assert.ok(html.includes(text),text);
    assert.match(html,/disabled=""[^>]*>Run on CPU/);
  } finally { await server.close(); }
});

test('playback profiling stays bounded and library filters keep failed members visible', async () => {
  const {frameProfile,filterRuns}=await import('../src/experiments/playbackProfile.ts');
  const result=frameProfile([...Array(700).fill(16),32]);
  assert.equal(result.samples,600);assert.equal(result.p50_ms,16);assert.equal(result.max_ms,32);
  assert.equal(frameProfile([NaN,0,-1]),null);
  const library=[{...record,status:'failed',batch_id:'batch-a'},{...record,run_id:'fixture-B',status:'complete'}];
  assert.deepEqual(filterRuns(library,'BATCH-A','all').map(r=>r.status),['failed']);
  assert.deepEqual(filterRuns(library,'','failed').map(r=>r.run_id),['fixture-A']);
  assert.deepEqual(filterRuns(library,'not-present','all'),[]);
  assert.throws(()=>requestDraft({...record,settings:{...request,seed:undefined}},request.configuration),/seed/);
});

test('full-rate is explicit, bounded and rejects decimated or truncated responses', async () => {
  const {telemetryUrl,validatePlaybackProfile,browserHeap}=await import('../src/experiments/playbackMode.ts');
  assert.equal(telemetryUrl('fixture-A','bounded'),'/api/runs/fixture-A/telemetry');
  assert.match(telemetryUrl('fixture-A','full-rate-benchmark'),/playback=full-rate-benchmark/);
  const payload={full_sample_count:3,returned_sample_count:3,sampling:{mode:'full-rate-benchmark'},columns:{time_s:[0,.001,.002],height_m:[0,1,2]}};
  assert.doesNotThrow(()=>validatePlaybackProfile(payload,'full-rate-benchmark'));
  assert.throws(()=>validatePlaybackProfile({...payload,full_sample_count:132856},'full-rate-benchmark'),/incomplete/);
  assert.throws(()=>validatePlaybackProfile({...payload,sampling:{mode:'bounded'}},'full-rate-benchmark'),/decimated/);
  assert.equal(browserHeap({}),null);
  assert.deepEqual(browserHeap({memory:{usedJSHeapSize:12,totalJSHeapSize:20,jsHeapSizeLimit:100}}),{used:12,total:20,limit:100});
});
