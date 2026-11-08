import assert from 'node:assert/strict';
import test from 'node:test';
import { interiorShellIds,interiorHiddenIds } from '../src/components/interiorWorkflow.ts';
const vehicle={parts:[{id:'body',outer_body:true},{id:'nose',nose:true},{id:'motor'},{id:'ring'},{id:'cell'}]};
test('interior visibility hides only source-labelled outer shell and reveals selected subsystem without changing positions',()=>{
 const before={hiddenIds:['motor','cell'],exploded:0,section:false,ghostShell:false};
 assert.deepEqual(interiorShellIds(vehicle),['body','nose']);
 assert.deepEqual(interiorHiddenIds(vehicle,before,['motor','ring']),['cell','body','nose']);
 assert.deepEqual(before.hiddenIds,['motor','cell']);
});
test('an unknown or meshless record does not invent a shell, hidden part or component geometry',()=>{
 assert.deepEqual(interiorShellIds({parts:[{id:'kevlar'}]}),[]);
 assert.deepEqual(interiorHiddenIds(vehicle,{hiddenIds:[],exploded:0,section:false,ghostShell:false},['unknown']),['body','nose']);
});
