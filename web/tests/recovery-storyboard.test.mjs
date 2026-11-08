import assert from 'node:assert/strict';
import test from 'node:test';
import {recoveryStoryboard} from '../src/experiments/recoverySequenceState.ts';
const record={run_id:'saved',configuration:'archived',events:{apogee:9,deployment:10,landing:100}};
test('recovery symbol requires a valid saved deployment event reached inside that run window',()=>{
  const window={start:0,end:100};
  assert.equal(recoveryStoryboard(record,9.999,window).reached,false);
  assert.equal(recoveryStoryboard(record,10,window).reached,true);
  assert.equal(recoveryStoryboard(record,11.150,window).reached,true);
  assert.equal(recoveryStoryboard(record,100,window).landed,true);
  for(const time of [-1,101,NaN])assert.equal(recoveryStoryboard(record,time,window).reached,false);
  assert.equal(recoveryStoryboard(record,11,null).reached,false);
  for(const events of [{apogee:12,deployment:10},{deployment:10,landing:9},{deployment:null},{deployment:NaN}])
    assert.equal(recoveryStoryboard({...record,events},11,window).reached,false);
  assert.equal(recoveryStoryboard(record,60,{start:0,end:45}).reached,false,'unequal recorded support cannot hold a canopy icon past its run');
});
test('actual React graphic distinguishes event marker, model and unavailable physical mechanism without changing pose',async()=>{
  const {createServer}=await import('vite');const {default:React}=await import('react');const {renderToStaticMarkup}=await import('react-dom/server');
  const server=await createServer({configFile:false,root:new URL('..',import.meta.url).pathname,server:{middlewareMode:true,hmr:false,ws:false},appType:'custom'});
  try{const {RecoveryStoryboard}=await server.ssrLoadModule('/src/experiments/RecoveryStoryboard.tsx');
    const render=(time,window={start:0,end:100})=>renderToStaticMarkup(React.createElement(RecoveryStoryboard,{record,time,window}));
    const after=render(11.15);assert.match(after,/data-recovery-symbol="event-derived"/);
    for(const text of ['not a flight pose','Line forces: unavailable','Section poses: unavailable','recorded rigid body','saved orientation','non-spatial diagram','deployment success'])assert.ok(after.includes(text),text);
    assert.doesNotMatch(render(9),/data-recovery-symbol/);assert.doesNotMatch(render(60,{start:0,end:45}),/data-recovery-symbol/);
  }finally{await server.close();}
});
