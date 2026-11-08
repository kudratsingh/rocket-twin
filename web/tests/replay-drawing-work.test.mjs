import assert from 'node:assert/strict';
import test from 'node:test';
import {readFile} from 'node:fs/promises';
import {LineGeometry,Line2,LineMaterial} from 'three-stdlib';
import {plotSegments} from '../src/experiments/plotWindow.ts';
import {plotScale} from '../src/experiments/plotScale.ts';
import {measureReplayWork} from '../src/experiments/replayWorkProfile.ts';

// Frozen first/only actual-data baseline from this packet. Do not overwrite it
// with a changed-source or browser result; timings below are Node preparation only.
export const REPLAY_WORK_OBSERVATION_JSON = `{
  "source_run_id":"exp-ab60bd4ac5c2412a9dd85f712072bca2",
  "record_sha256_before":"a21d8edd08c452f0b21a94c039971c5bfcd6145ee29330afd66c086da50ff49b",
  "record_sha256_after":"a21d8edd08c452f0b21a94c039971c5bfcd6145ee29330afd66c086da50ff49b",
  "scope":"Read-only saved-data JavaScript/geometry preparation; not browser paint, GPU timing, FPS, or proof of rendering dominance",
  "rows":132856,
  "trajectory":{"line_instances":132855,"base_triangles":6,"potential_instanced_triangles":797130,"attribute_bytes":4251520,"preparation_ms":24.633500000000026},
  "four_svg_series":{"channels":["north_m","east_m","down_m","thrust_n"],"vertices":531424,"point_string_characters":17343474,"preparation_ms":215.59612500000003},
  "budget":{"attempts":1,"max_cpu_seconds":10,"max_wall_seconds":30,"observed_python_cpu_seconds":0.623217,"observed_child_cpu_seconds":0.660581,"observed_wall_seconds":1.5171689999988303},
  "temporary_fixture_deleted":true,"new_simulation":false,"browser_observed":false
}`;

test('bounded app-owned preparation diagnostic reports actual source work without asserting FPS',async()=>{
  const path=process.env.ROCKET_REPLAY_WORK_JSON;
  const fixture=path?JSON.parse(await readFile(path,'utf8')):{source:'synthetic256',columns:{time_s:Array.from({length:256},(_,i)=>i*.001),north_m:Array.from({length:256},(_,i)=>i*.01),east_m:Array.from({length:256},(_,i)=>Math.sin(i*.01)),down_m:Array.from({length:256},(_,i)=>-i*.1),thrust_n:Array.from({length:256},(_,i)=>i%10)},events:{burnout:.05}};
  const c=fixture.columns,window={start:c.time_s[0],end:c.time_s.at(-1)};
  const trajectory=measureReplayWork('native trajectory LineGeometry preparation',()=>{
    const points=c.time_s.flatMap((_,i)=>[c.east_m[i],-c.down_m[i],-c.north_m[i]]);
    const geometry=new LineGeometry();geometry.setPositions(points);
    const line=new Line2(geometry,new LineMaterial());line.computeLineDistances();
    const instances=Math.min(geometry.instanceCount,geometry.getAttribute('instanceStart').count);
    const buffers=new Set(Object.values(geometry.attributes).map(value=>(value.data?.array??value.array).buffer));
    const result={source_rows:c.time_s.length,line_instances:instances,base_triangles:geometry.index.count/3,potential_instanced_triangles:instances*geometry.index.count/3,attribute_bytes:[...buffers].reduce((sum,value)=>sum+value.byteLength,0)};
    geometry.dispose();line.material.dispose();return result;
  });
  const plots=measureReplayWork('four native SVG point-string preparations',()=>{
    let vertices=0,characters=0;
    for(const name of ['north_m','east_m','down_m','thrust_n']){
      const segments=plotSegments(c.time_s,c[name],0,window);const available=segments.flat().map(([,v])=>v);const bounds=plotScale(available);
      for(const segment of segments){vertices+=segment.length;characters+=segment.map(([t,v])=>`${(t/window.end)*100},${95-(v-bounds.min)/(bounds.max-bounds.min||1)*90}`).join(' ').length;}
    }
    return {svg_vertices:vertices,svg_point_characters:characters};
  });
  assert.equal(trajectory.value.line_instances,c.time_s.length-1);assert.equal(plots.value.svg_vertices,c.time_s.length*4);
  assert.ok(trajectory.timing.elapsed_ms>=0&&plots.timing.elapsed_ms>=0);
  if(path)console.log(JSON.stringify({diagnostic:'actual saved data source/preparation work; not browser or FPS',source:fixture.source,record_sha256:fixture.record_sha256,trajectory,plots}));
});
