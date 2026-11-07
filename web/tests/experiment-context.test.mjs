import assert from 'node:assert/strict';
import test from 'node:test';
import { experimentConfiguration, experimentHref, savedRunHref } from '../src/workspaces/experimentContext.ts';
import { workspaceHref } from '../src/workspaces/navigation.ts';
const parse=(href)=>new URL(href,'http://local.test');
test('supported experiment selection does not replace the RP1 design, source or part',()=>{
 const original='/?workspace=experiments&design=RP1&spec=raw-rp1&part=fin_tabs&run=old&compare=other#evidence';
 const selected=parse(experimentHref(original,'modular-performance-v1'));
 for(const [key,value] of [['design','RP1'],['spec','raw-rp1'],['part','fin_tabs'],['experiment','modular-performance-v1']])assert.equal(selected.searchParams.get(key),value);
 assert.equal(selected.searchParams.has('run'),false);assert.equal(selected.searchParams.has('compare'),false);
 assert.equal(experimentConfiguration(selected.search,'RP1'),'modular-performance-v1');
 assert.equal(experimentConfiguration('','RP1'),'RP1','unsupported RP1 remains explicit; no automatic archive substitution');
 const run=parse(savedRunHref(selected.href,'exp-a',false));const compare=parse(savedRunHref(run.href,'exp-b',true));
 assert.equal(compare.searchParams.get('run'),'exp-a');assert.equal(compare.searchParams.get('compare'),'exp-b');assert.equal(compare.searchParams.get('design'),'RP1');
 const design=parse(workspaceHref(compare.href,'design'));assert.equal(design.searchParams.get('design'),'RP1');assert.equal(design.searchParams.get('part'),'fin_tabs');
 assert.equal(parse(savedRunHref(compare.href,null,true)).searchParams.has('compare'),false);
 assert.equal(parse(original).searchParams.get('experiment'),null,'input URL remains immutable');
});
