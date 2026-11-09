import assert from 'node:assert/strict';
import test from 'node:test';
import { readFileSync } from 'node:fs';
import { componentDepthAccess } from '../src/components/componentDepthAdmission.ts';
const core = JSON.parse(readFileSync(new URL('../../docs/studies/rp1-inspection-geometry-20261107/manifest.json', import.meta.url)));
function source() {
  return {
    id: 'G80-F2-RP1-AD1-definition-v2',
    identity: { configuration_id: core.identity.configuration_id, specification_sha256: core.identity.specification_sha256, inspection_geometry_sha256: core.identity.inspection_geometry_sha256 },
    parts: core.parts.map(p=>({id:p.id, inspection_shape_sha256:p.inspection_shape_sha256})), summary: {},
  };
}
test('current PCB and mechanical parts expose separate source-based detail kinds', () => {
  const vehicle = source();
  for (const id of ['fin_set','fin_tabs','root_gussets','body','motor_tube','forward_ring','aft_ring']) {
    const result = componentDepthAccess(vehicle,vehicle.parts.find(p=>p.id===id));
    assert.equal(result.available,true,id); assert.equal(result.kind,'mechanical');
  }
  assert.equal(componentDepthAccess(vehicle,vehicle.parts.find(p=>p.id==='high_g_accel')).kind,'pcb');
});
test('foreign, stale, incomplete and copied part objects cannot open source detail', () => {
  for (const mutate of [v=>v.id='modular-performance-v1',v=>v.identity.configuration_id='other',v=>v.identity.specification_sha256='0'.repeat(64),v=>v.identity.inspection_geometry_sha256='0'.repeat(64),v=>v.parts.pop(),v=>v.parts.push(v.parts[0]),v=>v.parts.find(p=>p.id==='high_g_accel').inspection_shape_sha256='0'.repeat(64)]) {
    const vehicle=source(); mutate(vehicle); assert.equal(componentDepthAccess(vehicle,vehicle.parts.find(p=>p.id==='high_g_accel')).available,false);
  }
  const vehicle=source(), part=vehicle.parts.find(p=>p.id==='forward_ring');
  assert.equal(componentDepthAccess(vehicle,{...part}).available,false);
});
test('undefined hardware and distributed allowances stay explicitly unavailable', () => {
  const vehicle=source();
  for (const id of ['independent_recovery','motor_retainer','fin_internal_bonds','rp1_kevlar_wrap']) {
    const result=componentDepthAccess(vehicle,vehicle.parts.find(p=>p.id===id));
    assert.equal(result.available,false); assert.match(result.reason,/not yet defined/);
  }
});
