import assert from 'node:assert/strict';
import test from 'node:test';
import { functionalGroupOpen } from '../src/components/groupExpansion.ts';
import { useInspection } from '../src/store.ts';
test('manual collapse wins for the current selection; a new pick including the same part reveals the group',()=>{
 const s=()=>useInspection.getState();s().resetVehicle();s().select('motor');
 const closed={motor_retention:s().selectionToken};
 assert.equal(functionalGroupOpen('motor_retention',false,'motor_retention',s().selectionToken,closed),false);
 s().select('motor');
 assert.equal(functionalGroupOpen('motor_retention',false,'motor_retention',s().selectionToken,closed),true);
 assert.equal(functionalGroupOpen('motor_retention',false,'recovery',s().selectionToken,closed),false);
 assert.equal(functionalGroupOpen('motor_retention',true,'recovery',s().selectionToken,closed),true);
});
test('selecting a group reveals it; clearing a part does not manufacture a new reveal event',()=>{
 const s=()=>useInspection.getState();s().resetVehicle();s().selectGroup('recovery',['parachute']);const token=s().selectionToken;
 s().select(null);assert.equal(s().selectionToken,token);assert.equal(s().selectedGroupId,'recovery');
 s().selectGroup('recovery',['parachute']);assert.ok(s().selectionToken>token);
});
